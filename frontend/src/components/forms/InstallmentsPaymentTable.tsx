"use client";

import Link from "next/link";
import { Money } from "@/components/money/Money";
import { InstallmentStatusBadge } from "@/components/badges/StatusBadge";
import { Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell, EmptyState } from "@/components/ui/Table";
import { SinglePayButton } from "./SinglePayButton";
import { BULK_PAY_FORM_ID, MAX_BULK_ITEMS } from "./BulkPayBar";
import { InlineReferenceNumberEditor } from "./InlineReferenceNumberEditor";
import type { InstallmentStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type InstallmentOut = components["schemas"]["InstallmentOut"];
type ActionState<T = undefined> = import("@/lib/api/action-state").ActionState<T>;
/** The raw (unbound) Server Action -- bound client-side per row via
 * .bind(null, installmentId), since a plain JS function that RETURNS a
 * bound action can't itself cross the server/client boundary as a prop,
 * only an actual Server Action reference can. */
type SingleAction = (
  installmentId: string,
  prevState: ActionState<undefined>,
  formData: FormData
) => Promise<ActionState<undefined>>;
type SetReferenceAction = (
  installmentId: string,
  prevState: ActionState<InstallmentOut>,
  formData: FormData
) => Promise<ActionState<InstallmentOut>>;

function isPayable(status: string): boolean {
  return status === "due" || status === "overdue";
}

/** Controlled by its parent (InstallmentsWorkspace) rather than owning its
 * own selection state -- the workspace also needs to track selections made
 * via the Excel upload, including ones that aren't in the currently
 * filtered `installments` array at all. */
export function InstallmentsPaymentTable({
  installments,
  canPay,
  selected,
  onToggle,
  createSinglePayment,
  canManageReference,
  setInstallmentReferenceNumber,
}: {
  installments: InstallmentOut[];
  canPay: boolean;
  selected: Set<string>;
  onToggle: (id: string) => void;
  createSinglePayment: SingleAction;
  canManageReference?: boolean;
  setInstallmentReferenceNumber?: SetReferenceAction;
}) {
  return (
    <Table>
      <TableHead>
        {canPay && <TableHeaderCell>{""}</TableHeaderCell>}
        <TableHeaderCell>Due date</TableHeaderCell>
        <TableHeaderCell>Amount</TableHeaderCell>
        <TableHeaderCell>Status</TableHeaderCell>
        <TableHeaderCell>Policy</TableHeaderCell>
        <TableHeaderCell>Reference</TableHeaderCell>
        {canPay && <TableHeaderCell>Actions</TableHeaderCell>}
      </TableHead>
      <TableBody>
        {installments.length === 0 && (
          <tr>
            <td colSpan={canPay ? 7 : 5}>
              <EmptyState>No installments found.</EmptyState>
            </td>
          </tr>
        )}
        {installments.map((installment) => {
          const payable = isPayable(installment.status);
          const atCap = !selected.has(installment.id) && selected.size >= MAX_BULK_ITEMS;
          return (
            <TableRow key={installment.id}>
              {canPay && (
                <TableCell>
                  {payable && (
                    <input
                      type="checkbox"
                      form={BULK_PAY_FORM_ID}
                      name="installment_ids"
                      value={installment.id}
                      checked={selected.has(installment.id)}
                      disabled={atCap}
                      onChange={() => onToggle(installment.id)}
                      aria-label={`Select installment due ${installment.due_date}`}
                      className="h-4 w-4 rounded-sm border-border-default-medium accent-brand"
                    />
                  )}
                </TableCell>
              )}
              <TableCell header>{new Date(installment.due_date).toLocaleDateString("en-NG")}</TableCell>
              <TableCell>
                <Money kobo={installment.amount_kobo} />
              </TableCell>
              <TableCell>
                <InstallmentStatusBadge status={installment.status as InstallmentStatus} />
              </TableCell>
              <TableCell>
                <Link
                  href={`/dashboard/policies/${installment.policy_id}`}
                  className="text-fg-brand hover:underline"
                >
                  View policy
                </Link>
              </TableCell>
              <TableCell>
                {canManageReference && setInstallmentReferenceNumber ? (
                  <InlineReferenceNumberEditor
                    installmentId={installment.id}
                    referenceNumber={installment.reference_number}
                    action={setInstallmentReferenceNumber}
                  />
                ) : (
                  (installment.reference_number ?? "—")
                )}
              </TableCell>
              {canPay && (
                <TableCell>
                  {payable && (
                    <SinglePayButton
                      installmentId={installment.id}
                      action={createSinglePayment.bind(null, installment.id)}
                    />
                  )}
                </TableCell>
              )}
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
