# SPS2 Round 25 — Amended Governance Package

Timestamp: 2026-10-16 22:31:01 +06:00  
Status: amended proposals only. No decision was created, approved, implemented, staged, or committed.  
Inputs:

```text
reports/SPS2-ROUND23-GOVERNANCE-DECISION-PACKAGE-20261016-194327.md
  SHA-256 98db6c5f7adff0dea3d4acd8e154fb93ec9c080a8b1aea8f99d1b25755489bfe

reports/SPS2-ROUND24-INDEPENDENT-GOVERNANCE-REVIEW-20261016-202254.md
  SHA-256 5d79e1dd7b4bc754bbbe00535a51d2bb4624247c0663d9ecbac048df1de360da
```

Independent-agent status: this package incorporates the Round 24 review but is not itself a separate-agent review.

## 1. Executive Summary

This package replaces the Round 23 proposals with narrower, fail-closed amendments.

| Proposal | Revised disposition | Key change from Round 23 |
|---|---|---|
| DEC-7301 Legacy Updater Exception | Ready for User decision after review | Correct worktree blobs, file modes, manifest canonical hash, worktree/index policy, and full legacy-checker reconciliation. |
| DEC-7302 Home/P9 SEO Dependency | Ready for User decision after review | Exact file/module/symbol groups, canonical manifest hash, shared scanner, syntax fail-closed, import-form rules, and explicit P9 rollback amendment. |
| DEC-7303 Historical Decision Identifiers | Ready for User decision after review | `D-P*` is historical compatibility-only; new decisions MUST use `DEC-####`; schema/validator agreement and duplicate tests are mandatory. |

DEC-7301, DEC-7302, and DEC-7303 were available at inspection time. They are not reserved. Implementation must recheck availability immediately before record creation.

## 2. Verified Live Baseline

At audit start and final verification:

