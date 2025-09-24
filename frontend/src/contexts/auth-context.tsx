/**
 * Authentication Context Provider
 * Global authentication state management using React Context
 * Provides authentication status, user data, and auth actions across the app
 * RELEVANT FILES: auth.ts, use-auth.ts, layout.tsx, login-form.tsx
 */

'use client';

import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { toast } from '@/hooks/use-toast';
import authAPI from '@/lib/api/auth';
import {
  User,
  LoginRequest,
  RegisterRequest,
  AuthState,
  AuthContextType,
  AuthAPIError,
} from '@/lib/api/types/auth';

// Authentication actions
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; token: string; refreshToken: string } }
  | { type: 'AUTH_ERROR'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'UPDATE_USER'; payload: User };

// Initial state
const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true, // Start with loading true for initial auth check
  error: null,
};

// Auth reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        refreshToken: action.payload.refreshToken,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case 'AUTH_ERROR':
      return {
        ...state,
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };

    case 'AUTH_LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };

    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };

    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload,
      };

    default:
      return state;
  }
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize authentication state on app start
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // Check if user has stored auth data
        const storedToken = authAPI.getStoredToken();
        const storedUser = authAPI.getStoredUser();
        const storedRefreshToken = authAPI.getStoredRefreshToken();

        if (storedToken && storedUser && storedRefreshToken) {
          // Verify token is still valid by fetching current user
          try {
            const currentUser = await authAPI.getCurrentUser();
            dispatch({
              type: 'AUTH_SUCCESS',
              payload: {
                user: currentUser,
                token: storedToken,
                refreshToken: storedRefreshToken,
              },
            });
          } catch (error) {
            // Token might be expired, try refresh
            try {
              const tokenResponse = await authAPI.refreshToken();
              dispatch({
                type: 'AUTH_SUCCESS',
                payload: {
                  user: tokenResponse.user,
                  token: tokenResponse.access_token,
                  refreshToken: tokenResponse.refresh_token,
                },
              });
            } catch (refreshError) {
              // Refresh failed, clear auth data
              authAPI.clearAuthData();
              dispatch({ type: 'AUTH_LOGOUT' });
            }
          }
        } else {
          // No stored auth data
          dispatch({ type: 'AUTH_LOGOUT' });
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        authAPI.clearAuthData();
        dispatch({ type: 'AUTH_LOGOUT' });
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = async (credentials: LoginRequest): Promise<void> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await authAPI.login(credentials);

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user,
          token: response.access_token,
          refreshToken: response.refresh_token,
        },
      });

      toast({
        title: '登录成功',
        description: `欢迎回来，${response.user.full_name}！`,
      });
    } catch (error) {
      const errorMessage =
        error instanceof AuthAPIError ? error.detail : '登录失败，请重试';

      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });

      toast({
        title: '登录失败',
        description: errorMessage,
        variant: 'destructive',
      });

      throw error;
    }
  };

  // Register function
  const register = async (userData: RegisterRequest): Promise<void> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await authAPI.register(userData);

      if (response.success) {
        // Registration successful, show success message
        toast({
          title: '注册成功',
          description: response.message || '账户创建成功，请登录',
        });

        // Don't auto-login after registration, let user login manually
        dispatch({ type: 'AUTH_LOGOUT' });
      } else {
        throw new AuthAPIError(response.message || '注册失败');
      }
    } catch (error) {
      const errorMessage =
        error instanceof AuthAPIError ? error.detail : '注册失败，请重试';

      dispatch({ type: 'AUTH_ERROR', payload: errorMessage });

      toast({
        title: '注册失败',
        description: errorMessage,
        variant: 'destructive',
      });

      throw error;
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      await authAPI.logout();

      dispatch({ type: 'AUTH_LOGOUT' });

      toast({
        title: '已登出',
        description: '您已成功登出账户',
      });
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails on server, clear local state
      dispatch({ type: 'AUTH_LOGOUT' });
    }
  };

  // Refresh tokens function
  const refreshTokens = async (): Promise<void> => {
    try {
      const response = await authAPI.refreshToken();

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: response.user,
          token: response.access_token,
          refreshToken: response.refresh_token,
        },
      });
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Refresh failed, logout user
      dispatch({ type: 'AUTH_LOGOUT' });
      authAPI.clearAuthData();

      toast({
        title: '会话已过期',
        description: '请重新登录',
        variant: 'destructive',
      });

      throw error;
    }
  };

  // Clear error function
  const clearError = (): void => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  // Context value
  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshTokens,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Auth status hook for convenience
export function useAuthStatus() {
  const { isAuthenticated, isLoading, user } = useAuth();
  return {
    isAuthenticated,
    isLoading,
    user,
    isReady: !isLoading, // Convenience flag for when auth status is determined
  };
}

export default AuthContext;