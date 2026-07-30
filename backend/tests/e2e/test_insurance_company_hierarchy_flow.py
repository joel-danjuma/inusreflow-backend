import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import (
    onboard_and_approve_insurance_company,
    seed_and_activate_insureflow_admin,
)


async def test_set_insurance_company_parent_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    parent, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Leadway Assurance",
        contact_email=f"admin-{uuid.uuid4()}@leadway-assurance.example.com",
    )
    subsidiary, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Leadway Assurance Life",
        contact_email=f"admin-{uuid.uuid4()}@leadway-assurance-life.example.com",
    )
    assert subsidiary["parent_company_id"] is None

    set_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{subsidiary['id']}/set-parent",
        json={"parent_company_id": parent["id"]},
        headers=admin_headers,
    )
    assert set_resp.status_code == 200, set_resp.text
    assert set_resp.json()["parent_company_id"] == parent["id"]

    # Unsetting it back to top-level.
    unset_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{subsidiary['id']}/set-parent",
        json={"parent_company_id": None},
        headers=admin_headers,
    )
    assert unset_resp.status_code == 200, unset_resp.text
    assert unset_resp.json()["parent_company_id"] is None


async def test_set_parent_rejects_self_reference(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    company, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Self Reference Insurance",
        contact_email=f"admin-{uuid.uuid4()}@self-reference-insurance.example.com",
    )
    resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{company['id']}/set-parent",
        json={"parent_company_id": company["id"]},
        headers=admin_headers,
    )
    assert resp.status_code == 409, resp.text


async def test_set_parent_rejects_nested_subparent(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    grandparent, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Grandparent Insurance",
        contact_email=f"admin-{uuid.uuid4()}@grandparent-insurance.example.com",
    )
    parent, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Parent Insurance",
        contact_email=f"admin-{uuid.uuid4()}@parent-insurance.example.com",
    )
    child, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Child Insurance",
        contact_email=f"admin-{uuid.uuid4()}@child-insurance.example.com",
    )
    set_parent_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{parent['id']}/set-parent",
        json={"parent_company_id": grandparent["id"]},
        headers=admin_headers,
    )
    assert set_parent_resp.status_code == 200, set_parent_resp.text

    nested_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{child['id']}/set-parent",
        json={"parent_company_id": parent["id"]},
        headers=admin_headers,
    )
    assert nested_resp.status_code == 409, nested_resp.text


async def test_set_parent_rejects_company_that_already_has_children(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """A company with its own subsidiaries can't itself become a subsidiary
    -- each individual link (child->this company, this company->new parent)
    would pass a naive single-hop check, but together hide a 2-level chain.
    """
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    new_parent, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Would-Be New Parent Insurance",
        contact_email=f"admin-{uuid.uuid4()}@would-be-new-parent-insurance.example.com",
    )
    middle, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Middle Insurance",
        contact_email=f"admin-{uuid.uuid4()}@middle-insurance.example.com",
    )
    grandchild, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Grandchild Insurance",
        contact_email=f"admin-{uuid.uuid4()}@grandchild-insurance.example.com",
    )
    set_child_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{grandchild['id']}/set-parent",
        json={"parent_company_id": middle["id"]},
        headers=admin_headers,
    )
    assert set_child_resp.status_code == 200, set_child_resp.text

    reparent_resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{middle['id']}/set-parent",
        json={"parent_company_id": new_parent["id"]},
        headers=admin_headers,
    )
    assert reparent_resp.status_code == 409, reparent_resp.text


async def test_set_parent_forbidden_for_non_insureflow_admin(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    admin_headers = await seed_and_activate_insureflow_admin(db_session, client)
    parent, _ = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Forbidden Parent Insurance",
        contact_email=f"admin-{uuid.uuid4()}@forbidden-parent-insurance.example.com",
    )
    subsidiary, subsidiary_headers = await onboard_and_approve_insurance_company(
        client,
        admin_headers,
        name="Forbidden Subsidiary Insurance",
        contact_email=f"admin-{uuid.uuid4()}@forbidden-subsidiary-insurance.example.com",
    )
    resp = await client.patch(
        f"/api/v1/admin/insurance-companies/{subsidiary['id']}/set-parent",
        json={"parent_company_id": parent["id"]},
        headers=subsidiary_headers,
    )
    assert resp.status_code == 403, resp.text
