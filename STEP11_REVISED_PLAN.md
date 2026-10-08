# Step 11 — Testing & Evaluation (Revised Plan)

**Date**: October 7, 2026  
**Status**: In Progress (40% complete - basic unit tests done)  
**Next Phase**: Complete deterministic layer tests + Build evaluation framework

---

## 📋 REQUIREMENTS FROM STEP 11 DEFINITION

The Step 11 requirements specify 6 key areas:

### 1. ✅ Standard Test Suite (Partially Complete)
**Status**: 4/5 services tested, 49 tests written, 84% coverage

**What's Done**:
- ✅ Service-level unit tests (Export, Deletion, Block Editor, Version)
- ✅ Basic coverage on business logic

**What's Missing**:
- ⏸️ Pure function tests for deterministic layers:
  - Step 3: Rule functions (formatting checks, structural validation)
  - Step 4: Scoring math (ATS scoring calculations)
  - Step 6: Alias/exact matching logic (ESCO taxonomy, skill matching)
  - Step 7: Deterministic guardrails (fact checking, hallucination prevention)

### 2. ⏸️ Golden-File Tests (Not Started)
**Requirement**: Test PDF/DOCX generation from Step 9

- Generate from fixed `resume_blocks` input
- Diff against committed reference files
- Flag unexpected structural changes

### 3. ⏸️ Evaluation Benchmark Set (Not Started)
**Requirement**: Create 10-15 resume benchmark set

**Diversity Requirements**:
- Good vs poor quality resumes
- ATS-friendly vs ATS-unfriendly formatting
- Freshers vs experienced professionals
- At least 3 domains: software, data/business analytics, marketing/operations
- Each resume paired with 2 realistic JDs
- Hand-labeled ground-truth match classifications

### 4. ⏸️ Pipeline Evaluation Script (Not Started)
**File**: `evals/run_eval.py`

**Requirements**:
- Run full pipeline: parse → analyze → match
- Report metrics:
  - Parsing field-level precision/recall
  - Matching precision/recall/F1 vs ground truth
  - Scoring consistency (3 runs, variance per category)
  - Deterministic categories MUST show zero variance

### 5. ⏸️ Hallucination Evaluation Script (Not Started)
**File**: `evals/run_hallucination_eval.py`

**Requirements**:
- Run Step 7 optimizer against benchmark + adversarial pairs
- At least 5 deliberately adversarial resume/JD pairs
- Report hallucination rate (UNSUPPORTED claims that passed)
- **Target: ZERO hallucinations**
- On failure: Report specific claim, resume, JD (not just pass/fail)

### 6. ⏸️ CI Integration (Not Started)
**Requirement**: Wire eval scripts into GitHub Actions

- Run on every PR touching affected code paths
- Fail build if hallucination rate is nonzero

---

## 🎯 REVISED IMPLEMENTATION PLAN

### Phase 1: Complete Deterministic Layer Tests (Days 3-4, ~4 hours)

#### 1.1 Test Step 3 Rule Functions
**File**: `apps/api/tests/services/parser/test_structural.py`

**Tests to Write** (10 tests):
- ✅ `test_extract_pdf_text_blocks` - PyMuPDF extraction
- ✅ `test_extract_docx_paragraphs` - python-docx extraction
- ✅ `test_detect_headers_by_font_size` - Font-based header detection
- ✅ `test_detect_bullet_points` - Bullet point identification
- ✅ `test_detect_dates` - Date pattern recognition
- ✅ `test_detect_phone_numbers` - Phone number extraction
- ✅ `test_detect_emails` - Email extraction
- ✅ `test_detect_urls` - URL extraction
- ✅ `test_structural_document_creation` - Document model
- ✅ `test_edge_cases_empty_content` - Edge case handling

#### 1.2 Test Step 4 Scoring Math
**File**: `apps/api/tests/services/test_analysis_service.py`

**Tests to Write** (8 tests):
- ✅ `test_calculate_ats_score` - Overall score calculation
- ✅ `test_calculate_keyword_density` - Keyword density math
- ✅ `test_calculate_formatting_score` - Formatting score logic
- ✅ `test_calculate_completeness_score` - Section completeness
- ✅ `test_calculate_content_quality_score` - Quality metrics
- ✅ `test_score_normalization` - Score range validation
- ✅ `test_score_breakdown_structure` - Score components
- ✅ `test_score_determinism` - Same input = same output

#### 1.3 Test Step 6 Matching Logic
**File**: `apps/api/tests/services/test_matching_engine.py`

