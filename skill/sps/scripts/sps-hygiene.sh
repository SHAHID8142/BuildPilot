#!/usr/bin/env bash
# sps-hygiene.sh — directory-hygiene check + safe-move fixer (T-23)
# Usage:
#   bash scripts/sps-hygiene.sh        # check (default): report only, exit 0
#   bash scripts/sps-hygiene.sh fix    # safe moves only; AMBIGUOUS listed; exit 2 if ambiguous remain
# Companion law: skill/sps/DIRECTORY-HYGIENE.md
# Never deletes: `fix` moves temp-pattern files to .sps/quarantine/ instead.
# ANSI colors only when stdout is a TTY. Deps: git, python3.
set -uo pipefail

if [ -t 1 ]; then
  C_HEAD=$'\033[1m'; C_DIM=$'\033[2m'; C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_BAD=$'\033[31m'; C_END=$'\033[0m'
else
  C_HEAD=""; C_DIM=""; C_OK=""; C_WARN=""; C_BAD=""; C_END=""
fi

MODE="check"
[ "${1:-}" = "fix" ] && MODE="fix"

REPO="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$REPO" ]; then
  echo "sps-hygiene: not inside a git repository" >&2
  exit 0
fi
cd "$REPO" || exit 1

VIOLATIONS=0      # count of reported problems
MOVED_N=0
AMBIGUOUS_N=0

note()  { printf '%s\n' "$1"; }
viol()  { VIOLATIONS=$((VIOLATIONS + 1)); printf '%s%s%s\n' "$C_BAD" "$1" "$C_END"; }
moved() { printf 'MOVED: %s -> %s\n' "$1" "$2"; MOVED_N=$((MOVED_N + 1)); }
ambig() { printf 'AMBIGUOUS: %s — %s\n' "$1" "$2"; AMBIGUOUS_N=$((AMBIGUOUS_N + 1)); }

# ---------------------------------------------------------------------------
# Root allowlist (everything else directly in root is a stray)
# ---------------------------------------------------------------------------
root_allowed() {
  case "$1" in
    # standard root docs
    README.md|LICENSE|LICENSE*|VERSION|CHANGELOG.md|CATALOG.md|USER-GUIDE.md) return 0 ;;
    # host lock mirrors
    AGENTS.md|CLAUDE.md|GEMINI.md) return 0 ;;
    # installer entrypoints
    install.sh|install.ps1|get-sps.sh|get-sps.ps1|uninstall.sh|uninstall.ps1|update-sps.ps1) return 0 ;;
    # dotfiles / machine config
    .gitignore|.gitmodules|.mcp.json|.editorconfig|.nvmrc|.npmrc) return 0 ;;
    # security gate config (scripts/secret-scan.sh reads this; manifest-pinned)
    .secrets-allowlist) return 0 ;;
    # standard directories
    .git|.github|.claude|.claude-plugin|.sps|.kilo|.vscode|.idea|.agents|.agent|.cursor|.cline|.roo|.continue|.codeium|.pytest_cache|.workbuddy-ai) return 0 ;;
    .claude-plugin*|.claude*) return 0 ;;
    # standard repo dirs
    scripts|skill|reports|docs|framework|lessons|templates|plugins|loop|tests) return 0 ;;
    SPS2-PROJECT-COMPLETION-RECORD) return 0 ;;  # pre-existing project-record dir (tracked)
    *) return 1 ;;
  esac
}

# Suggested home for a stray root file, when determinable. Empty = ambiguous.
suggest_home() {
  case "$1" in
    *REPORT*.md|SPS2-*.md|CODEX-*.md|CLAUDE-*-REVIEW*.md|SPS2-PROJECT-COMPLETION-RECORD*) echo "reports/" ;;
    *.sh|*.ps1) echo "scripts/ (+ byte-identical mirror in skill/sps/scripts/)" ;;
    test_*.py) echo "framework/sps2/tests/" ;;
    *.py) echo "framework/sps2/tools/ (validator) or framework/sps2/tests/ (test)" ;;
    *LESSON-*.md) echo "lessons/inbox/" ;;
    *DEC-*.md|*-DECISIONS*.json|*DECISION*.md) echo "framework/sps2/decisions/" ;;
    *.md) echo "docs/ (or skill/sps/ if it is a skill rule)" ;;
    *) echo "" ;;
  esac
}

