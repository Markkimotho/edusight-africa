'use client';

import * as React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import {
  ArrowLeft,
  User,
  GraduationCap,
  Calendar,
  Phone,
  ClipboardList,
  TrendingUp,
  Heart,
  Activity,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { RiskBadge } from '@/components/shared/RiskBadge';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ScoreTrendChart, RiskTrendChart } from '@/components/charts/ScoreTrendChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useStudent, useStudentAssessments, useStudentObservations } from '@/hooks/useStudents';
import { formatDate, getInitials, cn, formatPercent } from '@/lib/utils';
import type { RiskLevel } from '@/lib/types';

function generateScoreHistory(assessments: Array<{
  createdAt: string;
  mathScore: number;
  readingScore: number;
  writingScore: number;
  prediction?: { riskProbability?: number } | null;
}>) {
  if (!assessments.length) {
    // Generate mock history
    return Array.from({ length: 6 }, (_, i) => ({
      date: new Date(Date.now() - (5 - i) * 30 * 86400000).toISOString(),
      math: Math.floor(Math.random() * 30) + 55,
      reading: Math.floor(Math.random() * 30) + 55,
      writing: Math.floor(Math.random() * 30) + 55,
      riskProbability: Math.random() * 0.6,
    }));
  }
  return assessments.map((a) => ({
    date: a.createdAt,
    math: a.mathScore,
    reading: a.readingScore,
    writing: a.writingScore,
    riskProbability: a.prediction?.riskProbability || 0,
  }));
}

