# SPS2 PHASE 2 — RELEASE-READINESS ASSESSMENT

- **Mission**: SPS2 Phase 2 — false-PASS remediation, checker hardening, test
  infrastructure analysis, regression testing, CI readiness, governance-safe patch
  preparation, reproducibility, and release-readiness assessment.
- **Report path**: `reports/SPS2-PHASE2-RELEASE-READINESS-20261016-072628.md`
  (confirmed absent before first write; new file, nothing overwritten).
- **Repository**: `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`
- **Branch**: `build/roadmap-p3-completion`
- **Starting HEAD**: `320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71` (short `320d3a5`)
- **Final HEAD**: `320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71` (**unchanged**)
- **Cached origin ref**: `788bf8a2892ee72705276c9d846626ca0470400d` (short `788bf8a`)
- **Divergence**: ahead 1 / behind 0.

> **Verification standard.** Every number in this report was produced or reproduced by the
> lead agent on this host. The six workstream deliverables were treated as *leads to
> verify, not facts to repeat*. Where a workstream claim could not be reproduced it is
> marked `[NOT VERIFIED]`. Nothing was staged, committed, amended, pushed, deployed,
> stashed, reset, cleaned, fetched or pulled. No network access, no installs, no lockfile
> changes.

---

## 1. Executive summary

Phase 2 set out to remediate false-PASS defects, harden checkers, analyse test
infrastructure, assess CI readiness and prepare governance-safe patches. It succeeded on
remediation and patch preparation, and produced a **net-negative result on the Phase-1
report's own accuracy** — five of its claims were wrong, two in the direction of
*understating* risk.

The most important outcome is that **the false-PASS class is wider than Phase 1
concluded.** Three independent, separately reproduced instances now exist:

1. **`check_p2.py` non-dict list elements** — a present, correctly-typed list of integers
   still crashes each handler, escapes `main()`, and leaves stdout empty, which
   `validate-p2.sh` scores as PASS. **Fixed in this mission.**
2. **`check_p3.py records` unknown kind** — a bare `else:` falls through to the handoffs
   check, emits nothing, and `validate-p3.sh:103` scores PASS. Proposal B.
3. **`load_agent_tokens()` semantic fail-open** — a well-typed but degenerate `tokens[]`
   silently disables agent-attribution detection across three harnesses while every run
   reports clean. This **directly contradicts the Phase-1 report's §7.2 matrix**, which
   listed those exact payloads as *not* false-PASS. Proposal F.

A **self-inflicted defect in the Phase-1 test suite** was also found and fixed: the test
written to prevent checker drift was a tautology that passed with the checker fully
reverted.

Release readiness is **not achieved**. Three HIGH blockers remain, and all three are
blocked on **User authority rather than on engineering**. No amount of further agent work
unblocks them.

---

## 2. Overall status

**PARTIAL — NOT release-ready.**

| Dimension | Verdict |
|---|---|
| False-PASS surface | **Reduced, not eliminated** (1 of 3 instances fixed; 2 are proposals) |
| Checker hardening | Improved (`check_p2.py` element guard + 2 regression tests) |
| Test infrastructure | Analysed; **zero-test discovery defect proven**; layout fix required before CI |
| Regression testing | 878 passed / 3 failed / 1 skipped across 29 modules |
| CI readiness | **Not ready** — CI is RED at HEAD and runs zero Python tests |
| Patch preparation | 7 proposals written outside the repository, none applied |
| Reproducibility | Deterministic; three provenance hazards documented |
| Governance | **Respected** — no approval inferred, no protected file modified |
| Preservation | **Verified** — HEAD, index, branches, protected hashes all unchanged |

Status is **PARTIAL** rather than BLOCKED because substantial safe work advanced and each
remaining item has a concrete, documented unblock path. It is not VERIFIED because three
confirmed defects remain unfixed by design (authority withheld) and the suite is not fully
green.

---

## 3. Repository identity and baseline

| Item | Value |
|---|---|
| Repository root | `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main` |
| Branch | `build/roadmap-p3-completion` |
| HEAD (start and end) | `320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71` |
| Cached origin ref | `788bf8a2892ee72705276c9d846626ca0470400d` |
| Ahead / behind | 1 / 0 (no fetch performed; cached ref only) |
| Porcelain entries | 23 (identical at start and end) |
| Staged files | 0 |
| Stash count | 0 |
| Index sha256[:16] | `647138fe9ec717e5` (unchanged) |
| Python | 3.14.7; `pytest` **absent** |
| Network | **not used** |

### 3.1 The 13-file attribution commit manifest `[VERIFIED]`

```
 1. sps2/capability/engine.py                          8. sps2/tests/test_shell_validator_policy_contract.py
 2. sps2/capability/promotion_gates.py                 9. sps2/tools/check_p2.py
 3. sps2/decisions/ATTRIBUTION-POLICY-DECISIONS.json  10. sps2/tools/check_p3.py
 4. sps2/decisions/OPEN-DECISION-ATTRIBUTION-TOKEN-SET.json  11. sps2/tools/check_sps2.py
 5. sps2/governance/attribution.py                    12. sps2/tools/validate-p3.sh
 6. sps2/governance/attribution_policy.json           13. sps2/tools/validate-p4.sh
 7. sps2/tests/test_attribution_policy.py
```

Confirmed: exactly 13 paths, **all** under `sps2/`, with **0** p10-named and **0**
`domain/` entries. (The repository *tree* does contain 6 p10-named and 45 `domain/` tracked
files; that is a different measurement and does not contradict the manifest.)

### 3.2 Pre-existing generated artifacts — recorded, NOT cleaned `[VERIFIED]`

12 `__pycache__` directories and 76 `.pyc` files exist under `sps2/` and `domain/`. Per
rule 15 these were **left in place**. All mission commands used
`PYTHONDONTWRITEBYTECODE=1`, so the mission created none.

### 3.3 Baseline state vs Phase 2 changes

| Category | Detail |
|---|---|
| **Pre-existing before Phase 2** | 12 tracked files modified (incl. the 3 protected `.sps/tools` validators, 3 checker/test files from Phase 1), plus untracked `domain/frontend/`, `domain/cms/data/`, `sps2/tools/p10_runtime_gate.py`, `sps2/tests/test_p10_runtime_gate.py` |
| **Changed by Phase 2** | `sps2/tools/check_p2.py` (+9 lines over Phase 1), `sps2/tests/test_attribution_policy.py` (drift test replaced + 1 new test), and this report file |
| **Still blocked from modification** | `.sps/tools/validate-capability.sh`, `validate-control.sh`, `validate-governance.sh` (clause C); `REQ-P3-08` / "legacy paths" (clause D); `sps2/governance/*`; `domain/seo/` (P9); P10 decision records |

### 3.4 Starting-state discrepancies vs the brief

None. Branch, HEAD, cached origin ref, 13-file commit, and the previous report's location
all matched the brief exactly. No value was "restored" and nothing was reset.

---

## 4. Previous report cross-check

Previous report: `reports/SPS2-OVERNIGHT-BUILD-VERIFICATION-20261016-063738.md`
(56,549 bytes, sha256[:16] `cb8c421721f4d54f`, status PARTIAL, claimed 828/3/1).
It was read in full and validated against the actual tree. **It was not overwritten and
remains present and byte-identical.**

### 4.1 Claims that were CHECKED and SURVIVED `[VERIFIED]`

| Claim | Verification | Result |
|---|---|---|
| Two false-PASS defects fixed in `check_p2.py` / `check_p3.py` | `REQUIRED_COLLECTIONS` present; p3 registry guard present at `main():184` | **confirmed, fixes persist in tree** |
| Regression tests added | `TestCheckerDocumentShapesFailVisibly`, `TestP3RecordsModeActuallyChecks` present | **confirmed** |
| 3 SEO isolation failures reproduced at pristine `788bf8a` by adding only the untracked gate | 4-configuration clone matrix | **confirmed exactly** |
| Attribution commit excludes P10/frontend/CMS/SEO | 13-file manifest inspected | **confirmed** |
| Committed revision has 3 failures in `test_shell_validator_policy_contract` | pristine clone at `320d3a5` | **confirmed 3/7 fail** |
| Three `.sps/tools` validators remain protected | `git status` shows ` M`, unstaged | **confirmed** |
| PCRE/POSIX grep incompatibility in `validate-governance.sh` | `:180` lookahead + BSD grep rc=2 | **confirmed as root cause** |
| Stderr suppression in `validate-p2.sh` / `validate-sps2.sh` | `:34` / `:36` both `2>/dev/null` | **confirmed** |
| CI does not run Python unit tests | full read of `sps-ci.yml`; grep for python/unittest/pytest = 0 matches | **confirmed** |
| `check_p3.py` silently accepts unknown record kinds | corrupt-fixture test | **confirmed as a real false PASS** |
| Matcher does not match `co-pilot` | 4 spelling variants tested | **confirmed, and correctly an approved non-goal** |
| P10/P9 remediation governance-blocked | `P10-DECISIONS.json` `standing_bounds.P9` | **confirmed verbatim** |

### 4.2 Claims that did NOT survive — corrected

