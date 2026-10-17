# AUDIT-ROADMAP-P3 — Readiness & Decision Audit

Audit date: 2026-10-04
Auditor: implementation agent (**not** a User; this audit is **not** an approval)
HEAD at audit: `fc3d271bc9b0cd590a574ac29037e3e4116daeb6`
Subject: **Roadmap P3 — Agent Interoperability** (recorded `NOT_SATISFIED` in
`REC-PHASES-0001`).
Status: **PLAN AND DECISION SUPPORT ONLY. ROADMAP P3 NOT STARTED / NOT
AUTHORISED. P7 NOT STARTED. Awaiting User decisions.**

**Disambiguation (read first).** "Roadmap P3" here is the authoritative roadmap
phase *Agent Interoperability* (`.sps/architecture/SPS2-ROADMAP.md`), **not** the
executed phase P3 (*Production Capability*, `sps2/decisions/P3-DECISIONS.json`).
The executed phase already happened; the roadmap phase has never been executed.
This audit concerns only the roadmap phase.

---

## 0. Scope and restraint

This document prepares a **bounded completion plan for roadmap P3** and reports
the exact User decisions required before its implementation may begin. It is
decision support only:

- No roadmap P3 implementation, no adapter, no conformance test, no install.
- No runtime activation; no capability promoted; CAP-P03-005 stays
  `DEFERRED / NOT_PROMOTED`.
- The production capability registry is byte-identical
  (`sha256 5f95f62b03851748f95ac501221597f95243aae80f69cde2a8aea9105537af56`).
- `CONF-001` remains `UNRESOLVED`; no LCP/INP threshold was invented.
- The threat model required by D-P7-D remains a **separate prerequisite**; this
  audit does not author the threat model and does not claim it is satisfied.
- No legacy file was modified; legacy diff 0.
- No existing decision record, reconciliation record, or guard was modified.
- Nothing was pushed.

---

## 1. What the roadmap defines as roadmap P3

Quoted verbatim from `.sps/architecture/SPS2-ROADMAP.md`:

- **Objective:** Prove portability with real adapters.
- **Dependencies:** P2. **Scope:** `core/adapters/` contract + adapters.
- **Forbidden:** adapters adding or weakening core rules.
- **Deliverables:** `contract.schema.json`; adapters; conformance test.
- **Acceptance:** deleting **all** adapters leaves core validators passing; a
  fresh agent can resume the project from `.sps/` alone.
- **Verification:** portability suite (4 criteria, `SPS2-AGENT-INTEROPERABILITY.md`
  section 7). **Approval:** user.
- **Rollback:** delete adapters; core unaffected.

The four verification criteria, verbatim from
`.sps/architecture/SPS2-AGENT-INTEROPERABILITY.md` section 7 — a candidate build
is portable only if:

1. The core test suite passes with **no adapter installed**.
2. Deleting every adapter directory does not break any core validator.
3. A fresh agent, given only `.sps/` + `docs/`, can determine phase, task, next
   and forbidden actions.
4. No core file references a vendor name (enforced by a grep-based CI check).

Boundary rules that any P3 work inherits from the same architecture document
(section 2): an adapter may render core rules, map paths, declare capabilities,
provide prompts, or be absent entirely — and must **not** add/weaken/reinterpret
a rule, move canonical state outside the project, assume unverified
capabilities, duplicate the lifecycle state machine, or be required for the
system to function.

---

## 2. Current state as verified

Roadmap P3 status, quoted from `sps2/decisions/ROADMAP-EXECUTION-RECONCILIATION.json`
(`REC-PHASES-0001`):

| Deliverable | Recorded status | Evidence in the record |
|---|---|---|
| `contract.schema.json` | PRESENT | `sps2/core/adapters/contract.schema.json` |
| adapters | INSUFFICIENT | "one adapter only, id 'generic', maturity DECLARED; roadmap requires real adapters" |
| conformance test | ABSENT | "no portability or delete-all-adapters test in sps2/tools/" |

Acceptance recorded unmet: the delete-all-adapters condition is untested, and
no fresh-agent resume/onboarding dry run exists.

Additional facts verified directly for this audit:

