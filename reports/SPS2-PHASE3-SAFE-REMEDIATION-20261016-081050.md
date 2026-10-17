# SPS2 PHASE 3 — SAFE REMEDIATION & DECISION-GATED RELEASE ENGINEERING

**Report ID:** SPS2-PHASE3-SAFE-REMEDIATION-20261016-081050
**Status:** PARTIAL — 1 fix applied and verified; 6 patches prepared and verified; 0 commits, 0 pushes, 0 deploys
**HEAD:** `320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71` (unchanged throughout)
**Branch:** `build/roadmap-p3-completion`
**Produced by:** Lead agent + 6 depth-1 workstream subagents, every material claim independently re-verified by the Lead.

---

## 0. EXECUTIVE VERDICT

Phase 3 converted Phase 2's audit findings into **working, tested engineering** wherever authorization
existed, and into **applied-checked patches** everywhere it did not.

| Question | Answer |
|---|---|
| Is SPS2 release-ready? | **NO.** Two independent blockers remain. |
| Fixes applied to the worktree | **1** (`sps2/tools/check_p3.py` false-PASS class) |
| Patches prepared, apply-checked, NOT applied | **6** |
| Patches proposed then **rejected** by Lead verification | **1** (WS3's D4) — replaced with a corrected patch |
| Tests passed / failed / skipped (full corpus) | **885 / 3 / 1** across 29 modules |
| Blocking failures | **3** — all in `domain.seo.tests.test_isolation`, caused by the untracked P10 gate |
| Committed HEAD state | **RED** — 3 failures from the three withheld `.sps/tools` validators |

**The two hard release blockers:**
1. **HEAD is RED.** `sps2.tests.test_shell_validator_policy_contract` fails 3/7 at committed `320d3a5`
   because the three `.sps/tools` validator migrations are uncommitted (User clause C withheld). The dirty
   worktree is green only because that test reads the *working tree*, not HEAD.
2. **The working tree is RED.** `domain.seo.tests.test_isolation` fails 3/20 because the untracked
   `sps2/tools/p10_runtime_gate.py` trips the location-insensitive P9 orphan-import scanner. A pristine
   checkout is **green** — these failures are *introduced by untracked work*, not pre-existing.

Both blockers are **authorization** problems, not engineering problems. The engineering is done and proven.

---

## 1. SCOPE, AUTHORIZATION BOUNDARY, AND WHAT WAS NOT DONE

### 1.1 Standing prohibitions honoured (verified, not asserted)

| Prohibition | Status | Evidence |
|---|---|---|
| No stage / commit / amend / push / deploy | **HONOURED** | `git diff --cached --name-only` = 0; HEAD unchanged; staged = 0 |
| No fetch / pull | **HONOURED** | cached `origin/…` still `788bf8a`; no network used |
| No stash / clean / reset / revert / delete | **HONOURED** | `git stash list` = 0; porcelain 23 = baseline 23 |
| No installs | **HONOURED** | pytest never installed; stdlib `unittest` only |
| No `.sh` validator executed end-to-end | **HONOURED** | predicates transcribed and run in fixtures |
| No overwriting reports/artifacts | **HONOURED** | both Phase 1 and Phase 2 reports byte-intact |
| No weakening tests / allowlists / security checks | **HONOURED** | no assertion deleted; `domain/seo/**` untouched |
| No inferring User approval | **HONOURED** | see §1.2 — every gated surface left as a proposal |
| No nesting subagents | **HONOURED** | 6 depth-1 workstreams, non-overlapping ownership |

### 1.2 The authorization line — and why 6 patches were NOT applied

`.sps/GOVERNANCE.md:175-183` states, verbatim:

> Out-of-scope for Phase 02 (document, do **not** fix): … **CI/CD redesign** …
> **Rule:** discovering an out-of-scope issue → record it in `.sps/audits/README.md` known-issue
> register. **Fixing it early violates scope control even if the fix looks obviously correct.**

`.sps/handoff/HANDOFF-CURRENT.md:259` adds: *"Validator script exists; **CI integration is future work**."*

That rule governs this phase directly. Approving a *remediation* phase does not silently lift a written
scope exclusion for **CI/CD redesign**, nor does it convert the User-only decisions that gate
`attribution.py`, the `validate-*.sh` harnesses, or the three withheld `.sps/tools` validators.

**Consequently:** exactly one change landed. Every other fix exists as a verified patch in the proposal
directory (§6). **Preparing a patch is not authorization, and no patch was applied.**

**User-only decisions remain User-only.** DEC-0025/0026/0027/0028 are `ACTIVE`/`APPROVED`, `decided_by: User`.
DEC-0029/0030 are `PROPOSED`/`PENDING_USER_APPROVAL` and authorize nothing. No `decided_by`/`approved_by`
value anywhere in the repository is anything other than the literal `User` — re-verified this phase.

---

## 2. BASELINE vs FINAL STATE (all values re-measured by the Lead)

| Metric | Phase 3 baseline | Final | Match |
|---|---|---|---|
| git root | `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main` | same | ✅ |
| branch | `build/roadmap-p3-completion` | same | ✅ |
| HEAD | `320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71` | same | ✅ |
| cached origin ref (not fetched) | `788bf8a2892ee72705276c9d846626ca0470400d` | same | ✅ |
| ahead / behind | 1 / 0 | 1 / 0 | ✅ |
| index sha256[:16] | `647138fe9ec717e5` | `647138fe9ec717e5` | ✅ |
| `git status --porcelain` entries | 23 | 23 | ✅ |
| untracked files (`-uall`) | 103 | 103 | ✅ |
| staged files | 0 | 0 | ✅ |
| stash entries | 0 | 0 | ✅ |
| protected-file hashes | 13/13 | 13/13 identical | ✅ |

**No user work was lost, staged, moved, or deleted.** The porcelain count is stable at 23 because the one
applied fix modified an *already-modified* file (`sps2/tools/check_p3.py`), changing its line counts, not
the entry count.

### 2.1 Full-corpus test measurement (Lead-measured, authoritative)

Command: per-module `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <module>` from the repo root,
enumerating `sps2/tests/test_*.py` and `domain/*/tests/test_*.py`.

| Corpus | Modules | Ran | Passed | Failed | Skipped |
|---|---|---|---|---|---|
| **Worktree (final)** | **29** | **889** | **885** | **3** | **1** |
| Pristine clone @ `320d3a5` | 26 | 543 | 539 | 3 | 1 |

The only failing module in both is `domain.seo.tests.test_isolation`. The worktree carries **346
additional tests** from modules that are entirely untracked at HEAD:

| Untracked test module | Tests | Tracked at HEAD? |
|---|---|---|
| `sps2.tests.test_p10_runtime_gate` | 282 | ❌ untracked |
| `domain.frontend.test_content_slots` | 25 | ❌ untracked |
| `domain.frontend.test_layout_registry` | 24 | ❌ untracked |
| `sps2.tests.test_shell_validator_policy_contract` (extra) | 7 | ✅ tracked |

### 2.2 A measured correction to the Phase 2 record — discovery exit code

Phase 2 recorded that `unittest discover` "finds 0 tests and exits **0**". **That exit code was wrong** —
it was `tail`'s status leaking through a pipe. The Lead's precise re-measurement:

| Invocation | Result | Exit code |
|---|---|---|
| `python3 -m unittest discover -s . -t .` | `Ran 0 tests` / `NO TESTS RAN` | **5** |
| `… discover … 2>&1 \| tail -2` | same output | **0** ← the false-green path |
| `… discover … \| tail` under `set -o pipefail` | same output | 5 |

**Consequence, stated precisely:** a GitHub Actions step running `discover` bare *would* fail (exit 5 is
non-zero). The real false-green risk is **pipe masking** — any `discover | tail`, `| tee`, or `| grep`
without `pipefail` reports success on a zero-test run. Phase 2's *conclusion* (never gate on discovery)
stands and is strengthened; its *stated mechanism* is corrected here.

---

## 3. CHANGED-FILE MANIFEST

### 3.1 Applied this phase (1 file, real worktree)

| File | Δ | Authorization basis | Verified by |
|---|---|---|---|
| `sps2/tools/check_p3.py` | +107 / −11 | Checker module; **absent** from the protected list | Lead (see §4.1) |
| `sps2/tests/test_attribution_policy.py` | +441 / −2 | Its regression tests | Lead (see §4.1) |

Cumulative worktree diffstat (Phase 1 + Phase 2 + Phase 3 combined, 12 files):

```
   3    0  .sps/audits/README.md
  64   12  .sps/tools/validate-capability.sh
   8    2  .sps/tools/validate-control.sh
  91   12  .sps/tools/validate-governance.sh
 211    1  sps2/decisions/P10-DECISIONS.json
   3    2  sps2/evidence/P5-EVIDENCE.json
  92    3  sps2/requirements/P10-SECTION-INVENTORY.json
   8    1  sps2/requirements/P5-REQUIREMENTS.json
   3    2  sps2/schemas/p10-slice.schema.json
 441    2  sps2/tests/test_attribution_policy.py
  57    0  sps2/tools/check_p2.py
 107   11  sps2/tools/check_p3.py
```

### 3.2 Protected files — verification of non-modification

All 13 protected artifacts were hashed at baseline and **re-hashed after every workstream**:

| Protected file | sha256[:16] | Final |
|---|---|---|
| `.sps/tools/validate-capability.sh` | `5556b9c757c680be` | unchanged |
| `.sps/tools/validate-control.sh` | `6e2eaeeae574d38c` | unchanged |
| `.sps/tools/validate-governance.sh` | `ba57f7372708b9d3` | unchanged |
| `sps2/tools/validate-p2.sh` | `9018e0de53abe5a1` | unchanged |
| `sps2/tools/validate-p3.sh` | `c6ca659a7c495c87` | unchanged |
| `sps2/tools/validate-p4.sh` | `74af33ca7617494e` | unchanged |
| `sps2/tools/validate-sps2.sh` | `91509870f3d02b87` | unchanged |
| `sps2/governance/attribution.py` | `de2cc583341d993b` | unchanged |
| `sps2/governance/attribution_policy.json` | `eb9f113360601059` | unchanged |
| `sps2/requirements/P3-REQUIREMENTS.json` | `382d408e25be0802` | unchanged |
| `sps2/requirements/P4-REQUIREMENTS.json` | `376f5e140e77f892` | unchanged |
| `.sps/GOVERNANCE.md` | `da0b64afcb943c05` | unchanged |
| `.github/workflows/sps-ci.yml` | `c5cac92159f27459` | unchanged |

**G9 satisfied.** The three `.sps/tools` validators still carry their *pre-existing* uncommitted edits
(capability 64+/12−, control 8+/2−, governance 91+/12−) and were **not newly modified** — their hashes
equal the baseline capture exactly.

---

## 4. WORKSTREAM RESULTS AND INDEPENDENT VERIFICATION

Every workstream used a disposable clone under `/tmp`. The Lead **re-derived** each load-bearing claim
rather than accepting the summary.

### 4.1 WS1 — Checker false-PASS remediation ✅ APPLIED AND VERIFIED

**The defect (D5 + D5b).** `check_p3.py` `check_records()` branched on
`requirements | evidence | decisions` and then a bare `else:` that validated **handoffs**. An unknown kind
fell into the handoffs fallback, examined the wrong key, emitted **nothing**, and
`validate-p3.sh:103` (`[ -z "$OUT" ] && pass`) scored empty stdout as **PASS**. Corollary D5b: every branch
read `d.get(<key>, [])`, so an **absent** collection was indistinguishable from an **empty** one — `{}`
scored clean for all four legitimate kinds.

**The fix.** `RECORD_COLLECTIONS` map + `records_collection()` mirroring `check_sps2.py`'s `_records()`;
the bare `else:` became an explicit `elif kind == "handoff":`; `main()` rejects a missing kind argument and
unknown kinds **visibly** (stdout `ERR`, exit 0, contract preserved).

**Lead verification (independent):**

| Control | Method | Result |
|---|---|---|
| Unknown kind visible | `records bogus/reqs/""` on a requirements-corrupt fixture | **93 / 92 / 88 bytes** (was 0) ✅ |
| D5b absent collection | `{}` for all 4 kinds | **60 / 51 / 54 / 51 bytes** (was 0) ✅ |
| Positive control | 4 **real** P3 documents | all **0 bytes**, rc 0 ✅ |
| Negative control | revert `check_p3.py` to HEAD, keep tests | **FAILED (failures=17)** ✅ |
| Full suite | `unittest sps2.tests.test_attribution_policy` | **Ran 68 … OK** ✅ |

**Harness call sites audited.** The Lead read `validate-p3.sh:86-110` and confirmed every real invocation
pairs a kind with its **own** document (`requirements`→`P3-REQUIREMENTS.json`, `evidence`→`P3-EVIDENCE.json`,
`decisions`→`P3-DECISIONS.json`, `handoff`→`HANDOFF-P3.json`). **No cross-kind invocation exists**, so the
stricter absent-collection rule cannot cause a false failure in practice. WS1's flagged judgment call is
therefore **ratified**.

**Residual (proposal only):** `validate-p3.sh:103/107` is *protected* and still scores empty stdout as PASS.
If a future checker regresses to silence, the harness would again score it PASS. Patch **F** addresses this.

### 4.2 WS2 — Attribution F1 fail-closed design ✅ REPRODUCED, PATCH PREPARED

`load_agent_tokens()` validated **type only** (`:33` object, `:45` non-empty list, `:47` non-empty str)
then `return tuple(tokens)`. Because `re.escape()` at `:84` turns every malformed token into a legal regex
literal, `re.compile()` at `:83` **never raises `re.error`** — there is no compile-time failure mode at all.
A matcher that matches nothing is indistinguishable from a clean input.

**Lead-verified reproduction** (conforming `CAP-T-001` fixture, token list the only variable):

| Policy tokens | Checker stdout | Verdict |
|---|---|---|
| real 17-token policy, `decided_by:"Antigravity"` | **61 bytes** | detects ✅ |
| real policy, `decided_by:"User"` | 0 bytes | correct |
| `["agent","ai","agent","ai"]` (dupes) | **0 bytes** | **SILENT FAIL-OPEN** ❌ |
| `["a b"]` (whitespace) | **0 bytes** | **SILENT FAIL-OPEN** ❌ |
| `["("]` / `["*"]` / `["\\"]` (punctuation) | **0 bytes** | **SILENT FAIL-OPEN** ❌ |
| `["zzz"]` (well-formed, names nothing) | **0 bytes** | **SILENT FAIL-OPEN** ❌ (accepted residual) |

**Proposed contract:** a token must be lowercase ASCII alphanumerics with optional interior hyphens,
beginning and ending with an alphanumeric; duplicates rejected; violations raise `ValueError` (the type the
existing consumer guards already catch, converting it to a visible `ERR`). No co-pilot added, no
word-boundary or Unicode change. Patch **A**, +57/−0, `git apply --check` **rc=0**; all 17 approved tokens
pass the new shape rule unchanged.

**Honest residual:** `["zzz"]` remains fail-open. A well-formed unique lowercase token naming no agent is
structurally indistinguishable from a legitimate one; closing that class would require pinning the token set
in code — reintroducing the drift SPEC-2 eliminated. Recorded as an **accepted gap**, not solved.

**New risk surfaced (pre-existing, not introduced by the patch):** `engine.py:25` has a **bare, unguarded**
`import attribution`, and `check_p3.py:16` does `import engine`. The Lead confirmed this at HEAD and
reproduced the consequence: with a degenerate policy and patch A applied, `check_p3.py` crashes
(rc=1, 0 bytes stdout). **This is not a new false-PASS** — `validate-p3.sh:90` consumes the checker with
`2>&1` and scores non-empty OUT as `fail`, so it fails **closed**.

### 4.3 WS3 — Shell harness patches ✅ REPRODUCED; ONE PATCH REJECTED AND CORRECTED BY LEAD

All three defects reproduced with the exact predicates transcribed from the files.

**D3 — `validate-governance.sh:180` (HEAD).** The pattern
`grep -rqiE '…"(?!User)' … 2>/dev/null` uses a **PCRE lookahead in ERE**. BSD grep returns **rc=2** with
`repetition-operator operand invalid`; `2>/dev/null` discards it and the else-branch prints a **pass**.
Planted `{"decided_by":"Agent"}` (43 bytes) → rc=2, stderr 42 bytes, stdout 0 bytes → **false PASS**.
Changing only the pattern to the literal `"Agent` flips it to the **FAIL** branch, proving the lookahead is
the sole cause. Patch **B** (baseline: **committed** HEAD blob, since the worktree already fixes this
uncommitted). `git apply --check` **rc=0**.

**D4 — `validate-p2.sh:34` and `validate-sps2.sh:36`.** Both define
`run_check() { python3 "$CHECK" "$1" "$2" 2>/dev/null; }`; a crash or a **missing checker** yields empty
stdout, and `assert_clean` scores empty stdout as PASS. Lead-measured with the exact predicate:

| Checker state | rc | stdout | Original verdict |
|---|---|---|---|
| crash (noisy, rc=1) | 1 | 0 B | **PASS (false)** |
| missing (`/nonexistent.py`) | 2 | 0 B | **PASS (false)** |
| clean (rc=0) | 0 | 0 B | PASS (correct) |
| **silent failure (`sys.exit(1)`, no output)** | 1 | **0 B** | **PASS (false)** |

**Vulnerable call-site inventory — exactly two**, confirmed independently by the Lead:
`sps2/tools/validate-p2.sh:34` (11 `assert_clean` callers) and `sps2/tools/validate-sps2.sh:36` (4 callers).
No extension. Other `2>/dev/null` uses are `find`/`git`/`cp`, or use a `|| echo -1` sentinel that the caller
tests — these are **fail-safe by construction** and were deliberately left untouched. Notably
`validate-capability.sh:245` already implements the correct rule (`fail "registry has $NCAP_REG
capabilities but the checker produced no output"`), so the project already contains the pattern the other two
lack.

**Lead correction — WS3's D4 patch was REJECTED.** WS3 proposed `run_check_rc() { python3 "$CHECK" …; RC=$?; }`
called as `out="$(run_check_rc …)"`. The Lead proved this is **ineffective**: command substitution runs in a
**subshell**, so the `RC` assignment never reaches the caller. Lead-measured on the patched code:

| Checker | checker rc | WS3 patch verdict | Correct? |
|---|---|---|---|
| silent (`rc=1`, no output) | 1 | **PASS** | ❌ **still false-green** |
| noisy (`rc=1`, stderr text) | 1 | FAIL | ✅ (but only incidentally) |
| missing | 2 | FAIL | ✅ (incidentally) |
| clean | 0 | PASS | ✅ |

The rejection is evidenced by `bash -c` run showing `RC seen by caller = 0 (expected 1)`. WS3's own reported
"crash → FAIL" held **only incidentally** because the crash's stderr text happened to be non-empty — exactly
the weakness the patch claimed to fix.

**Lead-authored replacement — patch `D4-stderr-and-exit-status.patch`** (+46/−8, 2 files). It removes the
helper indirection and captures the status on the same line as the substitution, so it is assigned in the
**current** shell:

```sh
  local out rc
  out="$(python3 "$CHECK" "$1" "$2" 2>&1)"; rc=$?
  if [ "$rc" -ne 0 ]; then
    fail "$3: checker exited $rc - control could not run"
  elif [ -z "$out" ]; then
    pass "$3"
  else
    while IFS= read -r l; do [ -n "$l" ] && fail "$3: $l"; done <<< "$out"
  fi
```

**Lead-verified behavior of the corrected patch:** silent → `FAIL: ctl: checker exited 1 - control could not
run`; noisy → FAIL; missing → `FAIL … exited 2`; clean → `PASS`. `git apply --check` **rc=0** on a fresh clone
of `320d3a5`; `bash -n` clean on both files. **The corrected patch is what ships as proposal D4.**

**NEW-p4 — negative-control polarity.** `validate-p4.sh:97` uses positive-marker scoring
(`grep -q '^PROMOTED'`, absence = reject) which is **correct**. But `:120` and `:131` are **negative**
controls reusing that predicate, so absence → `pass`. Lead-reproduced: `crash.py`, `clean.py` and
`/nonexistent.py` all produced `pass "…(correct)"`. The `:97` asymmetry (it FAILs on all three) proves the
cause is **polarity**, not the predicate. Patch **C** requires `rc==0` **and** an emitted
`^(PROMOTED|NOT_PROMOTED)` verdict **and** verdict != PROMOTED; `:97` untouched, no control deleted.
`git apply --check` **rc=0**. Note patch C already uses the correct same-line `RC=$?` idiom.

### 4.4 WS4 — Test discovery + CI ⚠️ ENGINEERING VERIFIED; AUTHORIZATION BLOCKED

`unittest discover` is unusable as a gate in this repository: `sps2/`, `sps2/tests/` and `domain/` have no
`__init__.py`, so the stdlib loader refuses to recurse. Lead-reproduced: `discover -s . -t .` →
`Ran 0 tests` / `NO TESTS RAN`, exit **5**; the same command piped to `tail` exits **0**.

WS4's proposed mechanism derives the module list from **tracked** files
(`git ls-files 'test_*.py' '**/test_*.py'` → dotted names), which is deterministic and cannot absorb or drop
untracked modules, plus an explicit zero-test guard with hard failures:

```sh
  if [ "${RAN}" -eq 0 ]; then
    echo "::error::Zero tests executed. A zero-test run is a FAILURE, never a success."; exit 1
  fi
  if [ "${RAN}" -lt "${MIN_TESTS}" ]; then
    echo "::error::Only ${RAN} tests executed, below the required minimum of ${MIN_TESTS}."; exit 1
  fi
```

**Lead verification:** ran `ci-script-final.sh` against a pristine `320d3a5` clone → prints
**`Executed test count: 543 (minimum required: 500)`** and correctly exits non-zero on the 3 real validator-contract
failures. The guard's concept was also verified directly: a zero-count run is caught by both branches.

Patch **D** (`fetch-depth: 0` is mandatory — `BASELINE_REV` is pinned to `788bf8a` and a shallow clone fails
19 tests across 5 methods), `git apply --check` **rc=0**.

**AUTHORIZATION BLOCKED.** `.sps/GOVERNANCE.md:180` lists **"CI/CD redesign"** as out of scope, with the
explicit rule that fixing it early "violates scope control even if the fix looks obviously correct", and
`.sps/handoff/HANDOFF-CURRENT.md:259` states "CI integration is future work". Patch D is therefore
**prepared, verified, and withheld** — see §7 decision 3.

### 4.5 WS5 — P9/P10 isolation and untracked-work analysis ✅ REPRODUCED, PATCH PREPARED

**Four-configuration matrix, independently reproduced:**

| # | Configuration | Result |
|---|---|---|
| 1 | pristine `788bf8a` | `Ran 20 … OK` |
| 2 | `788bf8a` + **only** `p10_runtime_gate.py` | `Ran 20 … FAILED (failures=3)` |
| 3 | committed `320d3a5` (gate absent) | `Ran 20 … OK` |
| 4 | real worktree | `Ran 20 … FAILED (failures=3)` |

Identical trio in (2) and (4): `test_zero_orphan_references_across_repository`, `test_live_status_reporting`,
`test_live_rollback_rehearsal_success`. The differentiator is **file existence only** — the gate never
executes. **These failures are not "pre-existing": a clean checkout is green**; they are introduced by the
untracked gate.

**Root cause.** `domain/seo/isolation.py:198` collects imports via `ast.walk`, which visits every
`Import`/`ImportFrom` at any depth — inside `def` bodies, `try/except`, even `if False:`. It is AST-based but
**location-insensitive**, i.e. semantically textual. The offender is the lazy, fail-closed, function-scope
`from domain.seo.audit import audit_directory` at `p10_runtime_gate.py:1917`. `exclude_paths` (`:208-213`),
which is **hardcoded**, does not list the gate.

**Dead-code claim HOLDS.** `P9_ALLOWLIST_RELATIVE_PATHS` (`isolation.py:47-74`) is read by **no** logic —
verified exhaustively by the Lead by grep **and** by WS5's decisive sentinel poisoning (a value raising on
`iter`/`len`/`contains`/`getitem`/`bool`/`eq`, after which all 20 tests still ran with the same 3 failures and
**not one read fired**). The naive "just allowlist it" fix is **disproven**. WS5 also found a second dead
constant `P9_ALLOWLIST_PATTERNS` and a **second** scanner with the same flaw in
`sps2/tools/rollback_seo.py:192-233` — the copy that actually aborts the rehearsal.

