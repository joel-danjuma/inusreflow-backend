from app.rbac.permissions import ROLE_PERMISSIONS, Permission, Role, role_has_permission


def test_every_role_has_a_matrix_entry() -> None:
    assert set(ROLE_PERMISSIONS) == set(Role)


def test_only_insureflow_admin_can_approve_onboarding() -> None:
    for role in Role:
        expected = role is Role.INSUREFLOW_ADMIN
        assert role_has_permission(role, Permission.APPROVE_INSURANCE_COMPANY) is expected
        assert role_has_permission(role, Permission.APPROVE_BROKER) is expected


def test_only_insureflow_admin_has_cross_tenant_visibility() -> None:
    for role in Role:
        expected = role is Role.INSUREFLOW_ADMIN
        assert role_has_permission(role, Permission.VIEW_ALL_INSURANCE_COMPANIES) is expected
        assert role_has_permission(role, Permission.VIEW_ALL_BROKERS) is expected


def test_only_broker_admin_manages_broker_staff() -> None:
    for role in Role:
        expected = role is Role.BROKER_ADMIN
        assert role_has_permission(role, Permission.MANAGE_BROKER_STAFF) is expected


def test_tenant_scoped_roles_can_view_their_own_org() -> None:
    """Insureflow Admin is excluded — it's cross-tenant by design and has no
    "own org" to view; it relies on VIEW_ALL_* instead.
    """
    for role in Role:
        expected = role is not Role.INSUREFLOW_ADMIN
        assert role_has_permission(role, Permission.VIEW_OWN_ORG) is expected
