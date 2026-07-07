'use client';

import * as React from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  HeartHandshake,
  ShieldCheck,
  Smartphone,
  Users,
} from 'lucide-react';
import { RiskBadge } from '@/components/shared/RiskBadge';
import { Button } from '@/components/ui/button';
import { useAssessments, useDashboardStats } from '@/hooks/useAssessments';
import { formatDate } from '@/lib/utils';
import type { Assessment, RiskLevel } from '@/lib/types';

function averageScore(assessment: Assessment) {
  const scores = [assessment.mathScore, assessment.readingScore, assessment.writingScore]
    .filter((score) => Number.isFinite(score));
  if (!scores.length) return 0;
  return Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length);
}

function priorityFor(assessment: Assessment) {
  const risk = assessment.prediction?.riskLevel || 'medium';
  if (risk === 'critical' || assessment.attendancePct < 70) return 'urgent';
  if (risk === 'high' || assessment.attendancePct < 85 || averageScore(assessment) < 55) return 'watch';
  return 'routine';
}

function recommendationFor(assessment: Assessment) {
  if (assessment.attendancePct < 85) return 'Guardian check-in and weekly attendance target';
  if (assessment.literacyLevel <= 4) return 'Daily reading support and short reassessment';
  if (averageScore(assessment) < 55) return 'Two-week subject remediation plan';
  return 'Continue routine monitoring';
}

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: assessmentsData, isLoading: assessmentsLoading } = useAssessments({
    page: 1,
    limit: 8,
  });

  const assessments = assessmentsData?.data || [];
  const supportQueue = [...assessments]
    .sort((a, b) => {
      const rank = { urgent: 0, watch: 1, routine: 2 };
      return rank[priorityFor(a)] - rank[priorityFor(b)];
    })
    .slice(0, 5);

  const urgentCount = supportQueue.filter((item) => priorityFor(item) === 'urgent').length;
  const readiness = stats ? Math.min(100, Math.round((stats.onTrackPct + 70) / 1.7)) : 0;

  return (
    <div className="space-y-3 pb-20 md:pb-0">
      <section className="glass-panel overflow-hidden rounded-[16px] p-5 sm:p-7">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl">
            <p className="eyebrow">STUDENT RETENTION OPERATIONS</p>
            <h1 className="mt-2 text-[30px] font-semibold leading-[1.05] tracking-[-0.04em] text-text-primary sm:text-[42px]">
              Keep more learners in school with a weekly support queue.
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-text-secondary sm:text-base">
              EduSight turns attendance, assessments, and observations into explainable support priorities.
              Every signal is framed for action, not profiling.
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              <Button asChild size="sm">
                <Link href="/assess">
                  <ClipboardList className="mr-2 h-4 w-4" />
                  New assessment
                </Link>
              </Button>
              <Button asChild size="sm" variant="outline">
                <Link href="/students">
                  <Users className="mr-2 h-4 w-4" />
                  Student records
                </Link>
              </Button>
            </div>
          </div>

          <div className="grid min-w-[220px] grid-cols-[104px_1fr] items-center gap-4 rounded-[14px] border border-black/10 bg-white/75 p-4 shadow-sm">
            <div
              className="grid h-[104px] w-[104px] place-items-center rounded-full"
              style={{ background: `conic-gradient(#0071E3 ${readiness}%, rgba(118,118,128,.15) 0)` }}
            >
              <div className="grid h-[78px] w-[78px] place-items-center rounded-full bg-white">
                <span className="text-xl font-semibold">{readiness}%</span>
              </div>
            </div>
            <div>
              <p className="eyebrow">READINESS</p>
              <p className="mt-1 text-sm font-semibold text-text-primary">Data quality gate</p>
              <p className="mt-1 text-xs leading-5 text-text-secondary">
                {statsLoading ? 'Calculating school signal coverage...' : 'Enough data for weekly support review.'}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard icon={Users} label="Learners" value={stats?.totalStudents ?? '...'} note="enrolled" />
        <StatCard icon={CheckCircle2} label="On track" value={`${stats?.onTrackPct ?? '...'}%`} note={`${stats?.onTrackCount ?? 0} learners`} tone="good" />
        <StatCard icon={AlertTriangle} label="Needs review" value={`${stats?.atRiskPct ?? '...'}%`} note={`${stats?.atRiskCount ?? 0} learners`} tone="warn" />
        <StatCard icon={HeartHandshake} label="Interventions" value={stats?.needInterventionCount ?? urgentCount} note="priority actions" tone="danger" />
      </section>

      <section className="grid gap-3 xl:grid-cols-[1.35fr_.65fr]">
        <div className="glass-panel rounded-[14px] p-4 sm:p-5">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <p className="eyebrow">SUPPORT QUEUE</p>
              <h2 className="mt-1 text-xl font-semibold tracking-[-0.03em] text-text-primary">Learners to review this week</h2>
            </div>
            <Button asChild variant="ghost" size="sm">
              <Link href="/students" className="text-primary">
                View all
                <ArrowRight className="ml-1 h-4 w-4" />
              </Link>
            </Button>
          </div>

          <div className="space-y-2">
            {assessmentsLoading ? (
              [1, 2, 3].map((item) => <div key={item} className="h-20 animate-pulse rounded-[12px] bg-white/70" />)
            ) : supportQueue.length ? (
              supportQueue.map((assessment) => {
                const priority = priorityFor(assessment);
                return (
                  <article
                    key={assessment.id}
                    className="grid gap-3 rounded-[12px] border border-black/10 bg-white/80 p-3 shadow-sm sm:grid-cols-[1fr_auto]"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="grid h-9 w-9 place-items-center rounded-[9px] bg-primary text-xs font-bold text-white">
                          {(assessment.studentName || 'S').slice(0, 2).toUpperCase()}
                        </span>
                        <div className="min-w-0">
                          <h3 className="truncate text-sm font-semibold text-text-primary">
                            {assessment.studentName || `Student ${assessment.studentId}`}
                          </h3>
                          <p className="text-xs text-text-secondary">
                            Last assessed {formatDate(assessment.createdAt)}
                          </p>
                        </div>
                        {assessment.prediction?.riskLevel && (
                          <RiskBadge level={assessment.prediction.riskLevel as RiskLevel} size="sm" />
                        )}
                        <span className={priorityClass(priority)}>{priority}</span>
                      </div>
                      <p className="mt-3 text-sm text-text-primary">{recommendationFor(assessment)}</p>
                      <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                        <Signal label="Attendance" value={`${Math.round(assessment.attendancePct || 0)}%`} />
                        <Signal label="Average" value={`${averageScore(assessment)}/100`} />
                        <Signal label="Literacy" value={`${assessment.literacyLevel || 0}/10`} />
                      </div>
                    </div>
                    <div className="flex items-center sm:justify-end">
                      <Button asChild size="sm" variant="outline">
                        <Link href={`/students/${assessment.studentId}`}>Open</Link>
                      </Button>
                    </div>
                  </article>
                );
              })
            ) : (
              <div className="rounded-[12px] border border-dashed border-black/15 bg-white/60 p-8 text-center text-sm text-text-secondary">
                No assessments yet. Create one to populate the weekly support queue.
              </div>
            )}
          </div>
        </div>

        <aside className="space-y-3">
          <div className="glass-panel rounded-[14px] p-5">
            <p className="eyebrow">MODEL TRUST</p>
            <h2 className="mt-1 text-lg font-semibold tracking-[-0.03em]">Decision support, not profiling</h2>
            <ul className="mt-4 space-y-3 text-sm text-text-secondary">
              <TrustItem icon={ShieldCheck} text="Every output should be reviewed by a teacher before action." />
              <TrustItem icon={Activity} text="Model version and feature snapshot are stored with predictions." />
              <TrustItem icon={Smartphone} text="The workflow is designed for low-bandwidth mobile review." />
            </ul>
          </div>

          <div className="glass-panel rounded-[14px] p-5">
            <p className="eyebrow">NEXT BEST ACTIONS</p>
            <div className="mt-4 space-y-3">
              <ActionStep label="1" title="Review urgent learners" copy="Start with attendance and literacy drivers." />
              <ActionStep label="2" title="Confirm context" copy="Check recent events before deciding support." />
              <ActionStep label="3" title="Assign intervention" copy="Track outcomes so the model learns safely." />
            </div>
          </div>
        </aside>
      </section>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  note,
  tone = 'default',
}: {
  icon: React.ElementType;
  label: string;
  value: React.ReactNode;
  note: string;
  tone?: 'default' | 'good' | 'warn' | 'danger';
}) {
  const toneClass = {
    default: 'text-primary bg-primary/10',
    good: 'text-success bg-success/10',
    warn: 'text-warning bg-warning/10',
    danger: 'text-danger bg-danger/10',
  }[tone];
  return (
    <article className="glass-panel grid grid-cols-[1fr_auto] rounded-[12px] p-4">
      <div>
        <p className="text-xs text-text-secondary">{label}</p>
        <strong className="mt-1 block text-2xl font-semibold text-text-primary">{value}</strong>
        <small className="mt-1 block text-xs text-text-secondary">{note}</small>
      </div>
      <span className={`grid h-9 w-9 place-items-center rounded-[9px] ${toneClass}`}>
        <Icon className="h-4 w-4" />
      </span>
    </article>
  );
}

