import type { ReactNode } from "react";

/** Mirrors the design system's PageHeader helper (ui_kits/insureflow-app/AppShell.jsx):
 * big Sora title, muted subtitle, right-aligned actions. */
export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-heading">
          {title}
        </h1>
        {subtitle && <p className="mt-1.5 text-sm text-body">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}
