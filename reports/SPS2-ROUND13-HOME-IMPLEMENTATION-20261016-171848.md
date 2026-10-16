# SPS2 ROUND 13 — HOME SLICE IMPLEMENTATION: RENDERER, BUILD PATH, INTEGRATION TESTS

Report time: 2026-10-16T17:18:48+06:00 (suffix 20261016-171848)
Scope: the Round 13 mission — implement the minimum real renderer/static-build
path and integration tests for `SLICE-P10-01`. **No publication, no approval,
no inventory change, no gate-semantics implementation, no git operations.**

---

## 1. Verified baseline (Phase 1 — revalidated, not assumed)

| Item | Observed |
|---|---|
| Branch / HEAD | `build/roadmap-p3-completion` / `c49f3852e1c31d0136269c80fe58201b059af3ec` — matches the mission's known HEAD exactly |
| Working tree | 8 modified tracked files (the 7 pre-existing user modifications + `.claude/settings.json`, already modified at session start), 15 untracked paths, nothing staged, no stashes |
| Round 12 artifacts | All present and intact: `SLICE-P10-01.json` (DRAFT, `user_approval: null`), `P10-DELEGATED-DECISIONS.json` (all ten decisions APPROVED), `P10-GATE-SEMANTICS-ADOPTION.json` (DEC-7112), `P10-ROUND12-USER-DECISIONS.json` (verbatim transcription), `P10-EVIDENCE.json` (BLOCKED placeholder) |
| Round 12 report | `reports/SPS2-ROUND12-EXECUTION-20261016-170620.md` present |
| Gate suite at start | 282 tests, OK |
| Real CMS inputs | Content `60e51f05…` status **`draft`**, `published_at: null`; ContentType `home` (`heading`/`body`, text, required) |

Diff stat at start: `377 insertions(+), 12 deletions(-)` across the 8 modified
files — identical to Round 12's end state. No other agent's work overwritten.

## 2. Files changed (2 new files; nothing else touched)

| File | Why |
|---|---|
| `domain/frontend/home_render.py` (new, ~490 lines) | The minimum renderer/static-build path: pure render function, stdlib reparse validator, in-process static build emitting exactly the `p10_to_p9_contract` artifact shape |
| `domain/frontend/tests/test_home_render.py` (new, 36 tests) | The integration suite required by Phase 3 |

**Nothing else changed.** The gate tool, schemas, inventory, decision records,
CMS data, and all existing tests are byte-identical to the Round 12 end state.

## 3. Renderer and build architecture

**Data flow (all in-process, stdlib-only):**

```
slice doc ─┐
CMS content ├─► render_home_document() ─► validate_home_document() ─► build_home_slice()
ContentTypes┘   (pure; no I/O)            (stdlib HTMLParser          (writes ONLY the
                                           reparse, stage 4)           declared build dir)
```

- **Slot resolution** goes through the pre-existing approved adapter
  `domain.frontend.content_slots.resolve_content_slots`, which enforces the
  ContentType shape, plain-text validation, and **`encode_for_html` exactly
  once at the sink**. The renderer never touches a raw CMS value: it
  interpolates only the adapter's already-encoded output.
- **SEO is P9-owned** (DEC-7109): `<head>` metadata from
  `domain.seo.metadata.render_html_meta_tags` (which auto-marks draft content
  `noindex, nofollow` per Threat Model §5.9), robots.txt from
  `generate_robots_txt`, sitemap.xml from `generate_sitemap_from_cms_items`
  (which strictly excludes unpublished records — a draft build carries an
  empty urlset).
