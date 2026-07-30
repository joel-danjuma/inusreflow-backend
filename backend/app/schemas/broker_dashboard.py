import uuid
from datetime import date

from pydantic import BaseModel


class MonthlyTrendPoint(BaseModel):
    month: str  # "YYYY-MM"
    amount_kobo: int


class BrokerDashboardSummary(BaseModel):
    total_premiums_collected_kobo: int
    total_premiums_this_month_kobo: int
    total_commission_kobo: int
    # active policies / total policies * 100 -- no historical churn tracking
    # exists yet, so this is a point-in-time proxy, not a cohort calculation.
    client_retention_rate: float
    active_clients_count: int
    monthly_trends: list[MonthlyTrendPoint]


class PortfolioItemOut(BaseModel):
    policyholder_id: uuid.UUID
    client_name: str
    policy_id: uuid.UUID
    policy_type: str
    policy_status: str
    premium_amount_kobo: int
    next_installment_id: uuid.UUID | None
    payment_status: str
    next_payment_date: date | None
    next_payment_reference_number: str | None


class BrokerPortfolioPage(BaseModel):
    items: list[PortfolioItemOut]
    total: int
    page: int
    per_page: int
