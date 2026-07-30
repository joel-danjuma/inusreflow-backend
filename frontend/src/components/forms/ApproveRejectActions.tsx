"use client";

import { useActionState, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Textarea } from "@/components/ui/Textarea";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";

type ApproveAction<T> = (
  prevState: ActionState<T>,
  formData: FormData
) => Promise<ActionState<T>>;
type RejectAction = (
  prevState: ActionState<undefined>,
  formData: FormData
) => Promise<ActionState<undefined>>;

export function ApproveRejectActions<T>({
  approveAction,
  rejectAction,
  label,
}: {
  approveAction: ApproveAction<T>;
  rejectAction: RejectAction;
  label: string;
}) {
  const [approveState, submitApprove, approvePending] = useActionState(
    approveAction,
    IDLE_STATE as ActionState<T>
  );
  const [rejectState, submitReject, rejectPending] = useActionState(rejectAction, IDLE_STATE);
  const [rejectOpen, setRejectOpen] = useState(false);

  if (approveState.status === "success") {
    return <p className="text-sm font-medium text-fg-success-strong">Approved</p>;
  }

  if (rejectState.status === "success") {
    return <p className="text-sm font-medium text-fg-danger-strong">Rejected</p>;
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <form action={submitApprove}>
        <Button type="submit" variant="success" size="sm" disabled={approvePending}>
          {approvePending ? "Approving…" : "Approve"}
        </Button>
      </form>
      <Button variant="danger" size="sm" onClick={() => setRejectOpen(true)}>
        Reject
      </Button>
      {approveState.status === "error" && (
        <p className="w-full text-xs text-fg-danger">{approveState.message}</p>
      )}

      <Modal open={rejectOpen} onClose={() => setRejectOpen(false)} title={`Reject ${label}`}>
        <form action={submitReject} className="space-y-4">
          {rejectState.status === "error" && (
            <p className="text-sm text-fg-danger">{rejectState.message}</p>
          )}
          <Textarea
            id="reason"
            name="reason"
            label="Reason"
            required
            error={rejectState.fieldErrors?.reason}
            placeholder="Why is this application being rejected?"
          />
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="sm" onClick={() => setRejectOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="danger" size="sm" disabled={rejectPending}>
              {rejectPending ? "Rejecting…" : "Confirm rejection"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
