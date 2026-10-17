"""P8 CMS publishing tests.

Tests for content publishing workflow.
"""
from __future__ import annotations

import tempfile
import unittest

from framework.domain.cms.api import CMSAPI
from framework.domain.cms.auth import AuthorizationError
from framework.domain.cms.publishing import InvalidTransitionError


class TestPublishing(unittest.TestCase):
    """Test content publishing workflow."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.api = CMSAPI(data_dir=self.tmpdir)
        self.ct = self.api.create_content_type(
            "super_admin", "Blog Post", [{"name": "title", "type": "string", "required": True}]
        )

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _create_content(self) -> dict:
        return self.api.create_content(
            "admin", self.ct["id"], "Test Post", "Test body", "user1"
        )

    def test_valid_transitions_accepted(self) -> None:
        """Valid transitions are accepted."""
        content = self._create_content()
        from framework.domain.cms.publishing import PublishingService
        pub = PublishingService(self.api._service._store, self.api._rbac)
        # draft -> preview
        result = pub.transition("admin", content["id"], "preview")
        self.assertEqual(result["status"], "preview")

        # preview -> published
        result = pub.transition("admin", content["id"], "published")
        self.assertEqual(result["status"], "published")

    def test_invalid_transitions_rejected(self) -> None:
        """Invalid transitions are rejected."""
        content = self._create_content()
        from framework.domain.cms.publishing import PublishingService
        pub = PublishingService(self.api._service._store, self.api._rbac)
        # draft -> archived is invalid
        with self.assertRaises(InvalidTransitionError):
            pub.transition("admin", content["id"], "archived")

    def test_unauthorized_transitions_rejected(self) -> None:
        """Unauthorized transitions are rejected."""
        content = self._create_content()
        from framework.domain.cms.publishing import PublishingService
        pub = PublishingService(self.api._service._store, self.api._rbac)
        # Admin cannot unpublish (published -> draft requires content_publish which admin has)
        # But admin cannot rollback
        pub.transition("admin", content["id"], "published")
        # Admin cannot rollback
        revisions = self.api.get_revisions("admin", content["id"])
        with self.assertRaises(AuthorizationError):
            self.api.rollback_to_revision("admin", content["id"], revisions[0]["id"])

    def test_immutable_revision_behavior(self) -> None:
        """Revisions are immutable."""
        content = self._create_content()
        revisions_before = self.api.get_revisions("admin", content["id"])
        self.api.update_content("admin", content["id"], body="Updated")
        revisions_after = self.api.get_revisions("admin", content["id"])
        # Original revision unchanged
        self.assertEqual(revisions_before[0]["body"], "Test body")
        self.assertEqual(revisions_after[0]["body"], "Test body")
        self.assertEqual(revisions_after[1]["body"], "Updated")

    def test_rollback_authorization(self) -> None:
        """Rollback requires Super Admin."""
        content = self._create_content()
        self.api.update_content("admin", content["id"], body="Version 2")
        revisions = self.api.get_revisions("admin", content["id"])
        # Super Admin can rollback
        result = self.api.rollback_to_revision("super_admin", content["id"], revisions[0]["id"])
        self.assertEqual(result["body"], "Test body")


if __name__ == "__main__":
    unittest.main()
