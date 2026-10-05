# Fresh-agent resume checklist (mechanical)

Purpose: a session with no prior memory must be able to determine, from
repository state alone, what Roadmap P3 is, what was authorised, which adapters
exist and why, what remains, what is forbidden, which decisions were made and
where the authoritative records live — together with the current phase, the
current task and the next allowed action.

This checklist is executed mechanically by `sps2/tools/test-portability.py`
section 4 (decision D-P3-E: the target set is the whole repository; the
historical `.sps/` + `docs/` assumption is stale, and the newest authoritative
state lives in `sps2/`).

## How to use this checklist

1. Read the canonical sources below, in order.
2. Answer the questions using only what those files say.
3. Do not act on anything the sources list as forbidden.

## Canonical sources (read in this order)
SOURCE: .sps/architecture/SPS2-ROADMAP.md
SOURCE: .sps/architecture/SPS2-AGENT-INTEROPERABILITY.md
SOURCE: sps2/decisions/ROADMAP-P3-DECISIONS.json
SOURCE: sps2/decisions/P7-READINESS-DECISIONS.json
SOURCE: sps2/decisions/ROADMAP-EXECUTION-RECONCILIATION.json
SOURCE: sps2/evidence/ROADMAP-P3-EVIDENCE.json
SOURCE: sps2/core/adapters/README.md
SOURCE: sps2/tools/portability.py
SOURCE: sps2/tools/test-portability.py
SOURCE: sps2/handoff/HANDOFF-P6.md
SOURCE: .sps/STATE.md

Note: `.sps/STATE.md` is the legacy phase pointer; it records PHASE-05 and is
NOT authoritative for the newest state. The newest state is in `sps2/`.

COMPLETION: PENDING_USER_APPROVAL

## What P3 is

Roadmap P3 is the *Agent Interoperability* phase of `.sps/architecture/SPS2-ROADMAP.md`:

- **Objective:** prove portability with real adapters.
- **Scope:** the `core/adapters/` contract plus adapters.
- **Deliverables:** `contract.schema.json`; adapters; a conformance test.
- **Acceptance:** deleting all adapters leaves the core validators passing, and
  a fresh agent can resume the project from repository state alone.
- **Verification:** the portability suite (four criteria, section 7 of
  `.sps/architecture/SPS2-AGENT-INTEROPERABILITY.md`).
- **Approval:** the User. No agent may record it.

"Roadmap P3" is the roadmap phase, not the executed phase `P3` (*Production
Capability*, `sps2/decisions/P3-DECISIONS.json`), which already happened. The
two are reconciled in `sps2/decisions/ROADMAP-EXECUTION-RECONCILIATION.json`
(`REC-PHASES-0001`, entry `P3`).

## What was authorised

`sps2/decisions/ROADMAP-P3-DECISIONS.json` records seven User decisions, all
`APPROVED`, `decided_by: User`, `decided_on: 2026-10-04`:

| Decision | Authorised content |
|---|---|
| `D-P3-A` | exactly two low-risk adapters: Codex and OpenCode; a third needs a new decision |
| `D-P3-B` | `VERIFIED` requires a recorded exercise; `EXPERIMENTAL` is acceptable while the generic fallback stands; `DECLARED` alone is insufficient |
| `D-P3-C` | declarative-only adapters under `core/adapters/<id>/`; no agent-convention file created or modified anywhere else |
| `D-P3-D` | "delete all adapters" means the per-agent entries and directories; the core-owned contract and registry remain; `{"adapters": []}` is a valid state |
| `D-P3-E` | fresh-agent resume targets the whole repository, executed mechanically |
| `D-P3-F` | the bounded implementation scope, and the explicit forbidden list |
| `D-P3-G` | exactly two guard corrections, at the invariant level, no broader weakening |

`D-P3-F` also forbids, explicitly: P7 implementation, threat-model
implementation or claim, closing `CONF-001`, inventing LCP/INP values,
promoting `CAP-P03-005`, production-registry changes, runtime activation,
package/dependency/skill/MCP installation, machine-global changes, legacy-file
changes, history rewrite, force-push and any ordinary push.

## Adapters delivered

| agent_id | maturity | what it is | why it exists |
|---|---|---|---|
| `generic` | DECLARED | the fallback for any repository-reading agent | the architecture requires an unknown agent to get correct behaviour from repository state alone, so the fallback must stand on its own |
| `codex` | EXPERIMENTAL | declarative entry for the OpenAI Codex CLI | the architecture's target-agent table marks Codex low risk, and `D-P3-A` selected the two low-risk targets |
| `opencode` | EXPERIMENTAL | declarative entry for OpenCode | as above; OpenCode is the other low-risk target |

