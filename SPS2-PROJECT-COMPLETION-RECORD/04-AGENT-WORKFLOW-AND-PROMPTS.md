# Agent Workflow, Communication Protocol, and Prompts

## Roles

- **Implementer:** either Codexx/Codex CLI or Claude Code, one at a time per package. Read the current dossier, source reports, approved scope, and live tree before writing.
- **Independent reviewer:** the other agent, read-only. Review exact diff, tests, risks, protected-file hashes, and whether the implementer’s claims match evidence. Do not patch silently.
- **Coordinator:** Codex primary in this conversation, responsible for preserving the task ledger, reporting blockers, preventing overlap, and keeping release readiness honest.
- **Watcher subagents:** dedicated to watching only `reports/SPS2-COMPLETION-COORDINATION.md`. They do not inspect source, implement, review, or make decisions. A watcher is not currently claimed as running unless a real process/automation is recorded.

## Shared communication file

Canonical append-only communication log: `reports/SPS2-COMPLETION-COORDINATION.md`.

Each post must include:

1. Dhaka timestamp, task ID, agent identity, and `IMPLEMENTATION`, `REVIEW`, `BLOCKER`, `HANDOFF`, or `CHECKPOINT` type.
2. Starting and ending branch/HEAD/worktree counts; explain every changed path and whether it predates this task.
3. Exact file scope, behavior change, tests/commands, exit codes/counts/skips, shell/runtime availability, hashes where relevant.
4. Findings, risks, false-positive/compatibility impact, what could not be verified, and whether the task is `DONE`, `NEEDS_REVIEW`, blocked, or deferred.
5. Handoff to the named next agent and explicit questions or evidence requested.
6. Cross-review response that states each finding as confirmed/contradicted/partially confirmed and links to evidence.

Use append-only entries. Do not overwrite another agent’s notes, resolve user decisions by editing records, or use the communication file as a substitute for a detailed report.

## One-package protocol

1. Re-read this dossier and the latest coordination entries. Confirm the other agent is not editing overlapping files.
2. Capture live state and protected hashes before any edits.
3. Announce exact package, owner, reviewer, files, exclusions, test plan, acceptance criteria, and stop boundaries.
4. Implement one bounded package. Preserve all unrelated tracked/untracked work. No destructive cleanup.
5. Run focused tests and relevant suites requested by the project; record test failures without hiding them. Never perform real installation/uninstallation or remote operations during safety testing.
6. Write an implementation report and append a handoff.
7. Reviewer works read-only, independently checks claims, and records PASS/NEEDS REVISION with line/test evidence. If defects are found, return them to the implementer for a bounded repair; reviewer rechecks only that repair.
8. Recheck branch/HEAD, staging, stash, porcelain inventory, and protected hashes.
9. Only then close the checkpoint and begin the next package.

## Bounded watcher instructions

Use two small watcher subagents only if supported by the current agent CLI. One may be assigned to watch for Codexx updates and one for Claude updates, but each watcher reads only the shared coordination Markdown file. Watchers must not poll continuously or perform unrelated work.

Bounded watcher prompt:

> Monitor only `reports/SPS2-COMPLETION-COORDINATION.md` for task ID `[ID]`. Check once on start and then at a bounded interval no more frequent than 5 minutes, for at most 60 minutes or until the requested implementation handoff/review verdict/blocker is recorded. Do not read source code, edit files, contact agents, start tasks, or duplicate work. Stay quiet if nothing meaningful changes. Notify the coordinator only on a handoff, verdict, blocker, preservation concern, or window end. Stop immediately after the checkpoint is resolved or the time limit expires. Record that you were a watcher only; do not claim implementation or verification.

If an automation/watch feature cannot be launched, say so. Do not simulate continuous monitoring. The previous C4 heartbeat was bounded to one hour; it is not evidence that a watcher remains active now.

## Prompt for Codexx CLI — next implementation package

```text
You are the single implementer for the next eligible SPS2 task. Repository: /Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main.

Read first:
- SPS2-PROJECT-COMPLETION-RECORD/README.md and files 01–05
- reports/SPS2-COMPLETION-COORDINATION.md (latest entries)
- reports/SPS2-DELEGATED-DECISIONS-20261017.md
- the exact current audit/report for the task you select

Start with a fresh read-only baseline of branch, HEAD, staged/unstaged/untracked paths, stashes, and protected hashes. Do not assume old counts remain current. Select only the first eligible item in file 03. Do not overlap another agent’s active task. State the exact package/files and acceptance tests in the coordination log before editing.

Scope order: (1) reconcile C4/C5 review state and live baseline; (2) assess the P10 dynamic-import refactor and implement only if behavior can be preserved and tests prove it without editing P10 gates/manifests/decisions; (3) narrow attribution fix; (4) Package 2 installer host-key handling; (5) Package 3 uninstaller confinement. One package per checkpoint. Keep scanner R-1 deferred absent a live reproducer or bounded evidence. Follow the specific delegated scope and stop if the exact change is protected or the safe behavior cannot be preserved.

Preserve all existing work. No reset, clean, stash, revert, delete, move, or overwrite. No staging, commit, push, merge, deploy, publish, or release. Do not change CI, validator baselines/exception manifests, DEC-7301/7302/7303, Round 26 records/sidecar, P10 evidence/decision/gate semantics, user-owned .claude/settings.json, or approval history. Do not run a real install or uninstall. Keep P10/release NOT READY unless actual gates and authentic prerequisites pass.

Run only relevant non-destructive tests and record exact evidence. Produce a timestamped report and append a handoff with before/after state. Request an independent read-only review from Claude. If Claude’s gateway remains unavailable, record the failure and do not label a different reviewer as Claude; use a separately launched Codexx review only if the coordinator explicitly asks, and keep the Claude review limitation visible. Stop at the checkpoint; do not continue into the next package.
```

## Prompt for Claude Code — independent review

```text
You are the independent read-only reviewer for SPS2 task [TASK ID]. Repository: /Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main.

Read the project dossier at SPS2-PROJECT-COMPLETION-RECORD/ and the latest implementation handoff/report in reports/SPS2-COMPLETION-COORDINATION.md. Review the exact patch, cited tests, scope, user-owned worktree preservation, protected hashes, and every acceptance criterion. Reproduce safe focused checks when possible; do not modify files.

Return PASS or NEEDS REVISION. For each finding, identify the file/line or command/output and severity. State which evidence you independently reproduced, which is static-only, and which is unavailable (including pwsh or gateway model failures). Check for false positives, compatibility changes, incomplete mirror updates, and boundary violations. Do not edit source or reports except for your own new timestamped review report and append-only coordination handoff if the implementer explicitly requested that documentation. Do not stage, commit, push, deploy, publish, merge, or release. Do not alter CI, baselines, manifests, governance decisions, disputed approval records, or P10 gates. Do not claim User approval. Stop after the review; do not start another task.
```

## Current CLI truth

- `codexx` exists as an interactive zsh alias invoking the installed Codex CLI with profile `river`. It was used for the C5 read-only review from an agent-managed shell.
- The C5 Codexx reviewer returned PASS. Its test attempt under read-only sandbox could not create temporary directories; the primary run passed 47 with one skip.
- `claude` is installed, but the configured local model gateway rejected the attempted model IDs (including the configured River GLM model and the tested Sonnet aliases). No resumed C4/C5 Claude review is complete.
- `pwsh` and ShellCheck were not available in the resumed environment.
- Do not tell the user a terminal is visible in VS Code unless it is visibly open and verified. The Codexx CLI call from this session ran in the agent-managed shell, not a visible VS Code terminal.
