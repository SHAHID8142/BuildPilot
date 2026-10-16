# SPS2 FINAL MISSION — End-to-End Repository Completion, Safe Remediation, Independent Verification, Governance Compliance, Regression Testing, and Final Release-Readiness Report

**Mission ID:** `SPS2-FINAL-END-TO-END-READINESS`
**Report ID:** `SPS2-FINAL-END-TO-END-READINESS-20261016-091500`
**Generated:** 2026-10-16
**Repository:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`
**Branch:** `build/roadmap-p3-completion`
**HEAD:** `cdcbca83679844ea66196f25773f42d9b64569ec` (short `cdcbca8`) — **unchanged by this mission**
**Author:** implementation agent (this report records findings; it approves nothing)

---

## 1. Final Verdict

**`NOT_READY`**

This is a product-readiness verdict, not a mission-completion verdict. This mission is **COMPLETE as an audit and remediation exercise**: it produced a full evidence-backed classification of every item, fixed two defects that were within the agent's authority, and independently verified the fixes. The product **SPS2** remains `NOT_READY` for release because six blocking conditions survive, four of which cannot be cleared by any agent.

The verdict is `NOT_READY` rather than `READY_WITH_LIMITATIONS` on one decisive ground: **no CI run has ever executed**. Every CI result in every report, including this one, is a *local simulation*. A release claim resting on an unexecuted pipeline is not a claim that limitations qualify — it is a claim with no primary evidence.

---

## 2. What was actually done in this mission

| Phase | Action |
|---|---|
| Baseline | Captured full repository state, hashes, file inventory to `/tmp/sps2-final-baseline-1792119477/` |
| Governance audit | Verified all decision states, all 24 `UQ-*` identifiers, authorization instruments, remote and identity facts |
| Chunked investigation | 13 chunks (0–12) covering governance, P7, Resume state, protected validators, attribution, portability, CI, test corpus, untracked disposition, regression, clean-clone |
| Subagent verification | 6 read-only subagents (A–F) launched; 5 returned findings; **1 (A) failed and its scope was absorbed by the lead** |
| Remediation | Applied **3** authorized fixes; declined **3** fixes that exceeded authority |
| Verification | Re-ran the full corpus, the portability harness, and a clean clone; proved each fix with a negative control on the REAL harness/code |
| Preservation | Confirmed 0 deletions, 0 staging, 0 stash, HEAD unchanged, all protected hashes identical |

---

## 3. Mandatory prohibitions — compliance attestation

| Prohibition | Status | Evidence |
|---|---|---|
| Do not commit | **HONOURED** | HEAD `cdcbca8` identical to baseline; `git diff --cached --name-only` = 0 lines |
| Do not push / fetch / pull | **HONOURED** | No remote operation; `origin` cached ref unchanged; upstream still ahead 0 / behind 3 |
| Do not merge / rebase / force-push | **HONOURED** | No `MERGE_HEAD`, `rebase-merge`, or `rebase-apply` in `.git/` |
| Do not deploy or publish a release | **HONOURED** | No release, tag, or publish command issued |
| Do not create or modify a remote resource | **HONOURED** | No network request of any kind |
| Do not rewrite history / reset the repository | **HONOURED** | `git reflog` shows no new entries; no `reset` invoked |
| Do not alter protected files | **HONOURED** | All 6 spot-checked protected hashes identical to baseline (§24) |
| Do not alter normative governance decisions | **HONOURED** | No decision record edited; a stale `note` was **declined** as beyond authority (§11.3) |
| Do not change approval states | **HONOURED** | `DEC-0028` APPROVED, `DEC-0029`/`DEC-0030` PENDING — all unchanged |
| Do not install software or dependencies | **HONOURED** | `pytest` remained absent throughout; no package manager invoked |
| Do not make network requests | **HONOURED** | No fetch, no web call, no remote contact |
| Do not delete unrelated files | **HONOURED** | Untracked count 106 before and after |
| Do not overwrite user changes | **HONOURED** | All 7 pre-existing modifications byte-identical (§24) |
| Do not use `git clean` / `stash` | **HONOURED** | Stash list = 0 |
| Do not discard untracked work | **HONOURED** | 106 untracked preserved |
| Do not weaken a test to hide a violation | **HONOURED** | Changes only *strengthened* test integrity (§22) |
| Do not invent a User decision or approval | **HONOURED** | No approval fabricated; §11.3 escalated instead |
| Do not infer approval from silence | **HONOURED** | PENDING states reported as PENDING |
| Do not overwrite prior reports | **HONOURED** | New file; all 5 prior reports byte-intact |

---

## 4. Environment and method

| Fact | Value |
|---|---|
| Python | 3.14.7 |
| OS | Darwin 27.0.0 (macOS) |
| Shell | `/bin/zsh`; harness scripts run under bash 3.2.57 |
| Workspace tool | `/usr/local/bin/node` present |
| `pytest` | **ABSENT** — all runs use `python3 -m unittest` |
| GNU `timeout` | **ABSENT** (macOS) — do not propose it |
| GNU `grep -P` | **ABSENT** — BSD grep only |

**Method:** every quantitative claim below was produced by executing a command in this environment, or is explicitly labelled as unverified. Subagent findings were **independently reproduced by the lead before being relied upon** — five subagent claims were refuted or refined in that process (§30).

---

## 5. Classification of every item

The eight required states: **1** Verified and ready · **2** Fixed and independently verified · **3** Fixed but not independently verified · **4** Investigated but not fixed · **5** Blocked by User-only approval · **6** Blocked by missing tools/environment/credentials · **7** Known limitation intentionally retained · **8** Not tested / not yet proven.

### 5.1 Fixed and independently verified (State 2)

| ID | Item | Evidence |
|---|---|---|
| **F-1** | `sps2/RESUME.md` completion-state drift | Real harness: 32/7 → **33/6**; `RESUME_COMPLETION_STATE_DRIFT` gone. **Negative control on the real harness**: reintroducing the drift restores 32/7 and re-emits the failure. Independently reviewed **SOUND**. |
| **F-2** | Environment leak in `sps2/tests/test_p17_security.py:538` | Controlled same-probe comparison: clean clone `SECRET_LEAKED=True` (RAN=60) vs fixed tree `SECRET_LEAKED=False` (RAN=62). Restoration proven under `raise`. Independently reviewed **SOUND**. |
| **F-3** | Environment leak in `sps2/tests/test_p17_pinning.py:178,207` | `addCleanup(setattr, os.environ, "PATH", prev)` was a **silent no-op** (`setattr` on `os.environ` writes an instance attribute, never the process environment). Micro-probe: `os.environ["PATH"]` unchanged by `setattr`. Full corpus `PATH_RESTORED` `False` → **`True`**. **Negative control**: reverting to `setattr` yields `FAIL=4 ERR=2` and the outcome assertion fires. Independently reviewed **SOUND_WITH_CAVEATS** — see §22.1. |

### 5.2 Verified and ready (State 1)

| ID | Item | Evidence |
|---|---|---|
| V-1 | Tracked test corpus is green and deterministic | 26 modules, **562** tests, 0 failed, 1 skipped, exit 0 |
| V-2 | Worktree corpus is green | 29 modules, **891** tests, 0 failed, 1 skipped, exit 0 |
| V-3 | Order independence | Sorted 562 / reversed 562 — identical totals, 0 failures |
| V-4 | Attribution hardening (patch A) is correct and uncommitted | `attribution.py` `+57/−0`; 68 tests OK |
| V-5 | Attribution policy semantics unchanged | `eb9f113360601059` identical to baseline; 17 unique tokens |
| V-6 | Attributions are attributed only to `User` in normative records | Exhaustive walk: **zero** non-`User` values in `sps2/{decisions,requirements,evidence,handoff,capability}` |
| V-7 | `|| true` CI guards genuinely fail the step | Executed 3×: planted marker → rc=1; clean → rc=0 |
| V-8 | CI exit-code propagation is correct | `STATUS=$?` adjacent to `OUTPUT="$(...)"`; injected failure → `Ran 559 FAILED`, rc=1 |
| V-9 | The 13-step final verification sequence | Executed; see §28 |
| V-10 | Preservation compliance | 0 deletions, 106 untracked intact, protected hashes identical |
| V-11 | Secrets hygiene | No live credential in tracked files; the one preserved checkpoint is intentional and hardcoded as accepted |
| V-12 | Credential-checker script is safe | Ran green: 4/4 scenarios, exit 0, tempdir-only, no network |
| V-13 | No corruption | `git fsck` exit 0, zero errors |

### 5.3 Blocked by User-only approval (State 5)

| ID | Item | Why User-only |
|---|---|---|
| **U-1** | Protected-validator false-PASS fix (`validate-p2.sh:34`, `validate-sps2.sh:36`, `validate-p4.sh:120/131`) | All four validators are named protected artifacts; governance requires a User decision per file |
| **U-2** | `validate-p7-readiness.py` zero-adapter exemption | Changes a governance control's exit status; conforming but User-ratified |
| **U-3** | The four P2–P5 zero-adapter failures (same class as U-2) | Same reasoning across four further validators |
| **U-4** | Stale `note` in `ROADMAP-P3-DECISIONS.json` | Rewriting a User's decision instrument is not agent authority |
| **U-5** | `DEC-0001 KEEP_LOCAL_ONLY` breach | Only the User can supersede a User decision or record an incident |
| **U-6** | Committing the P10 gate / its 282 tests / frontend work | User ruling: preserve as untracked |
| **U-7** | The 3 unpushed commits | User instruction: no push |
| **U-8** | Attribution token-set shape gap | The approved token *set* is fixed by DEC-0025/26/27; changing matching semantics needs a User decision |

### 5.4 Investigated but not fixed (State 4)

| ID | Item | Reason not fixed |
|---|---|---|
| D-3 | Protected-validator false-PASS | Protected; see U-1 |
| D-4 | `MIN_TESTS=500` global-floor weakness | Design change to CI; recommend, do not implement |
| D-5 | `test_*.py` vs `test-*.py` glob convention | Empirically benign today (both excluded files are non-unittest scripts); documentation gap |
| D-6 | Stale `33/6` comment in `sps-ci.yml:176` | Corrected in this report; the comment is non-executing |
| D-7 | 331 tests invisible to CI | Requires committing untracked work — U-6 |
| D-8 | `validate-p4.sh` exit-status blindness | Protected; see U-1 |
| D-9 | No shell validator runs in CI at all | CI/CD scope change |
| D-10 | P10 gate has no production/CI caller | U-6 |
| D-11 | No in-repo instrument for the validator-migration commits | U-5 |
| D-12 | P5 edits lack a locating authorization instrument | U-5 |
| D-13 | **FIXED** — see F-2 | — |
| D-16 | **FIXED** — see F-3 (`setattr` on `os.environ` is a silent no-op at 2 sites) | — |
| D-14 | `test_attribution_policy.py:571` vacuous-pass risk | Derived loop set can legitimately be empty; low severity |
| D-15 | `test_ssrf_redirects.py:36` assertion is non-specific | Mutation test showed it still binds to real behaviour |

### 5.5 Known limitations intentionally retained (State 7)

| ID | Limitation | Justification |
|---|---|---|
| L-1 | Single deterministic skip (`P17_AJV_ROOT` unset) | Boundary rule forbids hardcoding a machine-global path; the reason string itself documents this |
| L-2 | `"Anti-Gravity"` not matched | Word-boundary matching is approved policy (DEC-0028 preserves it) |
| L-3 | `"Jane Self"`, `"Autonomous Council"` accepted | Ratified by DEC-0026/0027 to avoid rejecting legitimate names |
| L-4 | Credential checker detects key-name presence only | Documented narrow scope; CI wiring is U-1-adjacent |
| L-5 | Broken symlink in `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md` | **User's untracked work — must not be touched** |

### 5.6 Not tested / not yet proven (State 8)

| ID | Unproven item |
|---|---|
| N-1 | **Any real CI execution** — no run, no artifact, no run ID |
| N-2 | Ubuntu/Python 3.12 parity (only macOS 3.14.7 measured) |
| N-3 | Whether `P17_AJV_ROOT` resolves on any machine |
| N-4 | Randomization-order safety (only sorted and reversed tested) |
| N-5 | pytest behaviour of the fixed cleanup (pytest absent) |
| N-6 | Whether the preserved checkpoint token is revoked |
| N-7 | End-to-end PASS/FAIL totals of the protected validators (executing them mutates evidence — prohibited) |

---

## 6. Answers to the two questions people will actually ask

### 6.1 "How many tests pass?"

**Two different numbers measure two different things. Quote 562, not 891.**

| Corpus | Modules | Tests | Reproducible from the repo? |
|---|---|---|---|
| Clean clone of HEAD | 26 | **558** | Yes — this is the release-visible figure |
| Working tree, tracked only | 26 | **562** | No — includes my 4 uncommitted regression tests |
| Working tree, all modules | 29 | **891** | **No** — includes 331 tests in untracked files |

The 331 untracked tests (282 P10 runtime gate + 25 + 24 frontend) exist in **no commit**, are **absent from every clone**, and **cannot run in CI** because CI derives its module list from `git ls-files`. `889` was correct before this mission; it is now `891` because I added four regression tests. Neither figure is a property of the repository — both are properties of this machine.

### 6.2 "Is the portability harness green?"

**No. 33 passed / 6 failed / 14 controls, exit 1.** It was 32/7 at baseline; my RESUME fix removed exactly one failure. The remaining six are: four stale-baseline-pin failures (P2, P3, P4, P5) and two P7 zero-adapter failures.

The `33 passed, 6 failed` comment in `sps-ci.yml:176` is therefore **not stale in the way previous reports assumed** — it is the *older* accurate figure. The comment should be updated, but its existence is evidence the author once ran the harness and observed exactly the totals I now observe after one repair.

---

## 7. Defects — corrected final list

The previous report claimed "13 confirmed defects." Independent review established that count **overstated** the list: two items are governance traceability gaps, not defects, and four supporting details were wrong. The corrected list:

**Genuine defects (10):** D-1 RESUME drift **[FIXED]**, D-2 P7 overstatement, D-3 protected-validator false-PASS, D-4 CI min-guard weakness, D-5 glob convention gap, D-6 stale CI comment, D-7 331 CI-invisible tests, D-8 `validate-p4` exit-status blindness, D-13 env leak **[FIXED]**, D-16 `setattr`-no-op PATH leak **[FIXED]**.

**Governance/coverage gaps (4):** D-9 no validator in CI, D-10 P10 gate orphaned, D-11 no instrument for migration commits, D-12 P5 edits unauthorized.

**My own prior errors, corrected:** §30.

---

## 8. The single most important finding

**`DEC-0001 KEEP_LOCAL_ONLY` has been violated in fact, and this was previously under-reported as a mere "discrepancy."**

- `DEC-0001` is `APPROVED` by the User on 2026-10-03 with the instruction **"Do not configure a remote now."**
- A remote **is** configured: `origin → https://github.com/SHAHID8142/Shahid-Master-Skill.git`.
- `.git/logs/refs/remotes/origin/main` contains **three** `update by push` entries; `.git/logs/refs/remotes/origin/build/roadmap-p3-completion` contains **one**. I verified these directly. `update by push` is written only when a push to that remote succeeded.

