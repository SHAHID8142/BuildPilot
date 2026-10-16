# SPS Enforcement Model

**Phase:** `PHASE-03` — Enforcement & Control Foundation
**Companion to:** `.sps/control/CONTROL-MODEL.md`

> This document defines **what enforcement means** and what is checked. It does not claim
> enforcement is complete. See `ENFORCEMENT-VS-INSTRUCTION.md` for the honest gap analysis.

---

## 1. Enforcement levels (§8)

Not every rule should be Level 4. The purpose is a **clear classification**, not maximal
severity.

| Level | Name | Mechanism | Failure outcome |
|---|---|---|---|
| **0** | `INFORMATIONAL` | Documented; agent informed | Nothing — a documented preference |
| **1** | `VALIDATION` | A validator inspects the result | Report only; progression continues |
| **2** | `BLOCKING` | Validator gates the transition | **Transition refused** |
| **3** | `APPROVAL_GATE` | Validation may pass; user approval needed | Holds at `AWAITING_USER_APPROVAL` |
| **4** | `HARD_GATE` | All conditions must hold | System cannot progress at all |

### Assignment rules

1. Level is assigned per **rule**, never per document.
2. A rule may not be raised above the strongest mechanism that actually exists.
   **This is why most SPS rules today are Level 0** — see the inventory below.
3. Raising a level requires evidence the mechanism is implemented *and* verified.
4. A Level 3–4 rule with no working gate is a **documentation defect**, not a control.

### Current enforcement inventory

| Control | Intended | Actual | Gap |
|---|---|---|---|
| Evidence must carry real captured output | 2 | **2** ✅ | — |
| Decision records must be user-attributed | 2 | **2** ✅ | — |
| Acceptance criteria required on requirements | 2 | **2** ✅ (Phase 03) | — |
| Phase transitions require approval | 3 | **2** (partial) | Convention, not machine-checked |
| No assumption on material decisions | 3 | **0** | Policy only; no gate exists |
| Stop conditions halt progression | 2 | **1** | Advisory in validator output only |

---

## 2. Stop conditions (§10)

A blocked condition must **stop** progression rather than let the agent continue by silently
assuming a solution.

| Code | Condition | Default level |
|---|---|---|
| `MISSING_REQUIREMENT` | Requirement absent or too vague to implement | 2 |
| `MISSING_USER_DECISION` | A material decision is unresolved | 3 |
| `FAILED_VALIDATION` | A validator rejected the result | 2 |
| `FAILED_TEST` | A test failed | 2 |
| `UNRESOLVED_SECURITY_ISSUE` | Known security issue not addressed | 4 |
| `CONFLICTING_REQUIREMENTS` | Two requirements contradict | 2 |
| `UNVERIFIED_IMPLEMENTATION` | Code exists but no evidence proves it | 2 |
| `PENDING_APPROVAL` | Approval required and not received | 3 |
| `MISSING_DEPENDENCY` | A prerequisite (incl. rollback plan) absent | 2 |
| `UNKNOWN_TECHNOLOGY` | Technology not understood well enough to use | 3 |

**Rules:**
- A stop condition forces the lifecycle stage to `BLOCKED` (or `AWAITING_USER_APPROVAL` for
  approval-type conditions).
- **Silently assuming a solution to clear a stop condition is itself a violation**, recorded
  as `MISSING_USER_DECISION` where the decision is material.
- Stop conditions are *reported by* validators; they are not self-certified by agents.

---

## 3. No-assumption rule (§9)

> If required information is missing and the missing information materially affects
> architecture, implementation, security, cost, UX, data model, deployment, or acceptance
> criteria, the agent must ask the user rather than inventing an assumption.

| Class | Test | Action |
|---|---|---|
| `SAFE_INFERENCE` | Reversible, local, low blast radius, and changes none of architecture/security/cost/UX/data/deployment/acceptance | Proceed; record the inference |
| `MATERIAL_DECISION` | Could change any of those seven areas | **Ask the user.** Do not assume. |

**Rule:** when classification is genuinely unclear, treat it as `MATERIAL_DECISION`.
Asking costs a turn; assuming wrongly can cost an architecture.

**Policy only in Phase 03.** No conversational planner is implemented. The
`assumption_classification` field exists in the action contract (`SCHEMA.md` §8) so future
phases can enforce this.
---

## 4. Phase gate (§11)

A phase **must not** transition automatically to the next phase.

| # | Question | If NO |
|---|---|---|
| 1 | All required tasks complete? | `BLOCKED` |
| 2 | All required verification complete? | `UNVERIFIED_IMPLEMENTATION` → `BLOCKED` |
| 3 | Known blocking issues resolved? | `BLOCKED` |
| 4 | Evidence recorded for all claims? | `UNVERIFIED_IMPLEMENTATION` |
| 5 | Is user approval required? | if not required, gate may pass |
| 6 | Has the user explicitly approved? | **`AWAITING_USER_APPROVAL`** |

**Rules:**
- If approval is required but missing, `AWAITING_USER_APPROVAL` **must** remain the state.
- Approval of one phase **never** carries forward to the next. Each gate is independent.
- A phase that is `VERIFIED` but not `APPROVED` may not advance.

### Precedent: Phase 02 → Phase 03

This gate was applied for real. When the Phase 03 brief was first received, the repository
state recorded `PHASE-02 → PENDING_USER_APPROVAL` and `PHASE-03 → NOT_APPROVED`. Work was
**refused** until the user issued an explicit approval. Phase 03 began only after a new
explicit instruction, consistent with this gate.

---

## 5. Explicit user approval (§12)

```text
agent believes the user approved   !=   the user explicitly approved
```

### Rules

1. Only an **explicit, attributable** user decision satisfies an approval gate.
2. The agent may never populate `decided_by` / `approved_by` itself.
3. An approval must record: subject, status, decider, date, basis.
4. **Natural-language guessing is prohibited.** "looks good", "okay", "fine", "continue",
   "go ahead" do **not** constitute approval unless a future approval system explicitly
   defines how they are parsed. Phase 03 defines no such parsing.

### Current implementation status

| Property | Status |
|---|---|
| Data model exists | `SCHEMA.md` §5 — **IMPLEMENTED** |
| Agent cannot self-approve | `validate-governance.sh` §6 — **IMPLEMENTED + VERIFIED** (`EV-P02-017`) |
| Natural-language approval parsing | **MISSING** — deliberately not implemented |
| Machine gate blocking progression | **DECLARED** — documented, not enforced |

---

## 6. Immutable evidence principle (§16)

Extends the Phase 02 evidence model; does not replace it.

> An agent must not be able to (1) fail a test, (2) modify the evidence, (3) make the failure
> disappear, (4) report success — without leaving traceable history.

### Rules

1. Evidence records are **append-only**. Existing records are never edited to change a result.
2. A superseding record is added with `supersedes: <id>`; the original remains readable.
3. Git history is the tamper-evidence layer: an altered evidence file is visible in
   `git log` / `git diff`.
4. `validate-control.sh` enforces structural append-only: unique record IDs, required
   `result`, and non-empty verbatim `actual` for every `PASS`.

**Honest limitation:** a determined agent with write access can rewrite a file before it is
committed. True immutability requires signed or externally-anchored evidence, which is
**deferred** — see Known Limitations in the Phase 03 report. Git provides *detection*, not
prevention.