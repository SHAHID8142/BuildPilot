# DEC-0006 — Provenance enforcement is detection-based, not runtime-based

- **Date:** 2026-10-03
- **Status:** Active
- **Approval:** `APPROVED`
- **Phase / Task:** `PHASE-04` / `PHASE-04-T04`
- **Evidence:** `EV-P04-001`
- **Supersedes:** none

---

## Decision

Implement provenance as **structural records plus deterministic validation**, and explicitly
declare runtime provenance tracking as `DECLARED` (not implemented).

## Reason

The brief requires provenance to be designed "now" while forbidding a runtime (§23: no daemon,
no AI runtime, no service). A validator can prove a record is *structurally* complete and
*internally consistent*. It cannot prove the record is *truthful* — that depends on the agent
reporting honestly, which is why Phase 03's maturity ladder exists.

Claiming runtime tracking would repeat the Phase 01 **F-9** pattern: documenting a capability
no code implements. `PROVENANCE.md` therefore tabulates enforcement honestly:

| Layer | Status |
|---|---|
| Structural completeness | `ENFORCED` |
| Chain ordering | `VALIDATED` |
| Truthful recording | `DOCUMENTED` |
| Runtime tracking | `DECLARED` — not implemented |

## Evidence

`EV-P04-001` — validator confirms the provenance section and its honesty table are present.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Build a runtime tracer | Forbidden by §23; a service/daemon is explicitly out of scope |
| Omit the honesty table | Would let readers assume full enforcement |
| Mark the whole contract `IMPLEMENTED` | Would overclaim; only some layers are enforced |

## Approval

**Required:** yes — this bounds a core Phase 04 guarantee.
**Status:** `APPROVED`
**Decided by:** User (explicit user approval, 2026-10-03)
**Approval basis:** Phase 04 implementation and verification were independently reviewed and accepted.