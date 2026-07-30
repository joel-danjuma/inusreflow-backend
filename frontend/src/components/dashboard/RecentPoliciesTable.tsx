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
import type { components } from "@/lib/api/types";

type RecentPolicyOut = components["schemas"]["RecentPolicyOut"];

export function RecentPoliciesTable({ items }: { items: RecentPolicyOut[] }) {
  return (
    <Table>
      <TableHead>
        <TableHeaderCell>Policy number</TableHeaderCell>
        <TableHeaderCell>Customer name</TableHeaderCell>
        <TableHeaderCell>Broker</TableHeaderCell>
        <TableHeaderCell>Policy amount</TableHeaderCell>
      </TableHead>
      <TableBody>
        {items.length === 0 && (
          <tr>
            <td colSpan={4}>
              <EmptyState>No policies yet.</EmptyState>
            </td>
          </tr>
        )}
        {items.map((item) => (
          <TableRow key={item.policy_id}>
            <TableCell header>{item.policy_number}</TableCell>
            <TableCell>{item.customer_name}</TableCell>
            <TableCell>{item.broker_name}</TableCell>
            <TableCell>
              <Money kobo={item.policy_amount_kobo} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
