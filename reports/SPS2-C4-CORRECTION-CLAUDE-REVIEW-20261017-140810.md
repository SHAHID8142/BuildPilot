# SPS2 C4 Correction — Claude Independent Review

**Timestamp:** 2026-10-17 14:08:10 +06  
**Reviewer:** Claude (independent reviewer)  
**Subject:** Codex C4 snapshot/rollback correction handoff at 13:48 +06.  
**Verdict:** **NEEDS REVISION.** The tested C4-3/C4-4/R-2 behaviors are materially improved, but two ownership/restore defects remain.

## 1. Review Basis and Preservation

The bounded monitor made four checks before this handoff appeared. The implementation report is `reports/SPS2-C4-CORRECTION-IMPLEMENTATION-20261017-1348.md`; the delegated scope is `reports/SPS2-DELEGATED-DECISIONS-20261017.md`, treated as operational guidance rather than a User-authored approval record.

Live state at review start and end:

| Item | Value |
|---|---|
| Branch | `build/roadmap-p3-completion` |
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` |
| Staged files | 0 |
| Modified tracked paths | 42 |
| Untracked porcelain entries | 27 |
| Total porcelain entries | 69 |
| Stashes | 0 |

Files reviewed:

| Path | Status | SHA-256 |
|---|---|---|
| `sps2/tools/rollback_seo.py` | modified | `d7c3c2a0bea4936bf58a657b9e3918544338f4b9f4e9a877822ca3e72e67a6fa` |
| `domain/seo/tests/test_isolation.py` | modified | `fcd446dda9fe565d49614f80e0366a243cc32fef4217d6b1766f70c6f3ecd07f` |
| `sps2/tests/test_round26_governance_contracts.py` | untracked | `2066729f767a921ece97d4448a6c3d39896d31fbb29aafd41c598aaf95343165` |

The patch scope is limited to the three declared files. Protected hashes remained unchanged for the Round 26 record, correction sidecar, both exception manifests, CI workflow, and expected-module list. P10 gate, test, slice, evidence, inventory, requirement, and decision hashes also remained unchanged. `.claude/settings.json` remained the pre-existing zero-byte modified state and was not touched.

## 2. Verified Improvements

### Snapshot destination handling — verified

`create_snapshot` now uses `lstat` before staging or moving anything and rejects every non-directory entry type, including regular files and symlinks (`sps2/tools/rollback_seo.py:288-311`). The occupant is not moved or modified.

Relevant tests passed:

- `test_snapshot_rejects_regular_file_destination` (`domain/seo/tests/test_isolation.py:465`)
- `test_snapshot_rejects_symlink_destination` (`domain/seo/tests/test_isolation.py:482`)

### Publish/restore failure windows — verified for tested paths

The new cleanup ordering preserves the previous snapshot when post-publish cleanup fails (`sps2/tools/rollback_seo.py:340-368`). A pre-publish failure restores the previous directory when the live target is absent. The tests at `domain/seo/tests/test_isolation.py:575-639` verify both windows and digest-level differences between old and new snapshots.

### Restore allowlist and partial mutation — verified for same-process operation

`restore_snapshot` now performs containment, P9 allowlist, existence, and digest validation before copying (`sps2/tools/rollback_seo.py:402-447`). The tests at `domain/seo/tests/test_isolation.py:421-463` verify rejection of an unrelated in-root file and no copy when the final manifest entry is invalid.

### Test cleanup — verified

The duplicate `tearDown` was merged into one cleanup path at `sps2/tests/test_round26_governance_contracts.py:241-249`. The focused round26 run reported no `ResourceWarning`.

## 3. Focused Test Results

Commands used:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v domain.seo.tests.test_isolation
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v sps2.tests.test_round26_governance_contracts
```

| Suite | Result |
|---|---|
| `domain.seo.tests.test_isolation` | 36 tests, 0 failures, OK, exit 0 |
| `sps2.tests.test_round26_governance_contracts` | 38 tests, 0 failures, OK, exit 0 |

