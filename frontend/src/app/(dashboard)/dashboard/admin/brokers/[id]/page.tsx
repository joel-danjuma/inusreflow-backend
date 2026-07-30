import { apiFetch } from "@/lib/api/client";
import { getAuthToken } from "@/lib/auth/session";
import { OnboardingStatusBadge } from "@/components/badges/StatusBadge";
import { AssignInsurerForm } from "@/components/forms/AssignInsurerForm";
import { UnassignInsurerButton } from "@/components/forms/UnassignInsurerButton";
import type { OnboardingStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";
import { assignBrokerToInsurer, unassignBrokerFromInsurer } from "../actions";

type BrokerOut = components["schemas"]["BrokerOut"];
type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];

export default async function AdminBrokerDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const token = await getAuthToken();
  const [broker, assignedInsurers, allInsurers] = await Promise.all([
    apiFetch<BrokerOut>(`/brokers/${id}`, { token }),
    apiFetch<InsuranceCompanyOut[]>(`/brokers/${id}/insurers`, { token }),
    apiFetch<InsuranceCompanyOut[]>("/admin/insurance-companies", { token }),
  ]);

  const assignedIds = new Set(assignedInsurers.map((i) => i.id));
  const unassignedApprovedInsurers = allInsurers
    .filter((i) => i.status === "approved" && !assignedIds.has(i.id))
    .map((i) => ({ id: i.id, name: i.name }));

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-heading">{broker.name}</h1>
        <p className="mt-1 text-sm text-body">{broker.contact_email}</p>
      </div>

      <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-body-subtle">Status</dt>
            <dd className="mt-1">
              <OnboardingStatusBadge status={broker.status as OnboardingStatus} />
            </dd>
          </div>
          {broker.rejection_reason && (
            <div>
              <dt className="text-body-subtle">Rejection reason</dt>
              <dd className="mt-1 text-heading">{broker.rejection_reason}</dd>
            </div>
          )}
          <div>
            <dt className="text-body-subtle">Virtual account number</dt>
            <dd className="mt-1 font-mono text-heading">{broker.squad_va_number ?? "Not provisioned"}</dd>
          </div>
          <div>
            <dt className="text-body-subtle">Virtual account bank</dt>
            <dd className="mt-1 text-heading">{broker.squad_va_bank ?? "Not provisioned"}</dd>
          </div>
        </dl>
      </div>

      {broker.status === "approved" && (
        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <h2 className="mb-1 text-base font-medium text-heading">Insurer assignments</h2>
          <p className="mb-4 text-sm text-body">
            A broker can work with several insurers at once &mdash; assign or remove as many as
            needed, this never affects any of their other active assignments.
          </p>

          {assignedInsurers.length === 0 ? (
            <p className="mb-4 text-sm text-body-subtle">Not assigned to any insurer yet.</p>
          ) : (
            <ul className="mb-4 divide-y divide-border-default">
              {assignedInsurers.map((insurer) => (
                <li key={insurer.id} className="flex items-center justify-between gap-3 py-2.5">
                  <span className="text-sm text-heading">{insurer.name}</span>
                  <UnassignInsurerButton
                    action={unassignBrokerFromInsurer.bind(null, broker.id, insurer.id)}
                  />
                </li>
              ))}
            </ul>
          )}

          <AssignInsurerForm
            action={assignBrokerToInsurer.bind(null, broker.id)}
            insurers={unassignedApprovedInsurers}
          />
        </div>
      )}
    </div>
  );
}
