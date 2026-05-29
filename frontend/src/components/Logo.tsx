import { GraduationCap } from "lucide-react";

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <span className="grid place-items-center w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm ring-1 ring-brand-700/20">
        <GraduationCap className="w-5 h-5" />
      </span>
      {!compact && (
        <span className="font-semibold text-slate-900 tracking-tight text-[15px]">
          Exam<span className="text-brand-600">Grader</span>
        </span>
      )}
    </span>
  );
}
