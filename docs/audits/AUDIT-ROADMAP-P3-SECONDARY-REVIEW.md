# AUDIT-ROADMAP-P3 — Secondary Engineering Review

Review date: 2026-10-04
Reviewer: secondary engineering/review agent (**not** a User; this review is
**not** an approval)
Branch: `review/roadmap-p3-secondary-review`
Reviewed HEAD: `df2a715091c152462ead038541885016fdfbc6d8`
(`feat(roadmap-p3): deliver the bounded Agent Interoperability scope under
D-P3-F`), which is `main` at the time of review.
Subject: the delivered **Roadmap P3 — Agent Interoperability** scope under
`D-P3-F`.
Status: **REVIEW ONLY. Roadmap P3 is NOT marked complete and NOT approved.
User approval of the delivered state remains authoritative and PENDING.**

---

## 0. Scope and restraint

This review was performed only within the explicitly authorised Roadmap P3
scope (`D-P3-F`): two declarative adapters (`D-P3-A..C`), the portability
conformance test (`D-P3-D/E`), the required P3 governance/evidence records, and
the two guard corrections (`D-P3-G`). Within that scope this review:

- ran the full existing validation suite **sequentially**, twice (before and
  after the review changes) and reports the results verbatim;
- inspected the P3 artefacts against the recorded `D-P3-A..G` decisions;
- fixed three in-scope defects (section 4.1) and documented three further
  findings it deliberately did **not** change (section 4.2).

This review did **not**: push; modify `main`; install, activate or promote any
capability; modify any legacy file; modify `.sps/` global state; resolve
`CONF-001`; start P7; create runtime activation; or make any governance decision
on behalf of the User. It commits only to its own branch. All review changes are
confined to the P3 surface (`sps2/tools/`, `sps2/evidence/`) and are revertible
in one commit.

---

## 1. What was reviewed

| Artefact | Path |
|---|---|
| Decisions | `sps2/decisions/ROADMAP-P3-DECISIONS.json` (`D-P3-A..G`) |
| Registry | `sps2/core/adapters/registry.json` |
| Adapters | `sps2/core/adapters/{codex,opencode,generic}/adapter.json` |
| Contract | `sps2/core/adapters/contract.schema.json` |
| Surface docs | `sps2/core/adapters/README.md` |
| Conformance test | `sps2/tools/test-portability.py` |
| Resume checklist | `sps2/RESUME.md` |
| Evidence | `sps2/evidence/ROADMAP-P3-EVIDENCE.json` |
| Reconciliation | `sps2/decisions/ROADMAP-EXECUTION-RECONCILIATION.json` |
| Guard corrections | `sps2/tools/validate-p7-readiness.py` (section 3), `sps2/tests/test_p5.py` (`TestAgentNeutrality`), `sps2/tools/validate-p5.py` (section 2), `sps2/tools/test-p7-readiness-mutation.sh` |
| Machinery reused | `sps2/core/adapter_registry.py`, `sps2/governance/attribution.py`, `sps2/tools/check_sps2.py`, `sps2/tools/validate-sps2.sh` |

---

## 2. Independent verification

### 2.1 Full suite, run sequentially

Run once on the reviewed HEAD and again after the review changes; the results
are byte-identical, confirming the review changes introduced no regression.

| Suite | Result (both runs) |
|---|---|
| `validate-sps2.sh` | 72 passed, 0 failed, 25 negative cases |
| `validate-p2.sh` | 69 passed, 0 failed, 22 negative cases |
| `validate-p3.sh` | 67 passed, 0 failed, 18 negative/positive controls |
| `validate-p4.sh` | 59 passed, 0 failed, 22 negative cases, 7 controls |
| `validate-p5.py` | 46 passed, 0 failed, 18 negative cases, 1 control |
| `validate-p6.py` | 65 passed, 0 failed, 24 negative cases, 1 control |
| `validate-p7-readiness.py` | 30 passed, 0 failed, 7 negative cases |
| `sps2/tests/test_p5.py` | 40 tests, OK |
| `test-snapshot-integrity.sh` | 9 caught, 0 missed |
| `test-phase-boundary.sh` | 11 caught, 0 missed |
| `test-p7-readiness-mutation.sh` | 22 caught, 0 missed (readiness) + 11 caught, 0 missed (phase validators) |
| `test-secret-safety.sh` | 9 checks, 0 failed |
| `.sps` governance | 54 passed, 0 failed |
| `test-history-credential-check.py` | all 4 scenarios behaved as required |
| `check_emoji.py sps2` | scanned=124, violations=0 |
| `test-portability.py` | 39 checks passed, 0 failed, 4 controls enforced |

