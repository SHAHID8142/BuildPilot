# SPS2 Round 24 — Independent Governance Decision Review

Timestamp: 2026-10-16 20:22:54 +06:00  
Mode: read-only review. No decision was approved, adopted, implemented, staged, or committed.  
Reviewed artifact: `reports/SPS2-ROUND23-GOVERNANCE-DECISION-PACKAGE-20261016-194327.md`  
Round 23 fingerprint: `98db6c5f7adff0dea3d4acd8e154fb93ec9c080a8b1aea8f99d1b25755489bfe`  
Independent-agent status: this is an independent Codex review of the Round 23 package, not a separate-agent review.

## 1. Executive Summary

The Round 23 package is directionally sound, but it is not ready for approval as written.

| Proposal | Recommendation | Principal reason |
|---|---|---|
| DEC-7301 Legacy Updater Exception | **AMEND — blocking** | All eight proposed `expected_blob` values are HEAD/index blobs, not the ratified working-tree blobs. The manifest also needs integrity pinning and explicit index/worktree divergence handling. |
| DEC-7302 Home/P9 SEO Dependency | **AMEND — blocking** | The four live import triples are correct, but alias, duplicate-import, syntax-failure, symlink, manifest-integrity, and rollback semantics need precise normative wording. |
| DEC-7303 Historical Decision Identifiers | **AMEND — minor** | The proposed pattern accepts all 77 current IDs, including all 40 historical IDs, and rejects every tested malformed form. It should explicitly make `D-P*` compatibility-only and require schema/validator agreement tests. |

No proposal should be approved until DEC-7301 and DEC-7302 are amended. DEC-7303 is technically sound but should receive the minor normative clarification before adoption.

## 2. Live Baseline and Preservation

At review start and at final verification:

