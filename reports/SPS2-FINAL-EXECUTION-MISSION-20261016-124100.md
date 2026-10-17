# SPS2 Final Execution Mission — 2026-10-16 12:41

**Mission:** Authorized Fixes, Validator Safety, CI Protection, and Release Readiness
**Repository:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`
**Branch:** `build/roadmap-p3-completion`
**HEAD:** `cdcbca83679844ea66196f25773f42d9b64569ec` (`cdcbca8`)
**Report:** `reports/SPS2-FINAL-EXECUTION-MISSION-20261016-124100.md`

---

## 1. Executive summary

### Verdict: `NOT_READY`

**No file in the repository was modified this round.** That is the correct outcome,
not an omission. Two governance instruments that the previous report and I both
missed were located and verified — and they **block** rather than enable the two
highest-priority work items.

### The two decisive discoveries

**1. `DEC-0025` through `DEC-0028` are ACTIVE and User-approved on 2026-10-15.**
My prior report asserted the newest approval anywhere was 2026-10-08. **That was
wrong.** These four decisions live in a **tracked, unmodified** file
(`sps2/decisions/ATTRIBUTION-POLICY-DECISIONS.json`). Two of them decide
priorities outright:

- **`DEC-0028` decides DP-2 against changing anything.** Verbatim: *"The three
  P3/P4 legacy-protection controls are NOT modified. No pathspec is narrowed, no
  control is weakened… the residual failures reported by `validate-p3.sh` and
  `validate-p4.sh` are **correct reports** that legacy governance files were
  modified, and they **remain red until the underlying requirement question is
  settled by a separate User decision**."*
- **`DEC-0027` decides DP-3's premise.** It ratifies the removal of `self` from
  the token set and states the denylist *"is a heuristic"* while *"the binding
  User-attribution checks are the exact-equality `'User'` checks in the P3/P4
  validators."*

**2. The shell validators are read-only.** I had previously instructed that they
must never be run against the real tree. That was **overly conservative and
empirically wrong**: all four use `mktemp -d` and touch nothing in the
repository. Verified by hashing the full `git status` before and after a run —
byte-identical. This makes DP-7's validator coverage directly achievable in CI.

### What this means

DP-9 (commit) and DP-1 (protected validator patches) **remain unauthorized**.
No instrument covers the five files, and `DEC-0028` explicitly forbids narrowing
the pathspecs. Priority work that *was* permitted — patch review, negative
controls, CI guard design, portability root-causing, attribution analysis,
traceability verification — was completed and is evidenced below.

---

## 2. Initial and final Git state

| Property | Initial | Final | Changed |
|---|---|---|---|
| Branch | `build/roadmap-p3-completion` | same | no |
| HEAD | `cdcbca83679844ea66196f25773f42d9b64569ec` | same | **no** |
| Staged | 0 | 0 | no |
| Stash | 0 | 0 | no |
| Modified tracked | 11 | 11 | no |
| Untracked (file-level) | 110 | 110 | no |
| Deletions | 0 | 0 | no |
| `git fsck` errors | 0 | 0 | no |
| Remote contacted | no | no | no |
| Reports | 8 | 8 | no overwrite |

**Protected files, all INTACT:** `validate-p2.sh`, `validate-sps2.sh`,
`validate-p3.sh`, `validate-p4.sh`, `attribution_policy.json`,
`.sps/tools/validate-governance.sh`, `attribution.py`.

**All seven pre-existing non-DP-9 user edits byte-identical.** Baseline:
`/tmp/sps2-r3-baseline-1792127668/`.

---

## 3. Authorization audit

### 3.1 Correction to the prior report — the approval register was understated

| Date | Decisions | State | File tracked? |
|---|---|---|---|
| **2026-10-15** | **DEC-0025, DEC-0026, DEC-0027, DEC-0028** | **ACTIVE / APPROVED / `decided_by: User`** | **yes** (`320d3a5`) |
| 2026-10-14 | P10 decisions | approved | yes |
| 2026-10-13 | P10 delegated | approved | no |
| — | DEC-0029, DEC-0030 | `PENDING_USER_APPROVAL` | no |

The prior report's claim "newest `decided_on` is 2026-10-08; nothing dated after"
is **refuted**. I had searched `decided_on`/`approved_on` but the attribution
records use the key **`decided_at`**, which my walker did not cover. That is the
root cause of the miss, and it is recorded here rather than quietly corrected.

### 3.2 Does any instrument authorize DP-9's five-file commit?

**No.** Searched all reports and both decision directories for
`test_p7_zero_adapter_readiness`, `test_p17_pinning`, `validate-p7-readiness`,
`RESUME.md`. Every hit is a *report* describing the files; none names them as an
authorized commit target. The Phase 3 report's own scope (Decision 1) is
*"exactly the 6 authorized files"* of commit `238c9e4` — a disjoint set.

### 3.3 Authorization status of each DP item

| Item | Status | Basis |
|---|---|---|
| DP-1 validator patches | **UNAUTHORIZED** | protected; `DEC-0028` forbids pathspec/control change |
| DP-2 `REQ-P3-08` | **DECIDED — do not change** | `DEC-0028` (ACTIVE, User 2026-10-15) |
| DP-3 attribution | **UNAUTHORIZED** | `attribution_policy.json:4`; `:202` excludes *"any matching-semantics change beyond the single token addition"*; `:198` separately excludes *"any P17 `decided_by` execution check"* |
| DP-4 P5 annotations | **UNAUTHORIZED** | no locating instrument |
| DP-5 DEC-0001/remote | **UNAUTHORIZED** | User-only |
| DP-6 register D-17 test | **BLOCKED** | touches protected `validate-sps2.sh` |
| DP-7 CI guard + validators | **UNAUTHORIZED** | workflow is protected |
| DP-8 git identity | **BLOCKED** | depends on DP-5 |
| DP-9 commit | **UNAUTHORIZED** | no instrument covers the five files |
| DP-10 durable record | **PREPARED, uncommitted** | committing prohibited |
| DP-11 `GOVERNANCE.md` fence | **UNAUTHORIZED** | file is protected |

**No new approval was invented, inferred, or converted from PROPOSED.**

---

## 4. Exact changes made

**None.** No repository file was created, modified, deleted, moved, or staged.

All operations were reads, or writes confined to `/tmp` (`/tmp/r4-d17`,
`/tmp/r4-dp2`, `/tmp/r4-clone`, `/tmp/r4-*`). The only repository-adjacent write
is this report.

---

## 5. Exact changes proposed but not applied

| ID | Change | Evidence | Blocker |
|---|---|---|---|
| DP-1a | `P1` → `validate-p2.sh` | full NC matrix, §7 | protected |
| DP-1b | `P2` → `validate-sps2.sh` | full NC matrix, §7 | protected |
| DP-1c | `P3` → `validate-p3.sh` | NC matrix, §7 | protected |
| DP-1d | `P4` → `validate-p4.sh` + 1-char regex widening | §7.5 | protected |
| DP-3a | `SELF_REFERENT` regex in `attribution.py` | §10 | new decision needed |
| DP-3b | P17 gate exact-equality `"User"` | §10 | new decision needed |
| DP-6 | register `test_p7_zero_adapter_readiness` in a runner | §11 | protected runner |
| DP-7a | per-module CI guard | §9, proven in `/tmp` | protected workflow |
| DP-7b | run the four validators in CI | §9, now known safe | protected workflow |
| DP-11 | insert one closing fence after `GOVERNANCE.md:100` | §12 | protected file |

---

## 6. Test results by repository state

| # | State | Modules | Ran | Failed | Skipped | Exit | Reproducible |
|---|---|---|---|---|---|---|---|
| 1 | worktree, tracked | 26 | **562** | 0 | 1 | 0 | yes |
| 2 | worktree, tracked, reverse order | 26 | **562** | 0 | 1 | 0 | yes |
| 3 | full worktree incl. untracked | 30 | **896** | 0 | 1 | 0 | yes |
| 4 | clean clone of HEAD | 26 | **558** | 0 | 1 | 0 | yes |
| 5 | clone + P1..P4 applied | 26 | **558** | 0 | 1 | 0 | yes |
| 6 | portability harness | — | 34P/5F/14C | 5 | — | 1 | yes |
| 7 | validator negative controls | — | see §7 | — | — | — | yes |
| 8 | CI guard negative controls | — | see §9 | — | — | — | yes |

Commands in §15. Skips parsed from stdout (`skipped=1`), never inferred from exit
code. The single skip is a deterministic schema test requiring `P17_AJV_ROOT`.

**Arithmetic:** 558 (clone) + 4 (prior-round tests added to tracked modules) =
**562**. Plus 331 untracked (`test_p10_runtime_gate.py` 282,
`test_content_slots.py` 25, `test_layout_registry.py` 24) + 3 (D-17 module) =
**896**. Order independence confirmed — identical counts both directions.

**`unittest discover` remains unusable** in this repository (reports 0 tests,
exit 5). All runs use explicit module lists.

---

## 7. Validator negative-control results

Reviewed by an independent adversarial reviewer; I re-verified its central claim.

### 7.1 Patch hashes and application

| Patch | sha256[:16] | `git apply --check` | Applied |
|---|---|---|---|
| `P1-validate-p2-exit-status` | `247ef4f055a6cc56` | OK | OK |
| `P2-validate-sps2-exit-status` | `0a90a2cefcca6be1` | OK | OK |
| `P3-validate-p3-exit-status` | `3a334297cc716416` | OK | OK |
| `P4-validate-p4-negative-controls` | `c9665a4cf08f6fff` | OK | OK |

The **subshell trap is avoided in all four** — every capture sits on the same
line as, and outside, the command substitution:
`out="$(python3 "$CHECK" "$1" "$2" 2>&1)"; rc=$?`. P1's second hunk is real and
verified at `validate-p2.sh:329` (`P0_RC=$?`).

### 7.2 The matrix (`validate-p2.sh`)

| State | Original | Patched |
|---|---|---|
| A clean | 68 P / 1 F | **68 P / 1 F (identical)** |
| B crashing checker | 47 P / 22 F | **39 P / 30 F** |
| C missing checker | 47 P / 22 F | **39 P / 30 F** |
| D silent non-zero | 47 P / 22 F | **39 P / 30 F** |

**8 fabricated PASSes eliminated** in each of B/C/D — exactly the 8 `assert_clean`
sites, including `PASS CASE P0 valid capability record accepted`, which the
original printed while the checker never ran.

### 7.3 Regression — clean state identical across all four

`validate-p2.sh` 68/1 · `validate-sps2.sh` 79/1 · `validate-p3.sh` 66/2 ·
`validate-p4.sh` 55/5. The pre-existing `legacy modified:
.github/workflows/sps-ci.yml` failure appears in **both** versions, confirming it
is not caused by any patch.

### 7.4 P3/P4 — same defect class, narrower surface

The claim "P3/P4 already use `2>&1`" is **literally true** and I verified it, but
`2>&1` alone never captures `$?`. The defect persists under a **silent** non-zero
exit: `P3` fabricates **7** PASSes, `P4` fabricates **2** (`POSCTRL-D/E`). A
*noisy* crash routes a traceback into stdout, so P3/P4 failed loudly there.
They are genuine hardening of the same defect class — **not** a different defect,
and **not** the false-PASS severity of P2/SPS2.

### 7.5 New finding — P4 regex brittleness (latent)

`check_p4.py:39` prints a **bare** `PROMOTED`; the new guard requires trailing
whitespace (`'^(PROMOTED|NOT_PROMOTED)[[:space:]]'`). I reproduced this:

```
printf 'PROMOTED\n' | grep -qE '^(PROMOTED|NOT_PROMOTED)[[:space:]]'   -> no match
printf 'PROMOTED\n' | grep -qE '^(PROMOTED|NOT_PROMOTED)([[:space:]]|$)' -> match
```

**Latent, not reachable today** — bare `PROMOTED` requires zero blocking gates,
which `POSCTRL-D/E` inputs do not produce. Both fall-through paths emit FAIL, so
**no control is weakened and no false PASS results**; only the diagnostic would
be misleading. The one-token widening above fixes it and is included in DP-1d.

### 7.6 Residual unpatched helper — fails safe

`run_check()` (`2>/dev/null`, `$?` uncaptured) survives at `validate-p2.sh:34,313,385,398,414`
and `validate-sps2.sh:36,367,451`. These are **negative** controls expecting
non-empty output, so a crash yields "NOT REJECTED" → FAIL. Verified empirically
in the crash state: they fail-safe, and are not a false-PASS vector.

---

## 8. Portability results

Reproduced exactly: **34 passed / 5 failed / 14 controls / exit 1**.

```
FAIL  copy: P2 research not green with zero adapters (rc=1)
FAIL  copy: P3 production not green with zero adapters (rc=1)
FAIL  copy: P4 promotion not green with zero adapters (rc=1)
FAIL  copy: P5 implementation not green with zero adapters (rc=1)
FAIL  copy: P7 readiness mutations not green with zero adapters (rc=1)
```

### 8.1 Root cause — two distinct controls, not one

The predicate resolves to **4 paths**, not 3:

```
.github/workflows/sps-ci.yml
.sps/tools/validate-capability.sh
.sps/tools/validate-control.sh
.sps/tools/validate-governance.sh
```

`DEC-0029`/`DEC-0030` and the validators report **3** because `.sps/` is caught by
a **separate** control at `validate-p3.sh:311-315` (`git diff HEAD -- .sps/`),
while `.github/` is caught by the `c11da27` pathspec. Two controls, two mechanisms.

### 8.2 Alternatives measured

| Alt | Pathspec | Paths | Normative change? |
|---|---|---|---|
| A | status quo | 4 | — |
| B | dir list, no glob | 1 | **yes** — redefines a VERIFIED criterion |
| C | drop `.github` | 3 | **yes** — `DEC-0029/0030` keep `.github` in scope |
| D | explicit `.sps/tools` | 4 | **yes** — and changes nothing today |

**`DEC-0030` itself measured that its definition yields the same 3 `.sps/tools`
files** — it is behaviour-preserving by design and therefore does **not** clear
the failures. My prior report correctly rejected it; this round confirms the
mechanism from the record's own evidence.

### 8.3 Disposition — `DEC-0028` already answers this

The five failures are **correct reports**, not regressions. `DEC-0028` holds they
*"remain red until the underlying requirement question is settled by a separate
User decision."* `DEC-0029` (PROPOSED) agrees the three files *"REMAIN WITHIN the
protected legacy scope."* **No engineering action is available or authorized.**
This is a governance decision, and the honest state is: the harness is red by
design, and the design is correct.

---

## 9. CI integrity results

| Fact | Verified |
|---|---|
| Discovery via `git ls-files 'test_*.py' '**/test_*.py'` (`:129`) | yes |
| `MIN_TESTS=500` (`:147`) | yes |
| Exit-code propagation `set +e`/`STATUS=$?`/`exit "$STATUS"` | correct |
| Validators executed in CI | **zero** |
| GitHub Actions runs observed | **zero** |

### 9.1 Guard negative controls (proposed, proven in `/tmp`)

| Case | Old guard | Proposed guard |
|---|---|---|
| healthy (26 modules) | PASS | PASS |
| delete small module (25 tests → 537 ran) | **PASS (wrong)** | **FAIL** |
| delete large module (68 → 494) | FAIL | FAIL |
| module present but runs **zero** tests (48 → 514) | **PASS (wrong)** | **FAIL** |
| import/syntax failure (0 tests, rc=1) | FAIL | FAIL |
| zero tests discovered | FAIL | FAIL |

The **zero-test module** case is the sharpest: a module can remain importable
while contributing no tests, and `MIN_TESTS=500` misses it (514 ≥ 500). The
per-module guard catches it because it compares executed modules against the
expected set parsed from `unittest -v`, independently of any total.

### 9.2 Validator coverage is now known to be safe

I previously prohibited running these validators against the real tree. That was
**overly conservative**. All four use `TMP="$(mktemp -d …)"` and write only
beneath it. Verified by hashing the complete `git status` before and after:

```
status hash before: 7e80ce045878b95e
status hash after:  7e80ce045878b95e
REPOSITORY UNCHANGED-by-validator
```

**No disposable checkout is required for CI validator steps.** This removes the
main obstacle to DP-7b and is a material improvement in feasibility.

---

## 10. Attribution and P17 gate findings

Independently reproduced by me and by a separate analyst.

### 10.1 The heuristic accepts seven self-approval phrasings

| Input | Current |
|---|---|
| `"Self (self-approved)"` | **ACCEPT** |
| `"Self-approved"`, `"SELF APPROVED"`, `"self approval"` | **ACCEPT** |
| `"approved by self"`, `"Self (self-authorised)"` | **ACCEPT** |
| `"Jane Self (self-approved)"` | **ACCEPT** |
| `"Claude (self-approved)"` | reject — *incidentally*, via token `claude` |

Detection currently depends on whether an unrelated vendor token happens to
co-occur. `"self"` was removed from the token set by `DEC-0027`, and adding it
back would reject the legitimate surname `Jane Self` — so the blunt fix is
correctly excluded.

### 10.2 The P17 execution gate is strictly weaker than the heuristic

`sps2/p17/__main__.py:379-380` checks **only** `state` and `decided_by_role`.
Grep confirms `sps2/p17/` references `attribution`, `AGENTISH`, or
`approval_is_user_attributable` **zero times**. Reproduced:

```
'User'                    -> gate PASSES -> EXECUTION PROCEEDS
'Self (self-approved)'    -> gate PASSES -> EXECUTION PROCEEDS
```

A sidecar with `decided_by: "Self (self-approved)"` and
`decided_by_role: "USER"` **executes**. `decided_by` is written literally at
`:281` but never read as a gate condition. This is the more serious of the two
gaps, because it is the path that actually spawns work.

### 10.3 Narrow proposal, adversarially tested

```
SELF_REFERENT = re.compile(
    r"(?:\bself\s*(?:[-\u2010-\u2015\u00a0]\s*)?(?:approv|authoris|authoriz)\w*"
    r"|\b(?:approv|authoris|authoriz)\w*\s*(?:by|from)\s*self\b)", re.I)
