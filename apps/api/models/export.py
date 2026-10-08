from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    format: Literal["pdf", "docx"] = Field(description="Export format")
    version_id: UUID | None = Field(None, description="Specific version to export (defaults to current)")


class ValidationDetails(BaseModel):
    fields_checked: int = 0
    fields_recovered: int = 0
    missing_fields: list[str] = []
    parsing_errors: list[str] = []


class ExportJobResponse(BaseModel):
    id: UUID
    status: Literal["pending", "generating", "validating", "completed", "failed"]
    format: str
    validation_passed: bool | None = None
    validation_details: ValidationDetails | None = None
    error_message: str | None = None
    created_at: datetime


class ExportJobCreateResponse(BaseModel):
    job_id: UUID
    message: str = "Export job created successfully"
