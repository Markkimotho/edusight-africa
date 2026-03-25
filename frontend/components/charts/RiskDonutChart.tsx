'use client';

import * as React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { RISK_COLORS } from '@/lib/utils';

interface RiskDonutChartProps {
  data: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  height?: number;
}

const LABELS = {
  low: 'Low Risk',
  medium: 'Medium Risk',
  high: 'High Risk',
  critical: 'Critical',
};

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    payload: { total: number };
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0];
  const total = item.payload.total;
  const pct = total > 0 ? ((item.value / total) * 100).toFixed(1) : '0';

  return (
    <div className="rounded-lg border border-gray-200 bg-white px-3 py-2 shadow-md text-sm">
      <p className="font-semibold text-text-primary">{item.name}</p>
      <p className="text-text-secondary">
        {item.value} students ({pct}%)
      </p>
    </div>
  );
}

interface CustomLegendProps {
  payload?: Array<{
    color: string;
    value: string;
  }>;
}

function CustomLegend({ payload }: CustomLegendProps) {
  return (
    <div className="flex flex-col gap-2 mt-2">
      {payload?.map((entry) => (
        <div key={entry.value} className="flex items-center gap-2 text-sm">
          <span
            className="inline-block h-3 w-3 rounded-full flex-shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-text-secondary">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

export function RiskDonutChart({ data, height = 280 }: RiskDonutChartProps) {
  const total = data.low + data.medium + data.high + data.critical;

  const chartData = [
    { name: LABELS.low, value: data.low, key: 'low', total },
    { name: LABELS.medium, value: data.medium, key: 'medium', total },
    { name: LABELS.high, value: data.high, key: 'high', total },
    { name: LABELS.critical, value: data.critical, key: 'critical', total },
  ].filter((d) => d.value > 0);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={chartData}
          cx="40%"
          cy="50%"
          innerRadius={70}
          outerRadius={110}
          paddingAngle={3}
          dataKey="value"
          strokeWidth={0}
        >
          {chartData.map((entry) => (
            <Cell
              key={entry.key}
              fill={RISK_COLORS[entry.key as keyof typeof RISK_COLORS]}
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          layout="vertical"
          align="right"
          verticalAlign="middle"
          content={<CustomLegend />}
        />
        {/* Center label */}
        <text x="40%" y="50%" textAnchor="middle" dominantBaseline="middle">
          <tspan
            x="40%"
            dy="-0.5em"
            style={{
              fontSize: '28px',
              fontWeight: 700,
              fill: '#1A1A2E',
            }}
          >
            {total}
          </tspan>
          <tspan
            x="40%"
            dy="1.5em"
            style={{
              fontSize: '12px',
              fill: '#6B7280',
            }}
          >
            Students
          </tspan>
        </text>
      </PieChart>
    </ResponsiveContainer>
  );
}
