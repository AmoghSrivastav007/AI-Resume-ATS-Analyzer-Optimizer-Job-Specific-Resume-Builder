from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class JobRequirement(BaseModel):
    """Single extracted requirement from a job description."""
    
    type: str  # 'required_skill' | 'preferred_skill' | 'responsibility' | 'education' | 'experience_years' | 'certification' | 'domain_knowledge' | 'competency_signal'
    text: str
    category: str | None = None  # Optional grouping (e.g., 'technical', 'soft_skills')


class JobDescriptionExtraction(BaseModel):
    """Structured extraction from job description."""
    
    title: str
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None  # 'full_time' | 'part_time' | 'contract' | 'internship'
    salary_range: str | None = None
    
    # Categorized requirements
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience_years: str | None = None  # e.g., "3-5 years", "5+ years"
    certifications: list[str] = Field(default_factory=list)
    domain_knowledge: list[str] = Field(default_factory=list)
    competency_signals: list[str] = Field(default_factory=list)  # e.g., "problem solving", "stakeholder management"
    
    summary: str | None = None


class JobPostingCreateRequest(BaseModel):
    """Request to create a job posting."""
    
    title: str
    company: str | None = None
    source_url: str | None = None
    raw_text: str | None = None
    # File upload handled separately via multipart/form-data


class JobPostingResponse(BaseModel):
    """Job posting with metadata."""
    
    id: UUID
    user_id: UUID
    title: str
    company: str | None
    source_url: str | None
    raw_text: str
    created_at: datetime
    updated_at: datetime


class JobRequirementResponse(BaseModel):
    """Individual requirement response."""
    
    id: UUID
    job_posting_id: UUID
    requirement_type: str
    requirement_text: str
    category: str | None
    created_at: datetime


class JobPostingDetailResponse(BaseModel):
    """Job posting with all extracted requirements."""
    
    job_posting: JobPostingResponse
    requirements: list[JobRequirementResponse]
    extraction_summary: dict  # Counts by type
