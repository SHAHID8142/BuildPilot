#!/usr/bin/env bash
# sps-hooks.sh — consent-gated Claude Code hook manager for SPS laws (T-32)
#
# Wires scripts/sps-hook-gate.sh into the PROJECT-local .claude/settings.json
# so law violations are blocked at write-time, OUTSIDE model context — not
# caught only when check_laws.py is later invoked. See skill/sps/HOOKS.md.
#
# Usage:
#   bash scripts/sps-hooks.sh install [--yes] [--force]
#   bash scripts/sps-hooks.sh status    # report-only, always exit 0
#   bash scripts/sps-hooks.sh remove
#
# TOOL-CONSENT law (skill/sps/TOOL-CONSENT.md): nothing auto-installs.
# `install` requires the explicit --yes flag; piped/EOF stdin never counts as
# consent, and a bare `install` (even interactive) is refused.
#
# Marker: every entry this script writes carries "_spsHook": "sps-law-gate" so
# `remove` strips only its own entries and leaves all other settings intact.
# Merge, never clobber: pre-existing hooks and unrelated keys are preserved.
set -euo pipefail

MARKER="sps-law-gate"
HOOK_CMD='bash "$CLAUDE_PROJECT_DIR/scripts/sps-hook-gate.sh"'

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "sps-hooks: not inside a git repository (run from within the repo)" >&2
  exit 1
}
SETTINGS="$ROOT/.claude/settings.json"
GATE="$ROOT/scripts/sps-hook-gate.sh"
GATE_REL="scripts/sps-hook-gate.sh"

cmd="${1:-}"
[ $# -gt 0 ] && shift

# --- status: report-only -----------------------------------------------------
if [ "$cmd" = "status" ]; then
  if [ ! -f "$SETTINGS" ]; then
    echo "sps-hooks: no .claude/settings.json — hooks NOT installed"
    echo "  install (consent-gated): bash scripts/sps-hooks.sh install --yes"
    exit 0
  fi
  MARKER="$MARKER" SETTINGS="$SETTINGS" GATE_REL="$GATE_REL" python3 - <<'PY'
import json, os, sys
from pathlib import Path

settings = Path(os.environ["SETTINGS"])
marker = os.environ["MARKER"]
gate = os.environ["GATE_REL"]
try:
    data = json.loads(settings.read_text(encoding="utf-8"))
except Exception as e:
    print(f"sps-hooks: settings.json unreadable ({e}) — hooks state UNKNOWN")
    sys.exit(0)

hooks = data.get("hooks", {}) if isinstance(data, dict) else {}
found = {"pre": False, "post": False}
for event in ("PreToolUse", "PostToolUse"):
    for entry in hooks.get(event, []) or []:
        for h in entry.get("hooks", []) or []:
            if h.get("_spsHook") == marker or gate in str(h.get("command", "")):
                found["pre" if event == "PreToolUse" else "post"] = True

print("sps-hooks status")
print(f"  settings: {settings}")
if found["pre"]:
    print("  PreToolUse  (Write|Edit): INSTALLED — blocks over-budget .sps/ writes (context-budget)")
else:
    print("  PreToolUse  (Write|Edit): not installed")
if found["post"]:
    print("  PostToolUse (Write|Edit): INSTALLED — non-blocking law warnings (dod-22 junk, dod-24 hardcoded-config, context-budget)")
else:
    print("  PostToolUse (Write|Edit): not installed")
print("  full checker: python3 framework/sps2/tools/check_laws.py (hooks are fast subsets)")
if not (found["pre"] or found["post"]):
    print("  install (consent-gated): bash scripts/sps-hooks.sh install --yes")
sys.exit(0)
PY
  exit 0
fi

# --- remove: strip only marked entries ---------------------------------------
if [ "$cmd" = "remove" ]; then
  [ -f "$SETTINGS" ] || { echo "sps-hooks: nothing to remove (no $SETTINGS)"; exit 0; }
  MARKER="$MARKER" SETTINGS="$SETTINGS" python3 - <<'PY'
import json, os, sys
from pathlib import Path

settings = Path(os.environ["SETTINGS"])
marker = os.environ["MARKER"]
data = json.loads(settings.read_text(encoding="utf-8"))
hooks = data.get("hooks", {})
removed = 0
for event in ("PreToolUse", "PostToolUse"):
    entries = hooks.get(event)
    if not isinstance(entries, list):
        continue
    kept = []
    for entry in entries:
        hs = entry.get("hooks", []) if isinstance(entry, dict) else []
        if any(h.get("_spsHook") == marker for h in hs if isinstance(h, dict)):
            removed += len(hs)
        else:
            kept.append(entry)
    hooks[event] = kept
if not removed:
    print("sps-hooks: no sps-law-gate hook entries found — nothing removed")
    sys.exit(0)
# drop now-empty event keys, keep everything else in settings intact
for event in ("PreToolUse", "PostToolUse"):
    if hooks.get(event) == []:
        del hooks[event]
settings.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"sps-hooks: removed {removed} hook entr{'y' if removed == 1 else 'ies'}; other settings preserved")
sys.exit(0)
PY
  exit 0
