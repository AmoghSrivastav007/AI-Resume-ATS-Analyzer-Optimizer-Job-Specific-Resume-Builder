from pydantic import BaseModel, Field


class QualityIssue(BaseModel):
    """Structured issue from Content Quality LLM analysis."""
    
    issue_category: str  # 'content' | 'grammar'
    problem: str
    severity: str  # 'critical' | 'high' | 'medium' | 'low'
    why_it_matters: str
    current_text: str
    suggested_correction: str
    expected_benefit: str
    confidence_level: str  # 'high' | 'medium' | 'low'
    affected_block_id: str | None = None
    location: str | None = None  # e.g., "Experience → Senior Engineer at TechCorp"


class ContentQualityAnalysis(BaseModel):
    """Result from LLM content quality evaluation."""
    
    issues: list[QualityIssue] = Field(default_factory=list)
    overall_content_quality: str  # 'excellent' | 'good' | 'needs_improvement' | 'poor'
    summary: str  # Brief overall assessment
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