| # | Phase-1 claim | Corrected finding | Severity |
|---|---|---|---|
| 1 | `check_p4.py` malformed input implies a false PASS | `validate-p4.sh` uses **positive-marker** scoring; crashes are scored as **rejection**. **Fails safe.** | over-claim, retracted |
| 2 | Malformed-policy matrix rows marked "NO" false-PASS | Those exact rows are **fail-open**: 60 B detection → **0 B** with degenerate tokens | **risk understated** |
| 3 | "27 and 29 failures" for the two fixes | 29 = 27 (p2 alone) + **2** (p3 alone); isolated p3 is 2, not 29 | measurement conflation |
| 4 | 828 passed / 27 modules | **878 passed / 29 modules**; `domain/frontend/` (49 tests) is untracked and was omitted | undercount |
| 5 | p3 tests "57 → 60" | **53 → 60** | arithmetic |
| 6 | Drift-prevention test existed | It was a **tautology** — passed with the checker reverted. **Replaced.** | self-inflicted, fixed |

---

## 5. Six workstream summaries

All six ran at depth 1 with no nested subagents. Each deliverable was independently
verified; three required correction.

| WS | Subject | Delivered | Lead verification outcome |
|---|---|---|---|
| 1 | Checker contracts & unknown-input hardening | `CHECKER-CONTRACTS.md`; D5 patch + regression test | D5 **confirmed**; provenance `788bf8a:198` path-as-kind **confirmed**; D7 **independently reached the same fail-safe conclusion**; its patch applied clean and fixed unknown kinds |
| 2 | Shell-harness false-pass analysis | `D3`, `D4` patches; execution-chain audit | D3/D4 **confirmed**; **new finding** `validate-p4.sh:120/:131` polarity inversion **confirmed**; **its D3 patch failed `git apply --check`** → lead regenerated against committed HEAD |
| 3 | Test infrastructure & discovery | `TEST-INFRA-CI.md`; CI job patch | zero-test discovery **confirmed with decisive proof** (0 → 543 tests); CWD-dependence **confirmed**; `fetch-depth: 0` need **confirmed** |
| 4 | Attribution security & semantic boundaries | `ATTRIBUTION-BOUNDARIES.md` | token set/matcher **confirmed**; **F1 semantic fail-open confirmed** with a properly controlled fixture; hyphen gap **confirmed** as approved non-goal |
| 5 | P10/P9, CMS, frontend, cross-dependencies | `P10-P9-DEPENDENCIES.md`, options, remediation patch | 4-configuration matrix **confirmed exactly**; "not pre-existing" terminology **accepted and sharpened**; `P9_ALLOWLIST_RELATIVE_PATHS` dead code **confirmed** |
| 6 | Independent adversarial review | `INDEPENDENT-REVIEW.md` | tautology **confirmed by two independent proofs**; residual p2 false-PASS **confirmed**; 878/3/1 totals **confirmed**; its "6 p10 + 45 domain" claim is a **scope error** (repo tree, not commit manifest) — Phase-1 claim stands |

### 5.1 A rejected workstream claim

WS6 asserted the Phase-1 statement "`320d3a5` contains zero p10/domain paths" is false. The
lead checked both readings: the **commit manifest** has 0 p10 and 0 `domain/` entries
(the original claim was correctly scoped), while the **repository tree** has 6 p10-named
and 45 `domain/` tracked files. Both facts are true; they answer different questions. The
original claim **stands**; the correction was a scope error.

---

## 6. All checkers reviewed

| Checker | Top-level type guard | Required keys | Collection type | Unknown mode | Unknown kind | Exit contract |
|---|---|---|---|---|---|---|
| `check_sps2.py` | ✅ ERR + exit 0 | ✅ ERR | ✅ ERR | ✅ `return 2` | ✅ `return 2` | ✅ compliant |
| `check_p2.py` | ✅ ERR + exit 0 | ✅ ERR | ✅ ERR | n/a | returns clean (no-op) | ✅ compliant |
| `check_p3.py` | ⚠️ inconsistent across modes | ✅ ERR (registry) | ✅ ERR | ✅ | ⚠️ **silent → false PASS** | ⚠️ D5/D5b |
| `check_p4.py` | ⚠️ uncaught traceback | n/a | n/a | n/a | n/a | ⚠️ exits 1 (documented: always 0) — **fails safe** |
| `check_p10_inventory.py` | ✅ names observed type | ✅ | ✅ | ✅ `return 2` | ✅ `return 2` | ✅ **best design in repo** |
| `validate-p5/p6/p7-readiness.py` | top-level validators, real exit codes — empty-stdout class **does not apply** |

`check_sps2.py` is the precedent: it already reports `capabilities[0] is not an object`,
which is exactly the shape `check_p2.py` was missing.

---

## 7. All harnesses reviewed

| Script | Checker call | stderr mode | Return-code check | Success condition | Missing-checker behavior | Crash behavior | False-PASS risk | Authorization |
|---|---|---|---|---|---|---|---|---|
| `validate-p2.sh` | `run_check()` `:34` | `2>/dev/null` | none | empty stdout = clean | **empty → PASS** | **empty → PASS** | **HIGH (D4)** | protected (clause C) |
| `validate-sps2.sh` | `run_check()` `:36` | `2>/dev/null` | none | empty stdout = clean | **empty → PASS** | **empty → PASS** | **HIGH (D4)** | protected (clause C) |
| `validate-p3.sh` | `:90`, `:103`, `:107` | `2>&1` | none | `[ -z "$OUT" ]` = pass | traceback captured | traceback captured | MEDIUM (D5 only) | protected (clause C) |
| `validate-p4.sh` | `:72`, `:97`, `:109` | `2>&1` | none | `grep -q '^PROMOTED'`; **absence = reject** | rejected ✅ | rejected ✅ | LOW — **fails safe**, but see §10 polarity | protected (clause C) |
| `.sps/tools/validate-capability.sh` | `ATTR.AGENTISH` | — | — | divergent list at HEAD | — | — | n/a | **protected, not executed** |
| `.sps/tools/validate-control.sh` | `ATTR.AGENTISH` | — | — | divergent list at HEAD | — | — | n/a | **protected, not executed** |
| `.sps/tools/validate-governance.sh` | `ATTR.AGENTISH` | `2>/dev/null` `:180` | none | lookahead fails → else prints pass | — | — | **HIGH (D3)** | **protected, not executed** |

**No protected validator was executed end-to-end.** All harness conclusions were derived by
transcribing the exact shell predicates and running them against real checker output, in
disposable fixtures.

---

## 8. False-PASS execution-chain matrix

The defining mechanism: **a shell harness scores empty stdout as PASS.** The enabling
mechanism is `set -uo pipefail` **without** `-e` — a failed command substitution does not
abort the script. Lead-verified: `bash -c 'set -uo pipefail; x="$(false)"; …'` survives
with rc-of-assignment 1.

### 8.1 Instance 1 — `check_p2.py` non-dict list elements **FIXED**

Chain: `{"sources": [1]}` → handler calls `.get()` on an `int` → `AttributeError` escapes
`main()` → stdout **empty**, stderr populated → `run_check()` discards stderr
(`validate-p2.sh:34`) → `assert_clean` sees `''` → **`pass()`**.

Measured before, all 7 kinds (`sources`, `capability`, `interop`, `requirements`,
`evidence`, `decision`, `handoff`): rc=1, **stdout 0 B**.
Measured after: **31–36 B** visible ERR, rc=0, no traceback.

### 8.2 Instance 2 — `check_p3.py records` unknown kind **PROPOSAL B**

Chain: unknown kind → falls to `else:` (the handoffs branch) → inspects `handoffs` key of a
non-handoff document → finds nothing → stdout **empty** → `validate-p3.sh:103`
`[ -z "$OUT" ] && pass` → **PASS**.

Measured against a fixture corrupt **only** for `requirements` (the discriminating
control): `requirements` → 31 B correct; `bogus`/`reqs`/`""` → **0 B**.

**Provenance `[VERIFIED]`:** at `788bf8a:198` the dispatch was
`check_records(sys.argv[2 + 1], sys.argv[3])` — the **path** was passed as the kind, so
*every* kind was vacuous. `320d3a5` corrected it to `sys.argv[2]`, narrowing the defect to
the unknown-kind residue. **Pre-existing, narrowed — not newly introduced.**

**Corollary D5b (arguably worse):** every branch reads `d.get(<key>, [])`, so `{}` scores
clean for **all four legitimate kinds**. An absent collection is indistinguishable from an
empty one — the same root cause the Phase-1 `check_p2.py` fix addressed, still present in
`check_p3.py`.

**Important non-defect:** `evidence`/`decisions`/`handoff` returning 0 B when pointed at a
*requirements* document is **correct** — such a document legitimately has no such key. All
four real P3 documents validate clean. Do not "fix" that.

### 8.3 Instance 3 — `load_agent_tokens()` semantic fail-open **PROPOSAL F**

Chain: a well-typed but degenerate `tokens[]` is accepted → `re.escape()` keeps the
malformed pattern compiling → the matcher matches nothing → each checker emits **0 B** →
`assert_clean` scores **clean** → the agent-attribution control is silently gone while
every harness reports success.

Controlled proof (one capability, fully conforming **except**
`approval.decided_by: "Antigravity"`):

| policy `tokens` | `check_sps2.py` stdout | detection |
|---|---|---|
| real 17-token policy | 60 B `ERR … APPROVED attributed to non-user 'Antigravity'` | ✅ |
| `["agent","ai","agent","ai"]` | **0 B** | ❌ fail-open |
| `["("]` / `["*"]` / `["a b"]` | **0 B** | ❌ fail-open |

