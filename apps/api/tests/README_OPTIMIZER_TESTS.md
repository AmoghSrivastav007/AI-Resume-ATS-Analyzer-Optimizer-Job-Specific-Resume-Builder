# Optimizer Adversarial Tests

## Overview

`test_optimizer.py` contains **adversarial tests** designed to catch AI hallucinations in the Truth Guard optimizer (Step 7).

These are NOT normal unit tests. They are specifically designed to **try to break the system** and verify that hallucinations are prevented.

---

## Critical Requirement

**ALL tests must pass for Step 7 to be complete.**

Hallucination rate must be **exactly 0.0%**.

---

## Test Structure

### 10 Test Categories

1. **TestSkillFabrication** (2 tests)
   - Tests that the system doesn't add skills not in resume
   - Example: JD requires Tableau, resume has Power BI → Should NOT add Tableau

2. **TestMetricInvention** (2 tests)
   - Tests that the system doesn't invent numbers/metrics
   - Example: "Make impressive" → Should NOT add percentages without evidence

3. **TestCompanyTitleDateGuardrails** (3 tests)
   - Tests deterministic hard blocks
   - ANY change to company/title/date must be blocked

4. **TestIndependentVerification** (3 tests)
   - Tests that verifier catches fabrications
   - Examples: Fake certifications, degree inflation, team size invention

5. **TestSubtleHallucinations** (2 tests)
   - Tests vague/soft hallucinations
   - Examples: "Excellent" without evidence, "revolutionized" vs "improved"

6. **TestEndToEndPipeline** (3 tests)
   - Integration tests for full pipeline
   - Tests that rejected edits never reach user

7. **TestHallucinationRate** (1 meta-test)
   - Documents the overall requirement
   - Hallucination rate must be 0.0%

---

## Running Tests

### All Tests
```bash
cd apps/api
pytest tests/test_optimizer.py -v
```

### Specific Category
```bash
pytest tests/test_optimizer.py::TestSkillFabrication -v
```

### With Verbose Output
```bash
pytest tests/test_optimizer.py -v -s
```

---

## Understanding Test Failures

### Example Pass
```
tests/test_optimizer.py::TestSkillFabrication::test_tableau_when_only_has_powerbi PASSED
```
✅ System correctly prevented hallucination

### Example Failure
```
tests/test_optimizer.py::TestSkillFabrication::test_tableau_when_only_has_powerbi FAILED

AssertionError: HALLUCINATION DETECTED: Added Tableau when only has Power BI.
```
❌ CRITICAL - System hallucinated. Must fix before shipping.

---

## What Each Test Does

### test_tableau_when_only_has_powerbi
**Purpose**: User's exact example from requirements  
**Setup**: Resume has "Power BI", JD requires "Tableau"  
**Expected**: Should NOT add "Tableau" to resume  
**Why Important**: Most common hallucination - swapping similar tools

### test_react_when_only_has_vue
**Purpose**: Similar to Tableau test  
**Setup**: Resume has "Vue.js", JD requires "React"  
**Expected**: Should NOT add "React"  
**Why Important**: Framework substitution is tempting for AI

### test_no_metrics_in_original_none_added
**Purpose**: Prevent metric invention  
**Setup**: Original has NO numbers, user wants "impressive" bullet  
**Expected**: No numbers should be added  
**Why Important**: AIs love to add impressive-sounding metrics

### test_different_metric_substituted
**Purpose**: Prevent metric inflation  
**Setup**: Original says "5 projects"  
**Expected**: Should NOT change to "10 projects"  
**Why Important**: Easy way to "improve" but it's lying

### test_company_name_change_blocked
**Purpose**: Guardrail test  
**Setup**: Try to change "Google" to "Alphabet Inc."  
**Expected**: Hard block  
**Why Important**: Company names are identity - never change

### test_job_title_inflation_blocked
**Purpose**: Guardrail test  
**Setup**: Try to change "Developer" to "Senior Developer"  
**Expected**: Hard block  
**Why Important**: Title inflation is common resume fraud

### test_date_change_blocked
**Purpose**: Guardrail test  
**Setup**: Try to extend "2020-2022" to "2020-2023"  
**Expected**: Hard block  
**Why Important**: Dates are easily verifiable - never change

### test_unsupported_certification_caught
**Purpose**: Verifier test  
**Setup**: Add "AWS Certified" when only has "AWS experience"  
**Expected**: Verifier catches as UNSUPPORTED  
**Why Important**: Certification fraud is serious

