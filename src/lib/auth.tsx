import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, setToken } from "./api";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("ziloo:token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      login: async (email, password) => {
        const { access_token } = await api.login(email, password);
        setToken(access_token);
        setUser(await api.me());
      },
      register: async (email, password, fullName) => {
        await api.register(email, password, fullName);
        const { access_token } = await api.login(email, password);
        setToken(access_token);
        setUser(await api.me());
      },
      logout: () => {
        setToken(null);
        setUser(null);
        localStorage.removeItem("ziloo:activeProjectId");
      },
    }),
    [user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
