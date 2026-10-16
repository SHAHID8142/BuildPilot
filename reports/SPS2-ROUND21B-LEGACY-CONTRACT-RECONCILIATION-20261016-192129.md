# SPS2 Round 21B — Legacy Contract Reconciliation & Commit-Readiness Audit

Timestamp: 2026-10-16 19:21:29 +06:00  
Audit class: read-only investigation and resolution planning  
Independent-agent review: none occurred; this report is the result of a second independent Codex investigation, not a separate-agent review.

## 1. Executive Summary

The repository remains on `build/roadmap-p3-completion` at `c49f3852e1c31d0136269c80fe58201b059af3ec`, with no staged changes. The live worktree contains 16 tracked modified paths and 142 untracked non-ignored files grouped into 33 porcelain entries.

The central conflict is normative, not merely a test bug. DEC-7201 ratified the eight updater-safety files and their test module, but DEC-0028 and the SEO isolation contracts preserve legacy-path and rollback-isolation controls. Those controls currently fail because the ratified updater changes touch legacy paths, while the Home renderer deliberately imports `domain.seo`. Committing the updater work would make the `git diff HEAD` controls green without resolving the underlying policy conflict. A User decision must establish precedence and record the contract amendment before commit.

The `D-P10-*` issue is a validator/schema contract mismatch, not a reason to rename historical decisions. The safest near-term option is a narrowly scoped legacy-namespace compatibility rule while preserving provenance.

`.claude/settings.json` remains an unexplained working-tree mutation from the known clean three-line HEAD blob. It must remain held and excluded from commit until the User chooses restore, retain-empty, or untrack. The existing HEAD-blob credential guard remains valuable.

No commit group is technically ready to commit without a separate User commit authorization. C1 and C2 are implementation/test ready but governance-blocked; C3 has governance and identifier-contract blockers; D1 has commit-authorization and SEO-contract blockers.

## 2. Verified Live Baseline