Every count matches the recorded evidence in
`sps2/evidence/ROADMAP-P3-EVIDENCE.json` (`EV-RP3-001..006`) exactly. The
recorded delivery is reproducible.

### 2.2 Invariants re-confirmed

- Production capability registry `sha256
  5f95f62b03851748f95ac501221597f95243aae80f69cde2a8aea9105537af56` — unchanged.
- Legacy diff over `skills/ scripts/ plugins/ .github/ templates/ README.md
  CHANGELOG.md CATALOG.md install.* uninstall.* get-sps.*` — 0.
- Checkpoint `a7767cf` present; `.sps/` unmodified by the P3 commit.
- No `AGENTS.md` or other agent-convention file anywhere outside the adapter
  surface (`D-P3-C` honoured).
- Adapter surface fully tracked; working tree clean; no stray files.
- `CAP-P03-005` still `DEFERRED / NOT_PROMOTED`; `CONF-001` still `UNRESOLVED`;
  no LCP/INP value introduced; nothing installed, activated, promoted or pushed.

### 2.3 Isolation of the zero-adapter exercise

`sps2/tools/test-portability.py` section 3 copies the repository to a temp
directory and runs the sps2-scoped suites there. Every suite in the exercise
derives its root from `__file__` / `BASH_SOURCE`, so no suite can reach back into
the live tree. The live adapter surface is hash-compared before and after the
exercise and was unchanged. The isolation claim holds.

---

## 3. Decision-vs-implementation reconciliation (`D-P3-A..G`)

| Decision | Requirement | Implementation | Verdict |
|---|---|---|---|
| `D-P3-A` | Exactly two low-risk adapters: Codex, OpenCode | registry holds `codex` + `opencode` (plus the retained `generic`) | CONFORMS |
| `D-P3-B` | `VERIFIED` needs a recorded exercise; `EXPERIMENTAL` acceptable while `generic` fallback stands; `DECLARED` alone insufficient | `codex`/`opencode` = `EXPERIMENTAL`; `generic` = `DECLARED` and present; no `VERIFIED` claimed | CONFORMS |
| `D-P3-C` | Declarative-only under `core/adapters/<id>/`; no agent-convention files outside the surface | one `adapter.json` per adapter; no file created outside the surface | CONFORMS |
| `D-P3-D` | "Delete all" = per-agent entries/dirs; contract+registry survive; empty `[]` registry valid and accepted by the test | section 3 deletes every dir and non-core-owned file, empties the registry to `[]`, and asserts the empty registry validates | CONFORMS |
| `D-P3-E` | Fresh-agent resume targets the whole repository, mechanically | `sps2/RESUME.md` + section 4 mechanical execution (sources resolve; four answers present; decisions User-attributed) | CONFORMS |
| `D-P3-F` | Bounded scope; explicit forbidden list | delivered items stay inside the four authorised items; no forbidden item was done (section 2.2) | CONFORMS |
| `D-P3-G` | Exactly two guard corrections, at the invariant level, controls kept non-vacuous | both corrections present; **but** the second correction's control in `validate-p5.py` was vacuous until fixed here (finding F3) | CONFORMS after F3 |

No decision was contradicted by the implementation. One stated property of
`D-P3-G` ("controls keep the check non-vacuous") was only partially true at
delivery and is made fully true by F3.

---

## 4. Findings

### 4.1 Defects fixed within the authorised P3 scope

**F1 — Vacuous control `C4` in the portability conformance test (P3 deliverable).**
`sps2/tools/test-portability.py` section 4 built its control from a hardcoded
absent path (`"no/such/resume-source.md"`), so the `detected` list could never be
empty and the control could never fail: it did not exercise the missing-source
predicate at all. Fixed: the control now runs the *same* existence predicate
over the real `SOURCE:` list plus exactly one injected missing source, and
requires exactly that entry to be detected. Non-vacuity demonstrated — with the
injection the predicate returns the injected entry; without it, it returns `[]`
and the control would fire.

**F2 — Duplicate mutation labels `M15/M16/M17` (P3-introduced traceability defect).**
`sps2/tools/test-p7-readiness-mutation.sh` labelled the three new roadmap-P3
completion mutations `M15/M16/M17`, but those labels were already used by the
P7 decision mutations later in the same file. The commit message and evidence
claim "three new controls (M15..M17)" was therefore ambiguous and untraceable.
Fixed: the three P3-completion mutations are renumbered `M20/M21/M22`; the
reference in `EV-RP3-004` is updated to match. No behaviour and no count changed
(still 22 readiness mutations caught). The historical commit message of
`df2a715` still says `M15..M17`; history is not rewritten, and this report
supersedes that text.

