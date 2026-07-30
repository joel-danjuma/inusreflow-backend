import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken } from "@/lib/auth/session";
import { Alert } from "@/components/ui/Alert";
import { ANOMALY_ACTION } from "@/lib/audit-actions";
import type { components } from "@/lib/api/types";

type AuditLogOut = components["schemas"]["AuditLogOut"];

export default async function AnomaliesPage() {
  const token = await getAuthToken();
  const logs = await apiFetch<AuditLogOut[]>("/admin/audit-logs", {
    token,
    searchParams: { action: ANOMALY_ACTION },
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Anomalies</h1>
      <p className="mt-1 text-sm text-body">
        Bulk batches whose size or value is far above a broker&apos;s own trailing history.
        Informational only &mdash; these are never blocked, only flagged for review.
      </p>

      <div className="mt-6 space-y-3">
        {logs.length === 0 && (
          <p className="text-sm text-body-subtle">No anomalies flagged.</p>
        )}
        {logs.map((log) => {
          const after = (log.after_state ?? {}) as {
            reasons?: string[];
            item_count?: number;
            total_amount_kobo?: number;
          };
          return (
            <div key={log.id} className="rounded-base border border-border-default bg-neutral-primary-soft p-4 shadow-xs">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-heading">
                  Batch <Link href={`/dashboard/payments/bulk/${log.entity_id}`} className="font-mono text-xs text-fg-brand hover:underline">{log.entity_id}</Link>
                </p>
                <span className="text-xs text-body-subtle">
                  {new Date(log.created_at).toLocaleString("en-NG")}
                </span>
              </div>
              {after.reasons && after.reasons.length > 0 && (
                <ul className="mt-2 list-inside list-disc text-sm text-body">
                  {after.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
              {typeof after.item_count === "number" && (
                <p className="mt-2 text-xs text-body-subtle">
                  {after.item_count} items in this batch
                </p>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-6">
        <Alert variant="brand">
          Flags are non-blocking &mdash; every batch listed here still processed normally. This
          view exists for manual review only.
        </Alert>
      </div>
    </div>
  );
}
