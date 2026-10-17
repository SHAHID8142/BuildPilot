# Lesson Capture & Promotion (cross-project self-improvement)

BuildPilot improves from real projects. When a mistake, gap, or better
pattern is found while building a CLIENT project with BuildPilot, it is
captured as a **lesson** and sent back to the BuildPilot repo as a PR.
Approved lessons become permanent skill rules.

## The flow (3 stages)

```
[client project]            [BuildPilot repo]              [skill docs]
1. capture  → .sps/lessons/pending/LESSON-*.md
2. send     → PR to BuildPilot lessons/inbox/
3. review   → user approves each lesson → rule merged into skill docs
```

## 1. Capture (in any client project)

```bash
bash scripts/sps-lesson.sh capture "short title"
```

Creates `.sps/lessons/pending/LESSON-<date>-<slug>.md` from the strict
template. The agent fills it WITH the user (one field at a time if the
user prefers — USER-GUIDANCE.md applies). The agent also auto-captures:
when it records a mistake in `.sps/mistakes.md` that is project-agnostic
(not a stack quirk of this one client), it proposes a lesson capture.

## 2. Strict template (every field required)

```markdown
---
lesson_id: LESSON-YYYYMMDD-<slug>
date: YYYY-MM-DD
project: <client project name or "generic">
host: <claude-code | cursor | codex | antigravity | windsurf | opencode | other>
category: <design | testing | deploy | security | legal | cms | seo | process | other>
severity: <blocker | major | minor>
status: pending
---
## Problem
What went wrong — facts and evidence, no narrative.

## Rule
The rule that prevents it. Imperative voice, one sentence where possible
("Never gate critical content behind hover; use @media (hover: hover)").

## Applies-to
The BuildPilot doc/section this belongs in — e.g. DESIGN-GATE.md,
SECTION-DOD.md, VERIFICATION-RECIPES.md, LEGAL-COMPLIANCE.md, install.sh.

## Evidence
How it was discovered; repro or before/after.
```

A lesson that cannot name its `Applies-to` target is not ready to send —
finish the thought first.

## 3. Send (PR to BuildPilot)

```bash
bash scripts/sps-lesson.sh send
```

- Clones BuildPilot to a temp dir (or reuses a cached clone), copies
  pending lessons onto a `lesson/<id>` branch, pushes, and opens a PR
  via `gh` when available; otherwise prints the compare URL to open.
- **Never sends automatically** — `send` is always an explicit user action.
- Secrets rule: a lesson containing client names, keys, or URLs is edited
  to `project: generic` before sending. The template defaults to generic.

## 4. Review (in the BuildPilot repo — user approves each one)

```bash
bash scripts/sps-lesson.sh review   # lists lessons/inbox/ and next actions
```

Per lesson, the agent: reads it, checks the `Applies-to` target exists,
proposes the exact doc edit, and asks the user approve / reject / edit.
On approval the agent:

1. Merges the rule into the named doc (right section, matching style).
2. Extends `check_laws.py` with a marker when the rule is machine-checkable.
3. Moves the file to `lessons/adopted/` and sets `status: adopted` with
   the date and the commit that shipped it.
4. Adds one line to the session report.

Rejected lessons move to `lessons/rejected/` with a one-line reason —
never deleted (a rejected lesson that reappears is a signal).

## Hard rules

- **No auto-send**: lessons leave a client project only on explicit `send`.
- **No auto-merge in BuildPilot**: every lesson needs the user's approval.
- **One lesson, one rule**: a lesson teaching three things is split into
  three lessons.
- **Client privacy**: lessons are sanitized before leaving the project.
- Promotion within a single project is still MISTAKE-PROMOTION.md —
  this file governs only the cross-project channel.
