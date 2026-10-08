from pathlib import Path
from typing import Any

import anthropic
from anthropic.types import ToolParam

from config import Settings
from models.job_posting import JobDescriptionExtraction

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "job_description_extraction.txt"

EXTRACT_JD_TOOL: ToolParam = {
    "name": "extract_job_description",
    "description": "Extract structured information from a job description",
    "input_schema": JobDescriptionExtraction.model_json_schema(),
}


def extract_job_description(raw_text: str, settings: Settings) -> JobDescriptionExtraction:
    """
    Extract structured requirements from job description text.
    
    Uses Haiku-class model for fast, cost-effective extraction.
    
    Extracts:
    - Required skills vs preferred skills
    - Responsibilities
    - Education requirements
    - Years of experience
    - Certifications
    - Domain knowledge
    - Competency signals (soft skills)
    
    Args:
        raw_text: Raw job description text
        settings: Application settings
    
    Returns:
        JobDescriptionExtraction with categorized requirements
    
    Raises:
        RuntimeError: If API key missing or extraction fails
    """
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is missing")
    if not settings.anthropic_haiku_model:
        raise RuntimeError("ANTHROPIC_HAIKU_MODEL is missing")

    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    response = client.messages.create(
        model=settings.anthropic_haiku_model,
        max_tokens=4096,
        system=system_prompt,
        tools=[EXTRACT_JD_TOOL],
        tool_choice={"type": "tool", "name": "extract_job_description"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract all requirements from this job description using the extract_job_description tool.\n\n"
                    f"<job_description>\n{raw_text}\n</job_description>"
                ),
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_job_description":
            return JobDescriptionExtraction.model_validate(block.input)

    raise RuntimeError("Anthropic response did not include extract_job_description structured output")


def extract_text_from_file(content: bytes, mime_type: str) -> str:
    """
    Extract plain text from uploaded file (PDF, DOCX, or TXT).
    
    Reuses extraction utilities from Step 2 parser.
    
    Args:
        content: File bytes
        mime_type: MIME type of file
    
    Returns:
        Extracted plain text
    
    Raises:
        ValueError: If file type not supported
    """
    if mime_type == "text/plain":
        return content.decode("utf-8", errors="ignore")
    
    elif mime_type == "application/pdf":
        import fitz
        
        document = fitz.open(stream=content, filetype="pdf")
        try:
            text_parts = []
            for page_index in range(document.page_count):
                page = document.load_page(page_index)
                text = page.get_text("text")
                text_parts.append(text)
            return "\n".join(text_parts)
        finally:
            document.close()
    
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        import io
        from docx import Document
        
        document = Document(io.BytesIO(content))
        text_parts = []
        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)
    
    else:
        raise ValueError(f"Unsupported file type: {mime_type}. Supported: PDF, DOCX, TXT")
