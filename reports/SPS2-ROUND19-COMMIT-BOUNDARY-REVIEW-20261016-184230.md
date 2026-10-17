# SPS2 ROUND 19 — COMMIT-BOUNDARY REVIEW AND CHANGE PRESERVATION PLAN

Report time: 2026-10-16T18:44:30+06:00 (suffix `20261016-184230`).  
Scope: read-only planning only. This report does **not** stage, commit, push, fetch, pull, reset, clean, stash, revert, publish, approve, or modify application, test, governance, evidence, inventory, CMS, CI, or historical-report files.

## 1. Live baseline

- Branch: `build/roadmap-p3-completion`.
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`.
- Upstream: `origin/build/roadmap-p3-completion`.
- Staged changes: none.
- Stashes: none.
- Tracked modified paths: 16.
- Untracked paths: 137.
- Existing report files before this report: 29. This report is file 30.
- CI diff: none.

The prior Round 18 report exists at
`reports/SPS2-ROUND18-CONSOLIDATION-AND-READINESS-20261016-183724.md`
and was preserved unchanged. Its critical fingerprints match the live files
inspected for this Round 19 plan.

## 2. Preservation manifest

### 2.1 Modified tracked paths

All paths below are `M` in unstaged Git status and are preserved unchanged by this round.

| Path | Classification | Summary | Authorization basis for the edit | Proposed commit |
|---|---|---|---|---|
| `.claude/settings.json` | E | Existing file emptied from 3 JSON lines to 0 bytes. | Uncertain; pre-existing, unrelated to updater or P10 authorization. | HOLD |
| `.sps/audits/README.md` | E | Adds SPEC-2 audit index and KI-15/KI-16 known issues. | Pre-existing SPEC-2 documentation work; no commit authorization identified. | HOLD |
| `get-sps.sh` | A | Removes destructive reset/delete fallbacks; adds dirty/non-Git fail-closed checks. | DEC-7201. | C1 |
| `get-sps.ps1` | A | Same PowerShell safety boundary; removes destructive fallbacks. | DEC-7201. | C1 |
| `scripts/bootstrap-sps.sh` | A | Removes silent auto-update execution. | DEC-7201. | C1 |
| `scripts/sps-update.sh` | A | Adds dirty/non-Git refusal and guarded `cd`; fails closed on fetch/checkout/pull. | DEC-7201. | C1 |
| `scripts/update-sps.ps1` | A | Moves safety checks before network; accurate clone-failure wording; fail-closed Git steps. | DEC-7201. | C1 |
| `skills/sps/scripts/bootstrap-sps.sh` | A | Byte-identical bootstrap mirror. | DEC-7201. | C1 |
| `skills/sps/scripts/sps-update.sh` | A | Byte-identical Bash updater mirror. | DEC-7201. | C1 |
| `skills/sps/scripts/update-sps.ps1` | A | Byte-identical PowerShell updater mirror. | DEC-7201. | C1 |
| `sps2/decisions/P10-DECISIONS.json` | C | Adds D-P10-6 through D-P10-9; updates header wording. | Existing P10 decision records; commit remains unauthorized. | C3 |
| `sps2/evidence/P5-EVIDENCE.json` | E | Adds SPEC-2 factual correction to a P5 verification observation while leaving `PASS` unchanged. | Pre-existing SPEC-2 correction; no commit authorization identified. | HOLD |
| `sps2/governance/attribution.py` | E | Adds malformed/duplicate attribution-token validation. | Pre-existing SPEC-2 governance work; no commit authorization identified. | HOLD |
| `sps2/requirements/P10-SECTION-INVENTORY.json` | C | Adds P10 inventory data and the two DEC-7202-authorized digest values; `user_approval` remains `null`. | P10 planning/decision chain plus DEC-7202. | C3 |
| `sps2/requirements/P5-REQUIREMENTS.json` | E | Adds SPEC-2 correction annotation to P5 verification evidence; state remains unchanged. | Pre-existing SPEC-2 correction; no commit authorization identified. | HOLD |
| `sps2/schemas/p10-slice.schema.json` | C | Adds unique `field_slots` and exact-match semantics per D-P10-9; corrects approval-attribution wording. | D-P10-9 and Round 14/DEC-7112 context. | C3 |

### 2.2 Untracked paths — classified groups

#### A — Ratified updater-safety work

| Path | Status | Authorization | Proposed commit |
|---|---|---|---|
| `sps2/tests/test_updater_safety.py` | Untracked | DEC-7201 explicitly includes this test module. | C1 |

#### B — Authorized P10 gate implementation and tests

| Path | Status | Authorization | Proposed commit |
|---|---|---|---|
| `sps2/tools/p10_runtime_gate.py` | Untracked | Round 14 `GATE-SEMANTICS IMPLEMENTATION: AUTHORIZE`; DEC-7112 contract. | C2 |
| `sps2/tests/test_p10_runtime_gate.py` | Untracked | Round 14 authorization includes the implementation and tests. | C2 |

#### C — P10 slice, decisions, evidence, inventory, and governance records

| Path | Status | Authorization / uncertainty | Proposed commit |
|---|---|---|---|
| `sps2/decisions/P10-DELEGATED-DECISIONS.json` | Untracked | Round 12 decision chain. | C3 |
| `sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json` | Untracked | DEC-7112. | C3 |
| `sps2/decisions/P10-ROUND12-USER-DECISIONS.json` | Untracked | Round 12 User decision transcription. | C3 |
| `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json` | Untracked | DEC-7201/7202/7203. | C3 |
| `sps2/project/SLICE-P10-01.json` | Untracked | Round 12/13 Home-slice planning chain; publication and approval remain deferred. | C3 |
| `sps2/requirements/P10-SECTION-INVENTORY.json` | Tracked modified | D-P10-7/D-P10-8 planning state plus DEC-7202 digest values. | C3 |
| `sps2/schemas/p10-slice.schema.json` | Tracked modified | D-P10-9. | C3 |
| `sps2/decisions/P10-DECISIONS.json` | Tracked modified | D-P10-6 through D-P10-9. | C3 |
| `sps2/evidence/P10-EVIDENCE.json` | Untracked | **HOLD:** stale R15-009 wording remains unresolved and evidence correction requires separate User authorization. | HOLD |

#### D — Frontend renderer, tests, and CMS data

All 18 paths below are untracked. They belong to the Home implementation workstream and are preserved. Commit authorization is separate and not yet granted.

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
domain/frontend/__pycache__/__init__.cpython-314.pyc
domain/frontend/__pycache__/content_slots.cpython-314.pyc
domain/frontend/__pycache__/home_render.cpython-314.pyc
domain/frontend/__pycache__/layout_registry.cpython-314.pyc
domain/frontend/tests/__pycache__/__init__.cpython-314.pyc
domain/frontend/tests/__pycache__/test_content_slots.cpython-314.pyc
domain/frontend/tests/__pycache__/test_layout_registry.cpython-314.pyc
```

