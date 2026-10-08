# Resume Scoring & Matching (Step 3)

This module implements ATS compatibility scoring and job description matching for parsed resumes.

## Components

### 1. ATS Scorer (`ats_scorer.py`)

Scores a resume for ATS compatibility **without** a job description.

**Scoring Categories (100 points total):**
- **Contact Information (20 pts)**: Completeness of email, phone, name, location, LinkedIn
- **Section Presence (20 pts)**: Required sections (experience, education, skills) and optional sections
- **Content Density (20 pts)**: Number of blocks, bullet points, sufficient detail
- **Work Experience Quality (20 pts)**: Dates, bullet count, quantifiable achievements
- **Skills & Keywords (20 pts)**: Number and diversity of skills

**Usage:**
```python
from services.scoring.ats_scorer import ATSScorer

scorer = ATSScorer()
result = scorer.score(resume_data)

print(result.overall_score)  # 0-100
print(result.summary)        # Category breakdown
print(result.issues)         # List of detected issues
```

**Output:**
- `overall_score`: Float 0-100
- `summary`: Dict with category scores and issue counts
- `issues`: List of dicts with `issue_type`, `severity`, `title`, `description`, `metadata`

### 2. JD Parser (`jd_parser.py`)

Extracts structured requirements from job description text using LLM.

**Extracted Fields:**
- `requirements`: List of requirement objects with text, type (required/preferred/nice_to_have), category
- `key_skills`: Flat list of technologies/tools
- `years_experience`: Integer if explicitly stated
- `education_level`: String if explicitly stated
- `summary`: 1-2 sentence role summary

**Usage:**
```python
from services.scoring.jd_parser import parse_job_description

parsed = parse_job_description(raw_jd_text, settings)
print(f"Found {len(parsed.requirements)} requirements")
```

**Classification Logic:**
- **Required**: "must have", "required", "essential"
- **Preferred**: "preferred", "desired", "ideally", "strong plus"
- **Nice to have**: "nice to have", "bonus", "plus"
- Default to "required" when ambiguous

### 3. JD Matcher (`jd_matcher.py`)

Matches resume against job requirements using keyword-based matching.

**Matching Strategy:**
- Extracts keywords from resume (skills, titles, certifications, technologies)
- Compares each requirement against resume keyword sets
- Scores each match 0-100 based on keyword overlap
- Classifies as: `matched` (≥70), `partial` (30-69), `missing` (<30)

**Scoring Weights:**
- Required requirements: 1.0x
- Preferred requirements: 0.7x
- Nice-to-have requirements: 0.3x

**Usage:**
```python
from services.scoring.jd_matcher import JDMatcher

matcher = JDMatcher()
result = matcher.match(resume_data, jd_requirements)

print(result.overall_score)  # 0-100 weighted score
for match in result.matches:
    print(f"{match.requirement_text}: {match.match_status}")
```

**Output:**
- `overall_score`: Weighted 0-100 score
- `matches`: List of RequirementMatch objects
- `summary`: Dict with matched/partial/missing counts

### 4. Analysis Service (`../analysis_service.py`)

Orchestrates scoring/matching and persists results to database.

**Methods:**
- `run_ats_analysis(user_id, resume_version_id)`: Run ATS scoring, persist issues
- `run_jd_match_analysis(user_id, resume_version_id, job_description_id)`: Run JD matching, persist matches
- `create_job_description(user_id, title, raw_text, ...)`: Parse and store JD
- `get_analysis(user_id, analysis_id)`: Fetch analysis with matches/issues

**Database Tables Used:**
- `resume_analyses`: Analysis metadata, status, overall score
- `match_results`: Per-requirement match scores and evidence
- `issues`: Detected problems (missing sections, thin content, etc.)
- `job_descriptions`: Stored JD text
- `job_requirements`: Parsed requirement items

## API Endpoints

### POST /api/job-descriptions
Create and parse a job description.

**Request:**
```json
{
  "title": "Senior Backend Engineer",
  "company": "TechCorp",
  "raw_text": "We are seeking...",
  "source_url": "https://..."
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Senior Backend Engineer",
  "company": "TechCorp",
  "requirement_count": 12
}
```

### POST /api/analyses
Run an analysis (ATS or JD match).

**Request (ATS):**
```json
{
  "resume_version_id": "uuid",
  "analysis_type": "ats"
}
```

**Request (JD Match):**
```json
{
  "resume_version_id": "uuid",
  "job_description_id": "uuid",
  "analysis_type": "jd_match"
}
```

**Response:**
```json
{
  "id": "uuid",
  "analysis_type": "ats",
  "status": "completed",
  "overall_score": 78.5,
  "summary": {
    "category_scores": {
      "contact": 20.0,
      "sections": 18.0,
      "density": 15.0,
      "experience": 17.5,
      "skills": 8.0
    },
    "total_issues": 3,
    "critical_issues": 0,
    "high_issues": 1
  },
  "issue_count": 3,
  "match_count": 0
}
```

### GET /api/analyses/{analysis_id}
Get detailed analysis results with matches and issues.

**Response:**
```json
{
  "analysis": { ... },
  "matches": [
    {
      "id": "uuid",
      "requirement_text": "5+ years Python",
      "requirement_type": "required",
      "match_score": 85.0,
      "match_status": "matched",
      "evidence": {
        "matched_terms": ["python", "django", "flask"]
      }
    }
  ],
  "issues": [
    {
      "id": "uuid",
      "issue_type": "keyword",
      "severity": "medium",
      "title": "Limited Skills",
      "description": "Only 3 skills listed. Add more relevant skills.",
      "metadata": { "skill_count": 3 }
    }
  ]
}
```

## Running Tests

```bash
cd apps/api
pytest tests/test_scoring.py -v
```

## Async Execution (Optional)

For long-running analyses, use the RQ worker:

```bash
# Start worker
rq worker analysis --url redis://localhost:6379/0

# Enqueue job
from services.queue import get_redis_queue
queue = get_redis_queue(settings, "analysis")
job = queue.enqueue("workers.analysis_worker.run_ats_analysis", user_id, version_id)
```

## Future Improvements (Out of Scope for MVP)

- Semantic similarity using embeddings (requires embedding generation)
- ML-based requirement extraction
- Industry-specific scoring models
- Competitive analysis (compare against other candidates)
- Historical analysis tracking
