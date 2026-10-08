# Resume Scoring System - Complete Guide

This document explains the complete scoring system implemented in Steps 3-4.

---

## Two Types of Scores

### 1. General Resume Quality Score (Step 4) ✅
**No job description required**

Evaluates overall resume quality across 5 categories:
- Parsing Compatibility (36.4%)
- Structure (27.3%)
- Content Quality (18.2%)
- Formatting (9.1%)
- Metadata (9.1%)

**Uses:**
- Deterministic checks (Step 3)
- LLM content analysis (Sonnet model)
- Explainable scoring with recommendations

**Endpoint:** `POST /api/analyses` with `"analysis_type": "ats"`

### 2. JD Match Score (Step 6) ⏳
**Requires job description**

Evaluates match against specific job requirements.
- Coming in Step 6
- Will use separate category weights
- Will include keyword matching + semantic analysis

---

## General Resume Quality Score (Detailed)

### Category Weights

Original design included 8 categories (55% general + 45% JD-dependent):

| Category | Original | Reweighted (no JD) |
|----------|----------|-------------------|
| Parsing Compatibility | 20% | 36.4% |
| Structure | 15% | 27.3% |
| Content Quality | 10% | 18.2% |
| Formatting | 5% | 9.1% |
| Metadata | 5% | 9.1% |
| **Subtotal** | **55%** | **100%** |
| *(JD categories)* | *(45%)* | *(removed)* |

**Total: 100%**

### Scoring Formula

For each category:
```
deductions = Σ (issue_severity_points)
  where:
    critical = 20 points
    high = 10 points
    medium = 5 points
    low = 2 points

raw_score = max(0, 100 - deductions)
weighted_score = raw_score × (category_weight / 100)
```

Overall score:
```
overall_score = Σ (all_weighted_scores)
```

### Issue Sources

**Deterministic Issues (Step 3 - ats_scorer.py)**
- Contact information completeness
- Section presence (experience, education, skills)
- Content density (block count, bullet count)
- Work experience quality (dates, bullets, metrics)
- Skills count

**LLM Issues (Step 4 - content_quality_analyzer.py)**
- Weak action verbs ("worked on", "helped with")
- Vague statements (missing context/scope)
- Unsupported claims (no evidence)
- Missing metrics (no quantification)
- Grammar/spelling (tense, capitalization, punctuation)

### Issue-to-Category Mapping

| Issue Type | Category |
|------------|----------|
| `content` | Content Quality |
| `grammar` | Content Quality |
| `keyword` | Structure |
| `formatting` | Formatting |
| `truth` | Content Quality |
| Missing fields | Structure |
| Other | Parsing Compatibility |

---

## Explainability Tree

Every analysis includes a full explainability tree in `score_breakdown`:

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
          "description": "Generic verbs don't stand out to recruiters",
          "severity": "high",
          "issue_id": "llm_0",
          "recommendation": "Replace 'Worked on backend systems' with 'Architected scalable backend handling 10M+ daily requests'"
        },
        {
          "points": -5.0,
          "reason": "Missing metric",
          "description": "Impact claim lacks quantification",
          "severity": "medium",
          "issue_id": "det_3",
          "recommendation": "Add specific numbers: 'Improved performance by 50%' instead of 'Improved performance'"
        }
      ]
    },
    "structure": { ... },
    "parsing_compatibility": { ... },
    "formatting": { ... },
    "metadata": { ... }
  }
}
```

### Accessing Explainability

1. **Full breakdown**: Included in analysis response
2. **Per-category**: `GET /api/analyses/{id}/explain/{category}`
3. **Frontend**: Expandable category cards show all deductions

---

## LLM Content Quality Analysis

### What It Analyzes

1. **Action Verbs**
   - Detects: "worked on", "was responsible for", "helped with"
   - Suggests: "architected", "led", "optimized", "achieved"

2. **Vagueness**
   - Flags: "large datasets", "improved performance", "various tools"
   - Needs: Specific sizes, percentages, tool names

3. **Unsupported Claims**
   - Flags: "excellent communicator" without evidence
   - Needs: Examples, metrics, outcomes

4. **Missing Metrics**
   - Flags: "managed a team", "reduced bugs"
   - Needs: Team size, percentage reduction

5. **Grammar**
   - Tense consistency
   - Capitalization
   - Punctuation

### Issue Structure

Every LLM issue includes:
```python
{
  "issue_category": "content" | "grammar",
  "problem": str,  # What's wrong
  "severity": "critical" | "high" | "medium" | "low",
  "why_it_matters": str,  # Business impact
  "current_text": str,  # Exact problematic text
  "suggested_correction": str,  # Specific fix
  "expected_benefit": str,  # What improves
  "confidence_level": "high" | "medium" | "low",
  "location": str,  # Where in resume
}
```

### Prompt Design

Located in `prompts/content_quality.txt`:
- Focuses on ATS and recruiter impact
- Provides specific correction examples
- Requires confidence level for each issue
- Returns structured output via Anthropic tool use

---

## Score Interpretation

### Letter Grades

| Score | Grade | Interpretation |
|-------|-------|----------------|
| 90-100 | A | Excellent - ATS-optimized, strong content |
| 80-89 | B | Good - Minor improvements needed |
| 70-79 | C | Fair - Several issues to address |
| 60-69 | D | Needs work - Multiple critical issues |
| 0-59 | F | Poor - Major overhaul required |

### Severity Impact

| Severity | Points | Example |
|----------|--------|---------|
| Critical | -20 | Missing work experience section |
| High | -10 | Weak action verbs in multiple bullets |
| Medium | -5 | Missing metric in one bullet |
| Low | -2 | Minor punctuation inconsistency |

### Category Interpretation

**Parsing Compatibility (36.4%)**
- Can ATS systems extract information?
- Are standard formats used?
- Impact: If low, ATS may reject automatically

**Structure (27.3%)**
- Are required sections present?
- Is information organized logically?
- Impact: Affects recruiter navigation

**Content Quality (18.2%)**
- Are accomplishments clear and impactful?
- Are verbs strong?
- Are metrics present?
- Impact: Affects human reviewer impression

**Formatting (9.1%)**
- Is formatting consistent?
- Are fonts/sizes appropriate?
- Impact: Professional appearance

**Metadata (9.1%)**
- Is contact info complete?
- Are dates formatted properly?
- Impact: Recruiter can reach you

---

## Usage Examples

### Basic Analysis

```python
# Run analysis
response = requests.post(
    "http://localhost:8000/api/analyses",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "resume_version_id": "uuid",
        "analysis_type": "ats"
    }
)

