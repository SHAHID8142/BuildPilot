# P6 — Tasks

Phase: **Technology Research** (roadmap definition, per D-P6-1).
Status: **IMPLEMENTED / VERIFIED / APPROVED** (User, 2026-10-04),
scope `TECHNOLOGY_RESEARCH_ONLY`.

P6 was not self-approved; the approval was given explicitly by the User.

| ID | Task | Status | Artefact |
|---|---|---|---|
| T6-01 | Convert the readiness audit into authoritative P6 scope and terminology | COMPLETE | `sps2/research/P6-SCOPE-AND-TERMINOLOGY.md` |
| T6-02 | Record the User decisions D-P6-1 and D-P6-2 | COMPLETE | `sps2/decisions/P6-DECISIONS.json` |
| T6-03 | Build the readiness evaluator (roadmap deliverable) | COMPLETE | `sps2/core/technology_readiness.py` |
| T6-04 | Populate the research cache with attributed evidence | COMPLETE | `sps2/research/cache.json` |
| T6-05 | Re-attempt the CONF-001 retrieval and record only what was observed | COMPLETE | `sps2/research/cache.json` |
| T6-06 | Replace the obsolete no-P6 invariant with a phase-aware one | COMPLETE | `sps2/tools/validate-p5.py` |
| T6-07 | Build the P6 validator with negative suite and positive control | COMPLETE | `sps2/tools/validate-p6.py` |
| T6-08 | Mutation-test the new phase boundary | COMPLETE | `sps2/tools/test-phase-boundary.sh` |
| T6-09 | P6 requirements, tasks, handoff | COMPLETE | this file and `sps2/handoff/HANDOFF-P6.md` |

## Out of scope, deliberately not started

| ID | Item | Reason |
|---|---|---|
| T6-X1 | Runtime activation of any kind | D-P6-2 explicitly not approved |
| T6-X2 | Installing any dependency, skill, MCP, CLI or package | not approved; none required |
| T6-X3 | Promoting any capability | not approved |
| T6-X4 | CAP-P03-005 promotion | gates F, H, K still open |
| T6-X5 | Closing CONF-001 | a User decision; P6 records evidence only |
| T6-X6 | P7 project-local state and memory | not started, not authorised |
| T6-X7 | Reconciling roadmap versus executed numbering | a User decision; recorded, not resolved |

## Deviations from the naive plan

- The P5 validator's invariant "no file named `P6*` may exist" became obsolete
  once D-P6-1 and D-P6-2 were recorded. It was **replaced**, not removed, with
  a phase-aware invariant that additionally asserts runtime, promotion, deferral
  and P7 boundaries. It checks strictly more than before.
- `governance/attribution.py` required `decided_on`, but the repository's own
  decision records (DEC-0011 to DEC-0015) use `decided_at`. Rather than work
  around it, the predicate was corrected to accept either name. Attribution is
  still judged on WHO and WHEN; agent deciders and missing dates are still
  rejected.