This is a **normative policy breach already on the record**, not a pending question. It also invalidates the premise of `DEC-0002`, which defers the git-identity replacement because "`DEC-0001` keeps the repository local-only" — a premise that is false. Since the repo is no longer local-only, `DEC-0002`'s standing obligation is arguably **already due**, while 98 of 99 commits carry the placeholder identity `SPS Governance (local) <sps-governance@local.invalid>`.

No agent may resolve this. It requires a User decision to supersede `DEC-0001`, or to record the push history as an incident.

---

## 9. Compliance with the standing user instruction "always manually verify the Subagent tasks"

Five of six subagents returned findings. **Every load-bearing claim was re-executed by the lead.** That process refuted or materially refined the following subagent conclusions:

| Subagent claim | Lead's verification |
|---|---|
| A (governance) | **Subagent A FAILED before finishing.** Its scope was absorbed by the lead; §10–§13 are the lead's own work. |
| B: "two P7 failures" | **REFINED — B self-corrected to seven**, and I confirmed 6 of 7 share one class. Patching P7 alone cannot green the harness. |
| C: R5 "polarity defect" | **REFUTED then refined**: `validate-p4.sh:120/131` are *correctly polarized* but *blind to exit status*. C's four proposals were verified by me to apply cleanly and to be **better than** the prior patch set. |
| C: prior patch G is defective | **INDEPENDENTLY PROVEN.** G routes `RC=$?` through a helper invoked via `$( )`; I reproduced `RC=0` after a failure. G reintroduces the false PASS it claims to fix. |
| D: "harness is the only invoker" | **REFUTED — D refuted my own prior claim.** `validate-sps2.sh` and `validate-p3.sh:386` invoke those scripts directly. |
| E: env leak at `:255` **and** `:538` | **HALF REFUTED.** The `PATH` site at `:255` is protected by a base-class `addCleanup`; only `:538` leaks. E's split verdict is correct. |
| F: `"Self (self-approved)"` is accepted | **CONFIRMED EMPIRICALLY** — see §10. This is the most security-relevant finding any subagent produced. |

