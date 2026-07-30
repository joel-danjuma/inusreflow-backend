"""Hits the real Squad sandbox API -- skipped unless real sandbox credentials
are present (CLAUDE.md). Not run by default or in CI's main job; run
explicitly via `uv run pytest -m squad_sandbox` once SQUAD_SECRET_KEY/
SQUAD_MERCHANT_ID are in .env, then manually verify the resulting virtual
account in Squad's sandbox dashboard.
"""

import pytest

from app.core.config import get_settings
from app.integrations.squad.client import HTTPSquadClient

pytestmark = pytest.mark.squad_sandbox

_settings = get_settings()
_has_sandbox_creds = bool(
    _settings.squad_secret_key
    and _settings.squad_merchant_id
    and _settings.squad_beneficiary_account
)


@pytest.mark.skipif(
    not _has_sandbox_creds,
    reason=("requires SQUAD_SECRET_KEY, SQUAD_MERCHANT_ID, and SQUAD_BENEFICIARY_ACCOUNT in .env"),
)
async def test_create_business_virtual_account_against_real_sandbox() -> None:
    """Smoke test: creates a permanent Business SVA for a test broker and
    verifies the response has an account_number. Requires real BVN/phone
    values -- substitute valid sandbox values before running.
    """
    client = HTTPSquadClient(
        base_url=_settings.squad_base_url, secret_key=_settings.squad_secret_key
    )

    va = await client.create_business_virtual_account(
        customer_identifier="sandbox-smoke-broker-001",
        business_name="Smoke Test Brokers",
        mobile_num="+2348000000001",
        bvn="00000000000",
        beneficiary_account=_settings.squad_beneficiary_account,
    )

    assert va.account_number
    assert va.customer_identifier == "sandbox-smoke-broker-001"
    assert va.bank
