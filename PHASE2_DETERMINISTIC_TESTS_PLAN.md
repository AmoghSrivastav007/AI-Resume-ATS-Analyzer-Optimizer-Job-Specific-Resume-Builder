# Phase 2: Deterministic Layer Tests - Detailed Plan

**Date**: October 7, 2026  
**Status**: Starting Phase 2  
**Goal**: Test pure functions with zero variance

---

## 🎯 OVERVIEW

**Phase 2 Goal**: Write 40 tests for deterministic layers (Steps 3, 4, 6, 7)

**Why Critical**: 
- Pure functions = Same input → Same output (always)
- Foundation for hallucination detection
- Zero tolerance for variance

**Timeline**: ~4 hours (estimated)

---

## 📋 TEST BREAKDOWN

### 1. Step 3: Rule Functions (10 tests) - `test_structural.py`

**Module**: `services/parser/structural.py`

**Pure Functions to Test**:
- `extract_structure(content, mime_type)` - Main orchestrator
- `_extract_pdf_structure(content)` - PDF extraction
- `_extract_docx_structure(content)` - DOCX extraction
- `StructuralBlock` - Data class
- `StructuralDocument` - Data class

**Tests**:
1. `test_extract_pdf_structure_basic` - Simple PDF with text blocks
2. `test_extract_pdf_structure_multi_page` - Multiple pages
3. `test_extract_pdf_structure_font_detection` - Font name/size extraction
4. `test_extract_pdf_structure_empty_lines` - Skips empty lines
5. `test_extract_docx_structure_basic` - Simple DOCX with paragraphs
6. `test_extract_docx_structure_headings` - Heading detection
7. `test_extract_docx_structure_font_info` - Font extraction
8. `test_extract_structure_dispatcher` - Route by mime type
9. `test_extract_structure_unsupported_type` - Error handling
10. `test_structural_block_immutability` - Frozen dataclass

**Determinism Check**: Same PDF/DOCX → Same blocks every time

---

### 2. Step 4: Scoring Math (8 tests) - `test_ats_scorer.py`

**Module**: `services/scoring/ats_scorer.py`

**Pure Functions to Test**:
- `score(resume_data)` - Main scoring
- `_score_contact(contact, issues)` - Contact scoring (0-20)
- `_score_sections(sections, issues)` - Section scoring (0-20)
- `_score_density(blocks, sections, issues)` - Density scoring (0-20)
- `_score_experience(work_exp, issues)` - Experience scoring (0-20)
- `_score_skills(skills, issues)` - Skills scoring (0-20)

**Tests**:
1. `test_score_contact_complete` - All fields = 20 points
2. `test_score_contact_missing_email` - Missing email = high severity
3. `test_score_sections_all_present` - All sections = 20 points
4. `test_score_sections_missing_experience` - Missing experience = critical
5. `test_score_density_adequate` - Good content = 20 points
6. `test_score_density_sparse` - Thin content = deductions
7. `test_score_experience_quality` - Metrics, dates, bullets
8. `test_score_skills_balanced` - 5-50 skills = good

**Determinism Check**: Same resume_data → Same score every time

---

### 3. Step 6: Matching Logic (12 tests) - `test_matching_engine.py`

**Module**: `services/matching_engine.py`

**Pure/Deterministic Functions to Test**:
- `normalize_text(text)` - Text normalization
- `_layer1_exact_match(req, skills, blocks)` - Exact matching
- `_layer2_alias_match(req, skills, blocks)` - Alias matching
- `_extract_companies(fact_ledger)` - Company extraction (guardrails)
- `_extract_titles(fact_ledger)` - Title extraction (guardrails)

**Tests** (Layer 1 - Exact Matching):
1. `test_normalize_text_basic` - Lowercase, trim, no special chars
2. `test_normalize_text_complex` - Multiple spaces, punctuation
3. `test_layer1_exact_match_skill` - Match in skills list
4. `test_layer1_exact_match_block` - Match in resume block
5. `test_layer1_exact_match_case_insensitive` - Case variations

**Tests** (Layer 2 - Alias Matching):
6. `test_layer2_alias_match_canonical` - Match canonical term
7. `test_layer2_alias_match_alias` - Match alias term
8. `test_layer2_alias_match_no_match` - No match returns None

**Tests** (Scoring Logic):
9. `test_match_result_score_layer1` - Layer 1 = 100 score
10. `test_match_result_score_layer2` - Layer 2 = 95 score
11. `test_match_result_score_layer3_high` - Similarity > 0.85 = matched
12. `test_match_result_score_layer3_medium` - 0.70 <= sim <= 0.85 = LLM

**Determinism Check**: Same inputs → Same matches every time (Layers 1-2)

**Note**: Layer 3 (semantic) and Layer 4 (LLM) are NOT deterministic, so we test the dispatching logic only, not the embedding/LLM calls.

---

### 4. Step 7: Guardrails (10 tests) - `test_guardrails.py`

**Module**: `services/optimizer/guardrails.py`

**Pure Functions to Test**:
- `_extract_companies(fact_ledger)` - Company extraction
- `_extract_titles(fact_ledger)` - Title extraction
- `_extract_dates(fact_ledger)` - Date extraction
- `_extract_skills(fact_ledger)` - Skill extraction
- `_extract_numbers(fact_ledger)` - Number extraction
- `_extract_company_names(text)` - Regex extraction
- `_extract_job_titles(text)` - Regex extraction
- `_extract_date_ranges(text)` - Regex extraction
- `_extract_technical_terms(text)` - Tech term extraction
- `_is_date_in_ledger(date, ledger_dates)` - Date fuzzy matching

