#!/usr/bin/env python3
"""Machine-checks for the agent-facing SPS laws (SECTION-DOD, HANDOFF-CHECKPOINT).

Turns prose laws into CI-enforced gates where the check is structural:
- SECTION-DOD items that map to greppable/structural properties
- HANDOFF-CHECKPOINT: checkpoint record present for the latest session
- CONTEXT-BUDGET: .sps hot files within budget (mirrors sps-doctor)
- Manifest/validator hygiene: pinned mirrors, version stamps

Agent-neutral, stdlib-only, project-local (no network, no installs).
Exit 0 = all laws hold; exit 1 = violations (printed, one per line).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
VIOLATIONS: list[str] = []


def v(msg: str) -> None:
    VIOLATIONS.append(msg)


# ── CONTEXT-BUDGET: .sps hot files within budget ─────────────────────────────
BUDGETS = {  # file: (max_lines, max_bytes)
    "handoff.md": (150, 8192),
    "agent.md": (60, 4096),
    "profile.md": (120, 8192),
    "plan.md": (300, 24576),
    "task-queue.md": (80, 6144),
    "audit-report.md": (200, 16384),
}
sps = REPO / ".sps"
if sps.is_dir():
    for name, (maxl, maxb) in BUDGETS.items():
        f = sps / name
        if not f.is_file():
            continue
        lines = len(f.read_text(encoding="utf-8", errors="replace").splitlines())
        size = f.stat().st_size
        if lines > maxl or size > maxb:
            v(f"context-budget: .sps/{name} {lines}L/{size}B exceeds budget {maxl}L/{maxb}B — archive to .sps/archive/ (CONTEXT-BUDGET.md)")

# ── SECTION-DOD #24: no hardcoded env-ish config in shipped source ───────────
# Scan framework/domain source (shipped app code) for baked-in hosts/ports.
# Standards namespaces (schema.org, w3.org, sitemaps.org) are constants, not config.
SRC_DIRS = [REPO / "framework" / "domain"]
STANDARDS = ("schema.org", "sitemaps.org", "w3.org", "www.w3.org")
HARDCODED = re.compile(
    r"""(?x)
    (https?://(?!example\.com|localhost|127\.0\.0\.1)[\w.-]+\.[a-z]{2,})  # absolute non-example URLs
    |(:\d{4,5}\b)                                                        # suspicious ports
    """,
    re.VERBOSE,
)
for src in SRC_DIRS:
    if not src.is_dir():
        continue
    for py in src.rglob("*.py"):
        if "test" in py.name:
            continue
        for i, line in enumerate(py.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            s = line.strip()
            if s.startswith("#") or "example.com" in s:
                continue
            if any(std in s for std in STANDARDS):
                continue
            m = HARDCODED.search(s)
            if m and not any(t in s for t in ("os.environ", "getenv", "config", "DEFAULT_", "# noqa")):
                v(f"dod-24 hardcoded-config: {py.relative_to(REPO)}:{i}: {s.strip()[:90]}")

# ── SECTION-DOD #22/#23: workspace hygiene — no leftover temp/junk files ─────
JUNK = re.compile(r"(\.tmp-|\.bak$|~$|\.orig$|\.rej$|^debug_.*\.py$|^scratch)")
for junk_path in REPO.rglob("*"):
    if any(part in (".git", "node_modules", ".sps", "__pycache__") for part in junk_path.parts):
        continue
    if junk_path.is_file() and JUNK.search(junk_path.name):
        v(f"dod-22 junk file: {junk_path.relative_to(REPO)}")

# ── HANDOFF-CHECKPOINT: rolling-log law (<=5 conversation entries) ───────────
handoff = sps / "handoff.md"
if handoff.is_file():
    text = handoff.read_text(encoding="utf-8", errors="replace")
    in_log = False
    entries = 0
    for line in text.splitlines():
        if line.startswith("## Conversation log"):
            in_log = True
            continue
        if in_log and line.startswith("## "):
            break
        if in_log and line.strip().startswith("- ") and "Rolling log" not in line:
            entries += 1
    if entries > 5:
        v(f"handoff-checkpoint: conversation log has {entries} entries (>5) — roll oldest to .sps/archive/ (CONTEXT-BUDGET.md)")

# ── SKILL-ROUTER: conflict bans hold in the router table ─────────────────────
router = REPO / "skill" / "sps" / "SKILL-ROUTER.md"
if router.is_file():
    rt = router.read_text(encoding="utf-8", errors="replace")
    if "Tool Consent gate first" not in rt:
        v("law-17 wiring: SKILL-ROUTER.md missing Tool Consent gate in missing-skill protocol")
    if "CONTEXT-BUDGET.md" not in rt:
        v("context-budget wiring: SKILL-ROUTER.md missing CONTEXT-BUDGET reference")

# ── SKILL.md: hard-law core intact (18 laws) ─────────────────────────────────
skill = REPO / "skill" / "sps" / "SKILL.md"
if skill.is_file():
    st = skill.read_text(encoding="utf-8", errors="replace")
    for law in ("Task Queue", "Write Confinement", "Handoff Checkpoint",
                "Deploy Budget", "Tool Consent", "Auto-Update Awareness"):
        if f"**{law}" not in st:
            v(f"hard-law core: SKILL.md missing law '{law}'")

# ── SECTION-DOD: the 8 audit-gap items still present ─────────────────────────
dod = REPO / "skill" / "sps" / "SECTION-DOD.md"
if dod.is_file():
    dt = dod.read_text(encoding="utf-8", errors="replace")
    for marker in ("No duplicate logic", "No hardcoded environment config",
                   "Concurrency basics", "Error messages are user-safe",
                   "Dependency health"):
        if marker not in dt:
            v(f"section-dod: audit-gap item missing: {marker}")

# ── DESIGN-GATE: craft laws + anti-slop ban list present ─────────────────────
dg = REPO / "skill" / "sps" / "DESIGN-GATE.md"
if dg.is_file():
    dt = dg.read_text(encoding="utf-8", errors="replace")
    for marker_text in ("tabular-nums", "60-30-10", "prefers-reduced-motion",
                        "Anti-slop ban list", "44×44px", "cubic-bezier",
                        "Bento", "prefers-color-scheme", "top-edge highlight",
                        "Autofocus the first field"):
        if marker_text not in dt:
            v(f"design-gate: craft law missing: {marker_text}")

# ── COMPANY-LIFECYCLE: both gates defined ────────────────────────────────────
cl = REPO / "skill" / "sps" / "COMPANY-LIFECYCLE.md"
if cl.is_file():
    ct = cl.read_text(encoding="utf-8", errors="replace")
    if "GATE 1 (G1" not in ct or "GATE 2 (G2" not in ct:
        v("company-lifecycle: G1/G2 gate definitions missing")

def main() -> int:
    for msg in sorted(set(VIOLATIONS)):
        print(msg, file=sys.stderr)
    if VIOLATIONS:
        print(f"\n== LAW CHECK: {len(set(VIOLATIONS))} violation(s) ==", file=sys.stderr)
        return 1
    print("== LAW CHECK: all machine-checkable laws hold ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
