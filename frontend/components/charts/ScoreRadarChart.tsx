'use client';

import * as React from 'react';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import type { RadarDataPoint } from '@/lib/types';

interface ScoreRadarChartProps {
  data?: RadarDataPoint[];
  mathScore?: number;
  readingScore?: number;
  writingScore?: number;
  attendancePct?: number;
  behaviorRating?: number;
  literacyLevel?: number;
  height?: number;
}

const BASELINE = {
  Math: 75,
  Reading: 75,
  Writing: 75,
  Attendance: 85,
  Behavior: 75,
  Literacy: 70,
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 shadow-md text-sm">
      <p className="font-semibold text-text-primary mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }} className="text-xs">
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
}

export function ScoreRadarChart({
  data,
  mathScore,
  readingScore,
  writingScore,
  attendancePct,
  behaviorRating,
  literacyLevel,
  height = 320,
}: ScoreRadarChartProps) {
  // If raw scores are passed, build the data from them
  const chartData: RadarDataPoint[] = data || [
    {
      subject: 'Math',
      student: mathScore ?? 0,
      baseline: BASELINE.Math,
    },
    {
      subject: 'Reading',
      student: readingScore ?? 0,
      baseline: BASELINE.Reading,
    },
    {
      subject: 'Writing',
      student: writingScore ?? 0,
      baseline: BASELINE.Writing,
    },
    {
      subject: 'Attendance',
      student: attendancePct ?? 0,
      baseline: BASELINE.Attendance,
    },
    {
      subject: 'Behavior',
      // Convert 1-5 scale to 0-100
      student: behaviorRating ? (behaviorRating / 5) * 100 : 0,
      baseline: BASELINE.Behavior,
    },
    {
      subject: 'Literacy',
      // Convert 1-10 scale to 0-100
      student: literacyLevel ? (literacyLevel / 10) * 100 : 0,
      baseline: BASELINE.Literacy,
    },
  ];

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={chartData} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
        <PolarGrid stroke="#E5E7EB" />
        <PolarAngleAxis
          dataKey="subject"
          tick={{ fill: '#6B7280', fontSize: 12, fontWeight: 500 }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fill: '#9CA3AF', fontSize: 10 }}
          tickCount={5}
        />
        <Radar
          name="Healthy Baseline"
          dataKey="baseline"
          stroke="#D1D5DB"
          fill="#F3F4F6"
          fillOpacity={0.5}
          strokeDasharray="5 5"
        />
        <Radar
          name="Student"
          dataKey="student"
          stroke="#1B4332"
          fill="#1B4332"
          fillOpacity={0.25}
          strokeWidth={2}
        />
        <Legend
          formatter={(value) => (
            <span style={{ color: '#6B7280', fontSize: 12 }}>{value}</span>
          )}
        />
        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
