import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import PremiumFrequency


class PolicyholderCreateRequest(BaseModel):
    full_name: str
    email: EmailStr | None = None
    phone_number: str | None = None
    identification_number: str | None = None


class PolicyholderOut(BaseModel):
    id: uuid.UUID
    broker_id: uuid.UUID
    insurance_company_id: uuid.UUID
    full_name: str
    email: str | None
    phone_number: str | None
    identification_number: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PolicyCreateRequest(BaseModel):
    policyholder_id: uuid.UUID
    premium_amount_kobo: int = Field(gt=0)
    premium_frequency: PremiumFrequency
    start_date: date
    policy_type: str = "GENERIC"


class PolicyOut(BaseModel):
    id: uuid.UUID
    policyholder_id: uuid.UUID
    broker_id: uuid.UUID
    insurance_company_id: uuid.UUID
    policy_type: str
    premium_amount_kobo: int
    premium_frequency: str
    start_date: date
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InstallmentOut(BaseModel):
    id: uuid.UUID
    policy_id: uuid.UUID
    due_date: date
    amount_kobo: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReminderCreateRequest(BaseModel):
    installment_id: uuid.UUID


class ReminderOut(BaseModel):
    id: uuid.UUID
    installment_id: uuid.UUID
    broker_id: uuid.UUID
    sent_by: uuid.UUID
    channel: str
    status: str
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