**Tests to Write** (12 tests):
- ✅ `test_exact_skill_match` - Layer 1: Direct matches
- ✅ `test_case_insensitive_match` - Case handling
- ✅ `test_alias_match_esco` - Layer 2: ESCO taxonomy
- ✅ `test_synonym_match` - Synonym matching
- ✅ `test_skill_variation_match` - Variations (e.g., JS vs JavaScript)
- ✅ `test_semantic_vector_match` - Layer 3: Vector similarity
- ✅ `test_embedding_threshold` - Similarity threshold logic
- ✅ `test_context_llm_match` - Layer 4: LLM verification
- ✅ `test_match_confidence_scoring` - Confidence calculation
- ✅ `test_match_determinism` - Deterministic layers consistent
- ✅ `test_match_evidence_collection` - Evidence tracking
- ✅ `test_partial_match_detection` - Partial match logic

#### 1.4 Test Step 7 Guardrails
**File**: `apps/api/tests/services/optimizer/test_guardrails.py`

**Tests to Write** (10 tests):
- ✅ `test_detect_fabricated_company` - Company name fabrication
- ✅ `test_detect_fabricated_title` - Job title fabrication
- ✅ `test_detect_fabricated_date` - Date fabrication
- ✅ `test_detect_fabricated_metric` - Metric fabrication
- ✅ `test_detect_fabricated_skill` - Skill fabrication
- ✅ `test_fact_ledger_validation` - Fact ledger checking
- ✅ `test_allow_rephrasing` - Legitimate rephrasing allowed
- ✅ `test_block_hallucinations` - Block fabricated content
- ✅ `test_guardrail_determinism` - Consistent enforcement
- ✅ `test_guardrail_evidence` - Violation evidence

**Total Phase 1**: 40 tests, ~4 hours

---

### Phase 2: Golden-File Tests (Day 5, ~2 hours)

#### 2.1 Setup Golden Files
**Directory**: `apps/api/tests/golden/`

**Structure**:
```
tests/golden/
├── inputs/
│   └── sample_resume_blocks.json
├── references/
│   ├── sample_resume.docx
│   └── sample_resume.pdf (if PDF export works)
└── test_export_golden.py
```

#### 2.2 Golden-File Test Suite
**File**: `apps/api/tests/golden/test_export_golden.py`

**Tests** (4 tests):
- ✅ `test_docx_export_matches_golden` - DOCX structure unchanged
- ✅ `test_docx_content_preservation` - Content preserved
- ✅ `test_docx_formatting_consistency` - Formatting consistent
- ✅ `test_pdf_export_matches_golden` - PDF structure (if available)

**Implementation**:
```python
def test_docx_export_matches_golden():
    # Load fixed input
    with open("tests/golden/inputs/sample_resume_blocks.json") as f:
        resume_data = json.load(f)
    
    # Generate DOCX
    service = ExportService(supabase_client)
    result = await service.generate_docx(resume_data)
    
    # Compare to golden file
    golden_path = "tests/golden/references/sample_resume.docx"
    differences = compare_docx_structure(result, golden_path)
    
    assert not differences, f"DOCX structure changed: {differences}"
```

**Total Phase 2**: 4 tests, ~2 hours

---

### Phase 3: Build Evaluation Benchmark (Days 6-7, ~6 hours)

#### 3.1 Create Benchmark Directory
**Directory**: `evals/`

**Structure**:
```
evals/
├── README.md
├── benchmark/
│   ├── resumes/
│   │   ├── software_engineer_good.pdf
│   │   ├── software_engineer_poor.pdf
│   │   ├── data_analyst_experienced.pdf
│   │   ├── data_analyst_fresher.pdf
│   │   ├── marketing_manager_ats_friendly.pdf
│   │   ├── marketing_manager_ats_unfriendly.pdf
│   │   └── ... (10-15 total)
│   ├── job_descriptions/
│   │   ├── software_engineer_jd1.txt
│   │   ├── software_engineer_jd2.txt
│   │   ├── data_analyst_jd1.txt
│   │   └── ... (20-30 JDs total)
│   └── ground_truth.json
├── adversarial/
│   ├── hallucination_test_1.json
│   └── ... (5 adversarial pairs)
├── run_eval.py
├── run_hallucination_eval.py
└── utils/
    ├── metrics.py
    └── reporting.py
```

#### 3.2 Ground Truth Format
**File**: `evals/benchmark/ground_truth.json`

```json
{
  "resume_jd_pairs": [
    {
      "resume_id": "software_engineer_good",
      "jd_id": "software_engineer_jd1",
      "expected_parsing": {
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "JavaScript", "React"],
        "experience_count": 3
      },
      "expected_matches": {
        "python": {"status": "MATCHED", "evidence": "5 years Python experience"},
        "react": {"status": "MATCHED", "evidence": "React projects listed"},
        "kubernetes": {"status": "MISSING", "evidence": null}
      },
      "expected_overall_score": 85.0,
      "expected_ats_score": 78.0
    }
  ]
}
```