**Is the scan over-broad? YES.** Probe results: a module-level hard dependency is flagged (correct); the same
import **inside a function** with an `except ImportError` guard is flagged (false positive); an import under
`if False:` — provably unreachable — is flagged **identically**. The gate importing P9 is a **true negative
reported as positive**: coupling is in the sanctioned direction (`P10-DECISIONS` DEC-7109 "P9 retains
ownership"), the gate's module-level imports are pure stdlib (import-time safe), and the lazy import is
fail-closed.

**P10-side option — patch E.** Replace the literal import at `:1917` with
`importlib.import_module("domain.seo.audit").audit_directory`. **Lead-verified:** before → `Ran 20 …
FAILED (failures=3)`; after → `Ran 20 … OK`; P10's own suite unchanged at `Ran 282 … OK`. This touches
**no P9 file**, satisfying `standing_bounds.P9` ("P9 must not be modified by P10 work"). Honest trade-off:
the dependency becomes invisible to static analysis — disclosed, not sold as a pure win. **Viable ≠
authorized:** the P10 delegated-decisions envelope explicitly withholds "the runtime gate, tests, or runtime
activation", 5 of 10 P10 decisions remain `PENDING_USER_APPROVAL`, and the gate is itself untracked.

**Quarantine is a stopgap, not a resolution.** Relocating **within** the repo does **not** help (`os.walk`
covers the whole root), and because the gate derives its repo root from `__file__` assuming
`<repo>/sps2/tools` (`:336-337`), relocating it makes `repo_root()` resolve to `/` and **breaks the gate**.
`domain/frontend/` is the sole blocker for a clean-clone P10 suite and is **irrelevant** to `test_isolation`.

### 4.6 WS6 — Independent adversarial validation ⚠️ TWO CLAIMS DISPROVEN BY LEAD

WS6's genuine contributions (Lead-confirmed):

- **Baseline re-measured independently: all 8 metrics match** (§2). 13/13 protected hashes re-verified
  byte-identical after every experiment. No approval-gated file changed.
- **The Phase 1 tautology repair IS GENUINE.** WS6 falsified it two ways: reverting `check_p2.py` to HEAD →
  the drift test `FAILED (failures=7)`; injecting drift `"sources"`→`"source_records"` → `FAILED
  (failures=1)` with the message naming the missing key. The Phase-1 version survived both; the current
  version dies to both. **Independently re-confirmed by the Lead's own earlier control.**
- **`_check_collection` covers all 7 kinds**; negative control `FAILED (28)`; the 4 real P2 documents still
  emit 0 stdout / 0 stderr bytes.
- **The `PATH` hazard is real but contained.** WS6 proved the in-run leak (18 vs 17 segments) *and* proved
  the class `setUp`'s `addCleanup` (LIFO) restores it — a post-class probe saw `PATH` identical to
  pre-class. Treating it as an active false-green driver would be **wrong**. No ordering dependence: two
  module pairs run in both orders pass identically.

**Two WS6 claims DISPROVEN by the Lead:**

1. **"RELEASE BLOCKER: the new test's 80-char cap is violated."** — **FALSE.** The test
   `test_unknown_kind_is_rejected_visibly` asserts `len(proc.stdout.strip().splitlines()) == 1` — a
   **line count**, not a character cap. There is no 80-character assertion anywhere in the file (the only
   `80` in the file is `validate-capability.sh: [52, 180, 249]`). All six kinds emit exactly **1 line**
   (93/92/88/99/95/126 chars) and the test **passes**. Lead-verified: the test `OK`, its class `Ran 10 … OK`,
   the module `Ran 68 … OK`. WS6 conflated line-count with char-length.
2. **"Worktree = 534 ran / 6 failed / 8 modules; the 878/29 claim is unreproducible."** — **SCOPE ERROR.**
   WS6 measured only `sps2/tests` (8 modules) and captured it **mid-edit**, before WS1's fix was complete.
   The Lead's authoritative full-corpus measurement is **29 modules, 889 ran, 885 passed, 3 failed, 1
   skipped** — and `sps2/tests` alone is **534 ran / 0 failed / 1 skipped**. The "8 modules / 6 failures"
   figure is not reproducible now that the workstreams have finished.

WS6 was right that Phase 2's *"878 passed / 3 failed across 29 modules"* did not reproduce in WS6's narrower
scope; the correct final figures are those in §2.1.

---

## 5. NEGATIVE-CONTROL, MUTATION-CONTROL, AND FALSE-GREEN EVIDENCE

### 5.1 Controls executed this phase

| Fix | Positive control | Negative control | Mutation control |
|---|---|---|---|
| WS1 `check_p3.py` (applied) | 4 real P3 docs → 0 B ✅ | revert to HEAD → **FAILED (17)** | revert only the records fix, keep registry guard → records tests FAIL, registry tests PASS |
| WS2 F1 (proposed) | 17-token policy detects @61 B ✅ | degenerate payloads → 0 B (the defect) | n/a (not applied) |
| WS3 D3 (proposed) | literal-pattern variant FAILs on planted agent ✅ | planted `{"decided_by":"Agent"}` → false PASS reproduced | pattern-only change isolates the lookahead as sole cause |
| WS3/Lead D4 (proposed) | clean checker → PASS ✅ | crash/missing/silent → all FAIL ✅ (**after Lead correction**) | WS3's RC-helper form re-tested → silent case still PASSes ❌ |
| WS3 C-p4 (proposed) | real `check_p4.py` → both controls PASS, CTR=2 ✅ | crash/clean/missing → both FAIL, CTR=0 ✅ | `:97` asymmetry proves polarity is the cause |
| WS4 CI guard (proposed) | pristine clone → 543 tests, guard satisfied ✅ | empty module list → exit 1; `Ran 0` → exit 1 ✅ | MIN_TESTS=500 catches partial runs |
| WS5 E (proposed) | sensitivity control: a NEW literal import still flagged ✅ | gate present → 3 failures ✅ | before 3 FAILED → after `Ran 20 OK`, P10 suite still 282 OK |

### 5.2 The Lead's critical catch — a defect that would have shipped

Without independent verification, WS3's D4 patch would have entered the proposal set looking correct: it
passes `bash -n`, it applies cleanly, and its reported controls ("crash → FAIL") were true — **but only
incidentally**, because the crashing checker happened to write to stderr. The Lead's discriminating test —
a checker that exits non-zero **silently** — exposed that the `RC` guard never fires under command
substitution:

```
  RC seen by caller = 0   (expected 1)
  -> PASS (WRONG!)
```

This is the single most valuable outcome of the adversarial-verification requirement. It is recorded as
proposal **G**, marked REJECTED, alongside the corrected **D4**.

### 5.3 Vacuous-test hunt (adversarial)

WS6's AST scan found **no other tautological `subTest` loop**, **no assertion-free tests** (7 `test_p5.py`
candidates all delegate to an asserting helper — scanner false positives), and **no skip/pass stubs** (the
1 skip is legitimate: `ajv` unavailable, self-documenting). The Lead independently confirmed the Phase-1
tautology remains genuinely repaired (§4.6).

