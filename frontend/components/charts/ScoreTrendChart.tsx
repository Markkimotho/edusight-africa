'use client';

import * as React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { formatDateShort } from '@/lib/utils';
import type { ScoreDataPoint } from '@/lib/types';

interface ScoreTrendChartProps {
  data: ScoreDataPoint[];
  showRisk?: boolean;
  height?: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 shadow-md text-sm">
      <p className="font-semibold text-text-primary mb-1">
        {label ? formatDateShort(label) : label}
      </p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2 text-xs">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: p.color }}
          />
          <span className="text-text-secondary">{p.name}:</span>
          <span className="font-medium text-text-primary">{p.value}</span>
        </div>
      ))}
    </div>
  );
}

export function ScoreTrendChart({
  data,
  showRisk = false,
  height = 300,
}: ScoreTrendChartProps) {
  const formattedData = data.map((d) => ({
    ...d,
    label: formatDateShort(d.date),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={formattedData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: '#9CA3AF', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: '#9CA3AF', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          formatter={(value) => (
            <span style={{ color: '#6B7280', fontSize: 12 }}>{value}</span>
          )}
        />
        <Line
          type="monotone"
          dataKey="math"
          name="Math"
          stroke="#1B4332"
          strokeWidth={2}
          dot={{ r: 4, fill: '#1B4332', strokeWidth: 0 }}
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="reading"
          name="Reading"
          stroke="#E76F51"
          strokeWidth={2}
          dot={{ r: 4, fill: '#E76F51', strokeWidth: 0 }}
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="writing"
          name="Writing"
          stroke="#F4A261"
          strokeWidth={2}
          dot={{ r: 4, fill: '#F4A261', strokeWidth: 0 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

interface RiskTrendChartProps {
  data: Array<{ date: string; riskProbability: number }>;
  height?: number;
}

export function RiskTrendChart({ data, height = 220 }: RiskTrendChartProps) {
  const formattedData = data.map((d) => ({
    ...d,
    label: formatDateShort(d.date),
    risk: Math.round(d.riskProbability * 100),
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={formattedData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
        <defs>
          <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#DC2626" stopOpacity={0.15} />
            <stop offset="95%" stopColor="#DC2626" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fill: '#9CA3AF', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: '#9CA3AF', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${v}%`}
        />
        <Tooltip
          formatter={(value) => [`${value}%`, 'Risk Probability']}
          labelFormatter={(label) => formatDateShort(label)}
          contentStyle={{
            border: '1px solid #E5E7EB',
            borderRadius: '8px',
            fontSize: '12px',
          }}
        />
        <Area
          type="monotone"
          dataKey="risk"
          name="Risk %"
          stroke="#DC2626"
          strokeWidth={2}
          fill="url(#riskGradient)"
          dot={{ r: 4, fill: '#DC2626', strokeWidth: 0 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
