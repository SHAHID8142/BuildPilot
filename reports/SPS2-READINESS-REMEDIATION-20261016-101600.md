# SPS2 Readiness Remediation — 2026-10-16 10:16

**Mission:** SPS2 Final Readiness Decision & Remediation Execution
**Repository:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`
**Branch:** `build/roadmap-p3-completion`
**HEAD:** `cdcbca83679844ea66196f25773f42d9b64569ec` (unchanged)
**Report file:** `reports/SPS2-READINESS-REMEDIATION-20261016-101600.md`

---

## 1. Executive summary

This round continued the SPS2 readiness mission. It reconciled the previous
report against the live repository, executed **one additional authorized
remediation**, independently reproduced the two highest-severity findings, and
re-verified every claim rather than inheriting it.

**What was done:**

1. **Reconciled** the prior report (`SPS2-FINAL-END-TO-END-READINESS-20261016-091500.md`)
   against the live repository. Every material claim held: HEAD unchanged, 10
   modified tracked files (7 pre-existing user edits + 3 prior-round fixes),
   0 staged, 0 stash, remote present, all 7 user edits byte-identical.
2. **Corrected a root-cause error in the prior report.** The four P2–P5
   zero-adapter failures were attributed to the stale `c11da27` baseline pin.
   That attribution is **confirmed correct** — but I initially "refuted" it
   with an invalid experiment (see §7.1) and had to retract that refutation.
3. **Fixed one authorized defect (Category A).** `validate-p7-readiness.py`
   required the `generic` fallback adapter even in the empty-registry state
   that approved decision **D-P3-D** explicitly requires to be accepted.
4. **Added a regression test** that is proven non-vacuous by negative control.
5. **Independently reproduced** the false-PASS defect in `validate-p2.sh` and
   the attribution self-approval fail-open, both with my own experiments.
6. **Verified** the full tracked corpus (562 tests), the full worktree corpus
   (896 tests), order independence, and a clean clone (558 tests).

**Product verdict: `NOT_READY`.** See §23.

---

## 2. Final verdict

| Dimension | Status |
|---|---|
| Audit mission | **COMPLETE** |
| Remediation implemented | **YES** — 1 new fix this round (4 total across rounds) |
| Remediation independently verified | **YES** — by negative control on real code |
| Changes committed | **NO** — explicitly prohibited |
| Changes published | **NO** |
| **Product ready for use** | **`NOT_READY`** |

`NOT_READY` is required because mandatory gates G13 (CI) and G14 (traceability)
fail, the portability harness remains red at **34 passed / 5 failed**, a
critical false-PASS risk remains unfixed in two protected validators pending
User approval, and the attribution self-approval path remains open pending a
User decision. None of these is within my authority to resolve.

---

## 3. Initial and final Git state

| Property | Value |
|---|---|
| Branch | `build/roadmap-p3-completion` |
| HEAD (initial = final) | `cdcbca83679844ea66196f25773f42d9b64569ec` |
| Staged | 0 → 0 |
| Stash | 0 → 0 |
| Modified tracked | 10 → **11** |
| Untracked (file-level) | 107 → **108** |
| Deletions | **0** |
| Remote | `origin` → `https://github.com/SHAHID8142/Shahid-Master-Skill.git` (never contacted this round) |
| Ahead / behind cached origin | 3 / 0 |
| `git fsck` errors | 0 |
| Baseline snapshot | `/tmp/sps2-r2-baseline-1792124248/` |

**Delta explained:** +1 modified (`sps2/tools/validate-p7-readiness.py`, my fix)
and +1 untracked (`sps2/tests/test_p7_zero_adapter_readiness.py`, my new
regression test). Nothing else changed.

---

## 4. Task list and completion status

| ID | Pri | Task | Status |
|---|---|---|---|
| T0 | 0 | Baseline + reconcile prior report vs live repo | VERIFIED |
| T1 | 1 | Verify protected-validator false-PASS claims | VERIFIED (2/4 confirmed, 2/4 refuted) |
| T2 | 2 | Separate pin-caused from registry-caused zero-adapter failures | VERIFIED |
| T3 | 2 | Fix P7 `generic` exemption contradicting D-P3-D | VERIFIED |
| T4 | 2 | Regression test + negative control for T3 | VERIFIED (non-vacuous) |
| T5 | 3 | Attribution self-approval fail-open | VERIFIED — BLOCKED_USER_APPROVAL (governance-gated file) |
| T6 | 4 | CI module-deletion invisibility + zero-validator gap | VERIFIED — BLOCKED_USER_APPROVAL (CI scope) |
| T7 | 5 | Durability: enumerate worktree-only fixes | VERIFIED — all 4 worktree-only |
| T8 | 6 | Governance: P5 authorization, CI traceability, DEC-0001, identity | VERIFIED — BLOCKED_USER_APPROVAL |
| T9 | 7 | P10/frontend/untracked disposition inventory | VERIFIED |
| T10 | 8 | Final corpus, clone, portability, order independence | VERIFIED |
| T11 | 8 | Report + decision packets | VERIFIED |

Statuses use the mission vocabulary: VERIFIED, BLOCKED_USER_APPROVAL,
NOT_TESTED, DEFERRED_WITH_REASON.

---

## 5. Subagent availability and assignments

Two read-only subagents were dispatched (the mission allows up to six at depth
one). Two — not six — were used, because the remaining investigations were
already resolved by direct experiment and a larger fan-out would have produced
overlapping evidence without adding independence.

| Agent | Role | Scope | Status |
|---|---|---|---|
| S1 | Protected-validator false-PASS | p2/sps2/p3/p4 `.sh` | Returned; claims verified manually |
| S2 | Attribution security | `attribution.py`, policy, consumers | Returned; claims verified manually |

