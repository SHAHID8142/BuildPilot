# AUDIT-ROADMAP-P3 — Adversarial Review of the D-P3-A Exact-Count Remediation

Review date: 2026-10-05
Reviewer: secondary **adversarial review/verification** agent (**not** a User;
this review is **not** an approval)
Branch: `review/roadmap-p3-secondary-review`
State reviewed: `b83b02329823fa146d54fe89478f63e71f7bd637`
Remediation chain under review: `22f44ce` → `d2c1786` → `b83b023`
(on top of the earlier verified review commit `d368a9f`; `main` is `df2a715`)

Verification method: the full suite and every behavioural probe were run against
an **isolated, frozen snapshot** of `b83b023` (`/tmp/p3snap`), never the live
tree, so concurrent tooling cannot contaminate the result. (During this review
the live tree was transiently polluted by orphaned probe files from interrupted
runs; that pollution produced spurious failures which are **not** defects and are
excluded. All results below are from the clean snapshot.)

---

## 1. Current commit/state reviewed

| Commit | Subject | Files |
|---|---|---|
| `22f44ce` | fix(roadmap-p3): enforce D-P3-A's exact two-adapter bound | `validate-p7-readiness.py`, `test-portability.py`, `test-p7-readiness-mutation.sh`, `ROADMAP-P3-EVIDENCE.json` |
| `d2c1786` | fix(roadmap-p3): make the D-P3-A control zero-adapter-safe | `test-p7-readiness-mutation.sh` |
| `b83b023` | fix(roadmap-p3): make the D-P3-A count mutations state-independent | `test-p7-readiness-mutation.sh` |

Note on timing: when this review began there was **no** remediation commit on any
ref. `22f44ce` landed during the review; `d2c1786`/`b83b023` followed after the
reviewer independently reproduced a regression in `22f44ce` (see §11.1). The
review therefore covers the whole chain at `b83b023`.

---

## 2. D-P3-A interpretation

`sps2/decisions/ROADMAP-P3-DECISIONS.json` `D-P3-A`, read directly:

> **decision:** "Implement real adapters for **exactly two** low-risk targets:
> Codex and OpenCode."
> **bounded_scope:** "**Two adapters only.** Adding any further adapter requires
> a new decision."

**Verdict: D-P3-A means EXACTLY two real adapters, named `codex` and `opencode`.**
It is not a floor and not an open-ended set. This is unambiguous.

---

## 3. Exact-count implementation verdict

Two enforcement points implement the invariant; both were inspected:

**`sps2/tools/test-portability.py` (section 1, lines 50-56, 209-231)**
```python
AUTHORISED_REAL_ADAPTERS = ("codex", "opencode")
REAL_MATURITIES = ("EXPERIMENTAL", "VERIFIED")
...
real = sorted(a.get("agent_id") for a in entries.values()
              if a.get("maturity") in REAL_MATURITIES)
if not entries:                                   # empty registry valid (D-P3-D)
    r.ok("zero-adapter registry accepted as valid (D-P3-D)")
elif len(real) != len(AUTHORISED_REAL_ADAPTERS):
    r.bad("ADAPTER_COUNT_VIOLATION: ...")          # exact count, not a floor
elif set(real) != set(AUTHORISED_REAL_ADAPTERS):
    r.bad("ADAPTER_IDENTITY_VIOLATION: ...")       # exact identity
else:
    r.ok("exactly the two authorised real adapters (D-P3-A): %s" % real)
```

**`sps2/tools/validate-p7-readiness.py` (`p3_delivery_state`, lines 151-175)** —
the same exact-count + exact-identity logic, appending
`ADAPTER_COUNT_VIOLATION` / `ADAPTER_IDENTITY_VIOLATION` to `errors`, with
`delivered = not errs and count_ok and generic and conformance`.

**"Real adapter" is defined consistently in both points**: a real adapter is one
whose `maturity` is `EXPERIMENTAL` or `VERIFIED`; the `DECLARED` `generic`
fallback is never counted. `generic` upgraded to `EXPERIMENTAL` *is* counted.

**Verdict: the invariant is genuinely EXACT (`!= 2` / set-equality), not `>= 2`,
in both enforcement points.** The `>= 2` floor of the reviewed finding is gone.
This is the correct fix and it is correct in substance.

---

## 4. Test matrix (behavioural, well-formed registries)

Run against the real `s1` and the real `validate-p7-readiness.py` at `b83b023`,
in an isolated copy. `generic` = DECLARED fallback unless stated.

