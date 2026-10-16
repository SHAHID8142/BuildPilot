# SPS Governance — Canonical Project State

> **This repository is the source of truth for SPS project state.**
> Agents are *clients* of this repository. Project-critical state must never live
> only in an agent's hidden memory, global memory, or machine-local planning dir.
>
> Read order for any agent picking up this project: **`STATE.md` → `tasks/` →
> `evidence/` → `decisions/`**. Do not rely on hidden memory.

**Tool-agnostic:** this format uses plain Markdown + JSON. It does not depend on
Cline, Claude, Codex, Antigravity, Gemini, OpenCode, any model, or any IDE.

---

## Current Phase

| Field | Value |
|---|---|
| Phase ID | `PHASE-05` |
| Phase name | SPS 2.0 Repository Architecture & Migration Planning |
| Phase status | `APPROVED` |
| Completion | `COMPLETE` |
| Verification | `VERIFIED` |
| **Approval** | **`APPROVED`** — granted by User, 2026-10-03 |
| Approved by | User (explicit approval) |
| Approval basis | User reviewed the Phase 05 planning report, architecture, migration strategy, repository separation strategy, global-vs-project-local model, and discrepancies, and approved Phase 05 |
| Started | 2026-10-03 |
| Approved | 2026-10-03 |
| Previous phase | `PHASE-04` — Discovery & Capability Architecture (`APPROVED` 2026-10-03) |
| Next phase | **Roadmap P1 — Repository Foundation** — `NOT_STARTED`, needs a NEW explicit instruction |

> **Planning only — nothing was implemented.** No SPS 2.0 implementation, no legacy
> modification, no dependency installed, no Git remote created, nothing pushed. The
> architecture, migration matrix and 16-phase roadmap live in `.sps/architecture/`. SPS 2.0
> will be built in a **NEW** repository (`DEC-0007`), leaving this repository as the
> immutable legacy reference.
>
> **Approval of Phase 05 does not authorise P1.** Every roadmap phase requires its own
> explicit gate.

> **Three axes, recorded separately.** Phase 04 is `COMPLETE` (work performed), `VERIFIED`
> (capability validator 52/52 + 16 negative cases; governance 50/50; control 49/49 + 8; lint
> PASSED), and now `APPROVED` (the user accepted it on 2026-10-03).
>
> **Repository strategy is changing.** The next phase will be a separate
> **"SPS 2.0 Repository Architecture & Migration Planning"** phase, NOT Phase 05. That phase
> has no ID, no scope and no approval yet, and must not begin without an explicit prompt.
>
> **Nothing was installed, discovered, or fabricated.** The capability registry and research
> cache remain intentionally empty (`DEC-0005`).

> **Three axes, recorded separately:** this phase is `COMPLETE` (work performed),
> `VERIFIED` (evidence proves it), and now `APPROVED` (the user accepted it on
> 2026-10-03). These remain distinct states and must never be collapsed into one
> field going forward.

## Current Position

```
PHASE-01 (audit)  ──►  PHASE-02 (governance)  ──►  PHASE-03 (enforcement)
   VERIFIED              APPROVED                   NOT_STARTED
                                                        ▲
                                        NOT approved; needs a NEW explicit
                                   instruction. Phase 02 approval does
                                    NOT carry forward to Phase 03.
```

## Approval Record

| Subject | Status | Decided by | Date | Basis |
|---|---|---|---|---|
| `PHASE-02` | `APPROVED` | User | 2026-10-03 | Independent review and acceptance |
| `DEC-0001` git remote | `APPROVED` → `KEEP_LOCAL_ONLY` | User | 2026-10-03 | Do not configure a remote now |
| `DEC-0002` git identity | `APPROVED` → `DEFER_IDENTITY_UPDATE` | User | 2026-10-03 | Replace before external publication |
| `PHASE-03` | `APPROVED` | User | 2026-10-03 | Implementation and verification independently reviewed and accepted |
| `DEC-0003` lifecycle extends status model | `APPROVED` | User | 2026-10-03 | Accepted as implemented |
| `DEC-0004` evidence immutability scope | `APPROVED` | User | 2026-10-03 | Accepted as detection-based, not prevention-based |
| `PHASE-04` | `APPROVED` | User | 2026-10-03 | Implementation and verification independently reviewed and accepted |
| `DEC-0005` empty registry | `APPROVED` | User | 2026-10-03 | Registry starts empty; no capability fabricated |
| `DEC-0006` provenance scope | `APPROVED` | User | 2026-10-03 | Detection-based, not runtime-traced |

