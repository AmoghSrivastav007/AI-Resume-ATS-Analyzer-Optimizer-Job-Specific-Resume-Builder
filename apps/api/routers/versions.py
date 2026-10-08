"""
Resume Versions API - Version History Management (Step 8)

Provides version control for resumes:
- List all versions
- View specific version
- Restore previous version
- Duplicate version
- Rename version
- Delete version
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from dependencies.auth import get_current_user
from services.supabase_client import get_supabase_client
from services.version_service import VersionService


router = APIRouter(prefix="/api/versions", tags=["versions"])


class VersionResponse(BaseModel):
    """Response for a single version."""
    id: str
    resume_id: str
    user_id: str
    version_number: int
    status: str
    storage_path: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    needs_ocr: bool
    parse_error: Optional[str]
    created_at: str
    updated_at: str


class VersionListResponse(BaseModel):
    """Response for list of versions."""
    resume_id: str
    resume_title: str
    current_version_id: Optional[str]
    versions: List[VersionResponse]


class RenameVersionRequest(BaseModel):
    """Request to rename a version."""
    title: str = Field(..., description="New title for the resume")


class DuplicateVersionRequest(BaseModel):
    """Request to duplicate a version."""
    new_title: Optional[str] = Field(None, description="Title for the duplicated resume")


@router.get("/resume/{resume_id}", response_model=VersionListResponse)
async def list_versions(
    resume_id: UUID,
    user: dict = Depends(get_current_user)
):
    """
    List all versions for a resume.
    
    Returns versions ordered by version_number descending (newest first).
    """
    try:
        supabase = get_supabase_client()
        
        # Get resume info
        resume_response = supabase.table("resumes").select(
            "id, title, current_version_id"
        ).eq("id", str(resume_id)).eq("user_id", user["id"]).execute()
        
        if not resume_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        resume = resume_response.data[0]
        
        # Get all versions
        versions_response = supabase.table("resume_versions").select(
            "*"
        ).eq("resume_id", str(resume_id)).eq(
            "user_id", user["id"]
        ).order("version_number", desc=True).execute()
        
        return VersionListResponse(
            resume_id=resume["id"],
            resume_title=resume["title"],
            current_version_id=resume.get("current_version_id"),
            versions=[VersionResponse(**v) for v in versions_response.data]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error listing versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list versions: {str(e)}"
        )


@router.get("/{version_id}", response_model=VersionResponse)
async def get_version(
    version_id: UUID,
    user: dict = Depends(get_current_user)
):
    """Get a specific version by ID."""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table("resume_versions").select(
            "*"
        ).eq("id", str(version_id)).eq("user_id", user["id"]).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        return VersionResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version: {str(e)}"
        )


@router.post("/{version_id}/restore", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def restore_version(
    version_id: UUID,
    user: dict = Depends(get_current_user)
):
    """
    Restore a previous version.
    
    Creates a new version with the content from the specified version.
    Sets it as the current version for the resume.
    """
    try:
        supabase = get_supabase_client()
        service = VersionService(supabase)
        
        # Verify version ownership
        version_response = supabase.table("resume_versions").select(
            "*"
        ).eq("id", str(version_id)).eq("user_id", user["id"]).execute()
        
        if not version_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Restore version
        result = await service.restore_version(
            version_id=str(version_id),
            user_id=user["id"]
        )
        
        return VersionResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error restoring version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore version: {str(e)}"
        )


@router.post("/{version_id}/duplicate", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_version(
    version_id: UUID,
    request: DuplicateVersionRequest,
    user: dict = Depends(get_current_user)
):
    """
    Duplicate a version as a new resume.
    
    Creates a new resume with the content from the specified version.
    Useful for creating variations (e.g., "Software Engineer Resume", "Data Analyst Resume").
    """
    try:
        supabase = get_supabase_client()
        service = VersionService(supabase)
        
        # Verify version ownership
        version_response = supabase.table("resume_versions").select(
            "*"
        ).eq("id", str(version_id)).eq("user_id", user["id"]).execute()
        
        if not version_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        # Duplicate version
        result = await service.duplicate_version(
            version_id=str(version_id),
            new_title=request.new_title,
            user_id=user["id"]
        )
        
        return VersionResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error duplicating version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate version: {str(e)}"
        )


@router.patch("/{version_id}/rename", response_model=VersionResponse)
async def rename_version(
    version_id: UUID,
    request: RenameVersionRequest,
    user: dict = Depends(get_current_user)
):
    """
    Rename a resume (via its version).
    
    Updates the title of the parent resume.
    """
    try:
        supabase = get_supabase_client()
        
        # Verify version ownership
        version_response = supabase.table("resume_versions").select(
            "id, resume_id"
        ).eq("id", str(version_id)).eq("user_id", user["id"]).execute()
        
        if not version_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        version = version_response.data[0]
        resume_id = version["resume_id"]
        
        # Update resume title
        supabase.table("resumes").update({
            "title": request.title,
            "updated_at": "now()"
        }).eq("id", resume_id).eq("user_id", user["id"]).execute()
        
        # Return updated version
        updated_version = supabase.table("resume_versions").select(
            "*"
        ).eq("id", str(version_id)).execute()
        
        return VersionResponse(**updated_version.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error renaming version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rename version: {str(e)}"
        )


@router.delete("/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    version_id: UUID,
    user: dict = Depends(get_current_user)
):
    """
    Delete a version.
    
    Cannot delete the current version of a resume.
    If this is the only version, the entire resume will be deleted.
    """
    try:
        supabase = get_supabase_client()
        
        # Verify version ownership
        version_response = supabase.table("resume_versions").select(
            "id, resume_id"
        ).eq("id", str(version_id)).eq("user_id", user["id"]).execute()
        
        if not version_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        version = version_response.data[0]
        resume_id = version["resume_id"]
        
        # Check if this is the current version
        resume_response = supabase.table("resumes").select(
            "current_version_id"
        ).eq("id", resume_id).execute()
        
        if resume_response.data and resume_response.data[0]["current_version_id"] == str(version_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the current version. Please set a different version as current first."
            )
        
        # Delete version (CASCADE will handle related records)
        supabase.table("resume_versions").delete().eq(
            "id", str(version_id)
        ).eq("user_id", user["id"]).execute()
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete version: {str(e)}"
        )