- Branch: `build/roadmap-p3-completion`.
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`.
- Upstream delta: `0 0`.
- Staged diff: empty.
- Tracked modified paths: 22.
- Untracked non-ignored files: 148.
- Porcelain entries: 40.

The concurrent modifications include Claude's Round 21A files:

```text
scripts/check-update.ps1
scripts/check-update.sh
skills/sps/scripts/check-update.ps1
skills/sps/scripts/check-update.sh
sps2/p17/scrub.py
sps2/tests/test_p17_security.py
```

The additional untracked Claude test is:

```text
sps2/tests/test_check_update_safety.py
```

All pre-existing work was preserved. No concurrent file was edited, moved, deleted, staged, or reconciled.

## 3. Review Method

Only read-only inspections and in-memory checks were used:

- Git status, staged-diff, HEAD/index/worktree object, and path inspection.
- `git hash-object` without `-w`.
- SHA-256 inspection.
- Python AST inspection with `PYTHONDONTWRITEBYTECODE=1`.
- In-memory regex testing against the live decision inventory.
- Static inspection of validators, schemas, decisions, requirements, and scanners.

No test suite, installer, updater, validator, network operation, or state-mutating command was run. No bytecode, fixture, temporary repository, or manifest artifact was created.

## 4. DEC-7301 — Legacy Updater Exception

### 4.1 Round 23 claim under review

Round 23 proposed a fixed baseline of `c49f3852e1c31d0136269c80fe58201b059af3ec`, exactly eight updater paths, and the test artifact `sps2/tests/test_updater_safety.py`. It stated that each exception must match a `path` and `expected_blob`.

### 4.2 Verified paths and scope

**VERIFIED.** The eight proposed paths are exactly:

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

They are all tracked, modified relative to HEAD, present as regular files, and not symlinks. The check-update mirrors are not among them:

```text
scripts/check-update.ps1
scripts/check-update.sh
skills/sps/scripts/check-update.ps1
skills/sps/scripts/check-update.sh
```

The proposed manifest's exactly-eight rule, if implemented and tested as written, prevents a ninth path and does not cover the check-update mirrors.

### 4.3 Verified pin defect

**VERIFIED DEFECT.** Round 23 labels the proposed values “Expected Git blob at current worktree,” but every value equals the HEAD/index blob, not the current working-tree blob. Because the staged diff is empty, index and HEAD agree. The working tree contains the ratified DEC-7201 changes.

Correct current working-tree Git blob IDs are:

| Path | Round 23 incorrect pin | Correct worktree blob |
|---|---|---|
| `get-sps.ps1` | `e28977e0ed3231f0e76a45e1bc943c1e7d5798db` | `27bb2cc52957e00ca0d2d2ecac1cd23ba893bcad` |
| `get-sps.sh` | `29d808d65227f23a22c6e4f56ddb31424c695327` | `44cb088d22c4fb030e6535811c8a02c4a8f29e51` |
| `scripts/bootstrap-sps.sh` | `2347c0124fbe482068d0ca47d8e933c28db1e6a4` | `f6c9d1bf0664eed155e1b706b5b64de5463d8c1f` |
| `scripts/sps-update.sh` | `585c24a3f7e380feb8237e0a720e6c0cddd461d9` | `ffe2cf6a149565a7ee7543d9bd9091e3d19bb3f2` |
| `scripts/update-sps.ps1` | `4054b1679f9fa50b85a4e8911587634fb166a9ce` | `74025aaebc098c6ca989dbdcaf50977f7e63ff20` |
| `skills/sps/scripts/bootstrap-sps.sh` | `2347c0124fbe482068d0ca47d8e933c28db1e6a4` | `f6c9d1bf0664eed155e1b706b5b64de5463d8c1f` |
| `skills/sps/scripts/sps-update.sh` | `585c24a3f7e380feb8237e0a720e6c0cddd461d9` | `ffe2cf6a149565a7ee7543d9bd9091e3d19bb3f2` |
| `skills/sps/scripts/update-sps.ps1` | `4054b1679f9fa50b85a4e8911587634fb166a9ce` | `74025aaebc098c6ca989dbdcaf50977f7e63ff20` |

The SHA-256 evidence in Round 23 still matches the live files. No `.gitattributes` filter changes the result: plain and `--path`-based `git hash-object` values agree for all eight files.

### 4.4 Test artifact

**VERIFIED.** `sps2/tests/test_updater_safety.py` remains untracked and its live SHA-256 is:

```text
d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b
```

This matches Round 23. Because it is untracked, it has no Git blob ID yet. The decision may record the current SHA-256 as ratification evidence, but any commit-boundary plan must separately require the file and recompute its identity immediately before staging.

### 4.5 Bypass analysis

**VERIFIED RISKS / REQUIRED AMENDMENTS.**

1. **Index/worktree divergence:** Round 23 says to check the current stage-0 blob. That checks what is staged, not what is executing in the worktree. A malicious worktree edit after staging could evade a stage-0-only check. Conversely, the current legitimate pre-staging state has an old index blob and a ratified worktree blob. The amended contract must define both. A safe rule is: the worktree blob must equal `expected_blob`; the stage-0 blob must equal either `expected_blob` or the fixed baseline blob. Any third index blob fails.
2. **Deleted files:** both stage-0 and worktree checks must fail if the path is absent. A missing stage-0 object and a missing regular file are separate failures.
3. **Symlinks:** `git hash-object` can follow a symlink, while a Git symlink blob stores the link target text. The checker must use `lstat` and reject non-regular files and symlinks before hashing.
4. **Duplicate entries:** the manifest must reject duplicate paths. Round 23 states this, but implementation tests must enforce it.
5. **Baseline changes:** `baseline_commit` must be fixed in the ratified record. A checker must fail if the commit is absent or if the manifest's baseline differs from the decision record.
6. **Manifest tampering:** the manifest is not currently cryptographically bound to the decision record. The decision record must embed the manifest's Git blob ID or SHA-256, and the checker must verify that identity before trusting any exception.
7. **Test-artifact drift:** the SHA-256 is valid now but can change before staging. The decision should require recomputation and fail closed on mismatch.
8. **Ninth-path creep:** the exactly-eight constraint is correct and must be enforced by both schema and runtime checks.

### 4.6 Conflicts with existing governance

**VERIFIED INCOMPLETE AMENDMENT SET.** Round 23 identifies DEC-0028, `REQ-P3-08`, `REQ-P9-10`, and the P9 threat model, but it does not reconcile every standing zero-legacy-diff statement.

At minimum, the User decision must explicitly address:

```text
sps2/decisions/P7-READINESS-DECISIONS.json:45-61  D-P7-C preserves legacy-diff zero
sps2/governance/P7-THREAT-MODEL.md:52-53          legacy diff stays 0
sps2/governance/P7-THREAT-MODEL.md:148            modifying legacy files prohibited
sps2/requirements/P10-REQUIREMENTS.json:14         legacy artefacts forbidden
sps2/tools/validate-p5.py:279-286                  P5 legacy checker
sps2/requirements/P2-REQUIREMENTS.json:199-215     historical evidence claims empty legacy diff
```

The normative P7 and P10 statements require amendment or explicit supersession. The P5 validator must either consume the same exception or remain visibly red by explicit decision. The P2 evidence is historical, but its status after the contract change should be recorded rather than silently ignored.

### 4.7 Required minimum amendments

1. Replace all eight `expected_blob` values with the corrected working-tree blob IDs above.
2. Require the checker to validate the worktree blob and define stage-0 divergence behavior as specified in §4.5.
3. Reject symlinks and non-regular files before hashing.
4. Pin the manifest's Git blob ID or SHA-256 inside DEC-7301 and verify it at runtime.
5. Recompute and match the updater test artifact before any staging or commit action.
6. Amend or explicitly supersede the P7 and P10 legacy-diff statements, and decide the P5 validator's treatment.
7. Keep the exception limited to exactly eight paths and do not include either check-update mirror.

### 4.8 Verdict

**AMEND — blocking.** Do not approve DEC-7301 as written. The concept is sound, but the proposed content pins are wrong and the amendment set is incomplete.

## 5. DEC-7302 — Home/P9 SEO Dependency

### 5.1 Live import verification

**VERIFIED.** AST inspection confirms exactly the four Round 23 import groups:

```text
domain/frontend/home_render.py:66-70
  from domain.seo.indexing import generate_robots_txt,
       generate_sitemap_from_cms_items, generate_sitemap_xml

