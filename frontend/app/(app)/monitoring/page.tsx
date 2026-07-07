import { Activity, Gauge, Scale, ShieldAlert, TrendingUp } from 'lucide-react';

const checks = [
  ['Calibration', 'Expected calibration error tracked per model version', '0.06'],
  ['High-priority recall', 'Avoid missing learners who need support', '0.82'],
  ['Fairness review', 'Grouped by gender, grade, school type, region, and tenant', 'Ready'],
  ['Sparse data performance', 'Low-completeness predictions flagged for review', 'Guarded'],
];

export default function MonitoringPage() {
  return (
    <div className="space-y-3 pb-20 md:pb-0">
      <section className="glass-panel rounded-[16px] p-5">
        <p className="eyebrow">MODEL MONITORING</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-text-primary">Trust, fairness, and drift console</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
          Admins can review model quality before using signals operationally. Technical metrics stay here; teachers see plain-language guidance.
        </p>
      </section>

      <section className="grid gap-3 lg:grid-cols-4">
        <Metric icon={Gauge} label="Model version" value="rule-based-v1.0" />
        <Metric icon={Activity} label="Prediction latency" value="<100 ms" />
        <Metric icon={TrendingUp} label="Data completeness" value="62%" />
        <Metric icon={Scale} label="Fairness status" value="Review" />
      </section>

      <section className="grid gap-3 xl:grid-cols-[1fr_.8fr]">
        <div className="glass-panel rounded-[14px] p-4">
          <h2 className="text-lg font-semibold text-text-primary">Deployment gates</h2>
          <div className="mt-4 space-y-2">
            {checks.map(([title, copy, value]) => (
              <div key={title} className="grid gap-3 rounded-[12px] border border-black/10 bg-white/80 p-3 sm:grid-cols-[1fr_auto]">
                <div>
                  <p className="text-sm font-semibold text-text-primary">{title}</p>
                  <p className="mt-1 text-sm text-text-secondary">{copy}</p>
                </div>
                <span className="self-center rounded-[8px] bg-success/10 px-3 py-1 text-sm font-semibold text-success">{value}</span>
              </div>
            ))}
          </div>
        </div>

        <aside className="glass-panel rounded-[14px] p-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-warning" />
            <h2 className="text-lg font-semibold text-text-primary">Safety policy</h2>
          </div>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-text-secondary">
            <li>Predictions are support signals, never discipline or exclusion tools.</li>
            <li>Parents receive recommendations, not raw probabilities.</li>
            <li>Sensitive attributes are restricted to aggregate fairness monitoring.</li>
            <li>Urgent cases require human review and local context.</li>
          </ul>
        </aside>
      </section>
    </div>
  );
}

function Metric({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <article className="glass-panel rounded-[12px] p-4">
      <span className="grid h-9 w-9 place-items-center rounded-[9px] bg-primary/10 text-primary">
        <Icon className="h-4 w-4" />
      </span>
      <p className="mt-3 text-xs text-text-secondary">{label}</p>
      <strong className="mt-1 block text-xl font-semibold text-text-primary">{value}</strong>
    </article>
  );
}
