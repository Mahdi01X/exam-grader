import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, BookOpen, ChevronRight, FilePlus2, X, GraduationCap } from "lucide-react";
import { api } from "../lib/api";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, EmptyState, Field } from "../components/ui";
import { examStatus } from "../lib/status";

type Exam = {
  id: number;
  title: string;
  subject: string;
  status: string;
  updated_at: string;
};

export default function Exams() {
  const nav = useNavigate();
  const { notify } = useToast();
  const [exams, setExams] = useState<Exam[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [busy, setBusy] = useState(false);

  async function refresh() {
    try {
      const r = await api.get("/api/exams");
      setExams(r);
    } catch (e: any) {
      notify(e.message, "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const exam = await api.post("/api/exams", { title, subject });
      notify("Examen créé.");
      setTitle("");
      setSubject("");
      setCreating(false);
      nav(`/exams/${exam.id}`);
    } catch (e: any) {
      notify(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">
            Examens
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Créez un examen, importez le barème, puis corrigez les copies.
          </p>
        </div>
        {!creating && (
          <Button variant="primary" icon={Plus} onClick={() => setCreating(true)}>
            Nouvel examen
          </Button>
        )}
      </div>

      {creating && (
        <Card className="p-5 animate-slide-up">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title flex items-center gap-2">
              <FilePlus2 className="w-4 h-4 text-brand-600" />
              Nouvel examen
            </h2>
            <button
              className="btn-ghost btn-icon"
              onClick={() => setCreating(false)}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <form onSubmit={create} className="grid sm:grid-cols-2 gap-4">
            <Field label="Titre de l'examen">
              <input
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="ex. Final — Calcul différentiel"
                autoFocus
                required
              />
            </Field>
            <Field label="Matière / sigle">
              <input
                className="input"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="ex. MAT1410"
              />
            </Field>
            <div className="sm:col-span-2 flex justify-end gap-2">
              <Button variant="ghost" type="button" onClick={() => setCreating(false)}>
                Annuler
              </Button>
              <Button variant="primary" type="submit" loading={busy} icon={Plus}>
                Créer l'examen
              </Button>
            </div>
          </form>
        </Card>
      )}

      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card p-5 h-32">
              <div className="skeleton h-4 w-2/3 mb-3" />
              <div className="skeleton h-3 w-1/3" />
            </div>
          ))}
        </div>
      ) : exams.length === 0 ? (
        <Card>
          <EmptyState
            icon={GraduationCap}
            title="Aucun examen pour l'instant"
            description="Créez votre premier examen pour commencer à corriger."
            action={
              <Button variant="primary" icon={Plus} onClick={() => setCreating(true)}>
                Nouvel examen
              </Button>
            }
          />
        </Card>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {exams.map((e) => {
            const meta = examStatus(e.status);
            return (
              <button
                key={e.id}
                onClick={() => nav(`/exams/${e.id}`)}
                className="card p-5 text-left group hover:shadow-elevated hover:border-brand-200 transition-all duration-200"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="grid place-items-center w-10 h-10 rounded-lg bg-brand-50 text-brand-600">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <Badge tone={meta.tone}>{meta.label}</Badge>
                </div>
                <h3 className="font-semibold text-slate-900 leading-snug line-clamp-2">
                  {e.title}
                </h3>
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
                  <span className="text-xs text-slate-400 font-mono">
                    {e.subject || "—"}
                  </span>
                  <span className="text-brand-600 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ChevronRight className="w-4 h-4" />
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
