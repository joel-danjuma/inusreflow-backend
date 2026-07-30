import uuid
from datetime import datetime

from pydantic import BaseModel


class LedgerAccountOut(BaseModel):
    id: uuid.UUID
    account_type: str
    insurance_company_id: uuid.UUID | None
    broker_id: uuid.UUID | None

    model_config = {"from_attributes": True}


class LedgerEntryOut(BaseModel):
    id: uuid.UUID
    ledger_account_id: uuid.UUID
    account_type: str
    account_broker_id: uuid.UUID | None
    account_insurance_company_id: uuid.UUID | None
    entry_type: str
    amount_kobo: int
    reference_type: str
    reference_id: uuid.UUID
    posting_group_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