analysis = response.json()
print(f"Score: {analysis['overall_score']}/100")
```

### Explain Category

```python
# Get content quality breakdown
response = requests.get(
    f"http://localhost:8000/api/analyses/{analysis_id}/explain/content_quality",
    headers={"Authorization": f"Bearer {token}"}
)

breakdown = response.json()
for deduction in breakdown['category_score']['deductions']:
    print(f"Issue: {deduction['reason']}")
    print(f"Fix: {deduction['recommendation']}")
```

### View on Frontend

Navigate to: `http://localhost:3000/resumes/{resume_id}/analysis`

Features:
- Overall score with grade
- Content quality assessment (strengths/weaknesses)
- Expandable category cards
- All issues grouped by severity
- Recommendations for each issue

---

## Performance

### Timing

| Component | Time | Notes |
|-----------|------|-------|
| Deterministic checks | ~200ms | Rule-based, fast |
| LLM content analysis | ~5-10s | Anthropic API call (Sonnet) |
| Score calculation | ~50ms | Pure computation |
| **Total** | ~6-11s | Mostly LLM latency |

### Costs

| Component | Cost | Notes |
|-----------|------|-------|
| Deterministic | $0 | Local computation |
| LLM (Sonnet) | ~$0.03 | Per analysis (~3K tokens in, ~1K out) |
| Database writes | $0 | Negligible |
| **Total** | ~$0.03 | Per analysis |

### Optimization Tips

1. **Cache resume text**: Don't rebuild on every analysis
2. **Batch analyses**: If analyzing multiple resumes
3. **Use Haiku for simpler checks**: Switch to Sonnet only for content quality
4. **Rate limiting**: Queue analyses to manage API costs

---

## Testing

### Unit Tests

```bash
# Test deterministic scorer (Step 3)
pytest tests/test_scoring.py -v

# Test general quality scorer (Step 4)
pytest tests/test_general_quality_scorer.py -v
```

### Integration Test

```bash
# Full workflow
python examples/step4_usage_example.py
```

### Manual Testing Checklist

- [ ] Upload resume
- [ ] Parse completes successfully
- [ ] Run ATS analysis
- [ ] Score is 0-100
- [ ] All 5 categories present
- [ ] Weights sum to 100
- [ ] Weighted scores sum to overall
- [ ] Explainability tree is complete
- [ ] Category explain endpoint works
- [ ] Frontend displays correctly
- [ ] Issues have recommendations

---

## Troubleshooting

### "ANTHROPIC_SONNET_MODEL is missing"
- Add to `.env`: `ANTHROPIC_SONNET_MODEL=claude-3-5-sonnet-20241022`

### Score doesn't match category sum
- Check for floating point rounding
- Verify all category weights sum to 100
- Ensure no negative scores (should floor at 0)

### No LLM issues detected
- Check resume has sufficient content
- Verify Anthropic API key is valid
- Check API response for structured output
- Review prompt in `prompts/content_quality.txt`

### Frontend shows 0 score
- Verify analysis completed (status='completed')
- Check `score_breakdown` exists in database
- Ensure `overall_score` is not null

---

## Future Enhancements

### Step 5: Advanced Issue Detection
- Pattern-based detection (e.g., wall of text)
- ATS-unfriendly elements (tables, columns)
- Font/formatting analysis

### Step 6: JD Match Score
- Separate score for JD matching
- Keyword coverage percentage
- Semantic similarity (using embeddings)
- Gap analysis

### Step 7: Truth Guard Optimizer
- Verify claims against fact ledger
- Suggest optimizations that stay factual
- Confidence scoring

### Beyond MVP
- Semantic matching with pgvector
- ML-based scoring models
- Industry-specific scoring
- Competitive benchmarking
- Time-series tracking

---

## References

- **Architecture**: `docs/architecture.md`
- **Step 3 Docs**: `apps/api/services/scoring/README.md`
- **Step 4 Complete**: `STEP4_COMPLETE.md`
- **API Docs**: http://localhost:8000/docs
- **Example Usage**: `examples/step4_usage_example.py`

---

**Last Updated**: Step 4 completion  
**Version**: 1.0.0  
**Status**: Production-ready ✅
