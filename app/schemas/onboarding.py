import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class InsuranceCompanyOnboardRequest(BaseModel):
    name: str
    contact_email: EmailStr


class BrokerOnboardRequest(BaseModel):
    name: str
    contact_email: EmailStr


class RejectRequest(BaseModel):
    reason: str


class InsuranceCompanyOut(BaseModel):
    id: uuid.UUID
    name: str
    contact_email: str
    status: str
    rejection_reason: str | None
    settlement_bank_code: str | None
    settlement_account_number: str | None
    settlement_account_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SettlementAccountSetRequest(BaseModel):
    bank_code: str
    account_number: str


class BrokerOut(BaseModel):
    id: uuid.UUID
    name: str
    contact_email: str
    status: str
    rejection_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalResult(BaseModel):
    """activation_token is shown exactly once — there is no email infra yet, so
    the approving admin is responsible for relaying it to the org's contact.
    """

    activation_token: str


class CreateBrokerStaffRequest(BaseModel):
    email: EmailStr


class AssignBrokerInsurerRequest(BaseModel):
    insurance_company_id: uuid.UUID


class BrokerInsurerAssignmentOut(BaseModel):
    id: uuid.UUID
    broker_id: uuid.UUID
    insurance_company_id: uuid.UUID
    is_active: bool
    assigned_at: datetime

    model_config = {"from_attributes": True}
