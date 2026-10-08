"""
Pydantic models for matching (Step 6).
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    """Single match result for a job requirement."""
    requirement_id: str
    requirement_text: str
    requirement_type: str
    match_status: str  # matched, partially_matched, missing, weak_evidence, not_relevant
    match_layer: int  # 1-4
    match_score: float  # 0-100
    evidence_block_id: Optional[str] = None
    evidence_text: Optional[str] = None
    similarity_score: Optional[float] = None
    recommendation: Optional[str] = None


class CategoryScore(BaseModel):
    """Score for a single category."""
    weight: int  # Percentage weight
    score: float  # 0-100
    contribution: float  # Weighted contribution to overall
    details: Dict[str, Any]


class MatchBreakdown(BaseModel):
    """Explainability tree for JD Match Score."""
    overall_score: float
    categories: Dict[str, CategoryScore]


class GapItem(BaseModel):
    """Single gap in requirements."""
    requirement: str
    type: str
    recommendation: str


class GapAnalysis(BaseModel):
    """Gap analysis summary."""
    total_gaps: int
    critical_gaps: int
    gaps: Dict[str, List[GapItem]]


class JDMatchAnalysis(BaseModel):
    """Complete JD match analysis."""
    analysis_id: str
    resume_version_id: str
    job_posting_id: str
    jd_match_score: float
    keyword_relevance: float
    skills_alignment: float
    experience_relevance: float
    match_breakdown: MatchBreakdown
    gap_analysis: GapAnalysis
    total_requirements: int
    matched: int
    partially_matched: int
    missing: int
    weak_evidence: int
    match_results: List[MatchResult]


class MatchSummary(BaseModel):
    """Summary of match results."""
    total: int
    matched: int
    partially_matched: int
    weak_evidence: int
    missing: int
    not_relevant: int


class GroupedMatchResults(BaseModel):
    """Match results grouped by status."""
    matched: List[Dict[str, Any]]
    partially_matched: List[Dict[str, Any]]
    weak_evidence: List[Dict[str, Any]]
    missing: List[Dict[str, Any]]
    not_relevant: List[Dict[str, Any]]


class MatchResultsResponse(BaseModel):
    """Response with complete match results."""
    analysis: Dict[str, Any]
    match_results: List[Dict[str, Any]]
    grouped_matches: GroupedMatchResults
    summary: MatchSummary
