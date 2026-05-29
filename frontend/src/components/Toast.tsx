import { createContext, useCallback, useContext, useState, ReactNode } from "react";
import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";

type ToastKind = "success" | "error" | "info";
type Toast = { id: number; kind: ToastKind; message: string };

type ToastCtx = {
  notify: (message: string, kind?: ToastKind) => void;
};

const Ctx = createContext<ToastCtx>({ notify: () => {} });

const kindMeta: Record<
  ToastKind,
  { icon: typeof Info; ring: string; iconColor: string }
> = {
  success: { icon: CheckCircle2, ring: "ring-emerald-200", iconColor: "text-emerald-500" },
  error: { icon: AlertTriangle, ring: "ring-rose-200", iconColor: "text-rose-500" },
  info: { icon: Info, ring: "ring-brand-200", iconColor: "text-brand-500" },
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: number) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const notify = useCallback(
    (message: string, kind: ToastKind = "success") => {
      const id = Date.now() + Math.random();
      setToasts((t) => [...t, { id, kind, message }]);
      setTimeout(() => dismiss(id), 4000);
    },
    [dismiss],
  );

  return (
    <Ctx.Provider value={{ notify }}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 w-80">
        {toasts.map((t) => {
          const meta = kindMeta[t.kind];
          const Icon = meta.icon;
          return (
            <div
              key={t.id}
              className={`animate-toast-in flex items-start gap-3 bg-white border border-slate-200 rounded-xl shadow-pop ring-1 ${meta.ring} p-3.5`}
            >
              <Icon className={`w-5 h-5 shrink-0 ${meta.iconColor}`} />
              <p className="text-sm text-slate-700 flex-1 leading-snug">{t.message}</p>
              <button
                onClick={() => dismiss(t.id)}
                className="text-slate-300 hover:text-slate-500 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </Ctx.Provider>
  );
}

export const useToast = () => useContext(Ctx);
