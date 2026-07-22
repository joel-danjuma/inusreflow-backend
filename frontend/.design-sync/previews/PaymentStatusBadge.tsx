import { PaymentStatusBadge } from "@/components/badges/StatusBadge";

export function AllStatuses() {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      <PaymentStatusBadge status="initiated" />
      <PaymentStatusBadge status="success" />
      <PaymentStatusBadge status="mismatch" />
      <PaymentStatusBadge status="expired" />
      <PaymentStatusBadge status="failed" />
    </div>
  );
}
