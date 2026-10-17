# SPS2 ROUND 21A IMPLEMENTATION — UPDATER AND P17 SECURITY PATCHES

Report time: 2026-10-16T19:37:14+06:00 (suffix 20261016-193714)
Authorization: User message "USER AUTHORIZATION — ROUND 21A SECURITY
IMPLEMENTATION" (Scope A: update checker; Scope B: P17 secret scrubber).
Basis: `reports/SPS2-ROUND21A-UPDATER-P17-PATCH-PREPARATION-20261016-191745.md`.

**Files changed: exactly the five authorized.** Nothing staged, committed,
pushed, deployed, or published. HEAD unchanged (`c49f385`).

---

## 1. Pre-edit worktree reinspection (boundary 1)

At 19:19+06, before any edit: HEAD `c49f385`, 33 porcelain, 0 staged,
0 stashes — identical to the Round 21A report's end state. All five target
hashes matched the report's fingerprints byte-for-byte:

| File | Pre-edit SHA-256 (first 16) |
|---|---|
| `scripts/check-update.sh` | `37af1927220ce0b4` |
| `scripts/check-update.ps1` | `020e551de553efdf` |
| `sps2/p17/scrub.py` | `153a9515d2ce6239` |
| `sps2/tests/test_updater_safety.py` | `d51c20dd98dda505` (untouched all round) |
| `sps2/tests/test_p17_security.py` | `9e1f1ebabb560c96` |

No concurrent work observed; no reconciliation needed.

## 2. Scope A — what changed

### `scripts/check-update.sh` (3 edits, +23 lines)
- **`is_valid_version()`** (new, after `installed_version`): strict
  `^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$` grep for remote VERSION.
  (The plan's draft `case` guard `*[!0-9.\-]*` was dropped during testing —
  it rejected prerelease letters and defeated the regex.)
- **CHECKED_AT validation** (cached path): rejects non-`^[0-9]{1,12}$`
  values and values more than one TTL in the future; corrupt state →
  warning on stderr, cache ignored, fresh check runs. `now` is computed
  before the validation (an ordering bug caught in testing).
- **Remote VERSION validation** (fresh path, before any comparison):
  malformed → stderr warning, `STATUS=offline`/`LATEST=unknown` persisted,
  exit 2. A malformed remote can therefore no longer produce "up to date"
  (the old `is_greater` arithmetic-error fall-through) nor be persisted as
  a hostile `LATEST` value.

### `scripts/check-update.ps1` (3 edits, mirroring semantics)
- **`Test-VersionFormat`** function with the same regex.
- **CHECKED_AT**: explicit `^[0-9]{1,12}$` regex gate *before* the
  `[int64]` cast (the `SilentlyContinue` preference would otherwise turn a
  failed cast into a silent `$null`), plus a `$last -le ($now + $ttlSeconds)`
  future bound on the freshness test.
- **Malformed remote VERSION** → offline state + exit 2, before the
  `$installed -eq $latest` comparison.

Preserved by construction and pinned by tests: offline handling, `--force`
bypass, cached hits, equal/newer/dev-build comparisons, prerelease
acceptance.

### `sps2/tests/test_check_update_safety.py` (new, 19 tests, all green)
Behavioral bash tests (temp HOME, stub curl, 15 s timeouts) + static PS
tests. **Network safety**: the default fixture is a *dead* curl stub — a
test only gets a working stub when it explicitly passes `curl_payload`, so
no test can ever reach the real network. The `network="absent"` case uses
a symlink-whitelisted PATH (every tool except curl) with bash invoked by
absolute path. No test touches the real `~/.sps`.

Test list: future CHECKED_AT cannot freeze the cache; corrupt CHECKED_AT
ignored; negative CHECKED_AT ignored; fresh healthy cache honored (cached
exit 0); fresh update-available cache exits 1; `--force` bypasses a frozen
cache; malformed remote → offline, never up-to-date, hostile value not
persisted; garbage remote → offline; `v`-prefixed rejected; two-component
rejected; equal → up-to-date (state pinned); newer → update available;
local-ahead → up to date; prerelease accepted; missing state + dead
network → offline; no curl at all → offline; curl failure never evidence
of up-to-date; two PS static guards (validation order pinned textually).

