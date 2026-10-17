# P5 — Tasks

Phase status: **AWAITING_USER_APPROVAL**. No task below is self-approved.

| ID | Task | Status | Artefact |
|---|---|---|---|
| T5-01 | Core registry API with the ten-link trace | COMPLETE | `sps2/core/registry_api.py` |
| T5-02 | Deterministic project-local selection | COMPLETE | `sps2/core/selection.py` |
| T5-03 | Adapter boundary validation | COMPLETE | `sps2/core/adapter_registry.py` |
| T5-04 | Move approval attribution into governance | COMPLETE | `sps2/governance/attribution.py` |
| T5-05 | Integration CLI (select / verify / report) | COMPLETE | `sps2/tools/sps5.py` |
| T5-06 | Generate the project-local selection record | COMPLETE | `sps2/project/SELECTION-P5-0001.json` |
| T5-07 | Wire the selection link into the registry | COMPLETE | `sps2/capability/registry.json` |
| T5-08 | Unit tests, positive and negative | COMPLETE | `sps2/tests/test_p5.py` |
| T5-09 | P5 validator with negative suite | COMPLETE | `sps2/tools/validate-p5.py` |
| T5-10 | P5 requirements record | COMPLETE | `sps2/requirements/P5-REQUIREMENTS.json` |
| T5-11 | P5 evidence record | COMPLETE | `sps2/evidence/P5-EVIDENCE.json` |
| T5-12 | P5 handoff documentation | COMPLETE | `sps2/handoff/HANDOFF-P5.md` |
| T5-13 | P5 audit report | COMPLETE | `sps2/audit/AUDIT-P5.md` |
| T5-14 | Update project-local state | COMPLETE | `sps2/project/LOCAL-STATE.md` |

## Out of scope, deliberately not started

| ID | Item | Reason |
|---|---|---|
| T5-X1 | CAP-P03-005 promotion | Gates F, H and K block it; no approval given |
| T5-X2 | Runtime activation / lifecycle transition | Not approved; no transition defined |
| T5-X3 | Global installation or configuration | Forbidden by the architecture |
| T5-X4 | MCP or skill installation | Not approved |
| T5-X5 | Resolving CONF-001 | Requires evidence that does not exist |
| T5-X6 | Legacy remediation or KI-01 remediation | Explicitly not authorised |
| T5-X7 | History rewrite, reflog expiry, GC, push | Explicitly forbidden |
| T5-X8 | P6 and any later roadmap phase | Out of scope for P5 |

## Deviations from plan

- T5-04 was not in the original plan. It became necessary because the first
  draft put agent-name detection inside `core/`, which the agent-neutrality
  rule forbids. Moving it to `governance/` fixed the violation without
  weakening the control.
- T5-09 was first written in bash and had to be rewritten in Python. See
  `EV-P5-017`.