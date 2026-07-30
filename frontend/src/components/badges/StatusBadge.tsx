import { Badge } from "@/components/ui/Badge";
import {
  INSTALLMENT_STATUS,
  ONBOARDING_STATUS,
  PAYMENT_STATUS,
  POLICY_STATUS,
  REMINDER_STATUS,
  SETTLEMENT_PAYOUT_STATUS,
  type InstallmentStatus,
  type OnboardingStatus,
  type PaymentStatus,
  type PolicyStatus,
  type ReminderStatus,
  type SettlementPayoutStatus,
} from "@/lib/enums";

export function OnboardingStatusBadge({ status }: { status: OnboardingStatus }) {
  const { label, variant } = ONBOARDING_STATUS[status];
  return <Badge variant={variant}>{label}</Badge>;
}

export function PolicyStatusBadge({ status }: { status: PolicyStatus }) {
  const { label, variant } = POLICY_STATUS[status];
  return <Badge variant={variant}>{label}</Badge>;
}

export function InstallmentStatusBadge({ status }: { status: InstallmentStatus }) {
  const { label, variant } = INSTALLMENT_STATUS[status];
  return <Badge variant={variant}>{label}</Badge>;
}

export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  const { label, variant } = PAYMENT_STATUS[status];
  return <Badge variant={variant}>{label}</Badge>;
}

export function SettlementPayoutStatusBadge({ status }: { status: SettlementPayoutStatus }) {
  const { label, variant } = SETTLEMENT_PAYOUT_STATUS[status];
  return <Badge variant={variant}>{label}</Badge>;
}

export function ReminderStatusBadge({ status }: { status: ReminderStatus }) {
  const { label, variant } = REMINDER_STATUS[status];
  return <Badge variant={variant}>{label}</Badge>;
}