fi

# --- install: consent-gated ----------------------------------------------------
if [ "$cmd" = "install" ]; then
  yes=0; force=0
  for arg in "$@"; do
    case "$arg" in
      --yes) yes=1 ;;
      --force) force=1 ;;
      *) echo "sps-hooks: unknown option: $arg" >&2; exit 2 ;;
    esac
  done
  [ -f "$GATE" ] || { echo "sps-hooks: gate script missing: $GATE_REL" >&2; exit 1; }

  if [ "$yes" -ne 1 ]; then
    echo "sps-hooks: REFUSED — installing hooks changes your Claude Code" >&2
    echo "  write-time behavior, so it needs explicit consent (TOOL-CONSENT law)." >&2
    echo "  Run: bash scripts/sps-hooks.sh install --yes" >&2
    echo "  (stdin/piped input never counts as consent; nothing was written)" >&2
    exit 1
  fi

  MARKER="$MARKER" SETTINGS="$SETTINGS" GATE_CMD="$HOOK_CMD" FORCE="$force" \
    GATE_REL="$GATE_REL" python3 - <<'PY'
import json, os, sys
from pathlib import Path

settings = Path(os.environ["SETTINGS"])
marker = os.environ["MARKER"]
gate_cmd = os.environ["GATE_CMD"]
force = os.environ.get("FORCE") == "1"
gate_rel = os.environ["GATE_REL"]

PRE = {
    "matcher": "Write|Edit",
    "hooks": [{
        "type": "command",
        "command": gate_cmd,
        "_spsHook": marker,
    }],
}
POST = json.loads(json.dumps(PRE))  # deep copy

data = {}
if settings.exists():
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except ValueError:
        print(f"sps-hooks: {settings} is not valid JSON — refusing to touch it", file=sys.stderr)
        sys.exit(1)
if not isinstance(data, dict):
    print("sps-hooks: settings.json root is not an object — refusing", file=sys.stderr)
    sys.exit(1)

hooks = data.setdefault("hooks", {})
already = 0
for event, entry in (("PreToolUse", PRE), ("PostToolUse", POST)):
    for e in hooks.get(event, []) or []:
        if any(h.get("_spsHook") == marker for h in e.get("hooks", []) if isinstance(h, dict)):
            already += 1
if already and not force:
    print("sps-hooks: hooks already installed — refusing to install twice "
          "(use --force to re-install)")
    sys.exit(1)

# replace our own entries (idempotent / --force), preserve everything else
for event, entry in (("PreToolUse", PRE), ("PostToolUse", POST)):
    entries = [e for e in hooks.get(event, []) or []
               if not any(h.get("_spsHook") == marker
                          for h in e.get("hooks", []) if isinstance(h, dict))]
    entries.append(entry)
    hooks[event] = entries

settings.parent.mkdir(parents=True, exist_ok=True)
settings.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print("sps-hooks: installed (consent recorded via --yes)")
print(f"  settings : {settings}")
print(f"  gate     : {gate_rel}")
print("  PreToolUse  Write|Edit -> blocks over-budget .sps/ writes (context-budget)")
print("  PostToolUse Write|Edit -> non-blocking law warnings (dod-22, dod-24, context-budget)")
print("  hooks run OUTSIDE model context — a blocked write never reaches the model")
sys.exit(0)
PY
  exit 0
fi

echo "usage: sps-hooks.sh {install [--yes] [--force]|status|remove}" >&2
exit 2
