#!/usr/bin/env python3
"""Product-proof validator (T-31): prove it runs, not just follows rules.

SECTION-DOD item "Product proof" requires the approval packet / handoff to
carry the proof itself (test output, screenshot, boot log) — not a claim
about it. This tool fail-closes on that rule.

Conservative by design: it only fires when `.sps/plan.md` exists (a real
build project). It then checks `.sps/handoff.md` for a "Product proof" or
"Verification evidence" section (approved plans get a grace pass — the
proof is due at the section handoff, not at plan approval). A build project
whose handoff carries no such section fails with PRODUCT_PROOF_MISSING.

Format and exit convention mirror check_generated_tests.py / check_laws.py:
one violation per line on stderr (`CHECK_ID: target: detail`), a
`== ... CHECK: N violation(s) ==` summary, exit 0 when all hold, exit 1
otherwise. Stdlib-only, project-local.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

CHECK_ID = "PRODUCT_PROOF_MISSING"

# A "Product proof" / "Verification evidence" section heading, markdown-style.
PROOF_HEADING = re.compile(
    r"^#{1,6}\s*(?:\*\*)?\s*(product proof|verification evidence)\b",
    re.IGNORECASE | re.MULTILINE,
)

# A plan still on these statuses has not been approved — grace pass.
# `draft…` (prefix match) also catches the unfilled template, whose status
# line lists every option: `Status: draft | pending-approval | approved | …`.
UNAPPROVED_STATUS = re.compile(
    r"^Status:\s*(draft\b.*|pending-approval\s*$|rejected\s*$|superseded\s*$)",
    re.IGNORECASE | re.MULTILINE,
)


def check_repo(repo: Path) -> tuple[list[str], list[str]]:
    """Check one repo; return (violations, notes)."""
    violations: list[str] = []
    notes: list[str] = []
    plan = repo / ".sps" / "plan.md"
    if not plan.is_file():
        notes.append(
            "note: no .sps/plan.md — not an active build project, "
            "product-proof check not applicable"
        )
        return violations, notes

    plan_text = plan.read_text(encoding="utf-8", errors="replace")
    if UNAPPROVED_STATUS.search(plan_text):
        notes.append(
            "note: .sps/plan.md not approved yet — proof is due at the "
            "section handoff, check passes for now"
        )
        return violations, notes

    handoff = repo / ".sps" / "handoff.md"
    if not handoff.is_file():
        violations.append(
            f"{CHECK_ID}: .sps/handoff.md: missing — an approved plan means "
            f"build work, and build work needs a handoff with a proof "
            f"section (SECTION-DOD product proof)"
        )
        return violations, notes

    text = handoff.read_text(encoding="utf-8", errors="replace")
    if not PROOF_HEADING.search(text):
        violations.append(
            f"{CHECK_ID}: .sps/handoff.md: no 'Product proof' / 'Verification "
            f"evidence' section found — attach the proof (test output / "
            f"screenshot / boot log), not a claim about it"
        )
    return violations, notes


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    repo = Path(args[0]) if args else Path.cwd()
    violations, notes = check_repo(repo)
    for note in notes:
        print(note)
    if not violations:
        print("== PRODUCT-PROOF CHECK: proof attached (or not yet due) ==")
        return 0
    for msg in violations:
        print(msg, file=sys.stderr)
    print(f"\n== PRODUCT-PROOF CHECK: {len(violations)} violation(s) ==",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
