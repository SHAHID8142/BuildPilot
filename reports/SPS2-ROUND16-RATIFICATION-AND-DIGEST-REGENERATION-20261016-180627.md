# SPS2 ROUND 16 — UPDATER-SAFETY RATIFICATION & INVENTORY DIGEST REGENERATION

Report time: 2026-10-16T18:06:27+06:00 (suffix 20261016-180627)
Trigger: the User's Round 16 decision message (transcribed verbatim in
`sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json`, DEC-7201 evidence array).

**What this round did — exactly two authorized actions, nothing else:**
1. **UPDATER-SAFETY WORKSTREAM: RATIFY** → recorded as DEC-7201 in the new
   decision record, resolving Round 15 finding G-1.
2. **INVENTORY DIGEST REGENERATION: AUTHORIZE** → executed as DEC-7202: the
   two Round 15-verified digest values written into the inventory
   provenance block. No other inventory field touched (programmatically
   asserted before/after).

No existing report or decision was overwritten. Nothing published, nothing
approved, nothing staged, committed, or pushed, no CI change.

---

## 1. Authorization boundary as executed

| Round 16 line | Execution |
|---|---|
| `UPDATER-SAFETY WORKSTREAM: RATIFY` | DEC-7201 recorded; the eight updater-script files + `sps2/tests/test_updater_safety.py` now stand on a recorded User authorization. No file was modified for this — ratification is a governance record, not a code change |
| `INVENTORY DIGEST REGENERATION: AUTHORIZE` | DEC-7202 executed: `provenance.cms_state_digest` and `provenance.p8_contract_digest` written with the exact Round 15-verified values; inventory revalidated; gate tests re-run |
| `Do not overwrite existing reports or decisions` | Honored — one new decision record, one new report; 24 files in `reports/` (was 23) |
| `Do not change any other inventory field` | Honored — verified by a full before/after deep-compare (only the two digest keys differ) |
| `Do not publish content or set user_approval` | Honored — CMS untouched, `user_approval` still `null` everywhere |
| `PUBLICATION: DEFER` | Honored — content remains `draft` |
| `USER APPROVAL: NOT GRANTED` | Honored — no approval act recorded or fabricated |
| `COMMIT/PUSH: NOT AUTHORIZED` | Honored — 0 staged, 0 stashes, HEAD `c49f385` unchanged |
| `CI CHANGES: NOT AUTHORIZED` | Honored — no CI file touched |

## 2. Files changed (2, both new/untracked — nothing else touched)

