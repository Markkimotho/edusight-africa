'use client';

import * as React from 'react';
import Link from 'next/link';
import { GraduationCap, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface p-8">
      <div className="w-full max-w-md text-center">
        <div className="flex justify-center mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary">
            <GraduationCap className="h-8 w-8 text-white" />
          </div>
        </div>

        <h1 className="text-2xl font-bold text-text-primary mb-2">
          Create an Account
        </h1>
        <p className="text-text-secondary mb-8">
          EduSight Africa accounts are managed by school administrators.
          Please contact your school administrator to receive your login credentials.
        </p>

        <div className="rounded-xl border border-gray-200 bg-white p-6 mb-6">
          <h2 className="font-semibold text-text-primary mb-3">How to get access</h2>
          <ol className="space-y-2 text-sm text-text-secondary text-left">
            <li className="flex gap-2">
              <span className="flex-shrink-0 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-white text-xs font-bold">1</span>
              Contact your school or district administrator
            </li>
            <li className="flex gap-2">
              <span className="flex-shrink-0 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-white text-xs font-bold">2</span>
              Provide your name, email, and role (teacher, parent, etc.)
            </li>
            <li className="flex gap-2">
              <span className="flex-shrink-0 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-white text-xs font-bold">3</span>
              Receive your credentials and sign in
            </li>
          </ol>
        </div>

        <div className="space-y-3">
          <Button asChild className="w-full">
            <Link href="mailto:admin@edusight.africa">
              Contact Administrator
            </Link>
          </Button>
          <Button asChild variant="outline" className="w-full">
            <Link href="/login">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Sign In
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