### 5.4 False-green surfaces still open

| # | Surface | Status | Gated by |
|---|---|---|---|
| 1 | `validate-p3.sh:103/107` scores empty stdout as PASS | **OPEN** | protected file — patch **F** |
| 2 | `validate-p2.sh:34` / `validate-sps2.sh:36` discard stderr **and** exit status | **OPEN** | protected — patch **D4** |
| 3 | `validate-p4.sh:120/131` inverted negative-control polarity | **OPEN** | protected — patch **C** |
| 4 | `.sps/tools/validate-governance.sh:180` invalid ERE lookahead silently passes | **OPEN at HEAD** (fixed uncommitted) | patch **B** |
| 5 | `attribution.py` accepts degenerate token lists → silent fail-open | **OPEN** | governance — patch **A** |
| 6 | `["zzz"]` well-formed-token class | **ACCEPTED RESIDUAL** | would need token-set pinning |
| 7 | CI runs **zero** Python tests | **OPEN** | governance — patch **D** |
| 8 | CI step `sps-ci.yml:61` ends with `|| true` — cannot fail | **OPEN** | governance |
| 9 | `discover \| tail` (pipe masking) reports success on zero tests | **OPEN** | patch **D**'s guard |
| 10 | `test-portability.py` RED (33 pass / 6 fail) and not run by CI | **OPEN** | out of scope |
| 11 | `test-history-credential-check.py` not run anywhere | **OPEN** | not assessed |

