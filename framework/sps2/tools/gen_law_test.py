#!/usr/bin/env python3
"""gen_law_test.py — T-20 lessons-to-validators automation (test generator).

Reads the rejection ledger ``.sps/law-rejections.jsonl`` (appended by
scripts/sps-lawlog.sh), finds (check_id, target_file) pairs rejected on
>= 2 separate runs, and emits a negative regression test
``framework/sps2/tests/test_law_regress_<check_id_snake>.py`` that replants
the violation in a temp copy of the repo and asserts the law checker
(framework/sps2/tools/check_laws.py) FAILs with the expected check id.

Human gate (LESSONS.md hard rule — nothing auto-lands):
  - WITHOUT --approved-by: the proposed test is printed to stdout, nothing
    is written, exit 0.
  - WITH --approved-by <name>: the test is written with a review header
    naming the approver and the UTC date. An existing file is never
    overwritten unless --force is passed.

check_laws.py has no per-check callables (its checks are inline module
code appending to a global VIOLATIONS list), so every generated test is
subprocess-based: it copies the repo to a tempdir, mutates the copy, and
runs the checker script from the copy — the same invocation pattern as
framework/sps2/tests/test_law_checker.py.

Usage:
  python3 framework/sps2/tools/gen_law_test.py --list
  python3 framework/sps2/tools/gen_law_test.py --check <check_id> --file <path>
  python3 framework/sps2/tools/gen_law_test.py --check <check_id> \
      --file <path> --approved-by <name> [--force]

stdlib only. Regeneration is idempotent per (check_id, target_file).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LEDGER = REPO / ".sps" / "law-rejections.jsonl"
TESTS_DIR = REPO / "framework" / "sps2" / "tests"
GEN_LINE = "GEN_LAW_TEST: preview only — pass --approved-by to write"

# check_id is interpolated into the generated test's docstring and module
# filename (via snake()), so a hostile ledger value containing e.g. `"""`
# could break out of the string literal and inject code. Spaces are allowed
# because real ledger ids contain them (e.g. "dod-22 junk file").
CHECK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]*$")


def _check_check_id(check_id: str) -> str:
    if not CHECK_ID_RE.match(check_id):
        raise ValueError(
            f"unsafe check_id in ledger: {check_id!r} — must match "
            f"^[A-Za-z0-9][A-Za-z0-9 ._-]*$"
        )
    return check_id


def read_ledger(path: Path) -> list[dict]:
    """Parse the JSONL ledger; skip blank/corrupt lines gracefully."""
    if not path.is_file():
        return []
    entries: list[dict] = []
    for i, line in enumerate(
        path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
    ):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            print(f"gen_law_test: skipping corrupt ledger line {i}", file=sys.stderr)
            continue
        if isinstance(obj, dict) and obj.get("check_id") and obj.get("target_file"):
            entries.append(
                {
                    "check_id": str(obj["check_id"]),
                    "target_file": str(obj["target_file"]),
                    "message": str(obj.get("message", "")),
                }
            )
    return entries


def _rel(target_file: str) -> str:
    """Validate a ledger target_file as a safe repo-relative path.

    Blocks absolute paths, traversal, quotes, backslashes and newlines —
    the value is interpolated into generated Python source, so a hostile
    filename from the ledger must never be able to break out of a string
    literal (injection found by second-opinion verification, T-20).
    """
    p = Path(target_file)
    if (
        p.is_absolute()
        or ".." in p.parts
        or not p.parts
        or any(c in target_file for c in ('"', "'", "\\", "\n", "\r", "`", "$"))
    ):
        raise ValueError(f"unsafe target_file in ledger: {target_file!r}")
    return p.as_posix()


def _remove(rel: str, marker: str, repl: str = "") -> list[str]:
    """Mutate lines: strip (or rewrite) a marker inside the target file."""
    return [
        f"p = tmp / {rel!r}",
        f'p.write_text(p.read_text(encoding="utf-8").replace({marker!r}, {repl!r}))',
    ]


def _unlink(rel: str) -> list[str]:
    return [f"(tmp / {rel!r}).unlink()"]


def _marker_after(message: str, sep: str) -> str | None:
    marker = message.split(sep, 1)[-1].strip() if sep in message else ""
    return marker or None


