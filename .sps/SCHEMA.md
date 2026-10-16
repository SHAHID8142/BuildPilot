# SPS Governance — Machine-Readable Schemas

Contracts for every governance record. Plain Markdown + JSON so any tool, agent,
model, or IDE can read them without a vendor runtime. No YAML parser, no framework.

---

## 1. Task Record

```json
{
  "id": "PHASE-02-T01",
  "phase": "PHASE-02",
  "title": "Establish Git provenance",
  "requirement": "REQ-P02-01",
  "status": "VERIFIED",
  "completion": "COMPLETE",
  "verification": "VERIFIED",
  "approval": "PENDING_USER_APPROVAL",
  "implemented_by": ["<agent-id>"],
  "files_changed": ["<path>"],
  "evidence": ["EV-P02-001"],
  "decisions": ["DEC-0001"],
  "blocked_by": null,
  "notes": ""
}
```

**Field rules:**
- `status` — the state machine value (`GOVERNANCE.md` §2).
- `completion` — `NOT_STARTED` | `PARTIAL` | `COMPLETE` (agent-set).
- `verification` — `UNVERIFIED` | `VERIFIED` | `FAILED` (agent-set, needs evidence).
- `approval` — `NOT_REQUIRED` | `PENDING_USER_APPROVAL` | `APPROVED` | `REJECTED`
  (**user-set only**).

---

## 2. Evidence Record

```json
{
  "id": "EV-P02-001",
  "task": "PHASE-02-T01",
  "requirement": "REQ-P02-01",
  "command": "<exact command>",
  "expected": "<what success looks like>",
  "actual": "<verbatim captured output>",
  "result": "PASS",
  "timestamp": "2026-10-03T00:00:00Z",
  "file": "<relevant file or null>",
  "test": "<validator/test name>",
  "commit": "<sha or null>",
  "maturity": "VERIFIED"
}
```

`result` enum: `PASS` | `FAIL` | `SKIP` | `BLOCKED`

---

## 3. Decision Record

```json
{
  "id": "DEC-0001",
  "title": "Initialise Git locally without a remote",
  "decision": "<what was decided>",
  "reason": "<why>",
  "evidence": ["<evidence ids or file:line refs>"],
  "alternatives": [
    { "option": "<considered>", "rejected_because": "<why>" }
  ],
  "approval": {
    "required": true,
    "status": "PENDING_USER_APPROVAL",
    "approved_by": null,
    "approved_at": null
  },
  "supersedes": null,
  "date": "2026-10-03"
}
```

---

## 4. Handoff Record

```json
{
  "id": "HANDOFF-PHASE-02-01",
  "phase": "PHASE-02",
  "from": "<agent-id>",
  "to": "<agent-id or ANY>",
  "timestamp": "2026-10-03T00:00:00Z",
  "task_performed": "<what was being worked on>",
  "completed": ["<done>"],
  "not_completed": ["<explicitly not done>"],
  "files_changed": ["<path>"],
  "tests_executed": ["<command>"],
  "tests_passed": ["<id>"],
  "tests_failed": ["<id or none>"],
  "known_risks": ["<risk>"],
  "unresolved_questions": ["<question>"],
  "decisions_made": ["DEC-0001"],
  "next_recommended_action": "<action>",
  "user_approval_required": true,
  "git_commit": "<sha>"
}
```

All 12 fields from §9 of the brief are mandatory. `"not_completed"` and
`"unresolved_questions"` may be `[]` but must never be omitted.

---

## 5. Approval Record

```json
{
  "subject": "PHASE-02",
  "requested_by": "<agent-id>",
  "requested_at": "2026-10-03T00:00:00Z",
  "scope": "<what is being approved>",
  "evidence_summary": ["EV-P02-001"],
  "state": "PENDING_USER_APPROVAL",
  "decided_by": null,
  "decided_at": null,
  "decision_comment": null
}
```

