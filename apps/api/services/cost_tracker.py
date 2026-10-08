"""
LLM Cost Tracking Service

Logs every LLM API call with task type, token counts, and estimated cost.
Provides simple analytics and cost monitoring for production usage.
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from redis import Redis

from config import get_settings

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Task types for cost attribution"""
    RESUME_EXTRACTION = "resume_extraction"
    JOB_EXTRACTION = "job_extraction"
    CONTENT_QUALITY = "content_quality"
    RESUME_OPTIMIZATION = "resume_optimization"
    MATCHING_ANALYSIS = "matching_analysis"
    OTHER = "other"


class ModelType(str, Enum):
    """Supported model types with pricing"""
    # Anthropic Claude pricing (as of 2024)
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # OpenAI pricing (if needed in future)
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"
    GPT35_TURBO = "gpt-3.5-turbo"


# Pricing per 1M tokens (input, output) in USD
MODEL_PRICING = {
    ModelType.CLAUDE_3_OPUS: (15.00, 75.00),
    ModelType.CLAUDE_3_SONNET: (3.00, 15.00),
    ModelType.CLAUDE_3_HAIKU: (0.25, 1.25),
    ModelType.GPT4: (30.00, 60.00),
    ModelType.GPT4_TURBO: (10.00, 30.00),
    ModelType.GPT35_TURBO: (0.50, 1.50),
}