**Methodological note retained deliberately:** the lead's *first* attempt at this test was
invalid — the fixtures carried unrelated errors (`bad capability_id`,
`invalid security status 'CLEAN'`) whose ERR lines dominated stdout (43/46 B for every
payload) and made everything look closed. Only after making the document conforming in
every other respect did the true 60 B → 0 B delta appear. This is the same class of mistake
that produced the Phase-1 error.

### 8.4 Complete shape coverage after Phase 2

| Shape | `check_sps2.py` | `check_p2.py` | `check_p3.py` |
|---|---|---|---|
| missing collection key | ERR ✅ | ERR ✅ | ERR ✅ |
| non-list collection value | ERR ✅ | ERR ✅ | ERR ✅ |
| **non-dict list elements** | ERR ✅ | **ERR ✅ (fixed)** | n/a |
| unknown kind | exit 2 ✅ | clean (no-op) | **silent → PASS ⚠️** |
| absent collection `{}` | — | ERR ✅ | **silent → PASS ⚠️** |
| degenerate policy tokens | **silent → PASS ⚠️** | **silent → PASS ⚠️** | **silent → PASS ⚠️** |

Phase 2 closed one row. Until proposals B and F land, the class is **reduced, not
eliminated**.

---

## 9. Every defect confirmed

| ID | Defect | Location | Class | Provenance | State |
|---|---|---|---|---|---|
| D-nondict | Non-dict list elements → empty stdout → PASS | `check_p2.py:_check_collection` | **A — false PASS** | Phase-1 fix left it open | **FIXED** |
| D5 | Unknown `records` kind → handoffs fallback → empty stdout → PASS | `check_p3.py:check_records` | **A — false PASS** | pre-existing (total at `788bf8a`, narrowed at `320d3a5`) | Proposal B |
| D5b | Absent collection indistinguishable from empty | `check_p3.py` all branches | **A — false PASS** | pre-existing | Proposal B |
| F1 | Degenerate well-typed policy silently disables attribution | `attribution.py:load_agent_tokens` | **A — false PASS** | pre-existing | Proposal F |
| D3 | PCRE lookahead in `grep -E` → rc=2 discarded → pass printed | `.sps/tools/validate-governance.sh:180` | **A — false PASS** | pre-existing (identical at `788bf8a:180`) | Proposal D3 (protected) |
| D4 | `2>/dev/null` + empty-stdout-PASS; missing checker passes | `validate-p2.sh:34`, `validate-sps2.sh:36` | **A — false PASS** | pre-existing | Proposal D4 (protected) |
| NEW-p4 | Negative controls invert the positive control's polarity | `validate-p4.sh:120`, `:131` | **A — false PASS (control level)** | pre-existing | Proposal E (protected) |
| D7 | Unactionable `AttributeError`; exits 1 vs documented always-0 | `check_p4.py` | **B — visible failure** | pre-existing | documented, not fixed (would alter P4 scoring) |
| D9 | Raw/misleading messages for non-dict payload and missing path arg | `check_p3.py` | **C — robustness** | pre-existing | documented |
| D10 | Top-level-type handling inconsistent across modes | `check_p3.py` | **C — robustness** | pre-existing | documented |
| NEW-taut | Drift-prevention test was a tautology | `test_attribution_policy.py:1258` | **test defect** | introduced in Phase 1 | **FIXED** |

**Confirmed defect count: 11** (6 false-PASS class, 1 visible-failure, 2 robustness,
1 test defect, 1 control-polarity).

---

## 10. Every defect disproven or reclassified

| Claim | Reclassification | Evidence |
|---|---|---|
| **D7 is a false PASS** (Phase-1 implication) | **DISPROVEN — fails safe.** `validate-p4.sh` scores by positive marker (`grep -q '^PROMOTED'`, absence = reject); `check_p4.py` on `null`/`[]`/`42`/`"string"`/`true` → rc=1, 0 B stdout, 612–617 B traceback, captured via `2>&1`, contains no `^PROMOTED` → scored **rejection**. `{}` → 303 B genuine `GATE_RESULTS … FAIL`. Not-JSON → 68 B `GATE_ERROR`. Two workstreams and the lead independently agreed. | exact predicate transcription |
| **The p3 registry guard covers 9 payloads** | **RECLASSIFIED — load-bearing for 2 of 9.** At HEAD only `{}` and `{"capabilities":null}` give empty stdout; 7 payloads were already visible via a pre-existing blanket `except Exception`. | per-payload measurement at HEAD |
| **Isolated p3 revert = 29 failures** | **RECLASSIFIED — 2.** 29 is both-reverted; 27 is p2-only. | three-clone isolation matrix |
| **"Pre-existing" SEO failures** | **RECLASSIFIED — introduced by the untracked gate.** A clean checkout is green; only the developer tree is red, because of one untracked file. `320d3a5` is not the cause (contra neither reading). | 4-configuration clone matrix |
| **`320d3a5` contains p10/domain paths** (WS6 correction) | **DISPROVEN — scope error.** The commit manifest has 0 p10 and 0 `domain/` entries. The repo *tree* has 6 and 45. Original claim stands. | manifest vs `git ls-files` |
| **The naive P9 allowlist fix would work** | **DISPROVEN — dead code.** `P9_ALLOWLIST_RELATIVE_PATHS` (`isolation.py:47-74`) is read by no logic anywhere. | grep for all readers |
| **`co-pilot` mismatch is a defect** | **RECLASSIFIED — approved non-goal.** See §20. | DEC-0025 + `non_goals[3]` |
| **`openai` should match** | **WORKSTREAM SELF-CORRECTION.** `ai` has no word boundary inside `openai`; non-match is correct. Recorded so it is not mistaken for a defect. | boundary test |

---

## 11. Every fix applied

Two changes, both within authorized runtime scope (checker modules and their tests —
not protected validators, not governance artifacts). Both **unstaged**.

### Fix 1 — `sps2/tools/check_p2.py`: reject non-dict list elements

Closes the residual false-PASS. `_check_collection()` now iterates the collection and
appends `<key>[i] is not an object` for any non-dict element, returning `False` so the
per-record handler is skipped. This mirrors `check_sps2.py`'s existing behavior exactly.

Scope compliance: not a protected validator; not a governance artifact; requires no new
decision; strengthens rather than weakens a control; backed by a reproducible defect; a
regression test was added; related tests pass; user changes preserved.

### Fix 2 — `sps2/tests/test_attribution_policy.py`: repair the tautology + add a regression test

`test_checker_document_guards_do_not_drift_between_siblings` now builds its commands from
the loop variables (it previously ran the byte-identical hardcoded command 7 times), and
`test_non_object_list_elements_are_reported` covers Fix 1 across 7 kinds × 4 element types.
No assertion was weakened and none removed; assertion count increased.

### Not fixed, by design

D5, D5b, D3, D4, NEW-p4, F1 — proposals only (authority withheld or scope governed).
D7, D9, D10 — documented; D7's fix would alter P4's positive-marker scoring and belongs to
the harness owner.

---

## 12. Exact diff summary for every changed file

| File | vs HEAD (cumulative) | Phase 2 contribution | Staged |
|---|---|---|---|
| `sps2/tools/check_p2.py` | **+57 / −0** | +9 (element guard + comment) | no |
| `sps2/tools/check_p3.py` | **+17 / −1** | 0 (Phase 1 only) | no |
| `sps2/tests/test_attribution_policy.py` | **+261 / −2** | drift test replaced; +1 test method | no |
| `reports/SPS2-PHASE2-RELEASE-READINESS-20261016-072628.md` | new file | this report | no |

The Phase 2 addition to `check_p2.py`, verbatim:

```python
    # A present, correctly-typed list of NON-OBJECT elements is the third shape
    # that makes the per-record checks vacuous: each handler calls .get() on the
    # element, raises AttributeError, escapes main(), and leaves stdout empty --
    # which the shell harness scores as a PASS. check_sps2.py already reports
    # this ("<key>[i] is not an object"); mirror it so the siblings agree.
    for i, item in enumerate(d.get(key)):
        if not isinstance(item, dict):
            e.append("%s[%d] is not an object" % (key, i))
            return False
```

`check_p3.py` was **not** touched by Phase 2; its +17/−1 predates this mission.

---

## 13. Regression-test evidence for every fix

### Fix 1 — negative control (defect present), positive control (defect fixed)

| Control | Command | Result |
|---|---|---|
| **Negative** — checker reverted to HEAD | revert `check_p2.py` only | `FAILED (failures=27)` |
| **Negative** — revert both | revert `check_p2.py` + `check_p3.py` | `FAILED (failures=29)` |
| **Negative** — revert p3 only | revert `check_p3.py` only | `FAILED (failures=2)` |
| **Positive** — fix present | worktree | `Ran 61` / **OK** |
| **Positive** — real documents unaffected | 4 real P2 documents | **0 B** before and after |

### Fix 2 — the repaired drift test genuinely detects drift

| Control | Result |
|---|---|
| correct `check_p2.py` | **OK** |
| injected drift (`"sources"` → `"source_records"`) | **FAILED (failures=1)** |
| `check_p2.py` fully reverted | **FAILED (failures=7)** |
| *before repair:* checker reverted | **OK** ← the tautology |
| *before repair:* drift injected | **OK** ← the tautology |

