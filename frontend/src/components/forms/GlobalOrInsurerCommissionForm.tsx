"use client";

import { useActionState, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type CommissionConfigOut = components["schemas"]["CommissionConfigOut"];
type Action = (
  prevState: ActionState<CommissionConfigOut>,
  formData: FormData
) => Promise<ActionState<CommissionConfigOut>>;

export function GlobalOrInsurerCommissionForm({
  action,
  insurers,
}: {
  action: Action;
  insurers: { id: string; name: string }[];
}) {
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);
  const [scope, setScope] = useState<"global" | "insurance_company">("global");

  return (
    <form action={formAction} className="space-y-4">
      {state.status === "error" && <p className="text-sm text-fg-danger">{state.message}</p>}
      {state.status === "success" && (
        <p className="text-sm text-fg-success-strong">New rate is now effective.</p>
      )}

      <div>
        <label htmlFor="scope" className="mb-2 block text-sm font-medium text-heading">
          Scope
        </label>
        <select
          id="scope"
          name="scope"
          value={scope}
          onChange={(e) => setScope(e.target.value as typeof scope)}
          className="block w-full rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        >
          <option value="global">Global (platform default)</option>
          <option value="insurance_company">Specific insurer</option>
        </select>
      </div>

      {scope === "insurance_company" && (
        <div>
          <label
            htmlFor="insurance_company_id"
            className="mb-2 block text-sm font-medium text-heading"
          >
            Insurer
          </label>
          <select
            id="insurance_company_id"
            name="insurance_company_id"
            required
            className="block w-full rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          >
            {insurers.map((insurer) => (
              <option key={insurer.id} value={insurer.id}>
                {insurer.name}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <Input
          id="gtbank_rate_pct"
          name="gtbank_rate_pct"
          label="GTBank rate (%)"
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
          label="Insureflow rate (%)"
          type="number"
          step="0.01"
          min="0"
          max="100"
          required
          defaultValue="0.5"
          error={state.fieldErrors?.insureflow_rate_bps}
        />
      </div>

      <Button type="submit" disabled={pending}>
        {pending ? "Saving…" : "Set new rate"}
      </Button>
    </form>
  );
}