Both were instructed to work only in `/tmp` and to make no repository edits.
I manually re-ran every load-bearing claim from both; results in §6.

---

## 6. Findings independently reproduced

Every claim below was re-executed by me. I did not accept a subagent summary.

| Finding | How I verified | Result |
|---|---|---|
| `run_check` at `validate-p2.sh:34` and `validate-sps2.sh:36` discards exit status **and** stderr | Read the source | Confirmed verbatim |
| A crashed checker still prints **7 fabricated PASS lines** in `validate-p2.sh` | Replaced `check_p2.py` with `raise SystemExit(...)` in a `/tmp` copy; ran the validator | Confirmed: section 2 printed 7 PASS, byte-identical to a healthy run |
| Same corrupted record: rejected when healthy, silently PASSed when crashed | Corrupted `sps2/research/P2-SOURCES.json` → `sources[0].url = ""`; ran both ways | Confirmed: `FAIL sources: ERR SRC-001` vs `PASS sources` |
| `validate-p3.sh:90` / `validate-p4.sh:72` do **not** share the defect | Read both; both use `2>&1` | **Refuted** for p3/p4 |
| A fully crashed checker still exits 1 in p2 | Ran it | Confirmed: `P2 RESEARCH INVALID: 47 passed, 22 failed, 21 missed`, rc=1 |
| `Self (self-approved)` is accepted as user-attributable | Imported the module, called the predicate on 11 inputs | Confirmed: accepted; `Antigravity`/`Claude`/`the model` rejected |
| `self` is deliberately absent from the 17 approved tokens | Enumerated the token list | Confirmed: 0 tokens contain `self` |
| The pinning test asserts acceptance **by design** | Read `test_attribution_policy.py:407-424` | Confirmed: `assertTrue`, labelled approved behaviour |
| Emptying the registry makes P7 emit `RECORD_OVERSTATES_P3` | Faithful `copytree` copy + `apply_delete_all` | Confirmed: rc=1, `delivered=False approved=True` |
| The four P2–P5 failures are the `c11da27` pin, not the registry | Ran the pin predicate with adapters present and deleted | Confirmed identical output → adapter-independent |

---

## 7. Defects, root causes, and changes

### 7.1 Correction to my own work this round

While isolating the P2–P5 failures I built an isolated copy using
`git archive HEAD | tar -x`. `git archive` **excludes `.git`**, so
`repository_has_licence()` (`promotion_gates.py:46-54`, which shells out to
`git -C REPO ls-files`) returned `False` in that tree, flipping gate **D**
(LICENCE) and producing `ASSESSMENT_STALE` errors. I briefly concluded the
P2–P5 failures were caused by capability-assessment staleness rather than the
stale pin.

That conclusion was **wrong**, and I discarded it once I replicated the
harness's actual copy method (`portability.py:487-489`, `shutil.copytree`). In
a faithful copy the failures are exactly the `legacy modified` check driven by
the `c11da27` pin — the originally reported cause. The predicate output is
byte-identical with adapters present or deleted:

```
.github/workflows/sps-ci.yml
.sps/tools/validate-capability.sh
.sps/tools/validate-control.sh
.sps/tools/validate-governance.sh
```

Recorded because a wrong root cause is more dangerous than no root cause, and
because the mission requires that a tree without `.git` not be treated as
equivalent to the repository.

### 7.2 D-17 — P7 requires `generic` in the state D-P3-D says must pass

| Field | Value |
|---|---|
| **ID** | D-17 |
| **Severity** | Medium |
| **File** | `sps2/tools/validate-p7-readiness.py:167` |
| **Protected?** | **No** — not on the 13-file Phase 3 protected list, not modified in the worktree |
| **Category** | A — clearly authorized technical correction |

**Root cause.** The validator computed

```python
generic = PT.FALLBACK_ADAPTER_ID in PT.entry_ids(adapters)
```

and required `generic` for `delivered` (`:197`). The `generic` fallback is
itself a per-agent adapter entry, so deleting all adapters necessarily deletes
it. Under an empty registry `generic` was `False`, `delivered` became `False`,
and the validator emitted `RECORD_OVERSTATES_P3` — in exactly the state
**D-P3-D** requires to be accepted:

> "An empty adapter registry [] is valid and must be accepted by the
> portability test."

The `count_ok` invariant immediately below (`:176-177`) already carried the
empty-registry exemption; `generic` did not. The exemption was only
partially applied.

**Fix (8 insertions, 1 deletion):**

```python
generic = (not adapters) or PT.FALLBACK_ADAPTER_ID in PT.entry_ids(adapters)
```

with a comment citing D-P3-D.

**Before / after:**

| State | Before | After |
|---|---|---|
| Live repo (adapters present), `validate-p7-readiness.py` | rc=0, 30 passed | rc=0, 30 passed (unchanged) |
| Zero-adapter copy, `validate-p7-readiness.py` | **rc=1**, `RECORD_OVERSTATES_P3`, `26 passed, 2 failed` | **rc=0**, `30 passed, 0 failed, 7 negative cases` |
| Non-empty registry **without** `generic` | rc=1, rejected | **rc=1, still rejected** |
| Portability harness | 33 passed / 6 failed | **34 passed / 5 failed** |

**Regression test.** `sps2/tests/test_p7_zero_adapter_readiness.py` (new, 3
tests). It executes the real validator in a disposable copy — it does **not**
re-derive the predicate in Python.

**Negative control (decisive).** I reverted the one-line predicate in a `/tmp`
copy and ran the new test against it → `FAILED (failures=1)`, with the
validator reporting `RECORD_OVERSTATES_P3`. Against the fixed tree → `OK`. The
test therefore detects the original defect and is not vacuous.

