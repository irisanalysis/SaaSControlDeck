/**
 * Login Form Component
 * User authentication form with validation and error handling
 * RELEVANT FILES: auth.ts, use-auth.ts, auth-context.tsx, register-form.tsx
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Eye, EyeOff, Loader2, LogIn } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useLoginForm } from '@/hooks/use-auth';
import { LoginRequest } from '@/lib/api/types/auth';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
  className?: string;
}

export function LoginForm({ onSuccess, onSwitchToRegister, className }: LoginFormProps) {
  const { handleLogin, isLoading, error, getFieldError, clearError } = useLoginForm();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState<LoginRequest>({
    email: '',
    password: '',
  });

  const handleInputChange = (field: keyof LoginRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear errors when user starts typing
    if (error) clearError();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await handleLogin(formData);
      // If login is successful, the auth context will handle the state update
      onSuccess?.();
    } catch (error) {
      // Error is already handled by the auth context and useLoginForm hook
      console.error('Login submission failed:', error);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(prev => !prev);
  };

  return (
    <Card className={`w-full max-w-md mx-auto ${className}`}>
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-center mb-4">
          <div className="flex items-center space-x-2">
            <LogIn className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">SaaS Control</span>
          </div>
        </div>
        <CardTitle className="text-2xl text-center">登录账户</CardTitle>
        <CardDescription className="text-center text-muted-foreground">
          输入您的邮箱和密码来访问您的账户
        </CardDescription>
      </CardHeader>

      <form onSubmit={handleSubmit}>
        <CardContent className="space-y-4">
          {/* Global error message */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Email field */}
          <div className="space-y-2">
            <Label htmlFor="email">邮箱地址</Label>
            <Input
              id="email"
              type="email"
              placeholder="输入您的邮箱"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              disabled={isLoading}
              className={getFieldError('email') ? 'border-destructive' : ''}
              autoComplete="email"
              required
            />
            {getFieldError('email') && (
              <p className="text-sm text-destructive">{getFieldError('email')}</p>
            )}
          </div>

          {/* Password field */}
          <div className="space-y-2">
            <Label htmlFor="password">密码</Label>
            <div className="relative">
              <Input
                id="password"
                type={showPassword ? 'text' : 'password'}
                placeholder="输入您的密码"
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                disabled={isLoading}
                className={getFieldError('password') ? 'border-destructive pr-10' : 'pr-10'}
                autoComplete="current-password"
                required
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={togglePasswordVisibility}
                disabled={isLoading}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
                <span className="sr-only">
                  {showPassword ? '隐藏密码' : '显示密码'}
                </span>
              </Button>
            </div>
            {getFieldError('password') && (
              <p className="text-sm text-destructive">{getFieldError('password')}</p>
            )}
          </div>

          {/* Forgot password link */}
          <div className="flex justify-end">
            <Link
              href="/auth/forgot-password"
              className="text-sm text-primary hover:underline"
            >
              忘记密码？
            </Link>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col space-y-4">
          {/* Login button */}
          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !formData.email || !formData.password}
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                登录中...
              </>
            ) : (
              <>
                <LogIn className="mr-2 h-4 w-4" />
                登录
              </>
            )}
          </Button>

          {/* Register link */}
          <div className="text-center text-sm text-muted-foreground">
            还没有账户？{' '}
            {onSwitchToRegister ? (
              <button
                type="button"
                onClick={onSwitchToRegister}
                className="text-primary hover:underline font-medium"
              >
                立即注册
              </button>
            ) : (
              <Link href="/auth/register" className="text-primary hover:underline font-medium">
                立即注册
              </Link>
            )}
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}

export default LoginForm;