/**
 * Authentication Layout Component
 * Combined login/register interface with tab switching
 * RELEVANT FILES: login-form.tsx, register-form.tsx, auth-page.tsx
 */

'use client';

import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LoginForm } from './login-form';
import { RegisterForm } from './register-form';

type AuthMode = 'login' | 'register';

interface AuthLayoutProps {
  defaultMode?: AuthMode;
  onAuthSuccess?: () => void;
  className?: string;
}

export function AuthLayout({ defaultMode = 'login', onAuthSuccess, className }: AuthLayoutProps) {
  const [activeTab, setActiveTab] = useState<AuthMode>(defaultMode);

  const handleSwitchToLogin = () => {
    setActiveTab('login');
  };

  const handleSwitchToRegister = () => {
    setActiveTab('register');
  };

  const handleLoginSuccess = () => {
    onAuthSuccess?.();
  };

  const handleRegisterSuccess = () => {
    // After successful registration, switch to login
    setActiveTab('login');
    onAuthSuccess?.();
  };

  return (
    <div className={`min-h-screen flex items-center justify-center bg-background p-4 ${className}`}>
      <div className="w-full max-w-md">
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as AuthMode)}>
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="login" className="text-sm">
              登录
            </TabsTrigger>
            <TabsTrigger value="register" className="text-sm">
              注册
            </TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="space-y-0">
            <LoginForm
              onSuccess={handleLoginSuccess}
              onSwitchToRegister={handleSwitchToRegister}
            />
          </TabsContent>

          <TabsContent value="register" className="space-y-0">
            <RegisterForm
              onSuccess={handleRegisterSuccess}
              onSwitchToLogin={handleSwitchToLogin}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default AuthLayout;