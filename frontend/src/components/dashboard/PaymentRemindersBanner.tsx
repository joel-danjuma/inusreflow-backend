"use client";

import { useState } from "react";

/** Dismissal is per tab session and re-appears once the overdue count itself
 * changes (e.g. more installments lapse into overdue) -- keyed on the count
 * rather than a fixed id, so a stale dismissal never hides a worse backlog. */
function storageKey(overdueCount: number): string {
  return `dismissed:payment-reminders:${overdueCount}`;
}

export function PaymentRemindersBanner({ overdueCount }: { overdueCount: number }) {
  // Lazy initializer (not useEffect+setState) so the sessionStorage read
  // never triggers a second render -- mirrors lib/idempotency.ts's pattern.
  const [dismissed, setDismissed] = useState(() => {
    if (overdueCount === 0 || typeof window === "undefined") return overdueCount === 0;
    return window.sessionStorage.getItem(storageKey(overdueCount)) === "1";
  });

  if (overdueCount === 0 || dismissed) return null;

  return (
    <div role="alert" className="flex items-center gap-4 rounded-base bg-dark px-5 py-4.5">
      <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/10 text-accent-yellow">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          <path
            d="M13.73 21a2 2 0 0 1-3.46 0"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-white">
          {overdueCount} overdue {overdueCount === 1 ? "installment needs" : "installments need"}{" "}
          attention
        </p>
        <p className="mt-0.5 text-sm text-white/70">
          {overdueCount === 1 ? "A premium payment is" : "Premium payments are"} past due for one
          or more of your clients &mdash; collect them from Installments before they lapse
          further.
        </p>
      </div>
      <button
        type="button"
        aria-label="Dismiss"
        onClick={() => {
          window.sessionStorage.setItem(storageKey(overdueCount), "1");
          setDismissed(true);
        }}
        className="shrink-0 rounded-full p-1.5 text-white/60 hover:bg-white/10 hover:text-white"
      >
        <svg width="18" height="18" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path
            d="M4 4L12 12M12 4L4 12"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </button>
    </div>
  );
}