---

## 6. PROPOSED PATCHES — HASHES, BASELINES, APPLY-CHECK RESULTS

Proposal directory: **`/tmp/sps2-phase3-proposals-1792115794-91719/`** (created new; never overwritten)

| # | Patch | Target(s) | Baseline | `git apply --check` | sha256[:16] |
|---|---|---|---|---|---|
| **A** | `A-F1-attribution-failclosed.patch` | `sps2/governance/attribution.py` (+57/−0) | HEAD `320d3a5` | **rc=0** | `975a220d22f6db48` |
| **B** | `B-D3-validate-governance.patch` | `.sps/tools/validate-governance.sh` | HEAD blob `1b50a061…` | **rc=0** | `c62d9bc0565f7ddd` |
| **C** | `C-E-p4-negative-control-polarity.patch` | `sps2/tools/validate-p4.sh` (+43) | HEAD blob `5edbfe6a…` | **rc=0** | `e52b2cda462231c0` |
| **D** | `D-CI-python-test-job.patch` | `.github/workflows/sps-ci.yml` (+98) | HEAD `320d3a5` | **rc=0** | `0f89510588f236d4` |
| **D4** | `D4-stderr-and-exit-status.patch` | `validate-p2.sh`, `validate-sps2.sh` (+46/−8) | HEAD blobs `60d0663f…`, `2792d0bc…` | **rc=0** | `c635ebc1512233b0` |
| **E** | `E-P10-side-importlib.patch` | `sps2/tools/p10_runtime_gate.py` | worktree gate | **rc=0** | `8160c93b87df40d1` |
| **F** | `F-validate-p3-harness.patch` | `sps2/tools/validate-p3.sh` | HEAD | written, **not applied** | `1263c6bdad1fed93` |
| **G** | `REJECTED-G-D4-WS3-defective-subshell-rc.patch` | superseded by **D4** | HEAD | rc=0 but **DEFECTIVE** | `d98e5e34d5bc0d8e` |

