from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ResumeVersionResponse(BaseModel):
    id: UUID
    resume_id: UUID
    version_number: int
    status: str
    storage_path: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    needs_ocr: bool = False
    parse_error: str | None = None
    created_at: datetime
    updated_at: datetime


class ResumeResponse(BaseModel):
    id: UUID
    title: str
    current_version_id: UUID | None
    created_at: datetime
    updated_at: datetime
    version: ResumeVersionResponse
    job_id: str | None = None


class ResumeUploadResponse(BaseModel):
    data: ResumeResponse = Field(description="Created resume, initial version, and parse job id")


class ResumeBlockResponse(BaseModel):
    id: UUID
    block_type: str
    content: dict[str, Any]
    sort_order: int


class ResumeSectionResponse(BaseModel):
    id: UUID
    section_type: str
    title: str | None
    sort_order: int
    blocks: list[ResumeBlockResponse]


class FactLedgerEntryResponse(BaseModel):
    id: UUID
    fact_type: str
    fact_text: str
    is_verified: bool
    source_block_id: UUID | None
    metadata: dict[str, Any]


class ResumeDetailData(BaseModel):
    id: UUID
    title: str
    current_version_id: UUID | None
    created_at: datetime
    updated_at: datetime
    version: ResumeVersionResponse
    sections: list[ResumeSectionResponse]
    facts: list[FactLedgerEntryResponse]


class ResumeDetailResponse(BaseModel):
    data: ResumeDetailData


class JobStatusData(BaseModel):
    id: str
    status: Literal["queued", "started", "finished", "failed", "deferred", "scheduled", "stopped", "canceled"]
    resume_id: str | None = None
    version_id: str | None = None
    error: str | None = None
    needs_ocr: bool = False
    result: dict[str, Any] | None = None


class JobStatusResponse(BaseModel):
    data: JobStatusData
