#!/usr/bin/env bash
# sps-lesson.sh — cross-project lesson capture & promotion (LESSONS.md)
# Usage:
#   bash scripts/sps-lesson.sh capture "short title"   # in a client project
#   bash scripts/sps-lesson.sh send [--yes]            # PR lessons to BuildPilot
#                                                      # (--yes skips the typed
#                                                      #  confirmation; without
#                                                      #  it, send shows exactly
#                                                      #  what will be published
#                                                      #  and asks first)
#   bash scripts/sps-lesson.sh review                  # in BuildPilot: review inbox
set -uo pipefail

BG_REPO="${BG_REPO:-SHAHID8142/BuildPilot}"
BG_BRANCH_BASE="${BG_BRANCH_BASE:-main}"

cmd="${1:-}"; shift || true

die() { echo "ERROR: $*" >&2; exit 1; }

have_gh() { command -v gh >/dev/null 2>&1; }

slugify() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-*$//;s/^-\+//;s/-\+$//' | cut -c1-40; }

today() { date +%Y%m%d; }

# section_body FILE HEADING — print the body of "## HEADING" up to the next "## "
section_body() {
  awk -v h="$2" '
    /^## / { on = ($0 == "## " h); next }
    on { print }
  ' "$1"
}

# section_snippet FILE HEADING MAXLINES — first non-empty lines, joined to one line
section_snippet() {
  section_body "$1" "$2" | grep -v '^[[:space:]]*$' | head -n "$3" | tr '\n' ' ' \
    | sed 's/[[:space:]]\{1,\}/ /g; s/^ //; s/ $//'
}

# next_action APPLIES_TEXT — suggested next action based on the Applies-to line
next_action() {
  target=""
  for word in $1; do
    case "$word" in
      *.md|*.sh|*.py) target="$word"; break ;;
    esac
  done
  if [[ -z "$target" ]]; then
    echo "Applies-to names no target doc — finish the thought (LESSONS.md: a lesson without a target is not ready)"
  elif [[ -f "skill/sps/$target" || -f "$target" ]]; then
    echo "target ${target} exists — propose the exact doc edit and ask the user: approve / reject / edit"
  else
    echo "Applies-to target ${target} NOT found in skill/sps/ or repo root — verify the name or pick the right doc"
  fi
}

case "$cmd" in
  capture)
    title="${1:-}"; [[ -n "$title" ]] || die "usage: sps-lesson.sh capture \"short title\""
    [[ -d .sps ]] || die "no .sps/ here — run inside a project with /sps initialized"
    id="LESSON-$(today)-$(slugify "$title")"
    dest=".sps/lessons/pending/${id}.md"
    [[ -e "$dest" ]] && die "lesson exists: $dest"
    mkdir -p .sps/lessons/pending
    cat > "$dest" <<EOF
---
lesson_id: ${id}
date: $(date +%F)
project: generic
host: other
category: other
severity: minor
status: pending
---
## Problem

(what went wrong — facts and evidence)

## Rule

(the rule that prevents it — imperative, one sentence where possible)

## Applies-to

(which BuildPilot doc/section: DESIGN-GATE.md, SECTION-DOD.md, …)

## Evidence

