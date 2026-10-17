#!/usr/bin/env bash
# sps-provenance.sh — pin & verify third-party skill content (T-29)
# Usage:
#   bash scripts/sps-provenance.sh pin             # digest every third-party skill -> ~/.sps/provenance.json
#   bash scripts/sps-provenance.sh check           # recompute digests; report-only, always exit 0
#   bash scripts/sps-provenance.sh check --strict  # same report; exit 1 on any PROVENANCE-DRIFT
#
# Bundled skills (MANAGED_SKILLS in install.sh: sps, sps-cms, sps-seo) are skipped —
# they are governed by the install manifest. Everything else found under the
# installer's SYNC_PATHS skills dirs is third-party and gets pinned:
#   { "<skill>": { "dir": ..., "sha256_skill_md": ..., "digest": ..., "pinned_at": ... } }
# digest = sha256 over the sorted file list + each file's sha256 (dir-content digest).
# check is report-only (like sps-hygiene check): PINNED-OK / PROVENANCE-DRIFT / UNPINNED.
# UNPINNED stays report-only even under --strict (onboarding state, not tampering).
# Deps: git, python3. ANSI colors only when stdout is a TTY.
set -euo pipefail

MODE="check"
STRICT=0
case "${1:-}" in
  pin) MODE="pin" ;;
  check|"") MODE="check" ;;
  *) echo "usage: sps-provenance.sh [pin|check] [--strict]" >&2; exit 2 ;;
esac
if [ "$MODE" = "check" ] && [ "${2:-}" = "--strict" ]; then STRICT=1; fi

SCRIPT_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

python3 - "$MODE" "$STRICT" "$SCRIPT_FILE" <<'PYEOF'
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

mode = sys.argv[1]
strict = sys.argv[2] == "1"
script = Path(sys.argv[3]).resolve()

TTY = sys.stdout.isatty()
def _c(code: str) -> str:
    return f"\033[{code}m" if TTY else ""
OK, WARN, BAD, DIM, END = _c("32"), _c("33"), _c("31"), _c("2"), _c("0")

home = Path(os.environ.get("HOME") or Path.home())
store_path = home / ".sps" / "provenance.json"

# --- locate install.sh and parse MANAGED_SKILLS / SYNC_PATHS from it --------
install_sh = None
for p in [script.parent.parent, *script.parents]:
    if (p / "install.sh").is_file():
        install_sh = p / "install.sh"
        break

def bash_array(text: str, name: str) -> list[str]:
    m = re.search(rf"^{name}=\(([^)]*)\)", text, re.M)
    if not m:
        return []
    out = []
    for a, b in re.findall(r'"([^"]*)"|(\S+)', m.group(1)):
        tok = a or b
        if tok:
            out.append(tok)
    return out

managed: list[str] = []
sync_paths: list[str] = []
if install_sh:
    text = install_sh.read_text(encoding="utf-8", errors="replace")
    managed = bash_array(text, "MANAGED_SKILLS")
    for raw in bash_array(text, "SYNC_PATHS"):
        expanded = raw.replace("$HOME", str(home)).replace("${HOME}", str(home))
        if "$" not in expanded:
            sync_paths.append(expanded)

# --- collect third-party skills (first dir seen wins for duplicate names) ---
skills: dict[str, Path] = {}
found_dirs = 0
for root in sync_paths:
    d = Path(root)
    if not d.is_dir():
        continue
    found_dirs += 1
    for child in sorted(d.iterdir()):
        if child.is_dir() and (child / "SKILL.md").is_file() and child.name not in managed:
            skills.setdefault(child.name, child)

if found_dirs == 0:
    print(f"{DIM}note: no skills directories found (install.sh SYNC_PATHS) — nothing to {mode}{END}")
    raise SystemExit(0)

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dir_digest(d: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(p for p in d.rglob("*") if p.is_file()):
        h.update(p.relative_to(d).as_posix().encode("utf-8"))
        h.update(b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()

if mode == "pin":
    store = {}
    for name in sorted(skills):
        d = skills[name]
        store[name] = {
            "dir": str(d),
            "sha256_skill_md": sha256_file(d / "SKILL.md"),
            "digest": dir_digest(d),
            "pinned_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        print(f"PINNED: {name}  {DIM}({d}){END}")
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(store, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"== PROVENANCE PIN: {len(store)} third-party skill(s) -> {store_path} ==")
    raise SystemExit(0)

# --- check mode --------------------------------------------------------------
try:
    store = json.loads(store_path.read_text(encoding="utf-8"))
except FileNotFoundError:
    store = {}
except (ValueError, OSError) as exc:
    print(f"{BAD}PROVENANCE-ERROR: unreadable {store_path}: {exc}{END}")
    raise SystemExit(1)

drift = unpinned = ok_n = 0
for name in sorted(skills):
    d = skills[name]
    if name not in store:
        unpinned += 1
        print(f"{WARN}UNPINNED: {name}{END} — present but never pinned (run: scripts/sps-provenance.sh pin)")
        continue
    rec = store[name]
    cur = dir_digest(d) if d.is_dir() else None
    md = sha256_file(d / "SKILL.md") if (d / "SKILL.md").is_file() else None
    if cur is None or cur != rec.get("digest") or md != rec.get("sha256_skill_md"):
        drift += 1
        print(f"{BAD}PROVENANCE-DRIFT: {name}{END} — content changed since pin ({rec.get('dir', '?')})")
    else:
        ok_n += 1
        print(f"{OK}PINNED-OK: {name}{END}")
for name in sorted(set(store) - set(skills)):
    drift += 1
    print(f"{BAD}PROVENANCE-DRIFT: {name}{END} — pinned but no longer installed")

print(f"== PROVENANCE CHECK: {ok_n} pinned-ok, {drift} drifted, {unpinned} unpinned ==")
if strict and drift > 0:
    raise SystemExit(1)
raise SystemExit(0)
PYEOF
