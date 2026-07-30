"use client";

import { useActionState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/Button";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type BrokerInsurerAssignmentOut = components["schemas"]["BrokerInsurerAssignmentOut"];
type Action = (
  prevState: ActionState<BrokerInsurerAssignmentOut>,
  formData: FormData
) => Promise<ActionState<BrokerInsurerAssignmentOut>>;

/** A broker can be assigned to several insurers at once (many-to-many) --
 * this form stays usable after a successful assign (resets rather than
 * permanently replacing itself), since there's usually more than one
 * assignment to make. The parent page's revalidatePath call refreshes the
 * "already assigned" list this component's `insurers` prop is filtered
 * against, so an insurer disappears from the dropdown once assigned. */
export function AssignInsurerForm({
  action,
  insurers,
}: {
  action: Action;
  insurers: { id: string; name: string }[];
}) {
  const [state, formAction, pending] = useActionState(action, IDLE_STATE);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state.status === "success") {
      formRef.current?.reset();
    }
  }, [state]);

  if (insurers.length === 0) {
    return <span className="text-xs text-body-subtle">No unassigned approved insurers</span>;
  }

  return (
    <form ref={formRef} action={formAction} className="flex flex-wrap items-center gap-2">
      <select
        name="insurance_company_id"
        required
        className="rounded-base border border-border-default-medium bg-neutral-secondary-medium px-2 py-1.5 text-xs text-heading focus:border-border-brand focus:outline-none focus:ring-1 focus:ring-brand"
      >
        <option value="">Assign to insurer…</option>
        {insurers.map((insurer) => (
          <option key={insurer.id} value={insurer.id}>
            {insurer.name}
          </option>
        ))}
      </select>
      <Button type="submit" variant="secondary" size="xs" disabled={pending}>
        {pending ? "Assigning…" : "Assign"}
      </Button>
      {state.status === "success" && (
        <span className="text-xs font-medium text-fg-success-strong">Assigned</span>
      )}
      {state.status === "error" && <span className="text-xs text-fg-danger">{state.message}</span>}
    </form>
  );
}
