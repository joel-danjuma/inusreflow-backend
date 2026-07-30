"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { useIdempotencyKey } from "@/lib/idempotency";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";

type Action = (
  prevState: ActionState<undefined>,
  formData: FormData
) => Promise<ActionState<undefined>>;

export function SinglePayButton({
  installmentId,
  action,
}: {
  installmentId: string;
  action: Action;
}) {
  const { key } = useIdempotencyKey(`single:${installmentId}`);
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  return (
    <form action={formAction} className="inline-flex items-center gap-2">
      <input type="hidden" name="idempotency_key" value={key} />
      <Button type="submit" variant="brand" size="xs" disabled={pending}>
        {pending ? "Starting…" : "Pay"}
      </Button>
      {state.status === "error" && (
        <span className="text-xs text-fg-danger">{state.message}</span>
      )}
    </form>
  );
}
