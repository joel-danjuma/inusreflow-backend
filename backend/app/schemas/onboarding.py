import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class InsuranceCompanyOnboardRequest(BaseModel):
    name: str
    contact_email: EmailStr


class BrokerOnboardRequest(BaseModel):
    name: str
    contact_email: EmailStr
    bvn: str | None = None
    phone_number: str | None = None


class BrokerKybUpdateRequest(BaseModel):
    """Self-service KYB update -- both required, since Squad's virtual
    account creation needs them together (app/services/onboarding_service.py
    create_broker_virtual_account).
    """

    bvn: str
    phone_number: str


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
    parent_company_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InsuranceCompanyOnboardResult(BaseModel):
    """otp is shown exactly once — there is no email infra yet, so whoever
    submitted the onboarding form is responsible for using it to log in and
    relaying it to the org's contact if they aren't the same person.
    """

    company: InsuranceCompanyOut
    otp: str


class SetParentCompanyRequest(BaseModel):
    parent_company_id: uuid.UUID | None = None


class SettlementAccountSetRequest(BaseModel):
    bank_code: str
    account_number: str


class BrokerOut(BaseModel):
    id: uuid.UUID
    name: str
    contact_email: str
    status: str
    rejection_reason: str | None
    squad_va_number: str | None
    squad_va_bank: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BrokerOnboardResult(BaseModel):
    """Mirrors InsuranceCompanyOnboardResult -- otp shown exactly once."""

    broker: BrokerOut
    otp: str


class OtpResult(BaseModel):
    """Generic "an OTP was (re)issued, shown exactly once" response, reused
    for insurer/broker OTP reissue and for broker-staff creation -- all three
    are the same shape (nothing else to return), so one schema instead of
    three near-identical ones.
    """

    otp: str


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
    ended_at: datetime | None

    model_config = {"from_attributes": True}
