import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { Money } from "@/components/money/Money";
import { PaymentStatusBadge } from "@/components/badges/StatusBadge";
import { PaymentStatusPoller } from "@/components/forms/PaymentStatusPoller";
import { Alert } from "@/components/ui/Alert";
import { roleHasPermission } from "@/lib/auth/rbac";
import type { PaymentStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type PaymentOut = components["schemas"]["PaymentOut"];

export default async function PaymentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  const payment = await apiFetch<PaymentOut>(`/payments/${id}`, { token });
  const canViewLedger = roleHasPermission(session!.role, "view_ledger");

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-heading">
          <Money kobo={payment.amount_kobo} />
        </h1>
        <div className="mt-2 flex items-center gap-3">
          <PaymentStatusBadge status={payment.status as PaymentStatus} />
          <PaymentStatusPoller statusUrl={`/api/payments/${payment.id}/status`} initialStatus={payment.status} />
        </div>
      </div>

      {payment.status === "initiated" && payment.squad_virtual_account_number && (
        <div className="rounded-base border border-border-brand-subtle bg-brand-softer p-6">
          <p className="text-sm font-medium text-fg-brand-strong">
            Transfer the exact amount above to this account
          </p>
          <p className="mt-1 text-xs text-fg-brand-strong">
            This is your team&apos;s permanent collection account &mdash; we match inbound
            transfers to this installment by account number and exact amount, so any mismatch in
            the amount sent will not be matched automatically.
          </p>
          <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-body-subtle">Account number</dt>
              <dd className="mt-1 font-mono text-lg text-heading">
                {payment.squad_virtual_account_number}
              </dd>
            </div>
            <div>
              <dt className="text-body-subtle">Bank</dt>
              <dd className="mt-1 text-lg text-heading">{payment.squad_virtual_account_bank}</dd>
            </div>
          </dl>
        </div>
      )}

      {payment.status === "success" && (
        <Alert variant="success" title="Payment received">
          This installment has been marked paid and the insurer&apos;s settlement has been
          triggered.
          {canViewLedger && (
            <div className="mt-2">
              <Link
                href={`/dashboard/ledger?reference_type=payment&reference_id=${payment.id}`}
                className="font-medium underline"
              >
                View ledger postings
              </Link>
            </div>
          )}
        </Alert>
      )}

      {(payment.status === "mismatch" || payment.status === "expired") && (
        <Alert variant="warning" title="Auto-refunded by Squad">
          {payment.status === "mismatch"
            ? "The amount transferred didn't match this installment exactly, so Squad automatically refunded the sender."
            : "This attempt expired before a matching transfer arrived, so Squad automatically refunded the sender."}{" "}
          Start a new payment to try again.
        </Alert>
      )}

      {payment.status === "failed" && (
        <Alert variant="danger" title="Payment failed">
          {payment.failure_reason ?? "This payment could not be completed."}
        </Alert>
      )}
    </div>
  );
}
