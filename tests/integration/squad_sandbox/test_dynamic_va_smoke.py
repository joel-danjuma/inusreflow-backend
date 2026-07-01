"""Hits the real Squad sandbox API -- skipped unless real sandbox credentials
are present (CLAUDE.md). Not run by default or in CI's main job; run
explicitly via `uv run pytest -m squad_sandbox` once SQUAD_SECRET_KEY/
SQUAD_MERCHANT_ID are in .env, then manually verify the resulting virtual
account in Squad's sandbox dashboard.
"""

import pytest

from app.core.config import get_settings
from app.integrations.squad.client import HTTPSquadClient, generate_squad_ref

pytestmark = pytest.mark.squad_sandbox

_settings = get_settings()
_has_sandbox_creds = bool(_settings.squad_secret_key and _settings.squad_merchant_id)


@pytest.mark.skipif(
    not _has_sandbox_creds,
    reason="requires real Squad sandbox credentials (SQUAD_SECRET_KEY / SQUAD_MERCHANT_ID) in .env",
)
async def test_create_dynamic_virtual_account_against_real_sandbox() -> None:
    client = HTTPSquadClient(
        base_url=_settings.squad_base_url, secret_key=_settings.squad_secret_key
    )
    transaction_ref = generate_squad_ref(_settings.squad_merchant_id)

    va = await client.create_dynamic_virtual_account(
        amount_kobo=10_000,
        duration_seconds=1800,
        email="sandbox-smoke-test@example.com",
        transaction_ref=transaction_ref,
    )

    assert va.account_number
    assert va.transaction_reference == transaction_ref
