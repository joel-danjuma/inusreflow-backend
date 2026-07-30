from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_squad_client
from app.integrations.squad.client import SquadClient
from app.services import webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/squad", status_code=status.HTTP_200_OK)
async def receive_squad_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    squad_client: Annotated[SquadClient, Depends(get_squad_client)],
) -> dict[str, str]:
    """No auth dependency -- Squad sends no JWT, protected purely by
    signature verification inside webhook_service (CLAUDE.md / docs/adr/0004).
    Always acks 200 once the delivery is persisted, even for an invalid
    signature or an unresolved payment, so Squad's own retry policy is what
    recovers a transient failure rather than us triggering a retry storm.
    """
    payload: dict[str, Any] = await request.json()
    settings = get_settings()
    await webhook_service.handle_squad_webhook(
        db,
        payload=payload,
        headers=request.headers,
        secret_key=settings.squad_secret_key,
        squad_client=squad_client,
        merchant_id=settings.squad_merchant_id,
    )
    return {"status": "received"}
