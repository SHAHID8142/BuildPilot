# SPS2 CLAUDE CROSS-REVIEW — C4/C5/C8/C9/C10/C12 AUDIT BATCH

Report time: 2026-10-17T13:12+06
Owner: Claude (independent reviewer)
Subject: Bounded read-only cross-review of six pending Codex audits:
- C4 `reports/SPS2-COMPLETION-C4-CODEX-REVIEW-20261017-121735.md` (note: the tasking named `...-REVIEW-P1-P4-...`; the actual file has no `P1-P4` segment — same report, confirmed by timestamp 12:17:35)
- C5 `reports/SPS2-COMPLETION-C5-CODEX-AUDIT-20261017-123100.md`
- C8 `reports/SPS2-COMPLETION-C8-CODEX-GOVERNANCE-AUDIT-20261017-1239.md`
- C9 `reports/SPS2-COMPLETION-C9-CODEX-P10-READINESS-AUDIT-20261017-1243.md`
- C10 `reports/SPS2-COMPLETION-C10-CODEX-AUDIT-20261017-124611.md`
- C12 `reports/SPS2-COMPLETION-C12-RESIDUAL-ASSESSMENT-20261017-124804.md`

Mode: read-only. Checks run: file/line citation verification, hash recomputation, validator
re-runs (they are read-only checks by design), two sandboxed Bash function reproductions of
`is_greater`, one unittest discovery run, zero writes outside this report and the coordination
append. No source, CI, baseline, governance, approval, P10, `.sps/`, or backlog file touched.
Baseline at review: branch `build/roadmap-p3-completion`, HEAD `c49f3852e1c31d0136269c80fe58201b059af3ec`, 0 staged, 0 stashes.

---

## Verdict summary

| Audit | Verdict | Corrections |
|---|---|---|
| C4 | **PASS** (completes my earlier partial review; all five findings now verified) | C4-2 severity: data-loss path is narrower than the report implies |
| C5 | **PASS** | C5-2 reproduction is real but partially masked at the call site; C5-4 severity LOW (guarded upstream) |
| C8 | **PASS** | none material |
| C9 | **PASS** | C9-07 wording: rollback's post-delete orphan failure is a WARNING+exit-1, not silent corruption |
| C10 | **PASS** | P7 history commits verified; one framing note on "false green" |
| C12 | **PASS** | none |

No finding in any of the six reports was contradicted. Two severity/wording calibrations below.

---

## C4 — Packages 1/4 adversarial audit: PASS (partial review now completed)

My 12:30 partial review confirmed C4-1..C4-4 from prior-round evidence and left C4-5
UNVERIFIED (probes halted at User direction). This round completes it **by inspection only**:

- **C4-5a duplicate `tearDown` — CONFIRMED.** `sps2/tests/test_round26_governance_contracts.py`
  defines `tearDown` at both :241 and :276; the second definition silently overrides the
  first, so the earlier cleanup body never runs. This matches the observed `ResourceWarning`s
  (also seen in C5's and C8's runs). Test-hygiene defect, no production impact.
- **C4-5b `isolation.py:203` delegation — CONFIRMED.** `scan_for_orphan_imports` deletes its
  `check_subsystem`/`exclude_paths` arguments and returns
  `scan_import_exceptions(project_root)["violations"]` — the DEC-7302 manifest contract owns
  the scan. The audit's non-ratifying framing is correct.

Re-verified C4-3/C4-4 against live code while here: the publish-window code at
`rollback_seo.py:301-317` matches exactly (move-aside → publish → rmtree(previous); except-path
restores previous only if target absent; `finally` rmtree can destroy the only prior copy when
both publish and restore fail — the joint-failure window I confirmed at MEDIUM-LOW).
`restore_snapshot` (:348-380) enforces containment + digest per entry and copies as it
validates — no P9-path allowlist, partial mutation on a later invalid entry, exactly as C4-4
states.

**Calibration (C4-2):** the symlinked-`domain/seo`-root data-loss path requires the P9 root
itself to be a symlink — a non-normal state no live caller produces and no test creates.
Confirmed as a real boundary defect, but MEDIUM-LOW reachability, not a routine-input hazard.

**Verdict: PASS.** All five findings verified; severity calibrations above; the one-repair
cycle proposal (minimal proof tests: symlinked root fixture, kill-injection between the two
`os.replace` calls, valid-digest in-root non-P9 restore entry) stands.

