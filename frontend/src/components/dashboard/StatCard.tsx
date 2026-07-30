import type { ReactNode } from "react";

export type StatAccent = "teal" | "green" | "yellow" | "orange" | "pink";

const ACCENT_CLASSES: Record<StatAccent, string> = {
  teal: "bg-accent-teal/15 text-accent-teal",
  green: "bg-accent-green/15 text-accent-green",
  yellow: "bg-accent-yellow/15 text-accent-yellow",
  orange: "bg-accent-orange/15 text-accent-orange",
  pink: "bg-accent-pink/15 text-accent-pink",
};

export function StatCard({
  label,
  value,
  hint,
  icon,
  accent = "teal",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  accent?: StatAccent;
}) {
  return (
    <div className="rounded-base border border-border-default bg-neutral-primary-soft p-5 shadow-xs">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold text-body">{label}</p>
        {icon && (
          <span
            className={`inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${ACCENT_CLASSES[accent]}`}
          >
            {icon}
          </span>
        )}
      </div>
      <p className="font-display mt-3.5 text-[32px] leading-[38px] font-semibold text-heading tabular-nums">
        {value}
      </p>
      {hint && <p className="mt-1 text-xs text-body-subtle">{hint}</p>}
    </div>
  );
}
