import uuid
from datetime import date, datetime

from pydantic import BaseModel


class InsurerDashboardSummary(BaseModel):
    new_policies_count: int  # created in the current calendar month
    outstanding_premiums_kobo: int  # sum of due/overdue installment amounts
    total_brokers_count: int  # actively assigned brokers
    overdue_policies_count: int  # distinct policies with >=1 overdue installment


class OutstandingPolicyOut(BaseModel):
    policy_id: uuid.UUID
    policy_number: str
    customer_name: str
    broker_name: str
    premium_amount_kobo: int
    days_overdue: int
    last_payment_date: date | None
    reference_number: str | None


class RecentPolicyOut(BaseModel):
    policy_id: uuid.UUID
    policy_number: str
    customer_name: str
    broker_name: str
    policy_amount_kobo: int
    created_at: datetime


class BrokerPerformanceOut(BaseModel):
    broker_id: uuid.UUID
    broker_name: str
    policies_sold: int
    commission_earned_kobo: int


class LatestPaymentOut(BaseModel):
    id: uuid.UUID
    broker_name: str
    total_amount_kobo: int
    policies_paid: int
    payment_method: str
    status: str
    payment_date: datetime
