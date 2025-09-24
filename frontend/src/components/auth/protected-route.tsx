/**
 * Protected Route Component
 * Wrapper component that ensures user authentication before rendering protected content
 * RELEVANT FILES: auth-context.tsx, use-auth.ts, layout.tsx, data-management/page.tsx
 */

'use client';

import React, { ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStatus } from '@/hooks/use-auth';
import { Loading } from '@/components/ui/loading';
import { AuthLayout } from './auth-layout';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
  redirectTo?: string;
  className?: string;
}

export function ProtectedRoute({
  children,
  fallback,
  redirectTo = '/auth',
  className
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuthStatus();
  const router = useRouter();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return fallback || (
      <div className="min-h-screen flex items-center justify-center">
        <Loading size="lg" text="验证身份中..." />
      </div>
    );
  }

  // If not authenticated, show auth layout or redirect
  if (!isAuthenticated) {
    if (fallback) {
      return <>{fallback}</>;
    }

    // Show inline auth layout
    return (
      <AuthLayout
        onAuthSuccess={() => {
          // After successful auth, the auth context will handle the state update
          // and the component will re-render with isAuthenticated = true
        }}
        className={className}
      />
    );
  }

  // User is authenticated, render protected content
  return <>{children}</>;
}

// Higher-order component version for easier usage
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  options?: {
    fallback?: ReactNode;
    redirectTo?: string;
  }
) {
  const WrappedComponent = (props: P) => {
    return (
      <ProtectedRoute {...options}>
        <Component {...props} />
      </ProtectedRoute>
    );
  };

  WrappedComponent.displayName = `withAuth(${Component.displayName || Component.name})`;

  return WrappedComponent;
}

export default ProtectedRoute;