# Phase 3: Golden-File Export Tests - Detailed Plan

**Date**: October 7, 2026  
**Status**: Starting Phase 3  
**Goal**: Validate export quality with reference files

---

## 🎯 OVERVIEW

**Phase 3 Goal**: Write 4-6 tests that validate DOCX/PDF exports against golden reference files

**Why Critical**: 
- Ensure exports maintain formatting quality
- Catch regressions in export generation
- Verify structure preservation
- Validate content accuracy

**Timeline**: ~2 hours (estimated)

---

## 📋 TEST BREAKDOWN

### Test Strategy

**Golden-File Testing Approach**:
1. Create reference "golden" files manually with known good structure
2. Generate exports programmatically from test data
3. Compare generated exports to golden files
4. Assert structural and content equivalence

**What We're Testing**:
- DOCX structure preservation (sections, bullets, formatting)
- Content accuracy (all text present)
- Format elements (bold, bullets, headings)
- Edge cases (minimal content, special characters)

---

## 🔧 TESTS TO WRITE

### 1. DOCX Structure Validation (2 tests)

**Test 1**: `test_docx_structure_complete_resume`
- Create reference DOCX with all sections
- Generate DOCX from test resume data
- Compare: paragraph count, heading count, bullet count
- Verify: all section types present

**Test 2**: `test_docx_structure_minimal_resume`
- Create reference DOCX with minimal sections
- Generate DOCX from minimal data
- Compare: basic structure preserved
- Verify: no extra content added

### 2. DOCX Content Validation (2 tests)

**Test 3**: `test_docx_content_accuracy`
- Generate DOCX from known data
- Extract all text from DOCX
- Verify: all expected text present
- Check: name, email, job titles, bullets

**Test 4**: `test_docx_special_characters`
- Test data with special chars: &, <, >, ", ', unicode
- Generate DOCX
- Verify: special chars preserved correctly
- Check: no corruption or escaping issues

### 3. Format Preservation (2 tests)

**Test 5**: `test_docx_format_elements`
- Test data with bold text, bullets, headings
- Generate DOCX
- Verify: formatting preserved
- Check: bold runs, bullet styles, heading styles

**Test 6**: `test_docx_section_ordering`
- Test data with specific section order
- Generate DOCX
- Verify: section order maintained
- Check: contact → summary → experience → education → skills

---

## 🔧 TEST STRUCTURE

### Approach: Structural Comparison

Instead of binary file comparison (too brittle), we'll:
1. Parse the generated DOCX
2. Extract structural elements
3. Compare counts and content
4. Verify formatting attributes

**Why**: DOCX files have metadata (timestamps, IDs) that change each generation, making binary comparison impractical.

### Standard Pattern

```python
import pytest
from docx import Document
import io

def test_docx_structure():
    """Test DOCX structure preservation."""
    # Arrange: Create test data
    resume_data = {...}
    
    # Act: Generate DOCX
    docx_bytes = export_service.generate_docx(user_id, version_id)
    
    # Parse generated DOCX
    doc = Document(io.BytesIO(docx_bytes))
    
    # Assert: Structure
    assert len(doc.paragraphs) == expected_count
    assert paragraph_styles_match(doc, expected_styles)
    assert text_content_present(doc, expected_texts)
```

---

## 📁 FILE STRUCTURE

```
tests/
  golden_files/
    __init__.py
    test_docx_exports.py        # 6 tests
    reference/                  # Reference data (not files)
      sample_resume_data.json   # Test data
    conftest.py                 # Fixtures for export testing
```

**Note**: We won't store reference DOCX files because:
1. DOCX metadata changes (timestamps, IDs)
2. Binary comparison too brittle
3. Structural comparison more robust

---

## 🎯 SUCCESS CRITERIA

### Per Test
- **All tests passing** - 100% pass rate
- **Structural validation** - Element counts match
- **Content validation** - All text present
- **Format validation** - Styles preserved

### Overall Phase 3
- **6 tests written** - Complete coverage
- **100% pass rate** - All tests passing
- **Fast execution** - <5 seconds
- **Documentation** - Clear test descriptions
- **Regression detection** - Catch export changes

---

## 🚀 IMPLEMENTATION PLAN

### Step 1: Create Test Data (15 min)
- Create `sample_resume_data.json` with complete resume
- Create `minimal_resume_data.json` with minimal sections
- Create `special_chars_data.json` with edge cases

### Step 2: Write Structure Tests (30 min)
- Test 1: Complete resume structure
- Test 2: Minimal resume structure
- Verify paragraph counts, heading counts

### Step 3: Write Content Tests (30 min)
- Test 3: Content accuracy
- Test 4: Special characters
- Extract and verify all text

### Step 4: Write Format Tests (30 min)
- Test 5: Format elements (bold, bullets)
- Test 6: Section ordering
- Check styles and attributes

### Step 5: Review & Document (15 min)
- Run all tests
- Check coverage
- Update documentation

**Total Time**: ~2 hours

---

## 📊 EXPECTED OUTCOMES

### Coverage Goals
- `export_service.py` DOCX methods: 70%+ coverage
- Focus on `generate_docx()` and helper methods
- Structural validation comprehensive

### Quality Metrics
- **Pass Rate**: 100%
- **Speed**: <5 seconds for 6 tests
- **Clarity**: Clear test names
- **Maintainability**: Simple comparisons

---

## 🎯 WHY THIS MATTERS

### Export Quality Assurance
- Ensures exports are production-ready
- Catches formatting regressions
- Validates content accuracy
- Protects user experience

### CI/CD Integration
These tests will:
1. Run on every export service change
2. Fail builds on export quality issues
3. Prevent broken exports from shipping
4. Give confidence in export feature

---

## 📝 COMPARISON STRATEGY

### What We Compare

**Structure**:
- Paragraph count
- Heading count (by level)
- Bullet/list item count
- Table count (if any)

**Content**:
- All expected text present
- Contact info correct
- Job titles correct
- Bullet text correct

**Format**:
- Bold text preserved
- Heading styles correct
- Bullet styles correct
- Section ordering maintained

### What We DON'T Compare

**Metadata** (changes each generation):
- Creation timestamp
- Document IDs
- Author info
- Revision history

**Exact Binary** (too brittle):
- File bytes
- XML structure details
- Namespace ordering

---

## ✅ READY TO START

**Next**: Create test data files and write first test

**Command**:
```bash
cd apps/api
pytest tests/golden_files/ -v
```

**Let's validate those exports!** 🚀