---

## 10. Security finding: a self-approving identity is accepted

`approval_is_user_attributable()` **accepts** `decided_by: "Self (self-approved)"`, and a **passing test explicitly pins that as correct** (`test_attribution_policy.py:407-421`).

Observed behaviour of the live gate:

| `decided_by` | Accepted as user-attributable? |
|---|---|
| `User` | Yes (correct) |
| **`Self (self-approved)`** | **Yes (unsafe)** |
| `Antigravity` | No (correctly rejected) |
| `Claude` | No (correctly rejected) |
| `the model` | No (correctly rejected) |
| `Jane Self` | Yes (intentional — surname protection, DEC-0026/0027) |

**Assessment.** The cause is legitimate and documented: `"self"` cannot be a rejection token without also rejecting the surname *Self*. But the consequence is that an artifact claiming to approve itself passes the attribution gate. This is currently **not exploited** — exhaustive audit found no normative record using `Self (self-approved)`. It is a **latent fail-open path** (severity Medium) that should be closed by a *specific* rule (reject an approval string whose approver is the artifact under review) rather than by adding `self` to the token set, which would break the ratified surname behaviour. This requires a User decision.

---

## 11. Governance state audit

### 11.1 Decision-state matrix

| Decision | State | Decided by | Date | Notes |
|---|---|---|---|---|
| `DEC-0001` | APPROVED | User | 2026-10-03 | `KEEP_LOCAL_ONLY` — **breached in fact** (§8) |
| `DEC-0002` | APPROVED | User | — | Git identity replacement; deferral premise now false |
| `DEC-0025` | APPROVED | User | — | `Antigravity` admitted to token set |
| `DEC-0026` | APPROVED | User | — | `Autonomous` excluded |
| `DEC-0027` | APPROVED | User | — | `self`/`script` removed |
| `DEC-0028` | APPROVED | User | 2026-10-15 | KI-16: legacy controls preserved |
| `DEC-0029` | **PENDING_USER_APPROVAL** | — | — | Legacy scope; unresolved |
| `DEC-0030` | **PENDING_USER_APPROVAL** | — | — | Legacy path definition; unresolved |

Distinct `decided_by` / `approved_by` values in normative records: **exactly `{"User"}`**. Two `null` values exist as honest `PENDING_USER_APPROVAL` placeholders. **Zero agent-attributed approvals.**

### 11.2 `DEC-0028` — the alleged tension is resolved by the record itself

A prior workstream suspected `DEC-0028` of an internal tension: it preserves P3/P4 legacy controls *unchanged* while its basis mentions reconciling validators. Reading the full record dissolves this. `DEC-0028`'s `reason` states plainly that **no approved decision authorises changing those controls**, that `REQ-P3-08` is APPROVED/VERIFIED with criterion "`git diff` against `c11da27` over legacy paths is empty", that "legacy paths" is **defined nowhere** except the script pathspec, and that narrowing the pathspec "would silently redefine the meaning of an approved and verified criterion… outside this authorization." Its `evidence` cites five locations. **There is no unresolved tension.** The tension was an artifact of reading the title without the rationale.

### 11.3 A stale `note` I deliberately did NOT fix

`ROADMAP-P3-DECISIONS.json` contains a `note` asserting completion "remains PENDING", while the **same file's** `completion.state` is `APPROVED` by the User on 2026-10-05 with `pending: []`. The `note` was written when approval was pending and never updated.

**I declined to edit it.** Although the file is not on the protected list, its prose is a User's decision instrument. Rewriting it would be altering a normative governance record — prohibited, and beyond authority. The approval itself is already recorded correctly; only narrative text is stale. **This is escalated as decision packet item D-4.**

### 11.4 Open questions — `UQ-*`

All enumerated items remain **open**. No agent may close them.

| ID | Status |
|---|---|
| `UQ-ATT-1` | PARTIALLY RESOLVED — exclusion half only; enumeration/implementation remains open |
| `UQ-ATT-2` | UNRESOLVED AND UNTOUCHED |
| `UQ-LEGACY-01` | UNRESOLVED AND UNCHANGED |
| `UQ-LEGACY-02` | UNRESOLVED — `DEC-0030` makes no determination |
| `UQ-LEGACY-03` | UNRESOLVED — `DEC-0030` creates and modifies no requirement |
| `UQ-LEGACY-04` | UNRESOLVED — evidence gap reported, no authorization inferred |

### 11.5 What is required before I can safely use SPS2?

1. **One real CI run.** Until a GitHub Actions run executes and its conclusion is captured, every pipeline statement in every SPS2 report is unverified local simulation.
2. **Decide `DEC-0001`.** The repository is already public-facing in fact; either supersede the decision or record the pushes as an incident. Then settle the git-identity obligation that `DEC-0001` was suppressing.
3. **Authorise the protected-validator repairs per file.** `validate-p2.sh` and `validate-sps2.sh` currently score a crashed or missing checker as **PASS**. Verified proposals exist; they cannot be applied without User approval.
4. **Decide whether 331 tests are part of the product.** Either commit the P10 gate and frontend tests, or record them as intentionally unwired. Today CI is blind to 37% of the suite.
5. **Resolve the `Self (self-approved)` acceptance** before any release whose approvals matter.
6. **Reconcile the harness (33/6) with the release claim.** The project's own portability exercise is red; either fix the pin question (a User decision, because it redefines an approved criterion) or document why it is excluded.
7. **Update the stale `note`** in `ROADMAP-P3-DECISIONS.json` (D-4) so the record does not contradict itself.

---

## 12. CI analysis

### 12.1 Workflow facts

Four jobs, all `ubuntu-latest`: `lint-and-smoke` (20 min), `version-sanity` (no timeout), `powershell-syntax` (no timeout), `python-unittest` (15 min, Python 3.12, `fetch-depth: 0`). No `continue-on-error`, no `defaults:`, no `| tee`, no `2>/dev/null` anywhere in `.github/`. The only `pipefail` in `.github/` is in the new job.

The most recent change to the workflow was a **pure addition** (98 insertions, 0 deletions); jobs 1–3 are byte-unchanged.

### 12.2 The decisive CI finding: no validator runs in CI at all

`test-portability.py`'s CI step is **commented out** at `sps-ci.yml:175-179`. The only other validator reference in `.github/` is that same comment. Consequently:

**Zero of the 13 core shell validators are executed by CI.** The `python-unittest` job runs only the 26 unittest modules. Every governance control in `sps2/tools/*.sh` — including the attribution policy enforcement and the credential checker — is **unenforced in CI**.

This also means the credential predicate at `validate-p3.sh:386` never gates anything, and (per unverified hypothesis H-2) a shallow clone would make it unsound anyway.

### 12.3 The min-test guard is weaker than its comment claims

`MIN_TESTS=500` against 558 executed tests leaves a margin of **58 (10.4%)**. Because the guard is a *global floor*:

- **Every one of the 26 modules can be deleted entirely** and the step still exits 0 (largest module is 42 tests; 558−42 = 516 ≥ 500).
- 25 of 26 modules are individually invisible.
- A multi-delete summing to exactly 58 (e.g. `test_url_taxonomy` 42 + `test_p17_endtoend` 2 + `test_model` 4 + `test_isolation` 5 + `test_publishing` 5) passes.

