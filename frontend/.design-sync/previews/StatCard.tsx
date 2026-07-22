import { StatCard } from "@/components/dashboard/StatCard";

export function Default() {
  return (
    <div className="grid grid-cols-2 gap-4 p-4">
      <StatCard label="Total premiums collected" value="₦2,450,000" hint="This month" />
      <StatCard label="Active policies" value="142" hint="Across all brokers" />
      <StatCard label="Pending installments" value="23" hint="Due in the next 7 days" />
      <StatCard label="Settlement amount" value="₦1,890,000" hint="Pending disbursement" />
    </div>
  );
}

export function WithoutHint() {
  return (
    <div className="grid grid-cols-3 gap-4 p-4">
      <StatCard label="Brokers" value="8" />
      <StatCard label="Policyholders" value="314" />
      <StatCard label="Overdue" value="7" />
    </div>
  );
}
