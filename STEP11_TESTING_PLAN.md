# Step 11: Testing & Optimization - Implementation Plan

**Date Started**: October 6, 2026  
**Status**: In Progress  
**Estimated Time**: 2-3 weeks  
**Goal**: Achieve 90%+ test coverage and optimize performance

---

## 🎯 OBJECTIVES

1. **Comprehensive Test Coverage** - 90%+ on critical services
2. **Performance Optimization** - Meet latency targets
3. **Bug Identification** - Find and fix issues before production
4. **Confidence Building** - Ensure reliability for launch

---

## 📋 TESTING STRATEGY

### Phase 1: Unit Tests (Week 1)
Focus on individual services and functions in isolation

### Phase 2: Integration Tests (Week 1-2)
Test complete workflows and API endpoints

### Phase 3: E2E Tests (Week 2)
Test through browser like a real user

### Phase 4: Performance Tests (Week 2-3)
Load testing and optimization

### Phase 5: Bug Fixes (Week 3)
Address issues found during testing

---

## 🧪 PHASE 1: UNIT TESTS (Days 1-3)

### Priority: CRITICAL Services

#### 1.1 Export Service Tests ⚡ HIGH PRIORITY
**File**: `apps/api/tests/services/test_export_service.py`

**Tests to Write**:
- ✅ `test_generate_docx_success` - Normal resume to DOCX
- ✅ `test_generate_docx_with_special_characters` - Unicode handling
- ✅ `test_generate_docx_with_long_content` - Large resumes
- ✅ `test_generate_pdf_fails_gracefully_without_gtk` - Error handling
- ✅ `test_validate_export_success` - Validation passes
- ✅ `test_validate_export_fails_low_recovery` - Validation fails (<80%)
- ✅ `test_fetch_resume_data` - Data retrieval
- ✅ `test_prepare_template_data` - Data transformation
- ✅ `test_compare_parsed_data` - Validation logic

**Coverage Target**: 90%+

#### 1.2 Deletion Service Tests ⚡ HIGH PRIORITY
**File**: `apps/api/tests/services/test_deletion_service.py`

**Tests to Write**:
- ✅ `test_delete_resume_success` - Complete deletion
- ✅ `test_delete_resume_with_storage_files` - Storage cleanup
- ✅ `test_delete_resume_cascades` - Related records deleted
- ✅ `test_delete_nonexistent_resume` - Error handling
- ✅ `test_delete_other_user_resume_fails` - Security check
- ✅ `test_audit_log_created` - Audit trail
- ✅ `test_cleanup_old_audit_logs` - Retention policy

**Coverage Target**: 85%+

#### 1.3 Block Editor Service Tests ⚡ MEDIUM PRIORITY
**File**: `apps/api/tests/services/test_block_editor_service.py`

**Tests to Write**:
- ✅ `test_update_block_content` - Basic update
- ✅ `test_update_block_triggers_reanalysis` - Side effects
- ✅ `test_update_block_validation` - Input validation
- ✅ `test_update_other_user_block_fails` - Security
- ✅ `test_add_block` - Block creation
- ✅ `test_delete_block` - Block removal
- ✅ `test_reorder_blocks` - Block ordering

**Coverage Target**: 85%+

#### 1.4 Version Service Tests ⚡ MEDIUM PRIORITY
**File**: `apps/api/tests/services/test_version_service.py`

**Tests to Write**:
- ✅ `test_create_version` - Version creation
- ✅ `test_restore_version` - Version restoration
- ✅ `test_duplicate_version` - Version duplication
- ✅ `test_delete_version` - Version deletion
- ✅ `test_rename_resume` - Resume renaming
- ✅ `test_version_numbering` - Increment logic
- ✅ `test_list_versions` - Version retrieval

**Coverage Target**: 85%+

#### 1.5 Matching Service Tests ⚡ MEDIUM PRIORITY
**File**: `apps/api/tests/services/test_matching_service.py`

