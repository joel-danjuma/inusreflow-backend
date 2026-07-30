import uuid
from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class CommissionConfigCreateRequest(BaseModel):
    scope: Literal["global", "insurance_company", "broker"]
    gtbank_rate_bps: int = Field(ge=0, le=10_000)
    insureflow_rate_bps: int = Field(ge=0, le=10_000)
    broker_rate_bps: int | None = Field(default=None, ge=0, le=10_000)
    insurance_company_id: uuid.UUID | None = None
    broker_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def check_scope_id_consistency(self) -> Self:
        if self.scope == "insurance_company" and self.insurance_company_id is None:
            raise ValueError("insurance_company_id is required for scope='insurance_company'")
        if self.scope == "broker" and self.broker_id is None:
            raise ValueError("broker_id is required for scope='broker'")
        return self


class CommissionConfigOut(BaseModel):
    id: uuid.UUID
    scope: str
    insurance_company_id: uuid.UUID | None
    broker_id: uuid.UUID | None
    gtbank_rate_bps: int
    insureflow_rate_bps: int
    broker_rate_bps: int | None
    effective_from: datetime
    effective_to: datetime | None
    created_by: uuid.UUID | None

    model_config = {"from_attributes": True}
