# SPS2 Final Remediation — 2026-10-16 11:14

**Mission:** SPS2 Final Remediation — Evidence-Driven Fixes, Release Readiness, Regression Prevention, Governance-Safe Completion
**Repository:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`
**Branch:** `build/roadmap-p3-completion`
**HEAD:** `cdcbca83679844ea66196f25773f42d9b64569ec` (unchanged, never committed)
**Report:** `reports/SPS2-FINAL-REMEDIATION-20261016-111400.md`

---

## 1. Executive verdict

# `NOT_READY`

The mission's authorized engineering work is **complete**. No new remediation was
applied this round, because the one defect that surfaced as newly-fixable was
**already fixed in the prior round and is now independently verified** — and
every remaining blocker is gated behind a User decision that does not exist in
the repository.

`NOT_READY` is required because, on measured evidence:

- two protected validators can still fabricate PASS verdicts (DP-1 unapproved);
- the portability harness is red at **34 passed / 5 failed** and all five trace
  to a criterion whose repair is explicitly reserved to the User;
- the attribution path accepts a self-attributed approval, and the **actual P17
  execution gate never inspects the decider at all**;
- no GitHub Actions run has ever been observed, and **no shell validator executes
  in CI**;
- all five verified fixes exist only in the working tree and are absent from
  every clone.

---

## 2. Repository identity and preservation audit

| Property | Baseline (start) | Final | Status |
|---|---|---|---|
| Branch | `build/roadmap-p3-completion` | same | unchanged |
| HEAD | `cdcbca83679844ea66196f25773f42d9b64569ec` | same | unchanged |
| Staged | 0 | 0 | none |
| Stash | 0 | 0 | none |
| Modified tracked | 11 | 11 | unchanged |
| Untracked (file-level) | 109 | 109 | unchanged |
| Deletions | 0 | 0 | none |
| `git fsck` errors | 0 | 0 | clean |
| Reports | 7 | 7 | none overwritten |
| Remote contacted | — | **no** | `git remote -v` only |

**Protected files, all INTACT (byte-identical to baseline):**
`sps2/tools/validate-p2.sh` `9018e0de53abe5a1` ·
`validate-sps2.sh` `91509870f3d02b87` ·
`validate-p3.sh` `c6ca659a7c495c87` ·
`validate-p4.sh` `74af33ca7617494e` ·
`sps2/governance/attribution_policy.json` `eb9f113360601059` ·
`.sps/tools/validate-governance.sh` `ba57f7372708b9d3` ·
`sps2/governance/attribution.py` `b6c21d73cea2290f` (worktree; HEAD is `de2cc583341d993b`).

**All four pre-existing user edits byte-identical.** Baseline snapshot:
`/tmp/sps2-r3-baseline-1792127668/`.

---

## 3. Reports reconciled

All seven located and read; none overwritten or moved.

| Report | Role this round |
|---|---|
| `SPS2-FINAL-REMEDIATION-...` (this) | new |
| `SPS2-READINESS-REMEDIATION-20261016-101600.md` | primary prior; its numbers re-measured |
| `SPS2-FINAL-END-TO-END-READINESS-20261016-091500.md` | cross-checked |
| `SPS2-PHASE3-DECISION-EXECUTION-20261016-082741.md` | **decisive**: proved to be the CI/migration authorization instrument (§12) |
| `SPS2-PHASE3-SAFE-REMEDIATION-20261016-081050.md` | the 13-file protected list |
| `SPS2-PHASE4-RELEASE-VERIFICATION-20261016-084449.md` | historical |
| `SPS2-PHASE2-RELEASE-READINESS-20261016-072628.md` | corroborates CI was gated before approval |

---

## 4. Changes applied this round

**None.** No file in the real repository was modified in this round.

This is a substantive result, not an omission. I re-measured every claim, looked
for new authorization, and found that:

- the only defect that had been classified as fixable-but-unfixed is **D-17**,
  which **was** fixed in the prior round and is now independently verified (§10);
- every other open item reduces to a User decision (§14), with no new
  authorization recorded anywhere in the repository (newest `decided_on` is
  **2026-10-08**; DEC-0029/0030 remain `PENDING_USER_APPROVAL`).

Applying any of the prepared patches would have crossed an approval boundary.

## 5. Changes proposed but not applied

| ID | Proposal | Blocker | State |
|---|---|---|---|
| DP-1 | `P1`/`P2` validator exit-status patches | protected files | verified working, not applied |
| DP-2 | `c11da27` legacy-path criterion repair | `REQ-P3-08` is APPROVED+VERIFIED | analyzed, not applied |
| DP-3 | narrow self-approval rejection rule | governance-gated file + pinning test | prototyped, not applied |
| DP-6 | register the D-17 test in a runner | touches `validate-sps2.sh` (protected) | identified, not applied |
| DP-7 | per-module CI guard | `.github/workflows/sps-ci.yml` protected | prototyped and proven, not applied |
| DP-4 | stale `note` correction | decision instrument | identified |
| DP-9 | commit the five verified fixes | committing prohibited | enumerated |
| DP-5/8/10 | governance records | User-only | reconciliation prepared |

---

## 6. Test results — all four states measured separately

| State | Modules | Ran | Failed | Skipped | Exit |
|---|---|---|---|---|---|
| **A** current worktree, tracked | 26 | **562** | 0 | 1 | 0 |
| **A2** tracked, reversed order | 26 | **562** | 0 | 1 | 0 |
| **A3** full worktree (incl. untracked) | 30 | **896** | 0 | 1 | 0 |
| **B** clean clone of HEAD `cdcbca8` | 26 | **558** | 0 | 1 | 0 |
| **C** clone + P1/P2 patches | 26 | 558 | 0 | 1 | 0 |

Exact commands in §15. Skips parsed from stdout (`skipped=1`), never inferred
from the exit code. The single skip is `test_p17_endtoend.test_generated_record_conforms_to_the_approved_schema`
(deterministic; requires `P17_AJV_ROOT`, which is unset).

**Arithmetic reconciliation (measured, not estimated):**
558 (clone) + 4 (prior-round tests added to tracked modules: `test_p17_security.py`
60→62, `test_p17_pinning.py` 23→25) = **562** tracked. Then +331 untracked
(`test_p10_runtime_gate.py` 282, `test_content_slots.py` 25,
`test_layout_registry.py` 24) + 3 (new D-17 module) = **896** full worktree.

**Order independence:** identical 562 / 0 / 1 in both directions. No order
dependence detected.

**`unittest discover` remains unusable as a gate** — it reports zero tests and
exits 5 in this repository. All runs use explicit module lists.

---

## 7. Portability harness — 34 passed / 5 failed / 14 controls

Reproduced exactly (`exit 1`):

```
FAIL  copy: P2 research not green with zero adapters (rc=1)
FAIL  copy: P3 production not green with zero adapters (rc=1)
FAIL  copy: P4 promotion not green with zero adapters (rc=1)
FAIL  copy: P5 implementation not green with zero adapters (rc=1)
FAIL  copy: P7 readiness mutations not green with zero adapters (rc=1)
```

**All five trace to ONE root cause: the `c11da27` legacy-path criterion.**
Measured predicate output, identical with adapters present or deleted:

```
.github/workflows/sps-ci.yml
.sps/tools/validate-capability.sh
.sps/tools/validate-control.sh
.sps/tools/validate-governance.sh
```

| # | Failure | Underlying cause |
|---|---|---|
| F1–F4 | P2/P3/P4/P5 not green | `legacy modified: .github/workflows/sps-ci.yml` |
| F5 | P7 readiness mutations | **same pin**, surfacing via the p4/p5 "blanket-ban" sub-tests |

**Correction to the prior report (C2).** F5 was described as a P7
zero-adapter/registry issue. It is not. The mutation suite reports
**`35 caught, 3 MISSED` identically** with adapters present and deleted, and it
does not depend on `validate-p7-readiness.py`. The `FAIL` lines are
`(p4) blanket-ban regression, rejected: intact record` and the same for `p5` —
because `validate-p4.sh` itself fails on an *intact* record:

```
FAIL  P7_ARTIFACT_CREATED: decisions/P7-DECISIONS.json
FAIL  P7_ARTIFACT_CREATED: memory
FAIL  legacy modified: .github/workflows/sps-ci.yml
```

**Correction to the prior report (C3) — material.** The prior report implied that
adopting `DEC-0030`'s proposed definition of "legacy paths" would help clear the
four pin failures. **It would not.** `DEC-0030` names `.sps/tools/`
**explicitly**, so the three `.sps/tools/*.sh` files would still match.
Simulated against the tree:

```
skills scripts plugins .github templates .sps/tools README.md CHANGELOG.md
CATALOG.md install.sh install.ps1 uninstall.sh uninstall.ps1 get-sps.sh get-sps.ps1
  -> .github/workflows/sps-ci.yml
  -> .sps/tools/validate-capability.sh
  -> .sps/tools/validate-control.sh
  -> .sps/tools/validate-governance.sh
```

Only `.github/workflows/sps-ci.yml` is *not* covered by `DEC-0030`'s directory
list, and that single file is what F1–F4 actually report. So the fix is either
a narrower `.sps/tools/` decision **plus** a decision about `.github/`, or a
deliberate exception for migrated-in-place files. Either way it is a normative
decision, not an engineering one.

**`DEC-0030` cannot authorize it, by its own text:**

> "Changing a validator's pathspec to match this definition is a SEPARATE
> decision, is NOT taken here, and would require its own explicit
> authorization."

Its `approval.state` is `PENDING_USER_APPROVAL`; its `author` field states it
"originates no approval and grants none."

**Diagnostic (not a proposal):** substituting `HEAD` for `c11da27` in a throwaway
copy cleared F1 and F4 (`validate-p2.sh` rc=0, `validate-p5.py` rc=0) and
reduced F3 to the unrelated `P7_ARTIFACT_CREATED` gate, confirming the pin is the
dominant cause. This was run only in `/tmp`; no real file was touched.

---

## 8. Protected validator false-PASS — reproduction and patch review

### 8.1 The defect (verified fact)

`sps2/tools/validate-p2.sh:34` and `sps2/tools/validate-sps2.sh:36`:

```bash
run_check() { python3 "$CHECK" "$1" "$2" 2>/dev/null; }

assert_clean() {
  local out; out="$(run_check "$1" "$2")"
  if [ -z "$out" ]; then pass "$3"; else ... fail ...; fi
}
```

stderr is discarded and `$?` is never captured. A legitimate pass and a crash
both yield empty stdout, so **both score PASS**.

Independently reproduced: with the checker replaced by
`raise SystemExit("SIMULATED CRASH")`, section 2 printed **7 fabricated PASS
lines**, byte-identical to a healthy run. Decisive control — a record corrupted
to `url: ""`:

| Checker | Output |
|---|---|
| healthy | `FAIL sources: ERR SRC-001: missing or non-http url` |
| crashed | `PASS sources` |

**Severity scoping (not exaggerated).** The negative suites require *non-empty*
output, so a **full** crash still exits 1. The defect is that structural PASSes
are fabricated and the PASS counter inflates. It becomes a true fail-open only
for a partially-dead checker; every kind has negative coverage, so I could not
construct an exit-0 fabrication with a whole-checker crash. **High, not
Critical.**

**Refuted:** `validate-p3.sh` and `validate-p4.sh` do **not** share the defect —
both use `2>&1`, so a crash becomes a visible FAIL. Verified by injection.

### 8.2 Patch review — `P1` and `P2`

| Patch | sha256[:16] | `git apply --check` | Shell syntax |
|---|---|---|---|
| `P1-validate-p2-exit-status.patch` | `247ef4f055a6cc56` | clean | OK |
| `P2-validate-sps2-exit-status.patch` | `0a90a2cefcca6be1` | clean | OK |
| `P3-validate-p3-exit-status.patch` | `3a334297cc716414` | clean | OK |
| `P4-validate-p4-negative-controls.patch` | `c9665a4cf08f6fff` | clean | OK |

`P1` is technically correct and avoids the subshell trap: it assigns
`out="$(python3 ... 2>&1)"; rc=$?` on the **same** line, so `rc` is captured in
the current shell rather than a subshell that is discarded.

**Negative-control matrix for `P1` (in a faithful `shutil.copytree` copy):**

| Case | Checker state | Result | Verdict |
|---|---|---|---|
| A | clean | `68 passed, 1 failed`, `22 correctly rejected, 0 missed` | unchanged |
| B | crashes | `FAIL sources: checker exited 1 - control could not run` | **now fails** |
| C | missing | `FAIL ... checker exited 2` | **now fails** |
| D | silent non-zero (`sys.exit(3)`) | `FAIL ... checker exited 3` | **now fails** |

Previously all of B/C/D printed fabricated PASSes.

**Regression check:** patched vs unpatched on the same clean tree gives
identical counts — `68 passed, 1 failed`, `22 correctly rejected, 0 missed`.
The patch converts fabricated PASSes into visible FAILs and **removes or weakens
no control**. The single clean-tree failure is the pre-existing `c11da27` pin.

**`P2` behaves identically:** clean `rc=0`, `79 checks passed, 0 failed, 27
negative cases enforced`; crash `rc=1`; silent-nonzero `rc=1`.

**Not applied.** These are protected files and no authorization exists (§12).

---

## 9. Attribution self-approval

### 9.1 Verified facts

`sps2/governance/attribution.py:144-162` is a **denylist**; acceptance is the
default when no token matches. `self` is deliberately excluded from the 17
approved tokens (DEC-0027, to preserve the surname "Self"). Measured:

| `decided_by` | Accepted |
|---|---|
| `"User"` | yes |
| **`"Self (self-approved)"`** | **yes** |
| `"Self"`, `"Jane Self"`, `"self"` | yes |
| `"Antigravity"`, `"Claude"`, `"the model"`, `"Assistant"`, `"AI"` | no |
| `""`, `None` | no |

`test_attribution_policy.py:407-424` asserts the acceptance with `assertTrue`
and labels it **"by design"** — so closing it is a governance change.

### 9.2 The larger finding — the execution gate ignores the decider entirely

`sps2/p17/__main__.py:379-384`, the real execution gate:

```python
if not approval or approval.get("state") != "APPROVED" \
        or approval.get("decided_by_role") != "USER":
```

**Zero** references to `attribution`, `AGENTISH`, or
`approval_is_user_attributable` in that file (verified by grep). The gate accepts
any `state == APPROVED` with a self-asserted `decided_by_role == "USER"`, so a
record reading `decided_by: "Self (self-approved)", decided_by_role: "USER"`
**passes the execution gate**. The self-approval problem is therefore not
confined to validators; it reaches the path that actually spawns work.

### 9.3 Prototype (proposal only, not applied)

Reject the self-approval **semantic phrase**, not the bare word:

```python
SELF_REFERENT = re.compile(
    r"\bself[-\s]?approved\b|\bself[-\s]?approval\b|"
    r"\bapproved\s+by\s+self\b|\bself[-\s]?authori[sz]ed\b", re.I)
```

Composed with the existing denylist, across 17 inputs **exactly one behaviour
changes**:

| `decided_by` | Current | Proposed |
|---|---|---|
| `"Self (self-approved)"` | accept | **reject** |
| `"User"`, `"Self"`, `"Jane Self"`, `"Marcus Self"`, `"self"` | accept | accept (unchanged) |
| `Antigravity`, `Claude`, `the model`, `Assistant`, `AI`, `Cursor`, `Codex`, `Gemini`, `ChatGPT`, `Cline`, `Copilot`, `opencode` | reject | reject (unchanged) |

It also rejects `"Self-approved"`, `"SELF APPROVED"`, `"self approval"`,
`"approved by self"`, `"Self (self-authorised)"`.

**Adding `self` to the token list must not be done** — it would reject
`"Jane Self"` and violate DEC-0027. The policy file requires a User decision
record to add or remove a token.

---

## 10. D-17 independent review and mutation results

An independent verifier that did not write the fix reviewed it read-only.

**Verdict: fix SOUND. Test NON-VACUOUS. Causality proven.**

- `D-P3-D` confirmed genuinely APPROVED by User on 2026-10-04, quoted verbatim.
- The one-line change makes `generic` consistent with the empty-registry
  exemption `count_ok` already carried.

| Case | rc | `RECORD_OVERSTATES_P3` |
|---|---|---|
| empty registry | 0 | absent — **accepted** |
| codex+opencode, no `generic` | 1 | **present — rejected** |
| normal registry | 0 | absent |
| **predicate reverted + empty** | 1 | **present — fails again** |

The fourth case is the causal proof: reverting only that line restores the
failure, so the fix — not incidental behaviour — makes D-P3-D pass.

**No over-acceptance found** across five further shapes (unknown 4th adapter,
3 real adapters, generic-only, downgraded generic, downgraded opencode) — all
still rejected.

**No checker-crash interaction:** `validate-p7-readiness.py` contains **zero**
subprocess calls, so it cannot fabricate a PASS from an ignored exit status.

**Caveat accepted and escalated as DP-6:** the regression test is **not wired
into any runner**. It is absent from `portability.py` `CORE_VALIDATORS` (which
lists `sps2/tests/test_p5.py` as the precedent) and from `validate-sps2.sh`, and
it is untracked, so CI cannot see it. It runs only by explicit invocation.

---

## 11. CI integrity

| Fact | Verified |
|---|---|
| Discovers modules via `git ls-files 'test_*.py' '**/test_*.py'` (line 129) | yes |
| Excludes `test-portability.py` / `test-history-credential-check.py` (hyphen, standalone) | yes |
| `MIN_TESTS=500` (line 147) | yes |
| Exit-code propagation: `set +e`, `STATUS=$?`, `exit "$STATUS"` | correct |
| **No shell validator executes in CI** | yes — zero references under `.github/` |
| **No GitHub Actions run ever observed** | yes |

