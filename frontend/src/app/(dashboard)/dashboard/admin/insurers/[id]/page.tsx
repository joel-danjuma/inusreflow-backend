import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { OnboardingStatusBadge } from "@/components/badges/StatusBadge";
import { MaskedField } from "@/components/pii/MaskedField";
import { SettlementAccountForm } from "@/components/forms/SettlementAccountForm";
import { SetParentCompanyForm } from "@/components/forms/SetParentCompanyForm";
import { Alert } from "@/components/ui/Alert";
import type { OnboardingStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";
import { setSettlementAccount, setInsurerParent } from "../actions";

type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];

export default async function AdminInsurerDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  const company = await apiFetch<InsuranceCompanyOut>(`/insurance-companies/${id}`, { token });

  const canManageSettlement =
    session?.role === "insurance_company_admin" && session.orgId === company.id;
  const isInsureflowAdmin = session?.role === "insureflow_admin";

  let parentName: string | null = null;
  let children: InsuranceCompanyOut[] = [];
  let candidateParents: { id: string; name: string }[] = [];
  if (isInsureflowAdmin) {
    const allCompanies = await apiFetch<InsuranceCompanyOut[]>("/admin/insurance-companies", {
      token,
    });
    if (company.parent_company_id) {
      parentName = allCompanies.find((c) => c.id === company.parent_company_id)?.name ?? null;
    }
    children = allCompanies.filter((c) => c.parent_company_id === company.id);
    // A company can't become its own parent, its own child's parent, or a
    // subsidiary of another subsidiary (max depth 1, enforced server-side).
    candidateParents = allCompanies
      .filter((c) => c.id !== company.id && !c.parent_company_id)
      .map((c) => ({ id: c.id, name: c.name }));
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-heading">{company.name}</h1>
        <p className="mt-1 text-sm text-body">{company.contact_email}</p>
      </div>

      <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-body-subtle">Status</dt>
            <dd className="mt-1">
              <OnboardingStatusBadge status={company.status as OnboardingStatus} />
            </dd>
          </div>
          {company.rejection_reason && (
            <div>
              <dt className="text-body-subtle">Rejection reason</dt>
              <dd className="mt-1 text-heading">{company.rejection_reason}</dd>
            </div>
          )}
          <div>
            <dt className="text-body-subtle">Settlement bank</dt>
            <dd className="mt-1 text-heading">{company.settlement_bank_code ?? "Not set"}</dd>
          </div>
          <div>
            <dt className="text-body-subtle">Settlement account</dt>
            <dd className="mt-1 text-heading">
              {company.settlement_account_number ? (
                <MaskedField
                  value={company.settlement_account_number}
                  label="settlement account number"
                />
              ) : (
                "Not set"
              )}
            </dd>
          </div>
          {company.settlement_account_name && (
            <div className="col-span-2">
              <dt className="text-body-subtle">Settlement account name</dt>
              <dd className="mt-1 text-heading">{company.settlement_account_name}</dd>
            </div>
          )}
        </dl>
      </div>

      {isInsureflowAdmin && (
        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <h2 className="mb-1 text-base font-medium text-heading">Corporate structure</h2>
          <p className="mb-4 text-sm text-body">
            Organizational grouping only &mdash; each company remains a fully independent tenant
            regardless of parent/subsidiary labeling.
          </p>
          <dl className="mb-4 grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-body-subtle">Parent</dt>
              <dd className="mt-1 text-heading">{parentName ?? "Top-level company"}</dd>
            </div>
            <div>
              <dt className="text-body-subtle">Subsidiaries</dt>
              <dd className="mt-1 text-heading">
                {children.length === 0
                  ? "None"
                  : children.map((child) => child.name).join(", ")}
              </dd>
            </div>
          </dl>
          {children.length === 0 && (
            <SetParentCompanyForm
              action={setInsurerParent.bind(null, company.id)}
              currentParentId={company.parent_company_id}
              candidateParents={candidateParents}
            />
          )}
        </div>
      )}

      {canManageSettlement && (
        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <h2 className="mb-1 text-base font-medium text-heading">Settlement account</h2>
          <p className="mb-4 text-sm text-body">
            Required before any payout can settle to this insurer. Verified live against Squad.
          </p>
          <SettlementAccountForm action={setSettlementAccount.bind(null, company.id)} />
        </div>
      )}

      {company.status === "approved" && !company.settlement_account_number && !canManageSettlement && (
        <Alert variant="warning" title="No settlement account">
          This insurer has not confirmed a settlement account yet &mdash; payouts cannot settle
          until they do.
        </Alert>
      )}
    </div>
  );
}
