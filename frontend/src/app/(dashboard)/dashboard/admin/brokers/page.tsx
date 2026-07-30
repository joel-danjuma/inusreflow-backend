import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken } from "@/lib/auth/session";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import { OnboardingStatusBadge } from "@/components/badges/StatusBadge";
import { ApproveRejectActions } from "@/components/forms/ApproveRejectActions";
import { Button } from "@/components/ui/Button";
import type { OnboardingStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";
import { approveBroker, rejectBroker } from "./actions";

type BrokerOut = components["schemas"]["BrokerOut"];

export default async function AdminBrokersPage() {
  const token = await getAuthToken();
  const brokers = await apiFetch<BrokerOut[]>("/admin/brokers", { token });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Brokers</h1>
      <p className="mt-1 text-sm text-body">All brokers onboarded to the platform.</p>

      <div className="mt-6">
        <Table>
          <TableHead>
            <TableHeaderCell>Name</TableHeaderCell>
            <TableHeaderCell>Contact email</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            <TableHeaderCell>Approval</TableHeaderCell>
            <TableHeaderCell>Insurer assignment</TableHeaderCell>
          </TableHead>
          <TableBody>
            {brokers.length === 0 && (
              <tr>
                <td colSpan={5}>
                  <EmptyState>No brokers yet.</EmptyState>
                </td>
              </tr>
            )}
            {brokers.map((broker) => (
              <TableRow key={broker.id}>
                <TableCell header>
                  <Link
                    href={`/dashboard/admin/brokers/${broker.id}`}
                    className="text-fg-brand hover:underline"
                  >
                    {broker.name}
                  </Link>
                </TableCell>
                <TableCell>{broker.contact_email}</TableCell>
                <TableCell>
                  <OnboardingStatusBadge status={broker.status as OnboardingStatus} />
                </TableCell>
                <TableCell>
                  {broker.status === "pending" ? (
                    <ApproveRejectActions
                      approveAction={approveBroker.bind(null, broker.id)}
                      rejectAction={rejectBroker.bind(null, broker.id)}
                      label={broker.name}
                    />
                  ) : (
                    <span className="text-xs text-body-subtle">No actions</span>
                  )}
                </TableCell>
                <TableCell>
                  {broker.status === "approved" ? (
                    <Link href={`/dashboard/admin/brokers/${broker.id}`}>
                      <Button variant="tertiary" size="xs">
                        Manage assignments
                      </Button>
                    </Link>
                  ) : (
                    <span className="text-xs text-body-subtle">&mdash;</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
