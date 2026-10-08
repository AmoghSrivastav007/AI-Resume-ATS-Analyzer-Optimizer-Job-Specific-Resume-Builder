/**
 * Resume Optimization Page
 * 
 * Displays AI-generated optimization suggestions with Truth Guard verification.
 * Users can review, apply, or reject individual suggestions.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { OptimizationCard } from '@/components/OptimizationCard';
import {
  getOptimizations,
  applyOptimization,
  rejectOptimization,
  applyAllOptimizations,
  rejectAllOptimizations,
  generateOptimizations,
} from '@/lib/api/optimization';
import type { Optimization, OptimizationListResponse } from '@/types/optimization';

interface OptimizePageProps {
  params: { id: string };
}

export default function OptimizePage({ params }: OptimizePageProps) {
  const router = useRouter();
  const resumeId = params.id;

  // State
  const [data, setData] = useState<OptimizationListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());

  // Load optimizations on mount
  useEffect(() => {
    loadOptimizations();
  }, [resumeId]);

  async function loadOptimizations() {
    setLoading(true);
    setError(null);
    
    try {
      const result = await getOptimizations(resumeId);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load optimizations');
      console.error('Error loading optimizations:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate(jobPostingId: string) {
    setGenerating(true);
    setError(null);
    
    try {
      await generateOptimizations({
        resume_version_id: resumeId,
        job_posting_id: jobPostingId,
      });
      
      // Reload to show new optimizations
      await loadOptimizations();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate optimizations');
      console.error('Error generating optimizations:', err);
    } finally {
      setGenerating(false);
    }
  }

  async function handleApply(optimizationId: string) {
    setProcessingIds(prev => new Set(prev).add(optimizationId));
    
    try {
      await applyOptimization(optimizationId);
      
      // Remove from list (it's been applied)
      setData(prev => {
        if (!prev) return prev;
        
        const removeFromGroup = (group: Optimization[]) =>
          group.filter(opt => opt.id !== optimizationId);
        
        return {
          ...prev,
          grouped: {
            supported: removeFromGroup(prev.grouped.supported),
            partially_supported: removeFromGroup(prev.grouped.partially_supported),
          },
          total: prev.total - 1,
          summary: {
            supported: removeFromGroup(prev.grouped.supported).length,
            partially_supported: removeFromGroup(prev.grouped.partially_supported).length,
          },
        };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply optimization');
      console.error('Error applying optimization:', err);
    } finally {
      setProcessingIds(prev => {
        const next = new Set(prev);
        next.delete(optimizationId);
        return next;
      });
    }
  }

  async function handleReject(optimizationId: string) {
    setProcessingIds(prev => new Set(prev).add(optimizationId));
    
    try {
      await rejectOptimization(optimizationId);
      
      // Remove from list (it's been rejected)
      setData(prev => {
        if (!prev) return prev;
        
        const removeFromGroup = (group: Optimization[]) =>
          group.filter(opt => opt.id !== optimizationId);
        
        return {
          ...prev,
          grouped: {
            supported: removeFromGroup(prev.grouped.supported),
            partially_supported: removeFromGroup(prev.grouped.partially_supported),
          },
          total: prev.total - 1,
          summary: {
            supported: removeFromGroup(prev.grouped.supported).length,
            partially_supported: removeFromGroup(prev.grouped.partially_supported).length,
          },
        };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject optimization');
      console.error('Error rejecting optimization:', err);
    } finally {
      setProcessingIds(prev => {
        const next = new Set(prev);
        next.delete(optimizationId);
        return next;
      });
    }
  }

  async function handleApplyAll() {
    if (!data) return;
    if (!confirm('Apply all supported suggestions? This will modify your resume.')) return;
    
    const allIds = data.grouped.supported.map(opt => opt.id);
    setProcessingIds(new Set(allIds));
    
    try {
      await applyAllOptimizations(allIds);
      await loadOptimizations(); // Reload to get updated state
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply all optimizations');
    } finally {
      setProcessingIds(new Set());
    }
  }

  async function handleRejectAll() {
    if (!data) return;
    if (!confirm('Reject all suggestions?')) return;
    
    const allIds = [
      ...data.grouped.supported.map(opt => opt.id),
      ...data.grouped.partially_supported.map(opt => opt.id),
    ];
    setProcessingIds(new Set(allIds));
    
    try {
      await rejectAllOptimizations(allIds);
      await loadOptimizations(); // Reload to get updated state
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject all optimizations');
    } finally {
      setProcessingIds(new Set());
    }
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
          <p className="text-gray-600">Loading optimizations...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
          <div className="text-red-600 text-center mb-4">
            <svg className="h-16 w-16 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h2 className="text-xl font-bold mb-2">Error Loading Optimizations</h2>
            <p className="text-gray-600">{error}</p>
          </div>
          <div className="space-y-2">
            <button
              onClick={loadOptimizations}
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
  if (data && data.total === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <svg className="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h2 className="text-xl font-bold text-gray-900 mb-2">No Suggestions Yet</h2>
          <p className="text-gray-600 mb-4">
            Generate AI-powered optimization suggestions to improve your resume.
          </p>
          <button
            onClick={() => router.push(`/resumes/${resumeId}/matches`)}
            disabled={generating}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:bg-gray-300"
          >
            {generating ? 'Generating...' : 'Match to Job & Generate'}
          </button>
        </div>
      </div>
    );
  }

  const supportedCount = data?.grouped.supported.length || 0;
  const partialCount = data?.grouped.partially_supported.length || 0;
  const totalCount = supportedCount + partialCount;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push(`/resumes/${resumeId}`)}
            className="text-blue-600 hover:text-blue-800 mb-4 flex items-center gap-2"
          >
            ← Back to Resume
          </button>
          
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Resume Optimization
          </h1>
          <p className="text-gray-600">
            Review AI-generated suggestions to improve your resume. All suggestions are verified for accuracy.
          </p>
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

        {/* Summary */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Total Suggestions</p>
              <p className="text-2xl font-bold text-gray-900">{totalCount}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Auto-Approved</p>
              <p className="text-2xl font-bold text-green-600">{supportedCount}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Verify Required</p>
              <p className="text-2xl font-bold text-yellow-600">{partialCount}</p>
            </div>
          </div>

          {/* Bulk Actions */}
          {totalCount > 0 && (
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                onClick={handleApplyAll}
                disabled={supportedCount === 0 || processingIds.size > 0}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 font-medium"
              >
                ✓ Apply All Supported ({supportedCount})
              </button>
              <button
                onClick={handleRejectAll}
                disabled={totalCount === 0 || processingIds.size > 0}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-300 font-medium"
              >
                ✗ Reject All
              </button>
            </div>
          )}
        </div>

        {/* Supported Suggestions */}
        {supportedCount > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              ✓ Auto-Approved Suggestions ({supportedCount})
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              These suggestions are verified and ready to apply.
            </p>
            <div className="space-y-4">
              {data.grouped.supported.map(opt => (
                <OptimizationCard
                  key={opt.id}
                  optimization={opt}
                  onApply={handleApply}
                  onReject={handleReject}
                  disabled={processingIds.has(opt.id)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Partially Supported Suggestions */}
        {partialCount > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              ⚠ Verification Required ({partialCount})
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              These suggestions need your confirmation. Only apply if you have genuine experience.
            </p>
            <div className="space-y-4">
              {data.grouped.partially_supported.map(opt => (
                <OptimizationCard
                  key={opt.id}
                  optimization={opt}
                  onApply={handleApply}
                  onReject={handleReject}
                  disabled={processingIds.has(opt.id)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
