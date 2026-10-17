"""Contract tests for the client-project scaffold (scripts/sps-init.sh).

T-36: one command scaffolds a fresh CLIENT project for the SPS workflow:
  .sps/, .sps/kickoff.md (empty answer slots), .sps/backups/,
  .sps/agent.md (commented options incl. "# language: plain"),
  .sps/task-queue.md skeleton, and a CHEAT-SHEET.md link/pointer at root.

The scaffold must compose with T-28's kickoff checker
(framework/sps2/tools/check_kickoff.py): after scaffolding, the checker gets
PAST the KICKOFF_NOT_RECORDED check — the kickoff record exists. (Other
checks — KICKOFF_SECTION_MISSING / KICKOFF_ANSWER_EMPTY — still fire until a
human fills the answers in; the script scaffolds questions, not answers.)

Subprocess-driven, scratch temp dirs only; the live repo is never scaffolded.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "sps-init.sh"
MIRROR = REPO_ROOT / "skill" / "sps" / "scripts" / "sps-init.sh"
CHECKER = REPO_ROOT / "framework" / "sps2" / "tools" / "check_kickoff.py"


def _run_scaffold(target: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), str(target)],
        capture_output=True,
        text=True,
        cwd=tempfile.gettempdir(),  # any cwd must work
    )


def _run_checker(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(project)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


class SpsInitScaffoldTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="sps-init-test-")
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name) / "client-project"
        self.project.mkdir()

    # (a) fresh dir -> all expected files/dirs exist, kickoff has question slots
    def test_fresh_scaffold_creates_expected_files(self) -> None:
        proc = _run_scaffold(self.project)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sps = self.project / ".sps"
        for path in [
            sps,
            sps / "backups",
            sps / "kickoff.md",
            sps / "agent.md",
            sps / "task-queue.md",
        ]:
            self.assertTrue(path.exists(), f"missing scaffold output: {path}")
        # CHEAT-SHEET.md exists at root (pointer file when skill not installed)
        self.assertTrue(
            (self.project / "CHEAT-SHEET.md").exists(),
            "missing CHEAT-SHEET.md link/pointer at project root")

        kickoff = (sps / "kickoff.md").read_text(encoding="utf-8")
        # Required sections check_kickoff.py looks for (T-28 contract)
        for heading in ["Project goal", "Deploy target", "Stack",
                        "Content", "CMS"]:
            self.assertIn(f"## {heading}", kickoff,
                          f"kickoff.md missing '## {heading}' section")
        # Answers stay EMPTY: fill-in slots present, no fabricated answers
        self.assertIn("<fill in:", kickoff)
        # agent.md starter carries the commented plain-language option (T-35)
        agent_md = (sps / "agent.md").read_text(encoding="utf-8")
        self.assertIn("# language: plain", agent_md)
        # task-queue skeleton
        tq = (sps / "task-queue.md").read_text(encoding="utf-8")
        self.assertIn("# Task Queue", tq)
        self.assertIn("## doing", tq)
        self.assertIn("## queued", tq)
        # pointer file names where the real cheat sheet lives after install
        pointer = (self.project / "CHEAT-SHEET.md").read_text(encoding="utf-8")
        self.assertIn("skill/sps/CHEAT-SHEET.md", pointer)

    # (b) check_kickoff.py gets PAST KICKOFF_NOT_RECORDED on a scaffolded dir
    def test_checker_kickoff_not_recorded_gone(self) -> None:
        proc = _run_scaffold(self.project)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        chk = _run_checker(self.project)
        self.assertNotIn(
            "KICKOFF_NOT_RECORDED", chk.stderr + chk.stdout,
            "checker still reports KICKOFF_NOT_RECORDED after scaffolding — "
            ".sps/kickoff.md must exist so the check progresses past it")
        # The scaffold does NOT fabricate answers: empty-section violations
        # are expected and correct at this stage.
        self.assertIn("KICKOFF_ANSWER_EMPTY", chk.stderr)

    # (c) re-run is idempotent — existing kickoff.md content unchanged
    def test_rerun_is_idempotent(self) -> None:
        first = _run_scaffold(self.project)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = (self.project / ".sps" / "kickoff.md").read_text(encoding="utf-8")
        # simulate the human having answered one question
        kickoff_path = self.project / ".sps" / "kickoff.md"
        kickoff_path.write_text(
            before.replace("<fill in: what the site/app must do, in the "
                           "client's words>", "Sell ceramics online."),
            encoding="utf-8")
        second = _run_scaffold(self.project)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("kept existing", second.stdout)
        self.assertEqual(
            kickoff_path.read_text(encoding="utf-8"),
            before.replace("<fill in: what the site/app must do, in the "
                           "client's words>", "Sell ceramics online."),
            "re-run clobbered existing kickoff.md content")
        # human answer survived
        self.assertIn("Sell ceramics online.",
                      kickoff_path.read_text(encoding="utf-8"))

    # (d) refuses to run inside the BuildPilot repo (exit 1, nothing created)
    def test_refuses_inside_buildpilot_repo(self) -> None:
        # a scratch dir INSIDE the repo: framework/sps2 is in its ancestry
        with tempfile.TemporaryDirectory(dir=REPO_ROOT,
                                         prefix=".sps-init-repo-try-") as d:
            inside = Path(d)
            proc = _run_scaffold(inside)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("BuildPilot", proc.stderr)
            self.assertFalse((inside / ".sps").exists(),
                             "scaffold created .sps/ inside the BuildPilot repo")
            # and the repo root itself is refused too
            proc_root = subprocess.run(
                ["bash", str(SCRIPT), str(REPO_ROOT)],
                capture_output=True, text=True, cwd=tempfile.gettempdir())
            self.assertEqual(proc_root.returncode, 1)

    # (e) bash -n clean — asserted by actually running bash -n on both copies
    def test_bash_n_clean(self) -> None:
        for path in [SCRIPT, MIRROR]:
            proc = subprocess.run(
                ["bash", "-n", str(path)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0,
                             f"bash -n failed for {path}: {proc.stderr}")

    # mirror law: skill/sps/scripts copy is byte-identical to scripts/ copy
    def test_mirror_byte_identical(self) -> None:
        self.assertTrue(MIRROR.exists(), "mirror skill/sps/scripts/sps-init.sh missing")
        self.assertEqual(
            SCRIPT.read_bytes(), MIRROR.read_bytes(),
            "skill/sps/scripts/sps-init.sh is not byte-identical to scripts/sps-init.sh")

    # CHEAT-SHEET: when the skill IS installed in the project, a symlink is used
    def test_cheat_sheet_symlink_when_skill_installed(self) -> None:
        skill_dir = self.project / "skill" / "sps"
        skill_dir.mkdir(parents=True)
        (skill_dir / "CHEAT-SHEET.md").write_text(
            "# BuildPilot Cheat Sheet (say this, get that)\n", encoding="utf-8")
        proc = _run_scaffold(self.project)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        link = self.project / "CHEAT-SHEET.md"
        self.assertTrue(link.is_symlink(), "expected a symlink to skill/sps/CHEAT-SHEET.md")
        self.assertEqual(link.resolve(), (skill_dir / "CHEAT-SHEET.md").resolve())


if __name__ == "__main__":
    unittest.main()
