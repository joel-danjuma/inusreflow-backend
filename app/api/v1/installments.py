import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user, get_tenant_id
from app.models.enums import InstallmentStatus
from app.models.platform_user import PlatformUser
from app.models.policy import Policy
from app.models.premium_installment import PremiumInstallment
from app.rbac.permissions import Role
from app.schemas.policy import InstallmentOut

router = APIRouter(prefix="/installments", tags=["installments"])


@router.get("", response_model=list[InstallmentOut])
async def list_installments(
    actor: Annotated[PlatformUser, Depends(get_current_user)],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[InstallmentStatus | None, Query(alias="status")] = None,
) -> list[InstallmentOut]:
    """Implicitly scoped to the caller's own visibility — Insureflow Admin
    sees every installment, an Insurance Company Admin sees every installment
    under their tenant, and broker roles see only their own broker's.
    """
    stmt = select(PremiumInstallment).join(Policy, PremiumInstallment.policy_id == Policy.id)
    if tenant_id is not None:
        stmt = stmt.where(Policy.insurance_company_id == tenant_id)
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF):
        stmt = stmt.where(Policy.broker_id == actor.broker_id)
    if status_filter is not None:
        stmt = stmt.where(PremiumInstallment.status == status_filter.value)
    stmt = stmt.order_by(PremiumInstallment.due_date)

    result = await db.scalars(stmt)
    return [InstallmentOut.model_validate(i) for i in result.all()]