---

## C5 — Updater/bootstrap audit: PASS

All five findings verified against live code; two reproduced by execution:

- **C5-1 bootstrap `--force` symlink overwrite — CONFIRMED (inspection).**
  `copy_template` at `scripts/bootstrap-sps.sh:38-46` does `cp "$TEMPLATE_DIR/$name" "$dest"`
  with no symlink check on `$dest` or `$DEST/.sps`; `--force` skips the `-f` keep-branch.
  Codex's temp-fixture probe (outside sentinel overwritten) is consistent with the code path.
- **C5-2 huge prerelease numeric — CONFIRMED (reproduced).** I extracted `is_greater` into a
  sandbox and ran `is_greater 1.2.3-alpha.1 1.2.3-alpha.999…999` (36 nines): **returns 0**
  ("local newer") — bash wraps the out-of-range literal. Note the wrapper
  `is_valid_version` caps *core* components at 9 digits but the prerelease segment
  `(-[0-9A-Za-z.-]+)?` is unbounded, so the huge value passes validation and reaches the
  arithmetic. **Calibration:** at the actual call site the *remote* value is the huge one and
  the failure says "up to date" — a missed-update (fail-open on freshness), not a downgrade;
  local-huge/remote-small cannot occur through validation. Real defect, LOW-MEDIUM.
- **C5-3 stale cache across installed-version change — CONFIRMED (inspection).**
  `check-update.sh:150-160` trusts cached `STATUS` after only `is_valid_cached_state`
  (format check); no comparison of cached `LATEST` against the live installed version. Both
  described scenarios (stale up-to-date exit 0; stale update-available exit 1) follow from
  the code. PowerShell twin unverified (`pwsh` unavailable) — correctly flagged by C5.
- **C5-4 malformed installed version reaches arithmetic — CONFIRMED (reproduced), severity
  LOW.** `is_greater unknown 2.0.0` emits exactly the two `10#unknown` arithmetic errors and
  returns 1. **Calibration:** C5 itself notes `:127-131` maps malformed installed values to
  `unknown` *before* the comparison, and `:177-181` then guards `is_greater` behind
  `INSTALLED != unknown` — so the reachable trigger is narrower than the raw function
  precondition suggests (the `is_greater` call at :191 runs only for a validated, non-unknown
  installed version; the malformed path is exercised by direct callers/tests). The arithmetic
  errors are real; the end-user-visible impact is an "update available" path with stderr
  noise, not a wrong verdict. Also confirmed: the existing test at
  `test_check_update_safety.py:176-181` does not assert stderr cleanliness.
- **C5-5 mirror parity not asserted for checkers — CONFIRMED.**
  `test_updater_safety.py:296-303` covers bootstrap + two updater pairs only; the two
  check-update pairs are absent from the regression. My earlier session verified all five
  current pairs are byte-identical, so this is a coverage gap, not a live divergence.

**DEC-7301 boundary (validator 79/4):** re-ran `validate-sps2.sh` — exit 1, 79/4, failures are
exactly the four check-update paths excluded by the DEC-7301 manifest. C5's classification
(current protection-boundary failure, not a validator defect; resolution User-gated; disputed
approval ≠ authorization) is correct. The stale-hash observation (current `1955279a…`/
`2829a1db…` vs recorded `f175ed77…`/`ca00fcea…`) matches my own prior hash captures.

**Verdict: PASS.** All five findings stand; C5-2/C5-4 severity calibrations above; code-owned
fixes are proposable, but any change to the four excluded paths re-opens the legacy-baseline
question — Packages 2/3 remain BLOCKED_USER.

---

## C8 — Governance audit: PASS

All six findings verified:

1. **Manifest integrity ≠ approval — CONFIRMED.** `legacy_exceptions.py:236-237` grants the
   8-path exemption purely on manifest-pin pass; `import_exceptions.py:174-184` loads the
   manifest as allowlist with no decision/sidecar consultation. The sidecar's unapproved/
   fail-closed language is on record. Fail-open mismatch if the sidecar is authoritative —
   correctly held User-gated, no change made.
