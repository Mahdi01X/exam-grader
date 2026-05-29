import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Download,
  FileCheck2,
  ChevronLeft,
  ChevronRight,
  Check,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import { api } from "../lib/api";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, Spinner } from "../components/ui";

type RubricItem = {
  id: number;
  question_number: string;
  intitule: string;
  expected_answer: string;
  points_max: number;
};
type Policy = { id: number; name: string; fraction_points: number };
type Grade = {
  id: number;
  rubric_item_id: number;
  applied_policy_id: number | null;
  extracted_text: string;
  proposed_points: number;
  applied_fraction: number;
  justification: string;
  confidence: number;
  needs_human_review: boolean;
  final_points: number | null;
  validated_at: string | null;
};
type Copy = {
  id: number;
  exam_id: number;
  student_identifier: string;
  page_count: number;
  status: string;
  grades: Grade[];
};

export default function CopyReview() {
  const { id } = useParams();
  const copyId = Number(id);
  const { notify } = useToast();
  const [copy, setCopy] = useState<Copy | null>(null);
  const [rubric, setRubric] = useState<RubricItem[]>([]);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [page, setPage] = useState(1);
  const [err, setErr] = useState<string | null>(null);

  async function reload() {
    const exams: { id: number }[] = await api.get("/api/exams");
    for (const e of exams) {
      try {
        const c: Copy = await api.get(`/api/exams/${e.id}/copies/${copyId}`);
        const [r, p] = await Promise.all([
          api.get(`/api/exams/${e.id}/rubric`),
          api.get(`/api/exams/${e.id}/policies`),
        ]);
        setCopy(c);
        setRubric(r);
        setPolicies(p);
        return;
      } catch {
        /* try next */
      }
    }
    setErr("Copie introuvable.");
  }

  useEffect(() => {
    reload().catch((e) => setErr(e.message));
  }, [copyId]);

  if (err)
    return (
      <Card className="p-8 text-center text-rose-600">
        <AlertTriangle className="w-6 h-6 mx-auto mb-2" />
        {err}
      </Card>
    );
  if (!copy)
    return (
      <div className="flex justify-center py-20">
        <Spinner className="w-6 h-6" />
      </div>
    );

  const gradesByQ = new Map(copy.grades.map((g) => [g.rubric_item_id, g]));

  async function override(
    g: Grade,
    patch: { final_points?: number; applied_policy_id?: number; justification?: string },
  ) {
    if (!copy) return;
    try {
      const updated: Grade = await api.post(
        `/api/exams/${copy.exam_id}/copies/${copy.id}/grades/${g.id}/override`,
        {
          final_points: patch.final_points ?? g.final_points ?? g.proposed_points,
          applied_policy_id: patch.applied_policy_id ?? g.applied_policy_id ?? null,
          justification: patch.justification ?? g.justification,
        },
      );
      setCopy({ ...copy, grades: copy.grades.map((x) => (x.id === g.id ? updated : x)) });
      notify("Question validée.");
    } catch (e: any) {
      notify(e.message, "error");
    }
  }

  async function finalize() {
    if (!copy) return;
    if (!confirm("Finaliser la copie ? Les questions non modifiées seront validées à la note proposée."))
      return;
    try {
      await api.post(`/api/exams/${copy.exam_id}/copies/${copy.id}/finalize`);
      notify("Copie finalisée.");
      await reload();
    } catch (e: any) {
      notify(e.message, "error");
    }
  }

  const total = rubric.reduce((s, r) => {
    const g = gradesByQ.get(r.id);
    return s + (g?.final_points ?? g?.proposed_points ?? 0);
  }, 0);
  const totalMax = rubric.reduce((s, r) => s + r.points_max, 0);
  const reviewCount = copy.grades.filter((g) => g.needs_human_review).length;
  const pct = totalMax > 0 ? Math.round((total / totalMax) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            to={`/exams/${copy.exam_id}`}
            className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-600 transition mb-2"
          >
            <ArrowLeft className="w-4 h-4" /> Examen
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold text-slate-900 tracking-tight">
              {copy.student_identifier}
            </h1>
            <span className="inline-flex items-baseline gap-1 px-2.5 py-1 rounded-lg bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200">
              <span className="text-lg font-semibold">{total.toFixed(2)}</span>
              <span className="text-xs text-brand-500">/ {totalMax.toFixed(2)} · {pct}%</span>
            </span>
            {reviewCount > 0 && (
              <Badge tone="warn" icon={AlertTriangle}>
                {reviewCount} à réviser
              </Badge>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            icon={Download}
            onClick={() =>
              api
                .download(
                  `/api/exams/${copy.exam_id}/export/copy/${copy.id}.pdf`,
                  `copy-${copy.student_identifier}.pdf`,
                )
                .then(() => notify("PDF téléchargé."))
                .catch((e) => notify(e.message, "error"))
            }
          >
            Export PDF
          </Button>
          <Button variant="primary" icon={FileCheck2} onClick={finalize}>
            Finaliser
          </Button>
        </div>
      </div>

      {/* Side by side */}
      <div className="grid lg:grid-cols-2 gap-4 lg:h-[calc(100vh-200px)]">
        {/* Page viewer */}
        <Card className="flex flex-col overflow-hidden h-[60vh] lg:h-full">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-100 bg-slate-50/50">
            <span className="text-sm text-slate-500">
              Page <span className="font-medium text-slate-700">{page}</span> / {copy.page_count}
            </span>
            <div className="flex gap-1">
              <button
                className="btn-ghost btn-icon disabled:opacity-40"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                className="btn-ghost btn-icon disabled:opacity-40"
                disabled={page >= copy.page_count}
                onClick={() => setPage(page + 1)}
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-auto bg-slate-100 p-3">
            <PageImage examId={copy.exam_id} copyId={copy.id} page={page} />
          </div>
        </Card>

        {/* Questions */}
        <div className="lg:overflow-y-auto pr-1 space-y-3">
          {rubric.map((r) => {
            const g = gradesByQ.get(r.id);
            return (
              <QuestionCard
                key={r.id}
                rubric={r}
                grade={g}
                policies={policies}
                onSave={(patch) => g && override(g, patch)}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

function PageImage({ examId, copyId, page }: { examId: number; copyId: number; page: number }) {
  const [url, setUrl] = useState<string>("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let revoked = "";
    setLoading(true);
    api
      .get(`/api/exams/${examId}/copies/${copyId}/pages/${page}`)
      .then(async (r: any) => {
        const blob = await r.blob();
        const u = URL.createObjectURL(blob);
        revoked = u;
        setUrl(u);
      })
      .catch(() => setUrl(""))
      .finally(() => setLoading(false));
    return () => {
      if (revoked) URL.revokeObjectURL(revoked);
    };
  }, [examId, copyId, page]);
  if (loading)
    return (
      <div className="h-full grid place-items-center">
        <Spinner />
      </div>
    );
  if (!url)
    return (
      <div className="h-full grid place-items-center text-sm text-slate-400">
        Page indisponible
      </div>
    );
  return (
    <img
      src={url}
      alt={`page ${page}`}
      className="w-full rounded-lg shadow-card bg-white"
    />
  );
}

function QuestionCard({
  rubric,
  grade,
  policies,
  onSave,
}: {
  rubric: RubricItem;
  grade?: Grade;
  policies: Policy[];
  onSave: (patch: { final_points?: number; applied_policy_id?: number; justification?: string }) => void;
}) {
  const [pts, setPts] = useState(grade?.final_points ?? grade?.proposed_points ?? 0);
  const [polId, setPolId] = useState<number | null>(grade?.applied_policy_id ?? null);
  const [just, setJust] = useState(grade?.justification ?? "");

  const validated = !!grade?.validated_at;
  const review = grade?.needs_human_review;
  const accent = validated
    ? "border-l-emerald-400"
    : review
      ? "border-l-amber-400"
      : "border-l-brand-300";

  const conf = grade?.confidence ?? 0;
  const confColor = conf >= 0.8 ? "bg-emerald-500" : conf >= 0.6 ? "bg-amber-500" : "bg-rose-500";

  return (
    <div className={`card border-l-4 ${accent} p-4`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <span className="font-semibold text-slate-900">Q{rubric.question_number}</span>
          <span className="text-sm text-slate-500 ml-2">{rubric.intitule}</span>
        </div>
        {grade ? (
          validated ? (
            <Badge tone="ok" icon={CheckCircle2}>Validée</Badge>
          ) : review ? (
            <Badge tone="warn" icon={AlertTriangle}>À réviser</Badge>
          ) : (
            <Badge tone="brand" icon={Sparkles}>Proposée</Badge>
          )
        ) : (
          <Badge tone="neutral">Non notée</Badge>
        )}
      </div>

      {!grade ? (
        <p className="text-sm text-slate-400 mt-2">
          Lancez la notation depuis l'examen pour obtenir une proposition.
        </p>
      ) : (
        <div className="mt-3 space-y-3">
          {/* Confidence */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 uppercase tracking-wide w-20">Confiance</span>
            <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
              <div className={`h-full ${confColor}`} style={{ width: `${conf * 100}%` }} />
            </div>
            <span className="text-xs font-medium text-slate-500 w-9 text-right">
              {(conf * 100).toFixed(0)}%
            </span>
          </div>

          {/* Transcription */}
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wide">Transcription</span>
            <p className="text-sm text-slate-700 bg-slate-50 rounded-lg p-2.5 mt-1 whitespace-pre-wrap ring-1 ring-inset ring-slate-100">
              {grade.extracted_text || <em className="text-slate-400">aucune</em>}
            </p>
          </div>

          {/* Expected */}
          <details className="group">
            <summary className="text-xs text-slate-400 uppercase tracking-wide cursor-pointer hover:text-slate-600 select-none">
              Réponse attendue
            </summary>
            <p className="text-sm text-slate-600 mt-1 pl-1">{rubric.expected_answer || "—"}</p>
          </details>

          {/* Justification */}
          <div>
            <span className="text-xs text-slate-400 uppercase tracking-wide">Justification</span>
            <textarea
              className="input mt-1 min-h-[3rem] text-sm"
              rows={2}
              value={just}
              onChange={(e) => setJust(e.target.value)}
            />
          </div>

          {/* Controls */}
          <div className="grid grid-cols-12 gap-2 items-end">
            <div className="col-span-7">
              <label className="label">Règle appliquée</label>
              <select
                className="input"
                value={polId ?? ""}
                onChange={(e) => {
                  const v = e.target.value ? Number(e.target.value) : null;
                  setPolId(v);
                  const p = policies.find((x) => x.id === v);
                  if (p) setPts(Number((rubric.points_max * p.fraction_points).toFixed(2)));
                }}
              >
                <option value="">—</option>
                {policies.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({(p.fraction_points * 100).toFixed(0)}%)
                  </option>
                ))}
              </select>
            </div>
            <div className="col-span-3">
              <label className="label">Note /{rubric.points_max}</label>
              <input
                type="number"
                step="0.25"
                min={0}
                max={rubric.points_max}
                className="input"
                value={pts}
                onWheel={(e) => e.currentTarget.blur()}
                onChange={(e) => setPts(Number(e.target.value))}
              />
            </div>
            <div className="col-span-2">
              <Button
                variant="primary"
                size="sm"
                icon={Check}
                className="w-full"
                onClick={() =>
                  onSave({ final_points: pts, applied_policy_id: polId ?? undefined, justification: just })
                }
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
