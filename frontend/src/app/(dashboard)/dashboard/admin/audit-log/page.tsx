import { apiFetch } from "@/lib/api/client";
import { getAuthToken } from "@/lib/auth/session";
import { Badge } from "@/components/ui/Badge";
import { StateDiff } from "@/components/audit/StateDiff";
import { AUDIT_ACTIONS, AUDIT_ENTITY_TYPES } from "@/lib/audit-actions";
import type { components } from "@/lib/api/types";

type AuditLogOut = components["schemas"]["AuditLogOut"];

export default async function AuditLogPage({
  searchParams,
}: {
  searchParams: Promise<{
    action?: string;
    entity_type?: string;
    date_from?: string;
    date_to?: string;
  }>;
}) {
  const { action, entity_type: entityType, date_from: dateFrom, date_to: dateTo } =
    await searchParams;
  const token = await getAuthToken();
  const logs = await apiFetch<AuditLogOut[]>("/admin/audit-logs", {
    token,
    searchParams: { action, entity_type: entityType, date_from: dateFrom, date_to: dateTo },
  });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Audit Log</h1>
      <p className="mt-1 text-sm text-body">
        Every onboarding approval, commission change, and financial state transition &mdash;
        immutable, insert-only.
      </p>

      <form method="GET" className="mt-4 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="action" className="mb-1 block text-xs font-medium text-body">
            Action
          </label>
          <select
            id="action"
            name="action"
            defaultValue={action ?? ""}
            className="rounded-base border border-border-default-medium bg-neutral-secondary-medium px-2 py-1.5 text-sm text-heading focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          >
            <option value="">All actions</option>
            {AUDIT_ACTIONS.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="entity_type" className="mb-1 block text-xs font-medium text-body">
            Entity type
          </label>
          <select
            id="entity_type"
            name="entity_type"
            defaultValue={entityType ?? ""}
            className="rounded-base border border-border-default-medium bg-neutral-secondary-medium px-2 py-1.5 text-sm text-heading focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          >
            <option value="">All entities</option>
            {AUDIT_ENTITY_TYPES.map((e) => (
              <option key={e} value={e}>
                {e}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="date_from" className="mb-1 block text-xs font-medium text-body">
            From
          </label>
          <input
            id="date_from"
            name="date_from"
            type="date"
            defaultValue={dateFrom ?? ""}
            className="rounded-base border border-border-default-medium bg-neutral-secondary-medium px-2 py-1.5 text-sm text-heading focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
        <div>
          <label htmlFor="date_to" className="mb-1 block text-xs font-medium text-body">
            To
          </label>
          <input
            id="date_to"
            name="date_to"
            type="date"
            defaultValue={dateTo ?? ""}
            className="rounded-base border border-border-default-medium bg-neutral-secondary-medium px-2 py-1.5 text-sm text-heading focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
        <button
          type="submit"
          className="rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-1.5 text-sm font-medium text-heading hover:bg-neutral-tertiary-medium"
        >
          Filter
        </button>
        <a href="/dashboard/admin/audit-log" className="text-sm text-fg-brand hover:underline">
          Clear
        </a>
      </form>

      <div className="mt-6 space-y-3">
        {logs.length === 0 && <p className="text-sm text-body-subtle">No audit log entries found.</p>}
        {logs.map((log) => (
          <details
            key={log.id}
            className="rounded-base border border-border-default bg-neutral-primary-soft p-4 shadow-xs"
          >
            <summary className="flex cursor-pointer items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <Badge variant="neutral">{log.action}</Badge>
                <span className="text-sm text-body">
                  {log.entity_type} <span className="font-mono text-xs">{log.entity_id}</span>
                </span>
              </div>
              <div className="flex items-center gap-3 text-xs text-body-subtle">
                <span>{log.actor_role ?? "system"}</span>
                <span>{new Date(log.created_at).toLocaleString("en-NG")}</span>
              </div>
            </summary>
            <div className="mt-4 border-t border-border-default pt-4">
              <StateDiff before={log.before_state} after={log.after_state} />
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
