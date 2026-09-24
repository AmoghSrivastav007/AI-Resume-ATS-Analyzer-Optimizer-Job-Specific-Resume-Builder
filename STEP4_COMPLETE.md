# Step 4 - ATS Scoring (General Resume Quality Score) - COMPLETE ✅

## What Was Built

Step 4 implements the **General Resume Quality Score** - a comprehensive, explainable resume quality score that does NOT require a job description. This score is based on 5 categories with full deduction tracking and LLM-powered content analysis.

### Core Components

**1. Content Quality Analyzer** (`services/scoring/content_quality_analyzer.py`)
- Uses Anthropic Sonnet model for deep content analysis
- Evaluates: weak action verbs, vague statements, unsupported claims, missing metrics, grammar/spelling
- Returns structured issues with full explainability (problem, severity, why it matters, current text, suggested correction, expected benefit, confidence level)
- Builds formatted resume text from parsed data for LLM analysis

**2. General Quality Scorer** (`services/scoring/general_quality_scorer.py`)
- Calculates overall score from 5 reweighted categories:
  - **Parsing Compatibility**: 36.4% (was 20% of 55% total)
  - **Structure**: 27.3% (was 15% of 55% total)
  - **Content Quality**: 18.2% (was 10% of 55% total)
  - **Formatting**: 9.1% (was 5% of 55% total)
  - **Metadata**: 9.1% (was 5% of 55% total)
- Merges deterministic issues (Step 3) + LLM issues (Step 4)
- Each category score = 100 - Σ(deductions), floored at 0
- Deduction points by severity:
  - Critical: -20 pts
  - High: -10 pts
  - Medium: -5 pts
  - Low: -2 pts

**3. Explainability Tree** (score_breakdown JSONB column)
```json
{
  "overall_score": 78.5,
  "categories": {
    "content_quality": {
      "raw_score": 85.0,
      "weighted_score": 15.47,
      "max_score": 18.2,
      "weight_percentage": 18.2,
      "deductions": [
        {
          "points": -10.0,
          "reason": "Weak action verb",
          "description": "Generic verbs don't stand out",
          "severity": "high",
          "recommendation": "Replace 'Worked on' with 'Architected'"
        }
      ]
    },
    ...
  }
}
```

**4. Enhanced Analysis Service** (`services/analysis_service.py`)
- Updated `run_ats_analysis()` to:
  1. Run deterministic ATS scoring (Step 3)
  2. Run LLM content quality analysis (Sonnet)
  3. Calculate General Resume Quality Score
  4. Persist all issues (deterministic + LLM)
  5. Store explainability tree in `score_breakdown`

**5. Category Explain API** (`routers/analyses.py`)
- `GET /api/analyses/{id}/explain/{category}` - Get deduction tree for specific category
- Returns raw score, weighted score, and full deduction list with recommendations

**6. Frontend Analysis Page** (`apps/web/src/app/resumes/[id]/analysis/page.tsx`)
- Overall score with letter grade (A-F)
- Issue counts by severity (critical, high, medium, low)
- Content Quality Assessment (strengths/weaknesses from LLM)
- Expandable category breakdown showing:
  - Raw score (0-100)
  - Weighted score (contribution to overall)
  - Weight percentage
  - All deductions with recommendations
- Full issue list grouped by severity with color coding

---

## Scoring Methodology

### Category Weighting

Original weights (with JD categories):
- Parsing Compatibility: 20%
- Structure: 15%
- Content Quality: 10%
- Formatting: 5%
- Metadata: 5%
- **[JD-dependent categories: 45%]**

Reweighted for General Score (no JD):
- Parsing Compatibility: 36.4% (20/55 * 100)
- Structure: 27.3% (15/55 * 100)
- Content Quality: 18.2% (10/55 * 100)
- Formatting: 9.1% (5/55 * 100)
- Metadata: 9.1% (5/55 * 100)

**Total: 100.0%**

### Issue Mapping to Categories

