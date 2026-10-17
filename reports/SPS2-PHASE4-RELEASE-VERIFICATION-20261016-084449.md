# SPS2 PHASE 4 — RELEASE VERIFICATION AND RESIDUAL RISK AUDIT

**Report ID:** SPS2-PHASE4-RELEASE-VERIFICATION-20261016-084449
**Branch:** `build/roadmap-p3-completion` · **HEAD:** `cdcbca83679844ea66196f25773f42d9b64569ec`
**Mode:** verification only. No commits, no staging, no push, no network, no destructive git, no fixes applied.
**Method:** six parallel workstreams at depth 1, with every material claim re-verified independently by the lead.

---

## 1. EXECUTIVE VERDICT

### Verdict: **NOT READY**

Not because the tests are broken — the committed corpus is genuinely green and reproducible. The
blockers are elsewhere:

1. **The release claim in the Phase 3 report contains a factually false statement.** It asserts
   "There is no remote (`DEC-0001 = KEEP_LOCAL_ONLY`)". A remote **does** exist
   (`origin` → `github.com/SHAHID8142/Shahid-Master-Skill.git`). This was my error and is corrected in §2.4.
2. **A genuine release-blocking defect is confirmed**: `sps2/RESUME.md` states
   `COMPLETION: PENDING_USER_APPROVAL` while `ROADMAP-P3-DECISIONS.json` is `APPROVED`, and
   `test-portability.py`'s `RESUME_COMPLETION_STATE_DRIFT` check fails on it.
3. **A second genuine defect**: `validate-p7-readiness.py` `p3_delivery_state()` reports
   `RECORD_OVERSTATES_P3` under the D-P3-D zero-adapter state.
4. **The portability harness reproduces at 32 passed / 7 failed, not the claimed 33/6.** The
   figure printed in the CI comment (`sps-ci.yml:176`) is stale.
5. **Two high-severity residual false-PASS patterns remain in protected validators** still
   unpatched in this repository (`validate-p2.sh:34`, `validate-sps2.sh:36`).
6. **The entire validator suite has no CI foothold** — it is reachable only from inside the
   excluded portability harness. 331 of 889 worktree tests (37%) cannot run in CI.
7. **CI has never executed.** Everything CI-related in this report is a *local simulation*.

### What IS verified green

| Claim | Status |
|---|---|
| Committed HEAD `cdcbca8` is green | **VERIFIED** |
| 29 modules / 889 ran / 888 passed / 0 failed / 1 skipped | **REPRODUCED EXACTLY** (worktree only) |
| Repository-reproducible figure | **26 modules / 558 ran / 557 passed / 0 failed / 1 skipped** |
| CI job body runs 558 tests and passes locally | **VERIFIED** (local only) |
| CI job correctly FAILS on a failing test | **VERIFIED** (local injection) |
| Committed checker fixes hold | **VERIFIED** byte-level |
| Attribution hardening (patch A) fails closed | **VERIFIED** |
| P9/P10 isolation green, `domain/seo/**` untouched | **VERIFIED** (4-config matrix) |
| No user work lost | **VERIFIED** (zero removals) |
| Only `"User"` ever named as approver | **VERIFIED** (202 values) |

---

## 2. VERIFIED REPOSITORY BASELINE

### 2.1 Identity and integrity

| Property | Value | Expected | Match |
|---|---|---|---|
| Branch | `build/roadmap-p3-completion` | same | YES |
| HEAD | `cdcbca83679844ea66196f25773f42d9b64569ec` | same | YES |
| `238c9e4`, `cdcbca8` present | both commits | yes | YES |
| Staged entries | 0 | 0 | YES |
| `git write-tree` | `60580087c109ae984b234d2971f009c73b48d126` | == `HEAD^{tree}` | YES |
| Merge/rebase/bisect in progress | none | none | YES |
| `git fsck` | exit 0, **zero** errors/missing/broken | clean | YES |
| Dangling objects | 323 (informational) | — | — |
| Stash entries | 0 | 0 | YES |

### 2.2 Workstream-independent reproduction of the test corpus

The lead reproduced the claimed result from the real worktree:

```
29 modules, ran=889, passed=888, failed=0, errors=0, skipped=1
VERDICT: CLAIM REPRODUCED EXACTLY
```

