/**
 * Authentication Page
 * Standalone authentication page for login and registration
 * RELEVANT FILES: auth-layout.tsx, login-form.tsx, register-form.tsx
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStatus } from '@/hooks/use-auth';
import { AuthLayout } from '@/components/auth';
import { Loading } from '@/components/ui/loading';

export default function AuthPage() {
  const { isAuthenticated, isLoading } = useAuthStatus();
  const router = useRouter();

  useEffect(() => {
    // If user is already authenticated, redirect to dashboard
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  // Show loading while checking auth status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading size="lg" text="检查登录状态..." />
      </div>
    );
  }

  // If authenticated, show loading (will redirect)
  if (isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading size="lg" text="重定向到仪表盘..." />
      </div>
    );
  }

  // Show auth layout
  return (
    <AuthLayout
      onAuthSuccess={() => {
        // Redirect to dashboard after successful authentication
        router.push('/');
      }}
    />
  );
}