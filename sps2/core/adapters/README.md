# core/adapters

The adapter surface of SPS 2.0. It holds two kinds of content:

## Core-owned boundary files (must survive any adapter deletion, per D-P3-D)

| File | Role |
|---|---|
| `contract.schema.json` | the adapter contract; the machine-authoritative shape of an adapter entry |
| `registry.json` | the adapter index; `{"adapters": []}` is a valid zero-adapter state |
| `README.md` | this file |

## Per-agent adapters

Each adapter lives in its own directory `core/adapters/<agent-id>/` and is
declarative only (D-P3-C): a single `adapter.json` whose content equals the
entry with the same `agent_id` in `registry.json`. No hooks, no scripts, no
writes, and no agent-convention files outside this surface.

Invariants (machine-checked by `sps2/tools/test-portability.py` section 1 and
`sps2/core/adapter_registry.py`):

- every required contract field is present and no unknown field is;
- `writes_global_state` is always `false`;
- `detection`, when declared, is read-only;
- no duplicate `agent_id`;
- the core never imports or branches on an adapter.

## Current adapters (delivered under roadmap P3, decision D-P3-A)

| agent_id | maturity | meaning |
|---|---|---|
| `generic` | `DECLARED` | fallback for any repository-reading agent; must remain sufficient on its own |
| `codex` | `EXPERIMENTAL` | declarative entry; not yet exercised, so VERIFIED is not claimed |
| `opencode` | `EXPERIMENTAL` | declarative entry; not yet exercised, so VERIFIED is not claimed |

Maturity policy (D-P3-B): `DECLARED` alone is insufficient for P3 completion;
`VERIFIED` requires a recorded exercise; `EXPERIMENTAL` is the honest value
while the generic fallback remains available and no exercise has been recorded.

## Deletion semantics (D-P3-D)

"Delete all adapters" means: delete every `<agent-id>/` directory and empty
the registry's adapter list. The contract and the registry file remain
(core-owned), the registry becomes `{"adapters": []}` (valid), and every core
suite must still pass. `sps2/tools/test-portability.py` section 3 rehearses
exactly this on an isolated copy; it doubles as the documented rollback.

## Evidence

- decisions: `sps2/decisions/ROADMAP-P3-DECISIONS.json` (D-P3-A..G)
- evidence: `sps2/evidence/ROADMAP-P3-EVIDENCE.json`
- conformance test: `sps2/tools/test-portability.py`
