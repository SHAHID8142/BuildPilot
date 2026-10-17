# P7 Threat Model — Persistent Project State

**Author**: implementation agent (design author, not a User; not an approval)  
**Date**: 2026-10-05  
**Scope**: Roadmap P7 persistent project-local state only. Does not authorise P7 implementation.  
**Prerequisite**: D-P7-D (threat model required before P7 implementation begins) — satisfied by this artefact.  
**Companion**: `sps2/tools/validate-p7-readiness.py` (machine-checked)

---

## 1. What P7 persistent state is and where it may live

P7 introduces **persistent project-local state** — the memory layout — as its
primary deliverable. That state:

- lives **inside the SPS 2.0 project only** (the roadmap forbids writing state
  outside the project);
- lives **outside** the production capability registry (the registry is a
  separate lifecycle-controlled artefact);
- must not be written to machine-global paths, legacy paths, or outside the
  repository.

The memory layout is the only new persistent artefact P7 creates. Team bootstrap
and the isolation validator are derived from it; they do not introduce
additional durable state.

## 2. Assets

| Asset | Owner | Protected by |
|---|---|---|
| Memory layout files | SPS 2.0 project | integrity checks + rollback |
| Production capability registry | lifecycle controls | read-only for P7 |
| Decision / evidence / handoff records | governance format | attribution + schema |
| Existing adapters (codex, opencode) | D-P3-A contract | validation |
| Checkpoint `a7767cf` | P3 incident record | not purged |

## 3. Threat actors and failure modes

| Actor / source | Failure mode | Risk |
|---|---|---|
| Accidental agent action | Writes stale, partial, or wrong memory layout | Integrity loss |
| Malicious repo write | Memory layout tampered or injected | Integrity + attribution |
| Interrupted operation | Partial write leaves layout corrupt | Stale/corrupt state |
| Cross-project share | Two projects use the same memory layout | Isolation breach |
| Stale layout after change | Layout diverges from actual project state | Degraded onboarding |
| Activation before authorisation | P7 state used while P7 is unauthorised | Accidental activation |
| Credential in layout | Secrets written into memory layout | Secret exposure |

## 4. Trust boundaries

1. **Project-local boundary** — memory layout must not leave the repository.
2. **SPS 2.0 vs legacy boundary** — legacy files untouched (D-P7-C); legacy
   diff stays 0.
3. **Registry boundary** — P7 state must not modify, promote, or activate
   capabilities in the production registry.
4. **Agent vs User boundary** — memory layout authored by an agent must be
   distinguishable from User-attributed decisions (per `attribution.py`).
5. **Phase boundary** — P7 state must not break P1–P6 validators.

## 5. Integrity risks

- Partial/interrupted writes: the memory layout must be written atomically
  (write to temp, validate, then rename) so a crash never leaves a half-written
  layout.
- Stale layout: after any project change the layout must be re-validated before
  reuse; a layout that fails validation must be regenerated or rolled back, not
  patched by inference.
- Corruption detection: the validator must detect corrupt layout content (wrong
  schema, missing required fields, unhashable keys) and reject it with a
  controlled message — never crash.

## 6. Attribution risks

- Agent-authored memory entries must not be treated as User decisions. The
  governance attribution predicate (`approval_is_user_attributable`) must be
  applied to any approval recorded against the memory layout.
- The memory layout must carry a `maintained_by` field that names an
  identifiable human User, not an agent.

## 7. Accidental activation risks

- P7 memory state must not be activated, loaded, or applied by any P1–P6
  validator or tool unless the caller explicitly opts into P7 context.
- No runtime activation of capabilities derived from the memory layout.
- The readiness validator must reject any claim that P7 is active without
  explicit User authorisation.

## 8. Stale / corrupt state

- A corrupt memory layout must be detected and reported with a controlled
  message (no traceback leak).
- Stale layout entries (referencing removed adapters, capabilities, or
  decisions) must be flagged, not silently ignored.
- Fresh-agent resume must rebuild the layout from repository state alone
  (D-P3-E portable checklist applies).

## 9. Rollback / removal

- Memory layout must be revertible to the prior state by a single operation
  (the roadmap names "revert memory layout" as rollback).
- Removal of the memory layout must leave the project in a valid, cloneable
  state (no orphaned references, no broken validator paths).
- Rollback must not require modifying legacy files or the production registry.

## 10. Partial-write / interrupted-operation behaviour

- Writes must be atomic: write-temp → validate → rename. Interruption at any
  point leaves the prior layout intact.
- On resume after interruption the validator must detect the incomplete write
  and reject it cleanly, not silently accept partial data.

## 11. Portability / fresh-agent recovery

- A fresh clone must recover the memory layout from repository state alone
  (mechanical checklist, no machine-global or legacy fallback).
- The portability test's zero-adapter and full-adapter exercises must both
  pass with the memory layout present.

## 12. Secret / credential exposure

- No credential, token, key, or secret may be stored in the memory layout.
- The validator must reject any layout entry containing secret-like values.
- No credential may be read, printed, hashed, or transmitted by P7 tooling.

## 13. Interaction with existing registry and lifecycle controls

- The production capability registry is read-only for P7; no promotion,
  activation, or lifecycle change.
- CAP-P03-005 stays DEFERRED / NOT_PROMOTED.
- Adapter contract and maturity rules (D-P3-A/B) remain enforced.

## 14. Safeguards and validation requirements

- `validate-p7-readiness.py` must pass on the live tree and on every isolated
  clone before P7 implementation begins.
- Isolation test: two projects remain isolated (roadmap acceptance).
- Onboarding dry run: a new teammate understands the project from the repo
  alone (roadmap acceptance).
- Negative tests for each threat category above.
- No P7 implementation artefact (`requirements/P7-REQUIREMENTS.json`,
  `evidence/P7-EVIDENCE.json`, `tasks/P7-TASKS.md`, `handoff/HANDOFF-P7.json`,
  `decisions/P7-DECISIONS.json`, `memory`, `isolation_validator.py`,
  `bootstrap`) may exist while P7 is unauthorised.

## 15. Explicit prohibited behaviours

- Writing state outside the project (roadmap forbidden).
- Modifying legacy files outside the eight content-and-mode-pinned updater files authorized by DEC-7301; D-P7-C's legacy-diff-zero intent otherwise remains binding.
- Modifying the production capability registry.
- Promoting or activating any capability.
- Resolving CONF-001 (unchanged).
- Inventing LCP / INP observations (unchanged).
- Runtime activation of any kind (D-P6-2).
- Installing any dependency, skill, MCP, CLI, or package.
- Machine-global state writes.
- Purging checkpoint `a7767cf`, rewriting history, force-pushing.
- Beginning P8 or later.
- Self-approval of any P7 gate.

## 16. Acceptance criteria (machine-checkable)

1. Isolation test passes: two projects isolated.
2. Onboarding dry run passes: fresh agent resumes from repo state alone.
3. Memory layout validates with controlled messages on malformed input.
4. Rollback restores prior layout in a single operation.
5. `validate-p7-readiness.py` passes with the threat model present and P7
   still unstarted.
6. No P7 implementation artefact exists.
7. Production registry byte-identical; legacy diff contains only the DEC-7301 pinned exception.
8. CONF-001 UNRESOLVED; LCP/INP NOT_OBSERVED.

## 17. Rollback / removal criteria

1. Memory layout revertible to prior state by a single operation.
2. Removal leaves project cloneable and validators green.
3. No orphaned references after removal.
4. Rollback does not touch legacy files or the production registry.
