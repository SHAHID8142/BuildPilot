# SPS2 PHASE 3 — USER DECISION EXECUTION REPORT

**Report ID:** SPS2-PHASE3-DECISION-EXECUTION-20261016-082741
**Scope:** Execution of the seven User decisions issued after Phase 3's decision-ready report.
**Status:** COMPLETE — all authorized changes applied and verified; full corpus GREEN.

---

## 0. EXECUTIVE VERDICT

All seven User decisions were executed. Two local commits were created (7 files total) on
`build/roadmap-p3-completion`. **The complete runnable test corpus is now fully green:**
`29 modules, Ran 889, passed 888, failed 0, skipped 1` — down from `failed 3` at the start of this round.

No push, deploy, fetch, pull, reset, clean, or stash was performed. All untracked user work is preserved.

| Commit | Files | Content |
|---|---|---|
| `238c9e4` | 6 | `.sps/tools` validator migrations + checker/test changes (Decision 1) |
| `cdcbca8` | 1 | CI Python unittest job (Decision 4) |

`HEAD` moved `320d3a5` → `238c9e4` → `cdcbca8`. Branch unchanged, ahead 3, behind 0, **unpushed**.

---

## 1. DECISION EXECUTION LOG

### Decision 1 — APPROVED: commit the three `.sps/tools` migrations + checker/test changes
**Executed.** Commit `238c9e4`, exactly the 6 authorized files, `768 insertions(+), 39 deletions(-)`:

```
 .sps/tools/validate-capability.sh     |  76 +++++-
 .sps/tools/validate-control.sh        |  10 +-
 .sps/tools/validate-governance.sh     | 103 +++++++-
 sps2/tests/test_attribution_policy.py | 443 +++++++++++++++++++++-
 sps2/tools/check_p2.py                |  57 +++++
 sps2/tools/check_p3.py                | 118 ++++++-
```

**The decisive verification:** committed HEAD `320d3a5` was RED
(`test_shell_validator_policy_contract`: `Ran 7 — FAILED (failures=3)`). A **fresh checkout of the
new tree** is GREEN (`Ran 7 — OK`). This confirms the three validator migrations were the sole cause.

### Decision 2 — APPROVED: patches D4, C, F, B on a disposable clone only
**Executed on a disposable clone; the real repo's protected harnesses are untouched.**

Disposable clone: `/tmp/sps2-phase4-disposable-1792117248` (created from the new HEAD).

| Patch | Target | Applied | Verified behaviour |
|---|---|---|---|
| **D4** | `validate-p2.sh`, `validate-sps2.sh` | ✅ | silent→FAIL, noisy→FAIL, missing→FAIL, clean→PASS |
| **C** | `validate-p4.sh` | ✅ | requires `rc==0` + a `^(PROMOTED\|NOT_PROMOTED)` verdict |
| **F** | `validate-p3.sh` | ✅ | records-absent/handoff branches now check `RC` first |
| **B** | `.sps/tools/validate-governance.sh` | **SUPERSEDED** | per your ruling — the committed worktree fix is strictly more complete |

All four patched files pass `bash -n`. The real repo shows **zero** modifications to
`validate-p2.sh`, `validate-sps2.sh`, `validate-p4.sh`, or `validate-p3.sh`.

**Patch F was found MALFORMED and regenerated.** As shipped in the Phase 3 proposal directory, F was
missing its `+++ b/` file header line (`error: patch fragment without header ... :14`). It was
regenerated as a valid diff against committed HEAD; it now applies cleanly (`--check` rc=0).
New hash `0764a5e7cd719ca6`.

> **Resolution of the Decision 1 vs Decision 2 conflict (your ruling):** patch B and the worktree D3
> fix repair the same defect. The worktree version is strictly more complete — patch B replaces only
> the invalid-ERE JSON check, while the worktree edit also rewrites the markdown control and adds
> `agent_flagged_md()`. Patch B is therefore recorded as **superseded** and was not applied.

### Decision 3 — APPROVED: attribution fail-closed hardening (patch A)
**Executed in the worktree.** `sps2/governance/attribution.py` now `b6c21d73cea2290f` (was `de2cc583341d993b`).

Reproduced F1 first with a **conforming** fixture, then re-measured after the patch:

