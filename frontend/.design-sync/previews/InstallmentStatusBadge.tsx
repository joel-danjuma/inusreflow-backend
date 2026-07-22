import { InstallmentStatusBadge } from "@/components/badges/StatusBadge";

export function AllStatuses() {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      <InstallmentStatusBadge status="due" />
      <InstallmentStatusBadge status="overdue" />
      <InstallmentStatusBadge status="paid" />
      <InstallmentStatusBadge status="cancelled" />
    </div>
  );
}
