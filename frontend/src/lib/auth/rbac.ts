/**
 * Hand-transcribed mirror of backend/app/rbac/permissions.py's
 * ROLE_PERMISSIONS matrix. UI-only (hide nav items/buttons the current
 * role's permission ceiling doesn't include) -- the backend remains the
 * sole enforcement point, since there is no shared package or runtime
 * introspection endpoint between backend/ and frontend/. Keep in sync by
 * hand whenever backend/app/rbac/permissions.py changes.
 */
export type Role =
  | "insureflow_admin"
  | "insurance_company_admin"
  | "broker_admin"
  | "broker_staff";

export type Permission =
  | "approve_insurance_company"
  | "approve_broker"
  | "view_all_insurance_companies"
  | "view_all_brokers"
  | "manage_own_insurance_company"
  | "manage_own_broker"
  | "manage_broker_staff"
  | "view_own_org"
  | "create_policyholder"
  | "create_policy"
  | "send_reminder"
  | "assign_broker_to_insurer"
  | "manage_global_commission_config"
  | "manage_broker_commission_config"
  | "view_commission_configs"
  | "create_payment"
  | "view_payments"
  | "retry_settlement_payout"
  | "view_all_virtual_accounts"
  | "manage_virtual_accounts"
  | "view_own_virtual_account"
  | "view_settlements"
  | "view_audit_logs"
  | "view_ledger"
  | "manage_installment_reference"
  | "manage_insurance_company_hierarchy";

export const ROLE_PERMISSIONS: Record<Role, ReadonlySet<Permission>> = {
  insureflow_admin: new Set([
    "approve_insurance_company",
    "approve_broker",
    "view_all_insurance_companies",
    "view_all_brokers",
    "assign_broker_to_insurer",
    "manage_global_commission_config",
    "view_commission_configs",
    "view_payments",
    "retry_settlement_payout",
    "view_all_virtual_accounts",
    "manage_virtual_accounts",
    "view_settlements",
    "view_audit_logs",
    "view_ledger",
    "manage_insurance_company_hierarchy",
  ]),
  insurance_company_admin: new Set([
    "manage_own_insurance_company",
    "view_own_org",
    "send_reminder",
    "manage_broker_commission_config",
    "view_commission_configs",
    "create_policyholder",
    "create_policy",
    "view_payments",
    "view_settlements",
    "view_ledger",
    "manage_installment_reference",
  ]),
  broker_admin: new Set([
    "manage_own_broker",
    "manage_broker_staff",
    "view_own_org",
    "view_commission_configs",
    "create_payment",
    "view_payments",
    "view_own_virtual_account",
    "manage_installment_reference",
  ]),
  broker_staff: new Set([
    "view_own_org",
    "create_payment",
    "view_payments",
    "manage_installment_reference",
  ]),
};

export function roleHasPermission(role: Role, permission: Permission): boolean {
  return ROLE_PERMISSIONS[role].has(permission);
}

export const ROLE_LABELS: Record<Role, string> = {
  insureflow_admin: "Insureflow Admin",
  insurance_company_admin: "Insurance Company Admin",
  broker_admin: "Broker Admin",
  broker_staff: "Broker Staff",
};
