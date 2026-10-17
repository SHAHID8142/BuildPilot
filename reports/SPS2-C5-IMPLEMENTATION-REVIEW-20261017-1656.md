# SPS2 C5 Updater/Bootstrap Implementation and Review

**Date:** 2026-10-17 16:56 +06  
**Implementer:** Codex primary  
**Independent review:** Codexx CLI, read-only, **PASS**  
**Claude review:** Not obtained. Claude CLI could not select a supported model through the configured gateway; no Claude verdict is claimed.

## Scope

Addressed the five confirmed C5 findings from `reports/SPS2-COMPLETION-C5-CODEX-AUDIT-20261017-123100.md` in the bootstrap and check-update scripts and their skill mirrors. Added focused regression coverage. No real install or uninstall was run.

## Changes

- Bootstrap rejects a symlinked `.sps` destination, non-directory `.sps` destination, and symlinked template paths before writing. Tests cover a symlinked `.sps` directory plus existing and dangling template-file symlinks; sentinels and pre-write behavior are checked.
- Bash and PowerShell version comparisons handle arbitrarily long numeric prerelease identifiers as strings, normalized by leading zeroes, length, and digit order.
- Fresh cached status is recomputed from the current installed version and cached latest version; a valid offline cache remains exit 2.
- Bash validates installed versions before comparison, preventing malformed values from reaching `10#` arithmetic.
- Root-to-skill parity tests now include both check-update script pairs.
- Root/mirror SHA-256 hashes match for the bootstrap, Bash checker, and PowerShell checker.

## Verification

- `python3 -m unittest sps2.tests.test_check_update_safety sps2.tests.test_updater_safety -v`: **47 tests passed, 1 skipped**. The skip is PowerShell behavioral coverage because `pwsh` is unavailable. Bash behavior includes 36-digit prerelease identifiers in both comparison directions.
- Bash syntax check across the four Bash root/mirror scripts: **passed**.
- Focused `git diff --check` for the six implementation scripts: **passed**. A repository-wide check still reports pre-existing trailing whitespace in `.sps/plan.md`; that file was not changed.
- `shellcheck` and `pwsh` are unavailable in this environment.
- Codexx CLI reviewed the five findings and exact code/test surface and returned **PASS**. It independently passed six static/mirror tests and Bash syntax/diff checks. Its attempt to run the full focused suites under its read-only sandbox was blocked because temporary test fixtures could not be created (33 environment errors, 1 skip); this does not override the primary run above.
- Claude CLI review was attempted but the configured gateway rejected the available model IDs. This is an environment limitation and is not a Claude review.

## Preservation and readiness

- Branch `build/roadmap-p3-completion`, HEAD `c49f3852e1c31d0136269c80fe58201b059af3ec`.
- Worktree inventory at report time: 81 porcelain entries before adding this report/log; no staging or stashes were created by this work.
- No CI, validator baseline/exception manifest, governance/decision, approval, P10 gate, or release record was changed. P10 and release readiness remain **NOT READY**; validator failures remain visible.
- No commit, push, deploy, publish, merge, release, cleanup, or real install/uninstall occurred.

## Follow-up

C5 has a PASS from Codexx CLI but still lacks the specifically requested Claude cross-review. `pwsh` runtime behavior remains unverified until a PowerShell runtime is available. Keep this limitation visible; continue with the next separately scoped, already delegated package only after recording this checkpoint.
