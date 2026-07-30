import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { roleHasPermission } from "@/lib/auth/rbac";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import { Button } from "@/components/ui/Button";
import type { components } from "@/lib/api/types";

type PolicyholderOut = components["schemas"]["PolicyholderOut"];

export default async function PolicyholdersPage() {
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  // No broker_id param -- the backend derives the right scope per role: a
  // broker always sees only their own, an insurer sees every policyholder
  // across every broker they work with (narrow via ?broker_id= if needed).
  const policyholders = await apiFetch<PolicyholderOut[]>("/users", { token });
  const canCreate = roleHasPermission(session!.role, "create_policyholder");

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-heading">Policyholders</h1>
          <p className="mt-1 text-sm text-body">Everyone recorded a policy for.</p>
        </div>
        {canCreate && (
          <Link href="/dashboard/policyholders/new">
            <Button size="sm">New policyholder</Button>
          </Link>
        )}
      </div>

      <div className="mt-6">
        <Table>
          <TableHead>
            <TableHeaderCell>Full name</TableHeaderCell>
            <TableHeaderCell>Email</TableHeaderCell>
            <TableHeaderCell>Phone</TableHeaderCell>
          </TableHead>
          <TableBody>
            {policyholders.length === 0 && (
              <tr>
                <td colSpan={3}>
                  <EmptyState>No policyholders yet.</EmptyState>
                </td>
              </tr>
            )}
            {policyholders.map((ph) => (
              <TableRow key={ph.id}>
                <TableCell header>
                  <Link
                    href={`/dashboard/policyholders/${ph.id}`}
                    className="text-fg-brand hover:underline"
                  >
                    {ph.full_name}
                  </Link>
                </TableCell>
                <TableCell>{ph.email ?? "—"}</TableCell>
                <TableCell>{ph.phone_number ?? "—"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
