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

  useEffect(() => {
    let mounted = true;
    const initAuth = async () => {
      try {
        let userData: MeResponse | null = null;

        if (api.isAuthenticated()) {
          try {
            userData = await api.me();
          } catch {
            // Stored access token is stale/unusable; clear and let the user log in.
            api.clearTokens();
          }
        }

        if (mounted) setUser(userData);
      } finally {
        // Always release the loading flag so the UI can render.
        if (mounted) setIsLoading(false);
      }
    };
    initAuth();
    return () => { mounted = false; };
  }, [refreshUser]);

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
