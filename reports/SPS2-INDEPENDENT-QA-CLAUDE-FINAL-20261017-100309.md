# SPS2 INDEPENDENT QA (CLAUDE LEAD) — FINAL REPORT

Report time: 2026-10-17T10:03:09+06 (suffix 20261017-100309)
Owner: Claude (independent adversarial QA lead)
Branch: `build/roadmap-p3-completion` · HEAD at open and close: `c49f3852e1c31d0136269c80fe58201b059af3ec`
Inputs independently verified: `SPS2-TECHNICAL-COMPLETION-FINAL-20261017-090901.md` (Codex completion),
`SPS2-SECOND-PASS-INTEGRATION-FINAL-20261017-092558.md` + ledger `…084905.md` (my second pass),
`SPS2-DEEP-QA-CODEX-FINAL-20261017-095249.md` + findings `…093559.md` + ledger `…093559.md` (Codex deep QA).
Companion deliverables from this audit: `SPS2-INDEPENDENT-QA-CLAUDE-TODO-20261017-100309.md`,
`SPS2-INDEPENDENT-QA-CLAUDE-FINDINGS-20261017-100309.md` (this file's evidence base).

**Subagent roster note:** this session exposes no subagent-execution mechanism, so the
eight work packages were executed directly as independent investigation batches with
freshly derived commands and temp-fixture probes. No finding was accepted from any prior
report without independent reproduction. No prohibited operation occurred at any point.

---

## 1. Baseline and protected hashes (captured at open, re-verified at close)

| Item | Value | Status |
|---|---|---|
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` | unchanged |
| Staged / stashes | 0 / 0 | unchanged |
| Porcelain | 65 (39 modified + 26 untracked entries) | unchanged |
| Subject record | `7c35617b309bef3557ad439fbb74be8455535f26a21cfe323d574ff73be5ed69` | intact |
| Correction sidecar | `a50bfd25fa54c8a6b38ee97515f043d0a29f9518ceabe3b3dfc9457b8620f1e6` | intact |
| Import-exception manifest | `f818665f471d015d6940a6ddbf4c08f02bfeabd6cc6d72e20295c7a321b5c8a8` | intact |
| `.claude/settings.json` | 0 bytes (e3b0c442…); HEAD version non-empty (0fe84d03…) | unresolved provenance |
| Backup manifest (Codex QA-0001) | `be3e8cc4…` present, matches | stale-vs-live confirmed |
| Concurrent activity during audit | none (only `.DS_Store` mtime) | clean |

## 2. Exact commands and reconciled outcomes

**Test matrix (run twice):**
`PYTHONPATH=. python3 -B -m unittest $(cat /tmp/qaD-modules-args.txt)` over 35 modules enumerated independently via `find sps2/tests domain -name "test_*.py"` →
**Run 1: `Ran 1057 tests in 38.907s` / `OK (skipped=2)`, exit 0. Run 2: `Ran 1057 tests in 39.142s` / `OK (skipped=2)`, exit 0.**
Skips: `test_p17_endtoend` (P17_AJV_ROOT unset — deliberate per GOVERNANCE.md §4, verified at `test_p17_endtoend.py:213-216`) and `test_updater_safety` (pwsh unavailable, verified at `test_updater_safety.py:305`).

**P10 gate:** `python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json [--json]` → exit 1, `OVERALL: FAIL (required controls failing: 7; integrity problems: 0; required controls: 16)`; JSON `controls[].result` = **9 PASS / 5 FAIL / 2 BLOCKED**; `missing/duplicate/demoted/unknown/malformed/integrity` all empty. Failing: published-only-content, slice-id-uniqueness, evidence-authenticity, approval-authenticity, req-p10-07-reconciliation. Blocked: exposure-declaration, p9-deployment-audit. `user_approval` null; publication unset; no fabricated state.

**Validators (all exit 1, exact summaries):**
- `validate-sps2.sh` → **79 passed, 4 failed, 0 missed** (4 = check-update mirrors)
- `validate-p2.sh` → **68/9/0** · `validate-p3.sh` → **66/10/0** · `validate-p4.sh` → **57/11/0** · `validate-p5.py` → **44/1/0**
- Failure lists extracted line-by-line; see §4 for the baseline-split reconciliation.

**Focused suites:** isolation 23 OK; P17 security 65 OK; updater 43 OK (1 skip); gate 320 OK; round26 33; frontend 25+36+24.

**CI coverage:** manifest = 28 modules; live = 35; the 7 absent modules sum to **481 tests outside CI** (576 inside).

**Mirrors:** all five pairs byte-identical by SHA-256 (check-update.sh `1955279a…`, check-update.ps1 `2829a1db…`, bootstrap-sps.sh `81390654…`, sps-update.sh `4148b530…`, update-sps.ps1 `fc207b82…`); `bash -n` clean on all three bash scripts in `scripts/`.

## 3. Codex deep-QA challenge results (C7)

All 25 Codex findings were checked; **24 CONFIRMED, 1 PARTLY CONFIRMED, 0 contradicted.**
Highlights with independent evidence:
- **QA-0021 (scanner evasion) — CONFIRMED and EXTENDED:** temp-fixture probes show four missed forms — bare-name rebind (`f = import_module; f(...)`), `getattr` rebind, `__dict__` subscript — plus Codex's two. Direct and aliased-attribute forms are correctly detected. Root cause: `_is_dynamic_import` matches only `Name`/`Attribute` callables, never `Call`/`Subscript` callables; the code comment claiming getattr coverage is unimplemented.
- **QA-0007 (my P10 4/12 claim) — CONFIRMED as a genuine error in MY report.** No invocation reproduces 4/12; the live gate is 9/5/2 with "required controls failing: 7". My line 117 ("12/16 FAIL") and line 129 ("4 PASS / 12 FAIL") are unsupported numbers — most plausibly transcribed from the pre-fix baseline rather than captured from the final run. The report's *conclusion* (gate fail-closed, exit 1, 0 integrity problems) was accurate; the *counts* were wrong. This correction is recorded append-only here; the prior report is deliberately not edited.
- **QA-0009/0010/0011 (installer/uninstaller) — CONFIRMED:** `install.sh:15` StrictHostKeyChecking=no; `uninstall.sh:99` `rm -rf "$p"` over fixed + manifest-fed arrays; `SYNC_PATHS` from `$HOME/.sps/install-manifest.env` reaches `rm -rf "$dest_root/sps"` with no path validation (nuance: only when the manifest key is present; defaults are fixed).
- **QA-0019 (snapshot atomicity) — CONFIRMED:** `create_snapshot` docstring claims atomic; implementation is per-file copy with manifest written last (interruption → no manifest → restore fails closed, accidentally safe).
- **QA-0014/0015/0016/0017 (governance) — CONFIRMED**, with the sharper fact that all five normative docs' DEC-73xx "authorized/approved" wording is absent at HEAD (`git show HEAD:<file>` = 0 refs) and exists only in uncommitted modifications.
- **QA-0024 (resource warnings) — PARTLY CONFIRMED:** updater module green even under `-W error::ResourceWarning`; full-suite warning surface not exhaustively re-characterized in this audit.

## 4. Findings Codex missed or under-specified (new in this audit)

1. **Two-baseline validator split (MEDIUM):** `validate-sps2.sh` pins `--baseline c49f3852` (HEAD) while p2/p3/p4/p5 pin `--baseline c11da27` (older). Consequently P2/P3/P4/P5 flag `.github/expected-test-modules.txt`, `.github/workflows/sps-ci.yml`, and three `.sps/tools/validate-*.sh` files that are **byte-identical to HEAD** — baseline-age artifacts, not live divergence. This fully explains why P2/P3/P4/P5 can never reach zero legacy failures without a governance act (advance baseline) or reverting committed work, and why cross-phase failure comparisons mislead.
2. **Fourth scanner-evasion form:** the bare-name rebind (`f = import_module`) is missed by the scanner and was not in Codex's register.
3. **`uninstall.sh` double-iteration nuance:** line 167 iterates `"${SYNC_PATHS[@]}" "${DEFAULT_SYNC_PATHS[@]}"` — when a manifest supplies SYNC_PATHS, the defaults are *still* processed, so a poisoned manifest adds targets rather than replacing them (worse than a plain override).
4. **`create_snapshot` fail-closed-by-accident:** the missing-manifest-on-interruption behavior is safe but undocumented as such; the docstring's "atomically" claim is affirmatively false.

## 5. Disposition of the mission's named discrepancies

| Discrepancy | Verdict |
|---|---|
| Tests 1,051 vs 1,057 | Both true in their windows; current = 1,057/0/2 (verified twice). Delta = tests added in my second pass; Codex QA-0004's explanation confirmed. |
| P10 9/5/2 vs 4/12 | **Live truth = 9/5/2, 7 required failing/blocked, 0 integrity. My 4/12 was an error; corrected here.** Codex's challenge stands. |
| Validators 78/4→79/4 etc. | Current counts verified exactly; +1 SPS2 (p17 dir check) and +1 P5 (revived s9) deltas from Codex's completion baseline are real and intentional. |
| 26 vs 65 porcelain | Methodology difference (untracked entries vs total entries); both correct. Expanded = 177 files. |
| 7 untracked modules outside CI | Confirmed; 481 tests. |
| "19 fixes applied and tested" | All 19 present and spot-verified in the live tree; authorship report-supported, not cryptographically provable (no commits made). |
| 5 normative docs cite DEC-73xx | Confirmed; wording is uncommitted worktree addition, absent at HEAD. |
| P10 dynamic import | Still present at `p10_runtime_gate.py:1942-1948` (scanner violation pinned at :1944 in tests — pins verified accurate); policy-blocked. |

## 6. CI coverage and platform limitations

- 481/1,057 tests outside CI (7 modules); fixing requires a CI change — not authorized in any of these sessions.
- `pwsh` unavailable: PowerShell updater behavior verified statically only.
- `P17_AJV_ROOT` unset: one e2e schema-validation skip, deliberate design.
- No network operations performed; remote/push state unverifiable offline.

## 7. Unresolved governance / User decisions

Codex's 12-item decision list (its §12) is adopted unchanged — every item is verified as still open by this audit — with two additions:
13. Whether to advance the P2/P3/P4/P5 legacy baseline from `c11da27` to current HEAD (or otherwise reconcile the two-baseline split found in QA-C-012).
14. Whether to authorize scanner hardening for the four dynamic-loader evasion forms (QA-C-002) as security-only, without treating it as DEC-7302 ratification — noting Codex's decision item 8 already covers this; the four-form list here is the concrete scope.

## 8. Final git state and deliverables

- HEAD `c49f3852…` unchanged; 0 staged; 0 stashes; 65 porcelain entries; protected hashes intact; no source/test/validator/manifest/CI/doc/governance file modified during this audit; the only writes were the three new timestamped QA reports in `reports/`.
- Deliverables: `reports/SPS2-INDEPENDENT-QA-CLAUDE-TODO-20261017-100309.md`, `reports/SPS2-INDEPENDENT-QA-CLAUDE-FINDINGS-20261017-100309.md`, `reports/SPS2-INDEPENDENT-QA-CLAUDE-FINAL-20261017-100309.md` (this file). No prior report overwritten.

## 9. Prohibited-operations confirmation

This audit did **not** edit any source, test, validator, manifest, schema, CI, evidence, decision record, or documentation file; did **not** stage, commit, push, fetch, pull, merge, rebase, deploy, publish, release, approve, clean, reset, stash, revert, delete, move, or quarantine anything; did **not** alter the disputed Round 26 record or its sidecar; did **not** weaken or bypass any gate (all negative probes ran in temp directories); did **not** infer approval from any record, field, or prior wording. DEC-7301/7302/7303 are treated as UNAPPROVED throughout.

## 10. Final QA verdict

**QA DID NOT PASS — passed-with-blockers is not available either, because one finding is CRITICAL and unresolved.**

What is solid (independently verified): the offline suite is stable at 1,057/0/2 across repeated runs; the five validators reproduce exactly; the 19 second-pass fixes are real and behavioral; mirrors are identical; the P10 gate is honestly fail-closed with zero integrity problems; the rollback rehearsal is genuinely attributed and fail-closed; Codex's deep-QA dossier is accurate in all 25 findings.

What blocks QA passage:
1. **CRITICAL:** the Round 26 record still falsely attributes approval to the User (QA-C-001), and five normative docs cite those unapproved decisions as authoritative in uncommitted wording (QA-C-004).
2. **HIGH:** the import scanner misses four dynamic-loader evasion forms (QA-C-002) — a live false-green control, not merely theoretical.
3. **HIGH:** installer/uninstaller security defects (QA-C-006/007) remain in legacy-pinned paths.
4. **HIGH:** 481 tests outside CI (QA-C-005); P10 gate fail-closed on genuine missing prerequisites; rollback rehearsal policy-blocked; P9 requirements self-contradictory (QA-C-011).
5. **Report integrity:** my own second-pass report contained unsupported P10 counts (QA-C-003) — corrected here, and a standing reminder that report numbers must be captured from tool output, never reconstructed.

The repository is **not release-ready** and must not be represented as such. The next safe step remains a narrowly scoped, User-authorized remediation plan (scanner hardening + installer/uninstaller security), preceded by explicit User decisions on the governance items in §7. Per the mission's stop conditions, this audit ends here — no remediation is launched.
