# AUDIT-P7 — Readiness & Decision Audit

Audit date: 2026-10-04
Auditor: implementation agent (**not** a User; this audit is **not** an approval)
HEAD at audit: `8ad318eb71d1bb2d3db7c748f7141b59c695500d`
Status: **P7 NOT STARTED / NOT APPROVED. Awaiting User decision.**

---

## 0. Scope

Decision support only. No P7 implementation, no P7 artefact, no install, no
runtime activation, no promotion, no registry modification, no push. The
production capability registry is byte-identical and was not touched.

Machine-enforced companion: `sps2/tools/validate-p7-readiness.py`.

---

## 1. Reconciliation: authoritative roadmap vs executed phases

Recorded additively in `sps2/decisions/ROADMAP-EXECUTION-RECONCILIATION.json`.
No phase was renamed, reclassified or rewritten.

| Roadmap | Roadmap title | Executed as | Satisfaction |
|---|---|---|---|
| P1 | Repository Foundation | P1 | ALIGNED — SATISFIED |
| P2 | Core Orchestration & Governance | spread across executed P1–P4 | SUBSTANTIALLY_SATISFIED |
| P3 | Agent Interoperability | executed under D-P3-F | SATISFIED (User-approved 2026-10-05) |
| P4 | Capability Discovery | executed P2 + P3 | PARTIALLY_SATISFIED |
| P5 | Dynamic Skill Selection | executed P5 | PARTIALLY_SATISFIED |
| P6 | Technology Research | executed P6 (D-P6-1) | SATISFIED |

Only roadmap P1 and roadmap P6 align by number. Roadmap P6 was aligned by your
explicit decision D-P6-1; no equivalent decision exists for P2–P5.

### Ambiguities — all four now RESOLVED by explicit User decision

Recorded in `sps2/decisions/P7-READINESS-DECISIONS.json`, all
`decided_by: User`, `decided_on: 2026-10-04`.

| ID | Ambiguity | Resolved by | Effect |
|---|---|---|---|
| AMB-PHASE-1 | Roadmap/executed numbering diverges for P2–P5 | **D-P7-A** | Dependencies read as **roadmap numbers** |
| AMB-PHASE-2 | Roadmap P3 unsatisfied and is a P7 prerequisite | **D-P7-B** | P3 **not waived**; must be satisfied first |
| AMB-PHASE-3 | "retire global memory" may need legacy edits | **D-P7-C** | Narrowed to SPS 2.0 project-local only |
| AMB-PHASE-4 | Threat model absent; P7 adds persistent state | **D-P7-D** | Threat model **required** before P7 |

**Resolving an ambiguity records what must be true; it does not make it
true.** All four underlying gaps remain outstanding and are now tracked as
explicit prerequisites in section 6.

---

## 2. What the roadmap defines as P7

Quoted verbatim from `.sps/architecture/SPS2-ROADMAP.md`:

- **Objective:** Consolidate project memory; retire global memory.
- **Dependencies:** P2, P3.
- **Forbidden:** writing state outside the project.
- **Deliverables:** memory layout; team bootstrap; isolation validator.
- **Acceptance:** two projects remain isolated; a new teammate understands the project from the repo alone.
- **Verification:** isolation tests + onboarding dry run.
- **Approval:** user.
- **Rollback:** revert memory layout.

### Prerequisites

1. **D-P7-A** — resolve which P2/P3 the dependency refers to (AMB-PHASE-1).
2. **D-P7-B** — decide whether roadmap P3 must be satisfied first, or waived
   with a recorded rationale (AMB-PHASE-2).
3. **D-P7-C** — decide how far "retire global memory" may go given the
   legacy-protection boundary (AMB-PHASE-3).
4. **D-P7-D** — decide whether the absent threat model (AMB-PHASE-4) must be
   produced before P7, since P7 introduces persistent state.

### Expected artefacts (roadmap deliverables)

| Deliverable | Present? |
|---|---|
| memory layout | **no** |
| team bootstrap | **no** |
| isolation validator | **no** |

### Requirements and acceptance criteria

Roadmap acceptance is twofold and both are testable: an isolation test proving
two projects remain isolated, and an onboarding dry run proving a new
teammate can understand the project from the repository alone. Neither has a
harness today.

### Approval gates

User approval is required, per the roadmap. The pattern established by P5 and
P6 should carry forward: explicit User authorisation with named scope and named
forbidden scope; IMPLEMENTED / VERIFIED / APPROVED as three independent axes;
no self-approval; validator with positive and negative tests; a hard stop at
any further decision boundary.

### Security boundaries

- Project-local only. Writing state outside the project is forbidden by the
  roadmap itself and by `SPEC.md`.
- Machine-global configuration must stay untouched.
- Legacy SPS files must not be modified; legacy diff must remain 0.
- The P3 incident classification and checkpoint `a7767cf` constraints continue
  to bind.
