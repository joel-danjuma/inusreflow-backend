import { PolicyStatusBadge } from "@/components/badges/StatusBadge";

export function AllStatuses() {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      <PolicyStatusBadge status="active" />
      <PolicyStatusBadge status="lapsed" />
      <PolicyStatusBadge status="cancelled" />
    </div>
  );
}