`state` enum: `PENDING_USER_APPROVAL` | `APPROVED` | `REJECTED`

**Rule:** `decided_by` may only be set to a value identifying the **user**. An
agent must never populate it.

---

---

## 6. Requirement Contract (Phase 03)

Extends the Phase 02 record set. Traceability chain:
**Requirement → Task → Implementation → Verification → Evidence → Approval.**

```json
{
  "requirement_id": "REQ-P03-01",
  "title": "<short imperative title>",
  "description": "<what must be true, and why>",
  "source": "<origin: user | audit finding | decision | regulation>",
  "priority": "LOW | MEDIUM | HIGH | CRITICAL",
  "scope": "IN_SCOPE | OUT_OF_SCOPE",
  "acceptance_criteria": ["<observable outcome, verifiable by executing something>"],
  "dependencies": ["REQ-...", "TASK-..."],
  "implementation_status": "DECLARED | IMPLEMENTED",
  "implementation_refs": ["<file:line>"],
  "verification_status": "UNVERIFIED | VERIFIED",
  "verification_refs": ["VER-P03-001"],
  "approval_status": "NOT_REQUIRED | PENDING_USER_APPROVAL | APPROVED | REJECTED",
  "evidence": ["EV-P03-001"],
  "related_tasks": ["PHASE-03-T01"],
  "related_decisions": ["DEC-0003"]
}
```

**Field rules (enforced by `validate-control.sh`):**
- `requirement_id` must match `REQ-PNN-NN`.
- `acceptance_criteria` must be **non-empty** and each entry must be observable.
  Vague criteria (`good`, `fast`, `nice`, `robust`, `proper`) are **rejected** — `CASE A`.
- `implementation_status: IMPLEMENTED` requires ≥1 entry in `implementation_refs`.
- `verification_status: VERIFIED` requires ≥1 entry in `verification_refs`.
- `approval_status: APPROVED` requires an attributable user decision — never agent-set.

### Acceptance criteria quality (§7)

| BAD | GOOD |
|---|---|
| "Build a good homepage" | "Route renders HTTP 200; responsive at 320/768/1440; passes the defined a11y check" |
| "Improve performance" | "Lighthouse performance score >= 90 on the target route" |
| "Add tests" | "New branch covered by >=1 test that fails without the change" |

Rule: a criterion is acceptable if it names **what is observed**, **where**, and **how it is
checked**. Phase 03 does not invent project-specific criteria — it makes them mandatory.

---

## 7. Verification Contract (Phase 03)

```json
{
  "verification_id": "VER-P03-001",
  "requirement_id": "REQ-P03-01",
  "task_id": "PHASE-03-T01",
  "method": "AUTOMATED | AGENT | USER | EXTERNAL",
  "command_or_procedure": "<exact command or the manual procedure>",
  "expected_result": "<what success looks like>",
  "actual_result": "<verbatim observed output>",
  "status": "PASS | FAIL | SKIP | BLOCKED",
  "evidence_reference": "EV-P03-001",
  "verifier": "<agent or human identifier>",
  "timestamp": "2026-10-03T00:00:00Z"
}
```

**Field rules:**
- `method` ∈ the four verifier classes (`CONTROL-MODEL.md` §6).
- `method: AGENT` may **not** be the sole verification for `HIGH`/`CRITICAL` risk, nor for
  enforcement Level 3/4.
- `status: PASS` requires non-empty `actual_result` (never "should pass").
- `status: FAIL`/`BLOCKED` requires a stated reason.
- Verification is **append-only**; a changed outcome requires a new record with `supersedes`.

---

## 8. Agent Action Contract (Phase 03)

Representation for a *significant* action before it is performed. Not an agent runtime.

