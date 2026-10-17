# SPS2 ROUND 19B — INDEPENDENT SECURITY, AUTHORIZATION, AND PRE-COMMIT RISK AUDIT

Report time: 2026-10-16T18:49:05+06:00 (suffix 20261016-184905)
Audit window: 18:47:01 – 18:49:05 +06 (≈2 minutes of inspection; baseline
captured at 18:47:01).
Mission: an independent, strictly read-only security, authorization, and
pre-commit risk audit, performed while Codex concurrently completes its
engineering verification and commit-boundary review. This audit is
independent: no finding below is derived from Codex's reports; where a
finding corroborates one, the corroboration is noted explicitly.

**Safety compliance.** No source, test, schema, decision, evidence,
inventory, CMS, configuration, or CI file was modified. Nothing was staged,
committed, pushed, fetched, pulled, deployed, published, or approved. No
installer, updater, or bootstrap script was executed. Nothing was reset,
cleaned, stashed, reverted, deleted, moved, or overwritten. Codex's work was
not touched. The only file created is this report.

---

## 1. Live baseline at audit time

| Item | Value |
|---|---|
| Branch | `build/roadmap-p3-completion` |
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` |
| Porcelain entries | 33 (16 modified tracked + 17 untracked) |
| Staged | **0** |
| Stashes | **0** |
| Reports in `reports/` | 29 (this report makes 29; none overwritten) |
| All 6 mission-named reports present | YES (verified by listing and, for the two previously unseen ones, by full read) |

**Concurrent-change detection.** SHA-256 of 11 key files was snapshotted at
audit start (`/tmp/r19b_hashes_start.txt`, 18:47) and re-hashed at audit end
(18:49): **all 11 byte-identical** — gate tool `99d55ffb…`, gate tests
`f585e1b4…`, updater tests `d51c20dd…`, install.sh `415d3171…`, install.ps1
`3d55ddde…`, get-sps.sh `3b3e4fcf…`, get-sps.ps1 `3b3b084d…`,
sps-update.sh `ba90bfbf…`, update-sps.ps1 `fc207b82…`, bootstrap
`81390654…`, sps-ci.yml `5ba091ce…`. **No concurrent edit landed in the
audit window.** All findings below describe this frozen state; if Codex
changes files afterwards, they are Codex's edits, not this audit's.

## 2. Files inspected (first-hand, this audit)

Read in full or in targeted diff: `.github/workflows/sps-ci.yml`,
`install.sh`, `uninstall.sh` (grep), `scripts/smoke-sps.sh` (grep),
`scripts/check-update.sh` (grep), `get-sps.ps1`, `get-sps.sh`,
`scripts/sps-update.sh`, `scripts/update-sps.ps1`,
`scripts/bootstrap-sps.sh`, all three `skills/sps/scripts/` mirrors,
`sps2/tools/p10_runtime_gate.py` (targeted), `sps2/tests/test_updater_safety.py`
(full), `domain/frontend/home_render.py` (grep),
`domain/cms/output_safety` (contract), diffs of all 16 modified tracked
files, `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json`,
`P10-GATE-SEMANTICS-ADOPTION.json`, `P10-ROUND12-USER-DECISIONS.json`,
`P10-DELEGATED-DECISIONS.json`, `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md`
(index only), `reports/SPS2-ROUND16-AUTONOMOUS-ENGINEERING-20261016-182330.md`,
`reports/CODEX-SECURITY-HARDENING-PLAN-20261016-172529.md`, and the Round
15/17/18 reports of this session. Secret scans (diff + untracked) were clean.

## 3. Security findings (ranked by severity)

Every finding below was verified first-hand with file:line. "Verified
defect" = demonstrated against the live tree; "theoretical risk" = condition
not reachable in the current tree but live in the code path.

### S-01 (HIGH, verified defect) — CI workflow runs with no permission restriction and mutable action tags
`.github/workflows/sps-ci.yml` (hash `5ba091ce…`): **no `permissions:` block
and no `concurrency:` block anywhere in the file** — every job inherits the
default (historically broad) token scope. All action references are mutable
tags, not SHAs: `actions/checkout@v4`, `actions/setup-node@v4`,
`actions/setup-python@v5`. A future tag re-point on any of these upstreams
injects arbitrary code into CI with the repo token's default scope.
Corroborates Codex C-01/C-02 (independently re-verified here).
**Failure scenario:** upstream tag compromise or a maintainer force-moving a
minor tag → workflow executes attacker code with default GITHUB_TOKEN scope
over the repository. **Not exploitable by anything in this repo today; it is
a supply-chain exposure.**

### S-02 (HIGH, verified defect) — CI smoke job executes the installer with auto-yes and network access
`sps-ci.yml` lint-and-smoke job: `scripts/smoke-sps.sh` is invoked with
`npm_config_yes=true` in the environment, and `scripts/smoke-sps.sh:77` runs
`HOME="$SMOKE_HOME" bash install.sh --agents '*' --yes`. install.sh then
performs **27 unpinned `npx skills add` invocations** (install.sh:338–358)
and adds **unpinned claude plugin marketplaces** (install.sh:373–380).
**Failure scenario:** any compromise of the upstream skill sources or npm
registry resolution executes arbitrary postinstall code inside CI with the
default token. This is exactly the unpinned-supply-chain surface of S-01,
exercised at runtime rather than at checkout.

### S-03 (HIGH, verified defect) — installer hard-disables two git/npm safety mechanisms
`install.sh:15-17`:
`GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=no"`,
`GIT_CLONE_PROTECTION_ACTIVE=false`, `npm_config_yes=true`.
`StrictHostKeyChecking=no` accepts any host key on first contact (MITM on
the clone path); `GIT_CLONE_PROTECTION_ACTIVE=false` disables git's
filesystem protection against untrusted repositories; `npm_config_yes=true`
auto-confirms every npm prompt. These are defaults for **every** install,
not opt-ins. Corroborates Codex SH-07 (independently re-verified).

