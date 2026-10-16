# SPS 2.0 — Data Flow

**Phase:** `PHASE-05` · **Status:** `AWAITING_USER_APPROVAL`

Two flows: **control flow** (how work advances) and **capability flow** (how a capability gets chosen).

---

## 1. Control flow — requirement to delivery

```
USER REQUEST
   v
[1] DISCOVERY          what does the project actually need?
   v                    state: DISCOVERY
[2] REQUIREMENTS       requirement_id + acceptance criteria + priority
   v                    state: REQUIREMENTS
[3] RESEARCH GATE      unfamiliar technology? -> research cache entry,
   v                    readiness=SUFFICIENT required. state: REQUIREMENTS
[4] PLANNING           architecture, section inventory, dependency order
   v                    state: PLANNING
[5] PLAN APPROVAL      user accepts the plan
   v                    state: AWAITING_USER_APPROVAL -> APPROVED
[6] READY              plan approved, tasks decomposed
   v                    state: READY_FOR_IMPLEMENTATION
[7] VERTICAL SLICE     one section at a time: frontend + CMS + backend +
   v                    data + validation + assets + SEO + tests
[8] VERIFICATION       per-slice DoD + evidence + independent check
   v                    state: VERIFICATION
[9] USER APPROVAL      explicit, attributable
   v                    state: AWAITING_USER_APPROVAL -> APPROVED
[10] DELIVERY          release, then next slice
                        state: DELIVERED
```

**Invariant:** no state is skipped. `DELIVERED` is reachable only via `APPROVED`. Any stage may enter
`BLOCKED`; `REJECTED` may return to an earlier stage.

**Rollback:** each slice is independently revertible. `ROLLBACK_CONTRACT` records method, scope and whether
the rollback itself was verified.

---

## 2. Capability flow — requirement to activated capability

```
PROJECT REQUIREMENT
   v
DOMAIN + TECHNOLOGY identified
   v
RESEARCH GATE          technology understood?  (else research first)
   v
CANDIDATE DISCOVERY    enumerate >= 2 candidates (or record why only one exists)
   v
EVALUATION            16 criteria, each scored or explicitly UNKNOWN
   v
SECURITY GATE          supply-chain assessment; UNKNOWN != safe
   v
LICENCE GATE           compatibility with project policy
   v
COMPATIBILITY          technology / framework / agent-neutral
   v
FRESHNESS              staleness check; re-evaluation trigger
   v
RANKING                weighted score; popularity is a tie-breaker ONLY
   v
SELECTION              recorded justification + rejected alternatives
   v
PROPOSAL -> USER APPROVAL (Level 3 gate)
   v
PROJECT-LOCAL INSTALL  into .sps/skills/ — never global by default
   v
PROVENANCE RECORD      requirement -> ... -> verification
   v
VERIFY                 evidence that it actually works
   v
ACTIVE                 used by slices
   v
RE-EVALUATE            on staleness / stack change / advisory / failure
```

**Override precedence (highest first):**
1. Explicit user technology/skill choice
2. Project constraints in `.sps/PROFILE.md`
3. Security / licence veto (a veto is never overridden by preference)
4. Evaluated ranking
5. Built-in defaults (if any remain)

A forced user choice always wins over automatic selection.

---

## 3. State artifact flow (where each artefact lives)

| Artefact | Written by | Location | Read by |
|---|---|---|---|
| Current phase/state | agent + user approval | `.sps/STATE.md` | every agent |
| Task register | orchestrator | `.sps/tasks/` | orchestrator, reviewers |
| Evidence | validator run | `.sps/evidence/` | reviewers, CI |
| Decision record | agent proposes, user approves | `.sps/decisions/` + `docs/adr/` | all future agents |
| Capability registry | discovery/evaluation | `.sps/capabilities/registry.json` | selection engine |
| Research cache | research workflow | `.sps/research/` | research gate |
| Known issues | any phase | `.sps/audits/` | all phases |
| Handoff | outgoing agent | `.sps/handoff/` | incoming agent |

**All artefacts are project-local and agent-neutral.** No agent-specific memory location is authoritative.

---

## 4. Evidence flow

```
validator command executes
   v
exit code + verbatim output captured
   v
evidence record written (append-only)
   v
linked to requirement + task + commit
   v
gate evaluates: does required evidence exist AND pass?
   v
no  -> state stays short of the gate; transition REFUSED
yes -> state advances
```

**Evidence is never edited to change a result.** A changed outcome appends a new record that supersedes the old.
Git history is the tamper-evidence layer: it detects, it does not prevent.

---

## 5. Failure flow

```
any stage
   v
stop condition raised (MISSING_REQUIREMENT | FAILED_VALIDATION | PENDING_APPROVAL |
                        UNRESOLVED_SECURITY_ISSUE | CONFLICTING_REQUIREMENTS | ...)
   v
state -> BLOCKED  (or AWAITING_USER_APPROVAL for approval-type)
   v
agent must NOT proceed by silently assuming a solution
   v
surface to user with the exact blocker
```

Silently assuming a resolution to clear a stop condition is itself a violation and is recorded as such.