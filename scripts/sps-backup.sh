#!/usr/bin/env bash
# sps-backup.sh — timestamped .sps/ snapshots + guided restore (T-24)
# Usage:
#   bash scripts/sps-backup.sh snapshot                    # .sps/ -> .sps/backups/sps-<ts>.tar.gz (keep last 10)
#   bash scripts/sps-backup.sh restore <snapshot> [--yes]  # verify + preview; --yes replaces .sps/
#   bash scripts/sps-backup.sh list                        # table: name, size, age
# Snapshots exclude: .sps/backups itself, .sps/quarantine/, and
# law-rejections-*.jsonl ARCHIVES (the live .sps/law-rejections.jsonl ledger
# IS included — it is governance data). Restore moves the current .sps/ to
# .sps.pre-restore-<ts> and NEVER deletes it. Retention prunes only old
# sps-*.tar.gz snapshot files, one PRUNED: line each.
# Conventions: set -euo pipefail; git-root resolution; TTY-gated ANSI; no deps
# beyond git/tar/python3; works from any cwd inside the project.
set -euo pipefail

if [ -t 1 ]; then
  C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_DIM=$'\033[2m'; C_END=$'\033[0m'
else
  C_OK=""; C_WARN=""; C_DIM=""; C_END=""
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "sps-backup: not inside a git repository (run from within the project)" >&2
  exit 1
}
SPS="$ROOT/.sps"
BACKUPS="$SPS/backups"
KEEP=10

cmd="${1:-}"
if [ $# -gt 0 ]; then shift; fi

usage() {
  echo "usage: sps-backup.sh {snapshot|restore <snapshot> [--yes]|list}" >&2
  exit 2
}
case "$cmd" in
  snapshot|restore|list) ;;
  *) usage ;;
esac

# --- snapshot ------------------------------------------------------------------
if [ "$cmd" = "snapshot" ]; then
  if [ ! -d "$SPS" ]; then
    echo "sps-backup: no .sps/ here — nothing to snapshot (not an error)"
    exit 0
  fi
  mkdir -p "$BACKUPS"
  stamp="$(date +%Y%m%d-%H%M%S)"
  while [ -e "$BACKUPS/sps-$stamp.tar.gz" ]; do stamp="${stamp}-x"; done
  out="$BACKUPS/sps-$stamp.tar.gz"
  tar -czf "$out" -C "$ROOT" \
    --exclude='.sps/backups' \
    --exclude='.sps/quarantine' \
    --exclude='.sps/law-rejections-*.jsonl' \
    .sps
  files="$(tar -tzf "$out" | grep -vc '/$' || true)"
  echo "SNAPSHOT: .sps/backups/$(basename "$out") ($files files)"
  # Rolling retention: keep the newest $KEEP by name (timestamp names sort
  # chronologically); prune older snapshots only — never .sps content.
  total="$(ls -1 "$BACKUPS"/sps-*.tar.gz 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$total" -gt "$KEEP" ]; then
    excess=$((total - KEEP))
    ls -1 "$BACKUPS"/sps-*.tar.gz | sort | head -n "$excess" | while IFS= read -r old; do
      [ -z "$old" ] && continue
      rm -f "$old"
      echo "PRUNED: $(basename "$old")"
    done
  fi
  exit 0
fi

# --- restore -------------------------------------------------------------------
if [ "$cmd" = "restore" ]; then
  snap="${1:-}"
  if [ $# -gt 0 ]; then shift; fi
  [ -n "$snap" ] || usage
  yes_flag="no"
  for a in "$@"; do
    if [ "$a" = "--yes" ]; then yes_flag="yes"; fi
  done
  if [ ! -f "$snap" ] && [ -f "$BACKUPS/$snap" ]; then
    snap="$BACKUPS/$snap"
  fi
  if [ ! -f "$snap" ]; then
    echo "sps-backup: snapshot not found: $snap" >&2
    exit 1
  fi
  tar -tzf "$snap" >/dev/null   # integrity check: a corrupt archive aborts here
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/sps-restore.XXXXXX")"
  tar -xzf "$snap" -C "$tmp"
  if [ ! -d "$tmp/.sps" ]; then
    echo "sps-backup: archive does not contain a .sps/ directory: $snap" >&2
    rm -rf "$tmp"
    exit 1
  fi
  summary="$(python3 - "$tmp/.sps" <<'PY'
import os, sys, time
root = sys.argv[1]
count = 0
total = 0
mtimes = []
for d, _dirs, files in os.walk(root):
    for f in files:
        p = os.path.join(d, f)
        st = os.lstat(p)
        count += 1
        total += st.st_size
        mtimes.append(st.st_mtime)
if mtimes:
    fmt = lambda t: time.strftime("%Y-%m-%d %H:%M", time.localtime(t))
    newest, oldest = fmt(max(mtimes)), fmt(min(mtimes))
else:
    newest = oldest = "?"
print(count, total, newest, oldest)
PY
)"
  read -r fcount fsize newest oldest <<<"$summary"
  echo "RESTORE PREVIEW: $snap"
  echo "  files: $fcount   total size: $fsize bytes   newest mtime: $newest   oldest mtime: $oldest"
  if [ "$yes_flag" != "yes" ]; then
    echo "sps-backup: ${C_WARN}refusing to replace .sps/ without --yes${C_END} — preview only, nothing changed"
    rm -rf "$tmp"
    exit 1
  fi
  ts="$(date +%Y%m%d-%H%M%S)"
  pre="$ROOT/.sps.pre-restore-$ts"
  if [ -d "$SPS" ]; then
    mv "$SPS" "$pre"
    echo "MOVED ASIDE: .sps -> $(basename "$pre") (kept, never deleted)"
  else
    pre="(none — no prior .sps/)"
  fi
  mv "$tmp/.sps" "$SPS"
  rm -rf "$tmp"
  echo "RESTORED: .sps/ replaced from $(basename "$snap")"
  echo "  previous .sps/ kept at: $pre (your safety net — remove it yourself when satisfied)"
  exit 0
fi

# --- list ----------------------------------------------------------------------
if [ ! -d "$BACKUPS" ] || ! ls "$BACKUPS"/sps-*.tar.gz >/dev/null 2>&1; then
  echo "sps-backup: no snapshots in .sps/backups/"
  exit 0
fi
python3 - "$BACKUPS" <<'PY'
import os, sys, time
d = sys.argv[1]
snaps = sorted(f for f in os.listdir(d) if f.startswith("sps-") and f.endswith(".tar.gz"))
now = time.time()
print(f"{'snapshot':<44}{'size':>10}  age")
for f in snaps:
    p = os.path.join(d, f)
    kb = os.path.getsize(p) / 1024.0
    age_s = max(now - os.path.getmtime(p), 0)
    age = f"{age_s / 86400:.1f}d" if age_s >= 86400 else f"{age_s / 3600:.1f}h"
    print(f"{f:<44}{kb:>9.1f}K  {age}")
PY
