# P5 — Implementation / Integration

Phase status: **APPROVED** by the User on 2026-10-04, scope strictly limited to
P5 implementation/integration.

P6, runtime activation, capability installation, MCP installation, new
capability promotion and CAP-P03-005 promotion are all explicitly NOT
approved. Nothing in this file is self-approved.

## What P5 implemented

| Unit | Location | Purpose |
|---|---|---|
| Core registry API | `sps2/core/registry_api.py` | Read-only project-local access to the capability registry; ten-link trace chain |
| Core selection | `sps2/core/selection.py` | Deterministic selection over promoted capabilities only |
| Core adapter boundary | `sps2/core/adapter_registry.py` | Adapter contract validation; proves the core is adapter-free |
| Governance attribution | `sps2/governance/attribution.py` | Rejects agent-attributed approvals |
| Integration CLI | `sps2/tools/sps5.py` | `select`, `verify`, `report` |
| P5 validator | `sps2/tools/validate-p5.py` | Structural checks plus a 12-case negative suite |
| Unit tests | `sps2/tests/test_p5.py` | 39 unit tests |

## Architecture boundary

```text
core/  +  governance/      agent-neutral, no agent names, stdlib only
        |
      adapters/            thin, deletable, never write global state
        |
  agent-specific            out of scope for P5
```

The `AGENTISH` approval-attribution pattern lives in `governance/`, not `core/`,
because detecting an agent-attributed approval requires knowing what an agent
name is. The core receives it as an injected predicate, so the core stays
neutral while the control still holds.

## Capability integration

| Capability | Lifecycle | Selection rank | Integrated |
|---|---|---|---|
| CAP-P03-001 | EVALUATED | 1 | yes |
| CAP-P03-002 | EVALUATED | 2 | yes |
| CAP-P03-003 | EVALUATED | 3 | yes |
| CAP-P03-004 | EVALUATED | 4 | yes |
| CAP-P03-005 | DEFERRED | excluded | **no** |

All four remain `EVALUATED`, not `ACTIVE` or `INSTALLED`. Nothing was
installed, so no runtime-tracing claim is made. `CAP-P03-005` stays deferred
behind gates F, H and K; `CONF-001` is unresolved and no LCP or INP threshold
was invented.

## Operational commands

```bash
python3 sps2/tools/sps5.py select     # regenerate the project-local selection
python3 sps2/tools/sps5.py verify     # trace integrity, determinism, adapters
python3 sps2/tools/sps5.py report     # machine-readable integration summary
python3 sps2/tools/validate-p5.py     # full P5 validator plus negative suite
python3 sps2/tests/test_p5.py         # unit tests
```

All commands are project-local, read-only except `select`, and install nothing.

## Dependencies

None. Standard library only. No package, skill, MCP server or external agent was
installed. No global configuration was created or modified.

## Licence and provenance

SPS 2.0 remains MIT. The SPS-CMS provenance classification is unchanged at
`USER_ATTESTATION` with `independently_verified: false`. P5 did not upgrade it
and does not claim third-party relicensing.

## Stop conditions not triggered

No new security issue was found, no credential appeared, provenance stayed
certain, no unresolved dependency arose, no licence conflict appeared, no legacy
file needed modification, the architecture did not change, and no validator
needed repair. `CAP-P03-005` was not promoted.