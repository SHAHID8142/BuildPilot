# SPS2 ROUND 15 — UPDATER SAFETY + P10 WORKTREE RECONCILIATION

Report time: 2026-10-16T18:03:19+06:00  
Report file: `reports/SPS2-ROUND15-RECONCILIATION-20261016-180319.md`  
Audit mode: strictly read-only except creation of this report.  
HEAD at audit start and before report creation: `c49f3852e1c31d0136269c80fe58201b059af3ec`.

## 1. Executive Summary

The reported updater-safety implementation is substantially present: bootstrap auto-update was removed, Bash dirty/non-Git gates run before network activity, destructive fallbacks are absent from the inspected updater paths, and the Bash mirrors are byte-identical. The safe Bash and static PowerShell checks pass.

However, reconciliation found six verified defects and one high-risk preservation gap:

1. `REQ-P10-07` reconciliation is type-incompatible with the P10 slice schema for nonempty operations: the schema requires operation objects, while the gate extracts strings.
2. `evidence-authenticity` accepts an incomplete `gate_record`; it does not require the documented schema, command, timestamp, tool version, or even one digest claim.
3. Malformed declared backend operations are silently omitted from reconciliation rather than failing closed.
4. The PowerShell updater performs its network check before dirty/non-Git destination refusal; Bash performs those refusals first.
5. Installer replacement of managed global skills is destructive and has no verified backup or restore path; this predates the updater patch and remains within the previously deferred installer global-write workstream.

P10 governance state remains appropriately constrained: publication is still draft, `user_approval` is null, both inventory digests are null, the backend operations manifest is absent, and the real gate exits 1 with `OVERALL: FAIL`. The 308-test P10 gate suite and 85-test frontend suite pass. PowerShell runtime behavior remains unverified because `pwsh` is unavailable.

No source, test, decision, inventory, evidence, CMS, schema, CI, or historical report file was changed by this audit. The only intended working-tree addition is this report.

## 2. Verified Worktree Baseline

### 2.1 Git identity

- Branch: `build/roadmap-p3-completion`
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`
- Upstream: `origin/build/roadmap-p3-completion`
- Initial staged paths: none
- Initial deleted paths: none
- Initial timestamp: `2026-10-16T17:56:37+06:00`

### 2.2 Initial tracked modifications

```text
 M .claude/settings.json
 M .sps/audits/README.md
 M get-sps.ps1
 M get-sps.sh
 M scripts/bootstrap-sps.sh
 M scripts/sps-update.sh
 M scripts/update-sps.ps1
 M skills/sps/scripts/bootstrap-sps.sh
 M skills/sps/scripts/sps-update.sh
 M skills/sps/scripts/update-sps.ps1
 M sps2/decisions/P10-DECISIONS.json
 M sps2/evidence/P5-EVIDENCE.json
 M sps2/governance/attribution.py
 M sps2/requirements/P10-SECTION-INVENTORY.json
 M sps2/requirements/P5-REQUIREMENTS.json
 M sps2/schemas/p10-slice.schema.json
```

### 2.3 Initial untracked inventory

The principal untracked paths were:

```text
 .sps/evidence/P17/
 .sps/tasks/p17/
 AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md
 domain/cms/data/
 domain/frontend/
 reports/
 sps2/decisions/LEGACY-PATH-DEFINITION-DECISIONS.json
 sps2/decisions/LEGACY-SCOPE-DECISIONS.json
 sps2/decisions/P10-DELEGATED-DECISIONS.json
 sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json
 sps2/decisions/P10-ROUND12-USER-DECISIONS.json
 sps2/evidence/P10-EVIDENCE.json
 sps2/project/SLICE-P10-01.json
 sps2/tests/test_p10_runtime_gate.py
 sps2/tests/test_updater_safety.py
 sps2/tools/p10_runtime_gate.py
