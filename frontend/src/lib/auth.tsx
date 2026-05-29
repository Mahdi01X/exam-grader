import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api } from "./api";

type User = { id: number; name: string; email: string; role: string };

type AuthCtx = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const Ctx = createContext<AuthCtx>({
  user: null,
  loading: true,
  login: async () => {},
  logout: () => {},
  refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = localStorage.getItem("token");
    if (!t) {
      setLoading(false);
      return;
    }
    api
      .get("/api/auth/me")
      .then((u: any) => setUser(u))
      .catch(() => {
        localStorage.removeItem("token");
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const r = await api.login(email, password);
    localStorage.setItem("token", r.access_token);
    setUser({ id: r.user_id, name: r.name, email, role: r.role });
  }

  function logout() {
    localStorage.removeItem("token");
    setUser(null);
  }

  async function refreshUser() {
    const u = await api.get("/api/auth/me");
    setUser(u);
  }

  return (
    <Ctx.Provider value={{ user, loading, login, logout, refreshUser }}>
      {children}
    </Ctx.Provider>
  );
}

export const useAuth = () => useContext(Ctx);
