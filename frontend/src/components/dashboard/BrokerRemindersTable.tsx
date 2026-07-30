import Link from "next/link";
import { Money } from "@/components/money/Money";
import { ReminderStatusBadge } from "@/components/badges/StatusBadge";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import type { ReminderStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type ReminderOut = components["schemas"]["ReminderOut"];
type InstallmentOut = components["schemas"]["InstallmentOut"];

export function BrokerRemindersTable({
  reminders,
  installmentById,
}: {
  reminders: ReminderOut[];
  installmentById: Map<string, InstallmentOut>;
}) {
  const sorted = [...reminders].sort((a, b) => (a.created_at < b.created_at ? 1 : -1));

  return (
    <Table>
      <TableHead>
        <TableHeaderCell>Policy type</TableHeaderCell>
        <TableHeaderCell>Amount due</TableHeaderCell>
        <TableHeaderCell>Due date</TableHeaderCell>
        <TableHeaderCell>Channel</TableHeaderCell>
        <TableHeaderCell>Status</TableHeaderCell>
        <TableHeaderCell>Sent</TableHeaderCell>
      </TableHead>
      <TableBody>
        {sorted.length === 0 && (
          <tr>
            <td colSpan={6}>
              <EmptyState>No reminders yet.</EmptyState>
            </td>
          </tr>
        )}
        {sorted.map((reminder) => {
          const installment = installmentById.get(reminder.installment_id);
          return (
            <TableRow key={reminder.id}>
              <TableCell header>
                {installment ? (
                  <Link
                    href={`/dashboard/policies/${installment.policy_id}`}
                    className="text-fg-brand hover:underline"
                  >
                    {installment.policy_type}
                  </Link>
                ) : (
                  "—"
                )}
              </TableCell>
              <TableCell>{installment ? <Money kobo={installment.amount_kobo} /> : "—"}</TableCell>
              <TableCell>
                {installment ? new Date(installment.due_date).toLocaleDateString("en-NG") : "—"}
              </TableCell>
              <TableCell className="capitalize">{reminder.channel}</TableCell>
              <TableCell>
                <ReminderStatusBadge status={reminder.status as ReminderStatus} />
              </TableCell>
              <TableCell>
                {reminder.sent_at ? new Date(reminder.sent_at).toLocaleString("en-NG") : "—"}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
