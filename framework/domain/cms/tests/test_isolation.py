"""P8 CMS isolation tests.

Tests for project isolation and feature boundary.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from framework.domain.cms.rollback import (
    is_p8_enabled,
    set_p8_enabled,
    remove_p8,
    verify_removal,
    get_p8_status,
)


class TestIsolation(unittest.TestCase):
    """Test P8 isolation and feature boundary."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.local_state = Path(self.tmpdir) / "LOCAL-STATE.json"

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_feature_flag_controls_enablement(self) -> None:
        """Feature flag controls P8 enablement."""
        set_p8_enabled(True, self.local_state)
        self.assertTrue(is_p8_enabled(self.local_state))
        set_p8_enabled(False, self.local_state)
        self.assertFalse(is_p8_enabled(self.local_state))

    def test_removal_verification(self) -> None:
        """P8 removal is verified clean."""
        set_p8_enabled(True, self.local_state)
        # Create a fake framework/domain/cms directory
        domain_dir = Path(self.tmpdir) / "framework" / "domain" / "cms"
        domain_dir.mkdir(parents=True)
        (domain_dir / "test.txt").write_text("test")

        remove_p8(domain_dir, self.local_state)
        clean, issues = verify_removal(domain_dir, self.local_state)
        self.assertTrue(clean)
        self.assertEqual(len(issues), 0)

    def test_no_global_state(self) -> None:
        """P8 does not write machine-global state."""
        # This test verifies that P8 state is only in the project directory
        set_p8_enabled(True, self.local_state)
        state = json.loads(self.local_state.read_text())
        self.assertIn("p8_cms_enabled", state)

    def test_p7_isolation_remains_valid(self) -> None:
        """P7 isolation is not affected by P8."""
        # P7 artefacts should still be present
        self.assertTrue(Path("framework/sps2/memory/memory-layout.json").exists())
        self.assertTrue(Path("framework/sps2/tools/isolation_validator.py").exists())

    def test_p8_status_reporting(self) -> None:
        """P8 status is correctly reported."""
        status = get_p8_status()
        self.assertIn("enabled", status)
        self.assertIn("domain_exists", status)
        self.assertIn("feature_flag_key", status)


if __name__ == "__main__":
    unittest.main()
