import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken } from "@/lib/auth/session";
import { Money } from "@/components/money/Money";
import { SettlementPayoutStatusBadge } from "@/components/badges/StatusBadge";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import type { SettlementPayoutStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type SettlementPayoutOut = components["schemas"]["SettlementPayoutOut"];

export default async function SettlementsPage() {
  const token = await getAuthToken();
  const settlements = await apiFetch<SettlementPayoutOut[]>("/settlements", { token });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Settlements</h1>
      <p className="mt-1 text-sm text-body">
        Real-time payouts to insurers, net of commission, triggered automatically after each
        successful payment or batch.
      </p>

      <div className="mt-6">
        <Table>
          <TableHead>
            <TableHeaderCell>Amount</TableHeaderCell>
            <TableHeaderCell>Source</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            <TableHeaderCell>Attempt</TableHeaderCell>
            <TableHeaderCell>Created</TableHeaderCell>
          </TableHead>
          <TableBody>
            {settlements.length === 0 && (
              <tr>
                <td colSpan={5}>
                  <EmptyState>No settlements yet.</EmptyState>
                </td>
              </tr>
            )}
            {settlements.map((payout) => (
              <TableRow key={payout.id}>
                <TableCell header>
                  <Link
                    href={`/dashboard/settlements/${payout.id}`}
                    className="text-fg-brand hover:underline"
                  >
                    <Money kobo={payout.amount_kobo} />
                  </Link>
                </TableCell>
                <TableCell className="capitalize">
                  {payout.source_type.replace("_", " ")}
                </TableCell>
                <TableCell>
                  <SettlementPayoutStatusBadge status={payout.status as SettlementPayoutStatus} />
                </TableCell>
                <TableCell>#{payout.attempt_number}</TableCell>
                <TableCell>{new Date(payout.created_at).toLocaleString("en-NG")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
