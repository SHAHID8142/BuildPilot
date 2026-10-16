# SPS2 Final Authorized Execution & Release-Readiness — 2026-10-16 13:52

**Mission:** Final Authorized Execution & Release-Readiness
**Repository:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`
**Branch:** `build/roadmap-p3-completion`
**HEAD:** `cdcbca83679844ea66196f25773f42d9b64569ec` (`cdcbca8`) — unchanged
**Report:** `reports/SPS2-FINAL-AUTHORIZED-EXECUTION-20261016-135200.md`

---

## 1. Executive verdict

# `NOT_READY`

**No repository file was modified.** Every deliverable is a reviewed, applyable
artifact in `/tmp`, because the exact authorizations required were not present.

### What this round produced

Three patches, each verified against pristine `cdcbca8`, plus a draft governance
record — all ready to apply the moment authorization exists:

| Artifact | Bytes | sha256[:16] | Applies to `cdcbca8` |
|---|---|---|---|
| `P17-GATE-EXACT-USER.patch` | 739 | `43f888730ea1b020` | clean |
| `test_p17_execution_gate_attribution.py` | 9332 | `87ac91c3aa851ba4` | new file |
| `DP1-CONSOLIDATED.patch` | 10136 | `37830a650f4d8dcc` | clean |
| `DP7-CI-MODULE-GUARD.patch` | 3231 | `69dcc5cca94b3518` | clean |
| `DECISION-DEC-0031.json` (draft) | 18871 | parses OK | untracked |

### The three decisive findings

**1. The P17 gate hole is real, and I proved causality twice.**
Baseline gate: **22 hostile `decided_by` values all passed**. My first fix
(`.strip()`) closed 18 of 22 — an independent adversarial reviewer caught that my
own test demanded all 22 be rejected, making the packet self-contradictory. I had
independently reached the same conclusion and switched to **exact equality**,
which closes all 22 with zero false-rejections and no exception on any
non-string type. Final proof: unpatched → `FAILED (failures=22)`; patched →
`OK`.

**2. The proposed CI guard had a self-reference blind spot — and I found it by
testing rather than assuming.** CI derives its module list from `git ls-files` at
run time, so **deleting a module removes it from both the expected set and
execution**. A "did every discovered module run?" check is therefore vacuously
true. Measured: deleting a 25-test module leaves `ran=535` — the old threshold
**passes**, and my first per-module guard also **passes**. The manifest-based
guard correctly **fails**. This corrects the recommendation carried in the
previous two reports.

**3. The CI/migration authorization has no verbatim User text.** An independent
audit established that the Phase 3 report's blockquotes are agent-authored; it
never quotes the User, unlike `DEC-0025`–`DEC-0028` which all carry verbatim
authorization. A durable record is therefore draftable as a *transcription with a
stated provenance limitation*, but it cannot honestly assert a quoted basis.

---

## 2. Initial and final Git state

| Property | Initial | Final | Changed |
|---|---|---|---|
| Branch | `build/roadmap-p3-completion` | same | no |
| HEAD | `cdcbca83679844ea66196f25773f42d9b64569ec` | same | **no** |
| Staged | 0 | 0 | no |
| Stash | 0 | 0 | no |
| Modified tracked | 11 | 11 | no |
| Untracked (file-level) | 111 | 112 | +1 (this report only) |
| Deletions | 0 | 0 | no |
| Reports | 9 | 10 | +1 (this report); none overwritten |
| Remote contacted | no | no | no |

**Preservation audit (full 64-char SHA-256, corrected):** all **7 protected files
INTACT** (`validate-p2.sh`, `validate-sps2.sh`, `validate-p3.sh`,
`validate-p4.sh`, `attribution_policy.json`, `.sps/tools/validate-governance.sh`,
`attribution.py`) and all **11 pre-existing modified tracked files byte-identical**.
The untracked delta is exactly one file — this report. Nothing was removed.

*Audit caveat, recorded for honesty:* my first audit pass reported all 18 files as
CHANGED. That was a **bug in my audit script**, not repository drift — I compared
the baseline's full 64-character digests against truncated 16-character values.
I re-ran the comparison at matching precision before accepting the result. The
`reports/` count difference (9→10) is likewise just this round's addition.

**Independent integrity proof:** `sps2/tests/test_p5.py` in the real repository
hashes `e78fa5d2a3c2c7e7`, byte-identical to pristine `cdcbca8`. During CI-guard
testing I accidentally damaged that file **inside a disposable copy** and
restored it from the pristine clone — the real tree was never touched. This is
recorded because it is exactly the class of accident the disposable-copy rule
exists to contain.

---

## 3. Authorization evidence

### 3.1 The gate change is NOT authorized

| Instrument | Text | Effect |
|---|---|---|
| `P17-DECISIONS.json` **D-P17-3** | *"NOT delegated, and therefore still User decisions: approval gates (GATE-P17-2, GATE-P17-3) … and any change to an approved requirement, schema, decision record, or protected file."* | approval gates reserved to User |
| `ATTRIBUTION-POLICY-DECISIONS.json` → `explicitly_not_approved_by_this_record` | *"Any P10 inventory approval state change, P10 Phase B work, or **P17 `decided_by` execution check**"* | that record **disclaims** this exact change |
| same record → `non_goals` | *"No P10 inventory approval state, no **P17 execution check**, and no CI configuration is changed."* | disclaimed again |

No new approval exists. Newest recorded approval remains **2026-10-15**
(`DEC-0025`–`DEC-0028`).

### 3.2 Requirement analysis — defect fix, not a new control

`P17-REQUIREMENTS.json:469-478`, GATE-P17-3 verbatim:

- `requirements`: *"The specific task, its ordered plan, and its acceptance command are presented"*, *"Explicit User approval of that specific task execution (approval-packet convention)"*
- `approver`: *"User"*
- `evidence_required`: *"approval record in the task record (approval.state = APPROVED, decided_by_role = USER)"*

**GATE-P17-3 names only `state` and `decided_by_role` — it never mentions
`decided_by`.** So this patch is *not* literally required by GATE-P17-3's
evidence clause. The on-point authority is **SEC-P17-10**, which forbids
*"bypasses around existing approval gates"* and requires *"negative test output
for allowlist enforcement and gate bypass."* Because both accepted fields are
self-asserted in an unsigned sidecar, the pre-patch gate **is** bypassable.
Framing this as a **SEC-P17-10 security defect fix** is the strongest available
justification — and it still needs a User decision, because it tightens an
approval gate.

`ATTRIBUTION-POLICY-DECISIONS.json` also cannot authorize it, and
`attribution.py` cannot implement it — see §7.3.

### 3.3 What the mission's own wording does and does not grant

The mission says to implement the gate change *"if the user has explicitly
authorized the exact change"*, and to *"stop before applying it"* if
authorization is missing. No such authorization is present in the repository, and
the mission repeatedly warns *"Do not confuse a recommended action with
permission to perform it."* I therefore prepared and stopped.

---

## 4. Changes applied

**None.** No repository file was created, modified, deleted, or staged.

All work occurred under `/tmp` (`/tmp/r5-p17`, `/tmp/r5-verify`, `/tmp/r5-ci`,
`/tmp/r5-apply`, `/tmp/r5-dp1`, `/tmp/dp10-draft`).

---

## 5. Changes prepared but not applied

| ID | Artifact | Scope | Blocker |
|---|---|---|---|
| **A** | `P17-GATE-EXACT-USER.patch` | 1 condition in `sps2/p17/__main__.py:381` | new User decision (§3.1) |
| **A2** | `test_p17_execution_gate_attribution.py` | new test module (5 tests) | must ship with A; untracked so CI cannot see it |
| **B** | `DP1-CONSOLIDATED.patch` | 4 protected validators + P4 widening | protected files |
| **C** | `DP7-CI-MODULE-GUARD.patch` | workflow + new manifest file | protected workflow |
| **D** | `DECISION-DEC-0031.json` | new decision record | committing prohibited |
| **E** | DP-9 five-file commit | 5 files | no instrument covers them |

---

## 6. Test results by repository state

| # | State | Modules | Ran | Failed | Skipped | Exit |
|---|---|---|---|---|---|---|
| 1 | worktree, tracked | 26 | **562** | 0 | 1 | 0 |
| 2 | worktree, tracked, reverse | 26 | **562** | 0 | 1 | 0 |
| 3 | full worktree incl. untracked | 30 | **896** | 0 | 1 | 0 |
| 4 | clean clone of HEAD | 26 | **558** | 0 | 1 | 0 |
| 5 | clone + P1..P4 (validators not unittest modules) | 26 | **558** | 0 | 1 | 0 |
| 6 | portability harness | — | 34P/5F/14C | 5 | — | 1 |
| 7 | validator negative controls | — | §8 | — | — | — |
| 8 | CI guard negative controls | — | §9 | — | — | — |
| 9 | P17 gate negative controls | — | §7 | — | — | — |

**P17 gate, patched vs unpatched (the causality pair):**

| Tree | Result |
|---|---|
| patched (exact equality) | `Ran 567 tests … OK (skipped=1)` |
| unpatched (causality) | `Ran 5 tests … FAILED (failures=22)` |

Skips parsed from stdout, never inferred. `unittest discover` remains unusable
in this repository. Full commands in §15.

---

## 7. P17 execution-gate findings

### 7.1 The defect, reproduced

`sps2/p17/__main__.py:378-384` (baseline):

```python
approval = _approval_sidecar(task_id, root)
if not approval or approval.get("state") != "APPROVED" \
        or approval.get("decided_by_role") != "USER":
