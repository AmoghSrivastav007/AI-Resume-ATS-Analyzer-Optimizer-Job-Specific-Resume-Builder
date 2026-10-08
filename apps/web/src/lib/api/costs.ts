/**
 * Cost Tracking API Client
 * 
 * Client functions for LLM cost tracking and analytics endpoints.
 * Backend: apps/api/routers/costs.py
 */

import type { 
  CostSummary, 
  DailyStats, 
  LLMCall, 
  MonthlyStats 
} from '@/types/costs';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Get authorization header with access token
 */
function getAuthHeader(): HeadersInit {
  // In production, get token from auth context/cookie
  // For MVP, using placeholder
  const token = typeof window !== 'undefined' 
    ? localStorage.getItem('access_token') 
    : null;
  
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Get daily cost statistics for a specific date
 * GET /api/costs/daily?date=YYYY-MM-DD
 */
export async function getDailyCosts(date?: string): Promise<DailyStats> {
  const params = new URLSearchParams();
  if (date) params.set('date', date);
  
  const url = `${API_BASE}/api/costs/daily${params.toString() ? `?${params}` : ''}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch daily costs' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get monthly cost statistics for a specific month
 * GET /api/costs/monthly?month=YYYY-MM
 */
export async function getMonthlyCosts(month?: string): Promise<MonthlyStats> {
  const params = new URLSearchParams();
  if (month) params.set('month', month);
  
  const url = `${API_BASE}/api/costs/monthly${params.toString() ? `?${params}` : ''}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch monthly costs' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get cost summary over the last N days with daily breakdown
 * GET /api/costs/summary?days=7
 */
export async function getCostSummary(days: number = 7): Promise<CostSummary> {
  const params = new URLSearchParams({ days: days.toString() });
  const url = `${API_BASE}/api/costs/summary?${params}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch cost summary' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get recent LLM API calls with token usage and costs
 * GET /api/costs/recent?limit=100
 */
export async function getRecentCalls(limit: number = 100): Promise<LLMCall[]> {
  const params = new URLSearchParams({ limit: limit.toString() });
  const url = `${API_BASE}/api/costs/recent?${params}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch recent calls' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Export cost data as CSV
 * Client-side conversion of API data to CSV format
 */
export function exportCostDataToCSV(calls: LLMCall[]): string {
  const headers = [
    'Timestamp',
    'Call ID',
    'Model',
    'Task Type',
    'Input Tokens',
    'Output Tokens',
    'Total Tokens',
    'Cost (USD)',
    'User ID',
    'Resume ID',
  ];
  
  const rows = calls.map(call => [
    call.timestamp,
    call.call_id,
    call.model,
    call.task_type,
    call.input_tokens.toString(),
    call.output_tokens.toString(),
    call.total_tokens.toString(),
    call.cost_usd.toFixed(6),
    call.user_id,
    call.resume_id,
  ]);
  
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
  ].join('\n');
  
  return csvContent;
}

/**
 * Download CSV file
 */
export function downloadCSV(csvContent: string, filename: string): void {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}
