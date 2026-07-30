import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { InstallmentsWorkspace } from "@/components/forms/InstallmentsWorkspace";
import { roleHasPermission } from "@/lib/auth/rbac";
import {
  createSinglePayment,
  createBulkPayment,
  resolveBulkPaymentFile,
} from "@/app/(dashboard)/dashboard/payments/actions";
import { setInstallmentReferenceNumber } from "@/app/(dashboard)/dashboard/installments/actions";
import { CURATED_POLICY_TYPES, POLICY_TYPE_LABELS } from "@/lib/policyTypes";
import type { InstallmentStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type InstallmentOut = components["schemas"]["InstallmentOut"];

const FILTERS: { label: string; value: InstallmentStatus | undefined }[] = [
  { label: "All", value: undefined },
  { label: "Due", value: "due" },
  { label: "Overdue", value: "overdue" },
  { label: "Paid", value: "paid" },
  { label: "Cancelled", value: "cancelled" },
];

const POLICY_TYPE_FILTERS: { label: string; value: string | undefined }[] = [
  { label: "All types", value: undefined },
  ...CURATED_POLICY_TYPES.map((t) => ({ label: POLICY_TYPE_LABELS[t], value: t as string })),
];

function filterHref(status: string | undefined, policyType: string | undefined): string {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (policyType) params.set("policy_type", policyType);
  const qs = params.toString();
  return qs ? `/dashboard/installments?${qs}` : "/dashboard/installments";
}

export default async function InstallmentsPage({
  searchParams,
}: {
  searchParams: Promise<{ status?: string; policy_type?: string }>;
}) {
  const { status, policy_type: policyType } = await searchParams;
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  const installments = await apiFetch<InstallmentOut[]>("/installments", {
    token,
    searchParams: { status, policy_type: policyType },
  });
  const canPay = roleHasPermission(session!.role, "create_payment");
  const canManageReference = roleHasPermission(session!.role, "manage_installment_reference");

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Installments</h1>
      <p className="mt-1 text-sm text-body">
        Every premium installment across your team&apos;s policies. Nothing here is charged
        automatically &mdash; select one or more due/overdue installments below to collect them.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        {FILTERS.map((filter) => (
          <Link
            key={filter.label}
            href={filterHref(filter.value, policyType)}
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

      <div className="mt-2 flex flex-wrap gap-2">
        {POLICY_TYPE_FILTERS.map((filter) => (
          <Link
            key={filter.label}
            href={filterHref(status, filter.value)}
            className={`rounded-default border px-3 py-1.5 text-sm font-medium transition-colors ${
              policyType === filter.value
                ? "border-border-brand bg-brand-softer text-fg-brand-strong"
                : "border-border-default text-body hover:bg-neutral-secondary-medium"
            }`}
          >
            {filter.label}
          </Link>
        ))}
      </div>

      <div className="mt-6">
        <InstallmentsWorkspace
          installments={installments}
          canPay={canPay}
          createSinglePayment={createSinglePayment}
          createBulkPayment={createBulkPayment}
          canManageReference={canManageReference}
          setInstallmentReferenceNumber={setInstallmentReferenceNumber}
          resolveBulkPaymentFile={resolveBulkPaymentFile}
        />
      </div>
    </div>
  );
}
