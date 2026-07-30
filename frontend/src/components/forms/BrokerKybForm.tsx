"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type VirtualAccountOut = components["schemas"]["VirtualAccountOut"];
type Action = (
  prevState: ActionState<VirtualAccountOut>,
  formData: FormData
) => Promise<ActionState<VirtualAccountOut>>;

export function BrokerKybForm({ action }: { action: Action }) {
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  return (
    <form action={formAction} className="space-y-4">
      {state.status === "error" && <p className="text-sm text-fg-danger">{state.message}</p>}
      {state.status === "success" && (
        <p className="text-sm text-fg-success-strong">
          Virtual account provisioned: {state.data?.squad_va_number} ({state.data?.squad_va_bank})
        </p>
      )}
      <div className="grid grid-cols-2 gap-4">
        <Input
          id="bvn"
          name="bvn"
          label="BVN (11 digits)"
          pattern="[0-9]{11}"
          required
          error={state.fieldErrors?.bvn}
        />
        <Input
          id="phone_number"
          name="phone_number"
          label="Phone number"
          type="tel"
          required
          error={state.fieldErrors?.phone_number}
        />
      </div>
      <Button type="submit" variant="secondary" size="sm" disabled={pending}>
        {pending ? "Provisioning…" : "Save & provision account"}
      </Button>
    </form>
  );
}
