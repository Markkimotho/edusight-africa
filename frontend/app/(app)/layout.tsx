import { MobileNav, Sidebar } from '@/components/layout/Sidebar';
import { TopBar } from '@/components/layout/TopBar';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-3 pb-24 sm:p-4 sm:pb-24 md:pb-4 lg:p-5">
          <div className="mx-auto max-w-[1500px] animate-in">
            {children}
          </div>
        </main>
        <MobileNav />
      </div>
    </div>
  );
}
