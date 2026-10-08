from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from config import Settings, get_settings
from dependencies.auth import CurrentUser, get_current_user
from models.export import ExportJobCreateResponse, ExportJobResponse, ExportRequest, ValidationDetails
from services.export_service import ExportService
from services.supabase_client import create_service_client

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.post("/resumes/{resume_id}/export", response_model=ExportJobCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_export_job(
    resume_id: UUID,
    request: ExportRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ExportJobCreateResponse:
    """
    Create an export job for a resume.
    Generates the file, runs self-check validation, and stores the result.
    """
    client = create_service_client(settings)
    
    # Get resume version
    if request.version_id:
        version_id = str(request.version_id)
    else:
        # Get current version
        resume = client.table("resumes").select("current_version_id").eq("id", str(resume_id)).eq(
            "user_id", current_user.id
        ).single().execute()
        
        if not resume.data or not resume.data.get('current_version_id'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume or current version not found"
            )
        
        version_id = resume.data['current_version_id']
    
    # Verify user owns this version
    version = client.table("resume_versions").select("id").eq("id", version_id).eq(
        "user_id", current_user.id
    ).single().execute()
    
    if not version.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume version not found or access denied"
        )
    
    # Create export job record
    job = client.table("export_jobs").insert({
        "user_id": current_user.id,
        "resume_version_id": version_id,
        "format": request.format,
        "status": "generating",
    }).execute()
    
    job_id = job.data[0]['id']
    
    try:
        # Generate file
        export_service = ExportService(settings)
        
        if request.format == "pdf":
            file_bytes = export_service.generate_pdf(current_user.id, version_id)
            mime_type = "application/pdf"
        else:  # docx
            file_bytes = export_service.generate_docx(current_user.id, version_id)
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        # Update status to validating
        client.table("export_jobs").update({"status": "validating"}).eq("id", job_id).execute()
        
        # Run self-check validation (only for PDF in MVP)
        validation_result = None
        if request.format == "pdf":
            validation_result = export_service.validate_export(file_bytes, version_id, current_user.id)
        else:
            # For DOCX, skip validation in MVP (would require LibreOffice conversion)
            validation_result = {
                "validation_passed": True,
                "fields_checked": 0,
                "fields_recovered": 0,
                "missing_fields": [],
                "parsing_errors": ["DOCX validation skipped in MVP"],
            }
        
        # Store file in storage
        storage_path = f"exports/{current_user.id}/{job_id}.{request.format}"
        client.storage.from_("resumes").upload(
            storage_path,
            file_bytes,
            file_options={"content-type": mime_type}
        )
        
        # Update job with results
        client.table("export_jobs").update({
            "status": "completed",
            "storage_path": storage_path,
            "validation_passed": validation_result['validation_passed'],
            "validation_details": validation_result,
            "file_size_bytes": len(file_bytes),
            "generated_at": "now()",
        }).eq("id", job_id).execute()
        
        return ExportJobCreateResponse(
            job_id=UUID(job_id),
            message="Export completed successfully"
        )
        
    except Exception as e:
        # Update job as failed
        client.table("export_jobs").update({
            "status": "failed",
            "error_message": str(e),
        }).eq("id", job_id).execute()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export generation failed: {str(e)}"
        ) from e


@router.get("/{job_id}", response_model=ExportJobResponse)
async def get_export_job_status(
    job_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ExportJobResponse:
    """Get the status of an export job."""
    client = create_service_client(settings)
    
    job = client.table("export_jobs").select("*").eq("id", str(job_id)).eq(
        "user_id", current_user.id
    ).single().execute()
    
    if not job.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export job not found"
        )
    
    job_data = job.data
    
    # Parse validation details
    validation_details = None
    if job_data.get('validation_details'):
        validation_details = ValidationDetails(**job_data['validation_details'])
    
    return ExportJobResponse(
        id=UUID(job_data['id']),
        status=job_data['status'],
        format=job_data['format'],
        validation_passed=job_data.get('validation_passed'),
        validation_details=validation_details,
        error_message=job_data.get('error_message'),
        created_at=job_data['created_at'],
    )


@router.get("/{job_id}/download")
async def download_export(
    job_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    """
    Download the generated export file.
    Only allows download if validation passed (or was skipped for DOCX).
    """
    client = create_service_client(settings)
    
    job = client.table("export_jobs").select("*").eq("id", str(job_id)).eq(
        "user_id", current_user.id
    ).single().execute()
    
    if not job.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export job not found"
        )
    
    job_data = job.data
    
    # Check if completed
    if job_data['status'] != 'completed':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not ready. Current status: {job_data['status']}"
        )
    
    # Check validation result
    if job_data.get('validation_passed') is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Export failed validation self-check. The generated file does not contain recoverable text. Please contact support."
        )
    
    # Download from storage
    try:
        file_bytes = client.storage.from_("resumes").download(job_data['storage_path'])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        ) from e
    
    # Determine media type
    if job_data['format'] == 'pdf':
        media_type = "application/pdf"
        filename = f"resume_{job_id}.pdf"
    else:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"resume_{job_id}.docx"
    
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(file_bytes)),
        }
    )
