#!/usr/bin/env bash
#
# sps-loop.sh — Karpathy-style agent loop driver for the SPS2 project.
#
# An LLM calling tools in a loop, with a human gate at every iteration:
#   1. PICK  — read the next unchecked task from loop/QUEUE.md
#   2. RUN   — one bounded `claude -p` work package
#   3. CHECK — you review; the task is checked off only on your confirmation
#
# Design constraints (Karpathy's minimal loop + this repo's own SPS rules):
#   * No daemon, no scheduler, no autonomous mode. Default max iterations = 1.
#   * Human confirmation before every task (unless --auto) AND before checking
#     a task off afterwards.
#   * Fail-closed: any unexpected error aborts the loop with a nonzero exit.
#   * Nothing in this script stages, commits, pushes, or releases anything.
#
# Usage:
#   bash loop/sps-loop.sh              # 1 iteration, confirm before each task
#   bash loop/sps-loop.sh --max 3      # at most 3 iterations
#   bash loop/sps-loop.sh --auto       # skip pre-task confirm (post-task gate stays)
#   bash loop/sps-loop.sh --dry-run    # print what would run; execute nothing
#
# Exit codes:
#   0  queue empty / max reached / STOP file honored (clean stop)
#   1  usage error
#   2  environment error (missing files, missing claude, unreadable state)
#   3  task runner failed (claude -p nonzero or produced no output)
#   130  interrupted by the user (Ctrl-C)

set -uo pipefail
# NOTE: `set -e` is deliberately NOT used; errors are checked explicitly so the
# human gate and the STATE.md log always run, even after a task failure.

# ---------------------------------------------------------------- constants --

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOOP_DIR="$SCRIPT_DIR"                     # this script lives inside loop/
REPO_ROOT="$(cd "$LOOP_DIR/.." && pwd)"

QUEUE_FILE="$LOOP_DIR/QUEUE.md"
STATE_FILE="$LOOP_DIR/STATE.md"
STOP_FILE="$LOOP_DIR/STOP"
LOG_DIR="$LOOP_DIR/logs"

MAX_ITERATIONS=1          # overridden by --max
AUTO_CONFIRM=0            # overridden by --auto
DRY_RUN=0                 # overridden by --dry-run

# Timeouts (seconds). A stuck task must not hang the loop forever.
TASK_TIMEOUT="${SPS_LOOP_TASK_TIMEOUT:-3600}"   # 1 h default, overridable via env

# Portable timeout: macOS lacks coreutils `timeout`; fall back to gtimeout,
# then to a bash-native watchdog (background kill) if neither exists.
run_with_timeout() {
  local secs="$1"; shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
  elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$secs" "$@"
  else
    # No timeout/gtimeout available. Run the child in its own process group
    # (via perl's setpgrp — perl ships with macOS) so the watchdog can kill
    # the entire subtree, not just the direct child.
    if command -v perl >/dev/null 2>&1; then
      perl -e 'setpgrp(0,0); exec @ARGV or die "exec failed: $!\n"' "$@" &
      local pid=$!
    else
      "$@" &
      local pid=$!
    fi
    ( sleep "$secs" && kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null ) &
    local watchdog=$!
    set +e
    wait "$pid"; local rc=$?
    set -u
    # Stop the watchdog; if it already fired, reap any stragglers in the
    # child's process group (e.g. a `sleep` the child spawned).
    if ! kill -TERM "$watchdog" 2>/dev/null; then
      kill -TERM -- "-$pid" 2>/dev/null
    fi
    wait "$watchdog" 2>/dev/null
    # Map a signal death (128+signal) of the child to timeout's exit code 124.
    if (( rc >= 128 && rc <= 191 )); then return 124; fi
    return "$rc"
  fi
}

# ------------------------------------------------------------------- output --

info()  { printf '%s\n'  "[loop] $*"; }
warn()  { printf '%s\n'  "[loop] WARNING: $*" >&2; }
die()   { printf '%s\n'  "[loop] ERROR: $*" >&2; exit "${2:-2}"; }

# --------------------------------------------------------------- interrupts --

# Ctrl-C must leave the worktree untouched and the state file consistent.
on_interrupt() {
  printf '\n[loop] Interrupted by user. No task was marked done.\n' >&2
  log_state "INTERRUPTED" "User interrupted the loop (Ctrl-C)."
  exit 130
}
trap on_interrupt INT

# ------------------------------------------------------------------ helpers --

