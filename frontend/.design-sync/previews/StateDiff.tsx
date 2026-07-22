import { StateDiff } from "@/components/audit/StateDiff";

export function PolicyUpdate() {
  return (
    <div className="p-4 max-w-lg">
      <StateDiff
        before={{
          status: "active",
          premium_amount_kobo: 4500000,
          premium_frequency: "monthly",
        }}
        after={{
          status: "lapsed",
          premium_amount_kobo: 4500000,
          premium_frequency: "monthly",
        }}
      />
    </div>
  );
}

export function BrokerApproval() {
  return (
    <div className="p-4 max-w-lg">
      <StateDiff
        before={{
          status: "pending",
          approved_by: null,
          approved_at: null,
        }}
        after={{
          status: "approved",
          approved_by: "admin@insureflow.com",
          approved_at: "2024-06-15T10:32:00Z",
        }}
      />
    </div>
  );
}

export function NewRecord() {
  return (
    <div className="p-4 max-w-lg">
      <StateDiff
        before={null}
        after={{
          name: "Apex Insurance Brokers Ltd",
          status: "pending",
          email: "admin@apexbrokers.com",
          created_at: "2024-06-15T09:00:00Z",
        }}
      />
    </div>
  );
}
