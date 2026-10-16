# P3 Task Register — Production Capability Registry and Selection Engine

| ID | Task | Status | Evidence |
|---|---|---|---|
| T-01 | Gate check: P1 approved, P2 approved as RESEARCH_AND_AUDIT, P3 not started, tree clean, all validators green | COMPLETE | EV-P3-009 |
| T-02 | Read P1/P2 architecture, schemas, validators and research before changing anything | COMPLETE | EV-P3-009 |
| T-03 | Design the deterministic promotion gate | COMPLETE | EV-P3-001 |
| T-04 | Implement `promote()` with 30+ named rejection rules | COMPLETE | EV-P3-001 |
| T-05 | Implement evidence-weighted ranking | COMPLETE | EV-P3-002 |
| T-06 | Prove determinism across input permutations | COMPLETE | EV-P3-002 |
| T-07 | Prove popularity cannot outrank evidence | COMPLETE | EV-P3-002 |
| T-08 | Implement forced user choice with non-overridable safety | COMPLETE | EV-P3-003 |
| T-09 | Implement staleness model and stale-as-active refusal | COMPLETE | EV-P3-004 |
| T-10 | Promote only evidenced capabilities into the production registry | COMPLETE | EV-P3-001 |
| T-11 | Record every deferred or rejected candidate with a reason | COMPLETE | EV-P3-006 |
| T-12 | Create the project-local selection record | COMPLETE | EV-P3-005 |
| T-13 | Build `check_p3.py` behavioural validator | COMPLETE | EV-P3-001 |
| T-14 | Build `validate-p3.sh` with cases A-O plus positive controls | COMPLETE | EV-P3-001 |
| T-15 | Preserve all P2 research gaps as unresolved | COMPLETE | EV-P3-006 |
| T-16 | Confirm no machine-global change and no dependency installed | COMPLETE | EV-P3-007 |
| T-17 | Update P1/P2 validators whose invariants legitimately changed | COMPLETE | EV-P3-009 |
| T-18 | Record P3 requirements, evidence, decisions, tasks, handoff, audit | COMPLETE | EV-P3-009 |

## Validator defects found and fixed during P3

Each was a real defect, fixed rather than worked around:

1. `check_p3.py` swallowed exceptions, hiding a real `IndexError` behind a
   generic "not valid structured input" message.
2. `check_p3.py` `records` mode read the wrong `sys.argv` indices.
3. P3 requirement records carried acceptance criteria in the `evidence` field
   because the generator tuple indices were off by one.
4. `validate-p3.sh` gate helper lost a quoted regex argument, causing
   `$2: unbound variable`.
5. `validate-p2.sh` printed an empty FAIL line when a test passed, due to an
   `A && fail || pass` chain.
6. A missing closing `fi` in the POSCTRL-1 block left the structural section
   unterminated.

## Explicitly not done in P3

No capability installed. No skill or MCP installed. No CMS or SEO
implementation. No third-party code executed. No legacy modification. No remote
created. No push. No P4 work. `KI-01` untouched.