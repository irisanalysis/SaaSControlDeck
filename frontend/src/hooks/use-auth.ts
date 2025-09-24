/**
 * Custom Authentication Hook
 * Provides authentication utilities and form validation
 * RELEVANT FILES: auth-context.tsx, auth.ts, login-form.tsx, register-form.tsx
 */

'use client';

import { useState, useCallback } from 'react';
import { useAuth } from '@/contexts/auth-context';
import authAPI from '@/lib/api/auth';
import {
  LoginRequest,
  RegisterRequest,
  ValidationError,
  FormValidationResult,
} from '@/lib/api/types/auth';

// Form validation hook
export function useFormValidation() {
  const validateLoginForm = useCallback((data: LoginRequest): FormValidationResult => {
    const errors: ValidationError[] = [];

    // Email validation
    if (!data.email) {
      errors.push({ field: 'email', message: '邮箱不能为空' });
    } else if (!authAPI.validateEmail(data.email)) {
      errors.push({ field: 'email', message: '请输入有效的邮箱地址' });
    }

    // Password validation
    if (!data.password) {
      errors.push({ field: 'password', message: '密码不能为空' });
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }, []);

  const validateRegisterForm = useCallback((data: RegisterRequest): FormValidationResult => {
    const errors: ValidationError[] = [];

    // Email validation
    if (!data.email) {
      errors.push({ field: 'email', message: '邮箱不能为空' });
    } else if (!authAPI.validateEmail(data.email)) {
      errors.push({ field: 'email', message: '请输入有效的邮箱地址' });
    }

    // Password validation
    if (!data.password) {
      errors.push({ field: 'password', message: '密码不能为空' });
    } else {
      const passwordValidation = authAPI.validatePassword(data.password);
      if (!passwordValidation.isValid) {
        passwordValidation.errors.forEach(error => {
          errors.push({ field: 'password', message: error });
        });
      }
    }

    // Name validation
    if (!data.first_name || data.first_name.trim().length === 0) {
      errors.push({ field: 'first_name', message: '名字不能为空' });
    }

    if (!data.last_name || data.last_name.trim().length === 0) {
      errors.push({ field: 'last_name', message: '姓氏不能为空' });
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }, []);

  return {
    validateLoginForm,
    validateRegisterForm,
  };
}

// Login form hook
export function useLoginForm() {
  const { login, isLoading, error, clearError } = useAuth();
  const { validateLoginForm } = useFormValidation();
  const [formErrors, setFormErrors] = useState<ValidationError[]>([]);

  const handleLogin = useCallback(
    async (credentials: LoginRequest) => {
      // Clear previous errors
      clearError();
      setFormErrors([]);

      // Validate form
      const validation = validateLoginForm(credentials);
      if (!validation.isValid) {
        setFormErrors(validation.errors);
        return;
      }

      // Attempt login
      try {
        await login(credentials);
      } catch (error) {
        // Error is handled by the auth context
        console.error('Login failed:', error);
      }
    },
    [login, validateLoginForm, clearError]
  );

  const getFieldError = useCallback(
    (fieldName: string): string | undefined => {
      const fieldError = formErrors.find(e => e.field === fieldName);
      return fieldError?.message;
    },
    [formErrors]
  );

  return {
    handleLogin,
    isLoading,
    error,
    formErrors,
    getFieldError,
    clearError,
  };
}

// Register form hook
export function useRegisterForm() {
  const { register, isLoading, error, clearError } = useAuth();
  const { validateRegisterForm } = useFormValidation();
  const [formErrors, setFormErrors] = useState<ValidationError[]>([]);
  const [showPassword, setShowPassword] = useState(false);

  const handleRegister = useCallback(
    async (userData: RegisterRequest) => {
      // Clear previous errors
      clearError();
      setFormErrors([]);

      // Validate form
      const validation = validateRegisterForm(userData);
      if (!validation.isValid) {
        setFormErrors(validation.errors);
        return;
      }

      // Attempt registration
      try {
        await register(userData);
      } catch (error) {
        // Error is handled by the auth context
        console.error('Registration failed:', error);
      }
    },
    [register, validateRegisterForm, clearError]
  );

  const getFieldError = useCallback(
    (fieldName: string): string | undefined => {
      const fieldError = formErrors.find(e => e.field === fieldName);
      return fieldError?.message;
    },
    [formErrors]
  );

  const togglePasswordVisibility = useCallback(() => {
    setShowPassword(prev => !prev);
  }, []);

  return {
    handleRegister,
    isLoading,
    error,
    formErrors,
    getFieldError,
    clearError,
    showPassword,
    togglePasswordVisibility,
  };
}

// Protected route hook
export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth();

  return {
    isAuthenticated,
    isLoading,
    shouldRedirect: !isLoading && !isAuthenticated,
  };
}

// Auth status utilities
export function useAuthUtils() {
  const { user, isAuthenticated, logout } = useAuth();

  const getUserDisplayName = useCallback(() => {
    if (!user) return '';
    return user.full_name || user.email.split('@')[0];
  }, [user]);

  const getUserInitials = useCallback(() => {
    if (!user) return '';

    if (user.first_name && user.last_name) {
      return `${user.first_name.charAt(0)}${user.last_name.charAt(0)}`.toUpperCase();
    }

    const name = user.full_name || user.email;
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0].charAt(0)}${parts[1].charAt(0)}`.toUpperCase();
    }

    return name.substring(0, 2).toUpperCase();
  }, [user]);

  const handleLogout = useCallback(async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
  }, [logout]);

  return {
    user,
    isAuthenticated,
    getUserDisplayName,
    getUserInitials,
    handleLogout,
  };
}

// Token refresh utility
export function useTokenRefresh() {
  const { refreshTokens } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleTokenRefresh = useCallback(async () => {
    if (isRefreshing) return;

    setIsRefreshing(true);
    try {
      await refreshTokens();
    } catch (error) {
      console.error('Token refresh failed:', error);
      throw error;
    } finally {
      setIsRefreshing(false);
    }
  }, [refreshTokens, isRefreshing]);

  return {
    isRefreshing,
    handleTokenRefresh,
  };
}

// Main auth hook export
export { useAuth, useAuthStatus } from '@/contexts/auth-context';