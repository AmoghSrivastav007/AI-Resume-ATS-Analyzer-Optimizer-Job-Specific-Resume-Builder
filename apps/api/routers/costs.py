"""
Cost Tracking Dashboard API

Endpoints for viewing LLM usage costs and statistics.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from dependencies.auth import get_current_user
from services.cost_tracker import get_cost_tracker

router = APIRouter(prefix="/api/costs", tags=["costs"])


class DailyStats(BaseModel):
    date: str
    calls: int
    total_cost: float
    total_tokens: int
    by_task: dict[str, int]


class MonthlyStats(BaseModel):
    month: str
    calls: int
    total_cost: float
    total_tokens: int


class CostSummary(BaseModel):
    period_days: int
    daily: list[DailyStats]
    total_calls: int
    total_cost: float
    total_tokens: int


class LLMCall(BaseModel):
    call_id: str
    timestamp: str
    model: str
    task_type: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    user_id: str
    resume_id: str
    metadata: Optional[dict] = None


@router.get("/daily", response_model=DailyStats)
async def get_daily_costs(
    date: Optional[str] = None,
    _current_user: dict = Depends(get_current_user),
) -> DailyStats:
    """
    Get LLM usage costs for a specific day.
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
        
    Returns:
        Daily statistics with cost breakdown by task type
    """
    tracker = get_cost_tracker()
    stats = tracker.get_daily_stats(date)
    
    if not stats:
        raise HTTPException(status_code=404, detail="No data found for this date")
    
    return DailyStats(**stats)


@router.get("/monthly", response_model=MonthlyStats)
async def get_monthly_costs(
    month: Optional[str] = None,
    _current_user: dict = Depends(get_current_user),
) -> MonthlyStats:
    """
    Get LLM usage costs for a specific month.
    
    Args:
        month: Month in YYYY-MM format (defaults to current month)
        
    Returns:
        Monthly statistics with total costs and token usage
    """
    tracker = get_cost_tracker()
    stats = tracker.get_monthly_stats(month)
    
    if not stats:
        raise HTTPException(status_code=404, detail="No data found for this month")
    
    return MonthlyStats(**stats)


@router.get("/summary", response_model=CostSummary)
async def get_cost_summary(
    days: int = 7,
    _current_user: dict = Depends(get_current_user),
) -> CostSummary:
    """
    Get a summary of LLM costs over the last N days.
    
    Args:
        days: Number of days to look back (1-90, default 7)
        
    Returns:
        Summary with daily breakdown and totals
    """
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 90")
    
    tracker = get_cost_tracker()
    summary = tracker.get_cost_summary(days)
    
    return CostSummary(**summary)


@router.get("/recent", response_model=list[LLMCall])
async def get_recent_calls(
    limit: int = 100,
    _current_user: dict = Depends(get_current_user),
) -> list[LLMCall]:
    """
    Get the most recent LLM API calls.
    
    Args:
        limit: Maximum number of calls to return (1-1000, default 100)
        
    Returns:
        List of recent LLM calls with token usage and costs
    """
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
    
    tracker = get_cost_tracker()
    calls = tracker.get_recent_calls(limit)
    
    return [LLMCall(**call) for call in calls]