**A vacuous first attempt, caught and replaced.** My first version of this test
recomputed `delivered` locally in Python. It passed against the **reverted**
validator, because it was testing its own copy of the rule. I detected this by
running the negative control, rewrote the test to invoke the real validator via
`subprocess`, and re-ran the control. This is exactly the failure mode
Section 5 of the mission warns about.

**Independent reviewer verdict.** Not separately reviewed this round — I
verified it myself via the negative control above. Recorded as a limitation in
§24.

**Remaining risk.** Low. The change is confined to one boolean expression, adds
no new code path, and the rejection path for malformed non-empty registries is
proven intact.

### 7.3 D-18 — `validate-p2.sh` / `validate-sps2.sh` fabricate PASS on a dead checker

| Field | Value |
|---|---|
| **ID** | D-18 |
| **Severity** | **High** (not Critical — see scoping) |
| **Files** | `sps2/tools/validate-p2.sh:34`, `sps2/tools/validate-sps2.sh:36` |
| **Protected?** | **Yes** — both on the 13-file protected list |
| **Category** | B — requires User approval |

**Root cause.**

```bash
run_check() { python3 "$CHECK" "$1" "$2" 2>/dev/null; }
```

stderr is discarded and the exit status is never captured. The consumer tests
only stdout emptiness:

```bash
assert_clean() {
  local out; out="$(run_check "$1" "$2")"
  if [ -z "$out" ]; then pass "$3"; else ... fail ...; fi
}
```

A legitimate pass and a crash are indistinguishable (`stdout == ""`), so both
score PASS. Proven: with a crashing checker, section 2 printed 7 PASS lines
identical to a healthy run, and a corrupted record that the healthy checker
correctly rejects (`ERR SRC-001`) was silently accepted.

**Severity scoping — deliberately not inflated.** The negative suites in both
files require non-empty output, so a **full** crash still exits 1. The defect
is that structural PASSes are **fabricated** and the PASS counter inflates. It
becomes a true fail-open verdict only for a checker that dies on some
invocations while the rest stays green. I tested the partial-crash case and it
also exited 1, because each kind has negative-suite coverage. High, not
Critical.

**Refuted:** the same defect does **not** exist in `validate-p3.sh` or
`validate-p4.sh`; both use `2>&1`, so a crash writes a message into the
captured output and becomes a FAIL. Verified by injecting crashes into both.

**Test-coverage gap.** `sps2/tests/test_shell_validator_policy_contract.py:32-38`
lists p3 and p4 in `MIGRATED_SHELL` and **omits p2 and sps2** — the two
vulnerable files are precisely the two not covered by that static guard.

**Fix prepared, not applied.** Four patches exist and all four still apply
cleanly (`git apply --check`):

| Patch | sha256[:16] |
|---|---|
| `P1-validate-p2-exit-status.patch` | `247ef4f055a6cc56` |
| `P2-validate-sps2-exit-status.patch` | `0a90a2cefcca6be1` |
| `P3-validate-p3-exit-status.patch` | `3a334297cc716414` |
| `P4-validate-p4-negative-controls.patch` | `c9665a4cf08f6fff` |

Location: `/tmp/subC-final/proposals/`. These are proposals. Applying them to
the real repository requires explicit User authorization per file (DP-1).

### 7.4 D-19 — Attribution accepts a self-attributed approval

| Field | Value |
|---|---|
| **ID** | D-19 |
| **Severity** | **Medium** latent (High if ever exploited) |
| **File** | `sps2/governance/attribution.py:144-162` |
| **Protected?** | **Yes** — governance-gated |
| **Category** | B — requires User approval |

**Root cause.** The predicate is a **denylist**; acceptance is the default when
no token matches:

```python
AGENTISH = re.compile(r"\b(agent|ai|assistant|model|bot|claude|...)\b", re.I)
...
if not who or AGENTISH.search(who):
    return False
return bool((a.get("decided_on") or a.get("decided_at") or "").strip())
```

`self` is **deliberately excluded** from the 17 approved tokens (ratified by
DEC-0027, to preserve the legitimate surname "Self"). `"Self (self-approved)"`
therefore matches nothing and is accepted.

**Verified by my own experiment:**

| `decided_by` | Accepted |
|---|---|
| `"User"` | yes |
| **`"Self (self-approved)"`** | **yes** |
| `"Self"`, `"Jane Self"`, `"self"` | yes |
| `"Antigravity"`, `"Claude"`, `"the model"`, `"Assistant"`, `"AI"` | no |
| `""`, `None` | no |

**Currently not exploited.** No decision, requirement, or `.sps` record carries
a self-attributed value; the only occurrence is the test fixture itself.

**The pinning test asserts this is correct by design.**
`test_attribution_policy.py:407-424` uses `assertTrue` and states the
acceptance is approved behaviour. Closing the gap therefore arguably requires a
User decision, and a naive fix (adding `self` to the token list) would break
the legitimate surname and violate DEC-0027.

**Mitigating factor.** Several shell gates use exact equality
`decided_by == "User"` (`validate-p3.sh:113-119`, `validate-p4.sh:277,297,322`),
and those reject it. The exposure is on the denylist-governed consumers.
`p17/__main__.py:379-384` — the actual execution gate — consults **neither**
`AGENTISH` nor `approval_is_user_attributable`; it requires only
`state == APPROVED` and a self-asserted `decided_by_role == "USER"`. I verified
that file contains zero references to the attribution predicate.

