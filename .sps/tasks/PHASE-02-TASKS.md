# PHASE-02 Task Register

**Phase:** `PHASE-02` — Governance, Git & Evidence Foundation
**Status:** `APPROVED` (implementation `COMPLETE`, verification `VERIFIED`)
**Approval:** **`APPROVED` by User, 2026-10-03** — explicit user approval, not inferred
**Contract:** `.sps/SCHEMA.md` §1 · **Rules:** `.sps/GOVERNANCE.md`

> Reminder: `completion`, `verification` and `approval` are independent axes.
> This phase is all three — but they were established separately, in that order.

---

## Task Summary

| ID | Title | Status | Completion | Verification | Approval |
|---|---|---|---|---|---|
| `PHASE-02-T01` | Verify Git state & create baseline | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T02` | Repo-local Git identity (no global change) | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T03` | Hardened `.gitignore` (secret-safe) | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T04` | Governance state model + maturity levels | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T05` | Task/phase identity + traceability model | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T06` | Decision records (DEC-0001, DEC-0002) | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T07` | Agent handoff contract | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T08` | Evidence records + validation runs | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T09` | Governance validator (executable) | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T10` | Known-issue register for out-of-scope findings | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |
| `PHASE-02-T11` | Record user approval + resolve DEC-0001/0002 | `VERIFIED` | `COMPLETE` | `VERIFIED` | `APPROVED` |

> **Approval column updated 2026-10-03.** The user explicitly approved `PHASE-02` and
> resolved both pending decisions. See `.sps/STATE.md` → Approval Record.

---

## T01 — Verify Git state & create baseline

- **Requirement:** `REQ-P02-01` · **Decisions:** `DEC-0001`
- **Evidence:** `EV-P02-001`, `EV-P02-002`, `EV-P02-008`
- **What was done:** Verified no `.git` existed here or in any parent directory (not a
  worktree, not nested). Initialised with `git init --initial-branch=main`. Created the
  pre-remediation baseline commit `10ab67a` capturing 153 paths.
- **Not done:** No history was rewritten, reset, or force-pushed (there was none).

## T02 — Repo-local Git identity

- **Requirement:** `REQ-P02-02` · **Evidence:** `EV-P02-003`
- **What was done:** Set `user.name` / `user.email` with `git config --local` only.
- **Why it matters:** §16 forbids changing machine-global state. The global identity was
  confirmed still unset afterwards.

## T03 — Hardened `.gitignore`

- **Requirement:** `REQ-P02-03` · **Evidence:** `EV-P02-004` – `EV-P02-007`
- **What was done:** Reviewed 8 categories individually, then added secret, build-output,
  dependency-cache, coverage, repo-temp, OS, IDE and agent-cache rules.
- **Regression guard:** 11 real source paths verified still tracked; `.env.example`
  deliberately un-ignored because sanitised templates are legitimate documentation.
- **Not done:** The repo's 5 pre-existing rules were preserved, not replaced.

## T04 — Governance state model

- **Requirement:** `REQ-P02-04` · **Evidence:** `EV-P02-012`
- **What was done:** Defined the 8-state machine, the 3-axis rule, and the
  `DECLARED → IMPLEMENTED → VERIFIED → USER_APPROVED` maturity ladder in
  `.sps/GOVERNANCE.md`.
- **Why:** Directly mitigates Phase 01 **F-9** (documentation asserting capability).

## T05 — Identity & traceability

- **Requirement:** `REQ-P02-05` · **Evidence:** `EV-P02-012`
- **What was done:** Defined `PHASE-NN`, `PHASE-NN-TNN`, `EV-PNN-NNN`, `DEC-NNNN`,
  `REQ-PNN-NN` and the mandatory chain phase → task → requirement → implementation →
  evidence → approval.

## T06 — Decision records

- **Requirement:** `REQ-P02-06` · **Evidence:** `EV-P02-012`
- **What was done:** Created `DEC-0001` (git init / no remote) and `DEC-0002`
  (repo-local identity). Both record alternatives and approval state.

## T07 — Handoff contract

- **Requirement:** `REQ-P02-07` · **Evidence:** `EV-P02-012`
- **What was done:** Created `.sps/handoff/HANDOFF-CURRENT.md` covering all 12 fields
  required by §9, plus the JSON contract in `SCHEMA.md` §4.

## T08 — Evidence records

- **Requirement:** `REQ-P02-08` · **Evidence:** `EV-P02-009` – `EV-P02-011`
- **What was done:** Recorded 12 evidence entries with real captured output.
- **Honesty note:** `EV-P02-011` records `SKIP`, not `PASS`, for `smoke-sps.sh` —
  it invokes the real installer and was forbidden by §16.

## T09 — Governance validator

- **Requirement:** `REQ-P02-09` · **Evidence:** `EV-P02-012`
- **What was done:** Created `.sps/tools/validate-governance.sh` — read-only, no network,
  no installs, no machine-global writes. Makes governance checkable rather than merely
  documented.

## T10 — Known-issue register

- **Requirement:** `REQ-P02-10` · **Evidence:** `EV-P02-012`
- **What was done:** Registered 5 Phase 01 discrepancies and 5 out-of-scope observations in
  `.sps/audits/README.md` so later phases inherit known issues rather than rediscovering them.

## T11 — Record user approval and resolve pending decisions

- **Requirement:** `REQ-P02-11` · **Evidence:** `EV-P02-016` – `EV-P02-019`
- **Status:** `VERIFIED` · **Approval:** `APPROVED` (User, 2026-10-03)
- **What was done:** Recorded the user's explicit `PHASE-02` approval as genuine user
  approval (never inferred), and resolved both pending decisions:
  - `DEC-0001` → `APPROVED` / `KEEP_LOCAL_ONLY` (no remote configured)
  - `DEC-0002` → `APPROVED` / `DEFER_IDENTITY_UPDATE` (placeholder retained; replace before
    external publication — a standing obligation now tracked in `STATE.md` and `DEC-0002`)
- **Validator redesign required:** the Phase 02 approval check previously failed if *any*
  approval field was populated, which made recording a real approval impossible. Section 6 was
  redesigned to validate **user attribution** instead — strictly stronger, because it now also
  rejects agent-attributed approvals and per-record attribution gaps.
- **Bug found and fixed during this task:** the redesigned check originally used a
  directory-wide grep, so `DEC-0002`'s valid attribution masked `DEC-0001`'s missing one.
  Detected by negative test `EV-P02-017` and fixed to validate each record individually.
- **Not done:** `PHASE-03` was **not** started. It remains `NOT_STARTED` / `NOT_APPROVED`.