def resolve_fixture(
    check_id: str, target_file: str, message: str
) -> tuple[str, list[str]] | None:
    """Map a ledger rejection to (expected stderr substring, mutate lines).

    Returns None when no fixture template is registered for the check id —
    the caller then refuses to generate rather than emit a vacuous test.
    Extend this function as new checks land in check_laws.py.
    """
    rel = _rel(target_file)
    tgt = f"tmp / {rel!r}"
    cid = check_id.lower()

    # SKILL-ROUTER wiring checks (disambiguate from the .sps budget check)
    if cid.startswith("context-budget") and "SKILL-ROUTER" in message:
        return "context-budget wiring", _remove(rel, "CONTEXT-BUDGET.md")
    if cid.startswith("context-budget"):
        return "context-budget", [
            f'{tgt}.write_text("\\n".join(["x" * 80] * 200))',
        ]
    if cid.startswith("handoff-checkpoint"):
        return "conversation log has 7 entries", [
            'log = "\\n".join(f"- entry {i}" for i in range(7))',
            f"({tgt}).write_text(",
            '    f"# H\\n\\n## Conversation log\\n<!-- Rolling log -->\\n{log}\\n"',
            ")",
        ]
    if cid.startswith("dod-22") or "junk file" in message:
        return "junk file", [
            f"junk = {tgt}",
            "junk.parent.mkdir(parents=True, exist_ok=True)",
            'junk.write_text("junk")',
        ]
    if cid.startswith("dod-24") or "hardcoded-config" in message:
        snippet = '\nBASE = "https://internal-api.mycompany.io/v2"\n'
        return "hardcoded-config", [
            f"target = {tgt}",
            "text = target.read_text(encoding='utf-8') if target.is_file() else ''",
            "target.parent.mkdir(parents=True, exist_ok=True)",
            f"target.write_text(text + {snippet!r})",
        ]
    if cid.startswith("law-17"):
        return "law-17", _remove(rel, "Tool Consent gate first")
    if cid.startswith("hard-law"):
        m = re.search(r"'([^']+)'", message)
        if not m:
            return None
        return f"'{m.group(1)}'", _remove(rel, f"**{m.group(1)}")
    if cid.startswith("section-dod"):
        marker = _marker_after(message, "missing: ")
        return (marker, _remove(rel, marker)) if marker else None
    if cid.startswith("design-gate"):
        marker = _marker_after(message, "missing: ")
        return (marker, _remove(rel, marker)) if marker else None
    if cid.startswith("company-lifecycle"):
        if "LEGAL-COMPLIANCE" in message:
            return "LEGAL-COMPLIANCE", _remove(rel, "LEGAL-COMPLIANCE.md")
        return "G1/G2", _remove(rel, "GATE 2 (G2")
    if cid.startswith("lessons"):
        if "LESSONS.md missing" in message:
            return "LESSONS.md missing", _unlink(rel)
        if "sps-lesson.sh missing" in message:
            return "sps-lesson.sh missing", _unlink(rel)
        if "no-auto-send" in message:
            return "no-auto-send", _remove(rel, "No auto-send")
        if "user-approval" in message:
            return "user-approval", _remove(rel, "user approves")
        return None
    if cid.startswith("legal-compliance"):
        marker = _marker_after(message, "section missing: ")
        if marker:
            return marker, _remove(rel, marker)
        return "LEGAL-COMPLIANCE.md missing", _unlink(rel)
    if cid.startswith("file-splitting"):
        if "missing" in message and "500 lines" not in message:
            return "file-splitting", _unlink(rel)
        return "hard cap", _remove(rel, "500 lines", repl="600 lines")
    return None


def snake(check_id: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z]+", "_", check_id).strip("_").lower()
    return re.sub(r"_+", "_", s) or "unknown"


def class_name(s: str) -> str:
    return "".join(part.capitalize() for part in s.split("_"))


