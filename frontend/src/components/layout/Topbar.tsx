import { ROLE_LABELS, type Role } from "@/lib/auth/rbac";
import { LogoutButton } from "./LogoutButton";

export function Topbar({ role, orgName }: { role: Role; orgName: string | null }) {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-border-default bg-neutral-primary-soft px-6">
      <span className="font-display text-lg font-semibold tracking-tight text-heading">
        Insure<span className="text-fg-brand">flow</span>
      </span>
      <div className="flex items-center gap-4">
        <span className="text-sm text-body">{orgName ?? ROLE_LABELS[role]}</span>
        <LogoutButton />
      </div>
    </header>
  );
}