### Fix 1 — per-kind evidence

| kind | before | after |
|---|---|---|
| `sources` | 0 B | 31 B |
| `capability` | 0 B | 36 B |
| `interop` | 0 B | 31 B |
| `requirements` | 0 B | 36 B |
| `evidence` | 0 B | 31 B |
| `decision` | 0 B | 33 B |
| `handoff` | 0 B | 32 B |

### P3 provenance controls (not fixed, but controlled)

| Control | Result |
|---|---|
| requirements-only corrupt fixture, kind `requirements` | 31 B correct |
| same fixture, kind `bogus`/`reqs`/`""` | **0 B → vacuous PASS** |
| `{}` × 4 legitimate kinds | **0 B each → D5b confirmed** |
| 4 real P3 documents | 0 B clean (no false positives) |

The workstream recorded that its **first** D5 control was itself invalid — a fixture
corrupt for *all* kinds was masked by the handoffs fallback and reported OK on broken code.
Retained deliberately: any future control here **must** use a requirements-only fixture.

---

## 14. Negative-control results

Every negative control used a disposable clone under `/tmp`. The real worktree was never
mutated for a control.

| # | Control | Expected | Observed | Verdict |
|---|---|---|---|---|
| 1 | `check_p2.py` reverted, non-dict element | fail | `FAILED (failures=27)` | ✅ discriminates |
| 2 | `check_p3.py` reverted, registry payloads | fail | `FAILED (failures=2)` | ✅ discriminates |
| 3 | both reverted | fail | `FAILED (failures=29)` | ✅ |
| 4 | drift injected into `check_p2.py` mapping | fail | `FAILED (failures=1)` | ✅ discriminates |
| 5 | crashing checker under `2>/dev/null` | must not PASS | `''` → PASS | ❌ **defect reproduced (D4)** |
| 6 | nonexistent checker under `2>/dev/null` | must not PASS | `''` → PASS | ❌ **defect reproduced (D4)** |
| 7 | crashing checker under `2>&1` | fail | visible output → FAIL | ✅ correct |
| 8 | planted `{"decided_by":"Agent"}` vs D3 lookahead | must be flagged | lookahead never matches; valid-ERE variant **does** match | ❌ **defect reproduced (D3), root cause isolated** |
| 9 | crash/clean/missing checker vs `validate-p4.sh:120` | only clean+refuse should pass | **all three PASS** | ❌ **defect reproduced (NEW-p4)** |
| 10 | `check_p4.py` × 5 malformed + `{}` + not-JSON | must not PASS | rejected / genuine FAIL | ✅ fails safe |
| 11 | degenerate policy + agent-attributed approval | must be flagged | **0 B → clean** | ❌ **defect reproduced (F1)** |
| 12 | pristine `788bf8a` SEO isolation | pass | `Ran 20` / OK | ✅ |
| 13 | pristine + only the untracked gate | fail | `Ran 20` / `FAILED (3)` | ✅ isolates one file |
| 14 | `unittest discover` in a pristine clone | find tests | `Ran 0` / exit 0 | ❌ **defect reproduced** |
| 15 | same + three `__init__.py` | find tests | `Ran 543` / FAILED (3,1) | ✅ decisive proof |

**Controls 5, 6, 8, 9, 11, 14 are reproductions of confirmed defects. Controls 1–4, 12, 13,
15 discriminate correctly and prove the fixes and isolation claims are load-bearing.**

---

## 15. Test inventory and exact commands

All commands use `PYTHONDONTWRITEBYTECODE=1` and run **from the repository root**. `pytest`
is not installed and installing it is prohibited.

```bash
cd /Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main

# 1. attribution + checker contract (primary)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_attribution_policy

# 2. shell-validator policy contract
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_shell_validator_policy_contract

# 3. remaining sps2 modules
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_p5
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_p17_lifecycle
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_p17_pinning
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_p17_security
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_p17_endtoend
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest sps2.tests.test_p10_runtime_gate

# 4. domain modules (leaf-directory form; see discovery defect)
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest domain.seo.tests.test_isolation
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest domain.seo.tests.test_structured_data
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest domain.cms.tests.test_isolation
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest domain.frontend.tests.test_content_slots
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest domain.frontend.tests.test_layout_registry

# 5. what NOT to use
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s . -t .   # finds 0 tests, exits 0
```

`discover` cannot be mixed with dotted module names (exit 2). No Makefile and no
documented invocation exist; the only documented command anywhere is
`python3 sps2/tools/test-portability.py` in `sps2/README.md`.

---

## 16. Exact pass/fail/skip counts

### Current worktree (measured)

| scope | modules | ran | passed | failed | skipped |
|---|---|---|---|---|---|
| `sps2.tests.*` | 8 | 527 | 526 | 0 | 1 |
| `domain.*.tests.*` (incl. untracked frontend) | 21 | 355 | 352 | 3 | 0 |
| **total** | **29** | **882** | **878** | **3** | **1** |

### Pristine clone at `320d3a5` (authoritative for HEAD)

| modules | ran | passed | failed | skipped |
|---|---|---|---|---|
| 26 (3 modules are untracked-only) | 543 | 539 | 3 | 1 |

Lower because `domain.frontend.test_content_slots`,
`domain.frontend.test_layout_registry` and `sps2.tests.test_p10_runtime_gate` (331 tests)
are **untracked** and therefore absent from a clean checkout.

### Tests changed by Phase 2

`sps2.tests.test_attribution_policy`: **60 → 61** methods.
Cumulative vs committed HEAD: **53 → 61**.

### The 3 failures (identical in both scopes)

`domain.seo.tests.test_isolation` — `test_zero_orphan_references_across_repository`,
`test_live_status_reporting`, `test_live_rollback_rehearsal_success`. Single root cause
(§19). Pre-existing in the worktree, **absent in a clean checkout**.

---

## 17. Tests not run and reasons

| Not run | Reason | Classification |
|---|---|---|
| Any `.sh` validator end-to-end | Standing rule: prohibited; could mutate trackers/evidence | `[NOT RUN]` |
| `.sps/tools/validate-capability.sh`, `validate-control.sh`, `validate-governance.sh` (behavioral) | Protected scope; not executed | `[NOT RUN]` |
| GNU grep behavior on Linux | GNU grep absent; installs and network prohibited | `[NOT RUN]` |
| `sps2/tools/test-portability.py` | Reported RED (33 passed, 6 failed, 14 controls incl. a live `RESUME_COMPLETION_STATE_DRIFT`); excluded as mutation-sensitive | `[NOT RUN]` |
| `sps2/tools/test-history-credential-check.py` | Excluded by standing instruction | `[NOT RUN]` |
| `validate-p6.py` timeout root cause | Timed out on the *unmodified* good policy too → likely policy-independent | `[NOT RUN]` |
| Live remote state | No fetch permitted | `[BLOCKED]` |
| `p10_runtime_gate.py` inside a HEAD clone | File is untracked, absent from `320d3a5` | `[BLOCKED]` |
| `unittest discover` as a CI command | Finds 0 tests — explicitly **not** a success | `[NOT RUN]` |

**Total tests not run: 6 categories (not a test count).** No test was skipped to make
results look better; the single `skipped=1` is pre-existing in `test_p17_endtoend`.

---

## 18. Baseline comparison for every important failure

| Failure | At pristine `788bf8a` | At committed `320d3a5` | Real worktree | Classification |
|---|---|---|---|---|
| 3 × `domain.seo.tests.test_isolation` | **OK (20/20)** | **OK** | **FAILED (3)** | **Introduced by the untracked `p10_runtime_gate.py`.** Not inherited from history; a clean checkout is green. |
| 3 × `test_shell_validator_policy_contract` | pass | **FAILED (3/7)** | pass | **Committed-at-HEAD failure.** The test was committed without the fix it asserts; fixed only by uncommitted `.sps/tools` edits (clause C withheld). |
| `check_p2.py` non-dict element | false PASS | false PASS | **fixed** | Pre-existing; Phase 1 closed 2 of 3 shapes, Phase 2 closed the third. |
| `check_p3.py` unknown kind | **vacuous for ALL kinds** (`:198` path-as-kind) | vacuous for unknown kinds | same | Pre-existing, **narrowed** by `320d3a5`. |
| 3 × frontend / p10 test modules | **absent** | **absent** | present | Untracked-only; 331 tests invisible at HEAD. |

No failure was classified as a regression without this per-revision comparison.

---

## 19. P10 / P9 dependency findings

### 19.1 Dependency graph

| Layer | Components | Depends on |
|---|---|---|
| Attribution | `attribution.py`, `attribution_policy.json`, `AGENTISH` | nothing (import-time hard dependency on the policy file) |
| P10 runtime | `p10_runtime_gate.py` (untracked) | stdlib at module level; every `domain.*`/`sps2.*` import is **function-scope** |
| Frontend | `domain/frontend/` (untracked, 49 tests) | stdlib only |
| CMS fixtures | `domain/cms/data/` (untracked) | — |
| SEO isolation | `domain/seo/isolation.py` | AST scan of the whole repo |
| `.git`-dependent | `test_attribution_policy.py` (`BASELINE_REV`) | a real git repository |

### 19.2 The 4-configuration isolation matrix `[VERIFIED]`

