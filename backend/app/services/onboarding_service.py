import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import generate_otp, hash_password
from app.integrations.squad.client import SquadClient
from app.models.broker import Broker
from app.models.broker_insurer_assignment import BrokerInsurerAssignment
from app.models.enums import OnboardingStatus
from app.models.insurance_company import InsuranceCompany
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Role
from app.services.audit_service import record_audit_log


async def onboard_insurance_company(
    db: AsyncSession, *, name: str, contact_email: str
) -> tuple[InsuranceCompany, str]:
    company = InsuranceCompany(name=name, contact_email=contact_email)
    db.add(company)
    await db.flush()

    raw_otp, expires_at = generate_otp()
    admin_user = PlatformUser(
        email=contact_email,
        role=Role.INSURANCE_COMPANY_ADMIN.value,
        insurance_company_id=company.id,
        is_active=True,
        hashed_password=hash_password(raw_otp),
        must_change_password=True,
        otp_expires_at=expires_at,
    )
    db.add(admin_user)

    await record_audit_log(
        db,
        action="insurance_company.onboarded",
        entity_type="insurance_company",
        entity_id=company.id,
        after_state={"name": name, "contact_email": contact_email, "status": company.status},
    )
    await db.flush()
    return company, raw_otp


async def onboard_broker(
    db: AsyncSession,
    *,
    name: str,
    contact_email: str,
    bvn: str | None = None,
    phone_number: str | None = None,
) -> tuple[Broker, str]:
    broker = Broker(name=name, contact_email=contact_email, bvn=bvn, phone_number=phone_number)
    db.add(broker)
    await db.flush()

    raw_otp, expires_at = generate_otp()
    admin_user = PlatformUser(
        email=contact_email,
        role=Role.BROKER_ADMIN.value,
        broker_id=broker.id,
        is_active=True,
        hashed_password=hash_password(raw_otp),
        must_change_password=True,
        otp_expires_at=expires_at,
    )
    db.add(admin_user)

    await record_audit_log(
        db,
        action="broker.onboarded",
        entity_type="broker",
        entity_id=broker.id,
        after_state={"name": name, "contact_email": contact_email, "status": broker.status},
    )
    await db.flush()
    return broker, raw_otp


async def approve_insurance_company(
    db: AsyncSession, *, company_id: uuid.UUID, actor: PlatformUser
) -> InsuranceCompany:
    """No longer mints anything -- the admin's credential (an OTP) was already
    provisioned at onboard_insurance_company time. This is now purely a
    status flip; full access is separately gated on that OTP-derived password
    having been changed (app/core/deps.py require_full_access).
    """
    company = await db.get(InsuranceCompany, company_id)
    if company is None:
        raise NotFoundError("insurance company not found")
    if company.status != OnboardingStatus.PENDING.value:
        raise ConflictError(f"cannot approve insurance company in status {company.status}")

    before = {"status": company.status}
    company.status = OnboardingStatus.APPROVED.value
    company.approved_by = actor.id
    company.approved_at = datetime.now(UTC)

    await record_audit_log(
        db,
        action="insurance_company.approved",
        entity_type="insurance_company",
        entity_id=company.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={"status": company.status},
    )
    await db.flush()
    return company


async def reject_insurance_company(
    db: AsyncSession, *, company_id: uuid.UUID, reason: str, actor: PlatformUser
) -> InsuranceCompany:
    company = await db.get(InsuranceCompany, company_id)
    if company is None:
        raise NotFoundError("insurance company not found")
    if company.status != OnboardingStatus.PENDING.value:
        raise ConflictError(f"cannot reject insurance company in status {company.status}")

    before = {"status": company.status}
    company.status = OnboardingStatus.REJECTED.value
    company.rejection_reason = reason

    await record_audit_log(
        db,
        action="insurance_company.rejected",
        entity_type="insurance_company",
        entity_id=company.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={"status": company.status, "rejection_reason": reason},
    )
    await db.flush()
    return company


