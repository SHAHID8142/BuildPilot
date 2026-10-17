#!/usr/bin/env python3
"""propose_lessons.py — T-33 lesson auto-proposals (ECC-inspired, propose-only).

At session end the agent MAY draft lesson candidates (pattern + confidence)
as PROPOSALS ONLY. Proposals are inert data files in ``lessons/inbox/`` —
nothing lands in LESSONS.md or any rule file without the existing
user-approval review flow (skill/sps/LESSONS.md section 4). This tool can
never edit a rule file: ``promote`` moves a proposal to ``lessons/accepted/``
and PRINTS the manual edit the human still has to make.

Subcommands:
  propose --pattern "<one-line pattern>" --confidence 0.8 --source "<where>"
          [--evidence "<file:line or transcript ref>"] [--now YYYYMMDD-HHMMSS]
      Validate inputs and write lessons/inbox/prop-<date>-<time>-<slug>.md
      with structured frontmatter (status: PROPOSAL, confidence, source,
      date) plus the pattern and evidence. Never writes anywhere else.
      A timestamp+slug collision gets a -2, -3 ... suffix — never overwrites.
      --now pins the timestamp (test hook; defaults to local now).
  list
      Print inbox proposals with status/confidence. Exit 0 even when empty.
  promote --file <name> --approved-by <name>
      The ONLY path that moves a proposal out of the inbox: moves it to
      lessons/accepted/ and prints the manual LESSONS.md edit the human must
      still make. Requires a real --approved-by (placeholders like "me",
      "wip", "tbd" are refused). Does NOT edit LESSONS.md or any rule file.
  discard --file <name>
      Move a proposal from the inbox to lessons/rejected/.

lessons/inbox/, lessons/accepted/ and lessons/rejected/ are created on
first use. The lessons root defaults to <repo>/lessons; --root overrides it
(tests use a scratch dir so the live tree is never touched).

Fail-closed style mirrors check_generated_tests.py: errors as
``PROPOSE_*: detail`` on stderr, exit 1; exit 0 on success. Stdlib only.
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = REPO / "lessons"

PATTERN_MAX = 200
INBOX = "inbox"
ACCEPTED = "accepted"
REJECTED = "rejected"

# Placeholder approver names — same spirit as check_generated_tests.py's
# PLACEHOLDER regex for reviewed-by values. An approval must name a person.
PLACEHOLDER = re.compile(
    r"^(<[^>]*>|\?+|tbd\b.*|todo\b.*|pending\b.*|n/?a$|placeholder$"
    r"|your name$|user/date$|me$|myself$|wip\b.*|later\b.*|unset$|anonymous$)",
    re.IGNORECASE,
)

PROPOSAL_TEMPLATE = """---
lesson_id: {lesson_id}
status: PROPOSAL
confidence: {confidence}
source: {source}
date: {date}
evidence: {evidence}
---

## Pattern
{pattern}

## Evidence
{evidence_body}

