/**
 * Optimization Card Component
 * 
 * Displays a single optimization suggestion with:
 * - Verification status badge
 * - Original vs proposed text diff
 * - Reasoning explanation
 * - Fact references
 * - Apply/Reject actions
 */

'use client';

import { useState } from 'react';
import type { Optimization } from '@/types/optimization';

interface OptimizationCardProps {
  optimization: Optimization;
  onApply: (id: string) => Promise<void>;
  onReject: (id: string) => Promise<void>;
  disabled?: boolean;
}

export function OptimizationCard({
  optimization,
  onApply,
  onReject,
  disabled = false,
}: OptimizationCardProps) {
  const [isApplying, setIsApplying] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [showDiff, setShowDiff] = useState(false);

  const handleApply = async () => {
    setIsApplying(true);
    try {
      await onApply(optimization.id);
    } finally {
      setIsApplying(false);
    }
  };

  const handleReject = async () => {
    setIsRejecting(true);
    try {
      await onReject(optimization.id);
    } finally {
      setIsRejecting(false);
    }
  };

  const getStatusBadge = () => {
    const status = optimization.proposed_content.verification_status;
    
    if (status === 'supported') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
          ✓ Supported
        </span>
      );
    }
    
    if (status === 'partially_supported') {
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
          ⚠ Verify Required
        </span>
      );
    }
    
    return null;
  };

  const getConfidenceBar = () => {
    const confidence = optimization.proposed_content.confidence_score || 0;
    const percentage = Math.round(confidence * 100);
    
    let colorClass = 'bg-red-500';
    if (percentage >= 80) colorClass = 'bg-green-500';
    else if (percentage >= 60) colorClass = 'bg-yellow-500';
    
    return (
      <div className="mt-2">
        <div className="flex justify-between text-xs text-gray-600 mb-1">
          <span>Confidence</span>
          <span>{percentage}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`${colorClass} h-2 rounded-full transition-all duration-300`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 space-y-3 bg-white shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-900 capitalize">
              {optimization.section_type.replace('_', ' ')}
            </h3>
            {getStatusBadge()}
          </div>
          {optimization.proposed_content.verification_explanation && (
            <p className="text-xs text-gray-500 mt-1">
              {optimization.proposed_content.verification_explanation}
            </p>
          )}
        </div>
      </div>

      {/* Diff View Toggle */}
      <button
        onClick={() => setShowDiff(!showDiff)}
        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
      >
        {showDiff ? '▼ Hide Changes' : '▶ Show Changes'}
      </button>

      {/* Text Comparison */}
      {showDiff && (
        <div className="space-y-2 text-sm">
          <div className="bg-red-50 border border-red-200 rounded p-3">
            <p className="text-xs font-semibold text-red-700 mb-1">Original:</p>
            <p className="text-gray-800 whitespace-pre-wrap">{optimization.original_text}</p>
          </div>
          
          <div className="flex justify-center">
            <span className="text-gray-400">↓</span>
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded p-3">
            <p className="text-xs font-semibold text-green-700 mb-1">Proposed:</p>
            <p className="text-gray-800 whitespace-pre-wrap">
              {optimization.proposed_content.proposed_text}
            </p>
          </div>
        </div>
      )}

      {/* Reasoning */}
      <div className="bg-blue-50 border border-blue-200 rounded p-3">
        <p className="text-xs font-semibold text-blue-700 mb-1">Why this change?</p>
        <p className="text-sm text-gray-700">{optimization.proposed_content.reasoning}</p>
      </div>

      {/* Fact References */}
      {optimization.proposed_content.fact_references.length > 0 && (
        <div className="text-xs text-gray-600">
          <p className="font-semibold mb-1">Based on your resume facts:</p>
          <ul className="list-disc list-inside space-y-0.5 pl-2">
            {optimization.proposed_content.fact_references.slice(0, 3).map((ref, idx) => (
              <li key={idx} className="truncate">{ref}</li>
            ))}
            {optimization.proposed_content.fact_references.length > 3 && (
              <li className="text-gray-500">
                +{optimization.proposed_content.fact_references.length - 3} more
              </li>
            )}
          </ul>
        </div>
      )}

      {/* Confidence Score */}
      {optimization.proposed_content.confidence_score && getConfidenceBar()}

      {/* Warning for Partially Supported */}
      {optimization.proposed_content.verification_status === 'partially_supported' && (
        <div className="bg-yellow-50 border border-yellow-300 rounded p-3">
          <p className="text-xs font-semibold text-yellow-800 mb-1">⚠️ Verification Required</p>
          <p className="text-xs text-yellow-700">
            This suggestion couldn't be fully verified against your resume facts. 
            Only apply if you have genuine experience with this claim.
          </p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        <button
          onClick={handleApply}
          disabled={disabled || isApplying || isRejecting}
          className="flex-1 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {isApplying ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Applying...
            </span>
          ) : (
            '✓ Apply'
          )}
        </button>
        
        <button
          onClick={handleReject}
          disabled={disabled || isApplying || isRejecting}
          className="flex-1 px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
        >
          {isRejecting ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Rejecting...
            </span>
          ) : (
            '✗ Reject'
          )}
        </button>
      </div>
    </div>
  );
}
