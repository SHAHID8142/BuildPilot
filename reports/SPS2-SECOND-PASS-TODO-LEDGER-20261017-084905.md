# SPS2 SECOND-PASS INTEGRATION — TODO LEDGER (PLANNING)

Ledger time: 2026-10-17T08:49:05+06 planning window (suffix 20261017-084905)
Owner: Claude (independent integration engineer, second pass)
Status: **COMPLETE — final dispositions in
`reports/SPS2-SECOND-PASS-INTEGRATION-FINAL-20261017-092558.md` (authoritative
for statuses, evidence, and the full execution log).**

Inputs read: Codex's latest report
`reports/SPS2-FINAL-IMPLEMENTATION-PASS-HANDOFF-20261017-083157.md`
(no separate TODO ledger file exists anywhere in the tree — recorded as a
C0 finding), the master mission package, the 07:10 self-verification, my
own review and first-pass integration reports, and the live tree.

**Standing constraints honored:** DEC-7301/7302/7303 UNAPPROVED; subject
record hash `7c35617b…` and sidecar `a50bfd25…` verified this session;
no stage/commit/push/merge/deploy/publish/release/CI change; no policy
resolution by silent choice.

## Workstreams

| ID | Task | Priority | Risk | Dependencies | Acceptance criteria | Status |
|---|---|---|---|---|---|---|
| C0-1 | Reconcile Codex's 08:31 report claims (inventories, counts, hashes) against live tree | P0 | Low | — | Every claim checked; inaccuracies listed | DONE |
| C0-2 | Confirm "no separate TODO ledger exists" (Codex output is report-only) | P1 | Low | — | Ledger absence verified and recorded | DONE |
| C1-1 | Adversarial review: updater/installer/manifests/decision helpers (subagent W1) | P0 | Medium | C0-1 | Findings classified by severity w/ evidence | DONE (15 findings) |
| C1-2 | Adversarial review: validators + P10 gate + SEO/rollback (subagent W2) | P0 | Medium | C0-1 | Findings classified by severity w/ evidence | DONE (23 findings) |
| C1-3 | Adversarial review: test infrastructure — tests that pass without exercising intent (subagent W3) | P0 | Medium | C0-1 | Findings classified by severity w/ evidence | DONE (8 findings) |
| C2-1 | Independent test enumeration: tracked/untracked, skips, coverage gaps vs CI manifest | P0 | Low | C0-1 | Precise module/coverage table | DONE (35 modules: 28 tracked + 7 untracked) |
| C2-2 | Contract review: rollback rehearsal + disputed-governance test semantics; no test inversion | P0 | Medium | C1-3 | Contract fidelity documented; risks listed | DONE |
| C3-1 | Integration/maintainability: duplicate helpers, API mismatches, stale docs, import boundaries | P1 | Medium | C1-* | Safe fixes applied or documented | DONE (P9-REQUIREMENTS L351/352 contradiction documented — User decision) |
| C4-1 | Updater/installer/portability deep review incl. cache safety, TOCTOU, path validation (subagent W4) | P0 | Medium | C0-1 | Findings w/ evidence; mirrors/pins verified | DONE (12 findings F-01..F-12) |
| C5-1 | P10/SEO/rollback dependency analysis: is a policy-neutral path for the dynamic import possible? | P0 | Medium | C1-2 | Verified analysis + minimal reproduction + options | DONE (answer: NO policy-neutral path exists) |
| C6-1 | Governance/provenance sweep: sidecar, hash, all DEC-73xx references, false-attribution search | P0 | Low | C0-1 | All references truthful; anomalies listed | DONE (5 normative docs cite DEC-73xx as authorized — concurrent-agent additions; open User item) |
| C7-1 | Integrate safe fixes from C1–C6 findings, sequentially, testing each | P0 | Medium | C1–C6 | Every patch reviewed + focused tests green | DONE (19 fixes) |
| C7-2 | Final full offline matrix + validators; delta vs Codex baseline explained | P0 | Low | C7-1 | Exact numbers; every delta explained | DONE (1,057 OK / 0 fail / 2 skip; validators 79/4, 68/9, 66/10, 57/11+0-missed, 44/1; all deltas explained) |
| C7-3 | Final timestamped integration report + QA handoff checklist | P0 | Low | C7-2 | Report created; no prior report overwritten | DONE (`SPS2-SECOND-PASS-INTEGRATION-FINAL-20261017-092558.md`) |

## Execution log (safe fixes applied this session, sequential, each tested)

