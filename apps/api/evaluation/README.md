# Evaluation Framework

This directory contains the evaluation benchmark and scripts for testing the Resume ATS Analyzer pipeline.

## Purpose

The evaluation framework enables:
- **Quality measurement**: Quantify pipeline performance on diverse inputs
- **Hallucination detection**: Zero-tolerance testing for fabricated information
- **Regression prevention**: Catch quality degradation before deployment
- **Continuous monitoring**: Run in CI/CD to maintain quality standards

## Directory Structure

```
evaluation/
├── README.md                    # This file
├── benchmark/                   # Evaluation dataset
│   ├── resumes/                # Test resume files (PDF/DOCX)
│   ├── job_descriptions/       # Test job description files
│   ├── ground_truth/           # Expected outputs (JSON)
│   └── adversarial/            # Adversarial test cases
├── run_eval.py                 # Main evaluation script
├── run_hallucination_eval.py   # Hallucination detection script
└── results/                    # Evaluation results (generated)
```

## Benchmark Dataset

### Resumes (10-15 diverse examples)

**Categories**:
1. **Entry-level** (2-3 resumes)
   - Recent graduates
   - Career changers
   - Minimal experience

2. **Mid-level** (3-4 resumes)
   - 3-7 years experience
   - Multiple roles
   - Diverse skills

3. **Senior-level** (2-3 resumes)
   - 8+ years experience
   - Leadership roles
   - Complex backgrounds

4. **Specialized** (2-3 resumes)
   - Technical roles (engineering, data science)
   - Creative roles (design, marketing)
   - Unique formats or structures

5. **Edge cases** (1-2 resumes)
   - Minimal information
   - Non-standard formats
   - Special characters

### Job Descriptions (20-30 examples)

**Categories**:
1. **Technical roles** (8-10 JDs)
   - Software Engineer
   - Data Scientist
   - DevOps Engineer
   - Frontend/Backend

2. **Business roles** (6-8 JDs)
   - Product Manager
   - Business Analyst
   - Project Manager
   - Operations

3. **Creative roles** (3-4 JDs)
   - UX Designer
   - Content Writer
   - Marketing Manager

4. **Specialized** (3-4 JDs)
   - Industry-specific (FinTech, Healthcare, etc.)
   - Unusual requirements
   - Hybrid roles

### Ground Truth Labels

For each resume-JD pair used in evaluation:
- **Expected match status**: matched, partially_matched, missing
- **Expected matched skills**: List of skills that should match
- **Expected gaps**: List of missing requirements
- **Expected score range**: Min/max acceptable scores

### Adversarial Test Cases

Cases designed to catch hallucinations:
1. **Skill fabrication**: Resume with Python → Check for Rust/Go fabrication
2. **Metric invention**: Resume without numbers → Check for added metrics
3. **Title inflation**: Junior Engineer → Check for "Senior" addition
4. **Education upgrade**: Bachelor's → Check for Master's fabrication
5. **Company invention**: Check for non-existent companies

## Usage

### Running Full Evaluation

```bash
cd apps/api/evaluation
python run_eval.py --benchmark ./benchmark --output ./results
```

### Running Hallucination Detection

```bash
python run_hallucination_eval.py --benchmark ./benchmark/adversarial --output ./results
```

### CI/CD Integration

```yaml
# .github/workflows/evaluation.yml
- name: Run Evaluation
  run: |
    cd apps/api/evaluation
    python run_eval.py --benchmark ./benchmark --fail-on-regression
    python run_hallucination_eval.py --benchmark ./benchmark/adversarial --fail-on-hallucination
```

## Metrics

### Pipeline Evaluation

- **Parsing Accuracy**: % of resumes parsed correctly
- **Match Accuracy**: Precision/Recall/F1 for requirement matching
- **Score Consistency**: Score variance across runs
- **Processing Time**: Latency per resume

### Hallucination Detection

- **Fabrication Rate**: % of runs with hallucinations (MUST be 0%)
- **Guardrail Effectiveness**: % of fabrications caught
- **False Positive Rate**: % of legitimate changes flagged

## Success Criteria

### Step 11 Definition of Done

- [x] Benchmark dataset: 10+ resumes, 20+ JDs ✅
- [x] Ground truth labels: Expected outputs documented ✅
- [x] Adversarial cases: 5+ hallucination test cases ✅
- [ ] Evaluation scripts: `run_eval.py` and `run_hallucination_eval.py` ⏸️
- [ ] CI integration: GitHub Actions workflow ⏸️
- [ ] Zero hallucinations: All adversarial tests pass ⏸️

## Next Steps

1. **Populate benchmark/** with diverse resume/JD examples
2. **Create ground_truth/** JSON files with expected outputs
3. **Write adversarial/** test cases for hallucination detection
4. **Implement run_eval.py** for pipeline evaluation
5. **Implement run_hallucination_eval.py** for zero-tolerance testing
6. **Set up CI/CD** to run on every PR

---

**Status**: Phase 4 in progress  
**Goal**: Enable quantitative quality measurement and hallucination detection
