import type { ReactNode } from "react";
import type { BadgeVariant } from "@/lib/enums";

const VARIANT_CLASSES: Record<BadgeVariant, string> = {
  brand: "bg-brand-softer border-border-brand-subtle text-fg-brand-strong",
  neutral: "bg-neutral-primary-soft border-border-default text-heading",
  gray: "bg-neutral-secondary-medium border-border-default text-heading",
  danger: "bg-danger-soft border-border-danger-subtle text-fg-danger-strong",
  success: "bg-success-soft border-border-success-subtle text-fg-success-strong",
  warning: "bg-warning-soft border-border-warning-subtle text-fg-warning",
  info: "bg-info-soft border-transparent text-info-strong",
  processing: "bg-processing-soft border-transparent text-processing-strong",
  dark: "bg-dark border-transparent text-white",
};

export function Badge({
  variant = "neutral",
  children,
}: {
  variant?: BadgeVariant;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-default border px-1.5 py-0.5 text-xs font-medium ${VARIANT_CLASSES[variant]}`}
    >
      {children}
    </span>
  );
}
