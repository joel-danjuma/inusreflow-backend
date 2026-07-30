import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { roleHasPermission } from "@/lib/auth/rbac";
import { ClientPortfolioTable } from "@/components/dashboard/ClientPortfolioTable";
import { Money } from "@/components/money/Money";
import { PolicyStatusBadge } from "@/components/badges/StatusBadge";
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
import { createSinglePayment } from "@/app/(dashboard)/dashboard/payments/actions";
import type { PolicyStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type BrokerPortfolioPage = components["schemas"]["BrokerPortfolioPage"];
type PolicyOut = components["schemas"]["PolicyOut"];
type PolicyholderOut = components["schemas"]["PolicyholderOut"];
type BrokerOut = components["schemas"]["BrokerOut"];

const PER_PAGE = 10;
const BASE_PATH = "/dashboard/policies";

export default async function PoliciesPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, Number(pageParam) || 1);
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  const canCreate = roleHasPermission(session!.role, "create_policy");

  if (session!.role === "insurance_company_admin") {
    const [policies, policyholders, brokers] = await Promise.all([
      apiFetch<PolicyOut[]>("/policies", { token }),
      apiFetch<PolicyholderOut[]>("/users", { token }),
      apiFetch<BrokerOut[]>(`/insurance-companies/${session!.orgId}/brokers`, { token }),
    ]);
    const policyholderNames = new Map(policyholders.map((p) => [p.id, p.full_name]));
    const brokerNames = new Map(brokers.map((b) => [b.id, b.name]));

    return (
      <div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-heading">Policies</h1>
            <p className="mt-1 text-sm text-body">Every policy across the brokers you work with.</p>
          </div>
          {canCreate && (
            <Link href="/dashboard/policies/new">
              <Button size="sm">New policy</Button>
            </Link>
          )}
        </div>

        <div className="mt-6">
          <Table>
            <TableHead>
              <TableHeaderCell>Reference number</TableHeaderCell>
              <TableHeaderCell>Policyholder</TableHeaderCell>
              <TableHeaderCell>Broker</TableHeaderCell>
              <TableHeaderCell>Premium</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
            </TableHead>
            <TableBody>
              {policies.length === 0 && (
                <tr>
                  <td colSpan={5}>
                    <EmptyState>No policies yet.</EmptyState>
                  </td>
                </tr>
              )}
              {policies.map((policy) => (
                <TableRow key={policy.id}>
                  <TableCell header>
                    <Link
                      href={`/dashboard/policies/${policy.id}`}
                      className="text-fg-brand hover:underline"
                    >
                      {policy.reference_number ?? "—"}
                    </Link>
                  </TableCell>
                  <TableCell>{policyholderNames.get(policy.policyholder_id) ?? "—"}</TableCell>
                  <TableCell>{brokerNames.get(policy.broker_id) ?? "—"}</TableCell>
                  <TableCell>
                    <Money kobo={policy.premium_amount_kobo} />
                  </TableCell>
                  <TableCell>
                    <PolicyStatusBadge status={policy.status as PolicyStatus} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    );
  }

  const portfolio = await apiFetch<BrokerPortfolioPage>("/brokers/me/portfolio", {
    token,
    searchParams: { page, per_page: PER_PAGE },
  });
  const canPay = roleHasPermission(session!.role, "create_payment");

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-heading">Policies</h1>
          <p className="mt-1 text-sm text-body">Every policy your team manages.</p>
        </div>
      </div>

      <div className="mt-6">
        <ClientPortfolioTable
          items={portfolio.items}
          total={portfolio.total}
          page={portfolio.page}
          perPage={portfolio.per_page}
          basePath={BASE_PATH}
          canPay={canPay}
          createSinglePayment={createSinglePayment}
        />
      </div>
    </div>
  );
}