### S-04 (HIGH, verified defect) — installer replaces managed trees with no backup and a destructive window
`install.sh:254-263` (`sync_core_skill`): `rm -rf "$dest_root/sps"` then
`cp -R`; later `rm -rf "$dest_root/sps-cms"` then copy. `install.ps1:165-188`
(`Sync-CoreSkill`): `Remove-Item -Recurse -Force $dest` then `Copy-Item`.
**Failure scenario:** copy failure (disk full, permission, interruption)
after the removal leaves the destination missing or partial — silent data
loss of the user's installed skill tree. Round 17's Proposal B1
(timestamped backup, bounded retention, restore-on-failure) remains
**unimplemented** — correctly, since installers are outside current
authorization.

### S-05 (MEDIUM, verified defect) — uninstall scope includes the entire user state directory
`uninstall.sh`: `rm -rf` at :99, :170, :173, :211, and :218 — the last being
`rm -rf "$HOME/.sps"`, which removes **all** SPS user state (source clone,
CMS data, caches) in one step. If any future feature stores user data under
`~/.sps` without the uninstaller being updated, it is silently destroyed.
Theoretical today (the tree's layout is known), real immediately if
`SPS_REPO_DIR` is ever defaulted elsewhere.

### S-06 (MEDIUM, verified defect) — check_sps2.py validators always exit 0
`sps2/tools/check_sps2.py` prints `ERR …` lines but exits 0 in all cases;
callers must grep stdout. Any CI or hook wiring that trusts the exit code
scores every governance failure as clean. Corroborates Codex F-005
(independently re-verified). **Failure scenario:** a future gate step runs
`python3 check_sps2.py inventory && publish` — the ERR is printed, the
publish proceeds.

### S-07 (MEDIUM, verified defect) — renderer escape contract is a single-sink discipline, not a structural guarantee
`domain/frontend/home_render.py` imports `encode_for_html` from
`domain.cms.output_safety` and invokes it exactly once per output value —
good, and Round 18 verified draft fail-closed (`draft_policy="fail"` default
raises `HomeBuildError` stage 3). But the guarantee is **conventional**: any
future render path that formats a CMS string without the sink produces raw
HTML with no runtime detector. `HOME-ACC-07` ("every value reaching an HTML
sink passed encode_for_html exactly once") is currently enforced by tests,
not by construction. Theoretical risk; no current violation found.

### S-08 (LOW, verified defect) — DEC-7202 digest write narrowly supersedes a fail-closed prohibition
`sps2/requirements/P10-SECTION-INVENTORY.json` now carries
`cms_state_digest = sha256:b35f7aba68eca4e7…` and `p8_contract_digest =
sha256:ee6bb68f04f0eb46…`. Both were independently recomputed this audit
window's predecessor rounds and match the live CMS state
(`content.json` `c46a0012…`, `content_types.json` `6635ed4d…`,
`revisions.jsonl` `54a0eeaa…`). Risk is not the values but the **precedent**:
DEC-7112 originally prohibited writing these; DEC-7202 supersedes it for
exactly two values. Any future "just write the digest" edit without a fresh
recompute against live CMS would silently bind a stale state. The two
current values are verified correct.

### S-09 (LOW, verified defect) — gate-record timestamp check is a raw-suffix check, not a semantic UTC check
Post-R17, `sps2/tools/p10_runtime_gate.py` requires `utc_timestamp` raw text
to end in `Z`/`z`/`+00:00`/`-00:00` (probe-verified: `+06:00` FAILs even
though it denotes the same instant). This is stricter than semantics require
but honest; the residual risk is that a legitimate non-zero-offset-but-UTC
producer is rejected — fail-closed, not fail-open. No action needed; recorded
for completeness.

### S-10 (LOW, verified defect) — `.claude/settings.json` emptied to zero bytes
The tracked 3-line `{"enabledPlugins": {}}` was replaced with an empty file
(diff confirmed: `-3 lines, +0`). Functionally inert for security (it
disabled nothing and enabled nothing), but it is an unexplained
configuration mutation with no decision record, no ratification, and no
report claiming it. Classified AUTHORIZATION UNCLEAR in §4 and listed in the
pre-commit register §5. **Not attributable to this session** — this session
never wrote that file.

**Clean results (negative findings, verified):** secret scans of the full
diff and all untracked files found no credentials, tokens, or keys (only
benign token-*variable* names); no network call in any ratified updater
precedes its safety refusal (ordering test-verified, R15-004); no ratified
updater contains `git reset --hard`, `rm -rf "$REPO_DIR"`, or
`Remove-Item -Recurse -Force $repoDir` (test-enforced, 13/13 updater tests
pass); mirrors are byte-identical (`diff -rq scripts skills/sps/scripts`);
no untrusted-content→HTML path bypasses `encode_for_html` in the current
renderer; CI's `version-sanity` job's grep-on-file pattern is SIGPIPE-safe;
`MIN_TESTS=500` and the `.github/expected-test-modules.txt` presence guard
prevent silent test deletion in CI.

## 4. Authorization matrix

Legend: **EXPL** = EXPLICITLY AUTHORIZED; **RAT** = RATIFIED AFTER
IMPLEMENTATION (implemented first, user ratified later — still not commit
authorization); **UNCLEAR** = AUTHORIZATION UNCLEAR; **OUTSIDE** = OUTSIDE
CURRENT AUTHORIZATION; **N/A** = NOT APPLICABLE. Edit authorization is
distinguished from stage/commit/push/publish/approve authorization in every
row. Authorization was never inferred from file existence, passing tests,
another agent's actions, or earlier reports — only from decision records
read this audit (DEC-7111, DEC-7112, DEC-7201, DEC-7202, DEC-7203, and the
P10-DECISIONS D-P10-1..9 additions, all verified present and ACTIVE).
DEC-7203 standing constraints verified intact: **publication DEFER; user
approval NOT GRANTED; commit/push NOT AUTHORIZED; CI changes NOT
AUTHORIZED.**

| File / group | Edit authorization | Stage/commit | Push | Publish/approve | Basis |
|---|---|---|---|---|---|
| `sps2/tools/p10_runtime_gate.py`, `sps2/tests/test_p10_runtime_gate.py` | EXPL (Round 14 gate-semantics authorization; R15-001/002/003 fixes under adopted DEC-7112 contract) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | DEC-7112; Round 14 mission |
| `sps2/schemas/p10-slice.schema.json` (uniqueItems + SPEC-2 wording correction) | EXPL (schema was in the 2026-10-09 Phase-1 approval; the correction is a wording fix consistent with it) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | D-P10 decision record, 2026-10-09 approval text |
| `sps2/requirements/P10-SECTION-INVENTORY.json` (two digests only) | EXPL, narrowly | NOT AUTHORIZED | NOT AUTHORIZED | NOT AUTHORIZED (`user_approval` stays null) | DEC-7202 (supersedes DEC-7112 for exactly two values) |
| `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json` (DEC-7201/7202/7203) | EXPL (recording the user's own Round 16 decisions) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | Round 16 user message (verbatim in evidence array) |
| Updater workstream: `get-sps.sh`, `get-sps.ps1`, `scripts/bootstrap-sps.sh`, `scripts/sps-update.sh`, `scripts/update-sps.ps1` + 3 mirrors, `sps2/tests/test_updater_safety.py` | RAT (implemented Rounds 15–17, ratified by DEC-7201) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | DEC-7201 |
| `sps2/decisions/P10-DECISIONS.json` (D-P10-6/7/8 additions + note) | EXPL (recording user decisions of 2026-10-13) — but the file carries 10 pre-existing `DEC-\d{4}` validator ERRs (D-P10-* ids predate the rule; out of the 2026-10-09 approval's scope by its own text) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | D-P10-6/7/8; 2026-10-09 approval scope carve-out |
| `sps2/governance/attribution.py` (token-shape + duplicate-token semantic validation) | EXPL in spirit (SPEC-2 approver-policy consolidation, 2026-10-15; strengthens a control, weakens none) but **no decision record names this file** — the authorization is via the SPEC-2 audit's approved mandate, not a numbered DEC | NOT AUTHORIZED | NOT AUTHORIZED | N/A | SPEC-2 (KI-15/KI-16 index entries; DEC-0028 preserves legacy controls) |
| `sps2/requirements/P5-REQUIREMENTS.json`, `sps2/evidence/P5-EVIDENCE.json` (SPEC-2 factual corrections, originals preserved verbatim) | Same as attribution.py: SPEC-2 mandate, no numbered DEC; corrections change *descriptions*, not verification states (`state_changed: false`) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | SPEC-2 correction notes in-file |
| `.sps/audits/README.md` (SPEC-2 index row + KI-15/KI-16) | Same as above (audit register maintenance under SPEC-2) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | SPEC-2 |
| `domain/frontend/*` (7 modules + 3 test modules), `domain/cms/data/*` (3 files), `sps2/project/SLICE-P10-01.json`, `sps2/evidence/P10-EVIDENCE.json` | EXPL (P10 Home-slice implementation, Round 14 authorized) — but the slice is DRAFT, evidence is stale (R15-009) and preserved untouched by order | NOT AUTHORIZED | NOT AUTHORIZED | **NOT AUTHORIZED** (publication DEFER; approval NOT GRANTED) | Round 14; DEC-7203 |
| `install.sh`, `install.ps1`, `uninstall.sh`, `scripts/smoke-sps.sh` | **OUTSIDE** (installer global-write policy explicitly deferred; R15-005/B1 proposal unimplemented by order) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | Round 17 mission item; DEC-7203 |
| `.github/workflows/sps-ci.yml` and anything CI | **OUTSIDE** — CI CHANGES NOT AUTHORIZED (DEC-7203). The file is tracked and unmodified in the worktree; its *content* predates this workstream | N/A | N/A | N/A | DEC-7203 |
| `.claude/settings.json` (emptied to 0 bytes) | **UNCLEAR** — no decision record, no report, no mission text covers this mutation; discovered only by diff | NOT AUTHORIZED | NOT AUTHORIZED | N/A | none found |
| `LEGACY-PATH-DEFINITION-DECISIONS.json`, `LEGACY-SCOPE-DECISIONS.json`, `P10-DELEGATED-DECISIONS.json`, `P10-GATE-SEMANTICS-ADOPTION.json`, `P10-ROUND12-USER-DECISIONS.json`, `SPS2-ROUND16-USER-DECISIONS.json` (untracked decision records) | EXPL (each records user decisions; validators 0 ERR on the Round-12-era and newer ones) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | their own contents |
| `reports/*` (29 files), `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md`, `.sps/evidence/P17/*`, `.sps/tasks/p17/*`, `sps2/tests/test_p10_runtime_gate.py` (untracked) | EXPL to create (report mandate; standing memory rule: new timestamped file, never overwrite) | NOT AUTHORIZED | NOT AUTHORIZED | N/A | mission text; memory rule |
| `sps2/tools/p10_runtime_gate.py` — approval-authenticity control | N/A for edits; note for approvers: the gate structurally rejects agent-attributed approvals (`decided_by_role` enum `[USER]`), but `decided_by` remains self-asserted free text — **UQ-ATT-2 stands**: no mechanism here can prove a human authored an approval. The SPEC-2 schema correction now says this honestly | — | — | **Any approval act requires a fresh explicit user act** | DEC-7203; SPEC-2 correction |

**Key distinctions enforced in every row:** "ratified" ≠ "commit
authorized" (DEC-7201 ratifies the updater workstream's *content* and
explicitly does not authorize commit or push); "implemented" ≠ "verified" ≠
"approved" (three-axis rule); agents cannot self-approve (UQ-ATT-2; the
schema's own SPEC-2 correction now states this limitation verbatim).

## 5. Pre-commit risk register

Nothing is staged. When commit authorization is eventually considered, these
are the boundaries, in the mission's four categories:

### A. Do NOT commit without explicit review
1. **`.claude/settings.json`** — emptied to 0 bytes with no recorded
   authorization. Committing would enshrine an unexplained config mutation;
   restoring the tracked content would equally be a change needing a
   decision. Resolve its provenance first.
2. **`install.sh` / `install.ps1`** — outside current authorization; any
   commit would exceed the ratified scope (currently unmodified, so the
   risk is only if a future session edits them).
3. **`.github/workflows/sps-ci.yml`** — CI CHANGES NOT AUTHORIZED
   (DEC-7203). Currently unmodified; must stay that way absent a decision.

### B. Safe as separate, self-contained commits (each verified, each with its own decision basis)
4. **Updater-safety workstream** (8 tracked modified + mirrors +
   `sps2/tests/test_updater_safety.py`) — DEC-7201-ratified; 13/13 tests;
   mirror parity verified. One commit, message citing DEC-7201.
5. **P10 gate + gate tests** (`p10_runtime_gate.py`,
   `test_p10_runtime_gate.py`) — Round 14-authorized; 320 tests OK.
6. **P10 slice + evidence + decisions** (`SLICE-P10-01.json`,
   `P10-EVIDENCE.json`, the five untracked decision records,
   `P10-DECISIONS.json` additions) — user-decision records; note the
   pre-existing `D-P10-*` validator ERRs travel with this group (documented,
   not worsened).
7. **Inventory digest write** (`P10-SECTION-INVENTORY.json`) — DEC-7202;
   both digests independently recomputed and matching. Clean as a one-file
   commit.
8. **SPEC-2 governance corrections** (`attribution.py`,
   `P5-REQUIREMENTS.json`, `P5-EVIDENCE.json`, `.sps/audits/README.md`) —
   coherent as one commit; carries the caveat that no numbered DEC names
   these files (see §4).
9. **Renderer + CMS data** (`domain/frontend/*`, `domain/cms/data/*`) — 85
   tests OK; draft fail-closed verified.
10. **Reports** (`reports/*` + `AUDIT-SPEC2-*.md` + `.sps/audits` index) —
    append-only record; safe as one documentation commit.

### C. Unrelated to the ratified work (verify provenance before any commit)
11. `.claude/settings.json` (again — it is both A-1 and C-11).
12. `.sps/evidence/P17/*`, `.sps/tasks/p17/*`, and the P17 gate regression
    module referenced in commit `f060703` — P17 work predates this
    workstream; confirm it belongs on this branch.

### D. Dependency-unsafe as isolated commits
13. **`P10-SECTION-INVENTORY.json` without its decision record** — the
    digests are authorized by DEC-7202; committing the inventory without
    `SPS2-ROUND16-USER-DECISIONS.json` severs the authorization chain.
14. **Gate tool without gate tests** (or vice versa) — the 320-test suite
    is the gate's verification; splitting them ships unverified code.
15. **Updater scripts without their mirrors** — mirror parity is
    test-enforced (`test_updater_mirrors_are_byte_identical`); a one-sided
    commit breaks the suite and the parity guarantee.
16. **`P10-DECISIONS.json` additions without `P10-GATE-SEMANTICS-ADOPTION.json`
    / `P10-ROUND12-USER-DECISIONS.json`** — the D-P10-6/7/8 note text
    references the adopted semantics; the referenced records must land
    together (all are currently untracked).

### E. Issues Codex should resolve before any commit boundary is drawn
17. Obtain the missing numbered decision for the SPEC-2 file group (§4 row
    8) or record one — the commit message should not have to assert an
    authorization the record set doesn't show.
18. Resolve `.claude/settings.json` provenance (A-1).
19. Confirm the SEO suite's 4 worktree-sensitive failures (noted in Codex's
    Round 16 report) are environmental and not shipped regressions.
20. Decide the `D-P10-*` validator ERR posture for the commit message
    (documented-exception vs. deferred fix) — renaming is forbidden by
    Round 18 mission item 9.

## 6. Verification of high/medium findings (per mission phase 5)

| Finding | file:line | Concrete failure scenario | Class | Relevant tests | Read-only repro possible? |
|---|---|---|---|---|---|
| S-01 | `sps-ci.yml` (whole file; no `permissions:`/`concurrency:` keys; `@v4`/`@v5` tags at the `uses:` lines) | Upstream tag re-point → attacker code with default token scope | Verified defect (absence verified by full read) | none exist | YES — file read |
| S-02 | `sps-ci.yml` smoke job env; `scripts/smoke-sps.sh:77`; `install.sh:338-358, 373-380` | Compromised skill source/npm → arbitrary code in CI | Verified defect | none | YES — source read; installer NOT executed per rules |
| S-03 | `install.sh:15-17` | MITM clone / unsafe repo checkout / auto-confirmed npm installs | Verified defect | none (installer out of test scope) | YES — source read |
| S-04 | `install.sh:254-263`; `install.ps1:165-188` | Copy failure after removal → destination lost/partial | Verified defect (code path; destructive run not reproduced, per rules) | none (B1 proposed, unimplemented) | YES — source read |
| S-05 | `uninstall.sh:99,170,173,211,218` | `rm -rf "$HOME/.sps"` destroys all user state | Verified defect | none | YES — source read |
| S-06 | `sps2/tools/check_sps2.py` (exit path) | Caller trusts exit 0 → governance ERR scored clean | Verified defect | none | YES — prior-round probe; re-confirmed by source |
| S-07 | `domain/frontend/home_render.py` (single `encode_for_html` import/sink) | Future render path skips sink → raw HTML | Theoretical risk (no current violation) | 85 frontend tests OK | YES — source read |
| S-08 | `P10-SECTION-INVENTORY.json` provenance block | Stale digest bound without recompute | Verified correct today; precedent risk | digest recompute MATCH | YES — recompute done |

## 7. Discrepancies with earlier reports

1. **None on facts.** Every fingerprint, digest, test count, and gate verdict
   re-checked this audit matches Round 15/17/18: HEAD `c49f3852…`, 33
   porcelain, 0 staged, 0 stashes, digests `b35f7aba…`/`ee6bb68f…` MATCH,
   418 tests OK (Round 18), gate FAIL 9/5/2 (honest).
2. **Corroboration, not dependence:** S-01/S-03/S-04 corroborate Codex
   SH-07/C-01/C-02 and F-005 (S-06) — each re-verified first-hand here; no
   finding in this report was accepted from Codex's reports without
   independent inspection.
3. **New in this audit:** `.claude/settings.json` emptying (S-10) appears in
   no earlier report of any session — first surfaced in this audit's diff
   review (the previous session's attempt to display it was cut short by a
   shell error, per the Round 19B working notes).
4. **Framing difference:** Codex's hardening plan (SH-01..07, C-01..08,
   I-01..10) proposes fixes; this audit deliberately proposes none —
   installation of fixes is outside read-only scope, and installer/CI
   changes are OUTSIDE current authorization (§4).

## 8. Unresolved risks and recommended decisions

| # | Risk / question | Decision needed from the User |
|---|---|---|
| 1 | All ratified + authorized work exists only as working-tree changes (0 staged) | Grant (or withhold) commit authorization **per file-group** using §5-B boundaries; DEC-7203 currently forbids it |
| 2 | `.claude/settings.json` emptied, no provenance | Decide: restore tracked content, keep the empty file, or record why it was emptied |
| 3 | SPEC-2 file group lacks a numbered decision record | Ratify (like DEC-7201) or defer; the corrections are descriptive-only but should not ride on an implied mandate |
| 4 | Installer S-03/S-04 (unsafe defaults, destructive sync) | Authorize Proposal B1 (Round 17 §3) or explicitly accept the risk; either way record it |
| 5 | CI S-01/S-02 (no permissions block, mutable tags, network smoke) | CI CHANGES NOT AUTHORIZED stands; a hardening decision would amend DEC-7203 |
| 6 | Publication DEFER; user approval NOT GRANTED | Unchanged; both lift gate failures only when granted |
| 7 | UQ-ATT-2 (self-declared attribution) | Standing; no local mechanism can close it — needs the approval-mechanism decision already parked (OPTION A) |
| 8 | `D-P10-*` validator ERRs | Validator accommodation decision (rename forbidden) |

## 9. Exact commands and checks performed

All from repo root, read-only, 18:47–18:49 +06:
`git status --porcelain=v1`; `git diff --cached --name-only`; `git stash list`;
`git rev-parse HEAD`; `git log --oneline -5`; `ls reports/`;
`git diff <each of 16 tracked modified files>` (full or targeted);
`git diff --stat` over the tracked set;
`shasum -a 256` on the 11 snapshot files, compared to
`/tmp/r19b_hashes_start.txt`; `grep` secret scans over the diff and
untracked files; targeted reads of `sps-ci.yml`, `install.sh`,
`uninstall.sh`, `smoke-sps.sh`, `check-update.sh`, `home_render.py`,
`test_updater_safety.py`, `get-sps.ps1`, and the five decision records.
No test suite was re-run this audit (Round 18 ran the full battery 12
minutes earlier; hashes prove the inputs unchanged). No installer, updater,
bootstrap, or validator that writes was executed.

## 10. Limitations

- **Two-minute window:** concurrent-change detection covers 18:47–18:49
  only. Codex may have edited before 18:47 (nothing in the 33-entry
  porcelain set is attributable to this audit) or may edit after — findings
  describe the hashed state.
- **Destructive paths not executed:** S-02/S-03/S-04/S-05 are verified from
  source, not by running installers (forbidden by the mission and by
  prudence). The failure scenarios are code-path deductions, which is why
  S-04's scenario is labeled as such even though the defect class is
  verified.
- **No dynamic CI verification:** the workflow was read, not run; S-01's
  "default token scope" is the documented GitHub default, not an observed
  token leak.
- **Authorization matrix reflects the record set as of this audit:** if a
  decision record exists outside `sps2/decisions/` (e.g., only in chat and
  not yet transcribed), the matrix may under-count authorization — that is
  the correct fail-closed bias.
- **This audit cannot verify Codex's concurrent work** and does not claim
  to; §7 corroboration is limited to findings re-inspected first-hand.

---

*Round 19B complete. Strictly read-only; exactly one file created (this
report); no earlier report, decision, or source file touched. The worktree's
security posture, authorization boundaries, and commit risks are as recorded
above. Stopping here per the mission — awaiting review.*