- Branch: `build/roadmap-p3-completion`.
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`.
- Upstream delta: `0 0`.
- Staged diff: empty.
- Tracked modified paths: 22.
- Untracked non-ignored files: 149.
- Porcelain entries: 40.

Concurrent Claude work remains present, including:

```text
scripts/check-update.ps1
scripts/check-update.sh
skills/sps/scripts/check-update.ps1
skills/sps/scripts/check-update.sh
sps2/p17/scrub.py
sps2/tests/test_p17_security.py
sps2/tests/test_check_update_safety.py
```

All concurrent work was preserved. No existing file was changed.

## 3. Shared Contract Rules

### 3.1 Canonical manifest identity

For DEC-7301 and DEC-7302, the decision record MUST embed the manifest's canonical SHA-256 in its `evidence` array. The decision schema has `additionalProperties: false`, so no new decision field may be added.

Canonical JSON is defined as:

1. UTF-8 encoding;
2. object keys sorted lexicographically;
3. separators `,` and `:`;
4. no insignificant whitespace;
5. `ensure_ascii=false`;
6. no trailing newline;
7. only strings, integers, arrays, and objects—no floats.

The checker MUST parse the manifest, serialize it with these rules, recompute SHA-256, and compare it to the identity embedded in the approved decision. Unknown fields, malformed JSON, missing identity, or hash mismatch fail closed.

### 3.2 Fail-closed defaults

Every missing, unreadable, malformed, duplicate, unexpected, symlinked, outside-root, deleted, hash-mismatched, mode-mismatched, syntax-invalid, or integrity-invalid input fails closed. Silence is never compliance.

### 3.3 Authorization boundaries

Approval of any decision below would authorize only the normative contract. It would not authorize implementation, staging, commit, push, publication, User approval of P10, CI changes, installer redesign, inventory regeneration, backend-manifest creation, or validator exit-semantics changes. Each remains a separate permission.

## 4. DEC-7301 — Legacy Updater Exception

### 4.1 Proposed title

```text
Adopt a content-pinned exception for exactly eight ratified DEC-7201 updater files
```

### 4.2 Authority and amendments

- **Authority:** explicit User approval only.
- **Builds on:** DEC-7201, `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json:10-13`.
- **Amends:** the relevant legacy-diff-zero scope of DEC-0028, `REQ-P3-08`, `REQ-P9-10`, D-P7-C, the P7/P9 threat models, and the P10 roadmap prohibition.
- **Preserves:** DEC-0028's fail-closed intent for every other legacy path.
- **Does not amend:** DEC-7203, commit/push authority, publication, approval, CI prohibition, installer-preservation policy, or validator exit semantics.

### 4.3 Verified exception inventory

Fresh inspection confirms all eight paths are tracked, modified, regular, and non-symlink. The staged diff is empty, so HEAD and index agree. The following are the ratified working-tree identities:

| Path | Git mode | Worktree blob | SHA-256 |
|---|---|---|---|
| `get-sps.ps1` | `100644` | `27bb2cc52957e00ca0d2d2ecac1cd23ba893bcad` | `3b3b084dfcc7efd4e9d36a1b9fa301bc72a4bcfd187e17f258259cc4d69657af` |
| `get-sps.sh` | `100755` | `44cb088d22c4fb030e6535811c8a02c4a8f29e51` | `3b3e4fcfd7ac6e096a23ee28f598774e9eefcdad7b2b574c27d2c5caf216783f` |
| `scripts/bootstrap-sps.sh` | `100755` | `f6c9d1bf0664eed155e1b706b5b64de5463d8c1f` | `8139065418a8e24d0dd4e09d99eb4b3e8e7432f3f4e47115e1470d09fc362b18` |
| `scripts/sps-update.sh` | `100755` | `ffe2cf6a149565a7ee7543d9bd9091e3d19bb3f2` | `ba90bfbfe6f57fd6cdd15712c5f598affb09998f434d5823a0eb31dec9d5fde2` |
| `scripts/update-sps.ps1` | `100644` | `74025aaebc098c6ca989dbdcaf50977f7e63ff20` | `fc207b82ea549c49843249f8d0501e1ca2dfd4a999c4482447cda86c605eb1ad` |
| `skills/sps/scripts/bootstrap-sps.sh` | `100755` | `f6c9d1bf0664eed155e1b706b5b64de5463d8c1f` | `8139065418a8e24d0dd4e09d99eb4b3e8e7432f3f4e47115e1470d09fc362b18` |
| `skills/sps/scripts/sps-update.sh` | `100755` | `ffe2cf6a149565a7ee7543d9bd9091e3d19bb3f2` | `ba90bfbfe6f57fd6cdd15712c5f598affb09998f434d5823a0eb31dec9d5fde2` |
| `skills/sps/scripts/update-sps.ps1` | `100644` | `74025aaebc098c6ca989dbdcaf50977f7e63ff20` | `fc207b82ea549c49843249f8d0501e1ca2dfd4a999c4482447cda86c605eb1ad` |

The updater test evidence remains:

```text
sps2/tests/test_updater_safety.py
SHA-256 d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b
```

This file is untracked and is evidence, not a ninth legacy-path exception.

### 4.4 Proposed manifest identity

Proposed manifest path:

```text
sps2/governance/legacy-exception-manifest.json
```

Proposed schema name:

```text
sps2.legacy-exception-manifest/v1
```

The manifest MUST contain exactly:

```text
schema
decision_id
baseline_commit
exception_count
exceptions
related_test_artifacts
explicitly_excluded_paths
```

It MUST contain exactly eight exception records. Each record MUST contain exactly:

```text
path
expected_blob
expected_mode
sha256
authorization
reason
```

The four check-update mirrors MUST be listed only under `explicitly_excluded_paths`:

```text
scripts/check-update.ps1
scripts/check-update.sh
skills/sps/scripts/check-update.ps1
skills/sps/scripts/check-update.sh
```

Using the canonicalization rules in §3.1, the proposed manifest identity is:

```text
sha256:6daa14045f3f6759782c77ffff89ca93edc2a22a3a2095aff30174cf7ca5fe36
```

This identity is computed from the proposed manifest object, not from an existing file. No manifest exists yet. Implementation MUST create the exact object, recompute its canonical hash, and fail if it differs.

### 4.5 Proposed normative text

> DEC-7301 authorizes a content-pinned exception for exactly the eight updater paths and modes listed in the manifest whose canonical SHA-256 is `sha256:6daa14045f3f6759782c77ffff89ca93edc2a22a3a2095aff30174cf7ca5fe36`. The authority baseline is `c49f3852e1c31d0136269c80fe58201b059af3ec`.
>
> A path is exempt only when all of the following are true: the manifest is present, parseable, and hash-verified; the path appears exactly once; the path is repository-relative and resolves inside the root; `lstat` shows a regular file and not a symlink; its worktree Git blob and SHA-256 equal the manifest values; its Git file mode equals the manifest mode; and its stage-0 blob equals either the authority baseline blob or the expected worktree blob. A stage-0 blob with any third value fails.
>
> A missing worktree file, missing stage-0 entry, deletion, rename, type change, mode change, content change, untracked replacement, duplicate manifest entry, ninth exception, or check-update mirror modification fails. Legacy checkers SHALL NOT use mutable `HEAD` as the compliance test. They may retain their own historical enumeration baselines, including `c11da27`, but compliance for an exception is determined by pinned content.
>
> This decision narrowly amends the legacy-diff-zero invariant for the eight pinned files only. It does not permit later edits to those files, does not cover any other legacy path, and does not convert a commit into approval.

### 4.6 Worktree/index/baseline behavior

For each exception:

1. Obtain the worktree blob with `git hash-object --path <path> <path>` after `lstat` confirms a regular file.
2. Obtain the stage-0 blob with `git rev-parse :<path>`.
3. Obtain the authority baseline blob with `git rev-parse <baseline>:<path>`.
4. Require worktree blob == `expected_blob`.
5. Require SHA-256 == manifest `sha256`.
6. Require Git mode == `expected_mode`.
7. Require stage-0 blob ∈ {authority baseline blob, expected_blob}.
8. Require the path to appear as modified, not deleted, type-changed, or renamed, in the checker's historical diff enumeration.

For `validate-sps2.sh`, the checker may use authority baseline `c49f3852e1c31d0136269c80fe58201b059af3ec`. For P2, P3, P4, and P5, the checker may retain `c11da27` as its enumeration baseline while applying the same content exception. This preserves each control's historical scope instead of silently replacing it with `HEAD`.

### 4.7 Exact files and expected changes

Implementation would require separate authorization and would affect:

```text
sps2/decisions/SPS2-ROUND23-CONTRACT-DECISIONS.json
sps2/governance/legacy-exception-manifest.json
sps2/governance/legacy_exceptions.py
domain/seo/isolation.py
domain/seo/tests/test_isolation.py
sps2/tools/validate-sps2.sh
sps2/tools/validate-p2.sh
sps2/tools/validate-p3.sh
sps2/tools/validate-p4.sh
sps2/tools/validate-p5.py
sps2/requirements/P3-REQUIREMENTS.json
sps2/requirements/P9-REQUIREMENTS.json
sps2/requirements/P10-REQUIREMENTS.json
sps2/governance/P7-THREAT-MODEL.md
sps2/governance/P9-THREAT-MODEL.md
```

Historical D-P7-C itself MUST NOT be rewritten. DEC-7301 shall explicitly supersede only its legacy-diff-zero scope to the minimum extent needed for the eight pinned files.

Historical P2 evidence at `sps2/requirements/P2-REQUIREMENTS.json:199-215` MUST NOT be edited. It remains a point-in-time evidence claim, not a live assertion.

The `.sps/tools/validate-control.sh` and `.sps/tools/validate-capability.sh` probes inspect `install.sh` and unrelated skill files, not the eight updater paths. They MUST NOT be changed by this decision.

### 4.8 Required tests

**Positive**

1. The live eight files and modes match the manifest.
2. The manifest canonical hash matches DEC-7301.
3. The updater test SHA-256 matches.
4. Before staging, stage-0 equals the authority baseline and worktree equals the exception.
5. After staging the ratified content, stage-0 equals the exception and the checker still passes.
6. After committing the ratified content, fixed-baseline comparison still recognizes the exception.

**Negative**

7. Any worktree content change fails.
8. Any mode change fails.
9. Any deletion fails.
10. Any rename fails.
11. Any type change or symlink fails.
12. Any stage-0 blob other than baseline or expected fails.
13. Any non-allowed legacy path fails, including all four check-update mirrors.
14. A ninth exception fails.
15. Duplicate manifest paths fail.
16. Missing, malformed, or hash-mismatched manifest fails.
17. Unknown manifest fields fail.
18. Missing or changed baseline fails.
19. Missing or changed updater test artifact fails the commit-boundary check.
20. Removal of any negative test causes the governance mutation test to fail.

**Post-commit regression**

21. Re-run the shared helper tests.
22. Re-run `bash sps2/tools/validate-sps2.sh`, `validate-p2.sh`, `validate-p3.sh`, `validate-p4.sh`, and `python3 sps2/tools/validate-p5.py`.
23. Verify `git diff <authority baseline> -- <eight paths>` remains non-empty while the checker passes only because content is pinned.
24. Verify no amended checker uses mutable `HEAD` as the final compliance test.

### 4.9 Security and governance risks

- Git blobs and SHA-256 provide integrity, not human authentication.
- Manifest identity binding prevents silent allowlist expansion.
- Mode pinning prevents executable-bit or type changes from hiding behind content equality.
- Index-only checking would miss worktree edits; worktree-only checking would miss staged divergence. Both are required.
- Broad path-only exceptions would be unsafe and remain prohibited.

### 4.10 Remains prohibited

- Editing any of the eight files beyond the pinned blobs without a new decision.
- Adding a ninth exception.
- Covering either check-update mirror.
- Committing, pushing, publishing, or changing CI.
- Rewriting historical D-P7-C or P2 evidence.
- Weakening or deleting tests.

## 5. DEC-7302 — Home/P9 SEO Dependency

### 5.1 Proposed title

```text
Permit exactly four pinned P10 Home imports from the P9 SEO engine
```

### 5.2 Authority and amendments

- **Authority:** explicit User approval only.
- **Amends:** the P9 advisory rollback contract in `REQ-P9-10` and `P9-THREAT-MODEL.md`.
- **Amends:** the orphan-import scanner contract and rollback scanner behavior.
- **Preserves:** P9 ownership of SEO and rejection of every unrelated P9 consumer.

### 5.3 Verified import groups

AST inspection confirms exactly these four groups and no other live `domain.seo` imports outside the P9 surface:

| File | Module | Allowed source symbols |
|---|---|---|
| `domain/frontend/home_render.py` | `domain.seo.indexing` | `generate_robots_txt`, `generate_sitemap_from_cms_items`, `generate_sitemap_xml` |
| `domain/frontend/home_render.py` | `domain.seo.metadata` | `generate_metadata_from_content`, `render_html_meta_tags` |
| `domain/frontend/home_render.py` | `domain.seo.model` | `RobotsConfig`, `RobotsGroup` |
| `domain/frontend/tests/test_home_render.py` | `domain.seo.audit` | `audit_directory` |

No dynamic `__import__` or `importlib.import_module` call was found in either file.

### 5.4 Proposed manifest identity

Proposed manifest path:

```text
sps2/governance/p10-p9-import-exception-manifest.json
```

Proposed schema name:

```text
sps2.p10-p9-import-exception-manifest/v1
```

The manifest MUST contain exactly:

```text
schema
decision_id
baseline_commit
exception_count
exceptions
forbidden_import_forms
```

It MUST contain exactly four exception records. Each record MUST contain exactly:

```text
file
module
symbols
authorization
```

Using the canonicalization rules in §3.1, the proposed manifest identity is:

```text
sha256:71d7830ab6748f7c6755d0657f24b0a2075e170c48ba5a6890909a8c46f7ca49
```

No manifest exists yet. Implementation MUST create the exact object and verify this hash.

### 5.5 Proposed normative text

> DEC-7302 permits P10 Home to consume the P9 SEO engine only through the four file/module/symbol groups in the manifest whose canonical SHA-256 is `sha256:71d7830ab6748f7c6755d0657f24b0a2075e170c48ba5a6890909a8c46f7ca49`.
>
> A compliant import is an `ast.ImportFrom` whose canonical source file, source module, and imported source symbol exactly match one allowed triple. A local alias such as `from domain.seo.model import RobotsConfig as Config` is allowed only because source symbol `RobotsConfig` is approved. The following remain forbidden: `import domain.seo.*`, aliased module imports, star imports, unlisted files, unlisted modules, unlisted symbols, duplicate source symbols in the same file/module, dynamic imports, syntax-invalid files, symlinked files, path traversal, and paths outside the repository root.
>
> This is an owned P10 dependency, not a rollback orphan. P9 removal is therefore a coordinated architectural operation and is no longer guaranteed to leave Home buildable until the P10 dependency is retired or migrated. Every other `domain.seo` reference outside the P9 surface remains forbidden.

### 5.6 Scanner requirements

Implementation MUST replace the divergent scanner logic with one shared stdlib helper used by:

```text
domain/seo/isolation.py
sps2/tools/rollback_seo.py
```

The helper MUST:

1. parse and hash-verify the manifest;
2. lexically normalize each manifest path;
3. resolve it against the repository root;
4. use `lstat`, reject symlinks, require a regular file, and enforce containment;
5. parse Python with `ast.parse`;
6. fail closed on `SyntaxError`, `OSError`, `ValueError`, and `RecursionError`;
7. collect exact source symbols from `ast.ImportFrom`;
8. reject module imports, star imports, duplicate source symbols, and dynamic imports;
9. report approved dependencies separately from unapproved orphans;
10. reject duplicate manifest records and unknown fields.

Line numbers are diagnostic only; they MUST NOT be part of the compliance match.

### 5.7 Exact files and expected changes

Implementation would require separate authorization and would affect:

```text
sps2/decisions/SPS2-ROUND23-CONTRACT-DECISIONS.json
sps2/governance/p10-p9-import-exception-manifest.json
sps2/governance/import_exceptions.py
domain/seo/isolation.py
domain/seo/tests/test_isolation.py
sps2/tools/rollback_seo.py
sps2/requirements/P9-REQUIREMENTS.json
sps2/governance/P9-THREAT-MODEL.md
```

No CI workflow is changed.

### 5.8 Required tests

**Positive**

1. The live scanner accepts exactly the four approved file/module/symbol groups.
2. Local aliases of approved source symbols are accepted.
3. Rollback status reports four approved dependencies and zero unapproved orphans.
4. The manifest canonical hash matches DEC-7302.

**Negative**

5. Unlisted file fails.
6. Unlisted module fails.
7. Unlisted symbol fails.
8. Module import fails.
9. Aliased module import fails.
10. Star import fails.
11. Duplicate source symbol fails.
12. Dynamic `__import__` fails.
13. Dynamic `importlib.import_module` fails.
14. Symlinked file fails.
15. Path traversal fails.
16. Outside-root path fails.
17. Syntax error fails closed.
18. Duplicate manifest record fails.
19. Unknown manifest field fails.
20. Missing or hash-mismatched manifest fails.
21. Unapproved P9 import in any unrelated module fails.

**Post-commit regression**

22. Run the shared scanner tests.
23. Run the SEO isolation suite.
24. Run the Home renderer suite.
25. Run rollback status/reporting tests.
26. Search for `domain.seo` imports outside P9 and verify only the approved groups remain.

### 5.9 Security and governance risks

- Symbol-level matching prevents module-wide access.
- Duplicate-source-symbol rejection prevents incremental expansion of an approved import.
- Syntax fail-closed prevents malformed files from evading inspection.
- Shared scanner logic prevents isolation and rollback rules from diverging.
- Manifest identity binding prevents decision text and operative allowlist from drifting.

### 5.10 Remains prohibited

- Any unlisted P9 import.
- Moving SEO policy into P10.
- Claiming P9 deletion is non-breaking for Home after this dependency is approved.
- Publishing Home content or setting User approval.

## 6. DEC-7303 — Historical Decision Identifiers

### 6.1 Proposed title

```text
Adopt historical compatibility for D-P<phase>-* decision identifiers
```

### 6.2 Availability and current state

Fresh inspection found 77 unique decision IDs and no duplicates. DEC-7301, DEC-7302, and DEC-7303 are available. No `DEC-73xx` ID currently exists.

The proposed pattern is:

```text
^(?:DEC-[0-9]{4}|D-P[0-9]+(?:-[A-Z0-9]+)*)$
```

It accepts all 77 current IDs, including all 40 historical `D-P*` IDs, and rejects every malformed representative tested in Round 24.

### 6.3 Proposed normative text

> A valid `decision_id` is either a current identifier matching `^DEC-[0-9]{4}$` or a historical identifier matching `^D-P[0-9]+(?:-[A-Z0-9]+)*$`. The `D-P*` namespace is historical compatibility only. Every new decision MUST use `DEC-####`. Historical identifiers retain their original spelling, records, approval provenance, and cross-references and MUST NOT be renamed or renumbered.
>
> The JSON Schema and validator MUST enforce the same two-pattern contract. Duplicate decision IDs remain errors across both namespaces. A syntactically valid identifier never proves User approval. This decision changes identifier syntax only and does not change validator exit behavior, attribution policy, approval rules, or evidence requirements.

