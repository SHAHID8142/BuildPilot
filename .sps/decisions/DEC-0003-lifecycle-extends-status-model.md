# DEC-0003 — Lifecycle is an extension of the Phase 02 status model, not a replacement

- **Date:** 2026-10-03
- **Status:** Active
- **Approval:** `APPROVED`
- **Phase / Task:** `PHASE-03` / `PHASE-03-T01`
- **Evidence:** `EV-P03-001`
- **Supersedes:** none

---

## Decision

Add a lifecycle of 11 named stages to SPS and **map** it onto the existing Phase 02 status
model rather than defining a second, competing state system.

## Reason

The Phase 03 brief asked for 11 lifecycle stages while Phase 02 already defined 8 status
states. Defining both as independent systems would produce exactly the failure this programme
exists to prevent: two vocabularies for "where are we", which inevitably drift.

The resolution distinguishes two genuinely different questions:

- **Lifecycle** = *where* a unit is in its journey (ordered, forward-moving).
- **Status** = *what condition* it is in (orthogonal; can apply at any lifecycle point).

`CONTROL-MODEL.md` §3 provides the explicit mapping table, so no unit is ever described with
an ambiguous state.

## Evidence

`EV-P03-001` — `validate-control.sh` detects all 11 lifecycle stage names and all four truth
levels in `CONTROL-MODEL.md`; removing any one fails the check.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Define the 11 lifecycle states as a new independent state machine | Creates two competing vocabularies; violates "do not create duplicate state systems" |
| Discard the Phase 02 8-state model and replace it | Breaks the approved Phase 02 contract and all existing records that reference it |
| Rename Phase 02 states to match the lifecycle | Loses the `BLOCKED`/`FAILED` distinctions that the lifecycle cannot express |

## Approval

**Required:** yes — architecture decision affecting all future phases.
**Status:** `APPROVED`
**Decided by:** User (explicit user approval, 2026-10-03)
**Approval basis:** Phase 03 implementation and verification were independently reviewed and accepted.

The user explicitly approved this decision on 2026-10-03. The lifecycle extends the Phase 02
status model; it does not replace it. `CONTROL-MODEL.md` §3 carries the mapping table, and
`validate-control.sh` enforces the presence of the lifecycle and truth vocabulary.

**Consequence:** all future phases may reference lifecycle stage and status independently.
Two vocabularies for "where are we" are now explicitly prevented by `DEC-0003`.