| # | Configuration | `domain.seo.tests.test_isolation` |
|---|---|---|
| 1 | pristine `788bf8a` | `Ran 20` / **OK** |
| 2 | pristine `788bf8a` + **only** `p10_runtime_gate.py` | `Ran 20` / **FAILED (failures=3)** |
| 3 | committed `320d3a5` (gate absent) | `Ran 20` / **OK** |
| 4 | real worktree | `Ran 20` / **FAILED (failures=3)** |

Same three tests in (2) and (4). The green→red delta is **exactly one file**.

### 19.3 Root cause

`domain/seo/isolation.py:198` collects imports via `ast.walk` (`:80-104`), which visits
every `Import`/`ImportFrom` at **any** depth — inside `def` bodies, `if False:`,
`try/except`. It is AST-based but **location-insensitive**, so semantically it is a
textual scan. The sole repo-wide offender is the lazy, function-scope, fail-closed
`from domain.seo.audit import audit_directory` at `p10_runtime_gate.py:1917`.
`exclude_paths` is hardcoded at `:208-213` (`domain/seo`, `sps2/tools/seo_audit.py`,
`sps2/tools/rollback_seo.py`) and does not list the gate. The failure depends on the file
**existing on disk**, not on executing — the gate is wired into no validator and no CI.

### 19.4 Classification

- **Not pre-existing in the "already red" sense** — a clean checkout is green. The accurate
  statement: *introduced by the untracked P10 gate*, absent at both `788bf8a` and
  `320d3a5`.
- **Not caused by test invocation** — `Ran 20` in all four configurations, no collection
  errors.
- **Not caused by a missing dependency** — the *presence* of a file causes the failures.
- **Caused by a governance boundary** — the fix is blocked (19.5).

### 19.5 Why the fix is blocked

`sps2/decisions/P10-DECISIONS.json` `standing_bounds.P9` states verbatim: *"P9 is APPROVED
and CLOSED by D-P9-APPROVAL (commit 9a16a9e); P9 must not be modified by P10 work."*
`P10-DELEGATED-DECISIONS.json` leaves **5 of 10** decisions `PENDING_USER_APPROVAL`
(DEC-7101..7104, DEC-7110), and its envelope states it "does not authorize implementation,
inventory population, CMS records, a layout registry, a slice contract, THE RUNTIME GATE,
tests, or runtime activation."

### 19.6 Remediation options (proposal D)

| Option | Change | Touches P9? | Blocked? |
|---|---|---|---|
| A | Populate + wire `P9_ALLOWLIST_RELATIVE_PATHS` | **yes** | ❌ blocked — and the constant is **dead code** (read by no logic), so populating alone changes nothing |
| B | Make the scan reachability-aware | **yes** | ❌ blocked |
| **C** | **P10-side: resolve the audit import dynamically, or exclude the gate from its own scan, inside the untracked gate** | **no** | ⚠️ needs a decision because the gate is itself unauthorized, but **touches no P9 file** |

**Option C is the only path that does not violate `P10-DECISIONS.json`.**

### 19.7 Frontend / CMS

A clean clone at HEAD cannot run the P10 suite green: `domain/frontend/` is the sole
blocker (18 F + 1 E → `OK` when present). `domain/cms/data/` is irrelevant to red/green.

---

## 20. Attribution semantic-boundary findings

- **Token set `[VERIFIED]`**: 17 tokens; `attribution_policy.json:tokens[]` ≡
  `load_agent_tokens()` (identical ordered and as a set, no duplicates). `matching` =
  `regex_word_boundary_case_insensitive`, `case_sensitive: false`, `anchored: true`,
  `substring_matching: false`.
- **Matcher verified correct**: `agent`/`Agent`/`AGENT` MATCH; `gpt`/`GPT-4`/`gpt-4o`/
  `antigravity` MATCH; `agentic`, `said`, `train`, `Mai`, `Botany`, `user`, `self`,
  `script`, `autonomous` do **not** match. `openai` correctly does **not** match.
