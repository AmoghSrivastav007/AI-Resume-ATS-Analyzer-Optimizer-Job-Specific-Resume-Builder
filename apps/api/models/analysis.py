from pydantic import BaseModel, Field
from uuid import UUID


class JobDescriptionCreateRequest(BaseModel):
    title: str
    company: str | None = None
    source_url: str | None = None
    raw_text: str


class JobDescriptionResponse(BaseModel):
    id: UUID
    title: str
    company: str | None
    source_url: str | None
    raw_text: str
    requirement_count: int = 0


class AnalysisCreateRequest(BaseModel):
    resume_version_id: UUID
    job_description_id: UUID | None = None
    analysis_type: str = "ats"  # ats | jd_match | full


class AnalysisResponse(BaseModel):
    id: UUID
    resume_version_id: UUID
    job_description_id: UUID | None
    analysis_type: str
    status: str
    overall_score: float | None
    summary: dict
    match_count: int = 0
    issue_count: int = 0


class MatchResultDetail(BaseModel):
    id: UUID
    requirement_text: str
    requirement_type: str
    match_score: float
    match_status: str
    evidence: dict


class IssueDetail(BaseModel):
    id: UUID
    issue_type: str
    severity: str
    title: str
    description: str
    affected_block_id: UUID | None
    metadata: dict


class DetailedAnalysisResponse(BaseModel):
    analysis: AnalysisResponse
    matches: list[MatchResultDetail] = Field(default_factory=list)
    issues: list[IssueDetail] = Field(default_factory=list)