async def approve_broker(
    db: AsyncSession,
    *,
    broker_id: uuid.UUID,
    actor: PlatformUser,
    squad_client: SquadClient | None = None,
    beneficiary_account: str = "",
) -> Broker:
    """No longer mints a credential -- the admin's OTP was already
    provisioned at onboard_broker time. Still creates the Squad virtual
    account (a real side effect of approval, unrelated to credentials).
    """
    broker = await db.get(Broker, broker_id)
    if broker is None:
        raise NotFoundError("broker not found")
    if broker.status != OnboardingStatus.PENDING.value:
        raise ConflictError(f"cannot approve broker in status {broker.status}")

    before = {"status": broker.status}
    broker.status = OnboardingStatus.APPROVED.value
    broker.approved_by = actor.id
    broker.approved_at = datetime.now(UTC)

    # Create a permanent Business SVA for this broker if KYB fields are present.
    # If they're missing, approval still proceeds -- admin can create the VA later
    # via POST /virtual-accounts/{broker_id}.
    va_info: dict[str, str] = {}
    if squad_client is not None and broker.bvn and broker.phone_number:
        va = await squad_client.create_business_virtual_account(
            customer_identifier=str(broker.id),
            business_name=broker.name,
            mobile_num=broker.phone_number,
            bvn=broker.bvn,
            beneficiary_account=beneficiary_account,
        )
        broker.squad_va_number = va.account_number
        broker.squad_va_bank = va.bank
        broker.squad_customer_identifier = va.customer_identifier
        va_info = {"squad_va_number": va.account_number, "squad_va_bank": va.bank}

    await record_audit_log(
        db,
        action="broker.approved",
        entity_type="broker",
        entity_id=broker.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={"status": broker.status, **va_info},
    )
    await db.flush()
    return broker


async def create_broker_virtual_account(
    db: AsyncSession,
    *,
    broker_id: uuid.UUID,
    squad_client: SquadClient,
    beneficiary_account: str,
    actor: PlatformUser,
    bvn: str | None = None,
    phone_number: str | None = None,
) -> Broker:
    """Creates (or recreates) the permanent Business SVA for a broker.
    Called at approval time, via the admin VA management endpoint (no
    bvn/phone_number override -- reuses whatever's already stored), and via
    the broker's own self-service KYB update (both provided, persisted here
    before use -- this is the only place bvn/phone_number are ever written
    after onboarding, since onboarding no longer collects them upfront).
    """
    broker = await db.get(Broker, broker_id)
    if broker is None:
        raise NotFoundError("broker not found")
    if bvn is not None:
        broker.bvn = bvn
    if phone_number is not None:
        broker.phone_number = phone_number
    if not broker.bvn or not broker.phone_number:
        from app.core.exceptions import UnprocessableError

        raise UnprocessableError(
            "broker must have bvn and phone_number to create a virtual account"
        )

    before = {"squad_va_number": broker.squad_va_number}
    va = await squad_client.create_business_virtual_account(
        customer_identifier=str(broker.id),
        business_name=broker.name,
        mobile_num=broker.phone_number,
        bvn=broker.bvn,
        beneficiary_account=beneficiary_account,
    )
    broker.squad_va_number = va.account_number
    broker.squad_va_bank = va.bank
    broker.squad_customer_identifier = va.customer_identifier

    await record_audit_log(
        db,
        action="broker.virtual_account_created",
        entity_type="broker",
        entity_id=broker.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={
            "squad_va_number": broker.squad_va_number,
            "squad_va_bank": broker.squad_va_bank,
        },
    )
    await db.flush()
    return broker


async def reissue_insurance_company_otp(
    db: AsyncSession, *, company_id: uuid.UUID, actor: PlatformUser
) -> str:
    """Recovery path for a lost/expired OTP -- generates a fresh one for the
    company's one admin user. Unambiguous because onboard_insurance_company
    provisions exactly one insurance_company_admin per company.
    """
    company = await db.get(InsuranceCompany, company_id)
    if company is None:
        raise NotFoundError("insurance company not found")

    admin_user = await db.scalar(
        select(PlatformUser).where(PlatformUser.insurance_company_id == company_id)
    )
    if admin_user is None:
        raise ConflictError("no admin user provisioned for this insurance company")

    raw_otp, expires_at = generate_otp()
    admin_user.hashed_password = hash_password(raw_otp)
    admin_user.must_change_password = True
    admin_user.otp_expires_at = expires_at

    await record_audit_log(
        db,
        action="insurance_company.otp_reissued",
        entity_type="insurance_company",
        entity_id=company.id,
        actor_id=actor.id,
        actor_role=actor.role,
    )
    await db.flush()
    return raw_otp


