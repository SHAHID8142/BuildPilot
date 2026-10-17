# SPS2 C4 Repair — Implementation and Verification

Date: 2026-10-17 16:40 +06  
Implementer: Codex primary agent  
Scope: only the two blocking findings from Claude's 14:08 C4 correction review.

## Changes

1. **R-C4-1 — exact rollback ownership.** `get_unowned_domain_seo_files` now reports every entry whose repository-relative path is not in the exact P9 allowlist, including otherwise regular `.py` files. `execute_rollback` checks that result before snapshot or deletion. The new `test_rollback_aborts_on_unallowlisted_python_file` verifies that rollback stops and the user's `user_override.py` remains byte-identical.
2. **R-C4-2 — fresh-process recovery.** Moved the shared `P9_ALLOWLIST_RELATIVE_PATHS` definition to `sps2/core/p9_surface.py`, outside the removable `domain/seo` tree. Both `domain/seo/isolation.py` and `sps2/tools/rollback_seo.py` import this stable definition. The new `test_restore_snapshot_in_fresh_process_after_rollback` removes the temporary P9 tree, starts a new interpreter from the rolled-back project, imports the restore function, and verifies the snapshot restores `isolation.py`.

## Files

- `sps2/core/p9_surface.py` — new stable allowlist source.
- `domain/seo/isolation.py` — re-exports the shared allowlist through its existing module API.
- `sps2/tools/rollback_seo.py` — stable import and exact allowlist ownership check.
- `domain/seo/tests/test_isolation.py` — two regression tests and required subprocess imports.

No CI, baseline, manifest, governance decision, or P10 artifact was intentionally changed. Append-only current-session notes were added to `.sps/agent.md` and `.sps/handoff.md` as required by SPS v4.0; the approved `.sps/plan.md` and all pre-existing content were preserved. Scanner residual R-1 remains deferred. No staging, commit, push, deployment, publication, merge, release, live rollback, or destructive cleanup occurred.

## Verification

- `python3 -m unittest domain.seo.tests.test_isolation -v` — **38 tests passed**.
- `python3 -m unittest sps2.tests.test_round26_governance_contracts -v` — **38 tests passed**.
- Independent Codex subagent review — **PASS** for both R-C4-1 and R-C4-2; it reran both targeted regression tests (**2 passed**) and made no changes.
- `git diff --check` — clean.
- Claude CLI re-review was attempted but unavailable in this restored environment: its configured provider rejected `river-glm-5.3-flash` and `claude-sonnet-4-5` as invalid model IDs (HTTP 400). This is not represented as a Claude PASS.

## Preservation state

- Branch: `build/roadmap-p3-completion`.
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec` (unchanged).
- Staged paths: 0. Stashes: 0.
- Worktree: **70 porcelain entries** (42 tracked modifications and 28 untracked entries), compared with the 69-entry pre-repair baseline. The one additional untracked path is `sps2/core/p9_surface.py`, required so fresh-process restore can import its allowlist after `domain/seo` is removed.
- Protected records were outside the four-file patch; no protected path was edited by this repair.

## Review decision and remaining limitation

The independent Codex review is PASS for the two repair findings. The original Claude review remains accurately recorded as NEEDS REVISION for its original patch, and this repair has no Claude verdict because the local CLI model gateway rejected its configured model IDs. P10 remains **NOT READY** at 9 PASS / 5 FAIL / 2 BLOCKED; this repair does not change that gate.