- `sps2/core/adapters/registry.json` holds exactly one entry, `generic`,
  `maturity: DECLARED`, `writes_global_state: false`.
- `sps2/core/adapters/generic/` exists but is **empty and untracked**; git
  tracks only `README.md`, `contract.schema.json`, `registry.json` under
  `sps2/core/adapters/`. "Deleting every adapter directory" therefore currently
  deletes an empty, untracked directory — the *registry entry* is the only
  tracked representation of an adapter today.
- No portability or adapter-named tool exists in `sps2/tools/`.
- Reusable conformance machinery already exists in `sps2/core/adapter_registry.py`:
  `validate_adapter` (required fields, agent_id pattern, maturity enum,
  `writes_global_state` must be `false`, `detection.read_only` must be `true`
  when present, capabilities object, supports list, fallbacks object),
  `validate_registry` (shape, per-adapter checks, duplicate-id rejection,
  summary incl. `all_write_project_local`), and `core_is_adapter_free` (no core
  module outside `adapters/` imports an adapter; `registry_api` exempt). Its
  callers today are `validate-p5.py`, `sps5.py` and `sps2/tests/test_p5.py`.
- A valid zero-adapter state is already *proven* by unit test
  (`test_boundary_empty_adapter_registry`: empty `adapters` list validates with
  no errors), and a duplicate adapter id is rejected
  (`test_negative_duplicate_adapter_id`).
- Two guards will interact with real adapters (see section 4):
  `validate-sps2.sh` section 8 already excludes `/adapters/` from its
  vendor-name grep over `core/`; but `sps2/tests/test_p5.py::TestAgentNeutrality`
  walks all of `sps2/core` (including `adapters/`) and will fire on any
  vendor-named adapter file; and `validate-p7-readiness.py` pins the adapter
  state as exactly one adapter at `DECLARED`, so the first real adapter will
  raise `ADAPTER_STATE_CHANGED` by design.
- Project state today spans two trees: `.sps/` (`STATE.md` records PHASE-05
  APPROVED / COMPLETE) and `sps2/` (`handoff/HANDOFF-P1..P6`, `decisions/`
  including both P7 readiness records, `tasks/`, `evidence/`). The newest
  phase state (P6 APPROVED, P7 blocked) lives in `sps2/`, not `.sps/`. Root
  `docs/` does not exist; `sps2/docs/adr/` contains only a README.

---

## 3. Bounded completion plan

### 3.1 Required real adapters

"Real" must mean more than a second registry row: the roadmap objective is to
*prove portability*. The bounded plan is:

- Keep `generic` untouched in role (it must remain sufficient on its own, per
  architecture section 6: an unknown agent still gets correct behaviour from
  repository state alone).
- Add a **small, named set** of per-agent adapters (count and identity is
  decision D-P3-A). Each adapter deliverable is:
  1. one contract-conformant entry in `sps2/core/adapters/registry.json`;
  2. a directory `sps2/core/adapters/<agent-id>/` holding any adapter-owned
     content that decision D-P3-C permits;
  3. a truthful `maturity` value with the evidence behind it (decision D-P3-B);
  4. a declared `maintainer` and, where applicable, `verified_by`.
- Hard bounds: no agent binary is executed, installed, or required; detection
  is declarative and read-only; nothing is written outside the project; the
  adapter set stays small enough that every member can be conformance-checked
  and deleted in one commit.
- The architecture's target-agent table (section 6) is the candidate pool.
  Its own risk column already marks Gemini/Antigravity **high** risk
  ("does not reliably auto-load skills"), so a "build all six" reading is not
  a bounded plan and is not recommended.

### 3.2 Adapter contract requirements

The machine-authoritative source is `sps2/core/adapters/contract.schema.json`:

- Required fields: `agent_id` (lowercase pattern), `maturity`
  (`VERIFIED|EXPERIMENTAL|DECLARED`), `writes_global_state` (const `false`),
  `capabilities` (object of booleans), `supports` (list), `fallbacks`
  (object), `maintainer`. Optional: `display_name`, `detection`
  (`read_only` const `true`), `verified_by`. `additionalProperties` is `false`.
