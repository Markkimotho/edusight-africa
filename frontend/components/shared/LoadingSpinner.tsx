import * as React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  label?: string;
  fullPage?: boolean;
}

const sizeClasses = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-3',
  xl: 'h-16 w-16 border-4',
};

export function LoadingSpinner({
  size = 'md',
  className,
  label = 'Loading...',
  fullPage = false,
}: LoadingSpinnerProps) {
  const spinner = (
    <div
      className={cn(
        'animate-spin rounded-full border-gray-200 border-t-primary',
        sizeClasses[size],
        className
      )}
      role="status"
      aria-label={label}
    />
  );

  if (fullPage) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center gap-4">
        {spinner}
        <p className="text-sm text-text-secondary">{label}</p>
      </div>
    );
  }

  return spinner;
}

export function LoadingPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-white">
      <div className="flex flex-col items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary" />
          <span className="text-xl font-bold text-primary">EduSight Africa</span>
        </div>
        <LoadingSpinner size="lg" />
        <p className="text-sm text-text-secondary">Loading your dashboard...</p>
      </div>
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 animate-pulse">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <div className="h-4 w-24 rounded bg-gray-200" />
          <div className="h-8 w-16 rounded bg-gray-200" />
          <div className="h-3 w-32 rounded bg-gray-200" />
        </div>
        <div className="h-12 w-12 rounded-xl bg-gray-200" />
      </div>
    </div>
  );
}

export function SkeletonRow() {
  return (
    <div className="flex items-center gap-4 p-4 animate-pulse border-b border-gray-100">
      <div className="h-10 w-10 rounded-full bg-gray-200 flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-40 rounded bg-gray-200" />
        <div className="h-3 w-24 rounded bg-gray-200" />
      </div>
      <div className="h-6 w-20 rounded-full bg-gray-200" />
    </div>
  );
}