- **Artifact shape** = exactly the `p10_to_p9_contract`: `index.html` (route
  `/` via the audit's own index→`/` derivation), `robots.txt`, `sitemap.xml`
  at the build root. The build writes nothing outside the declared directory.
- **Draft boundary (requirement 9):** the default `draft_policy="fail"`
  **aborts the build** on draft content (harness stage-3 failure semantics).
  The explicit `draft_policy="noindex_preview"` mode exists solely for
  deterministic error-state coverage: it renders noindex/nofollow, excludes
  the record from the sitemap, and is never a published route. **The real
  repository content is draft, so the default build of the real slice
  aborts** — verified, and correct.
- **Determinism:** no timestamps, randomness, or locale text enter the
  emitted bytes; identical CMS state yields byte-identical output (tested).
- **No network, no backend:** no socket, server, subprocess, or exec
  primitive anywhere in the module (AST-verified by test); the slice's
  `state_changing_operations: []` declaration is implemented, not contradicted.

**Structural reparse assertions** (stage 4, run on the in-memory document
before anything is written): fully closed elements, exactly one `h1`, no
heading-level jumps, declared `lang`, viewport meta present. Per DEC-7102/7103
these are structural checks only — **no viewport range, no accessibility
conformance claim, no performance threshold** (requirement 7 held).

## 4. Integration tests and results (Phase 3)

Command: `python3 -B -m unittest domain.frontend.tests.test_home_render`
→ **Ran 36 tests, OK** (exit 0).

Coverage by mission requirement:

| Requirement | Tests |
|---|---|
| Valid CMS inputs | renders real content through the approved adapter; single-encoding verified (no `&amp;amp;`) |
| Missing/invalid required fields | empty title → `MISSING_VALUE`; non-string body → `INVALID_VALUE`; missing ContentType → abort; duplicate content id → abort (identity by id, never array position) |
| HTML escaping / output safety | `<script>`, `<img onerror>`, attribute-breakout (`">`), and metacharacter payloads all encoded, never interpreted |
| Home route/layout selection | unknown route aborts; unknown layout aborts; exactly-one-reference enforced |
| Draft vs published | default policy aborts on draft (including the REAL repo content); preview policy marks noindex/nofollow and excludes from sitemap; published build includes route in sitemap |
| Missing entry points/assets | gate's own BLOCKED/FAIL behavior verified live (§5); slice declares explicitly empty assets per DEC-7107 |
| Deterministic output | two builds of identical inputs → byte-identical `index.html`, `robots.txt`, `sitemap.xml` |
| Malformed input failure | truncated/mismatched HTML flagged (`UNCLOSED_ELEMENTS`, `MISMATCHED_TAGS`); two h1s → `H1_COUNT`; h1→h3 → `HEADING_JUMP`; missing lang/viewport flagged |
| No network exposure | AST scan bans socket/subprocess/http/urllib imports; runtime socket-spy test fails the build if any socket is created |
| No state-changing backend | slice declarations asserted; renderer source contains no write path outside the build dir; parent-dir listing unchanged by a build |
| Absent/invalid evidence | slice's evidence reference resolves; placeholder record is `BLOCKED`/`NOT_CLOSED`; slice is DRAFT with null approval |
| Runtime-gate integration | the REAL gate binary run against the REAL slice via subprocess: exit 1, `OVERALL: FAIL`, with the three genuinely-satisfied controls PASS — a PASS would fail this test as manufactured evidence |

**Two initial failures, both bugs in my test code (never in the
implementation, and no existing assertion was modified):**
1. The source-scan test tripped on the *word* "subprocess" in the module's
   docstring (which states the module uses no such primitive). Replaced with
   an AST-based import/attribute scan — strictly more precise.
2. The unclosed-element test's input produced `MISMATCHED_TAGS` (the
   `</body>` in the input closes over open elements) rather than
   `UNCLOSED_ELEMENTS`; the test now uses a genuinely truncated document for
   the unclosed case and keeps the original input for the mismatch case.

Combined regression run —
`python3 -B -m unittest domain.frontend.tests.test_home_render domain.frontend.tests.test_content_slots domain.frontend.tests.test_layout_registry sps2.tests.test_p10_runtime_gate`
→ **Ran 367 tests, OK** (36 new + 25 + 24 + 282 pre-existing; zero
regressions, no existing assertion weakened).

