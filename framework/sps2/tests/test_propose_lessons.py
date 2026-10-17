"""Contract tests for the lesson proposal tool (framework/sps2/tools/propose_lessons.py).

T-33: lesson auto-proposals are PROPOSALS ONLY. These tests pin that the tool:
1. writes a well-formed proposal file (frontmatter + pattern + evidence) to
   lessons/inbox/ and nowhere else,
2. refuses invalid input (empty/overlong pattern, confidence out of range or
   non-numeric, empty source),
3. lists inbox proposals with status/confidence,
4. refuses promote without --approved-by (and placeholder approvers),
5. promote moves to lessons/accepted/ and does NOT touch LESSONS.md or any
   rule file — it only prints the manual edit,
6. discard moves to lessons/rejected/,
7. never overwrites: a timestamp+slug collision gets a -2 suffix.

Runs the tool as a subprocess against a scratch lessons root (--root) — same
invocation style as test_generated_tests.py, so the live tree is never touched.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "framework" / "sps2" / "tools" / "propose_lessons.py"

PATTERN = "Never gate critical content behind hover; use @media (hover: hover)"
NOW = "20261018-120000"


class TestProposeLessons(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.root = Path(self._temp.name) / "lessons"

    def tearDown(self) -> None:
        self._temp.cleanup()

    # -- helpers ---------------------------------------------------------

    def run_tool(self, *argv: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.root), *argv],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

    def propose(self, *extra: str) -> subprocess.CompletedProcess:
        return self.run_tool(
            "propose",
            "--pattern", PATTERN,
            "--confidence", "0.8",
            "--source", "test scratch project",
            "--now", NOW,
            *extra,
        )

    def propose_with_confidence(self, confidence: str) -> subprocess.CompletedProcess:
        return self.run_tool(
            "propose", "--pattern", PATTERN, "--confidence", confidence,
            "--source", "test scratch project", "--now", NOW,
        )

    def inbox_proposal(self) -> Path:
        matches = sorted((self.root / "inbox").glob("prop-*.md"))
        self.assertEqual(len(matches), 1, f"expected one proposal, got {matches}")
        return matches[0]

    # -- (a) propose writes a well-formed proposal file -------------------

    def test_propose_writes_wellformed_proposal(self) -> None:
        proc = self.propose("--evidence", "DESIGN-GATE.md:41")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        path = self.inbox_proposal()
        self.assertEqual(path.name, "prop-20261018-120000-never-gate-critical-content-behind-hover.md")
        text = path.read_text(encoding="utf-8")
        self.assertIn("status: PROPOSAL", text)
        self.assertIn("confidence: 0.80", text)
        self.assertIn("source: test scratch project", text)
        self.assertIn("date: 2026-10-18", text)
        self.assertIn("evidence: DESIGN-GATE.md:41", text)
        self.assertIn(PATTERN, text)
        # Only the three lesson dirs are created — nothing else in the root.
        self.assertEqual(
            sorted(p.name for p in self.root.iterdir()), ["accepted", "inbox", "rejected"]
        )

    def test_propose_without_evidence_uses_placeholder(self) -> None:
        proc = self.propose()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = self.inbox_proposal().read_text(encoding="utf-8")
        self.assertIn("evidence: none recorded", text)

    # -- (b) invalid input rejected ---------------------------------------

    def test_invalid_confidence_over_one_rejected(self) -> None:
        proc = self.propose_with_confidence("1.5")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_CONFIDENCE:", proc.stderr)
        self.assertFalse((self.root / "inbox").exists())

    def test_invalid_confidence_negative_rejected(self) -> None:
        proc = self.propose_with_confidence("-0.1")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_CONFIDENCE:", proc.stderr)

    def test_invalid_confidence_non_numeric_rejected(self) -> None:
        proc = self.propose_with_confidence("high")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_CONFIDENCE:", proc.stderr)

    def test_empty_pattern_rejected(self) -> None:
        proc = self.run_tool(
            "propose", "--pattern", "   ", "--confidence", "0.5",
            "--source", "s", "--now", NOW,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_PATTERN:", proc.stderr)

    def test_overlong_pattern_rejected(self) -> None:
        proc = self.run_tool(
            "propose", "--pattern", "x" * 201, "--confidence", "0.5",
            "--source", "s", "--now", NOW,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_PATTERN:", proc.stderr)

    def test_multiline_pattern_rejected(self) -> None:
        proc = self.run_tool(
            "propose", "--pattern", "line one\nline two", "--confidence", "0.5",
            "--source", "s", "--now", NOW,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_PATTERN:", proc.stderr)

    def test_empty_source_rejected(self) -> None:
        proc = self.run_tool(
            "propose", "--pattern", "p", "--confidence", "0.5",
            "--source", "", "--now", NOW,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_SOURCE:", proc.stderr)

    # -- (c) list shows it -------------------------------------------------

    def test_list_shows_proposal(self) -> None:
        self.propose()
        proc = self.run_tool("list")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("status=PROPOSAL", proc.stdout)
        self.assertIn("confidence=0.80", proc.stdout)
        self.assertIn("prop-20261018-120000-", proc.stdout)

    def test_list_empty_inbox_exit_zero(self) -> None:
        proc = self.run_tool("list")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("inbox is empty", proc.stdout)

    # -- (d) promote gate ---------------------------------------------------

    def test_promote_without_approved_by_refused(self) -> None:
        self.propose()
        proc = self.run_tool("promote", "--file", self.inbox_proposal().name)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_APPROVED_BY:", proc.stderr)
        self.assertTrue(self.inbox_proposal().exists(), "proposal must stay in inbox")

    def test_promote_placeholder_approved_by_refused(self) -> None:
        self.propose()
        proc = self.run_tool(
            "promote", "--file", self.inbox_proposal().name, "--approved-by", "me"
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_APPROVED_BY:", proc.stderr)
        self.assertTrue(self.inbox_proposal().exists())

    def test_promote_missing_file_refused(self) -> None:
        proc = self.run_tool(
            "promote", "--file", "prop-20261018-000000-nope.md",
            "--approved-by", "Maryam",
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_FILE:", proc.stderr)

    def test_promote_unsafe_file_refused(self) -> None:
        proc = self.run_tool(
            "promote", "--file", "../LESSONS.md", "--approved-by", "Maryam"
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("PROPOSE_FILE:", proc.stderr)

    # -- (e) promote moves to accepted/, never edits LESSONS.md -------------

    def test_promote_moves_to_accepted_and_does_not_touch_lessons_md(self) -> None:
        self.propose()
        name = self.inbox_proposal().name
        before = self.read_live_lessons_md()
        proc = self.run_tool("promote", "--file", name, "--approved-by", "Maryam")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.root / "inbox" / name).exists())
        accepted = self.root / "accepted" / name
        self.assertTrue(accepted.is_file())
        self.assertIn("approved by Maryam", proc.stdout)
        # The manual edit is printed, never applied.
        self.assertIn("Manual edit still required", proc.stdout)
        self.assertEqual(self.read_live_lessons_md(), before, "LESSONS.md must be untouched")

    @staticmethod
    def read_live_lessons_md() -> bytes:
        lessons_md = REPO_ROOT / "skill" / "sps" / "LESSONS.md"
        return lessons_md.read_bytes() if lessons_md.is_file() else b"<missing>"

    # -- (f) discard moves to rejected/ --------------------------------------

    def test_discard_moves_to_rejected(self) -> None:
        self.propose()
        name = self.inbox_proposal().name
        proc = self.run_tool("discard", "--file", name)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.root / "inbox" / name).exists())
        self.assertTrue((self.root / "rejected" / name).is_file())

    # -- (g) collision gets -2 suffix, no overwrite ---------------------------

    def test_collision_gets_suffix_and_never_overwrites(self) -> None:
        self.propose()
        first = self.inbox_proposal()
        original = first.read_text(encoding="utf-8")
        proc = self.propose()  # same --now stamp, same slug
        self.assertEqual(proc.returncode, 0, proc.stderr)
        suffixed = self.root / "inbox" / (first.stem + "-2.md")
        self.assertTrue(suffixed.is_file(), "collision must get a -2 suffix")
        self.assertEqual(
            first.read_text(encoding="utf-8"), original, "first file must be untouched"
        )
        self.assertEqual(len(list((self.root / "inbox").glob("prop-*.md"))), 2)

    def test_triple_collision_gets_3_suffix(self) -> None:
        self.propose()
        self.propose()
        proc = self.propose()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        names = sorted(p.name for p in (self.root / "inbox").glob("prop-*.md"))
        self.assertEqual(len(names), 3)
        self.assertTrue(any(n.endswith("-3.md") for n in names), names)


if __name__ == "__main__":
    unittest.main()
