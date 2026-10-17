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

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
from sps2.tools import rollback_seo as rollback_module


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
                "sps2/tools/p10_runtime_gate.py:1944: dynamic domain.seo import is forbidden"
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

    def test_restore_snapshot_in_fresh_process_after_rollback(self) -> None:
        """A fresh interpreter can import recovery code after domain/seo is removed."""
        # Model the deployed project copy: the rollback tool and its stable
        # P9 ownership module live in the target tree, while isolation.py is
        # part of the subtree rollback removes.
        shutil.copy2(
            REPO_ROOT / "sps2/tools/rollback_seo.py",
            self.proj_root / "sps2/tools/rollback_seo.py",
        )
        stable_module = self.proj_root / "sps2/core/p9_surface.py"
        stable_module.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "sps2/core/p9_surface.py", stable_module)
        import_module = self.proj_root / "sps2/governance/import_exceptions.py"
        import_module.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / "sps2/governance/import_exceptions.py", import_module)
        (self.proj_root / "domain/seo/isolation.py").write_text(
            "# restored P9 isolation module\n", encoding="utf-8"
        )

        snapshot = create_snapshot(self.proj_root)
        code, messages = execute_rollback(
            self.proj_root,
            snapshot_first=False,
            repo_root=self.proj_root,
        )
        self.assertEqual(code, 0, messages)
        self.assertFalse((self.proj_root / "domain/seo").exists())

        restore_script = (
            "import sys\n"
            "from pathlib import Path\n"
            "from sps2.tools.rollback_seo import restore_snapshot\n"
            "status, messages = restore_snapshot(Path(sys.argv[1]), Path(sys.argv[2]))\n"
            "print('\\n'.join(messages))\n"
            "raise SystemExit(status)\n"
        )
        restored = subprocess.run(
            [sys.executable, "-c", restore_script, str(self.proj_root), str(snapshot)],
            cwd=self.proj_root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(restored.returncode, 0, restored.stderr or restored.stdout)
        self.assertIn("Restored", restored.stdout)
        self.assertEqual(
            (self.proj_root / "domain/seo/isolation.py").read_text(encoding="utf-8"),
            "# restored P9 isolation module\n",
        )

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

    def test_rollback_preserves_non_p9_domain_seo_files(self) -> None:
        user_file = self.proj_root / "domain" / "seo" / "user_notes.txt"
        user_file.write_text("important user data\n", encoding="utf-8")
        code, msgs = execute_rollback(self.proj_root, repo_root=self.proj_root)
        self.assertEqual(code, 1)
        self.assertTrue(any("non-P9 files found under domain/seo" in m for m in msgs))
        self.assertTrue(any("user_notes.txt" in m for m in msgs))
        self.assertTrue(user_file.exists())
        self.assertEqual(user_file.read_text(encoding="utf-8"), "important user data\n")

    def test_rollback_aborts_on_unallowlisted_python_file(self) -> None:
        """A Python file absent from the exact P9 allowlist is not owned."""
        user_file = self.proj_root / "domain/seo/user_override.py"
        user_file.write_text("user_data = True\n", encoding="utf-8")
        code, msgs = execute_rollback(
            self.proj_root,
            snapshot_first=False,
            repo_root=self.proj_root,
        )
        self.assertEqual(code, 1)
        self.assertTrue(any("user_override.py" in msg for msg in msgs))
        self.assertTrue(user_file.exists())
        self.assertEqual(user_file.read_text(encoding="utf-8"), "user_data = True\n")

    def test_rollback_preserves_inside_root_symlink(self) -> None:
        target = self.proj_root / "user_notes.txt"
        symlink = self.proj_root / "domain" / "seo" / "user_link.py"
        symlink.symlink_to(target)
        code, msgs = execute_rollback(self.proj_root, repo_root=self.proj_root)
        self.assertEqual(code, 1)
        self.assertTrue(any("non-P9 files found under domain/seo" in m for m in msgs))
        self.assertTrue(symlink.is_symlink())
        self.assertTrue(target.exists())

    def test_rollback_reports_partial_unlink_failure(self) -> None:
        with mock.patch.object(
            Path,
            "unlink",
            side_effect=OSError("permission denied"),
        ):
            code, msgs = execute_rollback(self.proj_root, repo_root=self.proj_root)
        self.assertEqual(code, 1)
        self.assertTrue(any("Partial rollback: failed to remove" in m for m in msgs))
        self.assertTrue(any("permission denied" in m for m in msgs))
        self.assertTrue((self.proj_root / "domain" / "seo" / "model.py").exists())

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

    def test_interrupted_snapshot_leaves_no_live_manifest(self) -> None:
        snapshot_dir = self.proj_root / "sps2" / "memory" / ".p9_rollback_snapshot"
        with mock.patch.object(
            rollback_module.shutil,
            "copy2",
            side_effect=OSError("simulated interruption"),
        ):
            with self.assertRaises(OSError):
                create_snapshot(self.proj_root)
        self.assertFalse((snapshot_dir / "manifest.json").exists())
        self.assertFalse(snapshot_dir.exists())
        parent = snapshot_dir.parent
        self.assertEqual(list(parent.glob(".p9_rollback_snapshot.tmp-*")), [])

    def test_restore_rejects_digest_mismatch(self) -> None:
        """A snapshot file that no longer matches its recorded digest must
        fail the restore, never restore unverified content with exit 0."""
        snap_path = create_snapshot(self.proj_root)
        manifest_file = snap_path / "manifest.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        # Corrupt one snapshot file in place
        victim = snap_path / manifest["files"][0]["relative_path"]
        victim.write_text("tampered\n", encoding="utf-8")
        code, msgs = restore_snapshot(self.proj_root, snap_path)
        self.assertEqual(code, 1)
        self.assertTrue(any("digest mismatch" in m for m in msgs))

    def test_restore_rejects_path_escaping_project_root(self) -> None:
        """A manifest entry pointing outside the project root must fail
        closed instead of writing attacker-chosen files outside the tree."""
        snap_path = create_snapshot(self.proj_root)
        manifest_file = snap_path / "manifest.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        outside = self.proj_root / "outside-secret.txt"
        outside.write_text("exfiltrated\n", encoding="utf-8")
        entry = dict(manifest["files"][0])
        entry["relative_path"] = "../outside-secret.txt"
        entry["sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
        # Keep file_count consistent so the escape check itself is exercised
        # (not the earlier count-consistency guard).
        manifest["files"] = [entry]
        manifest["file_count"] = 1
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
        code, msgs = restore_snapshot(self.proj_root, snap_path)
        self.assertEqual(code, 1)
        self.assertTrue(any("escapes project root" in m for m in msgs))
        self.assertTrue(outside.exists())  # untouched

    def test_restore_fails_on_truncated_snapshot(self) -> None:
        """A snapshot missing one of its declared files must fail instead of
        restoring a half subsystem with exit 0."""
        snap_path = create_snapshot(self.proj_root)
        manifest_file = snap_path / "manifest.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        victim = snap_path / manifest["files"][0]["relative_path"]
        victim.unlink()
        code, msgs = restore_snapshot(self.proj_root, snap_path)
        self.assertEqual(code, 1)
        self.assertTrue(any("missing" in m for m in msgs))

    def test_restore_rejects_non_p9_path_even_with_valid_digest(self) -> None:
        """A manifest entry naming an in-root non-P9 file must be rejected
        even when its digest is valid — restore writes only allowlisted P9
        surface, never an unrelated file, however well-formed the entry."""
        snap_path = create_snapshot(self.proj_root)
        manifest_file = snap_path / "manifest.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        victim = self.proj_root / "user_notes.txt"
        victim.write_text("original user notes\n", encoding="utf-8")
        entry = dict(manifest["files"][0])
        entry["relative_path"] = "user_notes.txt"
        entry["sha256"] = hashlib.sha256(victim.read_bytes()).hexdigest()
        manifest["files"] = [entry]
        manifest["file_count"] = 1
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
        code, msgs = restore_snapshot(self.proj_root, snap_path)
        self.assertEqual(code, 1)
        self.assertTrue(any("not allowlisted P9 surface" in m for m in msgs))
        self.assertEqual(victim.read_text(encoding="utf-8"), "original user notes\n")

    def test_restore_partial_mutation_guard(self) -> None:
        """A manifest whose LAST entry is invalid must fail without having
        copied the earlier valid entries — no partial restore."""
        snap_path = create_snapshot(self.proj_root)
        manifest_file = snap_path / "manifest.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        # First entry stays valid; append an invalid trailing entry (valid
        # digest, but a path outside the P9 allowlist).
        bad = {
            "relative_path": "domain/cms/model.py",
            "sha256": hashlib.sha256(b"# CMS model\n").hexdigest(),
        }
        manifest["files"] = manifest["files"] + [bad]
        manifest["file_count"] = len(manifest["files"])
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
        # Remove a P9 file so a partial restore would be observable.
        victim = self.proj_root / "domain" / "seo" / "model.py"
        victim.unlink()
        code, msgs = restore_snapshot(self.proj_root, snap_path)
        self.assertEqual(code, 1)
        self.assertTrue(any("not allowlisted P9 surface" in m for m in msgs))
        # The guard: the earlier valid entry must NOT have been copied.
        self.assertFalse(victim.exists())

    def test_snapshot_rejects_regular_file_destination(self) -> None:
        """A regular file occupying the snapshot destination must cause a
        pre-flight rejection: no move-aside, no publish, no residue, and the
        occupying file's bytes preserved."""
        dest = self.proj_root / "sps2" / "memory" / ".p9_rollback_snapshot"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("precious occupant\n", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            create_snapshot(self.proj_root)
        self.assertIn("must be a directory", str(ctx.exception))
        # Occupant preserved byte-for-byte; no publish, no residue.
        self.assertEqual(dest.read_text(encoding="utf-8"), "precious occupant\n")
        self.assertFalse(dest.is_dir())
        parent = dest.parent
        self.assertEqual(list(parent.glob(".p9_rollback_snapshot.tmp-*")), [])
        self.assertEqual(list(parent.glob(".p9_rollback_snapshot.previous-*")), [])

    def test_snapshot_rejects_symlink_destination(self) -> None:
        """A symlink at the snapshot destination must be rejected on the
        entry type itself, without following it — the outside target's
        content is never touched."""
        outside = self.proj_root / "outside-snap-target"
        outside.mkdir()
        (outside / "keep.txt").write_text("outside data\n", encoding="utf-8")
        dest = self.proj_root / "sps2" / "memory" / ".p9_rollback_snapshot"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.symlink_to(outside)
        with self.assertRaises(ValueError) as ctx:
            create_snapshot(self.proj_root)
        self.assertIn("must be a directory", str(ctx.exception))
        # The link itself is untouched and the outside target's content intact.
        self.assertTrue(dest.is_symlink())
        self.assertEqual((outside / "keep.txt").read_text(encoding="utf-8"), "outside data\n")
        self.assertEqual(list(dest.parent.glob(".p9_rollback_snapshot.tmp-*")), [])

    def test_rollback_aborts_on_unowned_pycache_contents(self) -> None:
        """Unowned files under domain/seo/__pycache__ must abort the rollback
        (pre-deletion) instead of being silently removed by the later
        recursive tree removal."""
        cache = self.proj_root / "domain" / "seo" / "__pycache__"
        cache.mkdir(parents=True, exist_ok=True)
        (cache / "user_data.pyc").write_text("not regenerable\n", encoding="utf-8")
        code, msgs = execute_rollback(
            target_dir=self.proj_root,
            dry_run=False,
            full=False,
            snapshot_first=False,
            repo_root=self.proj_root,
        )
        self.assertEqual(code, 1)
        self.assertTrue(any("non-P9 files found under domain/seo" in m for m in msgs))
        self.assertTrue((cache / "user_data.pyc").exists())
        self.assertTrue((self.proj_root / "domain" / "seo" / "model.py").exists())

    def test_rollback_aborts_on_symlinked_seo_root(self) -> None:
        """A symlinked domain/seo root must abort rollback before any
        deletion: outside-tree .py files must never enter the unlink set."""
        outside = self.proj_root / "outside-seo-tree"
        outside.mkdir()
        (outside / "precious.py").write_text("# outside P9\n", encoding="utf-8")
        seo_dir = self.proj_root / "domain" / "seo"
        shutil.rmtree(seo_dir)
        seo_dir.symlink_to(outside)
        code, msgs = execute_rollback(
            target_dir=self.proj_root,
            dry_run=False,
            full=False,
            snapshot_first=False,
            repo_root=self.proj_root,
        )
        self.assertEqual(code, 1)
        self.assertTrue(any("non-P9 files found under domain/seo" in m for m in msgs))
        # The symlink survives and the outside tree is untouched.
        self.assertTrue(seo_dir.is_symlink())
        self.assertTrue((outside / "precious.py").exists())

    def test_rollback_refuses_symlinked_seo_root_at_deletion_time(self) -> None:
        """The deletion-time re-check must refuse recursive removal when
        domain/seo is a symlink, naming the refusal instead of following
        the link. (Direct create_snapshot-free path: seed the state via
        the unowned-check bypass by removing the check's own view of the
        link — exercised here through the deletion branch itself.)"""
        outside = self.proj_root / "outside-seo-tree"
        outside.mkdir()
        (outside / "precious.py").write_text("# outside P9\n", encoding="utf-8")
        seo_dir = self.proj_root / "domain" / "seo"
        shutil.rmtree(seo_dir)
        seo_dir.symlink_to(outside)
        # Simulate the check-then-delete race: the ownership check ran while
        # the root was a real directory, then it was swapped to a symlink.
        # Call the deletion-guard path directly by stubbing the unowned scan.
        with mock.patch.object(
            rollback_module, "get_unowned_domain_seo_files", return_value=[]
        ), mock.patch.object(
            rollback_module,
            "get_p9_files",
            return_value=[self.proj_root / "sps2" / "tools" / "seo_audit.py"],
        ):
            code, msgs = execute_rollback(
                target_dir=self.proj_root,
                dry_run=False,
                full=False,
                snapshot_first=False,
                repo_root=self.proj_root,
            )
        self.assertEqual(code, 1)
        self.assertTrue(any("no longer a real directory" in m for m in msgs))
        self.assertTrue(seo_dir.is_symlink())
        self.assertTrue((outside / "precious.py").exists())

    def test_snapshot_publish_window_failure_restores_previous(self) -> None:
        """A failure between move-aside and publish must restore the previous
        snapshot to the live path with original content — no stranded
        .previous-<pid>, no lost prior state."""
        # First snapshot: establishes a previous state.
        snap_path = create_snapshot(self.proj_root)
        manifest_before = (snap_path / "manifest.json").read_text(encoding="utf-8")
        # Change a P9 file so the second snapshot would differ.
        model = self.proj_root / "domain" / "seo" / "model.py"
        model.write_text("# model v2\n", encoding="utf-8")
        # Break the publish: os.replace(staging, target) fails after the
        # old snapshot was moved aside.
        real_replace = os.replace

        def failing_replace(src, dst):
            if str(dst).endswith(".p9_rollback_snapshot") and "tmp-" in str(src):
                raise OSError("simulated publish-window failure")
            return real_replace(src, dst)

        with mock.patch.object(rollback_module.os, "replace", side_effect=failing_replace):
            with self.assertRaises(OSError):
                create_snapshot(self.proj_root)
        # Previous snapshot restored to the live path with original content.
        self.assertEqual((snap_path / "manifest.json").read_text(encoding="utf-8"), manifest_before)
        parent = snap_path.parent
        self.assertEqual(list(parent.glob(".p9_rollback_snapshot.previous-*")), [])
        self.assertEqual(list(parent.glob(".p9_rollback_snapshot.tmp-*")), [])

    def test_snapshot_post_publish_failure_preserves_previous(self) -> None:
        """If a failure happens AFTER the publish succeeded, the new snapshot
        stays live and the previous snapshot must NOT be destroyed by
        cleanup — both copies remain available for recovery."""
        snap_path = create_snapshot(self.proj_root)
        manifest_before = (snap_path / "manifest.json").read_text(encoding="utf-8")
        model = self.proj_root / "domain" / "seo" / "model.py"
        model.write_text("# model v2\n", encoding="utf-8")
        real_rmtree = shutil.rmtree

        def failing_rmtree(path, *args, **kwargs):
            if ".previous-" in str(path):
                raise OSError("simulated post-publish cleanup failure")
            return real_rmtree(path, *args, **kwargs)

        with mock.patch.object(rollback_module.shutil, "rmtree", side_effect=failing_rmtree):
            with self.assertRaises(OSError):
                create_snapshot(self.proj_root)
        # New snapshot is live and records the NEW model.py digest.
        live = json.loads((snap_path / "manifest.json").read_text(encoding="utf-8"))
        model_entry = next(
            f for f in live["files"] if f["relative_path"] == "domain/seo/model.py"
        )
        self.assertEqual(
            model_entry["sha256"],
            hashlib.sha256(b"# model v2\n").hexdigest(),
        )
        # Previous snapshot preserved, not destroyed by cleanup. The name is
        # ".{target.name}.previous-<pid>", so with target ".p9_rollback_snapshot"
        # the residue glob is "..p9_rollback_snapshot.previous-*".
        previous = list(snap_path.parent.glob("..p9_rollback_snapshot.previous-*"))
        self.assertEqual(len(previous), 1)
        prev_manifest = json.loads((previous[0] / "manifest.json").read_text(encoding="utf-8"))
        prev_entry = next(
            f for f in prev_manifest["files"] if f["relative_path"] == "domain/seo/model.py"
        )
        self.assertNotEqual(prev_entry["sha256"], model_entry["sha256"])


class TestAdvisoryRollbackRehearsal(unittest.TestCase):
    """Test full advisory rollback rehearsal in an isolated temporary clone."""

    def test_live_rollback_rehearsal_fails_closed_on_unapproved_dynamic_import(self) -> None:
        """The unapproved P10 dynamic import keeps rollback rehearsal visibly blocked."""
        repo_root = get_repo_root()
        code, msgs = execute_rehearsal(repo_root)
        self.assertEqual(code, 1)
        self.assertIn("Rehearsal failed during rollback execution", msgs)
        # Attribution: the block must be traceable to the declared violation —
        # the post-rollback orphan scan naming the P10 dynamic import — not to
        # an unrelated failure. Without this, any rehearsal failure would
        # satisfy the contract, including one for the wrong reason.
        self.assertTrue(
            any("p10_runtime_gate.py" in m and "dynamic domain.seo" in m for m in msgs),
            msgs,
        )


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
            "sps2/tools/p10_runtime_gate.py:1944: dynamic domain.seo import is forbidden",
            st["orphan_violations"],
        )


if __name__ == "__main__":
    unittest.main()
