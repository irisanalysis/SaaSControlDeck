/**
 * Authentication API types and interfaces
 * TypeScript definitions for authentication system
 * RELEVANT FILES: auth.ts, use-auth.ts, auth-context.tsx, login-form.tsx
 */

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
  full_name: string;
  first_name?: string | null;
  last_name?: string | null;
  avatar_url?: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user?: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshTokens: () => Promise<void>;
  clearError: () => void;
}

// API Error types
export class AuthAPIError extends Error {
  public statusCode?: number;
  public detail: string;

  constructor(detail: string, statusCode?: number) {
    super(detail);
    this.name = 'AuthAPIError';
    this.detail = detail;
    this.statusCode = statusCode;
  }
}

// Token storage interface
export interface TokenStorage {
  getToken: () => string | null;
  setToken: (token: string) => void;
  removeToken: () => void;
  getRefreshToken: () => string | null;
  setRefreshToken: (token: string) => void;
  removeRefreshToken: () => void;
  clear: () => void;
}

// Validation types
export interface ValidationError {
  field: string;
  message: string;
}

export interface FormValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

// Constants
export const AUTH_STORAGE_KEYS = {
  ACCESS_TOKEN: 'saascontrol_access_token',
  REFRESH_TOKEN: 'saascontrol_refresh_token',
  USER_DATA: 'saascontrol_user_data',
} as const;

export const PASSWORD_REQUIREMENTS = {
  MIN_LENGTH: 8,
  REQUIRE_DIGIT: true,
  REQUIRE_LETTER: true,
} as const;