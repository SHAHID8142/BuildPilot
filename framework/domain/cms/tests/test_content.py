"""P8 CMS content/section tests.

Tests for content and section model validation and authorization.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.domain.cms.api import CMSAPI
from framework.domain.cms.auth import AuthorizationError


class TestContentSection(unittest.TestCase):
    """Test content and section operations."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.api = CMSAPI(data_dir=self.tmpdir)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_valid_content_type_accepted(self) -> None:
        """Valid content type is accepted."""
        ct = self.api.create_content_type(
            "super_admin", "Blog Post", [{"name": "title", "type": "string", "required": True}]
        )
        self.assertIn("id", ct)
        self.assertEqual(ct["name"], "Blog Post")

    def test_invalid_content_type_rejected(self) -> None:
        """Invalid content type is rejected."""
        with self.assertRaises(Exception):
            self.api.create_content_type("super_admin", "", [])

    def test_valid_content_accepted(self) -> None:
        """Valid content is accepted."""
        ct = self.api.create_content_type(
            "super_admin", "Blog Post", [{"name": "title", "type": "string", "required": True}]
        )
        content = self.api.create_content(
            "admin", ct["id"], "Test Post", "Test body", "user1"
        )
        self.assertIn("id", content)
        self.assertEqual(content["title"], "Test Post")

    def test_invalid_content_rejected(self) -> None:
        """Invalid content is rejected."""
        with self.assertRaises(Exception):
            self.api.create_content("admin", "nonexistent", "Test", "Body", "user1")

    def test_admin_cannot_create_section(self) -> None:
        """Admin cannot create sections."""
        with self.assertRaises(AuthorizationError):
            self.api.create_section("admin", "Hero", "hero_layout")

    def test_super_admin_can_create_section(self) -> None:
        """Super Admin can create sections."""
        section = self.api.create_section("super_admin", "Hero", "hero_layout")
        self.assertIn("id", section)
        self.assertEqual(section["name"], "Hero")

    def test_admin_cannot_delete_content(self) -> None:
        """Admin cannot delete content."""
        ct = self.api.create_content_type(
            "super_admin", "Blog Post", [{"name": "title", "type": "string", "required": True}]
        )
        content = self.api.create_content(
            "admin", ct["id"], "Test Post", "Test body", "user1"
        )
        with self.assertRaises(AuthorizationError):
            self.api.delete_content("admin", content["id"])

    def test_revision_integrity(self) -> None:
        """Revision integrity is maintained."""
        ct = self.api.create_content_type(
            "super_admin", "Blog Post", [{"name": "title", "type": "string", "required": True}]
        )
        content = self.api.create_content(
            "admin", ct["id"], "Test Post", "Version 1", "user1"
        )
        revisions = self.api.get_revisions("admin", content["id"])
        self.assertEqual(len(revisions), 1)
        self.assertEqual(revisions[0]["body"], "Version 1")

        self.api.update_content("admin", content["id"], body="Version 2")
        revisions = self.api.get_revisions("admin", content["id"])
        self.assertEqual(len(revisions), 2)
        self.assertEqual(revisions[1]["body"], "Version 2")


if __name__ == "__main__":
    unittest.main()
