# SPS2 ROUND 12 — P10 DECISION RESOLUTION, TECHNICAL DESIGN & IMPLEMENTATION READINESS

Report time: 2026-10-16T15:47:56+06:00 (suffix 20261016-154756)
Mode: **Read-only decision-preparation round.** No file was created, edited,
staged, committed, or pushed. This report is written under the User's standing
instruction that all round reports be delivered as `.md` files under `reports/`.
No prior report was overwritten.

**Legend:** 📌 = fact directly observed · 📄 = statement from a repository
record · 🔶 = technical inference · ⭐ = recommendation (not approval) ·
🧑 = reserved for the User

---

## 0. VERIFIED BASELINE

Identical to Rounds 10/11, verified at turn start:

| Item | Value |
|---|---|
| Branch / HEAD | `build/roadmap-p3-completion` / `c49f3852e1c31d0136269c80fe58201b059af3ec` |
| CI run | `38878290068` — success, head SHA matches HEAD exactly |
| Working tree | 18 paths (7 modified tracked + 11 untracked), byte-identical to Rounds 10/11; nothing staged |
| Round 10/11 reports | Exist only in-conversation (those rounds forbade file creation); no `SPS2-ROUND10/11-*.md` under `reports/` |
| Material discrepancy with historical reports | None |

---

## PART 1 — THE FIVE PENDING DECISIONS (Phase B)

### DEC-7101 — Pure in-process execution for the initial slice

**A. Source record** 📌 `sps2/decisions/P10-DELEGATED-DECISIONS.json`,
`status: PROPOSED`, `approval.state: PENDING_USER_APPROVAL`, no decider or
date. Title: "UQ-P10-01 — Pure in-process execution for the initial slice."
Evidence refs: `UQ-P10-01` (P10-REQUIREMENTS), `D-P10-1`,
`axis_contracts.backend.exposure_class`.

**B. Technical problem** 🔶 The slice schema forces a declared
`exposure_class`. Enum: `LOCAL_NON_NETWORK_EXPOSED` /
`NETWORK_EXPOSED_PRODUCTION`; the latter is hard-blocked until the four
D-P10-1 controls (authentication, authorization, CSRF, rate limiting) exist
AND are authorized. The initial slice must pick a backend shape first.

**C. Options** 📄 (documented in the record):
- **A** — pure in-process: no socket anywhere; build produced by a library
  call, served only as static files; `state_changing_operations: []` triggers
  no auth/CSRF/rate-limit work.
- **B** — loopback HTTP bind for local preview (still
  `LOCAL_NON_NETWORK_EXPOSED`).
