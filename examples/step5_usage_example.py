"""
Example usage of Step 5 - Job Description Analyzer

This script demonstrates:
1. Creating a job posting from pasted text
2. Creating a job posting from uploaded file
3. Viewing extracted requirements by category
4. Understanding the 8 requirement types

Prerequisites:
- API server running on http://localhost:8000
- Valid authentication token
- ANTHROPIC_HAIKU_MODEL configured
"""

import requests
from typing import Any

# Configuration
API_BASE_URL = "http://localhost:8000/api"
AUTH_TOKEN = "your_jwt_token_here"  # Replace with actual token

HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
}

# Sample job description
SAMPLE_JOB_DESCRIPTION = """
Senior Backend Engineer - TechCorp

We are seeking a talented Senior Backend Engineer to join our growing team.

Required Skills:
- 5+ years of professional software development experience
- Strong proficiency in Python and Django framework
- Experience with PostgreSQL or other relational databases
- RESTful API design and development
- Git version control

Preferred Skills:
- Experience with AWS or other cloud platforms
- Knowledge of Redis and caching strategies
- Docker and container orchestration
- CI/CD pipeline experience

Responsibilities:
- Design and implement scalable backend services
- Write clean, maintainable, and well-tested code
- Participate in code reviews and architectural discussions
- Mentor junior engineers
- Collaborate with frontend and mobile teams

Requirements:
- Bachelor's degree in Computer Science or related field (or equivalent experience)
- Strong problem-solving and analytical thinking skills
- Excellent communication and stakeholder management
- Ability to work independently and in a team environment

Nice to have:
- AWS Certified Solutions Architect certification
- Experience in e-commerce or fintech domains
- Previous experience with microservices architecture
"""


def create_job_posting_from_text() -> str:
    """Create a job posting from pasted text."""
    print("\n" + "="*70)
    print("CREATING JOB POSTING FROM TEXT")
    print("="*70)
    
    data = {
        "title": "Senior Backend Engineer",
        "company": "TechCorp Inc.",
        "source_url": "https://techcorp.com/careers/senior-backend-engineer",
        "raw_text": SAMPLE_JOB_DESCRIPTION,
    }
    
    response = requests.post(
        f"{API_BASE_URL}/job-postings",
        headers=HEADERS,
        data=data,
    )
    response.raise_for_status()
    
    result = response.json()
    job_id = result["id"]
    
    print(f"\n✓ Job posting created successfully!")
    print(f"  ID: {job_id}")
    print(f"  Title: {result['title']}")
    print(f"  Company: {result['company']}")
    
    return job_id


def create_job_posting_from_file(file_path: str) -> str:
    """Create a job posting from uploaded file."""
    print("\n" + "="*70)
    print("CREATING JOB POSTING FROM FILE")
    print("="*70)
    
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f)}
        data = {
            "title": "Senior Backend Engineer",
            "company": "TechCorp Inc.",
        }
        
        response = requests.post(
            f"{API_BASE_URL}/job-postings",
            headers=HEADERS,
            data=data,
            files=files,
        )
        response.raise_for_status()
    
    result = response.json()
    job_id = result["id"]
    
    print(f"\n✓ Job posting created from file!")
    print(f"  ID: {job_id}")
    print(f"  File: {file_path}")
    
    return job_id


def get_job_posting_detail(job_id: str) -> dict[str, Any]:
    """Get job posting with extracted requirements."""
    print("\n" + "="*70)
    print("FETCHING EXTRACTED REQUIREMENTS")
    print("="*70)
    
    response = requests.get(
        f"{API_BASE_URL}/job-postings/{job_id}",
        headers=HEADERS,
    )
    response.raise_for_status()
    
    return response.json()


def display_extraction_summary(detail: dict[str, Any]) -> None:
    """Display extraction summary."""
    summary = detail["extraction_summary"]
    
    print("\n" + "="*70)
    print("EXTRACTION SUMMARY")
    print("="*70)
    
    print(f"\n  Total Requirements: {summary['total']}")
    print(f"\n  Breakdown:")
    print(f"    🔴 Required Skills: {summary['required_skills']}")
    print(f"    🟡 Preferred Skills: {summary['preferred_skills']}")
    print(f"    📋 Responsibilities: {summary['responsibilities']}")
    print(f"    🎓 Education: {summary['education']}")
    print(f"    📅 Experience: {summary['experience_years']}")
    print(f"    🏆 Certifications: {summary['certifications']}")
    print(f"    🏢 Domain Knowledge: {summary['domain_knowledge']}")
    print(f"    💡 Competency Signals: {summary['competency_signals']}")


