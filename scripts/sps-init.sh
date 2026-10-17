#!/usr/bin/env bash
# sps-init.sh — one-command client-project scaffold (T-36)
# Usage:
#   bash scripts/sps-init.sh [target-dir]    # default: current directory
#
# Scaffolds a fresh CLIENT project for the SPS workflow, idempotently:
#   .sps/                    workflow directory
#   .sps/kickoff.md          kickoff questionnaire with EMPTY answer slots
#                            (the human answers; matches what
#                            framework/sps2/tools/check_kickoff.py expects)
#   .sps/backups/            snapshot dir used by scripts/sps-backup.sh
#   .sps/agent.md            starter options (commented out, incl.
#                            "# language: plain" for plain-language mode)
#   .sps/task-queue.md       empty task-queue skeleton
#   CHEAT-SHEET.md           symlink to skill/sps/CHEAT-SHEET.md when the
#                            skill is installed in the project, else a
#                            one-line pointer note
#
# Refuses to run inside the BuildPilot repo itself (framework/sps2 present)
# — this scaffolds client projects, not the framework.
#
# NEVER overwrites: existing files are left untouched with a "kept existing"
# note; there is no --force. Re-running is always safe.
#
# Conventions: set -euo pipefail; TTY-gated ANSI (NO_COLOR / TERM=dumb
# respected); no deps beyond bash/coreutils/python3; works from any cwd.
set -euo pipefail

# --- ANSI gating ---------------------------------------------------------------
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-}" != "dumb" ]; then
  C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_DIM=$'\033[2m'; C_END=$'\033[0m'
else
  C_OK=""; C_WARN=""; C_DIM=""; C_END=""
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  echo "usage: sps-init.sh [target-dir]   (default: current directory)" >&2
  echo "       no --force: existing files are never overwritten" >&2
  exit 2
}
case "${1:-}" in
  -h|--help) usage ;;
  "") ;;
  -*) usage ;;
esac

TARGET_ARG="${1:-.}"
mkdir -p "$TARGET_ARG"
TARGET="$(cd "$TARGET_ARG" && pwd)"

# --- refuse to scaffold inside the BuildPilot repo -----------------------------
# Walk up from the target looking for framework/sps2 (the framework's marker).
in_buildpilot() {
  local d="$1"
  while :; do
    [ -d "$d/framework/sps2" ] && return 0
    [ "$d" = "/" ] && return 1
    d="$(dirname "$d")"
  done
}
if in_buildpilot "$TARGET"; then
  echo "sps-init: ${TARGET} is inside the BuildPilot repo (framework/sps2 found)" >&2
  echo "  this scaffold is for CLIENT projects — run it in a fresh project" >&2
  echo "  directory, not inside the framework checkout." >&2
  exit 1
fi

# --- helpers -------------------------------------------------------------------
rel() { printf '%s' "${1#"$TARGET"/}"; }

# write_new <path>: copy stdin into <path> unless it already exists.
write_new() {
  local path="$1"
  if [ -e "$path" ]; then
    echo "  ${C_DIM}kept existing:${C_END} $(rel "$path")"
  else
    cat > "$path"
    echo "  ${C_OK}created:${C_END} $(rel "$path")"
  fi
}

# ensure_dir <path>
ensure_dir() {
  local path="$1"
  if [ -d "$path" ]; then
    echo "  ${C_DIM}kept existing:${C_END} $(rel "$path")/"
  else
    mkdir -p "$path"
    echo "  ${C_OK}created:${C_END} $(rel "$path")/"
  fi
}

echo "sps-init: scaffolding SPS workflow in ${TARGET}"
echo

# --- scaffold ------------------------------------------------------------------
ensure_dir "$TARGET/.sps"
ensure_dir "$TARGET/.sps/backups"

# Kickoff questionnaire — answers stay EMPTY; the human fills them in.
# Structure matches framework/sps2/tools/check_kickoff.py (T-28), which
# requires headed sections for: project goal, deploy target, stack,
# content, CMS. The <fill in: ...> slots are recognized placeholders, so
# the checker correctly reports KICKOFF_ANSWER_EMPTY until real answers
# are recorded.
write_new "$TARGET/.sps/kickoff.md" <<'SPS_KICKOFF_TEMPLATE'
# Kickoff — Project Questionnaire

Answer each section below in your own words; plain words are fine.
The agent fills in nothing here — this file records YOUR answers.
Missing answers are asked once more, batched; anything still unknown is
recorded in `.sps/profile.md` as `Assumed` and flagged at gate G1.

