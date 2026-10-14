import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi } from "../api/auth";
import { candidatesApi } from "../api/candidates";
import { registerUnauthorizedHandler } from "../api/client";
import { getToken, setToken as persistToken, clearToken } from "../utils/storage";
import type { LoginRequest, RegisterRequest, UserResponse } from "../types/auth";

interface AuthContextValue {
  user: UserResponse | null;
  candidateId: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  register: (payload: RegisterRequest) => Promise<void>;
  logout: () => void;
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadSession = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
      if (me.role === "CANDIDATE") {
        const profile = await candidatesApi.me().catch(() => null);
        setCandidateId(profile?.id ?? null);
      }
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSession();
    registerUnauthorizedHandler(() => {
      setUser(null);
      setCandidateId(null);
    });
  }, [loadSession]);

  const login = useCallback(async (payload: LoginRequest) => {
    const token = await authApi.login(payload);
    persistToken(token.access_token);
    const me = await authApi.me();
    setUser(me);
    if (me.role === "CANDIDATE") {
      const profile = await candidatesApi.me().catch(() => null);
      setCandidateId(profile?.id ?? null);
    }
  }, []);

  const register = useCallback(async (payload: RegisterRequest) => {
    await authApi.register(payload);
    await login({ email: payload.email, password: payload.password });
  }, [login]);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    setCandidateId(null);
  }, []);

  const value = useMemo(
    () => ({ user, candidateId, isLoading, isAuthenticated: !!user, login, register, logout }),
    [user, candidateId, isLoading, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
