"use client";

import { useActionState, useState } from "react";
import { Button } from "@/components/ui/Button";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type InstallmentOut = components["schemas"]["InstallmentOut"];
type SetReferenceAction = (
  installmentId: string,
  prevState: ActionState<InstallmentOut>,
  formData: FormData
) => Promise<ActionState<InstallmentOut>>;

export function InlineReferenceNumberEditor({
  installmentId,
  referenceNumber,
  action,
}: {
  installmentId: string;
  referenceNumber: string | null;
  action: SetReferenceAction;
}) {
  const [editing, setEditing] = useState(false);
  const [state, formAction, pending] = useActionState(
    action.bind(null, installmentId),
    IDLE_STATE as ActionState<InstallmentOut>
  );

  const currentValue = state.status === "success" ? (state.data?.reference_number ?? null) : referenceNumber;

  if (!editing) {
    return (
      <button
        type="button"
        onClick={() => setEditing(true)}
        className="text-left text-sm text-body hover:text-fg-brand hover:underline"
      >
        {currentValue ?? <span className="text-body-subtle">Add reference…</span>}
      </button>
    );
  }

  return (
    <form
      action={async (formData) => {
        await formAction(formData);
        setEditing(false);
      }}
      className="flex items-center gap-1.5"
    >
      <input
        type="text"
        name="reference_number"
        defaultValue={currentValue ?? ""}
        autoFocus
        maxLength={255}
        placeholder="Debit note / reference"
        className="w-36 rounded-sm border border-border-default-medium bg-neutral-secondary-medium px-2 py-1 text-xs text-heading focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
      />
      <Button type="submit" variant="tertiary" size="xs" disabled={pending}>
        {pending ? "…" : "Save"}
      </Button>
      <button
        type="button"
        onClick={() => setEditing(false)}
        className="text-xs text-body hover:text-fg-danger"
      >
        Cancel
      </button>
      {state.status === "error" && (
        <span className="text-xs text-fg-danger">{state.message}</span>
      )}
    </form>
  );
}
