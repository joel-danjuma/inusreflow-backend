import Link from "next/link";
import { apiFetch } from "@/lib/api/client";
import { getAuthToken } from "@/lib/auth/session";
import { Money } from "@/components/money/Money";
import { Badge } from "@/components/ui/Badge";
import {
  Table,
  TableHead,
  TableHeaderCell,
  TableBody,
  TableRow,
  TableCell,
  EmptyState,
} from "@/components/ui/Table";
import { LEDGER_ACCOUNT_TYPE_LABELS, type LedgerAccountType } from "@/lib/enums";
import type { components } from "@/lib/api/types";

type LedgerEntryOut = components["schemas"]["LedgerEntryOut"];

const ACCOUNT_TYPES = Object.keys(LEDGER_ACCOUNT_TYPE_LABELS) as LedgerAccountType[];

export default async function LedgerPage({
  searchParams,
}: {
  searchParams: Promise<{
    account_type?: string;
    posting_group_id?: string;
    reference_type?: string;
    reference_id?: string;
  }>;
}) {
  const {
    account_type: accountType,
    posting_group_id: postingGroupId,
    reference_type: referenceType,
    reference_id: referenceId,
  } = await searchParams;
  const token = await getAuthToken();
  const entries = await apiFetch<LedgerEntryOut[]>("/ledger-entries", {
    token,
    searchParams: {
      account_type: accountType,
      posting_group_id: postingGroupId,
      reference_type: referenceType,
      reference_id: referenceId,
    },
  });
  const isFiltered = Boolean(postingGroupId || referenceType);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-heading">Ledger</h1>
      <p className="mt-1 text-sm text-body">
        Every double-entry posting behind your payments and settlements &mdash; debits always
        balance credits within a posting group.
      </p>

      {isFiltered && (
        <div className="mt-4 flex items-center gap-2 rounded-base border border-border-brand-subtle bg-brand-softer px-4 py-2 text-sm text-fg-brand-strong">
          {postingGroupId ? (
            <>
              Filtered to posting group <code className="font-mono text-xs">{postingGroupId}</code>
            </>
          ) : (
            <>
              Filtered to {referenceType} <code className="font-mono text-xs">{referenceId}</code>
            </>
          )}
          <Link href="/dashboard/ledger" className="ml-auto font-medium hover:underline">
            Clear
          </Link>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          href="/dashboard/ledger"
          className={`rounded-default border px-3 py-1.5 text-sm font-medium transition-colors ${
            !accountType
              ? "border-border-brand bg-brand-softer text-fg-brand-strong"
              : "border-border-default text-body hover:bg-neutral-secondary-medium"
          }`}
        >
          All accounts
        </Link>
        {ACCOUNT_TYPES.map((type) => (
          <Link
            key={type}
            href={`/dashboard/ledger?account_type=${type}`}
            className={`rounded-default border px-3 py-1.5 text-sm font-medium transition-colors ${
              accountType === type
                ? "border-border-brand bg-brand-softer text-fg-brand-strong"
                : "border-border-default text-body hover:bg-neutral-secondary-medium"
            }`}
          >
            {LEDGER_ACCOUNT_TYPE_LABELS[type]}
          </Link>
        ))}
      </div>

      <div className="mt-6">
        <Table>
          <TableHead>
            <TableHeaderCell>Account</TableHeaderCell>
            <TableHeaderCell>Entry</TableHeaderCell>
            <TableHeaderCell>Amount</TableHeaderCell>
            <TableHeaderCell>Reference</TableHeaderCell>
            <TableHeaderCell>Posted</TableHeaderCell>
          </TableHead>
          <TableBody>
            {entries.length === 0 && (
              <tr>
                <td colSpan={5}>
                  <EmptyState>No ledger entries found.</EmptyState>
                </td>
              </tr>
            )}
            {entries.map((entry) => (
              <TableRow key={entry.id}>
                <TableCell header>
                  {LEDGER_ACCOUNT_TYPE_LABELS[entry.account_type as LedgerAccountType] ??
                    entry.account_type}
                </TableCell>
                <TableCell>
                  <Badge variant={entry.entry_type === "debit" ? "gray" : "brand"}>
                    {entry.entry_type}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Money kobo={entry.amount_kobo} />
                </TableCell>
                <TableCell>
                  <Link
                    href={`/dashboard/ledger?posting_group_id=${entry.posting_group_id}`}
                    className="text-fg-brand hover:underline"
                  >
                    {entry.reference_type}
                  </Link>
                </TableCell>
                <TableCell>{new Date(entry.created_at).toLocaleString("en-NG")}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
