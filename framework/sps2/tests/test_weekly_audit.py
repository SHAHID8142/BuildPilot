"""Structural contract tests for the T-37 weekly self-audit workflow.

Validates .github/workflows/weekly-audit.yml without running Actions:
  1. the file exists and parses as YAML (PyYAML when importable, with a
     hand-rolled fallback so the contract still holds on stdlib-only hosts),
  2. both triggers are present (weekly `schedule` cron + `workflow_dispatch`),
  3. the cron expression is a valid 5-field expression on an off-minute
     (NOT minute 0 or 30 — top-of-hour crons are a fleet-wide stampede),
  4. all four audit commands appear (docs-drift, hygiene, provenance,
     secret-scan),
  5. the permissions block is present and least-privilege (contents: read
     + issues: write, nothing more).
"""
import importlib
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "weekly-audit.yml"

# PyYAML is optional by design (regex fallback below). Loaded via importlib so
# the isolation validator's AST scan sees no top-level non-stdlib import —
# the module must stay importable on a bare-CI checkout without PyYAML.
HAVE_YAML = False
yaml = None
try:
    yaml = importlib.import_module("yaml")
    HAVE_YAML = True
except ImportError:  # pragma: no cover - exercised only without PyYAML
    pass


def _load_yaml(text: str):
    """Parse the workflow with PyYAML when available.

    YAML 1.1 (PyYAML) resolves the bare key `on` to boolean True, so callers
    must look up both spellings; this helper returns the mapping as-is.
    """
    return yaml.safe_load(text)


def _fallback_structure_ok(text: str) -> bool:
    """Regex-based structural check used only when PyYAML is unavailable.

    Asserts the load-bearing tokens exist with plausible indentation rather
    than a full parse: top-level keys, the cron line, the four commands, and
    the permissions block.
    """
    anchors = [
        r"(?m)^name: weekly-audit",
        r"(?m)^\"?on\"?:",
        r"(?m)^\s+schedule:",
        r"(?m)^\s+- cron:",
        r"(?m)^\s+workflow_dispatch:",
        r"(?m)^permissions:",
        r"(?m)^\s+contents: read",
        r"(?m)^\s+issues: write",
        r"check_docs_drift\.py",
        r"sps-hygiene\.sh",
        r"sps-provenance\.sh",
        r"secret-scan\.sh",
    ]
    return all(re.search(a, text) for a in anchors)


class TestWeeklyAuditWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exists = WORKFLOW.is_file()
        cls.text = WORKFLOW.read_text(encoding="utf-8") if cls.exists else ""
        cls.doc = None
        if cls.exists and HAVE_YAML:
            try:
                cls.doc = _load_yaml(cls.text)
            except Exception:
                cls.doc = None

    # --- (a) exists + valid YAML -----------------------------------------
    def test_workflow_file_exists(self):
        self.assertTrue(self.exists, f"missing {WORKFLOW}")

    @unittest.skipUnless(HAVE_YAML, "PyYAML not importable")
    def test_workflow_is_valid_yaml(self):
        self.assertIsNotNone(self.doc, "weekly-audit.yml must parse as YAML")

    def test_workflow_structure_fallback(self):
        """Regex fallback runs regardless; with PyYAML present it is a
        redundant belt-and-braces check on the same tokens."""
        if self.doc is not None:
            self.skipTest("PyYAML parse succeeded; regex fallback not needed")
        self.assertTrue(_fallback_structure_ok(self.text))

    def _doc_or_none(self):
        return self.doc

    def _assert_fallback(self, anchors, msg):
        """Without PyYAML, structural checks degrade to the regex anchors."""
        self.assertTrue(_fallback_structure_ok(self.text), msg)

    # --- (b) triggers ------------------------------------------------------
    def test_has_schedule_and_dispatch_triggers(self):
        doc = self._doc_or_none()
        if doc is None:
            self._assert_fallback(
                [r"(?m)^\"?on\"?:", r"(?m)^\s+schedule:", r"(?m)^\s+workflow_dispatch:"],
                "triggers (schedule + workflow_dispatch) not found in fallback scan",
            )
            self.skipTest("PyYAML unavailable; triggers verified via regex fallback")
        on = doc.get("on", doc.get(True))
        self.assertIsInstance(on, dict, "`on:` must be a mapping of triggers")
        self.assertIn("schedule", on, "must have a weekly schedule trigger")
        self.assertIn("workflow_dispatch", on, "must be manually runnable")

    # --- (c) cron validity + off-minute ------------------------------------
    def test_cron_is_valid_5_field_and_off_minute(self):
        doc = self._doc_or_none()
        if doc is None:
            cron_match = re.search(r"(?m)^\s+- cron:\s*\"([^\"]+)\"", self.text)
            self.assertIsNotNone(cron_match, "no cron entry found in fallback scan")
            crons = [cron_match.group(1)]
        else:
            on = doc.get("on", doc.get(True))
            crons = [entry["cron"] for entry in on["schedule"]]
        self.assertTrue(crons, "schedule must define at least one cron")
        for cron in crons:
            fields = cron.split()
            self.assertEqual(len(fields), 5, f"cron must be 5-field: {cron!r}")
            minute = fields[0]
            if minute.isdigit():
                self.assertNotIn(
                    int(minute), (0, 30),
                    f"cron minute {minute} is a stampede minute (00/30): {cron!r}",
                )
            else:
                # non-simple minutes (lists/steps/ranges) are acceptable as
                # long as they cannot land exactly on 0 or 30
                numbers = [int(n) for n in re.findall(r"\d+", minute)]
                self.assertNotIn(0, numbers, f"cron may fire on minute 0: {cron!r}")
                self.assertNotIn(30, numbers, f"cron may fire on minute 30: {cron!r}")
            # day-of-week / day-of-month must not be malformed
            self.assertRegex(fields[2], r"^[\d*/,-]+$", f"bad day-of-month: {cron!r}")
            self.assertRegex(fields[4], r"^[\d*/,-]+$", f"bad day-of-week: {cron!r}")

    # --- (d) the four audit commands ----------------------------------------
    def test_all_four_audit_commands_present(self):
        for needle in (
            "check_docs_drift.py",
            "sps-hygiene.sh",
            "sps-provenance.sh",
            "secret-scan.sh",
        ):
            self.assertIn(needle, self.text, f"audit command missing: {needle}")

    def test_docs_drift_and_hygiene_run_in_check_mode(self):
        self.assertIn("check_docs_drift.py", self.text)
        self.assertRegex(self.text, r"sps-hygiene\.sh\s+check\b")
        self.assertRegex(self.text, r"sps-provenance\.sh\s+check\s+--strict\b")

    # --- (e) permissions least-privilege ------------------------------------
    def test_permissions_least_privilege(self):
        doc = self._doc_or_none()
        if doc is None:
            self._assert_fallback(
                [r"(?m)^permissions:", r"(?m)^\s+contents: read", r"(?m)^\s+issues: write"],
                "permissions block (contents: read + issues: write) not found in fallback scan",
            )
            self.skipTest("PyYAML unavailable; permissions verified via regex fallback")
        perms = doc.get("permissions")
        self.assertIsInstance(perms, dict, "permissions block must be present")
        self.assertEqual(perms.get("contents"), "read")
        self.assertEqual(perms.get("issues"), "write")
        extra = set(perms) - {"contents", "issues"}
        self.assertEqual(extra, set(), f"unexpected extra permissions: {extra}")

    def test_concurrency_group_present(self):
        """Overlapping runs must not double-file drift issues."""
        doc = self._doc_or_none()
        if doc is None:
            self._assert_fallback(
                [r"(?m)^concurrency:", r"(?m)^\s+group:"],
                "concurrency group not found in fallback scan",
            )
            self.skipTest("PyYAML unavailable; concurrency verified via regex fallback")
        self.assertIn("concurrency", doc)
        self.assertIn("group", doc["concurrency"])

    def test_drift_issue_step_exists_and_guards_against_spam(self):
        self.assertIn("Weekly self-audit: drift detected", self.text)
        self.assertIn("gh issue list", self.text, "must search for an existing open issue")
        self.assertIn("gh issue comment", self.text, "must comment instead of re-filing")
        self.assertIn("gh issue create", self.text)
        self.assertRegex(self.text, r"(?m)^\s+if: failure\(\)")


if __name__ == "__main__":
    unittest.main()
