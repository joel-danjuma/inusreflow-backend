import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from "@/components/ui/Table";

export function Default() {
  return (
    <div className="p-4">
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Name</TableHeaderCell>
            <TableHeaderCell>Amount</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>Amaka Okonkwo</TableCell>
            <TableCell>₦45,000</TableCell>
            <TableCell>Paid</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Chidi Nwosu</TableCell>
            <TableCell>₦120,000</TableCell>
            <TableCell>Due</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>Ngozi Adeyemi</TableCell>
            <TableCell>₦85,000</TableCell>
            <TableCell>Overdue</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  );
}