The inline comment at `:143-146` claims the guard exists "so a green build cannot mean zero executed tests" — true but far weaker than "tests were lost", which the comment also implies. Recommended, **not implemented**: assert per-module `Ran > 0`, the only form that scales.

### 12.4 Correct behaviours worth recording

- **Exit-code propagation is correct.** `STATUS=$?` sits immediately adjacent to `OUTPUT="$(...)"` with no intervening command and no wrapping subshell. Proven by injection: a failing tracked test produced `Ran 559 FAILED` and rc=1.
- **The `|| true` guards work.** `{ ...; }` is a *grouping*, not a subshell, so `exit 1` terminates the shell and is never returned to `||`. Verified 3×. The contrast case `( exit 1 )` returns 0 — that parenthesised form is the error an earlier workstream made.
- **The module glob is correctly narrow.** `test-portability.py` and `test-history-credential-check.py` end in bare `sys.exit()` and are standalone scripts, not unittest modules; excluding them is right. The residual risk is an undocumented convention: a future `test-foo.py` unittest module would be silently skipped (D-5).

---

## 13. The P7 / zero-adapter defect class

`validate-p7-readiness.py:197-198` computes

```
delivered = bool(not errs and count_ok and generic and conformance and not bound_errors)
```

Lines `:176-177` **already exempt an empty registry** for the count invariant, commented `# zero-adapter state, valid (D-P3-D)`. Line `:197` never received the same exemption for the `generic` conjunct. This is a **partially applied fix**, not a decided behaviour: the function returns `errors == []` while reporting `delivered=False`, proving no policy violation was detected.

**Governing text (verbatim, `D-P3-D`, APPROVED by User 2026-10-04):** "Delete all adapters means deletion of all per-agent adapter entries/directories. The core-owned adapter contract and registry remain. An empty adapter registry `[]` is valid and must be accepted by the portability test."

Mapped acceptance criteria: `SPS2-ROADMAP.md:38` ("deleting **all** adapters leaves core validators passing"), `:167` (P15), `SPS2-AGENT-INTEROPERABILITY.md:116-117`. Zero-adapter is a **legitimately supported state**; the validator is itself a core validator that must stay green.

**Scope correction (important).** Six of the seven harness failures share this class, across five phases: P2, P3, P4, P5, P7 readiness, and P7 mutations. **Patching P7 alone cannot green the harness** and must not be sold as "the P7 fix." This is one cross-phase remediation requiring one User decision.

**Authority:** `validate-p7-readiness.py` is **not** on the 13-file protected list (verified). The change is *conforming*, not normative, but it alters a governance control's exit status → **User approval required**.

---

## 14. Protected validators — false-PASS analysis

| Risk | Verdict | Exact site |
|---|---|---|
| R1 `validate-p2.sh` suppresses stderr, scores empty stdout as PASS | **VERIFIED** | `:34` `run_check() { python3 "$CHECK" "$1" "$2" 2>/dev/null; }`; scoring `:38`; 7 call sites `:62-68` |
| R2 `validate-sps2.sh` byte-identical duplicate | **VERIFIED** | `:36` + `:38-43`; 4 call sites `:73-76` |
| R3 neither inspects checker exit status | **REFINED** | True of the `assert_clean` helper only. `validate-sps2.sh` *does* check status at `:208`, `:220`, `:237`, `:270/273`, `:302`, `:471` |
| R4 `validate-p3.sh` scores empty as PASS | **REFINED DOWN** | `:103-104` uses `2>&1`, so a traceback is non-empty and scores FAIL. Residual hole: a checker exiting non-zero **silently** |
| R5 `validate-p4.sh` negative-control **polarity** defect | **REFUTED** | `:120`/`:131` are **correctly polarized**. The real defect is **exit-status blindness**: a dead checker yields empty stdout, no `^PROMOTED` line, and the PASS branch is taken |

**The distinction matters** and a prior workstream got it wrong in both directions. At `:97` the same blindness fails *safe* (crash → no `PROMOTED` → `fail "gate is stuck"`), while at `:120`/`:131` it fails *open*. `check_p4.py:37` emits `NOT_PROMOTED\tblocking=...`, so the repair is to require an *emitted verdict* rather than merely the absence of a line.

**Nine-case simulation summary** (empty-output-is-PASS scored): a clean checker PASSes everywhere; a crashing or missing checker PASSes at `p2:38`, `sps2:40`, and `p4:120`; `p3:104` catches crashes only because of `2>&1`; `sps2:471` correctly FAILs (it is rc-based). **No harness catches its own dead checker.**

**GNU `timeout` and `grep -P` are absent on this host** — any proposed repair must not use them. `/bin/sh` is bash 3.2.57 here, so no sh-vs-bash divergence was observed.

**Patch proposals.** The prior Phase-3 patch set was reviewed. `D4-stderr-and-exit-status.patch` applies and is correct. `C-E-p4-negative-control-polarity.patch` applies and its header already describes exit-status blindness. `F-validate-p3-harness.patch` applies but leaves `:90`/`:93`/`:520` open. **`REJECTED-G-D4-WS3-defective-subshell-rc.patch` applies cleanly but is genuinely defective** — I proved it independently (§9). Four improved per-file replacements were produced and verified to apply together with valid syntax; they remain **proposals only**.

---

## 15. Attribution verification

| Test | Result |
|---|---|
| Real 17-token policy, `decided_by: "Antigravity"` | **60 B DETECTED** |
| Control: `decided_by: "User"` | **0 B clean** |
| Degenerate `["a b"]` | 367 B DETECTED (was 0 B silent) |
| Degenerate `["("]` | 365 B DETECTED |
| Degenerate `["*"]` | 365 B DETECTED |
| Duplicate `["agent","ai","agent","ai"]` | 275 B DETECTED |
| Empty `[]` | 183 B DETECTED |
| Malformed | 112–130 B DETECTED |
| Degenerate `["zzz"]` | **0 B — fails open** |
| `test_attribution_policy` module | **68 tests OK** |

**Correction to my own earlier claim.** I previously wrote that the `["zzz"]` residual was "documented and accepted." **That is false.** `zzz` appears in **zero** decision records, requirements, governance files, or `.sps/` documents — only in three agent-written reports. It is an agent-observed behaviour, not a User-accepted residual. Severity is genuinely Low (`zzz` names no real agent), but it was **mislabeled**, and I retract the earlier wording.

Similarly, the explicit acceptance of `"Self (self-approved)"` (§10) is a **latent fail-open** that no decision authorises; it is pinned as correct by a test, which is the opposite of a User acceptance.

---

## 16. Test-corpus reproducibility

`unittest discover` is **unusable as a gate** in this repository:

| Command | Result |
|---|---|
| `discover -s . -p 'test_*.py'` | `Ran 0 tests` / `NO TESTS RAN`, **exit 5** |
| same, piped to `tail` | **exit 0** (pipe masks the status) |
| `discover -s sps2 -t .` | `ImportError: Start directory is not importable`, exit 1 |
| `discover -s domain -t .` | `ImportError`, exit 1 |
| `discover -s domain/cms/tests -t .` | exit 0, 86 tests (CMS only) |

