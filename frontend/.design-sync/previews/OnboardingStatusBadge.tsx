import { OnboardingStatusBadge } from "@/components/badges/StatusBadge";

export function AllStatuses() {
  return (
    <div className="flex flex-wrap gap-2 p-4">
      <OnboardingStatusBadge status="pending" />
      <OnboardingStatusBadge status="approved" />
      <OnboardingStatusBadge status="rejected" />
      <OnboardingStatusBadge status="suspended" />
    </div>
  );
}
