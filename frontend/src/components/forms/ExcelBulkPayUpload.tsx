"use client";

import { useActionState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/Button";
import { IDLE_STATE, type ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type BulkPaymentFileResolution = components["schemas"]["BulkPaymentFileResolution"];
type ResolveFileAction = (
  prevState: ActionState<BulkPaymentFileResolution>,
  formData: FormData
) => Promise<ActionState<BulkPaymentFileResolution>>;

export function ExcelBulkPayUpload({
  action,
  onResolved,
}: {
  action: ResolveFileAction;
  onResolved: (installmentIds: string[]) => void;
}) {
  const [state, formAction, pending] = useActionState(
    action,
    IDLE_STATE as ActionState<BulkPaymentFileResolution>
  );
  const formRef = useRef<HTMLFormElement>(null);
  const lastHandledResolution = useRef<BulkPaymentFileResolution | null>(null);

  useEffect(() => {
    if (state.status !== "success" || !state.data) return;
    if (lastHandledResolution.current === state.data) return;
    lastHandledResolution.current = state.data;
    onResolved(state.data.matched.map((row) => row.installment_id));
  }, [state, onResolved]);

  const resolution = state.status === "success" ? state.data : undefined;

  return (
    <div className="rounded-base border border-border-default bg-neutral-primary-soft p-4">
      <h3 className="text-sm font-medium text-heading">Upload premiums to pay</h3>
      <p className="mt-1 text-sm text-body">
        Upload an Excel file listing the debit note / reference numbers of the premiums you want
        to pay &mdash; matched rows are pre-selected below, so you don&apos;t have to search for
        each one individually.{" "}
        <a href="/api/payments/bulk/template" download className="text-fg-brand hover:underline">
          Download a reference template
        </a>{" "}
        if you&apos;re not sure what the system expects.
      </p>

      <form
        ref={formRef}
        action={(formData) => {
          formAction(formData);
        }}
        className="mt-3 flex flex-wrap items-center gap-3"
      >
        <input
          type="file"
          name="file"
          accept=".xlsx"
          required
          className="text-sm text-body file:mr-3 file:rounded-default file:border file:border-border-default file:bg-neutral-secondary-medium file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-heading"
        />
        <Button type="submit" variant="tertiary" size="sm" disabled={pending}>
          {pending ? "Matching…" : "Match premiums"}
        </Button>
      </form>

      {state.status === "error" && (
        <p className="mt-3 text-sm text-fg-danger">{state.message}</p>
      )}

      {resolution && (
        <div className="mt-3 text-sm">
          {resolution.file_error ? (
            <p className="text-fg-danger">{resolution.file_error}</p>
          ) : (
            <>
              <p className="text-fg-success-strong">
                Matched {resolution.matched.length} of {resolution.total_rows} row
                {resolution.total_rows === 1 ? "" : "s"}
                {resolution.matched.length > 0 && " and selected them below."}
              </p>
              {resolution.unmatched.length > 0 && (
                <div className="mt-2 overflow-x-auto rounded-default border border-border-default">
                  <table className="w-full text-left text-xs text-body">
                    <thead className="bg-neutral-secondary-soft">
                      <tr>
                        <th className="px-3 py-2 font-medium">Row</th>
                        <th className="px-3 py-2 font-medium">Reference</th>
                        <th className="px-3 py-2 font-medium">Why it was skipped</th>
                      </tr>
                    </thead>
                    <tbody>
                      {resolution.unmatched.map((row) => (
                        <tr key={row.row_number} className="border-t border-border-default">
                          <td className="px-3 py-2">{row.row_number}</td>
                          <td className="px-3 py-2">{row.reference_number ?? "—"}</td>
                          <td className="px-3 py-2 text-fg-danger">{row.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
