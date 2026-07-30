"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type BrokerInsurerAssignmentOut = components["schemas"]["BrokerInsurerAssignmentOut"];
type Action = (
  prevState: ActionState<BrokerInsurerAssignmentOut>,
  formData: FormData
) => Promise<ActionState<BrokerInsurerAssignmentOut>>;

export function UnassignInsurerButton({ action }: { action: Action }) {
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  return (
    <form action={formAction} className="flex items-center gap-2">
      <Button type="submit" variant="tertiary" size="xs" disabled={pending}>
        {pending ? "Removing…" : "Unassign"}
      </Button>
      {state.status === "error" && <span className="text-xs text-fg-danger">{state.message}</span>}
    </form>
  );
}
