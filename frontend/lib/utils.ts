import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { RiskLevel } from './types';

// ─── Class name utility ───────────────────────────────────────────────────────

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ─── Risk level utilities ─────────────────────────────────────────────────────

export const RISK_COLORS: Record<RiskLevel, string> = {
  low: '#059669',
  medium: '#D97706',
  high: '#E76F51',
  critical: '#DC2626',
};

export const RISK_BG_COLORS: Record<RiskLevel, string> = {
  low: 'bg-emerald-100 text-emerald-800',
  medium: 'bg-amber-100 text-amber-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

export const RISK_LABELS: Record<RiskLevel, string> = {
  low: 'Low Risk',
  medium: 'Medium Risk',
  high: 'High Risk',
  critical: 'Critical',
};

// ─── Formatters ───────────────────────────────────────────────────────────────

export function formatDate(date: string | Date, locale = 'en-US'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateShort(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
}

export function formatPercent(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatScore(value: number): string {
  return value.toFixed(0);
}

export function formatProbability(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

// ─── Score utilities ──────────────────────────────────────────────────────────

export function getScoreColor(score: number): string {
  if (score >= 80) return 'text-success';
  if (score >= 60) return 'text-warning';
  return 'text-danger';
}

export function scoreToRisk(probability: number): RiskLevel {
  if (probability < 0.25) return 'low';
  if (probability < 0.5) return 'medium';
  if (probability < 0.75) return 'high';
  return 'critical';
}

// ─── Trend utilities ──────────────────────────────────────────────────────────

export type TrendDirection = 'up' | 'down' | 'neutral';

export function getTrend(current: number, previous: number): TrendDirection {
  const diff = current - previous;
  if (Math.abs(diff) < 2) return 'neutral';
  return diff > 0 ? 'up' : 'down';
}

// ─── String utilities ─────────────────────────────────────────────────────────

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
}

export function getInitials(name?: string | null): string {
  const safeName = name?.trim() || 'Student';
  return safeName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

// ─── Feature label mapping ────────────────────────────────────────────────────

export const FEATURE_LABELS: Record<string, string> = {
  math_score: 'Math Score',
  reading_score: 'Reading Score',
  writing_score: 'Writing Score',
  attendance_pct: 'Attendance',
  behavior_rating: 'Behavior',
  literacy_level: 'Literacy Level',
  homework_completion: 'Homework',
  reading_minutes: 'Reading Time',
  sleep_hours: 'Sleep',
};

export function getFeatureLabel(feature: string): string {
  return FEATURE_LABELS[feature] || capitalize(feature.replace(/_/g, ' '));
}
