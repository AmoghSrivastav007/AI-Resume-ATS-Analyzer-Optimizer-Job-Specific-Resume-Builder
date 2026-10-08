/**
 * Resume Matching Page
 * 
 * Displays job matching results for a resume.
 * Users can:
 * - View all matches with scores
 * - Filter by score threshold
 * - Sort by different criteria
 * - Click to see detailed breakdown
 * - Export results to CSV
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { MatchCard } from '@/components/MatchCard';
import { MatchDetailModal } from '@/components/MatchDetailModal';
import {
  getAnalyses,
  getJobPostings,
  runMatchingAnalysis,
} from '@/lib/api/matching';
import type { MatchResponse, JobPosting } from '@/types/matching';

interface MatchesPageProps {
  params: { id: string };
}

export default function MatchesPage({ params }: MatchesPageProps) {
  const router = useRouter();
  const resumeId = params.id;

  // State
  const [matches, setMatches] = useState<MatchResponse[]>([]);
  const [jobPostings, setJobPostings] = useState<Record<string, JobPosting>>({});
  const [filteredMatches, setFilteredMatches] = useState<MatchResponse[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<MatchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  
  // Filters
  const [minScore, setMinScore] = useState(0);
  const [sortBy, setSortBy] = useState<'score' | 'title' | 'company'>('score');

  // Load matches on mount
  useEffect(() => {
    loadMatches();
  }, [resumeId]);

  // Apply filters when matches or filters change
  useEffect(() => {
    applyFilters();
  }, [matches, minScore, sortBy]);

  async function loadMatches() {
    setLoading(true);
    setError(null);
    
    try {
      // Load analyses and job postings in parallel
      const [analysesData, jobPostingsData] = await Promise.all([
        getAnalyses(resumeId),
        getJobPostings(),
      ]);
      
      // Create job postings lookup
      const jobsMap: Record<string, JobPosting> = {};
      jobPostingsData.forEach(job => {
        jobsMap[job.id] = job;
      });
      setJobPostings(jobsMap);
      
      // Extract match data from analyses
      const matchData: MatchResponse[] = analysesData
        .filter(analysis => analysis.summary?.jd_match_score !== undefined)
        .map(analysis => ({
          analysis_id: analysis.id,
          resume_version_id: analysis.resume_version_id,
          job_posting_id: analysis.summary.job_posting_id || '',
          jd_match_score: analysis.summary.jd_match_score,
          keyword_relevance: analysis.summary.keyword_relevance || 0,
          skills_alignment: analysis.summary.skills_alignment || 0,
          experience_relevance: analysis.summary.experience_relevance || 0,
          match_breakdown: analysis.summary.match_breakdown || {},
          gap_analysis: analysis.summary.gap_analysis || {},
          total_requirements: analysis.summary.total_requirements || 0,
          matched: analysis.summary.matched || 0,
          partially_matched: analysis.summary.partially_matched || 0,
          missing: analysis.summary.missing || 0,
          weak_evidence: analysis.summary.weak_evidence || 0,
        }));
      
      setMatches(matchData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load matches');
      console.error('Error loading matches:', err);
    } finally {
      setLoading(false);
    }
  }

  function applyFilters() {
    let filtered = [...matches];
    
    // Filter by minimum score
    filtered = filtered.filter(match => match.jd_match_score >= minScore);
    
    // Sort
    filtered.sort((a, b) => {
      if (sortBy === 'score') {
        return b.jd_match_score - a.jd_match_score;
      }
      if (sortBy === 'title') {
        const titleA = jobPostings[a.job_posting_id]?.title || '';
        const titleB = jobPostings[b.job_posting_id]?.title || '';
        return titleA.localeCompare(titleB);
      }
      if (sortBy === 'company') {
        const companyA = jobPostings[a.job_posting_id]?.company || '';
        const companyB = jobPostings[b.job_posting_id]?.company || '';
        return companyA.localeCompare(companyB);
      }
      return 0;
    });
    
    setFilteredMatches(filtered);
  }

  function exportToCSV() {
    if (filteredMatches.length === 0) return;
    
    // CSV headers
    const headers = [
      'Job Title',
      'Company',
      'Location',
      'Overall Score',
      'Keyword Relevance',
      'Skills Alignment',
      'Experience Relevance',
      'Total Requirements',
      'Matched',
      'Partially Matched',
      'Missing',
    ];
    
    // CSV rows
    const rows = filteredMatches.map(match => {
      const job = jobPostings[match.job_posting_id];
      return [
        job?.title || '',
        job?.company || '',
        job?.location || '',
        Math.round(match.jd_match_score),
        Math.round(match.keyword_relevance),
        Math.round(match.skills_alignment),
        Math.round(match.experience_relevance),
        match.total_requirements,
        match.matched,
        match.partially_matched,
        match.missing,
      ];
    });
    
    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');
    
    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resume-matches-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-gray-600">Loading matches...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && matches.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
          <div className="text-red-600 text-center mb-4">
            <svg className="h-16 w-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-bold mb-2">Error Loading Matches</h2>
            <p className="text-gray-600">{error}</p>
          </div>
          <div className="space-y-2">
            <button
              onClick={loadMatches}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Try Again
            </button>
            <button
              onClick={() => router.push(`/resumes/${resumeId}`)}
              className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
            >
              Back to Resume
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (matches.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <svg className="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
          </svg>
          <h2 className="text-xl font-bold text-gray-900 mb-2">No Matches Yet</h2>
          <p className="text-gray-600 mb-4">
            Run matching analysis to see how your resume matches against job postings.
          </p>
          <button
            onClick={() => router.push(`/jobs`)}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Browse Job Postings
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push(`/resumes/${resumeId}`)}
            className="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
          >
            ← Back to Resume
          </button>
          
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Job Matching Results
          </h1>
          <p className="text-gray-600">
            Showing {filteredMatches.length} of {matches.length} matches
          </p>
        </div>

        {/* Filters & Actions */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            {/* Score Filter */}
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Score: {minScore}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Sort By */}
            <div className="min-w-[180px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="score">Match Score</option>
                <option value="title">Job Title</option>
                <option value="company">Company</option>
              </select>
            </div>

            {/* Export */}
            <div className="flex items-end">
              <button
                onClick={exportToCSV}
                disabled={filteredMatches.length === 0}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 font-medium whitespace-nowrap"
              >
                Export CSV
              </button>
            </div>
          </div>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">{error}</p>
            <button
              onClick={() => setError(null)}
              className="text-red-600 hover:text-red-800 text-sm font-medium mt-2"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Matches Grid */}
        {filteredMatches.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {filteredMatches.map(match => (
              <MatchCard
                key={match.analysis_id}
                match={match}
                jobPosting={jobPostings[match.job_posting_id] || {
                  title: 'Unknown Job',
                  company: 'Unknown Company',
                }}
                onClick={setSelectedMatch}
              />
            ))}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <p className="text-gray-600">No matches found with current filters.</p>
            <button
              onClick={() => setMinScore(0)}
              className="mt-4 text-blue-600 hover:text-blue-800 font-medium"
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {selectedMatch && (
        <MatchDetailModal
          match={selectedMatch}
          jobTitle={jobPostings[selectedMatch.job_posting_id]?.title || 'Job Details'}
          onClose={() => setSelectedMatch(null)}
        />
      )}
    </div>
  );
}
