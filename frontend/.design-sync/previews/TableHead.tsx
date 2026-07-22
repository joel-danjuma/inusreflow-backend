import { Table, TableHead, TableRow, TableHeaderCell } from "@/components/ui/Table";

export function Default() {
  return (
    <div className="p-4">
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Policyholder</TableHeaderCell>
            <TableHeaderCell>Policy type</TableHeaderCell>
            <TableHeaderCell>Premium</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableRow>
        </TableHead>
      </Table>
    </div>
  );
}