## 3. Scope B — what changed

### `sps2/p17/scrub.py` (3 edits, patterns only — no logic change)
- **provider-token extended**: `ASIA[0-9A-Z]{16}` (AWS session tokens),
  `xapp-1-[A-Za-z0-9\-]{10,}` (Slack app tokens),
  `glpat-[A-Za-z0-9_\-]{16,}` (GitLab PATs).
- **private-key-block relaxed**: `-----BEGIN[A-Z ]*PRIVATE[ ]?KEY-----`
  (interior space optional) — catches the no-space `BEGINRSAPRIVATEKEY`
  evasion while still requiring the full BEGIN/END pair (pinned by a
  negative test).
- **base64-credential (new)**: `\b(?:cGFzc3dvcmQ6|dXNlcjo|YXV0aDo)
  [A-Za-z0-9+/=]{4,}` — the base64 of `password:` / `user:` / `auth:`
  prefixes only. (Two drafting errors were caught by probing before
  commit-quality: fabricated encodings, and a padding-`=` that is
  alignment-dependent — the stable prefixes are the unpadded `dXNlcjo` /
  `YXV0aDo`.) Explicitly NOT a general base64 matcher; docstring states
  the hedge's exact coverage.

`scrub()`/`scrub_obj()`/`assert_clean`/`SecretLeak`, MINIMAL_ENV, the
execution gate, and GATE-P17-4 are untouched.

### `sps2/tests/test_p17_security.py` (3 tests added; 62 → 65, all green)
- `test_scrub_covers_round21_evasion_shapes` — 7 positives (ASIA, xapp,
  glpat, no-space PEM, three base64 prefixes) each asserting the expected
  class and `[REDACTED]`.
- `test_scrub_negative_controls_are_not_over_redacted` — 11 near-misses
  that must survive untouched (short ASIA/AKIA, `glpat-` alone, short
  glpat/xapp, colon-less base64, prefix-alone base64, bare
  `BEGIN CERTIFICATE`, short Bearer, 64-hex digest).
- `test_space_free_pem_block_still_requires_full_block` — BEGIN without
  END must not match.
- The pre-existing `test_digests_are_not_mistaken_for_secrets` control is
  retained and green.

## 4. Verification results

| Check | Command | Result |
|---|---|---|
| New updater tests | `python3 -B -m unittest sps2.tests.test_check_update_safety` | **Ran 19 tests, OK** |
| Existing updater safety | `python3 -B -m unittest sps2.tests.test_updater_safety` | **Ran 13 tests, OK (skipped=1)** — pwsh absent, environmental, unchanged |
| P17 security (incl. new tests) | `python3 -B -m unittest sps2.tests.test_p17_security` | **Ran 65 tests, OK** |
| P17 lifecycle | `sps2.tests.test_p17_lifecycle` | **Ran 44 tests, OK** |
| P17 pinning | `sps2.tests.test_p17_pinning` | **Ran 25 tests, OK** |
| P17 end-to-end | `sps2.tests.test_p17_endtoend` | **Ran 2 tests, OK (skipped=1)** |
| P17 gate attribution | `sps2.tests.test_p17_execution_gate_attribution` | **Ran 5 tests, OK** |
| Core validator | `bash sps2/tools/validate-sps2.sh` | **78 passed, 1 failed** — the 1 is the pre-existing `legacy modified: get-sps.ps1` (T-06, unrelated to this round; baseline identical to Round 20B). The validator dynamically picked up the P17 suite's new 65-test count and still passes it |
| Real P10 gate | `python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json` | **exit 1, overall FAIL — 9 PASS / 5 FAIL / 2 BLOCKED**, same 5 unresolved_semantics — the genuine unmet prerequisites (publication defer, null approval, no gate_record, missing backend manifest, approval-mechanism option A). **Unchanged and honest; nothing weakened or fabricated** |
| Bash syntax | `bash -n scripts/check-update.sh` | OK |

