import io
import uuid
from datetime import date

import openpyxl
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import InstallmentStatus
from app.models.premium_installment import PremiumInstallment
from tests.fakes import FakeSquadClient
from tests.helpers import (
    assign_broker_to_insurer,
    create_policy,
    create_policyholder,
    onboard_and_approve_broker,
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


def _build_xlsx(rows: list[tuple[str | None, ...]], header: str = "Reference Number") -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append([header])
    for row in rows:
        sheet.append(list(row))
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


async def _create_policyholder_and_policy(
    client: AsyncClient,
    company_headers: dict[str, str],
    *,
    broker_id: str,
    name: str,
    premium_amount_kobo: int,
) -> dict:
    policyholder = await create_policyholder(
        client,
        company_headers,
        broker_id=broker_id,
        full_name=name,
        email=f"{uuid.uuid4()}@example.com",
    )
    return await create_policy(
        client,
        company_headers,
        broker_id=broker_id,
        policyholder_id=policyholder["id"],
        reference_number=f"DN-{uuid.uuid4()}",
        premium_amount_kobo=premium_amount_kobo,
        start_date=date.today().isoformat(),
    )


async def _set_reference(
    client: AsyncClient, headers: dict[str, str], installment_id: str, reference_number: str
) -> None:
    resp = await client.patch(
        f"/api/v1/installments/{installment_id}/reference-number",
        json={"reference_number": reference_number},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text


async def test_resolve_file_matches_by_reference_number(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Excel Upload Insurance",
        contact_email=f"admin-{uuid.uuid4()}@excel-upload-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Excel Upload Brokers",
        contact_email=f"admin-{uuid.uuid4()}@excel-upload-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    policy_a = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="Excel Client A",
        premium_amount_kobo=100_000,
    )
    policy_b = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="Excel Client B",
        premium_amount_kobo=200_000,
    )
    installments_a = (
        await client.get(f"/api/v1/policies/{policy_a['id']}/installments", headers=broker_headers)
    ).json()
    installments_b = (
        await client.get(f"/api/v1/policies/{policy_b['id']}/installments", headers=broker_headers)
    ).json()
    installment_a_id = installments_a[0]["id"]
    installment_b_id = installments_b[0]["id"]

    await _set_reference(client, broker_headers, installment_a_id, "DN-A-001")
    await _set_reference(client, broker_headers, installment_b_id, "DN-B-001")

    xlsx_bytes = _build_xlsx([("DN-A-001",), ("DN-B-001",)])
    resp = await client.post(
        "/api/v1/payments/bulk/resolve-file",
        headers=broker_headers,
        files={
            "file": (
                "premiums.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 200, resp.text
    resolution = resp.json()
    assert resolution["total_rows"] == 2
    assert len(resolution["matched"]) == 2
    assert len(resolution["unmatched"]) == 0
    matched_ids = {row["installment_id"] for row in resolution["matched"]}
    assert matched_ids == {installment_a_id, installment_b_id}


async def test_resolve_file_reports_unmatched_rows_with_reasons(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Excel Unmatched Insurance",
        contact_email=f"admin-{uuid.uuid4()}@excel-unmatched-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Excel Unmatched Brokers",
        contact_email=f"admin-{uuid.uuid4()}@excel-unmatched-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    # A second, unrelated broker -- its installment's reference number must
    # never resolve for the first broker (cross-tenant/ownership leak check).
    other_broker, other_broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Excel Unmatched Other Brokers",
        contact_email=f"admin-{uuid.uuid4()}@excel-unmatched-other-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=other_broker["id"], insurance_company_id=company["id"]
    )
    other_policy = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=other_broker["id"],
        name="Other Broker Client",
        premium_amount_kobo=100_000,
    )
    other_installments = (
        await client.get(
            f"/api/v1/policies/{other_policy['id']}/installments", headers=other_broker_headers
        )
    ).json()
    await _set_reference(
        client, other_broker_headers, other_installments[0]["id"], "DN-OTHER-BROKER"
    )

    # A paid-status installment for THIS broker, to trigger "already paid".
    policy = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="Excel Unmatched Client",
        premium_amount_kobo=100_000,
    )
    installments = (
        await client.get(f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers)
    ).json()
    await _set_reference(client, broker_headers, installments[0]["id"], "DN-PAID-ROW")

    xlsx_bytes = _build_xlsx(
        [
            (None,),  # missing reference
            ("DN-DOES-NOT-EXIST",),  # not found
            ("DN-OTHER-BROKER",),  # belongs to a different broker
            ("DN-PAID-ROW",),  # will be flipped to paid below
        ]
    )

    installment_row = await db_session.get(PremiumInstallment, uuid.UUID(installments[0]["id"]))
    assert installment_row is not None
    installment_row.status = InstallmentStatus.PAID.value
    await db_session.flush()

    resp = await client.post(
        "/api/v1/payments/bulk/resolve-file",
        headers=broker_headers,
        files={
            "file": (
                "premiums.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 200, resp.text
    resolution = resp.json()
    assert resolution["total_rows"] == 4
    assert len(resolution["matched"]) == 0
    assert len(resolution["unmatched"]) == 4
    reasons = {row["reference_number"]: row["reason"] for row in resolution["unmatched"]}
    assert reasons[None] == "missing reference number"
    assert "no installment found" in reasons["DN-DOES-NOT-EXIST"]
    assert "no installment found" in reasons["DN-OTHER-BROKER"]
    assert "already paid" in reasons["DN-PAID-ROW"]


async def test_resolve_file_flags_duplicate_reference_within_file(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Excel Duplicate Insurance",
        contact_email=f"admin-{uuid.uuid4()}@excel-duplicate-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Excel Duplicate Brokers",
        contact_email=f"admin-{uuid.uuid4()}@excel-duplicate-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )
    policy = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="Excel Duplicate Client",
        premium_amount_kobo=100_000,
    )
    installments = (
        await client.get(f"/api/v1/policies/{policy['id']}/installments", headers=broker_headers)
    ).json()
    await _set_reference(client, broker_headers, installments[0]["id"], "DN-DUP-001")

    xlsx_bytes = _build_xlsx([("DN-DUP-001",), ("DN-DUP-001",)])
    resp = await client.post(
        "/api/v1/payments/bulk/resolve-file",
        headers=broker_headers,
        files={
            "file": (
                "premiums.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 200, resp.text
    resolution = resp.json()
    assert len(resolution["matched"]) == 1
    assert len(resolution["unmatched"]) == 1
    assert "duplicate row" in resolution["unmatched"][0]["reason"]


async def test_resolve_file_rejects_oversized_row_count(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Excel Oversized Insurance",
        contact_email=f"admin-{uuid.uuid4()}@excel-oversized-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Excel Oversized Brokers",
        contact_email=f"admin-{uuid.uuid4()}@excel-oversized-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )

    xlsx_bytes = _build_xlsx([(f"DN-{i}",) for i in range(501)])
    resp = await client.post(
        "/api/v1/payments/bulk/resolve-file",
        headers=broker_headers,
        files={
            "file": (
                "premiums.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resp.status_code == 422, resp.text


async def test_resolved_ids_flow_through_existing_bulk_payment_endpoint(
    client: AsyncClient, db_session: AsyncSession, fake_squad_client: FakeSquadClient
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, company_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Excel To Bulk Pay Insurance",
        contact_email=f"admin-{uuid.uuid4()}@excel-to-bulk-pay-insurance.example.com",
    )
    broker, broker_headers = await onboard_and_approve_broker(
        client,
        admin_headers,
        name="Excel To Bulk Pay Brokers",
        contact_email=f"admin-{uuid.uuid4()}@excel-to-bulk-pay-brokers.example.com",
    )
    await assign_broker_to_insurer(
        client, admin_headers, broker_id=broker["id"], insurance_company_id=company["id"]
    )
    fake_squad_client.set_payout_account(
        bank_code="000013", account_number="0123456789", account_name="Excel To Bulk Pay Insurance"
    )
    settlement_resp = await client.post(
        f"/api/v1/insurance-companies/{company['id']}/settlement-account",
        json={"bank_code": "000013", "account_number": "0123456789"},
        headers=company_headers,
    )
    assert settlement_resp.status_code == 200, settlement_resp.text

    policy_a = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="Excel Pay Client A",
        premium_amount_kobo=100_000,
    )
    policy_b = await _create_policyholder_and_policy(
        client,
        company_headers,
        broker_id=broker["id"],
        name="Excel Pay Client B",
        premium_amount_kobo=150_000,
    )
    installment_a_id = (
        await client.get(f"/api/v1/policies/{policy_a['id']}/installments", headers=broker_headers)
    ).json()[0]["id"]
    installment_b_id = (
        await client.get(f"/api/v1/policies/{policy_b['id']}/installments", headers=broker_headers)
    ).json()[0]["id"]
    await _set_reference(client, broker_headers, installment_a_id, "DN-BULK-A")
    await _set_reference(client, broker_headers, installment_b_id, "DN-BULK-B")

    xlsx_bytes = _build_xlsx([("DN-BULK-A",), ("DN-BULK-B",)])
    resolve_resp = await client.post(
        "/api/v1/payments/bulk/resolve-file",
        headers=broker_headers,
        files={
            "file": (
                "premiums.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert resolve_resp.status_code == 200, resolve_resp.text
    matched_ids = [row["installment_id"] for row in resolve_resp.json()["matched"]]
    assert len(matched_ids) == 2

    # Feeds straight into the existing, unmodified bulk-payment endpoint.
    bulk_resp = await client.post(
        "/api/v1/payments/bulk",
        json={"installment_ids": matched_ids},
        headers={**broker_headers, "Idempotency-Key": "excel-to-bulk-key-1"},
    )
    assert bulk_resp.status_code == 201, bulk_resp.text
    batch = bulk_resp.json()
    assert batch["item_count"] == 2
    assert batch["total_amount_kobo"] == 250_000
    assert batch["status"] == "initiated"