| Case | Before patch | After patch |
|---|---|---|
| Real 17-token policy, `decided_by:"Antigravity"` | 60 B `ERR … non-user 'Antigravity'` ✅ | 60 B — **unchanged** ✅ |
| Degenerate policy `["a b"]`, same fixture | **0 B — SILENT FAIL-OPEN** ❌ | **367 B visible `ERR attribution policy unavailable: ValueError …`** ✅ |
| Control: `decided_by:"User"` | 0 B clean ✅ | 0 B clean ✅ |

`sps2/governance/attribution_policy.json` is **byte-unchanged** (`eb9f113360601059`). No change to the
approved token set, word-boundary behavior, separator handling, or documented non-goals.

### Decision 4 — APPROVED: add the Python unittest CI job
**Executed, then committed as `cdcbca8`** — see §2 for why a second commit was required.

Pure addition to `.github/workflows/sps-ci.yml`: `98 insertions(+), 0 deletions(-)`. The three existing
jobs are untouched. Structural checks: `python-unittest` job present, `fetch-depth: 0` present, zero-test
guard present (`RAN == 0` → fail, `RAN < MIN_TESTS=500` → fail), no `pip install`, no network.

### Decision 5 — APPROVED: patch E; PRESERVE untracked P10/frontend work
**Executed.** `sps2/tools/p10_runtime_gate.py` patched (importlib resolution at `:1917`).

| | Before | After |
|---|---|---|
| `domain.seo.tests.test_isolation` | `Ran 20 — FAILED (failures=3)` | `Ran 20 — OK` |
| `sps2.tests.test_p10_runtime_gate` | `Ran 282 — OK` | `Ran 282 — OK` |
| `domain/seo/**` modified entries | 0 | **0** ✅ |

Untracked work confirmed present and unmodified: `p10_runtime_gate.py`, `test_p10_runtime_gate.py`,
`domain/frontend/`, `domain/cms/data/`, `.sps/tasks/p17/`. Untracked count 104, unchanged.

### Decision 6 — PRESERVE the `co-pilot` non-goal
**Executed — no change made.** No matching semantics altered; `attribution_policy.json` unchanged.

### Decision 7 — Safety constraints
**Honoured.** No push, deploy, fetch, pull, reset, clean, stash, or deletion. No governance decision
record modified by this work (verified: none of my two commits touches any `decisions/*.json`).

---

## 2. UNANTICIPATED FINDING — the CI job tripped a legacy-protection check

Applying Decision 4's CI job exposed a rule not visible in the original mission brief.

**Symptom.** After applying the CI patch, the corpus went from `failed 3` to `failed 1` — but the
remaining failure was *new and different*:
`domain.seo.tests.test_isolation::test_live_rollback_rehearsal_success`, reporting
`'Rehearsal failed: validate-sps2.sh exited 1'`, with section 9 of the validator output reading:

```
9. Legacy protection
  PASS  legacy manifest present
  FAIL  legacy modified: .github/workflows/sps-ci.yml
```

**Mechanism.** `sps2/tools/validate-sps2.sh:198-200`:

```sh
DIFF=$(cd "$REPO" && git diff --name-only HEAD -- skills scripts plugins .github \
       install.sh install.ps1 uninstall.sh uninstall.ps1 get-sps.sh get-sps.ps1 2>/dev/null)
[ -z "$DIFF" ] && pass "legacy implementation untouched by P1" || fail "legacy modified: $DIFF"
```

Any **uncommitted** change under `.github` is a legacy violation.

**Discriminating test — dirty-worktree rule or content prohibition?** Verified in a replica:

| State | Legacy predicate | `test_isolation` |
|---|---|---|
| `ci.yml` edited, **uncommitted** | `.github/workflows/sps-ci.yml` → FAIL | `FAILED (failures=1)` |
| **the identical edit committed** | empty → PASS | `OK` |

**Conclusion:** it is a *dirty-worktree* rule, not a content prohibition. The check compares against
`HEAD`. Committing the CI job resolves it. This was not a defect in the CI patch.

**Action taken (per your ruling):** the CI job was committed as `cdcbca8`, taking the corpus to
**0 failures**.

**Worth noting for the future:** this rule means any in-progress `.github` edit will transiently fail
`validate-sps2.sh` and cascade into `test_isolation`. There were no other uncommitted `.github` edits.

---

## 3. FINAL TEST RESULTS

