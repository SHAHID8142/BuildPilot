# SPS2 In-Depth QA Pass — Rounds 2–4 (installer, governance, CI+docs)

**Date:** 2026-10-18
**Scope:** User mandate — "run very indepth QA check every line of the cods and everything one by one."
**Method:** 5 read-only review agents on disjoint file groups (skill-docs, installers, scripts, governance, CI+docs); every finding re-verified by the build manager before fixing; second-opinion probes run live where claims were behavioral.

---

## Round 1 — skill-docs reviewer (committed in ed946d0)

All 6 findings fixed: LESSONS.md §3 send-flow truth (full-content preview, typed
yes, pre-push secret scan, fresh clone, dated branch), T-33 promotion-flow
disentangle, USER-GUIDE secret-scan mention + safety-model wording.

## Round 2 — installer reviewer (committed in f1009bf)

23 findings (5 MAJOR + 8 MINOR + 10 NIT). Fixed in this round:

| # | Severity | Finding | Fix |
|---|---|---|---|
| 22 | MAJOR | `"${ARR[@]:-}"` on empty arrays passes one stray empty arg to `npx` (install.sh step/extras_step sites, uninstall.sh plugin remove) | plain `"${ARR[@]}"` (expands to nothing; verified bash 3.2) |
| 11 | MAJOR | install.ps1 13 agents, uninstall.ps1 25 vs sh installers' 33 | both PS1 registries now match the full vercel-labs/skills registry |
| 12 | MAJOR | install.ps1 `$syncRoots` 11 vs install.sh 34 | raised to the same 34 roots |
| 14 | MAJOR | core-only reinstall overwrote the manifest, orphaning previously installed extras from uninstall's view | `write_manifest`/`Write-Manifest` preserve prior extras records when the run recorded none |
| 3 | MAJOR | native nonzero exits never failed PowerShell jobs | `Invoke-Native` throw wrapper, 46 call sites |
| 4 | MAJOR | managed-skill backup failures could still delete the skill | `Backup-ManagedSkill` + fail-safe `Sync-CoreSkill` + `-Force` |
| 1,2 | MINOR | ToB plugin scope gap + fallback lists | dual-scope uninstall both platforms |
| 19 | MINOR | install.ps1 manifest missing `SPS_VERSION=` | added |
| 16 | MINOR | `--interactive` parsed but never read | fails fast when stdin is not a TTY |
| 17 | NIT | uninstall.sh confinement comment miscounted roots | corrected (34 + 2 rules dirs + legacy `.antigravity/skills`) |
| 7,8,9,10,13,15,18,20,21,23 | — | success-line truth, core-only progress bar, exit semantics, get-sps.ps1 path/flags, help text, drift-check command, bounded prune, backup merge, graphify sweep | all applied |

## Round 3 — governance reviewer (committed in 2263684)

12 findings (1 MAJOR + 4 MINOR + 7 NIT). Hash chain and per-entry integrity
PASS. Key fixes:

- **MAJOR — import-scanner bypass:** `import framework.domain.seo`,
  `from framework.domain.seo import model`, `import domain.seo.model`, and
  relative `from . import seo` all evaded the DEC-7302 allowlist; f-string
  module names evaded the dynamic check. New `_is_domain_seo_module` helper,
  alias-qualified relative-import handling, `JoinedStr` detection. All bypass
  forms probed live — now caught; benign imports unaffected; the 4 approved
  pairs intact.
- MINOR: `--list` display sanitizes control chars (hostile ledger can't forge
  rows); `\Z` trailing-newline fix now has a regression test (reverting to `$`
  fails the suite); anchor-test docstring no longer overclaims a 4th surface.
- NITs: stale counts in `legacy_exceptions.py` header/docstring, redundant
  `startswith("/")`, gen_law_test message/docstring drift, round26 comment.

## Round 4 — CI+docs reviewer (committed in 2263684)