export default function StudentDetailPage() {
  const params = useParams();
  const studentId = params.id as string;

  const { data: student, isLoading: studentLoading } = useStudent(studentId);
  const { data: assessments = [] } = useStudentAssessments(studentId);
  const { data: observations = [] } = useStudentObservations(studentId);

  const scoreHistory = generateScoreHistory(assessments);

  const mockInterventions = [
    {
      id: '1',
      title: 'Extra Math Support',
      category: 'academic',
      status: 'active',
      startDate: '2024-09-01',
    },
    {
      id: '2',
      title: 'Reading Circle Group',
      category: 'academic',
      status: 'active',
      startDate: '2024-08-15',
    },
  ];

  if (studentLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <LoadingSpinner size="lg" label="Loading student profile..." />
      </div>
    );
  }

  if (!student) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <h2 className="text-xl font-semibold text-text-primary mb-2">Student not found</h2>
        <Button asChild variant="outline">
          <Link href="/students">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Students
          </Link>
        </Button>
      </div>
    );
  }

  const latestAssessment = assessments[0];
  const avgScore = scoreHistory.length
    ? Math.round(
        scoreHistory.reduce((sum, s) => sum + (s.math + s.reading + s.writing) / 3, 0) /
          scoreHistory.length
      )
    : null;

  return (
    <div className="space-y-6">
      {/* Back + Header */}
      <div className="flex items-center gap-3">
        <Button asChild variant="ghost" size="sm">
          <Link href="/students">
            <ArrowLeft className="mr-1 h-4 w-4" />
            Students
          </Link>
        </Button>
      </div>

      {/* Profile header card */}
      <Card className="overflow-hidden">
        <div className="gradient-primary px-6 pt-6 pb-16" />
        <CardContent className="-mt-10 p-6">
          <div className="flex flex-col sm:flex-row sm:items-end gap-4">
            {/* Avatar */}
            <div className="h-20 w-20 rounded-2xl bg-white border-4 border-white shadow-lg flex items-center justify-center text-2xl font-bold text-primary flex-shrink-0">
              {getInitials(student.name)}
            </div>

            {/* Info */}
            <div className="flex-1">
              <div className="flex flex-wrap items-start gap-3">
                <div>
                  <h1 className="text-xl font-bold text-text-primary">{student.name}</h1>
                  <p className="text-sm text-text-secondary">{student.grade}</p>
                </div>
                {student.currentRiskLevel && (
                  <RiskBadge level={student.currentRiskLevel as RiskLevel} size="md" />
                )}
              </div>

              <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  {
                    icon: User,
                    label: 'Guardian',
                    value: student.guardianName || '—',
                  },
                  {
                    icon: Phone,
                    label: 'Contact',
                    value: student.guardianContact || '—',
                  },
                  {
                    icon: Calendar,
                    label: 'Enrolled',
                    value: formatDate(student.enrollmentDate),
                  },
                  {
                    icon: ClipboardList,
                    label: 'Assessments',
                    value: String(student.totalAssessments || 0),
                  },
                ].map((item) => (
                  <div key={item.label} className="flex items-start gap-2">
                    <item.icon className="h-4 w-4 text-text-secondary mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-text-secondary">{item.label}</p>
                      <p className="text-sm font-medium text-text-primary truncate">
                        {item.value}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick stats */}
            <div className="flex gap-3">
              {avgScore !== null && (
                <div className="rounded-xl bg-gray-50 border border-gray-200 p-3 text-center min-w-[80px]">
                  <p className="text-2xl font-bold text-text-primary">{avgScore}</p>
                  <p className="text-xs text-text-secondary">Avg Score</p>
                </div>
              )}
              {latestAssessment?.prediction && (
                <div className="rounded-xl bg-gray-50 border border-gray-200 p-3 text-center min-w-[80px]">
                  <p className="text-2xl font-bold text-text-primary">
                    {formatPercent(
                      (latestAssessment.prediction.riskProbability || 0) * 100,
                      0
                    )}
                  </p>
                  <p className="text-xs text-text-secondary">Risk Prob.</p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="performance">
        <TabsList>
          <TabsTrigger value="performance">
            <TrendingUp className="h-4 w-4 mr-1.5" />
            Performance
          </TabsTrigger>
          <TabsTrigger value="assessments">
            <ClipboardList className="h-4 w-4 mr-1.5" />
            Assessments
          </TabsTrigger>
          <TabsTrigger value="interventions">
            <Activity className="h-4 w-4 mr-1.5" />
            Interventions
          </TabsTrigger>
          <TabsTrigger value="observations">
            <Heart className="h-4 w-4 mr-1.5" />
            Parent Observations
          </TabsTrigger>
        </TabsList>

        {/* Performance tab */}
        <TabsContent value="performance" className="mt-4 space-y-4">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Score History</CardTitle>
                <p className="text-xs text-text-secondary">Math, Reading & Writing over time</p>
              </CardHeader>
              <CardContent>
                <ScoreTrendChart data={scoreHistory} height={240} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Risk Trajectory</CardTitle>
                <p className="text-xs text-text-secondary">Risk probability over time</p>
              </CardHeader>
              <CardContent>
                <RiskTrendChart data={scoreHistory} height={240} />
              </CardContent>
            </Card>
          </div>

          {/* Score breakdown */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Current Score Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                {[
                  {
                    label: 'Math',
                    score: student.averageMathScore,
                    color: 'bg-primary',
                  },
                  {
                    label: 'Reading',
                    score: student.averageReadingScore,
                    color: 'bg-accent',
                  },
                  {
                    label: 'Writing',
                    score: student.averageWritingScore,
                    color: 'bg-accent-light',
                  },
                ].map((item) => (
                  <div key={item.label}>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="font-medium text-text-primary">{item.label}</span>
                      <span className="font-bold text-text-primary">
                        {item.score !== undefined ? Math.round(item.score) : '—'}
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
                      <div
                        className={cn('h-full rounded-full', item.color)}
                        style={{ width: `${item.score || 0}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Assessments tab */}
        <TabsContent value="assessments" className="mt-4">
          <Card>
            <CardContent className="p-0">
              {assessments.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="pl-6">Date</TableHead>
                      <TableHead>Math</TableHead>
                      <TableHead>Reading</TableHead>
                      <TableHead>Writing</TableHead>
                      <TableHead>Attendance</TableHead>
                      <TableHead>Risk Level</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {assessments.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell className="pl-6 text-sm">
                          {formatDate(a.createdAt)}
                        </TableCell>
                        <TableCell>
                          <span className={cn(
                            'font-semibold',
                            a.mathScore >= 75 ? 'text-success' : a.mathScore >= 55 ? 'text-warning' : 'text-danger'
                          )}>
                            {a.mathScore}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className={cn(
                            'font-semibold',
                            a.readingScore >= 75 ? 'text-success' : a.readingScore >= 55 ? 'text-warning' : 'text-danger'
                          )}>
                            {a.readingScore}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className={cn(
                            'font-semibold',
                            a.writingScore >= 75 ? 'text-success' : a.writingScore >= 55 ? 'text-warning' : 'text-danger'
                          )}>
                            {a.writingScore}
                          </span>
                        </TableCell>
                        <TableCell className="text-sm">{a.attendancePct}%</TableCell>
                        <TableCell>
                          {a.prediction?.riskLevel ? (
                            <RiskBadge level={a.prediction.riskLevel as RiskLevel} size="sm" />
                          ) : (
                            <span className="text-xs text-text-secondary">Pending</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <ClipboardList className="h-12 w-12 text-gray-200 mb-3" />
                  <h3 className="font-medium text-text-primary mb-1">No assessments yet</h3>
                  <p className="text-sm text-text-secondary mb-4">
                    No assessments recorded for this student
                  </p>
                  <Button asChild size="sm">
                    <Link href="/assess">Create Assessment</Link>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Interventions tab */}
        <TabsContent value="interventions" className="mt-4">
          <Card>
            <CardContent className="p-6">
              {mockInterventions.length > 0 ? (
                <div className="space-y-3">
                  {mockInterventions.map((intervention) => (
                    <div
                      key={intervention.id}
                      className="flex items-start gap-4 rounded-xl border border-gray-200 p-4"
                    >
                      <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                        {intervention.status === 'active' ? (
                          <CheckCircle2 className="h-5 w-5 text-primary" />
                        ) : (
                          <Clock className="h-5 w-5 text-text-secondary" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-semibold text-text-primary">{intervention.title}</p>
                            <p className="text-xs text-text-secondary capitalize">
                              {intervention.category} · Started {formatDate(intervention.startDate)}
                            </p>
                          </div>
                          <span
                            className={cn(
                              'text-xs font-semibold px-2 py-0.5 rounded-full capitalize',
                              intervention.status === 'active'
                                ? 'bg-emerald-100 text-emerald-800'
                                : 'bg-gray-100 text-gray-600'
                            )}
                          >
                            {intervention.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Activity className="h-12 w-12 text-gray-200 mb-3" />
                  <h3 className="font-medium text-text-primary">No active interventions</h3>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Observations tab */}
        <TabsContent value="observations" className="mt-4">
          <Card>
            <CardContent className="p-6">
              {observations.length > 0 ? (
                <div className="space-y-3">
                  {observations.map((obs) => (
                    <div
                      key={obs.id}
                      className="rounded-xl border border-gray-200 p-4 space-y-3"
                    >
                      <div className="flex items-center justify-between">
                        <p className="font-semibold text-text-primary text-sm">
                          {formatDate(obs.observationDate || obs.createdAt)}
                        </p>
                        <span className="text-2xl">
                          {obs.mood === 5
                            ? '😊'
                            : obs.mood === 4
                            ? '🙂'
                            : obs.mood === 3
                            ? '😐'
                            : obs.mood === 2
                            ? '😕'
                            : '😢'}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-sm">
                        <div>
                          <p className="text-xs text-text-secondary">Homework</p>
                          <p className="font-medium">{obs.homeworkCompletion}%</p>
                        </div>
                        <div>
                          <p className="text-xs text-text-secondary">Reading</p>
                          <p className="font-medium">{obs.readingMinutes} min</p>
                        </div>
                        <div>
                          <p className="text-xs text-text-secondary">Sleep</p>
                          <p className="font-medium">{obs.sleepHours}h</p>
                        </div>
                      </div>
                      {obs.notes && (
                        <p className="text-xs text-text-secondary bg-gray-50 rounded-lg p-2">
                          {obs.notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Heart className="h-12 w-12 text-gray-200 mb-3" />
                  <h3 className="font-medium text-text-primary">No parent observations yet</h3>
                  <p className="text-sm text-text-secondary mt-1">
                    Encourage the guardian to use the Parent Portal
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