- Branch: `build/roadmap-p3-completion`.
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`.
- Upstream: `0 0` against `origin/build/roadmap-p3-completion`; no local-only or remote-only commits.
- Initial staged diff: empty.
- Initial status counts: 16 tracked modified paths, 142 untracked non-ignored files, 33 porcelain entries when untracked directories are collapsed.
- No stashes were inspected or changed.
- HEAD author is the repository's placeholder governance identity, not evidence of User approval.

### 2.1 Tracked modified paths

```text
.claude/settings.json
.sps/audits/README.md
get-sps.ps1
get-sps.sh
scripts/bootstrap-sps.sh
scripts/sps-update.sh
scripts/update-sps.ps1
skills/sps/scripts/bootstrap-sps.sh
skills/sps/scripts/sps-update.sh
skills/sps/scripts/update-sps.ps1
sps2/decisions/P10-DECISIONS.json
sps2/evidence/P5-EVIDENCE.json
sps2/governance/attribution.py
sps2/requirements/P10-SECTION-INVENTORY.json
sps2/requirements/P5-REQUIREMENTS.json
sps2/schemas/p10-slice.schema.json
```

### 2.2 Untracked group counts

```text
10  .sps/evidence/P17/
117 .sps/tasks/p17/
1   AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md
3   domain/cms/data/
8   domain/frontend/
34  reports/
6   sps2/decisions/
1   sps2/evidence/
1   sps2/project/
2   sps2/tests/
1   sps2/tools/
```

### 2.3 Critical artifact fingerprints

```text
c7f430d94a2ac20a2c5c83afe04300907d8b92d248696902f4f281f694052d20  sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json
ee8ae8bb9742fa52f5a125485d443fceb2fa03f4a3f80e460826297e6ee0143c  sps2/decisions/ATTRIBUTION-POLICY-DECISIONS.json
f8b0041d82ff27a0c5ff8b7129d433159c2ca91c0661088fa34ff623d11bfd62  sps2/decisions/OPEN-DECISION-CLAUDE-SETTINGS.json
d0984c0ddf394ade74cf35296d7363072592bdc89504ece20a56c23a68d35893  sps2/requirements/P10-SECTION-INVENTORY.json
a3d29c3927a6c0bfa8385881c8dc3adfa0cf3dd11bd97f7a83b0fc376b938058  sps2/project/SLICE-P10-01.json
99d55ffb8c8af8f5c002d9165614b5f89171c5e1405d8972d3e938cd718d0e4b  sps2/tools/p10_runtime_gate.py
f585e1b4b8a90780bc9420b6ed35fde90f308ee8bd00f6d4310d5ad1aa46fbd5  sps2/tests/test_p10_runtime_gate.py
d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b  sps2/tests/test_updater_safety.py
854148c6db6d7cbd48e0b69dfe92337077f3d85bd53332644382414ab4ab0bbb  domain/seo/isolation.py
```

Prior report fingerprints matched the referenced files:

```text
fb33142a3f2ce808...  reports/SPS2-ROUND20-AUTHORIZATION-RECONCILIATION-20261016-190200.md
cea6a4495b31339d...  reports/SPS2-ROUND20B-DEEP-SECURITY-RELIABILITY-AUDIT-20261016-191028.md
95fdc7318fbec13f...  reports/SPS2-ROUND19-COMMIT-BOUNDARY-REVIEW-20261016-184230.md
```

## 3. Workstream A — DEC-7201 Versus Legacy-Preservation Contracts

### 3.1 DEC-7201 scope

**VERIFIED.** `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json:10-13` ratifies exactly the eight modified updater files plus `sps2/tests/test_updater_safety.py`. The decision explicitly says ratification authorizes the changes to stand, but not commit or push. The standing constraints at lines 29-32 and DEC-7203 at lines 82-91 preserve publication deferral, null User approval, commit/push prohibition, and CI prohibition.

### 3.2 Legacy-diff-zero conflict

**VERIFIED DEFECT/CONTRACT CONFLICT.**

- `domain/seo/isolation.py:77` defines `LEGACY_DIRECTORIES = ("skills", "scripts", "plugins", "templates")`.
- `domain/seo/isolation.py:238-267` runs `git diff HEAD -- <legacy-directory>` and treats any uncommitted modification as a violation.
- `domain/seo/tests/test_isolation.py:133-136` asserts an empty violation list.
- `sps2/tools/validate-sps2.sh:208-210` independently checks `skills`, `scripts`, `plugins`, `.github`, installer scripts, and uninstallers against HEAD.
- `sps2/tools/validate-p3.sh:319-322` and `sps2/tools/validate-p4.sh:497-500` use broader legacy pathspecs against baseline `c11da27`.

The live updater diff includes:

```text
get-sps.ps1
get-sps.sh
scripts/bootstrap-sps.sh
scripts/sps-update.sh
scripts/update-sps.ps1
skills/sps/scripts/bootstrap-sps.sh
skills/sps/scripts/sps-update.sh
skills/sps/scripts/update-sps.ps1
```

These are exactly the files ratified by DEC-7201. Therefore the current red result is an accurate report of the unresolved conflict, not a false product failure.

`sps2/decisions/ATTRIBUTION-POLICY-DECISIONS.json:113-115` records DEC-0028: the P3/P4 legacy controls are preserved unchanged, no pathspec is narrowed, and residual failures remain red until a separate User decision. That decision remains binding.

### 3.3 Home-to-SEO orphan-import conflict

**VERIFIED DEFECT/CONTRACT CONFLICT.**

- `domain/seo/isolation.py:198-235` scans every Python file outside `domain/seo`, `sps2/tools/seo_audit.py`, and `sps2/tools/rollback_seo.py` for `domain.seo` imports.
- `domain/seo/tests/test_isolation.py:114-117` asserts zero orphan references.
- `domain/frontend/home_render.py:66`, `:71`, and `:75` import `domain.seo.indexing`, `domain.seo.metadata`, and `domain.seo.model`.
- `domain/frontend/tests/test_home_render.py:42` imports `domain.seo.audit`.

This creates four verified orphan-import violations. The ownership boundary appears intentional—P10 Home renders while P9 owns SEO—but the P9 advisory rollback contract says deleting `domain/seo/` should leave no orphaned references. Both can only be true if the contract is amended to recognize the P10 dependency or the renderer is refactored away from P9 SEO.

### 3.4 Recommended smallest contract resolution

**RECOMMENDATION, USER DECISION REQUIRED.**

1. Record a new explicit User decision that establishes precedence for DEC-7201 versus the legacy-diff-zero controls.
2. In the same normative record, enumerate the eight updater files as a ratified legacy-boundary exception, or define a new baseline commit after they are committed.
3. Update the executable checks to consume that explicit allowlist or baseline—not merely `HEAD`—so a later commit cannot silently erase the unresolved policy question.
4. Separately decide whether P10 Home may depend on P9 SEO. If yes, amend the orphan scanner with an explicit, named P10 dependency exception while preserving zero-orphan enforcement for all other consumers. If no, refactor Home to remove the P9 SEO dependency before commit.

This preserves the original controls' fail-closed intent. Do not weaken assertions or delete tests merely to turn them green.

## 4. Workstream B — D-P10 Decision Identifiers

### 4.1 Verified mismatch

**VERIFIED.** `sps2/tools/check_sps2.py:219-233` requires every `decision_id` to match `^DEC-[0-9]{4}$`. The live `sps2/decisions/P10-DECISIONS.json` contains:

```text
D-P10-1
D-P10-2
D-P10-3
D-P10-4
D-P10-5
D-P10-APPROVAL
D-P10-6
D-P10-7
D-P10-8
D-P10-9
```

Running `python3 sps2/tools/check_sps2.py decision sps2/decisions/P10-DECISIONS.json` produced exit code 0 and exactly 10 `bad decision_id` errors. The exit-0 behavior is the validator's existing process contract; it is not a silent pass.

The same validator reports comparable historical namespaces elsewhere, including `D-P17-*`, `D-P6-*`, `D-P7-*`, `D-P8-*`, `D-P9-*`, and `D-P3-*`. This supports classifying the issue as a validator/schema contract mismatch rather than a P10-specific history defect.

### 4.2 Recommended compatibility approach

**RECOMMENDATION, USER DECISION REQUIRED.** Preserve every existing identifier and provenance chain. Do not rename records.

Preferred smallest change: amend the validator and decision schema to accept a documented legacy namespace, such as `^D-P[0-9]+(?:-[A-Z0-9]+)*$` or a narrower P10-specific pattern, in addition to `^DEC-[0-9]{4}$`. Add a negative test for malformed identifiers and a positive test for the accepted legacy namespace.

Alternative governance-clean option: create new `DEC-*` supersession records that reference the historical `D-*` IDs as `supersedes` provenance. This is more schema-consistent but adds governance records and should not be done silently.

Alternative minimal option: an explicit exception registry naming accepted historical IDs. This preserves the records but leaves the broader schema mismatch.

## 5. Workstream C — `.claude/settings.json`

### 5.1 Evidence-supported history

**VERIFIED.**

- HEAD blob is three lines: `{`, `  "enabledPlugins": {}`, `}`.
- Working-tree file is zero bytes.
- Git diff is exactly the removal of those three lines.
- File birth time is 2026-10-04 22:38:43 +06:00; current mutation time is 2026-10-16 15:45:17 +06:00.
- DEC-0024, `sps2/decisions/OPEN-DECISION-CLAUDE-SETTINGS.json:1-26`, records that the file was restored to HEAD on 2026-10-04 under explicit User instruction and that the HEAD-blob credential guard remains permanent.
- `sps2/tools/validate-p4.sh:572-600` checks the committed HEAD blob for credential keys, rather than trusting the mutable working tree.

**NOT VERIFIED.** No repository evidence establishes which process or agent emptied the working-tree file on 2026-10-16. File metadata and absence of a decision record do not establish attribution.

### 5.2 Safe disposition

**RECOMMENDATION, USER DECISION REQUIRED.** Leave the file untouched and exclude it from every proposed commit. The User must choose one of:

1. `git restore .claude/settings.json`—return to the known clean HEAD state.
2. Retain and commit the empty file—only if the harness intentionally cleared it and the User accepts that configuration.
3. Untrack the file—strongest structural protection, but a repository-layout change requiring separate authorization.

Do not infer an authorization from the prior DEC-0024 restore. That decision was satisfied and does not authorize this new mutation.

## 6. Workstream D — Commit-Readiness Reconciliation

### 6.1 Dependency-aware commit-group table

| Group | Purpose | Exact current paths | Authorization basis | Dependencies | Technical readiness | Commit blockers |
|---|---|---|---|---|---|---|
| C1 — Updater safety | Preserve ratified updater safeguards and behavioral tests. | `get-sps.ps1`, `get-sps.sh`, `scripts/bootstrap-sps.sh`, `scripts/sps-update.sh`, `scripts/update-sps.ps1`, `skills/sps/scripts/bootstrap-sps.sh`, `skills/sps/scripts/sps-update.sh`, `skills/sps/scripts/update-sps.ps1`, `sps2/tests/test_updater_safety.py` | DEC-7201 edit/ratification only | Legacy contract amendment needed before meaningful governance validation | Yes: 13-test suite passes; syntax, mirror parity, and whitespace pass | Commit/push not authorized; legacy-contract precedence unresolved |
| C2 — P10 gate implementation | Preserve fail-closed P10 runtime gate and adversarial tests. | `sps2/tools/p10_runtime_gate.py`, `sps2/tests/test_p10_runtime_gate.py` | Round 14 / DEC-7112 edit authorization | Depends on C3 slice/schema/inventory and CMS inputs | Yes: 320 unit tests pass | Commit/push not authorized; real gate legitimately fails pending prerequisites |
| C3 — P10 planning/governance | Preserve P10 decisions, slice, schema, inventory, and authorized digest values. | `sps2/decisions/P10-DECISIONS.json`, `sps2/decisions/P10-DELEGATED-DECISIONS.json`, `sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json`, `sps2/decisions/P10-ROUND12-USER-DECISIONS.json`, `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json`, `sps2/project/SLICE-P10-01.json`, `sps2/requirements/P10-SECTION-INVENTORY.json`, `sps2/schemas/p10-slice.schema.json` | D-P10-6..9, DEC-7202, and P10 authoring records | C2 consumes slice/schema/inventory; CMS data affects real gate | Structurally ready, but governance validation has known errors | Commit/push not authorized; `D-P10-*` validator mismatch unresolved; stale `P10-EVIDENCE.json` is excluded |
| D1 — Home implementation | Preserve Home renderer, layout/slot modules, CMS fixtures, and tests. | `domain/cms/data/content.json`, `domain/cms/data/content_types.json`, `domain/cms/data/revisions.jsonl`, `domain/frontend/__init__.py`, `domain/frontend/content_slots.py`, `domain/frontend/home_render.py`, `domain/frontend/layout_registry.py`, `domain/frontend/tests/__init__.py`, `domain/frontend/tests/test_content_slots.py`, `domain/frontend/tests/test_home_render.py`, `domain/frontend/tests/test_layout_registry.py` | Round 13 Home implementation authorization | Depends on C3 schema/slice and CMS data; SEO contract affects isolation validation | Yes for focused implementation tests; SEO isolation remains red by structural conflict | Commit/push not authorized; P10/P9 dependency contract unresolved |

### 6.2 Files held outside all proposed commits

These paths must be preserved but are not safely assignable to a commit under current evidence:

- `.claude/settings.json`—unexplained emptying; HOLD.
- `.sps/audits/README.md`, `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md`, `sps2/evidence/P5-EVIDENCE.json`, `sps2/governance/attribution.py`, `sps2/requirements/P5-REQUIREMENTS.json`—SPEC-2 work lacks a numbered ratification/commit decision; HOLD.
- `.sps/evidence/P17/` and `.sps/tasks/p17/`—existing P17 work lacks a reviewed commit boundary; HOLD.
- `sps2/decisions/LEGACY-PATH-DEFINITION-DECISIONS.json` and `sps2/decisions/LEGACY-SCOPE-DECISIONS.json`—pending legacy governance decisions; HOLD.
- `sps2/evidence/P10-EVIDENCE.json`—stale wording at lines 5-7 and 23 says no P10 implementation exists, contradicting current files; correction requires a separate User decision.
- All historical and new reports—do not include merely because untracked; require separate report-preservation authorization.
- Generated `__pycache__` files—exclude; preserve without deletion.

### 6.3 Ready versus blocked

**Technically ready but not commit-authorized:** C1 and C2.  
**Technically ready with known governance errors:** C3.  
**Technically ready with unresolved cross-phase contract:** D1.  
**No group is commit-ready in the governance sense.**

## 7. Verification Results

### 7.1 Commands actually executed

| Command | Exit code | Result |
|---|---:|---|
| `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, `git status --porcelain=v1 --branch`, `git diff --cached --name-status` | 0 | Baseline captured above; staged diff empty. |
| `bash sps2/tools/validate-sps2.sh` | 1 | 78 passed, 1 failed, 0 missed; negative suite 27 correctly rejected. The single failure is `legacy modified`. |
| `python3 sps2/tools/check_sps2.py decision sps2/decisions/P10-DECISIONS.json` | 0 | 10 `bad decision_id` errors; process exit remains 0 by existing contract. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v domain.seo.tests.test_isolation` | 1 | 20 tests, 4 failures: live rollback rehearsal, legacy diff zero, orphan references, live status reporting. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v sps2.tests.test_updater_safety` | 0 | 13 tests, 12 passed, 1 skipped because `pwsh` is unavailable. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v sps2.tests.test_p10_runtime_gate` | 0 | 320 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json` | 1 | Real gate overall `FAIL`; five required controls FAIL and two are BLOCKED. |
| `bash -n` on five modified Bash scripts | 0 each | Syntax valid. |
| `diff -u` for Bash and PowerShell mirrors | 0 each | `bootstrap-sps.sh`, `sps-update.sh`, and `update-sps.ps1` mirrors are byte-identical. |
| `git diff --check` | 0 | No whitespace errors. |
| `pytest` | 2 | Not run: Python 3.14 environment has no `pytest` module. `unittest` was used instead. |
| `./sps2/tools/validate-sps2.sh` | 126 | First direct invocation was blocked by the non-executable file mode; rerun with `bash` succeeded as a process. |