- **C** — defer until the first section's needs are known.
- (A fourth option, `NETWORK_EXPOSED_PRODUCTION`, is not viable: controls
  don't exist and no authorization for them exists.)

**D. Consequences** 🔶

| | A (in-process) | B (loopback bind) | C (defer) |
|---|---|---|---|
| Functional | Static HTML; P9 audit contract satisfied with no server | Local preview server; same output | Blocks slice authoring (field is required) |
| Security | Narrowest blast radius; no bind to observe | Real socket exists; exposure control needs an *observed* bind | None |
| Fail-closed | "No socket" trivially verifiable | Gate must distinguish loopback from exposed | — |
| Testing | Negative: any socket creation fails | Negative: non-loopback bind fails | — |
| Gate impact | Coherent with no-bind observation | Requires the undefined "observed bind" evidence class | — |
| Policy obligations | None new | New evidence obligation with no defined format | — |

**E. Recommendation** ⭐ **Option A.** The record's own reasoning is
evidence-backed: static output satisfies the P9 audit contract (HOME-ACC-16
needs build output, not a server); Option B creates an undefined evidence
obligation; Option C blocks the slice for no benefit. *Does not solve:* any
future network exposure — that needs D-P10-1 controls + fresh authorization.
*Would change it:* a User requirement for interactive local preview before
the first build.

**F. User authority** 🧑 Defines the first slice's security posture —
normative policy. The delegated record itself is not approval.

---

### DEC-7102 — No fixed viewport width range

**A. Source** 📌 `PROPOSED` / `PENDING_USER_APPROVAL`. Title: "UQ-P10-02 —
No fixed viewport width range adopted."

**B. Problem** 🔶 Legacy asserted 320–1440px. D-P10-4 (APPROVED, User)
forbids importing legacy requirements without repository evidence. P10 still
needs a machine-checkable responsive criterion (HOME-ACC-08).

**C. Options** 📄 **A** — no numeric range; structural assertions only
(viewport meta present; no single fixed pixel width). **B** — adopt legacy
320–1440 with per-bound assertions (record: imports an unevidenced range;
forbidden by D-P10-4). **C** — named design breakpoints (record: no design
contract exists to justify them).

**D. Consequences** 🔶 Option A is implementable now via the stdlib reparse
check. B/C each invent a numeric contract with no evidentiary basis — what
D-P10-4 prohibits. No migration impact; breakpoints can be adopted later once
a design contract exists.

**E. Recommendation** ⭐ **Option A.** *Does not solve:* actual visual
responsiveness — it proves structure, not rendering. *Would change it:* a
User statement that a specific range is a genuine product requirement.

**F. User authority** 🧑 Product/quality policy.

---

### DEC-7103 — Evidence-based accessibility; no blanket WCAG AA

**A. Source** 📌 `PROPOSED` / `PENDING_USER_APPROVAL`. Title: "UQ-P10-03 —
Evidence-based accessibility checks; no blanket WCAG AA."

**B. Problem** 🔶 The legacy WCAG AA claim was recorded in the baseline audit
as asserted without citation. Under the stdlib-only, no-browser constraint
(HOME-ACC-19; P9/P10 boundary), AA *verification* is impossible today; an
unverifiable claim is what this governance system exists to prevent.

**C. Options** 📄 **A** — objective check list: language declared; viewport
meta present; exactly one `h1` with no heading-level jumps; images carry
CMS-authored alt text or are explicitly decorative. **B** — adopt a formal
conformance level (record: unverifiable blanket claim; forbidden by D-P10-4).

**D. Consequences** 🔶 Option A's four checks are already encoded in
HOME-ACC-08's reparse criteria. Option B requires either new tooling
dependencies (contradicting stdlib-only) or an unverifiable assertion.
Forward-compatible: criteria can grow.

**E. Recommendation** ⭐ **Option A.** *Does not solve:* real accessibility
for assistive-tech users — a floor, not conformance. *Would change it:*
authorization for browser-based/third-party a11y tooling.

**F. User authority** 🧑 Quality policy; also an honesty-of-claims decision.

---

### DEC-7104 — Design system not a prerequisite

**A. Source** 📌 `PROPOSED` / `PENDING_USER_APPROVAL`. Title: "UQ-P10-04 —
Design-system implementation is not a prerequisite for the first slice."

**B. Problem** 🔶 No design contract exists; requiring one blocks the first
slice indefinitely.

**C. Options** 📄 **A** — proceed under structural/content-safety/
output-safety/security criteria; design criteria apply forward only.
**B** — require a design-system contract first (record: blocks the first
slice without repository pressure).

**D. Consequences** 🔶 Option A keeps the machine-checkable bar intact —
nothing is weakened; design criteria are added later. Option B has no
evidentiary pressure. A future design contract can be imposed on later slices
without reworking Home.

**E. Recommendation** ⭐ **Option A.** *Does not solve:* visual quality —
Home will be structurally correct and plain.

**F. User authority** 🧑 Product priority.

---

### DEC-7110 — No invented performance thresholds; preserve CONF-001 and D-P10-4

**A. Source** 📌 `PROPOSED` / `PENDING_USER_APPROVAL`. Evidence: D-P10-4,
D-P10-5, REQ-P10-19, standing bound `CONF-001` ("UNRESOLVED — strictly no LCP
or INP thresholds invented; CWV verified via CLS ≤ 0.1 good / > 0.25 poor
only").

**B. Problem** 🔶 A *consolidation* decision: restates the exclusions already
approved in D-P10-4 and the standing bounds as one forward-binding record so
the initial slice cannot regress into unevidenced numeric gates.

**C/D. Options & consequences** 🔶 **A** — approve as written: no LCP/INP
thresholds, no viewport range, no blanket AA, no Lighthouse gates; P9 owns
SEO; CONF-001 stays unresolved. **B** — decline/defer: the same exclusions
still hold via D-P10-4 and CONF-001, so declining changes little today but
leaves the reaffirmation unrecorded.

**E. Recommendation** ⭐ **Option A**, with a dependency warning: 📄 DEC-7110's
text presupposes the outcomes of DEC-7102 and DEC-7103 ("no fixed viewport
range is imposed; no blanket WCAG AA requirement is asserted"). **Decide it
together with, or after, those two** — approving 7110 while deferring
7102/7103 would create an internally inconsistent record set.

**F. User authority** 🧑 Performance/quality policy.

---

## PART 2 — SIX RUNTIME-GATE SEMANTICS: DESIGN PROPOSALS (Phase C)

All six are 🔶 proposals. None is recorded normatively anywhere; adopting any
requires explicit User authorization (they define what "genuine evidence" and
"correct digest" *mean* — policy, not just code).

**Property vocabulary (kept distinct throughout):**
- **File existence** — path resolves.
- **Content integrity** — digest detects changes vs a trusted reference.
- **Provenance** — record of how/where an artifact was produced.
- **Cryptographic authenticity** — signature from a defined trust root.
- **Human authorization** — the human actually decided.

The repository has tooling for the first two only. Nothing here can establish
the last three, and these designs deliberately do not pretend to.

### 1. evidence-freshness
1. **Purpose:** bound evidence age relative to the slice decision.
2. **Requirement:** REQ-P10-09 c.5; DoD "no evidence missing, invalid or
   contradictory."
3. **Current:** UNIMPLEMENTED — "Path existence is not freshness."
4. **Missing:** a staleness policy.
5. **Proposed I/O:** evidence records gain `generated_at` (RFC 3339) +
   optional `freshness_window_days`; gate compares against gate-run time;
   missing timestamp → FAIL.
6. **Algorithm:** parse; compare; fail-closed.
7. **Failure:** FAIL naming the record.
8. **Positive tests:** fresh record passes.
9. **Negative tests:** stale fails; missing timestamp fails.
10. **Tampering tests:** a mutated `generated_at` is detectable only via
    gate-record cross-check — flagged as a limitation.
11. **Migration:** additive; old records without timestamps fail until
    regenerated.
12. **Security limitation:** a timestamp is self-declared; "fresh" ≠ "not
    backdated" (that needs a trusted clock or gate-record chaining).
13. **User decision:** 🧑 the window length — or "no window," which leaves
    the control permanently vacuous (the honest current state).

### 2. evidence-authenticity
1. **Purpose:** evidence is genuine and internally consistent.
2. **Requirement:** REQ-P10-09 c.5.
3. **Current:** UNIMPLEMENTED — "A resolved path is not authenticity."
4. **Missing:** a provenance/digest contract.
5. **Proposed I/O:** a defined **gate-record** JSON format (the gate's own
   docstring notes "no gate-record artifact schema exists"): producing
   command, input digests, output digests, UTC timestamp, emitting tool
   version.
6. **Algorithm:** gate recomputes digests of referenced artifacts and
   cross-checks them against the gate-record's claims; contradiction → FAIL.
7. **Failure:** FAIL naming the contradicted field.
8. **Positive:** consistent record passes.
9. **Negative:** missing record fails.
10. **Tampering:** digest mismatch fails; mutated record fails cross-check.
11. **Migration:** new artifact class; no backfill.
12. **Limitations — stated plainly:** this is *content integrity + provenance
    recording*, **not** cryptographic authenticity (no signatures, no trust
    root exists) and **not** human authorization. It proves artifacts agree
    with each other; it cannot prove who ran the gate or that a human
    sanctioned it.
13. **User decision:** 🧑 adopt the gate-record format at all; accept that
    "authenticity" in SPS2 means internal consistency pending any future
    signing mechanism (its own decision).

### 3. cms-state-digest
1. **Purpose:** bind inventory/slice to the exact CMS state it was derived
   from.
2. **Requirement:** REQ-P10-17 runtime verification; inventory schema: "the
   runtime gate recomputes it and fails closed on mismatch."
3. **Current:** UNIMPLEMENTED; field `null` ("No digest values are invented" —
   📄 D-P10-7/8 conditions).
4. **Missing:** serialization + algorithm.
5. **Proposed I/O:** digest over canonical CMS state files (`content.json`,
   `content_types.json`, `revisions.jsonl`).
6. **Algorithm (proposal):** canonical JSON (sorted keys, UTF-8, no
   insignificant whitespace) → SHA-256 → `sha256:<hex>`.
7. **Failure:** mismatch or null → FAIL.
8. **Positive:** unchanged state passes.
9. **Negative:** any semantic change fails; null fails.
10. **Tampering:** edited content fails; reordered keys still pass
    (canonicalization).
11. **Migration:** inventory regains a non-null value at next authorized
    regeneration.
12. **Limitation:** detects *change*, not *who changed it*.
13. **User decision:** 🧑 adopting the algorithm (the schema delegates
    recomputation but records no algorithm).

### 4. p8-contract-digest
Same scheme as #3, over the P8 contract inputs the slice references
(`content_types.json` — the ContentType definitions). Same tests, same
limitation, same 🧑 decision. Deliberately separate from #3 so a content edit
doesn't invalidate the *type* contract and vice versa.

### 5. req-p10-07-reconciliation
1. **Purpose:** declared `state_changing_operations` matches the actual
   backend surface (REQ-P10-07 is CRITICAL-risk: no operation reachable
   before its controls).
2. **Current:** UNIMPLEMENTED; declared value recorded "for inspection only."
3. **Missing:** the "actual" side has no machine-readable form.
4. **Proposed I/O:** a backend operation manifest (e.g.,
   `domain/backend/operations.json` — 📌 `domain/backend/` does not exist
   yet) listing every state-changing operation + required controls.
5. **Algorithm:** set-compare declared vs manifest; missing manifest → FAIL
   (fail-closed); manifest operation absent from declaration → FAIL;
   required-but-unimplemented controls → operation unreachable (negative test
   asserts).
6. **Failure:** FAIL naming the delta.
7. **Positive:** Home slice (empty==empty) passes.
8. **Negative:** undeclared manifest operation fails; phantom declared
   operation fails.
9. **Tampering:** manifest edit without re-declaration fails.
10. **Migration:** none — manifest arrives with the first backend code.
11. **Limitation:** the manifest is self-declared code; the control proves
    *consistency*, not real-world completeness — completeness needs a
    validator that actually enumerates backend routes.
12. **User decision:** 🧑 none beyond authorizing the implementation batch
    (📄 the empty-list representation `[]` is already defined; no new
    decision needed for it).

### 6. approval-state-interaction
1. **Purpose:** define how D-P10-8 (User approval of inventory *contents*,
   recorded in the decision ledger) interacts with `inventory.user_approval`
   (still `null`) and the terminal state
   `COMPLETE_VERIFIED_USER_APPROVED`.
2. **Current:** UNIMPLEMENTED; the gate observes and never writes (📌 code:
   "the gate never writes approval state").
3. **Missing:** the state machine and the meaning of the two approval loci.
4. **Proposed contract:** two distinct acts — (i) *contents approval* =
   D-P10-8, done, in the decision ledger; (ii) *inventory approval field* =
   `user_approval` in the artifact, set only by an authorized, separately
   approved act, never by the gate. Transition rule:
   `COMPLETE_AWAITING_USER_APPROVAL` → `COMPLETE_VERIFIED_USER_APPROVED`
   requires **both** the gate passing (all 16 controls) **and** a set
   `user_approval`; the transition is executed by a tool run under explicit
   User authorization; the gate stays read-only.
5. **Algorithm/failure:** while undefined, control 16 reports UNIMPLEMENTED;
   once defined, it verifies coherence (no APPROVED state with null approval,
   etc.).
6. **Positive:** both conditions met → transition allowed.
7. **Negative:** null approval + gate-pass → refused; set approval +
   gate-fail → refused.
8. **Tampering:** an agent-set `user_approval` is still caught by
   attribution's agent-detection denylist — but that is heuristic, not
   authentication.
9. **Migration:** none; the state machine is new.
10. **Limitations:** `decided_by: "User"` in the artifact remains a
    self-declaration — the same UQ-ATT-2 limit as everywhere else here.
11. **User decision:** 🧑 **the most policy-laden of the six**: whether
    D-P10-8's contents-approval may *also* be transcribed into
    `user_approval`, or whether a fresh approval act is required when the
    gate passes. ⭐ Recommend the latter (fresh act, at actual completion),
    but it is squarely the User's call.

---

## PART 3 — PROPOSED HOME SLICE CONTRACT (Phase D — design only; file NOT created)

Field-by-field for `sps2/project/SLICE-P10-01.json` against
`sps2.p10-slice/v1`:

| Field | Schema requirement | Proposed value / source | Covered by approved decision? | Gate validation |
|---|---|---|---|---|
| `slice_id` | `^SLICE-P10-[0-9]{2}$` | `"SLICE-P10-01"` — 📌 inventory's HOME-ACC criteria name exactly this id | Yes (D-P10-6 / HOME-ACC-01) 📄 | schema-structural; slice-id-uniqueness |
| `section_id` | string | `"home"` | ✅ DEC-7105 (APPROVED) | slice-required-fields; inventory cross-ref |
| `route` | `^/[a-z0-9/-]*$` | `"/"` | ✅ DEC-7105 | schema; HOME-ACC-13 uniqueness |
| `cms_content_references[0].content_id` | string | `"60e51f0536cb413e86e96ff6f750846a"` — 📌 the real persisted Home Content | Record exists; *referencing* it is new (blocker below) | published-only-content (runtime) |
| `.field_slots` | minItems 1, unique, set-equal to layout slots | `["heading","body"]` — 📌 registry verified: `home-default` consumes exactly `('heading','body')`; ContentType has exactly these fields | ✅ DEC-7106 + DERIVED ContentType | layout-slot-conformance |
| `.required_status` | enum, exactly `"published"` | **BLOCKER — see below** | — | published-only-content |
| `layout_id` | pattern | `"home-default"` | ✅ DEC-7106 | layout-slot-conformance (RESOLVED verified 📌) |
| `axis_contracts.frontend.renderer_entry_point` | non-empty string | **BLOCKER — no renderer exists** 📌 | No | gate must run it |
| `.produces` | enum | `"static_html_document"` | Consistent with D-P10-5 (string-composition approach) 📄 | — |
| `.encoding_contract` | enum | `"PER_SINK_HTML_ESCAPE"` | ✅ mechanism exists 📌 (`encode_for_html`, `escape_json_ld_for_html`) | reparse/round-trip checks |
| `cms.consumption_boundary` | enum | `"P8_SAFE_OUTPUT"` | ✅ boundary exists 📌 | — |
| `backend.exposure_class` | enum | `"LOCAL_NON_NETWORK_EXPOSED"` | ⏳ **pending DEC-7101** | exposure-declaration |
| `backend.state_changing_operations` | required; `[]` allowed | `[]` | ✅ DEC-7108 (declaration intent) | req-p10-07-reconciliation |
| `data.data_dependencies` | array | `[]` | ✅ DEC-7108 | — |
| `data.project_local` | enum `[true]` | `true` | Consistent with D-P10-1 boundary | — |
| `validation.schema_validation` / `.reparse_validation` | boolean | `true` as *declarations* — the gate re-validates and is the only authority (📄 schema wording) | — | gate recomputes |
| `assets.asset_references` | array | `[]` | ✅ DEC-7107 (explicit empty by decision; HOME-ACC-22 = NOT APPLICABLE, not a pass) | — |
| `seo.audit_mode` | enum | `"P9_DEPLOYMENT_AUDIT"` | ✅ DEC-7109 (four P9 contract refs verified on disk 📌) | p9-deployment-audit (needs build) |
| `tests.test_entry_point` | non-empty string | **BLOCKER — no slice test suite exists yet** | No | gate must run it |
| `acceptance_state` | enum | `"DRAFT"` at authoring; `"AWAITING_USER_APPROVAL"` when complete; `"APPROVED"` only after 🧑 | — | schema conditional; approval-authenticity |
| `evidence_references` | **minItems 1** | **BLOCKER — no evidence records exist to reference**; produced by harness stage 8 | No | evidence-references + freshness/authenticity |
| `rollback_reference` | string/null | Design needed: revert = remove build output + slice record; rehearsal required (HOME-ACC-23) | No | — |
| `user_approval` | object/null; APPROVED requires non-null | `null` — **never set by an agent** 🧑 | — | approval-authenticity; approval-state-interaction |

**Blockers preventing legitimate creation today** (dependency order):

1. 🧑 **No authorization exists** — 📄 the delegation record states none of
   the ten decisions "authorizes… a slice contract." Authoring requires an
   explicit User grant.
2. **`required_status: "published"` cannot be declared honestly** — 📌 the
   only Home Content is `status: "draft"`, `published_at: null`. Declaring
   `published` would be a fabricated declaration. Publication is a P8
   workflow act needing its own authorization. (Note 📄: P8 has a recorded
   internal status-vocabulary disagreement — `validation.py` knows `preview`,
   the schema/model don't; irrelevant here since `published` is agreed by all
   sources, and outside this round's scope.)
3. **`renderer_entry_point` and `test_entry_point` reference nothing that
   exists** — 📌 no renderer, no build, no harness, no `domain/backend/`.
4. **`evidence_references` has nothing to point at** — evidence comes from
   harness runs that cannot run without 2–3.

**Schema/inventory discrepancies:** none found — the 24 HOME-ACC criteria map
cleanly onto the schema's constraints; `minItems: 1` on content references
and the `published` enum are consistent with HOME-ACC-04/05. No schema
modification proposed.

---

## PART 4 — DEPENDENCY GRAPH & IMPLEMENTATION ROADMAP (Phase E)

```
[5 pending decisions]──┐
[D-P10-8 already done]─┤
                       ▼
        B1: authorize + author SLICE-P10-01.json (DRAFT)
                       │
        C1: authorize + define six gate semantics (normative record)
                       │
        B2: implement semantics in gate + tests ──► gate still FAILs (no build)
                       │
        B3: implement renderer + build (stdlib, in-process)      [needs DEC-7101]
                       │
        B4: implement integration harness (9-stage contract) ──► evidence records
                       │
        C2: authorize + publish Home content (draft→published)   [P8 workflow act]
                       │
        B5: run harness → evidence bundle → gate re-run
                       │
        🧑 USER: approve slice (acceptance_state APPROVED + user_approval)
                       │
        C3: authorized transition to COMPLETE_VERIFIED_USER_APPROVED
                       │
        B6: CI tracking/manifest additions (after tracking decision)
```

### Batches

| # | Batch | Files | Depends on | Authorization | Independently proceeds? |
|---|---|---|---|---|---|
| **A1** | Six-semantics *proposal* (this document; no repo change) | — | — | None | ✅ done |
| **B1** | Author `SLICE-P10-01.json` (DRAFT, honest blockers declared) | `sps2/project/SLICE-P10-01.json` (new) | 5 decisions approved + explicit slice-authoring grant | 🧑 narrow explicit | Only after decisions |
| **B2** | Gate semantics implementation + unit tests | `sps2/tools/p10_runtime_gate.py`, `sps2/tests/test_p10_runtime_gate.py` (both currently **untracked** — editing untracked files also needs authorization) | B1 (realistic fixtures) | 🧑 narrow explicit | Partly (algorithms can be built before the slice exists) |
| **B3** | Renderer + build (`domain/frontend/render.py`, build entry; stdlib-only, in-process per DEC-7101) | `domain/frontend/` | B1, DEC-7101 | 🧑 explicit P10 implementation grant | No |
| **B4** | Integration harness per the 9-stage contract | `sps2/tools/p10_harness.py` (new) or `domain/frontend/harness.py` | B3 | 🧑 explicit | No |
| **C1** | Normative recording of the six semantics | requirements/decision records (protected instruments) | B2 design accepted | 🧑 substantive | No |
| **C2** | Publish Home content (`draft`→`published`, real author attribution) | `domain/cms/data/content.json` | B3; publication is *distinct and consequential* | 🧑 explicit, separate from implementation | No |
| **C3** | Slice approval + state transition | slice doc, inventory | gate PASS | 🧑 the User, personally | No |
| **B6** | CI: track gate/tests + manifest sync | untracked files → tracked; `.github/expected-test-modules.txt` | tracking decision | 🧑 narrow | No |
| **D** | Deferred | network exposure (D-P10-1 controls), further sections, design system, P8 `preview` status reconciliation | — | — | — |

**Negative controls per batch (pattern):** every new control lands with a
test that fails when the control is removed (HOME-ACC-20); digest controls
get tamper tests; harness stage 7 is itself a negative suite.
**Rollback:** each batch is one commit-sized change set; the slice document is
versionless-replaceable pre-approval; `rollback_reference` + rehearsal covers
the built slice (HOME-ACC-23).
**Publication is never bundled** with implementation — its own authorization,
its own commit.

---

## PART 5 — USER DECISION INTERFACE (Phase F)

> Response format (illustration only, not a recommendation):
> `DEC-7101: OPTION A` … or `DEFER` for any line.

---

**DECISION 1 — slice-contract authoring** *(the pivotal one; not one of the
five, but nothing proceeds without it)*

- **Current status:** No authorization exists; 📄 the delegation record
  explicitly excludes "a slice contract" from everything approved so far.
- **QUESTION:** May the agent author `sps2/project/SLICE-P10-01.json`
  (initially `acceptance_state: "DRAFT"`, with honest placeholders for the
  not-yet-existing renderer/tests/evidence)?
- **OPTION A — Authorize authoring (DRAFT only):** unblocks B2–B4 design
  work; no runtime effect; nothing is claimed complete. *Risk:* minimal — a
  draft document asserts nothing.
- **OPTION B — Defer until implementation is authorized:** keeps the
  repository slice-free; B3/B4 then need design docs instead of a real
  contract. *Risk:* slower, more indirection.
- **RECOMMENDED:** A.
- **AFFECTED:** new file only.
- **DOWNSTREAM:** enables the whole B-track.
- **USER RESPONSE:** `SLICE-AUTHORING: AUTHORIZE` / `DEFER`

---

**DEC-7101: OPTION A (pure in-process, `LOCAL_NON_NETWORK_EXPOSED`, no
socket)** — narrowest blast radius; no auth/CSRF/rate-limit work triggered;
P9 contract satisfied statically. Alternative B (loopback bind) creates an
undefined evidence obligation. Alternative C blocks the slice.
→ `DEC-7101: OPTION A` / `OPTION B` / `DEFER`

**DEC-7102: OPTION A (no viewport range; structural assertions)** — honors
D-P10-4; machine-checkable today. The 320–1440 range is unevidenced legacy.
→ `DEC-7102: OPTION A` / `DEFER`

**DEC-7103: OPTION A (objective a11y checks; no blanket AA)** — AA is
unverifiable under stdlib-only constraints; the four checks are already
encoded in HOME-ACC-08. → `DEC-7103: OPTION A` / `DEFER`

**DEC-7104: OPTION A (design system not a prerequisite)** — unblocks the
slice without weakening any machine-checkable criterion.
→ `DEC-7104: OPTION A` / `DEFER`

**DEC-7110: OPTION A (reaffirm exclusions; preserve CONF-001)** — ⚠️ decide
**together with or after** DEC-7102/7103 (its text presupposes their
outcomes). → `DEC-7110: OPTION A` / `DEFER`

---

**DECISION 7 — approval-mechanism semantics** *(from the six-semantics work;
UQ-P10-06 + approval-state-interaction)*

- **QUESTION:** When the gate eventually passes, does D-P10-8's
  contents-approval carry over to `user_approval`, or is a fresh, explicit
  approval act required at that time?
- **OPTION A — Fresh act required (recommended ⭐):** approval is
  contemporaneous with actual completion; cleanest provenance.
- **OPTION B — D-P10-8 carries over:** fewer steps, but approves based on
  2026-10-13 contents, not the completed artifact.
- **AFFECTED:** inventory `user_approval`, gate control 16, the state
  machine.
- **USER RESPONSE:** `APPROVAL-MECHANISM: OPTION A` / `OPTION B` / `DEFER`

**DECISION 8 — digest/evidence semantics adoption** *(may be deferred
independently)*

- **QUESTION:** Adopt the proposed canonical-JSON + SHA-256 digest scheme and
  the gate-record format (with the explicit understanding that this is
  content-integrity/provenance, *not* cryptographic authenticity or human
  authentication)?
- **USER RESPONSE:** `SEMANTICS: ADOPT` / `DEFER`

**DECISION 9 — Home content publication** *(needed only at stage C2; noted
now for planning)*

- **QUESTION:** Once the renderer exists, may the Home Content be published
  (`draft`→`published`) through the P8 workflow, with real author
  attribution?
- **USER RESPONSE:** `PUBLICATION: AUTHORIZE` / `DEFER`

**Dependencies:** 7102 + 7103 → 7110. Slice-authoring → the whole B-track.
Publication (9) → gate PASS → approval (7's mechanism) → transition.

---

## PART 6 — UNVERIFIED CLAIMS & REMAINING UNCERTAINTIES

- 🧑-shaped uncertainty throughout: every `decided_by: "User"` — including
  D-P10-5–D-P10-8 and DEC-7105–7109 — is an unsigned record assertion; the
  *records* were verified, the *human acts* were not (UQ-ATT-2 remains open).
- The CMS data files' origin is self-declared (timestamps + provisional
  author string `p10-provisional-draft-author (not a human author;
  not User-approved)`); no digest attests their derivation — precisely what
  controls 3/4 would fix once adopted.
- Whether a loopback-bind option would ever be wanted (DEC-7101 Option B) is
  a product preference not inferable from the repository.
- The six semantics designs are 🔶 engineering proposals; the repository
  records *no* prior art for digest algorithms or evidence policy — nothing
  to reconcile against, and nothing to cite as precedent.

---

## REQUIRED FINAL DECISION BRIEF

1. **What the five decisions ask:** DEC-7101 — may the first slice run with
   no socket at all (pure in-process)? DEC-7102 — may P10 adopt *no* numeric
   viewport range, using structural assertions instead? DEC-7103 — may
   accessibility be judged by four objective checks rather than a blanket
   WCAG AA claim? DEC-7104 — is a design system formally *not* required
   before the first slice? DEC-7110 — reaffirm: no invented LCP/INP
   thresholds, no Lighthouse gates, P9 owns SEO, CONF-001 stays unresolved?

2. **Recommendations and why:** Option A on all five — each is the
   alternative best supported by repository evidence (D-P10-4's
   anti-legacy-import rule, the stdlib-only constraint, the P9-audit-suffices
   fact, and the absence of any design contract), and none weakens a
   machine-checkable criterion. DEC-7110 should be decided with/after
   7102+7103.

3. **Technical vs policy:** the *implementations* (structural checks, digest
   computation, reconciliation compare) are technical; the *choices* —
   security posture (7101), quality bars (7102/7103/7110), sequencing
   (7104), the approval mechanism (Decision 7), and what "authentic evidence"
   means (Decision 8) — are policy, and the User's.

4. **Proposed Home slice contract:** fully specified in Part 3 —
   `SLICE-P10-01`, section `home`, route `/`, the real Content record
   referenced with slots `heading`/`body` against layout `home-default`,
   `LOCAL_NON_NETWORK_EXPOSED`, empty backend/data/assets declarations, P9
   deployment audit, `acceptance_state: DRAFT`, `user_approval: null`.

5. **What prevents legitimate creation today:** (a) no authorization — the
   delegation record explicitly withholds slice-contract authority from
   everything approved; (b) the referenced content is `draft`, so
   `required_status: "published"` would be a false declaration; (c) the
   renderer, test suite, and evidence records the schema requires the
   document to name do not exist.

6. **Smallest safe implementation batch after the decisions:** authorize +
   author the DRAFT slice document (one new file, asserts nothing), then
   implement the six gate semantics with their negative/tamper tests — both
   independently verifiable, neither touching protected instruments nor CI.

7. **Exact responses needed:** the nine decision lines in Part 5 (five
   DEC-71xx, plus SLICE-AUTHORING, APPROVAL-MECHANISM, SEMANTICS,
   PUBLICATION) — any of which may be `DEFER`.

8. **Was the repository left unchanged?** **Yes** — verified: no file
   created/edited/staged/committed/pushed during the analysis; working tree
   byte-identical before and after (18 paths, as at Round 10); no governance
   record touched. (The single file written this round is this report itself,
   created at the User's explicit standing instruction, as a new file — no
   prior report overwritten.)

---

*Stopping point: awaiting the User's decision lines. No implementation phase
begins until the User reviews the decisions and supplies explicit
authorization.*
