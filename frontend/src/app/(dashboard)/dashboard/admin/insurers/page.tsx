import { Fragment } from "react";
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
import type { OnboardingStatus } from "@/lib/enums";
import type { components } from "@/lib/api/types";
import { approveInsurer, rejectInsurer } from "./actions";

type InsuranceCompanyOut = components["schemas"]["InsuranceCompanyOut"];

function CompanyRow({
  company,
  isSubsidiary,
}: {
  company: InsuranceCompanyOut;
  isSubsidiary: boolean;
}) {
  return (
    <TableRow key={company.id}>
      <TableCell header>
        <Link
          href={`/dashboard/admin/insurers/${company.id}`}
          className={`text-fg-brand hover:underline ${isSubsidiary ? "pl-4" : ""}`}
        >
          {isSubsidiary && <span className="mr-1 text-body-subtle">&#8627;</span>}
          {company.name}
        </Link>
      </TableCell>
      <TableCell>{company.contact_email}</TableCell>
      <TableCell>
        <OnboardingStatusBadge status={company.status as OnboardingStatus} />
      </TableCell>
      <TableCell>
        {company.status === "pending" ? (
          <ApproveRejectActions
            approveAction={approveInsurer.bind(null, company.id)}
            rejectAction={rejectInsurer.bind(null, company.id)}
            label={company.name}
          />
        ) : (
          <span className="text-xs text-body-subtle">No actions</span>
        )}
      </TableCell>
    </TableRow>
  );
}

export default async function AdminInsurersPage() {
  const token = await getAuthToken();
  const companies = await apiFetch<InsuranceCompanyOut[]>("/admin/insurance-companies", { token });

  const topLevel = companies.filter((c) => !c.parent_company_id);
  const childrenByParent = new Map<string, InsuranceCompanyOut[]>();
  for (const company of companies) {
    if (!company.parent_company_id) continue;
    const siblings = childrenByParent.get(company.parent_company_id) ?? [];
    siblings.push(company);
    childrenByParent.set(company.parent_company_id, siblings);
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Insurers</h1>
      <p className="mt-1 text-sm text-body">
        All insurance companies onboarded to the platform. Subsidiaries are grouped under their
        parent for organizational reference &mdash; each remains a fully independent tenant.
      </p>

      <div className="mt-6">
        <Table>
          <TableHead>
            <TableHeaderCell>Name</TableHeaderCell>
            <TableHeaderCell>Contact email</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
            <TableHeaderCell>Actions</TableHeaderCell>
          </TableHead>
          <TableBody>
            {companies.length === 0 && (
              <tr>
                <td colSpan={4}>
                  <EmptyState>No insurers yet.</EmptyState>
                </td>
              </tr>
            )}
            {topLevel.map((company) => (
              <Fragment key={company.id}>
                <CompanyRow company={company} isSubsidiary={false} />
                {(childrenByParent.get(company.id) ?? []).map((child) => (
                  <CompanyRow key={child.id} company={child} isSubsidiary />
                ))}
              </Fragment>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