- Invariants every new adapter must satisfy, enforced by the existing
  `adapter_registry.py` checks without weakening them:
  - no machine-global state (`writes_global_state` is `false`, forced by enum
    const in the schema and re-checked in code);
  - detection is read-only when declared;
  - one-way dependency: the core never imports, references, or branches on an
    adapter (`core_is_adapter_free` + `validate-sps2.sh` section 8);
  - no duplicate `agent_id`;
  - an adapter is never required for the system to function.
- Maturity must be truthful. `VERIFIED` may only be claimed with recorded
  evidence of the adapter actually being exercised; otherwise the honest value
  is `EXPERIMENTAL` (architecture section 4) or `DECLARED`. A self-asserted
  `VERIFIED` label is exactly the defect class that keeps CAP-P03-005 blocked
  at Gate F, and must not be reproduced in an adapter.
- Documentation note (not a defect introduced here): architecture section 4
  prose names the field `author`, while the schema requires `maintainer`. The
  schema is authoritative for machine checks; P3 adapters must satisfy the
  schema. Aligning the prose is a separate documentation question, out of
  scope for this audit.

### 3.3 The portability conformance test

The four section-7 criteria map to concrete assertions the P3 conformance test
must prove, with the existing machinery reused:

| Criterion | Concrete assertion for P3 |
|---|---|
| 1. suite passes with no adapter | full existing suite green in the normal state, and green again in the zero-adapter state (criterion 2's state) |
| 2. deleting every adapter directory breaks no core validator | definition of what is deletable per D-P3-D; recommended mechanics: perform deletion on a **copy** of the tree (or move-and-restore with a verified restore) so the working repo is never left damaged; assert all core validators pass with adapters absent |
| 3. fresh agent resumes from repository state alone | a recorded dry run that reads only the D-P3-E target set and answers: current phase, current task, next action, forbidden actions; the evidence names the exact files read |
| 4. no core file references a vendor name | extend the existing grep check to assert the only sanctioned vendor-name location is `adapters/`; `core_is_adapter_free` covers the import direction |

Operational bounds: the suite lives in `sps2/tools/` following the `test-*.sh`
convention, emits a count line like the existing suites, and carries negative
controls (it must fail when a core file names a vendor outside `adapters/`,
when the registry is malformed, and when a core module imports an adapter).
It may perform no install and no network access, and it must restore the tree
exactly (verified by `git status` clean afterwards and the normal-state suite
green).

### 3.4 Project-local scope

- All P3 artefacts live under `sps2/core/adapters/` (roadmap scope: "core/adapters/
  contract + adapters"), plus the conformance tool in `sps2/tools/` and its
  evidence record in `sps2/evidence/`.
- Detection entries are declarations; no subprocess execution, no global
  config writes, no writes outside the repository; the `writes_global_state:
  false` invariant is architectural, not advisory.
- Adapters remain optional and disposable: the system must work with zero of
  them, which is what criteria 1 and 2 test.

### 3.5 Security and attribution requirements

Security (all machine-checkable where possible):

- `writes_global_state: false` and read-only detection are non-negotiable
  contract invariant (no machine-global state, ever, without its own explicit
  User approval — which this plan does not seek).
- No adapter content may carry a credential or credential-shaped value; the
  existing `scan_secrets.py` + `test-secret-safety.sh` remain the gate.
- No network access, no installs, no subprocess execution of agent binaries;
  `detection` entries are declarative file/CLI *names*, not invocations.
- An adapter may never add, weaken or reinterpret a core rule, and the core
  validator suite must pass before and after adapter presence — so an adapter
  cannot smuggle a rule change past the phase validators.
- Unknown agent -> `generic` path must keep working even with every concrete
  adapter absent (criterion 1/2 state).

Attribution:

- Every adapter declares `maintainer`; `verified_by` present only where a
  real verification was performed (truthfulness rule of section 3.2).
- Roadmap verification for P3 says "Approval: user" — P3 cannot self-approve,
  and neither can any agent. The three axes IMPLEMENTED / VERIFIED / APPROVED
  stay independent, with approval by the User alone.
- Decision records, evidence and the conformance-test output must be
  User-attributable where they carry approval semantics; the existing
  attribution guards (`check_sps2.py`, `check_p2.py`, `validate-p4.sh`
  attribution checks, `governance/attribution.py`) already reject
  agent-attributed approvals and must keep doing so.

### 3.6 Acceptance criteria

Roadmap P3 is satisfied when, with a record evidencing each item:

1. Real adapters exist beyond `generic` (set per D-P3-A, maturity per D-P3-B),
   each contract-conformant under the unchanged `adapter_registry.py` checks.
2. The portability conformance test exists and passes: normal state green,
   zero-adapter state green (delete-all mechanics per D-P3-D), fresh-agent
   dry run recorded (target set per D-P3-E), vendor-name grep green with
   `adapters/` as the only sanctioned location.
3. The full existing suite (all phase validators, mutation suites, unit tests,
   snapshot and boundary suites, secret-safety, governance, history-credential,
   emoji) is green in the delivered state — with the deliberate, recorded
   guard updates of D-P3-G applied where the delivered state legitimately
   changes what those guards pin. No other guard may be weakened, and no
   guard may be edited silently.
4. Rollback is demonstrated (section 3.7) and the legacy diff remains 0.
5. User approval of the delivered state (roadmap: "Approval: user").

### 3.7 Rollback and removal criteria

- Roadmap rollback: "delete adapters; core unaffected." Concretely: removing
  the adapter directories, their registry entries, and any adapter-authored
  files permitted by D-P3-C returns the system to the exact pre-P3 state, in
  one reverting commit, with the normal suite green before and after.
- Removal must leave a *valid* zero-adapter state; that this is valid is
  already proven by `test_boundary_empty_adapter_registry`.
- Removal procedure is part of the P3 deliverable: documented, rehearsed once
  and recorded as evidence, and it must not require touching the core,
  `.sps/`, the production capability registry, or any legacy file.
- The conformance test itself is removable: deleting the test tool may not
  break any core validator once the P7-readiness guard update (D-P3-G) has
  been applied.

### 3.8 Dependencies required before P7 can begin

Unchanged from `AUDIT-P7-READINESS-AND-DECISION.md` section 5; this plan
resolves none of them and claims none satisfied:

| # | Prerequisite | Source | Status | Owned by |
|---|---|---|---|---|
| 1 | Real adapters beyond `generic` | D-P7-B | NOT DONE | roadmap P3 (this plan) |
| 2 | Delete-all-adapters conformance test | D-P7-B | NOT DONE | roadmap P3 (this plan) |
| 3 | Fresh-agent resume from repository state alone | D-P7-B | NOT DONE | roadmap P3 (this plan, D-P3-E) |
| 4 | Written threat model for persistent project-local state | D-P7-D | NOT DONE | **separate prerequisite, untouched** |
| 5 | Threat model treatment of two-project isolation and memory rollback | D-P7-D | NOT DONE | **separate prerequisite, untouched** |
| 6 | Roadmap P2 confirmed under D-P7-A | D-P7-A | SUBSTANTIALLY SATISFIED | roadmap P2 (not this plan) |
| 7 | Explicit User authorisation to begin roadmap P3 work | standing rule | NOT GIVEN | **decision D-P3-F below** |
| 8 | Explicit User authorisation to begin P7 | standing rule | NOT GIVEN | P7 (not this plan) |

Items 4–5 are deliberately *not* folded into roadmap P3: D-P7-D makes the
threat model its own prerequisite, and this audit neither authors it nor
claims it satisfied.

---

## 4. Conflicts and couplings found

1. **Delete-all wording vs core-owned presence checks (blocking).** The
   acceptance text ("deleting **all** adapters leaves core validators
   passing") read maximally would include `contract.schema.json` and
   `registry.json` — but `validate-sps2.sh` *requires* `core/adapters/`,
   the contract and the registry to be present (sections 1 and 8). As
   written, the maximal reading is unmeetable without amending an approved
   validator. Disposition: decision D-P3-D defines what "all adapters" means.
2. **The P7-readiness adapter pin will fire by design (operational).**
   `validate-p7-readiness.py` pins "exactly one adapter, `DECLARED`". The
   first real adapter makes the suite red with `ADAPTER_STATE_CHANGED`. That
   is the guard working — but it must be updated deliberately, in the same
   record as the change, never silently. Disposition: decision D-P3-G.
3. **`TestAgentNeutrality` walks `adapters/` too (operational).**
   `sps2/tests/test_p5.py` scans all of `sps2/core` for vendor names,
   including `adapters/`, while the sanctioned exception elsewhere
   (`validate-sps2.sh` section 8, `core_is_adapter_free`) excludes
   `adapters/`. A vendor-named adapter fails the unit test today.
   Disposition: decision D-P3-G.
4. **"Fresh agent from `.sps/` + `docs/` alone" is stale and partly absent
   (blocking interpretation).** Root `docs/` does not exist; `.sps/STATE.md`
   still reads PHASE-05 COMPLETE while the newest phase state (P6 APPROVED,
   P7 blocked) lives in `sps2/`. As literally worded, the criterion points a
   fresh agent at a stale state tree. Disposition: decision D-P3-E.
5. **No tracked adapter directory content exists yet.** `sps2/core/adapters/generic/`
   is empty and untracked; today's only adapter representation is a registry
   row. The delete-all test is therefore meaningful only once real adapters
   add tracked content — the test must not be claimed before then.
   Disposition: folded into D-P3-D.
6. **Prose/schema field-name mismatch (`author` vs `maintainer`).** Noted in
   section 3.2; the schema governs; nothing was changed by this audit.

None of these was changed or pre-empted by this audit. Nothing in section 4
is resolved here; each is routed to a User decision.

---

## 5. Validation evidence

Suite re-run for this audit, with this file present in the tree:

| Suite | Result |
|---|---|
| `validate-p2.sh` | 69 passed, 0 failed, 22 negative cases |
| `validate-p3.sh` | 67 passed, 0 failed, 18 negative/positive controls |
| `validate-p4.sh` | 59 passed, 0 failed, 22 negative cases, 7 controls |
| `validate-sps2.sh` | 72 passed, 0 failed, 25 negative cases |
| `validate-p5.py` | 46 passed, 0 failed, 18 negative cases, 1 control |
| `validate-p6.py` | 65 passed, 0 failed, 24 negative cases, 1 control |
| `validate-p7-readiness.py` | 30 passed, 0 failed, 7 negative cases |
| `sps2/tests` unit tests | 39 ran, OK |
| `test-snapshot-integrity.sh` | 9 caught, 0 missed |
| `test-phase-boundary.sh` | 11 caught, 0 missed |
| `test-p7-readiness-mutation.sh` | 19 caught, 0 missed (readiness) + 11 caught, 0 missed (phase validators) |
| `test-secret-safety.sh` | 9 checks, 0 failed |
| `.sps` governance | 54 passed, 0 failed |
| `test-history-credential-check.py` | all 4 scenarios behaved as required |
| `check_emoji.py sps2` | scanned 117, violations 0 |

Invariants confirmed in the same run: production registry
`sha256 5f95f62b03851748f95ac501221597f95243aae80f69cde2a8aea9105537af56`
(unchanged); CAP-P03-005 still deferred (blocked by gates F and K); legacy
diff 0; checkpoint `a7767cf` present; working tree clean after the suite.

---

## 6. Exact User decisions required before roadmap P3 implementation

All seven are open. Each is a single question; recommendations are marked as
recommendations, not decisions. Names use `D-P3-*` and refer to **roadmap**
P3 only.

**D-P3-A — Which agents get real adapters, and how many. [BLOCKING]**
Options: (1) minimum two beyond `generic`, the low-risk AGENTS.md targets from
the architecture table (Codex, OpenCode); (2) three, adding Claude Code;
(3) all target agents (includes the high-risk Gemini/Antigravity entry);
(4) the User names the exact set; (5) minimum one. Recommendation: (1) or (4).

**D-P3-B — What makes an adapter "real" for acceptance: maturity and
evidence. [BLOCKING]**
Options: (1) at least one adapter exercised in a recorded dry run at maturity
`VERIFIED`, others `EXPERIMENTAL`; (2) `EXPERIMENTAL` for all (honest when no
agent can be exercised here) with `generic` fallback guaranteed; (3)
`DECLARED` only. Not recommended: (3) — it would leave "real adapters"
unproven and risks a P3 marked satisfied on paper only. Note: `VERIFIED` may
never be self-asserted; the honesty rule of section 3.2 binds.

**D-P3-C — Adapter deliverable shape. [BLOCKING]**
Options: (1) declarative-only — registry entry plus content confined to
`sps2/core/adapters/<agent-id>/`; (2) adapters may also author agent-convention
files inside the repository (e.g. a root-level AGENTS.md or agent rule files),
tracked, listed as part of that adapter and deleted with it; (3) no
agent-specific content at all — entries and the conformance test only (weakest
against "real adapters"). Recommendation: (1).

**D-P3-D — Definition of "adapter" for the delete-all criterion. [BLOCKING]**
Options: (1) recommended — an adapter is its per-agent registry entry and its
`<agent-id>/` directory (plus any files D-P3-C authorises); `contract.schema.json`,
`registry.json` and `README.md` are core-owned boundary artefacts that must
survive, with the registry emptied to the already-proven valid
`{"adapters": []}` state; (2) treat the registry file itself as deletable too
— this requires amending the approved `validate-sps2.sh` presence checks and is
not recommended.

**D-P3-E — Fresh-agent resume: target set and method. [BLOCKING]**
Options: (1) repository-as-a-whole (recommended): the dry run may read the
repository without any agent memory (`.sps/` + `sps2/` + README/CATALOG),
because the newest phase state legitimately lives in `sps2/`; (2) literal
`.sps/` + `docs/` only, which today is stale (PHASE-05) and lacks the
referenced root `docs/`; (3) both, recorded separately. Method sub-choice:
mechanically executed checklist by a fresh session (recommended) versus a
narrative dry run. Either way the evidence must name the files read and the
phase/task/next/forbidden answers obtained.

**D-P3-F — Explicit authorisation to implement roadmap P3. [BLOCKING,
GATEWAY]**
`D-P7-B` deliberately withheld this: roadmap P3 work needs its own User
authorisation, with named scope and named forbidden scope. Proposed named
scope: adapters per D-P3-A..C, contract-conformant registry entries, the
portability conformance test per D-P3-D/E, and the D-P3-G guard updates.
Proposed named forbidden scope: any install, any runtime activation, any
capability promotion (CAP-P03-005 stays deferred), the production capability
registry, any legacy file, `CONF-001`, LCP/INP thresholds, the threat model,
P7 and beyond, and any push.

**D-P3-G — Authorised, recorded guard updates at delivery. [BLOCKING]**
When the first real adapter lands, two approved guards legitimately change
what they pin: `validate-p7-readiness.py` (the one-adapter `DECLARED` pin
raises `ADAPTER_STATE_CHANGED`) and `sps2/tests/test_p5.py::TestAgentNeutrality`
(walks `adapters/` and rejects vendor names there). Options: (1) recommended —
update exactly these two, in the same delivery, with the change recorded in
the P3 evidence trail; (2) defer both to a separate, separately authorised
commit before P3 delivery. "Change nothing" is not viable: any real adapter
carries a vendor-named `agent_id`, which the current unit-test walk rejects,
so freezing the guards means refusing the roadmap's own deliverable.

No roadmap P3 implementation may begin until D-P3-A through D-P3-G are
answered by the User and the D-P3-F authorisation is explicitly given. P7
remains blocked regardless (section 3.8), and the threat model remains a
separate prerequisite.

---

## 7. Statement of restraint

No roadmap P3 implementation artefact was created. No adapter was added. No
conformance test was written. Nothing was installed, activated or promoted.
CAP-P03-005 remains `DEFERRED / NOT_PROMOTED`. The production capability
registry is unchanged (hash in section 5). No legacy file was modified; no
`.sps/` file was modified. No existing decision record or reconciliation
record was modified. `CONF-001` remains `UNRESOLVED`; no LCP/INP threshold
was invented. No threat model was authored or claimed. No emoji was
introduced; no credential was read, printed, hashed or transmitted. Nothing
was pushed.

This audit plans and reports; it does not decide, and it approves nothing.

**Stopping here and awaiting the seven User decisions in section 6.**