# ---------------------------------------------------------------------------
# Collect candidate files: tracked files + untracked (git status --porcelain)
# ---------------------------------------------------------------------------
# File lists are newline-separated relative paths; -print0/-z for safety.
root_files="$(python3 - "$REPO" <<'PYEOF'
import subprocess, sys, os
repo = sys.argv[1]
os.chdir(repo)
out = set()
try:
    ls = subprocess.run(["git", "ls-files", "-z"], capture_output=True).stdout
    for p in ls.decode("utf-8", "replace").split("\0"):
        if p and "/" not in p:
            out.add(p)
except Exception:
    pass
try:
    st = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all"], capture_output=True).stdout
    toks = st.decode("utf-8", "replace").split("\0")
    i = 0
    while i < len(toks):
        tok = toks[i]
        i += 1
        if not tok:
            continue
        # -z format: XY <path>\0 [<origPath>\0 for renames]. Consume the
        # rename pair explicitly so the post-rename path is never parsed as
        # a standalone root path (audit NIT). -z never quotes, so no
        # quote-stripping (the old .replace mangled legit quoted names).
        p = tok[3:] if len(tok) > 3 and tok[2] == " " else tok
        if p.startswith("../") or "/" in p:
            # Still consume a rename orig-path if present.
            if tok[:2] in ("R ", "RM") and i < len(toks) and toks[i]:
                i += 1
            continue
        if tok[:2] in ("R ", "RM") and i < len(toks) and toks[i]:
            i += 1  # skip the paired orig-path token
        if p:
            out.add(p)
except Exception:
    pass
for p in sorted(out):
    if os.path.isfile(p):
        print(p)
PYEOF
)"

# All tracked files (for temp-pattern sweep) + untracked files anywhere.
tracked_tree="$(git ls-files -z | tr '\0' '\n')"
untracked_tree="$(git status --porcelain -z --untracked-files=all | tr '\0' '\n' | sed -n 's/^?? //p' | tr -d '"')"

