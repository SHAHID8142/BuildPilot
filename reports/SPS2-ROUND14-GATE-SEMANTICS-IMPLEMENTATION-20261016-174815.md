# SPS2 ROUND 14 — GATE-SEMANTICS IMPLEMENTATION (DEC-7112, SIX CONTROLS)

Report time: 2026-10-16T17:48:15+06:00 (suffix 20261016-174815)
Trigger: the User's Round 14 authorization —
`GATE-SEMANTICS IMPLEMENTATION: AUTHORIZE / EVIDENCE-FRESHNESS WINDOW: NO MAXIMUM-AGE WINDOW / PUBLICATION: DEFER / COMMIT/PUSH: NOT AUTHORIZED`
This resolves the authorization question UQ-R12-1 posed in
`reports/SPS2-ROUND13-HOME-IMPLEMENTATION-20261016-171848.md` §6.

**What this round did:** implemented the six DEC-7112-adopted semantics in
`sps2/tools/p10_runtime_gate.py` with full negative/tamper test coverage in
`sps2/tests/test_p10_runtime_gate.py`. Nothing else. No publication, no
approval, no inventory change, no CMS change, no git operations.

---

## 1. Authorization boundary as executed

| Round 14 line | Execution |
|---|---|
| `GATE-SEMANTICS IMPLEMENTATION: AUTHORIZE` | The six stubs implemented exactly per the DEC-7112 adopted designs (Round 12 decision package Part 2); no other gate behavior changed |
| `EVIDENCE-FRESHNESS WINDOW: NO MAXIMUM-AGE WINDOW` | Freshness = parseable RFC 3339 timestamp with offset, **nothing more**; age alone never fails a record (tested: a 2020 timestamp passes in 2026) |
| `PUBLICATION: DEFER` | Honored — `domain/cms/data/` untouched; content still `draft`; `published-only-content` still FAILs |
| `COMMIT/PUSH: NOT AUTHORIZED` | Honored — nothing staged, committed, or pushed; HEAD remains `c49f385` |

## 2. Files changed (2, both untracked — nothing else touched)

| File | Change |
|---|---|
| `sps2/tools/p10_runtime_gate.py` | `import hashlib` + `datetime`/`timezone`; the six stub bodies replaced with the DEC-7112 implementations; shared primitives (`_canonical_json_bytes`, `_sha256_digest`, `_canonical_state_digest`, `_parse_rfc3339_utc`, `_iter_evidence_records`, `GATE_RECORD_VERSION`, `MANIFEST_PATH`); `UNRESOLVED_SEMANTICS` rewritten to the five *remaining* limitations; docstring updated; one stale cross-reference in `check_evidence_references`' PASS detail corrected (it cited "UNIMPLEMENTED controls" that are now implemented); `run_gate` wiring threads `base_dir` to the two evidence controls |
| `sps2/tests/test_p10_runtime_gate.py` | Section H (`TestUndefinedControlsRemainUnimplemented`) replaced by the implemented-contract suites: `TestDec7112DigestControls` (10), `TestDec7112ReqP10_07Reconciliation` (3), `TestDec7112ApprovalStateInteraction` (4), `TestControlResultVocabulary` (kept), `TestDec7112EvidenceFreshness` (9), `TestDec7112EvidenceAuthenticity` (9); `TestEvidenceValidityClaimsRemainUnimplemented` updated to the implemented contract; two hostile-scalar tests updated (FAIL now, not UNIMPLEMENTED); `test_report_never_passes_without_real_prerequisites` updated (see §5) |

**Not modified:** schemas, inventory, decision records, CMS data, renderer,
renderer tests, `check_inventory_preconditions`, `check_approval_authenticity`,
`REQUIRED_CONTROL_IDS`, exit semantics, or the read-only guarantee (the gate
still performs zero write-mode opens; a dedicated test asserts the
authenticity cross-check never writes).

## 3. The six semantics as implemented

1. **evidence-freshness** — every referenced evidence record must carry a
   parseable RFC 3339 `generated_at` (or the evidence schema's `timestamp`
   fallback) **with an offset**; timezone-naive stamps fail (no timezone
   guessing). **No maximum-age window** per Round 14: age alone never fails.
   Missing/unparseable/naive → FAIL naming the record.