### 6.4 Exact files and expected changes

Implementation would require separate authorization and would affect:

```text
sps2/decisions/SPS2-ROUND23-CONTRACT-DECISIONS.json
sps2/tools/check_sps2.py
sps2/tools/check_p3.py
sps2/governance/SCHEMAS/decision.schema.json
sps2/tests/test_attribution_policy.py
```

The shared pattern SHOULD be centralized or tested for literal equality across consumers. `check_sps2.py` and `check_p3.py` currently duplicate the `DEC-\d{4}` rule, so both must be reconciled.

### 6.5 Required tests

**Positive**

1. All 40 current historical IDs are accepted.
2. All current `DEC-####` IDs remain accepted.
3. Legacy records still require valid reason, evidence, and approval semantics.
4. Schema and validator accept the same representative positive set.

**Negative**

5. Empty ID fails.
6. Lowercase `d-p10-1` fails.
7. `D-P10-_BAD`, `D-P10--1`, and `D-P10-1-` fail.
8. Phase-less `D-1` fails.
9. `DEC-72A1`, `DEC-721`, and `DEC-72011` fail.
10. Whitespace-padded IDs fail.
11. Duplicate IDs fail across namespaces.
12. A malformed ID still emits a visible `bad decision_id` error.

**Post-commit regression**