```json
{
  "action_id": "ACT-P03-001",
  "actor": "<agent or human identifier>",
  "phase": "PHASE-03",
  "task": "PHASE-03-T01",
  "intent": "<why this action is being taken>",
  "inputs": ["<file, parameter, or state consumed>"],
  "expected_output": "<observable result>",
  "action_class": "READ | ANALYZE | WRITE | EXECUTE | INSTALL | DELETE | DEPLOY | PUBLISH | DESTRUCTIVE",
  "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
  "assumption_classification": "SAFE_INFERENCE | MATERIAL_DECISION",
  "required_approval": "NONE | USER | BLOCKING",
  "validation_method": "<how the result will be checked>",
  "rollback_method": "<how to undo, or null>",
  "rollback_available": "yes | no | partial",
  "rollback_scope": "<what it restores>",
  "rollback_verified": true
}
```

**Field rules:**
- `action_class` ∈ the nine classes; `DESTRUCTIVE` is an overlay that wins.
- `risk_level` ∈ `LOW|MEDIUM|HIGH|CRITICAL`.
- `assumption_classification: MATERIAL_DECISION` **requires** `required_approval: USER` —
  otherwise `MISSING_USER_DECISION` (stop condition). Encodes the no-assumption rule.
---

## 9. Rollback Contract (Phase 03)

Referenced by the action contract; recorded per high-risk task.

```json
{
  "action_id": "ACT-P03-001",
  "rollback_available": "yes | no | partial",
  "rollback_method": "<concrete procedure>",
  "rollback_scope": "FILE | COMMIT | DATABASE | CONFIG | ENVIRONMENT | DATA",
  "rollback_verified": true,
  "verified_by": "<verifier id>",
  "verified_at": "2026-10-03T00:00:00Z"
}
```

Rule: `rollback_verified: false` on a `CRITICAL` action is a stop condition.

---

## 10. Handoff Extension (Phase 03)

`SCHEMA.md` §4 (Phase 02) is extended with these fields. Existing fields are unchanged.

```json
{
  "current_phase": "PHASE-03",
  "current_task": "PHASE-03-T01",
  "current_state": "<lifecycle stage>",
  "blockers": ["<stop-condition codes>"],
  "requirements": ["REQ-P03-01"],
  "implementation": ["<file:line refs>"],
  "verification": ["VER-P03-001"],
  "evidence": ["EV-P03-001"],
  "user_approval": "PENDING_USER_APPROVAL",
  "next_allowed_action": "<action class + description that IS permitted>",
  "forbidden_next_action": "<action class + description that is NOT permitted>"
}
```

**The two critical fields** (Phase 03 brief §20):

- `next_allowed_action` — what a receiving agent **may** do next.
- `forbidden_next_action` — what it **must not** do, even if it believes that would help.

These exist to stop a receiving agent from simply deciding what it wants to do next.

---

## 11. Validation (updated)

```bash
bash .sps/tools/validate-governance.sh          # Phase 02 governance rules
bash .sps/tools/validate-control.sh             # Phase 03 control rules + CASE A-F
bash .sps/tools/validate-control.sh --negative  # run the negative test suite only
```

Exit codes: `0` all valid · `1` validation failure · `2` tooling unavailable.
- `risk_level: CRITICAL` requires `rollback_available != "no"` and `rollback_verified: true`.

---

## 12. Capability Contract (Phase 04)

Registry: `.sps/capability/registry/PHASE-04-CAPABILITIES.json`.
`fact_class` applies the `FACT`/`EVIDENCE`/`INFERENCE`/`UNKNOWN` taxonomy
(`CAPABILITY-MODEL.md` s2) to every field.

Required fields (full shape and semantics: `.sps/capability/PROVENANCE.md` s4):

