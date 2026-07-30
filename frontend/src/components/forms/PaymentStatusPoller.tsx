"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

/** Polls a same-origin Route Handler (never FastAPI directly -- no CORS,
 * JWT stays server-side) every `intervalMs` while status is "initiated".
 * Once it resolves to a terminal state, triggers one router.refresh() so
 * the surrounding Server Component re-fetches the full, final record. */
export function PaymentStatusPoller({
  statusUrl,
  initialStatus,
  intervalMs = 3000,
}: {
  statusUrl: string;
  initialStatus: string;
  intervalMs?: number;
}) {
  const router = useRouter();
  const [status, setStatus] = useState(initialStatus);

  useEffect(() => {
    if (initialStatus !== "initiated") return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      if (cancelled) return;
      try {
        const response = await fetch(statusUrl, { cache: "no-store" });
        if (response.ok) {
          const data = (await response.json()) as { status?: string };
          if (data.status && data.status !== "initiated") {
            if (!cancelled) {
              setStatus(data.status);
              router.refresh();
            }
            return;
          }
        }
      } catch {
        // transient network error -- just retry on the next tick
      }
      if (!cancelled) timer = setTimeout(poll, intervalMs);
    }

    timer = setTimeout(poll, intervalMs);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [statusUrl, initialStatus, intervalMs, router]);

  if (status !== "initiated") return null;

  return (
    <div className="flex items-center gap-2 text-sm text-body">
      <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-brand" aria-hidden />
      Waiting for payment confirmation&hellip;
    </div>
  );
}
