#!/usr/bin/env bash
# sps-lawlog.sh — run the SPS law checkers and keep a rejection ledger (T-20)
# Usage:
#   bash scripts/sps-lawlog.sh run          # check + append FAILs to .sps/law-rejections.jsonl
#   bash scripts/sps-lawlog.sh show         # summarize ledger: counts, first/last seen, repeat hints
#   bash scripts/sps-lawlog.sh clear --yes  # archive ledger to .sps/law-rejections-<YYYYMMDD>.jsonl
# Works from any cwd inside the repo (root resolved via git). ANSI colors on TTY only.
# A "repeat" = same (check_id, target_file) already in the ledger from an earlier
# run; dates are compared by date part only (ts[:10] <= today), so a same-day
# rerun of a still-unfixed violation counts as a repeat (plan trigger: two runs).
set -euo pipefail

# --- optional colors (TTY only) ---------------------------------------------
if [ -t 1 ]; then
  C_HEAD=$'\033[1m'; C_DIM=$'\033[2m'; C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_END=$'\033[0m'
else
  C_HEAD=""; C_DIM=""; C_OK=""; C_WARN=""; C_END=""
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "sps-lawlog: not inside a git repository (run from within the repo)" >&2
  exit 1
}
LEDGER="$ROOT/.sps/law-rejections.jsonl"
CHECKER="$ROOT/framework/sps2/tools/check_laws.py"
GEN_CHECKER="$ROOT/framework/sps2/tools/check_generated_tests.py"
mkdir -p "$ROOT/.sps"

cmd="${1:-}"
[ $# -gt 0 ] && shift
case "$cmd" in
  run|show|clear) ;;
  *)
    echo "usage: sps-lawlog.sh {run|show|clear [--yes]}" >&2
    exit 2
    ;;
esac

# --- run: checkers + ledger append ------------------------------------------
if [ "$cmd" = "run" ]; then
  [ -f "$CHECKER" ] || { echo "sps-lawlog: checker missing: $CHECKER" >&2; exit 1; }
  tmpout="$(mktemp "${TMPDIR:-/tmp}/sps-lawlog.XXXXXX")"
  trap 'rm -f "$tmpout"' EXIT
  ( cd "$ROOT" && python3 "$CHECKER" . ) >"$tmpout" 2>&1 || true
  # Sibling checker (T-20) — run if present, skip silently if not yet built.
  # No path argument: it defaults to its own tests dir (a "." arg breaks its glob).
  if [ -f "$GEN_CHECKER" ]; then
    ( cd "$ROOT" && python3 "$GEN_CHECKER" ) >>"$tmpout" 2>&1 || true
  fi
  cat "$tmpout"
  LAWLOG_LOG="$LEDGER" python3 - "$tmpout" <<'PY'
import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

out_path = Path(sys.argv[1])
ledger_path = Path(os.environ["LAWLOG_LOG"])
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# check_laws.py main() prints one violation per line to stderr, via v(...):
#   v(f"dod-24 hardcoded-config: {rel}:{i}: {code}")  -> "id words: path:line: text"
#   v(f"dod-22 junk file: {rel}")                     -> "id words: path"
#   v(f"context-budget: .sps/{name} {n}L/{b}B ...")   -> "id words: path ..."
# check_generated_tests.py mirrors it: "GENERATED_TEST_UNREVIEWED: <path>: detail"
# i.e. "<check id words>: <message>"; summary lines start with "==" and its
# "note: no generated tests ..." line is informational, never a FAIL.
LINE_RE = re.compile(r"^([A-Za-z0-9][^:]*):\s*(.+)$")


def parse_line(line):
    m = LINE_RE.match(line)
    if not m:
        return None
    check_id = m.group(1).strip()
    rest = m.group(2).strip()
    fm = re.match(r"^(\S+?):\d+:", rest)  # "path/to/file.py:12: code"
    if fm:
        target = fm.group(1)
    else:
        tok = rest.split()
        cand = tok[0] if tok else ""
        if cand.endswith(":"):  # GENERATED_TEST_UNREVIEWED: "<abs path>: detail"
            cand = cand[:-1]
        target = cand if cand and ("/" in cand or re.search(r"\.[A-Za-z0-9]{1,6}$", cand)) else ""
    return check_id, target, line


prior = set()
if ledger_path.exists():
    for raw in ledger_path.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except ValueError:
            continue
        d = str(rec.get("ts", ""))[:10]  # date part only
        if d and d <= today:
            prior.add((str(rec.get("check_id", "")), str(rec.get("target_file", ""))))

entries, repeats = [], 0
for line in out_path.read_text(encoding="utf-8", errors="replace").splitlines():
    line = line.strip()
    if not line or line.startswith("==") or line.startswith("note:"):
        continue
    parsed = parse_line(line)
    if parsed is None:
        continue
    check_id, target, message = parsed
    if (check_id, target) in prior:
        repeats += 1
    entries.append({
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "check_id": check_id,
        "target_file": target,
        "message": message,
    })

if entries:
    with ledger_path.open("a", encoding="utf-8") as fh:
        for e in entries:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
print(f"LAWLOG: {len(entries)} failures logged ({repeats} repeats)")
PY
  exit 0
fi

# --- show: ledger summary ----------------------------------------------------
if [ "$cmd" = "show" ]; then
  LAWLOG_WARN="$C_WARN" LAWLOG_END="$C_END" python3 - "$LEDGER" <<'PY'
import json, os, sys
from pathlib import Path

ledger = Path(sys.argv[1])
warn = os.environ.get("LAWLOG_WARN", "")
end = os.environ.get("LAWLOG_END", "")
groups = {}
if ledger.exists():
    for raw in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except ValueError:
            continue
        d = str(rec.get("ts", ""))[:10]
        if not d:
            continue
        key = (str(rec.get("check_id", "")), str(rec.get("target_file", "")))
        groups.setdefault(key, []).append(d)

if not groups:
    print("LAWLOG: ledger empty")
    raise SystemExit(0)

print("LAWLOG ledger: .sps/law-rejections.jsonl")
for (check_id, target), dates in sorted(groups.items()):
    dates.sort()
    loc = target if target else "(no file)"
    print(f"  {check_id} | {loc} | count={len(dates)} | first {dates[0]} | last {dates[-1]}")
    if len(dates) >= 2:
        print(f"    {warn}REPEAT — propose test: python3 framework/sps2/tools/gen_law_test.py"
              f" --check {check_id} --file {target}{end}")
PY
  exit 0
fi

# --- clear: archive the ledger ----------------------------------------------
if [ "${1:-}" != "--yes" ]; then
  echo "sps-lawlog: refusing to clear the ledger without --yes" >&2
  echo "  (clear archives .sps/law-rejections.jsonl to .sps/law-rejections-<YYYYMMDD>.jsonl)" >&2
  exit 1
fi
if [ ! -f "$LEDGER" ]; then
  echo "LAWLOG: ledger empty"
  exit 0
fi
stamp="$(date +%Y%m%d)"
archive="$ROOT/.sps/law-rejections-${stamp}.jsonl"
if [ -e "$archive" ]; then
  echo "sps-lawlog: archive already exists: .sps/law-rejections-${stamp}.jsonl — remove or rename it first" >&2
  exit 1
fi
mv "$LEDGER" "$archive"
echo "LAWLOG: ledger archived to .sps/law-rejections-${stamp}.jsonl"