Command per module: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <dotted.module>` from the repo
root. `pytest` is not installed and was not installed.

### 2.3 Uncommitted change classification — and a correction

Seven tracked files are modified. Ownership was determined by mtime against the Phase 3 commit
window (Oct 16 06:02–08:27) and by decision-record citation:

| File | mtime | Classification | Evidence |
|---|---|---|---|
| `sps2/governance/attribution.py` | Oct 16 08:20 | **Authorized (Decision 3, patch A)** | sha256[:16] `b6c21d73cea2290f`, +57/−0, still uncommitted |
| `.sps/audits/README.md` | Oct 15 20:38 | Pre-existing user work | cites DEC-0028 (KI-15/KI-16 rows) |
| `sps2/decisions/P10-DECISIONS.json` | Oct 14 18:12 | Pre-existing user work | +211/−1, adds D-P10-6/7/8 |
| `sps2/schemas/p10-slice.schema.json` | Oct 15 14:01 | Likely pre-existing | matches D-P10-9 clause 5 |
| `sps2/requirements/P10-SECTION-INVENTORY.json` | Oct 13 17:09 | Likely pre-existing | consistent with D-P10-7 |
| `sps2/evidence/P5-EVIDENCE.json` | Oct 15 13:58 | **Pre-existing; traceability gap** | see below |
| `sps2/requirements/P5-REQUIREMENTS.json` | Oct 15 13:58 | **Pre-existing; traceability gap** | see below |

**Correction to a workstream finding.** WS1 flagged the two P5 files as "uncertain — action needed
before Phase 4 treats them as sanctioned." That is right as a *traceability* observation but
misleading as an *ownership* one: both carry mtime **Oct 15 13:58**, before this mission began, and
neither appears in any Phase 3 commit. They are **pre-existing user work, not agent changes**.

Their content is a self-documenting SPEC-2 correction that preserves the original text verbatim and
explicitly does not change `result` or `state`:

> `[SPEC-2 CORRECTION 2026-10-15: the final clause is factually wrong. 'self' is NOT rejected ...]`
> `"state_changed": false`

So the edits are honest and non-normative in effect. The **residual issue is real but narrow**: no
User decision record authorizes editing these two files, and `P5-REQUIREMENTS.json` is a normative
artifact. This is a **governance traceability gap (Medium)**, not a defect and not an agent change.

### 2.4 CORRECTION — the remote statement in the Phase 3 report was false

The Phase 3 decision-execution report states:

> "There is no remote (`DEC-0001 = KEEP_LOCAL_ONLY`), so no GitHub Actions run has been observed."

**This is factually wrong.** `git remote -v` returns:

```
origin  https://github.com/SHAHID8142/Shahid-Master-Skill.git (fetch)
origin  https://github.com/SHAHID8142/Shahid-Master-Skill.git (push)
```

A remote is configured and was **not** contacted (no fetch, no push, no `ls-remote`). Consequences:

- The claim "no remote exists" must be **retracted**. The correct statement is "no remote
  communication was performed, and no CI run has been observed."
- The three commits are genuinely unpushed: ahead 3 / behind 0 against the **local** cached
  `origin/build/roadmap-p3-completion` ref (`788bf8a…`).
- The untracked audit file `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md` independently records
  push history on `origin/main`, so `DEC-0001 KEEP_LOCAL_ONLY` appears to have been outrun by
  reality. Resolving that is a **User decision**; this report only records it.

### 2.5 Protected validators — unchanged

All protected hashes match the pre-mission baseline exactly:

| File | sha256[:16] |
|---|---|
| `sps2/tools/validate-p2.sh` | `9018e0de53abe5a1` |
| `sps2/tools/validate-sps2.sh` | `91509870f3d02b87` |
| `sps2/tools/validate-p3.sh` | `c6ca659a7c495c87` |
| `sps2/tools/validate-p4.sh` | `74af33ca7617494e` |
| `sps2/governance/attribution_policy.json` | `eb9f113360601059` |

The disposable clone `/tmp/sps2-phase4-disposable-1792117248` still holds the four patched files
(`validate-p2.sh`, `validate-sps2.sh`, `validate-p3.sh`, `validate-p4.sh`); the real repository has
**none** of them. Isolation is intact.

---

## 3. FULL TEST RESULTS WITH EXACT COMMANDS

### 3.1 Committed HEAD — clean clone control

A fresh local clone (`git clone --no-hardlinks . <tmp>`, **no network**) of `HEAD` was tested. This
is the artifact a CI runner would receive.

| Module | Result |
|---|---|
| `sps2.tests.test_shell_validator_policy_contract` | `Ran 7 — OK` |
| `sps2.tests.test_attribution_policy` | `Ran 68 — OK` |

The previously-RED committed HEAD (`320d3a5`: `Ran 7 — FAILED (failures=3)`) is genuinely resolved
by commit `238c9e4`.

### 3.2 Real worktree — full corpus

```
29 modules, ran=889, passed=888, failed=0, errors=0, skipped=1
```

Wall-clock approximately 66 seconds across two independent sweeps (72s and 66s). The two arms of this
mission — the lead's sweep and an independent workstream's — produced **identical** totals with zero
discrepancies. Corroborated independently by a third sweep whose raw per-module data was summed by the
lead (§3.5).

**A real trap, recorded so it is not repeated.** A test runner that infers skips from the exit code
(`rc == 0 ⇒ no skips`) reports `889 ran / 889 passed / 0 failed / 0 skipped` and appears to contradict
the claimed result. **The skip occurs on an `rc == 0` run.** Skip counts must be parsed from the
`skipped=N` field on stdout regardless of exit status. The claimed figure is correct; the
exit-code-derived figure is the artifact.

**The single skip is environment-driven and is not a defect.** It is

```
sps2.tests.test_p17_endtoend.test_generated_record_conforms_to_the_approved_schema
```

skipped because `P17_AJV_ROOT` is unset (verified unset; `node` *is* present at `/usr/local/bin/node`).
The skip message states that the machine-global path is deliberately not hardcoded because the
project-local boundary rule forbids it inside `sps2/`, and that the runtime structural self-check still
ran. Deterministic, intentional, and repeatable.

One consequence worth stating precisely: `889` is stable only because the skip counts *inside* `Ran`.
With `P17_AJV_ROOT` set, the same corpus becomes `889 executed / 0 skipped`. The number `889` therefore
survives either configuration, but the skip total does not.

Key modules:

| Module | Result |
|---|---|
| `sps2.tests.test_attribution_policy` | `Ran 68 — OK` |
| `sps2.tests.test_shell_validator_policy_contract` | `Ran 7 — OK` |
| `domain.seo.tests.test_isolation` | `Ran 20 — OK` |
| `sps2.tests.test_p10_runtime_gate` | `Ran 282 — OK` |
| `sps2.tests.test_p5` | `Ran 48 — OK` |
| `sps2.tests.test_p17_security` | `Ran 60 — OK` |

### 3.3 CRITICAL FINDING — 37% of tests cannot run in CI

The CI job derives its module list from **tracked** files (`git ls-files 'test_*.py' '**/test_*.py'`),
which is correct for determinism. The consequence was not previously reported:

| | Modules | Tests |
|---|---|---|
| CI can collect (tracked) | 26 | 558 |
| Real worktree runs | 29 | 889 |
| **Invisible to CI** | **3** | **331 (37%)** |

The three invisible modules are exactly the files preserved untracked by **User Decision 5**:

| Untracked module | Tests |
|---|---|
| `sps2/tests/test_p10_runtime_gate.py` | 282 |
| `domain/frontend/tests/test_content_slots.py` | 25 |
| `domain/frontend/tests/test_layout_registry.py` | 24 |

This is **not a CI defect** — the job behaves as designed. It is a direct, previously-unstated
consequence of preserving those files untracked: **the 282-test P10 gate suite has no CI coverage at
all**, and a clean-clone CI has *zero* P9/P10 orphan coverage. Decision 5 must be revisited if CI
coverage of P10 is wanted.

**The most important framing consequence.** `889` and `558` are **not two measurements of the same
thing** and must never be conflated:

- **889** is the **worktree including uncommitted and untracked WIP**. It depends on files that exist
  only on this machine.
- **558** is what **any fresh clone and CI actually receive**.

A release claim of "889 tests passing" is therefore **not reproducible from the repository alone**. The
committed, clone-reproducible figure is **26 modules / 558 ran / 557 passed / 0 failed / 0 errors /
1 skipped**. Either sign off explicitly on the worktree-with-untracked-WIP basis, or commit the three
untracked modules and re-run to make 889 achievable from a clean clone.

### 3.4 Test-discovery limitation (confirmed)

`python3 -m unittest discover` is **unusable as a gate** here. The lead recorded these exact exit codes:

| Command | Result | Exit |
|---|---|---|
| `discover -s . -p 'test_*.py'` | `Ran 0 tests`, `NO TESTS RAN` | **5** |
| `discover -s sps2 -t .` | `ImportError: Start directory is not importable` | **1** |
| `discover -s domain -t .` | same `ImportError` | **1** |
| `discover -s domain/cms/tests -t .` | 86 tests — covers `domain/cms` **only** | 0 |

Root cause: `__init__.py` is **absent** in `sps2/`, `sps2/tests/` and `domain/`, but **present** in
`domain/{cms,seo,frontend}[/tests]`. The discovery walker is stricter than ordinary namespace-package
import, which is why dotted per-module names work while discovery does not.

**Exit-code masking confirmed.** `discover … | tail -3` returns **pipeline exit 0** while the raw
command exits **5**, because the shell reports the last pipeline element's status. That is a green
looking, zero-test, meaningless gate — the most dangerous shape a gate can take.

The CI job's refusal to use `discover`, its `git ls-files` derivation, and its `MIN_TESTS` guard are
therefore **correct and necessary**, and the comment at `sps-ci.yml:116-121` documents this accurately.

### 3.5 Independent per-module corroboration

An independent workstream captured per-module `ran/failures/errors/skipped/duration` for both the
worktree and a clean clone. The lead summed that raw data directly rather than trusting a summary:

| Environment | Modules | Ran | Passed | Failed | Skipped |
|---|---|---|---|---|---|
| Worktree | 29 | 889 | 888 | 0 | 1 |
| Clean clone | 26 | 558 | 557 | 0 | 1 |

Module-set difference, computed by the lead: **exactly the three modules above, and zero clean-only
modules**. `889 − 558 = 331 = 282 + 25 + 24` exactly.

### 3.6 Determinism, ordering and isolation

| Test | Result |
|---|---|
| Two largest modules, run twice | identical (`282 OK` / `282 OK`; `68 OK` / `68 OK`) |
| **All 29 modules in one shared process, sorted** | `889 ran / 0 failed / 1 skipped` |
| **All 29 modules in one shared process, reversed** | `889 ran / 0 failed / 1 skipped` |

The corpus is **order-independent** — a stronger result than per-module repetition. No flakiness was
observed across five full or partial sweeps plus all re-runs.

**Pinned-revision tests are clone-safe.** `test_attribution_policy.py:49` pins `BASELINE_REV` to
`788bf8a…`; in the clean clone that object resolves (`git cat-file -t` → `commit`) and the four
`TestKnownDivergencesAreAccurate` methods pass. This independently confirms that CI's `fetch-depth: 0`
is **mandatory**.

**Slowest modules** (worktree): `domain.seo.tests.test_isolation` 31.66 s (48% of the sweep),
`test_p17_lifecycle` 17.26 s, `test_p17_security` 7.20 s, `test_attribution_policy` 5.31 s. The top four
account for ~93% of wall-clock; the remaining 25 modules each run in under 0.55 s. This matters for CI
timeout budgeting (`timeout-minutes: 15`).

### 3.7 NEW FINDING — two tests leak into the process environment (Low, latent)

An environment audit found seven `os.environ[...] =` assignments in the test tree. Five restore
themselves via `addCleanup`; **two do not**:

| Site | Assignment | Restored? |
|---|---|---|
| `sps2/tests/test_p17_security.py:255` | prepends a temp dir to `PATH` | **NO** |
| `sps2/tests/test_p17_security.py:538` | sets `P17_FAKE_PARENT_SECRET` | **NO** |

The lead **empirically confirmed the leak** in a shared process:

```
PATH_CHANGED:   False
SECRET_LEAKED:  True
```

Assessment: **Low severity, latent.** It does not affect any current result — the corpus is
order-independent under sorted and reversed single-process runs, so no test depends on the leaked
state, and `:255` only *prepends* a temp directory so lookups still resolve. The leaked variable name is
a deliberate test fixture (`must-not-be-inherited`) asserted absent from the explicitly-built minimal
environment, not a real credential. The genuine hazard is forward-looking: a future in-process collector
(for example a `pytest` migration) would inherit the mutated environment between modules.

**Not fixed** — outside this mission's read-only remit. Proposed as packet **P-D13** in §13.

### 3.8 Discovery-omission inventory — nothing silently missed

The corpus covers **all 29** Python `unittest` modules present. Every deliberate exclusion is a
non-`unittest` artifact, verified as such:

| Excluded artifact | Count | Why excluded |
|---|---|---|
| `sps2/tools/test-portability.py`, `test-history-credential-check.py` | 2 | Standalone scripts with their own `main`/exit contract; zero `unittest` references. Not run in the corpus; both were executed separately (§5, §6). |
| `test-secret-safety.sh`, `test-p7-readiness-mutation.sh`, `test-phase-boundary.sh`, `test-snapshot-integrity.sh` | 4 | Bash harnesses that **mutate real registry/decision files**; excluded to honour read-only boundaries. |
| `test_claude.sh`, `test_timeout.sh`, `test_uiux.sh` | 3 | Ad-hoc root probes that invoke the `claude` CLI and/or the network. Never run. |
| `sps2/tests/fixtures/p17/test-allowlist.json` | 1 | A fixture, not a test. |

The 331-test CI gap (§3.3) is the *only* coverage shortfall, and it is a tracking decision, not a
discovery failure. No `test_*.py` module was silently missed.

---

## 4. CI AUDIT

### 4.1 What the job does — verified correct

Locally executed verbatim body (`sps-ci.yml:114-173`) in a disposable clone:

```
26 modules found
Executed test count: 558 (minimum required: 500)
unittest exit status: 0
guard pass: YES
```

Red-path also verified: injecting a failing **tracked** test produced `Ran 559 — FAILED`, exit 1,
propagating unittest → `$STATUS` → `exit $STATUS` → step → job.

**Exit-status capture is correct.** `OUTPUT="$(...)"` and `STATUS=$?` sit on adjacent lines in the
same shell (`sps-ci.yml:149-152`), so the subshell-status-loss bug class is absent. Guard ordering
is sound: zero-check → minimum-check → status-check.

| Verified property | Result |
|---|---|
| Uses `set -euo pipefail` | YES (`:114`) |
| Zero-test guard (`RAN == 0` → fail) | YES |
| Minimum-count guard (`MIN_TESTS = 500`) | YES |
| Exit-status propagation | YES, correct |
| `fetch-depth: 0` | YES, and **necessary**: `test_attribution_policy.py:49` pins `BASELINE_REV` `788bf8a…`, unresolvable in a shallow clone |
| `pip install` / network | NONE |
| Three pre-existing jobs | byte-unchanged (98 insertions, 0 deletions) |
| Triggers | `push`, `pull_request` |

### 4.2 Minimum-count guard is weak (Medium)

`MIN_TESTS=500` against an actual 558 leaves a gap of 58:

```
lose  48 tests -> RAN=510 -> guard PASSES (blind)   <- an entire module (test_p5) can vanish
lose  58 tests -> RAN=500 -> guard PASSES (blind)
lose  59 tests -> RAN=499 -> guard FAILS (caught)
```

An entire module — or 10.2% of the suite — can disappear without the gate noticing. The guard is
adequate as an anti-catastrophe floor but is **not** a suite-integrity gate. Recommended (not
implemented): assert every module in `MODULES` contributes `Ran > 0`, or derive the floor from
`${#MODULES[@]}`.

### 4.3 FALSE-GREEN REGISTER

**One workstream finding was REFUTED and must not be repeated.** WS3 reported CRITICAL that the
`|| true` at `sps-ci.yml:61-63` means "even when the guard fires, the step is green." This is
**wrong.** `exit 1` is a shell builtin that terminates the process immediately; it is never
"returned" to the `||` operator. The lead executed the verbatim block three ways:

| Fixture | Result |
|---|---|
| `--profile` planted in `install.sh` | printed the marker, **rc=1** → step FAILS correctly |
| `Profile` planted in `install.ps1` only | second guard fired, **rc=1** |
| all clean (today's state) | **rc=0**, correct: nothing to find |

`|| true` correctly rescues only the *no-match* case (grep rc=1), which is exactly its purpose. The
guards work. **No retraction of the CI commit is warranted.**

Remaining **genuine** observations (all pre-existing, outside the new hunk, none introduced by
`cdcbca8`):

| Location | Severity | Finding |
|---|---|---|
| `sps-ci.yml:60-63` | Low | No `set -e`/`pipefail` in that block. Currently harmless because each line is independently guarded, but fragile. |
| `sps-ci.yml:42-53` (`version-sanity`) | Low | No `set -e`/`pipefail`; relies on last-command semantics. Currently correct. |
| `sps-ci.yml:66-69` | Informational | `grep -c '@(' … \| awk` pipeline without pipefail; value printed but never asserted, so no gate is lost. |
| `sps-ci.yml:176` | Medium | Comment records the **stale** portability figure `(33 passed, 6 failed, 14 controls)`. Actual is **32/7** (see §5). |

Explicitly **not** found anywhere in the file: `2>/dev/null`, `| tee`, gating `| tail`,
`continue-on-error`. The new job is the only place using `set -euo pipefail`.

### 4.4 What requires an actual CI run

**No real CI run exists.** There is no evidence of a GitHub Actions execution anywhere in the
repository. The following are *local simulations only* and must not be cited as CI evidence:

1. Any actual GitHub Actions execution.
2. `actions/checkout@v4`, `setup-python@v5`, the `ubuntu-latest` image (git/bash versions, shell flags).
3. **Python 3.12 specifically** — the host runs 3.14.7. The suite is green on 3.14.7 and under
   `-W error::DeprecationWarning`, and is stdlib-only, so risk is **Low**, but 3.12 was never executed.
4. The other three jobs (`lint-and-smoke` deliberately not run: `scripts/smoke-sps.sh` touches the environment).
5. GitHub-side branch protection / required checks.

---

## 5. PORTABILITY FAILURE ANALYSIS

### 5.1 The reported figure is wrong

`sps2/tools/test-portability.py` was run: **exit 1, 32 passed / 7 failed / 14 controls.**

The previously reported and still-commented figure of **33 passed / 6 failed** is **stale**. Both the
lead and an independent workstream reproduced 32/7. The stale number survives in the CI comment at
`sps-ci.yml:176`.

### 5.2 The seven failures, classified

| # | Check | Root cause | Class | Blocks release? |
|---|---|---|---|---|
| 1–4 | `copy: P2/P3/P4/P5 … not green with zero adapters (rc=1)` | Shared predicate `git diff --name-only c11da27 -- … .github …` flags `.github/workflows/sps-ci.yml`, added by `cdcbca8` **after** the pinned baseline `c11da27`. Fails identically in a pristine clone of committed HEAD. | **Pin-rot / pre-existing** | **NO** — but permanently prevents the harness from going green |
| 5–6 | `copy: P7 readiness not green` + `P7 readiness mutations not green` | `validate-p7-readiness.py` `p3_delivery_state()` requires the generic fallback adapter; under the D-P3-D zero-adapter state `delivered=False` while the record claims `SATISFIED` → `RECORD_OVERSTATES_P3` | **Genuine defect** | **YES (scoped)** |
| 7 | `RESUME_COMPLETION_STATE_DRIFT` | `cac77b6` set `ROADMAP-P3-DECISIONS.json` to `APPROVED` but never updated `sps2/RESUME.md`, which still reads `COMPLETION: PENDING_USER_APPROVAL` | **Genuine defect** | **YES (low effort)** |

Failure 7 was independently confirmed by the lead:

```
sps2/RESUME.md             -> COMPLETION: PENDING_USER_APPROVAL
ROADMAP-P3-DECISIONS.json  -> APPROVED  (set by cac77b6, which touched only 2 decision files)
```

### 5.3 Platform analysis — none of the seven are macOS artifacts

Every named cross-platform trap was checked and ruled out:

| Trap | Implicated? | Why |
|---|---|---|
| GNU `timeout` absent | **NO** | The harness uses Python `subprocess.run(timeout=900)`, not the `timeout` binary |
| `grep -P` unsupported on BSD | **NO** | Validators use `grep -E` only |
| BSD vs GNU `sed -i` | **NO** | Not implicated in any failure |
| `readlink -f` | **NO** | Not implicated |
| Case-insensitive filesystem, `.DS_Store` | **NO** | Not implicated |

All failures reproduce from **committed content**, making them repository properties rather than host
properties. **[INFERRED]** Ubuntu would also report 32/7 — this could **not** be measured (no Linux
host, no containers, no network).

### 5.4 A silent glob mismatch (Medium)

The CI glob uses an **underscore** (`test_*.py`); two tracked harness scripts use a **hyphen**:

```
git ls-files 'test_*.py' '**/test_*.py'   ->  0 files under sps2/tools/
git ls-files -- ':(glob)**/test-*.py'     ->  2 files:
    sps2/tools/test-history-credential-check.py
    sps2/tools/test-portability.py
```

Both files are tracked, so this is a **silent glob mismatch, not a missing file**. Consequence: any
future `test-<name>.py` added under a tool directory would be invisible to CI without warning.

---

## 6. HISTORY / CREDENTIAL CHECKER ASSESSMENT

**Location:** `sps2/tools/test-history-credential-check.py` (114 lines).

### 6.1 What it actually is — a correction to a prior report

A previous report (`SPS2-OVERNIGHT-BUILD-VERIFICATION…`) claimed this checker was **unsafe and out of
scope**. **That claim is false.** Inspection shows it scans **neither** real history **nor** the real
working tree. It is a **mutation test of the predicate**:

- It builds **four throwaway git repositories** under `tempfile.mkdtemp()` (`:29`), commits synthetic
  `.claude/settings.json` variants, and asserts that the `validate-p3.sh` §10 predicate classifies
  each correctly.
- It writes only inside its temp directory and cleans up with `shutil.rmtree(..., ignore_errors=True)`
  in a `finally` block (`:96`).
- **No network.** Verified by inspection.
- Exit contract: `0` = all four scenarios correct, `1` = unexpected.

**Safety verdict: SAFE to run.** The lead ran it with no repository effect.

### 6.2 Result — GREEN

```
=== mutation test: P3 history-credential check ===
  1 clean history                  rc=0 classified=False offenders=0 -> PASS
  2 preserved checkpoint only      rc=0 classified=True  offenders=1 -> PASS
  3 checkpoint + second offender   rc=1 classified=False offenders=2 -> PASS
  4 lone non-checkpoint offender   rc=1 classified=False offenders=1 -> PASS
RESULT: all 4 scenarios behaved as required      (exit 0)
```

Porcelain was unchanged afterwards (7 modified, as before). No artifacts left behind.

### 6.3 Detection scope — narrower than it appears

The predicate matches **key-name presence only**, against a four-name allow-list parsed from the JSON
`env` object. There is **no entropy analysis, no regex, and no value inspection**. Therefore:

- A secret stored under a different key name is invisible.
- A secret outside the `env` object is invisible.
- **A "clean" result does not mean "no secrets exist."** It means "no offending key names in `env`."

### 6.4 CI wiring — effectively never runs

It is **not** a workflow step. It is reachable only via `validate-p3.sh` (approximate line 386),
which is itself reachable only from inside the **excluded** portability harness. So the credential
predicate **never gates CI**. It is safe, fast, deterministic, and currently green — a good candidate
for direct wiring.

One caveat for any future wiring: a **shallow clone makes it unsound** (truncated `rev-list`
produces a false PASS). The workflow already sets `fetch-depth: 0`.

No credential values are reproduced in this report.

---

## 7. ATTRIBUTION-HARDENING AUDIT

### 7.1 The change under audit

`sps2/governance/attribution.py` carries the authorized **Decision 3, patch A** change
(sha256[:16] `b6c21d73cea2290f`, `+57/−0`) and remains **uncommitted** — as required. The policy file
`sps2/governance/attribution_policy.json` is **byte-unchanged** (`eb9f113360601059`).

### 7.2 Approved semantics unchanged

| Property | Verified |
|---|---|
| Policy file hash | `eb9f113360601059` — identical to baseline |
| Tracked-clean vs HEAD | YES |
| Token count | 17, all unique |
| Word-boundary anchored matching | unchanged |
| `case_sensitive` | `false` — unchanged |
| `substring_matching` | `false` — unchanged |

### 7.3 Behavioural verification with a conforming fixture

The fixture is conforming in **every** other respect (valid `capability_id`, `VERIFIED_SAFE`,
`agent_neutral`, `FRESH`, `ACTIVE`, non-empty evidence). The **control was verified first**:

| Payload | Bytes | Verdict |
|---|---|---|
| Control: `decided_by: "User"` | 0 | clean — **control verified before trusting the agent case** |
| Real 17-token policy, `decided_by: "Antigravity"` | 60 | **DETECTED** (`ERR … non-user 'Antigravity'`) |
| Degenerate `["a b"]` | 367 | visible ERR (was **0 B silent fail-open** before patch A) |
| Degenerate `["("]` | 365 | visible ERR |
| Degenerate `["*"]` | 365 | visible ERR |
| Duplicate `["agent","ai","agent","ai"]` | 275 | visible ERR |
| Empty `[]` | 183 | visible ERR |
| Malformed / non-object / non-JSON policy | 112–130 | visible ERR |

**Patch A works.** Degenerate and malformed policies now fail closed with visible output.

### 7.4 Accepted residual — unchanged, not a new finding

`["zzz"]` → **0 bytes, fails open.** This remains an **accepted, documented residual**: patch A
validates token *shape*, not *membership*. Also failing open by design: `"Anti-Gravity"` (word-boundary
semantics), and `"Jane Self"` / `"Autonomous Council"` (ratified exclusions, DEC-0026/DEC-0027).

**No matching semantics were altered.** Fixing the `zzz` residual would require a Policy-4 change and
is **User-approval-gated**.

---

## 8. PROTECTED-HARNESS RISK REGISTER

These patterns are present in the **committed** code of this repository. The remediation patches
(**D4, C, F, B**) exist **only** in the disposable clone
`/tmp/sps2-phase4-disposable-1792117248` and have **not** been applied here.

| ID | Location | Pattern | Severity | Confidence | Patch status |
|---|---|---|---|---|---|
| **R1** | `sps2/tools/validate-p2.sh:34` (`run_check()`) with scoring at `:36-41`, 7 call sites `:62-68` | stderr discarded via `2>/dev/null`; emptiness of stdout scored as PASS. A crashing or missing checker yields **empty stdout → PASS**. | **HIGH** | Confirmed | **D4 proposed only** |
| **R2** | `sps2/tools/validate-sps2.sh:36` with scoring `:38-43`, call sites `:73-76` | Byte-identical duplicated helper — same false-PASS. | **HIGH** | Confirmed | **D4 proposed only** |
| **R3** | `validate-p2.sh`, `validate-sps2.sh` | Neither harness inspects the checker's **exit status**; only stdout emptiness. | **MEDIUM** | Confirmed | **D4 proposed only** |
| **R4** | `sps2/tools/validate-p3.sh:104` | Empty stdout → pass. **Largely mitigated**: `:90, :93, :103, :107` use `2>&1`, so tracebacks land on stdout and score FAIL. | **LOW** | Confirmed | **F proposed only** |

### 8.1 Demonstration of R1/R2

With the checker caused to raise at import time, via a patch-A-hardened `check_p2.py`, the checker
prints a visible `ERR` (82 B). But on an **interpreter-level** failure — where stdout is genuinely
empty and rc is 127 — the harness's `assert_clean` scores **PASS**. Only the harness itself can close
this class.

### 8.2 Patch C — a correction to its stated rationale

The disposition of patch C requires care, because two different defects were conflated.

**The polarity at `validate-p4.sh:120` and `:131` is already correct.** Both sites grep for
`^PROMOTED` inside an `if`, with the outcome **inverted** in the branches:

```sh
if python3 "$CHECK" "$TMP/c_noappr.json" --promote 2>&1 | grep -q '^PROMOTED'; then
  fail "POSCTRL-D  promotion became possible on a licence alone"
else
  CTR=$((CTR+1)); pass "POSCTRL-D  a declared licence alone does not enable promotion (correct)"
fi
```

This is sound negative-control construction. One workstream concluded from this that "patch C appears
unnecessary." **That conclusion is defensible, but its reasoning was wrong**, because it stated the
defect was inverted polarity and therefore absent.

**The real residual defect at `:120`/`:131` is exit-status blindness.** Because the test is "no
`^PROMOTED` line appeared," a checker that **crashes** produces empty stdout, which is
indistinguishable from "correctly refused" — so the control PASSes. Verified:

```
simulated dead checker -> empty stdout -> PASS branch taken   (false PASS confirmed)
```

Contrast `:97` (the positive control), where a crash yields empty stdout → no `^PROMOTED` → **FAIL**,
which is correct behaviour.

So the residual risk in `validate-p4.sh` is real but it is **exit-status blindness (Medium)**, not
inverted polarity. Patch C's *value* should be re-justified on that basis.

### 8.3 The `legacy protection` predicate — a dirty-worktree rule

`sps2/tools/validate-sps2.sh:198-200` treats **any uncommitted change** under `.github` as a legacy
violation:

```sh
DIFF=$(cd "$REPO" && git diff --name-only HEAD -- skills scripts plugins .github \
       install.sh install.ps1 uninstall.sh uninstall.ps1 get-sps.sh get-sps.ps1 2>/dev/null)
[ -z "$DIFF" ] && pass "legacy implementation untouched by P1" || fail "legacy modified: $DIFF"
```

This is a **dirty-worktree rule, not a content prohibition**: the same `.github` edit passes once
committed. It is also the mechanism behind four of the seven portability failures (§5.2, via the
`c11da27` pin). Not a defect, but a recurring trap: any in-progress `.github` edit transiently reddens
this check.

### 8.4 Authorization required before any application

Applying D4, C, or F would modify `sps2/tools/validate-p2.sh`, `validate-sps2.sh`,
`validate-p4.sh`, and `validate-p3.sh` — all **protected**. This requires **explicit User
authorization** for each file. Patch B is **superseded** by the committed `.sps/tools` work and
should not be applied.

---

## 9. GOVERNANCE COMPLIANCE FINDINGS

### 9.1 Verified holdings

| Check | Result |
|---|---|
| Distinct `decided_by`/`approved_by` values | **exactly `{"User"}`** — 202 occurrences across 53 files |
| Non-`User` approver values | **zero**. Two `null` values are honest `PENDING_USER_APPROVAL` placeholders (`capability/registry.json`, `PROJECT/SELECTION-P3-0001.json`); their sibling `state` is `PENDING_USER_APPROVAL` |
| Agent-attributed approvals | **none** |
| Schema definitions mistaken for approvals | The only other non-`User` strings are JSON **schema** definition text (`"description": "MUST NOT name an agent…"`), not decision values |
| Approval inferred from an instruction to investigate | **none found** |

### 9.2 Scope-control rule — exact lines

```
174  ## 8. Scope Control (§18 of the brief)
176  Out-of-scope for Phase 02 (document, do **not** fix):
178  dynamic skill discovery · MCP discovery · … SEO · CMS · backend/frontend redesign ·
180  accessibility · CI/CD redesign · multi-agent orchestration implementation ·
183  **Rule:** discovering an out-of-scope issue → record it in `.sps/audits/README.md`
184  known-issue register. Fixing it early violates scope control even if the fix looks
185  obviously correct.
```

A prior assumption placed this at 176–183; the correct range is **174–185**.

### 9.3 Traceability gap for the CI commit (Medium) — not a confirmed violation

Commit `cdcbca8` (the CI job) rests on the **User's conversational authorization** as recorded by the
agent. No **in-repo instrument** records it:

- `grep` for `CI/CD` across `sps2/decisions`, `sps2/requirements`, `sps2/governance`, `.sps/decisions`
  returns **zero** hits.
- `.sps/GOVERNANCE.md` has exactly one commit (`ec32dfa`) and was never amended, so the §8 line-180
  "CI/CD redesign" out-of-scope entry was **never formally lifted in-repo**.

Two mitigating facts, stated honestly:

1. §8's Rule is scoped to **"Phase 02"** (`:176`), so it may not bind this work at all.
2. The User **did** authorize the CI change in the conversation preceding this phase.

**Conclusion: a traceability gap, not a violation.** The distinction that matters: *authorized by User
instruction* (true) versus *authorized by an in-repo instrument* (false). The same holds for
`238c9e4`'s three `.sps/tools` validator migrations — and the repository documents its own gap
(`LEGACY-PATH-DEFINITION-DECISIONS.json`: *"the granting instrument is locatable nowhere"*).

**A correction to my own prior verification.** I previously reported that "no decision record was
modified" by these commits. That is **wrong**. `git log --name-only 320d3a5^..HEAD` shows commit
`320d3a5` touched two decision records:

```
sps2/decisions/ATTRIBUTION-POLICY-DECISIONS.json
sps2/decisions/OPEN-DECISION-ATTRIBUTION-TOKEN-SET.json
```

Commits `238c9e4` and `cdcbca8` touch **no** decision or requirement file — that half holds. Whether
`320d3a5`'s edits are purely additive was **not** diffed and remains **unverified**.

### 9.4 Pending decisions — none promoted

| Record | Status |
|---|---|
| `DEC-0029` (LEGACY-SCOPE) | `PENDING_USER_APPROVAL`, null decider/date — authorizes nothing |
| `DEC-0030` (LEGACY-PATH-DEFINITION) | `PENDING_USER_APPROVAL`, null decider/date — authorizes nothing |
| `OPEN-DECISION-ATTRIBUTION-TOKEN-SET` | pending |
| `DEC-7101…7104`, `DEC-7110` (P10-DELEGATED) | technical direction only |
| `OPEN-DECISION-CLAUDE-SETTINGS`, `OPEN-DECISION-LICENCE` | pending |

23 older `D-Pn-*` APPROVED records lack `decided_at` — a provenance-completeness gap, **not** a
misreadable approval. `HANDOFF-CURRENT.md:263-270` still lists six open questions (remote config, git
identity, Phase 03 scope, `smoke-sps.sh` safety, validator wiring into CI, CI/CD redesign scope).

**A framing correction I must record against my own work in this phase.** During drafting I initially
treated `HANDOFF-CURRENT.md:296` ("**Phase 03 approval: NOT GRANTED.** `PHASE-03` is `NOT_STARTED`")
as a live governance blocker. **It is not.** Line 296 falls inside the block headed at `:173`
"## PHASE 02 RECORD (superseded as current state, retained for history)". The **current** statement is
at `:131`, in the PHASE 03 EXTENSION section: *"Phase 03 approval: granted by the User on 2026-10-03 …
`DEC-0003` and `DEC-0004` are resolved as `APPROVED` on the same basis."* So `:296` records what was
true at Phase 02 time, and reading it as current is an error of exactly the kind this mission exists
to catch. **No live contradiction and no Phase 03 approval blocker.** The residual observation is
narrower: a superseded section carries no machine-readable marker, so a reader or tool scanning the
file linearly can mistake history for current state. That is a document-ergonomics risk (Low).

### 9.5 Governance-axis verdict: **CONDITIONAL**

No violation was confirmed; several traceability gaps were. Unmet conditions are listed in §14.

---

## 10. PRESERVATION AUDIT

### 10.1 No user work was removed

Untracked sets were diffed against both prior baselines:

| Comparison | Added | Removed |
|---|---|---|
| Phase 3 baseline (103) → now (105) | 2 | **0** |
| Phase 4 baseline (104) → now (105) | 1 | **0** |

Both additions are this mission's own reports. **Zero removals in either comparison.** The
103 → 104 → 105 progression is fully explained by reports being written, not by file loss.

### 10.2 The "104 untracked" figure in the Phase 3 report was wrong

My Phase 3 report stated "Untracked count 104, unchanged." That number is **structurally
unreachable**:

```
git status --porcelain                 -> 11 dir-collapsed '??' entries
git status --porcelain -uall           -> 105 file-level '??' entries
```

`104` is a directory-collapse artifact. The true count is **105**. This did not affect any
conclusion — the *set comparison*, not the count, established preservation — but the figure should
not be cited again.

### 10.3 A caution about the baseline files themselves

Both prior `untracked.txt` baselines contain a **non-existent path**:

```
baseline:  AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md     <- does not exist
reality:   AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md     <- 8275 B, present
```

They are also differently formatted (Phase 3 bare paths, Phase 4 `?? `-prefixed) while sharing their
directories' mtimes, indicating they were **reconstructed rather than captured raw**. Their exact
bytes should not be relied upon for preservation sign-off. The set-difference method used above is
robust to this. Byte-identity for user-work paths also rests on **size equality only**, since no
pre-existing hash manifest was supplied.

### 10.4 Preservation verdict

| Item | Status |
|---|---|
| `sps2/tools/p10_runtime_gate.py` | present — 100,626 B / 2,221 lines |
| `sps2/tests/test_p10_runtime_gate.py` | present — 141,560 B / 2,945 lines / 282 tests |
| `domain/frontend/` | present — 6 source files + 6 ignored `.pyc`, 49 tests |
| `domain/cms/data/` | present — 3 files |
| `.sps/tasks/p17/` | present — 117 files |
| `.sps/evidence/P17/` | present — 10 files, all valid JSON |
| 3 untracked decision JSONs | present, byte-identical |
| 4 prior reports | byte-identical at 56549 / 69975 / 64788 / 15562 B |
| Ignored `__pycache__` / `.pyc` | preserved (`.gitignore:131`) |
| `domain/seo/**` modifications | **0** |
| Stash | empty; none created |

**Verdict: PRESERVED.** No work was lost, moved, renamed, or quarantined.

---

## 11. CONFIRMED DEFECTS VS HYPOTHESES

### 11.1 Confirmed defects

| ID | Defect | Severity | Evidence |
|---|---|---|---|
| **D-1** | `RESUME_COMPLETION_STATE_DRIFT` — `sps2/RESUME.md` says `PENDING_USER_APPROVAL` while `ROADMAP-P3-DECISIONS.json` is `APPROVED` | **High** | Reproduced: portability check 7 fails; `cac77b6` touched neither `RESUME.md`. Blocks release. |
| **D-2** | `validate-p7-readiness.py` `p3_delivery_state()` reports `RECORD_OVERSTATES_P3` in the D-P3-D zero-adapter state | **High (scoped)** | Portability checks 5–6 fail |
| **D-3** | `validate-p2.sh:34` / `validate-sps2.sh:36` false-PASS (stderr suppressed, empty stdout scored as PASS) | **High** | R1/R2; unpatched in this repo |
| **D-4** | CI minimum-count guard is too weak — 58 tests (10.2%) or an entire module can vanish undetected | **Medium** | `500` vs actual `558`; arithmetic verified |
| **D-5** | CI glob `test_*.py` cannot match `test-*.py` | **Medium** | `git ls-files` returns 0 vs 2 |
| **D-6** | Stale portability figure `(33 passed, 6 failed)` in `sps-ci.yml:176` | **Medium** | Actual 32/7 |
| **D-7** | 331 of 889 tests (37%) cannot run in CI | **Medium** | WS2 clean-clone data: 558 vs 889 |
| **D-8** | `validate-p4.sh:120`/`:131` exit-status blindness in negative controls | **Medium** | Dead-checker simulation PASSes |
| **D-9** | The entire validator suite has no CI foothold (reachable only from the excluded harness) | **Medium** | Only reference: `validate-p3.sh:386`, inside the excluded portability harness |
| **D-10** | `p10_runtime_gate.py` (100 KB gate) has **no caller** anywhere | **Medium** | Zero references repo-wide |
| **D-11** | No in-repo instrument authorizes the CI commit or the `.sps/tools` validator migrations | **Medium (governance)** | `grep CI/CD` → zero hits in decisions/requirements |
| **D-12** | P5 file edits lack an authorizing decision record | **Medium (governance)** | Pre-existing user work; normative file affected |
| **D-13** | Two tests mutate the process environment without restoring it (`test_p17_security.py:255` PATH, `:538` secret) | **Low (latent)** | Empirically confirmed leak: `SECRET_LEAKED: True` |

### 11.2 Hypotheses (not confirmed)

| ID | Hypothesis | Why unconfirmed |
|---|---|---|
| H-1 | Ubuntu would also report 32/7 portability failures | No Linux host, no containers, no network. **Inferred only.** |
| H-2 | Python 3.12 runs the suite identically to 3.14.7 | Stdlib-only and clean under `-W error::DeprecationWarning`, but **3.12 was never executed** |
| H-3 | `320d3a5`'s decision-file edits are purely additive | Not diffed against the prior revision |
| H-4 | Shallow clone causes "19 tests across 5 methods" to fail | Mechanism proven (`fetch-depth: 0` is necessary); exact blast radius not reproduced |
| H-5 | No other runtime false-PASS exists in the protected harnesses | Validators were **never run end-to-end** (safety boundary). Verdicts are static reads plus transcribed predicates. |
| H-6 | The credential predicate would detect a real leak | The predicate checks key **names** only; no real leak was present to test against |

### 11.3 Claims refuted during this audit

| Claim | Source | Status |
|---|---|---|
| `|| true` at `sps-ci.yml:61-63` means the guard can never fail | One workstream (CRITICAL) | **REFUTED** — verbatim execution gives rc=1 when a marker is planted; `exit` terminates the shell. Guards work. |
| "There is no remote (`KEEP_LOCAL_ONLY`)" | My own Phase 3 report | **REFUTED** — a remote exists |
| "No decision record was modified by these commits" | My own Phase 3 report | **REFUTED** for `320d3a5` (2 decision files) |
| "Untracked count 104, unchanged" | My own Phase 3 report | **REFUTED** — 105 under `-uall` |
| `validate-p4.sh` has inverted polarity | Prior phase analysis | **REFUTED** — polarity is correct; the defect is exit-status blindness |
| `test-history-credential-check.py` is unsafe | Prior overnight report | **REFUTED** — ran it; safe, green, self-contained |
| Phase 03 approval is NOT GRANTED (a live blocker) | Prior briefing | **REFUTED** — that line is in a superseded historical section |

---

## 12. RISK REGISTER

| ID | Risk | Severity | Confidence | Release-blocking |
|---|---|---|---|---|
| R-1 | `RESUME.md` / decision-record drift (D-1) | High | Confirmed | **YES** |
| R-2 | P7 readiness overstates delivery under D-P3-D (D-2) | High | Confirmed | **YES (scoped)** |
| R-3 | `validate-p2.sh` / `validate-sps2.sh` false-PASS (D-3) | High | Confirmed | No (risk exposure, not a test failure) |
| R-4 | CI has never executed — all CI evidence is local simulation | High | Confirmed | **YES** for a CI-backed release claim |
| R-5 | 3 unpushed commits; publish path unrehearsed | High | Confirmed | **YES** for any actual release |
| R-6 | `attribution.py` patch A is uncommitted — a clone of HEAD does not contain the hardening | Medium | Confirmed | No, but it means the fix is not durable |
| R-7 | 37% of tests have no CI coverage (D-7) | Medium | Confirmed | No |
| R-8 | CI audit minimum guard too weak (D-4) | Medium | Confirmed | No |
| R-9 | Entire validator suite has no CI foothold (D-9) | Medium | Confirmed | No |
| R-10 | `p10_runtime_gate.py` orphaned, no caller (D-10) | Medium | Confirmed | No |
| R-11 | CI glob mismatch `test_*.py` vs `test-*.py` (D-5) | Medium | Confirmed | No |
| R-12 | Stale portability figure in CI comment (D-6) | Medium | Confirmed | No |
| R-13 | `validate-p4.sh` exit-status blindness (D-8) | Medium | Confirmed | No |
| R-14 | No in-repo instrument authorizes CI / validator migrations (D-11) | Medium | Confirmed | Governance |
| R-15 | P5 normative edits lack a decision record (D-12) | Medium | Confirmed | Governance |
| R-16 | Accepted residual: `["zzz"]` fails open by design | Low | Confirmed | No — documented and User-accepted |
| R-17 | `legacy protection` flags any uncommitted `.github` edit | Low | Confirmed | No |
| R-18 | Superseded handoff section lacks a machine-readable marker | Low | Confirmed | No |
| R-19 | Ubuntu/Python 3.12 behaviour unmeasured | Low | Unverified | No |
| R-20 | Protected-harness runtime false-PASS beyond static review | Low | Unverified | No |
| R-21 | Test-process environment leak affects future in-process collectors (D-13) | Low | Confirmed | No |

---

## 13. PROPOSED REMEDIATION PACKETS

**Nothing here has been implemented.** Every packet is a proposal only. Findings D-1 through D-13 are
addressed; each packet states its approval requirement.

### Category 1 — Safe, non-normative technical remediation

**P-D1 — Fix `RESUME.md` completion drift** (addresses D-1)
- **Files:** `sps2/RESUME.md`
- **Root cause:** `cac77b6` set `ROADMAP-P3-DECISIONS.json` to `APPROVED` without updating the resume
  checklist, so `COMPLETION: PENDING_USER_APPROVAL` is stale.
- **Minimal change:** update the `COMPLETION` line to match the decision record.
- **Regression test:** `test-portability.py` check 7 (`RESUME_COMPLETION_STATE_DRIFT`) must go green;
  the harness count should move 32/7 → 33/6 (which incidentally makes the CI comment correct).
- **Negative control:** deliberately revert the `RESUME.md` line and confirm the check fails again.
- **Compatibility risk:** none. `RESUME.md` is documentation.
- **Changes normative behaviour:** **NO.**
- **User approval required:** not for the edit itself. **But note:** `COMPLETION: PENDING_USER_APPROVAL`
  may be the *deliberate* record of an outstanding User approval. Confirm before editing — if it is
  intentional, the defect is in the decision record instead, and this becomes User-gated.

**P-D4 — Strengthen the CI minimum-count guard** (addresses D-4)
- **Files:** `.github/workflows/sps-ci.yml` (`MIN_TESTS`, near `:147`)
- **Minimal change:** assert each module in `MODULES` contributes `Ran > 0`, or derive the floor from
  `${#MODULES[@]}` instead of the magic `500`.
- **Regression test:** per-module `Ran > 0` assertion; add a case that drops one module.
- **Negative control:** remove a module from the list and confirm the step fails.
- **Changes normative behaviour:** no.
- **User approval required:** **YES** — CI/CD scope (§6 of the standing rules).

**P-D5 — Correct the CI glob** (addresses D-5)
- **Files:** `.github/workflows/sps-ci.yml:129`
- **Minimal change:** widen to `test[-_]*.py` (or add the explicit hyphen glob).
- **Regression test:** confirm both `sps2/tools/test-*.py` scripts become visible.
- **Negative control:** verify a hyphenated file is now collected, then that removing it re-drops it.
- **Compatibility risk:** the two tool scripts are not unittest modules; collect them deliberately or
  explicitly, not by accident.
- **Changes normative behaviour:** no.
- **User approval required:** **YES** — CI/CD scope.

**P-D6 — Correct the stale figure** (addresses D-6)
- **Files:** `.github/workflows/sps-ci.yml:176`
- **Minimal change:** `(33 passed, 6 failed, 14 controls)` → the measured value, recomputed at the time
  of the edit.
- **Changes normative behaviour:** no.
- **User approval required:** **YES** — CI/CD scope.

**P-D10 — Decide the fate of `p10_runtime_gate.py`** (addresses D-10)
- **Observation:** a 100 KB gate with no caller and an untracked 282-test suite.
- **Options:** wire it into CI (requires tracking both files, contradicting Decision 5) or record it as
  intentionally unwired. **Recommendation: record a decision either way**, since an unrun gate is
  indistinguishable from a passing gate.
- **Changes normative behaviour:** possibly.
- **User approval required:** **YES.**

**P-D13 — Restore the process environment after the two leaking tests** (addresses D-13)
- **Files:** `sps2/tests/test_p17_security.py` (`:255`, `:538`) — test files, not protected
- **Root cause:** two `os.environ[...] =` assignments lack an `addCleanup`, unlike the five sibling sites
  that restore correctly.
- **Minimal change:** register `self.addCleanup(...)` immediately after each assignment, matching the
  established pattern used elsewhere in the same suite.
- **Regression test:** assert `PATH` is unchanged and `P17_FAKE_PARENT_SECRET` is absent after the
  module completes in a shared process.
- **Negative control:** remove one `addCleanup` and confirm the new assertion fails.
- **Compatibility risk:** none; no assertion or result changes.
- **Changes normative behaviour:** **NO.**
- **User approval required:** no, for the edit itself — but it touches test files, so it should be
  routed with the same care as other test changes. Low urgency.

### Category 2 — Protected validator / harness changes

**P-D3 — Apply the D4 stderr/exit-status patch** (addresses D-3, R3)
- **Files:** `sps2/tools/validate-p2.sh`, `sps2/tools/validate-sps2.sh` — **both protected**
- **Root cause:** `run_check()` discards stderr; emptiness of stdout is scored as PASS, so a crashed
  checker PASSes.
- **Minimal change:** capture stderr with `2>&1` and check the checker's exit status before scoring.
- **Regression test:** the four-case matrix already verified in the disposable clone — silent → FAIL,
  noisy → FAIL, missing → FAIL, clean → PASS.
- **Negative control:** remove the checker binary and confirm FAIL rather than PASS.
- **Compatibility risk:** may surface previously-masked failures as new red results.
- **Changes normative behaviour:** no — it makes existing behaviour *observable*.
- **User approval required:** **YES, explicitly, per file.**
- **Isolation:** apply and validate in a disposable worktree first.

**P-D8 — Re-justify patch C on its true defect** (addresses D-8)
- **Files:** `sps2/tools/validate-p4.sh` — **protected**
- **Correction:** the polarity at `:120`/`:131` is already correct. The genuine defect is exit-status
  blindness: a crashed checker is indistinguishable from a correct refusal.
- **Minimal change:** require `rc == 0` before accepting "not promoted".
- **Negative control:** simulate a dead checker and confirm the control now FAILS.
- **Changes normative behaviour:** no.
- **User approval required:** **YES.**

### Category 3 — Governance / requirements / decision records

**P-D11 — Record an instrument for the CI commit and the validator migrations** (addresses D-11, R-14)
- **Options:** (a) record retroactive decision entries citing the User's conversational authorization;
  (b) explicitly note that §8's Rule is scoped to Phase 02 and does not bind.
- **Constraint:** an agent must never author a User approval. A decision record may be **prepared**, but
  `decided_by: "User"` may only be set by the User.
- **User approval required:** **YES — User-only.**

**P-D12 — Authorize or revert the P5 file edits** (addresses D-12)
- **Files:** `sps2/evidence/P5-EVIDENCE.json`, `sps2/requirements/P5-REQUIREMENTS.json`
- **Note:** the edits are honest (they preserve original text and set `state_changed: false`), but
  `P5-REQUIREMENTS.json` is normative and no record authorizes the edit.
- **User approval required:** **YES — User-only.**

### Category 4 — CI/CD scope changes

All of P-D4, P-D5, P-D6, and any wiring of the credential checker or the validator suite fall here.
Each requires explicit User authorization, since `GOVERNANCE.md:180` lists CI/CD redesign as
out-of-scope and no in-repo instrument lifts it.

**P-D9 — Give the validator suite a CI foothold** (addresses D-9, R-9)
- **Recommendation:** wire `test-history-credential-check.py` directly as a CI step (safe, fast,
  deterministic, currently green) rather than leaving it reachable only through an excluded harness.
- **Caution:** requires `fetch-depth: 0`, which the workflow already sets.
- **User approval required:** **YES — CI/CD scope.**

### Category 5 — Changes requiring explicit User-only approval

1. Commit `sps2/governance/attribution.py` (patch A) — durable hardening.
2. Push the three unpushed commits.
3. Apply D4 / C / F to protected validators.
4. Any CI/CD change (P-D4, P-D5, P-D6, P-D9).
5. Resolve the remote / `DEC-0001 KEEP_LOCAL_ONLY` discrepancy.
6. Authorize or revert the P5 file edits.
7. Replace the placeholder Git identity (handoff question 2).
8. Decide the fate of `p10_runtime_gate.py`.
9. Any change to `["zzz"]` residual semantics.

---

## 14. USER-ONLY DECISIONS STILL REQUIRED

| # | Decision | Why User-only | Minimal sufficient wording |
|---|---|---|---|
| 1 | Commit `attribution.py` (patch A)? | Only the User authorizes commits in this project | "Commit `sps2/governance/attribution.py` on the current branch, no push." |
| 2 | Push the three commits? | Publishing is User-only | "Push `build/roadmap-p3-completion` to origin." |
| 3 | Apply D4 to `validate-p2.sh` + `validate-sps2.sh`? | Protected validators | "Apply patch D4 to both files on the current branch." |
| 4 | Apply patch C to `validate-p4.sh`? | Protected validator | "Apply patch C to `validate-p4.sh`." |
| 5 | Apply patch F to `validate-p3.sh`? | Protected validator | "Apply patch F to `validate-p3.sh`." |
| 6 | Authorize the CI changes (P-D4/D5/D6/D9)? | CI/CD is out of scope per `GOVERNANCE.md:180` | "CI/CD scope is authorized for these specific changes." |
| 7 | Record an instrument for the CI commit and validator migrations? | An agent may never author a User approval | "Record DEC-00xx as APPROVED, decided_by User, dated <date>." |
| 8 | Authorize or revert the P5 edits? | Normative file, no record | "The P5 SPEC-2 correction edits are authorized" (or "revert them"). |
| 9 | Resolve the remote / `KEEP_LOCAL_ONLY` discrepancy? | Normative policy | "Supersede `DEC-0001`; the remote is intentional." |
| 10 | Replace the placeholder Git identity? | Publishing identity | "Replace the Git identity with <name/email>." |
| 11 | Decide the fate of `p10_runtime_gate.py`? | May require tracking, contradicting Decision 5 | "Wire the P10 gate into CI" (or "record it as intentionally unwired"). |
| 12 | Fix D-1 and D-2? | D-1 may record an *outstanding* User approval | "`RESUME.md` drift is a defect — fix it" (or "the PENDING state is intentional"). |

---

## 15. ACTIONS NOT PERFORMED

Explicitly, this mission did **not**:

- Create any commit, tag, or annotated object.
- Stage any file (`git diff --cached` remained empty throughout; index == `HEAD^{tree}`).
- Push, fetch, pull, `ls-remote`, or otherwise contact `origin`.
- Reset, clean, stash, revert, checkout, move, rename, or delete any file.
- Overwrite, quarantine, or alter any user work.
- Install any dependency (`pytest` and `PyYAML` remained absent).
- Modify any tracked file. Final verification: 7 modified, 105 untracked, staged 0 — identical to
  mission start.
- Modify, apply, or test-apply patches D4/C/F/B to the real repository.
- Run any protected shell validator end-to-end.
- Modify any governance record, requirement, decision, or policy.
- Commit the uncommitted `attribution.py` change.
- Change the approved token set, matching semantics, or the `co-pilot` non-goal.
- Weaken or skip any test; no failure was suppressed.
- Treat any pending decision as approved.
- Declare release readiness beyond the verdict below.

Network operations: **none**. All isolation used `git clone --no-hardlinks` against local objects.

---

## 16. FINAL RELEASE RECOMMENDATION

### Verdict: **NOT READY**

**Why not READY.** Release readiness requires evidence that does not exist. The committed test corpus
is genuinely green and independently reproduced, which clears exactly one gate. But:

- **A confirmed release-blocking defect exists** (D-1, `RESUME.md` drift) and is caught by the
  project's own harness.
- **A second confirmed defect exists** (D-2, P7 readiness overstatement).
- **CI has never executed.** Every CI result in this report is a local simulation.
- **Nothing has been published**; three commits are unpushed and the publish path is unrehearsed.
- **The hardening fix is not durable** — patch A is uncommitted, so a clone of HEAD lacks it.
- **Governance traceability gaps remain** for the CI commit and the validator migrations.

**Why not UNKNOWN.** The evidence is sufficient. The green results are real and reproduced; the
failures are reproduced, attributed, and classified. This is not an evidence shortfall.

**Why not CONDITIONAL.** The convention offered was "core tests pass, but one or more noncritical
verification steps remain." Two confirmed defects block release under the project's own harness, and
CI has never run. Calling that "noncritical" would understate it.

### Gates

| Gate | Verdict |
|---|---|
| Reproducible tests | **PASS** — 889/888/0/1 reproduced exactly |
| Committed HEAD green | **PASS** |
| CI execution and failure propagation | **PARTIAL** — logic verified locally; never executed remotely |
| Portability results | **FAIL** — 32/7, two genuine defects |
| Credential/history scan | **PASS** (checker green) but **never gates CI** |
| Protected harness false-PASS risk | **FAIL** — R1/R2 unpatched |
| Clean-checkout reproducibility | **PASS** — 558/557/0/1 |
| Uncommitted changes | **PASS** — classified; patch A correctly uncommitted |
| Governance compliance | **CONDITIONAL** — gaps, no confirmed violation |
| User-work preservation | **PASS** — zero removals |
| Actual release/deployment evidence | **FAIL** — none; CI never ran, nothing pushed |

**Nine of eleven gates pass or partially pass; three fail outright.**

### Minimal path to CONDITIONAL

1. Fix D-1 and D-2 (both genuine defects).
2. Commit `attribution.py` so the hardening survives a clone.
3. Obtain authorization for the CI changes, then actually execute CI once.
4. Push, or explicitly record that publishing remains deferred.

---

## 17. MACHINE-READABLE SUMMARY

```json
{
  "report_id": "SPS2-PHASE4-RELEASE-VERIFICATION-20261016-084449",
  "phase": 4,
  "verdict": "NOT_READY",
  "head": "cdcbca83679844ea66196f25773f42d9b64569ec",
  "branch": "build/roadmap-p3-completion",
  "baseline_match": true,
  "remote_exists": true,
  "network_operations": 0,
  "commits_created": 0,
  "files_staged": 0,
  "files_modified_by_mission": 0,
  "tests": {
    "worktree": {"modules": 29, "ran": 889, "passed": 888, "failed": 0, "skipped": 1,
                 "reproducible_from_repo": false},
    "clean_clone": {"modules": 26, "ran": 558, "passed": 557, "failed": 0, "skipped": 1,
                    "reproducible_from_repo": true},
    "invisible_to_ci": 331,
    "order_independent": true,
    "flaky": false,
    "single_skip_is_environment_driven": true
  },
  "ci": {
    "job_present": true,
    "locally_simulated_ran": 558,
    "min_tests": 500,
    "margin": 58,
    "red_path_verified": true,
    "rc_capture_correct": true,
    "real_run_observed": false,
    "discover_raw_exit": 5,
    "discover_piped_exit": 0,
    "discover_usable_as_gate": false
  },
  "portability": {"passed": 32, "failed": 7, "controls": 14, "reported_stale": "33/6"},
  "credential_checker": {"safe": true, "ran": true, "exit": 0, "scenarios": "4/4"},
  "p9_p10": {"domain_seo_modified": 0, "worktree": "OK", "no_patch_e": "FAILED(3)"},
  "confirmed_defects": 13,
  "hypotheses": 6,
  "claims_refuted": 7,
  "gates": {"reproducible_tests":"PASS","committed_head_green":"PASS","ci_execution":"PARTIAL",
            "portability":"FAIL","credential_scan":"PASS","harness_false_pass":"FAIL",
            "clean_checkout":"PASS","uncommitted_changes":"PASS","governance":"CONDITIONAL",
            "preservation":"PASS","release_evidence":"FAIL"},
  "user_decisions_required": 12,
  "preservation_removals": 0
}
```
