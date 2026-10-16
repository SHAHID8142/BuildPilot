# SPS Control Model

**Phase:** `PHASE-03` — Enforcement & Control Foundation
**Status:** `AWAITING_USER_APPROVAL`
**Depends on:** `.sps/GOVERNANCE.md` (Phase 02) — this document **extends** it, it does not replace it.

> **Relationship to Phase 02.** Phase 02 defined a *status* model (8 states) and a *maturity*
> ladder. Phase 03 adds a *lifecycle* (11 ordered stages) plus enforcement semantics. These
> are complementary, **not competing**: the lifecycle says **where** a unit is in its journey;
> the status model says **what condition** it is in. A mapping is given in §3.

---

## 1. The central problem

Phase 01 finding **F-1** (*determinism inversion*): SPS is deterministic about installing its
own files and non-deterministic about everything it governs. Every "hard law" is Markdown.
Nothing can *reject* non-compliant output.

Phase 03 does **not** claim to solve this. It establishes the vocabulary and checkable
contracts so a later phase can enforce.

---

## 2. Four separate truths (§5)

These are the spine of the model. Collapsing any two is the primary failure mode this system
exists to prevent.

| Truth | Code | Means | Proves correctness? | Who sets |
|---|---|---|---|---|
| 1 | `DECLARED` | The requirement exists in documentation | **No** | Agent |
| 2 | `IMPLEMENTED` | Code exists intended to satisfy it | **No** | Agent |
| 3 | `VERIFIED` | Executed evidence demonstrates it | **Yes** | Agent w/ evidence |
| 4 | `USER_APPROVED` | The user explicitly accepted the result | n/a — a decision, not proof | **User only** |

### Non-collapse rules

```text
DECLARED  != IMPLEMENTED  != VERIFIED  != USER_APPROVED
(documented)  (code exists)  (proved)  (accepted)
```

1. A `DECLARED` requirement must never be described as working.
2. `IMPLEMENTED` requires a file/line reference. No reference ⇒ it is `DECLARED`.
3. `VERIFIED` requires an executed command and its **verbatim** output. "Should pass" is not
   evidence.
4. `VERIFIED` **never** implies `USER_APPROVED`.
5. `USER_APPROVED` requires an attributable user decision record. An agent may never set it.

### Worked example (governance-internal, not project-specific)

| Requirement | DECLARED | IMPLEMENTED | VERIFIED | USER_APPROVED |
|---|---|---|---|---|
| A passing test must have non-empty captured output | `GOVERNANCE.md` §4 | `validate-governance.sh` `pass-has-output` | `EV-P02-013` (injected empty output → FAIL) | Pending |
| Commits must be attributable to a real identity | `DEC-0002` | `.git/config` | `EV-P02-020` | `APPROVED` 2026-10-03 |

The first row is `VERIFIED` but **not approved**; the second is approved. Neither implies the
other.

---

## 3. Lifecycle (§4) and mapping to Phase 02 states

```
DISCOVERY -> REQUIREMENTS -> PLANNING -> READY_FOR_IMPLEMENTATION
                                                |
                                                v
                                       IMPLEMENTATION
                                                |
                                                v
                                         VERIFICATION
                                                |
                                                v
                                AWAITING_USER_APPROVAL
                                   |              |
                                   v              v
                               APPROVED      REJECTED
                                   |
                                   v
                               DELIVERED

Any stage may enter BLOCKED. REJECTED may return to an earlier stage.
```

| Lifecycle stage | Phase 02 status while in it | Enforcement level |
|---|---|---|
| `DISCOVERY` | `IN_PROGRESS` | 1 — VALIDATION |
| `REQUIREMENTS` | `IN_PROGRESS` | 2 — BLOCKING (criteria required) |
| `PLANNING` | `IN_PROGRESS` | 2 — BLOCKING |
| `READY_FOR_IMPLEMENTATION` | `IN_PROGRESS` | 2 — BLOCKING |
---

## 4. Tool action classification (§14)

What kind of action is being attempted? Portable across any agent.

| Class | Definition | Examples |
|---|---|---|
| `READ` | Observation, no state change | cat, grep, `git status`, `git log` |
| `ANALYZE` | Reasoning over existing state | static analysis, design review |
| `WRITE` | Creates/modifies tracked files | editing source or docs |
| `EXECUTE` | Runs project code | tests, build, linter |
| `INSTALL` | Adds software to the environment | npm/npx, skills, MCPs, plugins |
| `DELETE` | Removes files or data | `rm`, dropping a table |
| `DEPLOY` | Releases the application | CI/CD release step |
| `PUBLISH` | Makes content externally visible | push, npm publish |
| `DESTRUCTIVE` | Irreversible or high-impact | `reset --hard`, `rm -rf ~`, history rewrite |

