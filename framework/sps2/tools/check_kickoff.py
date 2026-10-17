#!/usr/bin/env python3
"""Kickoff-proof check (T-28): prove the kickoff questionnaire ran before build.

COMPANY-LIFECYCLE.md Phase 0 says the agent opens every client project with a
consolidated questionnaire and builds nothing until it is answered — but no
checker proved answers were recorded. This tool closes that gap.

The lifecycle doc does not name a kickoff artifact file, so this check
standardizes on `.sps/kickoff.md` (`.sps/kickoff-answers.md` also accepted):
the agent writes the user's answers there during Phase 0, one headed section
per questionnaire item.

Required sections (derived from the Phase 0 questionnaire):
  purpose  (project goal) · deploy target · stack · content · CMS

A section counts as ANSWERED when the heading is followed by non-empty,
non-placeholder content before the next heading.

Fail-closed behavior mirrors check_generated_tests.py:
- No `.sps/` at all -> PASS with a note (project not started; nothing built).
- No kickoff answers BUT build artifacts exist (.sps/plan.md, src/, index.html)
  -> KICKOFF_NOT_RECORDED, exit 1.
- Kickoff file missing required sections, or a section with an empty/placeholder
  answer -> violation, exit 1.
- Kickoff file complete -> PASS.

Violation lines go to stderr as `<CHECK_ID>: <target>: <detail>`, one per line,
followed by a `== ... CHECK: N violation(s) ==` summary. Exit 0 = all hold.
Stdlib-only, project-local, agent-neutral.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KICKOFF_NAMES = ("kickoff.md", "kickoff-answers.md")
BUILD_ARTIFACTS = ("plan.md",)          # inside .sps/
BUILD_ARTIFACT_PATHS = ("src", "index.html")  # at project root
CHECK_ID_MISSING = "KICKOFF_NOT_RECORDED"
CHECK_ID_SECTION = "KICKOFF_SECTION_MISSING"
CHECK_ID_EMPTY = "KICKOFF_ANSWER_EMPTY"

# keyword -> accepted heading fragments (case-insensitive), from COMPANY-LIFECYCLE.md Phase 0
REQUIRED_SECTIONS: list[tuple[str, tuple[str, ...]]] = [
    ("purpose", ("project goal", "purpose", "goal")),
    ("deploy target", ("deploy target", "deploy")),
    ("stack", ("stack",)),
    ("content", ("content",)),
    ("cms", ("cms",)),
]

PLACEHOLDER = re.compile(
    r"^(<[^>]*>|\?+|tbd\b.*|todo\b.*|pending\b.*|n/?a$|placeholder$|none yet$|—|-{1,3})$",
    re.IGNORECASE,
)


def find_kickoff(project: Path) -> Path | None:
    sps = project / ".sps"
    for name in KICKOFF_NAMES:
        f = sps / name
        if f.is_file():
            return f
    return None


def parse_sections(text: str) -> dict[str, list[str]]:
    """Map lowercase heading text -> body lines until the next heading."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            current = line.lstrip("#").strip().lower()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return sections


def section_answered(sections: dict[str, list[str]], keywords: tuple[str, ...]) -> tuple[bool, str | None]:
    """Return (answered, matched_heading). A section is answered when any body
    line after the heading (before the next) is non-empty and not a placeholder."""
    for heading, body in sections.items():
        if any(k in heading for k in keywords):
            for line in body:
                s = line.strip().lstrip("-*").strip()
                if s and not PLACEHOLDER.match(s):
                    return True, heading
            return False, heading  # heading found but answer empty/placeholder
    return False, None  # heading not found at all


def check_project(project: Path) -> list[str]:
    violations: list[str] = []
    sps = project / ".sps"
    kickoff = find_kickoff(project)

    if kickoff is None:
        has_build = any((sps / a).exists() for a in BUILD_ARTIFACTS) if sps.is_dir() else False
        has_build = has_build or any((project / a).exists() for a in BUILD_ARTIFACT_PATHS)
        if not has_build:
            return []  # project not started — that's OK
        return [f"{CHECK_ID_MISSING}: {project}: build artifacts exist "
                f"(.sps/plan.md or src/ or index.html) but no kickoff answers "
                f"(.sps/kickoff.md) — record the questionnaire before building "
                f"(COMPANY-LIFECYCLE.md Phase 0)"]

    sections = parse_sections(kickoff.read_text(encoding="utf-8", errors="replace"))
    for label, keywords in REQUIRED_SECTIONS:
        answered, heading = section_answered(sections, keywords)
        if answered:
            continue
        if heading is None:
            violations.append(
                f"{CHECK_ID_SECTION}: {kickoff}: no section for required kickoff "
                f"answer '{label}' — add a '## {label.title()}' heading with the user's answer")
        else:
            violations.append(
                f"{CHECK_ID_EMPTY}: {kickoff}: section '{heading}' has an empty or "
                f"placeholder answer — record the user's actual answer for '{label}'")
    return violations


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    project = Path(args[0]) if args else Path.cwd()
    if not project.is_dir():
        print(f"KICKOFF_CHECK: project root not found: {project}", file=sys.stderr)
        return 1
    violations = check_project(project)
    if not violations:
        if not (project / ".sps").is_dir():
            print(f"note: no .sps/ in {project} — project not started, "
                  f"kickoff check not applicable")
        elif find_kickoff(project) is None:
            print(f"note: no build artifacts in {project} — kickoff check not "
                  f"applicable yet")
        print("== KICKOFF CHECK: kickoff answers recorded ==")
        return 0
    for msg in violations:
        print(msg, file=sys.stderr)
    print(f"\n== KICKOFF CHECK: {len(violations)} violation(s) ==", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
