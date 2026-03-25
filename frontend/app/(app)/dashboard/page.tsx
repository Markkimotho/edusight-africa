'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Users,
  CheckCircle,
  AlertTriangle,
  Activity,
  ChevronRight,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { MetricCard } from '@/components/shared/MetricCard';
import { RiskBadge } from '@/components/shared/RiskBadge';
import { RiskDonutChart } from '@/components/charts/RiskDonutChart';
import { SubjectBarChart } from '@/components/charts/SubjectBarChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SkeletonCard, SkeletonRow } from '@/components/shared/LoadingSpinner';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useDashboardStats } from '@/hooks/useAssessments';
import { useAssessments } from '@/hooks/useAssessments';
import { formatDate, formatPercent } from '@/lib/utils';
import type { RiskLevel } from '@/lib/types';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: assessmentsData, isLoading: assessmentsLoading } = useAssessments({
    page: 1,
    limit: 6,
  });

  const assessments = assessmentsData?.data || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle="Student performance overview"
      >
        <Button asChild size="sm">
          <Link href="/assess">
            New Assessment
          </Link>
        </Button>
      </PageHeader>

      {/* KPI Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statsLoading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : stats ? (
          <>
            <MetricCard
              title="Total Students"
              value={stats.totalStudents}
              subtitle="Enrolled this year"
              icon={Users}
              iconColor="text-primary"
              iconBgColor="bg-primary/10"
              trend="up"
              trendValue="+12 this month"
            />
            <MetricCard
              title="On Track"
              value={`${stats.onTrackPct}%`}
              subtitle={`${stats.onTrackCount} students`}
              icon={CheckCircle}
              iconColor="text-success"
              iconBgColor="bg-emerald-100"
              trend="up"
              trendValue="+2.3%"
              valueColor="text-success"
            />
            <MetricCard
              title="At Risk"
              value={`${stats.atRiskPct}%`}
              subtitle={`${stats.atRiskCount} students`}
              icon={AlertTriangle}
              iconColor="text-warning"
              iconBgColor="bg-amber-100"
              trend="down"
              trendValue="-1.1%"
              valueColor="text-warning"
            />
            <MetricCard
              title="Need Intervention"
              value={stats.needInterventionCount}
              subtitle="Immediate action required"
              icon={Activity}
              iconColor="text-danger"
              iconBgColor="bg-red-100"
              trend="neutral"
              trendValue="Stable"
              valueColor="text-danger"
            />
          </>
        ) : null}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Donut chart */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Risk Distribution</CardTitle>
            <p className="text-sm text-text-secondary">Current student risk levels</p>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="h-[280px] flex items-center justify-center">
                <div className="h-32 w-32 rounded-full bg-gray-100 animate-pulse" />
              </div>
            ) : stats ? (
              <RiskDonutChart data={stats.riskDistribution} />
            ) : (
              <div className="h-[280px] flex items-center justify-center text-text-secondary text-sm">
                No data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent assessments */}
        <Card className="lg:col-span-3">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Recent Assessments</CardTitle>
                <p className="text-sm text-text-secondary mt-0.5">Latest student evaluations</p>
              </div>
              <Button asChild variant="ghost" size="sm">
                <Link href="/students" className="flex items-center gap-1 text-primary">
                  View all
                  <ChevronRight className="h-3.5 w-3.5" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            {assessmentsLoading ? (
              <div className="space-y-0">
                {[1, 2, 3, 4].map((i) => (
                  <SkeletonRow key={i} />
                ))}
              </div>
            ) : assessments.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student</TableHead>
                    <TableHead>Risk Level</TableHead>
                    <TableHead>Avg Score</TableHead>
                    <TableHead>Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {assessments.map((assessment) => {
                    const avgScore = Math.round(
                      (assessment.mathScore +
                        assessment.readingScore +
                        assessment.writingScore) /
                        3
                    );
                    return (
                      <TableRow key={assessment.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                              {(assessment.studentName || 'S')
                                .split(' ')
                                .map((n: string) => n[0])
                                .join('')
                                .slice(0, 2)}
                            </div>
                            <span className="font-medium text-text-primary text-sm">
                              {assessment.studentName || `Student ${assessment.studentId}`}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          {assessment.prediction?.riskLevel ? (
                            <RiskBadge
                              level={assessment.prediction.riskLevel as RiskLevel}
                              size="sm"
                            />
                          ) : (
                            <span className="text-xs text-text-secondary">Pending</span>
                          )}
                        </TableCell>
                        <TableCell>
                          <span
                            className={
                              avgScore >= 75
                                ? 'text-success font-semibold'
                                : avgScore >= 55
                                ? 'text-warning font-semibold'
                                : 'text-danger font-semibold'
                            }
                          >
                            {avgScore}
                          </span>
                          <span className="text-xs text-text-secondary">/100</span>
                        </TableCell>
                        <TableCell className="text-text-secondary text-sm">
                          {formatDate(assessment.createdAt)}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            ) : (
              <div className="flex h-40 items-center justify-center text-sm text-text-secondary">
                No assessments recorded yet.{' '}
                <Link href="/assess" className="ml-1 text-primary hover:underline">
                  Create one
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Subject performance */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Subject Performance</CardTitle>
          <p className="text-sm text-text-secondary">
            Average scores across all students this term
          </p>
        </CardHeader>
        <CardContent>
          {statsLoading ? (
            <div className="h-[240px] animate-pulse bg-gray-50 rounded-lg" />
          ) : stats ? (
            <SubjectBarChart data={stats.subjectAverages} />
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
