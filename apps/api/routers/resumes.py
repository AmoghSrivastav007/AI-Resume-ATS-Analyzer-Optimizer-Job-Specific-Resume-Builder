from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from config import Settings, get_settings
from dependencies.auth import CurrentUser, get_current_user
from models.resume import ResumeDetailResponse, ResumeUploadResponse
from services.resume_query import get_resume_detail
from services.resume_upload import ResumeUploadService
from services.supabase_client import create_user_client

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    file: UploadFile = File(...),
) -> ResumeUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    content = await file.read()
    service = ResumeUploadService(settings)

    try:
        return await service.upload_resume(current_user, file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload resume: {exc}",
        ) from exc


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    resume_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResumeDetailResponse:
    client = create_user_client(settings, current_user.token)
    try:
        return get_resume_detail(client, current_user.id, str(resume_id))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
