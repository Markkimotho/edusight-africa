'use client';

import Link from 'next/link';
import { AlertTriangle, CheckCircle2, ClipboardCheck, MessageSquare, UserRoundCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCreateInterventionFromSignal, useSupportQueue, useSupportSummary } from '@/hooks/useSupport';

export default function SupportPage() {
  const { data: items = [], isLoading } = useSupportQueue(25);
  const { data: summary } = useSupportSummary();
  const createPlan = useCreateInterventionFromSignal();

  return (
    <div className="space-y-3 pb-20 md:pb-0">
      <section className="glass-panel rounded-[16px] p-5">
        <p className="eyebrow">SUPPORT QUEUE</p>
        <div className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-semibold tracking-[-0.04em] text-text-primary">Intervention workbench</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-text-secondary">
              Prioritize support without profiling learners. Every urgent item should be reviewed by a human before action.
            </p>
          </div>
          <Button asChild size="sm">
            <Link href="/assess">
              <ClipboardCheck className="mr-2 h-4 w-4" />
              Record update
            </Link>
          </Button>
        </div>
      </section>

      <section className="grid gap-3 lg:grid-cols-3">
        <Summary icon={AlertTriangle} label="Urgent review" value={summary?.urgent ?? items.filter((item) => item.supportLevel === 'urgent').length} />
        <Summary icon={UserRoundCheck} label="Watch list" value={summary?.watch ?? items.filter((item) => item.supportLevel === 'watch').length} />
        <Summary icon={CheckCircle2} label="Open plans" value={summary?.openInterventions ?? items.reduce((sum, item) => sum + item.openInterventions, 0)} />
      </section>

      <section className="glass-panel rounded-[14px] p-4">
        <div className="space-y-2">
          {isLoading ? (
            [1, 2, 3, 4].map((item) => <div key={item} className="h-24 animate-pulse rounded-[12px] bg-white/70" />)
          ) : items.length ? (
            items.map((item) => (
              <article key={`${item.studentId}-${item.latestAssessmentId}`} className="rounded-[12px] border border-black/10 bg-white/85 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-[8px] bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
                        {item.supportLevel}
                      </span>
                      <h2 className="text-sm font-semibold text-text-primary">{item.studentName}</h2>
                      <span className="text-xs text-text-secondary">Grade {item.gradeLevel}</span>
                    </div>
                    <p className="mt-2 text-sm text-text-secondary">
                      {item.recommendedActions[0] || 'Review learner context and decide the next support action.'}
                    </p>
                    {item.riskDrivers.length > 0 && (
                      <p className="mt-1 text-xs text-text-secondary">
                        Driver: {String(item.riskDrivers[0].label || item.riskDrivers[0].feature)}
                      </p>
                    )}
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center text-xs sm:w-[260px]">
                    <Metric label="Attendance" value={`${Math.round(item.attendancePct || 0)}%`} />
                    <Metric label="Average" value={item.academicAverage ? `${item.academicAverage}/100` : 'n/a'} />
                    <Metric label="Signal" value={item.riskLevel} />
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={createPlan.isPending}
                    onClick={() =>
                      createPlan.mutate({
                        studentId: item.studentId,
                        assessmentId: item.latestAssessmentId,
                        action: item.recommendedActions[0] || 'Teacher review and support check-in',
                        interventionType:
                          item.attendancePct !== undefined && item.attendancePct < 85
                            ? 'attendance'
                            : item.riskDrivers.some((driver) => String(driver.feature).includes('behavior'))
                              ? 'behavioral'
                              : 'academic',
                      })
                    }
                  >
                    Create plan
                  </Button>
                  <Button size="sm" variant="ghost">
                    <MessageSquare className="mr-2 h-4 w-4" />
                    Parent note
                  </Button>
                </div>
              </article>
            ))
          ) : (
            <div className="rounded-[12px] border border-dashed border-black/15 bg-white/70 p-8 text-center text-sm text-text-secondary">
              No support items yet. Record an assessment to generate the first queue.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function Summary({ icon: Icon, label, value }: { icon: any; label: string; value: number }) {
  return (
    <div className="glass-panel flex items-center justify-between rounded-[12px] p-4">
      <div>
        <p className="text-xs text-text-secondary">{label}</p>
        <p className="mt-1 text-2xl font-semibold text-text-primary">{value}</p>
      </div>
      <span className="grid h-10 w-10 place-items-center rounded-[10px] bg-primary/10 text-primary">
        <Icon className="h-5 w-5" />
      </span>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[9px] bg-black/[.035] px-2 py-2">
      <span className="block text-[10px] uppercase text-text-secondary">{label}</span>
      <b className="text-text-primary">{value}</b>
    </div>
  );
}