13. Run `check_sps2.py decision` over every decision file and confirm the 40 historical errors disappear without changing records.
14. Run `check_p3.py` decision checks.
15. Run attribution-policy tests.
16. Confirm malformed-ID tests still fail.
17. Confirm `check_sps2.py` still exits 0 after printing ERR lines and exits 2 only for usage/kind errors.

### 6.6 Risks

- A broader legacy regex would weaken identifier integrity; the proposed pattern is anchored and restrictive.
- Pattern equivalence between JSON Schema and Python must be tested, not assumed.
- Compatibility must not be interpreted as approval validity.

### 6.7 Remains prohibited

- Renaming historical IDs.
- Creating new `D-P*` IDs.
- Changing validator exit semantics.
- Changing attribution, approval, evidence, publication, or CI policy.

## 7. Normative Amendments Versus Implementation

### 7.1 Normative amendments requiring User approval

- DEC-7301 narrows legacy-diff-zero for exactly eight content-pinned updater files.
- DEC-7301 explicitly supersedes the conflicting scope of D-P7-C without rewriting that historical record.
- DEC-7302 reclassifies the four Home imports as owned dependencies and amends P9 rollback independence for Home.
- DEC-7303 admits historical `D-P*` identifiers as compatibility-only and mandates `DEC-####` for new decisions.