class CostTracker:
    """
    Track LLM API usage and costs in Redis.
    
    Stores individual call logs and aggregated statistics.
    """
    
    def __init__(self):
        settings = get_settings()
        self.redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        self.enabled = settings.cost_tracking_enabled
        
        # Redis key patterns
        self.calls_key = "llm:calls"  # Sorted set (timestamp -> call_id)
        self.call_prefix = "llm:call:"  # Hash per call
        self.stats_prefix = "llm:stats:"  # Daily/monthly aggregates
        
    def log_call(
        self,
        model: str,
        task_type: TaskType,
        input_tokens: int,
        output_tokens: int,
        user_id: Optional[str] = None,
        resume_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Log an LLM API call with token usage and cost.
        
        Args:
            model: Model identifier (e.g., "claude-3-sonnet-20240229")
            task_type: Type of task (extraction, optimization, etc.)
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            user_id: Optional user ID for per-user cost tracking
            resume_id: Optional resume ID for per-resume cost tracking
            metadata: Optional additional metadata (prompt snippet, error info, etc.)
            
        Returns:
            call_id: Unique identifier for this call
        """
        if not self.enabled:
            return ""
        
        try:
            # Calculate cost
            cost = self._calculate_cost(model, input_tokens, output_tokens)
            
            # Generate call ID
            timestamp = datetime.utcnow()
            call_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{task_type.value}"
            
            # Store call details
            call_data = {
                "call_id": call_id,
                "timestamp": timestamp.isoformat() + "Z",
                "model": model,
                "task_type": task_type.value,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "cost_usd": round(cost, 6),
                "user_id": user_id or "",
                "resume_id": resume_id or "",
            }
            
            if metadata:
                call_data["metadata"] = json.dumps(metadata)
            
            # Store in Redis
            pipe = self.redis_client.pipeline()
            
            # Add to sorted set (timestamp index)
            pipe.zadd(self.calls_key, {call_id: timestamp.timestamp()})
            
            # Store call details as hash
            pipe.hset(f"{self.call_prefix}{call_id}", mapping=call_data)
            
            # Update daily statistics
            day_key = f"{self.stats_prefix}day:{timestamp.strftime('%Y-%m-%d')}"
            pipe.hincrby(day_key, "calls", 1)
            pipe.hincrbyfloat(day_key, "total_cost", cost)
            pipe.hincrby(day_key, "total_tokens", input_tokens + output_tokens)
            pipe.hincrby(day_key, f"task:{task_type.value}", 1)
            pipe.expire(day_key, 7776000)  # 90 days retention
            
            # Update monthly statistics
            month_key = f"{self.stats_prefix}month:{timestamp.strftime('%Y-%m')}"
            pipe.hincrby(month_key, "calls", 1)
            pipe.hincrbyfloat(month_key, "total_cost", cost)
            pipe.hincrby(month_key, "total_tokens", input_tokens + output_tokens)
            pipe.expire(month_key, 31536000)  # 1 year retention
            
            pipe.execute()
            
            logger.info(
                f"LLM call logged: {task_type.value} | {model} | "
                f"{input_tokens}+{output_tokens} tokens | ${cost:.4f}"
            )
            
            return call_id
            
        except Exception as e:
            logger.error(f"Failed to log LLM cost: {e}", exc_info=True)
            return ""
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD based on token usage and model pricing."""
        # Try to find pricing for this model
        pricing = None
        for model_type in ModelType:
            if model_type.value in model:
                pricing = MODEL_PRICING.get(model_type)
                break
        
        if not pricing:
            logger.warning(f"Unknown model pricing: {model}, using default Sonnet pricing")
            pricing = MODEL_PRICING[ModelType.CLAUDE_3_SONNET]
        
        input_price_per_million, output_price_per_million = pricing
        
        input_cost = (input_tokens / 1_000_000) * input_price_per_million
        output_cost = (output_tokens / 1_000_000) * output_price_per_million
        
        return input_cost + output_cost
    
    def get_daily_stats(self, date: Optional[str] = None) -> dict:
        """
        Get aggregated statistics for a specific day.
        
        Args:
            date: Date string in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary with calls, total_cost, total_tokens, and per-task breakdown
        """
        if not self.enabled:
            return {}
        
        if not date:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        day_key = f"{self.stats_prefix}day:{date}"
        stats = self.redis_client.hgetall(day_key)
        
        # Convert numeric values
        result = {
            "date": date,
            "calls": int(stats.get("calls", 0)),
            "total_cost": float(stats.get("total_cost", 0)),
            "total_tokens": int(stats.get("total_tokens", 0)),
            "by_task": {},
        }
        
        # Extract per-task counts
        for key, value in stats.items():
            if key.startswith("task:"):
                task_name = key.replace("task:", "")
                result["by_task"][task_name] = int(value)
        
        return result
    
    def get_monthly_stats(self, month: Optional[str] = None) -> dict:
        """
        Get aggregated statistics for a specific month.
        
        Args:
            month: Month string in YYYY-MM format (defaults to current month)
            
        Returns:
            Dictionary with calls, total_cost, and total_tokens
        """
        if not self.enabled:
            return {}
        
        if not month:
            month = datetime.utcnow().strftime("%Y-%m")
        
        month_key = f"{self.stats_prefix}month:{month}"
        stats = self.redis_client.hgetall(month_key)
        
        return {
            "month": month,
            "calls": int(stats.get("calls", 0)),
            "total_cost": float(stats.get("total_cost", 0)),
            "total_tokens": int(stats.get("total_tokens", 0)),
        }
    
    def get_recent_calls(self, limit: int = 100) -> list[dict]:
        """
        Get the most recent LLM API calls.
        
        Args:
            limit: Maximum number of calls to return (default 100)
            
        Returns:
            List of call dictionaries sorted by timestamp (newest first)
        """
        if not self.enabled:
            return []
        
        # Get recent call IDs from sorted set
        call_ids = self.redis_client.zrevrange(self.calls_key, 0, limit - 1)
        
        # Fetch call details
        pipe = self.redis_client.pipeline()
        for call_id in call_ids:
            pipe.hgetall(f"{self.call_prefix}{call_id}")
        
        results = pipe.execute()
        
        # Convert to list of dicts
        calls = []
        for call_data in results:
            if call_data:
                # Convert numeric strings back to proper types
                call_data["input_tokens"] = int(call_data["input_tokens"])
                call_data["output_tokens"] = int(call_data["output_tokens"])
                call_data["total_tokens"] = int(call_data["total_tokens"])
                call_data["cost_usd"] = float(call_data["cost_usd"])
                
                # Parse metadata if present
                if "metadata" in call_data:
                    try:
                        call_data["metadata"] = json.loads(call_data["metadata"])
                    except:
                        pass
                
                calls.append(call_data)
        
        return calls
    
    def get_cost_summary(self, days: int = 7) -> dict:
        """
        Get a summary of costs over the last N days.
        
        Args:
            days: Number of days to look back (default 7)
            
        Returns:
            Dictionary with daily breakdown and totals
        """
        if not self.enabled:
            return {}
        
        summary = {
            "period_days": days,
            "daily": [],
            "total_calls": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
        }
        
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily = self.get_daily_stats(date)
            
            if daily.get("calls", 0) > 0:
                summary["daily"].append(daily)
                summary["total_calls"] += daily["calls"]
                summary["total_cost"] += daily["total_cost"]
                summary["total_tokens"] += daily["total_tokens"]
        
        return summary


# Global singleton instance
_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get or create the global cost tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = CostTracker()
    return _tracker