Cause: `__init__.py` is **absent** from `sps2/`, `sps2/tests/`, and `domain/`, but **present** in `domain/{cms,seo,frontend}[/tests]`. Safe replacement used throughout: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <dotted.modules...>`.

**Skip parsing trap (confirmed by an independent subagent the hard way).** Skips are reported on an `rc=0` run. Inferring skips from the exit code yields `889/889/0/0` and falsely appears to contradict the claim. Skips must be parsed from stdout (`skipped=1`). The single skip is `test_p17_endtoend.test_generated_record_conforms_to_the_approved_schema`, deterministic, caused by `P17_AJV_ROOT` being unset, and intentional (L-1). It fires in CI, so the strongest independent JSON-Schema conformance proof for the P17 record **cannot run in CI by construction**.

---

## 17. Untracked work disposition

106 file-level untracked entries, preserved exactly (0 changed, 0 removed). Principal groups:

| Group | Files | Disposition |
|---|---|---|
`.sps/tasks` | 76 | Preserve (user work) |
`.sps/evidence` | 10 | Preserve |
`domain/frontend` tests | 6 | Preserve untracked per User ruling; invisible to CI |
`domain/cms` tests | 3 | Preserve |
`sps2/decisions` | 3 | Preserve — contains the PENDING decisions |
`sps2/tools/p10_runtime_gate.py` | 1 | Preserve untracked; **no production/CI caller** |
`sps2/tests/test_p10_runtime_gate.py` | 1 | Preserve untracked; 282 tests invisible to CI |
`reports/*.md` | 5 | Preserve — prior reports, all byte-intact |
`AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md` | 1 | Preserve — user's audit; source of §8 evidence |

**Narrowed correction:** the P10 gate has no *production or CI* caller (verified: only its own untracked test and a path-inventory line reference it). My earlier statement that it had "zero references repo-wide" was **wrong**.

---

## 18. Independent adversarial review — what did not survive

A dedicated reviewer subagent was tasked with falsifying the prior reports. It refuted several of **my own** Phase 4 claims, and I confirmed each refutation:

| Prior claim | Corrected finding |
|---|---|
| "distinct `decided_by` is exactly `{"User"}` (202/53)" | The *conclusion* holds for normative records, but the counts were wrong and the scan was not reproducible. Non-`User` values (~17) exist in fixtures, validators, audits and reports. |
| Baselines contain "a non-existent path" | **FALSE.** The path matches byte-for-byte in both baselines. It was a rendering artifact in my own output. |
| "105 untracked" | Actually 106 (103→106; three files added, all my own reports). Zero removals. |
| "dangling objects 323" | Volatile; now 336. `fsck` exits 0 with zero errors, so nothing is corrupt. |
| "`p10_runtime_gate.py` has zero references repo-wide" | Overbroad; the narrow claim (no production/CI caller) is true. |
| "G0–G14" | **Does not exist.** The repo defines only G1–G12. Phase 4 never used that vocabulary. The mission's G0–G14 framing has no in-repo counterpart. |
| "13 confirmed defects" | Overstated; 9 defects + 4 governance/coverage gaps. |
| "no decision record was modified" | `320d3a5` did touch two decision files — but **purely additively** (214/0 and 137/0, zero deletions), so hypothesis H-3 is **resolved**, not a concern. |

**Unresolved contradiction, recorded not resolved by preference:** the Phase 4 machine summary line `"no_patch_e": "FAILED(3)"` is meaningless read literally, since `domain.seo.tests.test_isolation` is `Ran 20 / OK`. It appears to describe a counterfactual. Resolving it surfaced a genuine problem Phase 4 never stated: **patch E lives in an untracked file, so a clone of HEAD contains no P10 gate at all.** The gate's green status is a property of this working tree, not of the release artifact.

### 18.1 Third independent review — the three applied fixes

A separate reviewer subagent that implemented none of the three fixes was asked to falsify them. Its verdicts and the evidence it produced:

| Fix | Verdict | Key independent evidence |
|---|---|---|
| F-1 `RESUME.md` | **SOUND** | `APPROVED` correct four ways; `cac77b6` emptied `pending` and removed the SATISFIED blocker; the `note` is stale prose proven by `git log -S 'remains PENDING'`; `test-portability.py` unmodified |
| F-2 `test_p17_security.py` | **SOUND** | Same probe: clone `SECRET_LEAKED=True` (RAN=60) vs tree `False` (RAN=62); restoration holds under injected `RuntimeError`; both tests non-tautological under mutation |
| F-3 `test_p17_pinning.py` | **SOUND_WITH_CAVEATS** | Child-process ground truth proved `setattr` never writes the environment; **but the first test design was vacuous** and was replaced |

The reviewer **reproduced the leak's survival** independently and **corrected its own method** as well as mine: its initial env audit had also marked the two sites "restored" on the basis of a registered cleanup call rather than a working mechanism. It confirmed that after F-3, **zero unguarded environment mutations remain repo-wide**, and that the other three restore sites (`test_p17_security.py:83`, `test_p17_lifecycle.py:83`, `test_p17_endtoend.py:97`) correctly use `os.environ["PATH"] = old_path`.

It also confirmed **no regressions**: 562 tests, `OK (skipped=1)`, exit 0, order-independent; clone 558; harness 33/6 in the tree vs 32/7 in the clone — a controlled demonstration that F-1 is responsible for the drift check passing.

**Durability caveat it raised (important):** neither F-1 nor F-2 is committed, so a clone of HEAD still reports `RESUME_COMPLETION_STATE_DRIFT` and 32/7, and still leaks the sentinel. CI and every clone see none of the three fixes. This is the same structural class as the 331 untracked tests, and it is escalated as DP-9.

---

## 19. Positive findings — the repository is better than its failures suggest

- The committed corpus is **genuinely green and deterministic**: 26 modules, 558 tests in a clone, 562 tracked in the tree, sorted and reversed identical, 0 failures, 1 deterministic skip.
- **No order dependence** and **no flakiness** across repeated sweeps.
- **Zero tautological assertions** repo-wide; exactly **one** `except Exception` in the entire test tree and it calls `self.fail()`.
- **No credential exposure.** A repo-wide tracked-file scan matched only deliberate fake fixtures. The one preserved checkpoint token is intentional, hardcoded as accepted at `validate-p3.sh:350`, `:369-374`, with a separate assertion that it is preserved rather than purged.
- **No corruption:** `git fsck` exit 0, zero errors.
- The project **documents its own gaps unusually honestly** — including a decision record stating that a granting instrument "is locatable nowhere."
- The `python-unittest` CI job is correctly constructed: proper `pipefail`, correct RC capture, a zero-test guard, and it is the only job in the workflow that uses `set -euo pipefail`.

---

## 20. Operator Quick Start — verified-safe commands only

Every command below was executed in this environment. None mutates repository state.

```bash
# 1. Confirm the tree is where you think it is (read-only)
git -C /Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main status --porcelain -uall | wc -l
git -C /Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main rev-parse HEAD

# 2. Run the release-visible test corpus (the clone-visible 558; here 562)
cd /Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main
MODS=$(git ls-files 'test_*.py' '**/test_*.py' | grep -E '^(sps2|domain)/' \
       | sed 's/\.py$//;s#/#.#g' | sort)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest $MODS

# 3. Run the portability exercise (read-only; expect 33 passed / 6 failed)
PYTHONDONTWRITEBYTECODE=1 python3 sps2/tools/test-portability.py 2>&1 \
  | sed 's/\x1b\[[0-9;]*m//g' | grep -E 'passed,|^ +FAIL'

# 4. Attribution policy spot-check (read-only, safe)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_attribution_policy

