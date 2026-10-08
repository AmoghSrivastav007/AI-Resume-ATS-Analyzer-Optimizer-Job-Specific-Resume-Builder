# Phase 4: Evaluation Benchmark - Execution Plan

## Status
- **Current Phase**: 4 of 6
- **Started**: Session 3
- **Timeline**: 6 hours estimated
- **Dependencies**: Phases 1 & 2 complete (130 tests)

## Objectives
1. Create diverse resume corpus (10+ files)
2. Create comprehensive JD corpus (17+ files)
3. Generate ground truth labels (10 resume-JD pairs)
4. Build adversarial test cases (5 edge cases)
5. Enable hallucination detection and quality measurement

## Benchmark Requirements

### 1. Resume Corpus (10 files)
**Diversity dimensions:**
- **Experience levels**: Entry (0-2yr), Mid (3-7yr), Senior (8-15yr), Executive (15+yr)
- **Industries**: Tech, Finance, Healthcare, Marketing, Engineering
- **Formats**: Clean PDF, DOCX, scanned PDF, multi-column layout
- **Content quality**: Strong, average, weak ATS optimization
- **Edge cases**: Career gaps, job hopping, non-linear paths

**File naming**: `resume_<id>_<level>_<industry>.pdf`

### 2. Job Description Corpus (17 files)
**Categories:**
- **Tech roles (6)**: SWE, ML Engineer, DevOps, Frontend, Backend, Full-stack
- **Business roles (4)**: PM, Marketing, Sales, Operations
- **Executive roles (3)**: CTO, VP Engineering, Head of Product
- **Specialized (4)**: Data Scientist, Security Engineer, UX Designer, QA Engineer

**Characteristics per JD:**
- Required skills (5-10)
- Preferred skills (3-5)
- Experience range
- Education requirements
- Keywords for ATS optimization

**File naming**: `jd_<id>_<role_slug>.txt`

### 3. Ground Truth Labels (10 files)
**Each label includes:**
```json
{
  "resume_id": "resume_01_mid_tech",
  "jd_id": "jd_03_backend_engineer",
  "expected_match_score": 0.78,
  "score_range": [0.73, 0.83],
  "match_category": "strong_match",
  "key_matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "missing_critical_skills": ["Kubernetes"],
  "ats_score_expectations": {
    "keyword_density": [0.7, 0.9],
    "section_completeness": 1.0,
    "format_quality": [0.8, 1.0]
  },
  "hallucination_check": {
    "fabricated_skills": [],
    "exaggerated_experience": false,
    "invented_companies": false
  },
  "notes": "Backend engineer with strong Python skills, missing K8s"
}
```

**Label categories:**
- Strong match (3): Score 0.75-0.90
- Moderate match (4): Score 0.50-0.74
- Weak match (3): Score 0.20-0.49

**File naming**: `truth_<resume_id>_<jd_id>.json`

### 4. Adversarial Test Cases (5 files)
**Hallucination traps:**
1. **Skill inflation**: Resume with "familiar with" → Should NOT map to "expert in"
2. **Date manipulation**: 1-year role → Should NOT become 3 years
3. **Title embellishment**: "Junior Dev" → Should NOT become "Senior Engineer"
4. **Fake credentials**: Non-existent certifications → Must be detected
5. **Company fabrication**: Made-up companies → Must be flagged

**Each case includes:**
```json
{
  "case_id": "adv_01_skill_inflation",
  "resume_file": "resume_adv_01.pdf",
  "jd_file": "jd_01_senior_swe.txt",
  "trap_type": "skill_inflation",
  "planted_error": "Resume says 'familiar with Kubernetes', JD requires 'Kubernetes expert'",
  "expected_behavior": "Should NOT match at expert level",
  "failure_mode": "Hallucinated expertise upgrade",
  "detection_method": "Compare extracted skill level with original text",
  "zero_tolerance": true
}
```

**File naming**: `adversarial_<case_id>.json`

## Execution Steps

### Step 1: Generate Resumes (2 hours)
- [ ] Create 10 diverse resume text templates
- [ ] Convert to PDF format (use pdfkit or reportlab)
- [ ] Validate structural parsing works on all
- [ ] Store in `evaluation/benchmark/resumes/`

### Step 2: Generate Job Descriptions (1 hour)
- [ ] Write 17 realistic JD texts covering target roles
- [ ] Include required/preferred skills, experience, education
- [ ] Ensure ATS keyword variety
- [ ] Store in `evaluation/benchmark/job_descriptions/`

### Step 3: Generate Ground Truth (2 hours)
- [ ] Manually score 10 resume-JD pairs
- [ ] Define expected score ranges (allow ±5% variance)
- [ ] Document skill matches and gaps
- [ ] Include ATS score expectations
- [ ] Store in `evaluation/benchmark/ground_truth/`

### Step 4: Create Adversarial Cases (1 hour)
- [ ] Design 5 hallucination trap scenarios
- [ ] Create corresponding resume/JD pairs
- [ ] Document expected vs failure behaviors
- [ ] Define detection methods
- [ ] Store in `evaluation/benchmark/adversarial/`

### Step 5: Validation
- [ ] Run structural parser on all resumes (100% success)
- [ ] Run JD extraction on all descriptions (100% success)
- [ ] Verify ground truth labels are realistic
- [ ] Confirm adversarial traps are subtle enough to test LLM

## Success Criteria
- ✅ 10+ diverse resumes covering experience levels and industries
- ✅ 17+ job descriptions covering key roles
- ✅ 10 ground truth labels with score expectations
- ✅ 5 adversarial test cases with zero-tolerance checks
- ✅ All files parseable by existing pipeline
- ✅ Documentation explains benchmark usage

## Next Phase
**Phase 5**: Evaluation scripts (`run_eval.py`, `run_hallucination_eval.py`)

## Files to Create
```
evaluation/
├── benchmark/
│   ├── resumes/
│   │   ├── resume_01_entry_tech.pdf
│   │   ├── resume_02_mid_finance.pdf
│   │   ├── ... (8 more)
│   │   └── resume_adv_01_skill_inflation.pdf (for adversarial)
│   ├── job_descriptions/
│   │   ├── jd_01_senior_swe.txt
│   │   ├── jd_02_ml_engineer.txt
│   │   └── ... (15 more)
│   ├── ground_truth/
│   │   ├── truth_01_01.json
│   │   ├── truth_01_03.json
│   │   └── ... (8 more)
│   └── adversarial/
│       ├── adversarial_01_skill_inflation.json
│       ├── adversarial_02_date_manipulation.json
│       └── ... (3 more)
└── PHASE4_EVALUATION_BENCHMARK_PLAN.md (this file)
```

## Time Tracking
- Plan creation: 30 min
- Resume generation: 2 hours
- JD generation: 1 hour
- Ground truth: 2 hours
- Adversarial cases: 1 hour
- **Total**: 6.5 hours
