#!/usr/bin/env python3
"""Docs-drift checker (T-30): commands referenced in docs must exist.

Scans the repo's user-facing docs — USER-GUIDE.md, README.md,
skill/sps/SKILL.md, skill/sps/METHOD-CARD.md, skill/sps/CHEAT-SHEET.md
(absent tolerated) — and extracts every command-like reference:

  - `bash scripts/<name>.sh` / `scripts/<name>.sh`   (also `bash ~/.sps/src/.../scripts/x.sh`)
  - `/sps <subcommand>`                              (e.g. `/sps audit`)
  - `sps-<name>.sh <sub>`                            (e.g. `sps-lesson.sh review`)

and verifies each against the repo:
  - script refs must exist in scripts/ (or skill/sps/scripts/, or the
    ~/.sps/src/BuildPilot install location for doc paths that name it);
  - /sps subcommands must appear in SKILL.md's Modes sections or METHOD-CARD;
  - flags (--yes, --force, --approved-by, --keep-personal, -g) mentioned in a
    doc must appear in the referenced script's own text (usage/header).

Output mirrors check_laws.py FAIL style: one line per finding on stderr
(`DOCS_DRIFT: <doc>: references <cmd> — not found`), a summary, exit 1 on
drift / 0 clean. Report tool for this repo itself. Stdlib-only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

DOCS = [
    REPO / "USER-GUIDE.md",
    REPO / "README.md",
    REPO / "skill" / "sps" / "SKILL.md",
    REPO / "skill" / "sps" / "METHOD-CARD.md",
    REPO / "skill" / "sps" / "CHEAT-SHEET.md",  # may not exist yet — tolerated
]

SCRIPT_DIRS = [REPO / "scripts", REPO / "skill" / "sps" / "scripts"]
INSTALL_SCRIPTS = Path.home() / ".sps" / "src" / "BuildPilot" / "scripts"

CHECK_ID = "DOCS_DRIFT"

# Flags that docs mention and that must exist in the target script's text.
FLAGS = ("--yes", "--force", "--approved-by", "--keep-personal", "-g")

# /sps subcommands that are documented as valid (SKILL.md Modes / METHOD-CARD).
SPS_ALIASES = {"unlock": "release-lock", "cms-sync": "sync", "couple": "sync"}


def doc_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def valid_sps_subcommands() -> set[str]:
    """Subcommands accepted per SKILL.md Modes sections + METHOD-CARD Modes list."""
    subs: set[str] = set()
    skill = doc_text(REPO / "skill" / "sps" / "SKILL.md")
    card = doc_text(REPO / "skill" / "sps" / "METHOD-CARD.md")
    for text in (skill, card):
        for m in re.finditer(r"`?/sps(?:\s+([a-z][a-z-]*(?:\s+[a-z-]+)?)?)`?", text):
            sub = (m.group(1) or "").strip()
            if sub:
                subs.add(sub)
    return subs


def find_script(name: str, doc: Path | None = None) -> Path | None:
    # Resolve relative to the doc's own tree first (scratch trees in tests),
    # walking up from the doc's dir until a scripts/<name> is found; then the
    # repo's script dirs; then the installed ~/.sps/src/BuildPilot location.
    if doc is not None:
        for base in [doc.parent, *doc.parents]:
            p = base / "scripts" / name
            if p.is_file():
                return p
    for d in SCRIPT_DIRS:
        p = d / name
        if p.is_file():
            return p
    if INSTALL_SCRIPTS.is_dir() and (INSTALL_SCRIPTS / name).is_file():
        return INSTALL_SCRIPTS / name
    return None


def check_doc(path: Path, sps_subs: set[str]) -> list[str]:
    text = doc_text(path)
    if not text:
        return []
    try:
        rel = path.relative_to(REPO)
    except ValueError:
        rel = path  # scratch/external tree (tests); report the path as-is
    out: list[str] = []

    # 1. Script references: scripts/<name>.sh (optionally after `bash ` or a path prefix).
    for m in re.finditer(r"(?:bash\s+)?(?:~/?[\w./-]*/)?scripts/([\w-]+\.sh)", text):
        name = m.group(1)
        if find_script(name, path) is None:
            out.append(f"{CHECK_ID}: {rel}: references scripts/{name} — not found")

    # 2. sps-<name>.sh <sub> — subcommand must exist in the script's own text.
    for m in re.finditer(r"\b(sps-[\w-]+\.sh)\s+([a-z][\w-]*)", text):
        name, sub = m.group(1), m.group(2)
        script = find_script(name, path)
        if script is None:
            out.append(f"{CHECK_ID}: {rel}: references {name} — not found")
            continue
        body = script.read_text(encoding="utf-8", errors="replace")
        if not re.search(rf"[\s\"'|]{re.escape(sub)}[\s\"'|)\]]", body):
            out.append(f"{CHECK_ID}: {rel}: references {name} {sub} — subcommand not found in {name}")

    # 3. /sps <subcommand> — must appear in SKILL.md Modes or METHOD-CARD.
    for m in re.finditer(r"`/sps\s+([a-z][a-z-]*(?:\s+[a-z-]+)?)`", text):
        sub = m.group(1).strip()
        if sub in sps_subs or sub in SPS_ALIASES:
            continue
        # A subcommand is valid if any documented one starts the same way
        # (e.g. `/sps lesson review` is fine when `/sps lesson review` is listed).
        out.append(f"{CHECK_ID}: {rel}: references /sps {sub} — not found in SKILL.md Modes or METHOD-CARD")

    # 4. Flags mentioned in the doc must exist in the referenced script.
    for m in re.finditer(r"(sps-[\w-]+\.sh|scripts/[\w-]+\.sh)[^\n`]*?((?:--[\w-]+|-g)\b)", text):
        flag = m.group(2)
        if flag not in FLAGS:
            continue
        ref = m.group(1)
        name = ref.split("/")[-1]
        script = find_script(name, path)
        if script is None:
            continue  # already reported by checks above
        body = script.read_text(encoding="utf-8", errors="replace")
        if flag not in body:
            out.append(f"{CHECK_ID}: {rel}: references {flag} — flag not found in {name}")

    return out


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)  # scratch/external tree (tests)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    docs = [Path(a) if not a.startswith("-") else None for a in args] if args else DOCS
    docs = [d if d.is_absolute() else REPO / d for d in docs if d]
    sps_subs = valid_sps_subcommands()
    findings: list[str] = []
    for path in docs:
        findings.extend(check_doc(path, sps_subs))
    if findings:
        for line in findings:
            print(line, file=sys.stderr)
        print(f"\n== DOCS-DRIFT CHECK: {len(findings)} drift finding(s) ==", file=sys.stderr)
        return 1
    present = [d for d in docs if d.is_file()]
    if not present:
        print("== DOCS-DRIFT CHECK: no docs found to scan ==")
        return 0
    scanned = ", ".join(_rel(d) for d in present)
    missing = [d for d in docs if not d.is_file()]
    note = f" (absent, tolerated: {', '.join(_rel(d) for d in missing)})" if missing else ""
    print(f"== DOCS-DRIFT CHECK: all documented commands exist (scanned: {scanned}){note} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
