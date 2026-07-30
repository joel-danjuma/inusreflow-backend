import Link from "next/link";
import { Money } from "@/components/money/Money";
import {
  PolicyStatusBadge,
  InstallmentStatusBadge,
  PaymentStatusBadge,
} from "@/components/badges/StatusBadge";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { SinglePayButton } from "@/components/forms/SinglePayButton";
import type { InstallmentStatus, PolicyStatus } from "@/lib/enums";
import type { ActionState } from "@/lib/api/action-state";
import type { components } from "@/lib/api/types";

type PortfolioItemOut = components["schemas"]["PortfolioItemOut"];
type SingleAction = (
  installmentId: string,
  prevState: ActionState<undefined>,
  formData: FormData
) => Promise<ActionState<undefined>>;

export function ClientPortfolioTable({
  items,
  total,
  page,
  perPage,
  basePath,
  canPay,
  createSinglePayment,
}: {
  items: PortfolioItemOut[];
  total: number;
  page: number;
  perPage: number;
  basePath: string;
  canPay: boolean;
  createSinglePayment: SingleAction;
}) {
  const totalPages = Math.max(1, Math.ceil(total / perPage));

  return (
    <div>
      <Table>
        <TableHead>
          <TableHeaderCell>Client name</TableHeaderCell>
          <TableHeaderCell>Policy type</TableHeaderCell>
          <TableHeaderCell>Policy status</TableHeaderCell>
          <TableHeaderCell>Payment status</TableHeaderCell>
          <TableHeaderCell>Premium amount</TableHeaderCell>
          <TableHeaderCell>Payment due date</TableHeaderCell>
          <TableHeaderCell>Debit note / reference</TableHeaderCell>
          {canPay && <TableHeaderCell>{""}</TableHeaderCell>}
        </TableHead>
        <TableBody>
          {items.length === 0 && (
            <tr>
              <td colSpan={canPay ? 8 : 7}>
                <EmptyState>No clients yet &mdash; create a policyholder to get started.</EmptyState>
              </td>
            </tr>
          )}
          {items.map((item) => (
            <TableRow key={item.policy_id}>
              <TableCell header>
                <Link
                  href={`/dashboard/policyholders/${item.policyholder_id}`}
                  className="text-fg-brand hover:underline"
                >
                  {item.client_name}
                </Link>
              </TableCell>
              <TableCell>
                <Link
                  href={`/dashboard/policies/${item.policy_id}`}
                  className="text-fg-brand hover:underline"
                >
                  {item.policy_type}
                </Link>
              </TableCell>
              <TableCell>
                <PolicyStatusBadge status={item.policy_status as PolicyStatus} />
              </TableCell>
              <TableCell>
                {item.payment_status === "in_progress" ? (
                  <PaymentStatusBadge status="initiated" />
                ) : (
                  <InstallmentStatusBadge status={item.payment_status as InstallmentStatus} />
                )}
              </TableCell>
              <TableCell>
                <Money kobo={item.premium_amount_kobo} />
              </TableCell>
              <TableCell>
                {item.next_payment_date
                  ? new Date(item.next_payment_date).toLocaleDateString("en-NG")
                  : "—"}
              </TableCell>
              <TableCell>{item.next_payment_reference_number ?? "—"}</TableCell>
              {canPay && (
                <TableCell>
                  {item.next_installment_id && (
                    <SinglePayButton
                      installmentId={item.next_installment_id}
                      action={createSinglePayment.bind(null, item.next_installment_id)}
                    />
                  )}
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {totalPages > 1 && (
        <div className="mt-4 flex justify-end">
          <Pagination basePath={basePath} currentPage={page} totalPages={totalPages} />
        </div>
      )}
    </div>
  );
}