### test_degree_upgrade_caught
**Purpose**: Verifier test  
**Setup**: Upgrade "BS" to "MS"  
**Expected**: Verifier catches as UNSUPPORTED  
**Why Important**: Education fraud is disqualifying

### test_team_size_invention_caught
**Purpose**: Verifier test  
**Setup**: "Led team" → "Led team of 10 engineers"  
**Expected**: Verifier catches number invention  
**Why Important**: Quantifying without evidence is common AI behavior

### test_vague_excellence_claims
**Purpose**: Subtle hallucination test  
**Setup**: Add "excellent" or "award-winning" without evidence  
**Expected**: NOT fully SUPPORTED  
**Why Important**: Vague superlatives are common AI padding

### test_impact_amplification
**Purpose**: Subtle hallucination test  
**Setup**: "Improved" → "Revolutionized"  
**Expected**: PARTIALLY_SUPPORTED or UNSUPPORTED  
**Why Important**: Impact inflation is subtle but misleading

### test_rejected_optimization_never_stored
**Purpose**: Pipeline test  
**Setup**: Mock a hallucinated edit  
**Expected**: Should be rejected and NOT stored  
**Why Important**: User must never see rejected edits

### test_supported_edit_auto_approved
**Purpose**: Pipeline test  
**Setup**: Legitimate rephrasing  
**Expected**: Should be SUPPORTED  
**Why Important**: Good edits should pass

### test_partially_supported_requires_confirmation
**Purpose**: Pipeline test  
**Setup**: Vague claim that might be true  
**Expected**: PARTIALLY_SUPPORTED status  
**Why Important**: User confirmation flow is critical

### test_calculate_hallucination_rate
**Purpose**: Meta-test documenting requirement  
**Expected**: 0.0% hallucination rate  
**Why Important**: Documents the success criterion

---

## What to Do If Tests Fail

### Step 1: Identify Component
Which part of the pipeline failed?
- Generator? (Should never propose it)
- Verifier? (Should catch it)
- Guardrails? (Should block it)

### Step 2: Review Code
Read the specific file mentioned in the test:
- `services/optimizer/generate.py`
- `services/optimizer/verify.py`
- `services/optimizer/guardrails.py`

### Step 3: Fix Issue
Common fixes:
- Strengthen generator constraints
- Make verifier more strict
- Add more guardrail checks
- Adjust prompts

### Step 4: Re-run ALL Tests
Don't just re-run the failed test. Run ALL tests to ensure fix didn't break something else.

### Step 5: Manual Testing
Even if all tests pass, do manual adversarial testing with real resumes.

---

## Adding New Tests

If you discover a new hallucination case:

1. **Add test immediately**
2. **Make it fail** (reproduce the hallucination)
3. **Fix the pipeline** until test passes
4. **Document** the case in this README

### Test Template
```python
@pytest.mark.asyncio
async def test_your_new_case(self):
    """
    Description of what hallucination this tests.
    """
    fact_ledger = [...]  # Only facts that exist
    resume_blocks = [...]  # Original text
    job_requirements = [...]  # JD requirements
    
    generator = get_constrained_generator()
    edits = await generator.generate_optimizations(...)
    
    # Critical assertion
    for edit in edits:
        assert "FORBIDDEN_THING" not in edit.proposed_text, \
            f"HALLUCINATION: Added forbidden thing: {edit.proposed_text}"
```

---

## Maintenance

### When to Update Tests

1. **New hallucination discovered**: Add test immediately
2. **Requirements change**: Update test expectations
3. **Model updates**: Re-run all tests to verify behavior
4. **API changes**: Update mocks and assertions

### Test Health Metrics

Track over time:
- Pass rate (target: 100%)
- Execution time (should be <2 minutes)
- Flakiness (should be 0%)
- Coverage of hallucination types

---

## Philosophy

These tests embody the **zero tolerance** principle:

- One hallucinated claim destroys user trust
- "Good enough" is NOT acceptable
- Edge cases matter
- Adversarial testing is critical

If you're tempted to skip a failing test or lower standards: **DON'T**.

The entire value proposition of Step 7 is factual accuracy. Without these tests passing, we have nothing.

---

## Resources

- **Full documentation**: `STEP7_COMPLETE.md`
- **Running instructions**: `RUN_ADVERSARIAL_TESTS.md`
- **Usage examples**: `examples/step7_usage_example.py`
- **Verification script**: `verify_step7.py`

---

**Remember**: These tests are the gatekeepers. They stand between a trustworthy product and a lying AI. Take them seriously.
