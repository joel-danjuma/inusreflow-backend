import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { Money } from "@/components/money/Money";
import { PaymentStatusBadge } from "@/components/badges/StatusBadge";
import { PaymentStatusPoller } from "@/components/forms/PaymentStatusPoller";
import { Alert } from "@/components/ui/Alert";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
} from "@/components/ui/Table";
import { roleHasPermission } from "@/lib/auth/rbac";
import type { PaymentStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type PaymentBatchOut = components["schemas"]["PaymentBatchOut"];

export default async function PaymentBatchDetailPage({
  params,
}: {
  params: Promise<{ batchId: string }>;
}) {
  const { batchId } = await params;
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  const batch = await apiFetch<PaymentBatchOut>(`/payments/bulk/${batchId}`, { token });
  const canViewLedger = roleHasPermission(session!.role, "view_ledger");

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-heading">
          <Money kobo={batch.total_amount_kobo} /> &middot; {batch.item_count} installments
        </h1>
        <div className="mt-2 flex items-center gap-3">
          <PaymentStatusBadge status={batch.status as PaymentStatus} />
          <PaymentStatusPoller
            statusUrl={`/api/payments/bulk/${batch.id}/status`}
            initialStatus={batch.status}
          />
        </div>
      </div>

      {batch.status === "initiated" && batch.squad_virtual_account_number && (
        <div className="rounded-base border border-border-brand-subtle bg-brand-softer p-6">
          <p className="text-sm font-medium text-fg-brand-strong">
            Transfer the exact total above to this account
          </p>
          <p className="mt-1 text-xs text-fg-brand-strong">
            One transfer settles the whole batch &mdash; it must match this exact total, sent to
            your team&apos;s permanent collection account below.
          </p>
          <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-body-subtle">Account number</dt>
              <dd className="mt-1 font-mono text-lg text-heading">
                {batch.squad_virtual_account_number}
              </dd>
            </div>
            <div>
              <dt className="text-body-subtle">Bank</dt>
              <dd className="mt-1 text-lg text-heading">{batch.squad_virtual_account_bank}</dd>
            </div>
          </dl>
        </div>
      )}

      {batch.status === "success" && (
        <Alert variant="success" title="Batch received">
          Every installment in this batch has been marked paid and the insurer&apos;s settlement
          has been triggered as one payout.
        </Alert>
      )}

      {(batch.status === "mismatch" || batch.status === "expired") && (
        <Alert variant="warning" title="Auto-refunded by Squad">
          {batch.status === "mismatch"
            ? "The amount transferred didn't match this batch's total exactly, so Squad automatically refunded the sender."
            : "This attempt expired before a matching transfer arrived, so Squad automatically refunded the sender."}{" "}
          None of the installments in this batch were marked paid. Start a new batch to try again.
        </Alert>
      )}

      {batch.status === "failed" && (
        <Alert variant="danger" title="Batch failed">
          {batch.failure_reason ?? "This batch could not be completed."}
        </Alert>
      )}

      <div>
        <h2 className="mb-3 text-base font-medium text-heading">Items</h2>
        <Table>
          <TableHead>
            <TableHeaderCell>Installment</TableHeaderCell>
            <TableHeaderCell>Amount</TableHeaderCell>
            {canViewLedger && batch.status === "success" && (
              <TableHeaderCell>{""}</TableHeaderCell>
            )}
          </TableHead>
          <TableBody>
            {batch.items.map((item) => (
              <TableRow key={item.id}>
                <TableCell header>
                  <span className="font-mono text-xs">{item.installment_id}</span>
                </TableCell>
                <TableCell>
                  <Money kobo={item.amount_kobo} />
                </TableCell>
                {canViewLedger && batch.status === "success" && (
                  <TableCell>
                    <Link
                      href={`/dashboard/ledger?reference_type=payment_batch_item&reference_id=${item.id}`}
                      className="text-fg-brand hover:underline"
                    >
                      View ledger
                    </Link>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