### 7.2 Implementation requirements after separate authorization

- Create the exact manifests and verify canonical hashes.
- Implement the shared legacy and import scanners.
- Amend only the validators and normative documents listed above.
- Add all positive, negative, integrity, and post-commit tests.
- Recheck decision-ID availability and file identities immediately before implementation.

### 7.3 Future authorization boundaries

Separate User authorization remains required for:

1. creating decision records;
2. implementing each decision;
3. staging or committing any group;
4. pushing;
5. publication;
6. P10 User approval;
7. CI changes;
8. installer preservation redesign;
9. inventory digest regeneration;
10. backend operations manifest creation;
11. validator exit-semantics changes.

## 8. Unresolved Policy Choices

1. **P5 legacy checker treatment:** DEC-7301 lists `validate-p5.py` for amendment so the same exception applies consistently. The User may instead choose to leave P5 visibly red. Both are valid; they must not be mixed silently.
2. **Whether to approve all three decisions together or separately:** the contracts are independent. Separate approval provides cleaner scope; combined approval reduces round trips.
3. **Whether implementation may proceed immediately after approval:** contract approval does not imply implementation authorization. The User must state this separately.
4. **Whether commit groups may be staged after implementation:** staging and commit require separate authorization.

No other policy choice is silently resolved by this package.

