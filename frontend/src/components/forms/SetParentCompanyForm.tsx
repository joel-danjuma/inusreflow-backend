"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/Button";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];
type Action = (
  prevState: ActionState<InsuranceCompanyOut>,
  formData: FormData
) => Promise<ActionState<InsuranceCompanyOut>>;

export function SetParentCompanyForm({
  action,
  currentParentId,
  candidateParents,
}: {
  action: Action;
  currentParentId: string | null;
  candidateParents: { id: string; name: string }[];
}) {
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);

  return (
    <form action={formAction} className="space-y-4">
      {state.status === "error" && <p className="text-sm text-fg-danger">{state.message}</p>}
      {state.status === "success" && (
        <p className="text-sm text-fg-success-strong">
          {state.data?.parent_company_id ? "Parent company updated." : "Now a top-level company."}
        </p>
      )}
      <div>
        <label htmlFor="parent_company_id" className="mb-2 block text-sm font-medium text-heading">
          Parent company
        </label>
        <select
          id="parent_company_id"
          name="parent_company_id"
          defaultValue={currentParentId ?? ""}
          className="block w-full rounded-base border border-border-default-medium bg-neutral-secondary-medium px-3 py-2.5 text-sm text-heading shadow-xs focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        >
          <option value="">Top-level company (no parent)</option>
          {candidateParents.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>
      <Button type="submit" variant="tertiary" size="sm" disabled={pending}>
        {pending ? "Saving…" : "Save"}
      </Button>
    </form>
  );
}
