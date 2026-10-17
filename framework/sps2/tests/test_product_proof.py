"""Contract tests for the product-proof validator (framework/sps2/tools/check_product_proof.py).

T-31: a section is not done until the proof exists — the approval packet /
handoff carries the proof itself (test output / screenshot / boot log), not a
claim about it (SECTION-DOD "Product proof"). These tests pin that the
validator:
1. passes (with a note) when there is no .sps/plan.md — not a build project,
2. passes when plan + handoff carry a "Product proof" / "Verification evidence" section,
3. FIRES (PRODUCT_PROOF_MISSING) when plan is approved but the handoff has no proof section,
4. FIRES when plan is approved but .sps/handoff.md is missing entirely,
5. passes with a grace note while the plan is not yet approved.

Runs the validator as a subprocess against a temp repo dir — same invocation
style as test_generated_tests.py, scoped to a scratch directory so the live
tree is never touched.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "framework" / "sps2" / "tools" / "check_product_proof.py"

APPROVED_PLAN = "# SPS Project Plan\n\nStatus: approved\nApproved by: Maryam\n"
DRAFT_PLAN = "# SPS Project Plan\n\nStatus: draft\nApproved by:\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_validator(repo: Path):
    proc = subprocess.run(
        [sys.executable, str(TOOL), str(repo)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return proc.returncode, proc.stdout, proc.stderr


class TestCheckProductProof(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.repo = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def test_no_plan_passes_with_note(self) -> None:
        rc, out, err = _run_validator(self.repo)
        self.assertEqual(rc, 0, f"validator red without plan.md:\n{err}")
        self.assertIn("note: no .sps/plan.md", out)
        self.assertIn("not applicable", out)

    def test_plan_plus_proof_section_passes(self) -> None:
        _write(self.repo / ".sps" / "plan.md", APPROVED_PLAN)
        _write(
            self.repo / ".sps" / "handoff.md",
            "## Handoff\n\n## Product proof\n\n```\nRan 12 tests... OK\n```\n",
        )
        rc, out, err = _run_validator(self.repo)
        self.assertEqual(rc, 0, f"validator red on proof section:\n{err}")
        self.assertIn("proof attached", out)

    def test_plan_plus_verification_evidence_heading_passes(self) -> None:
        _write(self.repo / ".sps" / "plan.md", APPROVED_PLAN)
        _write(
            self.repo / ".sps" / "handoff.md",
            "## Handoff\n\n### Verification evidence\n\nboot log attached\n",
        )
        rc, _out, err = _run_validator(self.repo)
        self.assertEqual(rc, 0, f"validator red on evidence heading:\n{err}")

    def test_plan_without_proof_section_fires(self) -> None:
        _write(self.repo / ".sps" / "plan.md", APPROVED_PLAN)
        _write(self.repo / ".sps" / "handoff.md", "## Handoff\n\nAll done, trust me.\n")
        rc, _out, err = _run_validator(self.repo)
        self.assertEqual(rc, 1)
        self.assertIn("PRODUCT_PROOF_MISSING", err)
        self.assertIn("no 'Product proof'", err)

    def test_plan_without_handoff_fires(self) -> None:
        _write(self.repo / ".sps" / "plan.md", APPROVED_PLAN)
        rc, _out, err = _run_validator(self.repo)
        self.assertEqual(rc, 1)
        self.assertIn("PRODUCT_PROOF_MISSING", err)
        self.assertIn("missing", err)

    def test_unapproved_plan_passes_with_grace_note(self) -> None:
        _write(self.repo / ".sps" / "plan.md", DRAFT_PLAN)
        rc, out, err = _run_validator(self.repo)
        self.assertEqual(rc, 0, f"validator red on unapproved plan:\n{err}")
        self.assertIn("not approved yet", out)

    def test_template_plan_status_line_gets_grace(self) -> None:
        # The shipped plan template lists every status on one line
        # (`Status: draft | pending-approval | approved | rejected | ...`).
        # That is an unfilled template, not an approved plan.
        _write(
            self.repo / ".sps" / "plan.md",
            "# SPS Project Plan\n\nStatus: draft | pending-approval | approved | rejected | superseded\n",
        )
        rc, out, err = _run_validator(self.repo)
        self.assertEqual(rc, 0, f"validator red on template plan:\n{err}")
        self.assertIn("not approved yet", out)

    def test_claim_without_proof_is_not_enough(self) -> None:
        # The exact defect class: a handoff that *claims* verification in
        # prose but carries no proof section must still fail.
        _write(self.repo / ".sps" / "plan.md", APPROVED_PLAN)
        _write(
            self.repo / ".sps" / "handoff.md",
            "## Handoff\n\nTests were run and everything passed. Product proof: yes.\n",
        )
        rc, _out, err = _run_validator(self.repo)
        self.assertEqual(rc, 1)
        self.assertIn("PRODUCT_PROOF_MISSING", err)


if __name__ == "__main__":
    unittest.main()
