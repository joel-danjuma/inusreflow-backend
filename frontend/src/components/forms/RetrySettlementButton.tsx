"use client";

import { useActionState } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Button } from "@/components/ui/Button";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type SettlementPayoutOut = components["schemas"]["SettlementPayoutOut"];
type Action = (
  prevState: ActionState<SettlementPayoutOut>,
  formData: FormData
) => Promise<ActionState<SettlementPayoutOut>>;

export function RetrySettlementButton({ action }: { action: Action }) {
  const router = useRouter();
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  useEffect(() => {
    if (state.status === "success" && state.data) {
      router.push(`/dashboard/settlements/${state.data.id}`);
    }
  }, [state, router]);

  return (
    <form action={formAction} className="flex items-center gap-2">
      <Button type="submit" variant="secondary" size="sm" disabled={pending}>
        {pending ? "Retrying…" : "Retry settlement"}
      </Button>
      {state.status === "error" && <span className="text-sm text-fg-danger">{state.message}</span>}
    </form>
  );
}
