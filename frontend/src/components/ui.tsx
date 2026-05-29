import { ButtonHTMLAttributes, ReactNode, forwardRef } from "react";
import { LucideIcon, Loader2 } from "lucide-react";

/* ---------------- Button ---------------- */
type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "md" | "sm";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  icon?: LucideIcon;
  loading?: boolean;
}

const variantClass: Record<Variant, string> = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  ghost: "btn-ghost",
  danger: "btn-danger",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { variant = "secondary", size = "md", icon: Icon, loading, children, className = "", disabled, ...rest },
    ref,
  ) => {
    const iconSize = size === "sm" ? "w-3.5 h-3.5" : "w-4 h-4";
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`${variantClass[variant]} ${size === "sm" ? "btn-sm" : ""} ${className}`}
        {...rest}
      >
        {loading ? (
          <Loader2 className={`${iconSize} animate-spin`} />
        ) : Icon ? (
          <Icon className={iconSize} />
        ) : null}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";

/* ---------------- Badge ---------------- */
export type Tone = "neutral" | "brand" | "ok" | "warn" | "danger";

const toneClass: Record<Tone, string> = {
  neutral: "badge-neutral",
  brand: "badge-brand",
  ok: "badge-ok",
  warn: "badge-warn",
  danger: "badge-danger",
};

export function Badge({
  tone = "neutral",
  icon: Icon,
  children,
}: {
  tone?: Tone;
  icon?: LucideIcon;
  children: ReactNode;
}) {
  return (
    <span className={toneClass[tone]}>
      {Icon && <Icon className="w-3 h-3" />}
      {children}
    </span>
  );
}

/* ---------------- Card ---------------- */
export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`card ${className}`}>{children}</div>;
}

/* ---------------- Spinner ---------------- */
export function Spinner({ className = "w-5 h-5" }: { className?: string }) {
  return <Loader2 className={`${className} animate-spin text-brand-500`} />;
}

/* ---------------- EmptyState ---------------- */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-6">
      <div className="grid place-items-center w-12 h-12 rounded-xl bg-slate-100 text-slate-400 mb-3">
        <Icon className="w-6 h-6" />
      </div>
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {description && (
        <p className="text-sm text-slate-400 mt-1 max-w-sm">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

/* ---------------- Field ---------------- */
export function Field({
  label,
  hint,
  children,
}: {
  label?: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div>
      {label && <label className="label">{label}</label>}
      {children}
      {hint && <p className="hint">{hint}</p>}
    </div>
  );
}
