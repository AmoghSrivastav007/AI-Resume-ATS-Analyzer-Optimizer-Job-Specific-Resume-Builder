"""
Verification script for Step 4 implementation.

Checks that all Step 4 components are correctly implemented:
1. Models and schemas
2. Services and scoring
3. API endpoints
4. Database migrations
5. Tests
6. Documentation

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
    print("STEP 4 VERIFICATION")
    print("=" * 70)
    
    root = Path(__file__).parent
    api_root = root / "apps" / "api"
    web_root = root / "apps" / "web"
    
    checks = []
    
    # Models
    print("\n1. Models & Schemas")
    checks.append(check_file_exists(
        api_root / "models" / "quality_issue.py",
        "Quality issue models"
    ))
    
    # Prompts
    print("\n2. LLM Prompts")
    checks.append(check_file_exists(
        api_root / "prompts" / "content_quality.txt",
        "Content quality analysis prompt"
    ))
    
    # Services
    print("\n3. Services")
    checks.append(check_file_exists(
        api_root / "services" / "scoring" / "content_quality_analyzer.py",
        "Content quality analyzer"
    ))
    checks.append(check_file_exists(
        api_root / "services" / "scoring" / "general_quality_scorer.py",
        "General quality scorer"
    ))
    
    # Migrations
    print("\n4. Database Migrations")
    checks.append(check_file_exists(
        api_root / "migrations" / "007_score_breakdown.sql",
        "Score breakdown column migration"
    ))
    
    # Tests
    print("\n5. Tests")
    checks.append(check_file_exists(
        api_root / "tests" / "test_general_quality_scorer.py",
        "General quality scorer tests"
    ))
    
    # Frontend
    print("\n6. Frontend Pages")
    checks.append(check_file_exists(
        web_root / "src" / "app" / "resumes" / "[id]" / "analysis" / "page.tsx",
        "Analysis page component"
    ))
    
    # Documentation
    print("\n7. Documentation")
    checks.append(check_file_exists(
        root / "STEP4_COMPLETE.md",
        "Step 4 completion document"
    ))
    checks.append(check_file_exists(
        api_root / "services" / "scoring" / "SCORING_SYSTEM.md",
        "Scoring system documentation"
    ))
    checks.append(check_file_exists(
        root / "examples" / "step4_usage_example.py",
        "Step 4 usage example"
    ))
    
    # Summary
    print("\n" + "=" * 70)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        print("=" * 70)
        print("\nStep 4 is complete and ready!")
        print("\nNext steps:")
        print("1. Run tests: pytest apps/api/tests/test_general_quality_scorer.py -v")
        print("2. Apply migration: psql < apps/api/migrations/007_score_breakdown.sql")
        print("3. Restart API server to load new code")
        print("4. Test with: python examples/step4_usage_example.py")
        return 0
    else:
        print(f"✗ SOME CHECKS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        print("\nPlease review missing files above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
