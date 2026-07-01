import uuid
from datetime import datetime

from pydantic import BaseModel


class PaymentCreateRequest(BaseModel):
    installment_id: uuid.UUID


class PaymentOut(BaseModel):
    id: uuid.UUID
    installment_id: uuid.UUID
    broker_id: uuid.UUID
    insurance_company_id: uuid.UUID
    amount_kobo: int
    status: str
    squad_transaction_ref: str
    squad_virtual_account_number: str | None
    squad_virtual_account_bank: str | None
    va_expires_at: datetime | None
    failure_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
