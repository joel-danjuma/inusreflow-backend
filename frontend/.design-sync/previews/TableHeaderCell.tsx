import { Table, TableHead, TableRow, TableHeaderCell } from "@/components/ui/Table";

export function Default() {
  return (
    <div className="p-4">
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Policy ID</TableHeaderCell>
            <TableHeaderCell>Policyholder</TableHeaderCell>
            <TableHeaderCell>Premium amount</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableRow>
        </TableHead>
      </Table>
    </div>
  );
}
