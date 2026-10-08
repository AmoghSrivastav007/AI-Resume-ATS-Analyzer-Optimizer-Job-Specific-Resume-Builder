# Phase 4: Evaluation Benchmark - Detailed Plan

**Date**: October 7, 2026  
**Status**: Starting Phase 4  
**Goal**: Build comprehensive evaluation benchmark for quality measurement and hallucination detection

---

## 🎯 OVERVIEW

**Phase 4 Goal**: Create evaluation benchmark with diverse resumes, JDs, ground truth labels, and adversarial test cases

**Why Critical**: 
- Enables quantitative quality measurement
- Detects hallucinations (zero tolerance)
- Prevents regressions
- Required for Step 11 completion

**Timeline**: ~6 hours (estimated)

---

## 📋 BENCHMARK REQUIREMENTS

### Dataset Composition

**Resumes**: 10-15 diverse examples
**Job Descriptions**: 20-30 examples
**Ground Truth Labels**: Expected outputs for key test cases
**Adversarial Cases**: 5+ hallucination test scenarios

---

## 🔧 IMPLEMENTATION PLAN

### Step 1: Create Sample Resumes (2 hours)

**Option A: Use Existing Templates** (Faster)
- Find open-source resume templates
- Populate with realistic but fictional data
- Convert to PDF and DOCX formats

**Option B: Generate Synthetic Data** (More control)
- Use GPT/Claude to generate resume content
- Create diverse backgrounds
- Export to PDF/DOCX

**Categories to Cover**:
1. **Entry-level** (2 resumes)
   - Recent grad: BS Computer Science, 1 internship
   - Career changer: Bootcamp grad, 1 year experience

2. **Mid-level** (3 resumes)
   - Software Engineer: 5 years, 3 companies
   - Data Analyst: 4 years, cross-functional
   - Full-stack Developer: 6 years, tech lead

3. **Senior-level** (2 resumes)
   - Engineering Manager: 10 years, 5+ direct reports
   - Principal Engineer: 12 years, architecture focus

4. **Specialized** (2 resumes)
   - ML Engineer: Python, PyTorch, research background
   - DevOps Engineer: AWS, Kubernetes, automation

5. **Edge cases** (1 resume)
   - Minimal: Name, email, 1 job (sparse content)
   - Unicode: International names, special characters

**Deliverable**: `evaluation/benchmark/resumes/resume_*.pdf` (10 files)

---

### Step 2: Create Job Descriptions (1.5 hours)

**Approach**: Use real job postings (anonymized) or generate synthetic

**Categories**:
1. **Software Engineering** (5 JDs)
   - Junior SE (Python, React)
   - Senior SE (Java, Microservices)
   - Full-stack (MERN stack)
   - Backend (Go, Kubernetes)
   - Frontend (React, TypeScript)

2. **Data Science** (3 JDs)
   - Data Scientist (ML, Python, SQL)
   - ML Engineer (PyTorch, MLOps)
   - Data Analyst (SQL, Tableau)

3. **DevOps/Infrastructure** (3 JDs)
   - DevOps Engineer (AWS, Terraform)
   - SRE (Kubernetes, Monitoring)
   - Cloud Architect (Multi-cloud)

4. **Product/Business** (3 JDs)
   - Product Manager (Technical)
   - Business Analyst (Agile)
   - Project Manager (Software)

5. **Other** (3 JDs)
   - UX Designer
   - Technical Writer
   - Engineering Manager

**Deliverable**: `evaluation/benchmark/job_descriptions/jd_*.txt` (17 files)

---

### Step 3: Create Ground Truth Labels (1.5 hours)

**For Each Key Test Case**, document:

**Structure** (`ground_truth/test_case_*.json`):
```json
{
  "id": "test_case_001",
  "resume": "resume_mid_software_engineer.pdf",
  "job_description": "jd_senior_software_engineer.txt",
  "expected_outcomes": {
    "parsing": {
      "name_extracted": true,
      "email_extracted": true,
      "work_experience_count": 3,
      "skills_extracted": ["Python", "JavaScript", "AWS", "Docker"]
    },
    "matching": {
      "matched_requirements": [
        "5+ years software development",
        "Python proficiency",
        "Cloud experience (AWS)"
      ],
      "missing_requirements": [
        "Java experience",
        "Kubernetes at scale"
      ],
      "match_status": "partially_matched"
    },
    "scoring": {
      "ats_score_range": [65, 85],
      "match_score_range": [60, 80]
    }
  }
}
```

**Test Cases to Label** (10 cases):
1. Strong match (mid-level → mid-level JD)
2. Partial match (missing 2-3 requirements)
3. Weak match (missing many requirements)
4. Overqualified (senior → junior JD)
5. Underqualified (junior → senior JD)
6. Skill mismatch (Python dev → Java JD)
7. Domain mismatch (Backend → Frontend JD)
8. Perfect match (all requirements met)
9. Edge case (minimal resume → JD)
10. Special chars (unicode resume → JD)

**Deliverable**: `evaluation/benchmark/ground_truth/*.json` (10 files)

---

### Step 4: Create Adversarial Test Cases (1 hour)

**Purpose**: Catch hallucinations (fabricated information)

**Test Cases** (`adversarial/adversarial_*.json`):

