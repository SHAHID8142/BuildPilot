#!/usr/bin/env python3
"""Approval-string validation tests for framework/sps2/tools/gen_law_test.py.

The --approved-by reviewer name is interpolated into the generated test's
header comment, so a multi-line or quote-bearing value could inject
module-level Python that executes when the test battery imports the file.
These tests pin the validation gate: valid names are accepted (and appear
only on the single header comment line), every hostile shape is refused
with a nonzero exit and no file written. Same subprocess-against-scratch-
repo pattern as test_gen_law_test.py.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

LEDGER_PAIR = ("dod-22", "skill/sps/SKILL.md")
LEDGER_MESSAGE = "dod-22: junk file: .tmp-x (remove it)"


def _write_ledger(repo: Path, entries: list[dict]) -> None:
    ledger = repo / ".sps" / "law-rejections.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(
        "".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8"
    )


class GenLawTestApprovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="gen-law-approval-"))
        cls.repo = cls._tmp / "repo"
        shutil.copytree(
            REPO_ROOT,
            cls.repo,
            ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"),
        )
        _write_ledger(
            cls.repo,
            [
                {"check_id": LEDGER_PAIR[0], "target_file": LEDGER_PAIR[1],
                 "message": LEDGER_MESSAGE},
                {"check_id": LEDGER_PAIR[0], "target_file": LEDGER_PAIR[1],
                 "message": LEDGER_MESSAGE},
            ],
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _run_gen(self, *cli: str) -> subprocess.CompletedProcess:
        # Run the SCRATCH COPY of the tool: it resolves its output dir from
        # Path(__file__), so only a copied script writes inside the copy.
        return subprocess.run(
            [sys.executable,
             str(self.repo / "framework" / "sps2" / "tools" / "gen_law_test.py"),
             *cli],
            capture_output=True,
            text=True,
            cwd=self.repo,
        )

    def _generated(self) -> list[Path]:
        return list((self.repo / "framework" / "sps2" / "tests").glob(
            "test_law_regress_*.py"))

    def test_a_valid_names_accepted(self):
        for name in ("Maryam", "reviewer-2", "a.b@x"):
            with self.subTest(name=name):
                proc = self._run_gen(
                    "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
                    "--approved-by", name, "--force",
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                out = self.repo / "framework" / "sps2" / "tests" / (
                    "test_law_regress_dod_22.py")
                self.assertTrue(out.is_file(), f"not written for {name!r}")
                text = out.read_text(encoding="utf-8")
                self.assertIn(f"# reviewed by: {name} ", text)
                out.unlink()

    def test_b_multiline_value_rejected(self):
        proc = self._run_gen(
            "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
            "--approved-by", "evil\nimport os",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid --approved-by value", proc.stderr)
        self.assertEqual(self._generated(), [], "multiline approver wrote a file")

    def test_c_quote_value_rejected(self):
        for hostile in ("o'brien", 'say "hi"', "back`tick"):
            with self.subTest(name=hostile):
                proc = self._run_gen(
                    "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
                    "--approved-by", hostile,
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn("invalid --approved-by value", proc.stderr)
        self.assertEqual(self._generated(), [], "quote-bearing approver wrote a file")

    def test_d_control_char_value_rejected(self):
        proc = self._run_gen(
            "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
            "--approved-by", "evil\x0bimport os",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid --approved-by value", proc.stderr)
        self.assertEqual(self._generated(), [], "control-char approver wrote a file")

    def test_e_carriage_return_value_rejected(self):
        proc = self._run_gen(
            "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
            "--approved-by", "evil\rimport os",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid --approved-by value", proc.stderr)
        self.assertEqual(self._generated(), [], "CR-bearing approver wrote a file")

    def test_f_empty_and_whitespace_rejected(self):
        for hostile in ("", "   "):
            with self.subTest(name=hostile):
                proc = self._run_gen(
                    "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
                    "--approved-by", hostile,
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn("invalid --approved-by value", proc.stderr)
        self.assertEqual(self._generated(), [], "empty approver wrote a file")

    def test_g_over_length_value_rejected(self):
        proc = self._run_gen(
            "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
            "--approved-by", "a" * 81,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid --approved-by value", proc.stderr)
        self.assertEqual(self._generated(), [], "over-length approver wrote a file")

    def test_h_reviewer_appears_only_on_header_comment_line(self):
        name = "header-only-reviewer"
        proc = self._run_gen(
            "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
            "--approved-by", name, "--force",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = self.repo / "framework" / "sps2" / "tests" / (
            "test_law_regress_dod_22.py")
        self.assertTrue(out.is_file())
        lines = out.read_text(encoding="utf-8").splitlines()
        hits = [ln for ln in lines if name in ln]
        self.assertEqual(
            len(hits), 1,
            f"reviewer name appears {len(hits)} times, expected exactly 1: {hits}",
        )
        self.assertTrue(
            hits[0].startswith("# reviewed by: "),
            f"reviewer name not on the header comment line: {hits[0]!r}",
        )
        # The header line is "# reviewed by: <name> <date>" — the name must be
        # followed only by the UTC date, nothing else.
        rest = hits[0][len("# reviewed by: "):].removeprefix(name).strip()
        self.assertRegex(rest, r"^\d{4}-\d{2}-\d{2}$")
        # The whole file must still be importable, single-line header or not.
        compile(out.read_text(encoding="utf-8"), str(out), "exec")


if __name__ == "__main__":
    unittest.main()
