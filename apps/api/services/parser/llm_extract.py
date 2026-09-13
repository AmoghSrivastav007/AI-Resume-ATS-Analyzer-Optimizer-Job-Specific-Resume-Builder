from pathlib import Path

import anthropic
from anthropic.types import ToolParam

from config import Settings
from models.extraction import ResumeExtraction

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "resume_extraction.txt"

EXTRACT_RESUME_TOOL: ToolParam = {
    "name": "extract_resume",
    "description": "Return structured resume fields extracted from the provided resume text.",
    "input_schema": ResumeExtraction.model_json_schema(),
}


def extract_resume_with_llm(plain_text: str, settings: Settings) -> ResumeExtraction:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing. Set it in .env — parsing cannot fake LLM output.")
    if not settings.anthropic_haiku_model:
        raise RuntimeError("ANTHROPIC_HAIKU_MODEL is missing. Set the Haiku-class model name in .env.")

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.create(
        model=settings.anthropic_haiku_model,
        max_tokens=4096,
        system=system_prompt,
        tools=[EXTRACT_RESUME_TOOL],
        tool_choice={"type": "tool", "name": "extract_resume"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract the resume using the extract_resume tool.\n\n"
                    f"<resume_text>\n{plain_text}\n</resume_text>"
                ),
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_resume":
            return ResumeExtraction.model_validate(block.input)

    raise RuntimeError("Anthropic response did not include extract_resume structured output")
