import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { OnboardingStatusBadge } from "@/components/badges/StatusBadge";
import { LogoutButton } from "@/components/layout/LogoutButton";
import type { OnboardingStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];
type BrokerOut = components["schemas"]["BrokerOut"];

export default async function PendingApprovalPage() {
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);

  const isInsurer = session!.role === "insurance_company_admin";
  const org = isInsurer
    ? await apiFetch<InsuranceCompanyOut>(`/insurance-companies/${session!.orgId}`, { token })
    : await apiFetch<BrokerOut>(`/brokers/${session!.orgId}`, { token });

  const isApproved = org.status === "approved";

  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-secondary-soft px-6 py-12">
      <div className="w-full max-w-sm rounded-base border border-border-default bg-neutral-primary-soft p-8 shadow-md">
        <h1 className="mb-1 text-xl font-semibold text-heading">
          {isApproved ? "You're approved" : "Awaiting approval"}
        </h1>
        <p className="mb-6 text-sm text-body">
          {isApproved
            ? `${org.name} has been approved by an Insureflow Admin. Sign out and back in to pick up full dashboard access.`
            : `${org.name} is not yet approved by an Insureflow Admin. This page will keep showing
               up until that happens and you sign in again.`}
        </p>

        <div className="mb-6 flex items-center justify-between rounded-base border border-border-default bg-neutral-secondary-soft px-4 py-3">
          <span className="text-sm text-body-subtle">Status</span>
          <OnboardingStatusBadge status={org.status as OnboardingStatus} />
        </div>

        {org.status === "rejected" && org.rejection_reason && (
          <div
            role="alert"
            className="mb-6 rounded-base border border-border-danger-subtle bg-danger-soft px-4 py-3 text-sm text-fg-danger-strong"
          >
            {org.rejection_reason}
          </div>
        )}

        <LogoutButton />
      </div>
    </main>
  );
}