**F3 — Vacuous control `POSCTRL-I` on a guard the P3 correction modified.**
`sps2/tools/validate-p5.py` section 2 was changed by `D-P3-G.2` to exclude the
adapter surface from the vendor-name walk, but its `POSCTRL-I` control only read
the probe file back and asserted the string it had just written was present — a
tautology that never exercised the walk. Fixed: the walk is extracted to
`neutrality_hits(core)` and shared by the assertion and the control, which now
plants a vendor name *outside* `adapters/` and requires the walk to flag it.
Non-vacuity demonstrated — with the probe, the walk flags it; without it, no
hit. The control count is unchanged (`validate-p5.py` still reports 1 control).

### 4.2 Findings documented but deliberately not changed

**G1 — The "exactly two" bound of `D-P3-A` is not enforced.**
Both `sps2/tools/test-portability.py` section 1 and
`sps2/tools/validate-p7-readiness.py` (`p3_delivery_state`) assert
`len(real) >= 2`, never `== 2`. A third `EXPERIMENTAL`/`VERIFIED` adapter would
therefore pass every guard even though `D-P3-A` bounds the set to exactly two
and states that adding more requires a new decision. Tightening this to `== 2`
(or gating on a recorded decision) is a policy choice, not a mechanical fix, so
it is left to the User. **Recommended follow-up.**

**G2 — Evidence `relates_to` shape deviates from the evidence contract.**
The roadmap-P3 records use `relates_to` keys (`decision_ids`, `deliverable`) that
`sps2/governance/SCHEMAS/evidence.schema.json` does not permit
(`additionalProperties: false`), and `decision_ids` is an array where the schema
expects `string|null`. No validator enforces the `relates_to` shape
(`check_sps2.py` checks only id pattern, result enum, non-empty `observed_result`
and duplicates), and the pre-existing `P4-EVIDENCE.json` already uses an
out-of-schema `incident_id`. This is a **systemic, pre-existing** convention, not
a P3 regression; flagged for a separate, deliberate consistency fix.

**G3 — Robustness of the adapter-surface exclusion.**
The neutrality walkers detect the adapter surface with the substring test
`"adapters" in root`. If the repository path itself contained the substring
`adapters`, the walk would be skipped entirely. In `test-portability.py` this is
caught loudly by control `C1` (the planted probe would go undetected and the test
would fail), but `validate-p5.py`, `test_p5.py` and `core_is_adapter_free()` have
no equivalent guard. Low risk given the fixed path; noted for hardening.

---

## 5. Statement

This review inspected, verified and (within the authorised P3 scope) corrected
the delivered Roadmap P3 work. It **does not** mark Roadmap P3 complete or
approved, does not record `SATISFIED`, does not begin P7, and does not touch any
item on the `D-P3-F` forbidden list. Roadmap P3 satisfaction remains below
`SATISFIED` until the User approves the delivered state; the completion block in
`sps2/decisions/ROADMAP-P3-DECISIONS.json` remains
`PENDING_USER_APPROVAL`. User approval is authoritative and is never substituted
by this agent.

Nothing was pushed. All changes are committed to
`review/roadmap-p3-secondary-review` only.

---

## 6. Reproduction

```
bash sps2/tools/validate-sps2.sh
bash sps2/tools/validate-p2.sh
bash sps2/tools/validate-p3.sh
bash sps2/tools/validate-p4.sh
python3 sps2/tools/validate-p5.py
python3 sps2/tools/validate-p6.py
python3 sps2/tools/validate-p7-readiness.py
python3 sps2/tests/test_p5.py
bash sps2/tools/test-snapshot-integrity.sh
bash sps2/tools/test-phase-boundary.sh
bash sps2/tools/test-p7-readiness-mutation.sh
bash sps2/security/test-secret-safety.sh
bash .sps/tools/validate-governance.sh
python3 sps2/tools/test-history-credential-check.py
python3 sps2/tools/check_emoji.py sps2
python3 sps2/tools/test-portability.py
```

Review changes are confined to:
`sps2/tools/test-portability.py`, `sps2/tools/test-p7-readiness-mutation.sh`,
`sps2/tools/validate-p5.py`, `sps2/evidence/ROADMAP-P3-EVIDENCE.json`
(label reference only; no result changed).