function Signal({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[9px] bg-black/[.035] px-3 py-2">
      <span className="block text-[10px] uppercase tracking-wide text-text-secondary">{label}</span>
      <b className="text-sm text-text-primary">{value}</b>
    </div>
  );
}

function TrustItem({ icon: Icon, text }: { icon: React.ElementType; text: string }) {
  return (
    <li className="flex gap-3">
      <span className="grid h-7 w-7 flex-none place-items-center rounded-[8px] bg-primary/10 text-primary">
        <Icon className="h-4 w-4" />
      </span>
      <span className="leading-5">{text}</span>
    </li>
  );
}

function ActionStep({ label, title, copy }: { label: string; title: string; copy: string }) {
  return (
    <div className="flex gap-3 rounded-[11px] bg-white/75 p-3">
      <span className="grid h-7 w-7 flex-none place-items-center rounded-full bg-success text-xs font-bold text-white">
        {label}
      </span>
      <div>
        <b className="text-sm text-text-primary">{title}</b>
        <p className="mt-1 text-xs leading-5 text-text-secondary">{copy}</p>
      </div>
    </div>
  );
}

function priorityClass(priority: string) {
  if (priority === 'urgent') {
    return 'rounded-full bg-danger/10 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-danger';
  }
  if (priority === 'watch') {
    return 'rounded-full bg-warning/10 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-warning';
  }
  return 'rounded-full bg-success/10 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-success';
}
