# P7 Deliverables — Documentation

Schema: sps2.p7-deliverables/v1
Generated: 2026-10-05
Purpose: Document the three roadmap P7 deliverables and how to validate them.

## Deliverables

### 1. Memory Layout — `sps2/memory/memory-layout.json`

Single source of truth for project memory. Consolidates scattered state
for fresh-agent onboarding and isolation validation.

- **Schema**: sps2.memory-layout/v1
- **Scope**: Project-local only; read-only for P1–P6 validators
- **Sections**: phase_index, capability_registry, decision_records,
  evidence_records, audit_records, portability, rollback, boundaries
- **Integrity**: Each entry carries a sha256 hash of the referenced file

**Validation**: `validate-bootstrap.py` check 3 — verifies schema and
non-emptiness.

### 2. Team Bootstrap — `sps2/memory/team-bootstrap.md`

Mechanical 7-step onboarding checklist for fresh agents. Based on
repository state and authoritative sources. No generated runtime state.

Steps:
1. Read the memory layout
2. Verify phase index
3. Verify capability registry
4. Verify P7 boundaries
5. Verify no P7 implementation artefacts beyond authorised scope
6. Verify CONF-001 and LCP/INP
7. Run the full sequential validation suite

**Validation**: `validate-bootstrap.py` checks 1–2 — readable, steps map
to repository artifacts.

### 3. Isolation Validator — `sps2/tools/isolation_validator.py`

Proves mechanically that two projects remain isolated:

- No shared persistent state (memory layout schema valid)
- No cross-project imports (no references to machine-global paths)
- No cross-project registry/state references (registry clean)

**Validation**: `isolation_validator.py` itself — 3 checks, 0 failures.

## Validation order

Run in this sequence (full sequential suite, Step 7):

1. `python3 sps2/tools/isolation_validator.py` — isolation check
2. `python3 sps2/tools/validate-bootstrap.py` — onboarding dry-run
3. `python3 sps2/tools/validate-p7-readiness.py` — P7 readiness audit
4. `python3 sps2/tools/validate-p5.py` — P5 implementation/integration
5. `python3 sps2/tools/validate-p6.py` — P6 technology research
6. Full sequential: all phases in order, 0 failures required

## Boundaries

- no_generated_runtime_state: True
- project_local_only: True
- no_legacy_modification: True
- no_machine_global: True
