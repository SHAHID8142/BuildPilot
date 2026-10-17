# SPS2 Round 23 — Governance Decision Package

Timestamp: 2026-10-16 19:43:27 +06:00  
Status: decision package only. No amendment is adopted, implemented, approved, staged, or committed.  
Independent-agent review: none occurred.

## 1. Executive Summary

This package prepares three numbered User decisions:

- **DEC-7301 — Legacy Updater Exception:** a fixed-baseline, blob-pinned exception for exactly the eight DEC-7201 updater files, with the updater test module retained as ratification evidence.
- **DEC-7302 — Home/P9 SEO Dependency:** an exact file/module/symbol exception for the four approved Home-to-P9 import sites, with explicit reconciliation of the P9 rollback contract.
- **DEC-7303 — Historical Decision Identifiers:** narrow compatibility for repository-wide historical `D-P<phase>-*` identifiers, without renaming records or changing validator exit semantics.

The proposed IDs use the next currently unused `73xx` range after DEC-7203. They are proposals, not reservations. The implementation step must recheck the live decision inventory and resolve any concurrent-ID collision before writing records.

All three require explicit User approval. This package does not grant or imply that approval.

## 2. Verified Baseline

- Branch: `build/roadmap-p3-completion`.
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`.
- Upstream delta: `0 0`.
- Staged diff: empty.
- Tracked modified paths at audit start: 20.
- Untracked non-ignored files at audit start: 146.
- Porcelain entries at audit start: 38.
- Round 22 report fingerprint: `c2f7cc0cb37e82c4ddce8248715b5e2234579f3c1752cd08cf800f1d0b7337d5`.

At audit start, the only visible change from Round 22 was one additional untracked Claude test file, `sps2/tests/test_check_update_safety.py`. Before final verification, Claude's Round 21A work also propagated to the mirrored tracked files `skills/sps/scripts/check-update.ps1` and `skills/sps/scripts/check-update.sh`. Those files are preserved and excluded from this package. The final state is recorded in Section 13.

Current focused verification:

```text
domain.seo.tests.test_isolation + updater + P10 gate:
  exit 1; 353 tests; 4 known SEO contract failures; 1 PowerShell skip.

sps2.tests.test_updater_safety:
  exit 0; 13 tests; 12 passed; 1 skipped (pwsh unavailable).

check_sps2.py decision P10-DECISIONS.json:
  exit 0 by existing contract; 10 bad decision_id errors.