### 7.2 Real P10 gate controls

The real gate remains legitimately fail-closed:

```text
PASS    schema-structural
PASS    slice-required-fields
PASS    evidence-references
PASS    layout-slot-conformance
FAIL    published-only-content
BLOCKED exposure-declaration
FAIL    slice-id-uniqueness
PASS    evidence-freshness
FAIL    evidence-authenticity
PASS    inventory-preconditions
FAIL    approval-authenticity
BLOCKED p9-deployment-audit
PASS    cms-state-digest
PASS    p8-contract-digest
FAIL    req-p10-07-reconciliation
PASS    approval-state-interaction
```

The two authorized digest values recompute correctly:

```text
cms_state_digest   sha256:b35f7aba68eca4e7c9b688ae979891330f2f3d08c2b4250ce855c55943f7e38e
p8_contract_digest sha256:ee6bb68f04f0eb468f0fd6eafaaea0b68639b88199e207c7a76ef57e10bbf217
```

Inventory state remains `COMPLETE_AWAITING_USER_APPROVAL`, `user_approval` remains `null`, CMS content remains `draft`, and `domain/backend/operations.json` remains absent.

## 8. Governance and Side-Effect Boundaries

**VERIFIED.**

- No CI file was modified.
- No dependency was installed.
- No network operation, remote query, fetch, pull, push, publication, deploy, or release occurred.
- No installer, updater, bootstrap, cleanup, or destructive path was executed.
- No Git mutation occurred: nothing was staged, committed, reset, cleaned, stashed, reverted, moved, or branch-switched.
- No inventory digest was regenerated.
- No backend operations manifest was created.
- No governance status, approval, or publication state was changed.
- No historical report was modified.

