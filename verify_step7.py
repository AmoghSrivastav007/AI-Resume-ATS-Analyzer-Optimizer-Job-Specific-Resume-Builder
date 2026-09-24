"""
Step 7 Verification Script - Truth Guard Optimizer

Verifies that all Step 7 components are properly implemented and integrated.

CRITICAL: This step has ZERO tolerance for hallucinations.
All adversarial tests must pass before considering Step 7 complete.

Checklist:
1. ✅ Fact Ledger Enhanced (company tracking)
2. ✅ Constrained Generation (services/optimizer/generate.py)
3. ✅ Independent Verification (services/optimizer/verify.py)
4. ✅ Deterministic Guardrails (services/optimizer/guardrails.py)
5. ✅ Pipeline Orchestration (services/optimization_service.py)
6. ✅ API Endpoints (routers/optimize.py)
7. ✅ Router Registration (main.py)
8. ✅ Comprehensive Tests (tests/test_optimizer.py)
9. ⚠️  Adversarial Tests Passing (MUST verify manually)
10. ⚠️  Frontend Integration (Coming next)
"""

import os
import sys
from pathlib import Path


def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a file exists."""
    if os.path.exists(file_path):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - FILE NOT FOUND: {file_path}")
        return False


def check_content_in_file(file_path: str, search_term: str, description: str) -> bool:
    """Check if content exists in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if search_term in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - NOT FOUND")
                return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def main():
    print("="*80)
    print("STEP 7 VERIFICATION: Truth Guard Optimizer")
    print("="*80)
    print()
    
    # Change to project root
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    checks = []
    
    print("--- Core Components ---")
    print()
    
    # 1. Constrained Generation
    checks.append(check_file_exists(
        "apps/api/services/optimizer/generate.py",
        "Constrained Generation module"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/generate.py",
        "class ConstrainedGenerator",
        "ConstrainedGenerator class"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/generate.py",
        "fact_ledger_ids",
        "Fact traceability (fact_ledger_ids)"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/generate.py",
        "REPHRASING",
        "REPHRASING vs CONTENT_ADDITION distinction"
    ))
    
    print()
    
    # 2. Independent Verification
    checks.append(check_file_exists(
        "apps/api/services/optimizer/verify.py",
        "Independent Verification module"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/verify.py",
        "class IndependentVerifier",
        "IndependentVerifier class"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/verify.py",
        "SUPPORTED",
        "SUPPORTED/PARTIALLY_SUPPORTED/UNSUPPORTED classification"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/verify.py",
        "haiku",
        "Uses Haiku model (different from generator)"
    ))
    
    print()
    
    # 3. Deterministic Guardrails
    checks.append(check_file_exists(
        "apps/api/services/optimizer/guardrails.py",
        "Deterministic Guardrails module"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/guardrails.py",
        "class DeterministicGuardrails",
        "DeterministicGuardrails class"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/guardrails.py",
        "company",
        "Company name guardrail"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/guardrails.py",
        "title",
        "Job title guardrail"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimizer/guardrails.py",
        "date",
        "Date guardrail"
    ))
    
    print()
    
    # 4. Pipeline Orchestration
    checks.append(check_file_exists(
        "apps/api/services/optimization_service.py",
        "Optimization Service (pipeline orchestration)"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimization_service.py",
        "class OptimizationService",
        "OptimizationService class"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimization_service.py",
        "generate_optimizations",
        "generate_optimizations method"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimization_service.py",
        "_determine_status",
        "Status assignment logic"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/optimization_service.py",
        "rejected",
        "Rejection handling"
    ))
    
    print()
    
    # 5. API Endpoints
    checks.append(check_file_exists(
        "apps/api/routers/optimize.py",
        "Optimization Router"
    ))
    checks.append(check_content_in_file(
        "apps/api/routers/optimize.py",
        "@router.post",
        "POST endpoints"
    ))
    checks.append(check_content_in_file(
        "apps/api/routers/optimize.py",
        "generate_optimizations",
        "Generate optimizations endpoint"
    ))
    checks.append(check_content_in_file(
        "apps/api/routers/optimize.py",
        "apply_optimization",
        "Apply optimization endpoint"
    ))
    checks.append(check_content_in_file(
        "apps/api/routers/optimize.py",
        "reject_optimization",
        "Reject optimization endpoint"
    ))
    
    print()
    
    # 6. Router Registration
    checks.append(check_file_exists(
        "apps/api/main.py",
        "Main application file"
    ))
    checks.append(check_content_in_file(
        "apps/api/main.py",
        "from routers.optimize import router as optimize_router",
        "Optimize router import"
    ))
    checks.append(check_content_in_file(
        "apps/api/main.py",
        "app.include_router(optimize_router)",
        "Optimize router registration"
    ))
    
    print()
    
    # 7. Enhanced Fact Ledger
    checks.append(check_file_exists(
        "apps/api/services/parser/persist.py",
        "Parser persist module (fact ledger)"
    ))
    checks.append(check_content_in_file(
        "apps/api/services/parser/persist.py",
        "company",
        "Company tracking in fact ledger"
    ))
    
    print()
    
    # 8. Tests
    checks.append(check_file_exists(
        "apps/api/tests/test_optimizer.py",
        "Optimizer tests"
    ))
    checks.append(check_content_in_file(
        "apps/api/tests/test_optimizer.py",
        "TestSkillFabrication",
        "Skill fabrication tests"
    ))
    checks.append(check_content_in_file(
        "apps/api/tests/test_optimizer.py",
        "TestMetricInvention",
        "Metric invention tests"
    ))
    checks.append(check_content_in_file(
        "apps/api/tests/test_optimizer.py",
        "TestCompanyTitleDateGuardrails",
        "Company/title/date guardrail tests"
    ))
    checks.append(check_content_in_file(
        "apps/api/tests/test_optimizer.py",
        "tableau_when_only_has_powerbi",
        "Tableau vs Power BI test (user's example)"
    ))
    checks.append(check_content_in_file(
        "apps/api/tests/test_optimizer.py",
        "HALLUCINATION",
        "Hallucination detection in assertions"
    ))
    
    print()
    
    # 9. Documentation
    checks.append(check_file_exists(
        "examples/step7_usage_example.py",
        "Usage example"
    ))
    
    print()
    print("="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print()
    
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Checks Passed: {passed}/{total} ({percentage:.1f}%)")
    print()
    
    if passed == total:
        print("✅ All automated checks passed!")
        print()
        print("="*80)
        print("⚠️  CRITICAL: MANUAL VERIFICATION REQUIRED")
        print("="*80)
        print()
        print("Before considering Step 7 complete, you MUST:")
        print()
        print("1. Run adversarial tests:")
        print("   cd apps/api")
        print("   pytest tests/test_optimizer.py -v")
        print()
        print("2. Verify ZERO test failures:")
        print("   - All skill fabrication tests must pass")
        print("   - All metric invention tests must pass")
        print("   - All guardrail tests must pass")
        print("   - Hallucination rate must be EXACTLY 0.0%")
        print()
        print("3. Manual adversarial testing:")
        print("   - Test with JD requiring skill resume doesn't have")
        print("   - Test with metric not in original")
        print("   - Test title inflation")
        print("   - Test company name changes")
        print("   - Test date tampering")
        print()
        print("4. If ANY test fails:")
        print("   - Step 7 is NOT complete")
        print("   - Fix the pipeline")
        print("   - Re-run all tests")
        print("   - DO NOT ship until hallucination rate is ZERO")
        print()
        print("="*80)
        print("DEFINITION OF DONE")
        print("="*80)
        print()
        print("✅ All 5 Truth Guard steps implemented")
        print("✅ All automated checks passed")
        print("⚠️  All adversarial tests passing (verify manually)")
        print("⚠️  Hallucination rate = 0.0% (verify manually)")
        print("⚠️  Frontend integration (coming next)")
        print()
        print("Step 7 core implementation is COMPLETE.")
        print("Run adversarial tests to verify hallucination prevention.")
        print()
    else:
        print("❌ Some checks failed. Please review the output above.")
        print()
        print("Step 7 is NOT complete until all checks pass.")
        print()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
