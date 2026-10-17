# Context Budget Law (.sps must never burn the session)

**Law:** `.sps/` files are for the agent to resume fast — not a ledger it
must re-read in full every session. Every `.sps/` file has a size budget;
oversized files are archived, never allowed to grow unbounded.

## Size budgets (enforced by `scripts/sps-doctor.sh`)

| File | Budget | On overflow |
|---|---|---|
| `.sps/handoff.md` | 150 lines / 8 KB | move old Conversation-log entries to `.sps/archive/log-YYYY-MM.md` |
| `.sps/agent.md` | 60 lines | same → `.sps/archive/` |
| `.sps/profile.md` | 120 lines | same |
| `.sps/plan.md` | 300 lines | superseded plan → `.sps/archive/plan-<date>.md`, keep only the active plan |
| `.sps/task-queue.md` | 80 lines | done items older than 14 days → `.sps/archive/tasks-YYYY-MM.md` |
| `.sps/section-todos/` | 1 file per ACTIVE section | completed section todos deleted at Section DoD |
| `.sps/audit-report.md` | 200 lines | full history lives in `reports/`, not here |

## The rules

1. **Snapshot, not ledger.** `handoff.md` is a CURRENT-STATE snapshot:
   sections like *Current phase*, *Verification status*, *Waiting for
   approval* are **overwritten** each session, never appended to. Only the
   Conversation log is append-style — and it rolls (rule 2).
2. **Rolling log.** The Conversation log keeps at most the **last 5
   entries**. When a 6th is written, the oldest moves to
   `.sps/archive/log-YYYY-MM.md` (created on demand). Full history stays
   in git — nothing is lost, just out of the hot path.
3. **Read order is tiered.** An agent resuming a project reads:
   - **Always:** `handoff.md` (≤150 lines) — this alone must be enough to
     resume correctly.
   - **On demand:** `plan.md`, `task-queue.md`, section todos — only the
     part the current task touches (grep for the section id first).
   - **Only when explicitly needed:** `archive/`, `architecture/`,
     `audit-report.md` — never as part of normal session start.
4. **Archive, never delete (except section todos).** Anything moved out of
   the hot files lands in `.sps/archive/` with a dated filename. Git
   history is the second copy.
5. **Doctor enforces the budgets.** `scripts/sps-doctor.sh` warns at 90%
   and fails at 150% of budget, printing which file to archive and where.
   An agent that sees the warning archives in the same session.
6. **Token-saving defaults on every task.** (Extends CONTEXT-EFFICIENCY.md)
   - Grep with line offsets before reading; cite `file:line` instead of
     pasting content.
   - One consolidated question block to the user per checkpoint — not a
     drip of single questions.
   - Tool output is filtered (`| tail`, `| grep`) before it enters the
     conversation; never dump full logs.
   - `reports/` files are written for humans; agents cite the path, they
     do not re-read the whole report in later sessions.

## Why this is safe

The current state (what am I building, what's approved, what's verified)
lives in the hot files and is always ≤ budget. History is in git +
archive. A fresh session therefore reads ~400 lines instead of an
unbounded ledger — resuming fast IS the memory's job.