- **Boundary comment accurate**: `attribution.py:71-72` ("`\b` does not fire across `_` or a
  digit") confirmed on all 6 underscore/digit rows.
- **Policy path `[VERIFIED]`**: `realpath`-based, absolute, identical from 5 different
  working directories.
- **Malformed policy `[VERIFIED]` — PARTIAL**: 24 payloads fail **closed** correctly
  (missing/invalid JSON, `null`, `[]`, `42`, `"string"`, `true`, `{}`, `tokens:null|"x"|[]|5`,
  `[1,2]`, `[""]`, nested, `[7]`, `[null]`, `{"other":1}`, BOM). **7 fail OPEN** — see F1.

### 20.1 The hyphenated-name case — an APPROVED NON-GOAL, not a defect

`copilot` / `Copilot` / `CoPilot` / `GitHub Copilot` **MATCH**.
`co-pilot` / `Co-Pilot` / `CO-PILOT` / `co_pilot` do **NOT** match.

**Mechanism:** `-` is a non-word character, so `\b` fires on both sides and `co-pilot`
decomposes into two words, `co` and `pilot`, neither of which is a token. This is the
identical mechanism that makes `gpt-4` and `antigravity-cli` MATCH — it is a consistent
consequence of word-boundary anchoring, not an oversight.

**Governing authority that makes this correct:**
- DEC-0025 (APPROVED): "Matching semantics are otherwise unchanged … **no separator
  joining**".
- `ATTRIBUTION-POLICY-DECISIONS.json`: "No Unicode normalization, no separator stripping or
  **joining**…".
- `attribution_policy.json` `non_goals[3]`: *"This policy does NOT handle Unicode
  cross-script confusables, **interior separators** or invisible characters."*

Admitting `co-pilot` would require separator joining → a **new User decision**. The token
was **not** added. `C-co-pilot-decision-brief.md` is prepared for that decision; the
recommended default is **no change**.

**Practical impact today is zero `[VERIFIED]`**: an exhaustive walk of every `decided_by`
and `approved_by` across all repository JSON yields exactly **one** distinct value —
`User`.

### 20.2 Adversarial matrix (characterization only — nothing changed)

- **NO MATCH, and explicitly covered by `non_goals[3]`:** full-width `ＡＩ`/`ａｇｅｎｔ`,
  circled `ⒶⓈ`, combining marks inside tokens, soft hyphen `co-00AD-pilot`, ZWSP/ZWJ/word
  joiner inside tokens, Cyrillic/Greek homoglyphs, interior separators (`a-i`, `a.i`,
  `a/i`), `anti-gravity`.
- **MATCH (caught):** `agent`, `agent`+combining acute, BOM-prefixed `agent`, `Aİ` (U+0130
  — matches via `re.I` Unicode case-fold; a **safe-direction over-rejection**), `aı`
  (dotless), `ai-agent`, `ai\nagent`.
- **Conclusion:** every adversarial non-match falls inside a documented non-goal. No
  undocumented semantic gap was found that would require a decision to *leave alone*.
  `_`/digit coverage rests on "interior separators" **by extension** — flagged `[INFERRED]`.
- **`Aİ` (U+0130) is not literally covered** by `non_goals[3]` (which names confusables,
  separators and invisibles, not case-folding), but it is an *over*-rejection, so no gap
  exists. Recorded for completeness.

### 20.3 Divergent hardcoded lists

**5 at committed HEAD, 0 in the working tree** — all in `.sps/tools/*.sh`:

| file:line @HEAD | n | missing vs canonical 17 |
|---|---|---|
| `validate-capability.sh:52` | 11 | aider, antigravity, chatgpt, cline, gpt, windsurf |
| `validate-capability.sh:180` | 10 | + copilot |
| `validate-capability.sh:249` | 5 | 12 missing |
| `validate-control.sh:90` | 9 | aider, antigravity, chatgpt, cline, copilot, gemini, opencode, windsurf |
| `validate-governance.sh:172` | 9 | same 8 |

All 5 are already replaced by `ATTR.AGENTISH` in the **working tree** (all three files are
` M`). Behaviourally: at HEAD an `Antigravity` approval is **ACCEPTED** — the exact gap
DEC-0025 exists to close. This is why `test_shell_validator_policy_contract` is **RED at
HEAD and GREEN in the worktree**.

**Legitimate, different-purpose lists (do not "fix"):** `validate-p5.py:27` (`AGENT_NAMES`),
`test-portability.py:67` (`VENDORS`), `test_p5.py:354` (`AGENTS`) are 10-token
core-neutrality *substring* scans, documented in the policy's `out_of_scope_vocabularies`.
`check_p2.py:49` (`HARNESSES`) is a schema enum. Note the two files declare their lists
under **different variable names**, which a name-based scan misses.

### 20.4 Duplicate module loading — latent only

`sps2/` has no `__init__.py`, so `attribution` and `sps2.governance.attribution` are two
module objects and the policy is parsed twice per process. `A1 is A2` → **False**, but
`A1.AGENTISH is A2.AGENTISH` → **True** because `re` caches compiled patterns.
`POLICY_PATH` and tokens are identical → **no divergent behavior today**.

### 20.5 No mocks, no stale artifacts

Zero `mock`/`patch`/`MagicMock`/`monkeypatch` in `sps2/tests/` (only substring hits on
"dispatches"); the only `unittest.mock` use in the repository is unrelated `domain/cms` and
`domain/seo` tests. Tests assert **object identity**. Editing the policy changes results in
a fresh process even with a stale `.pyc` present; a deliberately poisoned `.pyc` could not
win because CPython validates mtime+size and recompiles.

---

## 21. CI and test-discovery findings

`.github/workflows/sps-ci.yml` (sha256[:16] `c5cac92159f27459`, 3 jobs, 12 steps) contains
**zero** Python test execution — `[VERIFIED]` by reading the file in full; a grep for
`python|unittest|pytest|validate-p|sps2` returns **0** matches.

### 21.1 The zero-test discovery defect `[VERIFIED — proven, not inferred]`

`python3 -m unittest discover -s . -t .` → `Ran 0 tests`, **exit code 0** (not 5). A CI job
wired this way would pass green with **zero coverage**.

Cause: `sps2/`, `sps2/tests/` and `domain/` lack `__init__.py`; the stdlib loader refuses to
recurse into a directory without one.

**Decisive proof:** in a disposable pristine clone,
`touch domain/__init__.py sps2/__init__.py sps2/tests/__init__.py` turns `Ran 0 tests`
into **`Ran 543 tests / FAILED (failures=3, skipped=1)`** — reproducing the pristine figure
exactly.

It is **not** a namespace-package failure: PEP 420 namespaces import fine. The layout bug
manufactures the invocation problem (`discover -s domain -t .` →
`ImportError: Start directory is not importable`). Leaf-directory discovery works
(`-s domain/cms/tests` → 86 OK).

**Classification: a zero-test discovery result is a FAILURE and must never be treated as
success merely because the command exited 0.**

### 21.2 CI is already RED at HEAD

In a pristine `320d3a5` clone, `sps2.tests.test_shell_validator_policy_contract` fails
**3/7** — one per `.sps/tools/validate-{capability,control,governance}.sh`. Those failures
are fixed **only** by the uncommitted worktree edits. A new blocking Python job therefore
fails on arrival: the test was committed without the fix it asserts. This is the CI-side
view of §20.3 and the direct consequence of clause C being withheld.

### 21.3 Other CI observations

- `smoke-sps.sh:73-77` acknowledges it "may need network for npx"; `install.sh` then fires
  ~25 live `npx skills add` calls → **nondeterministic**.
- `chmod +x scripts/*.sh` mutates the checkout.
- `version-sanity` and `powershell-syntax` are clean and deterministic.
- `lint-sps.sh` asserts prose in Markdown — the repository's own documented F-9 weakness.

### 21.4 Governance verdict on extending CI

A Python *test* job is additive and touches no existing job, step, trigger or script, so it
is not literally a "redesign". But `.sps/GOVERNANCE.md:180` lists "CI/CD redesign" as out of
scope for Phase 02, and `.sps/handoff/HANDOFF-CURRENT.md` Q5/Q6 explicitly reserve wiring
validators into `sps-ci.yml` as an **open User question**. Verdict: this moves toward
reserved surface and should be authorized by a User-scoped decision record, **not** slipped
in as an agent change. `A-CI-python-test-job.patch` is prepared and validated but **not
applied**.

---

## 22. Governance and authorization matrix

### 22.1 Instrument state

| Instrument | State | `decided_by` | Authorizes |
|---|---|---|---|
| DEC-0025 .. DEC-0028 | `ACTIVE` / `APPROVED` | `User`, `decided_at: 2026-10-15` | the ratified attribution policy |
| DEC-0029, DEC-0030 | `PROPOSED` / `PENDING_USER_APPROVAL` | absent | **nothing** |

DEC-0029/0030 are untracked and lack `decided_by`/`decided_at`/`basis`. They are treated as
authorization **nowhere** in this report. No proposed decision was marked approved; no
approver was fabricated or inferred.

### 22.2 Authorization matrix

| Item | Authorized? | Evidence | Agent action taken |
|---|---|---|---|
| `check_p2.py` element guard | **yes** | checker module; not protected, not governance; reproducible defect; no new decision needed | **applied (unstaged)** |
| Regression test in `test_attribution_policy.py` | **yes** | same scope | **applied (unstaged)** |
| `.sps/tools/validate-capability.sh` | **NO — clause C withheld** | no approved instrument authorizes it | untouched; proposal only |
| `.sps/tools/validate-control.sh` | **NO — clause C withheld** | same | untouched; proposal only |
| `.sps/tools/validate-governance.sh` | **NO — clause C withheld** | same | untouched; proposal D3 |
| `sps2/tools/validate-p2.sh` / `validate-sps2.sh` | **NO** — protected harness | P3/P4 legacy-protection boundary | untouched; proposal D4 |
| `sps2/tools/validate-p4.sh` | **NO** — protected harness | same | untouched; proposal E |
| `REQ-P3-08` / "legacy paths" | **NO — clause D withheld** | "legacy paths" defined in no approved artifact | untouched, not redefined |
| `sps2/governance/attribution.py`, `attribution_policy.json` | **NO** — governance-controlled | changes matching/failure semantics | untouched; proposal F |
| `domain/seo/**` (P9) | **NO** | `P10-DECISIONS.json`: "P9 must not be modified by P10 work" | untouched |
| P10 decisions/requirements | **NO** | 5 of 10 delegated decisions `PENDING_USER_APPROVAL` | untouched |
| CI workflow | **unclear → not applied** | `GOVERNANCE.md:180`; `HANDOFF-CURRENT.md` Q5/Q6 reserve it | proposal A only |
| `fetch-depth: 0` CI change | **unclear** | same surface | documented in proposal A |

### 22.3 `IMPLEMENTED ≠ VERIFIED ≠ APPROVED`

Every artifact of this mission sits at **IMPLEMENTED** (or **PROPOSED**). Nothing is
VERIFIED by the User and nothing is APPROVED.

---

## 23. Protected files left unchanged

All 13 baseline-protected files match their Phase-2 baseline hashes exactly — verified
after the mission edits, after the full test suite, and immediately before this report.

| # | Protected file | sha256[:16] | State |
|---|---|---|---|
| 1 | `.sps/tools/validate-capability.sh` | `5556b9c757c680be` | match |
| 2 | `.sps/tools/validate-control.sh` | `6e2eaeeae574d38c` | match |
| 3 | `.sps/tools/validate-governance.sh` | `ba57f7372708b9d3` | match (worktree) |
| 4 | `sps2/tools/validate-p2.sh` | `9018e0de53abe5a1` | match |
| 5 | `sps2/tools/validate-p3.sh` | `c6ca659a7c495c87` | match |
| 6 | `sps2/tools/validate-p4.sh` | `74af33ca7617494e` | match |
| 7 | `sps2/tools/validate-sps2.sh` | `91509870f3d02b87` | match |
| 8 | `sps2/governance/attribution.py` | `de2cc583341d993b` | match |
| 9 | `sps2/governance/attribution_policy.json` | `eb9f113360601059` | match |
| 10 | `sps2/requirements/P3-REQUIREMENTS.json` | `382d408e25be0802` | match |
| 11 | `sps2/requirements/P4-REQUIREMENTS.json` | `376f5e140e77f892` | match |
| 12 | `.sps/GOVERNANCE.md` | `da0b64afcb943c05` | match |
| 13 | `.github/workflows/sps-ci.yml` | `c5cac92159f27459` | match |

**13/13 unchanged. `protected_files_modified = []`.**

Nuance: the three `.sps/tools/validate-*.sh` match the **Phase-1 baseline** but differ from
their **committed blobs** — they carry the pre-existing, still-unauthorized edits.
`validate-p3.sh` and `validate-p4.sh` are tracked and unmodified.

---

## 24. Patch proposals created outside the repository

Directory: **`/tmp/sps2-phase2-proposals-1792112518-56363/`** (created new; no existing
directory was overwritten). **Nothing in this directory has been applied.**

| File | Type | Applies cleanly? | Authorization needed |
|---|---|---|---|
| `A-CI-python-test-job.patch` | patch | ✅ `git apply --check` OK | User (CI is reserved surface) |
| `B-check_p3-records-kind-and-absent-collection.md` | proposal + patch | patch applies to the live worktree | User (commit only) |
| `C-co-pilot-decision-brief.md` | decision brief | n/a | **new User decision** |
| `D3-validate-governance.patch` | patch | ✅ **OK (lead-regenerated)** | User (governed validator) |
| `D4-stderr-preservation.patch` | patch | ✅ OK | User (P3/P4 validator) |
| `E-validate-p4-negative-control-polarity.md` | proposal | n/a | User (governed validator) |
| `F-harden-load-agent-tokens.md` | proposal | n/a | **new decision record recommended** |

Supporting workstream artifacts (evidence, not deliverables):
`/tmp/w1p2/check_p3-records-unknown-kind.patch`, `/tmp/w1p2/test_p3_records_unknown_kind.py`,
`/tmp/w3p2/CI-python-test-job.patch`, and the six workstream reports.

**A defect was found in a workstream deliverable and corrected.** The original
`/tmp/w2p2/D3-validate-governance.patch` **failed** `git apply --check`
(`.sps/tools/validate-governance.sh:169 … patch does not apply`) because it was generated
against stale worktree context, and its hunk removed the worktree's existing markdown
control. It was **not** shipped; the lead regenerated the patch against committed HEAD and
verified it applies. This is exactly the class of error the "verify, don't trust" rule
exists to catch.

---

## 25. Release-readiness matrix

| # | Severity | Item | Status | Blocked on |
|---|---|---|---|---|
| 1 | **HIGH** | Commit `320d3a5` is RED — 3 failures in `test_shell_validator_policy_contract`; the three `.sps/tools` validators still hardcode divergent lists at HEAD | **OPEN** | **User authorization (clause C)** |
| 2 | **HIGH** | CI runs **zero** Python tests; the obvious `unittest discover` wiring finds **0 tests while exiting 0** | **OPEN** | User decision + `__init__.py` layout fix |
| 3 | **HIGH** | Untracked `p10_runtime_gate.py` breaks P9 isolation (3 failures) on every checkout while invisible to git | **OPEN** | User decision (Option C unblocked) |
| 4 | MEDIUM | `domain/frontend/` (49 tests) entirely untracked and therefore unenforced | OPEN | User decision |
| 5 | MEDIUM | `check_p3.py` unknown kind + absent-collection false PASS | Proposal B | User (commit) |
| 6 | MEDIUM | `load_agent_tokens()` semantic fail-open | Proposal F | **new decision record** |
| 7 | MEDIUM | `validate-p4.sh:120/:131` unsound negative controls | Proposal E | User (governed validator) |
| 8 | MEDIUM | `check_p2.py` non-dict list elements false PASS | **CLOSED** | — |
| 9 | MEDIUM | Tautological drift test | **CLOSED** | — |
| 10 | LOW | D3 lookahead; D4 stderr; CWD-relative test paths; one unguarded `os.environ["PATH"]` mutation | Proposals / documented | User for protected scope |
| 11 | LOW | `check_p4.py` robustness + exit-code deviation | documented | harness owner |

**Verdict: NOT release-ready.** Blockers 1–3 each independently prevent a green,
reproducible, trustworthy build, and all three require **User authority rather than agent
work**. Two of them (1 and 3) are the governance model working as designed — authority was
withheld, and the honest result is a red build that says so.

### 25.1 Residual false-PASS risk

| Shape | `check_sps2.py` | `check_p2.py` | `check_p3.py` |
|---|---|---|---|
| missing collection key | ERR ✅ | ERR ✅ | ERR ✅ |
| non-list collection value | ERR ✅ | ERR ✅ | ERR ✅ |
| non-dict list elements | ERR ✅ | **ERR ✅ (fixed)** | n/a |
| unknown kind | exit 2 ✅ | clean (no-op) | **silent → PASS ⚠️** |
| absent collection `{}` | — | ERR ✅ | **silent → PASS ⚠️** |
| degenerate policy tokens | **silent → PASS ⚠️** | **silent → PASS ⚠️** | **silent → PASS ⚠️** |

---

## 26. Known pre-existing failures

| Failure | Count | Present at `788bf8a`? | Present at `320d3a5`? | Cause | Owner |
|---|---|---|---|---|---|
| `domain.seo.tests.test_isolation` | 3 | **no** | **no** | untracked `p10_runtime_gate.py:1917` orphan import into a rolled-back subsystem | User decision (P10/P9) |
| `test_shell_validator_policy_contract` | 3 | no | **yes** | committed test asserts a fix that is not in the commit | User (clause C) |
| `test_p17_endtoend` skip | 1 | yes | yes | pre-existing conditional skip | — |

**A clean checkout at `320d3a5` shows exactly 3 failures (all
`test_shell_validator_policy_contract`) and 1 skip.** The worktree shows the same 3
failures replaced-identity — the SEO trio — because the untracked gate is present. **The
two failure sets are disjoint and both are 3.**

---

## 27. Remaining risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| A governance control reports clean while disabled (D3, F1, D5) | medium | **high** — silent loss of an approval control | Proposals D3/F/B; only the worktree D3/D4 control is sound today |
| CI added naively → false-green gate | high | high — no coverage while reporting success | `__init__.py` layout fix **before** wiring; use the explicit module list |
| Red HEAD ships as "green" | high | high — 3 known failures | Resolve clause C; the commit message already discloses them |
| Untracked gate breaks P9 on other checkouts | high | medium | commit-and-fix or remove; needs a decision |
| Unsound p4 negative controls mask a promotion regression | low | high | Proposal E |
| `check_p3` unknown kind from a future typo | low | medium | Proposal B patch |
| Duplicate module loading diverges later | low | low | latent only today |
| CWD-relative test paths break under a different runner CWD | medium | medium | fix `__file__`-relative paths (pattern exists at `test_p17_pinning.py:33`) |

### 27.1 Honest limits of this assessment

This mission **did not** execute any shell validator end-to-end, **did not** verify GNU grep
semantics under Linux, **did not** reach the network to confirm remote state, and **did
not** fix three of the four confirmed false-PASS instances. Two structural issues (CI
wiring, the P9/P10 conflict) are blocked on **User authority, not engineering**. The report
therefore claims a **reduced** false-PASS surface, not an eliminated one, and **PARTIAL**
status.

---

## 28. Exact User decisions required

| # | Decision | Options | Recommendation |
|---|---|---|---|
| **U1** | Authorize clause C — migrating the three `.sps/tools/validate-*.sh` to `ATTR.AGENTISH` | (a) authorize and commit; (b) leave withheld and accept a permanently red HEAD | **(a)** — this is the sole cause of blocker 1 |
| **U2** | CI Python test job | (a) authorize + fix `__init__.py` first; (b) non-blocking job; (c) no CI change | **(a)** — (b) would create a false-green gate |
| **U3** | `domain/frontend/` + `p10_runtime_gate.py` | (a) commit both; (b) remove both; (c) leave untracked | **(a) or (b)**, but not (c) — (c) keeps the build ambiguous |
| **U4** | P9/P10 boundary | (a) Option C (P10-side dynamic resolution); (b) reopen P9 | **(a)** — (b) violates `P10-DECISIONS.json` |
| **U5** | `co-pilot` token semantics | (a) keep as approved non-goal; (b) admit the token; (c) enable separator joining | **(a)** — (b)/(c) require changing DEC-0025 semantics |
| **U6** | Harden `load_agent_tokens()` (F1) | (a) new decision record + shape/duplicate validation; (b) accept the fail-open | **(a)** |
| **U7** | Proposal B (p3 unknown kind + absent collection) | (a) authorize + commit; (b) defer | **(a)** — a confirmed false PASS |
| **U8** | Proposal E (p4 negative-control polarity) | (a) authorize; (b) defer | **(a)** — security control currently cannot fail |
| **U9** | Proposal D4 (stderr preservation) | (a) authorize; (b) defer | **(a)** — closes 2 HIGH false-PASS sites |
| **U10** | Commit the two Phase-2 checker/test changes | (a) commit; (b) keep unstaged | User's call; the mission stages nothing |

**No decision above has been taken by the agent. No proposal is approved.**

---

## 29. Final Git preservation audit

| Check | Expected | Measured | Result |
|---|---|---|---|
| HEAD unchanged | `320d3a58…` | `320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71` | ✅ |
| Branch unchanged | `build/roadmap-p3-completion` | same | ✅ |
| Cached origin ref unchanged | `788bf8a289…` | `788bf8a2892ee72705276c9d846626ca0470400d` | ✅ |
| Commit created / amended | none | none | ✅ |
| Push / deploy | none | none | ✅ |
| Staged count | 0 | 0 | ✅ |
| Stash count | 0 | 0 | ✅ |
| Index sha256[:16] | `647138fe9ec717e5` | `647138fe9ec717e5` | ✅ |
| Porcelain entries | 23 | 23 | ✅ |
| Attribution commit unchanged | 13 files | 13 files, same manifest | ✅ |
| Three `.sps/tools` validators uncommitted | ` M` | ` M` | ✅ |
| No baseline path disappeared | 23 entries | none missing | ✅ |
| No user modification overwritten | all preserved | verified by hash + porcelain | ✅ |
| Protected hashes match | 13 | 13/13 | ✅ |
| Dependency installed | none | none | ✅ |
| Lockfile changed | no | no | ✅ |
| pycache / generated artifacts cleaned | no | 12 dirs / 76 `.pyc` intact | ✅ |
| Network used | no | no | ✅ |
| `.sh` validator executed end-to-end | no | no | ✅ |
| Previous report overwritten | no | `cb8c421721f4d54f` intact | ✅ |

### 29.1 Newly changed files (complete list)

1. `sps2/tools/check_p2.py` — +57/−0 cumulative (Phase 1 +48, **Phase 2 +9**)
2. `sps2/tests/test_attribution_policy.py` — +261/−2 cumulative (Phase 1 majority, **Phase 2: drift test replaced + 1 test added**)
3. `reports/SPS2-PHASE2-RELEASE-READINESS-20261016-072628.md` — new

`sps2/tools/check_p3.py` (+17/−1) was **not** modified by Phase 2; its diff predates this
mission.

### 29.2 New tests added by Phase 2

1. `TestCheckerDocumentShapesFailVisibly.test_non_object_list_elements_are_reported`
   — 7 kinds × 4 element types (`[1]`, `["x"]`, `[null]`, `[[1,2]]`)
2. `TestCheckerDocumentShapesFailVisibly.test_checker_document_guards_do_not_drift_between_siblings`
   — **repaired** (was a tautology; now genuinely falsifiable)

### 29.3 Every patch proposal

See §24 — seven artifacts under `/tmp/sps2-phase2-proposals-1792112518-56363/`.

---

## 30. Recommended next actions in priority order

1. **U1 — authorise clause C.** Single highest-value action: it turns HEAD green and
   unblocks blocker 1. Nothing else can fix it.
2. **Fix the test layout** (`__init__.py` for `sps2/`, `sps2/tests/`, `domain/`) **before**
   any CI wiring, so discovery cannot silently find zero tests.
3. **U2 — then authorise the CI Python job** (`A-CI-python-test-job.patch`) with
   `fetch-depth: 0` and an explicit module list, not `discover`.
4. **U3/U4 — decide the P10/P9 and untracked-frontend questions.** A clean checkout should
   be green; today the answer depends on which untracked files happen to exist.
5. **U7/U9 — authorise proposals B and D4**; both close confirmed HIGH false-PASS sites at
   low risk.
6. **U8 — authorise proposal E**; the p4 negative controls currently cannot fail.
7. **U6 — record a decision for proposal F**; a one-line data edit currently disables a
   governance control.
8. **U5 — decide the `co-pilot` question.** Recommended default: no change (approved
   non-goal).
9. **U10 — decide whether to commit the two Phase-2 checker/test changes.**

### 30.1 What the agent recommends against

- Do **not** wire CI before the `__init__.py` fix — it would create a false-green gate.
- Do **not** add an allowlist entry for the P10 import; `P9_ALLOWLIST_RELATIVE_PATHS` is
  dead code and the change would modify P9 in violation of `P10-DECISIONS.json`.
- Do **not** treat any proposal in §24 as authorization; none is approved.
- Do **not** commit the three `.sps/tools` validators on the strength of this report.
- Do **not** accept `co-pilot` by relaxing word boundaries; that changes DEC-0025 semantics.

---

## 31. Exact paths of all generated artifacts

### Report
- `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main/reports/SPS2-PHASE2-RELEASE-READINESS-20261016-072628.md`

### Proposals (outside the repository)
- `/tmp/sps2-phase2-proposals-1792112518-56363/A-CI-python-test-job.patch`
- `/tmp/sps2-phase2-proposals-1792112518-56363/B-check_p3-records-kind-and-absent-collection.md`
- `/tmp/sps2-phase2-proposals-1792112518-56363/C-co-pilot-decision-brief.md`
- `/tmp/sps2-phase2-proposals-1792112518-56363/D3-validate-governance.patch`
- `/tmp/sps2-phase2-proposals-1792112518-56363/D4-stderr-preservation.patch`
- `/tmp/sps2-phase2-proposals-1792112518-56363/E-validate-p4-negative-control-polarity.md`
- `/tmp/sps2-phase2-proposals-1792112518-56363/F-harden-load-agent-tokens.md`

### Workstream evidence
- `/tmp/w1p2/CHECKER-CONTRACTS.md`, `check_p3-records-unknown-kind.patch`, `test_p3_records_unknown_kind.py`
- `/tmp/w2p2/` (D3/D4 patches — **the D3 patch here is defective; use the lead's regenerated one**)
- `/tmp/w3p2/TEST-INFRA-CI.md`, `CI-python-test-job.patch`
- `/tmp/w4p2/ATTRIBUTION-BOUNDARIES.md`
- `/tmp/w5p2/P10-P9-DEPENDENCIES.md`, `P10-P9-options.md`, `P10-P9-remediation.patch`
- `/tmp/w6p2/INDEPENDENT-REVIEW.md`

### Baselines (read-only)
- `/tmp/sps2-phase2-baseline-1792112424/` (porcelain, untracked, commit manifest, protected hashes)
- `/tmp/sps2_mission_1792109921/` (Phase 1 baseline)
- `/tmp/sps2_mission_ws_artifacts/WS2-EXECUTION-CHAIN-AUDIT.md`

### Preserved user work (untouched)
- `/tmp/all_items.json`, `/tmp/edu_cands.json`, `/tmp/a2.html`, `/tmp/articles/`

---

## Machine-readable summary

```json
{
  "report_version": 1,
  "status": "PARTIAL",
  "repository": "/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main",
  "branch": "build/roadmap-p3-completion",
  "starting_head": "320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71",
  "final_head": "320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71",
  "commit_created": false,
  "pushed": false,
  "deployed": false,
  "staged_count": 0,
  "stash_count": 0,
  "tests_passed": 878,
  "tests_failed": 3,
  "tests_skipped": 1,
  "tests_not_run": 6,
  "authorized_fixes_applied": [
    "sps2/tools/check_p2.py: reject non-dict list elements in _check_collection (closes residual empty-stdout false PASS across all 7 kinds)",
    "sps2/tests/test_attribution_policy.py: repair tautological drift test; add test_non_object_list_elements_are_reported"
  ],
  "protected_files_modified": [],
  "patch_proposals": [
    "A-CI-python-test-job.patch",
    "B-check_p3-records-kind-and-absent-collection.md",
    "C-co-pilot-decision-brief.md",
    "D3-validate-governance.patch",
    "D4-stderr-preservation.patch",
    "E-validate-p4-negative-control-polarity.md",
    "F-harden-load-agent-tokens.md"
  ],
  "report_path": "reports/SPS2-PHASE2-RELEASE-READINESS-20261016-072628.md",
  "unresolved_user_decisions": [
    "U1 authorize clause C: migrate the three .sps/tools validators to ATTR.AGENTISH (sole cause of the red HEAD)",
    "U2 authorize a CI Python test job, after the __init__.py test-layout fix",
    "U3 commit or remove domain/frontend/ and sps2/tools/p10_runtime_gate.py",
    "U4 resolve the P9/P10 boundary (Option C = P10-side dynamic resolution, touches no P9 file)",
    "U5 decide co-pilot token semantics (recommended: keep as approved non-goal)",
    "U6 record a decision to harden load_agent_tokens() against semantic degradation",
    "U7 authorize proposal B (check_p3 unknown kind + absent collection false PASS)",
    "U8 authorize proposal E (validate-p4.sh negative-control polarity)",
    "U9 authorize proposal D4 (stderr preservation in validate-p2.sh / validate-sps2.sh)",
    "U10 decide whether to commit the two Phase-2 checker/test changes"
  ],
  "known_preexisting_failures": [
    "domain.seo.tests.test_isolation fails 3 tests in the worktree, caused by the untracked sps2/tools/p10_runtime_gate.py:1917 orphan import; absent in a clean checkout",
    "sps2.tests.test_shell_validator_policy_contract fails 3 of 7 at committed HEAD 320d3a5 because the three .sps/tools validator migrations are not in the commit",
    "sps2.tests.test_p17_endtoend skips 1 test conditionally"
  ],
  "critical_findings": [
    "False PASS confirmed and FIXED: check_p2.py accepted a present list of non-dict elements, emitting empty stdout which validate-p2.sh scores as PASS",
    "False PASS confirmed, proposal B: check_p3.py records falls through to the handoffs branch for an unknown kind and emits empty stdout, scored PASS by validate-p3.sh:103",
    "False PASS confirmed, proposal F: load_agent_tokens() validates type but not semantics; a well-typed degenerate tokens[] silently disables agent-attribution detection across three harnesses (60B detection -> 0B clean)",
    "False PASS confirmed, proposal D3: a PCRE lookahead inside grep -E in .sps/tools/validate-governance.sh:180 makes BSD grep return rc=2, which 2>/dev/null discards, after which a pass is printed",
    "False PASS confirmed, proposal D4: validate-p2.sh:34 and validate-sps2.sh:36 suppress stderr and score empty stdout as PASS, so a crashing or missing checker passes",
    "False PASS confirmed, proposal E: validate-p4.sh:120 and :131 invert the positive control's polarity, so a crashing, clean, or nonexistent checker all report a satisfied negative control",
    "CORRECTED from Phase 1: validate-p4.sh fails safe on malformed input (positive-marker scoring); the earlier false-PASS implication is retracted",
    "CORRECTED from Phase 1: the malformed-policy matrix wrongly marked three fail-open payloads as not false-PASS",
    "CORRECTED from Phase 1: 29 failures was both-reverted; isolated p3 revert is 2",
    "CORRECTED from Phase 1: test totals were 878/3/1 across 29 modules, not 828 across 27; domain/frontend/ (49 tests) is untracked",
    "CORRECTED from Phase 1: the drift-prevention test was a tautology; repaired and now genuinely fails under injected drift",
    "CI runs zero Python tests, and unittest discover finds 0 tests while exiting 0 - a false-green gate by construction",
    "3 of 13 protected files differ from their committed blobs but match the Phase-1 baseline: pre-existing, still-unauthorized edits, consequence of clause C being withheld",
    "A workstream-supplied D3 patch failed git apply --check and was discarded, not shipped; the lead regenerated it against committed HEAD"
  ],
  "false_pass_summary": {
    "confirmed": 6,
    "fixed_this_mission": 1,
    "proposed_only": 5,
    "class_eliminated": false
  },
  "not_verified": [
    "GNU grep behaviour on Ubuntu (grep absent; installs and network prohibited)",
    "end-to-end execution of any .sh validator (prohibited by standing rule)",
    "live remote state (no fetch permitted)",
    "validate-p6.py timeout root cause",
    "behavioural execution of the three .sps/tools validators",
    "p10_runtime_gate.py inside a HEAD clone (file is untracked)"
  ]
}
```
