#!/usr/bin/env bash
# sps-hook-gate.sh — Claude Code hook entrypoint for SPS law enforcement (T-32)
#
# Wired into the PROJECT-local .claude/settings.json by scripts/sps-hooks.sh
# (consent-gated; see skill/sps/HOOKS.md). Keeps settings.json a one-liner.
#
#   PreToolUse  (Write|Edit): blocks a write that would push an .sps/ hot file
#                             over its CONTEXT-BUDGET (mirrors check_laws.py).
#   PostToolUse (Write|Edit): fast targeted law subset on the written file;
#                             emits a NON-BLOCKING warning (systemMessage).
#
# Contract:
# - reads the Claude Code hook payload (JSON) on stdin
# - FAIL-OPEN: missing python3, malformed payload, or unknown input exits 0
#   silently — a broken hook must never break a normal write
# - blocking = exit code 2 with the reason on stderr (plus a JSON deny
#   decision on stdout for runtimes that prefer the decision format)
# - works from any cwd: repo root resolved via git, falling back to the
#   directory above this script (same relocation rule as other sps-*.sh)
# - interpreter override (tests / odd setups): SPS_PYTHON (default: python3)
# - fast: single python3 process, no repo-wide scans (<1s)
set -euo pipefail

MODE="${1:-}"
case "$MODE" in
  pre|post) ;;
  *) exit 0 ;;  # unknown mode -> fail open
esac

PYBIN="${SPS_PYTHON:-python3}"
command -v "$PYBIN" >/dev/null 2>&1 || exit 0  # no python3 -> never block

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" \
  || ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# The hook payload arrives on stdin, but the Python script itself comes from a
# heredoc — the two compete for stdin. Park the payload in a temp file first
# and hand it over by path (read-then-unlink, no litter even on error).
PAYLOAD="$(mktemp "${TMPDIR:-/tmp}/sps-hook-gate.XXXXXX")" || exit 0
cat >"$PAYLOAD" || { rm -f "$PAYLOAD"; exit 0; }

SPS_HOOK_MODE="$MODE" SPS_HOOK_ROOT="$ROOT" SPS_HOOK_PAYLOAD="$PAYLOAD" \
  "$PYBIN" - <<'PY'
import json, os, re, sys
from pathlib import Path

mode = os.environ.get("SPS_HOOK_MODE", "")
root = Path(os.environ.get("SPS_HOOK_ROOT", ".")).resolve()
payload_path = os.environ.get("SPS_HOOK_PAYLOAD", "")

# CONTEXT-BUDGET table — keep in sync with framework/sps2/tools/check_laws.py
BUDGETS = {
    "handoff.md": (150, 8192),
    "agent.md": (60, 4096),
    "profile.md": (120, 8192),
    "plan.md": (300, 24576),
    "task-queue.md": (80, 6144),
    "audit-report.md": (200, 16384),
}


def fail_open(msg=""):
    if msg:
        print(msg, file=sys.stderr)
    sys.exit(0)


try:
    with open(payload_path, encoding="utf-8") as fh:
        payload = json.load(fh)
except Exception:
    fail_open()  # malformed payload -> never block a write
finally:
    try:
        os.unlink(payload_path)  # no temp litter, even on error
    except OSError:
        pass

ti = payload.get("tool_input")
if not isinstance(ti, dict):
    fail_open()
fp = ti.get("file_path") or ""
if not fp:
    fail_open()
p = Path(fp)
if not p.is_absolute():
    p = root / p
p = Path(os.path.normpath(str(p)))

try:
    rel = p.resolve().relative_to(root)
except ValueError:
    rel = None
under_sps = p.name in BUDGETS and ".sps" in p.parts

# ── PreToolUse: context-budget BLOCK on .sps/ hot files ─────────────────────
if mode == "pre":
    if not under_sps:
        sys.exit(0)  # budget law only gates .sps hot files
    maxl, maxb = BUDGETS[p.name]
    if payload.get("tool_name") == "Edit":
        old = ti.get("old_string") or ""
        new = ti.get("new_string") or ""
        try:
            cur = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            cur = ""
        # projected result: first exact old->new swap (approximation is fine —
        # post-write check re-verifies the real file and warns)
        proj = cur.replace(old, new, 1) if old else cur + new
    else:
        proj = ti.get("content") or ""
    nl = len(proj.splitlines())
    nb = len(proj.encode("utf-8", errors="replace"))
    if nl > maxl or nb > maxb:
        reason = (
            f"SPS context-budget: .sps/{p.name} would become {nl}L/{nb}B, "
            f"over budget {maxl}L/{maxb}B — archive to .sps/archive/ "
            f"(CONTEXT-BUDGET.md). Write blocked by sps-hooks (T-32); "
            f"this decision was made OUTSIDE model context."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)

# ── PostToolUse: fast law subset, always non-blocking ───────────────────────
warnings = []

# dod-22: junk/temp filename (same pattern as check_laws.py)
if rel is not None and re.search(
    r"(\.tmp-|\.bak$|~$|\.orig$|\.rej$|^debug_.*\.py$|^scratch)", p.name
):
    warnings.append(f"dod-22 junk file: {rel}")

text = ""
try:
    if p.is_file() and p.stat().st_size <= 262144:
        text = p.read_text(encoding="utf-8", errors="replace")
except OSError:
    text = ""

# context-budget on .sps hot files (post-write reality; warn only)
if under_sps and text:
    maxl, maxb = BUDGETS[p.name]
    nl = len(text.splitlines())
    nb = len(text.encode("utf-8", errors="replace"))
    if nl > maxl or nb > maxb:
        warnings.append(
            f"context-budget: {rel or p.name} {nl}L/{nb}B exceeds budget "
            f"{maxl}L/{maxb}B — archive to .sps/archive/ (CONTEXT-BUDGET.md)"
        )

# dod-24: hardcoded env-ish config in shipped domain source (single file only)
if (
    rel is not None
    and len(rel.parts) >= 3
    and rel.parts[0] == "framework"
    and rel.parts[1] == "domain"
    and p.suffix == ".py"
    and "test" not in p.name
):
    HARDCODED = re.compile(
        r"(https?://(?!example\.com|localhost|127\.0\.0\.1)[\w.-]+\.[a-z]{2,})"
        r"|(:\d{4,5}\b)"
    )
    STANDARDS = ("schema.org", "sitemaps.org", "w3.org", "www.w3.org")
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("#") or "example.com" in s:
            continue
        if any(std in s for std in STANDARDS):
            continue
        if HARDCODED.search(s) and not any(
            t in s for t in ("os.environ", "getenv", "config", "DEFAULT_", "# noqa")
        ):
            warnings.append(f"dod-24 hardcoded-config: {rel}:{i}: {s[:90]}")
            break  # one hit suffices for a hook warning — keep it fast

if warnings:
    print(json.dumps({
        "systemMessage": "SPS law warning (non-blocking): " + " | ".join(warnings)
    }))
sys.exit(0)
PY
