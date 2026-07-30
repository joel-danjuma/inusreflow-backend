"""Seeds DB state for the bulk-payment Locust run (tests/load/locustfile.py).

Run with `uv run python -m tests.load.seed_data` against the local dev
Postgres (docker compose up -d) before starting the load-test server and
Locust -- see docs/adr/0008-load-testing.md for the full sequence.

Bypasses HTTP entirely (calls onboarding_service/policy_service directly)
because the volume of setup needed -- NUM_BROKERS brokers x
POLICIES_PER_BROKER policies, each minting INSTALLMENT_WINDOW_SIZE=12
installments -- would make onboarding through the API the dominant cost of
running this script, when only POST /payments/bulk's latency is what's
being measured. Also skips the RLS tenant-context GUC entirely (never
calls set_config('app.current_tenant_id', ...)) -- the policy in
docs/adr/0006-row-level-security.md treats an unset GUC as cross-tenant, so
this script's session sees/writes every row unrestricted, same as a
migration would.
"""

import asyncio
import json
import uuid
from datetime import date
from pathlib import Path

from sqlalchemy import select

import app.main  # noqa: F401  -- registers every model's mapper before any flush
from app.core.db import async_session_factory
from app.core.security import create_access_token
from app.models.enums import PremiumFrequency
from app.models.platform_user import PlatformUser
from app.models.policy import Policy
from app.models.premium_installment import PremiumInstallment
from app.rbac.permissions import Role
from app.services import policy_service
from app.services.onboarding_service import (
    approve_broker,
    approve_insurance_company,
    assign_broker_to_insurer,
    onboard_broker,
    onboard_insurance_company,
)

NUM_BROKERS = 5
#: 45 policies x INSTALLMENT_WINDOW_SIZE(12) = 540 installments per broker --
#: enough for one full Settings.max_bulk_payment_items(500) batch plus
#: headroom for a couple of smaller follow-up requests in the same run.
POLICIES_PER_BROKER = 45
PREMIUM_AMOUNT_KOBO = 500_000

OUTPUT_PATH = Path(__file__).parent / "seed_data.json"


async def _seed_admin(db) -> PlatformUser:  # type: ignore[no-untyped-def]
    admin = PlatformUser(
        email=f"load-admin-{uuid.uuid4()}@insureflow.local",
        role=Role.INSUREFLOW_ADMIN.value,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    return admin


async def main() -> None:
    async with async_session_factory() as db:
        admin = await _seed_admin(db)

        company = await onboard_insurance_company(
            db,
            name=f"Load Test Insurer {uuid.uuid4()}",
            contact_email=f"insurer-{uuid.uuid4()}@example.com",
        )
        await approve_insurance_company(db, company_id=company.id, actor=admin)
        company_admin = await db.scalar(
            select(PlatformUser).where(PlatformUser.insurance_company_id == company.id)
        )
        assert company_admin is not None

        brokers_payload = []
        for i in range(NUM_BROKERS):
            broker = await onboard_broker(
                db,
                name=f"Load Test Broker {i} {uuid.uuid4()}",
                contact_email=f"broker-{i}-{uuid.uuid4()}@example.com",
            )
            await approve_broker(db, broker_id=broker.id, actor=admin)
            await assign_broker_to_insurer(
                db, broker_id=broker.id, insurance_company_id=company.id, actor=admin
            )

            broker_admin = await db.scalar(
                select(PlatformUser).where(PlatformUser.broker_id == broker.id)
            )
            assert broker_admin is not None
            broker_admin.is_active = True
            await db.flush()

            # Policy/policyholder creation is insurer-only now (many-to-many
            # broker/insurer change) -- actor is the insurer's own admin,
            # broker_id names which broker this seeded data belongs to.
            policyholder = await policy_service.create_policyholder(
                db,
                actor=company_admin,
                insurance_company_id=company.id,
                broker_id=broker.id,
                full_name=f"Load Test Payer {i}",
                email=None,
                phone_number=None,
                identification_number=None,
            )

            for policy_index in range(POLICIES_PER_BROKER):
                await policy_service.create_policy(
                    db,
                    actor=company_admin,
                    insurance_company_id=company.id,
                    broker_id=broker.id,
                    reference_number=f"DN-LOAD-{broker.id}-{policy_index}",
                    policyholder_id=policyholder.id,
                    premium_amount_kobo=PREMIUM_AMOUNT_KOBO,
                    premium_frequency=PremiumFrequency.MONTHLY,
                    start_date=date.today(),
                )
            await db.flush()

            installment_ids = (
                await db.scalars(
                    select(PremiumInstallment.id)
                    .join(Policy, PremiumInstallment.policy_id == Policy.id)
                    .where(Policy.broker_id == broker.id)
                    .order_by(PremiumInstallment.due_date)
                )
            ).all()

            token = create_access_token(
                user_id=broker_admin.id, role=Role.BROKER_ADMIN, org_id=broker.id
            )
            brokers_payload.append(
                {
                    "broker_id": str(broker.id),
                    "jwt": token,
                    "installment_ids": [str(iid) for iid in installment_ids],
                }
            )
            print(f"seeded broker {i}: {len(installment_ids)} due installments")

        await db.commit()

    OUTPUT_PATH.write_text(json.dumps({"brokers": brokers_payload}, indent=2))
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
