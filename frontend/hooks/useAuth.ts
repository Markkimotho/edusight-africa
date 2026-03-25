import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useCallback } from 'react';
import { useAuthStore } from '@/lib/store';

export function useAuth() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const { user, setUser, clearUser } = useAuthStore();

  const isAuthenticated = status === 'authenticated';
  const isLoading = status === 'loading';
  const isAdmin = session?.user?.role === 'admin';
  const isTeacher = session?.user?.role === 'teacher';
  const isParent = session?.user?.role === 'parent';

  const logout = useCallback(async () => {
    clearUser();
    await signOut({ callbackUrl: '/login' });
  }, [clearUser]);

  const requireRole = useCallback(
    (role: string): boolean => {
      return session?.user?.role === role;
    },
    [session]
  );

  return {
    session,
    user: session?.user,
    status,
    isAuthenticated,
    isLoading,
    isAdmin,
    isTeacher,
    isParent,
    accessToken: session?.accessToken,
    logout,
    requireRole,
  };
}
