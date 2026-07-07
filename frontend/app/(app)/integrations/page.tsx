import { Code2, KeyRound, PlugZap, ShieldCheck, Webhook } from 'lucide-react';

const endpoints = [
  ['POST', '/api/v1/integrations/students', 'Upsert a partner learner record'],
  ['POST', '/api/v1/integrations/events', 'Ingest attendance, assessment, behavior, or LMS events'],
  ['POST', '/api/v1/integrations/assessments', 'Persist assessment and generate support signal'],
  ['POST', '/api/v1/integrations/predict', 'Synchronous prediction without persistence'],
  ['GET', '/api/v1/integrations/model-version', 'Current model metadata and feature contract'],
  ['POST', '/api/v1/webhooks/test', 'Validate webhook configuration'],
];

export default function IntegrationsPage() {
  return (
    <div className="space-y-3 pb-20 md:pb-0">
      <section className="glass-panel rounded-[16px] p-5">
        <p className="eyebrow">PARTNER INTEGRATION MODULE</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-text-primary">Embed EduSight in high-end edtech platforms</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
          Use API keys, event ingestion, synchronous prediction, and white-label UI surfaces. Outputs are support signals for human review.
        </p>
      </section>

      <section className="grid gap-3 lg:grid-cols-4">
        <Card icon={KeyRound} title="API keys" copy="Scoped partner keys with hashed storage and last-used tracking." />
        <Card icon={PlugZap} title="Event ingestion" copy="Attendance, behavior, assessment, assignment, and LMS activity events." />
        <Card icon={Webhook} title="Webhooks" copy="Test endpoint and event envelope ready for outbound delivery." />
        <Card icon={ShieldCheck} title="Governance" copy="No punitive recommendations, no raw parent-facing risk probabilities." />
      </section>

      <section className="glass-panel rounded-[14px] p-4">
        <div className="mb-4 flex items-center gap-2">
          <Code2 className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-text-primary">Integration contract</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="text-xs uppercase text-text-secondary">
              <tr>
                <th className="border-b border-black/10 py-2">Method</th>
                <th className="border-b border-black/10 py-2">Endpoint</th>
                <th className="border-b border-black/10 py-2">Purpose</th>
              </tr>
            </thead>
            <tbody>
              {endpoints.map(([method, path, purpose]) => (
                <tr key={path}>
                  <td className="border-b border-black/5 py-3">
                    <span className="rounded-[7px] bg-primary/10 px-2 py-1 text-xs font-semibold text-primary">{method}</span>
                  </td>
                  <td className="border-b border-black/5 py-3 font-mono text-xs text-text-primary">{path}</td>
                  <td className="border-b border-black/5 py-3 text-text-secondary">{purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function Card({ icon: Icon, title, copy }: { icon: any; title: string; copy: string }) {
  return (
    <article className="glass-panel rounded-[12px] p-4">
      <span className="grid h-10 w-10 place-items-center rounded-[10px] bg-primary/10 text-primary">
        <Icon className="h-5 w-5" />
      </span>
      <h2 className="mt-3 text-sm font-semibold text-text-primary">{title}</h2>
      <p className="mt-1 text-sm leading-5 text-text-secondary">{copy}</p>
    </article>
  );
}