domain/frontend/home_render.py:71-74
  from domain.seo.metadata import generate_metadata_from_content,
       render_html_meta_tags

domain/frontend/home_render.py:75
  from domain.seo.model import RobotsConfig, RobotsGroup

domain/frontend/tests/test_home_render.py:42
  from domain.seo.audit import audit_directory
```

No live `domain.seo` import was found outside these sites and the P9 surface.

### 5.2 AST and parser risks

**VERIFIED IMPLEMENTATION GAPS.**

1. The current scanner silently ignores Python `SyntaxError` and `OSError` at `domain/seo/isolation.py:87-90`. A malformed file can therefore evade the orphan scan. The amended scanner must fail closed on syntax errors in Python files subject to the scan.
2. The current scanner records module names but not imported symbols at `domain/seo/isolation.py:92-107` and `229-233`. The proposed symbol-level exception therefore requires new AST handling.
3. The rollback scanner has a second implementation at `sps2/tools/rollback_seo.py:192-234` and also silently ignores syntax errors. A shared helper is preferable to maintaining divergent rules.

### 5.3 Alias and duplicate-import analysis

**INFERRED RISK / AMENDMENT REQUIRED.**

Round 23 says “aliases that change the source symbol” remain forbidden, but local aliasing does not change the source symbol. The contract should state explicitly:

- `from domain.seo.indexing import generate_robots_txt as robots` is allowed only because the source symbol `generate_robots_txt` is exact; the local alias is irrelevant.
- `import domain.seo.indexing` and `import domain.seo.indexing as indexing` are forbidden because they expose the whole module rather than an approved symbol.
- `from domain.seo.indexing import *` is forbidden.
- A source symbol may occur at most once per approved file/module, regardless of local alias or statement formatting.
- Dynamic imports, including `__import__` and `importlib.import_module`, are forbidden and must be detected separately from `ast.Import`/`ast.ImportFrom`.

Round 23 calls them “four import sites,” but its manifest records file/module/symbol sets and does not pin line numbers or statement counts. That is acceptable only if the contract is changed from “site” to “file/module symbol set with no duplicate source symbols.” Line pinning would be brittle and is not recommended.

### 5.4 Path, symlink, and normalization risks

**VERIFIED RISK / AMENDMENT REQUIRED.**

The manifest rules require repository-relative paths, regular files, and rejection of traversal and symlink escapes. The implementation must:

1. lexically normalize the manifest path;
2. resolve it against the repository root;
3. use `lstat` to reject symlinks;
4. require a regular file;
5. verify the resolved path remains within the root;
6. compare the canonical relative path, not user-controlled text;
7. reject duplicate manifest records.

The current scanner does not perform these checks. They must be added with the exception.

### 5.5 Manifest integrity

**INFERRED RISK / AMENDMENT REQUIRED.**

As with DEC-7301, the exception manifest must be pinned in the decision record by Git blob ID or SHA-256 and verified before use. Otherwise the decision can be nominally approved while the operative allowlist is later altered.

### 5.6 Rollback semantics

**VERIFIED NORMATIVE CONFLICT.**

`REQ-P9-10` currently says removal of SEO must not break core builds and that rollback rehearsal proves deletion of `domain/seo/` leaves validators passing. The Home renderer imports P9 at module import time, so deleting P9 necessarily breaks Home until the dependency is migrated.

Round 23 correctly calls this a coordinated architectural operation, but the decision text must explicitly amend the P9 criterion. It must state that the approved P10 dependency is not an orphan, while P9 removal is no longer guaranteed to be non-breaking for Home. Otherwise the exception contradicts the existing requirement.

### 5.7 Can the exception coexist with P9 isolation?

**INFERENCE / CONDITIONALLY YES.**

The exception can coexist with P9 isolation if:

- only the four file/module/symbol groups are allowed;
- all other files, modules, symbols, star imports, dynamic imports, duplicates, and aliases are rejected;
- malformed Python fails closed;
- symlinks and traversal are rejected;
- the rollback scanner and isolation scanner share one implementation;
- the manifest is integrity-pinned;
- the P9 rollback requirement is explicitly amended.

Without those safeguards, the exception would weaken unrelated protections.

### 5.8 Required minimum amendments

1. Replace “four import sites” with “four approved file/module/symbol groups.”
2. Define local-alias, module-import, star-import, duplicate-import, and dynamic-import behavior exactly.
3. Require syntax-error fail-closed behavior.
4. Require canonical path, `lstat`, regular-file, and containment checks.
5. Pin the manifest identity in DEC-7302.
6. Use one shared scanner helper for isolation and rollback reporting.
7. Amend `REQ-P9-10` and the P9 threat model to state that P9 removal is coordinated and may break Home until migration.

### 5.9 Verdict

**AMEND — blocking.** The import inventory is correct, but the proposal needs the above precision before approval.

## 6. DEC-7303 — Historical Decision Identifiers

### 6.1 Proposed pattern

Round 23 proposed:

```text
^(?:DEC-[0-9]{4}|D-P[0-9]+(?:-[A-Z0-9]+)*)$
```

### 6.2 Live verification

**VERIFIED.** The repository currently contains 77 unique decision IDs and no duplicate IDs. Of these, 40 use historical `D-P*` forms. The proposed pattern accepts all 77 current IDs, including all 40 historical IDs.

Historical count by file:

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

The following representative malformed IDs were all rejected in memory:

```text
'' 
d-p10-1
D-P10-_BAD
D-P10--1
D-P10-1-
D-1
DEC-72A1
DEC-721
DEC-72011
' DEC-7201'
'DEC-7201 '
'D-P10-1 '
'D-P10-1_'
'D-P10-1*'
```

### 6.3 Schema and validator consistency

**VERIFIED CURRENT STATE.**

- `sps2/governance/SCHEMAS/decision.schema.json:18-21` accepts only `^DEC-[0-9]{4}$`.
- `sps2/tools/check_sps2.py:219-233` accepts only `DEC-\d{4}`.
- `sps2/tools/check_sps2.py:230-232` checks duplicate IDs.
- `sps2/tools/check_sps2.py:272-295` prints errors and exits 0 for validation findings; exit 2 is reserved for usage/kind errors.

**INFERRED RISK.** The proposed schema `anyOf` and Python alternation are simple enough to align, but the implementation must test the literal patterns and representative accepted/rejected values. Pattern equivalence should not be assumed.

### 6.4 Governance impact

**VERIFIED.** The change preserves identifiers and provenance. It does not alter approval identity rules, evidence requirements, or validator exit semantics. It does, however, need a normative statement that `D-P*` is compatibility-only and new decisions must use `DEC-*`.

### 6.5 Required minimum amendments

1. Change “new decisions should continue to use `DEC-[0-9]{4}`” to “new decisions MUST use `DEC-[0-9]{4}`.”
2. State explicitly that `D-P*` is a historical compatibility namespace, not an invitation for new identifiers.
3. Require a schema/validator agreement test.
4. Preserve duplicate-ID rejection across both namespaces.
5. Preserve the existing exit-0-with-ERR-lines contract.

### 6.6 Verdict

**AMEND — minor.** The technical pattern is correct. Apply the small normative clarification before approval.

## 7. Cross-Decision Conflict Matrix

| Proposal | Existing control affected | Status |
|---|---|---|
| DEC-7301 | DEC-0028 preserves P3/P4 legacy controls unchanged | Must be explicitly amended. |
| DEC-7301 | `REQ-P3-08` requires empty legacy diff | Must be explicitly amended. |
| DEC-7301 | `REQ-P9-10` and P9 threat model require legacy diff zero | Must be explicitly amended. |
| DEC-7301 | D-P7-C and P7 threat model preserve legacy-diff zero | Missing from Round 23; must be amended. |
| DEC-7301 | P10 roadmap forbids modifying legacy artefacts | Missing from Round 23; must be amended. |
| DEC-7301 | `validate-p5.py` legacy checker | Missing from Round 23; amend or explicitly leave red. |
| DEC-7301 | P2 evidence claims empty legacy diff | Historical evidence; record treatment explicitly. |
| DEC-7302 | `REQ-P9-10` rollback independence | Must be explicitly amended. |
| DEC-7302 | P9 threat model zero-orphan rollback | Must be explicitly amended. |
| DEC-7303 | Decision schema and validator | Must be amended together. |
| DEC-7303 | Attribution-policy tests using `DEC-*` | Must be updated only as explicitly authorized. |

## 8. Standing Boundaries

All three proposals preserve the following boundaries as drafted:

- no commit or push authorization;
- no CI change;
- no publication;
- no User approval;
- no inventory digest regeneration;
- no backend operations manifest creation;
- no validator exit-semantics change in DEC-7303;
- no renaming of historical decisions;
- no deletion or weakening of tests merely to obtain green results.

Approval of a decision would not authorize implementation, staging, commit, or push. Those remain separate permissions.

## 9. Verification Evidence

| Check | Result |
|---|---|
| Live branch/HEAD/status and staged diff | Verified; staged diff empty. |
| Round 23 report fingerprint | Matches `98db6c5f7adff0dea3d4acd8e154fb93ec9c080a8b1aea8f99d1b25755489bfe`. |
| Eight updater paths | All present, tracked, modified, regular, non-symlink. |
| Round 23 blob pins | All eight equal HEAD/index blobs, not worktree blobs. |
| Correct worktree blobs | Captured with read-only `git hash-object`; plain and `--path` results agree. |
| Updater test artifact | Untracked; SHA-256 matches Round 23. |
| Check-update mirrors | Present in legacy diff and excluded from the proposed eight-path exception. |
| Home/P9 imports | AST confirms exactly the four proposed groups. |
| Current scanners | Both silently ignore syntax errors and do not parse imported symbols. |
| Proposed decision-ID pattern | Accepts all 77 current IDs, including 40 historical IDs. |
| Malformed-ID controls | All 14 tested malformed forms rejected. |
| Duplicate decision IDs | None found across 77 unique IDs. |
| Validator exit semantics | `check_sps2.py` exits 0 after printing ERR lines; usage/kind errors exit 2. |

## 10. Final Recommendations

1. **DEC-7301:** AMEND before User approval. Correct all eight blobs, pin the manifest, define index/worktree policy, and reconcile P7/P10/P5 legacy controls.
2. **DEC-7302:** AMEND before User approval. Tighten symbol, alias, duplicate, syntax, path, manifest, and rollback semantics.
3. **DEC-7303:** AMEND minorly, then approve. Make `D-P*` compatibility-only and require schema/validator agreement tests.

The User may approve DEC-7303 independently after its minor amendment. DEC-7301 and DEC-7302 should not be approved as currently drafted.

## 11. Items Intentionally Not Changed

No source, test, schema, decision, evidence, inventory, settings, CI, validator, report, or generated file was changed. The only intended filesystem change is this new report.

No decision record was created or altered. No decision was approved. No staging, commit, push, fetch, pull, deploy, publication, cleanup, reset, stash, revert, branch switch, installer execution, dependency installation, or network access occurred.

## 12. Final Worktree Verification

At final verification, the staged diff remains empty. The 22 tracked modified paths, 148 untracked non-ignored files, and all concurrent-agent work remain preserved. The only new audit artifact is:

```text
reports/SPS2-ROUND24-INDEPENDENT-GOVERNANCE-REVIEW-20261016-202254.md
```

## 13. Limitations and Unverified Areas

- No external independent agent reviewed this review.
- No test suites or validators were executed in this round, to avoid any possibility of artifact mutation.
- PowerShell runtime behavior remains unverified because `pwsh` is unavailable.
- Git blob IDs provide content identity but do not authenticate human approval.
- The proposed manifests do not yet exist, so their runtime behavior could not be tested.
- The corrected DEC-7301 blob IDs are valid for the current worktree; they must be recomputed immediately before any staging or decision-record creation.
