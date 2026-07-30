import { apiFetch } from "@/lib/api/client";
import { getAuthToken } from "@/lib/auth/session";
import { Money } from "@/components/money/Money";
import { PolicyStatusBadge, InstallmentStatusBadge } from "@/components/badges/StatusBadge";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import { PREMIUM_FREQUENCY_LABELS, type InstallmentStatus, type PolicyStatus, type PremiumFrequency } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type PolicyOut = components["schemas"]["PolicyOut"];
type InstallmentOut = components["schemas"]["InstallmentOut"];

export default async function PolicyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const token = await getAuthToken();
  const [policy, installments] = await Promise.all([
    apiFetch<PolicyOut>(`/policies/${id}`, { token }),
    apiFetch<InstallmentOut[]>(`/policies/${id}/installments`, { token }),
  ]);

  const hasCoverageDetails =
    policy.coverage_amount_kobo != null || policy.coverage_items || policy.beneficiaries;
  const hasTags = policy.broker_notes || policy.internal_tags;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-heading">
          {policy.policy_name || policy.policy_type}
        </h1>
        <p className="mt-1 text-sm text-body">
          {policy.policy_name && <>{policy.policy_type} &middot; </>}
          <Money kobo={policy.premium_amount_kobo} className="font-medium text-heading" />{" "}
          {PREMIUM_FREQUENCY_LABELS[policy.premium_frequency as PremiumFrequency].toLowerCase()},
          starting {new Date(policy.start_date).toLocaleDateString("en-NG")}
          {policy.duration_months != null && <> for {policy.duration_months} months</>}
        </p>
      </div>

      <div className="rounded-base border border-border-default bg-neutral-primary-soft p-4 shadow-xs">
        <span className="text-sm text-body-subtle">Status</span>{" "}
        <PolicyStatusBadge status={policy.status as PolicyStatus} />
      </div>

      {hasCoverageDetails && (
        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <h2 className="mb-3 text-base font-medium text-heading">Coverage details</h2>
          <dl className="space-y-4 text-sm">
            {policy.coverage_amount_kobo != null && (
              <div>
                <dt className="text-body-subtle">Coverage amount</dt>
                <dd className="mt-1 text-heading">
                  <Money kobo={policy.coverage_amount_kobo} />
                </dd>
              </div>
            )}
            {policy.coverage_items && (
              <div>
                <dt className="text-body-subtle">Coverage items / risk type</dt>
                <dd className="mt-1 whitespace-pre-wrap text-heading">{policy.coverage_items}</dd>
              </div>
            )}
            {policy.beneficiaries && (
              <div>
                <dt className="text-body-subtle">Beneficiaries</dt>
                <dd className="mt-1 whitespace-pre-wrap text-heading">{policy.beneficiaries}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {hasTags && (
        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <h2 className="mb-3 text-base font-medium text-heading">Tags & broker visibility</h2>
          <dl className="space-y-4 text-sm">
            {policy.broker_notes && (
              <div>
                <dt className="text-body-subtle">Broker notes</dt>
                <dd className="mt-1 whitespace-pre-wrap text-heading">{policy.broker_notes}</dd>
              </div>
            )}
            {policy.internal_tags && (
              <div>
                <dt className="text-body-subtle">Internal tags</dt>
                <dd className="mt-1 flex flex-wrap gap-2 text-heading">
                  {policy.internal_tags.split(",").map((tag) => tag.trim()).filter(Boolean).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-default bg-neutral-secondary-medium px-2 py-1 text-xs font-medium"
                    >
                      {tag}
                    </span>
                  ))}
                </dd>
              </div>
            )}
          </dl>
        </div>
      )}

      <div>
        <h2 className="mb-3 text-base font-medium text-heading">Installment schedule</h2>
        <Table>
          <TableHead>
            <TableHeaderCell>Due date</TableHeaderCell>
            <TableHeaderCell>Amount</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableHead>
          <TableBody>
            {installments.length === 0 && (
              <tr>
                <td colSpan={3}>
                  <EmptyState>No installments generated yet.</EmptyState>
                </td>
              </tr>
            )}
            {installments.map((installment) => (
              <TableRow key={installment.id}>
                <TableCell header>
                  {new Date(installment.due_date).toLocaleDateString("en-NG")}
                </TableCell>
                <TableCell>
                  <Money kobo={installment.amount_kobo} />
                </TableCell>
                <TableCell>
                  <InstallmentStatusBadge status={installment.status as InstallmentStatus} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
