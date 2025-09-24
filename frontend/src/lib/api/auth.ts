/**
 * Authentication API Client
 * Handles all authentication-related API calls including login, register, token management
 * Provides secure token storage and automatic token refresh functionality
 * RELEVANT FILES: auth.ts, data-sources.ts, use-auth.ts, auth-context.tsx
 */

import {
  User,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  RefreshTokenRequest,
  AuthResponse,
  AuthAPIError,
  TokenStorage,
  AUTH_STORAGE_KEYS,
} from './types/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

// Token storage implementation for browser localStorage
class BrowserTokenStorage implements TokenStorage {
  getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN);
  }

  setToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN, token);
  }

  removeToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN);
  }

  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN);
  }

  setRefreshToken(token: string): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN, token);
  }

  removeRefreshToken(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN);
  }

  clear(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(AUTH_STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(AUTH_STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(AUTH_STORAGE_KEYS.USER_DATA);
  }

  getUserData(): User | null {
    if (typeof window === 'undefined') return null;
    const userData = localStorage.getItem(AUTH_STORAGE_KEYS.USER_DATA);
    return userData ? JSON.parse(userData) : null;
  }

  setUserData(user: User): void {
    if (typeof window === 'undefined') return;
    localStorage.setItem(AUTH_STORAGE_KEYS.USER_DATA, JSON.stringify(user));
  }

  removeUserData(): void {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(AUTH_STORAGE_KEYS.USER_DATA);
  }
}

class AuthAPIClient {
  private baseURL: string;
  private tokenStorage: TokenStorage;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    this.tokenStorage = new BrowserTokenStorage();
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    // Add authentication header if token exists
    const token = this.tokenStorage.getToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new AuthAPIError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof AuthAPIError) {
        throw error;
      }
      throw new AuthAPIError(
        error instanceof Error ? error.message : 'Network error'
      );
    }
  }

  // Authentication methods
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await this.request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    // Store tokens and user data
    this.tokenStorage.setToken(response.access_token);
    this.tokenStorage.setRefreshToken(response.refresh_token);
    (this.tokenStorage as BrowserTokenStorage).setUserData(response.user);

    return response;
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });

    return response;
  }

  async logout(): Promise<void> {
    try {
      // Call logout endpoint if authenticated
      const token = this.tokenStorage.getToken();
      if (token) {
        await this.request('/auth/logout', {
          method: 'POST',
        });
      }
    } catch (error) {
      // Even if logout fails on server, clear local storage
      console.warn('Server logout failed:', error);
    } finally {
      // Always clear local storage
      this.tokenStorage.clear();
    }
  }

  async refreshToken(): Promise<TokenResponse> {
    const refreshToken = this.tokenStorage.getRefreshToken();
    if (!refreshToken) {
      throw new AuthAPIError('No refresh token available');
    }

    const response = await this.request<TokenResponse>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    // Update stored tokens
    this.tokenStorage.setToken(response.access_token);
    this.tokenStorage.setRefreshToken(response.refresh_token);
    (this.tokenStorage as BrowserTokenStorage).setUserData(response.user);

    return response;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.request<User>('/auth/me');

    // Update stored user data
    (this.tokenStorage as BrowserTokenStorage).setUserData(response);

    return response;
  }

  // Token management methods
  getStoredToken(): string | null {
    return this.tokenStorage.getToken();
  }

  getStoredRefreshToken(): string | null {
    return this.tokenStorage.getRefreshToken();
  }

  getStoredUser(): User | null {
    return (this.tokenStorage as BrowserTokenStorage).getUserData();
  }

  isAuthenticated(): boolean {
    const token = this.tokenStorage.getToken();
    const user = this.getStoredUser();
    return !!(token && user);
  }

  clearAuthData(): void {
    this.tokenStorage.clear();
  }

  // Add authentication header to external requests
  getAuthHeaders(): HeadersInit {
    const token = this.tokenStorage.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // Check if token is likely expired (basic check)
  isTokenLikelyExpired(): boolean {
    const token = this.tokenStorage.getToken();
    if (!token) return true;

    try {
      // Basic JWT structure check - real expiry checking would require JWT decode
      const parts = token.split('.');
      if (parts.length !== 3) return true;

      // For now, just check if we have a valid-looking token structure
      return false;
    } catch {
      return true;
    }
  }

  // Validate email format
  validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  // Validate password requirements
  validatePassword(password: string): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (password.length < 8) {
      errors.push('密码长度至少8位');
    }
    if (!/\d/.test(password)) {
      errors.push('密码必须包含至少一个数字');
    }
    if (!/[a-zA-Z]/.test(password)) {
      errors.push('密码必须包含至少一个字母');
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }
}

// Export singleton instance
export const authAPI = new AuthAPIClient();
export default authAPI;