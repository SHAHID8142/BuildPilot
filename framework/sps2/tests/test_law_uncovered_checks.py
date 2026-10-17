"""Contract tests for the three law checks that had no negative coverage
(T-20 audit, codexx-target-1 follow-up: law-17 wiring, file-splitting,
legal-compliance). Pattern follows test_law_checker.py: shallow repo copy,
mutate, assert check_laws.py exits 1 with the expected id."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "framework" / "sps2" / "tools" / "check_laws.py"


def _run_on_copy(mutate):
    with tempfile.TemporaryDirectory() as temp:
        tmp = Path(temp) / "repo"
        shutil.copytree(
            REPO_ROOT,
            tmp,
            ignore=shutil.ignore_patterns(
                ".git", "node_modules", "__pycache__", ".tmp-smoke-sps"
            ),
        )
        mutate(tmp)
        proc = subprocess.run(
            [sys.executable, str(tmp / "framework/sps2/tools/check_laws.py")],
            capture_output=True,
            text=True,
            cwd=tmp,
        )
        return proc.returncode, proc.stderr


class TestUncoveredLawChecks(unittest.TestCase):
    def test_law_17_wiring_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            p = tmp / "skill/sps/SKILL-ROUTER.md"
            p.write_text(p.read_text(encoding="utf-8").replace("Tool Consent gate", "REMOVED"))
        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("law-17", err)

    def test_file_splitting_doc_missing_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            (tmp / "skill/sps/FILE-SPLITTING.md").unlink()
        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("file-splitting", err)

    def test_file_splitting_hard_cap_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            p = tmp / "skill/sps/FILE-SPLITTING.md"
            p.write_text(p.read_text(encoding="utf-8").replace("500 lines", "600 lines"))
        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("file-splitting", err)

    def test_legal_compliance_section_fires(self) -> None:
        def mutate(tmp: Path) -> None:
            p = tmp / "skill/sps/LEGAL-COMPLIANCE.md"
            text = p.read_text(encoding="utf-8")
            # Remove one required section heading
            lines = text.splitlines(keepends=True)
            drop = next(i for i, l in enumerate(lines) if l.startswith("## "))
            p.write_text("".join(lines[:drop] + lines[drop + 1 :]))
        rc, err = _run_on_copy(mutate)
        self.assertEqual(rc, 1)
        self.assertIn("legal-compliance", err)


if __name__ == "__main__":
    unittest.main()
