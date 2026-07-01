import uuid
from datetime import datetime

from pydantic import BaseModel


class SettlementPayoutOut(BaseModel):
    id: uuid.UUID
    insurance_company_id: uuid.UUID
    source_type: str
    source_id: uuid.UUID
    amount_kobo: int
    status: str
    squad_transfer_ref: str
    attempt_number: int
    previous_attempt_id: uuid.UUID | None
    failure_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