usage() {
  cat <<'USAGE'
Usage: bash loop/sps-loop.sh [--max N] [--auto] [--dry-run]

  --max N     Run at most N iterations (default 1).
  --auto      Skip the pre-task confirmation prompt. The post-task
              "mark done?" confirmation always runs.
  --dry-run   Print the next task and the command that would run, then exit 0.
  -h, --help  Show this help.

Stop conditions: QUEUE.md has no unchecked tasks, --max reached, Ctrl-C,
or the file loop/STOP exists at the start of an iteration.
USAGE
}

require_file() {
  [[ -f "$1" ]] || die "required file missing: $1 (see loop/README.md)" 2
}

# Append one line to STATE.md. Never fails the loop on its own; if the state
# file is unwritable we warn loudly instead of silently losing history.
log_state() {
  local status="$1" detail="$2"
  local ts
  ts="$(date '+%Y-%m-%dT%H:%M:%S%z')" || ts="unknown-time"
  if ! printf '%s | %s | %s\n' "$ts" "$status" "$detail" >> "$STATE_FILE" 2>/dev/null; then
    warn "cannot append to $STATE_FILE — state history may be incomplete"
  fi
}

# Print the first unchecked task line ("...") from QUEUE.md, or nothing.
next_task() {
  grep -n '^- \[ \] ' "$QUEUE_FILE" 2>/dev/null | head -n 1 | cut -d: -f2- || true
}

# Mark the given task line as done, precisely, by line number.
mark_done() {
  local lineno="$1"
  awk -v n="$lineno" 'NR==n { sub(/^- \[ \] /, "- [x] ") } { print }' \
    "$QUEUE_FILE" > "$QUEUE_FILE.tmp.$$" \
    && mv "$QUEUE_FILE.tmp.$$" "$QUEUE_FILE"
}

# ------------------------------------------------------- task prompt (fixed) --

# The standing constraints below are verbatim-critical for this repository.
# They are injected into every work package so no iteration can drift.
task_prompt() {
  local task="$1" report="$2"
  cat <<PROMPT
Work package (one bounded task; do not start any other task):

  $task

Standing constraints (verbatim-critical):
- Do not stage, commit, push, pull, fetch, merge, rebase, deploy, publish, or release anything.
- Preserve every pre-existing modified/untracked file: no reset, clean, stash, revert, delete, move, or quarantine.
- Do not weaken tests, security controls, validators, path restrictions, scanner rules, or gate semantics.
- Never fabricate User approval, evidence, gate records, or test results. Never infer approval from prompts, reports, or prior wording.
- P10 must remain fail-closed. Do not claim P10/release readiness while gates fail.
- The coordination log reports/SPS2-COMPLETION-COORDINATION.md is append-only; never rewrite or delete another agent's entries.
- New reports go to reports/ as a NEW timestamped .md file; never overwrite prior reports.
- Do not edit CI, baselines, manifests, governance/approval records, P10 evidence, or .sps files unless this task explicitly authorizes it.

Deliverable: when finished, write a NEW timestamped report at:
  $report
summarizing exactly what you changed, what you verified, and what remains open.

When you are done, reply with a one-paragraph summary of the outcome.
PROMPT
}

# -------------------------------------------------------------------- parse --

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max)
      [[ $# -ge 2 ]] || die "--max requires a value" 1
      [[ "$2" =~ ^[1-9][0-9]*$ ]] || die "--max must be a positive integer, got: '$2'" 1
      MAX_ITERATIONS="$2"; shift 2 ;;
    --auto)    AUTO_CONFIRM=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)         usage >&2; die "unknown argument: $1" 1 ;;
  esac
done

# ------------------------------------------------------------------- checks --

require_file "$QUEUE_FILE"
if [[ ! -d "$SCRIPT_DIR" ]]; then
  die "loop directory not found: $SCRIPT_DIR" 2
fi

# The interactivity guard is enforced per-iteration (inside the loop, right
# before the pre-task gate) so non-interactive callers with an empty queue or
# a STOP file still get a clean exit 0 instead of a usage error.

if [[ $DRY_RUN -eq 0 ]] && ! command -v claude >/dev/null 2>&1; then
  die "claude CLI not found in PATH" 2
fi

mkdir -p "$LOG_DIR" 2>/dev/null || die "cannot create log dir $LOG_DIR" 2
touch "$STATE_FILE" 2>/dev/null || die "cannot write state file $STATE_FILE" 2

info "repo root : $REPO_ROOT"
info "queue     : $QUEUE_FILE"
info "state     : $STATE_FILE"
info "max iters : $MAX_ITERATIONS$([[ $AUTO_CONFIRM -eq 1 ]] && printf ' (auto)')$([[ $DRY_RUN -eq 1 ]] && printf ' (dry-run)')"

