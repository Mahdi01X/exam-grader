import { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { LogIn } from "lucide-react";
import { useAuth } from "../lib/auth";
import { Logo } from "../components/Logo";
import { Button, Field } from "../components/ui";

export default function Login() {
  const { user, login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await login(email, password);
      nav("/");
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen grid place-items-center px-4 relative overflow-hidden">
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-slate-50 via-white to-brand-50" />
      <div className="absolute -z-10 top-[-12%] right-[-8%] w-[42rem] h-[42rem] rounded-full bg-brand-100/40 blur-3xl" />
      <div className="absolute -z-10 bottom-[-15%] left-[-10%] w-[36rem] h-[36rem] rounded-full bg-indigo-100/30 blur-3xl" />

      <div className="w-full max-w-sm animate-slide-up">
        <div className="flex justify-center mb-6">
          <Logo />
        </div>
        <div className="card-pad shadow-elevated">
          <h1 className="text-lg font-semibold text-slate-900 text-center">
            Connexion correcteur
          </h1>
          <p className="text-sm text-slate-400 text-center mt-1 mb-6">
            Accédez à votre espace de correction
          </p>
          <form onSubmit={submit} className="space-y-4">
            <Field label="Adresse email">
              <input
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="vous@universite.fr"
                autoFocus
              />
            </Field>
            <Field label="Mot de passe">
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••"
              />
            </Field>
            {err && (
              <div className="text-sm text-rose-600 bg-rose-50 ring-1 ring-inset ring-rose-200 rounded-lg px-3 py-2">
                {err}
              </div>
            )}
            <Button
              variant="primary"
              type="submit"
              icon={LogIn}
              loading={busy}
              className="w-full"
            >
              Se connecter
            </Button>
          </form>
        </div>
        <p className="text-center text-xs text-slate-400 mt-6">
          Plateforme de correction d'examens assistée par IA
        </p>
      </div>
    </div>
  );
}
