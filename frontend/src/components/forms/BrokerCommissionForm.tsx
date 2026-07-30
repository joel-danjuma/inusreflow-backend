"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type CommissionConfigOut = components["schemas"]["CommissionConfigOut"];
type Action = (
  prevState: ActionState<CommissionConfigOut>,
  formData: FormData
) => Promise<ActionState<CommissionConfigOut>>;

export function BrokerCommissionForm({
  action,
  brokers,
}: {
  action: Action;
  brokers: { id: string; name: string }[];
}) {
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  if (brokers.length === 0) {
    return <p className="text-sm text-body-subtle">No brokers assigned to your insurer yet.</p>;
  }

  return (
    <form action={formAction} className="space-y-4">
      {state.status === "error" && <p className="text-sm text-fg-danger">{state.message}</p>}
      {state.status === "success" && (
        <p className="text-sm text-fg-success-strong">New rate is now effective.</p>
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
          {brokers.map((broker) => (
            <option key={broker.id} value={broker.id}>
              {broker.name}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <Input
          id="gtbank_rate_pct"
          name="gtbank_rate_pct"
          label="GTBank (%)"
          type="number"
          step="0.01"
          min="0"
          max="100"
          required
          defaultValue="0.5"
          error={state.fieldErrors?.gtbank_rate_bps}
        />
        <Input
          id="insureflow_rate_pct"
          name="insureflow_rate_pct"
          label="Insureflow (%)"
          type="number"
          step="0.01"
          min="0"
          max="100"
          required
          defaultValue="0.5"
          error={state.fieldErrors?.insureflow_rate_bps}
        />
        <Input
          id="broker_rate_pct"
          name="broker_rate_pct"
          label="Broker (%)"
          type="number"
          step="0.01"
          min="0"
          max="100"
          required
          error={state.fieldErrors?.broker_rate_bps}
        />
      </div>

      <Button type="submit" disabled={pending}>
        {pending ? "Saving…" : "Set new rate"}
      </Button>
    </form>
  );
}
