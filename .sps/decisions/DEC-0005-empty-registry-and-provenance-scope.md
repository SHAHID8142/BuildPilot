# DEC-0005 — Registry starts EMPTY; no capability is fabricated

- **Date:** 2026-10-03
- **Status:** Active
- **Approval:** `APPROVED`
- **Phase / Task:** `PHASE-04` / `PHASE-04-T02`
- **Evidence:** `EV-P04-002`
- **Supersedes:** none

---

## Decision

Ship the Phase 04 capability registry and research cache **empty**, containing zero
capabilities and zero research entries.

## Reason

The temptation in a discovery-architecture phase is to demonstrate the registry by populating
it. Doing so would require either inventing capabilities or performing live research and
installation — both forbidden:

- **Inventing** capability records would fabricate facts about software that was never
  inspected. That is exactly the `DECLARED`-vs-`IMPLEMENTED` failure Phase 01 **F-9**
  identified, repeated in a new form.
- **Live research** would require network access and would begin populating a registry whose
  own security gate has not yet been validated by the user.

The mechanism is the deliverable. The content requires research and approval that belong to a
later, approved stage.

The validator treats an empty registry as **valid** and reports it explicitly, so emptiness is
a recorded state rather than a silent gap.

## Evidence

`EV-P04-002` — registry `capabilities: 0`, research `entries: 0`, both valid JSON. The
validator reports `registry is empty (mechanism only) - nothing to validate yet`.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Populate with the existing SKILL-ROUTER entries | Re-imports the hardcoded preferences the phase exists to replace, and would imply they were evaluated |
| Populate with 2-3 hand-written example capabilities | Fabricated security, licence and maintenance claims — precisely the prohibited behaviour |
| Add a `EXAMPLES.md` with illustrative records | Same fabrication risk; illustrative data is routinely mistaken for real data |
| Seed from a live registry scan | Requires network access and begins selecting before approval |

## Approval

**Required:** yes — this bounds what Phase 04 delivers.
**Status:** `APPROVED`
**Decided by:** User (explicit user approval, 2026-10-03)
**Approval basis:** Phase 04 implementation and verification were independently reviewed and accepted.

---
