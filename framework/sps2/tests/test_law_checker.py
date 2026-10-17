"""Contract tests for the machine law-checker (framework/sps2/tools/check_laws.py).

The checker turns agent-facing prose laws (SECTION-DOD, HANDOFF-CHECKPOINT,
CONTEXT-BUDGET, hard-law core) into CI gates. These tests pin:
1. the checker passes on the live repo (laws hold), and
2. each check FIRES on a constructed violation (non-vacuous, per the
   repo's negative-suite standard).
"""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "framework" / "sps2" / "tools" / "check_laws.py"

_spec = importlib.util.spec_from_file_location("check_laws", TOOL)
check_laws = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_laws)


def _run_on_copy(mutate=None):
    """Copy the repo (shallow, no .git) into a tempdir, apply mutate(tmp),
    run the checker's main() there, return (returncode, stderr)."""
    import subprocess
    import sys

    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp) / "repo"
        shutil.copytree(
            REPO_ROOT,
            tmp,
            ignore=shutil.ignore_patterns(
                ".git", "node_modules", "__pycache__", ".tmp-smoke-sps"
            ),
        )
        if mutate:
            mutate(tmp)
        proc = subprocess.run(
            [sys.executable, str(tmp / "framework/sps2/tools/check_laws.py")],
            capture_output=True,
            text=True,
            cwd=tmp,
        )
        return proc.returncode, proc.stderr


class TestLawCheckerLiveRepo(unittest.TestCase):
    def test_live_repo_passes(self) -> None:
        rc, err = _run_on_copy()
        self.assertEqual(rc, 0, f"law checker red on live repo:\n{err}")


class TestLawCheckerNegativeSuite(unittest.TestCase):
    """Each case constructs a violation and asserts the check fires."""

    def test_oversized_handoff_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            (tmp / ".sps/handoff.md").write_text("\n".join(["x" * 80] * 200))

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("context-budget", err)

    def test_rolling_log_overflow_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            log = "\n".join(f"- entry {i}" for i in range(7))
            (tmp / ".sps/handoff.md").write_text(
                f"# H\n\n## Conversation log\n<!-- Rolling log -->\n{log}\n"
            )

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("conversation log has 7 entries", err)

    def test_missing_hard_law_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            p = tmp / "skill/sps/SKILL.md"
            p.write_text(p.read_text(encoding="utf-8").replace("**Tool Consent", "**Renamed"))

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("'Tool Consent'", err)

    def test_missing_dod_gap_item_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            p = tmp / "skill/sps/SECTION-DOD.md"
            p.write_text(p.read_text(encoding="utf-8").replace("Concurrency basics", "Concurrency rules"))

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("Concurrency basics", err)

    def test_hardcoded_config_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            target = next((tmp / "framework/domain/cms").rglob("*.py"))
            target.write_text(
                target.read_text(encoding="utf-8")
                + '\nBASE = "https://internal-api.mycompany.io/v2"\n'
            )

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("hardcoded-config", err)

    def test_standards_urls_do_not_fire(self) -> None:
        """schema.org / sitemaps.org constants are allowed (not env config)."""
        rc, err = _run_on_copy()
        self.assertNotIn("schema.org", err)
        self.assertNotIn("sitemaps.org", err)

    def test_junk_file_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            (tmp / "framework/domain/old_module.py.bak").write_text("junk")

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("junk file", err)

    def test_missing_new_dod_law_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            p = tmp / "skill/sps/SECTION-DOD.md"
            p.write_text(p.read_text(encoding="utf-8").replace("Web/API hardening", "Web/API security"))

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("Web/API hardening", err)

    def test_missing_copy_laws_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            p = tmp / "skill/sps/DESIGN-GATE.md"
            p.write_text(p.read_text(encoding="utf-8").replace("No padded copy", "No filler copy"))

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("No padded copy", err)

    def test_missing_g2_gate_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            p = tmp / "skill/sps/COMPANY-LIFECYCLE.md"
            p.write_text(p.read_text(encoding="utf-8").replace("GATE 2 (G2", "GATE 2 (Plan"))

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("G1/G2", err)

    def test_missing_lessons_gate_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            (tmp / "skill/sps/LESSONS.md").unlink()

        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("LESSONS.md missing", err)


if __name__ == "__main__":
    unittest.main()
