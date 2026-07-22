import { LogoutButton } from "@/components/layout/LogoutButton";

export function Default() {
  return (
    <div className="p-4 inline-flex items-center gap-4 bg-neutral-primary-soft rounded-base border border-border-default">
      <span className="text-sm text-body">Broker Admin</span>
      <LogoutButton />
    </div>
  );
}

export function InTopbarContext() {
  return (
    <div className="inline-flex items-center gap-6 px-6 py-3 bg-neutral-primary-soft rounded-base border border-border-default">
      <span className="text-sm font-semibold text-heading">Insureflow</span>
      <span className="text-sm text-body">Insurance Company Admin</span>
      <LogoutButton />
    </div>
  );
}
