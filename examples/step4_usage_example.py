"""
Example usage of Step 4 - General Resume Quality Score

This script demonstrates:
1. Running the enhanced ATS analysis with LLM content quality
2. Viewing the explainability tree
3. Exploring category breakdowns
4. Understanding issue recommendations

Prerequisites:
- Resume uploaded and parsed (Steps 1-2)
- ANTHROPIC_SONNET_MODEL configured in .env
- API server running on http://localhost:8000
- Valid authentication token
"""

import requests
from typing import Any
import json

# Configuration
API_BASE_URL = "http://localhost:8000/api"
AUTH_TOKEN = "your_jwt_token_here"  # Replace with actual token

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json",
}


def run_general_quality_analysis(resume_version_id: str) -> dict[str, Any]:
    """Run General Resume Quality Score analysis."""
    print("\n" + "="*70)
    print("STEP 4: General Resume Quality Score Analysis")
    print("="*70)
    
    print("\n1. Running analysis (this may take 10-15 seconds)...")
    print("   - Deterministic checks (structure, formatting)")
    print("   - LLM content quality analysis (Sonnet model)")
    print("   - Score calculation and aggregation")
    
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
    
    print(f"\n✓ Analysis Complete!")
    print(f"  Analysis ID: {analysis_id}")
    
    return result


def display_overall_score(analysis: dict[str, Any]) -> None:
    """Display overall score with grade."""
    print("\n" + "="*70)
    print("OVERALL SCORE")
    print("="*70)
    
    score = analysis["overall_score"]
    summary = analysis.get("summary", {})
    
    # Determine grade
    if score >= 90:
        grade = "A"
        emoji = "🌟"
    elif score >= 80:
        grade = "B"
        emoji = "✨"
    elif score >= 70:
        grade = "C"
        emoji = "👍"
    elif score >= 60:
        grade = "D"
        emoji = "⚠️"
    else:
        grade = "F"
        emoji = "❌"
    
    print(f"\n  {emoji} Score: {score:.1f}/100 (Grade {grade})")
    print(f"\n  Score Type: {summary.get('score_type', 'general_resume_quality')}")
    print(f"  Total Issues: {summary.get('total_issues', 0)}")
    print(f"    - Critical: {summary.get('critical_issues', 0)} 🔴")
    print(f"    - High: {summary.get('high_issues', 0)} 🟠")


def display_content_quality_assessment(analysis: dict[str, Any]) -> None:
    """Display LLM content quality assessment."""
    summary = analysis.get("summary", {})
    content_quality = summary.get("content_quality")
    
    if not content_quality:
        print("\n  No content quality data available")
        return
    
    print("\n" + "="*70)
    print("CONTENT QUALITY ASSESSMENT (LLM Analysis)")
    print("="*70)
    
    print(f"\n  Overall: {content_quality.get('overall', 'N/A').upper()}")
    print(f"\n  {content_quality.get('summary', 'No summary')}")
    
    strengths = content_quality.get("strengths", [])
    if strengths:
        print(f"\n  ✅ Strengths:")
        for strength in strengths:
            print(f"     • {strength}")
    
    weaknesses = content_quality.get("weaknesses", [])
    if weaknesses:
        print(f"\n  ⚠️  Areas for Improvement:")
        for weakness in weaknesses:
            print(f"     • {weakness}")


def display_category_scores(analysis: dict[str, Any]) -> None:
    """Display category breakdown."""
    summary = analysis.get("summary", {})
    category_scores = summary.get("category_scores", {})
    
    if not category_scores:
        print("\n  No category scores available")
        return
    
    print("\n" + "="*70)
    print("CATEGORY BREAKDOWN")
    print("="*70)
    
    CATEGORY_NAMES = {
        "parsing_compatibility": "Parsing Compatibility",
        "structure": "Structure",
        "content_quality": "Content Quality",
        "formatting": "Formatting",
        "metadata": "Metadata",
    }
    
    print(f"\n  {'Category':<25} {'Weight':<10} {'Raw':<12} {'Weighted':<12}")
    print("  " + "-"*65)
    
    total_weighted = 0
    for cat_key, cat_data in category_scores.items():
        name = CATEGORY_NAMES.get(cat_key, cat_key)
        weight = cat_data.get("max_score", 0)
        raw = cat_data.get("raw_score", 0)
        weighted = cat_data.get("weighted_score", 0)
        total_weighted += weighted
        
        # Color based on raw score
        if raw >= 90:
            indicator = "🟢"
        elif raw >= 75:
            indicator = "🔵"
        elif raw >= 60:
            indicator = "🟡"
        else:
            indicator = "🔴"
        
        print(f"  {indicator} {name:<23} {weight:>6.1f}%   {raw:>8.1f}/100  {weighted:>8.2f}/{weight:.1f}")
    
    print("  " + "-"*65)
    print(f"    {'TOTAL':<23} {'100.0%':<10} {'':<12} {total_weighted:>8.2f}/100")


