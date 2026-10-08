"""
Example usage of Step 3 - Scoring & Matching API

This script demonstrates:
1. Creating a job description
2. Running ATS analysis on a resume
3. Running JD match analysis
4. Retrieving detailed results

Prerequisites:
- Resume already uploaded and parsed (Step 1 & 2 complete)
- API server running on http://localhost:8000
- Valid authentication token
"""

import requests
from typing import Any

# Configuration
API_BASE_URL = "http://localhost:8000/api"
AUTH_TOKEN = "your_jwt_token_here"  # Replace with actual token

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
}


def create_job_description() -> str:
    """Step 1: Create and parse a job description."""
    print("\n1. Creating Job Description...")
    
    jd_data = {
        "title": "Senior Backend Engineer",
        "company": "TechCorp Inc.",
        "source_url": "https://example.com/jobs/123",
        "raw_text": """
We are seeking a talented Senior Backend Engineer to join our growing team.

Requirements:
- 5+ years of professional software development experience
- Strong proficiency in Python and Django framework
- Experience with PostgreSQL or other relational databases
- Familiarity with Docker and container orchestration
- Bachelor's degree in Computer Science or related field

Nice to have:
- Experience with AWS or other cloud platforms
- Knowledge of Redis and caching strategies
- Previous experience with microservices architecture
- Kubernetes experience
"""
    }
    
    response = requests.post(
        f"{API_BASE_URL}/job-descriptions",
        headers=HEADERS,
        json=jd_data,
    )
    response.raise_for_status()
    
    result = response.json()
    jd_id = result["id"]
    
    print(f"✓ Created JD: {result['title']}")
    print(f"  Requirements parsed: {result['requirement_count']}")
    print(f"  JD ID: {jd_id}")
    
    return jd_id


def run_ats_analysis(resume_version_id: str) -> str:
    """Step 2: Run ATS compatibility analysis."""
    print("\n2. Running ATS Analysis...")
    
    analysis_data = {
        "resume_version_id": resume_version_id,
        "analysis_type": "ats",
    }
    
    response = requests.post(
        f"{API_BASE_URL}/analyses",
        headers=HEADERS,
        json=analysis_data,
    )
    response.raise_for_status()
    
    result = response.json()
    analysis_id = result["id"]
    
    print(f"✓ ATS Analysis Complete")
    print(f"  Overall Score: {result['overall_score']:.1f}/100")
    print(f"  Issues Found: {result['issue_count']}")
    
    if "summary" in result and "category_scores" in result["summary"]:
        print("\n  Category Scores:")
        for category, score in result["summary"]["category_scores"].items():
            print(f"    {category.capitalize()}: {score:.1f}/20")
    
    return analysis_id


def run_jd_match_analysis(resume_version_id: str, jd_id: str) -> str:
    """Step 3: Run job description match analysis."""
    print("\n3. Running JD Match Analysis...")
    
    analysis_data = {
        "resume_version_id": resume_version_id,
        "job_description_id": jd_id,
        "analysis_type": "jd_match",
    }
    
    response = requests.post(
        f"{API_BASE_URL}/analyses",
        headers=HEADERS,
        json=analysis_data,
    )
    response.raise_for_status()
    
    result = response.json()
    analysis_id = result["id"]
    
    print(f"✓ JD Match Analysis Complete")
    print(f"  Overall Match Score: {result['overall_score']:.1f}/100")
    
    if "summary" in result:
        summary = result["summary"]
        print(f"\n  Match Summary:")
        print(f"    Matched: {summary.get('matched', 0)}")
        print(f"    Partial: {summary.get('partial', 0)}")
        print(f"    Missing: {summary.get('missing', 0)}")
        print(f"    Total Requirements: {summary.get('total_requirements', 0)}")
        print(f"    Match Rate: {summary.get('match_rate', 0):.1f}%")
    
    return analysis_id


def get_detailed_results(analysis_id: str) -> dict[str, Any]:
    """Step 4: Retrieve detailed analysis results."""
    print(f"\n4. Fetching Detailed Results...")
    
    response = requests.get(
        f"{API_BASE_URL}/analyses/{analysis_id}",
        headers=HEADERS,
    )
    response.raise_for_status()
    
    result = response.json()
    
    print(f"✓ Retrieved Analysis Details")
    
    # Show matches
    if result.get("matches"):
        print(f"\n  Requirement Matches ({len(result['matches'])} total):")
        for match in result["matches"][:5]:  # Show first 5
            status_emoji = {
                "matched": "✓",
                "partial": "~",
                "missing": "✗",
            }.get(match["match_status"], "?")
            
            print(f"    {status_emoji} [{match['requirement_type']}] {match['requirement_text']}")
            print(f"      Score: {match['match_score']:.1f}/100 | Status: {match['match_status']}")
            if match.get("evidence", {}).get("matched_terms"):
                terms = match["evidence"]["matched_terms"][:3]
                print(f"      Evidence: {', '.join(terms)}")
        
        if len(result["matches"]) > 5:
            print(f"    ... and {len(result['matches']) - 5} more")
    
    # Show issues
    if result.get("issues"):
        print(f"\n  Issues Detected ({len(result['issues'])} total):")
        for issue in result["issues"][:5]:  # Show first 5
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }.get(issue["severity"], "⚪")
            
            print(f"    {severity_emoji} [{issue['severity'].upper()}] {issue['title']}")
            print(f"      {issue['description']}")
        
        if len(result["issues"]) > 5:
            print(f"    ... and {len(result['issues']) - 5} more")
    
    return result


def main():
    """Run complete example workflow."""
    print("=" * 60)
    print("Resume Analyzer - Step 3 Usage Example")
    print("=" * 60)
    
    # You need to replace this with an actual resume version ID
    # from a previously uploaded and parsed resume
    resume_version_id = input("\nEnter your resume_version_id: ").strip()
    
    if not resume_version_id:
        print("❌ Error: resume_version_id is required")
        print("\nHint: Upload a resume first using POST /api/resumes")
        print("      Then use the version_id from the response")
        return
    
    try:
        # Step 1: Create JD
        jd_id = create_job_description()
        
        # Step 2: Run ATS analysis
        ats_analysis_id = run_ats_analysis(resume_version_id)
        
        # Step 3: Run JD match analysis
        jd_analysis_id = run_jd_match_analysis(resume_version_id, jd_id)
        
        # Step 4: Get detailed results
        detailed_results = get_detailed_results(jd_analysis_id)
        
        print("\n" + "=" * 60)
        print("✓ All steps completed successfully!")
        print("=" * 60)
        print(f"\nATS Analysis ID: {ats_analysis_id}")
        print(f"JD Match Analysis ID: {jd_analysis_id}")
        print(f"\nYou can view these analyses at:")
        print(f"  {API_BASE_URL}/analyses/{ats_analysis_id}")
        print(f"  {API_BASE_URL}/analyses/{jd_analysis_id}")
        
    except requests.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
