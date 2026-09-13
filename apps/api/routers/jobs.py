from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from rq.job import Job
from rq.exceptions import NoSuchJobError

from config import Settings, get_settings
from dependencies.auth import CurrentUser, get_current_user
from models.resume import JobStatusData, JobStatusResponse
from services.queue import get_redis

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JobStatusResponse:
    try:
        job = Job.fetch(job_id, connection=get_redis(settings))
    except NoSuchJobError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found") from exc

    meta = job.meta or {}
    if meta.get("user_id") and meta["user_id"] != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    result = job.result if job.is_finished else None
    error = None
    needs_ocr = False
    parsed = None
    if isinstance(result, dict):
        error = result.get("error")
        needs_ocr = bool(result.get("needs_ocr"))
        parsed = result.get("parsed")
    elif job.is_failed:
        error = job.exc_info or "Job failed"

    return JobStatusResponse(
        data=JobStatusData(
            id=job.id,
            status=job.get_status() or "queued",
            resume_id=meta.get("resume_id"),
            version_id=meta.get("version_id"),
            error=error,
            needs_ocr=needs_ocr,
            result=parsed,
        )
    )
