# SPS2 ROUND 20 — AUTHORIZATION RECONCILIATION AND COMMIT READINESS

Report time: 2026-10-16T19:02:00+06:00 (suffix `20261016-190200`).  
Scope: read-only reconciliation of Claude Round 19B and Codex Round 19. No source, test, decision, evidence, configuration, schema, CI, or historical report was modified. Nothing was staged, committed, pushed, deployed, published, approved, reset, cleaned, stashed, deleted, moved, or overwritten.

## 1. Live baseline

- Branch: `build/roadmap-p3-completion`.
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`.
- Upstream: `origin/build/roadmap-p3-completion`.
- Staged changes: none.
- Stashes: none.
- Tracked modified paths: 16.
- Git-untracked non-ignored paths: 139 before this report; adding this report keeps the porcelain count at 33 because `reports/` is already untracked.
- CI diff: none.

The Round 19B report exists at
`reports/SPS2-ROUND19B-INDEPENDENT-SECURITY-AUTHORIZATION-AUDIT-20261016-184905.md`.
The Codex Round 19 report exists at
`reports/SPS2-ROUND19-COMMIT-BOUNDARY-REVIEW-20261016-184230.md`.
Both were preserved unchanged.

## 2. Reconciliation of the four unresolved issues

### 2.1 `.claude/settings.json` provenance — VERIFIED OPEN / USER DECISION

Verified facts:

- HEAD contains three lines: `{"enabledPlugins": {}}`.
- The working-tree file is zero bytes; `git diff` shows all three lines removed.
- File mtime is `2026-10-16 15:45:17 +0600`, before the Round 12 report at 17:06.
- Round 13 already recorded the file as modified at session start.
- `sps2/decisions/OPEN-DECISION-CLAUDE-SETTINGS.json` records historical DEC-0024: treatment A+C was applied on 2026-10-04 and the file was restored to HEAD.
- The historical decision does not authorize the later emptying. The current writer cannot be identified from Git alone.

Reconciliation: Claude S-10 and Codex Round 19 agree that this is an unexplained configuration mutation. It is not attributable to either report session. No existing authorization permits restoring, committing, or further changing it.

Required decision: choose restore-to-HEAD, retain-empty, untrack, or another treatment; record the choice in a new numbered decision before any commit containing this file.

### 2.2 Missing numbered decision for the SPEC-2 file group — VERIFIED OPEN / USER DECISION

Verified facts:

- The SPEC-2 working set includes `sps2/governance/attribution.py`, `sps2/requirements/P5-REQUIREMENTS.json`, `sps2/evidence/P5-EVIDENCE.json`, `.sps/audits/README.md`, and `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md`.
- `ATTRIBUTION-POLICY-DECISIONS.json` contains DEC-0025 through DEC-0028.
- DEC-0025 ratifies only addition of the `antigravity` token and states that no consumer edit was required and no behavior changed beyond that token.
- The working tree adds semantic token-shape and duplicate-token validation to `attribution.py`; this is beyond DEC-0025's authorized behavior change.
- The P5 files make factual corrections but explicitly leave verification state unchanged.
- `.sps/audits/README.md` adds SPEC-2 index entries KI-15 and KI-16.
- No numbered decision record was found that authorizes this exact four-file correction group for staging or commit.

Reconciliation: Claude and Codex agree that the edits are coherent and security-strengthening, but lack a numbered authorization/commit record. This is not a defect to fix silently under existing authorization.

Required decision: either ratify the exact SPEC-2 file group in a new numbered decision or explicitly defer it. The decision should distinguish edit ratification from commit authorization.

### 2.3 Four SEO test failures — TWO CONTRACT CONFLICTS, ONE DIRTY-WORKTREE CLASS

Read-only helper reproduction found:

```text
domain/frontend/home_render.py:66: orphan domain.seo.indexing
domain/frontend/home_render.py:71: orphan domain.seo.metadata
domain/frontend/home_render.py:75: orphan domain.seo.model
domain/frontend/tests/test_home_render.py:42: orphan domain.seo.audit
```

It also found two legacy-diff violations:

```text
skills/sps/scripts/bootstrap-sps.sh
scripts/bootstrap-sps.sh
```

Classification:

| Test | Classification | Cause |
|---|---|---|
| `test_zero_orphan_references_across_repository` | VERIFIED OPEN contract conflict | Home renderer intentionally imports P9 SEO modules, but the SEO rollback-isolation scanner classifies every outside reference as an orphan. |
| `test_live_status_reporting` | VERIFIED OPEN contract conflict | Same four Home-renderer references produce `orphan_count=4`. |
| `test_live_rollback_rehearsal_success` | VERIFIED OPEN contract conflict | Rehearsal runs in a temporary copy, but after deleting `domain/seo`, Home still references it, so validation fails. |
| `test_legacy_diff_zero` | DIRTY-WORKTREE SENSITIVITY | The two updater-safety bootstrap modifications are exactly the detected legacy diffs. |

These are not four independent product bugs. There are two underlying issues: the Home/P9 SEO boundary needs a normative allowance or architectural change, and the legacy-diff test cannot pass while ratified updater work remains uncommitted.

Required decisions:

1. Decide whether P10 Home may depend on P9 SEO and, if so, authorize a narrowly scoped SEO-isolation contract update.
2. Decide whether to commit the ratified updater work; committing it should remove the two legacy-diff violations without weakening the test.

No SEO test, Home renderer, or updater file should be changed for this in Round 20.

### 2.4 `D-P10-*` validator-error posture — VERIFIED OPEN / USER DECISION

Verified facts:

- `sps2/tools/check_sps2.py:224` requires `DEC-\d{4}`.
- HEAD has six `D-P10-*` decisions and produces six `bad decision_id` errors.
- The working tree has ten `D-P10-*` decisions and produces ten errors of the same class.
- The validator process exits 0 even while printing `ERR` lines.

Posture: preserve the historical IDs; do not rename them. Committing the P10 governance group will carry ten known validator errors unless the User separately chooses compatibility, migration, or documented acceptance.

Required decision: choose one of validator compatibility for legacy IDs, a governed migration plan, or explicit acceptance of visible errors. Renaming historical decision IDs should not be treated as a routine cleanup.

## 3. Security reconciliation

| Claude finding | Codex plan item | Current status | Authorization |
|---|---|---|---|
| S-01 CI lacks permissions/concurrency and uses mutable action tags | C-01, C-02, C-03, C-04 | Verified unchanged; CI file has no diff. | CI changes remain prohibited by DEC-7203. Requires explicit User authorization plus separately authorized network SHA verification. |
| S-02 CI smoke executes network installer with auto-yes | C-05, C-06, C-07 | Verified unchanged; smoke invokes installer with `--yes`. | Requires CI/installer authorization. |
| S-03 installer disables Git/npm safety controls | C-06, P0-6 | Verified at `install.sh:14-17`. | Installer policy deferred; requires User authorization. |
| S-04 installer deletes managed trees before verified backup | I-06, P0-4 | Verified at `install.sh:254-263`; PowerShell equivalent remains. | Installer preservation implementation requires User authorization. |
| S-05 uninstall can remove all `~/.sps` state | I-10 | Verified by source inspection. | Uninstall policy deferred; requires User authorization. |
| S-06 governance validators always exit 0 | Known governance risk | Verified; current validator prints ten `D-P10-*` errors and exits 0. | Changing exit semantics affects consumers/tests and requires User decision. |
| S-07 renderer escaping is conventional, not structural | Not separately planned | No current violation found; 85 frontend tests passed in Round 18. | Any structural enforcement is future implementation work requiring authorization. |
| S-08 digest writes create a stale-binding precedent | DEC-7202 narrowly authorized | Both current digests recomputed and matched in prior rounds. | Future digest writes require fresh authorization and recomputation. |
| S-09 gate timestamp check is raw-suffix strictness | Not a defect | Fail-closed behavior; no action recommended. | None. |
| S-10 `.claude/settings.json` emptied | Held in Codex Round 19 | Provenance unresolved. | User decision required. |

Both reports agree on the CI and installer exposures. Codex supplies implementation design; Claude independently corroborates the findings and correctly separates them from current authorization.

## 4. Proposed file-by-file commit plan

No group below is authorized to stage or commit by this report. Each requires an explicit User grant for that exact boundary.

### C1 — Updater safety

Proposed subject: `SPS2: preserve updater-safety boundaries and regression tests`

```text
get-sps.sh
get-sps.ps1
scripts/bootstrap-sps.sh
scripts/sps-update.sh
scripts/update-sps.ps1
skills/sps/scripts/bootstrap-sps.sh
skills/sps/scripts/sps-update.sh
skills/sps/scripts/update-sps.ps1
sps2/tests/test_updater_safety.py
```

- Edit basis: DEC-7201.
- Commit basis: missing; DEC-7201 explicitly does not authorize commit.
- Dependencies: none.
- Verification: updater unittest, Bash syntax, mirror parity, whitespace check.

### C2 — P10 runtime gate and tests

Proposed subject: `SPS2: preserve P10 runtime gate semantics and adversarial tests`

```text
sps2/tools/p10_runtime_gate.py
sps2/tests/test_p10_runtime_gate.py
```

- Edit basis: Round 14 and DEC-7112.
- Commit basis: missing.
- Dependencies: C3 provides governance context, but C2 is internally self-contained.
- Verification: P10 gate unittest; real gate expected to exit non-zero.

### C3 — P10 planning, governance, schema, and inventory contract

Proposed subject: `SPS2: preserve P10 planning contracts and governance decisions`

```text
sps2/decisions/P10-DECISIONS.json
sps2/decisions/P10-DELEGATED-DECISIONS.json
sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json
sps2/decisions/P10-ROUND12-USER-DECISIONS.json
sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json
sps2/project/SLICE-P10-01.json
sps2/requirements/P10-SECTION-INVENTORY.json
sps2/schemas/p10-slice.schema.json
```

- Edit basis: D-P10-6 through D-P10-9 and DEC-7202.
- Commit basis: missing.
- Dependencies: keep decision records with inventory/schema changes; do not split the authorization chain.
- Known validation errors: ten `D-P10-*` ID errors.
- Excluded: `sps2/evidence/P10-EVIDENCE.json`, pending stale-evidence wording decision.
- Verification: supported decision validators; protected-state checks; real gate expected non-zero.

### D1 — Home renderer, tests, and CMS data

Proposed subject: `SPS2: preserve Home renderer, CMS inputs, and integration tests`

```text
domain/cms/data/content.json
domain/cms/data/content_types.json
domain/cms/data/revisions.jsonl
domain/frontend/__init__.py
domain/frontend/content_slots.py
domain/frontend/home_render.py
domain/frontend/layout_registry.py
domain/frontend/tests/__init__.py
domain/frontend/tests/test_content_slots.py
domain/frontend/tests/test_home_render.py
domain/frontend/tests/test_layout_registry.py
```

- Edit basis: Round 13 Home implementation mission.
- Commit basis: missing.
- Dependencies: D1 can be committed independently, but the real gate and SEO reconciliation interact with C2/C3.
- Excluded: ignored `__pycache__/**` files.
- Verification: frontend and CMS unittest discovery; confirm Home content remains `draft`.

### S1 — Conditional SPEC-2 corrections

Proposed subject: `SPS2: preserve SPEC-2 attribution and governance corrections`

```text
.sps/audits/README.md
AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md
sps2/evidence/P5-EVIDENCE.json
sps2/governance/attribution.py
sps2/requirements/P5-REQUIREMENTS.json
```

- Edit basis: incomplete; no numbered decision covers the exact group.
- Commit basis: missing and should not be inferred.
- Dependencies: a new numbered decision is required first.
- Known risks: legacy-protection validators may still report modified legacy files; `check_sps2.py` still exits 0.

### R1 — Optional report-preservation group

Proposed subject: `docs(sps2): preserve SPS2 audit and execution reports`

Scope: the 30 existing untracked Markdown reports plus this Round 20 report.

- Commit basis: missing.
- Do not include reports merely because they are untracked.
- Dependencies: preferably after technical groups, so reports describe preserved state.

### Explicit exclusions and holds

| Path / group | Count | Reason |
|---|---|---|
| `.claude/settings.json` | 1 | Provenance unresolved. |
| `.sps/evidence/P17/` | 10 | No commit authorization. |
| `.sps/tasks/p17/` | 76 | No commit authorization; confirm branch ownership. |
| `sps2/decisions/LEGACY-PATH-DEFINITION-DECISIONS.json` | 1 | Pending legacy-path decision. |
| `sps2/decisions/LEGACY-SCOPE-DECISIONS.json` | 1 | Pending legacy-scope decision. |
| `sps2/evidence/P10-EVIDENCE.json` | 1 | Stale wording requires separate decision. |
| Ignored `domain/frontend/**/__pycache__/**` | 7 filesystem files | Test-generated bytecode; excluded from Git-untracked count and proposed commits. |

## 5. Decision register

| ID | Decision | Decide now | Defer consequence |
|---|---|---|---|
| D-20-1 | `.claude/settings.json` treatment and provenance record | Prevents accidental commit of an unexplained mutation. | File remains ambiguous and must stay excluded. |
| D-20-2 | Numbered SPEC-2 ratification/commit record | Makes the security corrections preservable. | SPEC-2 group remains held. |
| D-20-3 | Home/P9 SEO dependency contract | Resolves three SEO failures coherently. | SEO suite remains red for a non-product reason. |
| D-20-4 | `D-P10-*` validator compatibility/migration/acceptance | Makes governance validation status explicit. | Ten known errors remain visible. |
| D-20-5 | Commit authorization per C1/C2/C3/D1/S1/R1 | Preserves authorized work durably. | Work remains vulnerable to worktree loss. |
| D-20-6 | Installer preservation and uninstall safety | Removes high-severity data-loss paths. | High-risk installer behavior remains. |
| D-20-7 | CI permissions, concurrency, SHA pinning, and smoke separation | Reduces supply-chain exposure. | CI remains broadly permissioned and network-dependent. |
| D-20-8 | Stale P10 evidence correction | Removes contradictory governance wording. | Evidence remains stale but unchanged. |

Publication and `user_approval` remain deferred and are not part of any proposed commit.

## 6. Known validation errors and limitations

- `check_sps2.py decision sps2/decisions/P10-DECISIONS.json` prints ten `ERR ... bad decision_id` lines and exits 0.
- `check_sps2.py` exit code is not a failure signal; consumers must inspect stdout.
- SEO has two underlying conflicts producing four test failures.
- `pwsh` is unavailable, so PowerShell runtime behavior remains unverified.
- No full regression suite was rerun in this read-only round; Round 18 results remain the latest broad test evidence, and critical file fingerprints were rechecked.
- The current writer of `.claude/settings.json` cannot be established from local Git evidence.

## 7. Final Git status and side-effect verification

Expected final status remains 16 modified tracked paths and 139 non-ignored untracked paths before this report, with `reports/` still a single untracked directory in porcelain output. The only file created by this round is this report.

No `git add`, `git commit`, `git push`, `git fetch`, `git pull`, `git reset`, `git clean`, `git stash`, `git revert`, `git switch`, deployment, publication, approval, installer, updater, or destructive path was executed. No existing file was modified, moved, deleted, staged, or overwritten.

Stop here and await explicit User decisions.
