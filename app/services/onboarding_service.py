import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import generate_activation_token
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
) -> InsuranceCompany:
    company = InsuranceCompany(name=name, contact_email=contact_email)
    db.add(company)
    await db.flush()

    admin_user = PlatformUser(
        email=contact_email,
        role=Role.INSURANCE_COMPANY_ADMIN.value,
        insurance_company_id=company.id,
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
    return company


async def onboard_broker(db: AsyncSession, *, name: str, contact_email: str) -> Broker:
    broker = Broker(name=name, contact_email=contact_email)
    db.add(broker)
    await db.flush()

    admin_user = PlatformUser(
        email=contact_email,
        role=Role.BROKER_ADMIN.value,
        broker_id=broker.id,
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
    return broker


async def approve_insurance_company(
    db: AsyncSession, *, company_id: uuid.UUID, actor: PlatformUser
) -> tuple[InsuranceCompany, str]:
    company = await db.get(InsuranceCompany, company_id)
    if company is None:
        raise NotFoundError("insurance company not found")
    if company.status != OnboardingStatus.PENDING.value:
        raise ConflictError(f"cannot approve insurance company in status {company.status}")

    admin_user = await db.scalar(
        select(PlatformUser).where(PlatformUser.insurance_company_id == company_id)
    )
    if admin_user is None:
        raise ConflictError("no admin user provisioned for this insurance company")

    before = {"status": company.status}
    company.status = OnboardingStatus.APPROVED.value
    company.approved_by = actor.id
    company.approved_at = datetime.now(UTC)

    raw_token, token_hash, expires_at = generate_activation_token()
    admin_user.activation_token_hash = token_hash
    admin_user.activation_token_expires_at = expires_at

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
    return company, raw_token


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
    db: AsyncSession, *, broker_id: uuid.UUID, actor: PlatformUser
) -> tuple[Broker, str]:
    broker = await db.get(Broker, broker_id)
    if broker is None:
        raise NotFoundError("broker not found")
    if broker.status != OnboardingStatus.PENDING.value:
        raise ConflictError(f"cannot approve broker in status {broker.status}")

    admin_user = await db.scalar(select(PlatformUser).where(PlatformUser.broker_id == broker_id))
    if admin_user is None:
        raise ConflictError("no admin user provisioned for this broker")

    before = {"status": broker.status}
    broker.status = OnboardingStatus.APPROVED.value
    broker.approved_by = actor.id
    broker.approved_at = datetime.now(UTC)

    raw_token, token_hash, expires_at = generate_activation_token()
    admin_user.activation_token_hash = token_hash
    admin_user.activation_token_expires_at = expires_at

    await record_audit_log(
        db,
        action="broker.approved",
        entity_type="broker",
        entity_id=broker.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={"status": broker.status},
    )
    await db.flush()
    return broker, raw_token


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
    """Links an approved broker to an approved insurer. A broker may only
    have one active assignment at a time (see the partial unique constraint
    on broker_insurer_assignments) — assigning a new insurer ends the
    current one rather than erroring, matching the many-to-many-ready model
    where a broker can be reassigned over time.
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

    current = await db.scalar(
        select(BrokerInsurerAssignment).where(
            BrokerInsurerAssignment.broker_id == broker_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
    )
    before = None
    if current is not None:
        before = {"insurance_company_id": str(current.insurance_company_id)}
        current.is_active = False
        current.ended_at = datetime.now(UTC)

    assignment = BrokerInsurerAssignment(
        broker_id=broker_id, insurance_company_id=insurance_company_id
    )
    db.add(assignment)
    await db.flush()

    await record_audit_log(
        db,
        action="broker_insurer_assignment.created",
        entity_type="broker_insurer_assignment",
        entity_id=assignment.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
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
    staff_user = PlatformUser(
        email=email,
        role=Role.BROKER_STAFF.value,
        broker_id=broker_id,
    )
    db.add(staff_user)
    await db.flush()

    raw_token, token_hash, expires_at = generate_activation_token()
    staff_user.activation_token_hash = token_hash
    staff_user.activation_token_expires_at = expires_at

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
    return staff_user, raw_token


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
