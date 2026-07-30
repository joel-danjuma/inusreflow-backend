import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken } from "@/lib/auth/session";
import { Money } from "@/components/money/Money";
import { PaymentStatusBadge } from "@/components/badges/StatusBadge";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import type { PaymentStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type PaymentOut = components["schemas"]["PaymentOut"];
type PaymentBatchOut = components["schemas"]["PaymentBatchOut"];

const FILTERS: { label: string; value: PaymentStatus | undefined }[] = [
  { label: "All", value: undefined },
  { label: "In progress", value: "initiated" },
  { label: "Success", value: "success" },
  { label: "Mismatch", value: "mismatch" },
  { label: "Expired", value: "expired" },
  { label: "Failed", value: "failed" },
];

export default async function PaymentsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string }>;
}) {
  const { status } = await searchParams;
  const token = await getAuthToken();
  const [payments, batches] = await Promise.all([
    apiFetch<PaymentOut[]>("/payments", { token, searchParams: { status } }),
    apiFetch<PaymentBatchOut[]>("/payments/bulk", { token, searchParams: { status } }),
  ]);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Payments</h1>
      <p className="mt-1 text-sm text-body">
        Every premium collected &mdash; singly or in bulk &mdash; scoped to what you&apos;re
        permitted to see.
      </p>

      <div className="mt-4 flex gap-2">
        {FILTERS.map((filter) => (
          <Link
            key={filter.label}
            href={filter.value ? `/dashboard/payments?status=${filter.value}` : "/dashboard/payments"}
            className={`rounded-default border px-3 py-1.5 text-sm font-medium transition-colors ${
              status === filter.value
                ? "border-border-brand bg-brand-softer text-fg-brand-strong"
                : "border-border-default text-body hover:bg-neutral-secondary-medium"
            }`}
          >
            {filter.label}
          </Link>
        ))}
      </div>

      <div className="mt-10">
        <h2 className="mb-3 text-base font-medium text-heading">Single payments</h2>
        <Table>
          <TableHead>
            <TableHeaderCell>Amount</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            <TableHeaderCell>Virtual account</TableHeaderCell>
            <TableHeaderCell>Created</TableHeaderCell>
          </TableHead>
          <TableBody>
            {payments.length === 0 && (
              <tr>
                <td colSpan={4}>
                  <EmptyState>No single payments yet.</EmptyState>
                </td>
              </tr>
            )}
            {payments.map((payment) => (
              <TableRow key={payment.id}>
                <TableCell header>
                  <Link
                    href={`/dashboard/payments/${payment.id}`}
                    className="text-fg-brand hover:underline"
                  >
                    <Money kobo={payment.amount_kobo} />
                  </Link>
                </TableCell>
                <TableCell>
                  <PaymentStatusBadge status={payment.status as PaymentStatus} />
                </TableCell>
                <TableCell>
                  <span className="font-mono text-xs">
                    {payment.squad_virtual_account_number ?? "—"}
                  </span>
                </TableCell>
                <TableCell>{new Date(payment.created_at).toLocaleString("en-NG")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="mt-10">
        <h2 className="mb-3 text-base font-medium text-heading">Bulk batches</h2>
        <Table>
          <TableHead>
            <TableHeaderCell>Total</TableHeaderCell>
            <TableHeaderCell>Items</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            <TableHeaderCell>Created</TableHeaderCell>
          </TableHead>
          <TableBody>
            {batches.length === 0 && (
              <tr>
                <td colSpan={4}>
                  <EmptyState>No bulk batches yet.</EmptyState>
                </td>
              </tr>
            )}
            {batches.map((batch) => (
              <TableRow key={batch.id}>
                <TableCell header>
                  <Link
                    href={`/dashboard/payments/bulk/${batch.id}`}
                    className="text-fg-brand hover:underline"
                  >
                    <Money kobo={batch.total_amount_kobo} />
                  </Link>
                </TableCell>
                <TableCell>{batch.item_count}</TableCell>
                <TableCell>
                  <PaymentStatusBadge status={batch.status as PaymentStatus} />
                </TableCell>
                <TableCell>{new Date(batch.created_at).toLocaleString("en-NG")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
