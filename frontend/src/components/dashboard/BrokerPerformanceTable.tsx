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

type BrokerPerformanceOut = components["schemas"]["BrokerPerformanceOut"];

export function BrokerPerformanceTable({ items }: { items: BrokerPerformanceOut[] }) {
  return (
    <Table>
      <TableHead>
        <TableHeaderCell>Broker name</TableHeaderCell>
        <TableHeaderCell>Policies sold</TableHeaderCell>
        <TableHeaderCell>Commission earned</TableHeaderCell>
      </TableHead>
      <TableBody>
        {items.length === 0 && (
          <tr>
            <td colSpan={3}>
              <EmptyState>No brokers assigned yet.</EmptyState>
            </td>
          </tr>
        )}
        {items.map((item) => (
          <TableRow key={item.broker_id}>
            <TableCell header>{item.broker_name}</TableCell>
            <TableCell>{item.policies_sold.toLocaleString("en-NG")}</TableCell>
            <TableCell>
              <Money kobo={item.commission_earned_kobo} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
