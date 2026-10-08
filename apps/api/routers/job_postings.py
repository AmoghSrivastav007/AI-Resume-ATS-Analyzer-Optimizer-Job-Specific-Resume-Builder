from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from config import Settings, get_settings
from dependencies.auth import CurrentUser, get_current_user
from models.job_posting import (
    JobPostingCreateRequest,
    JobPostingDetailResponse,
    JobPostingResponse,
    JobRequirementResponse,
)
from services.audit import write_audit_log
from services.file_validation import validate_file_type
from services.job_posting_extractor import extract_job_description, extract_text_from_file
from services.supabase_client import create_service_client, create_user_client

router = APIRouter(prefix="/api/job-postings", tags=["job_postings"])


@router.post("", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job_posting(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    title: str = Form(...),
    company: str | None = Form(None),
    source_url: str | None = Form(None),
    raw_text: str | None = Form(None),
    file: UploadFile | None = File(None),
) -> JobPostingResponse:
    """
    Create a job posting from pasted text or uploaded file.
    
    Supports:
    - Pasted text (raw_text parameter)
    - Uploaded file (PDF, DOCX, TXT)
    
    Does NOT support:
    - URL scraping (explicitly out of scope per architecture)
    """
    client = create_service_client(settings)
    
    try:
        # Extract text from file or use pasted text
        if file:
            if raw_text:
                raise ValueError("Provide either raw_text or file, not both")
            
            file_content = await file.read()
            validated = validate_file_type(file_content, allowed_extensions=["pdf", "docx", "txt"])
            
            raw_text = extract_text_from_file(file_content, validated.mime_type)
        
        if not raw_text or not raw_text.strip():
            raise ValueError("Job description text is required (via raw_text or file)")
        
        # Extract structured information using LLM
        extraction = extract_job_description(raw_text, settings)
        
        # Create job_posting record
        posting_row = (
            client.table("job_postings")
            .insert({
                "user_id": current_user.id,
                "title": title,
                "company": company or extraction.company,
                "source_url": source_url,
                "raw_text": raw_text,
            })
            .execute()
        )
        
        if not posting_row.data:
            raise RuntimeError("Failed to create job_posting record")
        
        posting = posting_row.data[0]
        posting_id = posting["id"]
        
        # Create job_requirements records
        requirements_to_insert = []
        
        for skill in extraction.required_skills:
            requirements_to_insert.append({
                "user_id": current_user.id,
                "job_posting_id": posting_id,
                "requirement_type": "required_skill",
                "requirement_text": skill,
            })
        
        for skill in extraction.preferred_skills:
            requirements_to_insert.append({
                "user_id": current_user.id,
                "job_posting_id": posting_id,
                "requirement_type": "preferred_skill",
                "requirement_text": skill,
            })
        
        for resp in extraction.responsibilities:
            requirements_to_insert.append({
                "user_id": current_user.id,
                "job_posting_id": posting_id,
                "requirement_type": "responsibility",
                "requirement_text": resp,
            })
        
        for edu in extraction.education:
            requirements_to_insert.append({
                "user_id": current_user.id,
                "job_posting_id": posting_id,
                "requirement_type": "education",
                "requirement_text": edu,
            })
        
        if extraction.experience_years:
            requirements_to_insert.append({
                "user_id": current_user.id,
                "job_posting_id": posting_id,
                "requirement_type": "experience_years",
                "requirement_text": extraction.experience_years,
            })
        
        for cert in extraction.certifications:
            requirements_to_insert.append({
                "user_id": current_user.id,
                "job_posting_id": posting_id,
                "requirement_type": "certification",
                "requirement_text": cert,
            })
        
        for domain in extraction.domain_knowledge:
            requirements_to_insert.append({
                "user_id": current_user.id,
                "job_posting_id": posting_id,
                "requirement_type": "domain_knowledge",
                "requirement_text": domain,
            })
        
        for comp in extraction.competency_signals:
            requirements_to_insert.append({
                "user_id": current_user.id,
                "job_posting_id": posting_id,
                "requirement_type": "competency_signal",
                "requirement_text": comp,
            })
        
        # Bulk insert requirements
        if requirements_to_insert:
            client.table("job_requirements").insert(requirements_to_insert).execute()
        
        # Audit log
        write_audit_log(
            client,
            current_user.id,
            "create",
            "job_postings",
            posting_id,
            {"requirement_count": len(requirements_to_insert)},
        )
        
        return JobPostingResponse(
            id=posting["id"],
            user_id=posting["user_id"],
            title=posting["title"],
            company=posting.get("company"),
            source_url=posting.get("source_url"),
            raw_text=posting["raw_text"],
            created_at=posting["created_at"],
            updated_at=posting["updated_at"],
        )
    
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job posting: {exc}",
        ) from exc


@router.get("/{job_posting_id}", response_model=JobPostingDetailResponse)
async def get_job_posting(
    job_posting_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JobPostingDetailResponse:
    """Get job posting with all extracted requirements."""
    client = create_user_client(settings, current_user.token)
    
    try:
        # Get job posting
        posting_response = (
            client.table("job_postings")
            .select("*")
            .eq("id", str(job_posting_id))
            .eq("user_id", current_user.id)
            .single()
            .execute()
        )
        
        if not posting_response.data:
            raise ValueError("Job posting not found")
        
        posting = posting_response.data
        
        # Get requirements
        requirements_response = (
            client.table("job_requirements")
            .select("*")
            .eq("job_posting_id", str(job_posting_id))
            .eq("user_id", current_user.id)
            .execute()
        )
        
        requirements = requirements_response.data or []
        
        # Build extraction summary
        summary = {
            "total": len(requirements),
            "required_skills": len([r for r in requirements if r["requirement_type"] == "required_skill"]),
            "preferred_skills": len([r for r in requirements if r["requirement_type"] == "preferred_skill"]),
            "responsibilities": len([r for r in requirements if r["requirement_type"] == "responsibility"]),
            "education": len([r for r in requirements if r["requirement_type"] == "education"]),
            "experience_years": len([r for r in requirements if r["requirement_type"] == "experience_years"]),
            "certifications": len([r for r in requirements if r["requirement_type"] == "certification"]),
            "domain_knowledge": len([r for r in requirements if r["requirement_type"] == "domain_knowledge"]),
            "competency_signals": len([r for r in requirements if r["requirement_type"] == "competency_signal"]),
        }
        
        # Audit log
        write_audit_log(
            client,
            current_user.id,
            "read",
            "job_postings",
            str(job_posting_id),
            {},
        )
        
        return JobPostingDetailResponse(
            job_posting=JobPostingResponse(
                id=posting["id"],
                user_id=posting["user_id"],
                title=posting["title"],
                company=posting.get("company"),
                source_url=posting.get("source_url"),
                raw_text=posting["raw_text"],
                created_at=posting["created_at"],
                updated_at=posting["updated_at"],
            ),
            requirements=[
                JobRequirementResponse(
                    id=req["id"],
                    job_posting_id=req["job_posting_id"],
                    requirement_type=req["requirement_type"],
                    requirement_text=req["requirement_text"],
                    category=req.get("category"),
                    created_at=req["created_at"],
                )
                for req in requirements
            ],
            extraction_summary=summary,
        )
    
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job posting: {exc}",
        ) from exc