# ---------------------------------------------------------------------------
# Temp/scratch pattern matcher (shared by root scan and tree sweep)
# ---------------------------------------------------------------------------
is_temp_name() {
  local base="${1##*/}"
  case "$base" in
    *.tmp|*.bak|*~|*.swp|.DS_Store|scratch*|tmp*|*-copy*|[#]*[#]) return 0 ;;
    *) return 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# a. Stray files in repo root
# ---------------------------------------------------------------------------
printf '%s\n' "${C_HEAD}== Root strays ==${C_END}"
while IFS= read -r f; do
  [ -z "$f" ] && continue
  root_allowed "$f" && continue
  # temp-pattern files in root are flagged once, by the sweep below — skip here
  if is_temp_name "$f"; then continue; fi
  home="$(suggest_home "$f")"
  tracked="$(git ls-files --error-unmatch "$f" >/dev/null 2>&1 && echo yes || echo no)"
  if [ "$home" = "reports/" ]; then
    # orphan report in root: determinable home
    viol "ROOT-STRAY: $f — orphan report, home: reports/"
    if [ "$MODE" = "fix" ]; then
      if [ "$tracked" = "yes" ] && [ -n "$(git status --porcelain -- "$f")" ]; then
        ambig "$f" "tracked file with uncommitted changes — move it yourself after committing"
      elif [ -e "reports/$(basename "$f")" ]; then
        ambig "$f" "reports/$(basename "$f") already exists — rename with a fresh timestamp instead"
      else
        mkdir -p reports
        mv "$f" reports/ && moved "$f" "reports/$(basename "$f")"
      fi
    fi
  elif [ -n "$home" ] && [ "$tracked" = "no" ]; then
    # untracked stray with a determinable home, NOT a report: untracked work is
    # presumed user work — list it, never move it silently (law rule 9)
    viol "ROOT-STRAY: $f — untracked, suggested home: $home"
    [ "$MODE" = "fix" ] && ambig "$f" "untracked file with suggested home: $home — confirm before moving"
  elif [ -n "$home" ]; then
    viol "ROOT-STRAY: $f — suggested home: $home"
    if [ "$MODE" = "fix" ]; then
      if [ -n "$(git status --porcelain -- "$f")" ]; then
        ambig "$f" "tracked file with uncommitted changes — move it yourself after committing"
      else
        dest="${home%% *}"
        mkdir -p "$dest"
        mv "$f" "$dest" && moved "$f" "$dest$(basename "$f")"
      fi
    fi
  else
    viol "ROOT-STRAY: $f — no determinable home"
    [ "$MODE" = "fix" ] && ambig "$f" "no determinable home — user decides"
  fi
done <<ROOTEOF
$root_files
ROOTEOF
[ "$VIOLATIONS" -eq 0 ] && note "${C_OK}root is clean${C_END}"

# ---------------------------------------------------------------------------
# b. Temp/scratch patterns anywhere in the tracked + untracked tree
# ---------------------------------------------------------------------------
printf '\n%s\n' "${C_HEAD}== Temp/scratch patterns ==${C_END}"
temp_count=0
temp_seen="|"
temp_scan="$( { printf '%s\n' "$tracked_tree"; printf '%s\n' "$untracked_tree"; } \
  | sed '/^$/d' | sort -u )"
while IFS= read -r f; do
  [ -z "$f" ] && continue
  is_temp_name "$f" || continue
  case "$f" in
    .sps/quarantine/*|.git/*|.gitignore) continue ;;
  esac
  case "$temp_seen" in *"|$f|"*) continue ;; esac
  temp_seen="$temp_seen$f|"
  [ -f "$f" ] || continue
  temp_count=$((temp_count + 1))
  viol "TEMP-FILE: $f — temp/scratch pattern in tree, should not exist (quarantine or delete)"
  if [ "$MODE" = "fix" ]; then
    tracked="$(git ls-files --error-unmatch "$f" >/dev/null 2>&1 && echo yes || echo no)"
    if [ "$tracked" = "yes" ] && [ -n "$(git status --porcelain -- "$f")" ]; then
      ambig "$f" "temp-pattern file with uncommitted changes — user decides"
    else
      mkdir -p .sps/quarantine
      dest=".sps/quarantine/$(basename "$f")"
      if [ -e "$dest" ]; then
        dest=".sps/quarantine/$(date +%Y%m%d%H%M%S)-$(basename "$f")"
      fi
      mv "$f" "$dest" && moved "$f" "$dest"
    fi
  fi
done <<TEMPEOF
$temp_scan
TEMPEOF
[ "$temp_count" -eq 0 ] && note "${C_OK}no temp/scratch files in tree${C_END}"

# ---------------------------------------------------------------------------
# c. Orphan reports in repo root (subset of root strays, called out explicitly)
# ---------------------------------------------------------------------------
# Already flagged as ROOT-STRAY with home reports/ above; nothing extra here
# beyond a summary line for scanability.
orphan_n="$(printf '%s\n' "$root_files" | grep -Eic '^(.*REPORT[^/]*\.md|SPS2-[^/]*\.md)$' || true)"
if [ "$orphan_n" -gt 0 ]; then
  note "(${orphan_n} orphan report(s) in root flagged above)"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
printf '\n'
if [ "$VIOLATIONS" -eq 0 ]; then
  printf '%s== HYGIENE CHECK: clean ==%s\n' "$C_OK" "$C_END"
else
  printf '%s== HYGIENE CHECK: %s violation(s) ==%s\n' "$C_WARN" "$VIOLATIONS" "$C_END"
fi
if [ "$MODE" = "fix" ]; then
  note "moved: ${MOVED_N}   ambiguous (not touched): ${AMBIGUOUS_N}"
  if [ "$AMBIGUOUS_N" -gt 0 ]; then
    exit 2
  fi
fi
exit 0