## 9. Verification Evidence

Only read-only and in-memory checks were run.

| Check | Result |
|---|---|
| Git branch/HEAD/status/staged diff | Verified; staged diff empty. |
| Source report fingerprints | Both matched Round 23 and Round 24. |
| Eight updater files | Verified tracked, modified, regular, non-symlink. |
| Worktree blobs and modes | Freshly computed; values recorded above. |
| Updater test SHA-256 | Matched `d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b`. |
| Home/P9 imports | AST verified exactly four groups; no dynamic imports found. |
| Decision-ID availability | DEC-7301/7302/7303 available; 77 unique current IDs; no duplicates. |
| Historical-ID pattern | Accepts all 77 current IDs; Round 24 malformed controls remain rejected. |
| Legacy checker inventory | Found P2, P3, P4, P5, foundation, and `.sps` probes; amendment list updated. |

No validator, test suite, installer, updater, network operation, or state-mutating command was run.

## 10. Risks and Verification Limitations

- The proposed manifests do not exist, so their hashes bind proposed objects, not existing files.
- Git blob IDs and SHA-256 values are valid only for the current worktree and MUST be recomputed before implementation.
- Git object identity does not authenticate a human approver.
- PowerShell behavior remains unverified because `pwsh` is unavailable.
- No independent external agent reviewed this amended package.
- No validator or test suite was run in this round, so no new runtime evidence was produced.

