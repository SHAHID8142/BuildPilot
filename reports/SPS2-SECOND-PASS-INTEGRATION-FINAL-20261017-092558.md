# SPS2 SECOND-PASS INTEGRATION AND REMEDIATION — FINAL REPORT

Report time: 2026-10-17T09:25:58+06 (suffix 20261017-092558)
Owner: Claude (independent integration engineer, second pass)
Branch: `build/roadmap-p3-completion` · HEAD at start and end: `c49f3852e1c31d0136269c80fe58201b059af3ec`
Inputs: Codex's handoff (`reports/SPS2-FINAL-IMPLEMENTATION-PASS-HANDOFF-20261017-083157.md`),
Codex's TODO ledger (`reports/SPS2-TECHNICAL-COMPLETION-MASTER-TODO-20261017-084925.md`),
my TODO ledger (`reports/SPS2-SECOND-PASS-TODO-LEDGER-20261017-084905.md`), the live tree.
Companion reports (never overwritten): independent review `…072036.md`, integration pass `…083701.md`, ledger `…084905.md`.

**Standing constraints honored for the whole session:** DEC-7301/7302/7303 treated as
UNAPPROVED throughout; the false Round 26 approval attribution was never relied on; the
subject decision record stayed byte-identical (`7c35617b…` re-verified at end of session);
the correction sidecar stayed byte-identical (`a50bfd25…`); no stage/commit/push/merge/
rebase/deploy/publish/release/CI change (0 staged, 0 stashed, HEAD unchanged); every
pre-existing modified/untracked file preserved (65 porcelain entries at end, all
pre-existing or mine, none deleted); no test, security control, validator, path
restriction, scanner rule, or gate semantic weakened — every change below *strengthens*
a check or is a pure observability/hardening fix.

---

## 1. TODO LEDGER — FINAL DISPOSITIONS

| ID | Task | Status | Evidence / rationale |
|---|---|---|---|
| C0-1 | Reconcile Codex's 08:31 report | DONE | Every number reproduced (1,041/2 tests; gate 9/5/2 exit 1; validators 78/4, 68/9, 66/10, 57/11, 43/1; mirrors identical; 614-file snapshot 0 mismatches). Its "25 untracked" claim was accurate for its 08:32 window (sidecar landed 08:35). |
| C0-2 | Codex TODO-ledger existence | DONE | Codex's ledger is report-only (`SPS2-TECHNICAL-COMPLETION-MASTER-TODO-20261017-084925.md`); my ledger is separate. |
| C1-1 | W1 updater/helper adversarial review | DONE | 15 findings (0 CRITICAL, 7 MEDIUM, 7 LOW, 1 INFO) — see §3. |
| C1-2 | W2 validators/P10/SEO adversarial review | DONE | 23 findings (6 HIGH, 10 MEDIUM, 5 LOW, 2 INFO) — see §3. |
| C1-3 | W3 test-contract adversarial review | DONE | 8 findings (1 CRITICAL, 1 HIGH, rest MEDIUM/LOW) — see §3. |
| C2-1 | Test enumeration / coverage split | DONE | 35 modules: 28 tracked (CI-covered) + 7 untracked; see §5. |
| C2-2 | Contract review, no test inversion | DONE | F-1 strengthened the rehearsal test (right-failure attribution); no test was weakened or inverted anywhere. |
| C3-1 | Integration/maintainability | DONE (analysis) | P9-REQUIREMENTS internal contradiction (line 351 vs 352) documented in §6 — fixing it requires a User requirements decision (BLOCKED). |
| C4-1 | W4 updater portability deep review | DONE | 12 findings (F-01..F-12) — see §3. |
| C5-1 | P10/SEO/rollback policy-neutral path analysis | DONE (answer: NO) | The dynamic import cannot be made policy-neutral: inline expansion of `audit.py` (1,319 lines importing `domain.seo.cwv`) just recreates the dependency; removal flips the gate's P9-audit control to permanent FAIL; adding the gate to the DEC-7302 manifest requires amending an UNAPPROVED decision. BLOCKED on User decision. |
| C6-1 | Governance/provenance sweep | DONE | All 33 DEC-73xx-referencing files enumerated; new "authorized by DEC-7301"/"approved by DEC-7302" wording in 5 normative docs (P7/P9 threat models, P3/P9/P10 requirements) confirmed to be **concurrent-agent additions absent at HEAD** — treating UNAPPROVED decisions as authoritative in normative docs contradicts the sidecar; left untouched (editing them is a governance act), recorded as an open User item. |
| C7-1 | Integrate safe fixes | DONE | 19 fixes applied sequentially, each tested (§2). |
| C7-2 | Final offline matrix + delta explanation | DONE | 1,057/0/2 vs Codex 1,041/2; every delta explained (§5). |
| C7-3 | This report | DONE | This file; no prior report touched. |

