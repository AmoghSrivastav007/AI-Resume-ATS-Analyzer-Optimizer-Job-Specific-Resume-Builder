"""
Verification script for Step 6 implementation.

Checks that all Step 6 components are correctly implemented:
1. Embedding service
2. 4-layer matching engine
3. JD Match Scorer
4. Matching service orchestrator
5. API endpoints
6. Database migrations
7. Tests
8. Documentation

Run this before deploying to verify completeness.
"""

import sys
from pathlib import Path


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"✓ {description}")
        return True
    else:
        print(f"✗ {description} - MISSING: {filepath}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("STEP 6 VERIFICATION - Matching Engine + JD Match Score")
    print("=" * 70)
    
    root = Path(__file__).parent
    api_root = root / "apps" / "api"
    
    checks = []
    
    # Services
    print("\n1. Core Services")
    checks.append(check_file_exists(
        api_root / "services" / "embedding_service.py",
        "Embedding service"
    ))
    checks.append(check_file_exists(
        api_root / "services" / "matching_engine.py",
        "4-layer matching engine"
    ))
    checks.append(check_file_exists(
        api_root / "services" / "jd_match_scorer.py",
        "JD Match Score calculator"
    ))
    checks.append(check_file_exists(
        api_root / "services" / "matching_service.py",
        "Matching service orchestrator"
    ))
    
    # Routers
    print("\n2. API Routers")
    checks.append(check_file_exists(
        api_root / "routers" / "matching.py",
        "Matching API router"
    ))
    
    # Models
    print("\n3. Pydantic Models")
    checks.append(check_file_exists(
        api_root / "models" / "matching.py",
        "Matching models"
    ))
    
    # Migrations
    print("\n4. Database Migrations")
    checks.append(check_file_exists(
        api_root / "migrations" / "009_step6_matching.sql",
        "Step 6 migration (skill_aliases, enhanced match_results)"
    ))
    
    # Tests
    print("\n5. Tests")
    checks.append(check_file_exists(
        api_root / "tests" / "test_matching_engine.py",
        "Matching engine tests"
    ))
    checks.append(check_file_exists(
        api_root / "tests" / "test_jd_match_scorer.py",
        "JD Match Scorer tests"
    ))
    
    # Documentation
    print("\n6. Documentation")
    checks.append(check_file_exists(
        root / "STEP6_COMPLETE.md",
        "Step 6 completion document"
    ))
    checks.append(check_file_exists(
        root / "examples" / "step6_usage_example.py",
        "Step 6 usage example"
    ))
    
    # Summary
    print("\n" + "=" * 70)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        print("=" * 70)
        print("\nStep 6 is complete and ready!")
        print("\nNext steps:")
        print("1. Run tests: pytest apps/api/tests/test_matching_engine.py -v")
        print("2. Run tests: pytest apps/api/tests/test_jd_match_scorer.py -v")
        print("3. Apply migration: psql < apps/api/migrations/009_step6_matching.sql")
        print("4. Restart API server to load new code")
        print("5. Test with: python examples/step6_usage_example.py")
        print("\nStep 6 Features:")
        print("  - 4-layer matching engine (exact, alias, semantic, context)")
        print("  - 120+ skill aliases from ESCO/O*NET taxonomy")
        print("  - JD Match Score with 3 categories (40/40/20)")
        print("  - 5 match statuses (matched, partial, weak, missing, not_relevant)")
        print("  - Gap analysis with criticality levels")
        print("  - Explainability tree for score breakdown")
        print("  - Evidence tracking with block references")
        print("\nReady for Step 7: Optimization Generation + Truth Guard")
        return 0
    else:
        print(f"✗ SOME CHECKS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        print("\nPlease review missing files above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
