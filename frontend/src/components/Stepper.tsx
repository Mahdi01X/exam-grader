import { Check } from "lucide-react";

const STEPS = ["Barème", "Dépôt des copies", "Correction IA", "Revue & clôture"];

function stepForStatus(status: string): number {
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

export function Stepper({ status }: { status: string }) {
  const current = stepForStatus(status);
  return (
    <div className="flex items-center">
      {STEPS.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={label} className="flex items-center">
            <div className="flex items-center gap-2">
              <span
                className={`grid place-items-center w-7 h-7 rounded-full text-xs font-semibold transition-colors
                ${
                  done
                    ? "bg-brand-600 text-white"
                    : active
                      ? "bg-brand-50 text-brand-700 ring-2 ring-brand-500"
                      : "bg-slate-100 text-slate-400"
                }`}
              >
                {done ? <Check className="w-3.5 h-3.5" /> : i + 1}
              </span>
              <span
                className={`text-xs font-medium hidden sm:block ${
                  active ? "text-slate-900" : done ? "text-slate-600" : "text-slate-400"
                }`}
              >
                {label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
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