## 5. Runtime gate results (Phase 5)

Command: `python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json`
→ **exit 1, `OVERALL: FAIL`** (11 of 16 required controls failing/blocked/unimplemented).

| Control | Result | Note |
|---|---|---|
| schema-structural | PASS | unchanged from Round 12 |
| slice-required-fields | PASS | unchanged |
| evidence-references | PASS | unchanged (path resolution only) |
| layout-slot-conformance | PASS | unchanged — real CMS data |
| inventory-preconditions | PASS | observation only |
| published-only-content | **FAIL** | content is `draft` — **must remain a failure**; lifts only on authorized publication |
| slice-id-uniqueness | FAIL | no authoritative history supplied |
| approval-authenticity | **FAIL** | approval is null — **must remain a failure**; APPROVAL-MECHANISM: OPTION A requires a fresh User act |
| exposure-declaration | BLOCKED | no observed bind (Phase-A limitation) |
| p9-deployment-audit | BLOCKED | no build directory supplied to the gate; no build exists in the repo (correct — a build directory is runtime output, and the gate must observe one, not be told to trust one) |
| evidence-freshness / evidence-authenticity / cms-state-digest / p8-contract-digest / req-p10-07-reconciliation / approval-state-interaction | UNIMPL | adopted designs (DEC-7112), not implemented — see §6 |

**The gate did not pass, and was not made to pass.** No content was published,
no approval manufactured, no evidence fabricated.

## 6. Gate-semantics boundary (Phase 4) — authorization question, gate unchanged

DEC-7112 adopted the six designs; UQ-R12-1 records the open question of
whether adoption authorizes *implementation*. The mission instructs: do not
silently resolve that ambiguity; determine precisely what changes would be
required; if authorization is ambiguous, leave the gate unchanged and ask.

**Determined precisely, the implementation would require editing
`sps2/tools/p10_runtime_gate.py`:**

1. Replace the six stub bodies (`check_evidence_freshness` 14 lines,
   `check_evidence_authenticity` 12, `check_cms_state_digest` 11,
   `check_p8_contract_digest` 11, `check_req_p10_07_reconciliation` 16,
   `check_approval_state_interaction` 13) with the DEC-7112 logic — e.g.
   canonical-JSON + SHA-256 digests (`hashlib` is **not currently imported**
   by the gate and would need to be), gate-record cross-checking, freshness
   comparison, set-compare reconciliation, and the two-locus approval state
   machine (whose APPROVAL-MECHANISM: OPTION A resolution is already
   recorded).
2. Extend `sps2/tests/test_p10_runtime_gate.py` with positive/negative/tamper
   tests for each implemented control.
3. No change to `REQUIRED_CONTROL_IDS`, exit semantics, or the read-only
   guarantee (verified: the gate has no write-mode opens today; the designs
   preserve that).

**Decision: the gate is UNCHANGED.** The authorization is genuinely ambiguous:
DEC-7112's own non-goals state "Not an implementation … Implementation of any
adopted semantics … [is] explicitly not approved by this record," while the
User's `SEMANTICS: ADOPT` line could be read as wanting the semantics in
force. Per the mission's Phase-4 instruction, this is reported as an explicit
question rather than resolved by assumption:

> **AUTHORIZATION QUESTION (UQ-R12-1, now precise):** Does the User authorize
> editing `sps2/tools/p10_runtime_gate.py` and
> `sps2/tests/test_p10_runtime_gate.py` (both currently untracked) to
> implement the six DEC-7112-adopted semantics as specified above — canonical
> JSON + SHA-256 digests, gate-record cross-checks, freshness policy (window
> length to be confirmed or defaulted), backend-operation manifest
> reconciliation, and the fresh-approval state machine — with full
> negative/tamper test coverage? Yes/No.