2. **Date-validation inconsistency — CONFIRMED (code inspection).** `attribution.py:144-162`
   requires a date; `check_sps2.py:117-128`, `check_p3.py:237-240`, `check_p2.py:58-64`
   check only state/decided_by/AGENT — no date requirement; `decision.schema.json:61-84`
   requires only `approval.state`. C8's synthetic-fixture probe result is consistent with
   this code. Legacy `approved_by/approved_on` caveat noted.
3. **Identifier compatibility uneven — CONFIRMED.** `check_p2.py:221-226` is
   `re.fullmatch(r"DEC-\d{4}")` only; no DEC-7303 ratification proposed — correct.
4. **Live scanner violation + test gap — CONFIRMED.** The live-scan test
   (`test_round26_governance_contracts.py:284-307`) asserts exactly 8 approved imports and
   membership of two, but never asserts `violations == []` — its pass is compatible with the
   known `p10_runtime_gate.py:1944` violation. Verified the violation site exists as cited.
5. **Validator counts — REPRODUCED.** All five validators exit 1; foundation 79/4 re-run
   matches; P4 emits exactly the two `P7_ARTIFACT_CREATED` failures (`decisions/P7-DECISIONS.json`,
   `memory`); P5 re-run = 44/1. The C0–C3 P7-wording correction C8 requested is present
   (verified in my C11/C13 round).
6. **Stale prior findings — CONSISTENT.** I re-ran the governance/attribution-adjacent
   focused suites earlier this session (106 OK) and the attribution-fixture failure did not
   reproduce for me either.

**Verdict: PASS.** Every "do not change without User direction" boundary in C8 is correctly
drawn; nothing in it ratifies DEC-7301/2/3 or touches records.

---

## C9 — P10 readiness audit: PASS

- **Gate result 9/5/2 exit 1 — matches all my independent runs this session** (C0–C3 round,
  P1/P4 review round). Control ID lists (9 PASS / 5 FAIL / 2 BLOCKED) match my recorded runs
  exactly.
- **Hash table — RECOMPUTED, all eight SHA-256 values match live files** (gate, test, slice,
  evidence, requirements, inventory, P10 decisions, Round 16 decisions). The audit's captures
  are faithful to the current tree.
- **C9-02 draft content / null approval — verified live** in my C11/C13 round
  (`content.json` draft/published_at null; slice `user_approval: null`); Round 16
  DEFER/NOT-GRANTED framing correct.
- **C9-03 evidence placeholder — verified:** `P10-EVIDENCE.json` coverage_note/blocked_reason
  say exactly what C9 quotes (no build, no gate record, BLOCKED result class).
- **C9-07 rollback interaction — CONFIRMED with one wording calibration.** The dynamic import
  at `p10_runtime_gate.py:1938-1946` is as cited; `rollback_seo.py:231-232` shares the
  scanner; the zero-orphan check at :457-462 runs **after** P9 deletion. **Calibration:** the
  orphan failure path appends "WARNING: Orphan references detected after rollback:" and
  returns 1 — a loud, fail-closed post-condition failure, not silent corruption. The files
  are already deleted at that point (destruction is by design; the check is a safety
  *assertion*), so the accurate statement is: rollback would delete P9 files and then report
  failure because the known violation trips the post-check — operationally a rollback that
  cannot report success, which is the intended fail-closed posture, not an additional damage
  path. C9's "no rollback was run; a run against the working tree would be destructive"
  caution is exactly right.
- **C9-08 missing test-execution/rollback-rehearsal controls — consistent with the 16
  control IDs I captured in earlier rounds** (no such control IDs present).
- **C9-09/C9-10 stale presence claims and untracked-artifact provenance — CONFIRMED** in my
  C11/C13 round (inventory/evidence staleness; gate+test untracked; no authorizing record
  located). "Do not infer reversal from general finish-the-project language" is the correct
  standard.

**Verdict: PASS.** NOT READY is the only supportable reading; every escalation in C9 is
User-gated and correctly labeled.

---

## C10 — Capability validators / P7: PASS

- **Validator results — REPRODUCED:** P2 68/9, P3 66/10 (final), P4 57/11 (exactly the two
  P7 findings above the 9 protected paths), P5 44/1, all exit 1, zero missed negative cases.
  The nine-path protected list matches my two-baseline analysis from the QA round
  (`c49f3852` vs `c11da27` split).
