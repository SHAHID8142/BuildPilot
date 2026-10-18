#!/usr/bin/env bash
# sps-provenance.sh — pin & verify third-party skill content (T-29)
# Usage:
#   bash scripts/sps-provenance.sh pin             # digest every third-party skill -> ~/.sps/provenance.json
#   bash scripts/sps-provenance.sh pin --repo      # digest the shipped skills (skill/sps*) -> <repo>/.sps/provenance-store.json
#   bash scripts/sps-provenance.sh check           # recompute digests; report-only, always exit 0
#   bash scripts/sps-provenance.sh check --strict  # same report; exit 1 on any PROVENANCE-DRIFT
#
# Two stores, two trust surfaces:
# 1. $HOME store (~/.sps/provenance.json): third-party skills found under the
#    installer's SYNC_PATHS dirs. UNPINNED there is onboarding state (a user
#    can install a new skill any time) — report-only even under --strict.
# 2. Repo store (<repo>/.sps/provenance-store.json): the skills THIS repo
#    ships (skill/sps, skill/sps-cms, skill/sps-seo). The store is committed,
#    so CI always has it; any drift — or a shipped skill absent from the
#    store — is tampering evidence and FAILS --strict. This is what makes
#    the README receipt "third-party skills can't be tampered with" a real,
#    machine-checked claim rather than a weekly report-only scan.
#
# Bundled skills (MANAGED_SKILLS in install.sh: sps, sps-cms, sps-seo) are
# skipped in the $HOME scan — they are governed by the install manifest and,
# in-repo, by the repo store above.
# Store record: { "<skill>": { "dir": ..., "sha256_skill_md": ..., "digest": ..., "pinned_at": ... } }
# digest = sha256 over the sorted file list + each file's sha256 (dir-content digest).
# Deps: git, python3. ANSI colors only when stdout is a TTY.
set -euo pipefail

MODE="check"
STRICT=0
REPO_PIN=0
case "${1:-}" in
  pin) MODE="pin"; [ "${2:-}" = "--repo" ] && REPO_PIN=1 ;;
  check|"") MODE="check" ;;
  *) echo "usage: sps-provenance.sh [pin [--repo]|check] [--strict]" >&2; exit 2 ;;
esac
if [ "$MODE" = "check" ] && [ "${2:-}" = "--strict" ]; then STRICT=1; fi

SCRIPT_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"

python3 - "$MODE" "$STRICT" "$SCRIPT_FILE" "$REPO_PIN" <<'PYEOF'
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
repo_pin = sys.argv[4] == "1"

TTY = sys.stdout.isatty()
def _c(code: str) -> str:
    return f"\033[{code}m" if TTY else ""
OK, WARN, BAD, DIM, END = _c("32"), _c("33"), _c("31"), _c("2"), _c("0")

home = Path(os.environ.get("HOME") or Path.home())
store_path = home / ".sps" / "provenance.json"

# Repo store: pins the skills this repo ships. Resolved from the script's own
# location so it works from any cwd; overridable via SPS_PROVENANCE_STORE.
repo_root = script.parent.parent
repo_store_path = Path(
    os.environ.get("SPS_PROVENANCE_STORE") or (repo_root / ".sps" / "provenance-store.json")
)
# Shipped skills live at skill/<name> (matching MANAGED_SKILLS in install.sh).
SHIPPED_SKILLS = ("sps", "sps-cms", "sps-seo")

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

if found_dirs == 0 and not repo_store_path.is_file():
    if mode == "pin":
        print(f"{DIM}note: no skills directories found (install.sh SYNC_PATHS) — nothing to pin{END}")
        raise SystemExit(0)
    # check mode with no $HOME skills and no repo store: truly nothing to do.
    print(f"{DIM}note: no skills directories found and no repo store — nothing to check{END}")
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

# --- repo-store mode: pin the shipped skills ---------------------------------
if repo_pin:
    store = {}
    for name in SHIPPED_SKILLS:
        d = repo_root / "skill" / name
        if not (d / "SKILL.md").is_file():
            print(f"{BAD}PIN-ERROR: shipped skill missing: {d}{END}")
            raise SystemExit(1)
        store[name] = {
            "dir": f"skill/{name}",
            "sha256_skill_md": sha256_file(d / "SKILL.md"),
            "digest": dir_digest(d),
            "pinned_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        print(f"PINNED: {name}  {DIM}({d}){END}")
    repo_store_path.parent.mkdir(parents=True, exist_ok=True)
    repo_store_path.write_text(json.dumps(store, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"== PROVENANCE PIN: {len(store)} shipped skill(s) -> {repo_store_path} ==")
    print("commit this store — CI check --strict fails if shipped skills drift from it")
    raise SystemExit(0)

# --- repo-store check: runs whenever the committed store exists --------------
repo_missing: list[str] = []
if repo_store_path.is_file():
    try:
        repo_store = json.loads(repo_store_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        print(f"{BAD}PROVENANCE-ERROR: unreadable {repo_store_path}: {exc}{END}")
        raise SystemExit(1)
    repo_drift = 0
    for name in sorted(set(repo_store) | set(SHIPPED_SKILLS)):
        rec = repo_store.get(name)
        d = repo_root / "skill" / name
        if rec is None:
            repo_missing.append(name)
            continue
        cur = dir_digest(d) if (d / "SKILL.md").is_file() else None
        md = sha256_file(d / "SKILL.md") if (d / "SKILL.md").is_file() else None
        if cur is None or cur != rec.get("digest") or md != rec.get("sha256_skill_md"):
            repo_drift += 1
            print(f"{BAD}REPO-DRIFT: {name}{END} — shipped skill changed since pin (skill/{name})")
        else:
            print(f"{OK}REPO-PINNED-OK: {name}{END}")
else:
    repo_drift = 0
    if not (repo_root / "install.sh").is_file():
        # Not running from a BuildPilot checkout (e.g. installed copy on a
        # user machine): repo-store verification doesn't apply.
        repo_store = None
    else:
        # Running from a checkout with no committed store: that itself is a
        # hole in the enforcement chain — say so loudly, fail under strict.
        print(f"{BAD}REPO-STORE-MISSING: {repo_store_path}{END} — run: scripts/sps-provenance.sh pin --repo")
        repo_store = None
        repo_drift = 1

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
if repo_store is not None and repo_missing:
    for name in repo_missing:
        print(f"{BAD}REPO-UNPINNED: {name}{END} — shipped skill absent from committed store")
    repo_drift += len(repo_missing)
if strict and (drift > 0 or repo_drift > 0):
    raise SystemExit(1)
raise SystemExit(0)
PYEOF