**ENVIRONMENT LIMITATION.** PowerShell runtime behavior remains unverified because `pwsh` is unavailable. The PowerShell source and byte-identical mirror were inspected/statically compared, but not executed.

**NOT REPRODUCED.** No separate-agent review occurred. No external reviewer independently challenged this report.

## 9. User Decisions Required

1. **Legacy/updater contract precedence:** authorize either an explicit eight-file exception or a post-commit baseline amendment. Do not allow `git diff HEAD` to silently resolve the policy conflict.
2. **P10/P9 dependency contract:** decide whether Home may depend on P9 SEO, then authorize the corresponding explicit scanner exception or refactor.
3. **`D-P10-*` identifier contract:** choose legacy-namespace compatibility, governed supersession, or documented exception registry.
4. **`.claude/settings.json`:** choose restore, retain-empty, or untrack.
5. **SPEC-2 numbered ratification and commit boundary:** authorize or reject the five SPEC-2 files as a group.
6. **Per-group commit authorization:** separately authorize C1, C2, C3, and/or D1. Edit ratification does not imply commit authorization.
7. **Installer preservation redesign:** separately authorize the previously designed transactional backup/restore work.
8. **CI hardening:** separately amend the standing CI-change prohibition if SHA pinning, least-privilege permissions, and smoke separation are to be implemented.

## 10. Safe Next Actions Without New Decisions

- Continue read-only reconciliation and evidence mapping.
- Run focused offline suites with bytecode generation disabled when safe.
- Run `bash -n`, mirror diffs, and whitespace checks.
- Inspect validators and schemas without changing them.
- Preserve every current modified and untracked path.
- Await explicit User decisions before any contract edit, commit staging, settings change, evidence correction, identifier migration, CI change, installer redesign, or publication/approval action.

## 11. Final Worktree and Side-Effect Verification

At report creation, the only intended audit side effect is this new file:

`reports/SPS2-ROUND21B-LEGACY-CONTRACT-RECONCILIATION-20261016-192129.md`

The staged diff remained empty. The 16 tracked modified paths and all pre-existing untracked files were preserved. No existing file was edited, moved, deleted, reset, staged, or committed.

## 12. Limitations

- The environment lacks `pytest`, so `unittest` was used for supported focused suites.
- The environment lacks `pwsh`, so PowerShell behavior was not executed.
- Remote state was not queried by instruction; upstream comparison only proves matching local refs.
- No independent external agent reviewed this report.
- No forensic attribution was performed for `.claude/settings.json` because available local evidence cannot establish actor identity.
