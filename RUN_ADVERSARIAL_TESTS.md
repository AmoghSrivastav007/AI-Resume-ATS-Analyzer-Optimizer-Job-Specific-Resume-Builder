# How to Run Step 7 Adversarial Tests

## ⚠️ CRITICAL: This Must Be Done Before Step 7 is Complete

**Definition of Done**: ALL adversarial tests pass with 0.0% hallucination rate.

If ANY test fails, Step 7 is NOT complete.

---

## Prerequisites

1. **Environment Variables Set**:
   ```bash
   # Required for tests to run
   ANTHROPIC_API_KEY=your_key_here
   ANTHROPIC_SONNET_MODEL=claude-3-5-sonnet-20241022
   ANTHROPIC_HAIKU_MODEL=claude-3-haiku-20240307
   ```

2. **Dependencies Installed**:
   ```bash
   cd apps/api
   pip install -r requirements.txt
   ```

3. **Database Running** (for guardrail skill alias checks):
   ```bash
   # Start Supabase if needed
   docker-compose up -d
   ```

---

## Running the Tests

### Step 1: Quick Verification

First, verify that all files are in place:

```bash
python verify_step7.py
```

**Expected Output**:
```
✅ All 35/35 checks passed
```

If this fails, fix missing files before running adversarial tests.

---

### Step 2: Run All Adversarial Tests

```bash
cd apps/api
pytest tests/test_optimizer.py -v
```

**Expected Output**:
```
tests/test_optimizer.py::TestSkillFabrication::test_tableau_when_only_has_powerbi PASSED
tests/test_optimizer.py::TestSkillFabrication::test_react_when_only_has_vue PASSED
tests/test_optimizer.py::TestMetricInvention::test_no_metrics_in_original_none_added PASSED
tests/test_optimizer.py::TestMetricInvention::test_different_metric_substituted PASSED
tests/test_optimizer.py::TestCompanyTitleDateGuardrails::test_company_name_change_blocked PASSED
tests/test_optimizer.py::TestCompanyTitleDateGuardrails::test_job_title_inflation_blocked PASSED
tests/test_optimizer.py::TestCompanyTitleDateGuardrails::test_date_change_blocked PASSED
tests/test_optimizer.py::TestIndependentVerification::test_unsupported_certification_caught PASSED
tests/test_optimizer.py::TestIndependentVerification::test_degree_upgrade_caught PASSED
tests/test_optimizer.py::TestIndependentVerification::test_team_size_invention_caught PASSED
tests/test_optimizer.py::TestSubtleHallucinations::test_vague_excellence_claims PASSED
tests/test_optimizer.py::TestSubtleHallucinations::test_impact_amplification PASSED
tests/test_optimizer.py::TestEndToEndPipeline::test_rejected_optimization_never_stored PASSED
tests/test_optimizer.py::TestEndToEndPipeline::test_supported_edit_auto_approved PASSED
tests/test_optimizer.py::TestEndToEndPipeline::test_partially_supported_requires_confirmation PASSED
tests/test_optimizer.py::TestHallucinationRate::test_calculate_hallucination_rate PASSED

==================== 16 passed in 45.23s ====================
```

**✅ SUCCESS CRITERIA**: ALL tests pass, 0 failures

**❌ FAILURE CRITERIA**: ANY test fails → Fix pipeline, re-run

---

### Step 3: Run Specific Test Categories

If you want to focus on specific categories:

#### Skill Fabrication Tests
```bash
pytest tests/test_optimizer.py::TestSkillFabrication -v
```