2. **evidence-authenticity** — a `gate_record` object
   (`sps2.p10-gate-record/v1`: producing command, input digests, output
   digests, UTC timestamp, emitting tool version) must be present on each
   record; the gate recomputes SHA-256 over every claimed `inputs`/`outputs`
   path (resolved relative to the slice's directory, bounded by the allowed
   root — the same locator grammar as `evidence_references`) and FAILS on any
   contradiction, naming record, field, claimed and actual digest. No
   `gate_record` → FAIL (existence is not authenticity).
3. **cms-state-digest** — canonical JSON (sorted keys, UTF-8, no insignificant
   whitespace; `.jsonl` parsed line-delimited) over `content.json`,
   `content_types.json`, `revisions.jsonl`, combined with repo-relative paths,
   SHA-256, `sha256:<hex>`. Recomputed and compared against
   `provenance.cms_state_digest`; null or mismatch → FAIL.
4. **p8-contract-digest** — same scheme over the ContentType contract inputs
   (`content_types.json`), deliberately a disjoint file set from #3 so a
   content edit does not invalidate the type contract and vice versa.
5. **req-p10-07-reconciliation** — set-compare of the slice's declared
   `state_changing_operations` against `domain/backend/operations.json`
   (`operations[]`, by name). Missing/unreadable/manifest-without-array →
   FAIL (fail-closed); undeclared manifest op or phantom declared op → FAIL
   naming the delta. The manifest does not exist yet, so this honestly FAILs
   until the first backend code arrives.
