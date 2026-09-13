from config import get_settings
from services.parser.pipeline import ResumeParsePipeline


def parse_resume_job(user_id: str, resume_id: str, resume_version_id: str) -> dict:
    settings = get_settings()
    pipeline = ResumeParsePipeline(settings)
    result = pipeline.run(
        user_id=user_id,
        resume_id=resume_id,
        resume_version_id=resume_version_id,
    )
    return {
        "user_id": user_id,
        "resume_id": resume_id,
        "resume_version_id": resume_version_id,
        "status": result.status,
        "needs_ocr": result.needs_ocr,
        "error": result.error,
        "parsed": result.parsed,
    }
