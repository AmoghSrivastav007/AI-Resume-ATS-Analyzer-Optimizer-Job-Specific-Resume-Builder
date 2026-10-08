/**
 * Matching Types
 * 
 * Types for the resume-to-job matching feature.
 * Backend API: apps/api/routers/matching.py
 */

export type MatchStatus = 
  | 'matched'
  | 'partially_matched'
  | 'missing'
  | 'weak_evidence'
  | 'not_relevant';

export interface MatchResult {
  requirement_id: string;
  requirement_text: string;
  requirement_type: string;
  match_status: MatchStatus;
  match_layer: number; // 1-4
  match_score: number; // 0-100
  evidence_block_id?: string;
  evidence_text?: string;
  similarity_score?: number;
  recommendation?: string;
}

export interface CategoryScore {
  weight: number; // Percentage weight
  score: number; // 0-100
  contribution: number; // Weighted contribution to overall
  details: Record<string, any>;
}

export interface MatchBreakdown {
  overall_score: number;
  categories: Record<string, CategoryScore>;
}

export interface GapItem {
  requirement: string;
  type: string;
  recommendation: string;
}

export interface GapAnalysis {
  total_gaps: number;
  critical_gaps: number;
  gaps: {
    critical?: GapItem[];
    important?: GapItem[];
    needs_improvement?: GapItem[];
  };
}

export interface MatchRequest {
  resume_version_id: string;
  job_posting_id: string;
}

export interface MatchResponse {
  analysis_id: string;
  resume_version_id: string;
  job_posting_id: string;
  jd_match_score: number;
  keyword_relevance: number;
  skills_alignment: number;
  experience_relevance: number;
  match_breakdown: MatchBreakdown;
  gap_analysis: GapAnalysis;
  total_requirements: number;
  matched: number;
  partially_matched: number;
  missing: number;
  weak_evidence: number;
}

export interface MatchSummary {
  total: number;
  matched: number;
  partially_matched: number;
  weak_evidence: number;
  missing: number;
  not_relevant: number;
}

export interface GroupedMatchResults {
  matched: MatchResult[];
  partially_matched: MatchResult[];
  weak_evidence: MatchResult[];
  missing: MatchResult[];
  not_relevant: MatchResult[];
}

export interface MatchResultsResponse {
  analysis: any; // Analysis object from backend
  match_results: MatchResult[];
  grouped_matches: GroupedMatchResults;
  summary: MatchSummary;
}

export interface JobPosting {
  id: string;
  user_id: string;
  title: string;
  company: string;
  location?: string;
  description?: string;
  requirements?: string;
  created_at: string;
  updated_at: string;
}
