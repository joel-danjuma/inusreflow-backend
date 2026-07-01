"""Regenerates docs/rbac-matrix.md from app/rbac/permissions.py's ROLE_PERMISSIONS.

Run via `make rbac-matrix` after changing the permission matrix, so the doc
and the code can never drift apart.
"""

from pathlib import Path

from app.rbac.permissions import ROLE_PERMISSIONS, Permission, Role, role_has_permission

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "rbac-matrix.md"


def render() -> str:
    header = "| Permission | " + " | ".join(role.value for role in Role) + " |"
    separator = "|---|" + "|".join("---" for _ in Role) + "|"
    rows = [
        "| `"
        + permission.value
        + "` | "
        + " | ".join("✅" if role_has_permission(role, permission) else "" for role in Role)
        + " |"
        for permission in Permission
    ]
    return (
        "# RBAC Matrix\n\n"
        "Generated from `app/rbac/permissions.py`'s `ROLE_PERMISSIONS` via "
        "`scripts/generate_rbac_matrix.py` (`make rbac-matrix`) — do not hand-edit.\n\n"
        f"{header}\n{separator}\n" + "\n".join(rows) + "\n"
    )


def main() -> None:
    OUTPUT_PATH.write_text(render())
    print(f"wrote {OUTPUT_PATH} ({len(ROLE_PERMISSIONS)} roles, {len(Permission)} permissions)")


if __name__ == "__main__":
    main()