## Project goal
<fill in: what the site/app must do, in the client's words>

## Deploy target
<fill in: Vercel / shared hosting / cPanel / VPS / Cloudflare / other — and who owns the account/domain>

## Stack constraints
<fill in: required or banned technologies>

## Content
<fill in: who provides copy/images, language(s), RTL needs>

## CMS
<fill in: enabled? if yes, sps-cms ships with every section>

## Brand
<fill in: logo, colors, references to like / avoid>

## Contacts & integrations
<fill in: forms, WhatsApp, analytics, tracking IDs>

## Auth
<fill in: login/user accounts needed? if yes: what data, what roles>

## Mobile policy
<fill in: mobile-first / desktop-only / responsive parity; low-end device expectations>

## Multi-agent roles
<fill in: if other agents/people touch the repo, who does what; single-agent otherwise>

## Timeline & budget constraints
<fill in: if any>

## After-sale acknowledgment
<fill in: confirm the standard policy applies — 1 month all-type support + 1 month free SEO>
SPS_KICKOFF_TEMPLATE

# Agent options starter — everything commented out; uncomment to enable.
write_new "$TARGET/.sps/agent.md" <<'SPS_AGENT_TEMPLATE'
# .sps/agent.md — project agent options
# Lines starting with # are ignored. Uncomment a line to enable it;
# unknown lines are ignored by the tooling.

# Plain-language mode: every user-facing gate message (kickoff, G1, G2,
# approval packet, handoff) is rewritten in plain words for non-technical
# clients. See skill/sps/PLAIN-LANGUAGE.md.
# language: plain
SPS_AGENT_TEMPLATE

# Task queue skeleton.
write_new "$TARGET/.sps/task-queue.md" <<'SPS_TASKQUEUE_TEMPLATE'
# Task Queue

## doing

## queued
SPS_TASKQUEUE_TEMPLATE

# CHEAT-SHEET link at project root: symlink when the skill is installed
# here, otherwise a pointer note naming where it lives after install.
CHEAT_TARGET="skill/sps/CHEAT-SHEET.md"
if [ -e "$TARGET/CHEAT-SHEET.md" ] || [ -L "$TARGET/CHEAT-SHEET.md" ]; then
  echo "  ${C_DIM}kept existing:${C_END} CHEAT-SHEET.md"
elif [ -f "$TARGET/$CHEAT_TARGET" ]; then
  ln -s "$CHEAT_TARGET" "$TARGET/CHEAT-SHEET.md"
  echo "  ${C_OK}created:${C_END} CHEAT-SHEET.md -> $CHEAT_TARGET"
else
  write_new "$TARGET/CHEAT-SHEET.md" <<'SPS_CHEAT_POINTER_TEMPLATE'
# BuildPilot Cheat Sheet — pointer

The BuildPilot cheat sheet ships with the skill, not with this project.
After the SPS skill is installed here it lives at:

    skill/sps/CHEAT-SHEET.md

Open that file for the one-page "say this, get that" command list
(kickoff answers, G1/G2 gates, /sps status, /sps doctor, /sps audit).
SPS_CHEAT_POINTER_TEMPLATE
fi

echo
# --- next steps ----------------------------------------------------------------
CHECKER=""
for cand in \
  "$SCRIPT_DIR/../framework/sps2/tools/check_kickoff.py" \
  "$SCRIPT_DIR/../../framework/sps2/tools/check_kickoff.py"; do
  if [ -f "$cand" ]; then
    CHECKER="$(cd "$(dirname "$cand")" && pwd)/$(basename "$cand")"
    break
  fi
done

echo "${C_WARN}Next steps:${C_END}"
echo "  1. Fill in the kickoff answers in $(rel "$TARGET")/.sps/kickoff.md"
echo "     (replace each <fill in: ...> slot with the client's actual answer)."
if [ -n "$CHECKER" ]; then
  echo "  2. Verify the kickoff is recorded:"
  echo "       python3 $CHECKER $TARGET"
else
  echo "  2. Verify the kickoff is recorded:"
  echo "       python3 <BuildPilot>/framework/sps2/tools/check_kickoff.py $TARGET"
  echo "     (checker not found next to this script — install the full BuildPilot tree)"
fi
echo "  3. Load the /sps workflow (say \"load sps\") and answer the kickoff"
echo "     questions with the agent — nothing is built before gate G1."
echo
echo "${C_OK}sps-init: done${C_END} ${C_DIM}(idempotent — re-running never overwrites)${C_END}"