**Minimal rule proposed (not implemented).** Reject the self-approval
*semantic phrase* rather than the bare word, e.g.
`\bself[-\s]?approved\b|\bself[-\s]?approval\b|\bapproved\s+by\s+self\b`,
leaving `Jane Self` attributable and `attribution_policy.json` untouched. This
is a proposal only. Requires DP-3.

### 7.5 D-20 — CI does not execute any shell validator

| Field | Value |
|---|---|
| **Severity** | High |
| **File** | `.github/workflows/sps-ci.yml` |
| **Protected?** | **Yes** |
| **Category** | B — requires User approval |

No `validate-*.sh` is referenced executably anywhere under `.github/`. The
false-PASS defects in D-18 therefore cannot be caught by CI even if triggered.

**`MIN_TESTS=500` module-deletion exposure — measured, not estimated.** The
committed corpus is 558 tests, a margin of 58 over the threshold. I measured
the per-module test count for all 26 tracked modules by running each in
isolation:

- The **largest** module is `test_attribution_policy.py` at **68 tests**.
  `558 − 68 = 490 < 500`, so deleting it **would** fail CI.
- Any module with **more than 58 tests** is therefore caught.
- **24 of the 26 modules** have ≤58 tests and would be deleted **invisibly** —
  CI would stay green with the module entirely gone. The largest invisible
  modules are `test_p5.py` (48), `test_p17_lifecycle.py` (44), and
  `test_url_taxonomy.py` (42).
- Only 2 modules are protected by the guard: `test_attribution_policy.py` (68)
  and `test_p17_security.py` (62).

**Correction to my own earlier statement in this report.** I first wrote that
"deleting any single tracked module still clears the threshold". That is
**wrong** and I refuted it empirically. The accurate statement is the one
above: 24 of 26 are invisible, but the two largest are not. A guard that catches
2 of 26 modules is weak, not useless, and the distinction matters for
prioritizing the DP-7 repair.

---

## 8. Changes actually applied

| File | Change | Lines | Status |
|---|---|---|---|
| `sps2/tools/validate-p7-readiness.py` | D-P3-D empty-registry exemption extended to `generic` | +8 / −1 | applied, worktree-only |
| `sps2/tests/test_p7_zero_adapter_readiness.py` | new regression test (3 tests, executes the real validator) | new file | applied, untracked |

Both are **uncommitted**, per standing prohibition.

## 9. Changes proposed but not applied

| Proposal | Blocker | Decision |
|---|---|---|
| 4 protected-validator patches (`/tmp/subC-final/proposals/`) | Protected files | DP-1 |
| `generic`-pin / baseline-pin repair for P2–P5 | Redefines `REQ-P3-08` | DP-2 |
| Self-approval rejection rule | Governance-gated file + pinning test | DP-3 |
| Stale `note` in `ROADMAP-P3-DECISIONS.json` | Decision instrument | DP-4 |
| CI per-module guard / validator invocation | CI scope (workflow is protected) | DP-7 |
| Commit the worktree-only fixes | Committing is prohibited | DP-9 |

---

## 10. Regression tests

| Defect | Regression test | Non-vacuous? |
|---|---|---|
| D-17 (P7 zero-adapter) | `sps2/tests/test_p7_zero_adapter_readiness.py` — 3 tests | **Yes** — fails (`failures=1`) against the reverted validator, passes against the fixed one |
| Prior round F-1 (RESUME drift) | portability harness `RESUME_COMPLETION_STATE_DRIFT` | Yes — reintroducing the drift re-emits the failure |
| Prior round F-2 (env sentinel leak) | `test_p17_security.py` (2 tests) | Yes — proven by mutation |
| Prior round F-3 (PATH no-op) | `test_p17_pinning.py` (outcome assertion) | Yes — revert to `setattr` yields `FAIL=4 ERR=2` |

---

## 11. Negative-control evidence

| Control | Method | Observed |
|---|---|---|
| D-17 fix | Revert the predicate in a `/tmp` copy; run the new test | `FAILED (failures=1)` + `RECORD_OVERSTATES_P3` |
| D-17 fix (validator) | Revert in copy; run validator on empty registry | rc=1, `RECORD_OVERSTATES_P3` |
| D-17 control preserved | Non-empty registry without `generic` | rc=1, still rejected |
| D-18 false-PASS | Crash the checker in a copy | 7 fabricated PASS lines |
| D-18 false-PASS (decisive) | Corrupt a record, crash the checker | healthy → `FAIL ... ERR SRC-001`; crashed → `PASS` |
| D-18 refutation | Crash p3/p4 checkers | Both FAIL correctly; no false-PASS |
| D-19 predicate | 11 inputs through the real predicate | `Self (self-approved)` accepted |

---

## 12. Current-worktree test results

```
Modules discovered:   26 (tracked) / 30 (worktree incl. untracked)
Tests attempted:      562 (tracked) / 896 (worktree)
Passed:               561 (tracked) / 895 (worktree)
Failed:               0
Skipped:              1
Not run:              0
Exit code:            0
```

Reversed order: **562 / 0 failed / 1 skipped** — identical. No order dependence.

## 13. Clean-clone test results

```
Source commit:        cdcbca83679844ea66196f25773f42d9b64569ec
Modules discovered:   26
Tests attempted:      558
Passed:               557
Failed:               0
Skipped:              1
Exit code:            0
```

**Difference explained (measured exactly):**

| Contribution | Tests |
|---|---|
| Clean clone of `cdcbca8` (tracked) | 558 |
| Prior-round fixes to tracked modules (`test_p17_security.py` 60→62, `test_p17_pinning.py` 23→25) | +4 |
| **Worktree tracked total** | **562** |
| Untracked module `test_p10_runtime_gate.py` | +282 |
| Untracked `domain/frontend/tests/test_content_slots.py` | +25 |
| Untracked `domain/frontend/tests/test_layout_registry.py` | +24 |
| Untracked new `test_p7_zero_adapter_readiness.py` (mine) | +3 |
| **Worktree full total** | **896** |