| # | Registry | `test-portability.py` s1 | `validate-p7-readiness.py` | Required | Result |
|---|---|---|---|---|---|
| A | 0 real (generic only) | REJECT — `ADAPTER_COUNT_VIOLATION` | REJECT | REJECT | ✅ |
| B | 1 real (generic+codex) | REJECT — `ADAPTER_COUNT_VIOLATION` | REJECT | REJECT | ✅ |
| C | 2 real authorised (generic+codex+opencode) | **ACCEPT** | **ACCEPT** | ACCEPT | ✅ |
| D | 3 real (generic+codex+opencode+delta) | REJECT — `ADAPTER_COUNT_VIOLATION` (found 3) | REJECT | REJECT | ✅ |
| D2 | 3 real (generic upgraded to EXPERIMENTAL) | REJECT (`GENERIC_FALLBACK_CHANGED` + count) | REJECT — `ADAPTER_COUNT_VIOLATION` | REJECT | ✅ |
| E | wrong pair (generic+codex+delta) | REJECT — `ADAPTER_IDENTITY_VIOLATION` | REJECT — `ADAPTER_IDENTITY_VIOLATION` | REJECT | ✅ |
| E2 | no generic (codex+opencode) | REJECT — `GENERIC_FALLBACK_CHANGED_OR_MISSING` | ACCEPT (claim-check only; `delivered=False` so a `SATISFIED` claim would be refused) | REJECT | ⚠️ see §11.3 |
| F1 | duplicate `agent_id` | REJECT — `DUPLICATE_ADAPTER_ID` | REJECT | REJECT | ✅ |
| F2 | malformed entry (maturity real, no `agent_id`) | **CRASH — unhandled `TypeError`** | **CRASH — unhandled `TypeError`** | REJECT | ❌ see §11.2 |
| G | empty registry `[]` | REJECT (`GENERIC_FALLBACK_CHANGED_OR_MISSING`) + `ok zero-adapter accepted` | ACCEPT | (D-P3-D valid) | ⚠️ see §11.4 |

End-to-end mutation proof (inject a 3rd real adapter `delta`, run the **real**
tools): `test-portability.py` → `PORTABILITY CONFORMANCE INVALID` with
`ADAPTER_COUNT_VIOLATION: ... found 3 (codex, delta, opencode)`;
`validate-p7-readiness.py` → `P7 READINESS INVALID` with the same
`ADAPTER_COUNT_VIOLATION`. **The D-P3-A defect is genuinely fixed.**

---

## 5. Mutation / non-vacuity verification

New coverage in `test-p7-readiness-mutation.sh`: mutations `M23`–`M26` and three
controls; suite total `29 caught-or-control-satisfied, 0 missed` (+ 11 phase
validators, 0 missed), reproduced in the clean snapshot.

| Case | Mutation | Observed |
|---|---|---|
| M23 | 0 real (both downgraded) | CAUGHT `ADAPTER_COUNT_VIOLATION` |
| M24 | 1 real | CAUGHT `ADAPTER_COUNT_VIOLATION` |
| M25 | 3 real (generic upgraded) | CAUGHT `ADAPTER_COUNT_VIOLATION` |
| M26 | 2 real, wrong pair | CAUGHT `ADAPTER_IDENTITY_VIOLATION` |
| ctrl | intact authorised set | ADMIT |
| ctrl | empty registry `[]` (D-P3-D) | ADMIT |
| ctrl | generic DECLARED alone | REJECT (populated) / ADMIT (zero-adapter state) |

