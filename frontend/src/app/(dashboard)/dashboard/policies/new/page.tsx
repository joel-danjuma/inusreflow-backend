import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { CreatePolicyForm } from "@/components/forms/CreatePolicyForm";
import type { components } from "@/lib/api/types";

type PolicyholderOut = components["schemas"]["PolicyholderOut"];
type BrokerOut = components["schemas"]["BrokerOut"];

export default async function NewPolicyPage({
  searchParams,
}: {
  searchParams: Promise<{ policyholder_id?: string }>;
}) {
  const { policyholder_id: policyholderId } = await searchParams;
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);

  const [brokers, policyholders] = await Promise.all([
    apiFetch<BrokerOut[]>(`/insurance-companies/${session!.orgId}/brokers`, { token }),
    policyholderId ? Promise.resolve([]) : apiFetch<PolicyholderOut[]>("/users", { token }),
  ]);

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-semibold text-heading">New policy</h1>
      <p className="mt-1 text-sm text-body">Capture policy, coverage, and tagging details.</p>

      <div className="mt-6 rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
        <CreatePolicyForm
          brokers={brokers.map((b) => ({ id: b.id, name: b.name }))}
          policyholders={policyholders}
          fixedPolicyholderId={policyholderId}
        />
      </div>
    </div>
  );
}