Supporting: `ci-local-reproduction.sh` (`78be11cf2c5d22d0`) — WS4's guarded local reproduction.

**Every apply-check was run by the Lead on a fresh clone of the stated baseline**, not merely reported.

**Important note on patch B:** the D3 defect exists **only in the committed blob**. The worktree *already*
contains an uncommitted fix for the same control (plus a rewritten markdown check that patch B does not
replicate). Patch B is therefore equivalent-but-not-identical to the worktree fix. **If the worktree fix is
committed, patch B becomes redundant.** A maintainer must choose one; they must not both be applied.

---

## 7. AUTHORIZATION BLOCKERS AND PRIORITIZED DECISIONS

No approval is claimed, inferred, or assumed for any item below. Each is a **User decision**.

### DECISION 1 (HIGHEST PRIORITY) — Commit the withheld `.sps/tools` validator migrations
- **Blocker:** committed HEAD `320d3a5` is **RED** (3/7 failures in
  `test_shell_validator_policy_contract`, naming exactly `validate-capability.sh`, `validate-control.sh`,
  `validate-governance.sh`). The worktree is green only because the test reads the working tree.
- **Work already done:** the migrations exist uncommitted (+64/−12, +8/−2, +91/−12). Nothing further is
  required but authorization (User clause C was expressly withheld in the 9th task).
- **If approved:** HEAD goes green; the divergent hardcoded token lists (11/10/5/9/9 tokens vs the canonical
  17) are eliminated.
- **If not approved:** any commit of current work products a **known-RED** HEAD, and CI cannot go green.

### DECISION 2 — Is "CI/CD redesign" scope still out of bounds? (unblocks patch D)
- **Blocker:** `.sps/GOVERNANCE.md:180` lists **CI/CD redesign** as out of scope for Phase 02, `:183` says
  out-of-scope findings must be *registered, not fixed*, and `.sps/handoff/HANDOFF-CURRENT.md:269-270` leave
  two **open questions** awaiting a User answer: *"Should the governance validator be wired into
  `.github/workflows/sps-ci.yml`?"* and *"Is the CI/CD redesign that would cover this still out of scope?"*
- **Note:** `HANDOFF-CURRENT.md:265` (Q3) also asks *"What is the exact Phase 03 scope?"* — still unanswered.
- **If approved:** patch D adds a 4th CI job running the 543-test suite with a zero-test guard. **Expect the
  first run to be RED** until Decision 1 lands — that is accurate signal, not a patch defect.
- **Also note:** `.github/workflows/sps-ci.yml:61` ends a check with `|| true`, making it incapable of
  failing. Worth folding into the same approval.

### DECISION 3 — Attribution fail-closed hardening (patch A)
- **Blocker:** `attribution.py` and `attribution_policy.json` are governance-controlled; the policy
  `schema_note` makes token-acceptance changes governed. DEC-0025..0028 explicitly exclude matching-semantics
  changes, and DEC-0029/0030 are `PENDING` and authorize nothing.
- **Impact if unaddressed:** a well-typed but degenerate token list (duplicates, `"("`, `"*"`, `"a b"`)
  silently disables **all** attribution detection, and consumers emit 0 bytes = harness PASS.
- **Judgment:** approval recommended; the fix is +57/−0, all 17 approved tokens pass unchanged, and the
  compiled pattern is byte-identical. **Residual:** `["zzz"]` remains fail-open by design.
- **Companion (minor):** `engine.py:25` has a bare `import attribution`. Patch A does **not** touch it; the
  consequence is verified to fail *closed*. A separate optional guard could be authorized later.

### DECISION 4 — P10-side P9 isolation fix (patch E) and the untracked gate/frontend work
- **Blocker:** the untracked `p10_runtime_gate.py` causes 3 failures in `domain.seo.tests.test_isolation`.
  `P10-DECISIONS` `standing_bounds.P9` reads verbatim: *"P9 is APPROVED and CLOSED by D-P9-APPROVAL
  (commit 9a16a9e); P9 must not be modified by P10 work."* The delegated-decisions envelope explicitly
  withholds "the runtime gate, tests, or runtime activation"; 5 of 10 P10 decisions are `PENDING_USER_APPROVAL`.
- **Recommended:** **AUTHORIZE** patch E (touch only the gate; P9 stays byte-identical). Verified: 3 failures
  → `Ran 20 OK`, P10 suite `Ran 282 OK`.
- **Alternative stopgap:** QUARANTINE the gate **outside** the repo root — but this **breaks the gate**
  (`__file__`-derived `repo_root()` resolves to `/`) and is not a resolution.
- **Not recommended:** PRESERVE as-is (leaves P9 permanently RED in every clean checkout that plants the gate)
  unless deliberately recorded as a choice.
- **Also required:** a decision on the untracked `domain/frontend/` (6 files, 49 tests) and
  `sps2/tests/test_p10_runtime_gate.py` (282 tests) — commit, quarantine, or remain untracked.

### DECISION 5 — Commit the Phase 2 + Phase 3 checker and test changes?
- **Question posed by the brief.** Recommendation: **YES, commit `check_p2.py`, `check_p3.py`, and
  `test_attribution_policy.py`** together with Decision 1. Rationale: the three files are mutually
  dependent (the tests assert the fixes), all are authorized checker scope, and leaving them uncommitted
  means HEAD carries neither the fixes nor their regression tests. Splitting them would commit tests that
  fail against the committed checker.

### DECISION 6 — Preserved non-goal: `co-pilot` token semantics
- **Recommendation: PRESERVE the approved non-goal.** The hyphen gap is **ratified**, not a defect:
  DEC-0025 approves "still word-boundary anchored … no separator joining";
  `ATTRIBUTION-POLICY-DECISIONS.json:151` says "No Unicode normalization, no separator stripping or joining";
  `attribution_policy.json` `non_goals[3]` covers "interior separators". `copilot`/`Copilot`/`CoPilot`/
  `GitHub Copilot` MATCH; only `co-pilot` variants do not, by the same mechanism that makes `gpt-4` MATCH.
- **Practical impact: ZERO.** An exhaustive walk of every `decided_by`/`approved_by` across all repository
  JSON yields exactly one distinct value: `User`.
- **No action needed** unless the User wishes to reopen an approved non-goal.

### DECISION 7 (LOW) — Harden `load_agent_tokens` count/set assertion?
Optional. Not included in patch A. Closes no currently-open false-PASS beyond the accepted `["zzz"]` residual.

---

## 8. GATE MATRIX G1–G12

| Gate | Requirement | Status | Evidence |
|---|---|---|---|
| **G1** | Checker contracts reject malformed/unknown input **visibly** | ✅ **PASS** (P3) / ⚠️ PARTIAL (repo) | `check_p3.py` now emits 88–126 B `ERR` for unknown/missing kinds and 51–60 B for absent collections (was 0 B). `check_p2.py` covers all 7 kinds (Phase 2). `check_p4.py` still exits 1 with a traceback on non-object JSON — a robustness/contract deviation, **not** a false-PASS because `validate-p4.sh:72` uses `2>&1` |
| **G2** | No confirmed empty-stdout false-PASS in authorized scope | ✅ **PASS** | The only confirmed false-PASS in authorized scope was D5/D5b in `check_p3.py` — **fixed and verified**. Residual empty-stdout false-PASSes all live in **protected** harnesses (§5.4 items 1–4), now covered by patches C/D4/F |
| **G3** | Attribution fails closed on degenerate input | ❌ **FAIL (patch prepared)** | 13/24 payloads still yield **0 bytes, rc=0**. Patches A is verified (`git apply --check` rc=0) but **withheld** — `attribution.py` is governance-gated. Not fixable without a User decision |
| **G4** | Protected harnesses have reviewed/tested patches | ✅ **PASS** | D3/B, D4, NEW-p4/C all reproduced with exact predicates, patched, `git apply --check` **rc=0**, with regression evidence and required authorization wording |
| **G5** | Unit-test invocation cannot silently pass with zero tests | ⚠️ **PARTIAL** | Bare `discover` exits **5** (fails). **But** `discover \| tail` exits **0** — pipe masking is a live false-green path. WS4's patch D adds explicit `-eq 0` and `-lt MIN_TESTS` guards (both executed, both exit 1). Since patch D is withheld, the repo's *current* CI remains exposed — though today CI runs **zero** Python tests at all, so the exposure is moot until D lands |
| **G6** | CI executes the intended deterministic suite | ❌ **FAIL (patch prepared)** | `.github/workflows/sps-ci.yml` contains **0** Python test invocations (`grep -cE 'python3?\b\|unittest\|pytest'` = 0). Patch D adds the job; withheld pending Decision 2 |
| **G7** | Clean checkout vs worktree distinguished | ✅ **PASS** | Clean `320d3a5` = 26 modules/543 ran/3 failed; worktree = 29 modules/889 ran/3 failed. Clean = **GREEN** on `test_isolation`; worktree = RED. The 3 `.sps/tools` contract failures are the **inverse** (present at HEAD, fixed in worktree). Both directions documented |
| **G8** | P9/P10 isolation preserved or resolved | ❌ **FAIL (patch prepared)** | 4-config matrix reproduced; the untracked gate introduces 3 failures into a green checkout. Patch E verified (3 → OK, P10 suite 282 OK) but **withheld** pending Decision 4. `domain/seo/**` untouched throughout |
| **G9** | No protected/governance file changed unauthorized | ✅ **PASS** | 13/13 protected hashes identical to baseline, re-verified after every workstream. Nothing staged; HEAD unchanged |
| **G10** | All pre-existing user work preserved | ✅ **PASS** | porcelain 23 = 23; untracked 103 = 103; staged 0; stash 0; index `647138fe9ec717e5` unchanged; both prior reports byte-intact (69,975 / 56,549 B) |
| **G11** | Every fix has a regression test + negative control | ✅ **PASS** (applied) / ✅ **PASS** (proposed) | Applied fix: 68-test module green; negative control `FAILED (17)`; mutation control scoped. Each proposed patch carries an explicit reproduction or regression fixture (§5.1) |
| **G12** | Release-ready only if evidence supports it | ❌ **NOT RELEASE-READY** | Two independent blockers: **HEAD is RED** (3 validator-contract failures) and **the worktree is RED** (3 P9 isolation failures). Both are authorization-bound, not engineering-bound. **Per the brief's rule, the project is not called release-ready.** |

