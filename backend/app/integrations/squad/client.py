import uuid
from typing import Any, Protocol

import httpx

from app.integrations.squad.exceptions import SquadAPIError
from app.integrations.squad.schemas import (
    PayoutAccountLookup,
    StaticVATransaction,
    StaticVirtualAccount,
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
    """Covers exactly what payment/webhook/settlement services call."""

    async def create_business_virtual_account(
        self,
        *,
        customer_identifier: str,
        business_name: str,
        mobile_num: str,
        bvn: str,
        beneficiary_account: str,
    ) -> StaticVirtualAccount: ...

    async def verify_transaction(self, squad_tx_ref: str) -> StaticVATransaction | None: ...

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

    async def create_business_virtual_account(
        self,
        *,
        customer_identifier: str,
        business_name: str,
        mobile_num: str,
        bvn: str,
        beneficiary_account: str,
    ) -> StaticVirtualAccount:
        body = await self._request(
            "POST",
            "/virtual-account/business",
            json_body={
                "customer_identifier": customer_identifier,
                "business_name": business_name,
                # Squad requires exactly 11 (local, e.g. "08012345678") or 13
                # (international, no "+") digits -- our own Broker.phone_number
                # is stored in E.164 ("+234...") since that's the correct
                # canonical format, so the "+" is stripped only at this Squad
                # API boundary, confirmed against the live sandbox.
                "mobile_num": mobile_num.lstrip("+"),
                "bvn": bvn,
                "beneficiary_account": beneficiary_account,
            },
        )
        data = body["data"]
        # Squad's actual response fields (confirmed against the live sandbox,
        # not just docs): virtual_account_number/bank_code/first_name/
        # last_name -- not account_number/bank/account_name as previously
        # assumed, which would have KeyError'd on the very first real call.
        account_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
        bank_code = data.get("bank_code", "")
        return StaticVirtualAccount(
            account_number=data["virtual_account_number"],
            account_name=account_name or business_name,
            bank="GTBank" if bank_code == "058" else bank_code,
            customer_identifier=data.get("customer_identifier", customer_identifier),
            currency=data.get("currency", "NGN"),
            raw=body,
        )

    async def verify_transaction(self, squad_tx_ref: str) -> StaticVATransaction | None:
        """Independently re-queries a transaction via GET /transaction/verify/{ref}.
        Returns None on 404 (transaction not found yet), re-raises on other errors.
        """
        try:
            body = await self._request("GET", f"/transaction/verify/{squad_tx_ref}")
        except SquadAPIError as exc:
            if exc.status_code == 404:
                return None
            raise
        data = body.get("data") or {}
        return StaticVATransaction(
            transaction_reference=data.get("transaction_reference", squad_tx_ref),
            transaction_status=str(data.get("transaction_status") or "PENDING").upper(),
            raw=body,
        )

    async def lookup_payout_account(
        self, *, bank_code: str, account_number: str
    ) -> PayoutAccountLookup:
        """bank_code here (and on initiate_transfer) is Squad's 6-digit NIP
        code, not the classic 3-digit CBN bank code (e.g. GTBank is "000013",
        never "058") -- confirmed against the live sandbox, which otherwise
        rejects it with a validation error naming it "nip_code" internally
        even though the wire field is still called bank_code.
        """
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
        """bank_code is Squad's 6-digit NIP code -- see lookup_payout_account's
        docstring."""
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
