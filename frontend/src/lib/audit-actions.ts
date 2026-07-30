/** Full audit-log action vocabulary, copied verbatim from the
 * record_audit_log call sites across backend/app/services/*.py -- used to
 * populate the audit log filter dropdown rather than free text. */
export const AUDIT_ACTIONS = [
  "insurance_company.onboarded",
  "insurance_company.approved",
  "insurance_company.rejected",
  "insurance_company.settlement_account_set",
  "broker.onboarded",
  "broker.approved",
  "broker.rejected",
  "broker.virtual_account_created",
  "broker_insurer_assignment.created",
  "platform_user.broker_staff_created",
  "policyholder.created",
  "policy.created",
  "premium_installment.flagged_overdue",
  "reminder.created",
  "reminder.sent",
  "commission_config.changed",
  "payment.initiated",
  "payment.success",
  "payment.failed",
  "payment_batch.initiated",
  "payment_batch.success",
  "payment_batch.failed",
  "payment_batch.anomaly_flagged",
  "webhook_event.processed",
  "webhook_event.rejected",
  "settlement_payout.failed",
  "settlement_payout.reconciled",
  "settlement_payout.reconciliation_mismatch",
] as const;

export const AUDIT_ENTITY_TYPES = [
  "insurance_company",
  "broker",
  "broker_insurer_assignment",
  "platform_user",
  "policyholder",
  "policy",
  "premium_installment",
  "reminder",
  "commission_config",
  "payment",
  "payment_batch",
  "webhook_event",
  "settlement_payout",
] as const;

export const ANOMALY_ACTION = "payment_batch.anomaly_flagged";
