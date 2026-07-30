import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { CreatePolicyholderForm } from "@/components/forms/CreatePolicyholderForm";
import type { components } from "@/lib/api/types";

type BrokerOut = components["schemas"]["BrokerOut"];

export default async function NewPolicyholderPage() {
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  const brokers = await apiFetch<BrokerOut[]>(`/insurance-companies/${session!.orgId}/brokers`, {
    token,
  });

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-2xl font-semibold text-heading">New policyholder</h1>
      <p className="mt-1 text-sm text-body">
        A data record, not a login &mdash; policyholders never sign in to Insureflow themselves.
      </p>

      <div className="mt-6 rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
        <CreatePolicyholderForm
          brokers={brokers.map((b) => ({ id: b.id, name: b.name }))}
        />
      </div>
    </div>
  );
}
