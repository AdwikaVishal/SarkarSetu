"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { MeResponse } from "@/types/api";

interface AuthContextType {
  user: MeResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  /** Re-run the initial auth bootstrap (useful when the API was unreachable). */
  retryAuth: () => Promise<void>;
  /** True when the app auto-signs-in a demo user instead of showing a login form. */
  isDevMode: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEV_CREDENTIALS = {
  email: "demo@sarkarsetu.ai",
  password: "DemoPass123!",
  fullName: "Demo User",
};

const isDevMode = typeof window !== "undefined" && 
  (import.meta.env.DEV || import.meta.env.VITE_DEV_MODE === "true" || navigator.userAgent.includes("sarkarsetu-dev"));

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async (): Promise<MeResponse | null> => {
    // If already authenticated with a valid token, try to get user info
    if (api.isAuthenticated()) {
      try {
        const userData = await api.me();
        setUser(userData);
        return userData;
      } catch {
        // Token is stale/invalid; clear it
        api.clearTokens();
      }
    }

    // In dev mode, auto-login with demo credentials
    if (isDevMode) {
      try {
        const loginResponse = await api.login({
          email: DEV_CREDENTIALS.email,
          password: DEV_CREDENTIALS.password,
        });
        if (loginResponse.user) {
          setUser(loginResponse.user);
          return loginResponse.user;
        }
      } catch {
        // Login failed in dev; fall through to unauthenticated state
      }
    }

    setUser(null);
    return null;
  }, []);

  const refreshUser = useCallback(async (): Promise<void> => {
    await loadUser();
  }, [loadUser]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        await loadUser();
      } finally {
        if (mounted) setIsLoading(false);
      }
    })();
    return () => { mounted = false; };
  }, [loadUser]);

  const login = async (email: string, password: string) => {
    const response = await api.login({ email, password });
    if (response.user) {
      setUser(response.user);
    } else {
      await loadUser();
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const response = await api.register({ email, password, full_name: fullName });
    if (response.user) {
      setUser(response.user);
    } else {
      await loadUser();
    }
  };

  const logout = async () => {
    try {
      const refreshToken = api.getRefreshToken();
      if (refreshToken) {
        await api.logout({ refresh_token: refreshToken });
      }
    } finally {
      api.clearTokens();
      setUser(null);
    }
  };

  const retryAuth = useCallback(async () => {
    setIsLoading(true);
    try {
      await loadUser();
    } finally {
      setIsLoading(false);
    }
  }, [loadUser]);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
    retryAuth,
    isDevMode,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    // Fallback when used outside AuthProvider (e.g., during tests)
    return {
      user: null,
      isLoading: true,
      isAuthenticated: false,
      login: async () => {},
      register: async () => {},
      logout: async () => {},
      refreshUser: async () => {},
      retryAuth: async () => {},
      isDevMode: false,
    };
  }
  return context;
}