The `domain/frontend` group contains 15 files, including 7 test-generated bytecode files; the `domain/cms/data` group contains 3 files. The bytecode files were created by the offline test runs and are preserved because deletion is prohibited. They are **not** proposed for commit; if the User later authorizes a Home implementation commit, the commit boundary should exclude `__pycache__/**` unless the User explicitly chooses otherwise.

#### E — Existing unrelated work or changes with uncertain authorization

| Path / group | Status | Reason held |
|---|---|---|
| `.claude/settings.json` | Tracked modified | Empty-file change has no identified authorization. |
| `.sps/audits/README.md` | Tracked modified | SPEC-2 documentation update has no commit authorization. |
| `.sps/evidence/P17/` (10 files) | Untracked | Existing P17 evidence; no Round 19 authorization to commit. |
| `.sps/tasks/p17/` (117 files) | Untracked | Existing P17 task/evidence records; no Round 19 authorization to commit. |
| `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md` | Untracked | SPEC-2 audit artifact; no commit authorization. |
| `sps2/evidence/P5-EVIDENCE.json` | Tracked modified | SPEC-2 correction; no commit authorization. |
| `sps2/governance/attribution.py` | Tracked modified | SPEC-2 governance hardening; no commit authorization. |
| `sps2/requirements/P5-REQUIREMENTS.json` | Tracked modified | SPEC-2 correction; no commit authorization. |
| `sps2/decisions/LEGACY-PATH-DEFINITION-DECISIONS.json` | Untracked | Existing legacy decision record; no commit authorization. |
| `sps2/decisions/LEGACY-SCOPE-DECISIONS.json` | Untracked | Existing legacy decision record; no commit authorization. |

