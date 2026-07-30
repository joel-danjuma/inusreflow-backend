"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];
type Action = (
  prevState: ActionState<InsuranceCompanyOut>,
  formData: FormData
) => Promise<ActionState<InsuranceCompanyOut>>;

export function SettlementAccountForm({ action }: { action: Action }) {
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  return (
    <form action={formAction} className="space-y-4">
      {state.status === "error" && (
        <p className="text-sm text-fg-danger">{state.message}</p>
      )}
      {state.status === "success" && (
        <p className="text-sm text-fg-success-strong">
          Settlement account confirmed: {state.data?.settlement_account_name}
        </p>
      )}
      <div className="grid grid-cols-2 gap-4">
        <Input
          id="bank_code"
          name="bank_code"
          label="Bank NIP code"
          placeholder="e.g. 000013 for GTBank"
          required
          error={state.fieldErrors?.bank_code}
        />
        <Input
          id="account_number"
          name="account_number"
          label="Account number"
          required
          error={state.fieldErrors?.account_number}
        />
      </div>
      <Button type="submit" variant="secondary" size="sm" disabled={pending}>
        {pending ? "Verifying…" : "Confirm settlement account"}
      </Button>
    </form>
  );
}
