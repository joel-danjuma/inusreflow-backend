"use client";

import { Alert } from "@/components/ui/Alert";

/** Defense-in-depth backstop: proxy.ts and the sidebar hide pages a role
 * shouldn't see, but the FastAPI call itself is the real gate. A stale
 * cookie or a direct URL hit that slips past those still lands here when
 * apiFetch throws on a non-2xx response. */
export default function DashboardError({ error }: { error: Error & { status?: number } }) {
  const isForbidden = error.message.includes("permission");

  return (
    <div className="mx-auto max-w-2xl">
      <Alert variant={isForbidden ? "warning" : "danger"} title={isForbidden ? "Access denied" : "Something went wrong"}>
        {error.message || "An unexpected error occurred."}
      </Alert>
    </div>
  );
}