| # | Fix | Files | Tests after |
|---|---|---|---|
| 1 | F-01/F-02: atomic `write_state` (temp+rename), base-10 `CHECKED_AT` guard | `scripts/check-update.sh` + mirror | `test_check_update_safety` + `test_updater_safety` → 40 OK (1 skip) |
| 2 | F-01-PS/F-05/F-06: atomic `Write-State`, TLS 1.2 pin, `Test-GreaterVersion` local-ahead branch | `scripts/check-update.ps1` + mirror | same suite → OK; mirrors `cmp`-identical; `bash -n` n/a (PS) |
| 3 | F-4: scanner catches `from importlib import import_module` rebinding + any BinOp in dynamic-import args (fail-closed on computed module names) | `sps2/governance/import_exceptions.py` | both evasion shapes caught, benign clean; round26+isolation → 48 OK |
| 4 | F-6: positive control — both validators accept historical `D-P10-1` id with clean stdout | `sps2/tests/test_round26_governance_contracts.py` | round26 → 29 OK |
| 5 | F-5: guard `decision_identifiers` import in BOTH checkers (controlled `ERR\t` line instead of traceback+empty stdout); negative-control test deletes the module in a sandbox and asserts visible ERR | `sps2/tools/check_sps2.py`, `sps2/tools/check_p3.py`, test file | round26+attribution → 98 OK; live records still clean (rc=0, empty stdout) |
| 6 | F-1: `execute_rehearsal` propagates `rb_msgs` on rollback failure (attribution, not contract change); rehearsal test now requires the block to name the declared violation (`p10_runtime_gate.py` dynamic import) | `sps2/tools/rollback_seo.py`, `domain/seo/tests/test_isolation.py` | isolation → 20 OK |
| 7 | W1 F-8/F-1: version components capped at 9 digits (both platforms, overflow could invert comparison); ANY future `CHECKED_AT` rejected (was: values up to now+TTL accepted, extending cache authority ~2×TTL) | `scripts/check-update.sh`, `scripts/check-update.ps1` + mirrors | functional smoke OK (future rejected, fresh honored); mirrors `cmp`-identical |
| 8 | W1 F-5: scanner flags ANY `.import_module(...)` attribute call (aliased `importlib as il` evasion) | `sps2/governance/import_exceptions.py` | evasion caught; +1 regression test |
| 9 | W1 F-6: relative imports resolved (`climb = level-1`) and run through the allowlist; escaping relative imports fail closed (was: total bypass) | `sps2/governance/import_exceptions.py` | +2 regression tests; live 8 approved imports intact |
| 10 | W1 F-7: `handoff`/`action` duplicate-ID guard added (parity with other four kinds) | `sps2/tools/check_sps2.py` | +1 regression test; live records clean |
| 11 | W2 P5-1: revived dead control s9 in validate-p5.py (computed attribution problems, never reported); probe list aligned to ratified `attribution_policy.json` (DEC-0027: "self" is a legitimate surname, EXCLUDED) | `sps2/tools/validate-p5.py` | P5 43/1 → 44/1 (+1 real pass) |
| 12 | W2 SPS2-1: `p17` added to required directories (deletion had skipped 4 security suites with WARN-only, exit 0) | `sps2/tools/validate-sps2.sh` | sandbox-verified FAIL on missing p17; live 78/4 → 79/4 |
| 13 | W2 P4-1: N18 negative case was a tautology; now requires the checker's own `DUPLICATE` output via `check_p3.py registry` | `sps2/tools/validate-p4.sh` | P4 57/11, **0 missed** (was 1 missed) |
| 14 | W2 P5-2: negative-suite cases that RAISE now scored as missed with the exception reported | `sps2/tools/validate-p5.py` | P5 44/1 |
| 15 | W2 P5-3: s7 determinism requires rc==0 + non-empty output; s8 requires ≥1 collected test | `sps2/tools/validate-p5.py` | 48 tests reported, PASS genuine |
| 16 | W2 RB-1/RB-4: `restore_snapshot` digests, path containment, missing-file and file_count fail-closed; snapshot timestamp real UTC | `sps2/tools/rollback_seo.py` | +3 negative tests; isolation 23 OK |
| 17 | W2 RB-3: rehearsal proof obligations REQUIRED (missing validators/tests fail the rehearsal; hardcoded "72 checks passed" removed) | `sps2/tools/rollback_seo.py` | isolation 23 OK |
| 18 | W2 GATE-2/3/5: sys.path insert at position 1 (shadowing fix); `\bfresh\b` word-boundary basis check; slice-id history coerces non-strings | `sps2/tools/p10_runtime_gate.py` | gate suite 320 OK; isolation line pins updated 1941→1944 |
| 19 | W2 SPS2-2/SPS2-4: all four P17 suite gates require ≥1 collected test; unreachable post-`exit 1` line removed | `sps2/tools/validate-sps2.sh`, `sps2/tools/validate-p2.sh` | P17 counts real (65/44/2/25); P2 unchanged 68/9 |

Final matrix: **1,057 tests, 0 failures, 2 skips** across all 35 modules
(Codex baseline 1,041/2/2 — every delta explained in the final report).
Full dispositions, policy-blocked findings, open User decisions, and the QA
handoff checklist: `reports/SPS2-SECOND-PASS-INTEGRATION-FINAL-20261017-092558.md`.

## Subagent plan

- **W1** (read-only): adversarial review of updater scripts, mirrors,
  manifests, legacy/import helpers, decision helpers, installers.
- **W2** (read-only): adversarial review of validators, P10 gate, SEO
  isolation, rollback tooling.
- **W3** (read-only): adversarial review of test infrastructure and
  contract fidelity (rehearsal, disputed-governance tests).
- **W4** (read-only): portability/caching/TOCTOU review of shell and
  PowerShell updater paths.
- All subagents: read-only, no edits; report findings + evidence + risks.
  Integration edits performed solely by the lead (me), sequentially.

## Known follow-up candidates from prior rounds (to be verified, not assumed)

1. Codex's 08:31 report §3 claims ending untracked = 25 — but the tree
   now has 26 (my sidecar). Verify whether Codex's pass predated the
   sidecar (08:31 < 08:35) → likely accurate *for its window*; must be
   stated precisely.
2. Codex §6 CI coverage gap: verify the 7-module list and the 28-module
   expected manifest independently.
3. Codex §9 asserts "No new code-owned defect requiring immediate
   implementation was identified" — adversarial review (C1) is the check
   on that claim.
4. Codex's full-suite command (`find … | xargs python3 -B -m unittest -v`)
   differs from CI's invocation; verify both reach 1,041 and that the
   find-based enumeration is not silently dropping or adding modules.
5. Verify sidecar inertness claims (no checker/validator/test references
   it or enumerates the decisions directory).
