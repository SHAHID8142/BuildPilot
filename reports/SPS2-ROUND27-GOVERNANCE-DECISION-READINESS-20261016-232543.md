# SPS2 ROUND 27 — GOVERNANCE DECISION READINESS REVIEW

Report time: 2026-10-16T23:25:43+06:00 (suffix 20261016-232543)
Mission: independent, read-only readiness review of the DEC-7301/7302/7303
governance package against the live repository.

**READ-ONLY round.** The only filesystem change is this report. Nothing
staged, committed, pushed, deployed, published, or approved by this agent.

---

## 0. CRITICAL CONTEXT — CONCURRENT IMPLEMENTATION LANDED MID-REVIEW

This review was ordered as a pre-decision readiness check. **While it was
running, a concurrent agent implemented the entire Round 26 contract
package** (file timestamps 23:18–23:20 +06):

- `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json` — a decision record
  creating **DEC-7301, DEC-7302, DEC-7303 with `approval.state:
  "APPROVED"`, `decided_by: "User"`, `decided_at: 23:15:04+06`**, claiming
  verbatim transcription of a User "Round 26 decision message".
- Both manifests (`legacy-exception-manifest.json`,
  `p10-p9-import-exception-manifest.json`), both shared helpers
  (`legacy_exceptions.py`, `import_exceptions.py`),
  `decision_identifiers.py`, a 28-test contract suite
  (`test_round26_governance_contracts.py`), and amendments to the decision
  schema, both decision validators, all five phase validators, P3/P9/P10
  requirements, P7/P9 threat models, and both SEO scanners.

Porcelain went **40 → 49 → 61 → 62 during this review window**; the agent
was still writing at 23:25. Consequently this report is both the requested
readiness review **and** a live reconciliation of that implementation. The
decision records exist but are **untracked working-tree data**; per
UQ-ATT-2 (self-declared attribution, still open), this agent cannot verify
that the transcribed "User Round 26 message" was actually sent by the
User. **Only the User can confirm or repudiate the APPROVED states.**

## 1. Baseline and evidence (Task 1)

| Item | Value |
|---|---|
| Branch / HEAD | `build/roadmap-p3-completion` / `c49f3852…` (unchanged all rounds today) |
| Staged / stashes | 0 / 0 |
| Porcelain | **62 at 23:25** (was 40 at 23:14, end of Round 26A) — 32 tracked-modified + 30 untracked |
| Concurrent activity | **Heavy and ongoing** (see §0) |
| Historical-report discrepancies | Round 25's §4.7/5.7/6.4 name `SPS2-ROUND23-CONTRACT-DECISIONS.json`; the created record is `SPS2-ROUND26-CONTRACT-DECISIONS.json` (naming drift, same content intent). Round 25's proposed manifest hashes (`6daa1404…`, `71d7830a…`) are **superseded** — the created manifests hash to `71a054df…` / `d8dd5039…` because Round 26A changed `sps-update.sh` (+mirror) and `test_updater_safety.py` after Round 25; the decision record explicitly documents the recompute. Round 25's "40 porcelain / 22 tracked-modified / 149 untracked" is stale. |

## 2. DEC-7301 review — Legacy updater exception (Task 2)

**Independently verified (all checks run by this agent, not trusted from
any report):**

- Manifest canonical SHA-256 recomputed: `71a054df3f0fa884dae450d2bd7a586318c6bbb3624e0138fbf9442916a8891d` — **matches** the identity embedded in DEC-7301's decision text.
- All 8 exception entries re-verified against the live worktree: worktree blob (`git hash-object`), SHA-256, Git mode, and stage-0 ∈ {baseline blob, expected blob} — **8/8 OK**.
- Test artifact `sps2/tests/test_updater_safety.py` SHA-256 `e33af7dcafec0302…` — **matches** the manifest.
- All four check-update mirrors are in `explicitly_excluded_paths` — correct per contract.
- `legacy_exceptions.py` read in full: fail-closed on missing/malformed/duplicate/unexpected/symlinked/deleted/hash-/mode-mismatched files; traversal- and escape-rejecting path normalization; strict field-set equality; `verify_legacy_exceptions()` run live → **zero violations**.
- `validate-sps2.sh` amended to use the helper with baseline `c49f3852…`; run observed: **78 passed, 4 failed** — the 4 failures are exactly the four check-update mirrors (modified by User-authorized Rounds 21A/24A, excluded by DEC-7301). Previously 78/1 (`get-sps.ps1`); the exception now covers `get-sps.ps1` correctly.

**Findings:**

