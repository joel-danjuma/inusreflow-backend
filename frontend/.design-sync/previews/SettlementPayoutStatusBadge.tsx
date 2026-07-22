import { SettlementPayoutStatusBadge } from "@/components/badges/StatusBadge";

export function AllStatuses() {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      <SettlementPayoutStatusBadge status="pending" />
      <SettlementPayoutStatusBadge status="success" />
      <SettlementPayoutStatusBadge status="failed" />
    </div>
  );
}
