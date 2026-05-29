import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Upload,
  Plus,
  Save,
  Trash2,
  Sparkles,
  Eye,
  Download,
  ScrollText,
  ListChecks,
  Users,
  FileText,
  CheckCircle2,
  RefreshCw,
  type LucideIcon,
} from "lucide-react";
import { api } from "../lib/api";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, EmptyState, Spinner, type Tone } from "../components/ui";
import { Stepper } from "../components/Stepper";
import { examStatus, copyStatus } from "../lib/status";
import Dashboard from "../components/Dashboard";

type Exam = { id: number; title: string; subject: string; status: string };
type RubricItem = {
  id?: number;
  question_number: string;
  intitule: string;
  expected_answer: string;
  points_max: number;
  ordre: number;
};
type Policy = {
  id: number;
  name: string;
  condition_description: string;
  fraction_points: number;
};
type Copy = {
  id: number;
  student_identifier: string;
  status: string;
  page_count: number;
};

type Guidance = { icon: LucideIcon; title: string; text: string; tone: Tone };

function computeGuidance(p: {
  rubricCount: number;
  status: string;
  copiesCount: number;
  ungraded: number;
  graded: number;
  reviewed: number;
}): Guidance {
  if (p.rubricCount === 0)
    return {
      icon: ScrollText,
      title: "Étape 1 — Créez le barème",
      text: "Importez le corrigé (extraction automatique) ou ajoutez les questions à la main, puis cliquez « Enregistrer ».",
      tone: "brand",
    };
  if (p.status === "draft" || p.status === "rubric_pending")
    return {
      icon: Save,
      title: "Étape 1 — Validez le barème",
      text: "Relisez les questions, réponses et points, puis cliquez « Enregistrer » pour valider le barème.",
      tone: "warn",
    };
  if (p.copiesCount === 0)
    return {
      icon: Users,
      title: "Étape 2 — Déposez les copies",
      text: "Ajoutez les copies des étudiants (PDF ou image) avec leur identifiant, en haut de la section Copies.",
      tone: "brand",
    };
  if (p.ungraded > 0)
    return {
      icon: Sparkles,
      title: "Étape 3 — Lancez la correction IA",
      text: `${p.ungraded} copie(s) déposée(s) à noter. Cliquez « Noter » sur chaque copie pour lancer la correction.`,
      tone: "brand",
    };
  if (p.reviewed < p.copiesCount)
    return {
      icon: Eye,
      title: "Étape 4 — Révisez les notes",
      text: `${p.graded} copie(s) notée(s) à vérifier. Ouvrez « Réviser » pour valider/ajuster chaque note, puis « Finaliser ».`,
      tone: "warn",
    };
  return {
    icon: CheckCircle2,
    title: "Terminé — toutes les copies sont révisées",
    text: "Vous pouvez exporter les notes : PDF par copie et tableur de la classe.",
    tone: "ok",
  };
}

const bannerTone: Record<Tone, string> = {
  brand: "bg-brand-50 border-brand-200 text-brand-900",
  warn: "bg-amber-50 border-amber-200 text-amber-900",
  ok: "bg-emerald-50 border-emerald-200 text-emerald-900",
  danger: "bg-rose-50 border-rose-200 text-rose-900",
  neutral: "bg-slate-50 border-slate-200 text-slate-800",
};
const bannerIcon: Record<Tone, string> = {
  brand: "text-brand-600",
  warn: "text-amber-600",
  ok: "text-emerald-600",
  danger: "text-rose-600",
  neutral: "text-slate-500",
};

const blurOnWheel = (e: React.WheelEvent<HTMLInputElement>) => e.currentTarget.blur();

