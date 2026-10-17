# Finite SPS2 Completion Backlog

**Status vocabulary:** `TODO`, `IN_PROGRESS`, `NEEDS_REVIEW`, `BLOCKED_USER`, `BLOCKED_EXTERNAL`, `DONE`, `DEFERRED`, `CANCELLED`. `DONE` requires evidence for the exact item and current verification date. An unavailable reviewer/runtime is not a pass.

| ID | Priority | Work item | Owner / cross-check | Status at dossier creation | Exit condition |
|---|---:|---|---|---|---|
| B0 | P0 | Rebaseline branch, HEAD, staged/unstaged/untracked inventory, stashes, and protected hashes. Compare before/after each batch; explain new entries. | Codexx / Claude | `DONE` for this dossier checkpoint only; repeat before next code batch | Fresh capture recorded in file 02 and coordination log: 83 porcelain entries, 45 modified tracked, 38 untracked entries / 222 expanded files, 0 staged, 0 stashes; six protected-file hashes spot-checked. |
| B1 | P0 | Reconcile older completion backlog and decision packet with current C4/C5 outcomes and delegated decisions. Correct task status only with source evidence; do not rewrite governance history. | Codexx / Claude | `DONE` for this dossier only; older source reports/backlog left untouched | C4/C5 state and Packages 2/3 authorization/status discrepancy recorded in files 02 and 05, with dates and evidence links. The older status rows remain historical and were not edited. |
| B2 | P1 | C4 repair cross-review: request Claude review when gateway works; verify R-C4 repairs and R-2 guard tests remain current. | Claude / Codexx | `NEEDS_REVIEW` (Codex reviewer PASS; Claude unavailable) | Claude verdict or documented external blocker plus accepted alternate review policy; tests and no preservation delta. |
| B3 | P1 | C5 updater/bootstrap cross-review closure: Claude review when its model gateway is usable; verify all five findings and report. | Claude / Codexx | `NEEDS_REVIEW` (Codexx CLI PASS) | Claude verdict or documented external blocker and explicit alternative review; run focused tests. |
| B4 | P1 | Reassess P10 dynamic import against current scanner, runtime gate, tests, and import contracts. Implement/remove only if behavior is preserved and tests demonstrate it without changing gate/manifest/decision. | Codexx implement / Claude review | `TODO`; prior audit says no policy-neutral path | Safe tested refactor and cross-review, or precise `BLOCKED_EXTERNAL` report. No exception or gate weakening. |
| B5 | P1 | Narrow attribution predicate fix: reject literal self-approval as evidence, preserve real names such as “Jane Self,” add adversarial regression tests. Do not rewrite historical records or claim identity verification. | One agent implements / other reviews | `TODO` (authorized by delegated operating decision) | Focused and relevant suite pass; code and false-positive surface independently reviewed. |
| B6 | P1 | Package 2 installer SSH host-key verification (`install.sh` / `install.ps1` and mirrors); define first-use and changed-key behavior; inspect clone/global auto-yes safety. | One agent implements / other reviews | `TODO` (authorized as code fix; baseline stays unchanged) | Focused static/runtime tests; validator failures honestly recorded; no real network install. |
| B7 | P1 | Package 3 uninstaller path confinement in Bash/PowerShell; validate manifest paths, allowed roots, symlink/reparse points, malformed input, CWD-relative candidates, and add-vs-replace target semantics. | One agent implements / other reviews | `TODO` (authorized as code fix; baseline stays unchanged) | Temp-home adversarial tests and mirror review; no real uninstall. |
| B8 | P2 | Revalidate C10/P7 validator behavior and propose narrowly scoped code fixes only if project authorization covers them; do not alter baselines or historical decision records. | Codexx / Claude | `TODO` | Evidence-backed defect proposals/fixes; keep false green visible. |
| B9 | P2 | Revisit R-1 scanner residual (tuple unpack, walrus, container storage, dynamic getattr) only if a real in-tree case or bounded high-value hardening justifies false-positive risk. | Codexx / Claude | `DEFERRED` absent new evidence | Remains deferred with basis, or new isolated tests plus independent review. Never expand scanner broadly without probes. |
| B10 | P0 | Reconcile protected decision/provenance queue: DEC-7301/2/3, Round 26 attribution and sidecar, `.claude/settings.json`, P5 authorization, DEC-0001/DEC-0032 and unexplained push history. | Codexx prepares evidence; user remains approver for records | `BLOCKED_USER` for edits/ratification | Preserve records; present decisions, options, consequences, sources. User-authored decisions are required to change them. |
| B11 | P0 | CI/test discovery proposal for seven untracked test modules. Determine exact current module inventory and clean-checkout impact. | Codexx / Claude | `BLOCKED_USER` for CI/expected-module edits | Proposal and tests only until explicit authorization for CI/manifest change. |
| B12 | P0 | Obtain authentic P10 prerequisites: publication/approval, slice history, authentic gate evidence, observed exposure/bind state, deployment-audit input, backend operations manifest, build output, actual test execution, rollback rehearsal, and missing gate controls. | Human systems/approvers + agents prepare evidence | `BLOCKED_USER` / external evidence | Each prerequisite has a real source and required approval; no agent fabricates evidence or publishes. |
| B13 | P0 | Final verification after implementation/disposition: full offline test matrix, focused tests, all five validators, P10 gate, shell syntax, PowerShell/ShellCheck when available, mirrors, whitespace, protected hashes, and entire worktree inventory. | Codexx / Claude independently | `TODO` | Exact commands, exit codes, counts, skips, environment; failures/blocked results remain visible. |
| B14 | P0 | Final operator handoff: implemented/reviewed work, deferred items, blockers, safe commands, installation/update/uninstall usage, support and rollback procedure, current readiness verdict. | Codexx drafts / Claude reviews | `TODO` | Complete reproducible handoff. Say READY only if all actual criteria and approvals are true. |

## Execution order and dependency rules

1. Rebaseline and reconcile C4/C5 checkpoint records (B0–B3). Do not alter the old backlog or claim old counts are current.
2. Assess the P10 import refactor (B4); stop with a documented block if safe behavior preservation is impossible.
3. Implement and independently review attribution (B5), then Package 2 (B6), then Package 3 (B7), one package at a time. Delegated authorization permits code-owned fixes while validators stay red; it does not authorize baseline/governance/CI edits.
4. Reassess C10/P7 and scanner residual only with evidence (B8–B9).
5. Keep provenance/approval/CI and P10 evidence queues intact (B10–B12). No silence-as-approval.
6. Run B13 after all authorized code work or after all other work is dispositioned. Finish B14 with a truthful readiness status.

## Stop conditions

- The exact needed change touches a protected decision, baseline, manifest, CI, user-owned settings, approval record, publication, deployment, or remote state outside the recorded authorization.
- A necessary behavior change cannot be made without weakening a gate or depending on an unapproved decision.
- Tests, preservation, or reviewer evidence contradicts the expected result.
- Agent discovers concurrent edits or unexplained worktree changes: stop writes, preserve, rebaseline, report owner/paths, then proceed only when safe.
- Reviewer is unavailable: record `NEEDS_REVIEW` or `BLOCKED_EXTERNAL`; do not call the review passed.
- P10 has any FAIL/BLOCKED or missing authentic evidence: maintain NOT READY.