#### F — Historical and newly generated reports

All 29 pre-existing report files are untracked and preserved. This Round 19 report is newly created. Reports must not be included merely because they are untracked.

```text
reports/CODEX-INDEPENDENT-REPOSITORY-AUDIT-20261016-171338.md
reports/CODEX-SECURITY-HARDENING-PLAN-20261016-172529.md
reports/SPS2-FINAL-AUTHORIZED-EXECUTION-20261016-135200.md
reports/SPS2-FINAL-END-TO-END-READINESS-20261016-091500.md
reports/SPS2-FINAL-EXECUTION-MISSION-20261016-124100.md
reports/SPS2-FINAL-REMEDIATION-20261016-111400.md
reports/SPS2-OVERNIGHT-BUILD-VERIFICATION-20261016-063738.md
reports/SPS2-PHASE2-RELEASE-READINESS-20261016-072628.md
reports/SPS2-PHASE3-DECISION-EXECUTION-20261016-082741.md
reports/SPS2-PHASE3-SAFE-REMEDIATION-20261016-081050.md
reports/SPS2-PHASE4-RELEASE-VERIFICATION-20261016-084449.md
reports/SPS2-READINESS-REMEDIATION-20261016-101600.md
reports/SPS2-ROUND12-EXECUTION-20261016-170620.md
reports/SPS2-ROUND12-P10-DECISION-PACKAGE-20261016-154756.md
reports/SPS2-ROUND13-HOME-IMPLEMENTATION-20261016-171848.md
reports/SPS2-ROUND14-GATE-SEMANTICS-IMPLEMENTATION-20261016-174815.md
reports/SPS2-ROUND15-READ-ONLY-VERIFICATION-20261016-175720.md
reports/SPS2-ROUND15-RECONCILIATION-20261016-180319.md
reports/SPS2-ROUND16-AUTONOMOUS-ENGINEERING-20261016-182330.md
reports/SPS2-ROUND16-RATIFICATION-AND-DIGEST-REGENERATION-20261016-180627.md
reports/SPS2-ROUND17-R15-DEFECT-RESOLUTION-20261016-182229.md
reports/SPS2-ROUND18-CONSOLIDATION-AND-READINESS-20261016-183724.md
reports/SPS2-ROUND6-AUTHORIZED-IMPLEMENTATION-20261016-125200.md
reports/SPS2-ROUND6-EXECUTION-AND-VERIFICATION-20261016-132200.md
reports/SPS2-ROUND7-FINAL-COMMIT-CI-VERIFICATION-20261016-140500.md
reports/SPS2-ROUND8-FINAL-VERIFICATION.md
reports/SPS2-ROUND9-FINAL-CI-VERIFICATION-20261016-151500.md
reports/SPS2-ROUND9-PREFLIGHT-AND-PATCH-PROPOSAL-20261016-145509.md
```

The Round 19 report is:

```text
reports/SPS2-ROUND19-COMMIT-BOUNDARY-REVIEW-20261016-184230.md
```

## 3. Proposed commit boundaries

