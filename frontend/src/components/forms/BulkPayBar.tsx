"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { Money } from "@/components/money/Money";
import { useIdempotencyKey } from "@/lib/idempotency";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";

export const BULK_PAY_FORM_ID = "bulk-pay-form";
/** Mirrors the backend's Settings.max_bulk_payment_items default -- the
 * server remains the real cap enforcement (a 422 past this), this is only
 * a client-side UX guard against building an obviously-doomed selection. */
export const MAX_BULK_ITEMS = 500;

type Action = (
  prevState: ActionState<undefined>,
  formData: FormData
) => Promise<ActionState<undefined>>;

function BulkPayFormInner({
  selectedIds,
  totalKobo,
  action,
}: {
  selectedIds: string[];
  totalKobo: number;
  action: Action;
}) {
  const scopeKey = `bulk:${[...selectedIds].sort().join(",")}`;
  const { key } = useIdempotencyKey(scopeKey);
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  return (
    <form
      id={BULK_PAY_FORM_ID}
      action={formAction}
      className="flex flex-wrap items-center justify-between gap-3 rounded-base border border-border-brand-subtle bg-brand-softer px-4 py-3"
    >
      <input type="hidden" name="idempotency_key" value={key} />
      <div className="text-sm text-fg-brand-strong">
        <strong>{selectedIds.length}</strong> selected
        {selectedIds.length > 0 && (
          <>
            {" "}
            &middot; <Money kobo={totalKobo} className="font-medium" />
          </>
        )}
        {state.status === "error" && (
          <span className="ml-3 text-fg-danger">{state.message}</span>
        )}
      </div>
      <Button type="submit" size="sm" disabled={pending || selectedIds.length === 0}>
        {pending ? "Starting…" : `Pay ${selectedIds.length || ""} selected`}
      </Button>
    </form>
  );
}

/** Remounted (via key) whenever the selection changes so the idempotency
 * key -- and the action's pending/error state -- are always scoped to the
 * current set of installments being paid, never a stale prior selection. */
export function BulkPayBar(props: { selectedIds: string[]; totalKobo: number; action: Action }) {
  return <BulkPayFormInner key={[...props.selectedIds].sort().join(",")} {...props} />;
}