## 2. FIXES APPLIED THIS SESSION (all sequential, each verified)

| # | Finding | Fix | Files | Verification |
|---|---|---|---|---|
| 1 | W4 F-01/F-02 | Atomic `write_state` (mktemp+rename); base-10 `CHECKED_AT` arithmetic | `scripts/check-update.sh` + mirror | `test_check_update_safety`+`test_updater_safety` 40 OK (1 skip) |
| 2 | W4 F-01/F-05/F-06 | Atomic `Write-State`; TLS 1.2 pin; `Test-GreaterVersion` local-ahead branch | `scripts/check-update.ps1` + mirror | same suites OK; `cmp` mirrors identical |
| 3 | W3 F-4 | Scanner catches bare `import_module(...)` rebinding; any string concat in dynamic-import args fails closed | `sps2/governance/import_exceptions.py` | both evasion shapes caught, benign clean; 48 OK |
| 4 | W3 F-6 | Positive control: both validators accept historical `D-P10-1` id, clean stdout | `sps2/tests/test_round26_governance_contracts.py` | 29 OK |
| 5 | W3 F-5 | **Both checkers** guard the `decision_identifiers` import (controlled `ERR\t` line instead of traceback+empty stdout); negative-control test deletes the module in a sandbox and asserts visible ERR | `sps2/tools/check_sps2.py`, `sps2/tools/check_p3.py`, tests | round26+attribution 98 OK; live records still pass clean |
| 6 | W3 F-1 | `execute_rehearsal` propagates `rb_msgs` on rollback failure; rehearsal test now requires the block to name the declared violation (`p10_runtime_gate.py` dynamic import) — a wrong-reason failure no longer satisfies the contract | `sps2/tools/rollback_seo.py`, `domain/seo/tests/test_isolation.py` | isolation 20 OK |
| 7 | W1 F-8 / W1 F-1 | Version components capped at 9 digits (both platforms) — 64-bit arithmetic wrap could invert comparison; ANY future `CHECKED_AT` now rejected (future value up to now+TTL extended cache authority to ~2×TTL) | `scripts/check-update.sh`, `scripts/check-update.ps1` + mirrors | functional smoke: future timestamp → cache ignored; fresh cache honored; mirrors `cmp`-identical; `bash -n` OK |
| 8 | W1 F-5 | Scanner catches ANY `.import_module(...)` attribute call (aliased `importlib as il` evasion demonstrated by W1) | `sps2/governance/import_exceptions.py` | evasion caught, benign clean; +1 regression test |
| 9 | W1 F-6 | Relative imports resolved against the file's package (`climb = level-1`) and run through the same allowlist; escaping relative imports fail closed (was: `if node.level: continue` — total bypass) | `sps2/governance/import_exceptions.py` | resolution verified (`from ..seo.metadata` → `domain.seo.metadata` → flagged); +2 regression tests; live 8 approved imports intact |
| 10 | W1 F-7 | `handoff`/`action` records get the same duplicate-ID guard the other four kinds have | `sps2/tools/check_sps2.py` | dup fixtures flagged (`ERR duplicate handoff/action IDs`); +1 regression test; live records clean |
| 11 | W2 P5-1 | **Revived a dead control**: s9 in validate-p5.py computed approval-attribution problems and never reported them. Now reports. Its stale probe list included `"self"`, which the authoritative `attribution_policy.json` deliberately EXCLUDES (DEC-0027, "Self" is a real surname) — probe list aligned to the ratified policy, not the policy to the probe | `sps2/tools/validate-p5.py` | P5 43/1 → **44/1** (+1 real pass, same single pre-existing failure) |
| 12 | W2 SPS2-1 | `p17` added to required directories — previously `rm -r sps2/p17` skipped 4 security suites with WARN-only and exited 0 | `sps2/tools/validate-sps2.sh` | sandbox-verified: deleted `p17` → `FAIL missing dir p17`; live: 79/4 |
| 13 | W2 P4-1 | N18 negative case was a **tautology** (second disjunct re-read the fixture we just built — could never fail). Now requires the checker's own `DUPLICATE` output, run through `check_p3.py registry` (the actual registry-level duplicate control; `check_p4.py` is single-capability and has none) | `sps2/tools/validate-p4.sh` | P4 57/11 with `0 missed` (was 57/11 with **1 missed** — the tautology was masking that no checker could satisfy the case) |
| 14 | W2 P5-2 | Negative-suite cases that RAISE are now scored as missed with the exception reported (was: silently scored as rejected) | `sps2/tools/validate-p5.py` | P5 44/1, negative suite all genuinely rejected |
| 15 | W2 P5-3 | s7 determinism requires rc==0 and non-empty output (3 identical crashes no longer "byte-identical PASS"); s8 requires ≥1 collected test ("Ran 0 tests" no longer passes) | `sps2/tools/validate-p5.py` | 48 unit tests reported, PASS genuine |
| 16 | W2 RB-1/RB-4 | `restore_snapshot` now verifies each file's sha256 against the manifest, enforces path containment (absolute/`..`/realpath-escape rejected), fails on missing files and on `file_count` mismatch (was: silent partial restore with exit 0, no digest, no containment); snapshot timestamp is real UTC (was hardcoded `2026-10-07`) | `sps2/tools/rollback_seo.py` | +3 negative tests (digest mismatch, path escape, truncation all fail); restoration round-trip still OK; isolation 23 OK |
| 17 | W2 RB-3 | Rehearsal proof obligations are now REQUIRED: a missing `validate-sps2.sh`, `domain/cms/tests`, or `validate-p7-readiness.py` in the clone fails the rehearsal (was: skipped, still "SUCCESS"); removed the hardcoded "(72 checks passed)" claim | `sps2/tools/rollback_seo.py` | isolation 23 OK |
| 18 | W2 GATE-2/GATE-3/GATE-5 | Gate sys.path: repo root inserted at position 1 (appended entry let a planted `sps2/tools/domain/` shadow authoritative modules); fresh-act basis check uses word-boundary `\bfresh\b` ("refresh the cache" no longer satisfies it); slice-id history coerces non-string entries instead of silently dropping them | `sps2/tools/p10_runtime_gate.py` | gate suite 320 OK |
| 19 | W2 SPS2-2 + SPS2-4 | All four P17 suite gates require ≥1 collected test ("Ran 0 tests" no longer passes); unreachable trailing line after `exit 1` removed from validate-p2.sh | `sps2/tools/validate-sps2.sh`, `sps2/tools/validate-p2.sh` | suite counts now real (65/44/2/25); P2 unchanged 68/9 |

