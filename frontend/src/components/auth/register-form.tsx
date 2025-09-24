/**
 * Register Form Component
 * User registration form with validation and error handling
 * RELEVANT FILES: auth.ts, use-auth.ts, auth-context.tsx, login-form.tsx
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Eye, EyeOff, Loader2, UserPlus, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useRegisterForm } from '@/hooks/use-auth';
import { RegisterRequest } from '@/lib/api/types/auth';

interface RegisterFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
  className?: string;
}

export function RegisterForm({ onSuccess, onSwitchToLogin, className }: RegisterFormProps) {
  const {
    handleRegister,
    isLoading,
    error,
    getFieldError,
    clearError,
    showPassword,
    togglePasswordVisibility,
  } = useRegisterForm();

  const [formData, setFormData] = useState<RegisterRequest>({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  });

  const [isRegistrationSuccess, setIsRegistrationSuccess] = useState(false);

  const handleInputChange = (field: keyof RegisterRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear errors when user starts typing
    if (error) clearError();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await handleRegister(formData);
      // If registration is successful
      setIsRegistrationSuccess(true);
      onSuccess?.();
    } catch (error) {
      // Error is already handled by the auth context and useRegisterForm hook
      console.error('Registration submission failed:', error);
    }
  };

  // Show success message after successful registration
  if (isRegistrationSuccess) {
    return (
      <Card className={`w-full max-w-md mx-auto ${className}`}>
        <CardHeader className="space-y-1 text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full">
              <Check className="h-6 w-6 text-green-600" />
            </div>
          </div>
          <CardTitle className="text-2xl">注册成功！</CardTitle>
          <CardDescription>
            您的账户已成功创建，现在可以登录了
          </CardDescription>
        </CardHeader>
        <CardFooter>
          <Button
            onClick={onSwitchToLogin}
            className="w-full"
          >
            前往登录
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <Card className={`w-full max-w-md mx-auto ${className}`}>
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-center mb-4">
          <div className="flex items-center space-x-2">
            <UserPlus className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">SaaS Control</span>
          </div>
        </div>
        <CardTitle className="text-2xl text-center">创建账户</CardTitle>
        <CardDescription className="text-center text-muted-foreground">
          填写您的信息来创建新账户
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

          {/* Name fields row */}
          <div className="grid grid-cols-2 gap-4">
            {/* First name */}
            <div className="space-y-2">
              <Label htmlFor="first_name">名字</Label>
              <Input
                id="first_name"
                type="text"
                placeholder="您的名字"
                value={formData.first_name}
                onChange={(e) => handleInputChange('first_name', e.target.value)}
                disabled={isLoading}
                className={getFieldError('first_name') ? 'border-destructive' : ''}
                autoComplete="given-name"
                required
              />
              {getFieldError('first_name') && (
                <p className="text-sm text-destructive">{getFieldError('first_name')}</p>
              )}
            </div>

            {/* Last name */}
            <div className="space-y-2">
              <Label htmlFor="last_name">姓氏</Label>
              <Input
                id="last_name"
                type="text"
                placeholder="您的姓氏"
                value={formData.last_name}
                onChange={(e) => handleInputChange('last_name', e.target.value)}
                disabled={isLoading}
                className={getFieldError('last_name') ? 'border-destructive' : ''}
                autoComplete="family-name"
                required
              />
              {getFieldError('last_name') && (
                <p className="text-sm text-destructive">{getFieldError('last_name')}</p>
              )}
            </div>
          </div>

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
                placeholder="创建一个强密码"
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                disabled={isLoading}
                className={getFieldError('password') ? 'border-destructive pr-10' : 'pr-10'}
                autoComplete="new-password"
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
            <div className="text-xs text-muted-foreground">
              密码至少8位，包含字母和数字
            </div>
          </div>

          {/* Terms and privacy notice */}
          <div className="text-xs text-muted-foreground">
            注册即表示您同意我们的{' '}
            <Link href="/terms" className="text-primary hover:underline">
              服务条款
            </Link>{' '}
            和{' '}
            <Link href="/privacy" className="text-primary hover:underline">
              隐私政策
            </Link>
          </div>
        </CardContent>

        <CardFooter className="flex flex-col space-y-4">
          {/* Register button */}
          <Button
            type="submit"
            className="w-full"
            disabled={
              isLoading ||
              !formData.email ||
              !formData.password ||
              !formData.first_name ||
              !formData.last_name
            }
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                注册中...
              </>
            ) : (
              <>
                <UserPlus className="mr-2 h-4 w-4" />
                创建账户
              </>
            )}
          </Button>

          {/* Login link */}
          <div className="text-center text-sm text-muted-foreground">
            已经有账户？{' '}
            {onSwitchToLogin ? (
              <button
                type="button"
                onClick={onSwitchToLogin}
                className="text-primary hover:underline font-medium"
              >
                立即登录
              </button>
            ) : (
              <Link href="/auth/login" className="text-primary hover:underline font-medium">
                立即登录
              </Link>
            )}
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}

export default RegisterForm;