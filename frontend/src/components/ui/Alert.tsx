import type { ReactNode } from "react";

type AlertVariant = "brand" | "success" | "danger" | "warning";

const VARIANT_CLASSES: Record<AlertVariant, string> = {
  brand: "bg-brand-softer border-border-brand-subtle text-fg-brand-strong",
  success: "bg-success-soft border-border-success-subtle text-fg-success-strong",
  danger: "bg-danger-soft border-border-danger-subtle text-fg-danger-strong",
  warning: "bg-warning-soft border-border-warning-subtle text-fg-warning",
};

export function Alert({
  variant = "brand",
  title,
  children,
}: {
  variant?: AlertVariant;
  title?: string;
  children: ReactNode;
}) {
  return (
    <div role="alert" className={`rounded-base border p-4 ${VARIANT_CLASSES[variant]}`}>
      {title && <p className="text-sm font-medium">{title}</p>}
      <div className="text-sm leading-relaxed">{children}</div>
    </div>
  );
}
