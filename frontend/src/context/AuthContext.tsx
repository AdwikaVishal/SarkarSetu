"use client";

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";
import { api, type MeResponse } from "@/lib/api";

interface AuthContextType {
  user: MeResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const DEV_USER = {
  email: "demo@sarkarsetu.ai",
  password: "DemoPass123!",
  full_name: "Demo User"
};

const isDev = process.env.NODE_ENV === "development" || process.env.NEXT_PUBLIC_DEV_MODE === "true";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await api.me();
      setUser(userData);
    } catch {
      setUser(null);
    }
  }, []);

  const devLogin = useCallback(async (): Promise<MeResponse | null> => {
    if (!isDev) return null;
    
    try {
      // Try to login first
      console.log("Dev login: attempting login...");
      const loginResponse = await api.login({ email: DEV_USER.email, password: DEV_USER.password });
      console.log("Dev login response:", loginResponse);
      if (loginResponse.user) {
        return loginResponse.user;
      }
    } catch (err) {
      console.log("Dev login failed, trying register:", err);
    }
    
    try {
      console.log("Dev login: attempting register...");
      const registerResponse = await api.register({ email: DEV_USER.email, password: DEV_USER.password, full_name: DEV_USER.full_name });
      console.log("Dev register response:", registerResponse);
      if (registerResponse.user) {
        return registerResponse.user;
      }
      // Fallback to refresh
      const userData = await api.me();
      return userData;
    } catch (err) {
      console.log("Dev register failed:", err);
      return null;
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    const initAuth = async () => {
      try {
        let userData: MeResponse | null = null;

        if (api.isAuthenticated()) {
          try {
            userData = await api.me();
          } catch {
            // Stored access token is stale/unusable; fall through to dev login
            // instead of leaving the app stuck in its loading state.
            api.clearTokens();
          }
        }

        if (!userData && isDev) {
          userData = await devLogin();
        }

        if (mounted) setUser(userData);
      } finally {
        // No matter what happened (network error, refresh failure, unexpected
        // exception) the global loading flag must be released.
        if (mounted) setIsLoading(false);
      }
    };
    initAuth();
    return () => { mounted = false; };
  }, [devLogin]);

  const login = async (email: string, password: string) => {
    const response = await api.login({ email, password });
    if (response.user) {
      setUser(response.user);
    } else {
      await refreshUser();
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    const response = await api.register({ email, password, full_name: fullName });
    if (response.user) {
      setUser(response.user);
    } else {
      await refreshUser();
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

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
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
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}