- No credential may be read, printed, hashed or transmitted.

### Prohibited actions for any future P7

Installing any dependency, skill, MCP, CLI or package; runtime activation of any
kind; promoting any capability, including CAP-P03-005; resolving CONF-001 by
inference; inventing LCP or INP thresholds; modifying legacy files; modifying
machine-global state; writing state outside the project; purging checkpoint
`a7767cf`; rewriting history; force-pushing; beginning P8 or later.

---

## 3. CONF-001 re-checked — remains UNRESOLVED

Re-examined against existing repository evidence only. **It stays UNRESOLVED.**

- `P2-SOURCES.json` still records `UNRESOLVED - recorded as RESEARCH_FURTHER`.
- The P6 research entry records `LCP_thresholds: NOT_OBSERVED` and
  `INP_thresholds: NOT_OBSERVED`.
- CLS figures (0.1 good, 0.25 poor) **are** evidenced verbatim from a rank-1
  official source, but that is partial evidence and cannot close a conflict
  whose subject is "LCP and INP numeric thresholds".
- `TECH-WEB-VITALS` still carries `CONF-001` as a blocking conflict, so its
  computed readiness remains `INSUFFICIENT`.

No LCP or INP value was introduced, imported, or inferred.

---

## 4. Why P7 must not start yet

Roadmap P7 introduces **persistent project state**, the most state-creating
phase so far. Following D-P7-A and D-P7-B, the prerequisites are now explicit.

- Roadmap P3 (Agent Interoperability) is a **hard prerequisite** and is now
  **SATISFIED** (User-approved 2026-10-05; recorded in
  ROADMAP-P3-DECISIONS.json completion block).
- A **threat model** for persistent project-local state now exists
  (`sps2/governance/P7-THREAT-MODEL.md`; D-P7-D makes it mandatory) and is
  referenced by the readiness validator.
- All three roadmap P7 deliverables — memory layout, team bootstrap,
  isolation validator — are still absent (they are P7 implementation artefacts,
  not governance artefacts, and P7 is not authorised).

P7 implementation cannot begin without explicit User authorisation (Items 7–8
below). The threat model is a prerequisite, not an implementation step.

---

## 5. What remains before P7 implementation can begin

Resolved decisions fix the rules; they do not do the work. Outstanding:

| # | Prerequisite | Source | Status |
|---|---|---|---|
| 1 | Roadmap P3 satisfied: real adapters beyond `generic` | D-P7-B | DONE (User-approved 2026-10-05) |
| 2 | Portability conformance test: deleting all adapters leaves core validators passing | D-P7-B | DONE |
| 3 | Roadmap P3 acceptance: fresh agent resumes from repository state alone | D-P7-B | DONE |
| 4 | Written threat model covering persistent project-local state | D-P7-D | DONE — `sps2/governance/P7-THREAT-MODEL.md` |
| 5 | Threat-model treatment of two-project isolation and memory rollback | D-P7-D | DONE — sections 3, 9, 11 |
| 6 | Roadmap P2 confirmed against its own acceptance criteria under D-P7-A | D-P7-A | SUBSTANTIALLY SATISFIED |
| 7 | Explicit User authorisation to begin roadmap P3 work | standing rule | NOT GIVEN (P3 approved separately) |
| 8 | Explicit User authorisation to begin P7, with named scope and forbidden scope | standing rule | NOT GIVEN |

Items 1–3 require roadmap P3 to be executed first. Items 4–5 require the
threat model. Items 7–8 are User authorisations that do not yet exist. Each of
roadmap P3, the threat model and P7 needs its **own** explicit authorisation.

---

## 6. Statement of restraint

No P7 implementation artefact was created. Nothing was installed. Nothing was
activated. No capability was promoted. CAP-P03-005 remains DEFERRED /
NOT_PROMOTED. The production registry is unchanged. No legacy file was
modified. No machine-global state was written. Nothing was pushed. No emoji
was introduced. No credential was read, printed, hashed or transmitted.

### Enforcement

The record is not trusted on appearances. `validate-p7-readiness.py` checks it
directly (30 checks, 7 negative cases), and every phase validator rejects a
forged or gutted version of it: attribute a decision to an agent, delete one, or
plant any P7 deliverable, and P4, P5 and P6 all fail. The mutation suite reports
19 readiness mutations and 11 phase-validator mutations caught with 0 missed,
and it carries controls proving the legitimate record is still admitted, so the
guards cannot silently decay into a blanket ban.

**Threat model**: `sps2/governance/P7-THREAT-MODEL.md` covers P7 persistent
state, isolation, rollback, and prohibited behaviours. It is a governance
artefact — it authorises nothing and does not start P7.

**Stopping here and awaiting User decision on P7 authorisation.**