| Group | Fields |
|---|---|
| Identity | `capability_id` (`CAP-PNN-NNN`), `name`, `type`, `description`, `purpose`, `domain`, `serves_requirements`, `fact_class` |
| Source | `source`, `source_rank` (1-6), `official_url`, `repository_url`, `version`, `release_date` |
| Compatibility | `tech_compatibility`, `framework_compatibility`, `agent_compatibility`, `agent_specific_dependency` |
| Trust | `maintenance_status`, `licence`, `security_status`, `security_evidence`, `trust_level` |
| Quality | `evidence`, `quality_indicators`, `adoption_indicators`, `known_limitations`, `dependencies` |
| Install | `install_method`, `install_scope`, `global_installation_authorized_by`, `project_local_install_method`, `rollback_method`, `verification_method` |
| Freshness | `researched_at`, `research_id`, `version_checked`, `source_checked`, `last_verified`, `review_due`, `staleness` |
| Provenance | `provenance{requirement,discovery,research,evaluation,user_decision,installation,verification}` |
| Evaluation | `evaluation{evaluation_id,criteria{1..16},selection_reason,rejection_reason}` |
| State | `lifecycle_state`, `status`, `completion`, `approval_status`, `approval_decided_by` |
| MCP | `mcp{mcp_name,transport,source_url,maintainer,permissions,data_access,network_access,credentials_required,install_mechanism,project_local_feasible,requires_global_config,rollback,trust_level,trust_evidence}` |

**Enforced rules** (each maps 1:1 to a negative case A-N):
A provenance required | B `source` required | C `security_status: UNKNOWN` may never render
as safe | D `install_scope: GLOBAL` requires a **user** authorizer | E `lifecycle_state` >= `EVALUATED`
requires an evaluation | F selection requires `readiness: SUFFICIENT` research | G `APPROVED`
requires a user decider | H `VERIFIED` requires evidence | I `AGENT_NEUTRAL` requires
`agent_specific_dependency: null` | J `STALE` may not render as `CURRENT` | K `UNKNOWN` may not
render as known | L untrusted MCP blocks install | M replacing `ACTIVE` requires approval |
N project-local requirement may not entail a machine-global change.

---

## 13. Research Contract (Phase 04)

`.sps/research/PHASE-04-RESEARCH.json`.

| Field | Rule |
|---|---|
| `research_id` | `RSCH-PNN-NNN` |
| `subject`, `subject_type` | What was researched; `TECHNOLOGY` or `CAPABILITY` |
| `researched_at` | ISO-8601 UTC |
| `sources[]` | Each `{rank 1-6, type, url, accessed_at}` |
| `covered{}` | Ten required areas: official docs, version, compatibility, ecosystem, practices, security, tooling, MCP availability, testing, deployment - each `COVERED` or `UNKNOWN` |
| `conclusions[]` | Each `{claim, fact_class, source_rank}` |
| `uncertainties[]` | Explicitly `UNKNOWN` items |
| `readiness` | `SUFFICIENT` or `INSUFFICIENT` |
| `evidence[]` | Evidence IDs |

**Gate:** `readiness: SUFFICIENT` requires all ten `covered` fields `COVERED` **and** at
least one source of rank <= 4 (`CASE F`).

---

## 14. MCP Contract (Phase 04)

Registered as `type: "MCP"` plus the `mcp` block (semantics: `SECURITY.md` s5).
`requires_global_config: true` is a **material decision** (no-assumption rule);
`trust_level` `UNTRUSTED`/`UNKNOWN` blocks installation (`CASE L`);
**no MCP is installed during Phase 04**.

---

## 15. Project-Local Installation Contract (Phase 04)

`install_scope` defaults to `PROJECT_LOCAL`. `project_local_install_method`,
`rollback_method` and `verification_method` must all be non-empty.
`global_installation_authorized_by` must be empty unless a **user** authorised a global
install (`CASE D`, `CASE N`). Global installation is exceptional: explicit user request plus
the same security and approval gates.

---

## 16. Validation (Phase 04)

```bash
bash .sps/tools/validate-capability.sh             # structural + CASE A-N
bash .sps/tools/validate-capability.sh --negative  # negative suite only
```

Exit: `0` valid | `1` failure | `2` tooling unavailable.
