import { roleHasPermission, type Permission, type Role } from "./auth/rbac";
import type { IconName } from "@/components/ui/Icon";

export interface NavItem {
  href: string;
  label: string;
  section: "Admin" | "Broker" | "Payments" | "Insurer" | "Account";
  icon: IconName;
  /** Visible if the role holds this permission... */
  permission?: Permission;
  /** ...or, for items that don't map to a single permission (e.g.
   * reminders, which insureflow_admin never sees but has no dedicated
   * permission of its own), an explicit role allowlist. */
  roles?: Role[];
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard/admin/insurers", label: "Insurers", section: "Admin", icon: "shield", permission: "view_all_insurance_companies" },
  { href: "/dashboard/admin/brokers", label: "Brokers", section: "Admin", icon: "users", permission: "view_all_brokers" },
  { href: "/dashboard/admin/virtual-accounts", label: "Virtual Accounts", section: "Admin", icon: "credit-card", permission: "view_all_virtual_accounts" },
  { href: "/dashboard/admin/audit-log", label: "Audit Log", section: "Admin", icon: "file-text", permission: "view_audit_logs" },
  { href: "/dashboard/admin/anomalies", label: "Anomalies", section: "Admin", icon: "alert-triangle", permission: "view_audit_logs" },

  { href: "/dashboard/policyholders", label: "Policyholders", section: "Broker", icon: "users", roles: ["broker_admin", "broker_staff"] },
  { href: "/dashboard/policies", label: "Policies", section: "Broker", icon: "file-text", roles: ["broker_admin", "broker_staff"] },
  { href: "/dashboard/installments", label: "Installments", section: "Broker", icon: "clock", roles: ["broker_admin", "broker_staff"] },
  { href: "/dashboard/staff", label: "Staff", section: "Broker", icon: "users", permission: "manage_broker_staff" },
  { href: "/dashboard/virtual-account", label: "My Virtual Account", section: "Broker", icon: "credit-card", permission: "view_own_virtual_account" },

  { href: "/dashboard/policyholders", label: "Policyholders", section: "Insurer", icon: "users", roles: ["insurance_company_admin"] },
  { href: "/dashboard/policies", label: "Policies", section: "Insurer", icon: "file-text", roles: ["insurance_company_admin"] },

  { href: "/dashboard/payments", label: "Payments", section: "Payments", icon: "wallet", permission: "view_payments" },
  { href: "/dashboard/settlements", label: "Settlements", section: "Payments", icon: "arrow-up-right", permission: "view_settlements" },
  { href: "/dashboard/ledger", label: "Ledger", section: "Payments", icon: "file-text", permission: "view_ledger" },
  { href: "/dashboard/commission-config", label: "Commission Config", section: "Payments", icon: "trending-up", permission: "view_commission_configs" },

  {
    href: "/dashboard/reminders",
    label: "Reminders",
    section: "Insurer",
    icon: "bell",
    roles: ["insurance_company_admin", "broker_admin", "broker_staff"],
  },

  {
    href: "/dashboard/settings",
    label: "Settings",
    section: "Account",
    icon: "more-horizontal",
    roles: ["insurance_company_admin", "broker_admin", "broker_staff"],
  },
  {
    href: "/dashboard/support",
    label: "Support",
    section: "Account",
    icon: "inbox",
    roles: ["insurance_company_admin", "broker_admin", "broker_staff"],
  },
];

export function isNavItemVisible(item: NavItem, role: Role): boolean {
  if (item.roles) return item.roles.includes(role);
  if (item.permission) return roleHasPermission(role, item.permission);
  return false;
}

/** Coarse path-prefix -> required-permission gate used by proxy.ts for
 * redirect-away UX routing. Ownership-scoped detail routes (e.g. a specific
 * /admin/brokers/[id]) are deliberately NOT listed here -- they're reachable
 * by more than one role depending on record ownership, which proxy.ts can't
 * evaluate without a DB round-trip. Those pages must do their own
 * getSession()-based check server-side; this table only covers the
 * unambiguous, role-exclusive top-level pages the sidebar renders as links.
 */
export const PROTECTED_PATH_PERMISSIONS: { prefix: string; permission: Permission }[] = [
  ...NAV_ITEMS.filter((item): item is NavItem & { permission: Permission } =>
    Boolean(item.permission)
  ).map((item) => ({ prefix: item.href, permission: item.permission })),
  // The Policyholders/Policies list pages are now roles-gated (visible, read-
  // only, to both brokers and insurers), so they no longer appear in the
  // filter above -- but the create sub-routes are still permission-exclusive
  // to insurance_company_admin and need their own explicit entries here.
  { prefix: "/dashboard/policyholders/new", permission: "create_policyholder" },
  { prefix: "/dashboard/policies/new", permission: "create_policy" },
];
