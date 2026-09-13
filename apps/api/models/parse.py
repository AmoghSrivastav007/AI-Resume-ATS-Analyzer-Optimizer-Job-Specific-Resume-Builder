from typing import Literal

from pydantic import BaseModel, Field


class FieldConfidence(BaseModel):
    field: str
    llm_value: str | None
    regex_values: list[str] = Field(default_factory=list)
    confidence: Literal["high", "low"]
    reason: str | None = None


class CrossValidationResult(BaseModel):
    extraction: dict
    disagreements: list[FieldConfidence] = Field(default_factory=list)
    field_confidence: dict[str, str] = Field(default_factory=dict)