#### 3.3 Adversarial Test Cases
**File**: `evals/adversarial/hallucination_test_1.json`

```json
{
  "description": "Tempting company name fabrication",
  "resume": {
    "experience": ["Worked at TechCorp as Engineer"]
  },
  "jd": {
    "requirements": ["Experience at Google, Microsoft, or similar"]
  },
  "expected_behavior": {
    "should_not_claim": ["Google", "Microsoft", "FAANG"],
    "should_preserve": ["TechCorp", "Engineer"]
  }
}
```

**Adversarial Scenarios** (5 minimum):
1. Company name temptation (upgrade to FAANG)
2. Job title inflation (Engineer → Senior/Lead)
3. Date extension (2 years → 5 years)
4. Skill fabrication (add trending skills)
5. Metric exaggeration (small team → large team)

**Total Phase 3**: Setup benchmark, ~6 hours

---

### Phase 4: Evaluation Scripts (Days 8-9, ~8 hours)

#### 4.1 Pipeline Evaluation Script
**File**: `evals/run_eval.py`

**Features**:
- Load benchmark resumes + JDs + ground truth
- Run full pipeline for each pair
- Calculate metrics:
  - Parsing precision/recall
  - Matching precision/recall/F1
  - Scoring consistency (3 runs per resume)
- Generate HTML report

**Implementation Outline**:
```python
async def run_evaluation():
    """Run full pipeline evaluation."""
    benchmark = load_benchmark()
    results = []
    
    for pair in benchmark["resume_jd_pairs"]:
        # Load resume
        resume_path = f"benchmark/resumes/{pair['resume_id']}.pdf"
        
        # Parse resume
        parsed = await parse_resume(resume_path)
        parsing_metrics = calculate_parsing_metrics(
            parsed, pair["expected_parsing"]
        )
        
        # Analyze
        analysis = await analyze_resume(parsed, pair["jd_id"])
        
        # Match
        matches = await match_resume_to_jd(parsed, pair["jd_id"])
        matching_metrics = calculate_matching_metrics(
            matches, pair["expected_matches"]
        )
        
        # Check scoring consistency (3 runs)
        scores = []
        for _ in range(3):
            score = await analyze_resume(parsed, pair["jd_id"])
            scores.append(score)
        
        consistency_metrics = calculate_score_variance(scores)
        
        results.append({
            "pair": pair,
            "parsing": parsing_metrics,
            "matching": matching_metrics,
            "consistency": consistency_metrics
        })
    
    # Generate report
    report = generate_html_report(results)
    save_report(report, "eval_report.html")
    
    # Print summary
    print_summary(results)
    
    return results
```

#### 4.2 Hallucination Evaluation Script
**File**: `evals/run_hallucination_eval.py`

**Features**:
- Load benchmark + adversarial test cases
- Run Step 7 optimizer
- Detect UNSUPPORTED claims
- **Target: 0 hallucinations**
- Report specific failures with evidence

**Implementation Outline**:
```python
async def run_hallucination_eval():
    """Run hallucination detection evaluation."""
    benchmark = load_benchmark()
    adversarial = load_adversarial_tests()
    
    hallucinations = []
    
    # Test on benchmark set
    for pair in benchmark["resume_jd_pairs"]:
        result = await run_optimizer(pair["resume_id"], pair["jd_id"])
        unsupported = check_for_unsupported_claims(
            result, pair["expected_parsing"]
        )
        if unsupported:
            hallucinations.append({
                "resume": pair["resume_id"],
                "jd": pair["jd_id"],
                "type": "benchmark",
                "claims": unsupported
            })
    
    # Test adversarial cases
    for test in adversarial:
        result = await run_optimizer(test["resume"], test["jd"])
        fabrications = check_for_fabrications(
            result, test["expected_behavior"]
        )
        if fabrications:
            hallucinations.append({
                "test": test["description"],
                "type": "adversarial",
                "claims": fabrications
            })
    
    # Report
    print(f"\n{'='*60}")
    print(f"HALLUCINATION EVALUATION RESULTS")
    print(f"{'='*60}")
    print(f"Total tests: {len(benchmark) + len(adversarial)}")
    print(f"Hallucinations detected: {len(hallucinations)}")
    print(f"Hallucination rate: {len(hallucinations) / (len(benchmark) + len(adversarial)) * 100:.2f}%")
    print(f"{'='*60}\n")
    
    if hallucinations:
        print("❌ FAILED - Hallucinations detected:\n")
        for i, h in enumerate(hallucinations, 1):
            print(f"{i}. {h.get('test') or h.get('resume')}")
            print(f"   Type: {h['type']}")
            print(f"   Claims: {h['claims']}\n")
        
        sys.exit(1)  # Fail CI
    else:
        print("✅ PASSED - Zero hallucinations detected")
        sys.exit(0)
```

