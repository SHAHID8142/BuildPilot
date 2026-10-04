# Fresh-agent resume checklist (mechanical)

Purpose: a session with no prior memory must be able to determine, from
repository state alone, the current phase, the current task, the next allowed
action and the forbidden actions. This checklist is executed mechanically by
`sps2/tools/test-portability.py` section 4 (decision D-P3-E: the target set is
the whole repository; the historical `.sps/` + `docs/` assumption is stale, and
the newest authoritative state lives in `sps2/`).

## How to use this checklist

1. Read the canonical sources below, in order.
2. Answer the four questions using only what those files say.
3. Do not act on anything the sources list as forbidden.

## Canonical sources (read in this order)
SOURCE: sps2/decisions/ROADMAP-P3-DECISIONS.json
SOURCE: sps2/decisions/P7-READINESS-DECISIONS.json
SOURCE: sps2/decisions/ROADMAP-EXECUTION-RECONCILIATION.json
SOURCE: sps2/handoff/HANDOFF-P6.md
SOURCE: sps2/evidence/ROADMAP-P3-EVIDENCE.json
SOURCE: sps2/core/adapters/README.md
SOURCE: sps2/tools/test-portability.py
SOURCE: .sps/STATE.md

Note: `.sps/STATE.md` is the legacy phase pointer; it records PHASE-05 and is
NOT authoritative for the newest state. The newest state is in `sps2/`.

## Answers obtained from these sources (recorded 2026-10-04)

### Current phase
Roadmap P3 (Agent Interoperability) is implemented and verified under D-P3-F.
User approval of the delivered state is PENDING (the completion block in
ROADMAP-P3-DECISIONS.json). P7 has NOT started and is NOT authorised.

### Current task
None in progress. The roadmap P3 delivery is complete: two declarative
EXPERIMENTAL adapters (codex, opencode), the generic fallback retained, the
portability conformance test, the evidence record, and the two guard
corrections of D-P3-G.

### Next allowed action
User review of the delivered state: approve it, or direct rework. Only after a
recorded User approval may the reconciliation record report roadmap P3 as
SATISFIED. Until then P7 remains gated: D-P7-B's prerequisites are met in
substance but P3 approval and the D-P7-D threat model are outstanding, and
starting P7 still needs its own explicit User authorisation.

### Forbidden actions
- beginning P7 implementation of any kind;
- claiming a threat model exists, or treating D-P7-D as satisfied;
- closing CONF-001, or recording any LCP or INP threshold;
- promoting any capability, in particular CAP-P03-005;
- changing the production capability registry;
- runtime activation of any kind;
- installing any package, dependency, skill, MCP server or CLI;
- machine-global changes of any kind, including global git configuration;
- modifying any legacy artefact (legacy diff must remain 0);
- rewriting history, purging checkpoint a7767cf, or force-pushing;
- pushing to the public repository without separate authorisation.

## Rollback
Deleting every directory under `sps2/core/adapters/` except the core-owned
`README.md`, `contract.schema.json` and `registry.json`, and emptying the
registry's adapter list, is the documented rollback. It returns the system to
a valid zero-adapter state in one revert commit and is rehearsed by
`sps2/tools/test-portability.py` section 3.