558 + 4 = 562, and 562 + 331 + 3 = 896, which matches the measured worktree
total exactly.

**Critical:** the clone's `sps2/RESUME.md` still reads
`COMPLETION: PENDING_USER_APPROVAL` and contains zero occurrences of
`_restore_env_var` or `pin_path_entry`. **Every fix from both rounds is absent
from committed source.** See DP-9.

## 14. Portability harness results

```
Before this round:   33 passed, 6 failed, 14 controls  (exit 1)
After the D-17 fix:  34 passed, 5 failed, 14 controls  (exit 1)
```

Remaining 5 failures, all classified:

| Failure | Class | Cause |
|---|---|---|
| `copy: P2 research not green (rc=1)` | Stale baseline pin | `c11da27` legacy-path predicate |
| `copy: P3 production not green (rc=1)` | Stale baseline pin | same predicate |
| `copy: P4 promotion not green (rc=1)` | Stale baseline pin | same predicate |
| `copy: P5 implementation not green (rc=1)` | Stale baseline pin | same predicate |
| `copy: P7 readiness mutations not green (rc=1)` | Pre-existing, adapter-independent | `35 caught, 3 MISSED` in **both** zero-adapter and live states |

The P7-mutations failure is **not** related to my fix: the mutation suite
reports the identical `35 caught, 3 MISSED` in the real repository with adapters
present. It is unmodified and pre-existing.

## 15. Zero-adapter analysis

The six reported failures split cleanly into two independent classes:

- **Four are the stale `c11da27` pin** — proven adapter-independent: the
  predicate emits the same four paths with adapters present and deleted.
- **Two were the `generic` defect (D-17)** — one of them fixed this round; the
  remaining `P7 readiness mutations` failure belongs to neither class.

Moving the pin alone would **not** repair the four, because the modified `.sh`
files still match the pathspec. It requires a User decision because it
redefines `REQ-P3-08` (DP-2).

## 16. Protected validator analysis

| File | Defect | Protected | Fix prepared |
|---|---|---|---|
| `validate-p2.sh` | False-PASS on dead checker (`:34`) | Yes | `P1-...patch` |
| `validate-sps2.sh` | False-PASS on dead checker (`:36`) | Yes | `P2-...patch` |
| `validate-p3.sh` | None found (uses `2>&1`) | Yes | `P3-...patch` (exit-status hardening) |
| `validate-p4.sh` | None found (uses `2>&1`) | Yes | `P4-...patch` (negative controls) |

All four protected hashes are **byte-identical** to baseline. No protected file
was modified.

## 17. Attribution security analysis

See §7.4. Status: reproduced, not exploited, governance-gated, awaiting DP-3.
Preserve the legitimate surname behaviour: adding `self` to the token list
would violate DEC-0027 and must not be done.

## 18. P5 / P10 / frontend / CMS disposition

| Area | Tracked? | Tests | Classification |
|---|---|---|---|
| `sps2/tests/test_p10_runtime_gate.py` | No | 282 | Requires User disposition (DP-6) |
| `domain/frontend/tests/test_content_slots.py` | No | 25 | Requires User disposition (DP-6) |
| `domain/frontend/tests/test_layout_registry.py` | No | 24 | Requires User disposition (DP-6) |
| `sps2/requirements/P5-REQUIREMENTS.json` | modified | — | Investigated, not fixed — no locating authorization instrument |
| `sps2/evidence/P5-EVIDENCE.json` | modified | — | Investigated, not fixed |
| `sps2/governance/attribution.py` | modified (+57) | — | Governance-gated; patch prepared |
| `sps2/decisions/P10-DECISIONS.json` | modified | — | P10 gate NOT activated |
| `sps2/requirements/P10-SECTION-INVENTORY.json` | modified | — | Not activated |
| `sps2/schemas/p10-slice.schema.json` | modified | — | Not activated |
| `.sps/audits/README.md` | modified | — | Unrelated user edit, untouched |

The P10 runtime gate was **not** activated. All PROPOSED and
`PENDING_USER_APPROVAL` states remain unchanged.

## 19. Untracked-work preservation

Untracked file-level count 107 → 108 (+1: my regression test). **Zero
deletions.** No file was moved, quarantined, staged, or committed. The 7
pre-existing user-modified files are byte-identical to baseline. Ignored
artifacts were not touched.

## 20. Release-readiness gate matrix

| Gate | Status | Evidence |
|---|---|---|
| G0 Repository integrity | **PASS** | HEAD unchanged, 0 staged, 0 stash, 0 deletions, fsck clean |
| G1 Governance correctness | **PASS (audit) / FAIL (product)** | DEC-0029/0030 still pending; no agent-invented approvals |
| G2 P2/SPS2 validators | **FAIL** | D-18 false-PASS unfixed, protected |
| G3 P3 correctness | **PASS** | p3 correctly fails on crashed checker |
| G4 P4 correctness | **PASS** | p4 correctly fails on crashed checker |
| G5 Attribution correctness | **PASS with limitation** | 17 tokens intact; D-19 latent fail-open |
| G6 P7 readiness | **PASS** | D-17 fixed and negative-controlled |
| G7 Resume/decision consistency | **PASS (worktree)** | drift fixed; absent from clone |
| G8 Test integrity | **PASS** | 562/896 green, order-independent, isolation verified |
| G9 Portability | **FAIL** | 34 passed / 5 failed, all classified |
| G10 CI | **PASS (simulation)** | RC propagation correct |
| G11 Reproducibility | **PASS** | clone 558 green; differences explained |
| G12 User-work preservation | **PASS** | 7/7 identical, 0 deletions |
| G13 Operational readiness | **FAIL** | No real CI run; no validator executes in CI |
| G14 Release traceability | **FAIL** | Zero in-repo authorization instrument for CI/validator migration |

