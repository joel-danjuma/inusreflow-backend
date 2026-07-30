"use client";

import { useActionState, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Money } from "@/components/money/Money";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type OutstandingPolicyOut = components["schemas"]["OutstandingPolicyOut"];
type BulkReminderResult = components["schemas"]["BulkReminderResult"];
type SendRemindersAction = (
  prevState: ActionState<BulkReminderResult>,
  formData: FormData
) => Promise<ActionState<BulkReminderResult>>;

export function PaymentRemindersSection({
  overdueCount,
  outstandingPolicies,
  sendPaymentReminders,
}: {
  overdueCount: number;
  outstandingPolicies: OutstandingPolicyOut[];
  sendPaymentReminders: SendRemindersAction;
}) {
  const [expanded, setExpanded] = useState(false);
  const [state, formAction, pending] = useActionState(sendPaymentReminders, IDLE_STATE);

  return (
    <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-medium text-heading">Payment reminders</h2>
          <p className="mt-1 text-sm text-body">
            {overdueCount === 0
              ? "No overdue policies right now."
              : `${overdueCount} ${overdueCount === 1 ? "policy is" : "policies are"} overdue on premium payments.`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="tertiary"
            size="sm"
            onClick={() => setExpanded((v) => !v)}
            disabled={overdueCount === 0}
          >
            {expanded ? "Hide outstanding" : `View outstanding (${overdueCount})`}
          </Button>
          <form action={formAction}>
            <Button
              type="submit"
              variant="brand"
              size="sm"
              disabled={pending || overdueCount === 0}
            >
              {pending ? "Sending…" : "Send payment reminders"}
            </Button>
          </form>
        </div>
      </div>

      {state.status === "success" && (
        <p className="mt-3 text-sm text-fg-success-strong">
          Sent {state.data?.reminders_created ?? 0} reminder
          {(state.data?.reminders_created ?? 0) === 1 ? "" : "s"}.
        </p>
      )}
      {state.status === "error" && <p className="mt-3 text-sm text-fg-danger">{state.message}</p>}

      {expanded && (
        <div className="mt-4">
          <Table>
            <TableHead>
              <TableHeaderCell>Policy number</TableHeaderCell>
              <TableHeaderCell>Customer name</TableHeaderCell>
              <TableHeaderCell>Broker</TableHeaderCell>
              <TableHeaderCell>Premium amount</TableHeaderCell>
              <TableHeaderCell>Days overdue</TableHeaderCell>
              <TableHeaderCell>Last payment</TableHeaderCell>
              <TableHeaderCell>Debit note / reference</TableHeaderCell>
            </TableHead>
            <TableBody>
              {outstandingPolicies.length === 0 && (
                <tr>
                  <td colSpan={7}>
                    <EmptyState>No outstanding policies.</EmptyState>
                  </td>
                </tr>
              )}
              {outstandingPolicies.map((item) => (
                <TableRow key={item.policy_id}>
                  <TableCell header>{item.policy_number}</TableCell>
                  <TableCell>{item.customer_name}</TableCell>
                  <TableCell>{item.broker_name}</TableCell>
                  <TableCell>
                    <Money kobo={item.premium_amount_kobo} />
                  </TableCell>
                  <TableCell>{item.days_overdue}</TableCell>
                  <TableCell>
                    {item.last_payment_date
                      ? new Date(item.last_payment_date).toLocaleDateString("en-NG")
                      : "—"}
                  </TableCell>
                  <TableCell>{item.reference_number ?? "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