```

`cmd_approve` writes `decided_by` at `:281` as the hardcoded literal `"User"` —
but the gate **never reads it**. Both checked fields are written by the
requesting party into an unsigned sidecar. **22 hostile values all passed the
gate**, including the original attack `"Self (self-approved)"` and the empty
string.

### 7.2 The fix, hardened

```python
if not approval or approval.get("state") != "APPROVED" \
        or approval.get("decided_by_role") != "USER" \
        or approval.get("decided_by") != "User":
```

**Exact equality, deliberately without `.strip()`.** My first draft used
`(approval.get("decided_by") or "").strip() != "User"` and I found two defects in
it by adversarial self-testing:

| Draft defect | Evidence | Resolution |
|---|---|---|
| **Non-string truthy values raise** | `1`, `True`, `["User"]` → `AttributeError`, mislabeled `EXIT_TASK_FAILED` via the catch-all at `:1031` (the exact hazard `p10_runtime_gate.py:1106-1112` documents) | exact `!=` compares safely: end-to-end all of `1`, `True`, `["User"]`, `None` → clean `EXIT_REJECTED`, nothing spawned |
| **`.strip()` widens the sentinel** | `"User "`, `" User"`, `"\xa0User"`, `"User\n"`, `"\u3000User"`, `"\u2028User"` became indistinguishable from the real sentinel | all now rejected |

An independent reviewer simultaneously reached the same conclusion, noting
`.strip()` *"is the WRONG semantic for a security check"* — the exact `"User"`
sentinel is what is at stake. Verified: `"User"` alone is accepted; all 22
hostile values including 6 whitespace/Unicode near-misses are rejected.

### 7.3 Why `attribution.py` cannot fix this

`approval_is_user_attributable()` returns **True for `"Self (self-approved)"`** —
the original attack — because `DEC-0027` removed `self` from the token set. It is
strictly weaker than exact equality here. This matches `DEC-0027`'s own
hierarchy: *"the token denylist is a heuristic, and the binding User-attribution
checks are the exact-equality `'User'` checks."* Importing the heuristic into the
gate would invert that order.

### 7.4 Honest limitation

This change **does not authenticate a human**. The sidecar is unsigned,
self-asserted free text (UQ-ATT-2 remains open), and the gate is not
schema-validated. The change removes a bypass; it does not establish identity.

### 7.5 Negative-control matrix

| Input | Baseline | Patched |
|---|---|---|
| `"User"` | accept | **accept** |
| `"Self (self-approved)"`, `"Self"`, `"self"`, `"user"`, `"USER"`, `"the user"`, `"Assistant"`, `"Claude"`, `""` | accept | **reject** |
| `"User "`, `" User"`, `"\xa0User"`, `"User\n"`, `"\u3000User"`, `"\u2028User"` | accept | **reject** |
| `"User\u200b"`, `"\uff35ser"` | reject | reject |
| `0`, `1`, `True`, `None`, `[]`, `{}`, `["User"]` | accept / crash | **reject, no exception** |
| role `AGENT` | reject | reject |
| state `PENDING` | reject | reject |
| no sidecar | reject | reject |

All 22 baseline-bypassing values now rejected; every legitimate flow preserved.

### 7.6 Regression

Only writer of the sidecar is `cmd_approve:281` (literal `"User"`). Full tracked
suite: **567 tests, 0 failures, exit 0** — 562 existing plus 5 new. Reviewers
independently confirmed 558/OK patched and baseline.

---

## 8. Validator negative-control results

Reviewed by an independent adversarial reviewer; I re-verified the central claims.

### 8.1 Hashes and application

| Patch | sha256[:16] | Claimed in mission | Match |
|---|---|---|---|
| `P1-validate-p2-exit-status` | `247ef4f055a6cc56` | `247ef4f055a6cc56` | yes |
| `P2-validate-sps2-exit-status` | `0a90a2cefcca6be1` | `0a90a2cefcca6be1` | yes |
| `P3-validate-p3-exit-status` | `3a334297cc716416` | `3a334297cc716416` | yes |
| `P4-validate-p4-negative-controls` | `c9665a4cf08f6fff` | `c9665a4cf08f6fff` | yes |

All four apply cleanly. The **subshell trap is avoided**: every capture is
`cmd 2>&1); rc=$?` on the same shell level.

### 8.2 Regression — identical

| Validator | Unpatched | Patched |
|---|---|---|
| `validate-p2.sh` | 68 P / 1 F | **68 P / 1 F** |
| `validate-sps2.sh` | 79 P / 1 F | **79 P / 1 F** |
| `validate-p3.sh` | 67 P / 1 F | **67 P / 1 F** |
| `validate-p4.sh` | 57 P / 3 F | **57 P / 3 F** |

The pre-existing `c11da27` legacy-path failure appears in both, confirming it is
not patch-induced.

### 8.3 Crash-state controls (consolidated patch, `validate-p2.sh`)

| State | Original | Patched |
|---|---|---|
| clean | 68 P / 1 F | 68 P / 1 F |
| crashing checker | 47 P / 22 F | **39 P / 30 F** |
| silent non-zero (exit 3) | 47 P / 22 F | **39 P / 30 F** |

**8 fabricated PASSes eliminated** per crash state, with explicit
`FAIL sources: checker exited N - control could not run` diagnostics.

### 8.4 The P4 widening

The mission-supplied P4 patch contains
`'^(PROMOTED|NOT_PROMOTED)[[:space:]]'`, which **rejects a bare `PROMOTED`** —
and `check_p4.py:39` prints exactly that:

```
printf 'PROMOTED\n' | grep -qE '^(PROMOTED|NOT_PROMOTED)[[:space:]]'   -> no match (BUG)
printf 'PROMOTED\n' | grep -qE '^(PROMOTED|NOT_PROMOTED)([[:space:]]|$)' -> match
```

I applied the widening (2 occurrences) and verified both forms match. The bug is
**latent but real**: it requires zero blocking gates, so `POSCTRL-D/E` inputs,
which yield `NOT_PROMOTED\tblocking=…`, are unaffected today.

---

## 9. CI integrity and validator coverage

### 9.1 The blind spot — this round's most consequential finding

CI derives `MODULES` from `git ls-files` **at run time**. Deleting a module
therefore removes it from *both* the expected list and execution, so a
"did every discovered module run?" guard is **vacuously true**. Measured:

| Case | Ran | Old `MIN_TESTS=500` | Naive per-module guard | **Manifest guard** |
|---|---|---|---|---|
| healthy (26 modules) | 558 | PASS | PASS | **PASS** |
| small module deleted (25 tests) | 535 | **PASS (wrong)** | **PASS (wrong)** | **FAIL** |
| large module deleted (68 tests) | 490 | FAIL | **PASS (wrong)** | **FAIL** |

The naive guard is **strictly worse than the threshold** for the large-module
case. The fix is a **committed manifest** (`.github/expected-test-modules.txt`,
26 entries) compared against the discovered set.

### 9.2 A second trap: `-v` is required

CI runs `python3 -m unittest "${MODULES[@]}"` **without `-v`**, and
`unittest -v` writes per-test lines to **stderr** (99,373 bytes) not stdout
(1,227 bytes). Without `-v` the guard would flag **every module** as missing. The
patch adds `-v` and merges streams.

### 9.3 A third trap: shell variable size

A 100 KB+ captured variable is unreliable under macOS bash 3.2 — my first
simulation silently truncated and produced 18 phantom "0 tests" errors. The
patch therefore writes the run to a **temp file** and greps the file.

### 9.4 Empty-discovery and import-failure

- The workflow **already** guards zero modules (`:134-135`, `"refusing to report success"`).
- An import/syntax error aborts the run: `rc=1`, `Ran` absent, `SyntaxError`
  present → `MIN_TESTS` catches it.

### 9.5 Validator coverage

All four validators are **`mktemp -d`-based and read-only** with respect to the
repository — verified by hashing the full `git status` before and after a run
(identical), so no disposable checkout is needed. **No validator runs in CI
today, and no GitHub Actions run has ever been observed.**

---

## 10. D-17 registration status

| Check | Result |
|---|---|
| Fix present at `validate-p7-readiness.py:174` | yes |
| Test present | yes |
| Passes against fixed validator | `Ran 3 tests … OK` |
| Revert predicate → test fails | **`FAILED (failures=1)`** |
| Registered in any runner | **no** — absent from `CORE_VALIDATORS`, absent from `validate-sps2.sh`, and **untracked**, so CI's `git ls-files` cannot see it |

The minimal registration is one line in `portability.py`'s `CORE_VALIDATORS`,
whose precedent is `("P5 unit tests", ["python3", "sps2/tests/test_p5.py"], "OK")`.
`validate-sps2.sh` is protected. **The regression is real but unenforced.**

---

## 11. Durable authorization status

Verified independently: the mission's claims hold exactly. `238c9e4` is an
ancestor of HEAD; `cdcbca8` **is** HEAD; Decision 1's *"exactly the 6 authorized
files"* matches `6 files changed, 768 insertions(+), 39 deletions(-)`; Decision
4's scope is `+98/−0`. **In a clone, traceability is zero**: `reports/` has 0
tracked files, the Phase 3 report is absent, and 0 decision files name
`cdcbca8`.

**Critical evidentiary limitation:** the Phase 3 report contains **no verbatim
User quotation**. Its only blockquotes (`:64-67`) are agent-authored. By
contrast `DEC-0025`'s `approval.basis` carries the User's words verbatim. A draft
record (`DEC-0031`) was prepared that transcribes the authorization and states
this limitation plainly rather than fabricating a quote. Trade-offs:

| Option | Governance-native | Blast radius | Resolves DP-10 |
|---|---|---|---|
| (a) commit `reports/` (9 files) | no — narrative, no `decision_id` | 9 files, 7 unrelated | partial |
| **(b) canonical record (1 file)** | **yes — schema-validated** | **1 new file** | **direct** |

**Recommendation: (b).** `git check-ignore` finds no rule for `reports/`, so its
untracked status is an **omission, not policy** — but committing 9 narrative
files would sweep in claims the User never separately approved.

---

## 12. Status of DP-1 through DP-11

| ID | Evidence | Auth required | Independent | Safe meanwhile |
|---|---|---|---|---|
| **DP-1** | 8 fabricated PASSes/state; clean counts identical; P4 widening needed | User (protected) | yes | done in `/tmp` |
| **DP-2** | `DEC-0028` ACTIVE decides: retain. Failures are **correct reports** | none — settled | — | preserve red |
| **DP-3** | Gate bypassable by 22 values; exact-`User` closes all | **User** (D-P17-3) | yes | done in `/tmp` |
| **DP-4** | Additive, `state_changed:false`, no instrument | User scope ruling | yes | leave |
| **DP-5** | `origin` exists; 4 push reflogs; `DEC-0001` needs a new instruction | User | yes | leave |
| **DP-6** | Revert→fail proven; registered nowhere | after DP-9 | yes | prepared |
| **DP-7** | Manifest guard proven on 6 cases | User (protected) | yes | done in `/tmp` |
| **DP-8** | 136/138 commits placeholder; `DEC-0002` premise false | **after DP-5** | no | leave |
| **DP-9** | Clone lacks all 5 fixes; still `PENDING_USER_APPROVAL` | **User** | yes | leave |
| **DP-10** | 0 tracked reports; clone has zero traceability | User | yes | draft ready |
| **DP-11** | §4–§9 render as code; insert one fence after `:100` | User (protected) | yes | leave |

**DP-2 honoured:** no pathspec narrowed, no baseline moved, no P3/P4 control
weakened, `REQ-P3-08` untouched, and the five failures recorded as **correct
reports** — not reclassified as an engineering regression.

---

## 13. Remaining blockers

| # | Blocker | Severity | Class |
|---|---|---|---|
| 1 | P17 gate bypassable by self-attributed approval | Critical | Defect, patch ready |
| 2 | No validator in CI; no CI run ever observed | Critical | Missing evidence |
| 3 | P2/SPS2 fabricate PASS on a dead checker | High | Defect, patch ready |
| 4 | All five verified fixes worktree-only | High | Worktree-only |
| 5 | Portability red 34/5 | High | **Governance-settled (retain)** |
| 6 | CI misses a deleted module (manifest needed) | High | Defect, patch ready |
| 7 | D-17 test unenforced | Medium | Defect, needs DP-9 |
| 8 | `DEC-0001` contradicted by remote | Medium | Governance |
| 9 | CI authorization untraceable in a clone | Medium | Missing evidence |
| 10 | P5 annotations unauthorized | Low | Governance |
| 11 | `GOVERNANCE.md` §4–§9 render as code | Low | Mechanical, protected |

---

## 14. Exact user decisions still required

**DEC-A — P17 gate, exact `decided_by == "User"`.** *Evidence:* 22 hostile values
bypass the gate today; exact equality closes all with zero false-rejections and
no exception on any type; causality proven. *Framing:* a **SEC-P17-10 bypass fix**
(the record explicitly disclaims *"P17 `decided_by` execution check"*, so it
needs its own decision). *Cannot be done by* `attribution.py`, which accepts the
original attack. *Does not authenticate a human* (UQ-ATT-2 open).

**DEC-B — commit the five verified fixes (DP-9).** *Requested:* one commit of
`sps2/RESUME.md`, `sps2/tests/test_p17_security.py`,
`sps2/tests/test_p17_pinning.py`, `sps2/tools/validate-p7-readiness.py`,
`sps2/tests/test_p7_zero_adapter_readiness.py`. The 7 other modified files and
all user edits must be excluded.

**DEC-C — the four validator patches plus the P4 widening.** *Requested:*
`DP1-CONSOLIDATED.patch`, which includes
`'^(PROMOTED|NOT_PROMOTED)([[:space:]]|$)'`.

**DEC-D — the CI manifest guard.** *Requested:* `DP7-CI-MODULE-GUARD.patch` plus
the committed 26-entry manifest. *Note:* without the manifest, the guard is
**worse than the current threshold** for large-module deletion.

**DEC-E — durable authorization record.** *Requested:* choose (a) commit
`reports/`, or **(b) create `DEC-0031`**. *Constraint:* no verbatim User quote
exists, so the record must state that limitation rather than invent one.

**DEC-F — D-17 registration (DP-6)**, after DEC-B.

**Lower priority:** DP-4 scope ruling · DP-5 remote decision · DP-8 identity
(after DP-5) · DP-11 fence. **DP-2 needs no decision** — `DEC-0028` already
settled it.

---

## 15. Reproducible commands

```bash
# tracked corpus
MODS=$(git ls-files 'test_*.py' '**/test_*.py' | grep -E '^(sps2|domain)/' \
       | sed 's/\.py$//;s#/#.#g' | sort)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $MODS
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $(echo "$MODS" | sort -r)

