"""Contract tests for the kickoff-proof check (framework/sps2/tools/check_kickoff.py).

T-28: COMPANY-LIFECYCLE.md Phase 0 requires the kickoff questionnaire to be
answered before any build. check_kickoff.py proves it on disk:
1. no .sps/ at all -> pass with a note (project not started),
2. a complete .sps/kickoff.md -> pass,
3. kickoff.md missing required sections -> fail listing them,
4. build artifacts (.sps/plan.md / src/ / index.html) without kickoff.md
   -> fail KICKOFF_NOT_RECORDED,
5. a section with an empty/placeholder answer -> fail.

Runs the checker as a subprocess against a temp project dir — same invocation
style as test_generated_tests.py; the live tree is never touched.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "framework" / "sps2" / "tools" / "check_kickoff.py"

COMPLETE_KICKOFF = """# Kickoff answers

## Project goal
Sell handmade ceramics online with a small catalog.

## Deploy target
Vercel, client owns the account.

## Stack constraints
No required stack; no banned technologies.

## Content
Client provides copy and photos; English only.

## CMS
Enabled — sps-cms ships with every section.
"""


def _run_checker(project: Path):
    proc = subprocess.run(
        [sys.executable, str(TOOL), str(project)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return proc.returncode, proc.stdout, proc.stderr


class TestCheckKickoff(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.project = Path(self._temp.name) / "proj"

    def tearDown(self) -> None:
        self._temp.cleanup()

    # (a) no .sps at all -> pass with note
    def test_no_sps_passes_with_note(self) -> None:
        self.project.mkdir(parents=True)
        rc, out, err = _run_checker(self.project)
        self.assertEqual(rc, 0, f"checker red on empty project:\n{err}")
        self.assertIn("note: no .sps/", out)
        self.assertIn("kickoff answers recorded", out)

    # (b) complete kickoff.md -> pass
    def test_complete_kickoff_passes(self) -> None:
        (self.project / ".sps").mkdir(parents=True)
        (self.project / ".sps" / "kickoff.md").write_text(COMPLETE_KICKOFF, encoding="utf-8")
        rc, out, err = _run_checker(self.project)
        self.assertEqual(rc, 0, f"checker red on complete kickoff:\n{err}")
        self.assertIn("kickoff answers recorded", out)

    def test_kickoff_answers_md_alias_accepted(self) -> None:
        (self.project / ".sps").mkdir(parents=True)
        (self.project / ".sps" / "kickoff-answers.md").write_text(COMPLETE_KICKOFF, encoding="utf-8")
        rc, _out, err = _run_checker(self.project)
        self.assertEqual(rc, 0, f"checker red on kickoff-answers.md:\n{err}")

    # (c) missing sections -> fail listing them
    def test_missing_sections_fail_listed(self) -> None:
        (self.project / ".sps").mkdir(parents=True)
        (self.project / ".sps" / "kickoff.md").write_text(
            "# Kickoff answers\n\n## Project goal\nA ceramics shop.\n",
            encoding="utf-8",
        )
        rc, _out, err = _run_checker(self.project)
        self.assertEqual(rc, 1)
        self.assertIn("KICKOFF_SECTION_MISSING", err)
        for label in ("deploy target", "stack", "content", "cms"):
            self.assertIn(f"'{label}'", err)

    # (d) build artifacts without kickoff.md -> KICKOFF_NOT_RECORDED
    def test_plan_without_kickoff_fails(self) -> None:
        (self.project / ".sps").mkdir(parents=True)
        (self.project / ".sps" / "plan.md").write_text("# Plan\n", encoding="utf-8")
        rc, _out, err = _run_checker(self.project)
        self.assertEqual(rc, 1)
        self.assertIn("KICKOFF_NOT_RECORDED", err)

    def test_src_without_kickoff_fails(self) -> None:
        (self.project / "src").mkdir(parents=True)
        rc, _out, err = _run_checker(self.project)
        self.assertEqual(rc, 1)
        self.assertIn("KICKOFF_NOT_RECORDED", err)

    def test_index_html_without_kickoff_fails(self) -> None:
        self.project.mkdir(parents=True)
        (self.project / "index.html").write_text("<html></html>", encoding="utf-8")
        rc, _out, err = _run_checker(self.project)
        self.assertEqual(rc, 1)
        self.assertIn("KICKOFF_NOT_RECORDED", err)

    def test_sps_without_kickoff_or_plan_passes(self) -> None:
        # .sps/ exists (e.g. memory only) but nothing built yet -> not applicable
        (self.project / ".sps").mkdir(parents=True)
        (self.project / ".sps" / "agent.md").write_text("memory only\n", encoding="utf-8")
        rc, out, err = _run_checker(self.project)
        self.assertEqual(rc, 0, f"checker red on memory-only .sps:\n{err}")
        self.assertIn("no build artifacts", out)

    # (e) empty/placeholder answer -> fail
    def test_empty_answer_fails(self) -> None:
        (self.project / ".sps").mkdir(parents=True)
        (self.project / ".sps" / "kickoff.md").write_text(
            COMPLETE_KICKOFF.replace("Enabled — sps-cms ships with every section.", ""),
            encoding="utf-8",
        )
        rc, _out, err = _run_checker(self.project)
        self.assertEqual(rc, 1)
        self.assertIn("KICKOFF_ANSWER_EMPTY", err)
        self.assertIn("'cms'", err)

    def test_placeholder_answer_fails(self) -> None:
        (self.project / ".sps").mkdir(parents=True)
        (self.project / ".sps" / "kickoff.md").write_text(
            COMPLETE_KICKOFF.replace("Vercel, client owns the account.", "<to be decided>"),
            encoding="utf-8",
        )
        rc, _out, err = _run_checker(self.project)
        self.assertEqual(rc, 1)
        self.assertIn("KICKOFF_ANSWER_EMPTY", err)
        self.assertIn("placeholder", err)

    def test_missing_project_root_errors(self) -> None:
        rc, _out, _err = _run_checker(self.project)  # never created
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