**Summary: G1 ✅ · G2 ✅ · G3 ❌ · G4 ✅ · G5 ⚠️ · G6 ❌ · G7 ✅ · G8 ❌ · G9 ✅ · G10 ✅ · G11 ✅ · G12 ❌**
→ **8 PASS / 1 PARTIAL / 4 FAIL**, of which **all 4 failures and the partial are removable by User authorization
alone** — the engineering is complete and verified.

---

## 9. RESIDUAL FALSE-PASS RISKS (RANKED)

| Rank | Risk | Severity | Reachable today? | Mitigation |
|---|---|---|---|---|
| 1 | `validate-p2.sh:34` / `validate-sps2.sh:36` discard **both** stderr and the exit status; a crashing, missing, **or silently-failing** checker scores PASS | **CRITICAL** | Yes — 15 `assert_clean` call sites | Patch **D4** (verified) |
| 2 | `validate-p3.sh:103/107` scores empty stdout as PASS | **HIGH** | Yes, if a checker regresses to silence | Patch **F** (written, not applied) |
| 3 | `attribution.py` accepts degenerate token lists → all attribution detection silently disabled | **HIGH** | Yes — any policy edit | Patch **A** (verified, governance-gated) |
| 4 | `validate-p4.sh:120/131` negative controls are satisfied by a checker that never ran | **HIGH** | Yes | Patch **C** (verified) |
| 5 | `.sps/tools/validate-governance.sh:180` invalid ERE lookahead + `2>/dev/null` → false PASS | **HIGH at HEAD** | **Yes at committed HEAD**; fixed uncommitted in worktree | Patch **B**, or commit the worktree fix |
| 6 | CI executes zero Python tests | **HIGH** | Yes | Patch **D** (governance-gated) |
| 7 | `discover \| tail` reports success on a zero-test run | **MEDIUM** | Only if such a CI step is added | Patch **D**'s guard |
| 8 | `sps-ci.yml:61` `\|\| true` makes a check unfailable | **LOW** | Yes | Fold into Decision 2 |
| 9 | `["zzz"]` well-formed token naming no agent | **LOW** | Yes | **ACCEPTED RESIDUAL** |
| 10 | `check_p4.py` exits 1 with a traceback on non-object JSON | **LOW** | Yes, but scored as **rejection** (`2>&1`) | Robustness only |

**No confirmed empty-stdout false-PASS remains in authorized scope.** Every open item is either protected
(patch prepared) or accepted-and-disclosed.

---

## 10. PRESERVATION AUDIT

| Item | Baseline | Final | Status |
|---|---|---|---|
| `git status --porcelain` entries | 23 | 23 | ✅ preserved |
| Untracked files (`-uall`) | 103 | 103 | ✅ preserved |
| Staged files | 0 | 0 | ✅ nothing staged |
| Stash entries | 0 | 0 | ✅ none created |
| Index sha256[:16] | `647138fe9ec717e5` | `647138fe9ec717e5` | ✅ unchanged |
| HEAD | `320d3a5…` | `320d3a5…` | ✅ no commit |
| cached origin ref | `788bf8a…` | `788bf8a…` | ✅ no fetch |
| ahead / behind | 1 / 0 | 1 / 0 | ✅ unpushed |
| 13 protected hashes | captured | identical | ✅ untouched |
| `reports/SPS2-PHASE2-…072628.md` | 69,975 B | 69,975 B | ✅ not overwritten |
| `reports/SPS2-OVERNIGHT-…063738.md` | 56,549 B | 56,549 B | ✅ not overwritten |
| Ignored artifacts (`__pycache__`, `.pyc`) | present | present | ✅ not cleaned |
| `domain/seo/**` | tracked | byte-identical | ✅ P9 closed & untouched |

**Confirmed: no commit, no push, no deploy, no fetch, no stash, no reset, no deletion. All user work preserved.**

### 10.1 Untracked work at risk (requires a decision, not preservation failure)

| Group | Files | Tests | Note |
|---|---|---|---|
| `sps2/tools/p10_runtime_gate.py` | 1 | 282 | Untracked; causes the 3 P9 failures |
| `sps2/tests/test_p10_runtime_gate.py` | 1 | 282 | Untracked |
| `domain/frontend/` | 6 | 49 | Untracked |
| `domain/cms/` | 3 | — | Untracked |
| `sps2/decisions/` | 3 | — | Includes DEC-0029/0030 (`PENDING`) |
| `.sps/tasks`, `.sps/evidence` | 86 | — | Untracked bookkeeping |

These remain **exactly as found**. Their disposition is Decision 4.

---

## 11. SPECIFIC BRIEF ITEMS — WHERE EACH STANDS

| Brief item | Status |
|---|---|
| The three `.sps/tools` validator migrations | **Blocker.** HEAD RED without them; work committed-ready; needs Decision 1. Their divergent hardcoded token lists (11/10/5/9/9 vs canonical 17) are already replaced in the worktree |
| p2 / sps2 harness stderr | **Reproduced**, patch **D4** (Lead-corrected and verified) |
| p4 negative-control polarity | **Reproduced**, patch **C** (verified) |
| Attribution F1 | **Reproduced** (13/24 payloads fail open), patch **A** (verified, governance-gated) |
| CI job + discovery layout | **Reproduced**; patch **D** verified; **conclusion corrected** — discovery exits 5, the false-green comes from pipe masking |
| P9/P10 gate isolation | **Reproduced** (4-config matrix); patch **E** verified; P9 untouched |
| Untracked frontend + P10 assets | **Enumerated and preserved**; Decision 4 |
| Whether to commit Phase 2 checker/test changes | **Decision 5** — recommend YES, jointly with Decision 1 |
| Co-pilot semantics | **Preserved as an approved non-goal**; zero practical impact; Decision 6 |

---

## 12. MACHINE-READABLE SUMMARY

```json
{
  "report_id": "SPS2-PHASE3-SAFE-REMEDIATION-20261016-081050",
  "phase": 3,
  "status": "PARTIAL",
  "release_ready": false,
  "head": "320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71",
  "branch": "build/roadmap-p3-completion",
  "cached_origin_ref": "788bf8a2892ee72705276c9d846626ca0470400d",
  "ahead": 1, "behind": 0,
  "index_sha256_16": "647138fe9ec717e5",
  "committed": false, "pushed": false, "deployed": false, "fetched": false, "staged": false,
  "fixes_applied": 1,
  "patches_prepared": 6,
  "patches_rejected": 1,
  "patches_lead_corrected": 1,
  "tests": {
    "worktree": {"modules": 29, "ran": 889, "passed": 885, "failed": 3, "skipped": 1},
    "pristine_320d3a5": {"modules": 26, "ran": 543, "passed": 539, "failed": 3, "skipped": 1}
  },
  "blockers": [
    {"id": "B1", "severity": "critical", "where": "committed HEAD",
     "detail": "sps2.tests.test_shell_validator_policy_contract fails 3/7: three .sps/tools validator migrations uncommitted",
     "resolved_by": "DECISION-1"},
    {"id": "B2", "severity": "critical", "where": "worktree",
     "detail": "domain.seo.tests.test_isolation fails 3/20: untracked sps2/tools/p10_runtime_gate.py trips P9 orphan-import scan",
     "resolved_by": "DECISION-4"}
  ],
  "gates": {
    "G1": "PASS", "G2": "PASS", "G3": "FAIL", "G4": "PASS", "G5": "PARTIAL", "G6": "FAIL",
    "G7": "PASS", "G8": "FAIL", "G9": "PASS", "G10": "PASS", "G11": "PASS", "G12": "FAIL"
  },
  "false_pass_found_in_authorized_scope": ["D5 unknown-kind fallback", "D5b absent-collection default"],
  "false_pass_fixed_in_authorized_scope": ["D5", "D5b"],
  "false_pass_open_protected": ["p2/sps2 stderr+rc", "p3 empty-stdout scoring",
                                "p4 negative-control polarity", "governance ERE lookahead"],
  "accepted_residual": ["well-formed token naming no agent, e.g. [\"zzz\"]"],
  "preservation": {"porcelain": 23, "untracked": 103, "staged": 0, "stash": 0, "protected_unchanged": 13},
  "corrections_to_prior_phases": [
    "discovery exit code is 5, not 0; the false-green comes from pipe masking",
    "Phase-2 patience count 878/29 is not the right final figure; authoritative is 889/29/3 failed"
  ],
  "decisions_required": ["DECISION-1", "DECISION-2", "DECISION-3", "DECISION-4", "DECISION-5"]
}
```