| Issue Type | Category |
|------------|----------|
| `content`, `grammar` | Content Quality |
| `keyword` | Structure |
| `formatting` | Formatting |
| `truth` | Content Quality |
| Missing fields | Structure |
| Other | Parsing Compatibility |

### Deduction Calculation

```python
for each issue:
    deduction = SEVERITY_DEDUCTIONS[issue.severity]
    # critical: 20, high: 10, medium: 5, low: 2

raw_score = max(0, 100 - sum(deductions))
weighted_score = raw_score * (category_weight / 100)
overall_score = sum(all_weighted_scores)
```

---

## Files Created/Modified

### New Files
1. `models/quality_issue.py` - QualityIssue and ContentQualityAnalysis Pydantic models
2. `prompts/content_quality.txt` - LLM prompt for content analysis
3. `services/scoring/content_quality_analyzer.py` - LLM content analyzer
4. `services/scoring/general_quality_scorer.py` - Score aggregation engine
5. `migrations/007_score_breakdown.sql` - Add score_breakdown column
6. `tests/test_general_quality_scorer.py` - Comprehensive unit tests (12 tests)
7. `apps/web/src/app/resumes/[id]/analysis/page.tsx` - Frontend analysis UI
8. `STEP4_COMPLETE.md` - This file

### Modified Files
1. `services/analysis_service.py` - Enhanced ATS analysis with LLM + scoring
2. `routers/analyses.py` - Added category explain endpoint

---

## API Endpoints

### POST /api/analyses
Run General Resume Quality Score analysis.

**Request:**
```json
{
  "resume_version_id": "uuid",
  "analysis_type": "ats"
}
```

**Response:**
```json
{
  "id": "analysis_uuid",
  "analysis_type": "ats",
  "status": "completed",
  "overall_score": 78.5,
  "summary": {
    "overall_score": 78.5,
    "score_type": "general_resume_quality",
    "category_scores": {
      "parsing_compatibility": {
        "raw_score": 90.0,
        "weighted_score": 32.76,
        "max_score": 36.4
      },
      ...
    },
    "total_issues": 8,
    "critical_issues": 0,
    "high_issues": 2,
    "content_quality": {
      "overall": "good",
      "summary": "Resume has strong structure but could improve action verbs",
      "strengths": ["Clear metrics", "Good formatting", "Complete sections"],
      "weaknesses": ["Some weak verbs", "Missing quantification in 2 bullets"]
    }
  },
  "issue_count": 8
}
```

### GET /api/analyses/{id}
Get full analysis with all issues.

**Response includes:**
- Analysis metadata
- All issues (deterministic + LLM)
- Score breakdown (explainability tree)

### GET /api/analyses/{id}/explain/{category}
Get detailed breakdown for a specific category.

**Categories:**
- `parsing_compatibility`
- `structure`
- `content_quality`
- `formatting`
- `metadata`

**Response:**
```json
{
  "analysis_id": "uuid",
  "category": "content_quality",
  "overall_score": 78.5,
  "category_score": {
    "raw_score": 85.0,
    "weighted_score": 15.47,
    "max_score": 18.2,
    "weight_percentage": 18.2,
    "deductions": [
      {
        "points": -10.0,
        "reason": "Weak action verb in experience bullet",
        "description": "Generic verbs like 'worked on' don't convey impact",
        "severity": "high",
        "issue_id": "llm_0",
        "recommendation": "Replace with 'Architected scalable backend system handling 10M+ daily requests'"
      },
      {
        "points": -5.0,
        "reason": "Missing metric in achievement",
        "description": "Impact claim without quantification",
        "severity": "medium",
        "issue_id": "llm_1",
        "recommendation": "Add specific numbers: 'Improved performance by 50%' instead of 'Improved performance'"
      }
    ]
  }
}
```

---

## LLM Content Analysis

### What It Detects

**1. Weak Action Verbs**
- Generic: "worked on", "was responsible for", "helped with"
- Passive voice: "was tasked with", "was involved in"
- Better alternatives: "led", "architected", "optimized", "achieved"

