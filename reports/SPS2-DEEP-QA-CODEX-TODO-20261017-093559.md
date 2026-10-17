# SPS2 Deep QA Codex TODO Ledger

**Opened:** 2026-10-17 09:35:59 +06  
**Mission:** Read-only QA audit after Codex technical completion and Claude second-pass integration.  
**Branch:** `build/roadmap-p3-completion`  
**HEAD at open:** `c49f3852e1c31d0136269c80fe58201b059af3ec`  
**Method note:** No separate read-only subagent execution mechanism is exposed to this session. The required work packages are emulated as independently scoped investigation batches. No code-editing agent is started.

## Baseline Snapshot at Open

| Item | Value |
|---|---|
| Staged files | 0 |
| Modified tracked files | 39 |
| Untracked porcelain entries | 26 |
| Expanded untracked files | 174 |
| Stashes | 0 |
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` |

Expanded untracked files increased from the prior report's 172 because the two Claude artifacts (`SPS2-SECOND-PASS-INTEGRATION-FINAL-20261017-092558.md` and `SPS2-SECOND-PASS-TODO-LEDGER-20261017-084905.md`), this QA ledger, the findings register, and the final dossier are new report files; porcelain collapses the entire `reports/` directory into one entry.

Protected-state hashes were captured before substantive work and are reproduced in the findings register.

## TODO Queue

| ID | Work package | Priority | Dependencies | Acceptance criteria | Status |
|---|---|---|---|---|---|
| W0.1 | Baseline, preservation, provenance | P0 | None | Reproducible Git/status/hash baseline and report-snapshot comparison. | DONE |
| W1 | Test-suite reproducibility | P0 | W0.1 | Two full offline runs, exact module/test totals, skip/failure analysis, CI coverage table. | DONE |
| W2 | Validator forensic reproduction | P0 | W0.1 | Five validators with exit/status/counts/failures and classifications. | DONE |
| W3 | P10, frontend/security controls | P0 | W0.1 | Gate reconciliation, prerequisite table, scanner/tests, protected state evidence. | DONE |
| W4 | Updater/install/update safety | P0 | W0.1 | Per-control updater evidence, mirror identity, platform caveats, residual risks. | DONE |
| W5 | Governance/provenance/decision records | P0 | W0.1 | DEC-73xx reference and approval-language inventory, hashes, checker behavior. | DONE |
| W6 | Rollback/snapshot/rehearsal contracts | P1 | W0.1 | Control-by-control rollback review and isolated tests. | DONE |
| W7 | Test quality/false-green controls/coverage | P1 | W1-W6 | Severity-ranked test-quality findings with reproductions. | DONE |
| W8 | Cross-report/change attribution reconciliation | P0 | W1-W7 | Claim-by-claim verification table for Codex and Claude reports. | DONE |
| W9 | Integration, severity ranking, QA verdict | P0 | W8 | Deduplicated findings, final report, explicit verdict and User decisions. | DONE |

## Progress Log

- **2026-10-17 09:35:59 +06 — W0.1 opened.** Live Git state and protected hashes captured. No concurrent repository-writing process was identified; long-running Codex/Claude application processes exist but no active `git commit`, `push`, `fetch`, `pull`, `merge`, or `rebase` command was observed.
- **2026-10-17 09:36:40 +06 — W0.1 closed.** Claude reports were read for claims only. The local pre-mission backup manifest was compared read-only: 598/614 files match and 16 differ, all in preserved implementation work. The backup is a recovery point, not a current snapshot. No repository mutation occurred.
- **2026-10-17 09:40:20 +06 — W1 closed.** Two independent 35-module runs each executed 1,057 tests with 0 failures, 0 errors, and 2 expected skips. Run durations were 46.653s and 46.447s. Seven untracked modules are outside CI's committed 28-module manifest. Codex's 1,051 was a pre-Claude snapshot; Claude added six tests.
- **2026-10-17 09:42:10 +06 — W2 closed.** All five validators reproduced independently. Results: SPS2 79/4, P2 68/9, P3 66/10, P4 57/11 with 0 missed, and P5 44/1 with 0 missed. P4 N18 now requires checker-emitted `DUPLICATE`; P5 s7/s8/s9 now have genuine success conditions and report computed governance problems.
- **2026-10-17 09:44:30 +06 — W3 closed.** Live P10 gate is exit 1 with 9 PASS, 5 FAIL, 2 BLOCKED, and 0 integrity problems. Claude's 4 PASS / 12 FAIL claim is contradicted as a description of 16 required controls. Dynamic import remains an honest scanner violation. P10/frontend/SEO focused tests: 379 passed. P17 security: 65 passed. Protected P10 hashes unchanged.
- **2026-10-17 09:47:15 +06 — W4 closed.** All five updater mirror pairs are byte-identical; Bash syntax passes; focused updater suite is 43 tests with one expected PowerShell-runtime skip. Updater cache/version controls are present. Installer SSH host-key checking is disabled, uninstall paths from the manifest are not confinement-checked, and mirror sync is non-atomic.
- **2026-10-17 09:50:05 +06 — W5 closed.** Current tree has 36 files referencing DEC-73xx, including 20 outside `reports/`. Five normative documents contain "authorized/approved by DEC-7301/7302" language. Round 26 record and correction sidecar hashes are unchanged. Both decision checkers accept the false-attribution record structurally and cannot authenticate User attribution. `.claude/settings.json` is empty in the worktree but 27 bytes at HEAD.
- **2026-10-17 10:00:00 +06 — W6 closed.** The 23-test rollback/isolation suite passed with 0 failures/errors/skips. Rehearsal failure is correctly attributed to the unapproved dynamic import; it is not a false green. Snapshot integrity has residual strictness and atomicity gaps recorded as QA-0019/QA-0020.
- **2026-10-17 10:12:00 +06 — W7 closed.** Confirmed a scanner evasion for `getattr`/subscript dynamic-loader calls (QA-0021). Verified the two full-suite skips are environmental, N18/P5 controls are behavioral, P17 collection is nonempty, and PowerShell static coverage remains limited.
- **2026-10-17 10:25:00 +06 — W8 closed.** All 19 Claude fixes have live-tree evidence; authorship is report-supported but not independently provable. Current test/validator/P10 counts reconcile, except Claude's P10 4/12 claim remains contradicted by the live 9/5/2 gate.
- **2026-10-17 09:52:49 +06 — W9 closed.** Final protected hashes and controlled Git dimensions matched the opening baseline; expanded untracked files grew from 174 at audit open to 177 after the final dossier. The final dossier records 25 findings, a QA-not-passed repository verdict, and the bounded User decision list.
