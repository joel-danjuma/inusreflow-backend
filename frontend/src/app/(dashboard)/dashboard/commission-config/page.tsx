import { apiFetch } from "@/lib/api/client";
import { getAuthToken, getSession } from "@/lib/auth/session";
import { Badge } from "@/components/ui/Badge";
import { GlobalOrInsurerCommissionForm } from "@/components/forms/GlobalOrInsurerCommissionForm";
import { BrokerCommissionForm } from "@/components/forms/BrokerCommissionForm";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import { formatBasisPoints } from "@/lib/money";
import type { components } from "@/lib/api/types";
import { createGlobalOrInsurerCommissionConfig, createBrokerCommissionConfig } from "./actions";

type CommissionConfigOut = components["schemas"]["CommissionConfigOut"];
type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];
type BrokerOut = components["schemas"]["BrokerOut"];

export default async function CommissionConfigPage() {
  const [token, session] = await Promise.all([getAuthToken(), getSession()]);
  const role = session!.role;

  const configs = await apiFetch<CommissionConfigOut[]>("/commission-configs", { token });

  let insurers: InsuranceCompanyOut[] = [];
  let brokers: BrokerOut[] = [];
  if (role === "insureflow_admin") {
    insurers = (
      await apiFetch<InsuranceCompanyOut[]>("/admin/insurance-companies", { token })
    ).filter((i) => i.status === "approved");
  } else if (role === "insurance_company_admin") {
    brokers = await apiFetch<BrokerOut[]>(`/insurance-companies/${session!.orgId}/brokers`, {
      token,
    });
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-heading">Commission Config</h1>
        <p className="mt-1 text-sm text-body">
          Versioned rates &mdash; setting a new rate never edits history in place; it closes the
          previous row and starts a new one, effective immediately.
        </p>
      </div>

      {role === "insureflow_admin" && (
        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <h2 className="mb-4 text-base font-medium text-heading">Set a new rate</h2>
          <GlobalOrInsurerCommissionForm
            action={createGlobalOrInsurerCommissionConfig}
            insurers={insurers.map((i) => ({ id: i.id, name: i.name }))}
          />
        </div>
      )}

      {role === "insurance_company_admin" && (
        <div className="rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
          <h2 className="mb-4 text-base font-medium text-heading">
            Set a broker&apos;s commission rate
          </h2>
          <BrokerCommissionForm
            action={createBrokerCommissionConfig}
            brokers={brokers.map((b) => ({ id: b.id, name: b.name }))}
          />
        </div>
      )}

      <div>
        <h2 className="mb-3 text-base font-medium text-heading">History</h2>
        <Table>
          <TableHead>
            <TableHeaderCell>Scope</TableHeaderCell>
            <TableHeaderCell>GTBank</TableHeaderCell>
            <TableHeaderCell>Insureflow</TableHeaderCell>
            <TableHeaderCell>Broker</TableHeaderCell>
            <TableHeaderCell>Effective from</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableHead>
          <TableBody>
            {configs.length === 0 && (
              <tr>
                <td colSpan={6}>
                  <EmptyState>No commission configs yet.</EmptyState>
                </td>
              </tr>
            )}
            {configs.map((config) => (
              <TableRow key={config.id}>
                <TableCell header className="capitalize">
                  {config.scope.replace("_", " ")}
                </TableCell>
                <TableCell>{formatBasisPoints(config.gtbank_rate_bps)}</TableCell>
                <TableCell>{formatBasisPoints(config.insureflow_rate_bps)}</TableCell>
                <TableCell>
                  {config.broker_rate_bps !== null
                    ? formatBasisPoints(config.broker_rate_bps)
                    : "—"}
                </TableCell>
                <TableCell>
                  {new Date(config.effective_from).toLocaleDateString("en-NG")}
                </TableCell>
                <TableCell>
                  {config.effective_to === null ? (
                    <Badge variant="success">Active</Badge>
                  ) : (
                    <Badge variant="gray">Closed</Badge>
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
