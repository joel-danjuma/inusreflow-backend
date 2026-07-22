import { Table, TableHead, TableBody, TableRow, TableHeaderCell, EmptyState } from "@/components/ui/Table";

export function NoPolicies() {
  return (
    <div className="p-4">
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Policy ID</TableHeaderCell>
            <TableHeaderCell>Policyholder</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <EmptyState>No policies found. Add a policy to get started.</EmptyState>
        </TableBody>
      </Table>
    </div>
  );
}

export function NoPayments() {
  return (
    <div className="p-4">
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Reference</TableHeaderCell>
            <TableHeaderCell>Amount</TableHeaderCell>
            <TableHeaderCell>Date</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <EmptyState>No payments recorded yet.</EmptyState>
        </TableBody>
      </Table>
    </div>
  );
}