13 findings (1 CRITICAL + 3 MAJOR + 4 MINOR + 4 NIT). The CRITICAL (1c7f523
failed its own secret gate + suite via the audit reports' dummy token) was
already fixed in ed946d0. Fixes this round:

- **MAJOR:** README prove-it command `sps-backup.sh` → `sps-backup.sh snapshot`
  (the bare command printed usage and exited 2).
- **MAJOR:** ecosystem-scan.yml jq `;` separator was invalid — swallowed by
  `|| true`, dedup set always empty, duplicate proposal issues nightly →
  valid `,` stream.
- **MAJOR:** ecosystem-scan label never bootstrapped — fresh repos filed zero
  issues while the step reported success → `gh label create` guard added;
  scan step gains `set -euo pipefail` so a failed scan can't pass via tee.
- MINOR: CHANGELOG "52 modules" → 53; README stale "v4.3.0" → v4.4.0;
  windows-smoke comments corrected (installer exits 0 when core mirrors
  healthy); README "~27" → 26 third-party skills.
- NITs: sps-ci `on:` quoted, two jobs gained timeouts, redundant
  working-directory dropped, unused step id removed.

## Governance chain

Every round re-pinned the affected files and re-chained the canonical hash
across all three surfaces (manifest ↔ `legacy_exceptions.py`
`EXPECTED_MANIFEST_SHA256` ↔ `manifest-anchors.env`):
`11a3e8f7…` → `fd72245b…` (f1009bf) → `f11272c5…` (2263684).

## Final state after rounds 2–4

- 1,259 tests OK (1 new regression test), skipped=3
- Laws, docs-drift, mirrors, P2 (69 checks + 22 negatives), P3–P7,
  bootstrap, sps2 validator, anchor tests: all green
- Smoke: 128 PASS

## Outstanding

- Scripts reviewer report still pending (5th agent).
- Batch C design questions for the User (workbuddy 2-file verifier
  middle ground; codexx law-checker-own-docs) — to be presented after the
  scripts round lands.
- CI on 2263684 watched; auto-merge rule applies on green.

---

## Round 5 — scripts reviewer (committed in 02da7d3, + CI catch in 8281442)

12 findings (1 CRITICAL + 1 MAJOR + 6 MINOR + 4 NIT), all fixed. The
reviewer empirically tested every load-bearing claim on macOS bash 3.2.

- **CRITICAL**: empty-array expansion under `set -u` on bash 3.2 — the
  deeper form of round-2 finding 22. `"${ARR[@]:-}"` yields a stray empty
  arg; plain `"${ARR[@]}"` is an *unbound variable error* on an empty
  array. All 48 expansions across install.sh / uninstall.sh /
  sps-update.sh / sps-lesson.sh now use the bash-3.2-safe idiom
  `"${ARR[@]+${ARR[@]}}"`.
- **MAJOR**: sps-lesson.sh send was fail-open — missing scanner only
  warned, then pushed unscanned content to the public repo. Now aborts.
- MINOR/NIT: same-day resend branch reuse, commit-failure abort,
  restore-preview mtime split, smoke status-repo cwd, doctor --fix
  project-arg wipe, lesson overwrite skip, matched-text-only allowlist
  testing, NUL-safe file walk, unknown-option rejection, hygiene -z
  rename-pair parsing.

**Live CI catch:** windows-smoke on 6035452 exposed a PowerShell parse
error in install.ps1 (`"$LASTEXITCODE:"` inside a string parses as a
scoped-variable reference) — fixed in 8281442 with `${LASTEXITCODE}`.

Governance chain: 5 re-pin cycles this session, final canonical hash
`42b5a0bc…`. Final: 1,259 tests OK, smoke 128 PASS, all gates green.

**Repo-setting fact verified for Batch C:** branch protection requires 4
checks (Lint+smoke, PowerShell syntax, Python unit tests, Version
sanity), strict=true, **enforce_admins=false** (admin pushes bypass).