These are **conditional proposals only**. No staging or commit is authorized by this plan. Each proposed commit requires an explicit User grant for that exact boundary.

### C1 — Updater safety

**Proposed subject:** `SPS2: preserve updater-safety boundaries and regression tests`

Exact files:

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

- Purpose: preserve dirty/non-Git fail-closed behavior, removal of auto-update and destructive fallbacks, accurate clone diagnostics, guarded `cd`, and mirror parity.
- Dependencies: none.
- Authorization supporting edit: DEC-7201.
- Commit authorization: **required separately**.
- Inclusion risk if omitted: safety work remains vulnerable to worktree loss.
- Exclusion risk if included without grant: violates the standing commit prohibition.
- Verification: `python3 -B -m unittest sps2.tests.test_updater_safety`; `bash -n` on the five Bash scripts; `cmp` or `diff -rq scripts skills/sps/scripts`; `git diff --check`.

### C2 — P10 runtime gate and tests

**Proposed subject:** `SPS2: preserve P10 runtime gate semantics and adversarial tests`

Exact files:

```text
sps2/tools/p10_runtime_gate.py
sps2/tests/test_p10_runtime_gate.py
```

- Purpose: preserve the DEC-7112 six-semantics implementation and R15-001/002/003 fail-closed fixes.
- Dependencies: C3 for Governance validators and real-gate context, but C2 can be committed independently if the User chooses.
- Authorization supporting edit: Round 14 and DEC-7112.
- Commit authorization: **required separately**.
- Inclusion risk if omitted: gate implementation/tests remain untracked.
- Exclusion risk if included without grant: violates the standing commit prohibition.
- Verification: `python3 -B -m unittest sps2.tests.test_p10_runtime_gate`; real gate command with expected non-zero exit.

### C3 — P10 planning, governance, schema, and inventory contract

**Proposed subject:** `SPS2: preserve P10 planning contracts and governance decisions`

Exact files:

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

- Purpose: preserve the P10 decision chain, draft slice, planning inventory, authorized digest values, and field-slot schema contract.
- Dependencies: C2 consumes the schema and slice; the real gate depends on inventory and CMS state.
- Authorization supporting edit: P10 decision records D-P10-6 through D-P10-9 and DEC-7202.
- Commit authorization: **required separately**.
- Inclusion risk if omitted: governance and planning contracts remain untracked.
- Exclusion risk if included without grant: violates the standing commit prohibition.
- Verification: supported `check_sps2.py decision` calls; real P10 gate expected to exit non-zero; verify `user_approval` remains `null` and content remains `draft`.

**Not included in C3:** `sps2/evidence/P10-EVIDENCE.json`, because its stale R15-009 wording is an open User decision.

### D1 — Optional future Home implementation group

**Proposed subject:** `SPS2: preserve Home renderer, CMS fixtures, and integration tests`

Exact files:

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

- Purpose: preserve the Home renderer, slot/layout contracts, CMS inputs, and tests.
- Dependencies: C2/C3 improve end-to-end verification, but the suite can run independently.
- Authorization supporting edit: Round 13 Home implementation mission.
- Commit authorization: **required separately**.
- Inclusion risk if omitted: Home implementation remains untracked.
- Exclusion risk if included without grant: violates the standing commit prohibition.
- Verification: frontend and CMS unittest discovery commands; confirm Home Content remains `draft`.

### Explicit holds

