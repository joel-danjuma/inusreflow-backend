import uuid
from datetime import datetime

from pydantic import BaseModel


class PaymentBatchCreateRequest(BaseModel):
    installment_ids: list[uuid.UUID]


class PaymentBatchItemOut(BaseModel):
    id: uuid.UUID
    installment_id: uuid.UUID
    amount_kobo: int

    model_config = {"from_attributes": True}


class PaymentBatchOut(BaseModel):
    id: uuid.UUID
    broker_id: uuid.UUID
    insurance_company_id: uuid.UUID
    total_amount_kobo: int
    item_count: int
    status: str
    squad_transaction_ref: str
    squad_virtual_account_number: str | None
    squad_virtual_account_bank: str | None
    va_expires_at: datetime | None
    failure_reason: str | None
    created_at: datetime
    items: list[PaymentBatchItemOut]

    model_config = {"from_attributes": True}


class BulkPaymentResolvedRow(BaseModel):
    row_number: int
    installment_id: uuid.UUID
    reference_number: str
    amount_kobo: int
    policy_id: uuid.UUID


class BulkPaymentUnmatchedRow(BaseModel):
    row_number: int
    reference_number: str | None
    reason: str


class BulkPaymentFileResolution(BaseModel):
    total_rows: int
    matched: list[BulkPaymentResolvedRow]
    unmatched: list[BulkPaymentUnmatchedRow]
    file_error: str | None
