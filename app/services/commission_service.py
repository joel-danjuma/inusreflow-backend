import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.models.commission_config import CommissionConfig
from app.models.platform_user import PlatformUser
from app.services.audit_service import record_audit_log
from app.services.ledger.rounding import RoundingStrategy, get_rounding_strategy


async def resolve_commission_config(
    db: AsyncSession,
    *,
    broker_id: uuid.UUID,
    insurance_company_id: uuid.UUID,
    as_of: datetime | None = None,
) -> CommissionConfig:
    """Resolves broker -> insurance_company -> global, most-specific-wins,
    filtered to whichever row was active at `as_of` (defaults to now). The
    global row is a hard seed-data invariant (see the Phase 3 migration) --
    if it's ever missing that's a deployment bug, not a recoverable case.
    """
    moment = as_of or datetime.now(UTC)

    broker_config = await db.scalar(
        select(CommissionConfig).where(
            CommissionConfig.scope == "broker",
            CommissionConfig.broker_id == broker_id,
            CommissionConfig.effective_from <= moment,
            or_(CommissionConfig.effective_to.is_(None), CommissionConfig.effective_to > moment),
        )
    )
    if broker_config is not None:
        return broker_config

    insurer_config = await db.scalar(
        select(CommissionConfig).where(
            CommissionConfig.scope == "insurance_company",
            CommissionConfig.insurance_company_id == insurance_company_id,
            CommissionConfig.effective_from <= moment,
            or_(CommissionConfig.effective_to.is_(None), CommissionConfig.effective_to > moment),
        )
    )
    if insurer_config is not None:
        return insurer_config

    global_config = await db.scalar(
        select(CommissionConfig).where(
            CommissionConfig.scope == "global",
            CommissionConfig.effective_from <= moment,
            or_(CommissionConfig.effective_to.is_(None), CommissionConfig.effective_to > moment),
        )
    )
    if global_config is not None:
        return global_config

    raise ConflictError("no commission config resolved, including global -- seed data missing")


async def set_commission_config(
    db: AsyncSession,
    *,
    actor: PlatformUser,
    scope: str,
    gtbank_rate_bps: int,
    insureflow_rate_bps: int,
    broker_rate_bps: int | None = None,
    insurance_company_id: uuid.UUID | None = None,
    broker_id: uuid.UUID | None = None,
) -> CommissionConfig:
    """Never updates a rate row in place (PRD §9) -- closes whatever row is
    currently active for this exact scope key (effective_to = now()) and
    inserts a fresh one, so a Payment's locked-in commission_config_id keeps
    resolving to the exact historical rates forever.
    """
    if scope == "insurance_company" and insurance_company_id is None:
        raise ValueError("insurance_company_id is required for scope='insurance_company'")
    if scope == "broker" and broker_id is None:
        raise ValueError("broker_id is required for scope='broker'")

    id_column, id_value = {
        "global": (None, None),
        "insurance_company": (CommissionConfig.insurance_company_id, insurance_company_id),
        "broker": (CommissionConfig.broker_id, broker_id),
    }[scope]

    stmt = select(CommissionConfig).where(
        CommissionConfig.scope == scope, CommissionConfig.effective_to.is_(None)
    )
    if id_column is not None:
        stmt = stmt.where(id_column == id_value)
    current = await db.scalar(stmt)

    now = datetime.now(UTC)
    before = None
    if current is not None:
        before = {
            "gtbank_rate_bps": current.gtbank_rate_bps,
            "insureflow_rate_bps": current.insureflow_rate_bps,
            "broker_rate_bps": current.broker_rate_bps,
        }
        current.effective_to = now

    new_config = CommissionConfig(
        scope=scope,
        insurance_company_id=insurance_company_id if scope == "insurance_company" else None,
        broker_id=broker_id if scope == "broker" else None,
        gtbank_rate_bps=gtbank_rate_bps,
        insureflow_rate_bps=insureflow_rate_bps,
        broker_rate_bps=broker_rate_bps,
        effective_from=now,
        created_by=actor.id,
    )
    db.add(new_config)
    await db.flush()

    await record_audit_log(
        db,
        action="commission_config.changed",
        entity_type="commission_config",
        entity_id=new_config.id,
        actor_id=actor.id,
        actor_role=actor.role,
        before_state=before,
        after_state={
            "scope": scope,
            "gtbank_rate_bps": gtbank_rate_bps,
            "insureflow_rate_bps": insureflow_rate_bps,
            "broker_rate_bps": broker_rate_bps,
        },
    )
    await db.flush()
    return new_config


@dataclass(frozen=True)
class CommissionSplit:
    gross_amount_kobo: int
    gtbank_kobo: int
    insureflow_kobo: int
    broker_kobo: int
    insurer_payable_kobo: int


def calculate_split(
    gross_amount_kobo: int,
    config: CommissionConfig,
    rounding_strategy: RoundingStrategy | None = None,
) -> CommissionSplit:
    """Floors each party's bps share independently, then routes whatever
    kobo that flooring dropped through the pluggable rounding strategy.
    Asserts the four shares sum exactly back to gross before returning --
    this is the invariant the financial-invariant test suite exercises.
    """
    strategy = rounding_strategy or get_rounding_strategy()

    broker_rate_bps = config.broker_rate_bps or 0
    total_bps = config.gtbank_rate_bps + config.insureflow_rate_bps + broker_rate_bps
    if not 0 <= total_bps <= 10_000:
        raise ValueError(f"commission rates sum to {total_bps}bps, must be within [0, 10000]")
    insurer_bps = 10_000 - total_bps

    gtbank_kobo = gross_amount_kobo * config.gtbank_rate_bps // 10_000
    insureflow_kobo = gross_amount_kobo * config.insureflow_rate_bps // 10_000
    broker_kobo = gross_amount_kobo * broker_rate_bps // 10_000
    insurer_payable_kobo = gross_amount_kobo * insurer_bps // 10_000

    remainder_kobo = gross_amount_kobo - (
        gtbank_kobo + insureflow_kobo + broker_kobo + insurer_payable_kobo
    )
    gtbank_kobo, insureflow_kobo, broker_kobo, insurer_payable_kobo = strategy.allocate_remainder(
        remainder_kobo=remainder_kobo,
        gtbank_kobo=gtbank_kobo,
        insureflow_kobo=insureflow_kobo,
        broker_kobo=broker_kobo,
        insurer_payable_kobo=insurer_payable_kobo,
    )

    split = CommissionSplit(
        gross_amount_kobo=gross_amount_kobo,
        gtbank_kobo=gtbank_kobo,
        insureflow_kobo=insureflow_kobo,
        broker_kobo=broker_kobo,
        insurer_payable_kobo=insurer_payable_kobo,
    )
    assert (
        split.gtbank_kobo + split.insureflow_kobo + split.broker_kobo + split.insurer_payable_kobo
        == gross_amount_kobo
    )
    return split
