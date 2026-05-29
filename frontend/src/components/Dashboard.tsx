import { useEffect, useState } from "react";
import { Users, Gauge, SplitSquareVertical, AlertTriangle, BarChart3 } from "lucide-react";
import { LucideIcon } from "lucide-react";
import { api } from "../lib/api";
import { Card } from "./ui";

type Dash = {
  total_max: number;
  copies_count: number;
  pending_review_count: number;
  average: number;
  median: number;
  distribution: number[];
};

export default function Dashboard({ examId }: { examId: number }) {
  const [d, setD] = useState<Dash | null>(null);

  useEffect(() => {
    api.get(`/api/exams/${examId}/export/dashboard`).then(setD).catch(() => setD(null));
  }, [examId]);

  if (!d || d.copies_count === 0) return null;
  const max = Math.max(1, ...d.distribution);

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-4 h-4 text-brand-600" />
        <h2 className="section-title">Vue d'ensemble</h2>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        <Metric icon={Users} label="Copies" value={String(d.copies_count)} />
        <Metric
          icon={Gauge}
          label="Moyenne"
          value={d.average.toFixed(2)}
          sub={`/ ${d.total_max.toFixed(2)}`}
        />
        <Metric
          icon={SplitSquareVertical}
          label="Médiane"
          value={d.median.toFixed(2)}
          sub={`/ ${d.total_max.toFixed(2)}`}
        />
        <Metric
          icon={AlertTriangle}
          label="À réviser"
          value={String(d.pending_review_count)}
          tone={d.pending_review_count > 0 ? "warn" : "ok"}
        />
      </div>

      <div>
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">
          Distribution des notes
        </span>
        <div className="flex items-end gap-1.5 h-28 mt-3">
          {d.distribution.map((n, i) => (
            <div key={i} className="flex-1 flex flex-col items-center justify-end gap-1 group">
              <span className="text-[10px] text-slate-400 opacity-0 group-hover:opacity-100 transition">
                {n}
              </span>
              <div
                className="w-full rounded-t bg-gradient-to-t from-brand-500 to-brand-400 hover:from-brand-600 hover:to-brand-500 transition-colors min-h-[2px]"
                style={{ height: `${(n / max) * 100}%` }}
                title={`${i * 10}–${(i + 1) * 10}% : ${n} copie(s)`}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between text-[10px] text-slate-400 mt-1.5">
          <span>0%</span>
          <span>25%</span>
          <span>50%</span>
          <span>75%</span>
          <span>100%</span>
        </div>
      </div>
    </Card>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  sub,
  tone = "neutral",
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  sub?: string;
  tone?: "neutral" | "warn" | "ok";
}) {
  const valueColor =
    tone === "warn" ? "text-amber-600" : tone === "ok" ? "text-emerald-600" : "text-slate-900";
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/40 p-4">
      <div className="flex items-center gap-1.5 text-slate-400 mb-2">
        <Icon className="w-3.5 h-3.5" />
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className={`text-2xl font-semibold tracking-tight ${valueColor}`}>
          {value}
        </span>
        {sub && <span className="text-sm text-slate-400">{sub}</span>}
      </div>
    </div>
  );
}