**Module-deletion exposure (measured per-module, not estimated):**

| Module | Tests | Deletion caught by `MIN_TESTS=500`? |
|---|---|---|
| `test_attribution_policy.py` | 68 | **yes** (558−68 = 490 < 500) |
| `test_p17_security.py` | 62 | **yes** |
| 24 others | ≤58 | **no — CI stays green** |

Largest invisible modules: `test_p5.py` (48), `test_p17_lifecycle.py` (44),
`test_url_taxonomy.py` (42).

**Correction to my own prior report (C4).** I previously wrote that *any* single
module could be deleted undetected. That is wrong: the two largest are caught.
The accurate figure is **24 of 26 invisible**.

**Per-module guard — prototyped and proven in `/tmp` (proposal, not applied).**
Instead of a total threshold, compare executed modules against the expected set
parsed from `unittest -v` output:

| Case | Old guard | Proposed guard |
|---|---|---|
| healthy (26 modules) | PASS | PASS |
| delete `test_p17_pinning.py` (25 tests → 537 ran) | **PASS (wrong)** | **FAIL** |
| delete `test_attribution_policy.py` (68 → 494) | FAIL | FAIL |
| zero tests discovered | FAIL | FAIL |

The prototype correctly detects the exact case the threshold misses.

---

## 12. Governance reconciliation