```

## 3. Decision Record Envelope

Proposed file when separately authorized:

```text
sps2/decisions/SPS2-ROUND23-CONTRACT-DECISIONS.json
```

Proposed top-level shape:

```json
{
  "schema": "sps2/decision/v1",
  "record_id": "SPS2-ROUND23-CONTRACT-DECISIONS",
  "phase": "cross-cutting governance contracts",
  "generated": "2026-10-16",
  "author": "implementation agent (not a User; transcribes only an explicit User decision when one is received)",
  "decisions": []
}
```

Each decision must conform to `sps2/governance/SCHEMAS/decision.schema.json:6-16`, including `decision_id`, `title`, `decision`, `reason`, `evidence`, `alternatives`, and `approval`. Until the User approves, each record should use:

```json
{
  "approval": {
    "required": true,
    "state": "PENDING_USER_APPROVAL"
  }
}
```

Only after an explicit User act may `state` become `APPROVED`, `decided_by` become exactly `"User"`, and `decided_at`/`basis` record the actual User act. Agents must not self-approve.

## 4. DECISION A — DEC-7301 Legacy Updater Exception

### 4.1 Proposed title

```text
Adopt a fixed-baseline, blob-pinned exception for the eight ratified DEC-7201 updater files
```

### 4.2 Authority and amendments

- **Authority:** explicit User approval only.
- **Builds on:** DEC-7201 at `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json:10-13`, which ratified the eight updater files and test module but did not authorize commit.
- **Amends:** the relevant scope of DEC-0028 at `sps2/decisions/ATTRIBUTION-POLICY-DECISIONS.json:113-115`, which preserved P3/P4 legacy controls unchanged.
- **Amends:** `REQ-P3-08` legacy-path semantics only to the extent needed for the eight pinned updater files.
- **Amends:** `REQ-P9-10` acceptance criterion 3 at `sps2/requirements/P9-REQUIREMENTS.json:350` and the P9 threat-model statement at `sps2/governance/P9-THREAT-MODEL.md:167-172`.
- **Does not amend:** DEC-7203, publication, approval, commit/push authority, CI prohibition, installer-preservation policy, or the updater test module's status as required evidence.

### 4.3 Proposed normative text

> The legacy-preservation controls are amended to recognize exactly eight ratified updater paths, pinned to their Git object IDs at baseline `c49f3852e1c31d0136269c80fe58201b059af3ec`. A legacy checker may treat one of these paths as compliant only when the path appears exactly once in the authoritative exception manifest, its current stage-0 Git blob equals the recorded `expected_blob`, and the path exists as a regular, non-symlink repository file. Every other added, copied, modified, renamed, deleted, untracked, or unreadable legacy path remains a violation. Deleted, missing, duplicated, malformed, or hash-mismatched exception entries fail closed.
>
> The exception is tied to content, not merely filename. Committing the approved files does not erase the exception: checks shall compare against the fixed baseline and pinned blobs, not against mutable `HEAD`. The updater safety test module `sps2/tests/test_updater_safety.py`, SHA-256 `d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b`, is included in the ratification evidence and must accompany the eight files in any authorized C1 commit, but it is not one of the eight legacy-path exceptions.
>
> This amendment preserves DEC-0028's fail-closed intent. It does not create a general updater carve-out, does not permit later edits to the eight files without a new decision and manifest revision, and does not authorize commit, push, installer execution, or CI changes.

### 4.4 Exact exception inventory

| Path | Expected Git blob at current worktree | SHA-256 evidence |
|---|---|---|
| `get-sps.ps1` | `e28977e0ed3231f0e76a45e1bc943c1e7d5798db` | `3b3b084dfcc7efd4e9d36a1b9fa301bc72a4bcfd187e17f258259cc4d69657af` |
| `get-sps.sh` | `29d808d65227f23a22c6e4f56ddb31424c695327` | `3b3e4fcfd7ac6e096a23ee28f598774e9eefcdad7b2b574c27d2c5caf216783f` |
| `scripts/bootstrap-sps.sh` | `2347c0124fbe482068d0ca47d8e933c28db1e6a4` | `8139065418a8e24d0dd4e09d99eb4b3e8e7432f3f4e47115e1470d09fc362b18` |
| `scripts/sps-update.sh` | `585c24a3f7e380feb8237e0a720e6c0cddd461d9` | `ba90bfbfe6f57fd6cdd15712c5f598affb09998f434d5823a0eb31dec9d5fde2` |
| `scripts/update-sps.ps1` | `4054b1679f9fa50b85a4e8911587634fb166a9ce` | `fc207b82ea549c49843249f8d0501e1ca2dfd4a999c4482447cda86c605eb1ad` |
| `skills/sps/scripts/bootstrap-sps.sh` | `2347c0124fbe482068d0ca47d8e933c28db1e6a4` | `8139065418a8e24d0dd4e09d99eb4b3e8e7432f3f4e47115e1470d09fc362b18` |
| `skills/sps/scripts/sps-update.sh` | `585c24a3f7e380feb8237e0a720e6c0cddd461d9` | `ba90bfbfe6f57fd6cdd15712c5f598affb09998f434d5823a0eb31dec9d5fde2` |
| `skills/sps/scripts/update-sps.ps1` | `4054b1679f9fa50b85a4e8911587634fb166a9ce` | `fc207b82ea549c49843249f8d0501e1ca2dfd4a999c4482447cda86c605eb1ad` |

The test evidence is:

```text
sps2/tests/test_updater_safety.py
SHA-256 d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b
```

### 4.5 Exact files and expected changes

When DEC-7301 is approved and implementation is separately authorized:

1. Add `sps2/governance/legacy-exception-manifest.json` with schema `sps2.legacy-exception-manifest/v1`, fixed baseline, exactly eight exceptions, and a separate `related_test_artifacts` entry for the updater test.
2. Add a stdlib-only shared legacy-exception helper or implement the same deterministic algorithm in `domain/seo/isolation.py`.
3. Change `domain/seo/isolation.py:238-267` from `git diff HEAD` to fixed-baseline plus blob-pinned exception checking.
4. Change `domain/seo/tests/test_isolation.py:133-136` to exercise the amended contract.
5. Change `sps2/tools/validate-sps2.sh:208-210` to invoke the shared fail-closed checker.
6. Change `sps2/tools/validate-p3.sh:319-322` and `sps2/tools/validate-p4.sh:497-500` to invoke the same checker while retaining their existing broader pathspecs and baseline `c11da27`.
7. Add `sps2/decisions/SPS2-ROUND23-CONTRACT-DECISIONS.json` with DEC-7301 only after User approval.
8. Update only the affected wording in `REQ-P3-08`, `REQ-P9-10`, and `P9-THREAT-MODEL.md` to cite the exception; do not broaden any other requirement.

No CI workflow is changed.

### 4.6 Manifest contract

The manifest must use `additionalProperties: false` and require:

```text
schema
decision_id
baseline_commit
exceptions
related_test_artifacts
```

Each exception must require:

```text
path
expected_blob
authorization
reason
```

Validation rules:

- `path` is a relative POSIX path inside the repository, rejects `..`, absolute paths, Windows drive forms, null bytes, and symlink resolution outside the root.
- `expected_blob` matches `^[0-9a-f]{40}$`.
- `authorization` is exactly `DEC-7201` for this decision.
- `exceptions` has exactly eight unique paths.
- `related_test_artifacts` may pin the updater test by SHA-256 but grants no legacy-path exception.
- Missing or malformed manifest fails closed.

### 4.7 Required tests

**Positive**

1. The live worktree with the eight exact files and blobs produces zero legacy exceptions.
2. The helper accepts all eight unique paths and valid 40-character blob IDs.
3. The updater test evidence hash matches the manifest.
4. After committing the approved files without changing their content, comparison against fixed baseline still recognizes the exception and passes.

**Negative**

5. Change any approved file after ratification; blob mismatch fails.
6. Delete any approved file; missing stage-0 blob fails.
7. Rename an approved file; both old and new paths fail.
8. Modify a non-allowed legacy path, including Claude's `scripts/check-update.sh`, `scripts/check-update.ps1`, `skills/sps/scripts/check-update.sh`, or `skills/sps/scripts/check-update.ps1`, fails.
9. Add an untracked legacy file; fails.
10. Duplicate a manifest path; fails.
11. Add a ninth exception; fails.
12. Use a path-only exception with no blob; fails.
13. Use a malformed, absolute, traversal, or symlink-escaping path; fails.
14. Use a non-commit or unknown baseline; fails.
15. Remove or corrupt the manifest; fails closed.
16. Remove the updater test from the C1 commit boundary; governance/commit-boundary test fails even though the legacy checker may pass.

**Post-commit regression**

17. Re-run the SEO isolation suite.
18. Re-run `bash sps2/tools/validate-sps2.sh`, `validate-p3.sh`, and `validate-p4.sh`.
19. Verify `git diff <fixed-baseline> -- <eight paths>` remains non-empty and the checker still passes only because blobs match.
20. Verify no check uses `HEAD` as the exception baseline.

### 4.8 Security and governance risks

- Git blob IDs provide worktree tamper evidence but are not signatures and do not authenticate a human.
- A path-only allowlist would permit later code substitution; blob pinning prevents that.
- Fixed baselines accumulate historical scope and must be changed only by a new decision.
- The updater test is untracked today. Its SHA-256 evidence can change before staging; implementation must recompute and stop on mismatch.
- P3/P4 pathspecs are broader than the eight files; reusing the helper must not accidentally allow unrelated paths.

### 4.9 Remains prohibited

- Editing the eight files beyond the ratified blobs without a new User decision.
- Adding any ninth legacy exception.
- Treating commit as approval or staging as ratification.
- Committing or pushing without separate authorization.
- Changing CI, installer policy, publication, approval, or validator exit semantics.
- Deleting, moving, or weakening existing tests to obtain green results.

## 5. DECISION B — DEC-7302 Home/P9 SEO Dependency

### 5.1 Proposed title

```text
Permit the exact ratified P10 Home imports from the P9 SEO engine
```

### 5.2 Authority and amendments

- **Authority:** explicit User approval only.
- **Builds on:** the P10 Home implementation authorization and DEC-7112's six semantics.
- **Amends:** the P9 advisory rollback contract in `REQ-P9-10` at `sps2/requirements/P9-REQUIREMENTS.json:347-353` and `P9-THREAT-MODEL.md:167-172`.
- **Amends:** the orphan-import scanner contract at `domain/seo/isolation.py:198-235` and its zero-orphan test at `domain/seo/tests/test_isolation.py:114-117`.
- **Does not amend:** P9 ownership of SEO, P10 publication, User approval, backend manifest policy, or the prohibition on unrelated `domain.seo` imports.

### 5.3 Proposed normative text

> P10 Home is an approved, owned consumer of the P9 SEO engine at exactly four import sites. The allowed imports are:
>
> 1. `domain/frontend/home_render.py` imports `generate_robots_txt`, `generate_sitemap_from_cms_items`, and `generate_sitemap_xml` from `domain.seo.indexing`;
> 2. `domain/frontend/home_render.py` imports `generate_metadata_from_content` and `render_html_meta_tags` from `domain.seo.metadata`;
> 3. `domain/frontend/home_render.py` imports `RobotsConfig` and `RobotsGroup` from `domain.seo.model`;
> 4. `domain/frontend/tests/test_home_render.py` imports `audit_directory` from `domain.seo.audit`.
>
> Compliance requires an exact resolved `(relative_file, module, imported_symbol)` triple. Unlisted files, modules, symbols, star imports, aliases that change the source symbol, dynamic imports, path-normalization aliases, and symlink escapes remain forbidden. The exception is an owned dependency, not a rollback orphan. Deleting P9 remains a coordinated architectural operation: it necessarily breaks the approved P10 consumer until the P10 dependency is retired or migrated. All other `domain.seo` references outside the P9 surface remain violations.

### 5.4 Exact import inventory

| Relative file | Module | Allowed imported symbols | Current location |
|---|---|---|---|
| `domain/frontend/home_render.py` | `domain.seo.indexing` | `generate_robots_txt`, `generate_sitemap_from_cms_items`, `generate_sitemap_xml` | lines 66-70 |
| `domain/frontend/home_render.py` | `domain.seo.metadata` | `generate_metadata_from_content`, `render_html_meta_tags` | lines 71-74 |
| `domain/frontend/home_render.py` | `domain.seo.model` | `RobotsConfig`, `RobotsGroup` | line 75 |
| `domain/frontend/tests/test_home_render.py` | `domain.seo.audit` | `audit_directory` | line 42 |

### 5.5 Exact files and expected changes

When DEC-7302 is approved and implementation is separately authorized:

1. Add `sps2/governance/p10-p9-import-exceptions.json` with schema `sps2.p10-p9-import-exceptions/v1`, the DEC-7302 ID, fixed baseline, and exactly four exception records.
2. Change `domain/seo/isolation.py:198-235` to load and validate that manifest, resolve paths inside the repository, parse `ast.ImportFrom` names, and compare exact file/module/symbol triples.
3. Change `domain/seo/tests/test_isolation.py:114-127` to add positive, negative, malformed-manifest, and symlink-escape tests.
4. Change `sps2/tools/rollback_seo.py:237-265` so owned P10 dependencies are reported as approved dependencies rather than rollback orphans.
5. Update only the affected rollback wording in `REQ-P9-10` and `P9-THREAT-MODEL.md:167-172`.
6. Add DEC-7302 to the proposed Round 23 decision file only after User approval.

No CI workflow is changed.

### 5.6 Manifest contract

Each of exactly four exception records must require:

```text
file
module
symbols
authorization
```

Rules:

- `file` is a repository-relative POSIX path resolving to an existing regular Python file.
- `module` is exactly one of the four approved P9 modules.
- `symbols` is a non-empty, duplicate-free array of identifiers.
- `authorization` is exactly `DEC-7302`.
- The manifest rejects unknown fields, duplicate records, empty symbol sets, absolute paths, `..`, null bytes, and paths that resolve outside the repository.
- Missing, malformed, or unreadable manifest fails closed.

### 5.7 Required tests

**Positive**

1. The live scanner accepts exactly the four approved sites and symbol sets.
2. `scan_for_orphan_imports` returns no violations for the current Home implementation and test.
3. Rollback status reports four approved owned dependencies and zero unapproved orphans.
4. The manifest accepts exactly four unique `(file, module, symbol-set)` records.

**Negative**

5. Import an unlisted P9 module from any non-P9 file; fails.
6. Import an unlisted symbol from an approved module; fails.
7. Import an approved symbol into an unlisted file; fails.
8. Use `import domain.seo.indexing` instead of the approved `from` import; fails.
9. Use `from domain.seo.indexing import *`; fails.
10. Add a second unlisted symbol to an approved import statement; fails.
11. Rename a source symbol while retaining the local alias; fails.
12. Access the same file through a symlink or normalized alias; fails.
13. Duplicate a file/module/symbol record; fails.
14. Remove or corrupt the manifest; fails closed.
15. Use a path containing `..`, an absolute path, or a null byte; fails.

**Post-commit regression**

16. Run the SEO isolation suite and confirm exactly the approved dependency is recognized.
17. Run the frontend suite to ensure Home behavior is unchanged.
18. Run rollback status/reporting tests and confirm the count distinguishes owned dependencies from orphans.
19. Search for `domain.seo` imports outside P9 and verify only the four approved sites remain.

### 5.8 Alternative rejected as default

Removing P9 imports from Home would preserve literal P9 deletion independence but would require relocating or duplicating metadata, sitemap, robots, and audit behavior. It would increase maintenance risk and contradict the current ownership split. Refactor remains available only if the User decides rollback independence outweighs avoiding duplication.

### 5.9 Security and governance risks

- A module-level allowlist would permit arbitrary symbol expansion; symbol-level pinning prevents that.
- A textual path match alone could be evaded through symlinks; resolution and regular-file checks are required.
- The exception weakens the literal rollback rehearsal unless rollback reporting explicitly models owned consumers.
- The decision must not be read as permission for Home to bypass P9 validation or publication controls.

### 5.10 Remains prohibited

- Any unlisted P10-to-P9 import.
- Importing P9 from unrelated frontend, CMS, backend, or tool modules.
- Redefining P9 ownership or moving SEO policy into P10.
- Claiming P9 can be deleted with zero coordinated impact after the dependency is approved.
- Publishing Home content or setting User approval.

## 6. DECISION C — DEC-7303 Historical Decision Identifiers

### 6.1 Proposed title

```text
Adopt compatibility for historical D-P<phase>-* decision identifiers
```

### 6.2 Authority and amendments

- **Authority:** explicit User approval only.
- **Amends:** `decision_id` pattern in `sps2/governance/SCHEMAS/decision.schema.json:18-21` and `sps2/tools/check_sps2.py:219-233`.
- **Preserves:** every historical identifier and provenance chain; no record is renamed or superseded by this decision.
- **Does not amend:** validator exit semantics, attribution policy, approval identity rules, evidence requirements, or CI wiring.

### 6.3 Proposed normative text

> A valid `decision_id` is either a current identifier matching `^DEC-[0-9]{4}$` or a historical identifier matching `^D-P[0-9]+(?:-[A-Z0-9]+)*$`. Both namespaces remain valid. Historical identifiers retain their original spelling, records, approval provenance, and cross-references; they must not be renamed, renumbered, or silently migrated. New decisions should continue to use `DEC-[0-9]{4}`. Schema and validator must use the same two-pattern contract, and malformed identifiers remain errors. This decision changes identifier syntax only; it does not change whether an approval is valid, who may approve, or the validator's exit-code behavior.

### 6.4 Verified historical namespace

Current validator output reports 40 historical IDs across eight files:

```text
P10-DECISIONS.json                   10
P17-DECISIONS.json                    9
P6-DECISIONS.json                     2
P7-DECISIONS.json                     1
P7-READINESS-DECISIONS.json           4
P8-DECISIONS.json                     1
P9-DECISIONS.json                     6
ROADMAP-P3-DECISIONS.json             7
```

This supports a repository-wide compatibility rule rather than a P10-only exception.

### 6.5 Exact files and expected changes

When DEC-7303 is approved and implementation is separately authorized:

1. Add a named constant in `sps2/tools/check_sps2.py`, for example `DECISION_ID_PATTERN = re.compile(r"^(?:DEC-[0-9]{4}|D-P[0-9]+(?:-[A-Z0-9]+)*)$")`, and use `fullmatch`.
2. Change `sps2/governance/SCHEMAS/decision.schema.json:18-21` to an `anyOf` of the same two anchored patterns.
3. Add tests establishing schema/validator agreement and positive/negative namespace behavior.
4. Add DEC-7303 to the proposed Round 23 decision file only after User approval.
5. Do not change `check_sps2.py` CLI exit behavior or attribution policy.

### 6.6 Required tests

**Positive**

1. `D-P10-1` through `D-P10-9` and `D-P10-APPROVAL` are accepted.
2. Representative IDs from all eight historical files are accepted.
3. `DEC-7201`, `DEC-7202`, and `DEC-7203` remain accepted.
4. Legacy records still require `reason`, `evidence`, and valid approval semantics.
5. The schema pattern set and validator regex accept exactly the same set of representative IDs.

**Negative**

6. Reject empty IDs.
7. Reject lowercase `d-p10-1`.
8. Reject `D-P10-_BAD`, `D-P10--1`, and `D-P10-1-`.
9. Reject phase-less `D-1`.
10. Reject malformed current IDs `DEC-72A1`, `DEC-721`, and `DEC-72011`.
11. Reject duplicate IDs across namespaces.
12. Reject whitespace-padded IDs.
13. Preserve a visible `bad decision_id` error for malformed records.

**Post-commit regression**

14. Run `check_sps2.py decision` over every `sps2/decisions/*.json` file and confirm the 40 historical errors disappear without changing records.
15. Confirm malformed-ID negative tests still fail.
16. Confirm the validator still exits 0 while emitting errors, unless exit semantics are changed by a separate decision.
17. Run the attribution-policy suite to ensure its current `DEC-*` assertions are updated only as explicitly authorized.

### 6.7 Security and governance risks

- Too broad a legacy regex could admit attacker-controlled or meaningless IDs; the proposed pattern is anchored and restrictive.
- Compatibility must not be interpreted as approval validation; approval identity rules remain unchanged.
- JSON Schema and Python regex semantics are not identical for every construct. The proposed alternation is simple, but tests must still compare representative accepted/rejected values and the literal patterns.
- A repository-wide exception may legitimize future use of `D-P*` unless the record states that new decisions should use `DEC-*`.

### 6.8 Remains prohibited

- Renaming or renumbering historical decisions.
- Treating a syntactically valid ID as proof of User approval.
- Changing validator exit semantics in this workstream.
- Changing attribution, approval, evidence, or publication policy.
- Adding CI validators or changing CI configuration.

## 7. Cross-Decision Implementation Order

If all three are approved and implementation is separately authorized:

1. Write the pending decision envelope and verify it structurally.
2. Apply User approval only to decisions actually approved.
3. Implement DEC-7303 independently; it has no dependency on A or B.
4. Implement DEC-7301 legacy exception and fixed-baseline checks.
5. Implement DEC-7302 P10/P9 dependency exception.
6. Run focused and broad offline regression suites.
7. Recheck live Git state and obtain separate commit authorization before staging anything.

## 8. User Decisions Required

1. Approve, reject, or amend DEC-7301.
2. Approve, reject, or amend DEC-7302.
3. Approve, reject, or amend DEC-7303.
4. Separately authorize creation of the decision records.
5. Separately authorize implementation of each decision.
6. Separately authorize staging/commit; approval of a contract is not commit authorization.

## 9. Verification and Evidence

Commands actually run in this round:

| Command | Exit code | Result |
|---|---:|---|
| Git branch/HEAD/status and staged-diff inspection | 0 | Baseline recorded; staged diff empty. |
| `shasum -a 256 reports/SPS2-ROUND22-CONTRACT-RESOLUTION-PLAN-20261016-193213.md` | 0 | Matched Round 22 fingerprint. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v domain.seo.tests.test_isolation sps2.tests.test_updater_safety sps2.tests.test_p10_runtime_gate` | 1 | 353 tests; four known SEO contract failures; one PowerShell skip. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v sps2.tests.test_updater_safety` | 0 | 13 tests; 12 passed; one skipped because `pwsh` is unavailable. |
| `PYTHONDONTWRITEBYTECODE=1 python3 sps2/tools/check_sps2.py decision sps2/decisions/P10-DECISIONS.json` | 0 | 10 `bad decision_id` errors; exit 0 is the existing contract. |
| `git diff --cached --name-status` | 0 | Empty staged diff. |

## 10. Items Intentionally Not Changed

No source, test, schema, decision record, evidence, inventory, settings, CI, validator, report, or generated file was changed. The only intended side effect is this new report.

No decision was created or approved. No staging, commit, push, fetch, pull, deploy, publication, cleanup, reset, stash, revert, branch switch, installer execution, dependency installation, or network access occurred.

## 11. Final Worktree and Side-Effect Verification

At report creation, the staged diff remains empty. All pre-existing tracked modifications, all pre-existing untracked files, and Claude's concurrent work remain preserved. The only new audit artifact is:

```text
reports/SPS2-ROUND23-GOVERNANCE-DECISION-PACKAGE-20261016-194327.md
```

## 12. Limitations

- No independent external agent reviewed this package.
- PowerShell runtime behavior remains unverified because `pwsh` is unavailable.
- Git blob IDs identify repository content but do not authenticate approval identity.
- Proposed IDs and filenames are not reserved until an authorized record is written.
- This package does not authorize implementation, even though it is implementation-ready.

## 13. Concurrent-Change Addendum

After this report was drafted, the live worktree changed again without any action by this audit. Final observed state:

- Tracked modified paths: 22.
- Untracked non-ignored files: 148.
- Porcelain entries: 40.
- Staged diff: empty.

The two additional tracked modifications are Claude's mirrored Round 21A files:

```text
skills/sps/scripts/check-update.ps1
skills/sps/scripts/check-update.sh
```

Their SHA-256 values exactly match their `scripts/` counterparts:

```text
ca00fcea56b182d7c4de0e25203df4a399492658cd557be819f75f8547188002  scripts/check-update.ps1 / skills/sps/scripts/check-update.ps1
f175ed77f54cea9d5eeb9a92177ca0a05592639fa03f1cda3e3ecd4dd4b8043d  scripts/check-update.sh / skills/sps/scripts/check-update.sh
```

The additional untracked files are the new Claude test and this Round 23 report:

```text
sps2/tests/test_check_update_safety.py
reports/SPS2-ROUND23-GOVERNANCE-DECISION-PACKAGE-20261016-194327.md
```

No ownership reconciliation, mirror repair, test run, or file edit was performed on Claude's concurrent work. The proposed DEC-7301 exception remains limited to exactly the eight DEC-7201 updater files and does not cover either check-update mirror.
