#!/usr/bin/env python3
"""Subprocess-driven tests for framework/sps2/tools/gen_law_test.py (T-20).

gen_law_test.py is a code GENERATOR, so these tests exercise it as a
subprocess against a scratch copy of the repo (shallow copytree, no .git —
the same pattern the generated tests themselves use), with a fabricated
.sps/law-rejections.jsonl ledger. They prove the tool's human gate actually
gates: nothing lands without --approved-by, hostile ledger values are
refused, and an existing generated test is never silently overwritten.
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


def _make_repo() -> Path:
    """Shallow copy of the repo (no .git) with a fabricated 2-entry ledger."""
    tmp = Path(tempfile.mkdtemp(prefix="gen-law-test-"))
    repo = tmp / "repo"
    shutil.copytree(
        REPO_ROOT,
        repo,
        ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"),
    )
    _write_ledger(
        repo,
        [
            {"check_id": LEDGER_PAIR[0], "target_file": LEDGER_PAIR[1],
             "message": LEDGER_MESSAGE},
            {"check_id": LEDGER_PAIR[0], "target_file": LEDGER_PAIR[1],
             "message": LEDGER_MESSAGE},
        ],
    )
    return repo


def _run_gen(repo: Path, *cli: str) -> subprocess.CompletedProcess:
    # Run the SCRATCH COPY of gen_law_test.py, not the real repo's tool: the
    # generator resolves its output dir (and the default ledger) from
    # Path(__file__), so only a copied script writes inside the scratch copy.
    # The copy is byte-identical (same copytree), so behavior is unchanged.
    return subprocess.run(
        [sys.executable, str(repo / "framework" / "sps2" / "tools" / "gen_law_test.py"),
         *cli],
        capture_output=True,
        text=True,
        cwd=repo,
    )


class GenLawTestSubprocessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="gen-law-test-class-"))
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

    def test_a_list_shows_repeat_rejection_pair(self):
        proc = _run_gen(self.repo, "--list")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(LEDGER_PAIR[0], proc.stdout)
        self.assertIn(LEDGER_PAIR[1], proc.stdout)
        self.assertIn("count=2", proc.stdout)

    def test_b_preview_without_approved_by_writes_nothing(self):
        proc = _run_gen(
            self.repo, "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1]
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("preview only", proc.stdout)
        generated = list((self.repo / "framework" / "sps2" / "tests").glob(
            "test_law_regress_*.py"))
        self.assertEqual(generated, [], f"preview wrote files: {generated}")

    def test_c_approved_by_writes_file_with_headers(self):
        proc = _run_gen(
            self.repo, "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
            "--approved-by", "test-fixture",
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = self.repo / "framework" / "sps2" / "tests" / (
            "test_law_regress_" + LEDGER_PAIR[0].replace("-", "_") + ".py"
        )
        self.assertTrue(out.is_file(), f"not written: {out}")
        text = out.read_text(encoding="utf-8")
        self.assertIn("reviewed by: test-fixture", text)
        self.assertIn(LEDGER_PAIR[0], text)
        self.assertIn(LEDGER_PAIR[1], text)

    def test_d_overwrite_refused_without_force(self):
        target = self.repo / "framework" / "sps2" / "tests" / (
            "test_law_regress_" + LEDGER_PAIR[0].replace("-", "_") + ".py"
        )
        self.assertTrue(target.is_file(), "prerequisite: file from previous test")
        before = target.read_text(encoding="utf-8")
        # A second approval without --force must refuse and leave the file.
        proc = _run_gen(
            self.repo, "--check", LEDGER_PAIR[0], "--file", LEDGER_PAIR[1],
            "--approved-by", "someone-else",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("refusing to overwrite", proc.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), before)

    def test_e_hostile_target_file_refused(self):
        # Traversal and quote-injection target_file values from a hostile
        # ledger must be refused with the unsafe-target error, never
        # interpolated into generated source.
        for hostile in ("../escaped.md", 'x" + import("os") + "y'):
            with self.subTest(target_file=hostile):
                scratch = Path(tempfile.mkdtemp(
                    prefix="gen-law-test-hostile-", dir=self._tmp))
                repo = scratch / "repo"
                shutil.copytree(
                    REPO_ROOT,
                    repo,
                    ignore=shutil.ignore_patterns(
                        ".git", "node_modules", "__pycache__"),
                )
                _write_ledger(
                    repo,
                    [
                        {"check_id": "dod-22", "target_file": hostile,
                         "message": LEDGER_MESSAGE},
                        {"check_id": "dod-22", "target_file": hostile,
                         "message": LEDGER_MESSAGE},
                    ],
                )
                proc = _run_gen(
                    repo, "--check", "dod-22", "--file", hostile,
                    "--approved-by", "test-fixture",
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn("unsafe target_file", proc.stderr)
                self.assertEqual(
                    list((repo / "framework" / "sps2" / "tests").glob(
                        "test_law_regress_*.py")),
                    [],
                    f"hostile target_file {hostile!r} produced a test file",
                )
                shutil.rmtree(scratch, ignore_errors=True)

    def test_f_hostile_check_id_refused(self):
        # A check_id containing '"""' would be interpolated into the
        # generated test's docstring; the tool must refuse it (unsafe
        # check_id error) and write nothing.
        hostile = 'dod"""-inject'
        scratch = Path(tempfile.mkdtemp(
            prefix="gen-law-test-hostile-cid-", dir=self._tmp))
        repo = scratch / "repo"
        shutil.copytree(
            REPO_ROOT,
            repo,
            ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"),
        )
        _write_ledger(
            repo,
            [
                {"check_id": hostile, "target_file": LEDGER_PAIR[1],
                 "message": LEDGER_MESSAGE},
                {"check_id": hostile, "target_file": LEDGER_PAIR[1],
                 "message": LEDGER_MESSAGE},
            ],
        )
        proc = _run_gen(
            repo, "--check", hostile, "--file", LEDGER_PAIR[1],
            "--approved-by", "test-fixture",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("unsafe check_id", proc.stderr)
        self.assertEqual(
            list((repo / "framework" / "sps2" / "tests").glob(
                "test_law_regress_*.py")),
            [],
            "hostile check_id produced a test file",
        )
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
