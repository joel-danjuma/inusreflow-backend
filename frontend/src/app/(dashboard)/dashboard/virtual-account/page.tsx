import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { Alert } from "@/components/ui/Alert";
import { BrokerKybForm } from "@/components/forms/BrokerKybForm";
import { roleHasPermission } from "@/lib/auth/rbac";
import { updateOwnBrokerKyb } from "./actions";
import type { components } from "@/lib/api/types";

type VirtualAccountOut = components["schemas"]["VirtualAccountOut"];

export default async function OwnVirtualAccountPage() {
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  const account = await apiFetch<VirtualAccountOut>("/virtual-accounts/me", { token });
  const canManage = roleHasPermission(session!.role, "manage_own_broker");

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-semibold text-heading">My Virtual Account</h1>
      <p className="mt-1 text-sm text-body">
        Every premium your team collects &mdash; single or bulk &mdash; is paid into this same
        account, matched to the correct installment by the exact amount transferred.
      </p>

      {!account.squad_va_number ? (
        <div className="mt-6">
          <Alert variant="warning">
            {canManage
              ? "No virtual account has been provisioned yet. Enter your BVN and phone number below to set one up."
              : "No virtual account has been provisioned yet. Contact your broker admin."}
          </Alert>
        </div>
      ) : (
        <div className="mt-6 rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-body-subtle">Account number</dt>
              <dd className="mt-1 font-mono text-lg text-heading">{account.squad_va_number}</dd>
            </div>
            <div>
              <dt className="text-body-subtle">Bank</dt>
              <dd className="mt-1 text-lg text-heading">{account.squad_va_bank}</dd>
            </div>
          </dl>
        </div>
      )}

      {canManage && (
        <div className="mt-6 rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <h2 className="mb-1 text-base font-medium text-heading">
            {account.squad_va_number ? "Update KYB details" : "Provision your virtual account"}
          </h2>
          <p className="mb-4 text-sm text-body">
            Re-entering these will recreate your virtual account with Squad using the new details.
          </p>
          <BrokerKybForm action={updateOwnBrokerKyb} />
        </div>
      )}
    </div>
  );
}
