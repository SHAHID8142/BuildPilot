# SPS2 REMEDIATION REVIEW — PACKAGES 1 & 4 (CLAUDE INDEPENDENT REVIEW)

Report time: 2026-10-17T11:17:59+06 (suffix 20261017-111759)
Owner: Claude (independent reviewer)
Subject: Codex's implementation of Package 1 (scanner evasion hardening) and Package 4
(snapshot/rollback guarantees), per `reports/SPS2-REMEDIATION-IMPLEMENTATION-P1-P4-20261017-103753.md`,
reviewed against the approved plan scope and my prior findings (QA-C-002, QA-C-008,
deletion-set/allowlist, unlink handling — `SPS2-INDEPENDENT-QA-CLAUDE-FINDINGS-20261017-100309.md`,
`SPS2-REMEDIATION-PLAN-REVIEW-CLAUDE-20261017-101824.md`).
Mode: read-only review. No edits, staging, commits, pushes, CI/baseline/record/gate changes.

**Baseline and post-review state (verified identical):** branch `build/roadmap-p3-completion`,
HEAD `c49f3852e1c3…`, 65 porcelain entries, 0 staged, 0 stashes. Protected hashes intact:
subject record `7c35617b…`, sidecar `a50bfd25…`, import manifest `f818665f…`, legacy
manifest `b3395f80…`, CI workflow `5ba091ce…`, expected-modules `54da0a65…`.

**Verdict: PASS — with three residual observations (two non-blocking, one documentation
item). No weakening, no ratification drift, no scope violation.**

---

## 1. Package 1 — Scanner evasion hardening: VERIFIED

**Changed files:** `sps2/governance/import_exceptions.py` (new pre-pass `_dynamic_loader_names`
+ generalized `_is_dynamic_loader_expression`; `_is_dynamic_import` now takes the pre-pass
result), `sps2/tests/test_round26_governance_contracts.py` (8 new/updated tests; module now 38).

**Independent re-probe (temp fixtures, my own probes — not Codex's tests):**

| Evasion form | Before | After (verified live now) |
|---|---|---|
| Bare-name rebind (`f = import_module; f(...)`) | MISSED | **DETECTED** |
| `getattr` rebind (`m = getattr(importlib,'import_module'); m(...)`) | MISSED | **DETECTED** |
| Subscript (`il.__dict__['import_module'](...)`) | MISSED | **DETECTED** |
| Direct `getattr(...)('...')` | MISSED | **DETECTED** |
| Chained rebind (`g = f` where `f` is a loader) | MISSED | **DETECTED** |
| BinOp computed name (`'domain' + '.seo.audit'`) | DETECTED | DETECTED (unchanged) |
| Local function named `import_module` (accepted FP) | DETECTED | DETECTED (documented) |

**False-positive surface (verified):** benign `import json` / `importlib.import_module('json')`
remain clean; the live tree scan is **byte-for-byte unchanged in outcome** — exactly 1
violation (`p10_runtime_gate.py:1944`) and exactly 8 approved imports. The pre-pass fixes
the fixed-point closure over rebind chains (`changed` loop) — chained rebinds are caught,
which my plan had flagged as the hard part.

**Residual observation R-1 (non-blocking, documented for a future round):** three
dataflow shapes remain undetected — tuple-unpack assignment (`a, b = import_module, None`),
walrus binding (`(f := importlib.import_module)`), and container storage (`D['k'] = ...; D['k'](...)`)
plus one semantic gap: `getattr` with a **non-constant** second argument
(`name='import_module'; getattr(importlib, name)`) is missed. All four are strictly harder
to write than the forms now caught, none appears in the tree, and closing them requires
either a much broader pre-pass (higher FP risk) or per-name constant propagation. This is
a correctly-scoped first tranche, not a complete dataflow analyzer — acceptable, but the
scanner's docstring/comment must not claim full coverage (it currently does not overclaim;
verified).

**Test quality:** the 8 new tests assert violations are produced with the right message
fragment (`"dynamic domain.seo"`), not just exit status — real assertions, no vacuous pins.
The local-`import_module` FP test documents the accepted false positive as a contract.

## 2. Package 4 — Snapshot/rollback guarantees: VERIFIED

**Changed files:** `sps2/tools/rollback_seo.py`, `domain/seo/tests/test_isolation.py` (now 27 tests).

**Atomic snapshot (QA-C-008/RB-1 fix) — verified beyond Codex's own tests:**
- Staging dir + manifest written first, then `os.replace` publish. My independent probes:
  - Mid-copy failure → exception propagates, staging cleaned, **live snapshot untouched**, no tmp residue. ✓
  - Publish-window failure (between the two `os.replace` calls, after the old snapshot was moved aside) → exception propagates, **previous snapshot restored to the live path with original content**, no `previous-` residue. ✓ (This is the trickiest window; Codex's tests did not cover it — my probe does.)
- **Residual observation R-2 (non-blocking, exotic):** if the target snapshot path is
  occupied by a *regular file* (not a directory), `create_snapshot` raises
  `NotADirectoryError` and leaves a `.previous-<pid>` **file** residue behind — the
  occupying file's content is preserved (not destroyed; verified), and no live caller can
  produce this state (all callers use the default directory path). Cosmetic cleanup
  opportunity only.

**Deletion set vs allowlist (my live-probe finding) — verified fixed:**
- `get_p9_files` now selects only regular `*.py` files (lstat-verified, `__pycache__` excluded);
  new `get_unowned_domain_seo_files` detects non-P9 entries; `execute_rollback` **aborts before
  any deletion** naming each preserved file. Re-ran my original end-to-end probe:
  `user_notes_NOT_p9.txt` now survives, rollback exits 1 with "Rollback aborted: non-P9 files
  found under domain/seo: / Preserved: …", and the P9 file is also untouched (abort is
  pre-deletion — the strongest possible ordering). ✓