TEMPLATE = '''# AUTO-GENERATED by gen_law_test.py (T-20)
# reviewed by: {reviewer} {date}
"""Auto-generated negative regression test — T-20 lessons-to-validators loop.

Locks in the repeat rejection of ({check_id}, {target_file}) recorded in
.sps/law-rejections.jsonl: the test copies the repo into a temp dir,
replants the violation, and asserts the law checker
(framework/sps2/tools/check_laws.py) exits 1 with the expected FAIL line.

This file was written by framework/sps2/tools/gen_law_test.py and approved
by a human via --approved-by. Do not hand-edit — regenerate instead:

    python3 framework/sps2/tools/gen_law_test.py --check {check_id} \\
        --file {target_file} --approved-by <reviewer>

Invocation pattern follows framework/sps2/tests/test_law_checker.py
(subprocess run of the checker on a shallow repo copy).
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_on_copy(mutate=None):
    """Copy the repo (shallow, no .git) into a tempdir, apply mutate(tmp),
    run the law checker there, return (returncode, stderr)."""
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


class TestLawRegress{cls}(unittest.TestCase):
    """{check_id} must keep firing on {target_file} (repeat-rejection lock)."""

    def test_{method}_fires(self) -> None:
        def mutate(tmp: Path) -> None:
{mutate_body}

        rc, err = _run_on_copy(mutate)
        self.assertEqual(
            rc, 1, "law checker passed — regression fixture did not reproduce"
        )
        self.assertIn({expect!r}, err)


if __name__ == "__main__":
    unittest.main()
'''


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Generate negative law regression tests from the rejection ledger."
    )
    ap.add_argument("--list", action="store_true", help="list repeat rejections (count >= 2)")
    ap.add_argument("--check", help="check_id from the ledger")
    ap.add_argument("--file", dest="target_file", help="target_file from the ledger")
    ap.add_argument("--approved-by", help="reviewer name; required to write anything")
    ap.add_argument("--force", action="store_true", help="allow overwriting an existing test")
    ap.add_argument("--ledger", type=Path, default=LEDGER, help="ledger path override")
    args = ap.parse_args(argv)

    entries = read_ledger(args.ledger)
    if not entries:
        print(f"gen_law_test: ledger empty or missing: {args.ledger}", file=sys.stderr)
    counts = Counter((e["check_id"], e["target_file"]) for e in entries)

    if args.list:
        for (cid, tf), n in sorted(counts.items()):
            if n >= 2:
                print(f"{cid}\t{tf}\tcount={n}")
        return 0

    if not (args.check and args.target_file):
        ap.error("--check and --file are required (or use --list)")

    try:
        _check_check_id(args.check)
    except ValueError as exc:
        print(f"gen_law_test: {exc}", file=sys.stderr)
        return 1

    key = (args.check, args.target_file)
    seen = counts.get(key, 0)
    if seen < 2:
        print(
            f"gen_law_test: ({args.check}, {args.target_file}) seen {seen} time(s) in "
            f"{args.ledger}; a regression test requires >= 2 rejections (--list to inspect).",
            file=sys.stderr,
        )
        return 1

    message = next(
        e["message"] for e in entries if (e["check_id"], e["target_file"]) == key
    )
    try:
        fixture = resolve_fixture(args.check, args.target_file, message)
    except ValueError as exc:
        print(f"gen_law_test: {exc}", file=sys.stderr)
        return 1
    if fixture is None:
        print(
            f"gen_law_test: no fixture template registered for check_id "
            f"{args.check!r} — extend resolve_fixture() in gen_law_test.py; "
            f"refusing to emit a vacuous test.",
            file=sys.stderr,
        )
        return 1
    expect, mutate_entries = fixture
    flat = [ln for entry in mutate_entries for ln in entry.splitlines()]
    body = "\n".join(" " * 12 + ln for ln in flat)

    content = TEMPLATE.format(
        reviewer=args.approved_by or "<unset>",
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        check_id=args.check,
        target_file=args.target_file,
        cls=class_name(snake(args.check)),
        method=snake(args.check),
        mutate_body=body,
        expect=expect,
    )

    if not args.approved_by:
        sys.stdout.write(content)
        print(GEN_LINE)
        return 0

    out = TESTS_DIR / f"test_law_regress_{snake(args.check)}.py"
    if out.exists() and not args.force:
        print(
            f"gen_law_test: refusing to overwrite existing {out} (pass --force to replace).",
            file=sys.stderr,
        )
        return 1
    out.write_text(content, encoding="utf-8")
    print(f"gen_law_test: wrote {out} (reviewed by {args.approved_by})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
