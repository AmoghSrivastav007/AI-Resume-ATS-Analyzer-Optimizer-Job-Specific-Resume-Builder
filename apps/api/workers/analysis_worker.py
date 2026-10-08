"""
Worker for running resume analyses asynchronously.

Usage:
    rq worker analysis --url redis://localhost:6379/0
"""
from typing import Any

from config import get_settings
from services.analysis_service import AnalysisService


def run_ats_analysis(user_id: str, resume_version_id: str) -> dict[str, Any]:
    """Background job: Run ATS analysis."""
    settings = get_settings()
    service = AnalysisService(settings)
    return service.run_ats_analysis(user_id, resume_version_id)


def run_jd_match_analysis(
    user_id: str,
    resume_version_id: str,
    job_description_id: str,
) -> dict[str, Any]:
    """Background job: Run JD match analysis."""
    settings = get_settings()
    service = AnalysisService(settings)
    return service.run_jd_match_analysis(user_id, resume_version_id, job_description_id)
