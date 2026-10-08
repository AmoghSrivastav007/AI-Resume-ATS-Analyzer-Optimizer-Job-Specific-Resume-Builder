'use client';

/**
 * CostTrendChart Component
 * 
 * Line chart showing cost trends over time with dual Y-axes:
 * - Left axis: Cost in USD
 * - Right axis: Number of calls
 */

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { CostDataPoint } from '@/types/costs';

interface CostTrendChartProps {
  data: CostDataPoint[];
  className?: string;
}

export default function CostTrendChart({ data, className = '' }: CostTrendChartProps) {
  // Format data for display
  const chartData = useMemo(() => {
    return data.map(point => ({
      ...point,
      costDisplay: point.cost.toFixed(4), // For tooltip
    }));
  }, [data]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || payload.length === 0) return null;

    const data = payload[0].payload;

    return (
      <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
          {data.date}
        </p>
        <div className="space-y-1 text-sm">
          <p className="text-blue-600 dark:text-blue-400">
            Cost: ${data.cost.toFixed(4)}
          </p>
          <p className="text-green-600 dark:text-green-400">
            Calls: {data.calls.toLocaleString()}
          </p>
          <p className="text-gray-600 dark:text-gray-400">
            Tokens: {data.tokens.toLocaleString()}
          </p>
        </div>
      </div>
    );
  };

  // Empty state
  if (!data || data.length === 0) {
    return (
      <div className={`flex items-center justify-center h-80 bg-gray-50 dark:bg-gray-800 rounded-lg ${className}`}>
        <p className="text-gray-500 dark:text-gray-400">No cost data available</p>
      </div>
    );
  }

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          
          {/* X Axis: Date */}
          <XAxis
            dataKey="date"
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          
          {/* Left Y Axis: Cost (USD) */}
          <YAxis
            yAxisId="left"
            stroke="#3b82f6"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `$${value.toFixed(2)}`}
            label={{ 
              value: 'Cost (USD)', 
              angle: -90, 
              position: 'insideLeft',
              style: { fontSize: '12px', fill: '#3b82f6' }
            }}
          />
          
          {/* Right Y Axis: Calls */}
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#10b981"
            style={{ fontSize: '12px' }}
            label={{ 
              value: 'Calls', 
              angle: 90, 
              position: 'insideRight',
              style: { fontSize: '12px', fill: '#10b981' }
            }}
          />
          
          <Tooltip content={<CustomTooltip />} />
          
          <Legend 
            wrapperStyle={{ fontSize: '14px' }}
            iconType="line"
          />
          
          {/* Cost line */}
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="cost"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
            name="Cost (USD)"
          />
          
          {/* Calls line */}
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="calls"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 4 }}
            activeDot={{ r: 6 }}
            name="Calls"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