**Strategy change (2026-10-03):** the next phase is **not** `PHASE-05`. It is a separate
**"SPS 2.0 Repository Architecture & Migration Planning"** phase, recorded as
`NOT_YET_DEFINED`. No phase ID has been allocated and no approval exists for it.

**Standing obligation carried by `DEC-0002`:** the Git identity placeholder must be replaced
**before this repository is published or shared externally**. Not yet due, because `DEC-0001`
keeps the repository local-only.

## Phase Status Legend

`PLANNED` → `IN_PROGRESS` → `AWAITING_USER_APPROVAL` → `APPROVED` → `VERIFIED`

Terminal alternatives: `REJECTED` · `BLOCKED` · `FAILED`

**Critical distinction — these three are NOT the same:**

| Concept | Meaning | Recorded in |
|---|---|---|
| **Completed** | An agent believes the work was performed | `tasks/*.md` → `completion` |
| **Verified** | Objective evidence proves it works | `evidence/*.json` → `verification` |
| **Approved** | The *user* explicitly accepted it | `approval` block |

A phase may be `Completed` but not `Verified`, and `Verified` but not `Approved`.
Never collapse these into a single field.

## Phase Inventory

| Phase | Scope | Status | Report |
|---|---|---|---|
| `PHASE-01` | Read-only forensic audit | `VERIFIED` | `AUDIT-PHASE-01-BASELINE-FORENSIC.md` |
| `PHASE-02` | Governance + Git + evidence foundation | `APPROVED` (2026-10-03) | `AUDIT-PHASE-02-GOVERNANCE-IMPLEMENTATION.md` |
| `PHASE-03` | Enforcement & control foundation | `APPROVED` (2026-10-03) | `AUDIT-PHASE-03-ENFORCEMENT-CONTROL.md` |
| `PHASE-04` | Discovery & capability architecture | `APPROVED` (2026-10-03) | `AUDIT-PHASE-04-DISCOVERY-CAPABILITY-ARCHITECTURE.md` |
| `PHASE-05` | SPS 2.0 architecture & migration planning | `AWAITING_USER_APPROVAL` | `AUDIT-PHASE-05-SPS2-ARCHITECTURE.md` |
| P1-P16 | SPS 2.0 roadmap (`.sps/architecture/SPS2-ROADMAP.md`) | `NOT_STARTED` — P1 needs a new instruction | — |

## Governance Map

```
.sps/
├── STATE.md                    ◀── you are here: canonical entry point
├── GOVERNANCE.md               ◀── rules: states, maturity, IDs, evidence, approval
├── SCHEMA.md                   ◀── machine-readable contracts for every record
├── tasks/
│   └── PHASE-02-TASKS.md       ◀── task register for the active phase
├── evidence/
│   └── PHASE-02-EVIDENCE.json  ◀── objective verification records
├── decisions/
│   └── DEC-0001-*.md           ◀── decision records (why, not just what)
├── handoff/
│   └── HANDOFF-CURRENT.md      ◀── agent-to-agent contract
└── audits/
    └── README.md               ◀── index of audit reports + known-issue register
```

Existing SPS files (`profile.md`, `handoff.md`, `agent.md`, `audit-report.md`,
`mistakes.md`, `learned/`) are retained unchanged — governance **extends** the
existing convention rather than replacing it.

## Provenance

| Field | Value |
|---|---|
| Baseline commit | `10ab67a` — `chore(governance): establish pre-remediation baseline` |
| Governance commit | `ec32dfa` — `chore(governance): establish SPS phase governance foundation` |
| Approval commit | Recorded in the Phase 02 approval transition commit |
| Remote | `REMOTE_NOT_CONFIGURED` (`DEC-0001` → `KEEP_LOCAL_ONLY`) |
| Branch | `main` |

## Rules

1. **No hidden memory.** If it is not in this repository, another agent cannot see it.
2. **No claim without evidence.** Every status claim links to an evidence record.
3. **Never mark `APPROVED` on the user's behalf.** Only the user grants approval.
4. **Never mark `VERIFIED` without an executed command and its real output.**
5. **Traceability is mandatory:** phase → task → requirement → implementation →
   evidence → approval.
6. **Out-of-scope means documented, not fixed.**