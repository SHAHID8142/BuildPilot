# SPS2 Remediation Implementation — Packages 1 and 4

**Timestamp:** 2026-10-17 10:37:53 +06  
**Filename suffix:** `20261017-103753`  
**Branch:** `build/roadmap-p3-completion`  
**HEAD:** `c49f3852e1c31d0136269c80fe58201b059af3ec`  
**Scope:** Package 1 scanner evasion hardening and Package 4 rollback/snapshot hardening only.  
**Status:** Implementation and focused/offline testing complete; **Claude review is pending.**

## 1. Baseline and Final Preservation

| Item | Before | After |
|---|---:|---:|
| Staged files | 0 | 0 |
| Modified tracked files | 39 | 39 |
| Untracked porcelain entries | 26 | 26 |
| Total porcelain entries | 65 | 65 |
| Expanded untracked files | 182 | 182 |
| Stashes | 0 | 0 |

The expanded untracked count excludes this report until it is written. No pre-existing file was reset, reverted, deleted, moved, or cleaned.

## 2. Changes Implemented

### Package 1 — Scanner evasion hardening

Files:

- `sps2/governance/import_exceptions.py`
- `sps2/tests/test_round26_governance_contracts.py`

Changes:

1. Added dynamic-loader expression recognition for direct `getattr(..., "import_module")`, subscripted loader access, and rebound loader names.
2. Added a bounded AST pre-pass that follows assignments to recognized dynamic-loader expressions.
3. Preserved the existing manifest contract and did not add any import exception.
4. Added focused tests for bare-name rebinding, `getattr` rebinding, subscript rebinding, direct `getattr`, and a local `import_module` name.

This is security-only hardening. It does **not** ratify DEC-7302 or alter the disputed approval record.

### Package 4 — Snapshot and rollback hardening

Files:

- `sps2/tools/rollback_seo.py`
- `domain/seo/tests/test_isolation.py`

Changes:

1. Snapshot creation now stages files and publishes the completed snapshot atomically.
2. Interrupted snapshot creation cleans staging state and leaves no live manifest.
3. Rollback now restricts the deletion set to regular Python files in the allowlisted P9 surface.
4. Non-P9 files under `domain/seo` abort rollback and are preserved by name.
5. Inside-root symlinks under `domain/seo` abort rollback and are preserved.
6. Unlink failures now return a named partial-rollback failure instead of raising an unhandled traceback.
7. `domain/seo` directory removal is fail-closed on error.
8. Added focused tests for interrupted snapshots, non-P9 preservation, symlink preservation, and unlink failure.

The rollback rehearsal still fails closed on the known unapproved dynamic import. No rollback success was fabricated.

## 3. Tests Run

| Command | Exit | Result |
|---|---:|---|
| `python3 -B -m unittest -v sps2.tests.test_round26_governance_contracts` | 0 | 38 tests, 0 failures, 0 errors, 0 skips |
| `python3 -B -m unittest -v domain.seo.tests.test_isolation` | 0 | 27 tests, 0 failures, 0 errors, 0 skips |
| `python3 -B -m unittest -v sps2.tests.test_round26_governance_contracts domain.seo.tests.test_isolation` | 0 | 65 tests, 0 failures, 0 errors, 0 skips |
| Full offline module matrix | 0 | **1,066 tests, 0 failures, 0 errors, 2 expected skips** |
| `python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json` | 1 | **9 PASS / 5 FAIL / 2 BLOCKED**, 0 integrity problems |
| `git diff --check` | 0 | Clean |

The two full-suite skips remain environmental: missing `P17_AJV_ROOT` and unavailable `pwsh`.

## 4. Integrity and Governance Checks

Protected records remained unchanged:

| Path | SHA-256 |
|---|---|
| `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json` | `7c35617b309bef3557ad439fbb74be8455535f26a21cfe323d574ff73be5ed69` |
| `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS-CORRECTION-20261017.md` | `a50bfd25fa54c8a6b38ee97515f043d0a29f9518ceabe3b3dfc9457b8620f1e6` |
| `sps2/governance/legacy-exception-manifest.json` | `b3395f807296c9306a67112f54748bb7fdcbd26fb1ad0cc95fa911f42975554d` |
| `sps2/governance/p10-p9-import-exception-manifest.json` | `f818665f471d015d6940a6ddbf4c08f02bfeabd6cc6d72e20295c7a321b5c8a8` |
| `.github/workflows/sps-ci.yml` | `5ba091ceee048a81ede4eabd84174b0f314bf68af98cd8b64cf5323751bfebf0` |
| `.github/expected-test-modules.txt` | `54da0a650566c2e462f096c61f2cff63e230da546e3440d7a17450fd9a63443b` |

No CI, validator baseline, decision record, correction sidecar, exception manifest, P10 gate, or protected evidence file was changed.

## 5. Prohibited Operations

This round did **not** implement Packages 2 or 3, stage, commit, push, deploy, publish, merge, release, alter CI, change validator baselines, ratify DEC-7301/7302/7303, modify the disputed approval record, or perform any destructive cleanup.

## 6. Required Independent Review

Claude has **not** reviewed this resulting diff and tests yet. This report is an implementation handoff, not a completed review cycle. Claude must independently inspect:

1. the scanner dynamic-loader detection and false-positive surface;
2. rollback allowlist enforcement and non-P9 preservation;
3. atomic snapshot publication and interruption cleanup;
4. partial-rollback failure handling;
5. whether any change weakens, bypasses, or appears to ratify an unapproved governance contract.

Implementation remains unreviewed until Claude completes that inspection.
