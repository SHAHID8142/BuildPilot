# AUDIT-P6 — Readiness & Decision Audit

Audit date: 2026-10-04
Auditor: implementation agent (**not** a User; this audit is **not** an approval)
Repository HEAD at audit: `0e3d2f290265be0a814bfa067fb7d96ea93e46c6`
Status: **P6 NOT STARTED / NOT APPROVED. Awaiting User decision.**

---

## 0. Scope of this document

This is decision support only. It performs **no** P6 implementation, installs
nothing, activates nothing, and does **not** modify the production capability
registry. Its purpose is to tell the User what P6 would mean, what it would
risk, what it depends on, what must be approved, and — the substantive question
— whether runtime activation should exist at all.

Everything below is derived from repository state, not from intent.

---

## 1. Current state as verified

| Phase | Roadmap meaning | Actually executed here | Match |
|---|---|---|---|
| P1 | Repository Foundation | Repository Foundation | yes |
| P2 | Core Orchestration & Governance | Capability Intelligence (research) | no |
| P3 | Agent Interoperability | Production Capability (promotion) | no |
| P4 | Capability Discovery | Production Promotion | no |
| P5 | Dynamic Skill Selection | Implementation / Integration | partial |
| P6 | **Technology Research** | not started | — |

Verified conditions:

- Working tree clean; production registry byte-identical to the approved commit.
- Validators: P5 43/0, P4 59/0, P3 67/0, P2 69/0, Foundation 72/0.
- Four production capabilities, all `EVALUATED`. CAP-P03-005 `DEFERRED`.
- No runtime claim exists on any capability.
- `CONF-001` remains `UNRESOLVED`; no LCP/INP threshold invented.
- Legacy diff 0; checkpoint `a7767cf` preserved.

---

## 2. BLOCKING FINDING — the label "P6" is ambiguous

The authoritative roadmap (`.sps/architecture/SPS2-ROADMAP.md`) and the phases
actually executed in this repository **use the same numbers for different
work**.

The roadmap's **P6 is "Technology Research"**: a research gate that blocks use
of an unresearched technology, delivering a workflow, a cache schema, and a
readiness evaluator whose acceptance criterion is that a technology with
`readiness != SUFFICIENT` is rejected.

But this repository's own P2 was already "Capability Intelligence (research)".

**Therefore "start P6" is ambiguous and must not be acted on.** Two readings:

- **Reading A** — P6 means the roadmap's P6, *Technology Research*. Then P6 is a
  research-readiness gate and would sit *before* capability use.
- **Reading B** — P6 means the next slot after this repository's P5. Then it is
  an undefined continuation of implementation/integration.

These lead to completely different work. This audit does **not** choose between
them. Choosing silently would be exactly the kind of inferred approval the
architecture forbids.

**Decision D-P6-1 (required): which P6 is meant.**

---

## 3. What each candidate P6 would accomplish

### Reading A — Technology Research

Objective: refuse to use any technology whose readiness has not been researched
to `SUFFICIENT`.

Deliverables implied by the roadmap: a research workflow, a research cache
schema, and a readiness evaluator.

Acceptance: selection for a technology with `readiness != SUFFICIENT` is
rejected. Forbidden: auto-accepting `INSUFFICIENT`.

Note this interacts with the existing unresolved conflict `CONF-001`, which is
precisely a "research this further before encoding a number" case. Reading A
would formalise the mechanism that `CONF-001` currently lacks.

### Reading B — next implementation step

---

## 4. Readiness gaps, independent of which reading is chosen

| # | Gap | Evidence | Roadmap origin |
|---|---|---|---|
| G1 | Lifecycle state machine is a placeholder | `sps2/core/lifecycle/STATE-MACHINE.md` is a P1 stub | P2/P4 |
| G2 | `ACTIVE` and `INSTALLED` are defined nowhere | no spec defines either state | P4 |
| G3 | 7 further spec files are placeholders | GATES, PROTOCOLS, MODEL, adapters, schemas, mcp, skills READMEs | P1 |
| G4 | Only one adapter, `DECLARED`; no portability test | `core/adapters/registry.json` | P3 |
| G5 | No memory layout, no isolation validator | `sps2/memory` absent | P7 |
| G6 | No readiness evaluator | no `SUFFICIENT`/`readiness` logic in `tools/` | P6 (Reading A) |
| G7 | `CONF-001` unresolved | `research/P2-SOURCES.json` | P2 |
| G8 | CAP-P03-005 deferred, gates F/H/K open | capability registry | — |

G1–G3 are the material ones: the architecture's own lifecycle vocabulary is
still unwritten.

---

## 5. Risks