```

I tested it on 26 inputs. **Zero surname or vendor verdicts change.** All five
surnames (`Jane`, `Marcus`, `Robert Self`, `Nora Script`, `Myself`, `Selfer`,
`Selby`, `Selfs`, `Selfie`) and bare `Self`/`self` remain accepted; all six
intended phrases flip to reject.

**Honest cost — two over-broad rejections:**
`"Nora Self approved the plan"` and `"Mr Self-Approved-By-Nobody"` become
rejected (requires surname adjacent to an approval verb).

**Honest gap:** `"self_approved"` (underscore) is **not** caught, and
`"Self Analysis approved"` is not caught either.

Even the strongest P17 option (exact equality with `"User"`) does **not**
establish identity: `approval.json` is unsigned, self-asserted free text
(UQ-ATT-2). See §13 for the recommended framing.

---

## 11. D-17 regression re-verification

| Check | Result |
|---|---|
| Fix present at `validate-p7-readiness.py:174` | yes |
| Test present | yes |
| Test passes against fixed validator | `Ran 3 tests … OK` |
| **Revert predicate in disposable copy → test fails** | **`FAILED (failures=1)`** |

**Causality independently re-confirmed this round.** The mission's question is
registration: the test is wired into **no** runner (absent from
`CORE_VALIDATORS`, absent from `validate-sps2.sh`, untracked so CI cannot see
it). The minimal DP-6 change is one line in `portability.py`'s
`CORE_VALIDATORS`, whose existing precedent is
`("P5 unit tests", ["python3", "sps2/tests/test_p5.py"], "OK")`.

---

## 12. Governance reconciliation

### 12.1 DP-10 — verified and prepared

| Claim | Verified |
|---|---|
| Report names `238c9e4` and `cdcbca8` | yes (`:19-20`) |
| Hashes exist and match history | yes; `238c9e4` is an ancestor, `cdcbca8` **is** HEAD |
| Decision 1 "exactly the 6 authorized files" | yes — `6 files changed, 768 insertions(+), 39 deletions(-)` |
| Decision 4 pure addition | yes — `+98/−0` |
| Attribution hash pair | yes — HEAD `de2cc583341d993b` → worktree `b6c21d73cea2290f` |

**In a clone, traceability is zero:** `reports/` has **0** tracked files; the
Phase 3 report is absent; **0** decision files name `cdcbca8`; **0** mention
`sps-ci.yml`. The defect is **retention**, not absence of authorization.

### 12.2 DP-11 — fence defect confirmed

Fences at lines 69, 72, 93, 198. The fence opened at **93** closes only at
**198**, so **§4–§9** (Evidence Rules, Decision Records, Handoff Contract, Secret
Safety, Scope Control, Project-Local State Rule) render as literal code. The
orphan fragment `approval (user)` at `:197` corroborates it. **Mechanical, not
normative** — rule text is intact and `validate-governance.sh` reads raw text.
Protected (`da0b64afcb943c05`). Minimal fix: insert one closing fence after
line 100.

### 12.3 Untracked decision records

`DEC-0029` and `DEC-0030` are untracked, so clones lose the record that the
three `.sps/tools` files remain in protected scope. Same retention defect as
DP-10. Note `DEC-0029` is **PROPOSED**, so it cannot be relied upon even though
it is consistent with the ACTIVE `DEC-0028`.

---

## 13. Status of DP-1 through DP-11

| ID | Evidence establishes | Requested action | Files | Independent? | Safe meanwhile |
|---|---|---|---|---|---|
| **DP-1** | 8 fabricated PASSes per crash state; patches verified correct, zero regression | Authorize P1–P4 (incl. 1-char P4 widening) | 4 `validate-*.sh` | yes | all else |
| **DP-2** | `DEC-0028` (ACTIVE) already decides: do not change; failures are correct | **Confirm retention** or supersede `DEC-0028` | `P3-REQUIREMENTS.json` | yes | yes |
| **DP-3** | 7 phrasings accepted; P17 gate ignores `decided_by` entirely and **executes** | Authorize `SELF_REFERENT` + P17 exact-`User` check | `attribution.py`, `p17/__main__.py` | yes | yes |
| **DP-4** | Additive `state_changed:false`; no instrument; listed as forbidden scope elsewhere | Scope ruling: governed edit or ordinary? | 2 P5 files | yes | yes |
| **DP-5** | `origin` exists; 4 local push reflogs; `DEC-0001` requires a new instruction | Ratify remote, or record an incident | `.sps/decisions/` | yes | all else |
| **DP-6** | Revert→fail proven; test wired nowhere | Register in `CORE_VALIDATORS` | `portability.py`, `validate-sps2.sh` | after DP-9 | yes |
| **DP-7** | Guard catches zero-test + small-delete; validators proven read-only | Add per-module guard + 4 validator steps | `.github/workflows/sps-ci.yml` | yes | proven in `/tmp` |
| **DP-8** | 136/138 commits placeholder; `DEC-0002` premise false | Replace repo-local identity | git config | **after DP-5** | yes |
| **DP-9** | Clone lacks all 5 fixes and still says `PENDING_USER_APPROVAL` | Authorize one narrow commit | 5 files | yes | everything above |
| **DP-10** | 0 tracked reports; clone has zero traceability | Commit `reports/` or create decision record | `reports/`, `sps2/decisions/` | yes | draft prepared |
| **DP-11** | §4–§9 render as code; enforcement unaffected | Insert one fence after `:100` | `.sps/GOVERNANCE.md` | yes | yes |

---

## 14. Remaining blockers ranked by severity

| # | Blocker | Severity | Class |
|---|---|---|---|
| 1 | **P17 execution gate ignores `decided_by`; a self-attributed sidecar executes** | Critical | Engineering defect + governance gate |
| 2 | **No validator runs in CI; no CI run ever observed** | Critical | Missing evidence |
| 3 | **P2/SPS2 fabricate PASS on a dead checker** | High | Engineering defect (patch ready) |
| 4 | **All five verified fixes are worktree-only** | High | Worktree-only fix |
| 5 | Portability red 34/5 | High | **Governance decision (already made — retain)** |
| 6 | Attribution accepts 7 self-approval phrasings | Medium | Engineering defect + governance gate |
| 7 | CI misses a zero-test module | Medium | Engineering defect (guard ready) |
| 8 | `DEC-0001` contradicted by the remote | Medium | Governance decision |
| 9 | CI/migration authorization untraceable in a clone | Medium | Missing evidence |
| 10 | P5 annotations lack a located authorization | Low | Governance decision |
| 11 | `GOVERNANCE.md` §4–§9 render as code | Low | Known limitation (mechanical) |

---

## 15. Exact user decisions needed next

**DEC-A — P17 execution gate (highest value).** *Evidence:* gate at
`__main__.py:379-380` reads only `state` and `decided_by_role`; reproduced that
`"Self (self-approved)"` **executes**. *Requested:* authorize requiring
`decided_by` to equal exactly `"User"`. *Why this option:* `DEC-0027` names
exact-equality `"User"` checks as **the** binding control, so this implements the
approved control rather than importing the heuristic. *Cost:* `cmd_approve:281`
already writes literal `"User"`, so no test breaks. *Independence:* yes.
*Limitation:* this does not establish identity — `approval.json` is unsigned.

**DEC-B — commit the five verified fixes (DP-9).** *Evidence:* a clone of
`cdcbca8` contains none of them and still reports `PENDING_USER_APPROVAL`.
*Requested:* authorize one commit of exactly: `sps2/RESUME.md`,
`sps2/tests/test_p17_security.py`, `sps2/tests/test_p17_pinning.py`,
`sps2/tools/validate-p7-readiness.py`,
`sps2/tests/test_p7_zero_adapter_readiness.py`. *Independent:* yes. The four
pre-existing user edits and the other 7 modified files **must be excluded**.

**DEC-C — the four validator patches (DP-1), with the P4 widening.** *Evidence:*
full 4-state matrix; 8 fabricated PASSes eliminated per state; clean counts
identical. *Requested:* authorize all four including
`'^(PROMOTED|NOT_PROMOTED)([[:space:]]|$)'`. *Independent:* yes.

**DEC-D — attribution regex (DP-3).** *Evidence:* 6 behaviours change, 0
surnames affected; 2 adversarial over-broad rejections disclosed. *Requested:*
authorize `SELF_REFERENT` as a **new decision record** (`attribution_policy.json:4`
and `:202` both require it), and authorize updating
`test_attribution_policy.py:417-421`, which currently asserts the opposite.
*Needs your ruling on:* whether `"Nora Self approved the plan"` being rejected is
acceptable.

**DEC-E — CI guard and validator coverage (DP-7).** *Evidence:* guard proven
against 6 cases including zero-test; validators proven read-only. *Requested:*
authorize the per-module guard and four validator steps.

**DEC-F — commit the CI/migration authorization (DP-10).** *Requested:* choose
(a) commit `reports/`, or (b) create a canonical decision record citing
`238c9e4`/`cdcbca8`. *Recommendation:* (b) — a decision record is the
governance-native artifact; reports are narrative. *Do not* fabricate a new date
or alter the original decision's meaning.

**DEC-G — DP-2 retention.** `DEC-0028` already decides this. *Requested:* confirm
the harness stays red by design, or supersede `DEC-0028`. No engineering action
is available meanwhile.

**Lower priority:** DP-4 scope ruling, DP-5 remote decision, DP-6 registration
(after DEC-B), DP-8 identity (after DP-5), DP-11 fence.

---

## 16. Reproducible commands

```bash
# tracked corpus
MODS=$(git ls-files 'test_*.py' '**/test_*.py' | grep -E '^(sps2|domain)/' \
       | sed 's/\.py$//;s#/#.#g' | sort)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $MODS
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $(echo "$MODS" | sort -r)