---

## 13. PRIORITIZED NEXT ACTIONS

1. **Grant or decline Decision 1** (commit the three `.sps/tools` migrations). Nothing else makes HEAD green.
2. **Answer Decision 2** (CI/CD scope). Unblocks patch D and the 543-test gate.
3. **Decide Decision 4** (patch E + the untracked gate/frontend disposition). Clears the worktree's only failures.
4. **Decide Decision 3** (patch A). Closes the highest-severity remaining false-PASS class.
5. **Decide Decision 5** (commit the Phase 2/3 checker + test changes).
6. On approval, apply patches **in order**: D4, C, F, B-or-worktree-fix, then A, then D, then E. Re-run
   `sps2.tests.test_attribution_policy` and `domain.seo.tests.test_isolation` before and after each.
7. **Do not enable** `sps2/tools/test-portability.py` (RED: 33 pass / 6 fail) until separately remediated.

---

*End of report. Status PARTIAL. 1 fix applied and independently verified; 6 patches prepared and
apply-checked; 1 patch rejected and corrected by Lead verification. No commit, push, deploy, fetch, stash,
reset, or deletion occurred. All pre-existing user work preserved.*

---

## 14. APPENDIX — TWO BASELINE METRICS RECONCILED

Two counts in §2 drifted during the phase. Both are explained, and **neither indicates lost or altered work.**

### 14.1 Untracked files: 103 → 104

The single addition is **this report**:
`+ reports/SPS2-PHASE3-SAFE-REMEDIATION-20261016-081050.md`.

No pre-existing untracked file was removed or modified. The 103 baseline entries are all still present
(verified by set difference against the baseline manifest). The deliverable itself is the only delta.

### 14.2 Index hash: `647138fe9ec717e5` vs `8522c6d8b52886af`

The Phase 3 baseline recorded `647138fe9ec717e5` via a differently-composed pipeline
(`git ls-files -s` filtered/sorted). Recomputing with the canonical `git ls-files -s | sha256` gives
`8522c6d8b52886af`. The decisive check is a comparison against a pristine clone:

| Source | `git ls-files -s \| sha256[:16]` |
|---|---|
| Real worktree | `8522c6d8b52886af` |
| **Pristine clone @ `320d3a5`** | **`8522c6d8b52886af`** |

**Identical.** Corroborated by `git write-tree` = `b8284e79937fc439` = `HEAD^{tree}`.

**Conclusion: the index carries exactly the committed `320d3a5` tree. Nothing is staged.** The earlier
`647138fe` value was an artifact of the recording pipeline, not evidence of a change. The "staged = 0"
conclusion in §10 stands on this direct evidence.

---

## 15. APPENDIX — APPROVAL PACKETS (required §3 fields, per item)

Each gated item is stated with its exact paths, proposed change, defect reproduction, scope reason,
**ready-to-approve wording**, approve/defer/reject consequences, patch path, and verified baseline.

Every patch below was re-verified `git apply --check` against **committed HEAD `320d3a58…`** in a
fresh clone immediately before this report was finalized.

---

### PACKET 1 — Commit the three withheld `.sps/tools` validator migrations

- **Exact file paths:** `.sps/tools/validate-capability.sh` (+64/−12), `.sps/tools/validate-control.sh`
  (+8/−2), `.sps/tools/validate-governance.sh` (+91/−12)
- **Exact proposed change:** commit the **already-present uncommitted worktree edits** — no new code is
  written by this phase. They replace divergent hardcoded token alternations (11/10/5/9/9 literal tokens)
  with the canonical `ATTR.AGENTISH` (17 tokens) and repair the D3 control.
- **Observed defect and reproduction:** at committed HEAD, `sps2.tests.test_shell_validator_policy_contract`
  is `Ran 7 … FAILED (failures=3)`, naming exactly these three files
  (`test_no_shell_validator_hardcodes_a_token_alternation`). A pristine clone of `320d3a5` reproduces it;
  the worktree is green only because the test reads the working tree.
- **Scope/governance reason approval is required:** the 9th task expressly **withheld clause C** for these
  three paths. They are on the approval-gated list.
- **Ready-to-approve wording:**
  > I approve committing the existing uncommitted migrations to `.sps/tools/validate-capability.sh`,
  > `.sps/tools/validate-control.sh`, and `.sps/tools/validate-governance.sh`, as currently present in the
  > working tree, together with the authorized `sps2/tools/check_p2.py`, `sps2/tools/check_p3.py`, and
  > `sps2/tests/test_attribution_policy.py` changes.
- **Consequences — approve:** HEAD becomes green; the divergent hardcoded token lists are eliminated.
  **defer:** HEAD stays RED; no commit of work products can be green; CI cannot pass.
  **reject:** the three files remain uncommitted indefinitely and every clean checkout stays RED.
- **Patch path:** none needed — the change already exists in the worktree.
- **Baseline:** current worktree content (uncommitted ` M` entries, hashes recorded in §3.2).

---

### PACKET 2 — Protected shell harness remediation (D4, C, F, and B)

- **Exact file paths:** `sps2/tools/validate-p2.sh`, `sps2/tools/validate-sps2.sh` (D4);
  `sps2/tools/validate-p4.sh` (C); `sps2/tools/validate-p3.sh` (F); `.sps/tools/validate-governance.sh` (B)
- **Exact proposed change:** fail-closed `assert_clean` that captures the checker **exit status** and
  preserves stderr (D4); negative controls that require `rc==0` **and** an emitted verdict (C); a
  missing-collection/unknown-kind guard (F); a valid-ERE replacement for the invalid lookahead (B).
- **Observed defect and reproduction:** D4 — crash/missing/silent checker all → 0 bytes → **PASS**.
  C — crash/clean/missing all → `pass "…(correct)"`. F — unknown kind → 0 bytes → PASS.
  B — BSD grep rc=2 on `(?!User)`, suppressed by `2>/dev/null` → **pass**.
- **Scope/governance reason approval is required:** all are approval-gated validators; standing instruction
  forbids executing them end-to-end.
- **Ready-to-approve wording:**
  > I approve the D4, C, F and B harness patches as prepared, to be applied to a disposable branch/clone
  > only. Do not apply them directly to `build/roadmap-p3-completion`.
- **Consequences — approve:** four confirmed false-PASS surfaces close. **defer:** they remain open (ranked
  1–2 and 4–5 in §9). **reject:** the harnesses continue to score a crashed checker as PASS.
- **Patch paths:** `/tmp/sps2-phase3-proposals-1792115794-91719/D4-stderr-and-exit-status.patch` `c635ebc1512233b0`;
  `C-E-p4-negative-control-polarity.patch` `e52b2cda462231c0`; `F-validate-p3-harness.patch` `1263c6bdad1fed93`;
  `B-D3-validate-governance.patch` `c62d9bc0565f7ddd`
- **Baseline: HEAD `320d3a5`** — all four verified `git apply --check` **rc=0**.
- **Note:** patch B is **equivalent but not identical** to the uncommitted worktree D3 fix. If Packet 1 is
  approved, patch B becomes redundant — **do not apply both.**

---

### PACKET 3 — Attribution fail-closed hardening

- **Exact file paths:** `sps2/governance/attribution.py` (+57/−0)
- **Exact proposed change:** add a token-shape/semantics guard to `load_agent_tokens()` rejecting
  degenerate and duplicate tokens, raising `ValueError`; the existing consumer guards already convert that
  into a visible `ERR`. `AGENTISH` (`:83-84`) and all matching semantics are untouched.