## 11. Concise User Approval Checklist

The User may respond separately for each item.

### DEC-7301

- [ ] Approve the corrected eight-path, mode-and-blob-pinned exception.
- [ ] Approve manifest canonical hash `sha256:6daa14045f3f6759782c77ffff89ca93edc2a22a3a2095aff30174cf7ca5fe36`.
- [ ] Approve explicit exclusion of all four check-update mirrors.
- [ ] Choose P5 checker treatment: amend to shared exception, or leave visibly red.

### DEC-7302

- [ ] Approve the four exact Home/P9 import groups.
- [ ] Approve manifest canonical hash `sha256:71d7830ab6748f7c6755d0657f24b0a2075e170c48ba5a6890909a8c46f7ca49`.
- [ ] Approve explicit amendment of P9 rollback semantics for Home.

### DEC-7303

- [ ] Approve historical `D-P*` compatibility.
- [ ] Require all new decisions to use `DEC-####`.
- [ ] Preserve validator exit semantics.

### Separate Permissions

- [ ] Authorize decision-record creation.
- [ ] Authorize implementation, and specify which decisions.
- [ ] Authorize staging/commit, and specify exact groups.
- [ ] Withhold or grant push, publication, P10 approval, CI, installer, inventory, backend-manifest, and exit-code changes explicitly.

## 12. Items Intentionally Not Changed

No decision record, requirement, schema, source file, test, evidence file, inventory, setting, CI workflow, validator, historical report, or generated artifact was changed.

No decision was approved. No staging, commit, push, fetch, pull, deploy, publication, cleanup, reset, stash, revert, branch switch, installer execution, dependency installation, or network access occurred.

## 13. Final Worktree Verification

At final verification, the staged diff remains empty. The 22 tracked modified paths, 149 untracked non-ignored files, and all concurrent-agent work remain preserved. The only new artifact is:

```text
reports/SPS2-ROUND25-AMENDED-GOVERNANCE-PACKAGE-20261016-223101.md
```
