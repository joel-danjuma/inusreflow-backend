import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { Money } from "@/components/money/Money";
import { SettlementPayoutStatusBadge } from "@/components/badges/StatusBadge";
import { RetrySettlementButton } from "@/components/forms/RetrySettlementButton";
import { Alert } from "@/components/ui/Alert";
import { roleHasPermission } from "@/lib/auth/rbac";
import type { SettlementPayoutStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";
import { retrySettlement } from "../actions";

type SettlementPayoutOut = components["schemas"]["SettlementPayoutOut"];

const MAX_CHAIN_DEPTH = 10;

async function loadChain(
  id: string,
  token: string | null
): Promise<SettlementPayoutOut[]> {
  const chain: SettlementPayoutOut[] = [];
  let currentId: string | null = id;
  for (let i = 0; i < MAX_CHAIN_DEPTH && currentId; i++) {
    const payout: SettlementPayoutOut = await apiFetch<SettlementPayoutOut>(
      `/settlements/${currentId}`,
      { token }
    );
    chain.push(payout);
    currentId = payout.previous_attempt_id;
  }
  return chain;
}

export default async function SettlementDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  const chain = await loadChain(id, token);
  const payout = chain[0];
  const canRetry = roleHasPermission(session!.role, "retry_settlement_payout");

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-heading">
            <Money kobo={payout.amount_kobo} />
          </h1>
          <p className="mt-1 text-sm text-body capitalize">
            {payout.source_type.replace("_", " ")} payout &middot; attempt #{payout.attempt_number}
          </p>
        </div>
        <SettlementPayoutStatusBadge status={payout.status as SettlementPayoutStatus} />
      </div>

      {payout.status === "failed" && (
        <div className="flex items-center justify-between rounded-base border border-border-danger-subtle bg-danger-soft p-4">
          <div>
            <p className="text-sm font-medium text-fg-danger-strong">
              {payout.failure_reason ?? "This payout attempt failed."}
            </p>
            <p className="mt-1 text-xs text-fg-danger-strong">
              A retry always mints a fresh transfer reference &mdash; this attempt is never
              resubmitted.
            </p>
          </div>
          {canRetry && <RetrySettlementButton action={retrySettlement.bind(null, payout.id)} />}
        </div>
      )}

      {payout.status === "pending" && (
        <Alert variant="brand">
          Squad hasn&apos;t returned a definitive result for this transfer yet &mdash; it&apos;s
          re-queried automatically until it resolves.
        </Alert>
      )}

      {payout.status === "success" && (
        <Alert variant="success">This payout was confirmed successful by Squad.</Alert>
      )}

      <div className="rounded-base border border-border-default bg-neutral-primary-soft p-4 shadow-xs">
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-body-subtle">Squad transfer ref</dt>
            <dd className="mt-1 font-mono text-xs text-heading">{payout.squad_transfer_ref}</dd>
          </div>
          <div>
            <dt className="text-body-subtle">Created</dt>
            <dd className="mt-1 text-heading">
              {new Date(payout.created_at).toLocaleString("en-NG")}
            </dd>
          </div>
        </dl>
      </div>

      {chain.length > 1 && (
        <div>
          <h2 className="mb-3 text-base font-medium text-heading">Attempt history</h2>
          <ol className="space-y-3">
            {chain.map((attempt, index) => (
              <li
                key={attempt.id}
                className="flex items-center justify-between rounded-base border border-border-default bg-neutral-primary-soft p-4"
              >
                <div>
                  <p className="text-sm font-medium text-heading">
                    Attempt #{attempt.attempt_number}
                    {index === 0 && (
                      <span className="ml-2 text-xs font-normal text-body-subtle">(current)</span>
                    )}
                  </p>
                  <p className="mt-1 font-mono text-xs text-body">{attempt.squad_transfer_ref}</p>
                </div>
                <SettlementPayoutStatusBadge status={attempt.status as SettlementPayoutStatus} />
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
