import { Languages, Moon, Palette, Shield, WifiOff } from 'lucide-react';

const settings = [
  ['Terminology', 'Use early warning signal and intervention priority in teacher workflows.'],
  ['Thresholds', 'Tune support levels per tenant while keeping human review gates.'],
  ['Branding', 'White-label colors, logo, and partner display name.'],
  ['Languages', 'English, Kiswahili, French, Arabic, Amharic, Hausa, Yoruba, isiZulu, and more.'],
  ['Data retention', 'Configure retention, deletion, and anonymized exports by deployment.'],
];

export default function SettingsPage() {
  return (
    <div className="space-y-3 pb-20 md:pb-0">
      <section className="glass-panel rounded-[16px] p-5">
        <p className="eyebrow">TENANT SETTINGS</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-text-primary">Configure EduSight for each school context</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
          Settings are designed for white-label partners, ministries, NGOs, and individual schools operating in different countries and connectivity conditions.
        </p>
      </section>

      <section className="grid gap-3 lg:grid-cols-4">
        <Tile icon={Palette} label="Branding" value="Neutral" />
        <Tile icon={Languages} label="Language" value="English" />
        <Tile icon={WifiOff} label="Offline mode" value="Enabled" />
        <Tile icon={Moon} label="Theme" value="Light first" />
      </section>

      <section className="glass-panel rounded-[14px] p-4">
        <h2 className="text-lg font-semibold text-text-primary">Configuration backlog</h2>
        <div className="mt-4 space-y-2">
          {settings.map(([title, copy]) => (
            <div key={title} className="rounded-[12px] border border-black/10 bg-white/80 p-3">
              <div className="flex gap-3">
                <Shield className="mt-0.5 h-4 w-4 flex-none text-primary" />
                <div>
                  <p className="text-sm font-semibold text-text-primary">{title}</p>
                  <p className="mt-1 text-sm leading-5 text-text-secondary">{copy}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Tile({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <article className="glass-panel rounded-[12px] p-4">
      <Icon className="h-5 w-5 text-primary" />
      <p className="mt-3 text-xs text-text-secondary">{label}</p>
      <p className="mt-1 text-lg font-semibold text-text-primary">{value}</p>
    </article>
  );
}
