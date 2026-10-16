# Enforcement vs Instruction

**Phase:** `PHASE-03` — Enforcement & Control Foundation

> **This document does not claim SPS has achieved enforcement.** It states precisely what is
> enforced today, what is merely instructed, and what would close the gap.

---

## 1. The distinction

### Instruction

> "Please run tests before finishing."

Characteristics:
- The agent may comply, or not, with no consequence.
- Compliance is unverifiable after the fact.
- The failure mode is silent.
- A document can assert the rule while the system does nothing.

### Enforcement

> "The phase cannot transition to `VERIFIED` unless the required test evidence exists and
> passes."

Characteristics:
- A deterministic component evaluates a condition.
- The condition has an exit code.
- Non-compliance **prevents** a state transition.
- The check is reproducible by a third party.

---

## 2. Test for enforcement

A rule is **ENFORCED** only if all five are true:

1. A **machine-readable** representation of the condition exists.
2. A **deterministic validator** evaluates it (no LLM judgement in the gate itself).
3. It produces a **non-zero exit code** on violation.
4. Some **caller gates a state transition** on that exit code.
5. **Negative testing** has demonstrated the rule rejects a real violation.

**Criterion 5 is the one most often skipped.** A rule that has never been tested against a
deliberate violation is a *hypothesis*, not a control.

---

## 3. Honest status of each Phase 02/03 control

| Control | Instruction? | Enforcement? | Evidence |
|---|---|---|---|
| Evidence `PASS` must carry real output | — | **ENFORCED** (2) | `EV-P02-013` injects an empty `actual` → FAIL |
| Evidence task refs must match ID format | — | **ENFORCED** (2) | `EV-P02-013` injects a bad ref → FAIL |
| Approvals must be user-attributed | — | **ENFORCED** (2) | `EV-P02-017` agent attribution → FAIL |
| Decision records must be resolved | — | **ENFORCED** (2) | `EV-P02-018` pending decision → FAIL |
| Requirements need acceptance criteria | — | **ENFORCED** (2) | Phase 03 `CASE A` |
| Implemented task needs evidence | — | **ENFORCED** (2) | Phase 03 `CASE B` |
| Agent may not self-approve | — | **ENFORCED** (2) | Phase 03 `CASE E` |
| Evidence mutation detectable | — | **PARTIAL** (1–2) | Phase 03 `CASE F` |
| **Phase cannot advance without approval** | ✔ documented | **NOT enforced** | `DECLARED` — convention only |
| **Material decision must be asked** | ✔ documented | **NOT enforced** | `DECLARED` — policy only |
| **Stop conditions halt progression** | ✔ documented | **PARTIAL** (1) | Reported, not gating |
| Original SPS skill rules (Section DoD, plan gate, CMS coupling) | ✔ documented | **NOT enforced** | Phase 01 **F-1**; no validator |
| `lint-sps.sh` string-presence checks | ✔ documented | **MISLEADING** | Phase 01 **F-9** — greps text, not behaviour |

---

## 4. Why the gap exists

SPS's original design places its laws in Markdown read by an LLM. That design is portable,
tool-agnostic and cheap — and it is **structurally incapable of enforcement**, because nothing
executes those documents.

Phase 01 called this **F-1**. Phase 02 began closing it for governance state. Phase 03
extends it to requirements, verification, actions and risk.

**The gap is not a bug to be patched quickly.** It is an architectural consequence of
choosing Markdown laws. Converting the entire SPS rule set to machine-checkable form is a
multi-phase effort and is **not** attempted in Phase 03.

---

## 5. Migration path (not executed)

1. **Extract** each law into a rule ID with a structured precondition.
2. **Classify** its honest enforcement level (0–4).
3. **Implement** the smallest deterministic check.
4. **Negative-test** it against a deliberate violation.
5. Only then **raise** its declared level.

Steps 4 and 5 are what Phase 02/03 have done for governance rules — and they are what
separates a real control from an aspirational document.

---

## 6. Rule for future phases

> If a rule cannot be negative-tested in the phase that introduces it, it must be declared at
> **Level 0 (INFORMATIONAL)** and explicitly labelled as unenforced.

This prevents the recurring Phase 01 anti-pattern (**F-9**): documentation that asserts
capability which no code implements.