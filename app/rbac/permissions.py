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
        }
    ),
    Role.INSURANCE_COMPANY_ADMIN: frozenset(
        {
            Permission.MANAGE_OWN_INSURANCE_COMPANY,
            Permission.VIEW_OWN_ORG,
            Permission.SEND_REMINDER,
            Permission.MANAGE_BROKER_COMMISSION_CONFIG,
            Permission.VIEW_COMMISSION_CONFIGS,
            Permission.VIEW_PAYMENTS,
        }
    ),
    Role.BROKER_ADMIN: frozenset(
        {
            Permission.MANAGE_OWN_BROKER,
            Permission.MANAGE_BROKER_STAFF,
            Permission.VIEW_OWN_ORG,
            Permission.CREATE_POLICYHOLDER,
            Permission.CREATE_POLICY,
            Permission.VIEW_COMMISSION_CONFIGS,
            Permission.CREATE_PAYMENT,
            Permission.VIEW_PAYMENTS,
        }
    ),
    Role.BROKER_STAFF: frozenset(
        {
            Permission.VIEW_OWN_ORG,
            Permission.CREATE_POLICYHOLDER,
            Permission.CREATE_POLICY,
            Permission.CREATE_PAYMENT,
            Permission.VIEW_PAYMENTS,
        }
    ),
}


def role_has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]
