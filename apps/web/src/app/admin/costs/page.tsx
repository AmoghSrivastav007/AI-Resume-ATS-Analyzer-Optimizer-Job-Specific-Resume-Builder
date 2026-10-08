'use client';

/**
 * Cost Dashboard Page
 * 
 * Admin dashboard for monitoring LLM API usage and costs:
 * - Cost trend chart (last N days)
 * - Task breakdown chart
 * - Summary statistics
 * - Recent API calls table with export
 * 
 * Route: /admin/costs
 */

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import {
  getCostSummary,
  getRecentCalls,
  exportCostDataToCSV,
  downloadCSV,
} from '@/lib/api/costs';
import CostTrendChart from '@/components/CostTrendChart';
import TaskBreakdownChart from '@/components/TaskBreakdownChart';
import { 
  TASK_TYPE_LABELS,
  type CostSummary, 
  type LLMCall,
  type CostDataPoint,
  type TaskBreakdownPoint,
} from '@/types/costs';

export default function CostDashboardPage() {
  // State
  const [days, setDays] = useState<number>(7);
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [recentCalls, setRecentCalls] = useState<LLMCall[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportingCSV, setExportingCSV] = useState(false);

  // Fetch data
  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);

      try {
        const [summaryData, callsData] = await Promise.all([
          getCostSummary(days),
          getRecentCalls(100),
        ]);

        setSummary(summaryData);
        setRecentCalls(callsData);
      } catch (err) {
        console.error('Failed to fetch cost data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load cost data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [days]);

  // Transform summary data for charts
  const chartData = useMemo<CostDataPoint[]>(() => {
    if (!summary) return [];

    return summary.daily.map(day => {
      // Format date for display (e.g., "Dec 7")
      const date = new Date(day.date);
      const displayDate = date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });

      return {
        date: displayDate,
        cost: day.total_cost,
        calls: day.calls,
        tokens: day.total_tokens,
      };
    }).reverse(); // Oldest to newest for chart
  }, [summary]);

  // Transform task breakdown data for chart
  const taskBreakdownData = useMemo<TaskBreakdownPoint[]>(() => {
    if (!summary) return [];

    // Aggregate tasks across all days
    const taskTotals: Record<string, { calls: number; cost: number }> = {};

    summary.daily.forEach(day => {
      Object.entries(day.by_task).forEach(([taskType, calls]) => {
        if (!taskTotals[taskType]) {
          taskTotals[taskType] = { calls: 0, cost: 0 };
        }
        taskTotals[taskType].calls += calls;
        
        // Estimate cost per task (proportional to calls)
        const dayCallsTotal = Object.values(day.by_task).reduce((sum, c) => sum + c, 0);
        const taskCostShare = (calls / dayCallsTotal) * day.total_cost;
        taskTotals[taskType].cost += taskCostShare;
      });
    });

    // Convert to array with percentages
    const totalCalls = Object.values(taskTotals).reduce((sum, t) => sum + t.calls, 0);

    return Object.entries(taskTotals).map(([taskType, data]) => ({
      task: TASK_TYPE_LABELS[taskType as keyof typeof TASK_TYPE_LABELS] || taskType,
      calls: data.calls,
      cost: data.cost,
      percentage: totalCalls > 0 ? (data.calls / totalCalls) * 100 : 0,
    }));
  }, [summary]);

  // Handle CSV export
  const handleExportCSV = () => {
    setExportingCSV(true);
    try {
      const csv = exportCostDataToCSV(recentCalls);
      const filename = `llm-costs-${new Date().toISOString().split('T')[0]}.csv`;
      downloadCSV(csv, filename);
    } catch (err) {
      console.error('Failed to export CSV:', err);
      alert('Failed to export CSV. Please try again.');
    } finally {
      setExportingCSV(false);
    }
  };

  // Format currency
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(amount);
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <Link 
                href="/resumes" 
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline mb-2 inline-block"
              >
                ← Back to Resumes
              </Link>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                Cost Dashboard
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Monitor LLM API usage and costs
              </p>
            </div>

            {/* Time range selector */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-700 dark:text-gray-300">
                Show last:
              </label>
              <select
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={1}>1 day</option>
                <option value={7}>7 days</option>
                <option value={30}>30 days</option>
                <option value={90}>90 days</option>
              </select>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">Loading cost data...</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-start">
              <svg className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div>
                <h3 className="text-sm font-medium text-red-800 dark:text-red-300">
                  Failed to load cost data
                </h3>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        {!loading && !error && summary && (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Cost</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(summary.total_cost)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  Last {days} days
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Calls</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {summary.total_calls.toLocaleString()}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  API requests
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Tokens</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {(summary.total_tokens / 1000).toFixed(1)}K
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  {summary.total_tokens.toLocaleString()} tokens
                </p>
              </div>

              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Avg Cost/Call</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(summary.total_calls > 0 ? summary.total_cost / summary.total_calls : 0)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  Per API request
                </p>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Cost Trend Chart */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Cost Trend
                </h2>
                <CostTrendChart data={chartData} />
              </div>

              {/* Task Breakdown Chart */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Usage by Task Type
                </h2>
                <TaskBreakdownChart data={taskBreakdownData} />
              </div>
            </div>

            {/* Recent Calls Table */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Recent API Calls
                </h2>
                <button
                  onClick={handleExportCSV}
                  disabled={exportingCSV || recentCalls.length === 0}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700
                           disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed
                           transition-colors text-sm font-medium"
                >
                  {exportingCSV ? 'Exporting...' : 'Export CSV'}
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Task Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Model
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Tokens
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Cost
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {recentCalls.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                          No recent API calls
                        </td>
                      </tr>
                    )}
                    {recentCalls.slice(0, 50).map((call) => (
                      <tr key={call.call_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          {formatTimestamp(call.timestamp)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs">
                            {TASK_TYPE_LABELS[call.task_type] || call.task_type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                          {call.model.split('-').slice(0, 3).join('-')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-100">
                          {call.total_tokens.toLocaleString()}
                          <span className="text-xs text-gray-500 dark:text-gray-500 ml-1">
                            ({call.input_tokens}+{call.output_tokens})
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900 dark:text-gray-100">
                          {formatCurrency(call.cost_usd)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {recentCalls.length > 50 && (
                <div className="px-6 py-3 bg-gray-50 dark:bg-gray-700 text-center text-sm text-gray-600 dark:text-gray-400">
                  Showing 50 of {recentCalls.length} calls. Export CSV for full data.
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