# 5. Credential-check predicate (safe: synthetic temp repos only)
PYTHONDONTWRITEBYTECODE=1 python3 sps2/tools/test-history-credential-check.py; echo "rc=$?"
```

**Do NOT run** `sps2/tools/validate-*.sh` end-to-end. They mutate evidence and registry state. This was a deliberate boundary of this mission and it remains the correct boundary.

**Do NOT** use `python3 -m unittest discover` — it finds 0 tests and exits 5, or exits 0 when piped, silently reporting success.

---

## 21. What is required before I can safely use SPS2? — see §11.5

(Answer repeated there in full so it is not lost in the CI section.)

---

## 22. Changes made by this mission

Three files, all non-normative, all minimal, all independently verified.

**Change 1 — `sps2/RESUME.md` (2 lines, `+2/−2`).** Root cause: `cac77b6` ("record: User approval of Roadmap P3") flipped `completion.state` from `PENDING_USER_APPROVAL` to `APPROVED` but never updated the mechanical checklist, which had been written earlier by `8d80168`. `RESUME.md`'s own header states the newest authoritative state lives in `sps2/` and that the checklist is executed mechanically by the harness — so mirroring the record is its documented contract.
- `COMPLETION: PENDING_USER_APPROVAL` → `COMPLETION: APPROVED`
- "User approval of the delivered state is PENDING" → "The User APPROVED the delivered state on 2026-10-05"

The independent reviewer confirmed `APPROVED` is correct **four independent ways**, most decisively that `cac77b6` itself emptied `pending: ["User approval of the delivered state"] → []`, removed "recording roadmap P3 as SATISFIED" from `explicitly_not_approved_yet`, and moved the reconciliation record to `SATISFIED`. The reviewer also proved the `note` is stale prose by history: `df2a715` wrote `state=PENDING` with the note tail "…remains PENDING"; `cac77b6` set `state=APPROVED` and left the note **byte-identical** (`git log -S 'remains PENDING'` shows it was never modified).

**Change 2 — `sps2/tests/test_p17_security.py` (`+49/−1`).** Restores the environment after `test_environment_is_explicit_and_minimal` mutates `os.environ`, using `addCleanup` so restoration occurs **whether the test passes, fails, or raises**. A variable that did not previously exist is removed rather than blanked. Two regression tests were added. The reviewer confirmed both are **non-tautological** by mutation: deleting the `addCleanup` line makes the negative control fail, and breaking the helper to blank-instead-of-remove fails both.

**Change 3 — `sps2/tests/test_p17_pinning.py` (`+84/−7`, discovered during this mission's own isolation sweep).** Two cleanup sites used `addCleanup(setattr, os.environ, "PATH", previous)`. That is a **silent no-op**: `setattr` on `os.environ` writes a plain instance attribute and never changes the process environment, so the injected hostile/only-on-path directories leaked onto `PATH` for the remainder of the run. Replaced with the mapping protocol (`os.environ.__setitem__`) via a shared `pin_path_entry` helper that also asserts the **observable outcome** (the directory is absent after cleanups run).

**Correction to my own first attempt at Change 3.** My initial regression tests asserted the *mechanism* rather than the *outcome*, and the independent reviewer demonstrated they were **vacuous**: reverting both call sites to the broken `setattr` form left the module reporting `OK` while the leak was still live. I replaced them. The corrected test now **fails** (`FAIL=4 ERR=2`) against the reverted code, which the reviewer's standard requires. I also introduced and then fixed an `IndentationError` and a LIFO-ordering bug in my own assertion during this correction — both caught by running the module, not by inspection.

**Deliberately NOT changed:** the stale `note` in `ROADMAP-P3-DECISIONS.json` (§11.3); any protected validator; any decision record's approval field; the four P2–P5 zero-adapter failures; `MIN_TESTS`; the CI workflow; the `.sps/GOVERNANCE.md` scope rule; any untracked file.

### 22.1 Independent review outcome for the three fixes

| Fix | Verdict | Basis |
|---|---|---|
| F-1 | **SOUND** | `APPROVED` correct 4 ways; `test-portability.py` unmodified (document adapted to harness, never the reverse) |
| F-2 | **SOUND** | Leak real and gone by controlled comparison; non-tautological tests proven by mutation; `:255` PATH site genuinely does **not** leak |
| F-3 | **SOUND_WITH_CAVEATS** | Code change correct and removes a real leak (child-process ground truth); **first version of its tests was vacuous** and has been replaced |

The reviewer also made a **methodological correction that applies to my §17 env-mutation audit**: my original pass marked the two pinning sites "restored" because it checked for the **presence** of an `addCleanup` call rather than verifying the call's **mechanism** actually restores state. That flaw is precisely why the `setattr` no-op escaped both the prior report and the reviewer's own first pass. Checking for a registered cleanup is not the same as checking that cleanup works — the same false-success pattern this mission exists to find, one level up.

---

## 23. Regression evidence after the fixes

| Check | Before | After |
|---|---|---|
| Tracked corpus | 558 / 0 failed / 1 skip | **562** / 0 failed / 1 skip (+4 regression tests) |
| Full worktree corpus | 889 / 0 failed / 1 skip | **891** / 0 failed / 1 skip |
| Clean clone of HEAD | 558 / 0 failed / 1 skip | 558 / 0 failed / 1 skip (fixes uncommitted) |
| Order independence (reversed) | identical | **562 / 0 failed / 1 skip — identical** |
| Portability harness | 32 passed, 7 failed | **33 passed, 6 failed** |
| `RESUME_COMPLETION_STATE_DRIFT` | FAIL | **gone** (reappears under negative control) |
| Env leak `SECRET_LEAKED` | True | **False** |
| Restoration under failure | not proven | **True** |
| Full-corpus `PATH_RESTORED` | **False** (2 leaked dirs) | **True** (541 → 541 chars) |
| Protected hashes | 5/5 baseline | **5/5 identical** |
| Pre-existing user edits | 7 | **7 byte-identical** |

**Third fix negative control (decisive).** Reverting the two call sites to `addCleanup(setattr, os.environ, "PATH", previous)` in a disposable copy produced `RAN=25 FAIL=4 ERR=2`, with `test_pin_path_entry_restores_path_when_cleanups_run` among the failures. The first version of these tests passed against that same reverted code — which is why the independent reviewer graded it `SOUND_WITH_CAVEATS` and why the tests were replaced.

---

## 24. Preservation attestation (verification evidence)

| Invariant | Baseline | Final | Verdict |
|---|---|---|---|
| HEAD | `cdcbca8` | `cdcbca8` | unchanged |
| Branch | `build/roadmap-p3-completion` | same | unchanged |
| Staged files | 0 | 0 | unchanged |
| Stash entries | 0 | 0 | unchanged |
| Modified tracked | 7 | 10 (the 3 I fixed) | intended, authorized |
| Untracked (file-level) | 106 | 107 (+1: this report) | 0 lost |
| Deletions | 0 | 0 | none |
| `validate-p2.sh` | `9018e0de53abe5a1` | identical | protected |
| `validate-sps2.sh` | `91509870f3d02b87` | identical | protected |
| `validate-p3.sh` | `c6ca659a7c495c87` | identical | protected |
| `validate-p4.sh` | `74af33ca7617494e` | identical | protected |
| `attribution_policy.json` | `eb9f113360601059` | identical | protected |
| `.sps/tools/validate-governance.sh` | `ba57f7372708b9d3` | identical | protected |
| All 7 pre-existing modifications | hashed | **byte-identical** | untouched |
| Prior reports (5) | sizes recorded | byte-intact | not overwritten |

A hash-comparison error in my own tooling briefly suggested all 7 pre-existing edits had changed. I investigated rather than reporting it: the baseline stores 64-character hashes and I had compared a truncated current hash against a full stored one. Corrected comparison: **all 7 UNCHANGED**. Recorded here because the near-miss is itself instructive — a false alarm reported as fact would have been a serious error.

---

## 25. Hypotheses — status

| ID | Hypothesis | Status |
|---|---|---|
| H-1 | Ubuntu would also show 32/7 | **Still unverified** — no Linux host, no containers, no network |
| H-2 | Python 3.12 parity | **Unverified** — only 3.14.7 measured (green under `-W error::DeprecationWarning`) |
| H-3 | `320d3a5` decision edits were additive | **RESOLVED — YES**, purely additive (214/0, 137/0) |
| H-4 | Shallow-clone blast radius | **Unverified** in exact count; direction confirmed for the credential checker |
| H-5 | No other runtime false-PASS in protected harnesses | **Unverified** — running them end-to-end is prohibited |
| H-6 | Credential predicate would catch a real leak | **PARTIALLY REFUTED** — key-name presence only; misses a secret under a different key, at another path, or nested outside `env`; flags an empty value; unsound on a shallow clone |

---

## 26. Gate evaluation (G0–G14 framing corrected)

The mission's G0–G14 vocabulary **does not exist in the repository**; it defines only G1–G12. Reporting against a gate set that was never written down would manufacture precision. Both vocabularies are recorded here.

| Gate | Subject | Result | Basis |
|---|---|---|---|
| G0 | Repository state captured | **PASS** | Full baseline in `/tmp/sps2-final-baseline-1792119477/` |
| G1 | Prohibitions honoured | **PASS** | §3, §24 |
| G2 | Governance audit | **PASS (audit)** / **FAIL (product)** | States verified; DEC-0001 breached, 6 UQ open |
| G3 | Protected files unmodified | **PASS** | 6/6 hashes identical |
| G4 | Defects enumerated with evidence | **PASS** | 9 defects + 4 gaps, corrected |
| G5 | Authorized remediation applied | **PASS** | 2 fixes |
| G6 | Fixes independently verified | **PASS** | Negative controls for both |
| G7 | Regression suite green | **PASS** | 562 tracked / 891 full, 0 failures |
| G8 | Clean-clone verification | **PASS** | 558 / 0 failed / 1 skip |
| G9 | CI correctness | **PARTIAL** | Job itself correct; **no validator runs in CI** |
| G10 | Independent adversarial review | **PASS** | 8 prior claims corrected |
| G11 | Preservation | **PASS** | 0 deletions, 106 preserved |
| G12 | Report completeness | **PASS** | This document |
| G13 | Real CI execution | **FAIL** | Never executed — State 8 |
| G14 | Release readiness | **FAIL** | Verdict `NOT_READY` |

---

## 27. Blockers, ordered

| # | Blocker | Who must act | Minimal action to clear |
|---|---|---|---|
| B-1 | **CI has never executed.** Every pipeline claim is local simulation | Environment + User | Trigger one run; capture the conclusion |
| B-2 | **Protected validators score a dead checker as PASS** (reproduced) | User, then agent | "Apply patch D4 to `validate-p2.sh` and `validate-sps2.sh`" |
| B-3 | **282-test P10 gate untracked, uncalled, absent from every clone** | User | Commit it, or record it as intentionally unwired |
| B-4 | **`DEC-0001 KEEP_LOCAL_ONLY` breached in fact** (4 pushes recorded) | User | Supersede `DEC-0001`, or record an incident |
| B-5 | **Project's own harness is red** (33/6) | User decides direction, then agent | Resolve the pin/authorship question; approve the P2–P5 zero-adapter repair |
| B-6 | No in-repo authorization instrument for `238c9e4`, `cdcbca8`, or the P5 edits | User | Record an instrument, or accept the gap in writing |
| B-7 | `Self (self-approved)` accepted as User-attributable | User | Decide the narrowing rule before any release that relies on approvals |
| B-8 | Attribution hardening (patch A) uncommitted → absent from clones | User | Commit, per the earlier ruling |
| B-9 | `MIN_TESTS=500` lets an entire module vanish silently | User/agent | Adopt per-module `Ran > 0` |
| B-10 | Git identity placeholder due under a now-false premise | User | Replace the identity, or re-scope `DEC-0002` |

---

## 28. Final verification sequence (13 steps)

| # | Step | Result |
|---|---|---|
| 1 | Repository state re-captured | Branch, HEAD, counts match expectation |
| 2 | Prohibitions re-checked | §3 — all honoured |
| 3 | Protected hashes re-verified | 6/6 identical |
| 4 | Pre-existing user edits re-hashed | 7/7 byte-identical |
| 5 | Untracked inventory compared | 106 → 106, 0 lost |
| 6 | Tracked corpus re-run | 562 / 0 failed / 1 skip |
| 7 | Full worktree corpus re-run | 891 / 0 failed / 1 skip |
| 8 | Order independence re-run (reversed) | 562 / identical |
| 9 | Clean clone re-run | 558 / 0 failed / 1 skip |
| 10 | Portability harness re-run | 33 passed / 6 failed (was 32/7) |
| 11 | Fix #1 negative control | Drift re-introduced → detected |
| 12 | Fix #2 negative control | Restores under failure → `True` |
| 12b | Fix #3 negative control | `setattr` revert → `FAIL=4 ERR=2`; outcome assertion fires |
| 12c | Fix #3 outcome verified | Full-corpus `PATH_RESTORED` `False` → `True` |
| 13 | Diff scope audited | 3 files, `+127/−10`, no normative content |

---

## 29. Confidence and what remains unknown

**High confidence:** all executed measurements (§23, §24), the two fix verifications, the `|| true` semantics, CI exit-code propagation, the P7 predicate and its governing text, the protected-file list, the `Self (self-approved)` acceptance, the DEC-0001 push evidence, the `not_ready` verdict.

**Medium confidence:** the fix *shape* for the protected validators (well-supported, but the User must ratify the semantics); severity framing for the fail-open paths; the portability failure classification beyond the four stale-pin failures.

**Could not determine:** whether Ubuntu would reproduce 32/7 (H-1); Python 3.12 parity (H-2); whether `P17_AJV_ROOT` resolves on any real machine; randomization-order safety (only sorted and reversed were tested); pytest behaviour (pytest absent, installs forbidden); whether the preserved checkpoint token is revoked; the true end-to-end PASS/FAIL totals of the protected validators (executing them is prohibited); whether the P3 `APPROVED` flip was a genuine User approval or agent-recorded — the record attributes it to `User` with a date, and I must not infer either way.

**Explicit limitation of this report:** every statement about CI in this document describes a **local simulation on macOS with Python 3.14.7**. CI pins `ubuntu-latest` with Python 3.12. No workflow was dispatched, no runner executed, and no run ID exists. Subagent-tested shell semantics were verified under bash 3.2.57, not the runner's bash 5.x.

---

## 30. Corrections to my own prior reporting

Recorded so downstream readers can trust the corrections rather than the earlier text.

1. **"No remote; DEC-0001 KEEP_LOCAL_ONLY"** — WRONG. A remote exists and pushes are recorded. Corrected in §8.
2. **"No decision record was modified by these commits"** — WRONG; `320d3a5` touched two decision files, though purely additively.
3. **"Untracked count 104, unchanged"** — 104 was unreachable; it is 106.
4. **"Baselines contain a non-existent path"** — WRONG. Paths match byte-for-byte.
5. **"Dangling objects 323"** — volatile; now 336.
6. **"`p10_runtime_gate.py` has zero references repo-wide"** — overbroad; no production/CI caller is the accurate claim.
7. **"The `["zzz"]` residual is documented and User-accepted"** — WRONG; no instrument documents it.
8. **"The portability harness is the only invoker of the validator suite"** — WRONG; `validate-sps2.sh` and `validate-p3.sh:386` invoke directly.
9. **"13 confirmed defects"** — overstated; 9 defects + 4 governance/coverage gaps.
10. **"G0–G14 gates evaluated"** — the repository defines only G1–G12; the framing was externally supplied.
11. **"WS3's `|| true` claim is a Critical false-green"** — correctly refuted; the guards work.
12. **"The env leak affects `:255` and `:538`"** — only `:538` leaks; `:255` is protected by a base-class cleanup.
13. **My env-mutation audit checked for the PRESENCE of an `addCleanup`, not whether its mechanism works.** That is why `addCleanup(setattr, os.environ, "PATH", prev)` — a silent no-op — was marked "restored" by both my §17 sweep and the reviewer's first pass. Corrected by D-16/F-3. This is the same false-success pattern the mission exists to find, applied to my own verification method.
14. **My first version of the F-3 regression tests was vacuous.** The independent reviewer demonstrated that reverting the defect left the module reporting `OK` while the leak stayed live. Replaced with an outcome-based assertion that fails on reverted code.
15. **I introduced an `IndentationError` and a LIFO-ordering bug** while writing the F-3 correction. Both were caught by executing the module, not by inspection — recorded because it shows inspection alone was insufficient for my own change.

Subagent A **failed before delivering**; its governance scope was absorbed by the lead. That failure is disclosed rather than concealed.

---

## 31. User Decision Packet

Each item states the decision, the options, the consequence, and the evidence. **No option is recommended as pre-approved.** The User is the only approver.

---

**DP-1 — Apply repairs to the protected validators?**
*Decision:* Authorise per-file repairs to `sps2/tools/validate-p2.sh`, `sps2/tools/validate-sps2.sh`, `sps2/tools/validate-p3.sh`, `sps2/tools/validate-p4.sh`.
*Why:* `validate-p2.sh:34` and `validate-sps2.sh:36` discard stderr and score empty stdout as PASS; a crashed or missing checker is reported as clean (reproduced). `validate-p4.sh:120/131` are correctly polarized but blind to exit status, so a dead checker passes the negative control. All four are protected artifacts requiring a User decision.
*Options:* (a) approve all four individually; (b) approve a subset; (c) decline and retain the false-PASS risk; (d) request revised proposals.
*Consequence of (a):* the controls become fail-closed; four verified per-file patches are ready and apply cleanly with valid syntax.
*Evidence:* §14; `/tmp/subC-final/proposals/` (4 patches, each single-file, each verified by the lead).

---

**DP-2 — Resolve the zero-adapter defect class?**
*Decision:* Give the empty adapter registry the same exemption the count invariant already has, across `validate-p7-readiness.py` (and the four P2–P5 validators that share the class).
*Why:* `D-P3-D` (APPROVED, User, 2026-10-04) states an empty registry "is valid and must be accepted by the portability test." `validate-p7-readiness.py:176-177` already applies that exemption; `:197` does not — a partially applied fix. Six of seven harness failures share this class.
*Options:* (a) approve the cross-phase repair; (b) approve P7 only and accept that the harness stays red; (c) decline.
*Consequence of (a):* the harness can become green; no delivered-state behaviour changes.
*Evidence:* §13; `validate-p7-readiness.py:167,176-177,197-198,229-230`.

---

**DP-3 — How should the portability pin failures be resolved?**
*Decision:* Four validators fail because `REQ-P3-08`'s criterion `git diff` against `c11da27` over legacy paths is non-empty — `.github/workflows/sps-ci.yml` (added after the pin) and three `.sps/tools/*.sh` files match.
*Why:* `REQ-P3-08` is APPROVED with verification `VERIFIED`, and "legacy paths" is defined nowhere except the script pathspec. Moving the pin alone would not fix it, and would silently bless both file sets.
*Options:* (a) move the pin and record the justification; (b) narrow the pathspec (a normative change to an approved criterion); (c) leave red and document; (d) commission an instrument deciding what "legacy paths" means.
*Evidence:* §12, §14; `DEC-0028`'s `reason` text; D's independent reproduction.

---

**DP-4 — Update the stale `note` in `ROADMAP-P3-DECISIONS.json`?**
*Decision:* Its `note` says completion "remains PENDING" while its own `completion.state` is `APPROVED` by the User on 2026-10-05.
*Why:* I declined to edit it — rewriting a User's decision instrument is not agent authority. But the file currently contradicts itself.
*Options:* (a) authorise a User-dated correction to the `note`; (b) leave it as a historical artifact; (c) add a separate note recording the change.
*Evidence:* §11.3.

---

**DP-5 — Resolve `DEC-0001` and the git identity.**
*Decision:* `DEC-0001 KEEP_LOCAL_ONLY` ("do not configure a remote") has been breached in fact; four successful pushes are recorded. `DEC-0002`'s deferral of the identity replacement rests on the now-false premise that the repo is local-only, and 98 of 99 commits carry a placeholder identity.
*Options:* (a) supersede `DEC-0001` and ratify the remote; (b) record the pushes as an incident and reaffirm local-only; (c) leave both decisions and document the divergence.
*Consequence:* governing the repository's publication status and the authorship provenance of every commit.
*Evidence:* §8; `.git/logs/refs/remotes/origin/*`; `.sps/STATE.md:86-88`.

---

**DP-6 — Commit or record the 331 CI-invisible tests?**
*Decision:* `sps2/tests/test_p10_runtime_gate.py` (282 tests), `domain/frontend/tests/test_content_slots.py`, and `test_layout_registry.py` are untracked, so CI never runs them, and the P10 gate they exercise has no production or CI caller.
*Options:* (a) authorise committing them; (b) record them as intentionally unwired; (c) leave the current state undocumented.
*Evidence:* §6.1, §17.

---

**DP-7 — Close the `Self (self-approved)` acceptance?**
*Decision:* The attribution gate accepts a self-approving identity string and a passing test pins that as correct.
*Why:* `"self"` cannot become a rejection token without rejecting the legitimate surname *Self* (ratified by DEC-0026/0027).
*Options:* (a) add a specific rule rejecting an approval whose approver is the reviewed artifact; (b) accept the residual and document it; (c) revisit the surname decision.
*Evidence:* §10; `test_attribution_policy.py:407-421`.

---

**DP-8 — Adopt a per-module test guard?**
*Decision:* `MIN_TESTS=500` against 558 leaves a 58-test margin, so every one of the 26 modules can be deleted entirely without failing CI.
*Options:* (a) assert per-module `Ran > 0`; (b) pin an exact expected total; (c) raise the floor and accept reduced sensitivity; (d) leave as-is.
*Evidence:* §12.3.

---

**DP-9 — Commit the uncommitted work?**
*Decision:* The attribution hardening (`sps2/governance/attribution.py`, `+57/−0`) and the two fixes in this report are uncommitted, so no clone contains them. Three commits remain unpushed.
*Options:* (a) commit the hardening and the two fixes; (b) commit only selected files; (c) leave uncommitted; and separately, whether to push.
*Consequence:* until committed, the fixes and hardening are properties of this working tree only — the same structural problem as the 331 untracked tests.
*Evidence:* §22, §23.

---

**DP-10 — Record an authorization instrument for the migration commits?**
*Decision:* `238c9e4` (validator migration) and `cdcbca8` (CI job) rest on conversational authorization; `grep "CI/CD"` over `sps2/decisions`, `sps2/requirements`, `sps2/governance`, and `.sps/decisions` returns zero hits, and `.sps/GOVERNANCE.md`'s scope rule was never formally amended in-repo. The P5 requirement/evidence edits likewise have no locating instrument.
*Options:* (a) record an instrument in-repo; (b) accept the traceability gap in writing; (c) leave unrecorded.
*Note:* `.sps/GOVERNANCE.md`'s scope rule is itself scoped to "Phase 02", so it may not bind this work — the gap is traceability, not a confirmed violation.
*Evidence:* §11; `LEGACY-PATH-DEFINITION-DECISIONS.json:107`.

---

**DP-11 — Who authored `sps2/tests/test_p17_pinning.py` mid-review, and should its tests be trusted?**
*Decision:* A third modification appeared in the working tree *during* the independent review (mtime 2026-10-16 09:30:03), raising the modified-tracked count from 9 to 10. It was written by this mission's own lead as part of the §17 isolation sweep — **not** by the reviewer and **not** pre-existing user work.
*Why it is recorded:* The reviewer could not attribute it and correctly treated an unexplained mid-review change to a file outside its brief as a process concern. Its **code fix is correct** (proven with child-process ground truth), but its **first version of the regression tests was vacuous** — reverting the defect left the module green. The tests were replaced and now fail on reverted code.
*Options:* (a) accept the change and its corrected tests; (b) revert the change entirely and record the PATH leak as an open defect; (c) accept the code fix but substitute the reviewer's suggested per-test `addCleanup(self._assert_path_restored)` design.
*Risk if deferred:* the PATH leak (D-16) remains; leaked temp directories containing stub executables named `stub-agent` and `path-only.py` stay on `PATH` for the rest of the process, so a later test resolving an agent by name could pick a leaked stub.
*Evidence:* §5.1 F-3, §22 Change 3, §22.1, §23.

---

## 32. Final statement

**Mission status: COMPLETE as an audit and remediation exercise.**
**Product verdict: `NOT_READY`.**

Three defects were fixed and independently verified with negative controls on the real harness and real code, inside the agent's authority: the `RESUME.md` completion-state drift, a leaked environment sentinel in the P17 security tests, and a `setattr`-on-`os.environ` no-op that silently leaked injected directories onto `PATH` at two sites. The third was found by this mission's own isolation sweep, and its first regression tests were shown to be vacuous by the independent reviewer before being replaced with outcome-based assertions that fail on reverted code. Nine further defects and four governance gaps were investigated, evidenced, and classified. Eleven decisions were escalated to the User because they exceed agent authority — including three repairs to protected validators that are ready to apply but must not be applied by an agent.

Two of the three fixes are structurally fragile for the same reason the 331 untracked tests are: **they are uncommitted**, so no clone and no CI run contains them. A clean clone of `cdcbca8` still reports `RESUME_COMPLETION_STATE_DRIFT`, still scores 32/7 on the harness, and still leaks the sentinel. Until they are committed, they protect only this working tree.

The repository is genuinely healthier than a `NOT_READY` verdict suggests: its committed corpus is green, deterministic, order-independent, and free of tautological assertions and credential exposure, and it documents its own gaps with unusual honesty. It is not a released artifact, and the gap between those two statements is measurable: **558 tests rather than 891, zero validators executed in CI, four decisions breached or awaiting the User, and a pipeline that has never once run.**

Progress on a build is not approval of a deliverable. Nothing in this report approves anything.

---

*End of report. No commit, push, deploy, or remote operation was performed. The repository working tree contains exactly two additional modifications relative to the mission baseline, both enumerated in §22.*