**Tests to Write**:
- ✅ `test_exact_match` - Layer 1 matching
- ✅ `test_alias_match` - Layer 2 with ESCO taxonomy
- ✅ `test_semantic_match` - Layer 3 vector similarity
- ✅ `test_context_match` - Layer 4 LLM verification
- ✅ `test_calculate_jd_match_score` - Score calculation
- ✅ `test_identify_gaps` - Gap analysis
- ✅ `test_prioritize_gaps` - Gap prioritization

**Coverage Target**: 85%+

### Unit Test Commands
```bash
cd apps/api
.\.venv\Scripts\Activate.ps1

# Run all unit tests
pytest tests/services/

# Run specific test file
pytest tests/services/test_export_service.py -v

# Run with coverage
pytest tests/services/ --cov=services --cov-report=html

# Run tests in parallel
pytest tests/services/ -n auto
```

---

## 🔗 PHASE 2: INTEGRATION TESTS (Days 4-7)

### Priority: CRITICAL Workflows

#### 2.1 Full Upload-to-Export Workflow
**File**: `apps/api/tests/integration/test_full_workflow.py`

**Tests to Write**:
- ✅ `test_complete_workflow` - Upload → Parse → Analyze → Edit → Export
- ✅ `test_workflow_with_errors` - Error handling throughout
- ✅ `test_workflow_multiple_users` - User isolation
- ✅ `test_workflow_concurrent_operations` - Race conditions

#### 2.2 Job Description Workflow
**File**: `apps/api/tests/integration/test_jd_workflow.py`

**Tests to Write**:
- ✅ `test_jd_upload_match_optimize` - Full JD workflow
- ✅ `test_multiple_jds_same_resume` - Multiple JD matching
- ✅ `test_jd_match_score_calculation` - End-to-end scoring

#### 2.3 Version Management Workflow
**File**: `apps/api/tests/integration/test_version_workflow.py`

**Tests to Write**:
- ✅ `test_create_restore_workflow` - Version lifecycle
- ✅ `test_duplicate_edit_export` - Duplicate workflow
- ✅ `test_version_isolation` - Version independence

#### 2.4 Security Isolation Tests
**File**: `apps/api/tests/integration/test_security_isolation.py`

**Tests to Write**:
- ✅ `test_cross_user_resume_access` - RLS enforcement
- ✅ `test_cross_user_block_access` - Block isolation
- ✅ `test_cross_user_export_access` - Export isolation
- ✅ `test_invalid_jwt_rejected` - Auth validation
- ✅ `test_rate_limiting_enforced` - Rate limit testing

### Integration Test Commands
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with database reset between tests
pytest tests/integration/ --db-reset

# Run specific workflow
pytest tests/integration/test_full_workflow.py::test_complete_workflow -v
```

---

## 🌐 PHASE 3: E2E TESTS (Days 8-10)

### Setup Playwright
```bash
cd apps/web
npm install -D @playwright/test
npx playwright install
```

### Priority: CRITICAL User Journeys

#### 3.1 Authentication Flow
**File**: `apps/web/e2e/auth.spec.ts`

**Tests to Write**:
- ✅ `test_signup_success` - New user registration
- ✅ `test_login_success` - Existing user login
- ✅ `test_login_invalid_credentials` - Error handling
- ✅ `test_logout` - Session termination
- ✅ `test_protected_routes` - Auth guard

#### 3.2 Upload Flow
**File**: `apps/web/e2e/upload.spec.ts`

**Tests to Write**:
- ✅ `test_upload_pdf_resume` - PDF upload
- ✅ `test_upload_docx_resume` - DOCX upload
- ✅ `test_upload_invalid_file` - Error handling
- ✅ `test_upload_oversized_file` - Size validation
- ✅ `test_parsing_progress` - Progress indication

#### 3.3 Editor Flow
**File**: `apps/web/e2e/editor.spec.ts`

**Tests to Write**:
- ✅ `test_edit_block_inline` - Inline editing
- ✅ `test_ai_rewrite_apply` - AI suggestions
- ✅ `test_add_delete_block` - Block management
- ✅ `test_undo_redo` - History management

#### 3.4 Analysis Flow
**File**: `apps/web/e2e/analysis.spec.ts`

**Tests to Write**:
- ✅ `test_view_scores` - Score display
- ✅ `test_navigate_tabs` - Tab navigation
- ✅ `test_click_issue_highlights_block` - Issue linking
- ✅ `test_reanalyze` - Re-analysis trigger

#### 3.5 Export Flow
**File**: `apps/web/e2e/export.spec.ts`

**Tests to Write**:
- ✅ `test_export_docx_success` - DOCX export
- ✅ `test_export_validation_passes` - Validation display
- ✅ `test_export_download` - File download
- ✅ `test_export_validation_fails` - Validation failure
- ✅ `test_export_multiple_formats` - Format selection

#### 3.6 Error Handling
**File**: `apps/web/e2e/error-handling.spec.ts`

**Tests to Write**:
- ✅ `test_network_error` - Network failure
- ✅ `test_backend_error` - 500 error
- ✅ `test_not_found_error` - 404 error
- ✅ `test_rate_limit_error` - 429 error

### E2E Test Commands
```bash
cd apps/web

