"""P8 CMS RBAC tests.

Tests for role-based access control enforcement.
"""
from __future__ import annotations

import unittest

from domain.cms.auth import RBAC, AuthorizationError


class TestRBAC(unittest.TestCase):
    """Test RBAC enforcement."""

    def setUp(self) -> None:
        self.rbac = RBAC()

    def test_super_admin_can_create_section(self) -> None:
        """Super Admin is allowed structural operation."""
        self.assertTrue(self.rbac.can_create_section("super_admin"))

    def test_admin_cannot_create_section(self) -> None:
        """Admin is denied structural operation."""
        self.assertFalse(self.rbac.can_create_section("admin"))

    def test_admin_cannot_modify_layout(self) -> None:
        """Admin cannot modify layout."""
        self.assertFalse(self.rbac.can_modify_layout("admin"))

    def test_super_admin_can_modify_layout(self) -> None:
        """Super Admin can modify layout."""
        self.assertTrue(self.rbac.can_modify_layout("super_admin"))

    def test_admin_cannot_delete_content(self) -> None:
        """Admin cannot delete content."""
        self.assertFalse(self.rbac.can_delete_content("admin"))

    def test_admin_cannot_rollback(self) -> None:
        """Admin cannot rollback revisions."""
        self.assertFalse(self.rbac.can_rollback_revision("admin"))

    def test_admin_cannot_administer_roles(self) -> None:
        """Admin cannot administer roles."""
        self.assertFalse(self.rbac.can_administer_roles("admin"))

    def test_admin_cannot_self_promote(self) -> None:
        """Admin cannot self-promote to Super Admin."""
        with self.assertRaises(AuthorizationError):
            self.rbac.prevent_self_promotion("admin", "super_admin", "user1", "user1")

    def test_unauthorized_role_rejected(self) -> None:
        """Unauthorized role values are rejected."""
        with self.assertRaises(AuthorizationError):
            self.rbac.validate_role("superuser")

    def test_fail_closed_behavior(self) -> None:
        """Authorization fails closed for unknown roles."""
        self.assertFalse(self.rbac.check_permission("unknown_role", "content_create"))

    def test_admin_can_create_content(self) -> None:
        """Admin can create content."""
        self.assertTrue(self.rbac.can_create_content("admin"))

    def test_admin_can_publish_content(self) -> None:
        """Admin can publish content."""
        self.assertTrue(self.rbac.can_publish_content("admin"))

    def test_admin_can_upload_media(self) -> None:
        """Admin can upload media."""
        self.assertTrue(self.rbac.can_upload_media("admin"))

    def test_admin_can_view_audit(self) -> None:
        """Admin can view audit."""
        self.assertTrue(self.rbac.can_view_audit("admin"))

    def test_admin_cannot_export_audit(self) -> None:
        """Admin cannot export audit."""
        self.assertFalse(self.rbac.can_export_audit("admin"))


if __name__ == "__main__":
    unittest.main()