**Tests**:
1. `test_extract_companies_from_ledger` - Extract company facts
2. `test_extract_titles_from_ledger` - Extract title facts
3. `test_extract_dates_from_ledger` - Extract date facts
4. `test_extract_skills_from_ledger` - Extract skill facts
5. `test_extract_numbers_from_ledger` - Extract metric numbers
6. `test_extract_company_names_from_text` - Regex extraction
7. `test_extract_job_titles_from_text` - Title patterns
8. `test_extract_date_ranges_from_text` - Date patterns
9. `test_extract_technical_terms` - Tech term patterns
10. `test_is_date_in_ledger_fuzzy` - Year-based matching

**Determinism Check**: Same input → Same extraction every time

---

## 🔧 TEST STRUCTURE

### Standard Pattern

```python
import pytest
from services.module import function_to_test


class TestModuleName:
    """Tests for deterministic functions in module."""
    
    def test_function_name_scenario(self):
        """Test description."""
        # Arrange
        input_data = {...}
        
        # Act
        result = function_to_test(input_data)
        
        # Assert
        assert result == expected_output
        
        # Determinism check (run twice)
        result2 = function_to_test(input_data)
        assert result == result2
```

### Key Principles

1. **No Mocks for Pure Functions** - Test actual logic
2. **Determinism Verification** - Run twice, compare results
3. **Edge Cases** - Empty inputs, missing fields, malformed data
4. **No External Dependencies** - No API calls, no DB, no LLM
5. **Fast Execution** - Pure functions = instant

---

## ✅ SUCCESS CRITERIA

### Per Test File

- **All tests passing** - 100% pass rate
- **High coverage** - 80%+ on tested functions
- **Fast execution** - <1 second per file
- **Deterministic** - Same input → Same output

### Overall Phase 2

- **40 tests written** - Complete coverage
- **100% pass rate** - All tests passing
- **80%+ coverage** - High coverage on deterministic layers
- **Documentation** - Clear test descriptions
- **Zero variance** - Deterministic behavior verified

---

## 📁 FILE STRUCTURE

```
tests/
  deterministic/
    __init__.py
    test_structural.py          # 10 tests - Step 3
    test_ats_scorer.py          # 8 tests - Step 4
    test_matching_engine.py     # 12 tests - Step 6
    test_guardrails.py          # 10 tests - Step 7
```

---

## 🚀 EXECUTION PLAN

### Session 1 (1.5 hours)

**Work**:
1. Create test directory structure
2. Write Step 3 tests (structural.py) - 10 tests
3. Write Step 4 tests (ats_scorer.py) - 8 tests

**Expected**: 18 tests written, 100% passing

### Session 2 (1.5 hours)

**Work**:
1. Write Step 6 tests (matching_engine.py) - 12 tests
2. Write Step 7 tests (guardrails.py) - 10 tests

**Expected**: 22 tests written, 100% passing

### Session 3 (1 hour)

**Work**:
1. Review all tests
2. Check coverage
3. Document patterns
4. Update progress files

**Expected**: All 40 tests complete, documented, passing

---

## 📊 EXPECTED OUTCOMES

### Coverage Goals

- `structural.py`: 85%+ coverage
- `ats_scorer.py`: 90%+ coverage
- `matching_engine.py`: 70%+ coverage (only deterministic parts)
- `guardrails.py`: 85%+ coverage

### Quality Metrics

- **Determinism**: 100% (all tests verify same input → same output)
- **Speed**: <5 seconds for all 40 tests
- **Clarity**: Clear test names and descriptions
- **Maintainability**: Simple, focused tests

---

## 🎯 WHY THIS MATTERS

### Hallucination Detection Foundation

**Step 3 (Structural)**: 
- Ensures consistent parsing
- No phantom data introduced

**Step 4 (Scoring)**:
- Deterministic scoring math
- No arbitrary score inflation

**Step 6 (Matching)**:
- Exact matching logic tested
- No false matches

**Step 7 (Guardrails)**:
- ZERO tolerance for fabrications
- Hard blocks on ANY invented fact

### CI/CD Integration

These deterministic tests will:
1. Run on every commit
2. Fail builds on ANY variance
3. Catch regressions immediately
4. Prevent hallucinations from shipping

---

## 📝 NOTES

### What's NOT Tested Here

**Non-Deterministic Components**:
- LLM calls (Step 2, 4-part, 7-LLM)
- Embedding generation (Step 5)
- Layer 3 semantic matching (pgvector)
- Layer 4 context matching (LLM)

**Why**: These have variance by design and need evaluation framework testing (Phase 4-5)

### What IS Tested

**Deterministic Components**:
- PDF/DOCX parsing (Step 3)
- Scoring math (Step 4)
- Exact/alias matching (Step 6 Layers 1-2)
- Guardrail extraction logic (Step 7)

**Why**: These must be 100% deterministic, zero variance

---

## ✅ READY TO START

**Next**: Create test directory and start with Step 3 (structural.py)

**Command**:
```bash
cd apps/api
mkdir -p tests/deterministic
pytest tests/deterministic/ -v
```

**Let's build the hallucination detection foundation!** 🚀