## Review
PROPOSAL ONLY — inert data. Nothing lands in LESSONS.md or any rule file
without the user-approval review flow (skill/sps/LESSONS.md, section 4).
This tool can never edit rule files; `promote` only moves this file and
prints the suggested manual edit.
"""


class ProposeError(Exception):
    """A fail-closed error: printed as `PROPOSE_<ID>: detail`, exit 1."""

    def __init__(self, check_id: str, detail: str) -> None:
        super().__init__(detail)
        self.check_id = check_id
        self.detail = detail

    def render(self) -> str:
        return f"PROPOSE_{self.check_id}: {self.detail}"


def _one_line(value: str) -> bool:
    return "\n" not in value and "\r" not in value


def validate_pattern(pattern: str) -> str:
    pattern = pattern.strip()
    if not pattern:
        raise ProposeError("PATTERN", "pattern is empty — give a one-line lesson pattern")
    if not _one_line(pattern):
        raise ProposeError("PATTERN", "pattern must be a single line (no newlines)")
    if len(pattern) > PATTERN_MAX:
        raise ProposeError(
            "PATTERN",
            f"pattern is {len(pattern)} chars — max is {PATTERN_MAX}; "
            f"split it into one lesson, one rule",
        )
    return pattern


def validate_confidence(raw: str) -> str:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ProposeError("CONFIDENCE", f"confidence {raw!r} is not a number") from None
    if value != value or value in (float("inf"), float("-inf")):
        raise ProposeError("CONFIDENCE", f"confidence {raw!r} is not a finite number")
    if not 0.0 <= value <= 1.0:
        raise ProposeError(
            "CONFIDENCE", f"confidence {value} out of range — must be a float in 0..1"
        )
    # Canonical, injection-safe rendering for the frontmatter value.
    return f"{value:.2f}"


def validate_source(source: str) -> str:
    source = source.strip()
    if not source:
        raise ProposeError("SOURCE", "source is empty — say where the pattern was observed")
    if not _one_line(source):
        raise ProposeError("SOURCE", "source must be a single line (no newlines)")
    return source


def validate_evidence(evidence: str | None) -> str:
    evidence = (evidence or "").strip()
    if evidence and not _one_line(evidence):
        raise ProposeError("EVIDENCE", "evidence must be a single line (no newlines)")
    return evidence


def validate_approver(approved_by: str | None) -> str:
    name = (approved_by or "").strip()
    if not name:
        raise ProposeError(
            "APPROVED_BY",
            "--approved-by is required to promote — a human must own the approval",
        )
    if not _one_line(name) or PLACEHOLDER.match(name):
        raise ProposeError(
            "APPROVED_BY",
            f"--approved-by value {name!r} is a placeholder — give the real approver name",
        )
    return name


def validate_filename(name: str) -> str:
    if not name or name in (".", "..") or "/" in name or "\\" in name or name.startswith("."):
        raise ProposeError(
            "FILE",
            f"unsafe --file value {name!r} — give the proposal file name as `list` shows it",
        )
    if not name.startswith("prop-") or not name.endswith(".md"):
        raise ProposeError(
            "FILE",
            f"--file {name!r} is not a proposal file name (expected prop-*.md)",
        )
    return name


def slugify(pattern: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z]+", "-", pattern).strip("-").lower()
    s = re.sub(r"-+", "-", s)[:40].strip("-")
    return s or "lesson"


def ensure_dirs(root: Path) -> None:
    for sub in (INBOX, ACCEPTED, REJECTED):
        (root / sub).mkdir(parents=True, exist_ok=True)


def unique_path(directory: Path, stem: str) -> Path:
    """prop-<ts>-<slug>.md, colliding to -2, -3 ... — never overwrites."""
    candidate = directory / f"{stem}.md"
    n = 2
    while candidate.exists():
        candidate = directory / f"{stem}-{n}.md"
        n += 1
    return candidate


def cmd_propose(args: argparse.Namespace, root: Path) -> int:
    pattern = validate_pattern(args.pattern)
    confidence = validate_confidence(args.confidence)
    source = validate_source(args.source)
    evidence = validate_evidence(args.evidence)

    if args.now is not None:
        if not re.fullmatch(r"\d{8}-\d{6}", args.now):
            raise ProposeError(
                "NOW", f"--now {args.now!r} must look like YYYYMMDD-HHMMSS"
            )
        stamp = args.now
        date = f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"
    else:
        now = datetime.now()
        stamp = now.strftime("%Y%m%d-%H%M%S")
        date = now.strftime("%Y-%m-%d")

    ensure_dirs(root)
    stem = f"prop-{stamp}-{slugify(pattern)}"
    out = unique_path(root / INBOX, stem)
    lesson_id = out.stem

    content = PROPOSAL_TEMPLATE.format(
        lesson_id=lesson_id,
        confidence=confidence,
        source=source,
        date=date,
        evidence=evidence or "none recorded",
        pattern=pattern,
        evidence_body=evidence or "(no evidence ref given — add one before review)",
    )
    out.write_text(content, encoding="utf-8")
    print(f"wrote {out}")
    print(
        "note: PROPOSAL ONLY — a human must review it "
        "(promote --file <name> --approved-by <you>) before anything lands"
    )
    return 0


def read_field(text: str, field: str) -> str | None:
    m = re.search(rf"^{field}:\s*(.*)$", text, re.MULTILINE)
    return m.group(1).strip() if m else None


def cmd_list(_args: argparse.Namespace, root: Path) -> int:
    inbox = root / INBOX
    if not inbox.is_dir():
        print("inbox is empty (lessons/inbox/ does not exist yet)")
        return 0
    proposals = sorted(inbox.glob("prop-*.md"))
    if not proposals:
        print("inbox is empty")
        return 0
    for path in proposals:
        text = path.read_text(encoding="utf-8", errors="replace")
        status = read_field(text, "status") or "?"
        confidence = read_field(text, "confidence") or "?"
        source = read_field(text, "source") or "?"
        print(f"{path.name}  status={status}  confidence={confidence}  source={source}")
    return 0


def manual_edit_hint(path: Path, text: str) -> str:
    lines = text.splitlines()
    pattern_line = ""
    in_pattern = False
    for line in lines:
        if line.strip() == "## Pattern":
            in_pattern = True
            continue
        if in_pattern and line.strip():
            pattern_line = line.strip()
            break
    return (
        f"Manual edit still required (this tool never edits rule files):\n"
        f"  1. Read {path} and check the pattern against the evidence.\n"
        f"  2. If it holds, propose the exact LESSONS.md edit yourself, e.g. add "
        f"under the matching section:\n"
        f"       - {pattern_line or '<the pattern, in imperative voice>'}\n"
        f"  3. Only after the user approves that edit, apply it — the proposal "
        f"file in lessons/accepted/ is the record, not the rule."
    )


def move_proposal(name: str, root: Path, dest: str) -> tuple[Path, Path, str]:
    filename = validate_filename(name)
    src = root / INBOX / filename
    if not src.is_file():
        raise ProposeError(
            "FILE", f"no such proposal in lessons/{INBOX}/: {filename} (run `list`)"
        )
    ensure_dirs(root)
    dst_dir = root / dest
    dst = dst_dir / filename
    if dst.exists():
        raise ProposeError(
            "COLLISION",
            f"lessons/{dest}/{filename} already exists — resolve it by hand, "
            f"this tool never overwrites",
        )
    text = src.read_text(encoding="utf-8", errors="replace")
    src.rename(dst)
    return src, dst, text


def cmd_promote(args: argparse.Namespace, root: Path) -> int:
    approver = validate_approver(args.approved_by)
    _src, dst, text = move_proposal(args.file, root, ACCEPTED)
    print(f"moved to {dst} (approved by {approver})")
    print(manual_edit_hint(dst, text))
    return 0


def cmd_discard(args: argparse.Namespace, root: Path) -> int:
    _src, dst, _text = move_proposal(args.file, root, REJECTED)
    print(f"moved to {dst} — kept for the record (a reappearing proposal is a signal)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="propose_lessons.py",
        description=(
            "T-33 lesson auto-proposals: draft lesson candidates as PROPOSALS "
            "ONLY in lessons/inbox/. Nothing lands without the existing "
            "user-approval review flow; this tool can never edit rule files."
        ),
    )
    ap.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="lessons root (default: <repo>/lessons; tests use a scratch dir)",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p_propose = sub.add_parser(
        "propose", help="write a new proposal file to lessons/inbox/"
    )
    p_propose.add_argument("--pattern", required=True,
                           help=f"one-line lesson pattern (max {PATTERN_MAX} chars)")
    p_propose.add_argument("--confidence", required=True,
                           help="float in 0..1 — how sure the pattern generalizes")
    p_propose.add_argument("--source", required=True,
                           help="where the pattern was observed (project/session)")
    p_propose.add_argument("--evidence", default=None,
                           help="optional file:line or transcript reference")
    p_propose.add_argument("--now", default=None,
                           help="pin the timestamp as YYYYMMDD-HHMMSS (test hook)")

    sub.add_parser("list", help="print inbox proposals with status/confidence")

    p_promote = sub.add_parser(
        "promote",
        help="move a proposal to lessons/accepted/ and print the manual edit "
             "the human must still make",
    )
    p_promote.add_argument("--file", required=True, help="proposal file name (prop-*.md)")
    p_promote.add_argument("--approved-by", default=None,
                           help="real approver name; required, placeholders refused")

    p_discard = sub.add_parser(
        "discard", help="move a proposal to lessons/rejected/"
    )
    p_discard.add_argument("--file", required=True, help="proposal file name (prop-*.md)")

    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root if getattr(args, "root", None) is not None else DEFAULT_ROOT
    handlers = {
        "propose": cmd_propose,
        "list": cmd_list,
        "promote": cmd_promote,
        "discard": cmd_discard,
    }
    try:
        return handlers[args.command](args, root)
    except ProposeError as exc:
        print(exc.render(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