| Path / group | Reason |
|---|---|
| `.claude/settings.json` | Unexplained emptying; preserve and await User direction. |
| `.sps/audits/README.md` | SPEC-2 documentation work lacks commit authorization. |
| `.sps/evidence/P17/` | 10 existing P17 evidence files lack commit authorization. |
| `.sps/tasks/p17/` | 117 existing P17 task files lack commit authorization. |
| `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md` | SPEC-2 artifact lacks commit authorization. |
| `sps2/decisions/LEGACY-PATH-DEFINITION-DECISIONS.json` | Legacy governance record lacks commit authorization. |
| `sps2/decisions/LEGACY-SCOPE-DECISIONS.json` | Legacy governance record lacks commit authorization. |
| `sps2/evidence/P5-EVIDENCE.json` | SPEC-2 evidence correction lacks commit authorization. |
| `sps2/evidence/P10-EVIDENCE.json` | Stale wording requires a separate User decision. |
| `sps2/governance/attribution.py` | SPEC-2 governance hardening lacks commit authorization. |
| `sps2/requirements/P5-REQUIREMENTS.json` | SPEC-2 requirement correction lacks commit authorization. |
| All historical reports | Do not include reports merely because they are untracked. |
| Round 19 report | Include only if the User separately authorizes report preservation. |

## 4. Authorization mapping

| Boundary | Edit authorization | Commit authorization |
|---|---|---|
| C1 updater safety | DEC-7201 | Not granted; requires explicit User grant. |
| C2 P10 gate | Round 14 / DEC-7112 | Not granted; requires explicit User grant. |
| C3 P10 planning/governance | D-P10-6..9 and DEC-7202 | Not granted; requires explicit User grant. |
| D1 Home implementation | Round 13 mission | Not granted; requires explicit User grant. |
| SPEC-2 / unrelated files | Not established in reviewed records | Hold. |
| Historical reports | Point-in-time records | Hold unless separately authorized. |

DEC-7201 explicitly states that updater ratification does **not** authorize commit or push. DEC-7203 restates `COMMIT/PUSH: NOT AUTHORIZED` as a standing constraint.

## 5. Safety review

- No unrelated changes are proposed for staging.
- No unauthorized governance transition is proposed.
- `user_approval` remains `null` at `sps2/requirements/P10-SECTION-INVENTORY.json:12`.
- Publication remains deferred; Home Content remains `draft` at `domain/cms/data/content.json:7`.
- Inventory digest values remain exactly the DEC-7202-authorized values.
- No backend manifest is proposed or present.
- No CI file is modified or proposed.
- No push, fetch, pull, deploy, publication, reset, clean, move, delete, or overwrite is proposed.
- No historical decision ID is renamed.
- No stale evidence is corrected in this round.

## 6. Verification results and unresolved risks

Read-only checks run in this planning round:

| Check | Result |
|---|---|
| `git status --porcelain=v1 --branch` | 16 modified tracked paths, 137 untracked paths, no staged paths. |
| `git diff --cached --name-status` | Empty. |
| `git stash list` | Empty. |
| `git diff --check` | Exit 0. |
| `bash -n` on both bootstrap copies, both Bash updater copies, and `get-sps.sh` | Exit 0 for all five. |
| `diff -rq scripts skills/sps/scripts` | Exit 0; mirror parity confirmed. |
| CI path diff (`git diff --name-status -- .github`) | Empty. |
| Critical SHA-256 fingerprint comparison | Matches Round 18 for updater, gate, tests, slice, inventory, evidence, schema, frontend, and CMS files. |

Unresolved risks:

- The working tree contains a large volume of uncommitted authorized work; loss remains possible until the User authorizes preservation.
- `.claude/settings.json` is an empty tracked file with uncertain provenance.
- P10 evidence remains stale and must not be corrected without authorization.
- SPEC-2 changes are real but lack a reviewed commit boundary.
- PowerShell runtime behavior remains unverified because `pwsh` is unavailable.
- SEO isolation tests remain sensitive to the intentionally dirty worktree.

## 7. Explicit Git side-effect statement

No `git add`, `git commit`, `git push`, `git fetch`, `git pull`, `git reset`, `git clean`, `git stash`, `git revert`, `git switch`, or any other Git mutation was performed. No file was staged. No existing modification or untracked file was discarded, moved, reset, cleaned, or overwritten. The only file created by this round is this new report.

Stop here. Do not stage or commit any file until the User explicitly authorizes the exact boundary.
