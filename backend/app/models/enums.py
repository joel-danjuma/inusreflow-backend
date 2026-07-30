from enum import StrEnum


class OnboardingStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class SettlementMode(StrEnum):
    REAL_TIME = "real_time"
    SCHEDULED = "scheduled"


class PolicyStatus(StrEnum):
    ACTIVE = "active"
    LAPSED = "lapsed"
    CANCELLED = "cancelled"


class PremiumFrequency(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class InstallmentStatus(StrEnum):
    DUE = "due"
    OVERDUE = "overdue"
    PAID = "paid"
    CANCELLED = "cancelled"


class ReminderChannel(StrEnum):
    EMAIL = "email"


class ReminderStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class PaymentStatus(StrEnum):
    """A Payment starts INITIATED (a Dynamic Virtual Account has been minted
    and is awaiting a transfer) and resolves to exactly one terminal state —
    see docs/adr/0004-squad-virtual-account-collection.md. MISMATCH/EXPIRED
    are distinct from FAILED because Squad auto-refunds the sender in those
    two cases, whereas FAILED covers everything else (e.g. our own initiate
    call erroring before a VA was even created).
    """

    INITIATED = "initiated"
    SUCCESS = "success"
    MISMATCH = "mismatch"
    EXPIRED = "expired"
    FAILED = "failed"


class WebhookProcessingStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    REJECTED = "rejected"
    FAILED = "failed"


class SettlementPayoutStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
