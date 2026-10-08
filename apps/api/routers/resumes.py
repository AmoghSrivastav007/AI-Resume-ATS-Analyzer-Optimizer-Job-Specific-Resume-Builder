from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from config import Settings, get_settings
from dependencies.auth import CurrentUser, get_current_user
from middleware.rate_limit import limiter, HIGH_COST_LIMIT, LOW_COST_LIMIT
from models.resume import ResumeDetailResponse, ResumeUploadResponse
from services.audit import write_audit_log
from services.deletion_service import DeletionService
from services.resume_query import get_resume_detail
from services.resume_upload import ResumeUploadService
from services.supabase_client import create_user_client, create_service_client

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(HIGH_COST_LIMIT)  # 5/minute for uploads
async def upload_resume(
    request: Request,
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
@limiter.limit(LOW_COST_LIMIT)  # 100/minute for reads
async def get_resume(
    request: Request,
    resume_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResumeDetailResponse:
    client = create_user_client(settings, current_user.token)
    
    # Audit log for PII access
    service_client = create_service_client(settings)
    write_audit_log(
        service_client,
        user_id=current_user.id,
        action="read",
        resource_type="resume",
        resource_id=str(resume_id),
        metadata={
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "endpoint": str(request.url.path),
        }
    )
    
    try:
        return get_resume_detail(client, current_user.id, str(resume_id))
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    request: Request,
) -> None:
    """
    Permanently delete a resume and all associated data.
    
    This is a HARD DELETE that removes:
    - Resume record
    - All versions
    - All sections and blocks
    - All analyses
    - All storage files
    
    This operation cannot be undone.
    """
    deletion_service = DeletionService(settings)
    
    try:
        await deletion_service.delete_resume_completely(
            user_id=current_user.id,
            resume_id=str(resume_id),
            ip_address=request.client.host if request.client else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resume: {exc}",
        ) from exc
