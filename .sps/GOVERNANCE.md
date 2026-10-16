# SPS Governance Rules

Normative rules for Phase 02 onward. Plain Markdown — tool- and agent-agnostic.

---

## 1. Maturity Levels (DECLARED / IMPLEMENTED / VERIFIED / USER_APPROVED)

Phase 01 finding **F-9** showed `lint-sps.sh` asserts *string presence in Markdown*:
documentation can claim a capability that no code implements. Governance must
therefore forbid using a single word to describe reality.

| Level | Code | Definition | Requires |
|---|---|---|---|
| 1 | `DECLARED` | Docs/tests *say* the system supports it | Nothing — a claim only |
| 2 | `IMPLEMENTED` | Code/scripts actually perform it | Code + line/file reference |
| 3 | `VERIFIED` | Executed evidence demonstrates it | Evidence record with real output |
| 4 | `USER_APPROVED` | The user explicitly accepted the result | Approval record naming the user |

**Rules:**
- A capability at `DECLARED` must never be described as working.
- `IMPLEMENTED` requires a code reference; if none exists, the level is `DECLARED`.
- `VERIFIED` requires an executed command + captured output. Never "should pass".
- Levels are **not** a linear race to 4. A change may stay `IMPLEMENTED` while
  functionally `DECLARED` if no test can prove it.
- `USER_APPROVED` is orthogonal to `VERIFIED`: code can be `VERIFIED` and still
  await user approval.

**Worked example from this repository:**

| Capability | Level | Why |
|---|---|---|
| Install script syncs skills to hosts | `IMPLEMENTED` | `install.sh:246-270` |
| Install works on a clean machine | `DECLARED` | Not executed in Phase 02 (§16 forbids) |
| CI runs lint + smoke | `IMPLEMENTED` | `.github/workflows/sps-ci.yml` |
| CI passes on GitHub | `DECLARED` | No CI run observed (no remote) |
| `sps-cms` auth works | `DECLARED` | Template code only, never executed |
| Project governance exists | `VERIFIED` | `evidence/PHASE-02-EVIDENCE.json` |

---

## 2. State Model

Applies to **phases** and **tasks** independently.

| State | Meaning | May transition to |
|---|---|---|
| `PLANNED` | Identified, not started | `IN_PROGRESS`, `BLOCKED` |
| `IN_PROGRESS` | Agent actively working | `AWAITING_USER_APPROVAL`, `VERIFIED`, `BLOCKED`, `FAILED` |
| `AWAITING_USER_APPROVAL` | Work done, user decision required | `APPROVED`, `REJECTED`, `IN_PROGRESS` |
| `APPROVED` | **User** accepted | `VERIFIED` |
| `REJECTED` | **User** declined | `PLANNED` (with changes) or terminal |
| `BLOCKED` | Cannot proceed; blocker recorded | `IN_PROGRESS`, `PLANNED` |
| `VERIFIED` | Evidence proves correctness | terminal (unless re-verified) |
| `FAILED` | Attempted and failed | `IN_PROGRESS` (retry), `BLOCKED` |

### The three-axis rule (§6 of the brief)

Three *independent* axes must never be merged:

| Axis | Question | Field | Who sets it |
|---|---|---|---|
| **Completion** | Was the work performed? | `completion` | Agent |
| **Verification** | Does evidence prove it works? | `verification` | Agent (with evidence) |
| **Approval** | Did the user accept it? | `approval` | **User only** |

Anti-pattern this prevents:

```text
TASK COMPLETED  !=  TASK VERIFIED  !=  USER APPROVED
     (done)          (proved)          (accepted)
```

An agent must never infer approval from completion, or verification from approval.

---

## 3. Task & Phase Identity (§7 of the brief)

Deterministic, traceable, not over-engineered.

| Pattern | Meaning | Example |
|---|---|---|
| `PHASE-NN` | A phase | `PHASE-02` |
| `PHASE-NN-TNN` | A task within a phase | `PHASE-02-T03` |
| `EV-PNN-NNN` | An evidence record | `EV-P02-007` |
| `DEC-NNNN` | A decision record | `DEC-0002` |
| `F-N` / `I-N` | Phase 01 finding / anomaly | `F-3`, `I-9` |
| `REQ-PNN-NN` | A requirement a task satisfies | `REQ-P02-01` |

