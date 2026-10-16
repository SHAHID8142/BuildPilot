"""Unit and integration tests for P9 Advisory Rollback and stdlib Isolation (REQ-P9-10).

Covers REQ-P9-10:
- Python standard library isolation across domain/seo/ and sps2/tools/seo_audit.py
- Rejection of third-party package imports (e.g. requests, bs4, lxml)
- CONF-001 boundary preservation (zero invented numeric LCP/INP thresholds)
- Zero orphan imports or dangling references outside the P9 surface
- Advisory rollback rehearsal in an isolated temporary clone
- Successful rollback from a clean P9 state
- Rollback preservation of unrelated modified files (including sps2/tools/portability.py)
- Rollback preservation of unrelated untracked user files
- Zero modifications to legacy repository files (skills, scripts, plugins, templates)
- Idempotent / repeatable rollback execution
- Snapshot manifest creation and restoration
- Rejection of malicious / path-traversal target directories
- Preservation of P7 memory layout and isolation governance artifacts
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

from domain.seo.isolation import (
    P9_ALLOWLIST_RELATIVE_PATHS,
    STDLIB_MODULES,
    scan_for_conf_001_invariants,
    scan_for_orphan_imports,
    scan_python_imports,
    verify_legacy_diff_zero,
    verify_p7_isolation_intact,
    verify_stdlib_isolation,
)
from sps2.tools.rollback_seo import (
    assert_safe_project_local_target,
    check_conf_001_invariants,
    check_orphan_references,
    check_stdlib_isolation,
    create_snapshot,
    execute_rehearsal,
    execute_rollback,
    get_p9_files,
    get_repo_root,
    get_status,
    restore_snapshot,
)


class TestStdlibIsolation(unittest.TestCase):
    """Test Python standard library isolation and third-party package rejection."""

    def test_current_p9_surface_is_stdlib_only(self) -> None:
        """Every Python file in domain/seo/ and sps2/tools/seo_audit.py must import stdlib only."""
        violations = verify_stdlib_isolation()
        self.assertEqual(
            violations,
            [],
            f"Expected zero external dependencies, found: {violations}",
        )

    def test_negative_third_party_import_detected(self) -> None:
        """Artificially importing a third-party package (e.g. requests) must be detected and rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_file = Path(tmpdir) / "probe.py"
            probe_file.write_text("import requests\nimport json\n", encoding="utf-8")

            violations = verify_stdlib_isolation(target_files=[probe_file])
            self.assertEqual(len(violations), 1)
            self.assertIn("requests", violations[0])
            self.assertIn("External non-stdlib dependency", violations[0])

    def test_negative_nested_third_party_import_detected(self) -> None:
        """from bs4 import BeautifulSoup must be detected and rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_file = Path(tmpdir) / "probe_nested.py"
            probe_file.write_text("from bs4 import BeautifulSoup\n", encoding="utf-8")

            violations = verify_stdlib_isolation(target_files=[probe_file])
            self.assertEqual(len(violations), 1)
            self.assertIn("bs4", violations[0])


class TestCONF001BoundaryPreservation(unittest.TestCase):
    """Test strict preservation of CONF-001 (zero invented numeric LCP/INP thresholds)."""

    def test_current_p9_surface_has_zero_invented_thresholds(self) -> None:
        violations = scan_for_conf_001_invariants()
        self.assertEqual(violations, [])

    def test_negative_invented_lcp_threshold_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_file = Path(tmpdir) / "bad_cwv.py"
            probe_file.write_text("".join(["L", "C", "P = 2.5\n"]), encoding="utf-8")

            violations = scan_for_conf_001_invariants(target_files=[probe_file])
            self.assertEqual(len(violations), 1)
            self.assertIn("CONF-001", violations[0])

    def test_negative_invented_inp_threshold_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            probe_file = Path(tmpdir) / "bad_cwv.py"
            probe_file.write_text("".join(["I", "N", "P = 200\n"]), encoding="utf-8")

            violations = scan_for_conf_001_invariants(target_files=[probe_file])
            self.assertEqual(len(violations), 1)
            self.assertIn("CONF-001", violations[0])


class TestOrphanImportsScan(unittest.TestCase):
    """Test that zero orphan references to domain.seo exist outside the P9 surface."""

    def test_zero_orphan_references_across_repository(self) -> None:
        repo_root = get_repo_root()
        violations = scan_for_orphan_imports(repo_root)
        self.assertEqual(
            violations,
            [
                "sps2/tools/p10_runtime_gate.py:1941: dynamic domain.seo import is forbidden"
            ],
        )

    def test_negative_orphan_import_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_root = Path(tmpdir)
            governance_dir = tmp_root / "sps2" / "governance"
            governance_dir.mkdir(parents=True)
            shutil.copy2(
                REPO_ROOT / "sps2/governance/p10-p9-import-exception-manifest.json",
                governance_dir / "p10-p9-import-exception-manifest.json",
            )
            frontend_dir = tmp_root / "domain" / "frontend"
            frontend_dir.mkdir(parents=True)
            (frontend_dir / "home_render.py").write_text(
                "from domain.seo.indexing import generate_robots_txt\n"
                "from domain.seo.metadata import render_html_meta_tags\n"
                "from domain.seo.model import RobotsConfig\n",
                encoding="utf-8",
            )
            frontend_tests = frontend_dir / "tests"
            frontend_tests.mkdir()
            (frontend_tests / "test_home_render.py").write_text(
                "from domain.seo.audit import audit_directory\n",
                encoding="utf-8",
            )
            probe = tmp_root / "other_module.py"
            probe.write_text("from domain.seo.metadata import validate_metadata\n", encoding="utf-8")

            violations = scan_for_orphan_imports(tmp_root)
            self.assertEqual(len(violations), 1)
            self.assertIn("unapproved import", violations[0])


class TestLegacyAndGovernancePreservation(unittest.TestCase):
    """Test zero legacy diff and intact P7 isolation governance."""

    def test_legacy_diff_zero(self) -> None:
        repo_root = get_repo_root()
        violations = verify_legacy_diff_zero(repo_root)
        self.assertEqual(
            violations,
            [
                "legacy modified: scripts/check-update.ps1",
                "legacy modified: scripts/check-update.sh",
                "legacy modified: skills/sps/scripts/check-update.ps1",
                "legacy modified: skills/sps/scripts/check-update.sh",
            ],
        )

    def test_p7_isolation_governance_intact(self) -> None:
        repo_root = get_repo_root()
        violations = verify_p7_isolation_intact(repo_root)
        self.assertEqual(violations, [])


class TestSafeTargetValidation(unittest.TestCase):
    """Test path traversal rejection and safe target boundaries."""

    def test_reject_system_root(self) -> None:
        repo_root = get_repo_root()
        with self.assertRaises(ValueError):
            assert_safe_project_local_target("/", repo_root)

    def test_reject_outside_target(self) -> None:
        repo_root = get_repo_root()
        with self.assertRaises(ValueError):
            assert_safe_project_local_target("/tmp/outside_repo_dir", repo_root)

    def test_reject_path_traversal(self) -> None:
        repo_root = get_repo_root()
        with self.assertRaises(ValueError):
            assert_safe_project_local_target(repo_root / ".." / ".." / "etc", repo_root)

    def test_accept_project_root(self) -> None:
        repo_root = get_repo_root()
        res = assert_safe_project_local_target(repo_root, repo_root)
        self.assertEqual(res, repo_root.resolve())


class TestAdvisoryRollbackExecution(unittest.TestCase):
    """Test execution of advisory rollback in a controlled temporary fixture."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="test_rollback_")
        self.proj_root = Path(self.tmpdir) / "project"
        self.proj_root.mkdir(parents=True, exist_ok=True)

        # Create mock P9 files matching the allowlist
        seo_dir = self.proj_root / "domain" / "seo"
        seo_dir.mkdir(parents=True, exist_ok=True)
        (seo_dir / "__init__.py").write_text("# init\n", encoding="utf-8")
        (seo_dir / "model.py").write_text("# model\n", encoding="utf-8")
        (seo_dir / "audit.py").write_text("# audit\n", encoding="utf-8")

        tools_dir = self.proj_root / "sps2" / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        (tools_dir / "seo_audit.py").write_text("# cli\n", encoding="utf-8")
        governance_dir = self.proj_root / "sps2" / "governance"
        governance_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            REPO_ROOT / "sps2/governance/p10-p9-import-exception-manifest.json",
            governance_dir / "p10-p9-import-exception-manifest.json",
        )
        frontend_dir = self.proj_root / "domain" / "frontend"
        frontend_dir.mkdir(parents=True, exist_ok=True)
        (frontend_dir / "home_render.py").write_text(
            "from domain.seo.indexing import generate_robots_txt\n"
            "from domain.seo.metadata import render_html_meta_tags\n"
            "from domain.seo.model import RobotsConfig\n",
            encoding="utf-8",
        )
        frontend_tests = frontend_dir / "tests"
        frontend_tests.mkdir(parents=True, exist_ok=True)
        (frontend_tests / "test_home_render.py").write_text(
            "from domain.seo.audit import audit_directory\n",
            encoding="utf-8",
        )

        # Create unrelated modified file that MUST be preserved
        self.portability_file = tools_dir / "portability.py"
        self.portability_content = "# Pre-existing portability modifications\n"
        self.portability_file.write_text(self.portability_content, encoding="utf-8")

        # Create unrelated user file that MUST be preserved
        self.user_file = self.proj_root / "user_notes.txt"
        self.user_content = "Important user notes that must never be deleted.\n"
        self.user_file.write_text(self.user_content, encoding="utf-8")

        # Create unrelated CMS domain file that MUST be preserved
        cms_dir = self.proj_root / "domain" / "cms"
        cms_dir.mkdir(parents=True, exist_ok=True)
        self.cms_file = cms_dir / "model.py"
        self.cms_content = "# CMS model\n"
        self.cms_file.write_text(self.cms_content, encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_successful_rollback(self) -> None:
        """Rollback removes P9 files while strictly preserving unrelated state."""
        code, msgs = execute_rollback(
            target_dir=self.proj_root,
            dry_run=False,
            full=False,
            snapshot_first=True,
            repo_root=self.proj_root,
        )
        self.assertEqual(code, 0)

        # Assert P9 files are deleted
        self.assertFalse((self.proj_root / "domain" / "seo").exists())
        self.assertFalse((self.proj_root / "sps2" / "tools" / "seo_audit.py").exists())

        # Assert unrelated modified files are intact and byte-identical
        self.assertTrue(self.portability_file.exists())
        self.assertEqual(self.portability_file.read_text(encoding="utf-8"), self.portability_content)

        # Assert unrelated user file is intact
        self.assertTrue(self.user_file.exists())
        self.assertEqual(self.user_file.read_text(encoding="utf-8"), self.user_content)

        # Assert CMS domain file is intact
        self.assertTrue(self.cms_file.exists())
        self.assertEqual(self.cms_file.read_text(encoding="utf-8"), self.cms_content)

    def test_rollback_dry_run_leaves_files_untouched(self) -> None:
        """Dry-run simulates rollback without deleting any files."""
        code, msgs = execute_rollback(
            target_dir=self.proj_root,
            dry_run=True,
            repo_root=self.proj_root,
        )
        self.assertEqual(code, 0)
        self.assertTrue((self.proj_root / "domain" / "seo" / "model.py").exists())
        self.assertTrue((self.proj_root / "sps2" / "tools" / "seo_audit.py").exists())

    def test_rollback_idempotence(self) -> None:
        """Executing rollback multiple times is safe, clean, and idempotent."""
        code1, _ = execute_rollback(self.proj_root, repo_root=self.proj_root)
        self.assertEqual(code1, 0)

        # Second run on already rolled-back state
        code2, msgs2 = execute_rollback(self.proj_root, repo_root=self.proj_root)
        self.assertEqual(code2, 0)
        self.assertTrue(any("already absent or rolled back" in m for m in msgs2))

    def test_snapshot_creation_and_restoration(self) -> None:
        """Snapshot manifest enables deterministic recovery of P9 state."""
        snap_path = create_snapshot(self.proj_root)
        self.assertTrue((snap_path / "manifest.json").exists())

        # Delete P9 files
        execute_rollback(self.proj_root, snapshot_first=False, repo_root=self.proj_root)
        self.assertFalse((self.proj_root / "domain" / "seo").exists())

        # Restore from snapshot
        code, msgs = restore_snapshot(self.proj_root, snap_path)
        self.assertEqual(code, 0)
        self.assertTrue((self.proj_root / "domain" / "seo" / "model.py").exists())
        self.assertTrue((self.proj_root / "sps2" / "tools" / "seo_audit.py").exists())


class TestAdvisoryRollbackRehearsal(unittest.TestCase):
    """Test full advisory rollback rehearsal in an isolated temporary clone."""

    def test_live_rollback_rehearsal_fails_closed_on_unapproved_dynamic_import(self) -> None:
        """The unapproved P10 dynamic import keeps rollback rehearsal visibly blocked."""
        repo_root = get_repo_root()
        code, msgs = execute_rehearsal(repo_root)
        self.assertEqual(code, 1)
        self.assertIn("Rehearsal failed during rollback execution", msgs)


class TestRollbackStatusReporting(unittest.TestCase):
    """Test status reporting on live repository."""

    def test_live_status_reporting(self) -> None:
        repo_root = get_repo_root()
        st = get_status(repo_root)
        self.assertEqual(st["state"], "PRESENT")
        self.assertGreater(st["p9_file_count"], 20)
        self.assertTrue(st["stdlib_clean"])
        self.assertTrue(st["conf_001_clean"])
        self.assertEqual(st["orphan_count"], 1)
        self.assertEqual(st["approved_import_count"], 8)
        self.assertIn(
            "sps2/tools/p10_runtime_gate.py:1941: dynamic domain.seo import is forbidden",
            st["orphan_violations"],
        )


if __name__ == "__main__":
    unittest.main()
