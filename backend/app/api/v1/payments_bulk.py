import uuid
from typing import Annotated, Any, cast

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_squad_client, get_tenant_id, require_permission
from app.core.rate_limit import enforce_payment_rate_limit
from app.integrations.squad.client import SquadClient
from app.models.payment_batch import PaymentBatch
from app.models.payment_batch_item import PaymentBatchItem
from app.models.platform_user import PlatformUser
from app.rbac.permissions import Permission, Role
from app.schemas.payment_batch import (
    BulkPaymentFileResolution,
    PaymentBatchCreateRequest,
    PaymentBatchItemOut,
    PaymentBatchOut,
)
from app.services import bulk_payment_service, bulk_payment_upload_service, idempotency_service

router = APIRouter(prefix="/payments/bulk", tags=["payments"])


def _check_batch_access(
    batch: PaymentBatch, actor: PlatformUser, tenant_id: uuid.UUID | None
) -> None:
    if tenant_id is not None and batch.insurance_company_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF) and batch.broker_id != actor.broker_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


async def _build_batch_out(db: AsyncSession, batch: PaymentBatch) -> PaymentBatchOut:
    """No ORM relationships in this codebase (CLAUDE.md) -- items are
    fetched and assembled manually rather than relying on attribute
    traversal.
    """
    items = (
        await db.scalars(
            select(PaymentBatchItem).where(PaymentBatchItem.payment_batch_id == batch.id)
        )
    ).all()
    return PaymentBatchOut(
        id=batch.id,
        broker_id=batch.broker_id,
        insurance_company_id=batch.insurance_company_id,
        total_amount_kobo=batch.total_amount_kobo,
        item_count=batch.item_count,
        status=batch.status,
        squad_transaction_ref=batch.squad_transaction_ref,
        squad_virtual_account_number=batch.squad_virtual_account_number,
        squad_virtual_account_bank=batch.squad_virtual_account_bank,
        va_expires_at=batch.va_expires_at,
        failure_reason=batch.failure_reason,
        created_at=batch.created_at,
        items=[PaymentBatchItemOut.model_validate(item) for item in items],
    )


@router.post(
    "",
    response_model=PaymentBatchOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_payment_rate_limit)],
)
async def create_bulk_payment(
    payload: PaymentBatchCreateRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.CREATE_PAYMENT))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],  # noqa: ARG001 -- sets RLS context
    db: Annotated[AsyncSession, Depends(get_db)],
    squad_client: Annotated[SquadClient, Depends(get_squad_client)],
) -> PaymentBatchOut:
    # CREATE_PAYMENT is granted only to broker roles, for which broker_id is
    # always set. Which insurer this batch belongs to is derived inside
    # initiate_bulk_payment from the installments' own policies (and the
    # batch is rejected if it spans more than one insurer) -- a broker may
    # now work with several insurers at once, so there's no single tenant id
    # to resolve or trust here.
    broker_id = cast(uuid.UUID, actor.broker_id)
    settings = get_settings()

    async def handler(key_id: uuid.UUID) -> tuple[int, dict[str, Any], uuid.UUID | None]:
        batch = await bulk_payment_service.initiate_bulk_payment(
            db,
            actor=actor,
            installment_ids=payload.installment_ids,
            broker_id=broker_id,
            squad_client=squad_client,
            merchant_id=settings.squad_merchant_id,
            max_items=settings.max_bulk_payment_items,
            idempotency_key_id=key_id,
        )
        body = (await _build_batch_out(db, batch)).model_dump(mode="json")
        return status.HTTP_201_CREATED, body, batch.id

    _, body = await idempotency_service.with_idempotency(
        db,
        platform_user_id=actor.id,
        endpoint="POST /payments/bulk",
        idempotency_key=idempotency_key,
        request_body=payload.model_dump(mode="json"),
        handler=handler,
    )
    return PaymentBatchOut.model_validate(body)


@router.post(
    "/resolve-file", response_model=BulkPaymentFileResolution, status_code=status.HTTP_200_OK
)
async def resolve_bulk_payment_file(
    file: Annotated[UploadFile, File()],
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.CREATE_PAYMENT))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],  # noqa: ARG001 -- sets RLS context
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BulkPaymentFileResolution:
    """Resolves an uploaded Excel file's reference numbers to installment
    ids -- a pure lookup, never creates a Payment/PaymentBatch. The broker
    reviews the match/unmatched preview client-side, then submits the
    resolved installment_ids through the ordinary POST /payments/bulk. This
    is a preview/match step only, so it doesn't need to enforce the
    single-insurer-per-batch rule itself -- the broker can freely edit the
    matched set before it ever reaches POST /payments/bulk, which is where
    that check actually needs to bite.
    """
    # CREATE_PAYMENT is granted only to broker roles, for which broker_id is
    # always set.
    broker_id = cast(uuid.UUID, actor.broker_id)
    settings = get_settings()

    contents = await file.read()
    if len(contents) > settings.max_bulk_upload_file_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file too large"
        )

    return await bulk_payment_upload_service.resolve_installments_from_excel(
        db,
        file_bytes=contents,
        broker_id=broker_id,
        max_rows=settings.max_bulk_payment_items,
    )


@router.get("/template")
async def download_reference_template(
    _actor: Annotated[PlatformUser, Depends(require_permission(Permission.CREATE_PAYMENT))],
) -> Response:
    """A downloadable .xlsx showing the column header the Excel bulk-pay
    matcher (resolve_installments_from_excel) expects, so a broker doesn't
    have to guess it. Registered ahead of GET /{batch_id} below so "template"
    is never swallowed as a batch_id path param.
    """
    workbook_bytes = bulk_payment_upload_service.build_reference_template_workbook()
    return Response(
        content=workbook_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="bulk-pay-reference-template.xlsx"'},
    )


@router.get("", response_model=list[PaymentBatchOut])
async def list_bulk_payments(
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_PAYMENTS))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
    broker_id: Annotated[uuid.UUID | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
) -> list[PaymentBatchOut]:
    """Same scoping rules as list_payments: broker roles are always pinned
    to their own broker_id, an Insurance Company Admin is pinned to their
    tenant, and Insureflow Admin sees everything (optionally filtered).
    """
    stmt = select(PaymentBatch)
    if tenant_id is not None:
        stmt = stmt.where(PaymentBatch.insurance_company_id == tenant_id)
    role = Role(actor.role)
    if role in (Role.BROKER_ADMIN, Role.BROKER_STAFF):
        stmt = stmt.where(PaymentBatch.broker_id == actor.broker_id)
    elif broker_id is not None:
        stmt = stmt.where(PaymentBatch.broker_id == broker_id)
    if status_filter is not None:
        stmt = stmt.where(PaymentBatch.status == status_filter)
    stmt = stmt.order_by(PaymentBatch.created_at.desc())

    batches = (await db.scalars(stmt)).all()
    return [await _build_batch_out(db, b) for b in batches]


@router.get("/{batch_id}", response_model=PaymentBatchOut)
async def get_bulk_payment(
    batch_id: uuid.UUID,
    actor: Annotated[PlatformUser, Depends(require_permission(Permission.VIEW_PAYMENTS))],
    tenant_id: Annotated[uuid.UUID | None, Depends(get_tenant_id)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaymentBatchOut:
    batch = await db.get(PaymentBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment batch not found")
    _check_batch_access(batch, actor, tenant_id)
    return await _build_batch_out(db, batch)
