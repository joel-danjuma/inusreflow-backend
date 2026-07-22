import { PaymentRemindersBanner } from "@/components/dashboard/PaymentRemindersBanner";

export function WithOverdueItems() {
  return (
    <div className="p-4 max-w-xl">
      <PaymentRemindersBanner overdueCount={3} />
    </div>
  );
}

export function ManyOverdue() {
  return (
    <div className="p-4 max-w-xl">
      <PaymentRemindersBanner overdueCount={12} />
    </div>
  );
}
