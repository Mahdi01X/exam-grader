import { Check } from "lucide-react";

export const STEP_LABELS = ["Barème", "Dépôt des copies", "Correction IA", "Revue & clôture"];

export function stepForStatus(status: string): number {
  switch (status) {
    case "draft":
    case "rubric_pending":
      return 0;
    case "rubric_ready":
      return 1;
    case "grading":
      return 2;
    case "closed":
      return 3;
    default:
      return 0;
  }
}

/**
 * Fil d'Ariane des 4 étapes.
 * - `status` : déduit l'étape « atteinte » (pastilles cochées) depuis le statut.
 * - `current` : étape actuellement affichée (surligne la pastille active).
 * - `onStepClick` : rend les pastilles cliquables (navigation du wizard).
 */
export function Stepper({
  status,
  current,
  onStepClick,
}: {
  status: string;
  current?: number;
  onStepClick?: (i: number) => void;
}) {
  const reached = stepForStatus(status);
  const active = current ?? reached;
  const clickable = !!onStepClick;
  return (
    <div className="flex items-center">
      {STEP_LABELS.map((label, i) => {
        const done = i < active;
        const isActive = i === active;
        const inner = (
          <div className="flex items-center gap-2">
            <span
              className={`grid place-items-center w-7 h-7 rounded-full text-xs font-semibold transition-colors
              ${
                done
                  ? "bg-brand-600 text-white"
                  : isActive
                    ? "bg-brand-50 text-brand-700 ring-2 ring-brand-500"
                    : "bg-slate-100 text-slate-400"
              }`}
            >
              {done ? <Check className="w-3.5 h-3.5" /> : i + 1}
            </span>
            <span
              className={`text-xs font-medium hidden sm:block ${
                isActive ? "text-slate-900" : done ? "text-slate-600" : "text-slate-400"
              }`}
            >
              {label}
            </span>
          </div>
        );
        return (
          <div key={label} className="flex items-center">
            {clickable ? (
              <button
                type="button"
                onClick={() => onStepClick?.(i)}
                className="rounded-lg px-1 py-1 -mx-1 hover:bg-slate-50 transition focus:outline-none focus:ring-2 focus:ring-brand-200"
                title={`Aller à : ${label}`}
              >
                {inner}
              </button>
            ) : (
              inner
            )}
            {i < STEP_LABELS.length - 1 && (
              <div
                className={`w-6 sm:w-10 h-px mx-2 ${done ? "bg-brand-300" : "bg-slate-200"}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
