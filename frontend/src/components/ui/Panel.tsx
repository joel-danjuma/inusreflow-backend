import type { ReactNode } from "react";

/** The canonical white content panel: hairline border, optional header row
 * with a title + right-aligned action. Mirrors the design system's Panel
 * helper (ui_kits/insureflow-app/AppShell.jsx). */
export function Panel({
  title,
  action,
  children,
  pad = true,
}: {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  pad?: boolean;
}) {
  return (
    <section className="overflow-hidden rounded-base border border-border-default bg-neutral-primary-soft">
      {(title || action) && (
        <header className="flex items-center justify-between gap-3 border-b border-border-default px-5 py-4">
          {title && <h2 className="font-display text-base font-semibold text-heading">{title}</h2>}
          {action}
        </header>
      )}
      <div className={pad ? "p-5" : ""}>{children}</div>
    </section>
  );
}
