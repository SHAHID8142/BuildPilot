# PHASE-04 Task Register

**Phase:** `PHASE-04` — Discovery & Capability Architecture
**Status:** `AWAITING_USER_APPROVAL` (implementation `COMPLETE`, verification `VERIFIED`)
**Approval:** **`APPROVED` by User, 2026-10-03** — explicit user approval, not inferred
**Contracts:** `.sps/SCHEMA.md` §12–§16 · **Model:** `.sps/capability/`

---

## Task Summary

| ID | Title | Requirements | Status | Completion | Verification | Approval |
|---|---|---|---|---|---|---|
| `PHASE-04-T01` | Capability model, lifecycle, hardcoded-routing audit | `REQ-P04-01,09,11,12` | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` (User, 2026-10-03) |
| `PHASE-04-T02` | Capability + research contracts, registry, research cache | `REQ-P04-02,03` | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` (User, 2026-10-03) |
| `PHASE-04-T03` | Security gate + MCP evaluation contract | `REQ-P04-04,05,06` | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` (User, 2026-10-03) |
| `PHASE-04-T04` | Research gate + provenance chain | `REQ-P04-07,08` | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` (User, 2026-10-03) |
| `PHASE-04-T05` | Agent-interoperability contract | `REQ-P04-10` | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` (User, 2026-10-03) |
| `PHASE-04-T06` | Validator + negative suite CASE A–N | `REQ-P04-13` | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` (User, 2026-10-03) |

---

## T01 — Capability model, lifecycle, routing audit

- **Evidence:** `EV-P04-001`, `EV-P04-008`, `EV-P04-010`
- **Files:** `.sps/capability/CAPABILITY-MODEL.md`
- **Done:** 14-state lifecycle mapped onto the Phase 03 model; four claim classes
  (`FACT`/`EVIDENCE`/`INFERENCE`/`UNKNOWN`); selection pipeline; 6-rank source priority;
  staleness fields and triggers; no-emoji rule; measured audit of the existing hardcoded
  routing.
- **Measured audit:** `SKILL-ROUTER.md` has a 20-row static domain map; `install.sh` has 27
  `npx skills add` calls and 34 `-g` global flags; `SKILL-GOVERNANCE.md:35` names a single
  permanent taste operator. Recorded, not assumed.

## T02 — Contracts, registry, research cache

- **Evidence:** `EV-P04-002` · **Decision:** `DEC-0005`
- **Files:** `.sps/SCHEMA.md` §12–§13, `.sps/capability/registry/PHASE-04-CAPABILITIES.json`,
  `.sps/research/PHASE-04-RESEARCH.json`
- **Done:** capability contract and research contract defined; registry and research cache
  created **empty by design**.
- **Not done:** no capability discovered, evaluated, installed, or fabricated.

## T03 — Security gate and MCP contract

- **Evidence:** `EV-P04-004`, `EV-P04-005`, `EV-P04-006`
- **Files:** `.sps/capability/SECURITY.md`, `.sps/SCHEMA.md` §14–§15
- **Done:** threat model; security status enum where `UNKNOWN` blocks installation;
  project-local default with exceptional global path; MCP contract with `trust_level`,
  permissions, data access, network access, credentials and rollback.

## T04 — Research gate and provenance

- **Evidence:** `EV-P04-007` · **Decision:** `DEC-0006`
- **Files:** `.sps/capability/PROVENANCE.md`, `.sps/SCHEMA.md` §13
- **Done:** ten-area research contract with source-rank gate; provenance chain requirement →
  discovery → research → evaluation → decision → installation → verification → usage; honest
  enforcement table.

## T05 — Agent interoperability

- **Evidence:** `EV-P04-009`
- **Done:** consumption path identical for every agent; Markdown + JSON only; slash commands
  explicitly optional; agent-specific directories must not be written.

## T06 — Validator and negative suite

- **Evidence:** `EV-P04-003`, `EV-P04-011`, `EV-P04-012`
- **Files:** `.sps/tools/validate-capability.sh`, `.sps/tools/.cap-fixture.py`
- **Done:** 52 structural checks; **16 negative cases (A–N plus G2) all correctly rejected**;
  a **CASE 0 positive control** proving a valid capability is still accepted.
- **Defects found and fixed during development:** a research-fixture path bug that masked
  CASE H and M; an over-strict `SECURITY.md` grep; an empty-registry false failure. All fixed
  before commit.

---

## Explicitly Not Done

- No capability discovered, installed, or activated.
- No MCP installed or configured.
- No change to `SKILL-ROUTER.md` or `SKILL-GOVERNANCE.md` — migration deferred.
- No CMS, SEO, backend, or frontend work.
- No Phase 01 finding fixed (`KI-01`–`KI-14` remain open).
- No machine-global change, no remote configured, no push.
- **No Phase 05 work started.**