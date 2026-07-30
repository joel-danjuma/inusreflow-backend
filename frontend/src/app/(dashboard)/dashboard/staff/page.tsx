import { getSession } from "@/lib/auth/session";
import { CreateStaffForm } from "@/components/forms/CreateStaffForm";
import { createBrokerStaff } from "./actions";

export default async function StaffPage() {
  const session = await getSession();
  const brokerId = session!.orgId!;

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="text-2xl font-semibold text-heading">Staff</h1>
      <p className="mt-1 text-sm text-body">
        Create a Broker Staff login for someone on your team. There&apos;s no email delivery yet,
        so copy the activation token and share it with them directly.
      </p>

      <div className="mt-6 rounded-base border border-border-default bg-neutral-primary-soft p-6 shadow-xs">
        <CreateStaffForm action={createBrokerStaff.bind(null, brokerId)} />
      </div>
    </div>
  );
}
