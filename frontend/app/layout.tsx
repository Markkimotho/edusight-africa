import type { Metadata } from 'next';
import './globals.css';
import { Providers } from './providers';
import { ServiceWorkerRegister } from './service-worker-register';

export const metadata: Metadata = {
  title: {
    default: 'EduSight Africa',
    template: '%s | EduSight Africa',
  },
  description:
    'Explainable student support signals and retention workflows for African schools.',
  keywords: ['education', 'Africa', 'student support', 'retention', 'EdTech'],
  authors: [{ name: 'EduSight Africa' }],
  manifest: '/manifest.webmanifest',
  appleWebApp: {
    capable: true,
    title: 'EduSight',
    statusBarStyle: 'default',
  },
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white antialiased">
        <ServiceWorkerRegister />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
