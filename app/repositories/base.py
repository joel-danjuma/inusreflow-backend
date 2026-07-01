import uuid
from typing import Protocol, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped


class TenantScopedModel(Protocol):
    id: Mapped[uuid.UUID]
    insurance_company_id: Mapped[uuid.UUID | None]


class TenantScopedRepository[ModelT: TenantScopedModel]:
    """Filters every query by insurance_company_id unless tenant_id is None — only
    ever true for Insureflow Admin, who is cross-tenant by design (PRD §4).
    """

    model: type[ModelT]

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID | None):
        self.db = db
        self.tenant_id = tenant_id

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        stmt = select(self.model).where(self.model.id == entity_id)
        if self.tenant_id is not None:
            stmt = stmt.where(self.model.insurance_company_id == self.tenant_id)
        return cast("ModelT | None", await self.db.scalar(stmt))

    async def list(self) -> list[ModelT]:
        stmt = select(self.model)
        if self.tenant_id is not None:
            stmt = stmt.where(self.model.insurance_company_id == self.tenant_id)
        result = await self.db.scalars(stmt)
        return list(result.all())
