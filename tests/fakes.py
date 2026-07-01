from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.integrations.squad.exceptions import SquadAPIError
from app.integrations.squad.schemas import (
    DynamicVirtualAccount,
    DynamicVirtualAccountTransaction,
    PayoutAccountLookup,
    TransferResult,
    TransferStatusResult,
)


@dataclass
class FakeSquadClient:
    """Test double for app.integrations.squad.client.SquadClient. Tests script
    outcomes via simulate_transaction()/set_payout_account() instead of
    hitting the real sandbox -- mirrors the shape of a real webhook + re-query
    round trip without any network I/O.
    """

    created_accounts: dict[str, DynamicVirtualAccount] = field(default_factory=dict)
    transaction_outcomes: dict[str, DynamicVirtualAccountTransaction] = field(default_factory=dict)
    payout_accounts: dict[tuple[str, str], PayoutAccountLookup] = field(default_factory=dict)
    transfers: list[TransferResult] = field(default_factory=list)
    fail_transfer: bool = False
    transfer_status_overrides: dict[str, str] = field(default_factory=dict)
    next_transfer_status: str | None = None

    async def create_dynamic_virtual_account(
        self, *, amount_kobo: int, duration_seconds: int, email: str, transaction_ref: str
    ) -> DynamicVirtualAccount:
        account = DynamicVirtualAccount(
            account_number=str(abs(hash(transaction_ref)))[:10].rjust(10, "0"),
            account_name="SQUAD CHECKOUT",
            bank="GTBank",
            expires_at=datetime.now(UTC) + timedelta(seconds=duration_seconds),
            transaction_reference=transaction_ref,
            currency="NGN",
            raw={"fake": True, "amount_kobo": amount_kobo, "email": email},
        )
        self.created_accounts[transaction_ref] = account
        return account

    def simulate_transaction(
        self, transaction_ref: str, *, status: str, amount_received: str | None = None
    ) -> None:
        """Test helper standing in for Squad's sandbox payment-simulation call
        -- scripts what get_dynamic_virtual_account_transaction returns next.
        """
        self.transaction_outcomes[transaction_ref] = DynamicVirtualAccountTransaction(
            transaction_reference=transaction_ref,
            transaction_status=status,
            merchant_reference=transaction_ref,
            amount_received=amount_received,
            raw={"fake": True, "transaction_status": status},
        )

    async def get_dynamic_virtual_account_transaction(
        self, transaction_ref: str
    ) -> DynamicVirtualAccountTransaction | None:
        return self.transaction_outcomes.get(transaction_ref)

    def set_payout_account(self, *, bank_code: str, account_number: str, account_name: str) -> None:
        self.payout_accounts[(bank_code, account_number)] = PayoutAccountLookup(
            account_number=account_number, account_name=account_name, raw={"fake": True}
        )

    async def lookup_payout_account(
        self, *, bank_code: str, account_number: str
    ) -> PayoutAccountLookup:
        key = (bank_code, account_number)
        if key not in self.payout_accounts:
            raise SquadAPIError(f"no fake account registered for {key}", status_code=404)
        return self.payout_accounts[key]

    async def initiate_transfer(
        self,
        *,
        transaction_ref: str,
        bank_code: str,
        account_number: str,
        account_name: str,
        amount_kobo: int,
        remark: str,
    ) -> TransferResult:
        if self.fail_transfer:
            raise SquadAPIError("simulated transfer failure", status_code=500)
        result = TransferResult(
            transaction_reference=transaction_ref,
            status="success",
            raw={"fake": True, "amount_kobo": amount_kobo},
        )
        self.transfers.append(result)
        return result

    def simulate_transfer_status(self, transaction_ref: str, *, status: str) -> None:
        """Test helper standing in for Squad's sandbox transfer-status
        simulation -- scripts what requery_transfer/list_transfers report
        for this ref next. Defaults to "success" when unscripted, matching
        initiate_transfer's default outcome above.
        """
        self.transfer_status_overrides[transaction_ref] = status

    def simulate_next_transfer_status(self, *, status: str) -> None:
        """Like simulate_transfer_status, but for the next transfer this
        client initiates, before its ref is known -- settlement_service
        generates the ref internally, so a test can't pre-key an override by
        ref. Consumed once by the next requery_transfer call.
        """
        self.next_transfer_status = status

    async def requery_transfer(self, transaction_ref: str) -> TransferStatusResult:
        if transaction_ref in self.transfer_status_overrides:
            status = self.transfer_status_overrides[transaction_ref]
        elif self.next_transfer_status is not None:
            status = self.next_transfer_status
            self.next_transfer_status = None
        else:
            status = "success"
        return TransferStatusResult(
            transaction_reference=transaction_ref,
            transaction_status=status,
            raw={"fake": True, "transaction_status": status},
        )

    async def list_transfers(
        self, *, page: int = 1, per_page: int = 50
    ) -> list[TransferStatusResult]:
        if page > 1:
            return []
        return [
            TransferStatusResult(
                transaction_reference=transfer.transaction_reference,
                transaction_status=self.transfer_status_overrides.get(
                    transfer.transaction_reference, "success"
                ),
                raw={"fake": True},
            )
            for transfer in self.transfers
        ]
