import * as React from 'react';
import Link from 'next/link';
import { TrendingUp, TrendingDown, Minus, User } from 'lucide-react';
import { cn, formatDate, getInitials } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { RiskBadge } from './RiskBadge';
import type { StudentWithStats } from '@/lib/types';

interface StudentCardProps {
  student: StudentWithStats;
  className?: string;
}

const trendIcons = {
  improving: { icon: TrendingUp, color: 'text-success', label: 'Improving' },
  declining: { icon: TrendingDown, color: 'text-danger', label: 'Declining' },
  stable: { icon: Minus, color: 'text-text-secondary', label: 'Stable' },
};

export function StudentCard({ student, className }: StudentCardProps) {
  const trend = student.trend ? trendIcons[student.trend] : null;
  const TrendIcon = trend?.icon;

  const avgScore =
    ((student.averageMathScore || 0) +
      (student.averageReadingScore || 0) +
      (student.averageWritingScore || 0)) /
    3;

  return (
    <Link href={`/students/${student.id}`}>
      <Card
        className={cn(
          'hover:shadow-md transition-shadow duration-200 cursor-pointer',
          className
        )}
      >
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            {/* Avatar */}
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-white text-sm font-bold flex-shrink-0">
              {getInitials(student.name)}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-text-primary truncate">{student.name}</h3>
                  <p className="text-sm text-text-secondary">{student.grade}</p>
                </div>
                {student.currentRiskLevel && (
                  <RiskBadge level={student.currentRiskLevel} size="sm" />
                )}
              </div>

              <div className="mt-3 flex items-center justify-between">
                <div className="text-xs text-text-secondary">
                  {student.lastAssessmentDate ? (
                    <span>Last: {formatDate(student.lastAssessmentDate)}</span>
                  ) : (
                    <span>No assessments yet</span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {avgScore > 0 && (
                    <span className="text-sm font-semibold text-text-primary">
                      {Math.round(avgScore)}
                      <span className="text-xs text-text-secondary">/100</span>
                    </span>
                  )}
                  {trend && TrendIcon && (
                    <span className={cn('flex items-center gap-0.5 text-xs', trend.color)}>
                      <TrendIcon className="h-3.5 w-3.5" />
                      {trend.label}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