# Run all E2E tests (headless)
npx playwright test

# Run with UI mode (interactive)
npx playwright test --ui

# Run specific test
npx playwright test e2e/export.spec.ts

# Run in specific browser
npx playwright test --project=chromium

# Debug mode
npx playwright test --debug
```

---

## 📊 PHASE 4: PERFORMANCE TESTS (Days 11-14)

### Setup Locust
```bash
cd apps/api
pip install locust
```

#### 4.1 Load Test: Upload Endpoint
**File**: `apps/api/tests/load/test_upload_load.py`

**Tests to Write**:
- ✅ `test_upload_10_concurrent` - 10 concurrent uploads
- ✅ `test_upload_sustained_load` - 1 req/sec for 5 minutes
- ✅ `test_upload_spike` - Sudden load spike

**Targets**:
- p50 latency: <2s
- p95 latency: <5s
- Error rate: <1%

#### 4.2 Load Test: Export Endpoint
**File**: `apps/api/tests/load/test_export_load.py`

**Tests to Write**:
- ✅ `test_export_20_concurrent` - 20 concurrent exports
- ✅ `test_export_sustained_load` - 2 req/sec for 5 minutes
- ✅ `test_export_validation_performance` - Validation overhead

**Targets**:
- p50 latency: <8s
- p95 latency: <15s
- Error rate: <1%

#### 4.3 Load Test: Analysis Endpoint
**File**: `apps/api/tests/load/test_analysis_load.py`

**Tests to Write**:
- ✅ `test_analysis_30_concurrent` - 30 concurrent analyses
- ✅ `test_analysis_sustained_load` - 3 req/sec for 5 minutes

**Targets**:
- p50 latency: <12s
- p95 latency: <20s
- Error rate: <1%

#### 4.4 Load Test: Read Endpoints
**File**: `apps/api/tests/load/test_read_load.py`

**Tests to Write**:
- ✅ `test_read_100_concurrent` - 100 concurrent reads
- ✅ `test_read_sustained_load` - 10 req/sec for 5 minutes

**Targets**:
- p50 latency: <100ms
- p95 latency: <200ms
- Error rate: <0.1%

### Performance Test Commands
```bash
cd apps/api

# Run upload load test
locust -f tests/load/test_upload_load.py --host=http://localhost:8000

# Run with web UI
locust -f tests/load/test_upload_load.py --host=http://localhost:8000 --web-host=0.0.0.0