## 7. Security and output-safety considerations

- **Stored XSS:** every CMS value passes `validate_plain_text` →
  `encode_for_html` (quote=True) exactly once, inside the approved adapter,
  before any sink. The renderer adds no second, divergent encoding path.
  Tested against script, event-handler, and attribute-breakout payloads.
- **No network surface:** DEC-7101 honored — no socket, server, bind, or
  subprocess anywhere in the new code; verified statically (AST) and
  dynamically (socket-spy test).
- **No state-changing operations:** the only writes are the three declared
  build artifacts into the caller-supplied build directory; nothing outside
  it is touched (tested).
- **CMS integrity:** content identity resolved by unique id with duplicate
  rejection, mirroring the gate's `_duplicate_ids` hardening.
- **Draft never promoted:** the default build aborts on draft; the preview
  mode is machine-marked noindex/nofollow and sitemap-excluded. No author
  attribution invented (requirement 10); the provisional author string in
  the CMS data is untouched and unclaimed.
- **Honest limits:** these tests prove content integrity and structural
  safety only — not cryptographic authenticity, not human authentication,
  not WCAG conformance, not deployment readiness (D-P10-1 holds).

## 8. Publication remains deferred — explicit confirmation

**`PUBLICATION: DEFER` (Round 12) remains in force.** `domain/cms/data/` is
byte-untouched; the Home Content is still `status: "draft"`,
`published_at: null`; no published route was produced; the default build of
the real slice aborts by design. Nothing in this round published, promoted,
or staged content for publication.

## 9. Remaining blockers (to a future gate PASS — none actioned here)

1. **Publication** (deferred): `published-only-content` cannot pass while the
   content is draft.
2. **Gate semantics implementation** (authorization question §6): the six
   UNIMPL controls.
3. **Build observation**: `p9-deployment-audit` needs the gate to be pointed
   at a real build directory at gate-run time (the renderer can now produce
   one; the gate invocation and evidence recording are part of the harness/
   semantics work).
4. **Exposure observation**: `exposure-declaration` needs an observed-bind
   producer (Phase-A limitation, unchanged).
5. **Slice-id history**: `slice-id-uniqueness` needs an authoritative history
   input (design decision pending).
6. **User approval**: `approval-authenticity` passes only with a fresh,
   explicit User approval act at actual completion (APPROVAL-MECHANISM:
   OPTION A).

## 10. Final Git status and side-effect verification

`git status --porcelain` at end (unchanged shape from baseline, plus exactly
the two new files, all untracked):

- 8 modified tracked files — byte-identical to baseline (verified: diff stat
  still `377 insertions(+), 12 deletions(-)`); `.claude/settings.json` was
  already modified at session start and was not touched this round.
- 15 untracked paths — all pre-existing, plus:
  - `domain/frontend/home_render.py` (new)
  - `domain/frontend/tests/test_home_render.py` (new)
- Nothing staged, committed, pushed, stashed, reset, or deleted. HEAD remains
  `c49f385`. No report file overwritten (collision check performed).

## 11. Recommended next steps

1. **Answer the §6 authorization question** to unblock gate-semantics
   implementation (batch B2) — the largest remaining UNIMPL block.
2. **Publication decision** (currently DEFER): until granted, the gate cannot
   pass `published-only-content`, and the harness's stage-2 CMS edit /
   stage-3 build of the real slice must run in preview or fixture mode.
3. **Harness stages 5–9** (evidence assembly, rollback rehearsal) after
   semantics + publication, so stage-8 evidence records are real.
4. **Commit/push grant** when the User wants the accumulating untracked work
   (now: gate tool, tests, slice, evidence, three decision records, renderer,
   test suite) made durable — it survives only in the working tree today.

---

*Round 13 scope consumed exactly: renderer + tests implemented; gate
unchanged pending the explicit authorization answer; nothing published,
approved, staged, or committed.*
