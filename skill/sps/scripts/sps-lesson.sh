#!/usr/bin/env bash
# sps-lesson.sh — cross-project lesson capture & promotion (LESSONS.md)
# Usage:
#   bash scripts/sps-lesson.sh capture "short title"   # in a client project
#   bash scripts/sps-lesson.sh send                    # PR lessons to BuildPilot
#   bash scripts/sps-lesson.sh review                  # in BuildPilot: list inbox
set -uo pipefail

BG_REPO="${BG_REPO:-SHAHID8142/BuildPilot}"
BG_BRANCH_BASE="${BG_BRANCH_BASE:-main}"

cmd="${1:-}"; shift || true

die() { echo "ERROR: $*" >&2; exit 1; }

slugify() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-*$//;s/^-\+//;s/-\+$//' | cut -c1-40; }

 today() { date +%Y%m%d; }

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
    [[ -d .sps/lessons/pending ]] || die "no pending lessons"
    shopt -s nullglob
    lessons=(.sps/lessons/pending/LESSON-*.md)
    shopt -u nullglob
    [[ ${#lessons[@]} -gt 0 ]] || die "no pending lessons to send"
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
    git -C "$work" add lessons/inbox
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
    echo "Pending lessons (${#lessons[@]}) — review each per LESSONS.md:"
    for f in "${lessons[@]}"; do
      echo "  - $f"
      grep -m1 -E "^(category|severity):" "$f" | sed 's/^/      /'
    done
    echo "For each: read it, verify Applies-to exists, propose the doc edit, ask the user."
    ;;

  *)
    die "usage: sps-lesson.sh capture \"title\" | send | review"
    ;;
esac
have_gh() { command -v gh >/dev/null 2>&1; }