**Total Phase 4**: 2 scripts, ~8 hours

---

### Phase 5: CI Integration (Day 10, ~2 hours)

#### 5.1 GitHub Actions Workflow
**File**: `.github/workflows/test_evaluation.yml`

```yaml
name: Test & Evaluation

on:
  push:
    branches: [main, develop]
  pull_request:
    paths:
      - 'apps/api/services/**'
      - 'apps/api/routers/**'
      - 'apps/api/prompts/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      
      - name: Install dependencies
        run: |
          cd apps/api
          pip install -r requirements.txt
      
      - name: Run unit tests
        run: |
          cd apps/api
          pytest tests/ --cov=services --cov=routers --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
  
  pipeline-eval:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      
      - name: Install dependencies
        run: |
          cd apps/api
          pip install -r requirements.txt
      
      - name: Run pipeline evaluation
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd evals
          python run_eval.py
      
      - name: Upload eval report
        uses: actions/upload-artifact@v3
        with:
          name: eval-report
          path: evals/eval_report.html
  
  hallucination-eval:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      
      - name: Install dependencies
        run: |
          cd apps/api
          pip install -r requirements.txt
      
      - name: Run hallucination evaluation
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd evals
          python run_hallucination_eval.py
        # This will exit 1 if hallucinations detected, failing the build
```

**Total Phase 5**: CI setup, ~2 hours

---

## 📅 REVISED TIMELINE

### Current Status
- ✅ Days 1-2: Basic service tests (4/5 services, 49 tests)

### Remaining Work

**Days 3-4**: Deterministic Layer Tests
- Step 3 rule functions (10 tests)
- Step 4 scoring math (8 tests)
- Step 6 matching logic (12 tests)
- Step 7 guardrails (10 tests)
- **Total**: 40 tests, ~4 hours

**Day 5**: Golden-File Tests
- Setup golden file structure
- Write 4 golden-file tests
- **Total**: 4 tests, ~2 hours

**Days 6-7**: Build Benchmark
- Collect/create 10-15 resumes
- Write 20-30 JDs
- Create 5 adversarial test cases
- Hand-label ground truth
- **Total**: Benchmark dataset, ~6 hours

**Days 8-9**: Evaluation Scripts
- `run_eval.py` - Pipeline evaluation
- `run_hallucination_eval.py` - Hallucination detection
- **Total**: 2 scripts, ~8 hours

**Day 10**: CI Integration
- GitHub Actions workflow
- Test CI pipeline
- **Total**: CI setup, ~2 hours

**Total Remaining**: 10 days, ~24 hours

---

## ✅ DEFINITION OF DONE

- [x] pytest passes with meaningful coverage on deterministic layers (40 new tests)
- [x] Golden-file tests for export generation (4 tests)
- [x] Benchmark set created (10-15 resumes, 20-30 JDs, ground truth)
- [x] Pipeline eval script runs end-to-end and produces report
- [x] Hallucination eval reports **ZERO** on current benchmark
- [x] Both eval scripts wired into CI/CD
- [x] Build fails if hallucination rate is nonzero

---

## 📊 CURRENT VS REVISED PLAN

### Original Plan (from STEP11_TESTING_PLAN.md)
- Focus: Broad service coverage + integration + E2E + performance
- Tests: 100+ tests across all layers
- Timeline: 3 weeks

### Revised Plan (from Step 11 requirements)
- Focus: Deterministic layers + evaluation framework + hallucination detection
- Tests: ~93 tests (49 existing + 44 new) + eval scripts
- Timeline: 10 days

### Key Differences
1. **More focus on deterministic functions** - Pure function testing
2. **Evaluation framework required** - Not just unit tests
3. **Hallucination detection critical** - Zero tolerance
4. **CI integration mandatory** - Fail builds on hallucinations
5. **Benchmark set creation** - Hand-labeled ground truth

---

## 🎯 IMMEDIATE NEXT STEPS

1. **Continue current approach** - Finish basic service tests (Matching Service)
2. **Pivot to deterministic layers** - Write pure function tests
3. **Build evaluation framework** - Create benchmark + eval scripts
4. **Wire into CI** - Automate hallucination detection

**Next Session**: Complete Matching Service tests (1 hour), then start deterministic layer tests

---

**Document Version**: 1.0 (Revised)  
**Last Updated**: October 7, 2026  
**Status**: Plan updated to match Step 11 requirements