async def reissue_broker_otp(db: AsyncSession, *, broker_id: uuid.UUID, actor: PlatformUser) -> str:
    """Recovery path for a lost/expired OTP, scoped to the broker's own
    broker_admin (the one user onboard_broker provisions). Does not cover a
    broker_staff member who loses their OTP before ever logging in -- there
    can be many staff per broker, so that case is out of scope here.
    """
    broker = await db.get(Broker, broker_id)
    if broker is None:
        raise NotFoundError("broker not found")

    admin_user = await db.scalar(
        select(PlatformUser).where(
            PlatformUser.broker_id == broker_id, PlatformUser.role == Role.BROKER_ADMIN.value
        )
    )
    if admin_user is None:
        raise ConflictError("no admin user provisioned for this broker")

    raw_otp, expires_at = generate_otp()
    admin_user.hashed_password = hash_password(raw_otp)
    admin_user.must_change_password = True
    admin_user.otp_expires_at = expires_at

    await record_audit_log(
        db,
        action="broker.otp_reissued",
        entity_type="broker",
        entity_id=broker.id,
        actor_id=actor.id,
        actor_role=actor.role,
    )
    await db.flush()
    return raw_otp


async def reject_broker(
    db: AsyncSession, *, broker_id: uuid.UUID, reason: str, actor: PlatformUser
) -> Broker:
    broker = await db.get(Broker, broker_id)
    if broker is None:
        raise NotFoundError("broker not found")
    if broker.status != OnboardingStatus.PENDING.value:
        raise ConflictError(f"cannot reject broker in status {broker.status}")

    before = {"status": broker.status}
    broker.status = OnboardingStatus.REJECTED.value
    broker.rejection_reason = reason

    await record_audit_log(
        db,
        action="broker.rejected",
        entity_type="broker",
        entity_id=broker.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={"status": broker.status, "rejection_reason": reason},
    )
    await db.flush()
    return broker


async def assign_broker_to_insurer(
    db: AsyncSession, *, broker_id: uuid.UUID, insurance_company_id: uuid.UUID, actor: PlatformUser
) -> BrokerInsurerAssignment:
    """Activates (or reactivates) one broker<->insurer pair. Many-to-many: a
    broker may have several simultaneously-active insurer assignments, so
    this never touches any of the broker's other pairs -- only the partial
    unique index on (broker_id, insurance_company_id) is enforced, not one
    active assignment overall. Idempotent: assigning an already-active pair
    is a no-op that returns the existing row rather than erroring or
    inserting a duplicate.
    """
    broker = await db.get(Broker, broker_id)
    if broker is None:
        raise NotFoundError("broker not found")
    company = await db.get(InsuranceCompany, insurance_company_id)
    if company is None:
        raise NotFoundError("insurance company not found")
    if broker.status != OnboardingStatus.APPROVED.value:
        raise ConflictError(f"cannot assign broker in status {broker.status}")
    if company.status != OnboardingStatus.APPROVED.value:
        raise ConflictError(f"cannot assign to insurance company in status {company.status}")

    existing = await db.scalar(
        select(BrokerInsurerAssignment).where(
            BrokerInsurerAssignment.broker_id == broker_id,
            BrokerInsurerAssignment.insurance_company_id == insurance_company_id,
        )
    )
    if existing is not None and existing.is_active:
        return existing

    if existing is not None:
        existing.is_active = True
        existing.ended_at = None
        assignment = existing
        action = "broker_insurer_assignment.reactivated"
    else:
        assignment = BrokerInsurerAssignment(
            broker_id=broker_id, insurance_company_id=insurance_company_id
        )
        db.add(assignment)
        action = "broker_insurer_assignment.created"
    await db.flush()

    await record_audit_log(
        db,
        action=action,
        entity_type="broker_insurer_assignment",
        entity_id=assignment.id,
        actor_id=actor.id,
        actor_role=actor.role,
        after_state={
            "broker_id": str(broker_id),
            "insurance_company_id": str(insurance_company_id),
        },
    )
    await db.flush()
    return assignment