| # | Risk | Severity | Why it matters |
|---|---|---|---|
| R1 | Acting on an ambiguous phase label | **High** | Could deliver the wrong work under the wrong approval |
| R2 | Self-asserted runtime state | **High** | An `ACTIVE` flag with no executable verifier repeats the CAP-P03-005 Gate F failure exactly |
| R3 | Scope creep into domain subsystems | Medium | P8–P10 (CMS, SEO, slices) each need their own approval and security review |
| R4 | Credential-class incident recurrence | Medium | New install/config paths are the exact surface of the P3 incident |
| R5 | Global-state regression | Medium | Any runtime supervisor is the first component likely to want `~` writes |
| R6 | Undocumented dependency | Medium | Research phases tempt package intake without provenance records |
| R7 | Premature approval pressure | Medium | A green validator is not a User decision |

---

## 6. Prerequisites before any P6 work

1. **D-P6-1 resolved** — which P6 is meant.
2. Explicit User instruction authorising P6, its scope, and its forbidden scope.
3. A decision on runtime activation (section 7) if any P6 path touches it.
4. For Reading A specifically: a decision on whether `CONF-001` is resolved by
   research, or stays open by design.
5. The existing P5 approval remains scoped to P5 and does **not** carry over.

---

## 7. SUBSTANTIVE QUESTION — should runtime activation exist at all?

**Recommendation: do not introduce runtime activation as a distinct capability
state yet. Defer it, and first close G1 and G2.**

Evidence against introducing it now:

1. **It is undefined.** Neither `ACTIVE` nor `INSTALLED` is defined in any spec
   (G2). `STATE-MACHINE.md` is a placeholder (G1). There is nothing to implement
   against, and a document is explicitly *not* proof of behaviour
   (`SPEC.md` section 6).
2. **Nothing needs it.** The four promoted capabilities are pure-logic
   validators — a gate engine, scanners, conformance checks. They are invoked
   on demand and produce a verdict. There is no consumer that requires a
   persistent runtime.
3. **It would weaken a control.** Today `EVALUATED` is truthful and verified.
   Moving to `ACTIVE` would add a state that, absent an executable observer, is
   a self-asserted label — the same defect that blocks CAP-P03-005 at Gate F.
4. **It is the natural home for global-state leakage.** A supervisor process is
   the component most likely to want a machine-global location, which
   `SPEC.md` section 6 and the global-vs-local policy both forbid.
5. **Agent neutrality.** Real runtime execution is where agent-specific
   assumptions tend to re-enter. The core must stay neutral and deletable.

If the User wants activation semantics eventually, the safer framing is
**declarative binding** — a capability is *bound* to a named invocation site,
and "active" means "bound and reachable from that site", observable and
reversible — rather than a resident process. That keeps it deterministic and
verifiable.

**Minimum bar before any `ACTIVE` state may ever be used:**

- a written lifecycle state machine with an explicit, named transition;
- an **executable** observer that proves the state (not a flag in JSON);
- a defined rollback;
- its own User approval, separate from this one.

**Recommendation: record a decision that runtime activation is out of scope
until G1 and G2 are closed.** This is a recommendation, not a decision.

---

## 8. Approval gates for a future P6

If P6 is authorised, it should carry the same structure as P5:

- explicit User authorisation with named scope and named forbidden scope;
- IMPLEMENTED / VERIFIED / APPROVED recorded as three independent axes;
- no self-approval by the agent;
- a validator with positive **and** negative tests, mutation-tested;
- a stop at the decision boundary whenever a new User decision is required.

Explicitly excluded from any P6 without its own approval: new capability
promotion, CAP-P03-005 promotion, runtime activation, installing anything,
global configuration, and resolving `CONF-001` by assumption.

---

## 9. Decisions requiring User approval

| # | Decision | Blocking? |
|---|---|---|
| D-P6-1 | Which P6 is meant (Reading A Technology Research, or Reading B) | **Yes** |
| D-P6-2 | Whether runtime activation exists at all, and in what form | **Yes** |
| D-P6-3 | Whether `CONF-001` is resolved by research or stays open | Only for Reading A |
| D-P6-4 | Whether G1–G3 placeholder specs are in P6 scope or belong earlier | No |

---

## 10. Statement of restraint

- No P6 implementation was performed.
- Nothing was installed.
- No capability was activated; all four remain `EVALUATED`.
- The production capability registry was **not** modified.
- No capability was added, promoted, or demoted.
- No emoji was introduced; no credential was read, printed, hashed or
  transmitted.
- This audit recommends; it does not decide.

**Stopping here and awaiting User approval.**
There is no defined objective. This reading only makes sense once the User
states what should come next. Candidate work visible in the repository is
listed in section 4.