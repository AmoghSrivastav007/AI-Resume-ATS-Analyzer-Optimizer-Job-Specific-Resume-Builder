"""
Step 6 Usage Example: Matching Engine + JD Match Score

This example demonstrates:
1. Running matching analysis between a resume and job posting
2. Getting match results with evidence
3. Viewing gap analysis
4. Understanding the JD Match Score breakdown
"""

import os
import requests
from typing import Dict, Any


# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "your-jwt-token-here")


def run_matching_analysis(resume_version_id: str, job_posting_id: str) -> Dict[str, Any]:
    """
    Run matching analysis between resume and job posting.
    
    This triggers the 4-layer matching engine:
    - Layer 1: Exact match
    - Layer 2: Alias match
    - Layer 3: Semantic match (pgvector)
    - Layer 4: Context match (LLM)
    """
    print("=" * 70)
    print("STEP 1: Running Matching Analysis")
    print("=" * 70)
    
    response = requests.post(
        f"{API_BASE_URL}/match",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        json={
            "resume_version_id": resume_version_id,
            "job_posting_id": job_posting_id
        }
    )
    
    if response.status_code != 201:
        print(f"Error: {response.status_code}")
        print(response.json())
        return {}
    
    result = response.json()
    
    print(f"\n✓ Analysis complete!")
    print(f"Analysis ID: {result['analysis_id']}")
    print(f"\nJD Match Score: {result['jd_match_score']:.1f}/100")
    print(f"  - Keyword Relevance: {result['keyword_relevance']:.1f}/100")
    print(f"  - Skills Alignment: {result['skills_alignment']:.1f}/100")
    print(f"  - Experience Relevance: {result['experience_relevance']:.1f}/100")
    
    print(f"\nMatch Summary:")
    print(f"  Total Requirements: {result['total_requirements']}")
    print(f"  ✓ Matched: {result['matched']}")
    print(f"  ~ Partially Matched: {result['partially_matched']}")
    print(f"  ⚠ Weak Evidence: {result['weak_evidence']}")
    print(f"  ✗ Missing: {result['missing']}")
    
    return result