(how it was discovered; repro or before/after)
EOF
    echo "Created $dest"
    echo "Fill the template with the agent (one field at a time), then:"
    echo "  bash scripts/sps-lesson.sh send"
    ;;

  send)
    assume_yes=""
    for a in "$@"; do
      case "$a" in
        --yes) assume_yes="yes" ;;
        *) die "unknown option for send: $a (usage: sps-lesson.sh send [--yes])" ;;
      esac
    done
    [[ -d .sps/lessons/pending ]] || die "no pending lessons"
    shopt -s nullglob
    lessons=(.sps/lessons/pending/LESSON-*.md)
    shopt -u nullglob
    [[ ${#lessons[@]} -gt 0 ]] || die "no pending lessons to send"
    if [[ "$assume_yes" != "yes" ]]; then
      echo "About to publish ${#lessons[@]} lesson(s) to the PUBLIC repo ${BG_REPO}"
      echo "(branch lesson/$(today)-batch, then a pull request):"
      echo
      for f in "${lessons[@]}"; do
        echo "  ── $f ──"
        # Show the full content: this text is about to leave the machine,
        # so the user must be able to review exactly what is published.
        sed 's/^/  │ /' "$f"
        echo
      done
      echo
      read -r -p "Send these ${#lessons[@]} lesson(s) to ${BG_REPO}? (yes/no): " confirm
      if [[ "$confirm" != "yes" ]]; then
        echo "Aborted — nothing was sent, pending lessons left in .sps/lessons/pending/."
        echo "Send later:  bash scripts/sps-lesson.sh send"
        echo "Delete one:  rm .sps/lessons/pending/<file>"
        exit 1
      fi
    fi
    work="$(mktemp -d)/BuildPilot"
    if git clone --quiet "https://github.com/${BG_REPO}.git" "$work" 2>/dev/null; then
      :
    else
      die "could not clone ${BG_REPO} — check network/credentials"
    fi
    branch="lesson/$(today)-batch"
    git -C "$work" checkout -qb "$branch"
    mkdir -p "$work/lessons/inbox"
    copied=0
    for f in "${lessons[@]}"; do
      cp "$f" "$work/lessons/inbox/"
      copied=$((copied+1))
    done
    # Secret-scan the exact bytes about to be pushed (audit m-3): a lesson
    # containing a client API key must never reach the public repo. Stage the
    # copies first, then run secret-scan.sh inside the clone (it scans tracked
    # files of the repo it finds itself in) — so what is scanned == what is sent.
    git -C "$work" add lessons/inbox
    scan="$(dirname "$0")/secret-scan.sh"
    [[ -f "$scan" ]] || scan="$(pwd)/scripts/secret-scan.sh"
    if [[ -f "$scan" ]]; then
      echo "Running secret scan over the ${copied} staged lesson(s)…"
      if ! (cd "$work" && bash "$scan"); then
        echo "ABORTED — secret-scan flagged the lesson content." >&2
        echo "Redact the lesson files in .sps/lessons/pending/ and try again." >&2
        exit 1
      fi
    else
      echo "warning: secret-scan.sh not found — skipping the pre-push secret scan" >&2
    fi
    git -C "$work" -c user.name="SPS Lesson Bot" -c user.email="lessons@users.noreply.github.com" \
      commit -qm "Lessons from client project ($(basename "$PWD")): ${copied} item(s)"
    if git -C "$work" push -q "https://github.com/${BG_REPO}.git" "$branch" 2>/dev/null; then
      if have_gh; then
        gh pr create -R "$BG_REPO" --base "$BG_BRANCH_BASE" --head "$branch" \
          --title "Lessons: ${copied} captured in $(basename "$PWD")" \
          --body "Captured via sps-lesson.sh. Review each lesson per LESSONS.md (user approves every one)." >/dev/null 2>&1 \
          && echo "PR opened against ${BG_REPO}" \
          || echo "Pushed branch $branch — open the PR at: https://github.com/${BG_REPO}/compare/${BG_BRANCH_BASE}...$branch"
      else
        echo "Pushed branch $branch — open the PR at: https://github.com/${BG_REPO}/compare/${BG_BRANCH_BASE}...$branch"
      fi
    else
      echo "Could not push (no write access?). Branch committed locally in: $work"
      echo "Push manually or copy lessons/inbox/* into your BuildPilot clone."
    fi
    ;;

  review)
    shopt -s nullglob
    lessons=(lessons/inbox/LESSON-*.md)
    shopt -u nullglob
    if [[ ${#lessons[@]} -eq 0 ]]; then echo "Inbox empty."; exit 0; fi
    echo "Pending lessons (${#lessons[@]}) — review each per LESSONS.md (user approves every one):"
    echo
    n=0
    for f in "${lessons[@]}"; do
      n=$((n+1))
      category="$(sed -n 's/^category:[[:space:]]*//p' "$f" | head -n 1)"
      severity="$(sed -n 's/^severity:[[:space:]]*//p' "$f" | head -n 1)"
      problem="$(section_snippet "$f" "Problem" 2)"
      rule="$(section_snippet "$f" "Rule" 2)"
      applies="$(section_snippet "$f" "Applies-to" 2)"
      echo "[$n] $f"
      echo "    category: ${category:-?}  severity: ${severity:-?}"
      echo "    Problem:    ${problem:-<empty>}"
      echo "    Rule:       ${rule:-<empty>}"
      echo "    Applies-to: ${applies:-<empty>}"
      echo "    Next: $(next_action "${applies:-}")"
      echo
    done
    echo "Per lesson: read the full file, verify the Applies-to target exists, propose the exact doc edit, ask the user (approve / reject / edit)."
    echo "Approve: merge the rule into the named doc (+ check_laws.py marker if machine-checkable), move to lessons/adopted/ (status: adopted + date), add one line to the session report."
    echo "Reject: move to lessons/rejected/ with a one-line reason — never delete."
    ;;

  *)
    die "usage: sps-lesson.sh capture \"title\" | send | review"
    ;;
esac
