import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Language, User } from './types';

// ─── App Store (UI state + preferences) ──────────────────────────────────────

interface AppState {
  language: Language;
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  setLanguage: (language: Language) => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      language: 'en',
      theme: 'light',
      sidebarCollapsed: false,

      setLanguage: (language) => set({ language }),
      setTheme: (theme) => set({ theme }),
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      toggleSidebar: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    }),
    {
      name: 'edusight-app-preferences',
      partialize: (state) => ({
        language: state.language,
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
);

// ─── Auth Store (runtime auth state) ─────────────────────────────────────────

interface AuthState {
  user: User | null;
  isInitialized: boolean;
  setUser: (user: User | null) => void;
  clearUser: () => void;
  setInitialized: (initialized: boolean) => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  isInitialized: false,

  setUser: (user) => set({ user }),
  clearUser: () => set({ user: null }),
  setInitialized: (isInitialized) => set({ isInitialized }),
}));

// ─── Student Filter Store ─────────────────────────────────────────────────────

interface StudentFilterState {
  grade: string;
  riskLevel: string;
  search: string;
  page: number;
  setGrade: (grade: string) => void;
  setRiskLevel: (riskLevel: string) => void;
  setSearch: (search: string) => void;
  setPage: (page: number) => void;
  resetFilters: () => void;
}

export const useStudentFilterStore = create<StudentFilterState>()((set) => ({
  grade: '',
  riskLevel: '',
  search: '',
  page: 1,

  setGrade: (grade) => set({ grade, page: 1 }),
  setRiskLevel: (riskLevel) => set({ riskLevel, page: 1 }),
  setSearch: (search) => set({ search, page: 1 }),
  setPage: (page) => set({ page }),
  resetFilters: () => set({ grade: '', riskLevel: '', search: '', page: 1 }),
}));

// ─── Toast / Notification Store ───────────────────────────────────────────────

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  variant: 'default' | 'success' | 'error' | 'warning';
}

interface ToastState {
  toasts: ToastMessage[];
  addToast: (toast: Omit<ToastMessage, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

let toastCounter = 0;

export const useToastStore = create<ToastState>()((set) => ({
  toasts: [],

  addToast: (toast) => {
    const id = `toast-${++toastCounter}`;
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));
    // Auto-remove after 5s
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }));
    }, 5000);
  },

  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  clearToasts: () => set({ toasts: [] }),
}));
