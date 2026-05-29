import { ReactNode } from "react";
import { Link } from "react-router-dom";
import { LogOut } from "lucide-react";
import { useAuth } from "../lib/auth";
import { Logo } from "./Logo";
import { Badge } from "./ui";

const roleLabels: Record<string, string> = {
  admin: "Admin",
  professeur: "Professeur",
  assistant: "Assistant",
};

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link to="/" className="transition-opacity hover:opacity-80">
            <Logo />
          </Link>
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-medium text-slate-700 leading-tight">
                {user?.name}
              </div>
              <div className="text-xs text-slate-400 leading-tight">{user?.email}</div>
            </div>
            <Badge tone="neutral">{roleLabels[user?.role ?? ""] ?? user?.role}</Badge>
            <button
              onClick={logout}
              className="btn-ghost btn-icon"
              title="Déconnexion"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8 animate-fade-in">
        {children}
      </main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 py-3 text-xs text-slate-400 flex items-center justify-between">
          <span>
            Le professeur reste décideur final — chaque note est justifiée et tracée.
          </span>
          <span className="hidden sm:block">ExamGrader · v0.1</span>
        </div>
      </footer>
    </div>
  );
}
