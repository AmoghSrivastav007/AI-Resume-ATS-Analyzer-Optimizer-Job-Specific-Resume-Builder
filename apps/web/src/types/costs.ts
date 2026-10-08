/**
 * Cost Tracking Types
 * 
 * TypeScript types for LLM cost tracking and analytics API.
 * Backend: apps/api/routers/costs.py
 */

/**
 * Task types for cost attribution
 */
export type TaskType = 
  | 'resume_extraction'
  | 'job_extraction'
  | 'content_quality'
  | 'resume_optimization'
  | 'matching_analysis'
  | 'other';

/**
 * Daily cost statistics with task breakdown
 */
export interface DailyStats {
  date: string; // YYYY-MM-DD format
  calls: number;
  total_cost: number; // USD
  total_tokens: number;
  by_task: Record<TaskType, number>; // Task type -> call count
}

/**
 * Monthly cost statistics
 */
export interface MonthlyStats {
  month: string; // YYYY-MM format
  calls: number;
  total_cost: number; // USD
  total_tokens: number;
}

/**
 * Cost summary over N days with daily breakdown
 */
export interface CostSummary {
  period_days: number;
  daily: DailyStats[];
  total_calls: number;
  total_cost: number; // USD
  total_tokens: number;
}

/**
 * Individual LLM API call record
 */
export interface LLMCall {
  call_id: string;
  timestamp: string; // ISO 8601 format
  model: string;
  task_type: TaskType;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
  user_id: string;
  resume_id: string;
  metadata?: Record<string, unknown> | null;
}

/**
 * Chart data point for cost trends
 */
export interface CostDataPoint {
  date: string; // Display format (e.g., "Dec 7")
  cost: number;
  calls: number;
  tokens: number;
}

/**
 * Chart data point for task breakdown
 */
export interface TaskBreakdownPoint {
  task: string; // Display name (e.g., "Resume Extraction")
  calls: number;
  cost: number;
  percentage: number; // Percentage of total calls
}

/**
 * Filter options for cost dashboard
 */
export interface CostFilters {
  days: number; // 1, 7, 30, 90
  taskType?: TaskType | null;
}

/**
 * Task type display names
 */
export const TASK_TYPE_LABELS: Record<TaskType, string> = {
  resume_extraction: 'Resume Extraction',
  job_extraction: 'Job Extraction',
  content_quality: 'Content Quality',
  resume_optimization: 'Resume Optimization',
  matching_analysis: 'Matching Analysis',
  other: 'Other',
};

/**
 * Task type colors for charts
 */
export const TASK_TYPE_COLORS: Record<TaskType, string> = {
  resume_extraction: '#3b82f6', // blue-500
  job_extraction: '#10b981', // green-500
  content_quality: '#f59e0b', // amber-500
  resume_optimization: '#8b5cf6', // violet-500
  matching_analysis: '#ec4899', // pink-500
  other: '#6b7280', // gray-500
};
