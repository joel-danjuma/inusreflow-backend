import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IdempotencyKey(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Backs the mandatory Idempotency-Key header on every payment-initiating
    endpoint (CLAUDE.md). A row is inserted up front with response_status/
    response_body still NULL (claiming the key); the handler fills them in
    once it completes, so a concurrent replay can detect an in-flight call
    rather than racing it.
    """

    __tablename__ = "idempotency_keys"
    __table_args__ = (
        UniqueConstraint(
            "platform_user_id",
            "endpoint",
            "idempotency_key",
            name="ux_idempotency_keys_user_endpoint_key",
        ),
    )

    platform_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("platform_users.id"), nullable=False
    )
    endpoint: Mapped[str] = mapped_column(String, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    request_hash: Mapped[str] = mapped_column(String, nullable=False)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