**2. Vague Statements**
- Unclear scope: "worked with large datasets" → how large?
- Missing context: "improved performance" → of what? by how much?
- Unspecified technologies: "used various tools" → which tools?

**3. Unsupported Claims**
- Subjective without evidence: "excellent communicator"
- Impact claims without metrics: "significantly improved"
- Titles without work description

**4. Missing Metrics**
- No quantification: "managed a team" → "managed team of 5"
- No impact measurement: "reduced bugs" → "reduced bugs by 40%"
- No scale indication: "processed data" → "processed 10M+ transactions"

**5. Grammar & Spelling**
- Tense inconsistency within same role
- Capitalization errors
- Punctuation issues
- Spelling errors

### Issue Structure

Every LLM issue includes:
- `issue_category`: 'content' or 'grammar'
- `problem`: Clear description
- `severity`: 'critical' | 'high' | 'medium' | 'low'
- `why_it_matters`: Business impact (ATS parsing, recruiter impression)
- `current_text`: Exact problematic text
- `suggested_correction`: Specific improved version
- `expected_benefit`: What improvement this brings
- `confidence_level`: 'high' | 'medium' | 'low'
- `location`: Where in resume (e.g., "Experience → Senior Engineer, bullet 2")

---

## Frontend Features

### Overall Score Display
- Large numeric score (0-100) with color coding:
  - 90-100: Green (A)
  - 80-89: Blue (B)
  - 70-79: Yellow (C)
  - 60-69: Orange (D)
  - <60: Red (F)
- Issue summary (total, critical, high)

### Content Quality Assessment Card
- Overall assessment (excellent/good/needs improvement/poor)
- LLM-generated summary
- Strengths list (bullet points)
- Weaknesses list (bullet points)

### Category Breakdown (Expandable)
Each category shows:
- Weight percentage
- Raw score (0-100)
- Weighted contribution to overall
- Expand/collapse button

When expanded:
- All deductions with point values
- Severity color-coding
- Issue reason and description
- Specific recommendation

### All Issues List
Grouped by severity (critical → high → medium → low):
- Color-coded badges
- Issue title and description
- Suggested correction (for LLM issues)
- Metadata (current text, expected benefit)

---

## Testing

### Run Tests
```bash
cd apps/api
pytest tests/test_general_quality_scorer.py -v
```

### Test Coverage
✅ Perfect resume (no issues) → 100.0 score  
✅ Critical issues significantly reduce score  
✅ Issues grouped into correct categories  
✅ Score breakdown has correct structure  
✅ Deduction points match severity levels  
✅ Category weights sum to 100  
✅ Weighted scores sum to overall  
✅ Raw scores floor at zero  
✅ Explainability includes recommendations  
✅ LLM issue metadata preserved  

**12 tests, all passing**

---

## Example Usage

### 1. Upload & Parse Resume (Steps 1-2)
```bash
curl -X POST http://localhost:8000/api/resumes \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@resume.pdf"

# Wait for parsing to complete (poll job status)
```

### 2. Run General Quality Score Analysis
```bash
curl -X POST http://localhost:8000/api/analyses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_version_id": "VERSION_ID",
    "analysis_type": "ats"
  }'

# Response:
# {
#   "id": "analysis_id",
#   "overall_score": 78.5,
#   "summary": {
#     "category_scores": {...},
#     "content_quality": {
#       "overall": "good",
#       "summary": "...",
#       "strengths": [...],
#       "weaknesses": [...]
#     }
#   },
#   "issue_count": 8
# }
```

### 3. Get Detailed Results
```bash
curl http://localhost:8000/api/analyses/ANALYSIS_ID \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Explain Specific Category
```bash
curl http://localhost:8000/api/analyses/ANALYSIS_ID/explain/content_quality \
  -H "Authorization: Bearer $TOKEN"

# Shows all deductions in content_quality category
```

### 5. View on Frontend
Navigate to: `http://localhost:3000/resumes/RESUME_ID/analysis`

