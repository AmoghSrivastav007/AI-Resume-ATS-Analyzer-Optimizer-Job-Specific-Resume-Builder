/**
 * Optimization Types
 * 
 * Types for the resume optimization/Truth Guard feature.
 * Backend API: apps/api/routers/optimize.py
 */

export type VerificationStatus = 'supported' | 'partially_supported' | 'rejected';

export interface ProposedContent {
  proposed_text: string;
  reasoning: string;
  fact_references: string[];
  verification_status: VerificationStatus;
  verification_explanation?: string;
  confidence_score?: number;
}

export interface Optimization {
  id: string;
  resume_version_id: string;
  block_id: string;
  section_type: string;
  original_text: string;
  proposed_content: ProposedContent;
  verification_status: VerificationStatus;
  status: 'pending' | 'applied' | 'rejected';
  created_at: string;
  applied_at?: string;
  rejected_at?: string;
}

export interface OptimizationGenerateRequest {
  resume_version_id: string;
  job_posting_id: string;
}

export interface OptimizationGenerateResponse {
  resume_version_id: string;
  job_posting_id: string;
  total_generated: number;
  stored: number;
  auto_rejected: number;
  supported: number;
  partially_supported: number;
}

export interface OptimizationListResponse {
  resume_version_id: string;
  total: number;
  grouped: {
    supported: Optimization[];
    partially_supported: Optimization[];
  };
  summary: {
    supported: number;
    partially_supported: number;
  };
}

export interface OptimizationApplyResponse {
  optimization_id: string;
  status: 'applied';
  applied_at: string;
}

export interface OptimizationRejectResponse {
  optimization_id: string;
  status: 'rejected';
}
