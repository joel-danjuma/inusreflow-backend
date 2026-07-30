from enum import StrEnum


class Role(StrEnum):
    INSUREFLOW_ADMIN = "insureflow_admin"
    INSURANCE_COMPANY_ADMIN = "insurance_company_admin"
    BROKER_ADMIN = "broker_admin"
    BROKER_STAFF = "broker_staff"


class Permission(StrEnum):
    APPROVE_INSURANCE_COMPANY = "approve_insurance_company"
    APPROVE_BROKER = "approve_broker"
    VIEW_ALL_INSURANCE_COMPANIES = "view_all_insurance_companies"
    VIEW_ALL_BROKERS = "view_all_brokers"
    MANAGE_OWN_INSURANCE_COMPANY = "manage_own_insurance_company"
    MANAGE_OWN_BROKER = "manage_own_broker"
    MANAGE_BROKER_STAFF = "manage_broker_staff"
    VIEW_OWN_ORG = "view_own_org"
    CREATE_POLICYHOLDER = "create_policyholder"
    CREATE_POLICY = "create_policy"
    SEND_REMINDER = "send_reminder"
    ASSIGN_BROKER_TO_INSURER = "assign_broker_to_insurer"
    MANAGE_GLOBAL_COMMISSION_CONFIG = "manage_global_commission_config"
    MANAGE_BROKER_COMMISSION_CONFIG = "manage_broker_commission_config"
    VIEW_COMMISSION_CONFIGS = "view_commission_configs"
    CREATE_PAYMENT = "create_payment"
    VIEW_PAYMENTS = "view_payments"
    RETRY_SETTLEMENT_PAYOUT = "retry_settlement_payout"
    VIEW_ALL_VIRTUAL_ACCOUNTS = "view_all_virtual_accounts"
    MANAGE_VIRTUAL_ACCOUNTS = "manage_virtual_accounts"
    VIEW_OWN_VIRTUAL_ACCOUNT = "view_own_virtual_account"
    VIEW_SETTLEMENTS = "view_settlements"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    VIEW_LEDGER = "view_ledger"
    MANAGE_INSTALLMENT_REFERENCE = "manage_installment_reference"
    MANAGE_INSURANCE_COMPANY_HIERARCHY = "manage_insurance_company_hierarchy"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.INSUREFLOW_ADMIN: frozenset(
        {
            Permission.APPROVE_INSURANCE_COMPANY,
            Permission.APPROVE_BROKER,
            Permission.VIEW_ALL_INSURANCE_COMPANIES,
            Permission.VIEW_ALL_BROKERS,
            Permission.ASSIGN_BROKER_TO_INSURER,
            Permission.MANAGE_GLOBAL_COMMISSION_CONFIG,
            Permission.VIEW_COMMISSION_CONFIGS,
            Permission.VIEW_PAYMENTS,
            Permission.RETRY_SETTLEMENT_PAYOUT,
            Permission.VIEW_ALL_VIRTUAL_ACCOUNTS,
            Permission.MANAGE_VIRTUAL_ACCOUNTS,
            Permission.VIEW_SETTLEMENTS,
            Permission.VIEW_AUDIT_LOGS,
            Permission.VIEW_LEDGER,
            Permission.MANAGE_INSURANCE_COMPANY_HIERARCHY,
        }
    ),
    Role.INSURANCE_COMPANY_ADMIN: frozenset(
        {
            Permission.MANAGE_OWN_INSURANCE_COMPANY,
            Permission.VIEW_OWN_ORG,
            Permission.SEND_REMINDER,
            Permission.MANAGE_BROKER_COMMISSION_CONFIG,
            Permission.VIEW_COMMISSION_CONFIGS,
            Permission.CREATE_POLICYHOLDER,
            Permission.CREATE_POLICY,
            Permission.VIEW_PAYMENTS,
            Permission.VIEW_SETTLEMENTS,
            Permission.VIEW_LEDGER,
            Permission.MANAGE_INSTALLMENT_REFERENCE,
        }
    ),
    Role.BROKER_ADMIN: frozenset(
        {
            Permission.MANAGE_OWN_BROKER,
            Permission.MANAGE_BROKER_STAFF,
            Permission.VIEW_OWN_ORG,
            Permission.VIEW_COMMISSION_CONFIGS,
            Permission.CREATE_PAYMENT,
            Permission.VIEW_PAYMENTS,
            Permission.VIEW_OWN_VIRTUAL_ACCOUNT,
            Permission.MANAGE_INSTALLMENT_REFERENCE,
        }
    ),
    Role.BROKER_STAFF: frozenset(
        {
            Permission.VIEW_OWN_ORG,
            Permission.CREATE_PAYMENT,
            Permission.VIEW_PAYMENTS,
            Permission.MANAGE_INSTALLMENT_REFERENCE,
        }
    ),
}


def role_has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]