def get_detailed_matches(analysis_id: str) -> Dict[str, Any]:
    """Get detailed match results with evidence."""
    print("\n" + "=" * 70)
    print("STEP 2: Getting Detailed Match Results")
    print("=" * 70)
    
    response = requests.get(
        f"{API_BASE_URL}/match/{analysis_id}/results",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return {}
    
    result = response.json()
    
    # Display matched requirements
    print("\n✓ MATCHED Requirements:")
    for match in result['grouped_matches']['matched'][:5]:  # Show first 5
        req = match.get('job_requirements', {})
        print(f"  • {req.get('requirement_text', 'N/A')}")
        print(f"    Type: {req.get('requirement_type', 'N/A')}")
        print(f"    Layer: {match['match_layer']} | Score: {match['match_score']:.0f}")
        if match.get('evidence_text'):
            print(f"    Evidence: {match['evidence_text'][:80]}...")
    
    # Display missing requirements
    missing = result['grouped_matches']['missing']
    if missing:
        print(f"\n✗ MISSING Requirements ({len(missing)}):")
        for match in missing[:5]:  # Show first 5
            req = match.get('job_requirements', {})
            print(f"  • {req.get('requirement_text', 'N/A')}")
            print(f"    Type: {req.get('requirement_type', 'N/A')}")
            if match.get('recommendation'):
                print(f"    💡 {match['recommendation']}")
    
    # Display weak evidence
    weak = result['grouped_matches']['weak_evidence']
    if weak:
        print(f"\n⚠ WEAK EVIDENCE ({len(weak)}):")
        for match in weak[:3]:  # Show first 3
            req = match.get('job_requirements', {})
            print(f"  • {req.get('requirement_text', 'N/A')}")
            if match.get('recommendation'):
                print(f"    💡 {match['recommendation']}")
    
    return result


def get_gap_analysis(analysis_id: str) -> Dict[str, Any]:
    """Get gap analysis showing what's missing."""
    print("\n" + "=" * 70)
    print("STEP 3: Gap Analysis")
    print("=" * 70)
    
    response = requests.get(
        f"{API_BASE_URL}/match/{analysis_id}/gaps",
        headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return {}
    
    gaps = response.json()
    
    print(f"\nTotal Gaps: {gaps.get('total_gaps', 0)}")
    print(f"Critical Gaps: {gaps.get('critical_gaps', 0)}")
    
    # Critical gaps (missing required skills)
    critical = gaps.get('gaps', {}).get('critical', [])
    if critical:
        print(f"\n🔴 CRITICAL GAPS (Missing Required Skills):")
        for gap in critical:
            print(f"  • {gap['requirement']}")
            print(f"    💡 {gap['recommendation']}")
    
    # Important gaps (missing preferred skills/certs)
    important = gaps.get('gaps', {}).get('important', [])
    if important:
        print(f"\n🟡 IMPORTANT GAPS (Missing Preferred/Certifications):")
        for gap in important[:5]:  # Show first 5
            print(f"  • {gap['requirement']}")
            print(f"    💡 {gap['recommendation']}")
    
    # Needs improvement (weak evidence)
    needs_improvement = gaps.get('gaps', {}).get('needs_improvement', [])
    if needs_improvement:
        print(f"\n🟠 NEEDS IMPROVEMENT (Weak Evidence):")
        for gap in needs_improvement[:5]:  # Show first 5
            print(f"  • {gap['requirement']}")
            print(f"    💡 {gap['recommendation']}")
    
    return gaps


def display_explainability_tree(match_breakdown: Dict[str, Any]):
    """Display the explainability tree for JD Match Score."""
    print("\n" + "=" * 70)
    print("STEP 4: Score Explainability Tree")
    print("=" * 70)
    
    print(f"\nOverall Score: {match_breakdown['overall_score']:.1f}/100")
    print("\nCategory Breakdown:")
    
    categories = match_breakdown.get('categories', {})
    
    for category_name, category in categories.items():
        weight = category['weight']
        score = category['score']
        contribution = category['contribution']
        
        print(f"\n  {category_name.replace('_', ' ').title()}:")
        print(f"    Weight: {weight}%")
        print(f"    Score: {score:.1f}/100")
        print(f"    Contribution: {contribution:.1f}")
        
        # Show details
        details = category.get('details', {})
        if 'matched_keywords' in details:
            print(f"    Details:")
            print(f"      - Matched: {details['matched_keywords']}/{details['total_keywords']}")
            print(f"      - Match Rate: {details['match_rate']:.1f}%")
        elif isinstance(details, dict):
            print(f"    Details:")
            for key, value in details.items():
                if isinstance(value, dict) and 'matched' in value:
                    print(f"      - {key.replace('_', ' ').title()}: "
                          f"{value['matched']}/{value['total']} matched")


def main():
    """Run complete example workflow."""
    print("\n" + "=" * 70)
    print("Step 6 Example: Matching Engine + JD Match Score")
    print("=" * 70)
    
    # Example IDs (replace with actual IDs from your system)
    RESUME_VERSION_ID = os.getenv("RESUME_VERSION_ID", "your-resume-version-id")
    JOB_POSTING_ID = os.getenv("JOB_POSTING_ID", "your-job-posting-id")
    
    if RESUME_VERSION_ID == "your-resume-version-id":
        print("\n⚠ Please set environment variables:")
        print("  - RESUME_VERSION_ID")
        print("  - JOB_POSTING_ID")
        print("  - AUTH_TOKEN")
        return
    
    # Step 1: Run matching analysis
    analysis = run_matching_analysis(RESUME_VERSION_ID, JOB_POSTING_ID)
    
    if not analysis:
        return
    
    analysis_id = analysis['analysis_id']
    
    # Step 2: Get detailed matches
    detailed_results = get_detailed_matches(analysis_id)
    
    # Step 3: Get gap analysis
    gaps = get_gap_analysis(analysis_id)
    
    # Step 4: Display explainability tree
    if 'match_breakdown' in analysis:
        display_explainability_tree(analysis['match_breakdown'])
    
    print("\n" + "=" * 70)
    print("Example Complete!")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. Review missing requirements in gap analysis")
    print("2. Update resume to address critical gaps")
    print("3. Re-run analysis to see improvement")
    print("4. (Step 7) Generate AI-powered optimizations")


if __name__ == "__main__":
    main()
