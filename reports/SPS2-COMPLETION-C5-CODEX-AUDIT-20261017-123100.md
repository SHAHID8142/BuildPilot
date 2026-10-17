# SPS2 C5 Updater and Bootstrap — Codex Read-Only Audit

**Timestamp:** 2026-10-17 12:31:00 +06  
**Reviewer:** Codex subagent `c5_updater_audit`  
**Status:** Findings recorded; independent review pending  
**Branch / HEAD:** `build/roadmap-p3-completion` / `c49f3852e1c31d0136269c80fe58201b059af3ec`

## Scope and preservation

Audited updater/bootstrap/check-update mirrors and path/cache/fallback behavior. Rechecked the four P1 validator failures, focused tests, and mirror parity. The reviewer reports start and finish worktree inventories match: 40 modified tracked paths, 26 untracked porcelain entries, 0 staged, and 0 stashes. No repository files were edited. No real install or uninstall was run.

Focused suites: **43 passed, 1 skipped** because `pwsh` is unavailable. PowerShell runtime behavior remains unverified.

## DEC-7301 validator boundary

`bash sps2/tools/validate-sps2.sh`: **exit 1, 79 passed / 4 failed**. The four current failures are:

- `scripts/check-update.ps1`
- `scripts/check-update.sh`
- `skills/sps/scripts/check-update.ps1`
- `skills/sps/scripts/check-update.sh`

The validator failure is a current protection-boundary failure, not a validator-code defect: the live DEC-7301 manifest explicitly excludes these four paths, while the shared validator reports modified paths outside its eight pinned exceptions. Resolving this requires an explicit User choice to amend/re-pin that exception scope or accept the failing validator. DEC-7301 approval authenticity is disputed, so its record is not evidence of confirmed User approval.

Current check-update files also differ from the latest recorded Round 26 hashes: Bash `1955279a…` vs recorded `f175ed77…`; PowerShell `2829a1db…` vs `ca00fcea…`. The historical hashes are stale for current content; provenance and independent review of current changes remain unverified. Preserve the files.

## Findings

### C5-1 — Bootstrap `--force` follows a destination symlink

In `scripts/bootstrap-sps.sh:42-46`, `--force` copies directly to the destination. An isolated temporary-directory probe with `.sps/profile.md` symlinked to an outside sentinel overwrote the outside target; the probe cleaned up its fixture. The mirrored bootstrap file is byte-identical. Proposed fix: reject a symlinked `.sps` directory and symlinked destination before writing. Add tests for existing and dangling links; assert the outside target is unchanged.

### C5-2 — Large numeric prerelease values produce a false ordering

The Bash version pattern in `scripts/check-update.sh:57-64` permits arbitrarily long numeric prerelease identifiers, while `:111-113` compares them using Bash integer arithmetic. Reproduction: installed `1.2.3-alpha.1`, remote `1.2.3-alpha.999999999999999999999999999999999999` returns exit 0 and says local is newer, although remote is newer. PowerShell similarly casts prerelease numeric parts to `[int64]` at `scripts/check-update.ps1:63-69`; runtime impact is unverified without `pwsh`. Proposed consistent fix: compare normalized numeric strings by length, then digits. Test large values in both directions for both implementations; run PowerShell coverage when available.

### C5-3 — Fresh update cache can use a status from a different installed version

At `scripts/check-update.sh:153-157` and `scripts/check-update.ps1:134-144`, cached `STATUS` is trusted without comparing cached `LATEST` with the current installed version. Reproductions: cached `up-to-date / 4.0.0` with installed `3.0.0` exits 0 and reports up-to-date; cached update-available remains exit 1 after installed version reaches the cached latest. Updater scripts do not clear the cache after installation. Proposed fix: recompute status against the current installed version or key the cache to that version. Add both regression cases in Bash and PowerShell.

### C5-4 — Malformed Bash installed version reaches arithmetic comparison

`scripts/check-update.sh:127-131` maps malformed values to `unknown`, then unconditionally calls `is_greater` at `:191`, despite its valid-input precondition at `:83`. The malformed-version probe reports update available and emits two `10#unknown` arithmetic errors from `:91-92`. Proposed fix: guard comparison with version validation and assert there are no arithmetic diagnostics. Existing test `sps2/tests/test_check_update_safety.py:176-181` does not catch those diagnostics.

### C5-5 — Checker mirror parity is not asserted

All five current updater/checker root-to-skill mirror pairs are byte-identical, but `sps2/tests/test_updater_safety.py:296-303` checks only bootstrap and two updater pairs. Checker-specific tests exercise only root scripts. Add both check-update pairs to the mirror-parity regression test.

## Confirmed behavior and limitations

- Fallback in `scripts/sps-update.sh:41-55` tries sibling and installed-repository checkers, then fails closed with exit 2 and no network fetch; focused fallback tests passed.
- Dirty-source and non-Git destination refusal tests passed.
- The focused suites total 43 passing tests and one environment skip. PowerShell behavior is unverified because `pwsh` is unavailable.
- ShellCheck availability is separately recorded in the C0-C3 report.

## Next checkpoint

Claude should independently review the five findings, exact file/line claims, reproductions, proposed tests, and preservation state. Review only; no fixes or edits to source/tests/governance/baselines. In particular, distinguish code-owned fixes from the DEC-7301/recorded-hash approval boundary. Append the review to the coordination log and stop after one pass. Do not treat this audit as authorization or as a User decision.