```

The untracked directories contain the P17 evidence/task files, CMS data, frontend implementation/tests, and historical reports listed by `git ls-files --others --exclude-standard`. No untracked path was deleted, moved, staged, or cleaned.

### 2.4 Round 14 / P10 artifact fingerprints

These SHA-256 values were recorded at audit start and rechecked after all tests. They were identical at both points.

```text
0b6e92d891e30a8daab0c6851ff5534754ca7dc613072dedf93fea3cb109a842  reports/SPS2-ROUND14-GATE-SEMANTICS-IMPLEMENTATION-20261016-174815.md
2e5a4caab32e4d97e43ae150c875b493dfb1b914144efce8f0434abbbb987eb2  sps2/tools/p10_runtime_gate.py
83b63fddea1d89c744c23eae6ecd084af2286f748e0f3f2c4fd84266238cf527  sps2/tests/test_p10_runtime_gate.py
a3d29c3927a6c0bfa8385881c8dc3adfa0cf3dd11bd97f7a83b0fc376b938058  sps2/project/SLICE-P10-01.json
a5c3a5b42bb9395c24fd2ecf1a8b7c0100c10ca68ee33fac5b4387d161897192  sps2/decisions/P10-DECISIONS.json
ed283e21e5259ca273b7b77604fc1769d0467e40eaa3e449ebf081d2d5684576  sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json
5fd70bdbcff7a761913e6c0b2026cf2bed74129bed851dddc8162f16a6fb731c  sps2/decisions/P10-DELEGATED-DECISIONS.json
5d7f8782fbd5212a410697c892571a9f022a3032756ae159eae83ae3cfbd3465  sps2/decisions/P10-ROUND12-USER-DECISIONS.json
c58bcb14f5fed0e7982632f6e96fea93cdd8adf3d23991a75ca7ba1abe3f2dc3  sps2/evidence/P10-EVIDENCE.json
901e78d52ed6b4ee48ccdafc7acce25821aef179b56775fb6e7fbe99bda1ae2e  sps2/requirements/P10-SECTION-INVENTORY.json
713c5df3c6d8c82e579597940e3bd8a61400c46ab7c88a33496d27cffe8ecd69  sps2/schemas/p10-slice.schema.json
```

The expected Round 14 report and both expected Round 14 implementation/test files were present. Because all are untracked, Git cannot establish their prior-round history; the fingerprints establish only that they did not change during this audit.

## 3. Updater-Safety Findings

### 3.1 Verified controls

- `scripts/bootstrap-sps.sh:127-141` and the byte-identical mirror now end after the bootstrap completion message. The former session-start update check and `sps-update.sh --yes` invocation are absent.
- `get-sps.sh:46-75` refuses an unverifiable or dirty Git source, refuses a non-Git destination, checks fetch failure, and relies on `set -euo pipefail` at `get-sps.sh:14` to stop on checkout or clone failure. There is no recursive delete or hard reset.
- `scripts/sps-update.sh:72-87` gates unverifiable, dirty, and non-Git source states before `checker()` and therefore before network activity. Fetch, checkout, and fast-forward pull failures exit without destructive recovery (`scripts/sps-update.sh:118-131`).
- `get-sps.ps1:39-82` checks dirty/non-Git state before fetch, handles fetch/checkout/pull/clone failures, and no longer removes a non-Git destination or hard-resets.
- `scripts/update-sps.ps1:64-99` handles dirty/non-Git states and fetch/checkout/pull/clone failures without destructive fallback.
- `scripts/bootstrap-sps.sh`, `skills/sps/scripts/bootstrap-sps.sh`, `scripts/sps-update.sh`, and `skills/sps/scripts/sps-update.sh` are byte-identical mirror pairs. `scripts/update-sps.ps1` and `skills/sps/scripts/update-sps.ps1` are also byte-identical.
- A repository scan found `sps-update.sh --yes` only in usage comments; no active bootstrap auto-update call remains.

### 3.2 PowerShell ordering defect — VERIFIED DEFECT, Medium

**Finding R15-004.** In `scripts/update-sps.ps1`, `Checker` runs at lines 43-51 before the Git source is inspected at lines 64-75. Therefore a dirty or non-Git destination can trigger a network-dependent update check before the safety refusal. In contrast, `scripts/sps-update.sh:72-94` performs the safety gate before `checker`.

Impact: no source mutation occurs, but the PowerShell updater violates the intended fail-before-network ordering and can perform unnecessary network activity from an unsafe local state. The same ordering applies to a non-Git destination.

Confidence: High, by static control-flow inspection. Runtime PowerShell execution was not possible because `pwsh` is unavailable.

### 3.3 Global installer preservation risk — VERIFIED RISK / NEEDS CLARIFICATION, High

**Finding R15-005.** `install.sh:246-269` removes each managed destination (`rm -rf "$dest_root/sps"` and `"$dest_root/sps-cms"`) before copying the new tree. `install.ps1:165-188` performs the equivalent `Remove-Item -Recurse -Force` before `Copy-Item`. There is no backup, patch, transaction, or restore step.

Consent does exist for direct interactive use (`install.sh:320-325`, `install.ps1:211-214`) and is supplied by updater prompt/`--yes`/`--force` modes. However, `--yes` bypasses the interactive prompt, the previous manifest is overwritten (`install.sh:221-244`, `install.ps1:152-163`), and the install log is truncated (`install.sh:308-309`). If copy fails after removal, user modifications to managed destinations can be unrecoverable.

This is pre-existing and belongs to the explicitly deferred installer global-write workstream. It is not remediated by the updater patch.

### 3.4 Smaller updater gaps

- **R15-006, Low, VERIFIED GAP:** the tests cover four real Bash subprocess failure paths, but PowerShell dirty-tree execution is skipped locally and there are no PowerShell ordering, non-Git, fetch, checkout, pull, or clone failure tests. PowerShell destructive-pattern checks are string-based and can miss equivalent syntax.
- **R15-007, Low, VERIFIED DEFECT:** `get-sps.ps1:77-81` says “destination left unchanged” after clone failure, but Git may create a partial destination directory. The script does not delete it, so the message overstates the guarantee.
- **R15-008, Low, VERIFIED DEFECT:** `scripts/sps-update.sh:136-139` executes `cd "$REPO_DIR"` without an explicit failure check. If that `cd` fails after source update, execution can continue from the caller’s directory and invoke the wrong `./install.sh`. PowerShell uses `Set-Location` under `$ErrorActionPreference = "Stop"`.

## 4. Test Claims and Actual Results

All commands were run from `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`. No installer, updater, bootstrap, CI smoke, dependency install, fetch, pull, or network operation was run.

| Check | Command | Exit | Result |
|---|---|---:|---|
| Bash syntax | `bash -n` for `install.sh`, `uninstall.sh`, `get-sps.sh`, both bootstrap mirrors, and both Bash updater mirrors | 0 each | PASS |
| SPS lint | `bash scripts/lint-sps.sh` | 0 | PASS |
| Script mirror parity | `diff -rq scripts skills/sps/scripts` | 0 | PASS |
| Whitespace | `git diff --check --` on the eight updater scripts and safety test | 0 | PASS |
| Updater safety suite | `PYTHONPATH="$PWD" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v sps2.tests.test_updater_safety` | 0 | 8 tests, 1 skipped (`pwsh` unavailable), 0 failures |
| P10 gate suite | `PYTHONPATH="$PWD" PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest sps2.tests.test_p10_runtime_gate` | 0 | 308 tests, 0 failures |
| Frontend suites | `PYTHONPATH="$PWD" PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v domain.frontend.tests.test_home_render domain.frontend.tests.test_content_slots domain.frontend.tests.test_layout_registry` | 0 | 85 tests, 0 failures |
| Real P10 gate | `PYTHONPATH="$PWD" PYTHONDONTWRITEBYTECODE=1 python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json` | 1 | `OVERALL: FAIL`, as required |
| Governance validators | `python3 -B sps2/tools/check_sps2.py decision ...` for the three P10 decision records | 0 each | PASS |

The full repository suite was not rerun in this round. The worktree contains untracked P10 frontend files and dirty legacy paths that the SEO isolation suite treats as orphan/legacy violations; running it would reproduce environmental isolation failures rather than distinguish product regressions. Focused suites and the real gate were used instead. No test environment was changed to hide that limitation.

## 5. P10 Reconciliation

### 5.1 DEC-7112 semantics

`sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json` contains `DEC-7112`, status `ACTIVE`, approval state `APPROVED`, `decided_by: "User"`, and `decided_at: "2026-10-16"`. The six adopted controls are wired in `run_gate` at `sps2/tools/p10_runtime_gate.py:2530-2548`.

| Control | Evidence | Current assessment |
|---|---|---|
| `evidence-freshness` | `p10_runtime_gate.py:2149-2193` | Implemented as parseable RFC 3339 with offset and no maximum-age window. |
| `evidence-authenticity` | `p10_runtime_gate.py:2196-2283` | Digest cross-check is implemented, but the control is incomplete; see R15-002. |
| `cms-state-digest` | `p10_runtime_gate.py:2286-2315` | Implemented and fails on null/mismatch. Real inventory value remains null, so real gate FAIL is correct. |
| `p8-contract-digest` | `p10_runtime_gate.py:2318-2348` | Implemented and separate from CMS state. Real inventory value remains null, so real gate FAIL is correct. |
| `req-p10-07-reconciliation` | `p10_runtime_gate.py:2351-2405` | Missing manifest fails closed, but nonempty schema/gate type divergence and malformed-entry handling are defects; see R15-001 and R15-003. |
| `approval-state-interaction` | `p10_runtime_gate.py:2408-2470` | Read-only coherence logic is implemented; null approval in the awaiting state passes this control while overall gate remains FAIL. |

### 5.2 Verified gate defects

#### R15-001 — Schema/gate operations type divergence — High

`sps2/schemas/p10-slice.schema.json` defines `state_changing_operations` as an array of objects with required `operation` and `required_controls` fields. The gate at `sps2/tools/p10_runtime_gate.py:2360-2389` instead treats declared operations as strings and builds `declared_ops` with `_nonblank(op)`.

Safe probe using a temporary directory and a schema-conformant declaration:

```text
slice: [{"operation":"save","required_controls":["AUTHENTICATION"]}]
manifest: {"operations":[{"name":"save"}]}
control result: FAIL
detail: manifest operations absent from declaration: ['save']
```

The current Home slice avoids this only because `axis_contracts.backend.state_changing_operations` is `[]` (`sps2/project/SLICE-P10-01.json`). The defect is latent for the first nonempty backend operation.

#### R15-002 — Incomplete gate records accepted — High

`check_evidence_authenticity` only requires `gate_record` to be a dictionary (`p10_runtime_gate.py:2228-2234`). It does not enforce:

- `schema == "sps2.p10-gate-record/v1"`
- `producing_command`
- `utc_timestamp`
- `emitting_tool_version`
- at least one `inputs` or `outputs` claim

Safe probe result:

```text
gate_record: {"inputs":{"artifact.txt":"sha256:<valid>"}}
control result: PASS
```

This contradicts the control’s own detail text and the Round 14 report’s description of the required gate-record fields. It weakens the authenticity control even though the real current evidence still fails because it has no `gate_record`.

#### R15-003 — Malformed declared operations silently ignored — Medium

`p10_runtime_gate.py:2387` filters declared entries with `_nonblank(op)`. A probe containing `["op", "   ", 7]` against a manifest containing `op` returned `PASS`. Malformed entries should fail the reconciliation control rather than disappear from the comparison. The schema should independently reject malformed entries, but the dedicated control should not rely on another control to avoid a fail-open edge case.

### 5.3 Real gate result

The real gate was run read-only against the current Home slice. It exited 1 with:

```text
OVERALL: FAIL
missing_required_controls: []
unknown_controls: []
malformed_results: []
```

Expected failures and blocks:

- `published-only-content`: FAIL — content is `draft`.
- `exposure-declaration`: BLOCKED — no observed bind.
- `slice-id-uniqueness`: FAIL — no authoritative history supplied.
- `evidence-authenticity`: FAIL — `EV-P10-001` has no `gate_record`.
- `approval-authenticity`: FAIL — approval is null.
- `p9-deployment-audit`: BLOCKED — no build directory supplied.
- `cms-state-digest`: FAIL — inventory digest is null.
- `p8-contract-digest`: FAIL — inventory digest is null.
- `req-p10-07-reconciliation`: FAIL — backend operations manifest is absent.

`evidence-freshness`, `inventory-preconditions`, and `approval-state-interaction` pass as narrow controls, but they do not make the overall gate pass.

### 5.4 Governance and publication state

- `sps2/requirements/P10-SECTION-INVENTORY.json` has `inventory_state: COMPLETE_AWAITING_USER_APPROVAL`, `user_approval: null`, `provenance.cms_state_digest: null`, and `provenance.p8_contract_digest: null`.
- `sps2/project/SLICE-P10-01.json` has `acceptance_state: DRAFT` and `user_approval: null`.
- `domain/cms/data/content.json` has the referenced Home content in `draft` status.
- `domain/backend/operations.json` is absent.
- The three P10 decision validators exited 0.
- CMS data remained untracked and unchanged during this audit. Final CMS fingerprints:
  - `content.json`: `c46a001217eb479679109d776c8d2d69b66fb97f4338df8fc5c1b4c42e5c5433`
  - `content_types.json`: `6635ed4d508248477a42ef88eaf39914ed5f5fe86a82a6272153cb0e5ede8855`
  - `revisions.jsonl`: `54a0eeaa274b4a922a822a9f54c3a37b53ce9d3f50861e064300244956eb1762`

### 5.5 P10 governance discrepancy — NEEDS CLARIFICATION, Medium

**Finding R15-009.** `sps2/evidence/P10-EVIDENCE.json` still states that the gate tool and test module are untracked and that no recorded decision authorizes their creation or tracking. The Round 14 report records an explicit User authorization to implement the six gate semantics and identifies those two files as the authorized implementation. The evidence file also says “no P10 implementation exists,” although runtime-gate implementation now exists even though the Home slice/renderer/build does not.

This appears to be stale evidence rather than a new approval defect. It was not changed because this audit is read-only and evidence updates require separate authorization.

### 5.6 Inventory-change attribution — NEEDS CLARIFICATION

**Finding R15-010.** Relative to HEAD, the tracked inventory changed from `INCOMPLETE_PLANNING/complete:false` to `COMPLETE_AWAITING_USER_APPROVAL/complete:true`. The Round 14 report says it changed only the gate and tests and did not change the inventory. Because the working tree was already dirty at audit start and the inventory is modified relative to HEAD, this audit cannot attribute the pre-existing transition to a specific earlier round. It can verify only that the inventory fingerprint did not change during Round 15.

## 6. Findings Ranked by Severity

| ID | Severity | Label | Finding | Confidence |
|---|---|---|---|---|
| R15-001 | High | VERIFIED DEFECT | P10 slice schema and gate disagree on `state_changing_operations` object versus string shape. | High |
| R15-002 | High | VERIFIED DEFECT | `evidence-authenticity` accepts incomplete `gate_record` objects and records with no digest claims. | High |
| R15-005 | High | VERIFIED RISK / NEEDS CLARIFICATION | Managed global skill replacement has no backup or restore path; copy failure after deletion can lose destination changes. | High |
| R15-003 | Medium | VERIFIED DEFECT | Reconciliation silently ignores malformed declared operations. | High |
| R15-004 | Medium | VERIFIED DEFECT | PowerShell updater runs network check before dirty/non-Git refusal. | High |
| R15-009 | Medium | NEEDS CLARIFICATION | P10 evidence contains stale authorization/implementation wording relative to Round 14. | High |
| R15-010 | Medium | NEEDS CLARIFICATION | Inventory state transition is pre-existing relative to this audit; exact originating round cannot be proven from Git alone. | Medium |
| R15-006 | Low | VERIFIED GAP | Updater tests do not cover PowerShell ordering or Git failure injections; PowerShell checks are partly string-based. | High |
| R15-007 | Low | VERIFIED DEFECT | PowerShell clone-failure message overstates “destination left unchanged.” | High |
| R15-008 | Low | VERIFIED DEFECT | Bash updater lacks an explicit `cd "$REPO_DIR"` failure check before reinstall. | High |
| R15-011 | Informational | NOT VERIFIED | PowerShell runtime behavior could not be tested because `pwsh` is unavailable. | High |

## 7. Prioritized Next Steps

These are recommendations only. This audit did not implement fixes.

1. **P0 — Decide the backend operations contract.** Resolve whether `state_changing_operations` should remain schema-defined operation objects or become the gate’s string form. Update the schema, gate, manifest reader, and tests consistently. Requires User authorization because it is normative policy.
2. **P0 — Tighten evidence authenticity.** Require the documented gate-record schema/version, command, parseable UTC timestamp, tool version, and at least one digest claim; add negative fixtures. This is an implementation change requiring separate authorization.
3. **P0 — Make reconciliation fail closed.** Reject malformed declared operations and align manifest/declaration extraction with the decided contract. Requires the same policy decision as R15-001.
4. **P1 — Reorder PowerShell safety.** Move dirty and non-Git source checks before `Checker`, add PowerShell tests where `pwsh` is available, and correct the clone-failure message. Requires implementation authorization.
5. **P1 — Add installer backup/restore.** Under the separately deferred global-write workstream, design verified backups or a transactional replacement for managed skills, manifest, and logs. Requires explicit User authorization.
6. **P2 — Refresh stale P10 evidence.** Ask the User whether to update the evidence record to reflect Round 14 authorization while preserving the distinction that Home slice implementation, publication, and approval remain unauthorized.
7. **P2 — Expand updater tests.** Add failure-path tests for fetch, checkout, pull, clone, PowerShell ordering, non-Git destinations, and interrupted installs without weakening current tests.

## 8. Explicit Authorization Requirements

- No fix was implemented in this round.
- Changing the backend operations representation or reconciliation semantics requires explicit User direction.
- Updating `sps2/evidence/P10-EVIDENCE.json` or any approval/publication state requires explicit User authorization.
- Modifying installer global-write/backup behavior requires explicit User authorization and remains a previously deferred workstream.
- CI changes remain outside this round and require separate authorization.
- Staging, committing, pushing, publishing, and dependency changes were not authorized and did not occur.

## 9. Coordination Notes

The P10 files inspected here are the Round 14 gate artifacts explicitly requested by this audit. No P10 file was edited. Claude’s active Home-slice implementation should treat the three P10 gate defects as reconciliation findings, not as authorization to alter policy, publish content, set approval, or create the backend manifest.

## 10. Commands Executed

Read-only/inspection commands included:

```bash
git status --porcelain=v1 --branch
git rev-parse HEAD
git diff --cached --name-status
git diff --name-status
git ls-files --others --exclude-standard
git log --oneline -12 --decorate --no-abbrev-commit
sha256sum <P10 artifacts and CMS files>
rg/nl/jq/diff/cmp inspections
```

Safe verification commands included those listed in §4 plus two temporary-directory semantic probes. The probes imported the gate module, created files only under `$(mktemp -d)`, and made no repository changes.

Not run: installers, updaters, bootstrap, CI smoke, dependency installation, Git network commands, cleanup, destructive commands, or the full dirty-tree-sensitive suite.

## 11. Final Worktree and Side-Effect Verification

Immediately before creating this report, `git status --porcelain=v1 --branch` remained unchanged from the baseline except that no prior Round 15 report existed. The branch and HEAD were unchanged, no paths were staged, and no tracked/untracked pre-existing path was removed.

The only intended side effect of this audit is creation of this report:

```text
?? reports/SPS2-ROUND15-RECONCILIATION-20261016-180319.md
```

All P10 fingerprints listed in §2.4 were identical before and after testing. No CI, dependency, governance, publication, approval, inventory-digest, or backend-manifest change occurred during this audit.

## 12. Limitations and Unverified Areas

- PowerShell scripts were statically reviewed but not executed because `pwsh` is unavailable.
- Network failure behavior was not exercised because doing so would require network manipulation or installer execution.
- Installer backup/recovery behavior was reviewed statically; no installer was run.
- Full-suite dirty-tree sensitivity was not rerun in this round to avoid conflating pre-existing P10 isolation findings with updater regressions.
- Untracked-file history cannot be proven from Git; fingerprint comparison proves only stability during this audit.
- The audit did not cryptographically authenticate human attribution or evidence authorship; the repository explicitly has no trust root for those claims.