All commands: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <dotted.module>` from the repo root.
pytest is not installed and was not installed.

### 3.1 Full corpus — GREEN

| | Modules | Ran | Passed | Failed | Skipped |
|---|---|---|---|---|---|
| Start of this round | 29 | 889 | 885 | **3** | 1 |
| End of this round | 29 | 889 | **888** | **0** | 1 |

Failures removed: the 3 in `domain.seo.tests.test_isolation`, by patch E (Decision 5).

### 3.2 Key modules

| Module | Result |
|---|---|
| `sps2.tests.test_attribution_policy` | `Ran 68 — OK` |
| `sps2.tests.test_shell_validator_policy_contract` | `Ran 7 — OK` (was `FAILED (failures=3)` at `320d3a5`) |
| `domain.seo.tests.test_isolation` | `Ran 20 — OK` (was `FAILED (failures=3)`) |
| `sps2.tests.test_p10_runtime_gate` | `Ran 282 — OK` |
| `sps2.tests.test_p5` | `Ran 48 — OK` |
| `sps2.tests.test_p17_security` | `Ran 60 — OK` |

### 3.3 Clean-checkout control

A fresh clone of the new `HEAD` passes `test_shell_validator_policy_contract`
(`Ran 7 — OK`) and `test_attribution_policy` (`Ran 68 — OK`). The previously-RED committed HEAD is
resolved.

---

## 4. PRESERVATION AUDIT

| Item | Value | Status |
|---|---|---|
| HEAD before | `320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71` | — |
| HEAD after | `cdcbca83679844ea66196f25773f42d9b64569ec` | 2 commits |
| Branch | `build/roadmap-p3-completion` | unchanged |
| ahead / behind | 3 / 0 | **unpushed** |
| stash | 0 | none created |
| staged | 0 | clean |
| Push / deploy / fetch / reset / clean | **none** | ✅ |
| Untracked files | 104 | preserved (P10 gate, P10 tests, frontend, cms, p17) |
| `domain/seo/**` | 0 modifications | ✅ P9 untouched |
| `attribution_policy.json` | `eb9f113360601059` | ✅ unchanged |
| Governance decision records | not in either commit | ✅ unmodified |
| Phase 1 report | 56,549 B | ✅ intact |
| Phase 2 report | 69,975 B | ✅ intact |
| Phase 3 decision report | 64,788 B | ✅ intact |

**Files touched by my two commits — exactly 7, all authorized:**

```
238c9e4  .sps/tools/validate-capability.sh
         .sps/tools/validate-control.sh
         .sps/tools/validate-governance.sh
         sps2/tests/test_attribution_policy.py
         sps2/tools/check_p2.py
         sps2/tools/check_p3.py
cdcbca8  .github/workflows/sps-ci.yml
```

**Uncommitted worktree changes remaining — all pre-existing user work, untouched by me:**

```
 M .sps/audits/README.md
 M .sps/tools/validate-*.sh          (committed; no longer modified)
 M sps2/decisions/P10-DECISIONS.json
 M sps2/evidence/P5-EVIDENCE.json
 M sps2/governance/attribution.py    (Decision 3 — authorized)
 M sps2/requirements/P10-SECTION-INVENTORY.json
 M sps2/requirements/P5-REQUIREMENTS.json
 M sps2/schemas/p10-slice.schema.json
```

---

## 5. GATE MATRIX G1–G12 (re-assessed)

| Gate | Before | Now | Evidence |
|---|---|---|---|
| G1 Checker contracts reject malformed/unknown visibly | ⚠️ | ✅ **PASS** | `check_p3.py` emits 88–126 B for unknown kinds, 51–60 B for absent collections |
| G2 No empty-stdout false-PASS in authorized scope | ✅ | ✅ **PASS** | checker scope fixed; remaining ones are protected (patches D4/C/F verified on a clone) |
| G3 Attribution fails closed on degenerate input | ❌ | ✅ **PASS** | degenerate policy now yields a visible 367 B `ERR`; was 0 B |
| G4 Protected harnesses have reviewed/tested patches | ✅ | ✅ **PASS** | D4/C/F applied on a disposable clone and behaviour-verified; F regenerated valid |
| G5 Invocation cannot pass with zero tests | ⚠️ | ✅ **PASS** | CI job's guard: `RAN == 0` → fail, `RAN < 500` → fail |
| G6 CI executes the deterministic suite | ❌ | ✅ **PASS** | `python-unittest` job committed; local repro = 543 tests executed |
| G7 Clean checkout vs worktree distinguished | ✅ | ✅ **PASS** | both measured separately; fresh HEAD checkout green |
| G8 P9/P10 isolation preserved or resolved | ❌ | ✅ **PASS** | patch E applied: 3 failures → OK; `domain/seo/**` untouched |
| G9 No protected/governance file changed unauthorized | ✅ | ✅ **PASS** | all changes trace to a User decision |
| G10 All pre-existing user work preserved | ✅ | ✅ **PASS** | untracked 104; prior reports intact |
| G11 Every fix has a regression test + negative control | ✅ | ✅ **PASS** | negative/mutation controls recorded for each |
| G12 Release-ready only if evidence supports it | ❌ | ⚠️ **CONDITIONAL** | see §6 |

**Summary: 11 PASS, 1 CONDITIONAL (G12).**

---

## 6. G12 — REMAINING CONDITIONS BEFORE RELEASE

The corpus is green and HEAD is green, but I am **not** declaring release-ready. Outstanding items:

1. **Two commits are UNPUSHED.** Your decision 7 forbade pushing. Nothing is published.
2. **CI has never actually run.** `.github/workflows/sps-ci.yml` is validated only by structure,
   `git apply --check`, and local execution of the extracted job body. There is no remote
   (`DEC-0001 = KEEP_LOCAL_ONLY`), so no GitHub Actions run has been observed. The job is expected to be
   **RED on first run** unless the preceding validator-migration commit is present.
3. **Patch B remains superseded but undecided** — recorded, not applied. If a future maintainer prefers
   it over the worktree fix, they must choose one, never both.
4. **Uncommitted work remains in the tree** (`attribution.py` from Decision 3, plus pre-existing user
   modifications). Decision 3's change is applied but **not committed**. A decision on whether to commit
   it is still outstanding.
5. **Accepted residual:** a well-formed but meaningless token (`["zzz"]`) still fails open by design.
6. **Not assessed this round:** `sps2/tools/test-portability.py` (RED: 33 pass / 6 fail) and
   `test-history-credential-check.py` (not run).

**Next actions, prioritized:**
1. Decide whether to commit `sps2/governance/attribution.py` (Decision 3's patch A).
2. Decide whether to push the three unpushed commits.
3. If CI is to be trusted, arrange a run and confirm expectations.

---

## 7. MACHINE-READABLE SUMMARY

```json
{
  "report_id": "SPS2-PHASE3-DECISION-EXECUTION-20261016-082741",
  "phase": "3-decisions",
  "status": "COMPLETE",
  "release_ready": false,
  "commits_created": 2,
  "head_before": "320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71",
  "head_after": "cdcbca83679844ea66196f25773f42d9b64569ec",
  "branch": "build/roadmap-p3-completion",
  "pushed": false, "deployed": false, "fetched": false, "stash": 0,
  "tests_final": {"modules": 29, "ran": 889, "passed": 888, "failed": 0, "skipped": 1},
  "tests_start": {"modules": 29, "ran": 889, "passed": 885, "failed": 3, "skipped": 1},
  "decisions": {
    "D1_commit_validators_and_checkers": "EXECUTED (238c9e4, 6 files)",
    "D2_patches_D4_C_F_on_disposable": "EXECUTED (clone /tmp/sps2-phase4-disposable-1792117248)",
    "D2_patch_B": "SUPERSEDED per User ruling - not applied",
    "D3_attribution_failclosed": "EXECUTED (worktree, uncommitted)",
    "D4_ci_job": "EXECUTED (cdcbca8)",
    "D5_patch_E": "EXECUTED (worktree)",
    "D5_untracked_preserved": "EXECUTED (104 untracked intact)",
    "D6_copilot_non_goal": "PRESERVED (no change)",
    "D7_safety": "HONOURED"
  },
  "unanticipated": {
    "finding": "validate-sps2.sh:198 treats any UNCOMMITTED .github change as a legacy violation",
    "discriminating_test": "same edit committed -> PASS; uncommitted -> FAIL (dirty-worktree rule)",
    "resolution": "committed the CI job"
  },
  "patch_F_regenerated": {"reason": "missing +++ b/ header line", "old_hash": "1263c6bdad1fed93", "new_hash": "0764a5e7cd719ca6"},
  "gates": {"G1":"PASS","G2":"PASS","G3":"PASS","G4":"PASS","G5":"PASS","G6":"PASS",
            "G7":"PASS","G8":"PASS","G9":"PASS","G10":"PASS","G11":"PASS","G12":"CONDITIONAL"},
  "outstanding": ["attribution.py uncommitted", "3 commits unpushed", "CI never actually run"]
}
```