Tests:
- Tableau when only has Power BI (user's exact example)
- React when only has Vue.js

#### Metric Invention Tests
```bash
pytest tests/test_optimizer.py::TestMetricInvention -v
```

Tests:
- No metrics in original, none should be added
- Different metric substitution blocked

#### Guardrail Tests
```bash
pytest tests/test_optimizer.py::TestCompanyTitleDateGuardrails -v
```

Tests:
- Company name change blocked
- Job title inflation blocked
- Date change blocked

#### Verification Tests
```bash
pytest tests/test_optimizer.py::TestIndependentVerification -v
```

Tests:
- Fake certification caught
- Degree upgrade caught
- Team size invention caught

#### Subtle Hallucination Tests
```bash
pytest tests/test_optimizer.py::TestSubtleHallucinations -v
```

Tests:
- Vague excellence claims
- Impact amplification without evidence

---

### Step 4: Verbose Output (Debugging)

If you need to see print statements and detailed output:

```bash
pytest tests/test_optimizer.py -v -s
```

This shows:
- All assertions being checked
- Hallucination detection messages
- Guardrail violations
- Verification results

---

## Understanding Test Results

### ✅ Test Passed

```
tests/test_optimizer.py::TestSkillFabrication::test_tableau_when_only_has_powerbi PASSED
```

**Meaning**: The system correctly prevented adding Tableau when only Power BI exists.

### ❌ Test Failed

```
tests/test_optimizer.py::TestSkillFabrication::test_tableau_when_only_has_powerbi FAILED

AssertionError: HALLUCINATION DETECTED: Added Tableau when only has Power BI. 
Edit: "Created data visualizations using Tableau and Power BI"
```

**Meaning**: CRITICAL - The system hallucinated. Step 7 is NOT complete.

**Action Required**:
1. Review the specific test that failed
2. Check which component allowed the hallucination:
   - Generator? (Should never propose it)
   - Verifier? (Should catch it as UNSUPPORTED)
   - Guardrails? (Should block it)
3. Fix the bug
4. Re-run ALL tests (not just the failed one)
5. Repeat until 0 failures

---

## Manual Adversarial Testing

After automated tests pass, perform manual testing:

### Test Case 1: Skill Gap

**Setup**:
- Create resume with: Python, Django, PostgreSQL
- Create JD requiring: Python, FastAPI, Docker
- Run optimization

**Expected**:
- ❌ Should NOT add FastAPI experience
- ❌ Should NOT add Docker experience
- ✅ Should flag as MISSING
- ✅ Should optimize existing Python/Django bullets

**How to Verify**:
```bash
# Use the API or example script
python examples/step7_usage_example.py

# Or test via API
curl -X POST http://localhost:8000/api/optimize \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"resume_version_id": "...", "job_posting_id": "..."}'
```

### Test Case 2: Metric Invention

**Setup**:
- Resume: "Managed software development projects"
- No numbers or metrics in original
- Try to optimize

**Expected**:
- ❌ Should NOT add "10 projects" or "5 team members"
- ❌ Should NOT add "20% faster delivery"
- ✅ Can rephrase: "Led software development initiatives"

### Test Case 3: Title Inflation

**Setup**:
- Resume: "Software Engineer at TechCorp"
- JD: Looking for "Senior Software Engineer"
- Try to optimize

**Expected**:
- ❌ Should NOT change to "Senior Software Engineer"
- ✅ Title must remain exactly "Software Engineer"
- ✅ Can improve bullets to show senior-level work (if facts support it)

### Test Case 4: Date Extension

**Setup**:
- Resume: "2020-01-15 to 2022-06-30"
- Try to optimize

**Expected**:
- ❌ Should NOT change to "2020-01-15 to 2023-06-30"
- ❌ Should NOT round to "2020-2023"
- ✅ Dates must match exactly

### Test Case 5: Company Variation

**Setup**:
- Resume: "Google"
- Try to optimize

**Expected**:
- ❌ Should NOT change to "Google LLC"
- ❌ Should NOT change to "Alphabet Inc."
- ❌ Should NOT change to "Google Inc."
- ✅ Company name must match exactly "Google"

---

## Debugging Failed Tests

### Common Issues

#### 1. API Key Not Set
```
ValueError: ANTHROPIC_API_KEY environment variable is required
```

**Fix**:
```bash
export ANTHROPIC_API_KEY=your_key_here
# Or add to .env file
```

#### 2. Import Errors
```
ModuleNotFoundError: No module named 'anthropic'
```

**Fix**:
```bash
cd apps/api
pip install -r requirements.txt
```

#### 3. Generator Hallucinating

**Symptom**: Test fails with "HALLUCINATION DETECTED"

**Fix**:
- Review `services/optimizer/generate.py`
- Check prompt constraints
- Verify fact_ledger_ids are required
- Increase conservative constraints in prompt

#### 4. Verifier Not Catching Issues

**Symptom**: Verifier says SUPPORTED when it should be UNSUPPORTED

**Fix**:
- Review `services/optimizer/verify.py`
- Check verification prompt
- Ensure verifier doesn't see generator's reasoning
- Make classification rules more strict

#### 5. Guardrails Not Blocking

**Symptom**: Guardrail check passes when it should fail

**Fix**:
- Review `services/optimizer/guardrails.py`
- Check regex patterns for entity extraction
- Verify guardrail logic (ANY difference = block)
- Add more conservative checks

---

## Calculating Hallucination Rate

After all tests:

```
Total Tests: 16
Passed: 16
Failed: 0

Hallucination Rate = (Failed / Total) × 100
                   = (0 / 16) × 100
                   = 0.0%
```

**Target**: 0.0%  
**Acceptable**: 0.0%  
**Unacceptable**: Anything > 0.0%

---

## When Can You Ship?

### ✅ Ready to Move to Step 8 (Frontend)

- [x] `pytest tests/test_optimizer.py -v` → ALL PASS
- [x] Manual adversarial testing → ZERO hallucinations
- [x] Code review complete
- [x] Documentation reviewed
- [x] Hallucination rate = 0.0%

### ❌ Not Ready (Keep Working)

- [ ] ANY test fails
- [ ] Manual testing shows hallucinations
- [ ] Unsure about edge cases
- [ ] Code not reviewed
- [ ] Hallucination rate > 0.0%

---

## Getting Help

If tests are failing and you can't fix them:

1. **Read the test assertion carefully**:
   - What was expected?
   - What actually happened?
   - Which component failed?

2. **Check the test code**:
   - Read `tests/test_optimizer.py`
   - Understand what the test is checking
   - Verify your understanding matches the requirement

3. **Review implementation**:
   - Read the specific file mentioned in the test
   - Check if the logic matches the requirement
   - Look for gaps or edge cases

4. **Add debug output**:
   - Use `pytest -v -s` for verbose output
   - Add print statements to implementation
   - Log verification results

5. **Ask for code review**:
   - Another developer can spot issues
   - Fresh eyes catch edge cases
   - Pair programming helps

---

## The Bottom Line

**Before Step 7 is complete**:
```bash
cd apps/api
pytest tests/test_optimizer.py -v
```

**Must see**: ALL PASS, 0 failures

**If you see ANY failures**: Step 7 is NOT done. Fix and re-test.

**Remember**: Zero tolerance for hallucinations. One fabricated claim destroys user trust.

---

**Last Updated**: Step 7 Core Implementation  
**Next Step**: Run these tests and verify 0.0% hallucination rate