**Independent neuter experiment** (defeat the rule: `!=` → `<`, identity branch
disabled, in a copy): the mutation suite then reports **`M25` MISSED and `M26`
MISSED`** and `s1` returns **ACCEPT** for 3 real adapters. This proves the new
mutations genuinely exercise the exact-count/identity predicate and are **not
vacuous** — a regression to the old `>= 2` floor is caught.

**Zero-adapter state** (the D-P3-D delete-all copy): the mutation suite is
**green** — `29 caught-or-control-satisfied, 0 missed + 11/0`, rc 0, with all
three controls and the p4/p5/p6 admission controls satisfied.

Minor observation (not a defect): the `mut`/`ctrl` CAUGHT determination is
verdict-based (`grep 'P7 READINESS RECORDED'`), not code-specific; the specific
error code is only echoed. This matches the suite's pre-existing design.

---

## 6. Previous three fixes still intact?

| Fix (from `d368a9f`) | Present at `b83b023`? |
|---|---|
| F1 non-vacuous portability `C4` (`detected == ["sps2/no/such/resume-source.md"]`) | ✅ `test-portability.py:422` |
| F2 unique mutation labels `M20/M21/M22` | ✅ `test-p7-readiness-mutation.sh:60/62/64` |
| F3 shared `neutrality_hits(core)` + non-vacuous `POSCTRL-I` | ✅ `validate-p5.py:37/105/117-120` |

None were undone by the remediation.

---

## 7. Finding B — evidence `relates_to` vs evidence schema

**Independently confirmed real.** `sps2/governance/SCHEMAS/evidence.schema.json`
defines `relates_to` with `additionalProperties: false` and only
`requirement_id | capability_id | action_id | task_id` (each `string|null`).
Every record in `sps2/evidence/ROADMAP-P3-EVIDENCE.json` — including the new
`EV-RP3-007` added by `22f44ce` — uses `relates_to: {"decision_ids": [...],
"deliverable": "..."}`. `decision_ids` is an array and `deliverable` is not an
allowed key, so under strict schema validation all seven records are invalid.

- **Does it affect P3 correctness?** No. No validator applies
  `evidence.schema.json` (nothing references it or `relates_to`); `check_sps2.py`
  checks only id pattern, result enum, non-empty `observed_result` and
  duplicates, and it accepts the file.
- **Pre-existing or P3-introduced?** Systemic/pre-existing: the schema is simply
  not enforced, and `P4-EVIDENCE.json` already uses the out-of-schema
  `incident_id`. P3 (and `EV-RP3-007`) follow the same loose convention.
- **Recommendation:** a **separate, deliberate** consistency fix (either extend
  `evidence.schema.json` to admit the keys actually in use, or enforce it and
  correct all evidence files). Not a P3 blocker; do not fix inside this scope.

---

## 8. Finding C — `"adapters"` substring matching

**Independently confirmed real.** The neutrality walkers skip a path when
`"adapters" in root` (a bare substring). I reproduced the consequence by placing
the tree on a path containing `adapters` (`/tmp/.../my-adapters-probe-*/tree`):

| Check | Behaviour on an `adapters`-containing path |
|---|---|
| `validate-p5.py` | FAILS LOUDLY (`POSCTRL-I ... MISSED`, 4 failures) — protected by fix F3 |
| `test_p5.py` neutrality | FAILS LOUDLY (`AssertionError`) — protected by the D-P3-G.2 negative test |
| `test-portability.py` `C1` | fails loudly (planted probe undetected) |
| `core_is_adapter_free()` | returns `[]` — **silently vacuous** (no control) |

- **Does it affect P3 correctness?** No, not on the actual path
  (`/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`, which contains no
  `adapters` substring). It is a robustness hazard, not a live defect.
- **Pre-existing or P3-introduced?** Pre-existing; P3 copied the same substring
  pattern into `test-portability.py`/`validate-p5.py`.
- **Recommendation:** separate, low-priority hardening — match the path
  *segment* (`os.sep + "adapters" + os.sep`) instead of a bare substring, and add
  a control to `core_is_adapter_free()`. Do not change now.

---

## 9. Full validator results (clean snapshot, `b83b023`)

Run sequentially; every suite green; post-run tree clean.

| Suite | Result |
|---|---|
| `validate-sps2.sh` | 72 / 0 / 25 |
| `validate-p2.sh` | 69 / 0 / 22 |
| `validate-p3.sh` | 67 / 0 / 18 |
| `validate-p4.sh` | 59 / 0 / 22 + 7 controls |
| `validate-p5.py` | 46 / 0 / 18 + 1 control |
| `validate-p6.py` | 65 / 0 / 24 + 1 control |
| `validate-p7-readiness.py` | 30 / 0 / 7 |
| `test_p5.py` | 40 tests OK |
| `test-snapshot-integrity.sh` | 9 caught / 0 missed |
| `test-phase-boundary.sh` | 11 caught / 0 missed |
| `test-p7-readiness-mutation.sh` | 29 caught-or-control-satisfied / 0 missed + 11 / 0 |
| `test-secret-safety.sh` | 9 / 0 |
| `.sps` governance | 54 / 0 |
| `test-history-credential-check.py` | 4 scenarios as required |
| `check_emoji.py sps2` | scanned 124, violations 0 |
| `test-portability.py` | **39 / 0 / 4 controls — VALID** |

---

## 10. Security / scope verification

- Scope of `d368a9f..b83b023`: only
  `sps2/evidence/ROADMAP-P3-EVIDENCE.json`,
  `sps2/tools/test-portability.py`, `sps2/tools/validate-p7-readiness.py`,
  `sps2/tools/test-p7-readiness-mutation.sh`.
- No legacy file, no `.sps/`, no `ROADMAP-P3-DECISIONS.json`, no production
  capability registry change; production registry
  `sha256 5f95f62b…37af56` unchanged.
- `completion.state` = `PENDING_USER_APPROVAL`; recon P3 = `SUBSTANTIALLY_SATISFIED`
  (not `SATISFIED`). Nothing installed, activated, promoted or pushed. Working
  tree clean. Checkpoint `a7767cf` intact.

---

## 11. New defects

### 11.1 (resolved during review) Portability regression in `22f44ce`
`22f44ce`'s new zero-adapter-unsafe control/mutations made
`test-p7-readiness-mutation.sh` fail inside the portability test's zero-adapter
copy; `test-portability.py` went **`38 passed, 1 failed`**. Cline's `d2c1786` +
`b83b023` fixed it. Re-verified green at `b83b023` (`39/0/4`, and the mutation
suite `29/0 + 11/0` in the zero-adapter state). **Closed.**

### 11.2 (OPEN) Unhandled crash on malformed adapter entries — NEW regression
Both enforcement points crash with an unhandled `TypeError` when the registry
contains an adapter entry whose `maturity` is `EXPERIMENTAL`/`VERIFIED` but whose
`agent_id` is absent (→ `None`):

- `sps2/tools/test-portability.py:226` — `", ".join(real)` with `None`
  (`TypeError: sequence item 0: expected str instance, NoneType found`).
- `sps2/tools/test-portability.py:215` — `sorted(...)` over mixed `None`/`str`.
- `sps2/tools/validate-p7-readiness.py:168` and `:173` —
  `",".join(sorted(real))` with `None`.

Reproduction (isolated copy, registry = `[{generic DECLARED}, {"maturity":
"EXPERIMENTAL"}]`): `s1` → `TypeError` at line 226; `p7` → `TypeError` at line
168. **The pre-remediation code (`df2a715`) handled the same input cleanly**
(`s1`: clean, 13 failures; `p7`: clean, rc 1). So this is a **new** regression
introduced by `22f44ce`, and required behavioural test **F (malformed)** fails:
the tool crashes instead of reporting a controlled rejection, and the crash
aborts the remaining sections. It is untested — no mutation covers a malformed
entry.

**Severity:** low-to-moderate (it requires a malformed registry, which the
contract check already reports; the delivered registry is well-formed, so the
count invariant is unaffected). But a validator that crashes on invalid input is
a real defect and a required test case. **Send back to Cline** for a small fix —
coerce/filter `agent_id` before joining (e.g. only include `str` ids, or use
`str(a.get("agent_id"))`).

### 11.3 (observation) `E2` no-generic case: `validate-p7-readiness.py` admits
With `codex`+`opencode` and no `generic`, `p3_delivery_state` sets
`delivered=False`, so a `SATISFIED` claim is refused — but the validator's exit
code is 0 (it only hard-fails on count/identity). The generic requirement is
enforced by `test-portability.py` s1 instead. Acceptable as a "claim check", but
worth noting: `validate-p7-readiness.py` alone does not reject a missing
`generic`.

### 11.4 (observation) `s1` empty-registry branch is ineffective
`s1` emits `ok "zero-adapter registry accepted as valid (D-P3-D)"` for `[]`, but
the preceding `GENERIC_FALLBACK_CHANGED_OR_MISSING` check still fails, so `s1`
**rejects** an empty registry overall. D-P3-D is nevertheless satisfied because
the delete-all criterion is exercised in section 3 (which runs the suites, not
`s1`). Minor dead/inconsistent branch, not a correctness break.

---

## 12. Recommendation to the manager

The D-P3-A **count semantics are now correct and independently verified**: the
invariant is exact, `generic` DECLARED is never counted, a 3rd real adapter and a
wrong pair are both rejected by both enforcement points, the new mutation
coverage is non-vacuous (a neutered rule is caught), the zero-adapter regression
is fixed, and the full suite — including the portability conformance test — is
green.

The remediation is **not fully correct**, however: it introduced an unhandled
crash on malformed adapter entries (required behavioural test F), untested, and
a regression against the pre-remediation behaviour. One small, targeted fix
(§11.2) is required before this remediation can be signed off. Findings B and C
are real but pre-existing/systemic and should be handled in a separate change.

**This review does not approve Roadmap P3 and does not mark it complete. User
approval remains the only approval authority. Nothing was pushed.**

---

## Final conclusion

**FAIL — remediation is incomplete/incorrect.**

The D-P3-A exact-count rule itself is correctly enforced and independently
verified, but the remediation introduced a new unhandled-crash defect on
malformed registry entries (required behavioural test F) that remains open and
must be sent back to Cline for a small robustness fix.
