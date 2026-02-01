'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface User {
  id: number;
  email: string;
  name: string | null;
  credits: number;
  is_premium: boolean;
  is_verified: boolean;
  streak_days: number;
  total_clips_generated: number;
  total_videos_processed: number;
  created_at: string;
  last_login_at: string | null;
}

export interface Plan {
  id: string;
  name: string;
  credits: number;
  price: number;
  price_yearly: number;
  features: string[];
  limits: {
    max_video_duration: number;
    max_clips_per_video: number;
    max_projects: number;
  };
}

export interface Subscription {
  plan: Plan;
  status: string;
  is_yearly: boolean;
  current_period_end: string | null;
}

interface AuthContextType {
  user: User | null;
  subscription: Subscription | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  checkin: () => Promise<{ success: boolean; total_bonus?: number; streak_days?: number; message?: string }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'clipgenius_access_token';
const REFRESH_TOKEN_KEY = 'clipgenius_refresh_token';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const getStoredTokens = () => {
    if (typeof window === 'undefined') return { accessToken: null, refreshToken: null };
    return {
      accessToken: localStorage.getItem(TOKEN_KEY),
      refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
    };
  };

  const storeTokens = (accessToken: string, refreshToken: string) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  };

  const clearTokens = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  };

  const fetchUser = useCallback(async (token: string): Promise<{ user: User; subscription: Subscription | null } | null> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          return null;
        }
        throw new Error('Failed to fetch user');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching user:', error);
      return null;
    }
  }, []);

  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    const { refreshToken } = getStoredTokens();
    if (!refreshToken) return null;

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        clearTokens();
        return null;
      }

      const data = await response.json();
      storeTokens(data.access_token, data.refresh_token);
      return data.access_token;
    } catch (error) {
      console.error('Error refreshing token:', error);
      clearTokens();
      return null;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const { accessToken } = getStoredTokens();
    if (!accessToken) {
      setUser(null);
      setSubscription(null);
      setIsLoading(false);
      return;
    }

    let userData = await fetchUser(accessToken);

    // Try refreshing token if unauthorized
    if (!userData) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        userData = await fetchUser(newToken);
      }
    }

    if (userData) {
      setUser(userData.user);
      setSubscription(userData.subscription);
    } else {
      setUser(null);
      setSubscription(null);
      clearTokens();
    }

    setIsLoading(false);
  }, [fetchUser, refreshAccessToken]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    storeTokens(data.access_token, data.refresh_token);
    setUser(data.user);

    // Fetch subscription data
    await refreshUser();
  };

  const register = async (email: string, password: string, name?: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, name }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data = await response.json();
    storeTokens(data.access_token, data.refresh_token);
    setUser(data.user);

    // Fetch subscription data
    await refreshUser();
  };

  const logout = () => {
    clearTokens();
    setUser(null);
    setSubscription(null);
  };

  const checkin = async () => {
    const { accessToken } = getStoredTokens();
    if (!accessToken) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${API_BASE_URL}/auth/checkin`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Check-in failed');
    }

    const result = await response.json();

    // Refresh user to get updated credits
    if (result.success) {
      await refreshUser();
    }

    return result;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        subscription,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
        checkin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}
