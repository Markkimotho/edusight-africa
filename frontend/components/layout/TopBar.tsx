'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { signOut, useSession } from 'next-auth/react';
import {
  ChevronDown,
  LogOut,
  User,
  Settings,
  Bell,
  Globe,
} from 'lucide-react';
import { cn, getInitials } from '@/lib/utils';
import { useAppStore } from '@/lib/store';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import type { Language } from '@/lib/types';

const LANGUAGES: Array<{ code: Language; label: string; flag: string }> = [
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'sw', label: 'Swahili', flag: '🇰🇪' },
  { code: 'fr', label: 'French', flag: '🇫🇷' },
  { code: 'am', label: 'Amharic', flag: '🇪🇹' },
  { code: 'ha', label: 'Hausa', flag: '🇳🇬' },
  { code: 'yo', label: 'Yoruba', flag: '🇳🇬' },
  { code: 'ig', label: 'Igbo', flag: '🇳🇬' },
  { code: 'zu', label: 'Zulu', flag: '🇿🇦' },
  { code: 'xh', label: 'Xhosa', flag: '🇿🇦' },
  { code: 'ar', label: 'Arabic', flag: '🇸🇦' },
];

export function TopBar() {
  const { data: session } = useSession();
  const router = useRouter();
  const { language, setLanguage } = useAppStore();

  const [langOpen, setLangOpen] = React.useState(false);
  const [userOpen, setUserOpen] = React.useState(false);

  const langRef = React.useRef<HTMLDivElement>(null);
  const userRef = React.useRef<HTMLDivElement>(null);

  const currentLang = LANGUAGES.find((l) => l.code === language) || LANGUAGES[0];
  const userName = session?.user?.name || 'User';

  // Close dropdowns on outside click
  React.useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (langRef.current && !langRef.current.contains(e.target as Node)) {
        setLangOpen(false);
      }
      if (userRef.current && !userRef.current.contains(e.target as Node)) {
        setUserOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  async function handleLogout() {
    await signOut({ callbackUrl: '/login' });
  }

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6">
      {/* School name */}
      <div className="flex items-center gap-3">
        <h2 className="text-base font-semibold text-text-primary">
          Nairobi Primary School
        </h2>
        <span className="hidden sm:inline-block h-1 w-1 rounded-full bg-gray-300" />
        <span className="hidden sm:inline-block text-sm text-text-secondary">
          Academic Year 2024–2025
        </span>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        {/* Notification bell */}
        <button className="relative rounded-lg p-2 text-text-secondary hover:bg-gray-100 transition-colors">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-accent" />
        </button>

        {/* Language switcher */}
        <div ref={langRef} className="relative">
          <button
            onClick={() => setLangOpen((v) => !v)}
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-text-secondary hover:bg-gray-100 transition-colors"
          >
            <Globe className="h-4 w-4" />
            <span className="hidden sm:block">
              {currentLang.flag} {currentLang.label}
            </span>
            <span className="sm:hidden">{currentLang.flag}</span>
            <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', langOpen && 'rotate-180')} />
          </button>

          {langOpen && (
            <div className="absolute right-0 top-full mt-1 z-50 w-44 rounded-xl border border-gray-200 bg-white shadow-lg py-1 overflow-hidden">
              {LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  onClick={() => {
                    setLanguage(lang.code);
                    setLangOpen(false);
                  }}
                  className={cn(
                    'flex w-full items-center gap-2 px-4 py-2 text-sm transition-colors hover:bg-surface',
                    lang.code === language
                      ? 'text-primary font-medium'
                      : 'text-text-primary'
                  )}
                >
                  <span>{lang.flag}</span>
                  <span>{lang.label}</span>
                  {lang.code === language && (
                    <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User dropdown */}
        <div ref={userRef} className="relative">
          <button
            onClick={() => setUserOpen((v) => !v)}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-gray-100 transition-colors"
          >
            <Avatar className="h-8 w-8">
              <AvatarFallback className="text-xs">{getInitials(userName)}</AvatarFallback>
            </Avatar>
            <div className="hidden sm:block text-left">
              <p className="text-sm font-medium text-text-primary leading-tight">
                {userName}
              </p>
              <p className="text-xs text-text-secondary capitalize leading-tight">
                {session?.user?.role || 'teacher'}
              </p>
            </div>
            <ChevronDown
              className={cn(
                'hidden sm:block h-3.5 w-3.5 text-text-secondary transition-transform',
                userOpen && 'rotate-180'
              )}
            />
          </button>

          {userOpen && (
            <div className="absolute right-0 top-full mt-1 z-50 w-48 rounded-xl border border-gray-200 bg-white shadow-lg py-1 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="text-sm font-semibold text-text-primary">{userName}</p>
                <p className="text-xs text-text-secondary">
                  {session?.user?.email}
                </p>
              </div>
              <button
                onClick={() => { setUserOpen(false); router.push('/profile'); }}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-text-primary hover:bg-surface transition-colors"
              >
                <User className="h-4 w-4 text-text-secondary" />
                Profile
              </button>
              <button
                onClick={() => { setUserOpen(false); router.push('/settings'); }}
                className="flex w-full items-center gap-2 px-4 py-2 text-sm text-text-primary hover:bg-surface transition-colors"
              >
                <Settings className="h-4 w-4 text-text-secondary" />
                Settings
              </button>
              <div className="border-t border-gray-100 mt-1 pt-1">
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-danger hover:bg-red-50 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Log Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
