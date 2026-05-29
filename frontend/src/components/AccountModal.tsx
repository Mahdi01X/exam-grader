import { useState } from "react";
import { X, User as UserIcon, KeyRound } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useToast } from "./Toast";
import { Button, Field } from "./ui";

export function AccountModal({ onClose }: { onClose: () => void }) {
  const { user, refreshUser } = useAuth();
  const { notify } = useToast();

  const [name, setName] = useState(user?.name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [savingProfile, setSavingProfile] = useState(false);

  const [cur, setCur] = useState("");
  const [nw, setNw] = useState("");
  const [nw2, setNw2] = useState("");
  const [savingPw, setSavingPw] = useState(false);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await api.patch("/api/auth/me", { name, email });
      await refreshUser();
      notify("Profil mis à jour.");
    } catch (err: any) {
      notify(err.message, "error");
    } finally {
      setSavingProfile(false);
    }
  }

  async function savePassword(e: React.FormEvent) {
    e.preventDefault();
    if (nw !== nw2) {
      notify("Les deux mots de passe ne correspondent pas.", "error");
      return;
    }
    if (nw.length < 8) {
      notify("Le nouveau mot de passe doit faire au moins 8 caractères.", "error");
      return;
    }
    setSavingPw(true);
    try {
      await api.post("/api/auth/change-password", {
        current_password: cur,
        new_password: nw,
      });
      notify("Mot de passe changé. Utilise-le à ta prochaine connexion.");
      setCur("");
      setNw("");
      setNw2("");
    } catch (err: any) {
      notify(err.message, "error");
    } finally {
      setSavingPw(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="card w-full max-w-md shadow-pop animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <h2 className="section-title">Mon compte</h2>
          <button className="btn-ghost btn-icon" onClick={onClose} title="Fermer">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-6">
          {/* Profil */}
          <form onSubmit={saveProfile} className="space-y-3">
            <div className="flex items-center gap-2 text-slate-500">
              <UserIcon className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wide">Profil</span>
            </div>
            <Field label="Nom">
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
            </Field>
            <Field label="Email (identifiant de connexion)">
              <input
                className="input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </Field>
            <div className="flex justify-end">
              <Button type="submit" variant="primary" size="sm" loading={savingProfile}>
                Enregistrer le profil
              </Button>
            </div>
          </form>

          <div className="divider" />

          {/* Mot de passe */}
          <form onSubmit={savePassword} className="space-y-3">
            <div className="flex items-center gap-2 text-slate-500">
              <KeyRound className="w-4 h-4" />
              <span className="text-xs font-semibold uppercase tracking-wide">
                Mot de passe
              </span>
            </div>
            <Field label="Mot de passe actuel">
              <input
                className="input"
                type="password"
                value={cur}
                onChange={(e) => setCur(e.target.value)}
                autoComplete="current-password"
              />
            </Field>
            <Field label="Nouveau mot de passe (8 caractères min.)">
              <input
                className="input"
                type="password"
                value={nw}
                onChange={(e) => setNw(e.target.value)}
                autoComplete="new-password"
              />
            </Field>
            <Field label="Confirmer le nouveau mot de passe">
              <input
                className="input"
                type="password"
                value={nw2}
                onChange={(e) => setNw2(e.target.value)}
                autoComplete="new-password"
              />
            </Field>
            <div className="flex justify-end">
              <Button type="submit" variant="primary" size="sm" loading={savingPw}>
                Changer le mot de passe
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
