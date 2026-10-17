"""Behavioral regression tests for DEC-7301, DEC-7302, and DEC-7303."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from framework.sps2.governance import import_exceptions, legacy_exceptions
from framework.sps2.governance.decision_identifiers import (
    DECISION_ID_PATTERN,
    is_valid_decision_id,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE = "c39694fedd34b0b0e9fa91d24ac543d21ad52c9f"


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def init_repository(root: Path) -> str:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "--quiet")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Repository Test")
    for relative in legacy_exceptions.load_manifest(REPO_ROOT)["exceptions"]:
        path = root / relative["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"pinned {relative['path']}\n", encoding="utf-8")
        if relative["expected_mode"] == "100755":
            path.chmod(0o755)
    git(root, "add", ".")
    git(root, "commit", "--quiet", "-m", "baseline")
    return git(root, "rev-parse", "HEAD")


def write_synthetic_legacy_manifest(root: Path, baseline: str) -> dict:
    manifest = json.loads(
        (REPO_ROOT / legacy_exceptions.MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    manifest["baseline_commit"] = baseline
    for record in manifest["exceptions"]:
        path = root / record["path"]
        record["expected_blob"] = git(root, "hash-object", "--path", str(path), str(path))
        record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    artifact = root / manifest["related_test_artifacts"][0]["path"]
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("updater safety test\n", encoding="utf-8")
    manifest["related_test_artifacts"][0]["sha256"] = hashlib.sha256(
        artifact.read_bytes()
    ).hexdigest()
    path = root / legacy_exceptions.MANIFEST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(manifest))
    return manifest


def verify_synthetic_legacy(root: Path) -> list[str]:
    manifest = json.loads(
        (root / legacy_exceptions.MANIFEST_RELATIVE_PATH).read_text(encoding="utf-8")
    )
    with mock.patch.object(
        legacy_exceptions,
        "EXPECTED_MANIFEST_SHA256",
        hashlib.sha256(canonical_json(manifest)).hexdigest(),
    ):
        return legacy_exceptions.verify_legacy_exceptions(root)


class TestLegacyExceptionContract(unittest.TestCase):
    def test_live_manifest_identity_and_pins_match(self) -> None:
        manifest = legacy_exceptions.load_manifest(REPO_ROOT)
        self.assertEqual(
            hashlib.sha256(canonical_json(manifest)).hexdigest(),
            legacy_exceptions.EXPECTED_MANIFEST_SHA256,
        )
        self.assertEqual(legacy_exceptions.verify_legacy_exceptions(REPO_ROOT), [])

    def test_related_test_artifact_matches(self) -> None:
        manifest = legacy_exceptions.load_manifest(REPO_ROOT)
        artifact = manifest["related_test_artifacts"][0]
        self.assertEqual(
            hashlib.sha256((REPO_ROOT / artifact["path"]).read_bytes()).hexdigest(),
            artifact["sha256"],
        )

    def test_manifest_unknown_field_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = {
                "schema": legacy_exceptions.EXPECTED_SCHEMA,
                "decision_id": "DEC-7301",
                "baseline_commit": BASELINE,
                "exception_count": 8,
                "exceptions": [],
                "related_test_artifacts": [],
                "explicitly_excluded_paths": [],
                "unexpected": True,
            }
            path = root / legacy_exceptions.MANIFEST_RELATIVE_PATH
            path.parent.mkdir(parents=True)
            path.write_bytes(canonical_json(manifest))
            with mock.patch.object(
                legacy_exceptions,
                "EXPECTED_MANIFEST_SHA256",
                hashlib.sha256(canonical_json(manifest)).hexdigest(),
            ):
                with self.assertRaisesRegex(ValueError, "fields do not exactly match"):
                    legacy_exceptions.load_manifest(root)

    def test_manifest_duplicate_path_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = init_repository(root)
            manifest = write_synthetic_legacy_manifest(root, baseline)
            duplicate = dict(manifest["exceptions"][0])
            manifest["exceptions"].pop(1)
            manifest["exceptions"].append(duplicate)
            manifest["exception_count"] = 8
            path = root / legacy_exceptions.MANIFEST_RELATIVE_PATH
            path.write_bytes(canonical_json(manifest))
            with mock.patch.object(
                legacy_exceptions,
                "EXPECTED_MANIFEST_SHA256",
                hashlib.sha256(canonical_json(manifest)).hexdigest(),
            ):
                with self.assertRaisesRegex(ValueError, "duplicate exception path"):
                    legacy_exceptions.load_manifest(root)

    def test_worktree_content_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = init_repository(root)
            write_synthetic_legacy_manifest(root, baseline)
            (root / "scripts/bootstrap-sps.sh").write_text(
                "unexpected edit\n", encoding="utf-8"
            )
            violations = verify_synthetic_legacy(root)
            self.assertTrue(any("worktree blob mismatch" in item for item in violations))

    def test_worktree_mode_change_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = init_repository(root)
            write_synthetic_legacy_manifest(root, baseline)
            os.chmod(root / "scripts/bootstrap-sps.sh", 0o644)
            violations = verify_synthetic_legacy(root)
            self.assertTrue(any("worktree mode mismatch" in item for item in violations))

    def test_deleted_exception_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = init_repository(root)
            write_synthetic_legacy_manifest(root, baseline)
            (root / "scripts/bootstrap-sps.sh").unlink()
            violations = verify_synthetic_legacy(root)
            self.assertTrue(any("missing or unreadable" in item for item in violations))

    def test_symlink_replacement_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = init_repository(root)
            write_synthetic_legacy_manifest(root, baseline)
            target = root / "outside-target.txt"
            target.write_text("outside\n", encoding="utf-8")
            exception = root / "scripts/bootstrap-sps.sh"
            exception.unlink()
            exception.symlink_to(target)
            violations = verify_synthetic_legacy(root)
            self.assertTrue(any("not a regular file" in item for item in violations))

    def test_third_stage_zero_blob_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = init_repository(root)
            write_synthetic_legacy_manifest(root, baseline)
            (root / "scripts/bootstrap-sps.sh").write_text("staged divergence\n")
            git(root, "add", "scripts/bootstrap-sps.sh")
            violations = verify_synthetic_legacy(root)
            self.assertTrue(any("neither baseline nor expected" in item for item in violations))

    def test_non_allowed_legacy_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = init_repository(root)
            write_synthetic_legacy_manifest(root, baseline)
            (root / "scripts/check-update.sh").write_text("unexpected\n")
            git(root, "add", "scripts/check-update.sh")
            violations = legacy_exceptions.verify_legacy_repository(
                root, baseline, ["scripts"]
            )
            self.assertTrue(any("legacy modified: scripts/check-update.sh" in item for item in violations))

    def test_check_update_mirror_is_not_exempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            baseline = init_repository(root)
            write_synthetic_legacy_manifest(root, baseline)
            (root / "scripts/check-update.sh").write_text("mirror edit\n")
            git(root, "add", "scripts/check-update.sh")
            violations = legacy_exceptions.verify_legacy_repository(
                root, baseline, ["scripts/check-update.sh"]
            )
            self.assertTrue(any("scripts/check-update.sh" in item for item in violations))


class TestImportExceptionContract(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.modules = ("indexing", "metadata", "model", "audit")
        for module in self.modules:
            path = self.root / f"consumer_{module}.py"
            path.write_text(
                f"from framework.domain.seo.{module} import approved_symbol\n",
                encoding="utf-8",
            )
        self.write_manifest()

    def tearDown(self) -> None:
        # Single tearDown: both cleanup obligations (temporary directory and
        # the manifest-hash mock patcher) must run. A second tearDown
        # definition elsewhere in this class would silently override this
        # one, so the patcher stop is kept here with the cleanup.
        if self.patcher:
            self.patcher.stop()
            self.patcher = None
        self.temp.cleanup()

    def write_manifest(self) -> None:
        manifest = {
            "schema": import_exceptions.EXPECTED_SCHEMA,
            "decision_id": "DEC-7302",
            "baseline_commit": BASELINE,
            "exception_count": 4,
            "exceptions": [
                {
                    "file": f"consumer_{module}.py",
                    "module": f"framework.domain.seo.{module}",
                    "symbols": ["approved_symbol"],
                    "authorization": "DEC-7302",
                }
                for module in self.modules
            ],
            "forbidden_import_forms": [
                "module imports",
                "star imports",
                "duplicate source symbols",
                "dynamic imports",
            ],
        }
        path = self.root / import_exceptions.MANIFEST_RELATIVE_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json(manifest))
        self.patcher = mock.patch.object(
            import_exceptions,
            "EXPECTED_MANIFEST_SHA256",
            hashlib.sha256(canonical_json(manifest)).hexdigest(),
        )
        self.patcher.start()

    # NOTE: no second tearDown here. An earlier duplicate tearDown at this
    # spot silently overrode the class's first definition, so the temporary
    # directory cleanup never ran and ResourceWarnings were emitted on every
    # focused run. The single tearDown above handles both obligations.

    def scan(self) -> dict:
        return import_exceptions.scan_import_exceptions(self.root)

    def test_live_approved_imports_are_exact(self) -> None:
        self.patcher.stop()
        self.patcher = None
        result = import_exceptions.scan_import_exceptions(REPO_ROOT)
        self.assertEqual(len(result["approved"]), 8)
        self.assertIn(
            {
                "file": "framework/domain/frontend/home_render.py",
                "module": "framework.domain.seo.model",
                "symbol": "RobotsConfig",
                "local_alias": "RobotsConfig",
            },
            result["approved"],
        )
        self.assertIn(
            {
                "file": "framework/domain/frontend/tests/test_home_render.py",
                "module": "framework.domain.seo.audit",
                "symbol": "audit_directory",
                "local_alias": "audit_directory",
            },
            result["approved"],
        )

    def test_local_alias_of_approved_symbol_is_allowed(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "from framework.domain.seo.model import approved_symbol as Config\n",
            encoding="utf-8",
        )
        result = self.scan()
        self.assertTrue(any(item["local_alias"] == "Config" for item in result["approved"]))

    def test_unlisted_symbol_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "from framework.domain.seo.model import approved_symbol, unlisted_symbol\n",
            encoding="utf-8",
        )
        self.assertTrue(any("unapproved" in item for item in self.scan()["violations"]))

    def test_module_import_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "import framework.domain.seo.model\n", encoding="utf-8"
        )
        self.assertTrue(any("module import" in item for item in self.scan()["violations"]))

    def test_aliased_module_import_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "import framework.domain.seo.model as model\n", encoding="utf-8"
        )
        self.assertTrue(any("module import" in item for item in self.scan()["violations"]))

    def test_star_import_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "from framework.domain.seo.model import *\n", encoding="utf-8"
        )
        self.assertTrue(any("star import" in item for item in self.scan()["violations"]))

    def test_duplicate_source_symbol_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "from framework.domain.seo.model import approved_symbol as One\n"
            "from framework.domain.seo.model import approved_symbol as Two\n",
            encoding="utf-8",
        )
        self.assertTrue(any("duplicate source symbol" in item for item in self.scan()["violations"]))

    def test_dynamic_domain_seo_import_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "__import__('framework.domain.seo.model')\n", encoding="utf-8"
        )
        self.assertTrue(any("dynamic domain.seo" in item for item in self.scan()["violations"]))

    def test_importlib_domain_seo_import_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "import importlib\nimportlib.import_module('framework.domain.seo.model')\n",
            encoding="utf-8",
        )
        self.assertTrue(any("dynamic domain.seo" in item for item in self.scan()["violations"]))

    def test_aliased_importlib_domain_seo_import_fails(self) -> None:
        """`import importlib as il; il.import_module(...)` must not evade the scan."""
        (self.root / "consumer_model.py").write_text(
            "import importlib as il\nil.import_module('framework.domain.seo.model')\n",
            encoding="utf-8",
        )
        self.assertTrue(any("dynamic domain.seo" in item for item in self.scan()["violations"]))

    def test_rebound_import_module_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "from importlib import import_module\n"
            "loader = import_module\n"
            "loader('framework.domain.seo.model')\n",
            encoding="utf-8",
        )
        self.assertTrue(any("dynamic domain.seo" in item for item in self.scan()["violations"]))

    def test_getattr_rebound_import_module_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "import importlib\n"
            "loader = getattr(importlib, 'import_module')\n"
            "loader('framework.domain.seo.model')\n",
            encoding="utf-8",
        )
        self.assertTrue(any("dynamic domain.seo" in item for item in self.scan()["violations"]))

    def test_subscript_rebound_import_module_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "import importlib\n"
            "loader = importlib.__dict__['import_module']\n"
            "loader('framework.domain.seo.model')\n",
            encoding="utf-8",
        )
        self.assertTrue(any("dynamic domain.seo" in item for item in self.scan()["violations"]))

    def test_direct_getattr_import_module_fails(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "import importlib\n"
            "getattr(importlib, 'import_module')('framework.domain.seo.model')\n",
            encoding="utf-8",
        )
        self.assertTrue(any("dynamic domain.seo" in item for item in self.scan()["violations"]))

    def test_local_import_module_name_is_flagged(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "def import_module(name):\n"
            "    return name\n"
            "import_module('framework.domain.seo.model')\n",
            encoding="utf-8",
        )
        self.assertTrue(any("dynamic domain.seo" in item for item in self.scan()["violations"]))

    def test_relative_domain_seo_import_fails(self) -> None:
        """A relative import resolving into domain.seo must hit the allowlist.

        The file sits at <root>/consumer_model.py, i.e. the project root
        package; `from ..seo.model import ...` would escape the root, which
        fails closed as a violation.
        """
        (self.root / "consumer_model.py").write_text(
            "from ..seo.model import approved_symbol\n",
            encoding="utf-8",
        )
        result = self.scan()
        self.assertTrue(
            any("relative import" in item for item in result["violations"]),
            result["violations"],
        )

    def test_syntax_error_fails_closed(self) -> None:
        (self.root / "consumer_model.py").write_text(
            "from framework.domain.seo.model import\n", encoding="utf-8"
        )
        self.assertTrue(any("parse failed closed" in item for item in self.scan()["violations"]))

    def test_symlinked_consumer_fails(self) -> None:
        target = self.root / "target.py"
        target.write_text("from framework.domain.seo.model import approved_symbol\n")
        path = self.root / "consumer_model.py"
        path.unlink()
        path.symlink_to(target)
        self.assertTrue(any("not a regular file" in item for item in self.scan()["violations"]))

    def test_path_traversal_fails(self) -> None:
        manifest = json.loads(
            (self.root / import_exceptions.MANIFEST_RELATIVE_PATH).read_text("utf-8")
        )
        manifest["exceptions"][0]["file"] = "../consumer_model.py"
        (self.root / import_exceptions.MANIFEST_RELATIVE_PATH).write_bytes(
            canonical_json(manifest)
        )
        with mock.patch.object(
            import_exceptions,
            "EXPECTED_MANIFEST_SHA256",
            hashlib.sha256(canonical_json(manifest)).hexdigest(),
        ):
            self.assertTrue(any("manifest:" in item for item in self.scan()["violations"]))

    def test_missing_approved_dependency_fails(self) -> None:
        (self.root / "consumer_model.py").unlink()
        self.assertTrue(any("approved dependency missing" in item for item in self.scan()["violations"]))


class TestDecisionIdentifierContract(unittest.TestCase):
    def test_duplicate_handoff_and_action_ids_are_flagged(self) -> None:
        """handoff/action records must get the same duplicate-ID guard as the
        other four kinds: a repeated handoff_id/action_id is an append-only
        violation and must produce a visible ERR line, never a clean pass."""
        for kind, key, id_field in (
            ("handoff", "handoffs", "handoff_id"),
            ("action", "actions", "action_id"),
        ):
            with self.subTest(kind=kind):
                record = {id_field: "X-1"}
                if kind == "handoff":
                    record.update(
                        next_allowed_action="a",
                        forbidden_next_action="b",
                        completed=[],
                        not_completed=[],
                        blockers=[],
                    )
                with tempfile.TemporaryDirectory() as temp:
                    path = Path(temp) / "doc.json"
                    path.write_text(
                        json.dumps({key: [record, dict(record)]}),
                        encoding="utf-8",
                    )
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(REPO_ROOT / "framework/sps2/tools/check_sps2.py"),
                            kind,
                            str(path),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(
                    "duplicate %s IDs: ['X-1']" % kind, result.stdout, result.stdout
                )

    def test_historical_and_new_identifiers_are_accepted(self) -> None:
        for value in ("DEC-7301", "DEC-7302", "DEC-7303", "D-P7-C", "D-P10-1", "D-P10-12-A"):
            with self.subTest(value=value):
                self.assertTrue(is_valid_decision_id(value))

    def test_malformed_identifiers_are_rejected(self) -> None:
        for value in (
            "",
            "d-p10-1",
            "D-P10-_BAD",
            "D-P10--1",
            "D-P10-1-",
            "D-1",
            "DEC-72A1",
            "DEC-721",
            "DEC-72011",
            " DEC-7301",
            "DEC-7301 ",
        ):
            with self.subTest(value=value):
                self.assertFalse(is_valid_decision_id(value))

    def test_schema_uses_exact_canonical_pattern(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "framework/sps2/governance/SCHEMAS/decision.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(schema["properties"]["decision_id"]["pattern"], DECISION_ID_PATTERN)

    def test_validator_reports_malformed_id_without_changing_exit_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "decision.json"
            path.write_text(
                json.dumps({"decisions": [{"decision_id": "BAD-ID"}]}),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "framework/sps2/tools/check_sps2.py"), "decision", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("BAD-ID: bad decision_id", result.stdout)

    def test_validator_accepts_historical_d_p_identifier(self) -> None:
        """Both checkers accept a valid historical D-P id with clean stdout.

        Pins the compatibility half of DEC-7303 at the checker level: a
        silent revert of either checker to a DEC-only literal would break
        historical records and must fail here.
        """
        for checker in ("framework/sps2/tools/check_sps2.py", "framework/sps2/tools/check_p3.py"):
            with self.subTest(checker=checker):
                with tempfile.TemporaryDirectory() as temp:
                    path = Path(temp) / "decision.json"
                    path.write_text(
                        json.dumps(
                            {"decisions": [{"decision_id": "D-P10-1", "reason": "r", "evidence": ["e"], "approval": {"state": "PENDING_USER_APPROVAL"}}]}
                        ),
                        encoding="utf-8",
                    )
                    args = [sys.executable, str(REPO_ROOT / checker), "decision", str(path)]
                    if checker.endswith("check_p3.py"):
                        args = [sys.executable, str(REPO_ROOT / checker), "records", "decisions", str(path)]
                    result = subprocess.run(
                        args,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "", result.stdout)

    def test_missing_decision_identifiers_module_fails_visibly(self) -> None:
        """Negative control for the empty-stdout-as-PASS hole.

        If decision_identifiers.py is absent from a deployed tree, an unguarded
        import would abort with a traceback on stderr and EMPTY stdout — and
        assert_clean in the shell validators scores empty stdout as a PASS, so
        every record would be scored clean without ever being checked. Both
        checkers must instead emit a visible ERR line on stdout.
        """
        for checker in ("framework/sps2/tools/check_sps2.py", "framework/sps2/tools/check_p3.py"):
            with self.subTest(checker=checker):
                with tempfile.TemporaryDirectory() as temp:
                    # Isolated copy of the tools + governance tree so the
                    # module can be deleted without touching the worktree.
                    sandbox = Path(temp) / "repo"
                    (sandbox / "framework/sps2/tools").mkdir(parents=True)
                    (sandbox / "framework/sps2/governance").mkdir(parents=True)
                    (sandbox / "framework/sps2/capability").mkdir(parents=True)
                    for item in (REPO_ROOT / "framework/sps2/tools").glob("*.py"):
                        shutil.copy2(item, sandbox / "framework/sps2/tools" / item.name)
                    for item in (REPO_ROOT / "framework/sps2/governance").glob("*.py"):
                        shutil.copy2(item, sandbox / "framework/sps2/governance" / item.name)
                    for item in (REPO_ROOT / "framework/sps2/governance").glob("*.json"):
                        shutil.copy2(item, sandbox / "framework/sps2/governance" / item.name)
                    # check_p3.py also imports engine from framework/sps2/capability.
                    for item in (REPO_ROOT / "framework/sps2/capability").glob("*.py"):
                        shutil.copy2(item, sandbox / "framework/sps2/capability" / item.name)
                    # The module under test is REMOVED, not copied.
                    (sandbox / "framework/sps2/governance/decision_identifiers.py").unlink()
                    # The REAL attribution policy, so the attribution guard (a
                    # separate failure mode, already covered) stays green and
                    # this test isolates the decision-identifier guard.
                    shutil.copy2(
                        REPO_ROOT / "framework/sps2/governance/attribution_policy.json",
                        sandbox / "framework/sps2/governance/attribution_policy.json",
                    )
                    decision = sandbox / "decision.json"
                    decision.write_text(
                        json.dumps({"decisions": [{"decision_id": "DEC-0001"}]}),
                        encoding="utf-8",
                    )
                    args = [sys.executable, str(sandbox / checker), "decision", str(decision)]
                    if checker.endswith("check_p3.py"):
                        args = [sys.executable, str(sandbox / checker), "records", "decisions", str(decision)]
                    result = subprocess.run(
                        args,
                        capture_output=True,
                        text=True,
                        check=False,
                        cwd=str(sandbox),
                    )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("ERR\t", result.stdout, result.stdout)
                self.assertIn("decision-identifier policy unavailable", result.stdout)


if __name__ == "__main__":
    unittest.main()
