import { Table, TableBody, TableRow, TableCell } from "@/components/ui/Table";

export function Default() {
  return (
    <div className="p-4">
      <Table>
        <TableBody>
          <TableRow>
            <TableCell>POL-2024-001</TableCell>
            <TableCell>Amaka Okonkwo</TableCell>
            <TableCell>₦45,000</TableCell>
            <TableCell>Active</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>
  );
}
