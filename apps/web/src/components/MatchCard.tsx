/**
 * Match Card Component
 * 
 * Displays a single job matching result with:
 * - Job title and company
 * - Overall match score with visual indicator
 * - Key stats (requirements matched, gaps)
 * - Click to view detailed breakdown
 */

'use client';

import type { MatchResponse } from '@/types/matching';

interface MatchCardProps {
  match: MatchResponse;
  jobPosting: {
    title: string;
    company: string;
    location?: string;
  };
  onClick: (match: MatchResponse) => void;
}

export function MatchCard({ match, jobPosting, onClick }: MatchCardProps) {
  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreBarColor = (score: number): string => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const matchPercentage = Math.round(match.jd_match_score);
  const matchedCount = match.matched;
  const totalCount = match.total_requirements;
  const matchedPercentage = totalCount > 0 ? Math.round((matchedCount / totalCount) * 100) : 0;

  return (
    <div
      onClick={() => onClick(match)}
      className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 hover:border-blue-300 cursor-pointer transition-all duration-200 bg-white shadow-sm"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {jobPosting.title}
          </h3>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <span className="font-medium">{jobPosting.company}</span>
            {jobPosting.location && (
              <>
                <span>•</span>
                <span>{jobPosting.location}</span>
              </>
            )}
          </div>
        </div>
        
        {/* Overall Score Badge */}
        <div className={`px-3 py-2 rounded-lg ${getScoreColor(match.jd_match_score)} font-bold text-xl shrink-0 ml-4`}>
          {matchPercentage}%
        </div>
      </div>

      {/* Score Bar */}
      <div className="mb-3">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`${getScoreBarColor(match.jd_match_score)} h-2 rounded-full transition-all duration-500`}
            style={{ width: `${matchPercentage}%` }}
          />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
        <div className="text-center">
          <p className="text-xs text-gray-500">Requirements</p>
          <p className="text-lg font-semibold text-gray-900">{totalCount}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">Matched</p>
          <p className="text-lg font-semibold text-green-600">{matchedCount}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">Partial</p>
          <p className="text-lg font-semibold text-yellow-600">{match.partially_matched}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-gray-500">Missing</p>
          <p className="text-lg font-semibold text-red-600">{match.missing}</p>
        </div>
      </div>

      {/* 4-Layer Scores */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-3 border-t border-gray-200">
        <div>
          <p className="text-xs text-gray-500 mb-1">Keywords</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-blue-500 h-1.5 rounded-full"
                style={{ width: `${match.keyword_relevance}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-700">{Math.round(match.keyword_relevance)}%</span>
          </div>
        </div>
        
        <div>
          <p className="text-xs text-gray-500 mb-1">Skills</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-purple-500 h-1.5 rounded-full"
                style={{ width: `${match.skills_alignment}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-700">{Math.round(match.skills_alignment)}%</span>
          </div>
        </div>
        
        <div>
          <p className="text-xs text-gray-500 mb-1">Experience</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-indigo-500 h-1.5 rounded-full"
                style={{ width: `${match.experience_relevance}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-700">{Math.round(match.experience_relevance)}%</span>
          </div>
        </div>
        
        <div>
          <p className="text-xs text-gray-500 mb-1">Match Rate</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-1.5">
              <div
                className={`${getScoreBarColor(matchedPercentage)} h-1.5 rounded-full`}
                style={{ width: `${matchedPercentage}%` }}
              />
            </div>
            <span className="text-xs font-medium text-gray-700">{matchedPercentage}%</span>
          </div>
        </div>
      </div>

      {/* Click Hint */}
      <div className="mt-3 text-center text-xs text-blue-600 font-medium">
        Click to view detailed breakdown →
      </div>
    </div>
  );
}
