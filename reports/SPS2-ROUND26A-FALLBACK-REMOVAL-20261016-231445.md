# SPS2 ROUND 26A IMPLEMENTATION — INLINE UPDATER FALLBACK REMOVAL

Report time: 2026-10-16T23:14:45+06:00 (suffix 20261016-231445)
Authorization: User message "USER AUTHORIZATION — ROUND 26A INLINE UPDATER
FALLBACK REMOVAL" — the two updater scripts + regression tests in
`sps2/tests/test_updater_safety.py`.
Basis: Round 25A audit
(`reports/SPS2-ROUND25A-INLINE-UPDATER-AUDIT-20261016-223509.md`,
findings F-1/F-5, remediation §4).

**Files changed: exactly the three authorized** (2 updater scripts +
1 test module). Nothing staged, committed, pushed, deployed, or published.
HEAD unchanged (`c49f385`).

---

## 1. Pre-edit recheck (authorization item 4)

At 23:05+06: branch `build/roadmap-p3-completion`, HEAD `c49f385`, **40
porcelain / 0 staged / 0 stashes** — identical to the Round 25A end state.
No concurrent agent activity observed. Target hashes pre-edit:

| File | SHA-256 (first 16) | State |
|---|---|---|
| `scripts/sps-update.sh` | `ba90bfbfe6f57fd6` | pre-existing DEC-7201 modification, fallback intact (Round 25A audit subject) |
| `skills/sps/scripts/sps-update.sh` | `ba90bfbfe6f57fd6` | byte-identical mirror |
| `sps2/tests/test_updater_safety.py` | `d51c20dd98dda505` | unchanged since Round 18 |

## 2. What changed

### `scripts/sps-update.sh` — `checker()` rewritten (:41-58, net −11 lines)

The inline remote fetch (`raw` URL, curl, unvalidated `latest`, string
equality, "update available" message) is **deleted**. The function now:
1. Prefers `$ROOT/scripts/check-update.sh`, then
   `$REPO_DIR/scripts/check-update.sh` (unchanged logic) — the hardened,
   Round 21A-validated checker runs when found.
2. Otherwise **fails closed**: one stderr line
   (`check-update.sh not found; cannot check (installed: …)`), `return 2`.
   **No network request is possible from this path** — there is no curl
   invocation, no URL, no fetch of any kind left in the file.

The installed-version echo in the fail-closed message reads only the
local manifest (machine-local, installer-written) and is informational.
All other updater behavior — dirty-worktree refusal, `--check`, prompt,
force, clone/pull, reinstall — is untouched.

Two drafting errors were caught by `bash -n` + read-back before any test
ran: a missing closing quote in the candidate assignment (introduced and
fixed within the same edit sequence) and were never present in a tested
state.

### `skills/sps/scripts/sps-update.sh`

Exact byte copy of the patched source (`cp` + `diff` → identical).

### `sps2/tests/test_updater_safety.py` — new `InlineFallbackRemovalTests` class (3 tests)

1. **`test_no_inline_remote_version_fetch_remains`** — neither updater
   script contains `raw.githubusercontent.com` or `curl` (any occurrence;
   stricter than the mission's minimum).
2. **`test_missing_hardened_checker_fails_closed_with_exit_2`** —
   behavioral: isolated root with *no* `check-update.sh` at either
   candidate path, dead curl stub on PATH, `--check` → **exit 2**,
   "check-update.sh not found" on stderr, no "update available"/"up to
   date" anywhere in output.
3. **`test_missing_checker_path_makes_no_network_request`** — same
   fixture, but the curl stub writes a marker file if invoked; the test
   asserts the marker does not exist → **proof no network request was
   even attempted** from the fallback path.

Mirror byte-parity was already pinned by the pre-existing
`test_updater_mirrors_are_byte_identical`, which now covers the patched
pair automatically (green).

## 3. Test results (authorization items 3, 5, 6)

| Suite | Result |
|---|---|
| `sps2.tests.test_updater_safety` | **Ran 16 tests, OK (skipped=1)** — 13 pre-existing (unchanged, still green) + 3 new; the 1 skip is the pre-existing pwsh-absent environmental skip |
| `sps2.tests.test_check_update_safety` | **Ran 19 tests, OK** — proves the preferred checker path is unaffected |
| `bash sps2/tools/validate-sps2.sh` | **78 passed, 1 failed** — identical pre-existing baseline (`legacy modified: get-sps.ps1`, T-06, unrelated) |
| Real P10 gate | **exit 1, overall FAIL — 9 PASS / 5 FAIL / 2 BLOCKED** — unchanged honest baseline; no approval/publication state touched |
| `bash -n` both updater scripts | OK |

No test was weakened or skipped beyond the pre-existing environmental
skip; no unrelated behavior changed.

## 4. Mirror parity (authorization item 5)

`diff scripts/sps-update.sh skills/sps/scripts/sps-update.sh` → **clean**
(byte-identical, hash `4148b530881a5ae0` on both). The parity invariant is
also enforced going forward by `test_updater_mirrors_are_byte_identical`.

## 5. Exact diff summary

`git diff --stat` for the three files: `sps-update.sh` 69 lines changed
each mirror (84 insertions / 54 deletions across the pair vs HEAD — this
includes the pre-existing DEC-7201 modification relative to HEAD, not
just this round's edit); `test_updater_safety.py` modified (+85 lines,
the new test class). Post-edit hashes:

| File | Post-edit SHA-256 (first 16) |
|---|---|
| `scripts/sps-update.sh` | `4148b530881a5ae0` |
| `skills/sps/scripts/sps-update.sh` | `4148b530881a5ae0` |
| `sps2/tests/test_updater_safety.py` | `e33af7dcafec0302` |

## 6. Limitations

- **PowerShell behavioral coverage** remains unavailable (`pwsh` absent).
  Not a gap introduced here: `update-sps.ps1` never had an inline
  fallback (it returned 2 when `check-update.ps1` was missing — already
  fail-closed), and it was not in scope.
- The behavioral tests copy `BASH_UPDATER` into an isolated root rather
  than executing it in place, so `ROOT` resolves to the isolated tree and
  both checker candidates genuinely miss. This is the same temp-fixture
  pattern the module already uses; it does not exercise the in-repo path
  directly, but the in-repo path is what the 19 check-update tests cover
  from the checker side.

## 7. Final worktree state (authorization items 7, 8)

- HEAD `c49f385` unchanged; **0 staged; 0 stashes**; porcelain **40** —
  same entry count as pre-edit (the edits are inside already-modified
  tracked files; no new paths).
- No CI file, manifest, installer, uninstaller, governance decision,
  schema, evidence, CMS content, or publication state touched. The P10
  gate's failure state is unchanged and remains blocked by its genuine
  prerequisites.
- Nothing staged, committed, pushed, deployed, published, or approved.
- All pre-existing modifications and untracked files preserved; no
  concurrent agent work was overwritten.

---

*Round 26A complete: the last unvalidated remote-VERSION fetch site is
gone. Repo-wide, remote VERSION is now fetched in exactly two places —
the two byte-identical hardened `check-update.sh` copies — plus the
hardened PowerShell checker. The update trust chain has a single,
validated, fail-closed code path per platform. Tests: 16 updater-safety
(13+3 new) + 19 check-update, all green; validator and P10 gate at their
pre-existing baselines. Stopping — commit, push, CI, publication, and
final approval remain unauthorized.*
