import { ReminderStatusBadge } from "@/components/badges/StatusBadge";

export function AllStatuses() {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      <ReminderStatusBadge status="queued" />
      <ReminderStatusBadge status="sent" />
      <ReminderStatusBadge status="failed" />
    </div>
  );
}