Maturity is truthful by decision `D-P3-B`: no agent has actually been exercised
under this authorisation, so neither real adapter may claim `VERIFIED`. Each
adapter is one declarative file, `core/adapters/<agent_id>/adapter.json`, equal
to its registry entry in `core/adapters/registry.json`. No adapter writes
outside the project, executes a process, installs anything, or creates an
agent-convention file. The mechanics and the invariants are documented in
`sps2/core/adapters/README.md`.

## Current phase

Roadmap P3 (Agent Interoperability) is implemented and verified under
`D-P3-F`. User approval of the delivered state is PENDING (the `completion`
block in `ROADMAP-P3-DECISIONS.json`). P7 has NOT started and is NOT
authorised.

## Current task

None in progress. The roadmap P3 delivery is complete: two declarative
EXPERIMENTAL adapters (`codex`, `opencode`), the generic fallback retained, the
portability operation `sps2/tools/portability.py` with its conformance test
`sps2/tools/test-portability.py`, this resume checklist, the evidence records
`EV-RP3-001..`, and the two guard corrections of `D-P3-G`.

## Next allowed action

User review of the delivered state: approve it, or direct rework. Only after a
recorded User approval may the reconciliation record report roadmap P3 as
SATISFIED. Until then P7 remains gated: `D-P7-B`'s prerequisites are met in
substance but P3 approval and the `D-P7-D` threat model are outstanding, and
starting P7 still needs its own explicit User authorisation.

## What remains

1. User approval of the delivered roadmap P3 state.
2. The `D-P7-D` threat model for persistent project-local state. It is a
   separate prerequisite owned by P7, deliberately NOT part of roadmap P3.
3. P7 implementation itself, which is unauthorised.

Nothing else in the roadmap P3 scope is outstanding: the contract, the two
adapters, the fallback, the portability/delete-all conformance capability and
this resume state are all delivered.

## Forbidden actions
- beginning P7 implementation of any kind;
- claiming a threat model exists, or treating D-P7-D as satisfied;
- closing CONF-001, or recording any LCP or INP threshold;
- promoting any capability, in particular CAP-P03-005;
- changing the production capability registry;
- runtime activation of any kind;
- installing any package, dependency, skill, MCP server or CLI;
- machine-global changes of any kind, including global git configuration;
- modifying any legacy artefact (legacy diff must remain 0);
- creating or modifying an agent-convention file such as `AGENTS.md`
  (`D-P3-C`);
- rewriting history, purging checkpoint a7767cf, or force-pushing;
- pushing to the public repository without separate authorisation.

## Authoritative records

| Record | What it is authoritative for |
|---|---|
| `.sps/architecture/SPS2-ROADMAP.md` | the roadmap phase definitions, objective, deliverables and acceptance |
| `.sps/architecture/SPS2-AGENT-INTEROPERABILITY.md` | the adapter separation principle and the four portability criteria |
| `sps2/decisions/ROADMAP-P3-DECISIONS.json` | `D-P3-A..G`, the bounded scope, the forbidden list and the completion state |
| `sps2/decisions/ROADMAP-EXECUTION-RECONCILIATION.json` | roadmap-to-executed mapping and what may be claimed as satisfied |
| `sps2/decisions/P7-READINESS-DECISIONS.json` | the P7 gate, including the `D-P7-D` threat-model prerequisite |
| `sps2/evidence/ROADMAP-P3-EVIDENCE.json` | the recorded command output behind every roadmap P3 claim |
| `sps2/core/adapters/registry.json` | the adapter set, maturities and detection metadata |
| `sps2/core/adapters/contract.schema.json` | the machine-authoritative shape of one adapter |
| `sps2/core/adapters/README.md` | the surface, its invariants and its deletion semantics |
| `sps2/tools/portability.py` | the delete-all operation and the enforced `D-P3-A` bound |
| `sps2/tools/test-portability.py` | the conformance suite that executes all of it |
| `.sps/STATE.md` | legacy phase pointer only (PHASE-05); not authoritative for the newest state |

## Rollback

The rollback is the documented delete-all, mechanised so it can be rehearsed
before it is ever applied:

```
python3 sps2/tools/portability.py                  # rehearse on an isolated copy
python3 sps2/tools/portability.py --verify         # check the delivered state
python3 sps2/tools/portability.py --apply --root . --confirm   # DESTRUCTIVE
```

`--apply` deletes every `core/adapters/<agent-id>/` directory and empties the
registry to `{"adapters": []}`, keeping the core-owned `contract.schema.json`,
`registry.json` and `README.md` (`D-P3-D`). It requires `--root` and
`--confirm`, it is never run by any suite, and it changes nothing in `core/`,
`.sps/`, the production capability registry or any legacy file. The default
rehearsal proves the same removal on an isolated copy, re-runs every core
validator in the zero-adapter state, restores the surface and re-validates it,
so the rollback is known to leave a valid, reversible state.

Recorded 2026-10-04 under `D-P3-E`; extended 2026-10-05 to answer what P3 is,
what was authorised, which adapters exist and why, what remains and where the
authoritative records live.