6. **approval-state-interaction** — two-locus coherence machine, read-only:
   `COMPLETE_VERIFIED_USER_APPROVED` requires a set `user_approval` whose
   `basis` claims a fresh explicit User act (APPROVAL-MECHANISM: OPTION A —
   D-P10-8 does not carry over); a gate pass alone is never sufficient; a set
   `user_approval` on any non-terminal state is incoherent → FAIL. The gate
   never writes and never transitions. `check_inventory_preconditions`'s
   existing refusal to certify a self-claimed terminal state is untouched and
   remains correct (certification is a separate authorized tool run's job).

## 4. Test results (exact commands, real runs)

| Command | Result |
|---|---|
| `python3 -B -m unittest sps2.tests.test_p10_runtime_gate` | **Ran 308 tests, OK** (282 pre-existing + 26 new/updated net) |
| `python3 -B -m unittest domain.frontend.tests.test_home_render` | **Ran 36 tests, OK** (no regressions) |
| combined: gate + home_render + content_slots + layout_registry | **Ran 393 tests, OK** |

Test-contract changes (an authorized behavior change, not a weakening —
every replaced assertion now demands the *stronger* implemented behavior):

- Old section H asserted the six controls stay UNIMPLEMENTED; the new suites
  assert their real fail-closed/pass behavior, including tamper cases.
- `test_report_never_passes_without_real_prerequisites`: `approval-state-interaction`
  left the must-fail list — the fixture inventory
  (`COMPLETE_AWAITING_USER_APPROVAL`, `user_approval: null`) is a *coherent
  pre-transition state* under design #6, so the control honestly PASSes while
  every substantive prerequisite is still absent. The overall verdict is
  still asserted FAIL (9 substantive failures remain).
- Hostile-scalar tests: malformed `evidence_references`/`provenance` now
  assert FAIL (implemented fail-closed) instead of UNIMPLEMENTED.

**Two implementation bugs the new tests caught during this round (both fixed
in the gate, not papered over in tests):** (1) `revisions.jsonl` is
line-delimited JSON and the canonical digest initially rejected it — now
parsed line-by-line, with a dropped/reordered line changing the digest;
(2) gate-record claimed paths initially resolved against the repo root
instead of the slice's directory — now the same locator grammar as
`evidence_references`.

## 5. Real gate run (Phase 5 verification)

Command: `python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json`
→ **exit 1, `OVERALL: FAIL`** (9 failing/blocked of 16; integrity problems: 0).

| Control | Result | Meaning now |
|---|---|---|
| schema-structural, slice-required-fields, evidence-references, layout-slot-conformance | PASS | unchanged |
| **evidence-freshness** | **PASS** | the real evidence record carries a parseable RFC 3339 timestamp (`2026-10-16T17:00:00+06:00`); no window applied |
| inventory-preconditions | PASS | observation only, unchanged |
| **approval-state-interaction** | **PASS** | the real inventory (`COMPLETE_AWAITING_USER_APPROVED`-awaiting, `user_approval: null`) is a coherent pre-transition state; the gate still never writes |
| published-only-content | **FAIL** | content is `draft` — **must remain a failure** until publication is authorized |
| slice-id-uniqueness | FAIL | no authoritative history supplied (unchanged) |
| **evidence-authenticity** | **FAIL** | `EV-P10-001` carries no `gate_record` — honest: the placeholder evidence has no digest claims to cross-check |
| approval-authenticity | **FAIL** | approval is null — **must remain a failure** (fresh User act required) |
| exposure-declaration | BLOCKED | no observed bind (unchanged, Phase-A limitation) |
| p9-deployment-audit | BLOCKED | no build directory supplied (unchanged) |
| **cms-state-digest / p8-contract-digest** | **FAIL** | inventory digests are `null`; the gate recomputes and fails closed on null. **Writing the values is explicitly not approved (DEC-7112); they lift only on an authorized inventory regeneration** |
| **req-p10-07-reconciliation** | **FAIL** | the backend operation manifest does not exist; fail-closed until the first backend code |

**The gate did not pass, and was not made to pass.** The three new PASSes
(freshness, approval-state-interaction, plus the pre-existing four) are each
genuine observations; every remaining failure is a real, named prerequisite.
`--json` output verified: 16 controls, 5 `unresolved_semantics` entries, no
integrity problems. Governance validators (`check_sps2.py evidence/decision`)
re-run on the touched records: zero ERR lines.

## 6. What remains unresolved (now in `UNRESOLVED_SEMANTICS`, all 5 reported)

1. `evidence_references` locator grammar remains path-resolution only.
2. No trust root exists: digests and cross-checks are content integrity +
   provenance recording, **never cryptographic authenticity**
   (DEC-7112 `standing_bounds.authenticity_limit`).
3. Human attribution fields are self-declared (UQ-ATT-2 remains open).
4. The backend operation manifest does not exist yet (fails closed).
5. The gate never writes approval state; the terminal transition is executed
   only by a tool run under explicit User authorization.

## 7. Withheld actions (all explicitly not authorized this round)

- **Publication** — `PUBLICATION: DEFER`; CMS data byte-untouched.
- **Git** — `COMMIT/PUSH: NOT AUTHORIZED`; nothing staged; HEAD `c49f385`.
- **Inventory digest values** — `provenance.cms_state_digest` /
  `p8_contract_digest` stay `null` (writing them is explicitly not approved
  by DEC-7112; requires an authorized inventory regeneration).
- **`user_approval`** — stays `null` everywhere; no approval act fabricated.
- **Backend manifest** — not created (it arrives with the first backend code).

## 8. Side-effect verification

`git status --porcelain` at end: the pre-existing modified/untracked set is
unchanged in shape, plus my two edited (untracked) files. Nothing staged,
nothing committed, nothing pushed, no stashes. **Note recorded for
transparency:** 8 tracked updater-script files (`get-sps.*`, `scripts/*`,
`skills/sps/scripts/*`) and a new untracked `sps2/tests/test_updater_safety.py`
appear modified/created in this working tree relative to the Round 13 end
state — they are not this round's work (no SPS2 governance file was touched
by me beyond the two gate files listed in §2), and they are left exactly as
found.

## 9. Recommended next steps (User's call, dependency order)

1. **Authorized inventory regeneration** to write the two recomputed digest
   values (I can compute them: the control suites demonstrate the exact
   canonical scheme) — lifts `cms-state-digest` and `p8-contract-digest`.
2. **Publication decision** (still DEFER) — lifts `published-only-content`.
3. **Gate-record emission for real evidence** — once a real gate PASS is
   achievable, evidence records should embed a `gate_record` with recomputable
   digests; lifts `evidence-authenticity`.
4. **Harness stages 5–9** (evidence assembly, rollback rehearsal).
5. **Commit/push grant** — the accumulating untracked work (gate tool, tests,
   slice, evidence, decision records, renderer, test suite) survives only in
   the working tree.

---

*Round 14 authorization consumed exactly: the six DEC-7112 semantics are
implemented and tested; the gate still honestly FAILs on the real slice for
reasons that are all real; nothing published, approved, staged, or
committed.*