**Traceability chain (mandatory):**

```
PHASE-NN --> PHASE-NN-TNN --> REQ-PNN-NN --> implementation (file:line)
                |                                     |
                |                                     v
                +-----------------------------> evidence (EV-PNN-NNN)
                                                      |
                                                      v
---

## 4. Evidence Rules (§10 of the brief)

Objective evidence only. Statements like "Looks good." or "Implemented successfully."
are **not** evidence and must not be recorded as such.

| Field | Meaning |
|---|---|
| `id` | Evidence ID (`EV-P02-NNN`) |
| `task` | Task ID this evidences |
| `command` | Exact command executed |
| `expected` | What success looks like |
| `actual` | Real observed output (verbatim, truncated if long) |
| `result` | `PASS` / `FAIL` / `SKIP` / `BLOCKED` |
| `timestamp` | ISO-8601 UTC |
| `file` | Relevant file (if applicable) |
| `test` | Relevant test/validator |
| `commit` | Related commit SHA |

**Additional rules:**
- `actual` must be real captured output, never reconstructed from memory.
- `SKIP` is legitimate and must state *why* (e.g. "requires network").
- Never write `PASS` for a command that was not executed.
- If a command cannot be run, record `BLOCKED` with the reason — do not guess.

---

## 5. Decision Records (§8 of the brief)

Prevents future agents from re-litigating settled architecture because they did not
know why a decision was made.

| Section | Content |
|---|---|
| **Decision** | What was decided |
| **Reason** | Why it was decided |
| **Evidence** | What evidence supports it |
| **Alternatives** | What else was considered and why it was rejected |
| **Approval** | Whether user approval was required/received, and by whom |

**Rule:** a future agent may revisit a decision only by creating a **new** decision
record that supersedes the old one — never by silently editing history.

---

## 6. Handoff Contract (§9 of the brief)

Agent A → Agent B must record, per §9:

1. Task performed · 2. Completed · 3. Not completed · 4. Files changed
5. Tests executed · 6. Tests passed · 7. Tests failed · 8. Known risks
9. Unresolved questions · 10. Decisions made · 11. Next recommended action
12. Whether user approval is required

**Rule:** a handoff must be sufficient for another agent to understand project
state **without hidden memory**. If Agent B would need to ask A a question already
answered in the handoff, the handoff is incomplete.

---

## 7. Secret Safety (§12 of the brief)

- `.gitignore` blocks `.env*`, `*.pem`, `*.key`, `id_rsa*`, `credentials/`, etc.
- `.env.example` / `.env.*.example` are deliberately **not** ignored — sanitised
  templates are legitimate documentation.
- **Never** record an actual secret value in any report, evidence record, decision
  record, or commit message. Reference the *location* only.
- Pre-commit scan is mandatory before any commit touching auth/crypto/template code.
- A discovered secret is **documented**, not silently patched or deleted, unless
  leaving it would risk committing it.

---

## 8. Scope Control (§18 of the brief)

Out-of-scope for Phase 02 (document, do **not** fix):

dynamic skill discovery · MCP discovery · skill installation · technology research ·
SEO · CMS · backend/frontend redesign · security remediation · performance ·
accessibility · CI/CD redesign · multi-agent orchestration implementation ·
automatic approval enforcement · architecture rewrite · mass refactoring

**Rule:** discovering an out-of-scope issue → record it in `.sps/audits/README.md`
known-issue register. Fixing it early violates scope control even if the fix looks
obviously correct.

---

## 9. Project-Local State Rule (§14 of the brief)

- The **repository** is the canonical location for project state.
- Future agents must not rely on hidden memory, global memory, default agent memory
  directories, or machine-specific planning directories for project-critical state.
- Global install paths (`~/.sps/`, `~/.claude/skills/`, …) are **distribution**
  targets, not project state.
- Migration of existing mechanisms is deferred to a later phase.
                                               approval (user)
```

Every meaningful change must be traceable end-to-end. A task with no evidence
record is `IMPLEMENTED` at best — never `VERIFIED`.

---