**Any mandatory FAIL ⇒ not READY.**

## 21. Remaining blockers

1. **D-18 false-PASS** in two protected validators — needs DP-1.
2. **Portability harness red** at 34/5 — four need DP-2, one is pre-existing.
3. **No real CI execution**, and no validator runs in CI at all — DP-7.
4. **Attribution self-approval** open — DP-3.
5. **All four fixes worktree-only** — DP-9.
6. **Zero authorization traceability** for prior CI/validator migrations — DP-10.
7. **DEC-0001 vs actual remote history** — DP-5.

## 22. Commands used for verification

```bash
# corpus (tracked)
MODS=$(git ls-files 'test_*.py' '**/test_*.py' | grep -E '^(sps2|domain)/' \
       | sed 's/\.py$//;s#/#.#g' | sort)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $MODS

# P7 fix negative control (in a /tmp copy only)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_p7_zero_adapter_readiness

# portability harness
PYTHONDONTWRITEBYTECODE=1 python3 sps2/tools/test-portability.py

# P7 readiness, both registry states
python3 sps2/tools/validate-p7-readiness.py

# clean clone
git clone -q --no-hardlinks . /tmp/r2-clone && cd /tmp/r2-clone && git checkout -q cdcbca8
```

## 23. Tests not run and why

| Not run | Reason |
|---|---|
| Real GitHub Actions execution | Requires a push; pushing is prohibited. Never contacted the remote. |
| End-to-end `.sh` validators in the real tree | They mutate evidence/registry state. All runs used disposable `/tmp` copies. |
| `validate-p5.py` / `.sps/tools/validate-*.sh` end-to-end | Same mutation restriction |
| Python 3.12 matrix | Only 3.14.7 available locally; CI targets 3.12. Not inferable from 3.14. |
| Linux/macOS cross-platform | Only macOS available. No portability claim beyond it. |

## 24. Known limitations

- The D-17 fix was **not** independently reviewed by a separate agent this
  round; I verified it via negative control instead. All other fixes were.
- Only 2 of the permitted 6 subagents were used.
- The `MIN_TESTS=500` exposure in §7.5 is now **measured** (24 of 26 modules
  invisible; the two largest are caught), not analytic. My first statement of
  it in this report was wrong and is corrected in place.
- The `git archive` incident in §7.1 shows that isolated-copy methodology must
  replicate the harness exactly (`.git` present, `shutil.copytree`); results
  from any other copy method are void. Every `/tmp` experiment this round used
  the faithful method except the one recorded there.
- Per-module test counts were obtained by running each module standalone; a
  module that fails to import standalone would report 0 and be misclassified.
  I did not observe that here (all 26 imported cleanly), but the guard proposal
  should not rely on this method uncorrected.

## 25. Final recommendation

Continue to **`NOT_READY`**. One additional authorized defect was fixed and
proven. The remaining blockers are approval-gated, not technical unknowns.

**Recommended order of User action:**

1. **DP-1** — authorize the two false-PASS validator repairs. This is the
   highest-severity open item and the only one that can silently fabricate a
   green verdict.
2. **DP-9** — authorize committing the four verified fixes; until then every
   clone and CI run sees none of them.
3. **DP-2** — decide the baseline pin, which unblocks four of the five
   remaining harness failures.
4. **DP-7** — decide CI scope so the validators actually run.
5. **DP-3** — decide the self-approval rule.

---

## 25. User decision packets

Each decision is independent. Approving one does not authorize another. No
decision below has been inferred, pre-applied, or converted from a pending
state.

---

**DP-1 — Repair the false-PASS defects in two protected validators**

- **Question:** Do you authorize changing `sps2/tools/validate-p2.sh` and
  `sps2/tools/validate-sps2.sh` so a crashed or missing checker fails instead
  of fabricating PASS?
- **Why it matters:** These are the only two validators that score a dead
  checker as PASS. Their verdicts are consumed as evidence. A partially-dead
  checker can produce a green result that is untrue.
- **Authoritative sources:** The four scripts are on the 13-file protected list
  in `reports/SPS2-PHASE3-SAFE-REMEDIATION-20261016-081050.md:161-179`.
- **Current evidence:** `validate-p2.sh:34` and `validate-sps2.sh:36` read
  `run_check() { python3 "$CHECK" "$1" "$2" 2>/dev/null; }`; the consumer
  `assert_clean` never captures `$?`. Reproduced: 7 fabricated PASS lines with
  a crashed checker; a corrupted record that the healthy checker rejects
  (`ERR SRC-001`) is silently accepted. p3/p4 do **not** share the defect.
- **Options:** (a) authorize patches P1+P2 only; (b) authorize all four
  (P3/P4 add exit-status hardening and negative controls); (c) authorize none
  and accept the risk; (d) authorize a different mechanism.
- **Recommended:** (b) — P3/P4 currently pass, but their safety rests on
  `2>&1` alone, which is a weaker guarantee than an explicit exit-status check.
- **Files affected:** the four `sps2/tools/validate-*.sh`.
- **Risk if deferred:** a green P2/SPS2 verdict can be produced by a checker
  that never ran.
- **Exact action requiring approval:** applying
  `/tmp/subC-final/proposals/P{1,2,3,4}-*.patch` to the real worktree.
- **Safe work that can continue:** everything else in this report.

---

**DP-2 — The stale `c11da27` baseline pin behind four portability failures**

