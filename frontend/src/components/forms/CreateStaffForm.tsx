"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { CopyableToken } from "@/components/ui/CopyableToken";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type OtpResult = components["schemas"]["OtpResult"];
type Action = (
  prevState: ActionState<OtpResult>,
  formData: FormData
) => Promise<ActionState<OtpResult>>;

export function CreateStaffForm({ action }: { action: Action }) {
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  return (
    <div className="space-y-4">
      {state.status === "success" && state.data && (
        <div className="space-y-2 rounded-base border border-border-success-subtle bg-success-soft p-4">
          <p className="text-sm font-medium text-fg-success-strong">
            Staff account created &mdash; one-time password (shown once):
          </p>
          <CopyableToken token={state.data.otp} />
        </div>
      )}
      {state.status === "error" && (
        <p className="text-sm text-fg-danger">{state.message}</p>
      )}

      <form action={formAction} className="flex items-end gap-3">
        <div className="flex-1">
          <Input
            id="email"
            name="email"
            label="Staff email"
            type="email"
            required
            error={state.fieldErrors?.email}
          />
        </div>
        <Button type="submit" disabled={pending}>
          {pending ? "Creating…" : "Create staff account"}
        </Button>
      </form>
    </div>
  );
}