def display_requirements_by_category(detail: dict[str, Any]) -> None:
    """Display requirements grouped by category."""
    print("\n" + "="*70)
    print("EXTRACTED REQUIREMENTS BY CATEGORY")
    print("="*70)
    
    requirements = detail["requirements"]
    
    # Group by type
    grouped: dict[str, list[dict]] = {}
    for req in requirements:
        req_type = req["requirement_type"]
        if req_type not in grouped:
            grouped[req_type] = []
        grouped[req_type].append(req)
    
    # Display each category
    category_labels = {
        "required_skill": ("🔴 REQUIRED SKILLS", "critical for the role"),
        "preferred_skill": ("🟡 PREFERRED SKILLS", "nice to have, not essential"),
        "responsibility": ("📋 RESPONSIBILITIES", "what you'll be doing"),
        "education": ("🎓 EDUCATION", "degree requirements"),
        "experience_years": ("📅 EXPERIENCE", "years of experience needed"),
        "certification": ("🏆 CERTIFICATIONS", "professional certifications"),
        "domain_knowledge": ("🏢 DOMAIN KNOWLEDGE", "industry/business context"),
        "competency_signal": ("💡 COMPETENCY SIGNALS", "soft skills and behaviors"),
    }
    
    for req_type, (label, description) in category_labels.items():
        items = grouped.get(req_type, [])
        if not items:
            continue
        
        print(f"\n{label}")
        print(f"  ({description})")
        print()
        
        for item in items:
            print(f"    • {item['requirement_text']}")


def analyze_matching_potential(detail: dict[str, Any]) -> None:
    """Analyze matching potential for this JD."""
    print("\n" + "="*70)
    print("MATCHING ANALYSIS (Preview for Step 6)")
    print("="*70)
    
    summary = detail["extraction_summary"]
    requirements = detail["requirements"]
    
    required_skills = [
        r["requirement_text"]
        for r in requirements
        if r["requirement_type"] == "required_skill"
    ]
    
    preferred_skills = [
        r["requirement_text"]
        for r in requirements
        if r["requirement_type"] == "preferred_skill"
    ]
    
    print(f"\n  To match this job, a resume should have:")
    print(f"\n  Critical (Required):")
    for skill in required_skills[:5]:  # Show first 5
        print(f"    ✓ {skill}")
    if len(required_skills) > 5:
        print(f"    ... and {len(required_skills) - 5} more")
    
    print(f"\n  Bonus (Preferred):")
    for skill in preferred_skills[:5]:  # Show first 5
        print(f"    + {skill}")
    if len(preferred_skills) > 5:
        print(f"    ... and {len(preferred_skills) - 5} more")
    
    print(f"\n  Matching score will be calculated in Step 6 based on:")
    print(f"    - Keyword coverage (required vs preferred)")
    print(f"    - Experience match")
    print(f"    - Education match")
    print(f"    - Domain knowledge relevance")
    print(f"    - Competency signal alignment")


def main():
    """Run complete Step 5 example workflow."""
    print("\n" + "="*70)
    print("STEP 5 EXAMPLE: Job Description Analyzer")
    print("="*70)
    
    try:
        # Method 1: Create from pasted text
        print("\nMETHOD 1: Paste Text")
        job_id = create_job_posting_from_text()
        
        # Get and display extraction
        detail = get_job_posting_detail(job_id)
        display_extraction_summary(detail)
        display_requirements_by_category(detail)
        analyze_matching_potential(detail)
        
        # Method 2: Create from file (optional)
        print("\n\n" + "="*70)
        print("\nMETHOD 2: Upload File (Optional)")
        print("="*70)
        print("\nTo test file upload:")
        print("  1. Save a job description to a file (PDF, DOCX, or TXT)")
        print("  2. Uncomment the file upload section in the code")
        print("  3. Update the file path")
        print("  4. Run again")
        
        # Uncomment to test file upload:
        # file_job_id = create_job_posting_from_file("path/to/job_description.txt")
        # file_detail = get_job_posting_detail(file_job_id)
        # display_extraction_summary(file_detail)
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"\n✓ Job posting created: {job_id}")
        print(f"✓ Requirements extracted: {detail['extraction_summary']['total']} total")
        print(f"\nView in browser:")
        print(f"  http://localhost:3000/jobs/{job_id}")
        print(f"\nAPI endpoint:")
        print(f"  GET {API_BASE_URL}/job-postings/{job_id}")
        
        print("\n" + "="*70)
        print("✓ Step 5 Example Complete!")
        print("="*70)
        print("\nNext: Step 6 will match resumes against this job posting")
        
    except requests.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        if e.response is not None:
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
