import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'EduSight Africa',
    template: '%s | EduSight Africa',
  },
  description:
    'AI-powered student risk assessment and educational analytics platform for African schools.',
  keywords: ['education', 'Africa', 'student analytics', 'risk assessment', 'EdTech'],
  authors: [{ name: 'EduSight Africa' }],
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
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-white antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
