import * as React from 'react';
import { cn, RISK_BG_COLORS, RISK_LABELS } from '@/lib/utils';
import type { RiskLevel } from '@/lib/types';

interface RiskBadgeProps {
  level: RiskLevel;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
}

const DOT_COLORS: Record<RiskLevel, string> = {
  low: 'bg-emerald-500',
  medium: 'bg-amber-500',
  high: 'bg-orange-500',
  critical: 'bg-red-600',
};

export function RiskBadge({ level, className, size = 'md', showDot = true }: RiskBadgeProps) {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-semibold',
        RISK_BG_COLORS[level],
        sizeClasses[size],
        className
      )}
    >
      {showDot && (
        <span
          className={cn('inline-block rounded-full', DOT_COLORS[level], {
            'h-1.5 w-1.5': size === 'sm' || size === 'md',
            'h-2 w-2': size === 'lg',
          })}
        />
      )}
      {RISK_LABELS[level]}
    </span>
  );
}
