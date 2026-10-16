# P4 Task Register — Production Capability Promotion & Registry Hardening

| ID | Task | Status | Evidence |
|---|---|---|---|
| T-01 | Gate: verify P3 APPROVED, P4 NOT_STARTED, incident classification, legacy baseline | COMPLETE | EV-P4-008 |
| T-02 | Record legacy baseline before implementation | COMPLETE | EV-P4-011 |
| T-03 | Implement hardened promotion gate A-K | COMPLETE | EV-P4-001 |
| T-04 | Determine repository licence state by observation | COMPLETE | EV-P4-002 |
| T-05 | Correct the P3 KNOWN_PERMISSIVE claim to UNDECLARED | COMPLETE | EV-P4-003 |
| T-06 | Migrate registry to the CAP-P03 id scheme | COMPLETE | EV-P4-001 |
| T-07 | Execute real verification for each capability | COMPLETE | EV-P4-004 |
| T-08 | Prove ranking determinism and popularity independence | COMPLETE | EV-P4-005 |
| T-09 | Determine whether a CLS verifier implementation exists | COMPLETE | EV-P4-006 |
| T-10 | Evaluate all five candidates independently | COMPLETE | EV-P4-007 |
| T-11 | Store per-capability promotion assessments | COMPLETE | EV-P4-001 |
| T-12 | Implement the no-emoji validator with positive control | COMPLETE | EV-P4-009 |
| T-13 | Build validate-p4.sh with 20 negative cases | COMPLETE | EV-P4-010 |
| T-14 | Carry the P3 incident boundary forward unchanged | COMPLETE | EV-P4-008 |
| T-15 | Record P4 requirements, evidence, decisions, tasks, handoff, audit | COMPLETE | EV-P4-010 |

## Defects found and fixed during P4

Each was a real defect, diagnosed rather than waived:

1. **`REPO` path resolved one directory too high** in `promotion_gates.py`, so gate F
   could never find an implementation. Every capability failed gate F incorrectly.
2. **The popularity test was vacuous.** The original fixture made the most popular
   candidate also the evidence-best, so the assertion could not discriminate. The
   fixture was rebuilt so popularity and evidence deliberately disagree.
3. **The verification fixture lacked `source`** and used a P4 id against the P3
   engine, so two verifications failed for the wrong reason.
4. **`decide()` returned `None`** for multi-gate blocking sets.

None of these were resolved by relaxing a check.

## Explicitly not done in P4

No capability installed. No CMS or SEO implementation. No MCP. No third-party
package, skill or external software. No legacy modification. No machine-global
change. No remote created. No push. No P5 work. The P3 incident was not reopened.
Checkpoint `a7767cf` was not purged and no Git object was deleted.