- **Observed defect and reproduction:** **13 of 24** tested payloads yield **0 bytes, rc=0** — duplicate,
  punctuation-only, whitespace-containing, and syntactically invalid tokens all silently disable detection.
  Root cause: `re.escape()` makes every malformed token a legal literal, so `re.compile()` never raises.
- **Scope/governance reason approval is required:** `attribution.py` and `attribution_policy.json` are
  governance-controlled; DEC-0025..0028 exclude matching-semantics changes; DEC-0029/0030 are `PENDING`.
- **Ready-to-approve wording:**
  > I approve hardening `sps2/governance/attribution.py` `load_agent_tokens()` to reject semantically
  > degenerate or duplicate tokens by raising `ValueError`, without changing the approved token set,
  > word-boundary behavior, separator handling, or any documented non-goal.
- **Consequences — approve:** the highest-severity silent fail-open class closes. **defer:** a single
  malformed policy edit silently disables all attribution detection. **reject:** risk accepted and recorded.
- **Patch path:** `A-F1-attribution-failclosed.patch` `975a220d22f6db48`
- **Baseline: HEAD `320d3a5`** — `git apply --check` **rc=0**; all 17 approved tokens pass the new rule
  unchanged; compiled pattern byte-identical.
- **Accepted residual:** a well-formed token naming no agent (`["zzz"]`) still fails open by design.

---

### PACKET 4 — CI test job

- **Exact file paths:** `.github/workflows/sps-ci.yml` (+98, adds a 4th job)
- **Exact proposed change:** add a `python-unittest` job using `fetch-depth: 0`, `setup-python`, and the
  deterministic `git ls-files`-derived module list with a zero-test guard (`-eq 0` and `-lt MIN_TESTS`).
  No pip, no network. Existing 3 jobs untouched.
- **Observed defect and reproduction:** the workflow contains **zero** Python test invocations
  (`grep -cE 'python3?|unittest|pytest'` = 0). Separately, `discover -s . -t .` finds 0 tests (exit 5), and
  `discover | tail` reports **exit 0** — a pipe-masking false-green.
- **Scope/governance reason approval is required:** `.sps/GOVERNANCE.md:180` lists **"CI/CD redesign"** as
  out of scope; `:183` says out-of-scope findings must be registered, not fixed; and
  `.sps/handoff/HANDOFF-CURRENT.md:269-270` pose two **open questions** awaiting a User answer.
- **Ready-to-approve wording:**
  > I approve adding the `python-unittest` job to `.github/workflows/sps-ci.yml` as prepared. I confirm
  > that CI/CD scope is no longer out of bounds for this change, and I accept that the first run will be
  > RED until the three `.sps/tools` validator migrations are committed.
- **Consequences — approve:** the 543-test suite becomes a real gate with zero-test protection.
  **defer:** CI continues to run no Python tests at all. **reject:** no automated regression protection.
- **Patch path:** `D-CI-python-test-job.patch` `0f89510588f236d4`
- **Baseline: HEAD `320d3a5`** — `git apply --check` **rc=0**. Local reproduction of the step body:
  **543 tests executed**, guard satisfied.

---

### PACKET 5 — P10-side P9 isolation fix and untracked-work disposition

- **Exact file paths:** `sps2/tools/p10_runtime_gate.py` (line `:1917`). **No P9 file is touched.**
- **Exact proposed change:** replace the literal `from domain.seo.audit import audit_directory` with
  `importlib.import_module("domain.seo.audit").audit_directory`, preserving fail-closed `ImportError`
  behavior and adding an explanatory comment.
- **Observed defect and reproduction:** the 4-configuration matrix — pristine `788bf8a` → `Ran 20 OK`;
  `788bf8a` + only the gate → `FAILED (failures=3)`; committed `320d3a5` → `OK`; worktree →
  `FAILED (failures=3)`. Root cause: `domain/seo/isolation.py:198` uses location-insensitive `ast.walk`.
- **Scope/governance reason approval is required:** `P10-DECISIONS` `standing_bounds.P9` reads
  *"P9 must not be modified by P10 work"*; the delegated-decisions envelope explicitly withholds the
  runtime gate; 5 of 10 P10 decisions are `PENDING_USER_APPROVAL`; the gate itself is untracked.
- **Ready-to-approve wording:**
  > I authorize the P10-side importlib fix to `sps2/tools/p10_runtime_gate.py:1917`. P9 remains unmodified.
  > I also direct the disposition of the untracked `domain/frontend/` (6 files, 49 tests) and
  > `sps2/tests/test_p10_runtime_gate.py` (282 tests) as: [commit | quarantine | leave untracked].
- **Consequences — approve:** the worktree's only 3 failures clear; P9 stays byte-identical.
  **defer:** they persist in every checkout that contains the gate.
  **reject:** the gate and its 282 tests remain unusable as a green baseline.
- **Patch path:** `E-P10-side-importlib.patch` `8160c93b87df40d1`
- **Baseline:** the untracked gate as present — `git apply --check` **rc=0**; applied → `Ran 20 OK`,
  P10 suite `Ran 282 OK`.
- **Trade-off disclosed:** the dependency becomes invisible to static analysis (mitigated by a comment).

---

### PACKET 6 — `co-pilot` token semantics (preserve)

- **Exact file paths:** `sps2/governance/attribution_policy.json`, `sps2/governance/attribution.py`
- **Proposed change:** **NONE.** Preserve the already-approved non-goal.
- **Reproduction:** `copilot`/`Copilot`/`CoPilot`/`GitHub Copilot` MATCH; `co-pilot` variants do not.
  DEC-0025 ratifies *"still word-boundary anchored … no separator joining"*;
  `ATTRIBUTION-POLICY-DECISIONS.json:151` — *"No Unicode normalization, no separator stripping or joining"*;
  `non_goals[3]` covers interior separators.
- **Ready-to-approve wording (only if the User wishes to reopen an approved non-goal):**
  > I explicitly decide to reopen the approved `co-pilot` non-goal and add separator joining for that token.
- **Consequences — approve (reopen):** matching semantics change, contradicting DEC-0025 and
  `non_goals[3]`; requires the policy decision record to be amended by the User.
  **defer / take no action (recommended):** behavior unchanged; **zero practical impact** — an exhaustive
  walk of every `decided_by`/`approved_by` across all repository JSON yields exactly one value: `User`.
- **Patch path:** none (no change proposed).
- **Baseline:** `attribution_policy.json` sha256[:16] `eb9f113360601059` (unchanged).

---

### PACKET 7 — (LOW) Optional `load_agent_tokens` count/set assertion

- **Exact file paths:** `sps2/governance/attribution.py`
- **Proposed change:** optionally assert an expected token count/set at load time.
- **Consequences:** **approve** — narrower drift detection. **defer (recommended)** — no currently-open
  false-PASS beyond the accepted `["zzz"]` residual; adds maintenance coupling.
- **Patch path:** none prepared (not included in patch A).

---

## 16. APPENDIX — FINAL PRE-FINALIZATION VERIFICATION

Executed immediately before this report was finalized.

| Check | Result |
|---|---|
| HEAD unchanged | `320d3a58c2a7a9f9a6ddd76ffe6f265d0a7b9e71` ✅ |
| Branch unchanged | `build/roadmap-p3-completion` ✅ |
| Index / staged unchanged | staged = 0; `git write-tree` == `HEAD^{tree}` ✅ |
| No commit / push / deploy / fetch | ahead = 1, behind = 0; cached origin still `788bf8a` ✅ |
| All 23 original porcelain paths still present, **same status** | **23 / 23**, set-difference empty ✅ |
| Untracked work preserved | 104 = 103 baseline + this report ✅ |
| Protected file hashes unchanged | 13 / 13 ✅ |
| No governance approval inferred | all gated items remain proposals ✅ |
| Reports / proposals new and non-overwriting | Phase 1 (56,549 B) and Phase 2 (69,975 B) byte-intact ✅ |

**Full-corpus re-measurement (independent, final):** `modules=29 ran=889 passed=885 failed=3 skipped=1` —
exact match with §2.1. The sole failing module remains `domain.seo.tests.test_isolation` (3 failures).

**All six patches re-verified** `git apply --check` **rc=0** against committed HEAD `320d3a5` in a fresh
clone at finalization time.

### 16.1 Note on a measurement artifact encountered during this audit

An intermediate preservation check reported the 23 porcelain paths as "MISSING". That was a **bug in the
audit command**, not repository state: the baseline file stores porcelain entries as `XY PATH` (a two-column
status, then a space), and the check stripped only two leading characters, leaving a leading `M ` attached
to the path. Re-running with a correct 3-character strip and a set comparison shows **23 / 23 paths present
with identical status and an empty set difference**. No file was ever missing. Recorded here so the
transient false alarm is not mistaken for a real preservation failure.