def explain_category(analysis_id: str, category: str) -> None:
    """Get detailed explanation for a specific category."""
    print(f"\n" + "="*70)
    print(f"DETAILED BREAKDOWN: {category.upper().replace('_', ' ')}")
    print("="*70)
    
    response = requests.get(
        f"{API_BASE_URL}/analyses/{analysis_id}/explain/{category}",
        headers=HEADERS,
    )
    response.raise_for_status()
    
    data = response.json()
    cat_score = data.get("category_score", {})
    
    print(f"\n  Raw Score: {cat_score.get('raw_score', 0):.1f}/100")
    print(f"  Weight: {cat_score.get('weight_percentage', 0):.1f}%")
    print(f"  Contribution: {cat_score.get('weighted_score', 0):.2f}")
    
    deductions = cat_score.get("deductions", [])
    
    if not deductions:
        print(f"\n  ✓ No issues found in this category!")
        return
    
    print(f"\n  Deductions ({len(deductions)} issues):")
    print()
    
    SEVERITY_EMOJI = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }
    
    for idx, ded in enumerate(deductions, 1):
        severity = ded.get("severity", "medium")
        emoji = SEVERITY_EMOJI.get(severity, "⚪")
        
        print(f"  {idx}. {emoji} [{severity.upper()}] {ded.get('reason', 'Unknown issue')}")
        print(f"     Points: -{ded.get('points', 0)}")
        print(f"     Issue: {ded.get('description', 'No description')}")
        print(f"     💡 Recommendation: {ded.get('recommendation', 'No recommendation')}")
        print()


def get_detailed_analysis(analysis_id: str) -> dict[str, Any]:
    """Get full analysis with all issues."""
    response = requests.get(
        f"{API_BASE_URL}/analyses/{analysis_id}",
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json()


def display_sample_issues(detailed_analysis: dict[str, Any], limit: int = 3) -> None:
    """Display sample issues from the analysis."""
    issues = detailed_analysis.get("issues", [])
    
    if not issues:
        print("\n  ✓ No issues found!")
        return
    
    print("\n" + "="*70)
    print(f"SAMPLE ISSUES (showing {min(limit, len(issues))} of {len(issues)})")
    print("="*70)
    
    SEVERITY_EMOJI = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }
    
    for idx, issue in enumerate(issues[:limit], 1):
        severity = issue.get("severity", "medium")
        emoji = SEVERITY_EMOJI.get(severity, "⚪")
        
        print(f"\n{idx}. {emoji} [{severity.upper()}] {issue.get('title', 'Unknown')}")
        print(f"   Type: {issue.get('issue_type', 'other')}")
        print(f"   {issue.get('description', 'No description')}")
        
        metadata = issue.get("metadata", {})
        
        # Show LLM-specific fields
        if metadata.get("current_text"):
            print(f"   ❌ Current: \"{metadata['current_text']}\"")
        
        if metadata.get("suggested_correction"):
            print(f"   ✅ Suggested: \"{metadata['suggested_correction']}\"")
        
        if metadata.get("expected_benefit"):
            print(f"   📈 Benefit: {metadata['expected_benefit']}")
        
        if metadata.get("location"):
            print(f"   📍 Location: {metadata['location']}")


def main():
    """Run complete Step 4 example workflow."""
    print("\n" + "="*70)
    print("STEP 4 EXAMPLE: General Resume Quality Score")
    print("="*70)
    
    # Get resume version ID from user
    resume_version_id = input("\nEnter your resume_version_id: ").strip()
    
    if not resume_version_id:
        print("❌ Error: resume_version_id is required")
        print("\nHint: Upload and parse a resume first (Steps 1-2)")
        return
    
    try:
        # Step 1: Run analysis
        analysis = run_general_quality_analysis(resume_version_id)
        analysis_id = analysis["id"]
        
        # Step 2: Display overall score
        display_overall_score(analysis)
        
        # Step 3: Display content quality assessment (LLM)
        display_content_quality_assessment(analysis)
        
        # Step 4: Display category scores
        display_category_scores(analysis)
        
        # Step 5: Explain a specific category (content_quality)
        print("\n\n[Fetching detailed breakdown for Content Quality category...]")
        explain_category(analysis_id, "content_quality")
        
        # Step 6: Get and display sample issues
        print("\n\n[Fetching detailed issues...]")
        detailed = get_detailed_analysis(analysis_id)
        display_sample_issues(detailed, limit=5)
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"\n✓ Analysis ID: {analysis_id}")
        print(f"✓ Overall Score: {analysis['overall_score']:.1f}/100")
        print(f"✓ Total Issues: {analysis['summary'].get('total_issues', 0)}")
        print(f"\nView full analysis at:")
        print(f"  API: {API_BASE_URL}/analyses/{analysis_id}")
        print(f"  Web: http://localhost:3000/resumes/{resume_version_id}/analysis")
        print("\nTo explain other categories, try:")
        for category in ["parsing_compatibility", "structure", "formatting", "metadata"]:
            print(f"  GET {API_BASE_URL}/analyses/{analysis_id}/explain/{category}")
        
        print("\n" + "="*70)
        print("✓ Step 4 Example Complete!")
        print("="*70)
        
    except requests.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
