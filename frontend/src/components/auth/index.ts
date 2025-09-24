/**
 * Authentication Components Index
 * Central export point for all authentication-related components
 * RELEVANT FILES: login-form.tsx, register-form.tsx, auth-layout.tsx, protected-route.tsx
 */

export { LoginForm } from './login-form';
export { RegisterForm } from './register-form';
export { AuthLayout } from './auth-layout';
export { ProtectedRoute, withAuth } from './protected-route';

export * from './login-form';
export * from './register-form';
export * from './auth-layout';
export * from './protected-route';