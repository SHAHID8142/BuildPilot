"""Contract tests for the docs-drift checker (T-30).

framework/sps2/tools/check_docs_drift.py verifies that every command-like
reference in the repo's user-facing docs points at something that exists.
These tests pin that it:
1. FIRES on a doc referencing a nonexistent script,
2. passes when the referenced script exists,
3. FIRES when a doc mentions a flag the target script does not have,
4. FIRES on an /sps subcommand absent from SKILL.md Modes / METHOD-CARD,
5. tolerates an absent CHEAT-SHEET.md.

Subprocess-driven against a scratch tree — the live docs are never touched.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOL = REPO_ROOT / "framework" / "sps2" / "tools" / "check_docs_drift.py"


def _run(*args: str):
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


class TestDocsDrift(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.tree = Path(self._temp.name)
        (self.tree / "scripts").mkdir()
        (self.tree / "skill" / "sps").mkdir(parents=True)
        # Minimal SKILL.md Modes section so /sps subcommand validation has a
        # baseline (same shape as the real one).
        (self.tree / "skill" / "sps" / "SKILL.md").write_text(
            "# /sps\n\n## Modes\n\n### Audit\n`/sps audit` → scored audit.\n"
            "### Status\n`/sps status` → dashboard.\n",
            encoding="utf-8",
        )
        (self.tree / "skill" / "sps" / "METHOD-CARD.md").write_text(
            "## Modes\n\n- `/sps` — build\n- `/sps audit` — scored audit\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _write(self, rel: str, text: str) -> Path:
        p = self.tree / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def test_nonexistent_script_fires(self) -> None:
        self._write("USER-GUIDE.md", "Run `bash scripts/no-such-script.sh` first.\n")
        proc = _run(str(self.tree / "USER-GUIDE.md"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("DOCS_DRIFT", proc.stderr)
        self.assertIn("scripts/no-such-script.sh — not found", proc.stderr)

    def test_existing_script_is_clean(self) -> None:
        (self.tree / "scripts" / "real-tool.sh").write_text(
            "#!/usr/bin/env bash\n# real-tool.sh — exists\nset -euo pipefail\n",
            encoding="utf-8",
        )
        self._write("USER-GUIDE.md", "Run `bash scripts/real-tool.sh` first.\n")
        proc = _run(str(self.tree / "USER-GUIDE.md"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("all documented commands exist", proc.stdout)

    def test_flag_not_in_script_fires(self) -> None:
        (self.tree / "scripts" / "real-tool.sh").write_text(
            "#!/usr/bin/env bash\n# Usage: real-tool.sh [--yes]\nset -euo pipefail\n",
            encoding="utf-8",
        )
        self._write(
            "USER-GUIDE.md",
            "Run `bash scripts/real-tool.sh --yes` or `scripts/real-tool.sh --force`.\n",
        )
        proc = _run(str(self.tree / "USER-GUIDE.md"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--force", proc.stderr)
        self.assertIn("not found", proc.stderr)
        # --yes exists in the script: no finding for it
        self.assertNotIn("references --yes", proc.stderr)

    def test_unknown_sps_subcommand_fires(self) -> None:
        self._write("USER-GUIDE.md", "Use `/sps teleport` to jump.\n")
        proc = _run(str(self.tree / "USER-GUIDE.md"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("/sps teleport", proc.stderr)

    def test_documented_sps_subcommand_is_clean(self) -> None:
        self._write("USER-GUIDE.md", "Use `/sps audit` to score.\n")
        proc = _run(str(self.tree / "USER-GUIDE.md"))
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_sps_named_script_subcommand_validated(self) -> None:
        (self.tree / "scripts" / "sps-lesson.sh").write_text(
            "#!/usr/bin/env bash\n# Usage: sps-lesson.sh capture|send|review\ncase \"$1\" in\n  capture) ;;\n  send) ;;\n  review) ;;\nesac\n",
            encoding="utf-8",
        )
        self._write("USER-GUIDE.md", "Run `bash scripts/sps-lesson.sh capture \"t\"`.\n")
        proc = _run(str(self.tree / "USER-GUIDE.md"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self._write("USER-GUIDE.md", "Run `bash scripts/sps-lesson.sh teleport`.\n")
        proc = _run(str(self.tree / "USER-GUIDE.md"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("sps-lesson.sh teleport", proc.stderr)

    def test_absent_doc_tolerated(self) -> None:
        self._write("USER-GUIDE.md", "Use `/sps audit` to score.\n")
        proc = _run(str(self.tree / "USER-GUIDE.md"), str(self.tree / "skill" / "sps" / "CHEAT-SHEET.md"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("absent, tolerated", proc.stdout)

    def test_no_docs_found(self) -> None:
        proc = _run(str(self.tree / "docs" / "GHOST.md"))
        self.assertEqual(proc.returncode, 0)
        self.assertIn("no docs found", proc.stdout)


if __name__ == "__main__":
    unittest.main()
