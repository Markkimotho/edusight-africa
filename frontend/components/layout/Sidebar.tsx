'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  ClipboardList,
  Users,
  Heart,
  BookOpen,
  BarChart2,
  PlugZap,
  Upload,
  Settings,
  Wifi,
  ChevronLeft,
  ChevronRight,
  GraduationCap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppStore } from '@/lib/store';
import { useSession } from 'next-auth/react';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Support', href: '/support', icon: Heart },
  { label: 'Assess', href: '/assess', icon: ClipboardList },
  { label: 'Students', href: '/students', icon: Users },
  { label: 'Parent', href: '/parent', icon: Heart },
  { label: 'Resources', href: '/resources', icon: BookOpen },
  { label: 'Imports', href: '/imports', icon: Upload, adminOnly: true },
  { label: 'Reports', href: '/reports', icon: BarChart2, adminOnly: true },
  { label: 'Monitoring', href: '/monitoring', icon: Wifi, adminOnly: true },
  { label: 'Integrations', href: '/integrations', icon: PlugZap, adminOnly: true },
  { label: 'Settings', href: '/settings', icon: Settings, adminOnly: true },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useAppStore();
  const { data: session } = useSession();
  const isAdmin = session?.user?.role === 'admin';

  const visibleItems = NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin);

  return (
    <aside
      className={cn(
        'glass-panel m-2 hidden flex-col rounded-[14px] text-text-primary transition-all duration-300 ease-in-out md:flex',
        sidebarCollapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          'flex items-center gap-3 border-b border-black/10 px-4 py-4',
          sidebarCollapsed && 'justify-center px-0'
        )}
      >
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-primary shadow-sm">
          <GraduationCap className="h-5 w-5 text-white" />
        </div>
        {!sidebarCollapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-bold leading-tight">EduSight</p>
            <p className="truncate text-xs text-text-secondary">Africa</p>
          </div>
        )}
      </div>

      {/* Nav links */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === '/dashboard'
              ? pathname === '/dashboard'
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex items-center gap-3 rounded-[7px] px-3 py-2.5 text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-text-secondary hover:bg-black/5 hover:text-text-primary',
                sidebarCollapsed && 'justify-center px-2'
              )}
              title={sidebarCollapsed ? item.label : undefined}
            >
              <Icon
                className={cn(
                  'h-5 w-5 flex-shrink-0',
                  isActive ? 'text-white' : 'text-text-secondary'
                )}
              />
              {!sidebarCollapsed && (
                <span className="truncate">{item.label}</span>
              )}
              {isActive && !sidebarCollapsed && (
                <span className="ml-auto h-1.5 w-1.5 flex-shrink-0 rounded-full bg-white" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-black/10 p-2">
        <button
          onClick={toggleSidebar}
          className={cn(
            'flex w-full items-center gap-3 rounded-[7px] px-3 py-2 text-sm text-text-secondary transition-colors hover:bg-black/5 hover:text-text-primary',
            sidebarCollapsed && 'justify-center px-2'
          )}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}

export function MobileNav() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const isAdmin = session?.user?.role === 'admin';

  const visibleItems = NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin).slice(0, 5);

  return (
    <nav className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-5 rounded-[14px] border border-white/70 bg-white/90 p-1 shadow-[0_18px_45px_rgba(29,29,31,0.16)] backdrop-blur-xl md:hidden">
      {visibleItems.map((item) => {
        const Icon = item.icon;
        const isActive =
          item.href === '/dashboard'
            ? pathname === '/dashboard'
            : pathname.startsWith(item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex min-w-0 flex-col items-center justify-center gap-1 rounded-[10px] px-1 py-2 text-[10px] font-semibold transition-colors',
              isActive
                ? 'bg-primary text-white'
                : 'text-text-secondary hover:bg-black/5 hover:text-text-primary'
            )}
          >
            <Icon className="h-4 w-4 flex-shrink-0" />
            <span className="max-w-full truncate">{item.label.replace(' Portal', '')}</span>
          </Link>
        );
      })}
    </nav>
  );
}
