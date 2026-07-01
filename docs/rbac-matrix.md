# RBAC Matrix

Generated from `app/rbac/permissions.py`'s `ROLE_PERMISSIONS` via `scripts/generate_rbac_matrix.py` (`make rbac-matrix`) — do not hand-edit.

| Permission | insureflow_admin | insurance_company_admin | broker_admin | broker_staff |
|---|---|---|---|---|
| `approve_insurance_company` | ✅ |  |  |  |
| `approve_broker` | ✅ |  |  |  |
| `view_all_insurance_companies` | ✅ |  |  |  |
| `view_all_brokers` | ✅ |  |  |  |
| `manage_own_insurance_company` |  | ✅ |  |  |
| `manage_own_broker` |  |  | ✅ |  |
| `manage_broker_staff` |  |  | ✅ |  |
| `view_own_org` |  | ✅ | ✅ | ✅ |
| `create_policyholder` |  |  | ✅ | ✅ |
| `create_policy` |  |  | ✅ | ✅ |
| `send_reminder` |  | ✅ |  |  |
| `assign_broker_to_insurer` | ✅ |  |  |  |
| `manage_global_commission_config` | ✅ |  |  |  |
| `manage_broker_commission_config` |  | ✅ |  |  |
| `view_commission_configs` | ✅ | ✅ | ✅ |  |
| `create_payment` |  |  | ✅ | ✅ |
| `view_payments` | ✅ | ✅ | ✅ | ✅ |
| `retry_settlement_payout` | ✅ |  |  |  |
