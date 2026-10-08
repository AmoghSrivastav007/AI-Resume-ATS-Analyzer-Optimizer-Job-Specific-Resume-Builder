/**
 * Match Detail Modal Component
 * 
 * Displays detailed matching breakdown including:
 * - 4-layer score breakdown with evidence
 * - Skills gap analysis
 * - Matched requirements list
 * - Missing requirements with recommendations
 */

'use client';

import { useState, useEffect } from 'react';
import type { MatchResponse, MatchResultsResponse, GapAnalysis } from '@/types/matching';
import { getMatchResults, getGapAnalysis } from '@/lib/api/matching';

interface MatchDetailModalProps {
  match: MatchResponse | null;
  jobTitle: string;
  onClose: () => void;
}

export function MatchDetailModal({ match, jobTitle, onClose }: MatchDetailModalProps) {
  const [details, setDetails] = useState<MatchResultsResponse | null>(null);
  const [gaps, setGaps] = useState<GapAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'breakdown' | 'gaps'>('breakdown');

  useEffect(() => {
    if (match) {
      loadDetails();
    }
  }, [match]);

  async function loadDetails() {
    if (!match) return;
    
    setLoading(true);
    try {
      const [resultsData, gapsData] = await Promise.all([
        getMatchResults(match.analysis_id),
        getGapAnalysis(match.analysis_id),
      ]);
      setDetails(resultsData);
      setGaps(gapsData);
    } catch (err) {
      console.error('Error loading match details:', err);
    } finally {
      setLoading(false);
    }
  }

  if (!match) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBarColor = (score: number): string => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Match Analysis</h2>
            <p className="text-gray-600 mt-1">{jobTitle}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold w-8 h-8 flex items-center justify-center"
          >
            ×
          </button>
        </div>

        {/* Overall Score */}
        <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-sm text-gray-600">Overall Match Score</p>
              <p className={`text-4xl font-bold ${getScoreColor(match.jd_match_score)}`}>
                {Math.round(match.jd_match_score)}%
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">Requirements Coverage</p>
              <p className="text-2xl font-semibold text-gray-900">
                {match.matched} / {match.total_requirements}
              </p>
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`${getScoreBarColor(match.jd_match_score)} h-3 rounded-full transition-all duration-500`}
              style={{ width: `${Math.round(match.jd_match_score)}%` }}
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 bg-gray-50">
          <div className="flex">
            <button
              onClick={() => setActiveTab('breakdown')}
              className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'breakdown'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Score Breakdown
            </button>
            <button
              onClick={() => setActiveTab('gaps')}
              className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                activeTab === 'gaps'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              Skills Gap Analysis
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <svg className="animate-spin h-8 w-8 text-blue-600" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
          ) : activeTab === 'breakdown' ? (
            <div className="space-y-6">
              {/* 4-Layer Breakdown */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">4-Layer Matching Analysis</h3>
                <div className="space-y-4">
                  {/* Keyword Relevance */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">Keyword Relevance</h4>
                      <span className="text-lg font-bold text-blue-600">
                        {Math.round(match.keyword_relevance)}%
                      </span>
                    </div>
                    <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${match.keyword_relevance}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-700">
                      How well your resume keywords match job requirements
                    </p>
                  </div>

                  {/* Skills Alignment */}
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">Skills Alignment</h4>
                      <span className="text-lg font-bold text-purple-600">
                        {Math.round(match.skills_alignment)}%
                      </span>
                    </div>
                    <div className="w-full bg-purple-200 rounded-full h-2 mb-2">
                      <div
                        className="bg-purple-600 h-2 rounded-full"
                        style={{ width: `${match.skills_alignment}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-700">
                      Technical and soft skills match with requirements
                    </p>
                  </div>

                  {/* Experience Relevance */}
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">Experience Relevance</h4>
                      <span className="text-lg font-bold text-indigo-600">
                        {Math.round(match.experience_relevance)}%
                      </span>
                    </div>
                    <div className="w-full bg-indigo-200 rounded-full h-2 mb-2">
                      <div
                        className="bg-indigo-600 h-2 rounded-full"
                        style={{ width: `${match.experience_relevance}%` }}
                      />
                    </div>
                    <p className="text-sm text-gray-700">
                      Your work experience relevance to the role
                    </p>
                  </div>
                </div>
              </div>

              {/* Match Summary */}
              {details && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Requirements Summary</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                    <div className="bg-white border border-gray-200 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-gray-900">{details.summary.total}</p>
                      <p className="text-xs text-gray-600">Total</p>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-green-600">{details.summary.matched}</p>
                      <p className="text-xs text-gray-600">Matched</p>
                    </div>
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-yellow-600">{details.summary.partially_matched}</p>
                      <p className="text-xs text-gray-600">Partial</p>
                    </div>
                    <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-orange-600">{details.summary.weak_evidence}</p>
                      <p className="text-xs text-gray-600">Weak</p>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
                      <p className="text-2xl font-bold text-red-600">{details.summary.missing}</p>
                      <p className="text-xs text-gray-600">Missing</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-6">
              {/* Gap Analysis */}
              {gaps && (
                <>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-red-900 mb-2">
                      Skills Gap Summary
                    </h3>
                    <div className="flex gap-6">
                      <div>
                        <p className="text-3xl font-bold text-red-600">{gaps.total_gaps}</p>
                        <p className="text-sm text-gray-600">Total Gaps</p>
                      </div>
                      <div>
                        <p className="text-3xl font-bold text-red-700">{gaps.critical_gaps}</p>
                        <p className="text-sm text-gray-600">Critical</p>
                      </div>
                    </div>
                  </div>

                  {/* Critical Gaps */}
                  {gaps.gaps.critical && gaps.gaps.critical.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-red-900 mb-3 flex items-center gap-2">
                        <span className="text-red-600">🔴</span>
                        Critical Gaps ({gaps.gaps.critical.length})
                      </h4>
                      <div className="space-y-2">
                        {gaps.gaps.critical.map((gap, idx) => (
                          <div key={idx} className="bg-white border border-red-200 rounded-lg p-3">
                            <p className="font-medium text-gray-900 mb-1">{gap.requirement}</p>
                            <p className="text-sm text-gray-600 mb-2">{gap.recommendation}</p>
                            <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                              {gap.type}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Important Gaps */}
                  {gaps.gaps.important && gaps.gaps.important.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-yellow-900 mb-3 flex items-center gap-2">
                        <span className="text-yellow-600">🟡</span>
                        Important Gaps ({gaps.gaps.important.length})
                      </h4>
                      <div className="space-y-2">
                        {gaps.gaps.important.map((gap, idx) => (
                          <div key={idx} className="bg-white border border-yellow-200 rounded-lg p-3">
                            <p className="font-medium text-gray-900 mb-1">{gap.requirement}</p>
                            <p className="text-sm text-gray-600 mb-2">{gap.recommendation}</p>
                            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">
                              {gap.type}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Needs Improvement */}
                  {gaps.gaps.needs_improvement && gaps.gaps.needs_improvement.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                        <span className="text-blue-600">🔵</span>
                        Needs Improvement ({gaps.gaps.needs_improvement.length})
                      </h4>
                      <div className="space-y-2">
                        {gaps.gaps.needs_improvement.map((gap, idx) => (
                          <div key={idx} className="bg-white border border-blue-200 rounded-lg p-3">
                            <p className="font-medium text-gray-900 mb-1">{gap.requirement}</p>
                            <p className="text-sm text-gray-600 mb-2">{gap.recommendation}</p>
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                              {gap.type}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