# ------------------------------------------------------------------- the loop --

iteration=0
while : ; do
  # --- stop conditions ------------------------------------------------------
  if [[ -e "$STOP_FILE" ]]; then
    info "STOP file present at $STOP_FILE — halting."
    log_state "STOPPED" "STOP file honored before iteration $((iteration + 1))."
    exit 0
  fi
  if (( iteration >= MAX_ITERATIONS )); then
    info "Reached --max $MAX_ITERATIONS — halting."
    log_state "HALT_MAX" "Iteration cap reached ($MAX_ITERATIONS)."
    exit 0
  fi

  task_line="$(next_task)"
  if [[ -z "$task_line" ]]; then
    info "Queue empty — no unchecked tasks in QUEUE.md. Done."
    log_state "DONE_QUEUE" "No unchecked tasks remain."
    exit 0
  fi
  lineno="$(grep -n '^- \[ \] ' "$QUEUE_FILE" | head -n 1 | cut -d: -f1)"

  iteration=$((iteration + 1))
  info "─────────────────────────────────────────────────────────"
  info "iteration $iteration/$MAX_ITERATIONS"
  info "task      : $task_line"

  # --- human gate (pre-task) -------------------------------------------------
  if [[ $AUTO_CONFIRM -eq 0 && $DRY_RUN -eq 0 ]]; then
    if [[ ! -t 0 ]]; then
      die "stdin is not a terminal and --auto not given; run interactively or pass --auto" 1
    fi
    printf '[loop] Run this task? [y/N] '
    read -r answer
    case "$answer" in
      y|Y|yes|YES) ;;
      *) info "Skipped by user."; log_state "SKIPPED" "$task_line"; continue ;;
    esac
  fi

  # --- dry run ---------------------------------------------------------------
  report_file="$REPO_ROOT/reports/SPS2-LOOP-TASK-$(date '+%Y%m%d-%H%M%S').md"
  if [[ $DRY_RUN -eq 1 ]]; then
    info "dry-run: would execute:"
    printf '  claude -p "<work-package prompt; see loop/README.md>"\n'
    info "dry-run: report would be written to $report_file"
    exit 0
  fi

  # --- RUN: one bounded work package -----------------------------------------
  log_file="$LOG_DIR/task-$(date '+%Y%m%d-%H%M%S').log"
  prompt="$(task_prompt "$task_line" "$report_file")"
  info "running claude -p (timeout ${TASK_TIMEOUT}s) — log: $log_file"
  start_epoch="$(date +%s)"
  set +e
  run_with_timeout "${TASK_TIMEOUT}" claude -p "$prompt" > "$log_file" 2>&1
  rc=$?
  set -u
  end_epoch="$(date +%s)"

  # --- CHECK: classify the outcome --------------------------------------------
  if (( rc == 124 )); then
    warn "task timed out after ${TASK_TIMEOUT}s (exit 124)."
    log_state "TIMEOUT" "$task_line (log: $log_file)"
    printf '[loop] Mark this task done anyway? [y/N] '
    read -r answer
    case "$answer" in y|Y|yes|YES) mark_done "$lineno" && info "marked done." ;; esac
    continue
  fi
  if (( rc != 0 )); then
    warn "claude -p exited $rc — see $log_file"
    log_state "FAILED" "$task_line (rc=$rc, log: $log_file)"
    printf '[loop] Retry this task later (leave unchecked) or mark done? [r/y/N] '
    read -r answer
    case "$answer" in
      y|Y|yes|YES) mark_done "$lineno" && info "marked done." ;;
      r|R|retry)   log_state "RETRY_QUEUED" "$task_line"; info "left unchecked for retry." ;;
      *)           info "left unchecked." ;;
    esac
    continue
  fi
  if [[ ! -s "$log_file" ]]; then
    warn "claude -p produced no output — treating as failure."
    log_state "FAILED" "$task_line (empty output, log: $log_file)"
    continue
  fi

  info "task finished in $((end_epoch - start_epoch))s — output: $log_file"
  printf '%s\n' "──────── summary (last 30 lines of output) ────────"
  tail -n 30 "$log_file"
  printf '%s\n' "───────────────────────────────────────────────────"

  # --- human gate (post-task) --------------------------------------------------
  log_state "COMPLETED" "$task_line (rc=0, log: $log_file)"
  printf '[loop] Mark this task done? [y/N] '
  read -r answer
  case "$answer" in
    y|Y|yes|YES) mark_done "$lineno" && info "marked done." ;;
    *) info "left unchecked — it will run again next iteration." ;;
  esac
done