# P17 gate causality (in a disposable copy)
cp /tmp/r5-d17/tree/sps2/p17/__main__.py /tmp/keep.py
# revert only the decided_by condition, then:
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_p17_execution_gate_attribution
# expect FAILED (failures=22); restore -> OK

# validators are READ-ONLY (mktemp-based) and safe on the real tree:
bash sps2/tools/validate-p2.sh
bash sps2/tools/validate-p4.sh

# apply the prepared patches to a pristine clone
git clone -q --no-hardlinks . /tmp/apply && cd /tmp/apply && git checkout -q cdcbca8
git apply --check /tmp/r5-dp1/DP1-CONSOLIDATED.patch
git apply --check /tmp/r5-dp1/DP7-CI-MODULE-GUARD.patch
git apply --check /tmp/r5-dp1/P17-GATE-EXACT-USER.patch

# faithful disposable copy (NEVER git archive)
python3 - <<'PY'
import sys, os, importlib.util
sys.path.insert(0, os.path.join(os.getcwd(), "sps2", "tools"))
spec = importlib.util.spec_from_file_location("PT", "sps2/tools/portability.py")
PT = importlib.util.module_from_spec(spec); spec.loader.exec_module(PT)
PT.copy_tree(os.getcwd(), "/tmp/tree/tree")
PY
```

---

## 16. Limitations

- **No GitHub Actions run observed.** All CI results are local simulation.
- **Python 3.12 / Ubuntu unverified.** Local runs are macOS + Python 3.14.7.
- **`reports/` remains untracked**, so no authorization survives a clone.
- **UQ-ATT-2 open:** nothing establishes that `decided_by` is a real human. Every
  attribution control is a heuristic over self-asserted text; even exact
  equality only enforces a *sentinel*, not identity.
- **The P17 sidecar is not schema-validated**; the gate is the sole runtime control.
- **The manifest must be maintained.** A newly added module not in the manifest
  is invisible to the "absent" check (the "zero tests" check still covers it).
- **`bash 3.2` limitations** affect guard scripting; the patch uses temp files.
- **Two subagents used**; I independently re-verified their central claims,
  including finding that the P17 reviewer had tested my superseded `.strip()`
  draft — the shipped artifact uses exact equality, which closes the 4 residual
  failures it reported.
- **One accidental edit inside a disposable copy** (`test_p5.py`) was found and
  restored; the real tree was verified byte-identical to `cdcbca8`.

---

## 17. Machine-readable summary

```json
{
  "report": "SPS2-FINAL-AUTHORIZED-EXECUTION-20261016-135200",
  "verdict": "NOT_READY",
  "repository_files_modified": 0,
  "repository": {
    "branch": "build/roadmap-p3-completion",
    "head": "cdcbca83679844ea66196f25773f42d9b64569ec",
    "head_unchanged": true,
    "staged": 0, "stash": 0, "modified_tracked": 11,
    "untracked_file_level": 112, "deletions": 0,
    "remote_contacted": false, "reports_preserved": 10,
    "untracked_delta": ["reports/SPS2-FINAL-AUTHORIZED-EXECUTION-20261016-135200.md"],
    "preservation_audit": {
      "protected_files_intact": 7, "protected_files_changed": 0,
      "modified_tracked_identical": 11, "modified_tracked_changed": 0,
      "comparison_precision": "full 64-char sha256"
    },
    "integrity_probe": {"file": "sps2/tests/test_p5.py",
                        "sha256_16": "e78fa5d2a3c2c7e7",
                        "matches_pristine_cdcbca8": true}
  },
  "tests": {
    "worktree_tracked":          {"modules": 26, "ran": 562, "failed": 0, "skipped": 1, "exit": 0},
    "worktree_tracked_reversed": {"modules": 26, "ran": 562, "failed": 0, "skipped": 1, "exit": 0},
    "worktree_full":             {"modules": 30, "ran": 896, "failed": 0, "skipped": 1, "exit": 0},
    "clean_clone":               {"modules": 26, "ran": 558, "failed": 0, "skipped": 1, "exit": 0},
    "clone_plus_p1_p4":          {"modules": 26, "ran": 558, "failed": 0, "skipped": 1, "exit": 0},
    "p17_patched":               {"ran": 567, "failed": 0, "exit": 0},
    "order_dependent": false, "discover_usable": false
  },
  "portability": {"passed": 34, "failed": 5, "controls": 14, "exit": 1,
                  "disposition": "DEC-0028 ACTIVE: retain; failures are correct reports",
                  "engineering_action_available": false},
  "prepared_artifacts": {
    "P17-GATE-EXACT-USER.patch": {"bytes": 739, "sha256_16": "43f888730ea1b020", "applies_to_cdcbca8": true},
    "test_p17_execution_gate_attribution.py": {"bytes": 9332, "sha256_16": "87ac91c3aa851ba4"},
    "DP1-CONSOLIDATED.patch": {"bytes": 10136, "sha256_16": "37830a650f4d8dcc", "applies_to_cdcbca8": true},
    "DP7-CI-MODULE-GUARD.patch": {"bytes": 3231, "sha256_16": "69dcc5cca94b3518", "applies_to_cdcbca8": true},
    "DECISION-DEC-0031.json": {"bytes": 18871, "parses": true, "committed": false}
  },
  "p17_gate": {
    "baseline_bypassable_values": 22,
    "patched_closes": 22,
    "predicate": "approval.get('decided_by') != 'User'",
    "strip_used": false,
    "strip_rejected_reason": "widens accepted set and raises on non-string truthy values",
    "non_string_safe": true,
    "causality": {"unpatched": "FAILED (failures=22)", "patched": "OK"},
    "attribution_py_can_fix": false,
    "attribution_py_accepts_original_attack": true,
    "authenticates_human": false,
    "authorization": "REQUIRED",
    "requirements_framing": "SEC-P17-10 bypass fix; GATE-P17-3 evidence_required does not name decided_by"
  },
  "validator_patches": {
    "hashes_match_mission": true,
    "apply_clean": true,
    "subshell_trap_avoided": true,
    "clean_state_regression": "identical for all four",
    "fabricated_passes_eliminated_per_crash_state": 8,
    "p4_widening_required": true,
    "p4_widening": "'^(PROMOTED|NOT_PROMOTED)([[:space:]]|$)'",
    "p4_bare_promoted_reachable_today": false,
    "applied": false
  },
  "ci": {
    "validators_executed": 0, "gha_runs_observed": 0,
    "min_tests": 500,
    "naive_per_module_guard_insufficient": true,
    "naive_guard_blind_reason": "git ls-files shrinks with a deleted module",
    "manifest_guard_cases": {
      "healthy": "PASS", "small_module_deleted": "FAIL", "large_module_deleted": "FAIL",
      "import_error": "FAIL", "zero_discovered": "already guarded at workflow:134"
    },
    "small_module_deletion_old_guard": "PASS (wrong)",
    "verbose_flag_required": true,
    "temp_file_required_for_bash32": true,
    "manifest_entries": 26
  },
  "d17": {"fix_present": true, "test_present": true, "revert_makes_test_fail": true,
          "registered_in_runner": false, "tracked": false},
  "traceability": {
    "commit_238c9e4_verified": true, "commit_cdcbca8_verified": true,
    "decision1_scope_matches": true, "decision4_pure_insertion": true,
    "reports_tracked_files": 0, "phase3_report_present_in_clone": false,
    "verbatim_user_authorization_exists": false,
    "draft_record": "DEC-0031", "committed": false
  },
  "governance": {
    "new_approvals_found": 0, "new_approvals_invented": 0,
    "newest_approval": "2026-10-15",
    "dp2_settled_by": "DEC-0028 (ACTIVE)",
    "gate_change_disclaimed_by": "ATTRIBUTION-POLICY-DECISIONS explicitly_not_approved_by_this_record",
    "pending": ["DEC-0029","DEC-0030","DEC-7101","DEC-7102","DEC-7103","DEC-7104",
                "DEC-7110","OPEN-DECISION-ATTRIBUTION-TOKEN-SET"]
  },
  "user_decisions_required": ["DEC-A P17 gate exact User","DEC-B commit five fixes",
                              "DEC-C validator patches + P4 widening",
                              "DEC-D CI manifest guard","DEC-E durable authorization record",
                              "DEC-F D-17 registration"],
  "blockers_ranked": [
    {"rank":1,"item":"P17 gate bypassable by self-attributed approval","severity":"critical"},
    {"rank":2,"item":"no validator in CI, no CI run observed","severity":"critical"},
    {"rank":3,"item":"P2/SPS2 fabricate PASS on dead checker","severity":"high"},
    {"rank":4,"item":"five fixes worktree-only","severity":"high"},
    {"rank":5,"item":"portability red 34/5 (governance-settled)","severity":"high"},
    {"rank":6,"item":"CI misses deleted module","severity":"high"},
    {"rank":7,"item":"D-17 test unenforced","severity":"medium"},
    {"rank":8,"item":"DEC-0001 contradicted by remote","severity":"medium"},
    {"rank":9,"item":"CI authorization untraceable in clone","severity":"medium"},
    {"rank":10,"item":"P5 annotations unauthorized","severity":"low"},
    {"rank":11,"item":"GOVERNANCE.md sections render as code","severity":"low"}
  ]
}
```

---

## 18. Final release-readiness verdict

# `NOT_READY`

**Progress this round.** Three verified patches and a draft decision record now
exist, each checked against pristine `cdcbca8`. The P17 gate hole is proven and
closed by a patch with two independent causality demonstrations. The DP-1 patch
set is consolidated with the P4 widening and shows identical clean-state counts.
The CI guard was found to be **insufficient as previously specified** — a
self-reference blind spot made it worse than the threshold for large-module
deletion — and replaced with a manifest-based design proven across six cases.

**Why the verdict cannot move.** Five conditions remain unmet, and each is a
genuine approval boundary, not an un-attempted task:

1. **The P17 gate still accepts a self-attributed approval** in the shipped code.
2. **No validator executes in CI, and no CI run has ever been observed.**
3. **The five verified fixes remain worktree-only.**
4. **CI cannot detect a deleted test module.**
5. **No authorization evidence survives a clone.**

**What I deliberately did not do.** I did not commit, push, contact the remote,
weaken a test, narrow a pathspec, or convert the red portability harness into a
green one. `DEC-0028` settles DP-2, and I recorded the five failures as **correct
reports** rather than engineering regressions. I did not treat the mission's own
recommendations as authorization, and I did not apply a patch that the
repository's records explicitly disclaim. Where my own first draft was wrong —
the `.strip()` predicate, and the naive CI guard — I say so in the open, with the
evidence that refuted it.
