from dataclasses import dataclass, field
from typing import Any

from app.integrations.squad.exceptions import SquadAPIError
from app.integrations.squad.schemas import (
    PayoutAccountLookup,
    StaticVATransaction,
    StaticVirtualAccount,
    TransferResult,
    TransferStatusResult,
)


@dataclass
class FakeSquadClient:
    """Test double for app.integrations.squad.client.SquadClient.

    SVA-aware: one permanent VA per broker (keyed by customer_identifier).
    Tests script transaction outcomes via simulate_transaction() instead of
    hitting the real sandbox -- mirrors the SVA webhook + re-query round trip
    without any network I/O.

    Correlation in tests:
      - create_business_virtual_account() stores the VA keyed by customer_identifier.
      - simulate_transaction(squad_tx_ref, ...) scripts what verify_transaction() returns.
      - The squad_tx_ref is Squad's own UUID (not our squad_transaction_ref); in tests
        you pick any distinct string that will be used in the webhook payload and
        passed to verify_transaction.
    """

    created_accounts: dict[str, StaticVirtualAccount] = field(default_factory=dict)
    # Keyed by squad_tx_ref (Squad's own UUID from the webhook payload).
    transaction_outcomes: dict[str, StaticVATransaction] = field(default_factory=dict)
    payout_accounts: dict[tuple[str, str], PayoutAccountLookup] = field(default_factory=dict)
    transfers: list[TransferResult] = field(default_factory=list)
    fail_transfer: bool = False
    transfer_status_overrides: dict[str, str] = field(default_factory=dict)
    next_transfer_status: str | None = None

    async def create_business_virtual_account(
        self,
        *,
        customer_identifier: str,
        business_name: str,
        mobile_num: str,
        bvn: str,
        beneficiary_account: str,
    ) -> StaticVirtualAccount:
        account_number = str(abs(hash(customer_identifier)))[:10].rjust(10, "0")
        account = StaticVirtualAccount(
            account_number=account_number,
            account_name=f"SQUAD/{business_name.upper()[:10]}",
            bank="GTBank",
            customer_identifier=customer_identifier,
            currency="NGN",
            raw={"fake": True, "customer_identifier": customer_identifier},
        )
        self.created_accounts[customer_identifier] = account
        return account

    def simulate_transaction(
        self,
        squad_tx_ref: str,
        *,
        status: str,
        raw: dict[str, Any] | None = None,
    ) -> None:
        """Test helper that scripts what verify_transaction(squad_tx_ref) returns.

        squad_tx_ref is Squad's own transaction_reference from the SVA webhook
        (the value placed in the webhook payload's "transaction_reference" field).
        """
        self.transaction_outcomes[squad_tx_ref] = StaticVATransaction(
            transaction_reference=squad_tx_ref,
            transaction_status=status,
            raw=raw or {"fake": True, "transaction_status": status},
        )

    async def verify_transaction(self, squad_tx_ref: str) -> StaticVATransaction | None:
        return self.transaction_outcomes.get(squad_tx_ref)

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
        """Scripts what requery_transfer/list_transfers report for this ref."""
        self.transfer_status_overrides[transaction_ref] = status

    def simulate_next_transfer_status(self, *, status: str) -> None:
        """Like simulate_transfer_status but consumed by the next requery_transfer
        call, before its ref is known (settlement_service generates refs internally).
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
