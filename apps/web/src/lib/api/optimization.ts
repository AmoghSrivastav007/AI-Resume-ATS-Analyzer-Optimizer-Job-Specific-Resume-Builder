/**
 * Optimization API Client
 * 
 * API functions for resume optimization/Truth Guard feature.
 * Handles all HTTP communication with the backend optimize endpoints.
 */

import type {
  OptimizationGenerateRequest,
  OptimizationGenerateResponse,
  OptimizationListResponse,
  OptimizationApplyResponse,
  OptimizationRejectResponse,
} from '@/types/optimization';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Get authentication token from localStorage
 */
function getAuthToken(): string {
  if (typeof window === 'undefined') return '';
  // Supabase stores the session in localStorage
  const session = localStorage.getItem('sb-' + window.location.host.split('.')[0] + '-auth-token');
  if (!session) {
    throw new Error('Not authenticated');
  }
  try {
    const parsed = JSON.parse(session);
    return parsed.access_token || '';
  } catch {
    throw new Error('Invalid session');
  }
}

/**
 * Generate optimizations for a resume against a job posting
 * 
 * POST /api/optimize
 * 
 * @param request - Resume version ID and job posting ID
 * @returns Generation summary with counts
 */
export async function generateOptimizations(
  request: OptimizationGenerateRequest
): Promise<OptimizationGenerateResponse> {
  const response = await fetch(`${API_URL}/api/optimize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to generate optimizations' }));
    throw new Error(error.detail || 'Failed to generate optimizations');
  }

  return response.json();
}

/**
 * Get all optimizations for a resume version
 * 
 * GET /api/optimize/{resume_version_id}
 * 
 * @param resumeVersionId - Resume version ID
 * @returns Optimizations grouped by verification status
 */
export async function getOptimizations(
  resumeVersionId: string
): Promise<OptimizationListResponse> {
  const response = await fetch(
    `${API_URL}/api/optimize/${resumeVersionId}`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch optimizations' }));
    throw new Error(error.detail || 'Failed to fetch optimizations');
  }

  return response.json();
}

/**
 * Apply an optimization (user accepts the suggestion)
 * 
 * POST /api/optimize/{optimization_id}/apply
 * 
 * @param optimizationId - Optimization ID
 * @returns Apply confirmation with timestamp
 */
export async function applyOptimization(
  optimizationId: string
): Promise<OptimizationApplyResponse> {
  const response = await fetch(
    `${API_URL}/api/optimize/${optimizationId}/apply`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to apply optimization' }));
    throw new Error(error.detail || 'Failed to apply optimization');
  }

  return response.json();
}

/**
 * Reject an optimization (user declines the suggestion)
 * 
 * POST /api/optimize/{optimization_id}/reject
 * 
 * @param optimizationId - Optimization ID
 * @returns Reject confirmation
 */
export async function rejectOptimization(
  optimizationId: string
): Promise<OptimizationRejectResponse> {
  const response = await fetch(
    `${API_URL}/api/optimize/${optimizationId}/reject`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to reject optimization' }));
    throw new Error(error.detail || 'Failed to reject optimization');
  }

  return response.json();
}

/**
 * Apply all supported optimizations at once
 * 
 * Helper function that applies multiple optimizations in sequence
 * 
 * @param optimizationIds - Array of optimization IDs
 * @returns Array of apply responses
 */
export async function applyAllOptimizations(
  optimizationIds: string[]
): Promise<OptimizationApplyResponse[]> {
  const results: OptimizationApplyResponse[] = [];
  
  for (const id of optimizationIds) {
    try {
      const result = await applyOptimization(id);
      results.push(result);
    } catch (error) {
      console.error(`Failed to apply optimization ${id}:`, error);
      // Continue with next optimization even if one fails
    }
  }
  
  return results;
}

/**
 * Reject all optimizations at once
 * 
 * Helper function that rejects multiple optimizations in sequence
 * 
 * @param optimizationIds - Array of optimization IDs
 * @returns Array of reject responses
 */
export async function rejectAllOptimizations(
  optimizationIds: string[]
): Promise<OptimizationRejectResponse[]> {
  const results: OptimizationRejectResponse[] = [];
  
  for (const id of optimizationIds) {
    try {
      const result = await rejectOptimization(id);
      results.push(result);
    } catch (error) {
      console.error(`Failed to reject optimization ${id}:`, error);
      // Continue with next optimization even if one fails
    }
  }
  
  return results;
}