---

## Environment Variables

**Required (new for Step 4):**
- `ANTHROPIC_SONNET_MODEL` - e.g., `claude-3-5-sonnet-20241022`

**Already required (from Steps 1-3):**
- `ANTHROPIC_API_KEY`
- `ANTHROPIC_HAIKU_MODEL`
- `SUPABASE_*` variables
- `REDIS_URL`

---

## Definition of Done ✅

Per Step 4 requirements:

✅ **Content Quality LLM Analysis**: Sonnet model evaluates bullets for weak verbs, vague statements, unsupported claims, missing metrics, grammar issues  
✅ **Structured Output**: Issues match schema with problem, severity, why_it_matters, current_text, suggested_correction, expected_benefit, confidence_level  
✅ **Score Aggregation**: 5 categories reweighted to 100%, each = 100 - Σ(deductions), floored at 0  
✅ **Explainability Tree**: Full breakdown in score_breakdown JSONB matching required format  
✅ **Category Explain API**: GET /api/analyses/:id/explain/:category returns deduction tree  
✅ **Frontend Analysis Page**: Shows overall score, category scores, expandable issue list with severity color-coding  
✅ **No JD Dependency**: General Resume Quality Score works without job description  
✅ **Functional UI**: Single-page view (not final polish) displaying all required data  

---

## What's NOT in This Step

Per Step 4 instructions, these are explicitly out of scope:

❌ **JD-related features**: No JD upload, no matching, no JD Match Score (coming in Step 6)  
❌ **Final polished UI**: Tabbed analysis interface from §35 comes later  
❌ **Truth Guard**: Fact verification against ledger (Step 4+ TBD)  
❌ **Optimization Generation**: LLM rewrite suggestions (Step 6+ TBD)  

---

## Architecture Notes

### Why Separate Deterministic + LLM Issues?

**Deterministic (Step 3):**
- Fast, rule-based checks
- Consistent, predictable results
- No API costs
- Good for structure, formatting, presence checks

**LLM (Step 4 - Sonnet):**
- Deep content understanding
- Context-aware suggestions
- Catches nuanced issues (weak verbs, vague claims)
- Provides actionable corrections
- More expensive, so used strategically

**Best of both:** Merge for comprehensive analysis with full explainability.

### Why Reweight Categories?

Original design had 8 categories totaling 100%:
- 5 general categories (55%)
- 3 JD-dependent categories (45%)

For **General Resume Quality Score** (no JD), we:
1. Remove JD-dependent categories
2. Reweight remaining 5 to sum to 100%
3. Preserve relative importance ratios

Later, **JD Match Score** (Step 6) will be a separate score using the JD-dependent categories.

### Explainability Tree Format

Matches requirement for "category → point deductions → linked issue → recommendation":

```
Category: Content Quality (18.2%)
├─ Raw Score: 85/100
├─ Weighted: 15.47/18.2
└─ Deductions:
   ├─ -10 pts: Weak action verb
   │  └─ Recommendation: Use "Architected" instead of "Worked on"
   └─ -5 pts: Missing metric
      └─ Recommendation: Add "50% improvement" quantification
```

---

## Next Steps

According to the Master Prompt architecture:

**Step 5**: Issue Detection (Advanced) - Advanced pattern detection, formatting issues, ATS-unfriendly patterns  
**Step 6**: JD Match Score + Optimization Generation - Match against JD, generate LLM-powered suggestions  
**Step 7**: Truth Guard Optimizer - Reconcile optimizations with fact ledger (complex reasoning, premium model)  
**Step 8**: Resume Editor UI - Block-based editor with inline issues  
**Step 9**: Applications Tracker  
**Step 10**: Export System  
**Step 11**: Polish & Testing  
**Step 12**: Deployment  

---

**Status**: Step 4 is complete! General Resume Quality Score is fully functional with explainable scoring, LLM content analysis, and frontend display. 🚀
