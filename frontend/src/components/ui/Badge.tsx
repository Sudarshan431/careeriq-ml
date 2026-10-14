import type { HTMLAttributes } from "react";

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

const toneClasses: Record<Tone, string> = {
  success: "bg-green-50 text-green-700 ring-1 ring-inset ring-green-200",
  warning: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  danger: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-200",
  info: "bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200",
  neutral: "bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ tone = "neutral", className = "", children, ...rest }: BadgeProps) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${toneClasses[tone]} ${className}`} {...rest}>
      {children}
    </span>
  );
}
