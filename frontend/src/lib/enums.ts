/** Status string values copied verbatim from backend/app/models/enums.py. */

export type BadgeVariant =
  | "brand"
  | "neutral"
  | "gray"
  | "danger"
  | "success"
  | "warning"
  | "info"
  | "processing"
  | "dark";

export type OnboardingStatus = "pending" | "approved" | "rejected" | "suspended";
export const ONBOARDING_STATUS: Record<OnboardingStatus, { label: string; variant: BadgeVariant }> = {
  pending: { label: "Pending", variant: "warning" },
  approved: { label: "Approved", variant: "success" },
  rejected: { label: "Rejected", variant: "danger" },
  suspended: { label: "Suspended", variant: "dark" },
};

export type PolicyStatus = "active" | "lapsed" | "cancelled";
export const POLICY_STATUS: Record<PolicyStatus, { label: string; variant: BadgeVariant }> = {
  active: { label: "Active", variant: "success" },
  lapsed: { label: "Lapsed", variant: "warning" },
  cancelled: { label: "Cancelled", variant: "gray" },
};

export type InstallmentStatus = "due" | "overdue" | "paid" | "cancelled";
export const INSTALLMENT_STATUS: Record<InstallmentStatus, { label: string; variant: BadgeVariant }> = {
  due: { label: "Due", variant: "neutral" },
  overdue: { label: "Overdue", variant: "danger" },
  paid: { label: "Paid", variant: "success" },
  cancelled: { label: "Cancelled", variant: "gray" },
};

/**
 * mismatch/expired are Squad auto-refund cases -- distinct from a generic
 * failed initiate/charge -- so they get their own amber "refunded" treatment
 * rather than collapsing into the same red as `failed`.
 */
export type PaymentStatus = "initiated" | "success" | "mismatch" | "expired" | "failed";
export const PAYMENT_STATUS: Record<PaymentStatus, { label: string; variant: BadgeVariant }> = {
  initiated: { label: "In progress", variant: "brand" },
  success: { label: "Success", variant: "success" },
  mismatch: { label: "Mismatch (auto-refunded)", variant: "warning" },
  expired: { label: "Expired (auto-refunded)", variant: "warning" },
  failed: { label: "Failed", variant: "danger" },
};

export type SettlementPayoutStatus = "pending" | "success" | "failed";
export const SETTLEMENT_PAYOUT_STATUS: Record<
  SettlementPayoutStatus,
  { label: string; variant: BadgeVariant }
> = {
  pending: { label: "Pending", variant: "brand" },
  success: { label: "Success", variant: "success" },
  failed: { label: "Failed", variant: "danger" },
};

export type ReminderStatus = "queued" | "sent" | "failed";
export const REMINDER_STATUS: Record<ReminderStatus, { label: string; variant: BadgeVariant }> = {
  queued: { label: "Queued", variant: "neutral" },
  sent: { label: "Sent", variant: "success" },
  failed: { label: "Failed", variant: "danger" },
};

export type PremiumFrequency = "monthly" | "quarterly" | "annually";
export const PREMIUM_FREQUENCY_LABELS: Record<PremiumFrequency, string> = {
  monthly: "Monthly",
  quarterly: "Quarterly",
  annually: "Annually",
};

/** Ledger account types -- copied verbatim from
 * backend/app/models/ledger_account.py's ACCOUNT_TYPES tuple. */
export type LedgerAccountType =
  | "BROKER_CLEARING"
  | "GTBANK_REVENUE"
  | "INSUREFLOW_REVENUE"
  | "BROKER_COMMISSION"
  | "INSURER_PAYABLE"
  | "INSURER_SETTLED";

export const LEDGER_ACCOUNT_TYPE_LABELS: Record<LedgerAccountType, string> = {
  BROKER_CLEARING: "Broker Clearing",
  GTBANK_REVENUE: "GTBank Revenue",
  INSUREFLOW_REVENUE: "Insureflow Revenue",
  BROKER_COMMISSION: "Broker Commission",
  INSURER_PAYABLE: "Insurer Payable",
  INSURER_SETTLED: "Insurer Settled",
};
