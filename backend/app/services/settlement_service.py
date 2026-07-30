import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.metrics import settlement_payout_outcomes_total
from app.integrations.squad.client import SquadClient, generate_squad_ref
from app.integrations.squad.exceptions import SquadAPIError
from app.models.enums import SettlementPayoutStatus
from app.models.insurance_company import InsuranceCompany
from app.models.settlement_payout import SettlementPayout
from app.services.audit_service import record_audit_log
from app.services.ledger_service import (
    LedgerPosting,
    get_or_create_ledger_account,
    post_ledger_entries,
)

_logger = structlog.get_logger(__name__)


async def settle_payment(
    db: AsyncSession,
    *,
    insurance_company: InsuranceCompany,
    source_type: str,
    source_id: uuid.UUID,
    amount_kobo: int,
    squad_client: SquadClient,
    merchant_id: str,
) -> SettlementPayout:
    """Fires a real-time Transfer API payout of the insurer's net share right
    after a Payment or PaymentBatch resolves to success
    (docs/adr/0003-settlement-mode.md) -- source_type is 'payment' or
    'payment_batch', source_id the respective row's id; a batch settles once
    for its total, never once per item. Fails closed --
    SettlementPayout.status='failed', no Squad call -- if the insurer's
    settlement bank details aren't on file (CLAUDE.md); a transfer failure
    from Squad itself is caught here too, since the payment/batch and its
    commission-split ledger entries already succeeded and must not be rolled
    back just because the payout leg failed. This is attempt 1 of a payout --
    retry_failed_settlement below handles any later attempt, always with a
    fresh squad_transfer_ref.
    """
    if (
        insurance_company.settlement_bank_code is None
        or insurance_company.settlement_account_number is None
        or insurance_company.settlement_account_name is None
    ):
        return await _record_failed_payout(
            db,
            insurance_company_id=insurance_company.id,
            source_type=source_type,
            source_id=source_id,
            amount_kobo=amount_kobo,
            transfer_ref=generate_squad_ref(merchant_id),
            failure_reason="insurer settlement bank details not configured",
        )

    return await _attempt_transfer(
        db,
        insurance_company=insurance_company,
        source_type=source_type,
        source_id=source_id,
        amount_kobo=amount_kobo,
        squad_client=squad_client,
        merchant_id=merchant_id,
        attempt_number=1,
        previous_attempt_id=None,
    )


async def retry_failed_settlement(
    db: AsyncSession,
    failed_payout: SettlementPayout,
    *,
    insurance_company: InsuranceCompany,
    squad_client: SquadClient,
    merchant_id: str,
) -> SettlementPayout:
    """Explicit retry of a FAILED settlement payout -- always mints a fresh
    squad_transfer_ref and chains previous_attempt_id back to the attempt
    being retried, never reusing a reference (CLAUDE.md). Re-checks bank
    details since they may have been configured/corrected since the
    original failure.

    failed_payout itself is never mutated by a retry (its row stays the
    historical record of that attempt) -- so a second call against the same
    already-retried failed_payout is rejected by checking for an existing
    row chained to it via previous_attempt_id, not by re-reading its own
    status. Without this, two concurrent/duplicate retry calls against the
    same failed attempt would each mint a transfer, double-paying the
    insurer.
    """
    if failed_payout.status != SettlementPayoutStatus.FAILED.value:
        raise ConflictError(
            f"settlement_payout {failed_payout.id} is not failed "
            f"(status={failed_payout.status}); only a failed payout can be retried"
        )

    already_retried = await db.scalar(
        select(SettlementPayout.id).where(SettlementPayout.previous_attempt_id == failed_payout.id)
    )
    if already_retried is not None:
        raise ConflictError(
            f"settlement_payout {failed_payout.id} has already been retried "
            f"(see settlement_payout {already_retried})"
        )

    if (
        insurance_company.settlement_bank_code is None
        or insurance_company.settlement_account_number is None
        or insurance_company.settlement_account_name is None
    ):
        return await _record_failed_payout(
            db,
            insurance_company_id=insurance_company.id,
            source_type=failed_payout.source_type,
            source_id=failed_payout.source_id,
            amount_kobo=failed_payout.amount_kobo,
            transfer_ref=generate_squad_ref(merchant_id),
            failure_reason="insurer settlement bank details not configured",
            attempt_number=failed_payout.attempt_number + 1,
            previous_attempt_id=failed_payout.id,
        )

    return await _attempt_transfer(
        db,
        insurance_company=insurance_company,
        source_type=failed_payout.source_type,
        source_id=failed_payout.source_id,
        amount_kobo=failed_payout.amount_kobo,
        squad_client=squad_client,
        merchant_id=merchant_id,
        attempt_number=failed_payout.attempt_number + 1,
        previous_attempt_id=failed_payout.id,
    )


