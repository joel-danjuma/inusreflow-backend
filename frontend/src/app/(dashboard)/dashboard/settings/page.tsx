import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { ROLE_LABELS } from "@/lib/auth/rbac";
import { OnboardingStatusBadge } from "@/components/badges/StatusBadge";
import { MaskedField } from "@/components/pii/MaskedField";
import { SettlementAccountForm } from "@/components/forms/SettlementAccountForm";
import { setSettlementAccount } from "@/app/(dashboard)/dashboard/admin/insurers/actions";
import type { OnboardingStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];
type BrokerOut = components["schemas"]["BrokerOut"];

export default async function SettingsPage() {
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);

  if (session!.role === "insurance_company_admin") {
    const company = await apiFetch<InsuranceCompanyOut>(`/insurance-companies/${session!.orgId}`, {
      token,
    });

    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-heading">Settings</h1>
          <p className="mt-1 text-sm text-body">Your organization&apos;s account details.</p>
        </div>

        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-body-subtle">Organization</dt>
              <dd className="mt-1 text-heading">{company.name}</dd>
            </div>
            <div>
              <dt className="text-body-subtle">Role</dt>
              <dd className="mt-1 text-heading">{ROLE_LABELS[session!.role]}</dd>
            </div>
            <div>
              <dt className="text-body-subtle">Contact email</dt>
              <dd className="mt-1 text-heading">{company.contact_email}</dd>
            </div>
            <div>
              <dt className="text-body-subtle">Status</dt>
              <dd className="mt-1">
                <OnboardingStatusBadge status={company.status as OnboardingStatus} />
              </dd>
            </div>
          </dl>
        </div>

        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <h2 className="mb-1 text-base font-medium text-heading">Settlement account</h2>
          <p className="mb-4 text-sm text-body">
            Required before any payout can settle to your organization. Verified live against
            Squad.
          </p>
          <dl className="mb-4 grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-body-subtle">Bank</dt>
              <dd className="mt-1 text-heading">{company.settlement_bank_code ?? "Not set"}</dd>
            </div>
            <div>
              <dt className="text-body-subtle">Account number</dt>
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
                <dt className="text-body-subtle">Account name</dt>
                <dd className="mt-1 text-heading">{company.settlement_account_name}</dd>
              </div>
            )}
          </dl>
          <SettlementAccountForm action={setSettlementAccount.bind(null, company.id)} />
        </div>
      </div>
    );
  }

  const broker = await apiFetch<BrokerOut>(`/brokers/${session!.orgId}`, { token });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-heading">Settings</h1>
        <p className="mt-1 text-sm text-body">Your organization&apos;s account details.</p>
      </div>

      <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-body-subtle">Organization</dt>
            <dd className="mt-1 text-heading">{broker.name}</dd>
          </div>
          <div>
            <dt className="text-body-subtle">Role</dt>
            <dd className="mt-1 text-heading">{ROLE_LABELS[session!.role]}</dd>
          </div>
          <div>
            <dt className="text-body-subtle">Contact email</dt>
            <dd className="mt-1 text-heading">{broker.contact_email}</dd>
          </div>
          <div>
            <dt className="text-body-subtle">Status</dt>
            <dd className="mt-1">
              <OnboardingStatusBadge status={broker.status as OnboardingStatus} />
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
