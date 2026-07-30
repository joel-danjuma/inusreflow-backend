import { Money } from "@/components/money/Money";
import { PaymentStatusBadge } from "@/components/badges/StatusBadge";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import type { PaymentStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type LatestPaymentOut = components["schemas"]["LatestPaymentOut"];

export function LatestPaymentsTable({ items }: { items: LatestPaymentOut[] }) {
  return (
    <Table>
      <TableHead>
        <TableHeaderCell>Broker name</TableHeaderCell>
        <TableHeaderCell>Total amount</TableHeaderCell>
        <TableHeaderCell>Policies paid</TableHeaderCell>
        <TableHeaderCell>Payment method</TableHeaderCell>
        <TableHeaderCell>Status</TableHeaderCell>
        <TableHeaderCell>Payment date</TableHeaderCell>
      </TableHead>
      <TableBody>
        {items.length === 0 && (
          <tr>
            <td colSpan={6}>
              <EmptyState>No payments yet.</EmptyState>
            </td>
          </tr>
        )}
        {items.map((item) => (
          <TableRow key={item.id}>
            <TableCell header>{item.broker_name}</TableCell>
            <TableCell>
              <Money kobo={item.total_amount_kobo} />
            </TableCell>
            <TableCell>{item.policies_paid.toLocaleString("en-NG")}</TableCell>
            <TableCell>{item.payment_method}</TableCell>
            <TableCell>
              <PaymentStatusBadge status={item.status as PaymentStatus} />
            </TableCell>
            <TableCell>{new Date(item.payment_date).toLocaleDateString("en-NG")}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