# full worktree
ALL=$( (git ls-files 'test_*.py' '**/test_*.py'; \
         find sps2 domain -name 'test_*.py') | sort -u \
       | grep -E '^(sps2|domain)/' | sed 's/\.py$//;s#/#.#g')
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $(echo "$ALL")

# portability harness
PYTHONDONTWRITEBYTECODE=1 python3 sps2/tools/test-portability.py

# validators are READ-ONLY (mktemp-based) — safe on the real tree:
bash sps2/tools/validate-p2.sh ; python3 sps2/tools/validate-p5.py

# clean clone
git clone -q --no-hardlinks . /tmp/r4-clone && cd /tmp/r4-clone && git checkout -q cdcbca8

# faithful disposable copy (NEVER git archive — it omits .git and distorts a licence gate)
python3 - <<'PY'
import sys, os, importlib.util
sys.path.insert(0, os.path.join(os.getcwd(), "sps2", "tools"))
spec = importlib.util.spec_from_file_location("PT", "sps2/tools/portability.py")
PT = importlib.util.module_from_spec(spec); spec.loader.exec_module(PT)
tree = PT.copy_tree(os.getcwd(), "/tmp/r4-tree/tree")
PY

# D-17 causality check
sed -i '' 's/generic = (not adapters) or PT.FALLBACK_ADAPTER_ID/generic = PT.FALLBACK_ADAPTER_ID/' \
  /tmp/r4-tree/tree/sps2/tools/validate-p7-readiness.py
