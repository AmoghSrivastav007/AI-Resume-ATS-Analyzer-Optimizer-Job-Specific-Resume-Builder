"""
Optimization API endpoints (Step 7 - Truth Guard).

Endpoints:
- POST /api/optimize - Generate optimizations with Truth Guard
- GET /api/optimizations/:resume_version_id - List optimizations
- POST /api/optimizations/:id/apply - Apply optimization
- POST /api/optimizations/:id/reject - Reject optimization
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from dependencies.auth import get_current_user
from services.supabase_client import get_supabase_client
from services.optimization_service import OptimizationService


router = APIRouter(prefix="/optimize", tags=["optimize"])


class OptimizeRequest(BaseModel):
    """Request to generate optimizations."""
    resume_version_id: str = Field(..., description="Resume version ID")
    job_posting_id: str = Field(..., description="Job posting ID")


class OptimizationResponse(BaseModel):
    """Response from optimization generation."""
    resume_version_id: str
    job_posting_id: str
    total_generated: int
    stored: int
    auto_rejected: int
    supported: int
    partially_supported: int


@router.post("/", response_model=OptimizationResponse, status_code=status.HTTP_201_CREATED)
async def generate_optimizations(
    request: OptimizeRequest,
    user: dict = Depends(get_current_user)
):
    """
    Generate resume optimizations with Truth Guard pipeline.
    
    Truth Guard 5-step process:
    1. Fetch fact ledger (populated in Step 2)
    2. Generate with Sonnet (fact traceability required)
    3. Verify with Haiku (independent model, no generator context)
    4. Check deterministic guardrails (hard blocks)
    5. Assign status:
       - SUPPORTED + guardrails passed = 'supported' (auto-approved)
       - PARTIALLY_SUPPORTED = 'partially_supported' (requires confirmation)
       - UNSUPPORTED or guardrails failed = auto-rejected, logged
    
    Zero tolerance for hallucinations.
    """
    try:
        supabase = get_supabase_client()
        service = OptimizationService(supabase)
        
        # Verify resume version exists
        resume_response = supabase.table("resume_versions").select(
            "id"
        ).eq("id", request.resume_version_id).eq("user_id", user["id"]).execute()
        
        if not resume_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume version not found"
            )
        
        # Verify job posting exists
        job_response = supabase.table("job_postings").select(
            "id"
        ).eq("id", request.job_posting_id).eq("user_id", user["id"]).execute()
        
        if not job_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job posting not found"
            )
        
        # Generate optimizations with Truth Guard
        result = await service.generate_optimizations(
            resume_version_id=request.resume_version_id,
            job_posting_id=request.job_posting_id,
            user_id=user["id"]
        )
        
        return OptimizationResponse(
            resume_version_id=result["resume_version_id"],
            job_posting_id=result["job_posting_id"],
            total_generated=result["total_generated"],
            stored=result["stored"],
            auto_rejected=result["auto_rejected"],
            supported=result["supported"],
            partially_supported=result["partially_supported"]
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating optimizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate optimizations: {str(e)}"
        )


@router.get("/{resume_version_id}")
async def get_optimizations(
    resume_version_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get all proposed optimizations for a resume.
    
    Returns optimizations grouped by verification status:
    - supported: Auto-approved, can apply immediately
    - partially_supported: Requires user confirmation (see warning)
    """
    try:
        supabase = get_supabase_client()
        service = OptimizationService(supabase)
        
        optimizations = await service.get_optimizations(resume_version_id, user["id"])
        
        # Group by verification status
        grouped = {
            "supported": [],
            "partially_supported": []
        }
        
        for opt in optimizations:
            proposed_content = opt.get("proposed_content", {})
            verification_status = proposed_content.get("verification_status", "unknown")
            
            if verification_status in grouped:
                grouped[verification_status].append(opt)
        
        return {
            "resume_version_id": resume_version_id,
            "total": len(optimizations),
            "grouped": grouped,
            "summary": {
                "supported": len(grouped["supported"]),
                "partially_supported": len(grouped["partially_supported"])
            }
        }
    
    except Exception as e:
        print(f"Error getting optimizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get optimizations: {str(e)}"
        )


@router.post("/{optimization_id}/apply")
async def apply_optimization(
    optimization_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Apply an optimization (user accepted).
    
    For partially_supported optimizations, this means the user confirmed
    they have genuine experience with the claim.
    """
    try:
        supabase = get_supabase_client()
        service = OptimizationService(supabase)
        
        result = await service.apply_optimization(optimization_id, user["id"])
        
        return {
            "optimization_id": optimization_id,
            "status": "applied",
            "applied_at": result.get("applied_at")
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error applying optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply optimization: {str(e)}"
        )


@router.post("/{optimization_id}/reject")
async def reject_optimization(
    optimization_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Reject an optimization (user declined).
    """
    try:
        supabase = get_supabase_client()
        service = OptimizationService(supabase)
        
        result = await service.reject_optimization(optimization_id, user["id"])
        
        return {
            "optimization_id": optimization_id,
            "status": "rejected"
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        print(f"Error rejecting optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject optimization: {str(e)}"
        )