### 12.1 Major correction — the CI/migration authorization EXISTS

The prior report asserted "zero in-repo authorization instrument" for the CI job
and the `.sps/tools` validator migration (gate G14, DP-10). **That is refuted.**

The instrument is `reports/SPS2-PHASE3-DECISION-EXECUTION-20261016-082741.md`:

- *"### Decision 1 — APPROVED: commit the three `.sps/tools` migrations +
  checker/test changes"* → *"Executed. Commit `238c9e4`, exactly the 6 authorized
  files"*
- *"### Decision 4 — APPROVED: add the Python unittest CI job"* → *"Executed,
  then committed as `cdcbca8` … `98 insertions(+), 0 deletions(-)`"*

I verified independently:

- `238c9e4` **is** an ancestor of HEAD; `cdcbca8` **is** HEAD.
- The attribution hash pair in Decision 3 matches exactly: HEAD
  `de2cc583341d993b` → worktree `b6c21d73cea2290f`.
- `cdcbca8` is a pure addition (`+98/−0`) — nothing was weakened to add it.
- `SPS2-PHASE2-RELEASE-READINESS-...:§21.4` corroborates CI was gated before
  approval ("should be authorized by a User-scoped decision record, not slipped
  in as an agent change").

**The real defect is retention, not absence:** `git ls-files reports/` returns
**0 files**. A fresh clone has zero traceability. **G14 still fails — for
retention.** DP-10 should be re-scoped accordingly.

### 12.2 Authorization status of all five worktree-only fixes

| # | Change | Status | Basis |
|---|---|---|---|
| 1 | `attribution.py` (+57/−0) | **AUTHORIZED** | Phase 3 Decision 3, hash-verified |
| 2 | `RESUME.md` completion | **DERIVATIVE** | faithfully restates the verified `completion` block (APPROVED/User/2026-10-05) |
| 3 | `test_p17_security.py` (+48/−1) | **ordinary engineering authority** | test-only; adds cleanup + assertions |
| 4 | `test_p17_pinning.py` (+77/−7) | **ordinary engineering authority** | fixes a real `setattr` no-op |
| 5 | `validate-p7-readiness.py` (+8/−1) | **AUTHORIZED** | implements APPROVED D-P3-D |

No unauthorized governance change was found among them. None is committed.

### 12.3 DEC-0001 vs the remote

`DEC-0001` (APPROVED, User, 2026-10-03) says: *"Initialise a new local Git
repository … with **no remote configured**"* and *"No push may be attempted,
and no remote may be invented, until the user issues a new explicit
instruction."* But `origin` exists and local push logs record **4**
`update by push` entries (3 on `origin/main`, 1 on the branch).

**Fact:** the decision is contradicted by the remote's existence and by local
reflog evidence. **Uncertain:** whether objects actually reached GitHub (the
remote was deliberately never contacted), and whether an out-of-band instruction
covered the pushes — absence of evidence is not evidence of absence.

### 12.4 DEC-0002 identity premise

`DEC-0002` defers identity replacement *because* "`DEC-0001` resolves to
`KEEP_LOCAL_ONLY`, no push can occur." The premise is now false. Of 138 commits,
**136** carry the placeholder `SPS Governance (local) <sps-governance@local.invalid>`;
the global identity is `SHAHID8142 <shahiddesignhouse@gmail.com>`, which the
repository does not use. The standing obligation appears **due but undischarged**.

### 12.5 Stale `note`

`ROADMAP-P3-DECISIONS.json:7` says completion "remains PENDING" while the
`completion` block is `APPROVED` / `User` / `2026-10-05` / `pending: []`.
History pins it precisely: `df2a715` wrote both; `cac77b6` flipped only the
completion block; `git log -S 'remains PENDING'` returns **only `df2a715`** — the
note was never updated. **Cosmetic**, not normative.

### 12.6 P5 edits

`P5-REQUIREMENTS.json` (+9/−1) and `P5-EVIDENCE.json` (+5/−2) add
`[SPEC-2 CORRECTION 2026-10-15]` annotations with `"state_changed": false`.
`verification.state` stays `VERIFIED`. **No authorizing decision exists** — there
is no `P5-DECISIONS.json`, and `ATTRIBUTION-POLICY-DECISIONS.json:209` *lists*
the file as **forbidden scope**, not authorization. Whether annotating a
VERIFIED requirement's `observed_result` is governed remains an open User
question.

### 12.7 `.sps/GOVERNANCE.md` structural defect (verified)

Fence at **line 93** opens a block that closes only at **line 198**, so
**§4 Evidence Rules, §5 Decision Records, §6 Handoff Contract, §7 Secret Safety,
§8 Scope Control, §9 Project-Local State Rule** all render as literal code.
Corroborating evidence: the orphan fragment `approval (user)` at line 197.

**Mechanical, not normative** — the rule text is intact and
`validate-governance.sh` reads raw text. But §8's out-of-scope list and §5's
supersession rule are exactly the text agents cite. `.sps/GOVERNANCE.md` is
**protected** (`da0b64afcb943c05`), so I did not fix it.

### 12.8 Pending decisions (verified)

`PENDING_USER_APPROVAL` / `PROPOSED`: **DEC-0029, DEC-0030, DEC-7101, DEC-7102,
DEC-7103, DEC-7104, DEC-7110, OPEN-DECISION-ATTRIBUTION-TOKEN-SET**.
Additionally `DEC-0023` and `DEC-0024` carry **no approval.state field at all**.
Open UQs: **UQ-ATT-1** (partially resolved — exclusion half only), **UQ-ATT-2**,
**UQ-LEGACY-01/02/03** — all unresolved. Note `UQ-ATT-1` appears in **four**
files with differing status text; ids are not unique.

---

## 13. Remaining release blockers, ranked

| # | Blocker | Severity | Why it blocks |
|---|---|---|---|
| 1 | **No validator executes in CI, and no CI run has ever been observed** | Critical | The false-PASS defects cannot be caught; CI is unproven |
| 2 | **P2/SPS2 fabricate PASS on a dead checker** | High | A green verdict can be produced by a checker that never ran (DP-1) |
| 3 | **P17 execution gate ignores the decider** | High | `Self (self-approved)` + `decided_by_role: USER` authorizes execution |
| 4 | **Attribution accepts self-attributed approval** | Medium (latent) | 0 current records exploit it; pinned as "by design" (DP-3) |
| 5 | **Portability harness red (34/5)** | High | All five are `REQ-P3-08`, reserved to the User (DP-2) |
| 6 | **All five fixes worktree-only** | High | Every clone and CI run sees none of it (DP-9) |
| 7 | **CI guard misses 24 of 26 modules** | Medium | A module can vanish silently (DP-7) |
| 8 | **`DEC-0001` contradicted by the remote** | Medium | Records describe a state the repository does not satisfy (DP-5) |
| 9 | **CI/migration authorization untracked** | Medium | Zero traceability in any clone (DP-10) |
| 10 | **P5 edits lack a located authorization** | Low | Annotations only; state/approval untouched (DP-4b) |
| 11 | **`GOVERNANCE.md` §4–§9 render as code** | Low | Mechanical; enforcement unaffected (DP-11) |

---

## 14. User decision packet

Only decisions the repository cannot answer. Each is independent.

**DP-1 — Protected validator repairs.**
*Question:* authorize changing `validate-p2.sh` and `validate-sps2.sh` so a dead
checker fails? *Evidence:* 7 fabricated PASSes reproduced; P1/P2 verified across
clean/crash/missing/silent-nonzero with no control weakened and identical clean
counts. *Options:* (a) P1+P2; (b) all four; (c) none. *Recommended:* (b).
*Files:* four `sps2/tools/validate-*.sh`. *Risk if deferred:* a green verdict
from a checker that never ran. *Safe work meanwhile:* everything else.

**DP-2 — `REQ-P3-08` legacy-path criterion.**
*Question:* how should the legacy-path set be defined, given that all five
harness failures trace to it? *Evidence:* predicate emits the same four paths
with or without adapters; **DEC-0030 would not fix it** (it names `.sps/tools/`);
`DEC-0030` says changing a pathspec "is a SEPARATE decision … would require its
own explicit authorization." *Options:* (a) narrow `.sps/tools/` **and** decide
`.github/`; (b) move the baseline; (c) formally accept the five as known.
*Recommended:* (a) with the exact pathspec recorded. *Risk if deferred:* the
harness cannot distinguish a real legacy regression from permanent noise.

**DP-3 — Self-approval rejection.**
*Question:* adopt the narrow phrase rule, and make the P17 gate consult the
predicate? *Evidence:* prototype changes exactly one behaviour across 17 inputs;
`p17/__main__.py` has zero attribution references. *Recommended:* both.
*Must not do:* add `self` to the token list (violates DEC-0027).
*Note:* the pinning test asserts current behaviour is by design, so it must be
consciously re-scoped.

**DP-4 — P5 annotations.** *Question:* are the `SPEC-2 CORRECTION` annotations
ordinary authority or a governed edit? *Evidence:* additive, `state_changed:
false`, no authorizing decision, listed as forbidden scope elsewhere.
*Recommended:* a short scope ruling.

**DP-5 — DEC-0001 vs the remote.** *Question:* ratify remote usage, or record the
pushes as an incident and reaffirm local-only? *Evidence:* remote exists; 4 local
push reflog entries; DEC-0001 requires a new explicit instruction before any
push. *Recommended:* your determination — I will not infer intent.

**DP-6 — Register the D-17 test.** *Question:* add
`test_p7_zero_adapter_readiness.py` to `CORE_VALIDATORS` / `validate-sps2.sh`, or
is by-name invocation intended? *Risk if deferred:* the D-17 regression never
runs automatically. *Files:* `validate-sps2.sh` is protected.

**DP-7 — CI guard + validator coverage.** *Question:* adopt the per-module guard
and add validator steps? *Evidence:* prototype proves it catches the
small-module deletion that `MIN_TESTS=500` misses; zero validators run today.
*Recommended:* both.

**DP-8 — Git identity.** *Question:* replace the repository-local placeholder?
*Evidence:* 136/138 commits placeholder; DEC-0002's premise is false.
*Recommended:* decide only after DP-5.

**DP-9 — Commit the verified fixes.** *Question:* authorize one narrow commit of
exactly: `sps2/RESUME.md`, `sps2/tests/test_p17_security.py`,
`sps2/tests/test_p17_pinning.py`, `sps2/tools/validate-p7-readiness.py`,
`sps2/tests/test_p7_zero_adapter_readiness.py`? *Evidence:* a clone of `cdcbca8`
contains none of them and still reports `PENDING_USER_APPROVAL`.
*Recommended:* yes, one commit. The four pre-existing user edits must be
excluded.

**DP-10 — Durability of the authorization instrument.** *Question:* commit
`reports/` (or record the CI/migration decisions as a decision record) so
traceability survives a clone? *Evidence:* `git ls-files reports/` = 0 files, yet
the Phase 3 report is the only instrument naming `238c9e4` and `cdcbca8`.
*Recommended:* a durable decision record. **This supersedes the prior DP-10
premise** — authorization was never absent, only untracked.

**DP-11 — `GOVERNANCE.md` fence.** *Question:* authorize closing the line-93
fence so §4–§9 render? *Evidence:* six sections render as code; enforcement
unaffected. *Recommended:* yes, mechanical edit.

---

## 15. Commands and reproducible evidence

```bash
# tracked corpus
MODS=$(git ls-files 'test_*.py' '**/test_*.py' | grep -E '^(sps2|domain)/' \
       | sed 's/\.py$//;s#/#.#g' | sort)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $MODS
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $(echo "$MODS" | sort -r)   # reversed

# full worktree
ALL=$( (git ls-files 'test_*.py' '**/test_*.py'; \
         find sps2 domain -name 'test_*.py') | sort -u \
       | grep -E '^(sps2|domain)/' | sed 's/\.py$//;s#/#.#g')
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $(echo "$ALL")

# portability harness (self-isolating)
PYTHONDONTWRITEBYTECODE=1 python3 sps2/tools/test-portability.py

# P7 readiness
python3 sps2/tools/validate-p7-readiness.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_p7_zero_adapter_readiness

# clean clone
git clone -q --no-hardlinks . /tmp/r3-clone && cd /tmp/r3-clone && git checkout -q cdcbca8

# faithful disposable copy (NEVER use git archive: it omits .git and breaks
# repository_has_licence(), producing misleading ASSESSMENT_STALE errors)
python3 - <<'PY'
import sys, os, importlib.util
sys.path.insert(0, os.path.join(os.getcwd(), "sps2", "tools"))
spec = importlib.util.spec_from_file_location("PT", "sps2/tools/portability.py")
PT = importlib.util.module_from_spec(spec); spec.loader.exec_module(PT)
tree = PT.copy_tree(os.getcwd(), "/tmp/r3-tree/tree")   # shutil.copytree, .git kept
PT.apply_delete_all(tree)                               # zero-adapter state
PY
```

**Do NOT run** the real `.sh` validators against the working tree — they mutate
evidence/registry state. Use disposable copies.

---

## 16. Final Git-state comparison

| Property | Baseline | Final | Verdict |
|---|---|---|---|
| HEAD | `cdcbca8` | `cdcbca8` | unchanged |
| Branch | `build/roadmap-p3-completion` | same | unchanged |
| Staged / stash | 0 / 0 | 0 / 0 | clean |
| Modified tracked | 11 | 11 | unchanged |
| Untracked | 109 | 109 | unchanged |
| Deletions | 0 | 0 | none |
| Protected hashes | 7 recorded | all INTACT | preserved |
| Prior reports | 7 | 7 | none overwritten |
| Remote contact | none | none | complied |

All `/tmp` artifacts are disposable copies; the repository itself was never
mutated this round.

---

## 17. Known limitations and untested environments

- **No GitHub Actions run was observed.** Every CI result here is local
  simulation. Pushing is prohibited; the remote was never contacted.
- **Python 3.12 / Ubuntu not verified locally.** All runs are macOS with Python
  3.14.7; CI targets 3.12. Behaviour is not inferable across that gap.
- **Single-platform.** No Linux or Windows validation; no portability claim
  beyond macOS. macOS also lacks GNU `timeout`, which broke one early command.
- **`P17_AJV_ROOT` unset** → the JSON-schema conformance test skips. Claiming
  schema conformance requires that tool.
- **The D-17 fix was reviewed by one independent verifier**, not two.
- **The CI guard is a prototype** proven in `/tmp`; it is not in the workflow.
- **Per-module counts** were obtained by running modules standalone; a module
  that failed to import would report 0 and be misclassified. All 26 imported
  cleanly, but a production guard should assert imports separately.
- **Whether the pushes reached GitHub is undetermined** — deliberately, since
  contacting the remote was prohibited.
- Two of six permitted subagents were used; the rest was resolved by direct
  experiment.

---

## 18. Machine-readable summary

```json
{
  "report": "SPS2-FINAL-REMEDIATION-20261016-111400",
  "mission": "SPS2 Final Remediation",
  "verdict": "NOT_READY",
  "mission_status": {
    "audit_completed": true,
    "remediation_implemented_this_round": false,
    "remediation_applied_uncommitted": true,
    "remediation_independently_verified": true,
    "changes_committed": false,
    "changes_published": false,
    "product_ready": false
  },
  "repository": {
    "branch": "build/roadmap-p3-completion",
    "head": "cdcbca83679844ea66196f25773f42d9b64569ec",
    "head_unchanged": true,
    "staged": 0, "stash": 0,
    "modified_tracked": 11,
    "untracked_file_level": 109,
    "deletions": 0,
    "fsck_errors": 0,
    "remote_contacted": false,
    "protected_files_intact": 7,
    "preexisting_user_edits_intact": 4
  },
  "tests": {
    "worktree_tracked":   {"modules": 26, "ran": 562, "failed": 0, "skipped": 1, "exit": 0},
    "worktree_tracked_reversed": {"modules": 26, "ran": 562, "failed": 0, "skipped": 1, "exit": 0},
    "worktree_full":      {"modules": 30, "ran": 896, "failed": 0, "skipped": 1, "exit": 0},
    "clean_clone":        {"modules": 26, "ran": 558, "failed": 0, "skipped": 1, "exit": 0},
    "clone_plus_p1_p2":   {"modules": 26, "ran": 558, "failed": 0, "skipped": 1, "exit": 0},
    "order_dependent": false
  },
  "portability": {
    "passed": 34, "failed": 5, "controls": 14, "exit": 1,
    "failures": [
      {"id": "F1", "check": "P2 research zero-adapter",  "cause": "c11da27_legacy_pin"},
      {"id": "F2", "check": "P3 production zero-adapter","cause": "c11da27_legacy_pin"},
      {"id": "F3", "check": "P4 promotion zero-adapter", "cause": "c11da27_legacy_pin"},
      {"id": "F4", "check": "P5 implementation zero-adapter", "cause": "c11da27_legacy_pin"},
      {"id": "F5", "check": "P7 readiness mutations",    "cause": "c11da27_legacy_pin_via_p4_p5"}
    ],
    "single_root_cause": true
  },
  "defects": {
    "D17_p7_zero_adapter": {
      "status": "FIXED_UNCOMMITTED_INDEPENDENTLY_VERIFIED",
      "fix_verdict": "SOUND",
      "test_verdict": "NON_VACUOUS",
      "causal_proof": "revert_one_line_restores_failure",
      "authorization": "APPROVED_D_P3_D",
      "wired_into_runner": false
    },
    "D18_p2_sps2_false_pass": {
      "status": "REPRODUCED_NOT_FIXED",
      "severity": "high",
      "protected": true,
      "patch_verified": true,
      "patch_applied": false,
      "blocker": "DP-1",
      "p3_p4_affected": false
    },
    "D19_attribution_self_approval": {
      "status": "REPRODUCED_NOT_FIXED",
      "severity": "medium_latent",
      "predicate_accepts": "Self (self-approved)",
      "p17_gate_consults_predicate": false,
      "prototype_verified": true,
      "blocker": "DP-3"
    },
    "D20_ci_no_validator_no_run": {
      "status": "CONFIRMED_NOT_FIXED",
      "severity": "critical",
      "validators_in_ci": 0,
      "gha_runs_observed": 0,
      "min_tests": 500,
      "test_count": 558,
      "modules_deletable_invisibly": 24,
      "modules_total": 26
    }
  },
  "corrections_to_prior_reports": [
    {"id": "C1", "claim": "zero_authorization_instrument_for_ci_migration",
     "status": "REFUTED", "truth": "instrument exists at reports/SPS2-PHASE3-DECISION-EXECUTION-20261016-082741.md; reports/ is untracked"},
    {"id": "C2", "claim": "F5_is_p7_zero_adapter_issue",
     "status": "CORRECTED", "truth": "F5 is the same c11da27 pin via p4/p5 sub-tests"},
    {"id": "C3", "claim": "DEC0030_would_help_clear_pin_failures",
     "status": "CORRECTED", "truth": "DEC-0030 names .sps/tools/ so it would not fix them"},
    {"id": "C4", "claim": "any_single_module_deletable_invisibly",
     "status": "CORRECTED", "truth": "24 of 26 invisible; the two largest are caught"}
  ],
  "governance": {
    "pending_decisions": ["DEC-0029","DEC-0030","DEC-7101","DEC-7102","DEC-7103",
                          "DEC-7104","DEC-7110","OPEN-DECISION-ATTRIBUTION-TOKEN-SET"],
    "state_less_records": ["DEC-0023","DEC-0024"],
    "open_uq": ["UQ-ATT-1","UQ-ATT-2","UQ-LEGACY-01","UQ-LEGACY-02","UQ-LEGACY-03"],
    "new_approvals_found": 0,
    "newest_decided_on": "2026-10-08",
    "governance_fence_defect": {"file": ".sps/GOVERNANCE.md", "open_line": 93,
                                "close_line": 198, "sections_swallowed": 6,
                                "class": "mechanical", "protected": true}
  },
  "decision_packets": ["DP-1","DP-2","DP-3","DP-4","DP-5","DP-6","DP-7",
                       "DP-8","DP-9","DP-10","DP-11"],
  "shadow_heroes": {
    "git_archive_excludes_dot_git": "documented in §7; use shutil.copytree"
  }
}
```

---

## 19. Final recommendation

The mission's authorized engineering work is finished. **D-17 is the only fix
this line of work produced, and it is independently verified, causally proven,
and already applied.** No further authorized remediation exists in the
repository: every other open item is either a protected file, a governance
record, or a normative criterion — all reserved to the User.

The product remains `NOT_READY`, and the gap is governance, not capability.
Two facts dominate:

1. **Nothing is committed.** All five verified fixes live only in this working
   tree; a clone of `cdcbca8` reproduces none of them. Until **DP-9**, the
   engineering work in this repository has no effect on anything anyone else
   runs — including CI.
2. **CI has never run and executes no validator.** Even if the fixes were
   committed and the validator patches applied, the workflow as written would
   not exercise either. **DP-1** and **DP-7** are the pair that converts this
   work into real protection.

The fastest path to a genuinely usable SPS2 is therefore DP-9 and DP-1 together,
then DP-7, then DP-2 — each of which needs your explicit authorization, not
another round of analysis.

I did not commit, push, contact the remote, weaken a test, or cross an approval
boundary. Where I found my own prior reports wrong, I said so and showed the
evidence.