`DESTRUCTIVE` is an **overlay**, not a parallel class: an action may be both `EXECUTE` and
`DESTRUCTIVE`. Overlays always win.

---

## 5. Risk model (§15)

Deliberately coarse. Over-engineering risk scoring now would be premature.

| Level | Definition | Required verification | Required approval | Automation |
|---|---|---|---|---|
| `LOW` | Local, reversible, no external effect | `AGENT` or automated | No | Allowed |
| `MEDIUM` | Touches project behaviour or many files | Automated preferred | Recommended | Allowed |
| `HIGH` | Affects security, data, or deployment | Automated **+** independent reviewer | **Required** | Approval-gated |
| `CRITICAL` | Irreversible, external, or global | Automated **+** independent reviewer **+** rollback plan | **Required** | **Blocked without approval** |

**Rules:**
- Risk may only *raise* required verification and approval. It may never lower them.
- Risk may never substitute for missing verification.
- `CRITICAL` requires `rollback_verified` (see §7).

---

## 6. Verification independence (§18)

> The agent that performs an implementation must not automatically be sufficient proof that
> the implementation is correct.

| Verifier | Meaning | Independent of implementer? |
|---|---|---|
| `AUTOMATED` | Deterministic script / CI | **Yes** |
| `EXTERNAL` | Third party / separate system | **Yes** |
| `USER` | The user | **Yes** |
| `AGENT` | The implementing agent's own judgement | **No** |

**Rules:**
- `AGENT` verification may **never** be the sole verifier for `HIGH` or `CRITICAL` risk.
- `AGENT` verification may never satisfy a `LEVEL 3` or `LEVEL 4` requirement alone.
- Self-assessment ("I reviewed it, it looks right") is `AGENT` verification and inherits that
  weakness explicitly.

---

## 7. Rollback contract (§19)

Foundation only — no automated rollback infrastructure in Phase 03.

Every `HIGH`/`CRITICAL` task must record:

| Field | Meaning |
|---|---|
| `rollback_available` | `yes` / `no` / `partial` |
| `rollback_method` | The concrete procedure |
| `rollback_scope` | What it restores (file, commit, database, config…) |
| `rollback_verified` | Whether the rollback has itself been tested |

**Rule:** `rollback_verified: false` on a `CRITICAL` action is a stop condition.

---

## 8. Contracts

Machine-readable contracts live in `.sps/SCHEMA.md` — **extended, not duplicated**:

| Contract | Where |
|---|---|
| Task | `SCHEMA.md` §1 (Phase 02) |
| Evidence | `SCHEMA.md` §2 (Phase 02) |
| Decision | `SCHEMA.md` §3 (Phase 02) |
| Handoff | `SCHEMA.md` §4 (Phase 02), extended §5 (Phase 03) |
| Approval | `SCHEMA.md` §5 (Phase 02) |
| **Requirement** | `SCHEMA.md` §6 (Phase 03) |
| **Verification** | `SCHEMA.md` §7 (Phase 03) |
| **Agent action** | `SCHEMA.md` §8 (Phase 03) |
| **Rollback** | `SCHEMA.md` §9 (Phase 03) |

**Traceability chain** (`SCHEMA.md` §6): Requirement → Task → Implementation → Verification →
Evidence → Approval. A break anywhere invalidates the chain.
| `IMPLEMENTATION` | `IN_PROGRESS` | 1 — VALIDATION |
| `VERIFICATION` | `IN_PROGRESS` | 1 — VALIDATION |
| `AWAITING_USER_APPROVAL` | `AWAITING_USER_APPROVAL` | 3 — APPROVAL GATE |
| `APPROVED` | `APPROVED` | 3 — APPROVAL GATE |
| `REJECTED` | `REJECTED` | 2 — BLOCKING |
| `BLOCKED` | `BLOCKED` | 2 — BLOCKING |
| `DELIVERED` | `VERIFIED` | 4 — HARD GATE |
| — | `FAILED` | 2 — BLOCKING |

**Rules:**
- Lifecycle is **ordered and forward-only**, except `REJECTED` may return to an earlier stage.
- A stage may only be entered when its entry condition is satisfied (see `ENFORCEMENT.md`).
- `DELIVERED` is reachable **only** via `APPROVED`, never directly from `VERIFICATION`.