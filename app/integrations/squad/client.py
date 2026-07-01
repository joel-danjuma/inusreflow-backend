import uuid
from datetime import datetime
from typing import Any, Protocol

import httpx

from app.integrations.squad.exceptions import SquadAPIError
from app.integrations.squad.schemas import (
    DynamicVirtualAccount,
    DynamicVirtualAccountTransaction,
    PayoutAccountLookup,
    TransferResult,
    TransferStatusResult,
)


def generate_squad_ref(merchant_id: str) -> str:
    """Squad transaction/transfer references are server-generated as
    {merchant_id}_{uuid} (CLAUDE.md) -- call once per Payment/
    SettlementPayout and never reuse, even on retry.
    """
    return f"{merchant_id}_{uuid.uuid4()}"


class SquadClient(Protocol):
    """Covers exactly what Phase 4/5/6 services call."""

    async def create_dynamic_virtual_account(
        self, *, amount_kobo: int, duration_seconds: int, email: str, transaction_ref: str
    ) -> DynamicVirtualAccount: ...

    async def get_dynamic_virtual_account_transaction(
        self, transaction_ref: str
    ) -> DynamicVirtualAccountTransaction | None: ...

    async def lookup_payout_account(
        self, *, bank_code: str, account_number: str
    ) -> PayoutAccountLookup: ...

    async def initiate_transfer(
        self,
        *,
        transaction_ref: str,
        bank_code: str,
        account_number: str,
        account_name: str,
        amount_kobo: int,
        remark: str,
    ) -> TransferResult: ...

    async def requery_transfer(self, transaction_ref: str) -> TransferStatusResult: ...

    async def list_transfers(
        self, *, page: int = 1, per_page: int = 50
    ) -> list[TransferStatusResult]: ...


class HTTPSquadClient:
    """Real Squad API implementation (httpx, async). Sandbox vs live is
    purely base_url + a matching secret key from Settings -- the two are
    never co-loaded (CLAUDE.md).
    """

    def __init__(self, *, base_url: str, secret_key: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret_key = secret_key
        self._timeout = timeout

    async def _request(
        self, method: str, path: str, *, json_body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not self._secret_key:
            raise SquadAPIError(
                "Squad secret key is not configured (set SQUAD_SECRET_KEY in .env)",
                status_code=None,
            )
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(
                    method,
                    f"{self._base_url}{path}",
                    json=json_body,
                    headers={
                        "Authorization": f"Bearer {self._secret_key}",
                        "Content-Type": "application/json",
                    },
                )
        except httpx.HTTPError as exc:
            raise SquadAPIError(
                f"Squad request failed: {exc}",
                status_code=None,
            ) from exc
        try:
            body: dict[str, Any] = response.json()
        except ValueError as exc:
            raise SquadAPIError(
                f"Squad returned a non-JSON response (status {response.status_code})",
                status_code=response.status_code,
            ) from exc

        if response.status_code >= 400 or body.get("success") is False:
            raise SquadAPIError(
                str(body.get("message", "Squad API call failed")),
                status_code=response.status_code,
                raw_response=body,
            )
        return body

    async def create_dynamic_virtual_account(
        self, *, amount_kobo: int, duration_seconds: int, email: str, transaction_ref: str
    ) -> DynamicVirtualAccount:
        body = await self._request(
            "POST",
            "/virtual-account/initiate-dynamic-virtual-account",
            json_body={
                "amount": amount_kobo,
                "duration": duration_seconds,
                "email": email,
                "transaction_ref": transaction_ref,
            },
        )
        data = body["data"]
        return DynamicVirtualAccount(
            account_number=data["account_number"],
            account_name=data.get("account_name", ""),
            bank=data.get("bank", ""),
            expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")),
            transaction_reference=data.get("transaction_reference", transaction_ref),
            currency=data.get("currency", "NGN"),
            raw=body,
        )

    async def get_dynamic_virtual_account_transaction(
        self, transaction_ref: str
    ) -> DynamicVirtualAccountTransaction | None:
        try:
            body = await self._request(
                "GET",
                f"/virtual-account/get-dynamic-virtual-account-transactions/{transaction_ref}",
            )
        except SquadAPIError as exc:
            if exc.status_code == 404:
                return None
            raise
        data = body["data"]
        return DynamicVirtualAccountTransaction(
            transaction_reference=data.get("transaction_reference", transaction_ref),
            transaction_status=data["transaction_status"],
            merchant_reference=data.get("merchant_reference", transaction_ref),
            amount_received=data.get("amount_received"),
            raw=body,
        )

    async def lookup_payout_account(
        self, *, bank_code: str, account_number: str
    ) -> PayoutAccountLookup:
        body = await self._request(
            "POST",
            "/payout/account/lookup",
            json_body={"bank_code": bank_code, "account_number": account_number},
        )
        data = body["data"]
        return PayoutAccountLookup(
            account_number=data.get("account_number", account_number),
            account_name=data["account_name"],
            raw=body,
        )

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
        body = await self._request(
            "POST",
            "/payout/transfer",
            json_body={
                "transaction_reference": transaction_ref,
                "bank_code": bank_code,
                "account_number": account_number,
                "account_name": account_name,
                "amount": str(amount_kobo),
                "currency_id": "NGN",
                "remark": remark,
            },
        )
        data = body.get("data") or {}
        status = str(data.get("transaction_status") or data.get("status") or "pending")
        return TransferResult(transaction_reference=transaction_ref, status=status, raw=body)

    async def requery_transfer(self, transaction_ref: str) -> TransferStatusResult:
        body = await self._request(
            "POST",
            "/payout/requery",
            json_body={"transaction_reference": transaction_ref},
        )
        data = body.get("data") or {}
        status = str(data.get("transaction_status") or data.get("status") or "pending")
        return TransferStatusResult(
            transaction_reference=data.get("transaction_reference", transaction_ref),
            transaction_status=status,
            raw=body,
        )

    async def list_transfers(
        self, *, page: int = 1, per_page: int = 50
    ) -> list[TransferStatusResult]:
        body = await self._request("GET", f"/payout/list?page={page}&perPage={per_page}&dir=DESC")
        items = body.get("data") or []
        return [
            TransferStatusResult(
                transaction_reference=item["transaction_reference"],
                transaction_status=str(item.get("transaction_status") or "pending"),
                raw=item,
            )
            for item in items
        ]