| File | Change |
|---|---|
| `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json` | **New.** Three decisions: DEC-7201 (updater-safety ratification, with the User message transcribed verbatim), DEC-7202 (digest-write authorization, superseding DEC-7112's blanket digest-write prohibition *for these two values only*), DEC-7203 (transcription of the four standing constraints). Validator: **0 ERR lines** |
| `sps2/requirements/P10-SECTION-INVENTORY.json` | **Two fields only**, in the existing `provenance` block: `cms_state_digest: null → sha256:b35f7aba68eca4e7c9b688ae979891330f2f3d08c2b4250ce855c55943f7e38e`; `p8_contract_digest: null → sha256:ee6bb68f04f0eb468f0fd6eafaaea0b68639b88199e207c7a76ef57e10bbf217`. All other keys byte-identical (asserted programmatically); `inventory_state` still `COMPLETE_AWAITING_USER_APPROVAL`, `user_approval` still `null` |

**Not modified:** the eight updater scripts (ratification changes no code),
`test_updater_safety.py`, the gate tool, the slice, evidence, CMS data,
schemas, other decision records, CI, or any report.

## 3. Digest values — provenance of the numbers written

The values were **not** taken on faith from Round 14; they were:
1. Independently recomputed in the Round 15 audit by a from-scratch
   reimplementation of the DEC-7112 canonical scheme (§7 of the Round 15
   report), cross-checked against the gate's own helper;
2. **Recomputed a third time immediately before this write** (fresh run,
   identical results) — the same values the Round 15 report records;
3. Written, then re-loaded and deep-compared to confirm the write changed
   exactly two fields.

## 4. Revalidation (the User's explicit requirement)

| Check | Result |
|---|---|
| `python3 -B sps2/tools/check_sps2.py decision sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json` | **0 ERR lines** |
| `python3 -B sps2/tools/check_sps2.py inventory sps2/requirements/P10-SECTION-INVENTORY.json` | **0 ERR lines** |
| `python3 -B -m unittest sps2.tests.test_p10_runtime_gate` | **Ran 308 tests, OK** (full suite re-run post-write) |
| `TestDec7112DigestControls` re-run verbosely | **Ran 10 tests, OK** — including `test_matching_digest_passes_against_the_real_repo_state` and `test_recomputed_digests_of_the_real_state_are_stable`, which now exercise the *written* values against the live repo state |

## 5. Real gate result after the write

Command: `python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json`
→ **exit 1, OVERALL: FAIL** — still an honest failure, now **9 PASS / 5 FAIL / 2 BLOCKED** (was 7/6/3).

| Control | Before | After | Why |
|---|---|---|---|
| **cms-state-digest** | FAIL (null) | **PASS** | written value matches recomputation: `sha256:b35f7aba…f7e38e` |
| **p8-contract-digest** | FAIL (null) | **PASS** | written value matches recomputation: `sha256:ee6bb68f…bbf217` |
| approval-state-interaction | PASS | PASS | unchanged (coherent pre-transition) |
| published-only-content | FAIL | FAIL | content still `draft` — **must remain a failure** (PUBLICATION: DEFER) |
| slice-id-uniqueness | FAIL | FAIL | no authoritative history (unchanged) |
| evidence-authenticity | FAIL | FAIL | EV-P10-001 carries no `gate_record` (unchanged) |
| approval-authenticity | FAIL | FAIL | `user_approval` null — **must remain a failure** (USER APPROVAL: NOT GRANTED) |
| req-p10-07-reconciliation | FAIL | FAIL | backend manifest absent (unchanged) |
| exposure-declaration / p9-deployment-audit | BLOCKED | BLOCKED | no observed bind / no build (unchanged) |

The two newly lifted failures are the only ones the Round 16 authorization
could lift; the remaining five failures/blocks all map to explicitly
withheld actions. **The gate did not pass, and was not made to pass.**

## 6. Withheld actions (all explicitly not authorized this round)

- **Publication** — `PUBLICATION: DEFER`; CMS data byte-untouched.
- **User approval** — `user_approval` stays `null` everywhere; no approval
  act fabricated. APPROVAL-MECHANISM: OPTION A still requires a fresh
  explicit User act at actual completion.
- **Commit/push** — `COMMIT/PUSH: NOT AUTHORIZED`; nothing staged; HEAD
  `c49f3852e1c31d0136269c80fe58201b059af3ec` unchanged; 0 stashes.
- **CI** — no CI file or workflow touched.
- The ratification (DEC-7201) **does not authorize commit or push** of the
  updater workstream — the User's message says so and the record repeats it.

## 7. Side-effect verification

`git status --porcelain` at end: 33 entries (was 32; +1 = the new decision
record; the inventory edit modifies an already-modified tracked file, so it
adds no new entry). Nothing staged (0 cached paths), 0 stashes, HEAD
identical to the Round 15 end state. Files created this round: exactly two
(§2). Validator and test runs are read-only.

## 8. What remains before the gate can pass (all require separate User grants)

1. Publication decision (still DEFER) → lifts `published-only-content`.
2. Fresh explicit User approval act at actual completion → lifts
   `approval-authenticity`.
3. A `gate_record` on real evidence records → lifts `evidence-authenticity`.
4. The backend operation manifest (arrives with first backend code) → lifts
   `req-p10-07-reconciliation`.
5. Slice-id history source → lifts `slice-id-uniqueness`; observed bind +
   build → unblocks `exposure-declaration` and `p9-deployment-audit`.
6. Commit/push grant — the accumulating untracked work (gate tool, tests,
   slice, evidence, decision records, updater workstream, this record)
   survives only in the working tree.

---

*Round 16 authorization consumed exactly: the updater-safety workstream is
ratified on the record, the two verified digest values are written and
revalidated, and nothing else moved. The gate still honestly FAILs — now on
five real prerequisites instead of six — and nothing was published,
approved, staged, or committed.*
