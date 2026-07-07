import { FileSpreadsheet, FileText, RefreshCcw, UploadCloud } from 'lucide-react';

const formats = ['CSV students', 'CSV attendance', 'Excel assessments', 'Google Sheets export', 'xAPI/Caliper JSON'];

export default function ImportsPage() {
  return (
    <div className="space-y-3 pb-20 md:pb-0">
      <section className="glass-panel rounded-[16px] p-5">
        <p className="eyebrow">DATA INTAKE</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-text-primary">Import, validate, and sync school data</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
          Designed for low-resource schools that move between paper, spreadsheets, and partner systems. Imports should validate before they affect support signals.
        </p>
      </section>

      <section className="grid gap-3 lg:grid-cols-[.8fr_1.2fr]">
        <div className="glass-panel rounded-[14px] p-4">
          <div className="grid min-h-[220px] place-items-center rounded-[12px] border border-dashed border-primary/30 bg-white/70 p-6 text-center">
            <div>
              <UploadCloud className="mx-auto h-10 w-10 text-primary" />
              <h2 className="mt-3 text-base font-semibold text-text-primary">Drop a file to validate</h2>
              <p className="mt-1 text-sm text-text-secondary">CSV and Excel templates are supported in the current V1 workflow.</p>
            </div>
          </div>
        </div>

        <div className="glass-panel rounded-[14px] p-4">
          <h2 className="text-lg font-semibold text-text-primary">Required import checks</h2>
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {formats.map((format) => (
              <div key={format} className="rounded-[12px] border border-black/10 bg-white/80 p-3">
                <FileSpreadsheet className="h-5 w-5 text-primary" />
                <p className="mt-2 text-sm font-semibold text-text-primary">{format}</p>
                <p className="mt-1 text-xs leading-5 text-text-secondary">Schema validation, duplicates, missing fields, and tenant scope.</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-3 lg:grid-cols-3">
        <Step icon={FileText} title="1. Validate" copy="Detect missing IDs, invalid grades, and unsafe sensitive fields." />
        <Step icon={RefreshCcw} title="2. Review" copy="Admins approve import changes before predictions update." />
        <Step icon={UploadCloud} title="3. Sync" copy="Offline entries queue on phones and sync when connectivity returns." />
      </section>
    </div>
  );
}

function Step({ icon: Icon, title, copy }: { icon: any; title: string; copy: string }) {
  return (
    <article className="glass-panel rounded-[12px] p-4">
      <Icon className="h-5 w-5 text-primary" />
      <h2 className="mt-3 text-sm font-semibold text-text-primary">{title}</h2>
      <p className="mt-1 text-sm leading-5 text-text-secondary">{copy}</p>
    </article>
  );
}
