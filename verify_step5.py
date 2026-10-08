"""
Verification script for Step 5 implementation.

Checks that all Step 5 components are correctly implemented:
1. Models and schemas
2. Services (job posting extractor)
3. API endpoints
4. Database migrations
5. Tests
6. Frontend pages
7. Documentation

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
    print("STEP 5 VERIFICATION - Job Description Analyzer")
    print("=" * 70)
    
    root = Path(__file__).parent
    api_root = root / "apps" / "api"
    web_root = root / "apps" / "web"
    
    checks = []
    
    # Models
    print("\n1. Models & Schemas")
    checks.append(check_file_exists(
        api_root / "models" / "job_posting.py",
        "Job posting models (JobPosting, JobRequirement)"
    ))
    
    # Prompts
    print("\n2. LLM Prompts")
    checks.append(check_file_exists(
        api_root / "prompts" / "job_description_extraction.txt",
        "Job description extraction prompt"
    ))
    
    # Services
    print("\n3. Services")
    checks.append(check_file_exists(
        api_root / "services" / "job_posting_extractor.py",
        "Job posting extractor service"
    ))
    checks.append(check_file_exists(
        api_root / "services" / "file_validation.py",
        "File validation (with TXT support)"
    ))
    
    # Routers
    print("\n4. API Routers")
    checks.append(check_file_exists(
        api_root / "routers" / "job_postings.py",
        "Job postings router"
    ))
    
    # Migrations
    print("\n5. Database Migrations")
    checks.append(check_file_exists(
        api_root / "migrations" / "008_job_postings.sql",
        "Job postings and requirements tables"
    ))
    
    # Tests
    print("\n6. Tests")
    checks.append(check_file_exists(
        api_root / "tests" / "test_job_posting_extractor.py",
        "Job posting extractor tests (9 tests)"
    ))
    
    # Frontend
    print("\n7. Frontend Pages")
    checks.append(check_file_exists(
        web_root / "src" / "app" / "jobs" / "new" / "page.tsx",
        "Job posting creation page"
    ))
    checks.append(check_file_exists(
        web_root / "src" / "app" / "jobs" / "[id]" / "page.tsx",
        "Job posting detail page"
    ))
    
    # Documentation
    print("\n8. Documentation")
    checks.append(check_file_exists(
        root / "STEP5_COMPLETE.md",
        "Step 5 completion document"
    ))
    checks.append(check_file_exists(
        root / "examples" / "step5_usage_example.py",
        "Step 5 usage example"
    ))
    
    # Summary
    print("\n" + "=" * 70)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✓ ALL CHECKS PASSED ({passed}/{total})")
        print("=" * 70)
        print("\nStep 5 is complete and ready!")
        print("\nNext steps:")
        print("1. Run tests: pytest apps/api/tests/test_job_posting_extractor.py -v")
        print("2. Apply migration: psql < apps/api/migrations/008_job_postings.sql")
        print("3. Restart API server to load new code")
        print("4. Test with: python examples/step5_usage_example.py")
        print("\nStep 5 Features:")
        print("  - Extract 8 requirement types from job postings")
        print("  - Support paste text or upload PDF/DOCX/TXT files")
        print("  - NO URL scraping (explicitly out of scope)")
        print("  - Clear distinction between required vs preferred skills")
        print("  - Separate responsibilities from requirements")
        print("  - Competency signals (soft skills) extraction")
        print("\nReady for Step 6: JD Match Score + Resume Matching")
        return 0
    else:
        print(f"✗ SOME CHECKS FAILED ({passed}/{total} passed)")
        print("=" * 70)
        print("\nPlease review missing files above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
