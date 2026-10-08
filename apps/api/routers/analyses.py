from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from config import Settings, get_settings
from dependencies.auth import CurrentUser, get_current_user
from models.analysis import (
    AnalysisCreateRequest,
    AnalysisResponse,
    DetailedAnalysisResponse,
    IssueDetail,
    JobDescriptionCreateRequest,
    JobDescriptionResponse,
    MatchResultDetail,
)
from services.analysis_service import AnalysisService

router = APIRouter(prefix="/api", tags=["analyses"])


# Job Descriptions

@router.post("/job-descriptions", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_description(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    request: JobDescriptionCreateRequest,
) -> JobDescriptionResponse:
    """Create and parse a job description."""
    service = AnalysisService(settings)
    
    try:
        result = service.create_job_description(
            user_id=current_user.id,
            title=request.title,
            raw_text=request.raw_text,
            company=request.company,
            source_url=request.source_url,
        )
        
        return JobDescriptionResponse(
            id=result["id"],
            title=result["title"],
            company=result.get("company"),
            source_url=result.get("source_url"),
            raw_text=request.raw_text,
            requirement_count=result["requirement_count"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job description: {exc}",
        ) from exc


# Analyses

@router.post("/analyses", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
    request: AnalysisCreateRequest,
) -> AnalysisResponse:
    """Run an analysis (ATS or JD match)."""
    service = AnalysisService(settings)
    
    try:
        if request.analysis_type == "ats":
            result = service.run_ats_analysis(
                user_id=current_user.id,
                resume_version_id=str(request.resume_version_id),
            )
        elif request.analysis_type == "jd_match":
            if not request.job_description_id:
                raise ValueError("job_description_id required for jd_match analysis")
            
            result = service.run_jd_match_analysis(
                user_id=current_user.id,
                resume_version_id=str(request.resume_version_id),
                job_description_id=str(request.job_description_id),
            )
        else:
            raise ValueError(f"Unsupported analysis_type: {request.analysis_type}")
        
        return AnalysisResponse(
            id=result["analysis_id"],
            resume_version_id=request.resume_version_id,
            job_description_id=request.job_description_id,
            analysis_type=request.analysis_type,
            status="completed",
            overall_score=result.get("overall_score"),
            summary=result.get("summary", {}),
            match_count=result.get("match_count", 0),
            issue_count=result.get("issue_count", 0),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run analysis: {exc}",
        ) from exc


@router.get("/analyses/{analysis_id}", response_model=DetailedAnalysisResponse)
async def get_analysis(
    analysis_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DetailedAnalysisResponse:
    """Get detailed analysis results."""
    service = AnalysisService(settings)
    
    try:
        data = service.get_analysis(current_user.id, str(analysis_id))
        
        # Map matches
        matches = [
            MatchResultDetail(
                id=m["id"],
                requirement_text=m["requirement_text"],
                requirement_type=m["requirement_type"],
                match_score=float(m["match_score"]),
                match_status=m["match_status"],
                evidence=m["evidence"],
            )
            for m in data.get("match_results") or []
        ]
        
        # Map issues
        issues = [
            IssueDetail(
                id=i["id"],
                issue_type=i["issue_type"],
                severity=i["severity"],
                title=i["title"],
                description=i["description"],
                affected_block_id=i.get("affected_block_id"),
                metadata=i["metadata"],
            )
            for i in data.get("issues") or []
        ]
        
        return DetailedAnalysisResponse(
            analysis=AnalysisResponse(
                id=data["id"],
                resume_version_id=data["resume_version_id"],
                job_description_id=data.get("job_description_id"),
                analysis_type=data["analysis_type"],
                status=data["status"],
                overall_score=float(data["overall_score"]) if data.get("overall_score") else None,
                summary=data["summary"],
                match_count=len(matches),
                issue_count=len(issues),
            ),
            matches=matches,
            issues=issues,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis: {exc}",
        ) from exc


@router.get("/analyses/{analysis_id}/explain/{category}")
async def explain_category(
    analysis_id: UUID,
    category: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Get explainability tree for a specific category."""
    service = AnalysisService(settings)
    
    try:
        data = service.get_analysis(current_user.id, str(analysis_id))
        
        score_breakdown = data.get("score_breakdown", {})
        categories = score_breakdown.get("categories", {})
        
        if category not in categories:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category '{category}' not found in analysis",
            )
        
        category_data = categories[category]
        
        return {
            "analysis_id": str(analysis_id),
            "category": category,
            "overall_score": score_breakdown.get("overall_score"),
            "category_score": category_data,
        }
    
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category explanation: {exc}",
        ) from exc