Line-number pin updates (not weakenings): the isolation tests pin the gate's dynamic
import at `p10_runtime_gate.py:1941`; the sys.path fix's docstring shifted it to 1944 —
the pins were updated to 1944, preserving the exact-string single-violation contract.
`VALID_VERSION` in `test_check_update_safety.py` updated to the capped regex (same
validation intent, hardened form).

## 3. SUBAGENT FINDINGS — FULL DISPOSITION

### W1 (updater/helpers) — 15 findings
- **F-1** future-CHECKED_AT cache freeze — **FIXED** (#7)
- **F-2** uninstall.sh/ps1 manifest-controlled `rm -rf` traversal — **BLOCKED (policy)**: `uninstall.sh`/`install.sh` are inside the legacy pathspec and currently baseline-clean; editing them would create NEW legacy-diff validator failures, i.e. worsen the legacy-diff-zero contract that depends on UNAPPROVED DEC-7301 semantics. Requires User authorization to edit legacy paths.
- **F-3** install.sh `StrictHostKeyChecking=no` — **BLOCKED (policy, same reason as F-2)**
- **F-4** install.sh destroys live /sps mirror before copy — **BLOCKED (policy, same reason)**
- **F-5** aliased importlib evasion — **FIXED** (#8)
- **F-6** relative-import bypass — **FIXED** (#9)
- **F-7** handoff/action dup IDs — **FIXED** (#10)
- **F-8** semver overflow — **FIXED** (#7)
- **F-9** legacy_exceptions TOCTOU — **NOT DONE (accepted residual)**: content pins neutralize it (a swap only passes if byte-identical); O_NOFOLLOW rework is churn against a hash-verified module with no demonstrated exploit. Documented for a future round.
- **F-10** CLI `--baseline` never cross-checked against manifest `baseline_commit` — **BLOCKED (policy)**: which baseline is canonical is a governance call (validators deliberately use two: c11da27 vs c49f3852).
- **F-11/F-12/F-13/F-14** install/update script robustness — **BLOCKED (policy, legacy pathspec)** for install.sh items; F-13/F-14 (update-sps.ps1/install.ps1, both DEC-7301-pinned) — **BLOCKED (pin)**.
- **F-15** updater executes previously-fetched checker — **INFO, verified fail-closed** (test-covered; no hidden network fallback anywhere).

### W2 (validators/P10/SEO) — 23 findings
- **RB-1** restore_snapshot — **FIXED** (#16)
- **GATE-1** the dynamic import / permanently-false zero-orphan invariant — **BLOCKED (policy)**: resolution requires either amending UNAPPROVED DEC-7302 (add gate to manifest) or removing the import (changes gate behavior). This is exactly the C5-1 question; answer: no policy-neutral path exists. The test does NOT pin a violation as "good" — it pins that the block is *visible and exact*, which is the fail-closed direction.
- **P5-1** — **FIXED** (#11). **P4-1** — **FIXED** (#13). **SPS2-1** — **FIXED** (#12).
- **P4-2** validate-p4.sh flags existing `sps2/memory`/`isolation_validator.py` — **BLOCKED (policy)**: which side (P4 invariant vs P5 whitelist) is authoritative is a governance call; note P4 currently reports these among its 11 baseline failures.
- **GATE-2/GATE-3/GATE-5** — **FIXED** (#18)
- **GATE-4** audit TOCTOU / digest never compared — **NOT DONE**: fix requires re-walking the build dir and comparing digests inside the gate; the change touches the gate's P9-audit control semantics mid-control. Documented; recommend next round with an explicit test.
- **RB-2** execute_rollback partial-failure handling — **NOT DONE (deferred)**: hardening unlink error paths changes rollback failure semantics mid-loop; the snapshot exists and rehearsal exercises the happy path. Documented.
- **RB-3** — **FIXED** (#17). **RB-4** — **FIXED** (#16).
- **P5-2/P5-3** — **FIXED** (#14/#15). **P5-4** validator writes probe into governed tree — **NOT DONE (deferred)**: moving the probe to a temp copy changes what s2 verifies (real core/ vs copy). Documented.
- **SPS2-2** — **FIXED** (#19). **SPS2-3** `--exclude-dir=tools` over-match — **NOT DONE (LOW, documented)**. **SPS2-4** — **FIXED** (#19).
- **P3-1/P3-2** LOW validator gaps — **NOT DONE (LOW, documented)**.
- **ISO-1** narrowed signatures with no live caller — **INFO, verified**: no caller passes the dropped parameters; documented.
- **GATE-6** whole-file slurp — **NOT DONE (LOW, documented)**.

### W3 (test contracts) — 8 findings
- **F-1** CRITICAL rehearsal attribution — **FIXED** (#6)
- **F-2** re-baselined orphan contract — **BLOCKED (policy)**: entangled with DEC-7301's legacy-diff exception.
- **F-3** `explicitly_excluded_paths` dead data in manifest vs `verify_legacy_diff_zero` wiring — **BLOCKED (policy)**: wiring the exclusions = ratifying DEC-7301 behavior.
- **F-4** dynamic-import evasion shapes — **FIXED** (#3, #8)
- **F-5** unguarded decision_identifiers import — **FIXED** (#5)
- **F-6** D-P positive unpinned — **FIXED** (#4)
- **F-7** PS coverage skip-gated — **INFO**: documented (PowerShell not executable in this environment).
- **F-8** gate-vs-scanner tension — **BLOCKED (policy)** = GATE-1.

## 4. CODE DEFECT vs POLICY BLOCKER vs BASELINE vs MISSING PREREQUISITE

- **Code defects fixed this session (19)**: listed in §2 — all were real defects (dead controls, tautological tests, evasions, missing guards); none required a governance decision to fix because each fix *strengthens* an existing check without changing what any decision says.
- **Policy blockers (remain, correctly)**: GATE-1/C5-1 (dynamic import), F-2/F-3/F-4/F-11/F-12 (legacy-path edits), F-10 (baseline canonicality), P4-2 (which invariant is authoritative), F-2-W3/F-3-W3 (DEC-7301-entangled), C6-1's "authorized by DEC-73xx" wording in normative docs (5 files, concurrent-agent additions — a User decision is needed on whether normative docs may cite UNAPPROVED decisions as authoritative).
- **Baseline failures (unchanged, not regressions)**: the 4 validate-sps2 failures (check-update mirrors — disputed governance), 9 validate-p2, 10 validate-p3, 11 validate-p4 (incl. P4-2's memory/isolation_validator flags), 1 validate-p5 (legacy protection, now listing 9 paths), P10 gate 12/16 required controls FAIL, exit 1. All pre-date this session; all trace to the UNAPPROVED status of DEC-7301/7302 or to the unapproved dynamic import.
- **Missing prerequisites**: CI covers only the 28 tracked modules; the 7 untracked test modules (468+ tests) run locally but not in CI — changing CI is not authorized, so this remains a coverage limitation, not a completed state.

## 5. FINAL OFFLINE MATRIX — EXACT NUMBERS AND DELTAS

- **Full test matrix**: 35 modules, `PYTHONPATH=. python3 -m unittest …` → **Ran 1057 tests, OK (skipped=2)**. Codex baseline: 1,041 run, 2 failures, 2 skips. Delta: **+16 run, −2 failures, same 2 skips**.
  - +8 `test_check_update_safety` (19→27): concurrent agent's cache-safety additions (all pass against my script changes).
  - +2 `test_round26_governance_contracts` (28→30 at first matrix) then +2 more (30→32: aliased-importlib + relative-import regression tests), +1 dup-ID test (33), +1 missing-module negative control was already counted — final count 33.
  - +3 `test_isolation` (20→23): the three restore_snapshot negative tests.
  - −2 failures: the two isolation tests that pinned line 1941 now pin 1944 (updated, not weakened); the PS regex pin updated to the capped pattern.
  - Net: 1,041 + 8 + 2 + 2 + 1 + 3 = 1,057, zero failures.
- **Validators** (final): validate-sps2 **79/4** (baseline 78/4: +1 from the new `dir p17` check), validate-p2 **68/9** (unchanged), validate-p3 **66/10** (unchanged), validate-p4 **57/11 with 0 missed** (baseline 57/11 with 1 missed — N18 is now a real control), validate-p5 **44/1** (baseline 43/1: +1 from revived s9).
- **P10 gate**: exit 1, 4 PASS / 12 FAIL of 16 required controls, 0 integrity problems — identical to baseline.
- **Mirrors**: `scripts/check-update.{sh,ps1}` byte-identical to `skills/sps/scripts/` mirrors (`cmp` clean).
- **`bash -n`**: all 7 bash scripts clean.
- **Legacy exception pins**: all 8 pinned files verified, 0 violations; 614-file snapshot verified earlier this session (0 mismatches).
- **Protected hashes**: subject record `7c35617b…`, sidecar `a50bfd25…` — byte-identical at end of session.
- **Git**: HEAD `c49f3852…` unchanged, 0 staged, 0 stashes, 65 porcelain entries (pre-existing modifications/untracked preserved; my changes are additional modifications to already-modified files plus new untracked test content inside existing untracked paths).

## 6. OPEN USER DECISIONS (unchanged, plus new)

1. DEC-7301/7302/7303 approval (still UNAPPROVED; nothing this session implies otherwise).
2. GATE-1/C5-1: the P10 gate's dynamic `domain.seo.audit` import — amend DEC-7302, remove the import, or restructure the gate. No policy-neutral option exists (verified: inline expansion recreates the dependency; removal flips the P9-audit control).
3. C6-1 NEW: five normative docs (P7/P9 threat models, P3/P9/P10 requirements) now contain concurrent-agent wording citing DEC-7301/7302 as "authorized"/"approved" — wording absent at HEAD and inconsistent with the correction sidecar. A User decision is needed on whether to revert that wording or ratify the decisions.
4. P9-REQUIREMENTS internal contradiction: line 351 ("no longer guaranteed buildable") vs line 352 ("Rollback rehearsal proves deletion of domain/seo/ leaves core validators passing") — pre-existing at HEAD, needs a requirements decision.
5. W1 F-2/F-3/F-4: uninstall traversal, SSH host-key checking, non-atomic mirror sync in install.sh/uninstall.sh — all real, all inside the legacy pathspec; need User authorization to edit legacy paths.

## 7. QA HANDOFF CHECKLIST

- [x] Full 35-module offline matrix: 1,057 tests, 0 failures, 2 skips (`PYTHONPATH=. python3 -m unittest $(cat /tmp/sps2_modules.txt | tr '\n' ' ')`)
- [x] All five validators at documented counts (79/4, 68/9, 66/10, 57/11+0-missed, 44/1); every failure traced to a known policy blocker or baseline item
- [x] P10 runtime gate exit 1 (4/16 PASS) — expected while the dynamic import is unresolved
- [x] Mirrors byte-identical; `bash -n` clean on all 7 bash scripts
- [x] 8 legacy pins verified (0 violations); manifests hash-verified
- [x] Subject decision record and correction sidecar byte-identical
- [x] No staging, no commits, no stashes, HEAD unchanged, all pre-existing files preserved
- [x] DEC-7301/7302/7303 remain UNAPPROVED; no approval fabricated anywhere; every new test asserts fail-closed behavior
- [ ] CI coverage of the 7 untracked test modules — requires a CI change (not authorized this session)
- [ ] All §6 User decisions

**Verdict: the second-pass integration mission is complete.** All safely implementable work
identified by four adversarial reviews has been implemented and verified (19 fixes, +16
tests, +3 real validator controls, 2 tautologies/dead controls eliminated). The repository
is NOT release-ready and must not be represented as such: the P10 gate still fails on the
unapproved dynamic import, the four disputed-governance validator failures persist by
design, and every item in §6 requires a genuine User decision.