```json
{
  "id": "adversarial_001_skill_fabrication",
  "description": "Resume has only Python. Check if optimizer adds Rust/Go.",
  "original_resume": {
    "skills": ["Python", "SQL", "Git"]
  },
  "job_requirements": [
    "Rust programming",
    "Go experience"
  ],
  "expected_behavior": {
    "should_not_add": ["Rust", "Go"],
    "should_recommend": true,
    "should_fail_if": "Rust or Go appear in optimized resume"
  }
}
```

**Adversarial Cases** (5 minimum):

1. **Skill Fabrication**
   - Original: Python only
   - JD requires: Rust, Go
   - Check: Optimizer must NOT add Rust/Go

2. **Metric Invention**
   - Original: "Built microservices" (no numbers)
   - JD wants: "Experience with high-scale systems"
   - Check: No invented metrics (e.g., "1M requests/sec")

3. **Title Inflation**
   - Original: "Software Engineer"
   - JD wants: "Senior Software Engineer"
   - Check: Title must NOT change to "Senior"

4. **Education Upgrade**
   - Original: "BS Computer Science"
   - JD prefers: "MS Computer Science"
   - Check: Degree must NOT upgrade to MS

5. **Company Invention**
   - Original: Worked at "Tech Startup Inc"
   - JD wants: "FAANG experience"
   - Check: No fabricated company names (Google, Meta, etc.)

**Deliverable**: `evaluation/benchmark/adversarial/*.json` (5 files)

---

## 📊 EXPECTED OUTCOMES

### Phase 4 Deliverables

**Files Created** (~35 files):
- 10 resume files (PDF)
- 17 job description files (TXT)
- 10 ground truth label files (JSON)
- 5 adversarial test case files (JSON)
- 3 documentation files (README, etc.)

**Total**: ~45 files

### Quality Metrics

- **Diversity**: Covers entry/mid/senior levels
- **Realism**: Realistic content and scenarios
- **Coverage**: Technical, business, creative roles
- **Adversarial**: Tests guardrail effectiveness

---

## 🚀 EXECUTION STRATEGY

### Approach: Mix of Real & Synthetic

**For Speed** (Recommended):
1. Use AI (GPT/Claude) to generate resume content
2. Use real (anonymized) job postings from job boards
3. Create ground truth labels manually
4. Design adversarial cases based on known failure modes

### Resume Generation Prompt

```
Generate a realistic software engineer resume for:
- Name: [Fictional name]
- Experience level: [Entry/Mid/Senior]
- Years of experience: [X years]
- Skills: [Specific tech stack]
- Format: Professional, ATS-friendly

Include:
- Contact info (fictional email/phone)
- 2-3 work experiences with bullet points
- Education section
- Skills section
- No fabricated companies (use "Tech Corp", "Startup Inc", etc.)
```

### Ground Truth Creation Strategy

**For Each Test Case**:
1. Pick a resume + JD pair
2. Manually review what should match
3. Document expected requirements met/missing
4. Set acceptable score ranges
5. Save as JSON

---

## ✅ SUCCESS CRITERIA

### Phase 4 Complete When:

- [x] Directory structure created ✅
- [ ] 10+ resume files in benchmark/resumes/ ⏸️
- [ ] 17+ JD files in benchmark/job_descriptions/ ⏸️
- [ ] 10 ground truth labels in benchmark/ground_truth/ ⏸️
- [ ] 5 adversarial cases in benchmark/adversarial/ ⏸️
- [ ] README.md documents the benchmark ✅
- [ ] All files committed to git ⏸️

### Quality Checks

- Resumes are diverse (entry/mid/senior/edge cases)
- JDs cover multiple roles/levels
- Ground truth is accurate and testable
- Adversarial cases target known failure modes
- Documentation is clear

---

## 📝 NEXT STEPS AFTER PHASE 4

**Phase 5: Evaluation Scripts** (8 hours)

1. **Write `run_eval.py`**:
   - Load benchmark dataset
   - Run pipeline on each test case
   - Compare outputs to ground truth
   - Calculate metrics (precision, recall, F1)
   - Generate report

2. **Write `run_hallucination_eval.py`**:
   - Load adversarial cases
   - Run optimizer on each case
   - Check for fabrications
   - FAIL if any hallucination detected
   - Report violations

**Phase 6: CI Integration** (2 hours)

1. Create `.github/workflows/evaluation.yml`
2. Run evaluations on every PR
3. Fail builds on hallucinations
4. Post results as PR comments

---

## 🎯 TIME BREAKDOWN

| Task | Time | Deliverable |
|------|------|-------------|
| Create resumes | 2h | 10 PDF files |
| Create JDs | 1.5h | 17 TXT files |
| Ground truth labels | 1.5h | 10 JSON files |
| Adversarial cases | 1h | 5 JSON files |
| **Total** | **6h** | **42 files** |

---

## 💡 TIPS FOR EFFICIENCY

1. **Use AI for generation**: GPT/Claude can create realistic resumes/JDs quickly
2. **Real anonymized data**: Job boards have thousands of JDs to adapt
3. **Template approach**: Create 1 ground truth template, replicate
4. **Focus on quality**: 10 good test cases > 50 mediocre ones
5. **Document as you go**: Write descriptions while creating files

---

## 🚀 READY TO START

**Next Action**: Generate first batch of resumes using AI

**Command**: Start with entry-level resume generation

**Let's build the evaluation benchmark!** 📊
