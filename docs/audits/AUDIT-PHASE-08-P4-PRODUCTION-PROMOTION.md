# AUDIT-PHASE-08 — P4 Production Capability Promotion & Registry Hardening

**Status:** `COMPLETE / VERIFIED / AWAITING_USER_APPROVAL`
**Roadmap phase:** P4 (audit phase 08; phases 01-07 exist)
**Date:** 2026-10-03
**Baseline:** `702650b` (P3 approval transition)

> No credential value appears in this report. No external verification was
> performed or is claimed.

---

## 1. Headline

**Zero of five capabilities reached production.** Every blocker is named by gate.
This is the honest outcome of applying the specified gate to the actual evidence.

## 2. The decisive finding

**The repository declares no licence.** `git ls-files` returns no `LICENSE`,
`LICENCE` or `COPYING`. An unlicensed repository is all-rights-reserved by
default; it is not permissive.

P3 recorded `KNOWN_PERMISSIVE` for all five capabilities on the assumption that
project-authored source implies a permissive licence. That assumption was
unverified. **P4 corrected it to `UNDECLARED`.**

Because the P4 specification states that an unknown licence MUST block production
promotion, gate D blocks every capability. This is the gate working as designed,
not a failure of the phase.

## 3. Gate results (computed, never asserted)

| Gate | 001 | 002 | 003 | 004 | 005 |
|---|---|---|---|---|---|
| A Identity | PASS | PASS | PASS | PASS | PASS |
| B Provenance | PASS | PASS | PASS | PASS | PASS |
| C Security | PASS | PASS | PASS | PASS | PASS |
| **D Licence** | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| E Maintenance | PASS | PASS | PASS | PASS | PASS |
| **F Verification** | PASS | PASS | PASS | PASS | **FAIL** |
| G Requirements | PASS | PASS | PASS | PASS | PASS |
| **H Approval** | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| I Scope | PASS | PASS | PASS | PASS | PASS |
| J Staleness | PASS | PASS | PASS | PASS | PASS |
| **K Conflicts** | PASS | PASS | PASS | PASS | **FAIL** |

Recommendations: 001-004 `REMAIN_CANDIDATE`; 005 `DEFER`.

## 4. Why CAP-P03-005 is deferred

The CLS thresholds (good <= 0.1, poor > 0.25) are genuinely verified from
SRC-017. But **a verified fact is not an implemented capability**. No executable
CLS measurement code exists anywhere under `sps2`, and the record's provenance
pointed at a Markdown research file, not code. Gate F correctly refuses.

No LCP or INP threshold was introduced. CONF-001 remains `UNRESOLVED`.

## 5. SEO constraint honoured

- Only the retrieved CLS claim is represented.
- No LCP thresholds, no INP thresholds, no generic SEO optimiser or skill.
- No ranking or Core Web Vitals claim beyond retrieved evidence.
- Gate K blocks the SEO candidate while CONF-001 is open.

## 6. Verification executed

Four governance capabilities ran executable checks and reported VERIFIED. Two
initially failed and were diagnosed as a **fixture defect** and a **`REPO` path
defect** (the path resolved one directory too high, so gate F could never find an
implementation). Both were fixed; neither was waived.

## 7. Determinism and forced choice

- 40 input permutations produced exactly **one** ranking fingerprint.
- The popularity fixture was rebuilt so the most popular candidate is deliberately
  the weakest on evidence; **it did not win**. The first fixture was vacuous.
- A forced choice moves to rank 1; a `VULNERABLE` candidate is refused.

## 8. Staleness

`STALE_AS_ACTIVE` rejected · `STALE_WITHOUT_REVIEW` rejected · a `STALE` record
carrying `review_due` is permissible. ACTIVE / STALE / REVIEW_REQUIRED /
INVALIDATED are all modelled.

## 9. No-emoji

73 files scanned, zero violations. A planted emoji was detected (POSCTRL-B). The
rule documentation and the checker's own regex are exempted by **explicit
auditable suffix**, not a blanket skip.

## 10. P3 incident boundary

`USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED` — unchanged. Checkpoint `a7767cf`
`PRESERVED_BY_USER_DECISION` — object still resolves. No history rewrite, reflog
expiration, garbage collection, object deletion or force-push.

### 10.1 Credential recurrence observed during P4

The repository-wide secret scan run inside `validate-p4.sh` found the
`INCIDENT-P3-001` credential **re-present** in `.claude/settings.json`, with
fingerprint `6ebcb3ea914cea56` — matching the recorded incident fingerprint
exactly. This is the same credential, not a new one.

This **empirically confirms** the residual risk recorded in
`INCIDENT-P3-001-CLOSURE-ASSESSMENT.md`: the harness rewrites this file, so
containment of the working tree is not durable.

P4 action taken: the single `ANTHROPIC_AUTH_TOKEN` key was removed again, all
other settings keys were retained, and the repository-wide scan returned clean.
Recorded as `EV-P4-019`.

**The incident was not reopened.** Classification remains
`USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED`. Revocation remains User-attested
only and was not independently verified. The file remains tracked with
non-attributed history, so this recurrence is expected and is a governance item
for the User rather than a P4 fix.

## 11. Legacy protection

`git diff c11da27` over legacy paths: **0 files**.

## 12. Validation

| Validator | Result |
|---|---|
| P4 | 53 checks passed, 0 failed, 22 negative cases rejected, 0 missed |
| P3 | 67 checks + 18 controls |
| P2 | 69 checks + 22 negatives |
| P1 | 73 checks + 25 negatives |
| governance / control / capability | 53 / 49+8 / 55+16 |
| lint | PASS |
| secret-safety | 9/9 |

## 13. Phase state

**P4: `APPROVED`** by the User on 2026-10-04, as a completed, verified phase,
including its existing bounded scope and its outcome of **zero production
promotions**.

The approval is explicitly bounded and does **not** authorise:

- promotion of any capability to production;
- any licence selection or declaration (the licence stays `UNRESOLVED`);
- P5, or the beginning of any P5 work;
- creating a remote or pushing anything.

Each approval is attributed to the User by name and date. `validate-p4.sh`
rejects any approval attributed to an agent, a model or a self-reference, and
carries a positive control (`POSCTRL-D`) proving that rejection is real.

**P5: `NOT_STARTED / NOT_APPROVED`** — no P5 artefact exists.

### 13.1 Licence state

`UNRESOLVED`, recorded as an explicit User decision in `DEC-0022`. No licence
was selected, added or inferred. Gate D continues to block every promotion.
An unlicensed repository is all-rights-reserved by default; that default was
not overridden.

### 13.2 Capability promotion state

`0 of 5 promoted`, unchanged by the approval. Four remain `REMAIN_CANDIDATE`
(blocked by gates D and H) and one remains `DEFER` (CAP-P03-005, additionally
blocked by gates F and K).

### 13.3 Discrepancy found during the approval transition

The P4 validator's negative-suite summary reused the global `NP`/`NF` counters
that positive controls also incremented. A failing positive control was
therefore reported as a missed negative case, and the inline cases N18-N20 were
counted as controls rather than negative cases. This made the reported totals
wrong in both directions while the underlying assertions were correct.

Fixed by giving the negative suite its own `NNP`/`NNF` counters. The suite now
reports **22 negative cases rejected, 0 missed, 3 controls enforced**, which
matches the 19 `gate_case` invocations plus the 3 inline cases.