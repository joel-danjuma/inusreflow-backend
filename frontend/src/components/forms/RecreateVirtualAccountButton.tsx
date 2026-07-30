"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type VirtualAccountOut = components["schemas"]["VirtualAccountOut"];
type Action = (
  prevState: ActionState<VirtualAccountOut>,
  formData: FormData
) => Promise<ActionState<VirtualAccountOut>>;

export function RecreateVirtualAccountButton({ action }: { action: Action }) {
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  return (
    <form action={formAction} className="flex items-center gap-2">
      <Button type="submit" variant="tertiary" size="xs" disabled={pending}>
        {pending ? "Working…" : "Create / recreate"}
      </Button>
      {state.status === "error" && <span className="text-xs text-fg-danger">{state.message}</span>}
      {state.status === "success" && (
        <span className="text-xs text-fg-success-strong">Done</span>
      )}
    </form>
  );
}
