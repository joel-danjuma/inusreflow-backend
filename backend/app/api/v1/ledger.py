import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_tenant_id, require_permission
from app.models.broker_insurer_assignment import BrokerInsurerAssignment
from app.models.ledger_account import LedgerAccount
from app.models.ledger_entry import LedgerEntry
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission
from app.schemas.ledger import LedgerEntryOut

router = APIRouter(prefix="/ledger-entries", tags=["ledger"])


@router.get("", response_model=list[LedgerEntryOut])
async def list_ledger_entries(
    _: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_LEDGER))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    account_type: Annotated[str | None, Query()] = None,
    broker_id: Annotated[uuid.UUID | None, Query()] = None,
    insurance_company_id: Annotated[uuid.UUID | None, Query()] = None,
    posting_group_id: Annotated[uuid.UUID | None, Query()] = None,
    reference_type: Annotated[str | None, Query()] = None,
    reference_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(le=200)] = 50,
    offset: Annotated[int, Query()] = 0,
) -> list[LedgerEntryOut]:
    """VIEW_LEDGER is only granted to Insureflow Admin (cross-tenant,
    tenant_id is None, sees every account including platform-wide
    GTBANK_REVENUE/INSUREFLOW_REVENUE) and Insurance Company Admin (own
    tenant only). Tenant scoping lives on LedgerAccount, not LedgerEntry, so
    this requires a join; a broker-scoped account (BROKER_CLEARING/
    BROKER_COMMISSION) has no insurance_company_id of its own, so an
    Insurance Company Admin's own-tenant entries are the union of their
    directly-owned insurer accounts and their currently-assigned brokers'
    accounts.
    """
    stmt = select(LedgerEntry, LedgerAccount).join(
        LedgerAccount, LedgerEntry.ledger_account_id == LedgerAccount.id
    )
    if tenant_id is not None:
        own_broker_ids = select(BrokerInsurerAssignment.broker_id).where(
            BrokerInsurerAssignment.insurance_company_id == tenant_id,
            BrokerInsurerAssignment.is_active.is_(True),
        )
        stmt = stmt.where(
            or_(
                LedgerAccount.insurance_company_id == tenant_id,
                LedgerAccount.broker_id.in_(own_broker_ids),
            )
        )
    elif insurance_company_id is not None:
        stmt = stmt.where(LedgerAccount.insurance_company_id == insurance_company_id)
    if account_type is not None:
        stmt = stmt.where(LedgerAccount.account_type == account_type)
    if broker_id is not None:
        stmt = stmt.where(LedgerAccount.broker_id == broker_id)
    if posting_group_id is not None:
        stmt = stmt.where(LedgerEntry.posting_group_id == posting_group_id)
    if reference_type is not None:
        stmt = stmt.where(LedgerEntry.reference_type == reference_type)
    if reference_id is not None:
        stmt = stmt.where(LedgerEntry.reference_id == reference_id)
    stmt = stmt.order_by(LedgerEntry.created_at.desc()).limit(limit).offset(offset)

    rows = (await db.execute(stmt)).all()
    return [
        LedgerEntryOut(
            id=entry.id,
            ledger_account_id=entry.ledger_account_id,
            account_type=account.account_type,
            account_broker_id=account.broker_id,
            account_insurance_company_id=account.insurance_company_id,
            entry_type=entry.entry_type,
            amount_kobo=entry.amount_kobo,
            reference_type=entry.reference_type,
            reference_id=entry.reference_id,
            posting_group_id=entry.posting_group_id,
            created_at=entry.created_at,
        )
        for entry, account in rows
    ]
