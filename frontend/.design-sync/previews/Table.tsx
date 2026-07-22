import { Table, TableHead, TableBody, TableRow, TableHeaderCell, TableCell } from "@/components/ui/Table";

export function PolicyTable() {
  return (
    <div className="p-4">
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Policy ID</TableHeaderCell>
            <TableHeaderCell>Policyholder</TableHeaderCell>
            <TableHeaderCell>Type</TableHeaderCell>
            <TableHeaderCell>Premium</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>POL-2024-001</TableCell>
            <TableCell>Amaka Okonkwo</TableCell>
            <TableCell>Motor</TableCell>
            <TableCell>₦45,000/yr</TableCell>
            <TableCell>Active</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>POL-2024-002</TableCell>
            <TableCell>Chidi Nwosu</TableCell>
            <TableCell>Life</TableCell>
            <TableCell>₦120,000/yr</TableCell>
            <TableCell>Active</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>POL-2024-003</TableCell>
            <TableCell>Ngozi Adeyemi</TableCell>
            <TableCell>Health</TableCell>
            <TableCell>₦85,000/yr</TableCell>
            <TableCell>Lapsed</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  );
}

export function PaymentTable() {
  return (
    <div className="p-4">
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Reference</TableHeaderCell>
            <TableHeaderCell>Amount</TableHeaderCell>
            <TableHeaderCell>Date</TableHeaderCell>
            <TableHeaderCell>Status</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>PAY-20240101-001</TableCell>
            <TableCell>₦45,000</TableCell>
            <TableCell>1 Jan 2024</TableCell>
            <TableCell>Success</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>PAY-20240201-002</TableCell>
            <TableCell>₦45,000</TableCell>
            <TableCell>1 Feb 2024</TableCell>
            <TableCell>In progress</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  );
}
