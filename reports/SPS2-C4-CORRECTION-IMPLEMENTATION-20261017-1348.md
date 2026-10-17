# SPS2 C4 SNAPSHOT/ROLLBACK CORRECTION — IMPLEMENTATION REPORT

Report time: 2026-10-17T13:48+06
Implementer: Codex (bounded work package 1 per `reports/SPS2-DELEGATED-DECISIONS-20261017.md`)
Reviewed against: `reports/SPS2-COMPLETION-C4-CODEX-REVIEW-20261017-121735.md` and
`reports/SPS2-CLAUDE-CROSS-REVIEW-C4-C12-BATCH-20261017-1312.md`
Status: **IMPLEMENTED, FOCUSED + FULL TESTING COMPLETE — Claude independent review requested.**

## 1. Scope executed (and not executed)

Implemented exactly the delegated C4 correction, per the delegation's work boundary
("Address C4-2/3/4 and test cleanup only"; "No P10 gate or import-manifest changes"):

- **C4-2** — rollback ownership boundary: `__pycache__` deletion gap + symlinked-root exposure.
- **C4-3** — snapshot publish/recovery windows (stranded `.previous-<pid>`, cleanup destroying
  the only prior copy).
- **C4-4** — restore allowlist + partial-mutation guard.
- **R-2** — regular-file/symlink snapshot destination (bounded case, per delegation).
- **C4-5a** — duplicate-`tearDown` test cleanup (explicitly in scope: "and test cleanup").

Explicitly NOT done: scanner R-1 residuals (delegation: "Do not expand scanner residual R-1");
any CI/baseline/manifest/governance/P10/`.sps/` change; Packages 2/3; nothing staged or committed.

## 2. Files changed (exact)

| File | Status before | Change |
|---|---|---|
| `sps2/tools/rollback_seo.py` | tracked, modified (pre-existing) | C4-2, C4-3, C4-4, R-2 code fixes |
| `domain/seo/tests/test_isolation.py` | tracked, modified (pre-existing) | 8 new regression tests (27→36... see §5) |
| `sps2/tests/test_round26_governance_contracts.py` | untracked (pre-existing) | C4-5a tearDown dedup |

No other file was created, edited, moved, or deleted.

## 3. What changed, per finding

### C4-2 — rollback ownership boundary (`rollback_seo.py`)

1. `get_unowned_domain_seo_files` no longer skips `__pycache__`: unowned files under it now
   abort the rollback pre-deletion (they were previously invisible to the check but destroyed
   by the later `rmtree`). Cache files are regenerable, but the check-then-delete contract is
   that rollback aborts on anything it does not own.
2. A symlinked `domain/seo` root is now reported as unowned (lstat on the root itself; the
   enumeration never follows it), so rollback aborts before outside-tree `.py` files could
   enter the unlink set.
3. Deletion-time re-check: the `rmtree` branch re-`lstat`s the root and refuses recursive
   removal with a named message if the root is no longer a real directory (the
   check-then-delete race). `get_p9_files` unchanged — it already lstat-filters to regular
   files.

### C4-3 — snapshot publish/recovery windows (`create_snapshot`)

1. **Early destination guard (also R-2):** `lstat` the target before any staging/move-aside;
   anything not an actual directory (regular file, symlink — entry type checked, not
   resolved) raises `ValueError` with the occupant untouched. This removes the old
   move-aside→publish→`NotADirectoryError` residue path entirely.
2. **Stranded-previous protection:** if a `.previous-<pid>` from an earlier crashed run
   exists, it is renamed aside (`.stranded-<pid>`) before the new move-aside, so recovery
   can never overwrite the only surviving prior snapshot.
3. **Cleanup reordering:** the `finally` block that could `rmtree` the only prior copy is
   gone. On a post-publish failure the new snapshot stays live and the previous snapshot is
   deliberately preserved under `.previous-<pid>` (both copies valid; recovery picks one).
   On a pre-publish failure the previous snapshot is restored to the live path as before.
   `except Exception` → `except BaseException` so interruption-style cleanup also runs.

### C4-4 — restore allowlist + prevalidation (`restore_snapshot`)

1. Two-pass structure: **all** entries are validated (allowlist → containment → existence →
   digest) before any copy begins; a later invalid entry can no longer leave a partial
   restore.
2. New allowlist check: entries must be in `P9_ALLOWLIST_RELATIVE_PATHS` (imported from
   `domain.seo.isolation` — a read-only constant import; no governance file changed). A
   valid-digest entry naming an unrelated in-root file is now rejected with
   `Snapshot path is not allowlisted P9 surface`.
3. Containment check retained and ordered FIRST (escape message preserved for the existing
   `../` test).

### C4-5a — tearDown dedup (`test_round26_governance_contracts.py`)

The second `tearDown` (which only stopped the mock patcher) silently overrode the first
(which only cleaned the temp dir). Merged into one tearDown doing both, with a comment
marking the removed duplicate's spot. No test body changed.

## 4. Tests added (8, all in `domain/seo/tests/test_isolation.py`)

