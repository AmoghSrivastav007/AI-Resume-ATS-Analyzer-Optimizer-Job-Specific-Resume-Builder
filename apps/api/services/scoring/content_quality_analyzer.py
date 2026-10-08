from pathlib import Path
from typing import Any

import anthropic
from anthropic.types import ToolParam

from config import Settings
from models.quality_issue import ContentQualityAnalysis

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "content_quality.txt"

ANALYZE_CONTENT_TOOL: ToolParam = {
    "name": "analyze_content_quality",
    "description": "Return structured content quality issues found in the resume",
    "input_schema": ContentQualityAnalysis.model_json_schema(),
}


def analyze_content_quality(resume_data: dict[str, Any], settings: Settings) -> ContentQualityAnalysis:
    """
    Analyze resume content quality using LLM (Sonnet-class model).
    
    Evaluates:
    - Weak action verbs
    - Vague statements
    - Unsupported claims
    - Missing metrics
    - Grammar/spelling issues
    
    Returns structured issues matching the Issue schema.
    """
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing")
    if not settings.anthropic_sonnet_model:
        raise RuntimeError("ANTHROPIC_SONNET_MODEL is missing")

    # Build resume text for analysis
    resume_text = _build_resume_text(resume_data)
    
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.create(
        model=settings.anthropic_sonnet_model,
        max_tokens=8192,
        system=system_prompt,
        tools=[ANALYZE_CONTENT_TOOL],
        tool_choice={"type": "tool", "name": "analyze_content_quality"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyze this resume's content quality using the analyze_content_quality tool.\n\n"
                    f"<resume>\n{resume_text}\n</resume>"
                ),
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "analyze_content_quality":
            return ContentQualityAnalysis.model_validate(block.input)

    raise RuntimeError("Anthropic response did not include analyze_content_quality structured output")


def _build_resume_text(resume_data: dict[str, Any]) -> str:
    """Build formatted resume text for LLM analysis."""
    extraction = resume_data.get("extraction", {})
    parts = []
    
    # Contact
    contact = extraction.get("contact", {})
    if contact:
        parts.append("=== CONTACT ===")
        if contact.get("full_name"):
            parts.append(f"Name: {contact['full_name']}")
        if contact.get("email"):
            parts.append(f"Email: {contact['email']}")
        if contact.get("phone"):
            parts.append(f"Phone: {contact['phone']}")
        parts.append("")
    
    # Summary
    summary = extraction.get("summary")
    if summary:
        parts.append("=== SUMMARY ===")
        parts.append(summary)
        parts.append("")
    
    # Work Experience
    work_exp = extraction.get("work_experience", [])
    if work_exp:
        parts.append("=== WORK EXPERIENCE ===")
        for idx, exp in enumerate(work_exp):
            parts.append(f"\n{exp.get('title', 'Unknown Role')} at {exp.get('company', 'Unknown Company')}")
            if exp.get("start_date") or exp.get("end_date"):
                dates = f"{exp.get('start_date', '')} - {exp.get('end_date') or 'Present'}"
                parts.append(dates)
            if exp.get("description"):
                parts.append(exp["description"])
            bullets = exp.get("bullets", [])
            for bullet in bullets:
                parts.append(f"• {bullet}")
        parts.append("")
    
    # Education
    education = extraction.get("education", [])
    if education:
        parts.append("=== EDUCATION ===")
        for edu in education:
            degree_line = f"{edu.get('degree', '')} {edu.get('field_of_study', '')}".strip()
            institution = edu.get("institution", "")
            if degree_line:
                parts.append(f"{degree_line} - {institution}")
            elif institution:
                parts.append(institution)
            if edu.get("gpa"):
                parts.append(f"GPA: {edu['gpa']}")
        parts.append("")
    
    # Skills
    skills = extraction.get("skills", [])
    if skills:
        parts.append("=== SKILLS ===")
        skill_names = [s.get("name", "") for s in skills if s.get("name")]
        parts.append(", ".join(skill_names))
        parts.append("")
    
    # Certifications
    certifications = extraction.get("certifications", [])
    if certifications:
        parts.append("=== CERTIFICATIONS ===")
        for cert in certifications:
            cert_line = cert.get("name", "")
            issuer = cert.get("issuer")
            if issuer:
                cert_line += f" - {issuer}"
            parts.append(cert_line)
        parts.append("")
    
    # Projects
    projects = extraction.get("projects", [])
    if projects:
        parts.append("=== PROJECTS ===")
        for proj in projects:
            parts.append(f"\n{proj.get('name', 'Unnamed Project')}")
            if proj.get("description"):
                parts.append(proj["description"])
            techs = proj.get("technologies", [])
            if techs:
                parts.append(f"Technologies: {', '.join(techs)}")
        parts.append("")
    
    return "\n".join(parts)
