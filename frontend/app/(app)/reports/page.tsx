'use client';

import * as React from 'react';
import {
  BarChart2,
  Download,
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  Calendar,
  RefreshCw,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { MetricCard } from '@/components/shared/MetricCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { SubjectBarChart } from '@/components/charts/SubjectBarChart';
import { RiskDonutChart } from '@/components/charts/RiskDonutChart';
import { useDashboardStats } from '@/hooks/useAssessments';
import { formatPercent } from '@/lib/utils';

const TIME_PERIODS = [
  { value: 'month', label: 'Last Month' },
  { value: 'quarter', label: 'Last Quarter' },
  { value: 'semester', label: 'Last Semester' },
  { value: 'year', label: 'Full Year' },
];

export default function ReportsPage() {
  const [period, setPeriod] = React.useState('quarter');
  const { data: stats, isLoading } = useDashboardStats();

  // Mock trend data for the selected period
  const gradeData = [
    { grade: 'Grade 1', onTrack: 82, atRisk: 14, intervention: 4, total: 45 },
    { grade: 'Grade 2', onTrack: 71, atRisk: 22, intervention: 7, total: 42 },
    { grade: 'Grade 3', onTrack: 65, atRisk: 25, intervention: 10, total: 40 },
    { grade: 'Grade 4', onTrack: 60, atRisk: 28, intervention: 12, total: 38 },
    { grade: 'Grade 5', onTrack: 58, atRisk: 30, intervention: 12, total: 44 },
    { grade: 'Grade 6', onTrack: 55, atRisk: 33, intervention: 12, total: 39 },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        subtitle="Analytics and school-wide insights"
      >
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[160px]">
              <Calendar className="mr-2 h-4 w-4 text-text-secondary" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TIME_PERIODS.map((p) => (
                <SelectItem key={p.value} value={p.value}>
                  {p.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button size="sm">
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </Button>
        </div>
      </PageHeader>

      {/* Overview KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          title="Total Students"
          value={stats?.totalStudents || 248}
          subtitle="Enrolled"
          icon={Users}
          iconColor="text-primary"
          iconBgColor="bg-primary/10"
          trend="up"
          trendValue="+8 vs last period"
        />
        <MetricCard
          title="Avg Assessment Score"
          value="68.4"
          subtitle="All subjects"
          icon={Target}
          iconColor="text-accent"
          iconBgColor="bg-accent/10"
          trend="up"
          trendValue="+2.1 points"
        />
        <MetricCard
          title="Interventions Active"
          value="47"
          subtitle="Ongoing support"
          icon={BarChart2}
          iconColor="text-warning"
          iconBgColor="bg-amber-100"
          trend="neutral"
          trendValue="Stable"
        />
        <MetricCard
          title="Early Identifications"
          value="23"
          subtitle="Before decline"
          icon={TrendingUp}
          iconColor="text-success"
          iconBgColor="bg-emerald-100"
          trend="up"
          trendValue="+5 this period"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Risk Distribution</CardTitle>
            <p className="text-sm text-text-secondary">School-wide risk levels</p>
          </CardHeader>
          <CardContent>
            {stats && <RiskDonutChart data={stats.riskDistribution} />}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Subject Performance Overview</CardTitle>
            <p className="text-sm text-text-secondary">Average scores across all students</p>
          </CardHeader>
          <CardContent>
            {stats && (
              <SubjectBarChart
                data={{
                  math: stats.subjectAverages.math,
                  reading: stats.subjectAverages.reading,
                  writing: stats.subjectAverages.writing,
                }}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Grade breakdown */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">Grade-Level Breakdown</CardTitle>
              <p className="text-sm text-text-secondary mt-0.5">
                Risk distribution by grade
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {gradeData.map((row) => (
              <div key={row.grade}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm font-medium text-text-primary">{row.grade}</span>
                  <div className="flex items-center gap-4 text-xs text-text-secondary">
                    <span>{row.total} students</span>
                    <span className="text-success font-medium">{row.onTrack}% on track</span>
                    {row.atRisk > 25 && (
                      <span className="flex items-center gap-1 text-danger font-medium">
                        <TrendingDown className="h-3 w-3" />
                        High risk
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex h-3 w-full rounded-full overflow-hidden gap-0.5">
                  <div
                    className="bg-success rounded-l-full"
                    style={{ width: `${row.onTrack}%` }}
                    title={`On Track: ${row.onTrack}%`}
                  />
                  <div
                    className="bg-warning"
                    style={{ width: `${row.atRisk}%` }}
                    title={`At Risk: ${row.atRisk}%`}
                  />
                  <div
                    className="bg-danger rounded-r-full"
                    style={{ width: `${row.intervention}%` }}
                    title={`Need Intervention: ${row.intervention}%`}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-6 mt-6 pt-4 border-t border-gray-100">
            {[
              { color: 'bg-success', label: 'On Track' },
              { color: 'bg-warning', label: 'At Risk' },
              { color: 'bg-danger', label: 'Need Intervention' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2 text-xs text-text-secondary">
                <span className={`h-3 w-3 rounded-full ${item.color}`} />
                {item.label}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Insights */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {[
          {
            title: 'Key Insight: Math Performance Declining',
            body: 'Grade 4–6 students show a 4.2% decline in math scores over the past quarter. Consider allocating additional math support resources to upper grades.',
            icon: TrendingDown,
            color: 'border-red-200 bg-red-50',
            iconColor: 'text-danger',
          },
          {
            title: 'Positive Trend: Early Interventions Working',
            body: '89% of students who received early intervention in the previous quarter improved their risk score by at least one level. Continue expanding the program.',
            icon: TrendingUp,
            color: 'border-emerald-200 bg-emerald-50',
            iconColor: 'text-success',
          },
        ].map((insight) => (
          <Card key={insight.title} className={`border-2 ${insight.color}`}>
            <CardContent className="p-5">
              <div className="flex items-start gap-3">
                <insight.icon className={`h-5 w-5 flex-shrink-0 mt-0.5 ${insight.iconColor}`} />
                <div>
                  <p className="font-semibold text-text-primary text-sm">{insight.title}</p>
                  <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                    {insight.body}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