async def _attempt_transfer(
    db: AsyncSession,
    *,
    insurance_company: InsuranceCompany,
    source_type: str,
    source_id: uuid.UUID,
    amount_kobo: int,
    squad_client: SquadClient,
    merchant_id: str,
    attempt_number: int,
    previous_attempt_id: uuid.UUID | None,
) -> SettlementPayout:
    """Shared by settle_payment (attempt 1) and retry_failed_settlement
    (attempt N+1): initiates the transfer, then immediately re-queries it --
    the initiate response's own status field is never trusted as final (PRD
    §8.6) -- and records SUCCESS/FAILED/PENDING accordingly. A PENDING
    outcome is left for reconciliation_service.reconcile_transfers to
    resolve once Squad settles it.
    """
    assert insurance_company.settlement_bank_code is not None
    assert insurance_company.settlement_account_number is not None
    assert insurance_company.settlement_account_name is not None

    transfer_ref = generate_squad_ref(merchant_id)
    try:
        await squad_client.initiate_transfer(
            transaction_ref=transfer_ref,
            bank_code=insurance_company.settlement_bank_code,
            account_number=insurance_company.settlement_account_number,
            account_name=insurance_company.settlement_account_name,
            amount_kobo=amount_kobo,
            remark=f"Insureflow settlement {source_id}",
        )
    except SquadAPIError as exc:
        return await _record_failed_payout(
            db,
            insurance_company_id=insurance_company.id,
            source_type=source_type,
            source_id=source_id,
            amount_kobo=amount_kobo,
            transfer_ref=transfer_ref,
            failure_reason=str(exc),
            raw_squad_response=exc.raw_response,
            attempt_number=attempt_number,
            previous_attempt_id=previous_attempt_id,
        )

    try:
        requery_result = await squad_client.requery_transfer(transfer_ref)
        remote_status = requery_result.transaction_status
        raw_response: dict[str, Any] | None = requery_result.raw
    except SquadAPIError as exc:
        remote_status = "pending"
        raw_response = exc.raw_response

    if remote_status == "success":
        status = SettlementPayoutStatus.SUCCESS.value
    elif remote_status in ("failed", "reversed"):
        status = SettlementPayoutStatus.FAILED.value
    else:
        status = SettlementPayoutStatus.PENDING.value

    payout = SettlementPayout(
        insurance_company_id=insurance_company.id,
        source_type=source_type,
        source_id=source_id,
        amount_kobo=amount_kobo,
        status=status,
        squad_transfer_ref=transfer_ref,
        attempt_number=attempt_number,
        previous_attempt_id=previous_attempt_id,
        raw_squad_response=raw_response,
        failure_reason=(
            f"squad transaction_status={remote_status}"
            if status == SettlementPayoutStatus.FAILED.value
            else None
        ),
    )
    db.add(payout)
    await db.flush()
    settlement_payout_outcomes_total.labels(status=status).inc()
    log_method = _logger.info if status == SettlementPayoutStatus.SUCCESS.value else _logger.warning
    log_method(
        f"settlement_payout.{status}",
        payout_id=str(payout.id),
        squad_transfer_ref=transfer_ref,
        amount_kobo=amount_kobo,
    )

    if status == SettlementPayoutStatus.SUCCESS.value:
        await _post_settlement_ledger_entries(
            db, insurance_company=insurance_company, amount_kobo=amount_kobo, payout_id=payout.id
        )

    await record_audit_log(
        db,
        action=f"settlement_payout.{status}",
        entity_type="settlement_payout",
        entity_id=payout.id,
        after_state={
            "amount_kobo": amount_kobo,
            "squad_transfer_ref": transfer_ref,
            "squad_transaction_status": remote_status,
        },
    )
    await db.flush()
    return payout


async def _post_settlement_ledger_entries(
    db: AsyncSession,
    *,
    insurance_company: InsuranceCompany,
    amount_kobo: int,
    payout_id: uuid.UUID,
) -> None:
    insurer_payable_account = await get_or_create_ledger_account(
        db, account_type="INSURER_PAYABLE", insurance_company_id=insurance_company.id
    )
    insurer_settled_account = await get_or_create_ledger_account(
        db, account_type="INSURER_SETTLED", insurance_company_id=insurance_company.id
    )
    await post_ledger_entries(
        db,
        [
            LedgerPosting(
                ledger_account_id=insurer_payable_account.id,
                entry_type="debit",
                amount_kobo=amount_kobo,
                reference_type="settlement_payout",
                reference_id=payout_id,
            ),
            LedgerPosting(
                ledger_account_id=insurer_settled_account.id,
                entry_type="credit",
                amount_kobo=amount_kobo,
                reference_type="settlement_payout",
                reference_id=payout_id,
            ),
        ],
    )


async def _record_failed_payout(
    db: AsyncSession,
    *,
    insurance_company_id: uuid.UUID,
    source_type: str,
    source_id: uuid.UUID,
    amount_kobo: int,
    transfer_ref: str,
    failure_reason: str,
    raw_squad_response: dict[str, Any] | None = None,
    attempt_number: int = 1,
    previous_attempt_id: uuid.UUID | None = None,
) -> SettlementPayout:
    payout = SettlementPayout(
        insurance_company_id=insurance_company_id,
        source_type=source_type,
        source_id=source_id,
        amount_kobo=amount_kobo,
        status=SettlementPayoutStatus.FAILED.value,
        squad_transfer_ref=transfer_ref,
        attempt_number=attempt_number,
        previous_attempt_id=previous_attempt_id,
        failure_reason=failure_reason,
        raw_squad_response=raw_squad_response,
    )
    db.add(payout)
    await db.flush()
    await record_audit_log(
        db,
        action="settlement_payout.failed",
        entity_type="settlement_payout",
        entity_id=payout.id,
        after_state={"failure_reason": failure_reason},
    )
    await db.flush()
    settlement_payout_outcomes_total.labels(status=SettlementPayoutStatus.FAILED.value).inc()
    _logger.warning(
        "settlement_payout.failed", payout_id=str(payout.id), failure_reason=failure_reason
    )
    return payout