cd /tmp/r4-tree/tree && PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest sps2.tests.test_p7_zero_adapter_readiness   # expect FAILED
```

---

## 17. Limitations and unverified environments

- **No GitHub Actions run observed.** All CI results are local simulation.
- **Python 3.12 / Ubuntu not verified.** Local runs are macOS + Python 3.14.7;
  CI targets 3.12. Behaviour is not inferable across that gap.
- **`P17_AJV_ROOT` unset** → the schema-conformance test skips. Claiming schema
  conformance would require that tool.
- **No Linux or Windows validation**; macOS lacks GNU `timeout`.
- **The P4 widening is my recommendation, not the reviewer's**, though the
  reviewer identified the brittleness.
- **The DP-3 regex's two over-broad rejections are disclosed, not resolved.**
- **UQ-ATT-2 remains open:** no mechanism establishes that `decided_by` is a real
  authorized human. `approval.json` is unsigned free text; every attribution
  control, including DEC-A, is a heuristic over self-asserted strings.
- **DP-10 draft is prepared but uncommitted**, so traceability remains absent.
- Two subagents were used; both returned findings I re-verified independently.

---

## 18. Machine-readable summary

```json
{
  "report": "SPS2-FINAL-EXECUTION-MISSION-20261016-124100",
  "verdict": "NOT_READY",
  "repository_files_modified_this_round": 0,
  "repository": {
    "branch": "build/roadmap-p3-completion",
    "head": "cdcbca83679844ea66196f25773f42d9b64569ec",
    "head_unchanged": true,
    "staged": 0, "stash": 0, "modified_tracked": 11,
    "untracked_file_level": 110, "deletions": 0, "fsck_errors": 0,
    "remote_contacted": false,
    "protected_files_intact": 7,
    "preexisting_user_edits_intact": 7,
    "reports_preserved": 8
  },
  "tests": {
    "worktree_tracked":         {"modules": 26, "ran": 562, "failed": 0, "skipped": 1, "exit": 0},
    "worktree_tracked_reversed":{"modules": 26, "ran": 562, "failed": 0, "skipped": 1, "exit": 0},
    "worktree_full":            {"modules": 30, "ran": 896, "failed": 0, "skipped": 1, "exit": 0},
    "clean_clone":              {"modules": 26, "ran": 558, "failed": 0, "skipped": 1, "exit": 0},
    "clone_plus_p1_p4":         {"modules": 26, "ran": 558, "failed": 0, "skipped": 1, "exit": 0},
    "order_dependent": false,
    "discover_usable": false
  },
  "portability": {
    "passed": 34, "failed": 5, "controls": 14, "exit": 1,
    "root_cause": "c11da27_legacy_path_criterion",
    "predicate_paths": [".github/workflows/sps-ci.yml",
                        ".sps/tools/validate-capability.sh",
                        ".sps/tools/validate-control.sh",
                        ".sps/tools/validate-governance.sh"],
    "distinct_controls": 2,
    "disposition": "DEC-0028 ACTIVE decides: retain, failures are correct reports",
    "engineering_action_available": false
  },
  "authorization": {
    "new_instruments_found": ["DEC-0025","DEC-0026","DEC-0027","DEC-0028"],
    "newest_approval_date": "2026-10-15",
    "prior_report_claim_refuted": "newest approval 2026-10-08",
    "miss_cause": "key is decided_at, not decided_on",
    "covers_dp9_commit": false,
    "new_approvals_invented": 0
  },
  "validator_patches": {
    "P1": {"sha256_16": "247ef4f055a6cc56", "verdict": "SOUND_WITH_CAVEATS"},
    "P2": {"sha256_16": "0a90a2cefcca6be1", "verdict": "SOUND_WITH_CAVEATS"},
    "P3": {"sha256_16": "3a334297cc716416", "verdict": "SOUND_WITH_CAVEATS"},
    "P4": {"sha256_16": "c9665a4cf08f6fff", "verdict": "SOUND_WITH_CAVEATS",
           "finding": "latent regex brittleness on bare PROMOTED",
           "recommended_widening": "'^(PROMOTED|NOT_PROMOTED)([[:space:]]|$)'"},
    "subshell_trap_avoided": true,
    "clean_state_regression": "identical for all four",
    "fabricated_passes_eliminated_per_crash_state": 8,
    "applied": false
  },
  "defects": {
    "p17_gate_ignores_decided_by": {
      "status": "REPRODUCED_NOT_FIXED", "severity": "critical",
      "gate_checks": ["state", "decided_by_role"],
      "attribution_refs_in_p17_dir": 0,
      "self_approved_sidecar_executes": true,
      "blocker": "DEC-A"
    },
    "attribution_self_approval": {
      "status": "REPRODUCED_NOT_FIXED", "severity": "medium",
      "phrasings_accepted": 7,
      "proposal_changes": 6, "surnames_affected": 0,
      "over_broad_cases": ["Nora Self approved the plan","Mr Self-Approved-By-Nobody"],
      "gap_cases": ["self_approved","Self Analysis approved"],
      "blocker": "DEC-D"
    },
    "ci_zero_test_module": {
      "status": "CONFIRMED_NOT_FIXED", "severity": "medium",
      "old_guard": "PASS (514 >= 500)", "proposed_guard": "FAIL",
      "blocker": "DEC-E"
    },
    "D17_p7_zero_adapter": {
      "status": "FIXED_UNCOMMITTED", "fix_present": true, "test_present": true,
      "revert_makes_test_fail": true, "wired_into_runner": false,
      "blocker": "DEC-B then DP-6"
    }
  },
  "validators_read_only": {
    "verified": true,
    "method": "git status hash before/after identical",
    "all_four_use_mktemp": true,
    "prior_prohibition_corrected": true,
    "ci_disposable_checkout_required": false
  },
  "ci": {
    "validators_executed": 0, "gha_runs_observed": 0,
    "min_tests": 500, "test_count": 558,
    "modules_deletable_invisibly": 24, "modules_total": 26,
    "exit_code_propagation_correct": true
  },
  "traceability": {
    "reports_tracked_files": 0,
    "clone_has_phase3_report": false,
    "clone_decision_files_naming_cdcbca8": 0,
    "commit_238c9e4_verified": true, "commit_cdcbca8_verified": true,
    "decision1_scope_matches": true, "decision4_pure_addition": true,
    "durable_record_prepared": true, "committed": false
  },
  "governance": {
    "pending_decisions": ["DEC-0029","DEC-0030","DEC-7101","DEC-7102","DEC-7103",
                          "DEC-7104","DEC-7110","OPEN-DECISION-ATTRIBUTION-TOKEN-SET"],
    "governance_fence_defect": {"file": ".sps/GOVERNANCE.md", "open_line": 93,
                                "close_line": 198, "sections_swallowed": 6,
                                "class": "mechanical", "protected": true,
                                "fix": "insert closing fence after line 100"}
  },
  "user_decisions_needed": ["DEC-A P17 gate","DEC-B commit five fixes",
                            "DEC-C validator patches (incl P4 widening)",
                            "DEC-D attribution regex","DEC-E CI guard + validators",
                            "DEC-F durable authorization record",
                            "DEC-G DP-2 retention confirmation"],
  "blockers_ranked": [
    {"rank":1,"item":"P17 gate ignores decided_by","severity":"critical"},
    {"rank":2,"item":"no validator in CI, no CI run observed","severity":"critical"},
    {"rank":3,"item":"P2/SPS2 fabricate PASS on dead checker","severity":"high"},
    {"rank":4,"item":"five fixes worktree-only","severity":"high"},
    {"rank":5,"item":"portability red 34/5 (retain by DEC-0028)","severity":"high"},
    {"rank":6,"item":"attribution accepts 7 phrasings","severity":"medium"},
    {"rank":7,"item":"CI misses zero-test module","severity":"medium"},
    {"rank":8,"item":"DEC-0001 contradicted by remote","severity":"medium"},
    {"rank":9,"item":"CI authorization untraceable in clone","severity":"medium"},
    {"rank":10,"item":"P5 annotations unauthorized","severity":"low"},
    {"rank":11,"item":"GOVERNANCE.md sections render as code","severity":"low"}
  ]
}
```

---

## 19. Final release-readiness verdict

# `NOT_READY`

The product is not release-ready, and for the first time the reason is precise
and largely **not** an engineering failure.

**What improved this round.** The authorization picture is now correct: the
missing decisions were found, the two highest-priority items are provably
blocked (not merely un-attempted), the validator patches are independently
verified sound with zero clean-state regression, the CI guard is proven against
the zero-test case the old guard misses, and the shell validators are proven
read-only — which removes the main obstacle to CI validator coverage.

**Why the verdict cannot move yet.** Three conditions are unmet, and none is
within my authority:

1. **The P17 execution gate accepts a self-attributed approval.** A sidecar
   reading `decided_by: "Self (self-approved)"` with `decided_by_role: "USER"`
   executes. This is the most serious open defect because it governs the path
   that spawns work.
2. **No validator executes in CI, and no CI run has ever been observed.** Even
   with every patch applied, today's workflow would exercise none of them.
3. **The five verified fixes exist only in this working tree.** A clone of
   `cdcbca8` contains none of them and still reports `PENDING_USER_APPROVAL`.

**The honest characterisation of DP-2.** The portability harness is red at 34/5,
and `DEC-0028` — ACTIVE, User-approved — establishes that this is **correct
behaviour**: those failures accurately report modified legacy files, and the
record directs that they *"remain red until the underlying requirement question
is settled by a separate User decision."* I did not treat a red harness as a
defect to be engineered away, and I did not treat my own earlier recommendation
as authorization to narrow a verified criterion.

I committed nothing, pushed nothing, contacted no remote, weakened no test, and
crossed no approval boundary. Where this report corrects my own prior work — the
2026-10-08 date error and the overly conservative validator prohibition — the
correction and its root cause are stated in the open.