- **Question:** Should the legacy-path criterion `REQ-P3-08` be redefined, or
  the pin updated, so the four P2–P5 zero-adapter failures clear?
- **Why it matters:** Four of the five remaining harness failures are this one
  predicate. It is **not** caused by adapters — the predicate emits identical
  paths with adapters present or deleted.
- **Authoritative sources:** `REQ-P3-08` (APPROVED, VERIFIED; criterion "git
  diff against c11da27 over legacy paths is empty"); `validate-p2.sh:194`,
  `validate-p3.sh:297`, `validate-p4.sh:482`, `validate-p5.py:279-286`.
- **Current evidence:** `git diff --name-only c11da27 -- ...` yields
  `.github/workflows/sps-ci.yml` plus three `.sps/tools/*.sh`. Moving the pin
  alone would **not** fix it, because the `.sh` files still match the pathspec.
- **Options:** (a) narrow the pathspec to exclude legitimately-migrated files;
  (b) move the baseline to a later commit; (c) formally accept the four
  failures as known-and-expected; (d) leave unresolved.
- **Recommended:** (a) with the exact pathspec stated in the decision record,
  because it preserves the *intent* (legacy paths untouched) rather than
  weakening it.
- **Risk if deferred:** the harness cannot distinguish a real legacy
  regression from these four permanent failures — alarm fatigue.
- **Exact action requiring approval:** editing the pin pathspec in four files.
- **Safe work that can continue:** all local verification.

---

**DP-3 — Close the attribution self-approval fail-open**

- **Question:** Should `approval_is_user_attributable()` reject an approval
  whose decider asserts self-approval, while preserving the surname "Self"?
- **Why it matters:** `decided_by: "Self (self-approved)"` is currently
  accepted. No record uses it today, so this is latent, not active.
- **Authoritative sources:** `attribution.py:144-162`; the 17-token policy
  (DEC-0027 deliberately excludes `self`); the pinning test
  `test_attribution_policy.py:407-424`, which asserts acceptance is
  **by design** — so closing it is a governance change, not just a bug fix.
- **Current evidence:** verified across 11 inputs. `User`, `Self`,
  `Jane Self`, `Self (self-approved)` accepted; `Antigravity`, `Claude`, `the
  model`, `Assistant`, `AI` rejected. `p17/__main__.py:379-384` — the execution
  gate — never consults the predicate at all.
- **Options:** (a) add a narrow self-approval-phrase rule and re-scope the
  pinning test; (b) make `p17/__main__.py` consult the predicate; (c) invert to
  an allowlist (`decided_by == "User"`); (d) accept as-is.
- **Recommended:** (a) + (b). Do **not** add `self` to the token list — that
  would reject `Jane Self` and violate DEC-0027.
- **Risk if deferred:** an agent-authored approval could be recorded as User
  approval.
- **Exact action requiring approval:** editing `attribution.py`, or
  `p17/__main__.py`, or the pinning test.
- **Safe work that can continue:** everything else.

---

**DP-4 — Stale `note` in `ROADMAP-P3-DECISIONS.json`**

- **Question:** Should the `note` be corrected?
- **Why it matters:** The note's tail reads "…remains PENDING" while
  `completion.state = APPROVED` with `decided_by: User` and
  `decided_on: 2026-10-05` in the same record.
- **Current evidence:** verified present this round. `git log -S` shows the
  note was never modified after the approval commit — stale prose, not a
  contradiction of the approval.
- **Options:** (a) correct the note; (b) leave it (it self-identifies the
  completion block as authoritative); (c) supersede the record.
- **Recommended:** (a), purely cosmetic and provenance-preserving.
- **Risk if deferred:** a future reader may believe P3 is unapproved.
- **Exact action requiring approval:** editing a decision instrument.
- **Safe work that can continue:** everything else.

---

**DP-5 — `DEC-0001 KEEP_LOCAL_ONLY` versus actual remote history**

- **Question:** How should the conflict be disposed of?
- **Why it matters:** `DEC-0001` (APPROVED/User/2026-10-03) says
  "Do not configure a remote now", but `origin` exists and local push logs
  record successful pushes.
- **Current evidence:** inspected **locally only**; the remote was never
  contacted. `DEC-0002` additionally defers git-identity replacement on the
  premise that the repo is local-only — that premise is now false.
- **Options:** (A) supersede and ratify remote usage; (B) record the pushes as
  an incident and reaffirm local-only; (C) another documented disposition.
- **Recommended:** (A) if the pushes were intentional, else (B) — but this is
  the User's determination, not mine.
- **Risk if deferred:** decision records describe a state the repository does
  not satisfy.
- **Exact action requiring approval:** any new or amended decision record.
- **Safe work that can continue:** all local-only work.

---

**DP-6 — Disposition of 331 untracked tests**

- **Question:** Keep them untracked, commit a subset, or give them their own
  release scope?
- **Why it matters:** `test_p10_runtime_gate.py` (282),
  `test_content_slots.py` (25), `test_layout_registry.py` (24) exist in no
  commit and cannot run in CI, which derives modules from `git ls-files`.
- **Options:** (A) keep untracked and record as unwired; (B) authorize a
  separate future commit; (C) define a separate release scope for P10/frontend.
- **Recommended:** (A) now, (C) as the durable answer.
- **Risk if deferred:** 331 tests provide zero protection to any clone or CI
  run.
- **Exact action requiring approval:** staging or committing those files.
- **Safe work that can continue:** all local verification.

---

**DP-7 — CI scope: per-module guard, and running the validators**

- **Question:** Should CI gain a per-module presence guard and execute the
  protected validators?
- **Why it matters:** `MIN_TESTS=500` vs 558 leaves 24 of 26 modules deletable
  invisibly (measured; the two largest are caught). Separately, **no validator
  runs in CI at all**, so DP-1's defects cannot be caught even if triggered.
- **Authoritative sources:** `.github/workflows/sps-ci.yml` (protected).
- **Options:** (a) compare the discovered module set against `git ls-files`;
  (b) raise `MIN_TESTS` per module; (c) add validator steps; (d) no change.
- **Recommended:** (a) + (c).
- **Risk if deferred:** a module can silently vanish and the false-PASS
  defects remain unreachable by CI.
- **Exact action requiring approval:** editing the workflow.
- **Safe work that can continue:** local simulation.

---

**DP-8 — Git identity and commit provenance**

- **Question:** Should the placeholder identity be replaced?
- **Why it matters:** most commits use a placeholder author; identity is
  entangled with DP-5.
- **Options:** (a) replace going forward; (b) replace and rewrite history
  (**not recommended** — rewriting history is prohibited here); (c) leave.
- **Recommended:** (a) only, and only after DP-5.
- **Exact action requiring approval:** changing repo or global git config.

---

**DP-9 — Durability: the four verified fixes are worktree-only**

- **Question:** Do you authorize committing the verified changes?
- **Why it matters:** a clean clone of `cdcbca8` still reports
  `PENDING_USER_APPROVAL` and leaks the sentinel. **CI and every clone see none
  of the work.** This is the same structural class as the 331 untracked tests.
- **Current evidence:** verified this round by cloning `cdcbca8` and grepping
  for each fix — all absent.
- **Worktree-only changes:** `sps2/RESUME.md`,
  `sps2/tests/test_p17_security.py` (+49/−1),
  `sps2/tests/test_p17_pinning.py` (+73/−7),
  `sps2/tools/validate-p7-readiness.py` (+8/−1),
  `sps2/tests/test_p7_zero_adapter_readiness.py` (new).
- **Options:** (a) authorize a single commit of exactly these five paths;
  (b) leave uncommitted; (c) authorize a different grouping.
- **Recommended:** (a), as one narrow commit with the defect IDs in the
  message. The four **pre-existing** user edits must **not** be included.
- **Risk if deferred:** every fix is invisible to CI and to any collaborator.
- **Exact action requiring approval:** `git add` + `git commit` on those paths.
- **Safe work that can continue:** everything else.

---

**DP-10 — Authorization traceability for prior CI / validator migration**

- **Question:** What is the authorization instrument for the CI job and the
  validator migration already committed?
- **Why it matters:** Gate G14 (traceability) fails. I searched
  `sps2/decisions/`, `sps2/requirements/`, `sps2/governance/`, and
  `.sps/decisions/` for any CI/CD authorization reference: **zero hits**.
- **Options:** (a) record a retrospective decision naming the instrument;
  (b) identify an existing instrument I could not locate; (c) accept the gap.
- **Recommended:** (b) first — the instrument may exist outside those
  directories and I did not search the entire tree exhaustively.
- **Risk if deferred:** committed infrastructure changes have no traceable
  authority.
- **Exact action requiring approval:** creating a decision record — which I
  must not do on my own behalf.
- **Safe work that can continue:** everything else.

---

## 26. What is required before I can safely use SPS2?

**What can be used safely now?**

The tracked-source test corpus is green and reproducible: 558 tests in a clean
clone of `cdcbca8`, 562 in the worktree, 0 failures, 1 deterministic skip, order
independent. Running the unit suite is safe and mutates nothing.

**What remains blocked?**

Any reliance on the P2 or `validate-sps2.sh` verdicts as a *security* signal,
because a dead checker fabricates PASSes. Full release readiness, because the
portability harness is red, no validator runs in CI, and CI has never actually
executed a single run.

**What commands should be run first?**

The corpus command in §22. Not the shell validators in the live tree — they
mutate evidence and registry state.

**What must not be activated?**

The P10 runtime gate. It remains unapproved and unwired, and `p17/__main__.py`
executes on a self-asserted role field without consulting the attribution
predicate.

**What requires User approval?**

DP-1 through DP-10 in the accompanying decision packet. Nothing in that list
can be resolved by an agent.

**What would constitute sufficient evidence for readiness?**

A real, observed CI run executing the validators; the false-PASS defects
closed; the portability harness green or every failure formally accepted by the
User; and the self-approval path closed.

---

## 27. Operator Quick Start

Preconditions: run from the repository root, Python 3, no network needed.
These commands are verified safe — they read state and run tests only, and
write nothing into the repository.

```bash
cd /Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main

# 1. Confirm you are on the expected branch and HEAD.
git rev-parse --abbrev-ref HEAD   # build/roadmap-p3-completion
git rev-parse HEAD                # cdcbca83679844ea66196f25773f42d9b64569ec

# 2. Run the tracked test corpus (safe, read-only, ~60s).
MODS=$(git ls-files 'test_*.py' '**/test_*.py' | grep -E '^(sps2|domain)/' \
       | sed 's/\.py$//;s#/#.#g' | sort)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $MODS

# 3. Check P7 readiness (safe, read-only).
python3 sps2/tools/validate-p7-readiness.py

# 4. Check the portability harness (safe: rehearses in its own temp copy).
PYTHONDONTWRITEBYTECODE=1 python3 sps2/tools/test-portability.py
```

**Do NOT run** `sps2/tools/validate-p2.sh`, `validate-sps2.sh`, `validate-p3.sh`,
`validate-p4.sh`, or `validate-p5.py` directly against this working tree: they
mutate evidence and registry state. Use a disposable copy, as this mission did.

`unittest discover` is unusable in this repository — it reports zero tests and
exits 5. Use an explicit module list, as above.
