"""
Matching API endpoints (Step 6).

Endpoints:
- POST /api/match - Run matching analysis
- GET /api/match/:analysis_id/results - Get match results
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from dependencies.auth import get_current_user
from services.supabase_client import get_supabase_client
from services.matching_service import MatchingService


router = APIRouter(prefix="/match", tags=["matching"])


class MatchRequest(BaseModel):
    """Request to run matching analysis."""
    resume_version_id: str = Field(..., description="Resume version ID")
    job_posting_id: str = Field(..., description="Job posting ID")


class MatchResponse(BaseModel):
    """Response from matching analysis."""
    analysis_id: str
    resume_version_id: str
    job_posting_id: str
    jd_match_score: float
    keyword_relevance: float
    skills_alignment: float
    experience_relevance: float
    match_breakdown: Dict[str, Any]
    gap_analysis: Dict[str, Any]
    total_requirements: int
    matched: int
    partially_matched: int
    missing: int
    weak_evidence: int


@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def run_matching_analysis(
    request: MatchRequest,
    user: dict = Depends(get_current_user)
):
    """
    Run matching analysis between a resume and job posting.
    
    This triggers the complete 4-layer matching pipeline:
    1. Ensure embeddings exist for skills and requirements
    2. Run 4-layer matching (exact, alias, semantic, context)
    3. Calculate JD Match Score
    4. Persist results to match_results table
    
    Returns analysis with match breakdown and gap analysis.
    """
    try:
        supabase = get_supabase_client()
        service = MatchingService(supabase)
        
        # Verify resume version exists and belongs to user
        resume_response = supabase.table("resume_versions").select(
            "id"
        ).eq("id", request.resume_version_id).eq("user_id", user["id"]).execute()
        
        if not resume_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found"
            )
        
        # Verify job posting exists and belongs to user
        job_response = supabase.table("job_postings").select(
            "id"
        ).eq("id", request.job_posting_id).eq("user_id", user["id"]).execute()
        
        if not job_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        # Run matching analysis
        result = await service.run_matching_analysis(
            resume_version_id=request.resume_version_id,
            job_posting_id=request.job_posting_id,
            user_id=user["id"]
        )
        
        return MatchResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error running matching analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run matching analysis: {str(e)}"
        )


@router.get("/{analysis_id}/results")
async def get_match_results(
    analysis_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get match results for a completed analysis.
    
    Returns:
    - Analysis summary
    - All match results grouped by status
    - Detailed evidence and recommendations
    """
    try:
        supabase = get_supabase_client()
        service = MatchingService(supabase)
        
        result = await service.get_match_results(analysis_id, user["id"])
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error getting match results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get match results: {str(e)}"
        )


@router.get("/{analysis_id}/gaps")
async def get_gap_analysis(
    analysis_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get gap analysis for a completed analysis.
    
    Returns missing requirements grouped by criticality:
    - critical: Missing required skills
    - important: Missing preferred skills/certifications
    - needs_improvement: Weak evidence for requirements
    """
    try:
        supabase = get_supabase_client()
        
        # Fetch analysis
        analysis_response = supabase.table("resume_analyses").select(
            "summary"
        ).eq("id", analysis_id).eq("user_id", user["id"]).single().execute()
        
        if not analysis_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        summary = analysis_response.data.get("summary", {})
        gap_analysis = summary.get("gap_analysis", {})
        
        return gap_analysis
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting gap analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gap analysis: {str(e)}"
        )
