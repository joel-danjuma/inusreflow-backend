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
import { RecreateVirtualAccountButton } from "@/components/forms/RecreateVirtualAccountButton";
import type { components } from "@/lib/api/types";
import { recreateVirtualAccount } from "./actions";

type VirtualAccountOut = components["schemas"]["VirtualAccountOut"];

export default async function AdminVirtualAccountsPage() {
  const token = await getAuthToken();
  const accounts = await apiFetch<VirtualAccountOut[]>("/virtual-accounts", { token });

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Virtual Accounts</h1>
      <p className="mt-1 text-sm text-body">
        Every broker&apos;s permanent Squad collection account.
      </p>

      <div className="mt-6">
        <Table>
          <TableHead>
            <TableHeaderCell>Broker</TableHeaderCell>
            <TableHeaderCell>Account number</TableHeaderCell>
            <TableHeaderCell>Bank</TableHeaderCell>
            <TableHeaderCell>Actions</TableHeaderCell>
          </TableHead>
          <TableBody>
            {accounts.length === 0 && (
              <tr>
                <td colSpan={4}>
                  <EmptyState>No virtual accounts yet.</EmptyState>
                </td>
              </tr>
            )}
            {accounts.map((account) => (
              <TableRow key={account.broker_id}>
                <TableCell header>{account.broker_name}</TableCell>
                <TableCell>
                  <span className="font-mono">{account.squad_va_number ?? "Not provisioned"}</span>
                </TableCell>
                <TableCell>{account.squad_va_bank ?? "—"}</TableCell>
                <TableCell>
                  <RecreateVirtualAccountButton
                    action={recreateVirtualAccount.bind(null, account.broker_id)}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