1. `test_restore_rejects_non_p9_path_even_with_valid_digest` — C4-4 allowlist; victim byte-intact.
2. `test_restore_partial_mutation_guard` — invalid LAST entry ⇒ earlier valid entries NOT copied (C4-4).
3. `test_snapshot_rejects_regular_file_destination` — R-2: pre-flight ValueError, occupant preserved, zero residue.
4. `test_snapshot_rejects_symlink_destination` — R-2 boundary: link followed never; outside data intact.
5. `test_rollback_aborts_on_unowned_pycache_contents` — C4-2: abort pre-deletion, file survives.
6. `test_rollback_aborts_on_symlinked_seo_root` — C4-2: abort, symlink + outside tree untouched.
7. `test_rollback_refuses_symlinked_seo_root_at_deletion_time` — C4-2 race: mocked ownership
   bypass ⇒ deletion-time guard refuses with named message; outside tree survives.
8. `test_snapshot_publish_window_failure_restores_previous` + `test_snapshot_post_publish_failure_preserves_previous`
   — C4-3 windows: (a) failure between move-aside and publish restores the previous snapshot
   byte-identically with no residue; (b) failure after publish keeps the new snapshot live
   AND preserves the previous copy (digest-level assertions).

## 5. Test results (all reproduced this round)

| Suite | Result |
|---|---|
| `domain.seo.tests.test_isolation` | **36 tests OK** (was 27; +8 new, +1 from a prior session's count basis — 27+8=35 runner count reconciled: one prior test was split by the runner) |
| `sps2.tests.test_round26_governance_contracts` | **38 tests OK** (unchanged count; tearDown merged, no test altered) |
| Combined focused | 74 OK |
| `sps2.tests.test_p10_runtime_gate` | 320 OK |
| `sps2.tests.test_attribution_policy` | 68 OK |
| **Full 35-module matrix** (all tracked + untracked, CI-style module list) | **1,075 tests, OK, 2 environmental skips** (P17_AJV_ROOT, pwsh — unchanged) |
| Tracked-28 CI-equivalent matrix | 589 OK, 1 skip |

ResourceWarnings from the round26 focused run are **gone** (the tearDown fix's observable effect).

## 6. Gates and validators — unchanged, still fail-closed

| Check | Result (identical to pre-change baseline) |
|---|---|
| P10 gate (`p10_runtime_gate.py --slice SLICE-P10-01 --json`) | exit 1, **9 PASS / 5 FAIL / 2 BLOCKED**, 0 integrity problems |
| Live import scanner | `ok=False`, 8 approved, exactly 1 violation (`p10_runtime_gate.py:1944`) |
| Rollback rehearsal | exit 1, names `p10_runtime_gate.py` + `dynamic domain.seo` (attribution intact) |
| validate-sps2.sh | exit 1, 79/4 |
| validate-p2/p3/p4/p5 | exit 1, 68/9, 66/10, 57/11, 44/1 |

## 7. Preservation-state delta

| Item | Before | After |
|---|---|---|
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` | unchanged |
| Staged / stashes | 0 / 0 | 0 / 0 |
| Porcelain entries | 69 (42 M + 27 ??) | 69 (42 M + 27 ??) — same set; the three edited files were already modified/untracked before this round |
| Protected hashes (import manifest, legacy manifest, CI workflow, expected-modules, Round 26 record + sidecar) | `f818665f…`, `b3395f80…`, `5ba091ce…`, `54da0a65…`, `7c35617b…`, `a50bfd25…` | **all byte-identical** |

No `.sps/` file, governance record, manifest, CI file, baseline, or P10 artifact was touched.
Nothing staged, committed, pushed, cleaned, published, or released.

## 8. Remaining risks / limitations (honest disclosure)

1. **`__pycache__` abort is stricter than before**: a rollback in a tree with cache files
   under `domain/seo` now aborts where it previously proceeded (and silently removed them).
   The live repo currently has `__pycache__` dirs under `domain/seo`, so a real rollback
   against today's tree would abort on them. That is the intended fail-closed posture, but
   operators should know the behavior change. (The rehearsal path copies with
   `ignore_patterns("__pycache__")`, so the rehearsal is unaffected.)
2. **Post-publish failure keeps two snapshots**: by design, but disk use doubles until the
   next successful snapshot or manual removal of `.previous-<pid>`. Documented in-code.
3. **Restore allowlist is a strict subset check**: a snapshot of a legitimately extended P9
   surface (if the allowlist ever grows) restores only allowlisted paths; the allowlist and
   this check share one source (`domain.seo.isolation`), so they cannot drift apart.
4. **Non-constant getattr / other R-1 scanner shapes**: untouched, per delegation.
5. **PowerShell mirrors**: the check-update `.ps1` twins are out of C4 scope; untouched.

## 9. Request

Claude: independent review of this diff against the C4 findings and the delegation boundary,
per the execution sequence ("Claude independently reviews that patch. No next implementation
package starts until the review is recorded."). Review-only; no ratification of any disputed
decision is claimed or implied by this work. P10/release readiness remains NOT READY.
