'use client';

/**
 * TaskBreakdownChart Component
 * 
 * Bar chart showing LLM usage breakdown by task type with:
 * - Stacked bars for calls and cost
 * - Color-coded by task type
 * - Percentage labels
 */

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { TASK_TYPE_COLORS, TASK_TYPE_LABELS } from '@/types/costs';
import type { TaskBreakdownPoint } from '@/types/costs';

interface TaskBreakdownChartProps {
  data: TaskBreakdownPoint[];
  className?: string;
}

export default function TaskBreakdownChart({ data, className = '' }: TaskBreakdownChartProps) {
  // Sort by calls descending
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => b.calls - a.calls);
  }, [data]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    const data = payload[0].payload;

    return (
      <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
          {data.task}
        </p>
        <div className="space-y-1 text-sm">
          <p className="text-gray-900 dark:text-gray-100">
            Calls: {data.calls.toLocaleString()}
          </p>
          <p className="text-gray-900 dark:text-gray-100">
            Cost: ${data.cost.toFixed(4)}
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            {data.percentage.toFixed(1)}% of total
          </p>
        </div>
      </div>
    );
  };

  // Get color for task type
  const getTaskColor = (taskName: string): string => {
    // Find matching task type key
    const taskKey = Object.entries(TASK_TYPE_LABELS).find(
      ([_, label]) => label === taskName
    )?.[0] as keyof typeof TASK_TYPE_COLORS | undefined;

    return taskKey ? TASK_TYPE_COLORS[taskKey] : TASK_TYPE_COLORS.other;
  };

  // Empty state
  if (!data || data.length === 0) {
    return (
      <div className={`flex items-center justify-center h-80 bg-gray-50 dark:bg-gray-800 rounded-lg ${className}`}>
        <p className="text-gray-500 dark:text-gray-400">No task data available</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={sortedData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          
          {/* X Axis: Task Type */}
          <XAxis
            dataKey="task"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            angle={-45}
            textAnchor="end"
            height={100}
          />
          
          {/* Y Axis: Call Count */}
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            label={{ 
              value: 'Number of Calls', 
              angle: -90, 
              position: 'insideLeft',
              style: { fontSize: '12px' }
            }}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend 
            wrapperStyle={{ fontSize: '14px', paddingTop: '10px' }}
          />
          
          {/* Calls bar */}
          <Bar
            dataKey="calls"
            name="Calls"
            radius={[4, 4, 0, 0]}
          >
            {sortedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getTaskColor(entry.task)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend with percentages */}
      <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
        {sortedData.map((entry, index) => (
          <div key={index} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded"
              style={{ backgroundColor: getTaskColor(entry.task) }}
            />
            <span className="text-gray-700 dark:text-gray-300 truncate">
              {entry.task}: {entry.percentage.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
