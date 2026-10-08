from typing import Any

import anthropic
from anthropic.types import ToolParam
from pydantic import BaseModel, Field

from config import Settings


class JobRequirement(BaseModel):
    requirement_text: str
    requirement_type: str  # required | preferred | nice_to_have
    category: str | None = None  # skill | experience | education | certification


class ParsedJobDescription(BaseModel):
    requirements: list[JobRequirement] = Field(default_factory=list)
    key_skills: list[str] = Field(default_factory=list)
    years_experience: int | None = None
    education_level: str | None = None
    summary: str | None = None


PARSE_JD_TOOL: ToolParam = {
    "name": "parse_job_description",
    "description": "Extract structured requirements and key information from a job description",
    "input_schema": ParsedJobDescription.model_json_schema(),
}

SYSTEM_PROMPT = """You are parsing job descriptions to extract structured requirements.

Rules:
- Extract requirements as granular, actionable items (e.g., "5+ years Python", "Bachelor's degree", "AWS certification")
- Classify each requirement as "required", "preferred", or "nice_to_have" based on language cues:
  - Required: "must have", "required", "essential"
  - Preferred: "preferred", "desired", "ideally", "strong plus"
  - Nice to have: "nice to have", "bonus", "plus"
- When in doubt, mark as "required" rather than "preferred"
- Extract key_skills as a flat list of specific technologies, tools, and competencies
- Parse years_experience if explicitly stated (e.g., "5+ years")
- Parse education_level if explicitly stated (e.g., "Bachelor's degree", "Master's preferred")
- Provide a brief summary of the role in 1-2 sentences
"""


def parse_job_description(raw_text: str, settings: Settings) -> ParsedJobDescription:
    """Parse a job description using LLM structured extraction."""
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing")
    if not settings.anthropic_haiku_model:
        raise RuntimeError("ANTHROPIC_HAIKU_MODEL is missing")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.create(
        model=settings.anthropic_haiku_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[PARSE_JD_TOOL],
        tool_choice={"type": "tool", "name": "parse_job_description"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Parse this job description using the parse_job_description tool.\n\n"
                    f"<job_description>\n{raw_text}\n</job_description>"
                ),
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "parse_job_description":
            return ParsedJobDescription.model_validate(block.input)

    raise RuntimeError("Anthropic response did not include parse_job_description structured output")
