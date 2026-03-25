import * as React from 'react';
import { TrendingUp, TrendingDown, Minus, type LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon: LucideIcon;
  iconColor?: string;
  iconBgColor?: string;
  className?: string;
  valueColor?: string;
}

const trendConfig = {
  up: {
    icon: TrendingUp,
    color: 'text-success',
    label: 'increase',
  },
  down: {
    icon: TrendingDown,
    color: 'text-danger',
    label: 'decrease',
  },
  neutral: {
    icon: Minus,
    color: 'text-text-secondary',
    label: 'no change',
  },
};

export function MetricCard({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon: Icon,
  iconColor = 'text-primary',
  iconBgColor = 'bg-primary/10',
  className,
  valueColor = 'text-text-primary',
}: MetricCardProps) {
  const TrendIcon = trend ? trendConfig[trend].icon : null;
  const trendColor = trend ? trendConfig[trend].color : '';

  return (
    <Card className={cn('relative overflow-hidden', className)}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-text-secondary">{title}</p>
            <p className={cn('mt-2 text-3xl font-bold', valueColor)}>{value}</p>
            {(subtitle || (trend && trendValue)) && (
              <div className="mt-2 flex items-center gap-2">
                {trend && TrendIcon && trendValue && (
                  <span className={cn('flex items-center gap-1 text-xs font-medium', trendColor)}>
                    <TrendIcon className="h-3.5 w-3.5" />
                    {trendValue}
                  </span>
                )}
                {subtitle && (
                  <span className="text-xs text-text-secondary">{subtitle}</span>
                )}
              </div>
            )}
          </div>
          <div className={cn('flex h-12 w-12 items-center justify-center rounded-xl', iconBgColor)}>
            <Icon className={cn('h-6 w-6', iconColor)} />
          </div>
        </div>

        {/* Decorative gradient bar */}
        <div
          className="absolute bottom-0 left-0 right-0 h-1 rounded-b-xl"
          style={{
            background: 'linear-gradient(90deg, #1B4332, #2D6A4F)',
          }}
        />
      </CardContent>
    </Card>
  );
}
