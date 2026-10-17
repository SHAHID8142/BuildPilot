#!/usr/bin/env bash
# sps-status.sh — one-command project state dashboard (read-only)
# Usage: bash scripts/sps-status.sh   (from repo root; `/sps status`)
# Prints ~20 lines of plain text. ANSI colors only when stdout is a TTY.
set -uo pipefail

# --- optional colors (TTY only) -------------------------------------------
if [ -t 1 ]; then
  C_HEAD=$'\033[1m'; C_DIM=$'\033[2m'; C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_END=$'\033[0m'
else
  C_HEAD=""; C_DIM=""; C_OK=""; C_WARN=""; C_END=""
fi
sec() { printf '\n%s%s%s\n' "$C_HEAD" "$1" "$C_END"; }

# days_until YYYY-MM-DD -> integer days from today (portable: GNU/BSD date)
days_until() {
  local target="$1" now epoch_t epoch_n
  now="$(date +%Y-%m-%d)"
  if date -d "$target" +%s >/dev/null 2>&1 && date -d "$now" +%s >/dev/null 2>&1; then
    epoch_t="$(date -d "$target" +%s)"; epoch_n="$(date -d "$now" +%s)"
  elif date -j -f "%Y-%m-%d" "$target" +%s >/dev/null 2>&1 && date -j -f "%Y-%m-%d" "$now" +%s >/dev/null 2>&1; then
    epoch_t="$(date -j -f "%Y-%m-%d" "$target" +%s)"; epoch_n="$(date -j -f "%Y-%m-%d" "$now" +%s)"
  else
    echo "?"; return
  fi
  echo $(( (epoch_t - epoch_n) / 86400 ))
}

# --- git --------------------------------------------------------------------
sec "== SPS Status =="
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
  commit_date="$(git log -1 --format=%cs 2>/dev/null)"
  commit_subj="$(git log -1 --format=%s 2>/dev/null)"
  echo "Branch: ${branch}  ${C_DIM}| last commit: ${commit_date:-?} ${commit_subj:-?}${C_END}"
  dirty="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$dirty" -eq 0 ]; then
    echo "Working tree: ${C_OK}clean${C_END}"
  else
    echo "Working tree: ${C_WARN}${dirty} modified/untracked file(s)${C_END}"
  fi
  if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
    unpushed="$(git log '@{u}..' --oneline 2>/dev/null | wc -l | tr -d ' ')"
    echo "Unpushed commits: ${unpushed}"
  else
    echo "Unpushed commits: n/a (no upstream set)"
  fi
else
  echo "Not a git repository."
fi

# --- task queue -------------------------------------------------------------
sec "Task queue"
if [ -f .sps/task-queue.md ]; then
  doing="$(awk '/^## doing/{f=1;next} /^## /{f=0} f' .sps/task-queue.md | grep -v '^[[:space:]]*$' | grep -cv '(empty')"
  queued="$(awk 'tolower($0) ~ /^## queued/{f=1;next} /^## /{f=0} f' .sps/task-queue.md | grep -v '^[[:space:]]*$' | grep -cv '(empty')"
  if [ "$doing" -gt 0 ]; then
    echo "Doing: ${doing}"
    awk '/^## doing/{f=1;next} /^## /{f=0} f' .sps/task-queue.md | grep -v '^[[:space:]]*$' | grep -v '(empty' | sed 's/^/  /'
  else
    echo "Doing: nothing"
  fi
  echo "Queued: ${queued}"
  done_n="$(awk 'tolower($0) ~ /^## done/{f=1;next} /^## /{f=0} f' .sps/task-queue.md | grep -c '^- \[x\]')"
  [ "$done_n" -gt 0 ] && echo "Done: ${done_n} task(s) recorded"
else
  echo "No .sps/task-queue.md"
fi

# --- handoff ----------------------------------------------------------------
sec "Last handoff"
if [ -f .sps/handoff.md ]; then
  awk '/^## /{h=$0; n=0; next} n<2 && NF {if(n==0) l1=$0; else l2=$0; n++} END{print h; if(l1!="")print substr(l1,1,120); if(l2!="")print substr(l2,1,120)}' .sps/handoff.md | sed 's/^/  /'
else
  echo "  No .sps/handoff.md"
fi

# --- after-sale clocks ------------------------------------------------------
sec "After-sale"
if [ -f .sps/after-sale.md ]; then
  found=0
  while IFS= read -r line; do
    label="${line%%:*}"
    date_val="$(printf '%s' "$line" | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}' | head -1)"
    [ -z "$date_val" ] && continue
    remaining="$(days_until "$date_val")"
    case "$remaining" in
      ?)  echo "  ${label}: ${date_val} (unknown days)";;
      -*) echo "  ${label}: ${date_val} (${-remaining} day(s) past)";;
      *)  echo "  ${label}: ${date_val} (${remaining} day(s) remaining)";;
    esac
    found=1
  done <<AFTEREOF
$(grep -iE 'deliver|support|seo' .sps/after-sale.md)
AFTEREOF
  [ "$found" -eq 0 ] && echo "  after-sale.md exists but no delivery/support/SEO dates found"
else
  echo "  no active after-sale window"
fi

# --- skill version / lessons ------------------------------------------------
sec "Skill"
if [ -f skill/sps/VERSION ]; then
  echo "Version: $(cat skill/sps/VERSION)"
else
  echo "Version: unknown (skill/sps/VERSION missing)"
fi
lessons="$(ls lessons/inbox/LESSON-*.md 2>/dev/null | wc -l | tr -d ' ')"
echo "Pending lessons: ${lessons}"
