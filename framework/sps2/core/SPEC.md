# SPS 2.0 — Core Specification

Agent-neutral. This file must never reference a specific coding agent.
Agent-specific behaviour lives behind `core/adapters/`.

---

## 1. The three-axis rule

Three truths are independent and must never be collapsed:

```text
IMPLEMENTED  !=  VERIFIED  !=  APPROVED
```

| Axis | Question | Who sets | Requires |
|---|---|---|---|
| Implementation | Does the code exist? | Agent | File/line references |
| Verification | Does evidence prove it works? | Agent | Executed command + verbatim output |
| Approval | Did the **user** accept it? | **User only** | Attributable user decision |

Additional rule: **instruction is not approval.** "Do it" is not "approve the previous
phase" unless a phase gate explicitly defines that transition.

## 2. Lifecycle

```
DISCOVERY -> REQUIREMENTS -> PLANNING -> READY_FOR_IMPLEMENTATION
  -> IMPLEMENTATION -> VERIFICATION -> AWAITING_USER_APPROVAL
  -> APPROVED -> DELIVERED
```

`BLOCKED` is reachable from any stage. `REJECTED` may return to an earlier stage.
`DELIVERED` is reachable **only** via `APPROVED`.

## 3. Enforcement levels

| Level | Name | Mechanism | Failure outcome |
|---|---|---|---|
| 0 | INFORMATIONAL | Documented only | Nothing |
| 1 | VALIDATION | Validator inspects | Reported |
| 2 | BLOCKING | Validator gates the transition | Transition refused |
| 3 | APPROVAL_GATE | Validation may pass; user approval needed | Holds at `AWAITING_USER_APPROVAL` |
| 4 | HARD_GATE | All conditions must hold | Cannot progress |

A rule may not be declared above the strongest mechanism that actually exists.
A Level 3-4 rule with no working gate is a **documentation defect**.

## 4. Stop conditions

`MISSING_REQUIREMENT` · `MISSING_USER_DECISION` · `FAILED_VALIDATION` · `FAILED_TEST` ·
`UNRESOLVED_SECURITY_ISSUE` · `CONFLICTING_REQUIREMENTS` · `UNVERIFIED_IMPLEMENTATION` ·
`PENDING_APPROVAL` · `MISSING_DEPENDENCY` · `UNKNOWN_TECHNOLOGY`

A blocked condition stops progression. **Silently assuming a resolution is itself a
violation.**

## 5. Portability contract

The core must pass its full test suite with **every adapter deleted**. An agent that has
never seen SPS 2.0 must be able to determine phase, task, next allowed action and
forbidden actions from repository state alone.

## 6. What the core must never do

- Reference or branch on a specific agent.
- Import an agent SDK or proprietary memory mechanism.
- Write to a machine-global location.
- Treat a document as proof of behaviour.
- Infer approval.