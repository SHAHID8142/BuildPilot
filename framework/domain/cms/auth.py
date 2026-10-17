"""P8 CMS role-based access control.

Machine-enforced authorization. Every operation checks the caller's role
against the permission matrix. Unauthorized operations fail closed.
"""
from __future__ import annotations

from typing import Any

from framework.domain.cms.validation import validate_permission_matrix


# Default permission matrix per approved Phase 2 architecture
DEFAULT_PERMISSION_MATRIX: dict[str, Any] = {
    "roles": ["super_admin", "admin"],
    "permissions": [
        {
            "role": "super_admin",
            "content_create": True,
            "content_edit": True,
            "content_delete": True,
            "content_publish": True,
            "content_preview": True,
            "section_create": True,
            "section_edit": True,
            "section_delete": True,
            "layout_modify": True,
            "media_upload": True,
            "media_select": True,
            "media_external_import": True,
            "revision_view": True,
            "revision_rollback": True,
            "user_admin": True,
            "role_admin": True,
            "audit_view": True,
            "audit_export": True,
        },
        {
            "role": "admin",
            "content_create": True,
            "content_edit": True,
            "content_delete": False,
            "content_publish": True,
            "content_preview": True,
            "section_create": False,
            "section_edit": False,
            "section_delete": False,
            "layout_modify": False,
            "media_upload": True,
            "media_select": True,
            "media_external_import": True,
            "revision_view": True,
            "revision_rollback": False,
            "user_admin": False,
            "role_admin": False,
            "audit_view": True,
            "audit_export": False,
        },
    ],
    "invariants": [
        "Admin cannot self-promote to Super Admin",
        "Admin cannot modify layout or section structure",
        "Admin cannot delete content",
        "Admin cannot rollback revisions",
        "Admin cannot administer users or roles",
        "Admin cannot export audit logs",
    ],
}


class AuthorizationError(Exception):
    """Raised when an operation is not authorized."""

    def __init__(self, message: str, action: str = "", role: str = "") -> None:
        self.message = message
        self.action = action
        self.role = role
        super().__init__(message)


class RBAC:
    """Role-based access control enforcement."""

    def __init__(self, permission_matrix: dict | None = None) -> None:
        if permission_matrix is None:
            permission_matrix = DEFAULT_PERMISSION_MATRIX
        validate_permission_matrix(permission_matrix)
        self._matrix = permission_matrix
        self._permissions: dict[str, dict[str, bool]] = {}
        for perm in permission_matrix["permissions"]:
            self._permissions[perm["role"]] = perm

    def check_permission(self, role: str, action: str) -> bool:
        """Check if a role has permission for an action. Fails closed."""
        if role not in self._permissions:
            return False
        perm = self._permissions[role]
        return perm.get(action, False)

    def require_permission(self, role: str, action: str) -> None:
        """Require a permission or raise AuthorizationError."""
        if not self.check_permission(role, action):
            raise AuthorizationError(
                f"Role '{role}' does not have permission '{action}'",
                action=action,
                role=role,
            )

    def can_create_content(self, role: str) -> bool:
        return self.check_permission(role, "content_create")

    def can_edit_content(self, role: str) -> bool:
        return self.check_permission(role, "content_edit")

    def can_delete_content(self, role: str) -> bool:
        return self.check_permission(role, "content_delete")

    def can_publish_content(self, role: str) -> bool:
        return self.check_permission(role, "content_publish")

    def can_preview_content(self, role: str) -> bool:
        return self.check_permission(role, "content_preview")

    def can_create_section(self, role: str) -> bool:
        return self.check_permission(role, "section_create")

    def can_edit_section(self, role: str) -> bool:
        return self.check_permission(role, "section_edit")

    def can_delete_section(self, role: str) -> bool:
        return self.check_permission(role, "section_delete")

    def can_modify_layout(self, role: str) -> bool:
        return self.check_permission(role, "layout_modify")

    def can_upload_media(self, role: str) -> bool:
        return self.check_permission(role, "media_upload")

    def can_select_media(self, role: str) -> bool:
        return self.check_permission(role, "media_select")

    def can_import_external(self, role: str) -> bool:
        return self.check_permission(role, "media_external_import")

    def can_view_revisions(self, role: str) -> bool:
        return self.check_permission(role, "revision_view")

    def can_rollback_revision(self, role: str) -> bool:
        return self.check_permission(role, "revision_rollback")

    def can_administer_users(self, role: str) -> bool:
        return self.check_permission(role, "user_admin")

    def can_administer_roles(self, role: str) -> bool:
        return self.check_permission(role, "role_admin")

    def can_view_audit(self, role: str) -> bool:
        return self.check_permission(role, "audit_view")

    def can_export_audit(self, role: str) -> bool:
        return self.check_permission(role, "audit_export")

    def validate_role(self, role: str) -> None:
        """Validate that a role value is known. Fails closed."""
        if role not in self._permissions:
            raise AuthorizationError(
                f"Unknown role '{role}'",
                action="validate_role",
                role=role,
            )

    def prevent_self_promotion(
        self, actor_role: str, target_role: str, target_actor_id: str, actor_id: str
    ) -> None:
        """Prevent Admin from self-promoting to Super Admin."""
        if actor_role == "admin" and target_role == "super_admin":
            raise AuthorizationError(
                "Admin cannot promote to Super Admin",
                action="role_change",
                role=actor_role,
            )
        if actor_role == "admin" and target_actor_id == actor_id:
            raise AuthorizationError(
                "Admin cannot modify own role",
                action="role_change",
                role=actor_role,
            )
