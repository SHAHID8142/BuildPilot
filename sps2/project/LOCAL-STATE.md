# project/LOCAL-STATE

Project-local state for SPS 2.0. Nothing here is machine-global.

## Phase

P5 — implementation/integration. Status: **APPROVED** (User, 2026-10-04).
P6 — **NOT_STARTED / NOT_APPROVED**. Runtime activation **NOT_APPROVED**.

## Selected capabilities

`SELECTION-P5-0001.json` is the current project-local selection.

| Rank | Capability | Lifecycle | Approved by |
|---|---|---|---|
| 1 | CAP-P03-001 | EVALUATED | User, 2026-10-04 |
| 2 | CAP-P03-002 | EVALUATED | User, 2026-10-04 |
| 3 | CAP-P03-003 | EVALUATED | User, 2026-10-04 |
| 4 | CAP-P03-004 | EVALUATED | User, 2026-10-04 |

All four are `EVALUATED`, not `ACTIVE` or `INSTALLED`. No runtime-tracing
claim is made. Nothing was installed.

## Excluded

`CAP-P03-005` is `DEFERRED` and unselectable. Blocking gates F, H and K stand:
no executable CLS verifier, no production approval, and `CONF-001` unresolved.

## How to regenerate

```bash
python3 sps2/tools/sps5.py select
python3 sps2/tools/sps5.py verify
python3 sps2/tools/sps5.py report
```

Selection is deterministic: the same registry and requirement always yield the
same ordering and the same fingerprint.

## Boundary

- Global: SPS 2.0 core, and explicitly user-promoted preferences only.
- Project-local: capabilities, registry, MCP config, memory, research cache,
  decisions, evidence, selection, project configuration.

No `~/.sps/` path or any other machine-global location was created or modified
during P5.

## Related records

- Requirements: `sps2/requirements/P5-REQUIREMENTS.json`
- Evidence: `sps2/evidence/P5-EVIDENCE.json`
- Tasks: `sps2/tasks/P5-TASKS.md`
- Handoff: `sps2/handoff/HANDOFF-P5.md`
- Audit: `sps2/audit/AUDIT-P5.md`