| # | Finding | Severity |
|---|---|---|
| 7301-A | **check-update mirror exclusion leaves the foundation validator red on User-authorized work.** Rounds 21A/24A modified the mirrors under explicit authorization; DEC-7301 deliberately excludes them; result: `validate-sps2.sh` fails 4 legacy-protection checks indefinitely. The contract is internally consistent but the interaction with already-granted authorizations was not reconciled. | **Blocker (policy)** |
| 7301-B | **c11da27-baseline validators flag 17 paths the exception does not cover.** `validate-p2/3/4/5` diff from `c11da27` and flag `.github/expected-test-modules.txt`, `.github/workflows/sps-ci.yml`, `.sps/tools/validate-{capability,control,governance}.sh`, `sps2/security/test-secret-safety.sh`, `sps2/tools/test-*.sh`, `sps2/tools/validate-{p2,p3,p4,sps2}.sh` — legitimate changes from ratified earlier workstreams (and the validators' own DEC-7301 amendments). Observed: P2 68/17, P3 66/18, P4 57/19, P5 43/1. "P5 uses the shared exception" is true but insufficient — the shared exception covers only the 8 updater paths. | **Blocker (policy)** |
| 7301-C | `verify_legacy_repository()` couples exemption to perfection: if *any* of the 8 pins fails, the exempt set is emptied and every legacy diff line goes red. Fail-closed direction (safe), but one tampered file masks the exemption status of the other seven and produces noisy output. | Low (behavioral note) |
| 7301-D | The helper's `main()` prints violations to stderr and returns 1; the amended validators capture `2>&1` and string-match. A git error inside the helper would surface as violation text — correct direction, verified by read. | Info |
| 7301-E | Scope containment verified: the manifest authorizes exactly 8 paths + 1 test artifact + 4 excluded paths; no ninth path; no mirror coverage; no accidental authorization beyond the eight-path exception found. | Pass |

## 3. DEC-7302 review — Home/P9 SEO import exception (Task 3)

**Independently verified:**

- Manifest canonical SHA-256 recomputed: `d8dd50395689de0325c29fd55ea959205bee17b9a606b84b236fd3f044f22448` — **matches** DEC-7302's embedded identity; 4 records, exact field sets.
- Shared scanner `import_exceptions.py` read in full: hash-pins the manifest, rejects symlinks/traversal/outside-root, `ast.parse` fail-closed on SyntaxError/OSError/ValueError/RecursionError, rejects module/star/duplicate/dynamic imports, reports approved-vs-orphan separately, fails on missing approved dependencies.
- Scanner run live: **exactly the 8 approved (file, module, symbol) imports found; zero unapproved orphans** — except one violation (7302-A below).
- `domain/seo/isolation.py` and `sps2/tools/rollback_seo.py` both delegate to the shared scanner (divergence eliminated).
- Frontend suites re-run: **85 tests OK** (Home renderer unaffected).

**Findings:**

| # | Finding | Severity |
|---|---|---|
| 7302-A | **The P10 gate itself violates the new scanner.** `sps2/tools/p10_runtime_gate.py:1941` uses `importlib.import_module("domain.seo.audit").audit_directory` — deliberately (a code comment explains it avoided the old static orphan scan). The Round 25 AST inventory inspected only `home_render.py` and `test_home_render.py` and asserted "no dynamic imports" — **it never scanned the gate**. The new scanner flags it: `sps2/tools/p10_runtime_gate.py:1941: dynamic domain.seo import is forbidden`, so `scan_import_exceptions()['ok']` is **False**. The package's manifest has no group for the gate. User must choose: add a fifth DEC-7302 group (manifest hash changes → new decision identity), convert the gate to a static import, or exclude the gate file with justification. | **Blocker** |
| 7302-B | **SEO isolation suite is red: 20 tests, 8 failures.** `test_isolation.py`'s `test_legacy_diff_zero` and 7 rollback tests still enforce legacy-diff-zero against the *uncommitted* DEC-7201/7301 work ("Legacy directory 'skills' has uncommitted modifications"). Round 25 §5.7 listed `domain/seo/tests/test_isolation.py` for amendment; the concurrent agent amended `isolation.py` but the test expectations still fail. The rollback-rehearsal guarantee ("deletion of domain/seo/ leaves core validators passing") is currently unproven while validators are red for 7301-B reasons. | **Blocker** |
| 7302-C | `scan_for_orphan_imports()` now `del`s its `check_subsystem`/`exclude_paths` parameters — signature preserved for callers but semantics silently narrowed to the DEC-7302 contract. Any external caller passing custom excludes would be silently ignored. Grep found no other callers; risk accepted but worth pinning in a test. | Low |
| 7302-D | Symbol-level matching, alias tolerance, duplicate-symbol rejection, and the "approved dependency missing" tripwire all verified by code read + live run. P9 rollback wording amended in `P9-THREAT-MODEL.md` and `P9-REQUIREMENTS.json` (diffs read; the owned-dependency reclassification is accurately described). | Pass |

## 4. DEC-7303 review — Historical decision identifiers (Task 4)

**Independently verified:**

- `sps2/governance/decision_identifiers.py` implements exactly the proposed anchored pattern `^(?:DEC-[0-9]{4}|D-P[0-9]+(?:-[A-Z0-9]+)*)$`.
- Pattern probes run by this agent: 7 positives accepted (DEC-7201/7301/7302/7303, D-P7-C, D-P10-1, D-P3-FOO-2); 11 negatives rejected (empty, lowercase, `D-P10-_BAD`, `D-P10--1`, `D-P10-1-`, `D-1`, `DEC-72A1`, `DEC-721`, `DEC-72011`, whitespace-padded both sides). **All correct.**
- Both `check_sps2.py` and `check_p3.py` now import the single shared pattern (deduplication achieved; git diff confirms both changed).
- Schema `decision.schema.json` updated to the same pattern (diff read).
- Live validator runs: `check_sps2.py decision` on `SPS2-ROUND26-CONTRACT-DECISIONS.json` → **exit 0, no errors**; on `SPS2-ROUND16-USER-DECISIONS.json`, `LEGACY-SCOPE-DECISIONS.json`, `LEGACY-PATH-DEFINITION-DECISIONS.json` → **exit 0** (historical IDs now accepted). Exit-code contract unchanged (still exits 0 on data errors; observed "unknown kind" → exit 0, consistent with the stdout-contract design).
- Duplicate detection retained (`_dup` call verified in both validators).

**Findings:**

| # | Finding | Severity |
|---|---|---|
| 7303-A | **Attribution test fixture drift: 29 of 68 `test_attribution_policy` tests fail.** `check_sps2.py`/`check_p3.py` now import `decision_identifiers` from `sps2/governance`, but the tests' `_isolated_tree()` fixture copies only `attribution.py`, `attribution_policy.json`, and the two checkers — not `decision_identifiers.py`. Reproduced in isolation: the copied checker dies with `ModuleNotFoundError` → traceback, empty stdout (exit 1). Production behavior is fine (direct run emits `ERR … top-level document must be an object`, exit 0). Fix is one line in the fixture's copy list — but it is a real red suite introduced by the implementation. | **Blocker (test infra)** |
| 7303-B | The new `SPS2-ROUND26-CONTRACT-DECISIONS.json` validates clean under the amended validator — including its own DEC-7303 record. Self-consistent. | Pass |
| 7303-C | `decision_identifiers.py` is untracked; CI's tracked-module derivation will not see the new test module until a commit is authorized (standing CI-manifest note from Round 21A applies). | Info |

## 5. Cross-proposal interaction review (Task 5)

| Check | Result |
|---|---|
| Conflicts among the three | **No direct conflicts** — but 7302-A (gate vs scanner) is a conflict between DEC-7302's implementation and the *existing* P10 gate, and 7301-A/7301-B are conflicts between DEC-7301's scope and *already-authorized* work. |
| Dependencies on absent files/decisions | The decision records reference `SPS2-ROUND23-CONTRACT-DECISIONS.json` in the package text; the created file is `SPS2-ROUND26-…` (cosmetic). Both manifests exist. `decision_identifiers.py` exists. No missing dependencies found. |
| Sequencing constraints | Round 26A (fallback removal) correctly preceded DEC-7301's manifest creation — the manifest pins the post-removal blobs (`b0e5b8a8…`/`4148b530…`). Any future edit to any pinned file invalidates DEC-7301 and requires a new decision. DEC-7302's remedy for 7302-A must precede any claim that the scanner is green. |
| Could failures silently turn green | No. The exemption coupling (7301-C) errs red; the scanner fails closed on parse/manifest errors; the validators string-match violation lines. The one silent-green risk found: `check_sps2.py`'s empty-stdout-PASS harness quirk is guarded by the (currently failing) attribution tests — fixing 7303-A is what keeps that guard alive. |
| Accidental authorization of staging/commit/push/deploy/publication/P10-approval/CI/inventory/backend/installer | **None found.** The record's `non_goals` and `explicitly_not_approved_by_this_record` arrays explicitly withhold all of these; the amended validators and helpers contain no staging/commit/push logic (code read). The P10 gate's failure state was not touched by the package (gate re-run in Round 26A: exit 1, 9/5/2 — unchanged). |

**Classification:**
- **A. Normative User decisions:** (1) confirm or repudiate the APPROVED states in `SPS2-ROUND26-CONTRACT-DECISIONS.json` (UQ-ATT-2 — this agent cannot authenticate them); (2) check-update mirrors: amend DEC-7301 to cover them, or accept a permanently red foundation validator (7301-A); (3) c11da27-era legacy paths: extend the exception, re-baseline the validators, or accept red (7301-B); (4) P10 gate dynamic import remedy (7302-A); (5) whether SEO isolation's rollback-rehearsal contract remains binding given 7302-B.
- **B. Technical follow-ons after approval:** fix the attribution fixture copy list (7303-A); amend `test_isolation.py` expectations (7302-B); optionally decouple the exemption set from all-or-nothing (7301-C); pin 7302-C's narrowed semantics in a test.
- **C. Tests/evidence needed before acceptance:** green `test_round26_governance_contracts` (currently 28/1); green `test_attribution_policy` (currently 68/29); a decision on the scanner's `ok: False`; re-run of all five validators after the User resolves 7301-A/B; post-commit re-verification of pins (per Round 25 §4.8 tests 21–24).

## 6. Decision-ready checklist for the User

1. **[ ] Confirm the Round 26 decision record** (`SPS2-ROUND26-CONTRACT-DECISIONS.json`): did the User send the 23:15:04 message it transcribes? If yes, the records stand; if no, they are fabricated under UQ-ATT-2 and must be quarantined.
2. **[ ] DEC-7301 mirrors**: cover the four check-update mirrors (new manifest hash + decision amendment) or accept `validate-sps2.sh` at 78/4.
3. **[ ] DEC-7301 legacy scope**: resolve the 17 c11da27-era paths (extend / re-baseline / accept red at P2 68/17, P3 66/18, P4 57/19, P5 43/1).
4. **[ ] DEC-7302 gate import**: fifth manifest group for `p10_runtime_gate.py`, static-import conversion, or documented exclusion.
5. **[ ] DEC-7302 test amendment**: authorize fixing `test_isolation.py`'s legacy-diff-zero/rollback expectations.
6. **[ ] DEC-7303 fixture**: authorize the one-line `_isolated_tree()` fix.
7. **[ ] Separate permissions** (unchanged from Round 25 §11): record-creation ratification, implementation, staging/commit groups, push, publication, P10 approval, CI, installer, inventory, backend manifest, exit-code semantics.

## 7. Checks actually performed (Task 8) and limitations (Task 9)

**Run by this agent:** git baseline commands; SHA-256 of all relevant files; canonical-hash recomputation of both manifests (both MATCH); 8/8 manifest-entry verification (blob/mode/stage-0/SHA-256); live `verify_legacy_exceptions()` (clean); live `scan_import_exceptions()` (8 approved, 1 violation); ID-pattern positive/negative probes; `check_sps2.py decision` on 4 decision files; `validate-sps2.sh` (78/4), `validate-p2` (68/17), `validate-p3` (66/18), `validate-p4` (57/19), `validate-p5` (43/1); `test_round26_governance_contracts` (28/1); `test_attribution_policy` (68/29); `domain.seo.tests.test_isolation` (20/8); frontend suites (85 OK); full diffs read of schema, both validators, both scanners, P3/P9/P10 requirement amendments, P7/P9 threat-model amendments; isolated reproduction of the 7303-A fixture failure.

**Not independently verified / limitations:**
1. The authenticity of the transcribed User approval in `SPS2-ROUND26-CONTRACT-DECISIONS.json` (UQ-ATT-2) — **the central open question**.
2. `test_round26_governance_contracts.py` was run but not read line-by-line; its 1 failure (symlink-replacement test) was not root-caused — the test expects `"not a regular file"` in violations for a symlinked exception path; the helper does produce that message for worktree files, so the fixture's symlink setup may differ; needs investigation under implementation authorization.
3. Diffs of `P10-DECISIONS.json`, `P10-SECTION-INVENTORY.json`, `P5-REQUIREMENTS.json`, `P5-EVIDENCE.json`, `p10-slice.schema.json` (concurrent edits, +331/−86 lines total) were **not reviewed in detail** — the concurrent agent was still writing during this review.
4. PowerShell behavior unverified (pwsh absent, standing limitation).
5. The worktree moved twice during the review (49→61→62 entries); findings reflect the 23:25 state and must be re-confirmed once the concurrent agent goes quiet.
6. No validator exit-code behavior was changed by this agent; all observed exit codes are reported as seen.

## 8. Final worktree status

HEAD `c49f3852…` unchanged; **0 staged; 0 stashes; 62 porcelain entries** at 23:25+06 (32 modified tracked + 30 untracked paths, including this report under the untracked `reports/` directory). All pre-existing modifications and untracked files preserved; nothing reset, cleaned, stashed, reverted, moved, or overwritten. The only file created by this agent is this report.

---

*Round 27 review complete. The governance package is substantially implemented and mostly sound — both manifest identities verify, the 8 pins hold, the identifier contract works, and the shared scanners fail closed — but four red blockers stand between the current state and decision-ready green: the mirror-exclusion gap (7301-A), the c11da27 legacy scope (7301-B), the P10 gate's dynamic import vs the new scanner (7302-A), and the attribution fixture drift (7303-A). Above all, the User must confirm the Round 26 decision record itself. Stopping; awaiting instructions.*
