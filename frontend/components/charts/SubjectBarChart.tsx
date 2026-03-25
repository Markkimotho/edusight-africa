'use client';

import * as React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

interface SubjectBarChartProps {
  data: {
    math: number;
    reading: number;
    writing: number;
  };
  height?: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ value: number; payload: { subject: string; score: number; color: string } }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 shadow-md text-sm">
      <p className="font-semibold text-text-primary">{item.subject}</p>
      <p className="text-text-secondary">
        Average: <span className="font-bold text-text-primary">{item.score}</span>/100
      </p>
    </div>
  );
}

interface CustomLabelProps {
  x?: number;
  y?: number;
  width?: number;
  value?: number;
}

function CustomLabel({ x = 0, y = 0, width = 0, value = 0 }: CustomLabelProps) {
  return (
    <text
      x={x + width / 2}
      y={y - 6}
      fill="#1A1A2E"
      textAnchor="middle"
      fontSize={13}
      fontWeight={600}
    >
      {value}
    </text>
  );
}

export function SubjectBarChart({ data, height = 240 }: SubjectBarChartProps) {
  const chartData = [
    { subject: 'Math', score: Math.round(data.math), color: '#1B4332' },
    { subject: 'Reading', score: Math.round(data.reading), color: '#2D6A4F' },
    { subject: 'Writing', score: Math.round(data.writing), color: '#E76F51' },
  ];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={chartData}
        margin={{ top: 24, right: 10, left: -15, bottom: 5 }}
        barSize={56}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" horizontal={true} vertical={false} />
        <XAxis
          dataKey="subject"
          tick={{ fill: '#6B7280', fontSize: 13, fontWeight: 500 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fill: '#9CA3AF', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <ReferenceLine y={75} stroke="#E5E7EB" strokeDasharray="4 4" label="" />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
        <Bar dataKey="score" radius={[8, 8, 0, 0]} label={<CustomLabel />}>
          {chartData.map((entry) => (
            <Cell key={entry.subject} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
