/**
 * Matching API Client
 * 
 * API functions for resume-to-job matching feature.
 * Handles all HTTP communication with the backend matching endpoints.
 */

import type {
  MatchRequest,
  MatchResponse,
  MatchResultsResponse,
  GapAnalysis,
  JobPosting,
} from '@/types/matching';

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
 * Run matching analysis between resume and job posting
 * 
 * POST /api/match
 * 
 * @param request - Resume version ID and job posting ID
 * @returns Match analysis with scores and breakdown
 */
export async function runMatchingAnalysis(
  request: MatchRequest
): Promise<MatchResponse> {
  const response = await fetch(`${API_URL}/api/match`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAuthToken()}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to run matching analysis' }));
    throw new Error(error.detail || 'Failed to run matching analysis');
  }

  return response.json();
}

/**
 * Get detailed match results for an analysis
 * 
 * GET /api/match/{analysis_id}/results
 * 
 * @param analysisId - Analysis ID
 * @returns Complete match results with evidence
 */
export async function getMatchResults(
  analysisId: string
): Promise<MatchResultsResponse> {
  const response = await fetch(
    `${API_URL}/api/match/${analysisId}/results`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch match results' }));
    throw new Error(error.detail || 'Failed to fetch match results');
  }

  return response.json();
}

/**
 * Get gap analysis for an analysis
 * 
 * GET /api/match/{analysis_id}/gaps
 * 
 * @param analysisId - Analysis ID
 * @returns Gap analysis with missing requirements
 */
export async function getGapAnalysis(
  analysisId: string
): Promise<GapAnalysis> {
  const response = await fetch(
    `${API_URL}/api/match/${analysisId}/gaps`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch gap analysis' }));
    throw new Error(error.detail || 'Failed to fetch gap analysis');
  }

  return response.json();
}

/**
 * Get all job postings for a user
 * 
 * GET /api/job-postings
 * 
 * @returns List of job postings
 */
export async function getJobPostings(): Promise<JobPosting[]> {
  const response = await fetch(
    `${API_URL}/api/job-postings`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch job postings' }));
    throw new Error(error.detail || 'Failed to fetch job postings');
  }

  return response.json();
}

/**
 * Get analyses for a resume version
 * 
 * GET /api/analyses?resume_version_id={id}
 * 
 * @param resumeVersionId - Resume version ID
 * @returns List of analyses
 */
export async function getAnalyses(resumeVersionId: string): Promise<any[]> {
  const response = await fetch(
    `${API_URL}/api/analyses?resume_version_id=${resumeVersionId}`,
    {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`,
      },
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch analyses' }));
    throw new Error(error.detail || 'Failed to fetch analyses');
  }

  return response.json();
}