# Run headless with report
locust -f tests/load/test_upload_load.py --host=http://localhost:8000 --headless -u 50 -r 10 -t 5m --html=report.html
```

---

## ⚡ PHASE 5: PERFORMANCE OPTIMIZATION (Days 15-18)

### Based on Load Test Results

#### 5.1 Database Optimization
**Likely Needs**:
- ✅ Add indexes for frequently queried fields
- ✅ Optimize N+1 queries
- ✅ Connection pool tuning
- ✅ Query result caching

#### 5.2 Caching Layer
**Implement**:
- ✅ Redis caching for analysis results (30 min TTL)
- ✅ Redis caching for embeddings (24 hour TTL)
- ✅ Redis caching for resume data (5 min TTL)
- ✅ Cache invalidation on updates

#### 5.3 Background Jobs
**Move to Background**:
- ✅ Export validation (currently synchronous)
- ✅ Re-analysis triggers (debounced)
- ✅ Email notifications (if added)

#### 5.4 API Optimization
**Implement**:
- ✅ Response compression (gzip)
- ✅ Pagination on list endpoints
- ✅ Batch operations where possible
- ✅ Field selection (return only requested fields)

---

## 🐛 PHASE 6: BUG FIXES (Days 19-21)

### Process

1. **Run All Tests**
   ```bash
   pytest tests/ -v --tb=short
   ```

2. **Document Failures**
   - Create GitHub Issues for each bug
   - Categorize by severity
   - Assign priority

3. **Fix Critical Bugs** (P0)
   - Security issues
   - Data corruption
   - Complete feature breakage

4. **Fix High Priority Bugs** (P1)
   - Major functionality issues
   - Poor user experience
   - Performance degradation

5. **Fix Medium Priority Bugs** (P2)
   - Minor functionality issues
   - Edge cases
   - Cosmetic issues

6. **Document Known Issues** (P3)
   - Low impact issues
   - Future enhancements
   - Nice-to-haves

---

## 📊 SUCCESS CRITERIA

### Test Coverage
- [ ] Unit tests: 90%+ coverage on critical services
- [ ] Integration tests: 20+ tests covering main workflows
- [ ] E2E tests: 15+ tests covering user journeys
- [ ] Performance tests: 4 load test scenarios

### Performance Targets
- [ ] Upload endpoint: <2s p95
- [ ] Export endpoint: <10s p95
- [ ] Analysis endpoint: <15s p95
- [ ] Read endpoints: <200ms p95

### Quality Metrics
- [ ] All critical bugs fixed
- [ ] All high priority bugs fixed
- [ ] Test suite runs in <10 minutes
- [ ] CI/CD pipeline configured

### Documentation
- [ ] Test documentation written
- [ ] Performance benchmarks documented
- [ ] Known issues documented
- [ ] Regression test plan created

---

## 🛠️ TESTING INFRASTRUCTURE

### Required Tools
```bash
# Backend testing
pip install pytest pytest-asyncio pytest-cov pytest-xdist

# Load testing
pip install locust

# Frontend testing
npm install -D @playwright/test

# Code quality
pip install ruff mypy
npm install -D eslint @typescript-eslint/parser
```

### CI/CD Configuration
**File**: `.github/workflows/test.yml`

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - run: cd apps/api && pip install -r requirements.txt
      - run: cd apps/api && pytest tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '24'
      - run: cd apps/web && npm install
      - run: cd apps/web && npm run build
      - run: cd apps/web && npx playwright test
```

---

## 📅 TIMELINE

### Week 1: Unit & Integration Tests
- Days 1-3: Unit tests (export, deletion, editor, version)
- Days 4-7: Integration tests (workflows, security)

### Week 2: E2E & Performance Tests
- Days 8-10: E2E tests (auth, upload, editor, export)
- Days 11-14: Performance tests (load testing)

### Week 3: Optimization & Bug Fixes
- Days 15-18: Performance optimization
- Days 19-21: Bug fixes and documentation

**Total**: 21 days (3 weeks)

---

## 🎯 NEXT IMMEDIATE ACTIONS

1. ✅ Create test directory structure
2. ✅ Write test fixtures and helpers
3. ✅ Start with Export Service tests (highest priority)
4. ✅ Run tests and verify they work
5. ✅ Continue with other unit tests

---

## 📝 NOTES

### Testing Philosophy
- **Write tests for behavior, not implementation**
- **Test edge cases and error conditions**
- **Keep tests fast and isolated**
- **Mock external services (Anthropic, Supabase Storage)**
- **Use fixtures for common test data**

### Best Practices
- One assertion per test (when possible)
- Clear test names describing what is being tested
- Arrange-Act-Assert pattern
- Clean up after tests (no side effects)
- Deterministic tests (no randomness)

---

**Document Version**: 1.0  
**Last Updated**: October 6, 2026  
**Status**: Ready to begin implementation

**Next**: Create test directory structure and start writing export service tests
