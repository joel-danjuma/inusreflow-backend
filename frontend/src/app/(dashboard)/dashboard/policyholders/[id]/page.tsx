import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken } from "@/lib/auth/session";
import { MaskedField } from "@/components/pii/MaskedField";
import { Money } from "@/components/money/Money";
import { PolicyStatusBadge } from "@/components/badges/StatusBadge";
import { Button } from "@/components/ui/Button";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import { PREMIUM_FREQUENCY_LABELS, type PolicyStatus, type PremiumFrequency } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type PolicyholderOut = components["schemas"]["PolicyholderOut"];
type PolicyOut = components["schemas"]["PolicyOut"];

export default async function PolicyholderDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const token = await getAuthToken();
  const [policyholder, policies] = await Promise.all([
    apiFetch<PolicyholderOut>(`/users/${id}`, { token }),
    apiFetch<PolicyOut[]>("/policies", { token, searchParams: { user_id: id } }),
  ]);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-heading">{policyholder.full_name}</h1>
          <p className="mt-1 text-sm text-body">
            {policyholder.email ?? "No email"} &middot; {policyholder.phone_number ?? "No phone"}
          </p>
        </div>
        <Link href={`/dashboard/policies/new?policyholder_id=${policyholder.id}`}>
          <Button size="sm">New policy</Button>
        </Link>
      </div>

      {policyholder.identification_number && (
        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-4 shadow-xs">
          <p className="text-sm text-body-subtle">Identification number</p>
          <div className="mt-1">
            <MaskedField value={policyholder.identification_number} label="identification number" />
          </div>
        </div>
      )}

      <div>
        <h2 className="mb-3 text-base font-medium text-heading">Policies</h2>
        <Table>
          <TableHead>
            <TableHeaderCell>Type</TableHeaderCell>
            <TableHeaderCell>Premium</TableHeaderCell>
            <TableHeaderCell>Frequency</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableHead>
          <TableBody>
            {policies.length === 0 && (
              <tr>
                <td colSpan={4}>
                  <EmptyState>No policies yet.</EmptyState>
                </td>
              </tr>
            )}
            {policies.map((policy) => (
              <TableRow key={policy.id}>
                <TableCell header>
                  <Link
                    href={`/dashboard/policies/${policy.id}`}
                    className="text-fg-brand hover:underline"
                  >
                    {policy.policy_type}
                  </Link>
                </TableCell>
                <TableCell>
                  <Money kobo={policy.premium_amount_kobo} />
                </TableCell>
                <TableCell>
                  {PREMIUM_FREQUENCY_LABELS[policy.premium_frequency as PremiumFrequency]}
                </TableCell>
                <TableCell>
                  <PolicyStatusBadge status={policy.status as PolicyStatus} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