async def unassign_broker_from_insurer(
    db: AsyncSession, *, broker_id: uuid.UUID, insurance_company_id: uuid.UUID, actor: PlatformUser
) -> BrokerInsurerAssignment:
    """Deactivates one specific (broker, insurer) pair, leaving every other
    active assignment either side has untouched -- the many-to-many-safe
    counterpart to assign_broker_to_insurer.
    """
    assignment = await db.scalar(
        select(BrokerInsurerAssignment).where(
            BrokerInsurerAssignment.broker_id == broker_id,
            BrokerInsurerAssignment.insurance_company_id == insurance_company_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
    )
    if assignment is None:
        raise NotFoundError("no active assignment for this broker/insurer pair")

    assignment.is_active = False
    assignment.ended_at = datetime.now(UTC)
    await db.flush()

    await record_audit_log(
        db,
        action="broker_insurer_assignment.deactivated",
        entity_type="broker_insurer_assignment",
        entity_id=assignment.id,
        actor_id=actor.id,
        actor_role=actor.role,
        after_state={
            "broker_id": str(broker_id),
            "insurance_company_id": str(insurance_company_id),
        },
    )
    await db.flush()
    return assignment


async def create_broker_staff_user(
    db: AsyncSession, *, broker_id: uuid.UUID, email: str, actor: PlatformUser
) -> tuple[PlatformUser, str]:
    """No org-approval gate applies here -- the broker is already approved by
    the time staff are created, so the OTP + forced password change is the
    only thing gating a new staff member (require_full_access).
    """
    raw_otp, expires_at = generate_otp()
    staff_user = PlatformUser(
        email=email,
        role=Role.BROKER_STAFF.value,
        broker_id=broker_id,
        is_active=True,
        hashed_password=hash_password(raw_otp),
        must_change_password=True,
        otp_expires_at=expires_at,
    )
    db.add(staff_user)
    await db.flush()

    await record_audit_log(
        db,
        action="platform_user.broker_staff_created",
        entity_type="platform_user",
        entity_id=staff_user.id,
        actor_id=actor.id,
        actor_role=actor.role,
        after_state={"email": email, "role": staff_user.role, "broker_id": str(broker_id)},
    )
    await db.flush()
    return staff_user, raw_otp


async def set_insurer_settlement_account(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    bank_code: str,
    account_number: str,
    squad_client: SquadClient,
    actor: PlatformUser,
) -> InsuranceCompany:
    """Confirms the insurer's payout destination via Squad's Account Lookup
    API before persisting it (PRD §8.6) -- settlement_account_name always
    ends up as whatever Squad's lookup returned, never hand-entered (see the
    settlement_* fields' docstring on InsuranceCompany). settlement_service
    fails closed (no payout) until this has been called at least once.
    """
    company = await db.get(InsuranceCompany, company_id)
    if company is None:
        raise NotFoundError("insurance company not found")

    lookup = await squad_client.lookup_payout_account(
        bank_code=bank_code, account_number=account_number
    )

    before = {
        "settlement_bank_code": company.settlement_bank_code,
        "settlement_account_number": company.settlement_account_number,
        "settlement_account_name": company.settlement_account_name,
    }
    company.settlement_bank_code = bank_code
    company.settlement_account_number = lookup.account_number
    company.settlement_account_name = lookup.account_name

    await record_audit_log(
        db,
        action="insurance_company.settlement_account_set",
        entity_type="insurance_company",
        entity_id=company.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={
            "settlement_bank_code": company.settlement_bank_code,
            "settlement_account_number": company.settlement_account_number,
            "settlement_account_name": company.settlement_account_name,
        },
    )
    await db.flush()
    return company


async def set_insurance_company_parent(
    db: AsyncSession,
    *,
    company_id: uuid.UUID,
    parent_company_id: uuid.UUID | None,
    actor: PlatformUser,
) -> InsuranceCompany:
    """Organizational grouping only (e.g. "Leadway Assurance Life" under
    parent "Leadway Assurance") -- never changes tenant scoping, RLS, or
    broker assignments for either company. Max depth 1: a parent must
    itself be top-level, matching the firm's own example of one parent with
    flat subsidiaries underneath, not nested groups.
    """
    company = await db.get(InsuranceCompany, company_id)
    if company is None:
        raise NotFoundError("insurance company not found")

    if parent_company_id is not None:
        if parent_company_id == company_id:
            raise ConflictError("an insurance company cannot be its own parent")
        parent = await db.get(InsuranceCompany, parent_company_id)
        if parent is None:
            raise NotFoundError("parent insurance company not found")
        if parent.parent_company_id is not None:
            raise ConflictError("parent_company_id must itself be a top-level company")
        # A company with its own subsidiaries can't itself become a
        # subsidiary -- that would hide a 2-level chain (grandchild -> this
        # company -> new parent) behind two individually-valid single links.
        has_children = await db.scalar(
            select(InsuranceCompany.id).where(InsuranceCompany.parent_company_id == company_id)
        )
        if has_children is not None:
            raise ConflictError(
                "a company with its own subsidiaries cannot itself become a subsidiary"
            )

    before = {
        "parent_company_id": str(company.parent_company_id) if company.parent_company_id else None
    }
    company.parent_company_id = parent_company_id

    await record_audit_log(
        db,
        action="insurance_company.parent_set",
        entity_type="insurance_company",
        entity_id=company.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={"parent_company_id": str(parent_company_id) if parent_company_id else None},
    )
    await db.flush()
    return company
