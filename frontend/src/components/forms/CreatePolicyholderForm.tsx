"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import { createPolicyholder } from "@/app/(dashboard)/dashboard/policyholders/actions";
import type { components } from "@/lib/api/types";

type PolicyholderOut = components["schemas"]["PolicyholderOut"];

export function CreatePolicyholderForm({
  brokers,
}: {
  brokers: { id: string; name: string }[];
}) {
  const [state, formAction, pending] = useActionState(
    createPolicyholder,
    IDLE_STATE as ActionState<PolicyholderOut>
  );

  return (
    <form action={formAction} className="space-y-5">
      {state.status === "error" && (
        <p className="text-sm text-fg-danger">{state.message}</p>
      )}

      <div>
        <label htmlFor="broker_id" className="mb-2 block text-sm font-medium text-heading">
          Broker
        </label>
        <select
          id="broker_id"
          name="broker_id"
          required
          className="block w-full rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        >
          <option value="">Select a broker…</option>
          {brokers.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
      </div>

      <Input id="full_name" name="full_name" label="Full name" required error={state.fieldErrors?.full_name} />
      <Input id="email" name="email" label="Email" type="email" error={state.fieldErrors?.email} />
      <Input id="phone_number" name="phone_number" label="Phone number" type="tel" error={state.fieldErrors?.phone_number} />
      <Input
        id="identification_number"
        name="identification_number"
        label="Identification number (optional)"
        error={state.fieldErrors?.identification_number}
      />

      <Button type="submit" disabled={pending} className="w-full">
        {pending ? "Creating…" : "Create policyholder"}
      </Button>
    </form>
  );
}
