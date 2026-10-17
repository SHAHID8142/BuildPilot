"""P8 CMS audit tests.

Tests for audit log functionality.
"""
from __future__ import annotations

import tempfile
import unittest

from framework.domain.cms.audit import AuditService, AuditError
from framework.domain.cms.persistence import JSONStore


class TestAudit(unittest.TestCase):
    """Test audit log functionality."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.store = JSONStore(self.tmpdir)
        self.hmac_key = b"test-key-for-unit-tests-only"
        self.audit = AuditService(self.store, self.hmac_key)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_event_creation(self) -> None:
        """Audit events are created."""
        entry = self.audit.record("user1", "content_create", "content", "c1")
        self.assertEqual(entry["actor_id"], "user1")
        self.assertEqual(entry["action"], "content_create")
        self.assertEqual(entry["resource_type"], "content")

    def test_provenance_preserved(self) -> None:
        """Actor and action provenance is preserved."""
        entry = self.audit.record("user1", "content_publish", "content", "c1")
        self.assertEqual(entry["actor_id"], "user1")
        self.assertEqual(entry["action"], "content_publish")
        self.assertIn("timestamp", entry)

    def test_tamper_detection(self) -> None:
        """Tampering is detected."""
        self.audit.record("user1", "content_create", "content", "c1")
        self.audit.record("user2", "content_update", "content", "c1")
        valid, errors = self.audit.verify_chain()
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_mutation_rejected(self) -> None:
        """Audit entries cannot be mutated through the API."""
        entry = self.audit.record("user1", "content_create", "content", "c1")
        # No update or delete methods exist
        self.assertFalse(hasattr(self.audit, "update_entry"))
        self.assertFalse(hasattr(self.audit, "delete_entry"))

    def test_secret_absence(self) -> None:
        """Secrets are redacted from audit entries."""
        entry = self.audit.record(
            "user1",
            "content_update",
            "content",
            "c1",
            before_state={"title": "Old", "password": "secret123"},
            after_state={"title": "New", "api_key": "abc123"},
        )
        self.assertEqual(entry["before_state"]["password"], "[REDACTED]")
        self.assertEqual(entry["after_state"]["api_key"], "[REDACTED]")
        self.assertEqual(entry["before_state"]["title"], "Old")

    def test_chain_integrity(self) -> None:
        """Chain integrity is maintained across multiple entries."""
        for i in range(5):
            self.audit.record(f"user{i}", "content_create", "content", f"c{i}")
        valid, errors = self.audit.verify_chain()
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_no_default_key(self) -> None:
        """No default/test key is permitted."""
        with self.assertRaises(AuditError):
            AuditService(self.store, None)


if __name__ == "__main__":
    unittest.main()
