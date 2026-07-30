"use client";

import { useCallback, useMemo, useState } from "react";
import { InstallmentsPaymentTable } from "./InstallmentsPaymentTable";
import { BulkPayBar, BULK_PAY_FORM_ID, MAX_BULK_ITEMS } from "./BulkPayBar";
import { ExcelBulkPayUpload } from "./ExcelBulkPayUpload";
import type { components } from "@/lib/api/types";

type InstallmentOut = components["schemas"]["InstallmentOut"];
type BulkPaymentFileResolution = components["schemas"]["BulkPaymentFileResolution"];
type ActionState<T = undefined> = import("@/lib/api/action-state").ActionState<T>;
type SingleAction = (
  installmentId: string,
  prevState: ActionState<undefined>,
  formData: FormData
) => Promise<ActionState<undefined>>;
type BulkAction = (
  prevState: ActionState<undefined>,
  formData: FormData
) => Promise<ActionState<undefined>>;
type SetReferenceAction = (
  installmentId: string,
  prevState: ActionState<InstallmentOut>,
  formData: FormData
) => Promise<ActionState<InstallmentOut>>;
type ResolveFileAction = (
  prevState: ActionState<BulkPaymentFileResolution>,
  formData: FormData
) => Promise<ActionState<BulkPaymentFileResolution>>;

export function InstallmentsWorkspace({
  installments,
  canPay,
  createSinglePayment,
  createBulkPayment,
  canManageReference,
  setInstallmentReferenceNumber,
  resolveBulkPaymentFile,
}: {
  installments: InstallmentOut[];
  canPay: boolean;
  createSinglePayment: SingleAction;
  createBulkPayment: BulkAction;
  canManageReference?: boolean;
  setInstallmentReferenceNumber?: SetReferenceAction;
  resolveBulkPaymentFile?: ResolveFileAction;
}) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const amountById = useMemo(
    () => new Map(installments.map((i) => [i.id, i.amount_kobo])),
    [installments]
  );
  const visibleIds = useMemo(() => new Set(installments.map((i) => i.id)), [installments]);
  const hiddenSelectedIds = useMemo(
    () => [...selected].filter((id) => !visibleIds.has(id)),
    [selected, visibleIds]
  );

  const totalKobo = useMemo(() => {
    let sum = 0;
    for (const id of selected) sum += amountById.get(id) ?? 0;
    return sum;
  }, [selected, amountById]);

  const toggle = useCallback((id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else if (next.size < MAX_BULK_ITEMS) {
        next.add(id);
      }
      return next;
    });
  }, []);

  const selectMatchedIds = useCallback((ids: string[]) => {
    setSelected(new Set(ids.slice(0, MAX_BULK_ITEMS)));
  }, []);

  return (
    <div className="space-y-4">
      {canPay && resolveBulkPaymentFile && (
        <ExcelBulkPayUpload action={resolveBulkPaymentFile} onResolved={selectMatchedIds} />
      )}

      {canPay && (
        <>
          <BulkPayBar
            selectedIds={[...selected]}
            totalKobo={totalKobo}
            action={createBulkPayment}
          />
          {/* Matched-but-currently-filtered-out rows have no checkbox
           * rendered in the table below -- without this, they'd stay
           * "selected" in state but never actually submit, since
           * BulkPayBar's form only picks up inputs physically present in
           * the DOM. A hidden input with the same form= attribute submits
           * into the same form regardless of where it's rendered. */}
          {hiddenSelectedIds.length > 0 && (
            <p className="text-xs text-body-subtle">
              {hiddenSelectedIds.length} matched{" "}
              {hiddenSelectedIds.length === 1 ? "row is" : "rows are"} hidden by your current
              filter, but still included in this payment.
            </p>
          )}
          {hiddenSelectedIds.map((id) => (
            <input
              key={id}
              type="hidden"
              form={BULK_PAY_FORM_ID}
              name="installment_ids"
              value={id}
            />
          ))}
        </>
      )}

      <InstallmentsPaymentTable
        installments={installments}
        canPay={canPay}
        selected={selected}
        onToggle={toggle}
        createSinglePayment={createSinglePayment}
        canManageReference={canManageReference}
        setInstallmentReferenceNumber={setInstallmentReferenceNumber}
      />
    </div>
  );
}