export default function ExamDetail() {
  const { id } = useParams();
  const examId = Number(id);
  const nav = useNavigate();
  const { notify } = useToast();
  const [exam, setExam] = useState<Exam | null>(null);
  const [rubric, setRubric] = useState<RubricItem[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [copies, setCopies] = useState<Copy[]>([]);
  const [busy, setBusy] = useState(false);
  const [gradingId, setGradingId] = useState<number | null>(null);

  async function reload() {
    const [e, r, p, c] = await Promise.all([
      api.get(`/api/exams/${examId}`),
      api.get(`/api/exams/${examId}/rubric`),
      api.get(`/api/exams/${examId}/policies`),
      api.get(`/api/exams/${examId}/copies`),
    ]);
    setExam(e);
    setRubric(r);
    setPolicies(p);
    setCopies(c);
  }

  useEffect(() => {
    reload().catch((e) => notify(e.message, "error"));
  }, [examId]);

  // ---- Rubric ----
  async function uploadRubric(file: File) {
    setBusy(true);
    notify("Extraction du barème par vision en cours…", "info");
    try {
      const draft: RubricItem[] = await api.upload(
        `/api/exams/${examId}/rubric/extract`,
        file,
      );
      await reload();
      setRubric(draft.map((d, i) => ({ ...d, ordre: i })));
      notify(`${draft.length} questions extraites — vérifiez puis enregistrez.`);
    } catch (e: any) {
      notify(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function saveRubric() {
    setBusy(true);
    try {
      const items = rubric.map((r, i) => ({ ...r, ordre: i }));
      await api.put(`/api/exams/${examId}/rubric/bulk`, { items });
      notify("Barème validé.");
      await reload();
    } catch (e: any) {
      notify(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  const addRubricRow = () =>
    setRubric((r) => [
      ...r,
      { question_number: "", intitule: "", expected_answer: "", points_max: 0, ordre: r.length },
    ]);
  const updateRubric = (i: number, patch: Partial<RubricItem>) =>
    setRubric((r) => r.map((it, idx) => (idx === i ? { ...it, ...patch } : it)));
  const removeRubric = (i: number) =>
    setRubric((r) => r.filter((_, idx) => idx !== i));

  // ---- Policies ----
  async function savePolicy(p: Policy) {
    try {
      await api.patch(`/api/exams/${examId}/policies/${p.id}`, {
        name: p.name,
        condition_description: p.condition_description,
        fraction_points: p.fraction_points,
      });
      notify("Règle enregistrée.");
      await reload();
    } catch (e: any) {
      notify(e.message, "error");
    }
  }
  async function deletePolicy(pid: number) {
    await api.delete(`/api/exams/${examId}/policies/${pid}`);
    await reload();
  }
  async function addPolicy() {
    await api.post(`/api/exams/${examId}/policies`, {
      name: "Nouvelle règle",
      condition_description: "",
      fraction_points: 0.5,
    });
    await reload();
  }

  // ---- Copies ----
  async function uploadCopy(file: File, ident: string) {
    setBusy(true);
    try {
      await api.upload(`/api/exams/${examId}/copies`, file, {
        student_identifier: ident,
      });
      notify(`Copie de ${ident} déposée. Prochaine étape : « Noter ».`);
      await reload();
    } catch (e: any) {
      notify(e.message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function gradeCopy(copyId: number) {
    setGradingId(copyId);
    notify("Notation par IA en cours…", "info");
    try {
      await api.post(`/api/exams/${examId}/copies/${copyId}/grade`);
      notify("Notation terminée — passez à la revue.");
      await reload();
    } catch (e: any) {
      notify(e.message, "error");
    } finally {
      setGradingId(null);
    }
  }

  if (!exam)
    return (
      <div className="flex justify-center py-20">
        <Spinner className="w-6 h-6" />
      </div>
    );

  const meta = examStatus(exam.status);
  const total = rubric.reduce((s, r) => s + (Number(r.points_max) || 0), 0);
  const canGrade = ["rubric_ready", "grading", "closed"].includes(exam.status);
  const ungraded = copies.filter((c) => c.status === "uploaded" || c.status === "extracted").length;
  const graded = copies.filter((c) => c.status === "graded").length;
  const reviewed = copies.filter((c) => c.status === "reviewed").length;
  const guidance = computeGuidance({
    rubricCount: rubric.length,
    status: exam.status,
    copiesCount: copies.length,
    ungraded,
    graded,
    reviewed,
  });
  const GIcon = guidance.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-600 transition mb-2"
        >
          <ArrowLeft className="w-4 h-4" /> Examens
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">
                {exam.title}
              </h1>
              <Badge tone={meta.tone}>{meta.label}</Badge>
            </div>
            <p className="text-sm text-slate-500 mt-1 font-mono">{exam.subject || "—"}</p>
          </div>
        </div>
        <div className="mt-5 overflow-x-auto pb-1">
          <Stepper status={exam.status} />
        </div>
      </div>

      {/* Guidance — prochaine étape */}
      <div className={`flex items-start gap-3 rounded-xl border p-4 ${bannerTone[guidance.tone]}`}>
        <GIcon className={`w-5 h-5 shrink-0 mt-0.5 ${bannerIcon[guidance.tone]}`} />
        <div>
          <div className="text-sm font-semibold">{guidance.title}</div>
          <div className="text-sm opacity-90 mt-0.5">{guidance.text}</div>
        </div>
      </div>

      {/* Barème */}
      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <ScrollText className="w-4 h-4 text-brand-600" />
            <h2 className="section-title">Barème</h2>
            <Badge tone="neutral">{total.toFixed(2)} pts</Badge>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className={`btn-secondary btn-sm cursor-pointer ${busy ? "opacity-50 pointer-events-none" : ""}`}>
              <Upload className="w-3.5 h-3.5" />
              Importer un corrigé
              <input
                type="file"
                accept=".pdf,image/*"
                className="hidden"
                disabled={busy}
                onChange={(e) => e.target.files?.[0] && uploadRubric(e.target.files[0])}
              />
            </label>
            <Button size="sm" variant="ghost" icon={Plus} onClick={addRubricRow}>
              Question
            </Button>
            <Button size="sm" variant="primary" icon={Save} onClick={saveRubric} loading={busy}>
              Enregistrer
            </Button>
          </div>
        </div>

        {rubric.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="Aucune question"
            description="Importez le corrigé pour une extraction automatique, ou ajoutez les questions à la main."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wide bg-slate-50/60">
                  <th className="px-5 py-2.5 w-20">N°</th>
                  <th className="px-3 py-2.5">Intitulé</th>
                  <th className="px-3 py-2.5">Réponse attendue</th>
                  <th className="px-3 py-2.5 w-24">Points</th>
                  <th className="px-3 py-2.5 w-12" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rubric.map((r, i) => (
                  <tr key={i} className="align-top hover:bg-slate-50/40">
                    <td className="px-5 py-3">
                      <input
                        className="input"
                        value={r.question_number}
                        onChange={(e) => updateRubric(i, { question_number: e.target.value })}
                      />
                    </td>
                    <td className="px-3 py-3">
                      <textarea
                        className="input min-h-[2.75rem]"
                        rows={2}
                        value={r.intitule}
                        onChange={(e) => updateRubric(i, { intitule: e.target.value })}
                      />
                    </td>
                    <td className="px-3 py-3">
                      <textarea
                        className="input min-h-[2.75rem]"
                        rows={2}
                        value={r.expected_answer}
                        onChange={(e) => updateRubric(i, { expected_answer: e.target.value })}
                      />
                    </td>
                    <td className="px-3 py-3">
                      <input
                        type="number"
                        step="0.25"
                        min="0"
                        className="input"
                        value={r.points_max}
                        onWheel={blurOnWheel}
                        onChange={(e) => updateRubric(i, { points_max: Number(e.target.value) })}
                      />
                    </td>
                    <td className="px-3 py-3">
                      <button
                        className="btn-ghost btn-icon text-slate-300 hover:text-rose-600"
                        onClick={() => removeRubric(i)}
                        title="Supprimer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Règles de notation */}
      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <ListChecks className="w-4 h-4 text-brand-600" />
            <h2 className="section-title">Règles de notation partielle</h2>
          </div>
          <Button size="sm" variant="ghost" icon={Plus} onClick={addPolicy}>
            Règle
          </Button>
        </div>
        <div className="px-5 py-4 space-y-3">
          <p className="text-xs text-slate-400 -mt-1 mb-1">
            La note finale est calculée côté serveur : points = points max × fraction de la règle choisie.
          </p>
          {policies.map((p) => (
            <PolicyRow key={p.id} p={p} onSave={savePolicy} onDelete={() => deletePolicy(p.id)} />
          ))}
        </div>
      </Card>

      {/* Copies */}
      <Card className="overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-brand-600" />
            <h2 className="section-title">Copies</h2>
            <Badge tone="neutral">{copies.length}</Badge>
          </div>
          <CopyUploader onUpload={uploadCopy} disabled={busy} />
        </div>
        {copies.length === 0 ? (
          <EmptyState
            icon={Users}
            title="Aucune copie déposée"
            description="Déposez les copies (PDF ou images) avec l'identifiant de chaque étudiant."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[560px]">
              <thead>
                <tr className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wide bg-slate-50/60">
                  <th className="px-5 py-2.5">Étudiant</th>
                  <th className="px-3 py-2.5 w-20">Pages</th>
                  <th className="px-3 py-2.5 w-36">Statut</th>
                  <th className="px-3 py-2.5 text-right w-60" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {copies.map((c) => {
                  const cm = copyStatus(c.status);
                  const pending = c.status === "uploaded" || c.status === "extracted";
                  const isGraded = c.status === "graded";
                  const isReviewed = c.status === "reviewed";
                  return (
                    <tr key={c.id} className="hover:bg-slate-50/40">
                      <td className="px-5 py-3 font-medium text-slate-800">
                        {c.student_identifier}
                      </td>
                      <td className="px-3 py-3 text-slate-500">{c.page_count}</td>
                      <td className="px-3 py-3">
                        <Badge tone={cm.tone}>{cm.label}</Badge>
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex items-center justify-end gap-2 flex-wrap">
                          {pending && (
                            <Button
                              size="sm"
                              variant="primary"
                              icon={Sparkles}
                              loading={gradingId === c.id}
                              disabled={!canGrade}
                              title={canGrade ? "Lancer la correction IA" : "Validez d'abord le barème"}
                              onClick={() => gradeCopy(c.id)}
                            >
                              Noter
                            </Button>
                          )}
                          {(isGraded || isReviewed) && (
                            <Button
                              size="sm"
                              variant={isGraded ? "primary" : "secondary"}
                              icon={Eye}
                              onClick={() => nav(`/copies/${c.id}`)}
                            >
                              {isReviewed ? "Revoir" : "Réviser"}
                            </Button>
                          )}
                          {isGraded && (
                            <Button
                              size="sm"
                              variant="ghost"
                              icon={RefreshCw}
                              loading={gradingId === c.id}
                              title="Relancer la notation"
                              onClick={() => gradeCopy(c.id)}
                            >
                              Re-noter
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Dashboard */}
      <Dashboard examId={examId} />

      {/* Exports */}
      <Card className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Download className="w-4 h-4 text-brand-600" />
          <h2 className="section-title">Exports</h2>
        </div>
        <Button
          variant="secondary"
          icon={Download}
          onClick={() =>
            api
              .download(`/api/exams/${examId}/export/class.xlsx`, `exam-${examId}-notes.xlsx`)
              .then(() => notify("Tableur téléchargé."))
              .catch((e) => notify(e.message, "error"))
          }
        >
          Tableur de la classe (.xlsx)
        </Button>
      </Card>
    </div>
  );
}

function PolicyRow({
  p,
  onSave,
  onDelete,
}: {
  p: Policy;
  onSave: (p: Policy) => void;
  onDelete: () => void;
}) {
  const [name, setName] = useState(p.name);
  const [desc, setDesc] = useState(p.condition_description);
  const [frac, setFrac] = useState(p.fraction_points);
  const dirty =
    name !== p.name || desc !== p.condition_description || frac !== p.fraction_points;

  return (
    <div className="grid grid-cols-12 gap-3 items-start">
      <input
        className="input col-span-12 sm:col-span-3"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <textarea
        className="input col-span-12 sm:col-span-5 min-h-[2.5rem]"
        rows={1}
        value={desc}
        onChange={(e) => setDesc(e.target.value)}
      />
      <div className="col-span-6 sm:col-span-2">
        <input
          type="number"
          step="0.05"
          min="0"
          max="1"
          className="input"
          value={frac}
          onWheel={(e) => e.currentTarget.blur()}
          onChange={(e) => setFrac(Number(e.target.value))}
        />
        <span className="hint">fraction (0–1)</span>
      </div>
      <div className="col-span-6 sm:col-span-2 flex gap-2">
        <Button
          size="sm"
          variant={dirty ? "primary" : "secondary"}
          onClick={() => onSave({ ...p, name, condition_description: desc, fraction_points: frac })}
        >
          {dirty ? "Enregistrer" : "OK"}
        </Button>
        <button
          className="btn-ghost btn-icon text-slate-300 hover:text-rose-600"
          onClick={onDelete}
          title="Supprimer"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function CopyUploader({
  onUpload,
  disabled,
}: {
  onUpload: (f: File, ident: string) => void;
  disabled: boolean;
}) {
  const [ident, setIdent] = useState("");
  return (
    <div className="flex items-center gap-2">
      <input
        className="input w-44 py-1.5"
        placeholder="Identifiant étudiant"
        value={ident}
        onChange={(e) => setIdent(e.target.value)}
      />
      <label
        className={`btn-primary btn-sm cursor-pointer ${disabled || !ident ? "opacity-50 pointer-events-none" : ""}`}
      >
        <Upload className="w-3.5 h-3.5" />
        Déposer
        <input
          type="file"
          accept=".pdf,image/*"
          className="hidden"
          disabled={disabled || !ident}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f && ident) {
              onUpload(f, ident);
              setIdent("");
            }
          }}
        />
      </label>
    </div>
  );
}