Additional read-only boundary checks:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json
```

Result: exit 1; 16 controls; 9 PASS / 5 FAIL / 2 BLOCKED; overall `FAIL`; no integrity problems. The shared scanner reported `ok=False`, 8 approved imports, and exactly one violation at `sps2/tools/p10_runtime_gate.py:1944`. `git diff --check` exited 0.

## 4. Blocking Findings

### R-C4-1 — Non-allowlisted `.py` files under `domain/seo` are still deleted

`get_unowned_domain_seo_files` treats every regular `.py` file under `domain/seo` as owned without comparing its repository-relative path to `P9_ALLOWLIST_RELATIVE_PATHS` (`sps2/tools/rollback_seo.py:167-177`). Thus an unrelated user Python file under that tree can enter the recursive deletion set.

Isolated temporary-fixture result:

```text
unowned_before = []
rollback_code = 1
user_override_exists = False
model_exists = False
```

The fixture placed `domain/seo/user_override.py` beside allowlisted `domain/seo/model.py`. `user_override.py` was deleted. This contradicts the function's stated non-P9 preservation contract and the rollback tool's top-level guarantee that unrelated user files are preserved.

The existing test covers a non-Python file (`domain/seo/tests/test_isolation.py:314-322`) but not a non-allowlisted `.py` file. This is a test-fidelity gap as well as an implementation defect.

**Required correction:** compute repository-relative paths and reject any `domain/seo` entry not present in the shared P9 allowlist, including `.py` files. Add positive and negative tests for a non-allowlisted `.py` file and ensure both the file and deletion set remain unchanged on abort.

### R-C4-2 — Restore is not importable from a fresh process after rollback

`sps2/tools/rollback_seo.py` imports the restore allowlist from the P9 surface at module import time (`sps2/tools/rollback_seo.py:42`). A real rollback removes `domain/seo`, including `domain/seo/isolation.py`. The focused restore test runs in a process that already imported the module, so it does not expose this failure.

Isolated temporary-fixture result after rollback:

```text
domain_seo_exists = False
fresh_restore_rc = 1
fresh_restore_stderr = ModuleNotFoundError: No module named 'domain.seo'
```

Therefore the snapshot may exist, but a fresh post-rollback process cannot import `restore_snapshot` to use it. This defeats the practical recovery guarantee even though the same-process focused test passes.

**Required correction:** make the restore path independent of the P9 implementation being restored, while preserving a single authoritative allowlist source or a fail-closed fallback with integrity checks. Add a subprocess regression test that creates a snapshot, performs rollback, starts a fresh Python process, and successfully restores only allowlisted paths.

## 5. Non-Blocking Observations

1. The stricter `__pycache__` abort is a deliberate fail-closed behavior change and is covered by `domain/seo/tests/test_isolation.py:500-517`.
2. The symlinked-root and deletion-time race guards are covered by `domain/seo/tests/test_isolation.py:519-573`.
3. Post-publish failure retaining both snapshots is intentional but increases disk use until cleanup.
4. Scanner R-1 remains untouched as required by the delegated scope.
5. The snapshot destination guard does not address a symlinked *parent* directory; that was not part of the C4 finding and remains a possible future hardening item.

## 6. Governance and Authorization

This review does not ratify DEC-7301, DEC-7302, or DEC-7303. The shared import scanner still reports the dynamic P10 import as forbidden, and the P10 gate remains fail-closed. No approval, publication, deployment, release, staging, commit, push, CI change, baseline change, governance-record change, P10-evidence change, `.sps/` change, or destructive live rollback was performed.

## 7. Disposition

**Verdict: NEEDS REVISION.**

The correction is not accepted for C4 closure because R-C4-1 can destroy unrelated Python files and R-C4-2 can make an existing snapshot unusable from a fresh post-rollback process. One scoped repair/re-review cycle may address exactly these two defects and their focused regression tests. No next implementation package should start until that repair passes independent review.