- **P7 history commits — VERIFIED:** `8ae4068` (2026-10-05 16:04, "P7 implementation
  authorised"), `91b82e3` (20:09, pre-approval fixes), `75585b2` (21:15, "record User approval
  of the completed P7 implementation"), and `e743780` (15:11, last touch of the root audit)
  all exist with the cited timestamps. C10's staleness timeline for
  `AUDIT-P7-READINESS-AND-DECISION.md` is exact.
- **P7 readiness false green — REPRODUCED:** I re-ran `validate-p7-readiness.py` — exit 0,
  30/0 + 7 negative cases, while the three roadmap deliverables are tracked at HEAD (verified
  present in my C11/C13 round). `P7_IMPL_ARTEFACTS` at :56 checks only
  requirements/evidence/tasks/handoff/bootstrap paths; the "no P7 implementation deliverable
  exists" pass at :310 is therefore unsupported by what the check actually inspects. Real
  validator/phase-model defect; C10's refusal to suppress or rewrite-to-green is correct.
- **Focused P7 suite — RE-RUN:** 3 tests OK, matching C10.
- **Framing note:** "false green" is accurate for the validator's *claim* ("no deliverable
  exists"), but the P7 *state* it was written to assert (pre-authorization readiness) is
  itself superseded by the recorded 2026-10-05 authorization/approval commits — the defect
  is phase-model conflation, exactly as C10 concludes. No correction needed, this note just
  separates the two.

**Verdict: PASS.** Repair belongs in a separate authorized task with phase-aware inputs and
planted-deliverable regression fixtures, as C10 proposes.

---

## C12 — Residual assessment: PASS

- **R-1 (scanner dataflow residuals) — CONFIRMED still-current and correctly DEFERRED.** The
  four shapes (tuple-unpack, walrus, container-storage, non-constant getattr) are absent from
  `_dynamic_loader_names`/`_is_dynamic_loader_expression` (verified in my full read of
  `import_exceptions.py` this session); absent from the live tree; my earlier probes
  demonstrated the misses. C12's FP-risk rationale matches my own R-1 analysis — DEFER is the
  right call, and its refusal to change the codified local-`import_module` FP contract
  mid-hardening is correct.
- **R-2 (regular-file snapshot target) — CONFIRMED still-current; bounded fix recommendation
  is sound.** Live code at `rollback_seo.py:301-317` matches C12's description exactly
  (verified again this round); my own R-2 probe reproduced the residue-with-publish behavior.
  Production callers (:412, :650) use the default destination — LOW likelihood, reachable by
  contract. The proposed early `lstat`-based directory-shape guard with boundary tests
  (including symlink destinations) is the minimal correct fix, and C12 correctly scopes it
  inside a separately authorized Package 4 correction and explicitly disclaims that it
  closes C4-3/C4-4.
- Boundary discipline: no tests, no probes, no edits — consistent with everything I can see.

**Verdict: PASS.**

---

## Cross-batch observations

1. **Zero contradictions across six audits.** Every finding I could check against live code,
   hashes, validators, or history commits held up. The two severity calibrations (C4-2
   symlinked-root reachability; C5-4 malformed-version reachability) and one wording
   calibration (C9-07 rollback post-check semantics) narrow the claims; none overturns one.
2. **Reproducibility is high.** C9's eight-file hash table, C10's four P7 history commits,
   C8's validator counts, and C10's 30/0 false green all reproduced exactly.
3. **Boundary discipline held.** No audit edited source, CI, baselines, governance, P10, or
   `.sps/` files; all DEC-7301/2/3, legacy-baseline, publication, exposure, and provenance
   questions are consistently routed to BLOCKED_USER. Nothing in this batch claims P10 or
   release readiness.
4. **Filename note:** C4's report file is `SPS2-COMPLETION-C4-CODEX-REVIEW-20261017-121735.md`
   (no `P1-P4` segment); the tasking's longer name does not exist. Same report, reviewed here.

## Recommendation

All six audits may be marked reviewed and their backlog rows advanced from NEEDS_REVIEW.
Open User decisions are unchanged and remain BLOCKED_USER: DEC-7301/7302/7303, the
legacy-baseline scope for Packages 2/3, P10 gate-artifact provenance, publication/approval
boundaries, the DEC-0001/DEC-0032 push disposition, self-approval attribution policy, the
seven untracked test modules' CI tracking, P5 authorization basis, and
`.claude/settings.json` provenance. P10 and release readiness remain **NOT READY**.