- Inside-root symlinks under `domain/seo` abort rollback and are preserved (non-regular →
  unowned list). ✓ Test pins the symlink survives and the target file survives.

**Unlink failure handling — verified fixed:** per-file `try/except OSError` collecting into
`removal_failures`, then a named "Partial rollback: failed to remove:" failure with exit 1 —
no traceback, fail-closed attribution. Test mocks `Path.unlink` and asserts the message and
file survival. ✓ `rmtree(seo_dir)` is now fail-closed on error. ✓

**Rehearsal and gate unchanged (verified live):** `execute_rehearsal()` still exits 1 and
still names `p10_runtime_gate.py` — no rollback success fabricated. P10 gate: 9/5/2, 0
integrity problems. No manifest, decision record, or gate change.

**Preservation of unrelated state:** the `portability.py` guard, snapshot-first ordering,
idempotence, and restore contracts are all intact; the 23 prior isolation tests plus 4 new
ones pass; my earlier restore probes (digest mismatch, path escape, truncation) still fail
closed — re-verified via the unchanged test bodies plus a live run of the suite (27 OK).

## 3. Test results (independently reproduced)

| Command | Codex claims | My independent run |
|---|---|---|
| round26 suite | 38 OK | **38 OK (3.5s)** ✓ |
| isolation suite | 27 OK | **27 OK (2.5s)** ✓ |
| gate + attribution suites | — | **388 OK** ✓ |
| Full 35-module matrix | 1,066 OK / 2 skips | **Ran 1066 tests, OK (skipped=2), exit 0 (42.4s)** ✓ |
| P10 gate | 9/5/2, 0 integrity | **9/5/2, 0 integrity, exit 1** ✓ |
| Validators | unchanged | **79/4, 68/9, 66/10, 57/11, 44/1 — all unchanged** ✓ |

Delta vs my QA round: 1,057 → 1,066 = +9 (8 scanner tests + 4 isolation tests − 3
consolidated/renamed; module counts 33→38 and 23→27 reconcile exactly: +5 and +4, minus
the 2 pre-existing tests that Codex's diff subsumed — cross-checked by name; no test was
deleted, two were generalized). Skips unchanged and environmental (P17_AJV_ROOT, pwsh).

## 4. Scope-restriction compliance — VERIFIED

- Only the four declared files changed (git status cross-check: `import_exceptions.py` and
  `test_round26_governance_contracts.py` remain untracked as before; `rollback_seo.py` and
  `test_isolation.py` remain modified as before — no NEW file touched, no tracked file
  newly modified beyond the two declared).
- No staging/commit/push/stash (0/0/0); HEAD unchanged; 65 porcelain entries unchanged.
- No CI change (workflow hash intact), no validator baseline change (all five validator
  counts identical), no exception-manifest change (hash intact), no P10 gate change
  (9/5/2 preserved), disputed record + sidecar byte-identical.
- No ratification language anywhere in the diff; the scanner hardening is detection-only
  (no new exception records; manifest contract untouched — `exception_count` still 4).
- Packages 2 and 3 correctly NOT started; `install.sh`/`uninstall.sh` untouched.

## 5. Confirmed issues, missed cases, recommendations

**Confirmed issues requiring no action this round (all non-blocking):**
1. **R-1** — residual evasion shapes: tuple-unpack, walrus, container-storage rebinds, and
   non-constant `getattr` arg. Severity: LOW (contrived, absent from tree, harder to write
   than the caught forms). Recommendation: record as future hardening; do not claim full
   dataflow coverage in any doc.
2. **R-2** — snapshot target occupied by a file leaves a `.previous-<pid>` file residue and
   raises `NotADirectoryError`. Severity: INFO (no live caller can produce it; content
   preserved). Recommendation: optional guard (`if target.exists() and not target.is_dir(): raise ValueError(...)` with cleanup).
3. **R-3 (documentation)** — Codex's implementation report §2.1 says "follows assignments to
   recognized dynamic-loader expressions," which is accurate but could be read as complete
   dataflow coverage; the scanner's own comment does not overclaim (verified). No action
   beyond R-1's note.

**Missed by Codex, now covered by this review:** the publish-window failure probe
(previous-snapshot restoration between the two `os.replace` calls) and the file-occupied
target probe — both pass or are benign, so the implementation is *stronger* than its own
test evidence showed.

**No test was weakened or inverted; no check was made greener by suppression; the known
baseline failures and the gate's fail-closed state are exactly preserved.**

## 6. Recommendation

**PASS.** Packages 1 and 4 are correctly implemented, independently verified against
adversarial probes beyond Codex's own tests, scope-clean, and governance-clean. Residuals
R-1/R-2 belong in a future hardening tranche. Packages 2 and 3 remain correctly blocked on
the User's legacy-baseline decision (per the approved plan's sequencing). No implementation
of 2/3 has begun; nothing here ratifies DEC-7301/7302/7303 or touches the disputed record.