Total this round: 19 + 13 + 65 + 44 + 25 + 2 + 5 = **173 tests, 0
failures, 2 environmental skips** (both pwsh-absent).

## 5. Changed-file hashes (post-implementation)

| File | Post-edit SHA-256 (first 16) | Status |
|---|---|---|
| `scripts/check-update.sh` | `f175ed77f54cea9d` | modified (authorized) |
| `scripts/check-update.ps1` | `ca00fcea56b182d7` | modified (authorized) |
| `sps2/p17/scrub.py` | `8567049f7d861b7d` | modified (authorized) |
| `sps2/tests/test_p17_security.py` | `f3b37405382af8fa` | modified (authorized) |
| `sps2/tests/test_check_update_safety.py` | `5c02e0035ae4c54f` | **new** (authorized) |
| `sps2/tests/test_updater_safety.py` | `d51c20dd98dda505` | **untouched** |

## 6. Out-of-boundary findings (reported separately, per boundary 4 and the stop rule)

1. **Mirror divergence (needs a follow-up decision).**
   `skills/sps/scripts/check-update.sh` and `.ps1` are byte-identical
   mirrors of the `scripts/` copies at HEAD and follow the repo's
   mirror convention (the ratified updater files all carry mirrors, and
   `test_updater_safety.py` asserts mirror behavior). The authorization
   names only `scripts/check-update.sh`/`.ps1`, so **the mirrors were
   left untouched and are now one patch behind**. Options: (a) authorize
   mirroring the same three edits into the two `skills/sps/scripts/`
   copies (2-minute change, restores byte-parity), or (b) decide the
   mirrors are deprecated for these files. Until then the two copies of
   each checker behave differently — the mirror copy retains the T-01
   freeze/malformed-version defects.
2. **Inline-fallback risk (unchanged from the patch plan, boundary 4).**
   `scripts/sps-update.sh:51-66` (and its mirror) contains an inline
   fallback checker with the same unvalidated-VERSION / unvalidated-
   CHECKED_AT weaknesses. It is a DEC-7201-ratified file and was not
   touched. Note the practical exposure is low: the fallback only runs
   when `check-update.sh` is absent, and every current install path
   ships it — but a hostile *state file* written via the fallback path
   could still freeze *its* 24h cache. Requires its own authorization.
3. **PS behavioral coverage still open** — `pwsh` remains absent, so the
   PowerShell patch is verified statically (order-of-validation pinned by
   the two static tests) and by the pre-existing skipUnless pattern. Run
   the suite on a pwsh host when available.
4. **CI manifest (deferred, not done).** The new test module is untracked;
   CI's `git ls-files`-derived list will not see it until a commit is
   authorized, at which point `.github/expected-test-modules.txt` needs
   one added line. That is a CI-adjacent edit and remains unauthorized
   (DEC-7203 stands).

## 7. Side-effect verification

- Git: HEAD `c49f385` unchanged; **0 staged; 0 stashes**; porcelain 38
  (was 33) — the delta is exactly this round's authorized work: 4 modified
  files + 1 new test module (the report lives under the already-untracked
  `reports/` directory, so it adds no porcelain entry). Every other
  pre-existing modification and untracked file is preserved untouched.
- The live `~/.sps` state was **not accessed** during implementation
  (boundary 5) — all test fixtures are TemporaryDirectory-based.
- No CI file, test manifest, installer, uninstaller, governance contract,
  approval record, CMS content, publication state, `sps-update.sh`, or
  `update-sps.ps1` was modified.
- No staging, committing, pushing, deploying, or publishing occurred.
- The P10 gate's failure state is unchanged and remains blocked by its
  genuine prerequisites; no approval or evidence was fabricated.

---

*Round 21A implementation complete: both authorized scopes implemented,
173 tests green, governance at its pre-existing baseline, real gate still
honestly FAIL. Four follow-up items (mirror syncing, inline fallback,
pwsh coverage, CI manifest line) are reported above and await separate
decisions. Stopping — commit, push, CI, publication, and final approval
remain unauthorized.*
