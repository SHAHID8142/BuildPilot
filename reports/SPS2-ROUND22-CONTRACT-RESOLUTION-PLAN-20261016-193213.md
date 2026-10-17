# SPS2 Round 22 — Contract Resolution Design and Verification

Timestamp: 2026-10-16 19:32:13 +06:00  
Mode: read-only investigation and implementation planning. No contract change was made.  
Independent-agent review: none occurred.

## 1. Executive Summary

The worktree advanced after Round 21B because Claude’s Round 21A security implementation modified four additional tracked files: `scripts/check-update.ps1`, `scripts/check-update.sh`, `sps2/p17/scrub.py`, and `sps2/tests/test_p17_security.py`. Those changes are preserved and excluded from the Round 22 contract plan.

The smallest safe resolution is not to weaken `git diff HEAD` or the orphan scanner. Instead:

1. Create a User-ratified legacy exception manifest that pins the eight DEC-7201 files by path and Git blob ID against a fixed baseline. Checkers may ignore an entry only when both path and current blob match; every other legacy change remains fatal.
2. Create a User-ratified P10→P9 import exception manifest that pins four exact `(file, module, imported symbol)` triples. The scanner should compare resolved imported symbols, not merely module names. Every other `domain.seo` import remains fatal.
3. Extend the decision-ID contract with a narrow historical namespace while preserving every existing identifier. The evidence supports a repository-wide `D-P<phase>-<suffix>` compatibility rule because 40 historical IDs across eight files already use that form.

These changes require explicit User contract authorization. Edit authorization, ratification, and commit authorization remain separate.

## 2. Verified Baseline

- Branch: `build/roadmap-p3-completion`.
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`.
- Upstream delta: `0 0`; no local-only or remote-only commits.
- Staged diff: empty.
- Tracked modified paths: 20.
- Untracked non-ignored files: 144.
- Porcelain entries: 38.

### 2.1 Change since Round 21B

Round 21B recorded 16 tracked modified paths and 142 untracked files. Current state adds these four modified paths attributable to the Round 21A report:

```text
scripts/check-update.ps1
scripts/check-update.sh
sps2/p17/scrub.py
sps2/tests/test_p17_security.py
```

The untracked count increased by two generated/report files inside already-untracked directories. No ownership reconciliation was performed.

### 2.2 Critical fingerprints

```text
07e32fff88497590e5688e888ff1f8c7169aa5ff49155b74ce718c16cc9289d7  reports/SPS2-ROUND21B-LEGACY-CONTRACT-RECONCILIATION-20261016-192129.md
3b3b084dfcc7efd4e9d36a1b9fa301bc72a4bcfd187e17f258259cc4d69657af  get-sps.ps1
3b3e4fcfd7ac6e096a23ee28f598774e9eefcdad7b2b574c27d2c5caf216783f  get-sps.sh
8139065418a8e24d0dd4e09d99eb4b3e8e7432f3f4e47115e1470d09fc362b18  scripts/bootstrap-sps.sh
ba90bfbfe6f57fd6cdd15712c5f598affb09998f434d5823a0eb31dec9d5fde2  scripts/sps-update.sh
fc207b82ea549c49843249f8d0501e1ca2dfd4a999c4482447cda86c605eb1ad  scripts/update-sps.ps1
d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b  sps2/tests/test_updater_safety.py
854148c6db6d7cbd48e0b69dfe92337077f3d85bd53332644382414ab4ab0bbb  domain/seo/isolation.py
```

Concurrent Round 21A artifacts:

```text
ca00fcea56b182d7c4de0e25203df4a399492658cd557be819f75f8547188002  scripts/check-update.ps1
f175ed77f54cea9d5eeb9a92177ca0a05592639fa03f1cda3e3ecd4dd4b8043d  scripts/check-update.sh
8567049f7d861b7dcbfe33c165d4cfcd2412c34d7e6cb9e487136e39d8b65192  sps2/p17/scrub.py
f3b37405382af8faabb7dfbaf721eae707b40d97edb130658b2b23aded750e65  sps2/tests/test_p17_security.py
```

## 3. Workstream 1 — Legacy-Preservation Contract

### 3.1 Current behavior

**VERIFIED.**

- `domain/seo/isolation.py:77` defines legacy directories as `skills`, `scripts`, `plugins`, and `templates`.
- `domain/seo/isolation.py:238-267` compares `git diff HEAD -- <directory>` and reports any non-empty diff.
- `domain/seo/tests/test_isolation.py:133-136` requires an empty violation list.
- `sps2/tools/validate-sps2.sh:208-210` checks `skills`, `scripts`, `plugins`, `.github`, installer scripts, and uninstallers against HEAD.
- `sps2/tools/validate-p3.sh:319-322` and `sps2/tools/validate-p4.sh:497-500` check broader legacy pathspecs against `c11da27`.
- DEC-0028 at `sps2/decisions/ATTRIBUTION-POLICY-DECISIONS.json:113-115` preserves the P3/P4 controls unchanged and keeps their failures visible until a separate User decision.

Current `git diff --name-status HEAD -- <legacy paths>` shows the eight DEC-7201 files plus Claude’s two check-update files:

```text
M get-sps.ps1
M get-sps.sh
M scripts/bootstrap-sps.sh
M scripts/check-update.ps1
M scripts/check-update.sh
M scripts/sps-update.sh
M scripts/update-sps.ps1
M skills/sps/scripts/bootstrap-sps.sh
M skills/sps/scripts/sps-update.sh
M skills/sps/scripts/update-sps.ps1
```

Only the eight DEC-7201 files are eligible for the proposed exception. The two check-update files remain fatal unless separately ratified.

### 3.2 Proposed exception contract

Add a new governance artifact, provisionally `sps2/governance/legacy-exception-manifest.json`, only after explicit User authorization. Proposed schema:

```json
{
  "schema": "sps2.legacy-exception-manifest/v1",
  "decision_id": "<NEXT-USER-DECISION-ID>",
  "baseline_commit": "c49f3852e1c31d0136269c80fe58201b059af3ec",
  "additionalProperties": false,
  "exceptions": [
    {
      "path": "get-sps.ps1",
      "expected_blob": "e28977e0ed3231f0e76a45e1bc943c1e7d5798db",
      "authorization": "DEC-7201",
      "reason": "ratified updater-safety workstream"
    },
    {
      "path": "get-sps.sh",
      "expected_blob": "29d808d65227f23a22c6e4f56ddb31424c695327",
      "authorization": "DEC-7201",
      "reason": "ratified updater-safety workstream"
    },
    {
      "path": "scripts/bootstrap-sps.sh",
      "expected_blob": "2347c0124fbe482068d0ca47d8e933c28db1e6a4",
      "authorization": "DEC-7201",
      "reason": "ratified updater-safety workstream"
    },
    {
      "path": "scripts/sps-update.sh",
      "expected_blob": "585c24a3f7e380feb8237e0a720e6c0cddd461d9",
      "authorization": "DEC-7201",
      "reason": "ratified updater-safety workstream"
    },
    {
      "path": "scripts/update-sps.ps1",
      "expected_blob": "4054b1679f9fa50b85a4e8911587634fb166a9ce",
      "authorization": "DEC-7201",
      "reason": "ratified updater-safety workstream"
    },
    {
      "path": "skills/sps/scripts/bootstrap-sps.sh",
      "expected_blob": "2347c0124fbe482068d0ca47d8e933c28db1e6a4",
      "authorization": "DEC-7201",
      "reason": "ratified updater-safety workstream"
    },
    {
      "path": "skills/sps/scripts/sps-update.sh",
      "expected_blob": "585c24a3f7e380feb8237e0a720e6c0cddd461d9",
      "authorization": "DEC-7201",
      "reason": "ratified updater-safety workstream"
    },
    {
      "path": "skills/sps/scripts/update-sps.ps1",
      "expected_blob": "4054b1679f9fa50b85a4e8911587634fb166a9ce",
      "authorization": "DEC-7201",
      "reason": "ratified updater-safety workstream"
    }
  ]
}
```

The manifest must also require the test file `sps2/tests/test_updater_safety.py`, but that file is untracked and therefore has no Git blob ID yet. Its current SHA-256 is `d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b`. Record it as `expected_sha256` and switch the contract to its Git blob ID only after the User authorizes staging/commit. Before staging, the test can be covered by the decision record and updater tests rather than the Git legacy checker.

### 3.3 Proposed executable semantics

Replace the current “any diff is failure” behavior with a pinned-exception algorithm:

1. Use a fixed `baseline_commit`, never mutable `HEAD`.
2. Enumerate `git diff --name-status --diff-filter=ACMRTUXB <baseline> -- <legacy pathspecs>`.
3. For every changed path not present exactly once in `exceptions`, fail.
4. For an allowed path, obtain the current stage-0 blob with `git rev-parse :<path>` and compare it exactly to `expected_blob`.
5. Treat missing, deleted, renamed, unreadable, untracked, duplicate-manifest, or hash-mismatched entries as failures.
6. Never ignore a path merely because it is in the manifest.
7. Emit one violation per bad path, including expected and observed blob IDs.

This can be implemented as a shared helper in `domain/seo/isolation.py` or a small stdlib-only governance module consumed by that helper and the shell validators. A shared helper is preferable to three copies of the logic.

### 3.4 Governance records and tests requiring change

Implementation requires one new User decision record that explicitly amends or supersedes the relevant scope of DEC-0028 and names:

- fixed baseline `c49f3852e1c31d0136269c80fe58201b059af3ec`;
- the exact eight paths and blob IDs;
- whether the untracked test file is included by SHA-256 now or by blob ID after staging;
- the exact executable checks being amended;
- preservation of fail-closed behavior for every other legacy path.

The implementation would touch:

```text
domain/seo/isolation.py
domain/seo/tests/test_isolation.py
sps2/tools/validate-sps2.sh
sps2/tools/validate-p3.sh
sps2/tools/validate-p4.sh
sps2/governance/legacy-exception-manifest.json
sps2/decisions/<NEXT-USER-DECISION-ID or named decision file>.json
```

No CI wiring is included.

### 3.5 Required tests

Add behavioral tests around a temporary Git repository or a pure helper that accepts injected Git results. Prefer subprocess-based integration tests using temporary synthetic repositories; do not mutate the real worktree.

Positive:

1. Baseline has legacy files; working tree changes exactly the eight allowed paths to expected blobs; result is empty.
2. An allowed file is committed; `git diff <baseline>` still sees it; helper still returns empty because the blob matches.
3. Manifest validation accepts eight unique paths and valid blob IDs.

Negative:

4. Modify one allowed file after ratification; blob mismatch fails.
5. Delete one allowed file; missing stage-0 blob fails.
6. Rename an allowed file; both old and new paths fail.
7. Modify any non-allowed legacy path, including `scripts/check-update.sh`; fails.
8. Add an untracked legacy file; fails.
9. Duplicate a manifest path; fails.
10. Use a non-commit or unknown baseline; fails.
11. Remove or corrupt the manifest; fails closed.
12. Malformed path traversal, absolute path, or symlink escape; fails closed.

The critical post-commit assertion is test 2: the check must compare against the fixed baseline and pinned blobs, not `HEAD`, so committing cannot make an unresolved exception silently disappear.

### 3.6 Risks and trade-offs

- **Blob IDs are repository-local object names**, not cryptographic attestations of User approval. They provide tamper evidence for the working tree relative to the ratified manifest.
- **Pinning current content** means any intentional updater amendment requires a new decision and manifest revision.
- **A fixed baseline grows over time**, but remains auditable. It should not be advanced casually.
- **A path-only allowlist would be unsafe** because it would allow later edits under the same filename.

## 4. Workstream 2 — Home/P9 SEO Dependency

### 4.1 Current behavior

**VERIFIED.**

- The scanner at `domain/seo/isolation.py:198-235` detects every `domain.seo` import outside its P9 exclusions.
- The test at `domain/seo/tests/test_isolation.py:114-117` requires zero violations.
- Home imports at `domain/frontend/home_render.py:66-75`:
  - `domain.seo.indexing`: `generate_robots_txt`, `generate_sitemap_from_cms_items`, `generate_sitemap_xml`;
  - `domain.seo.metadata`: `generate_metadata_from_content`, `render_html_meta_tags`;
  - `domain.seo.model`: `RobotsConfig`, `RobotsGroup`.
- The Home test imports `domain.seo.audit.audit_directory` at `domain/frontend/tests/test_home_render.py:42`.

The focused suite currently reports four SEO failures, including the orphan scanner and rollback rehearsal/status tests. This is a structural contract conflict, not an implementation accident.

### 4.2 Proposed narrow dependency exception

After explicit User authorization, add to `domain/seo/isolation.py`:

```python
P10_P9_IMPORT_EXCEPTIONS: dict[str, dict[str, frozenset[str]]] = {
    "domain/frontend/home_render.py": {
        "domain.seo.indexing": frozenset({
            "generate_robots_txt",
            "generate_sitemap_from_cms_items",
            "generate_sitemap_xml",
        }),
        "domain.seo.metadata": frozenset({
            "generate_metadata_from_content",
            "render_html_meta_tags",
        }),
        "domain.seo.model": frozenset({
            "RobotsConfig",
            "RobotsGroup",
        }),
    },
    "domain/frontend/tests/test_home_render.py": {
        "domain.seo.audit": frozenset({
            "audit_directory",
        }),
    },
}
```

Extend the scanner to resolve imported symbols for `ast.ImportFrom`. Compare the exact `(relative file, module, imported symbol)` triple. A module-level allowlist alone is too broad. Unknown symbols, extra imports, renamed paths, symlink aliases, and imports in unrelated files must remain violations.

### 4.3 Proposed contract text

> P10 Home may depend on the P9 SEO engine only through the four explicitly ratified import sites and symbol sets recorded in `P10_P9_IMPORT_EXCEPTIONS`. This is an owned dependency, not a rollback orphan: deletion of P9 remains an intentional break requiring coordinated removal of the P10 consumer. All other `domain.seo` references outside the P9 surface remain forbidden.

The decision record must also reconcile the P9 rollback wording in `P9-REQUIREMENTS.json` and `P9-THREAT-MODEL.md:167-172` with this dependency. Do not silently redefine “deleting P9 leaves zero orphaned references.”

### 4.4 Required tests

Positive:

1. The live scanner accepts exactly the four approved import sites and symbol sets.
2. The orphan count is zero and rollback/status reporting treats approved P10 dependencies as owned dependencies, not orphans.
3. Manifest validation rejects duplicate files, duplicate modules, duplicate symbols, empty symbol sets, non-relative paths, and symlink aliases.

Negative:

4. Add `domain.seo.metadata.validate_metadata` to an unrelated module; fails.
5. Add an unlisted symbol from an approved module to `home_render.py`; fails.
6. Add an unlisted `domain.seo` module to `home_render.py`; fails.
7. Add an approved import to a different file; fails.
8. Use a symlink or path-normalization alias to evade the exact path; fails.
9. Remove the exception manifest; fails closed.
10. Replace an approved import with local duplication of the same behavior; scanner passes, but the governance test must verify the exception was removed or explicitly retired.

### 4.5 Alternative: remove P9 imports from Home

Removing the imports would preserve the strongest rollback property: deleting `domain/seo/` would leave Home buildable. It would require duplicating or relocating metadata, sitemap, robots, and audit primitives, then changing the renderer and tests. That is a larger architecture change, risks policy drift between Home and P9, and duplicates behavior the requirements deliberately assign to P9.

**Recommendation:** the explicit exception is the smallest maintainable option, provided the User approves the P10 dependency. Refactor only if the User decides that P9 rollback independence outranks avoiding duplication.

## 5. Workstream 3 — Historical Decision Identifiers

### 5.1 Current behavior

**VERIFIED.**

- `sps2/tools/check_sps2.py:219-233` accepts only `^DEC-[0-9]{4}$`.
- `sps2/governance/SCHEMAS/decision.schema.json:20-25` has the same pattern.
- `sps2/tests/test_attribution_policy.py:508-524` specifically enforces `^DEC-[0-9]{4}$` for the attribution-policy record; lines 547-553 enforce it for `closed_by`.
- The live P10 file has 10 `D-P10-*` IDs, producing 10 validator errors.
- Repository-wide, 40 historical IDs across eight files use `D-P*` forms:

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

The validator exits 0 while printing errors. That is its existing reporting contract and should not be changed in this contract task.

### 5.2 Proposed compatibility rule

Use one explicit legacy pattern in both validator and schema:

```text
^D-P[0-9]+(?:-[A-Z0-9]+)*$
```

Accept either `^DEC-[0-9]{4}$` or the legacy pattern. Preserve original IDs. Add a `decision_id_namespace` field only if a separate schema migration is authorized; otherwise infer namespace from the ID and avoid changing historical records.

The pattern should be centralized as a named constant so `check_sps2.py`, the JSON schema documentation, and tests cannot drift. If JSON Schema cannot import code, add a validator test that parses the schema and asserts its `decision_id.pattern` equals the same literal.

### 5.3 Required tests

Positive:

1. `D-P10-1` through `D-P10-9` and `D-P10-APPROVAL` are accepted.
2. Representative historical IDs from the other seven files are accepted.
3. `DEC-7201` remains accepted.
4. Required `reason`, `evidence`, and approval checks still run for legacy IDs.
5. The schema pattern and validator regex are identical.

Negative:

6. Reject empty IDs.
7. Reject lowercase legacy IDs such as `d-p10-1`.
8. Reject malformed suffixes such as `D-P10-_BAD`, `D-P10--1`, and `D-P10-1-`.
9. Reject phase-less forms such as `D-1`.
10. Reject new-style malformed IDs such as `DEC-72A1` and `DEC-721`.
11. Reject duplicates even when one is legacy and one is new-style.
12. Preserve the existing `bad decision_id` error text or update its tests deliberately.

### 5.4 Normative decision required

**USER DECISION REQUIRED.** The repository must choose:

1. accept the historical namespace as valid;
2. create `DEC-*` supersession records while preserving originals;
3. maintain an explicit exception registry.

The evidence favors option 1 as the smallest maintainable change because the namespace is already broadly used. It must not be implemented as a silent validator relaxation.

## 6. Workstream 4 — Commit Readiness

### 6.1 Dependency map

| Group | Current exact paths | Dependencies | Technical readiness | Governance readiness | Commit authorization |
|---|---|---|---|---|---|
| C1 updater safety | `get-sps.ps1`, `get-sps.sh`, `scripts/bootstrap-sps.sh`, `scripts/sps-update.sh`, `scripts/update-sps.ps1`, `skills/sps/scripts/bootstrap-sps.sh`, `skills/sps/scripts/sps-update.sh`, `skills/sps/scripts/update-sps.ps1`, `sps2/tests/test_updater_safety.py` | Legacy exception decision/manifest; fixed-baseline checker; updater tests | Ready: 13 tests, 12 passed, 1 PowerShell skip; syntax, mirror, and whitespace checks pass | Not ready: legacy contract amendment required | Not granted |
| C2 P10 gate | `sps2/tools/p10_runtime_gate.py`, `sps2/tests/test_p10_runtime_gate.py` | C3 slice/schema/inventory and CMS data | Ready: 320 tests passed | Ready for implementation preservation, but real gate remains legitimately `FAIL` | Not granted |
| C3 P10 governance | `sps2/decisions/P10-DECISIONS.json`, `sps2/decisions/P10-DELEGATED-DECISIONS.json`, `sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json`, `sps2/decisions/P10-ROUND12-USER-DECISIONS.json`, `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json`, `sps2/project/SLICE-P10-01.json`, `sps2/requirements/P10-SECTION-INVENTORY.json`, `sps2/schemas/p10-slice.schema.json` | C2; identifier compatibility; CMS state | Structurally ready; 320 gate tests pass | Not ready: 10 known `D-P10-*` validator errors | Not granted |
| D1 Home implementation | `domain/cms/data/content.json`, `domain/cms/data/content_types.json`, `domain/cms/data/revisions.jsonl`, `domain/frontend/__init__.py`, `domain/frontend/content_slots.py`, `domain/frontend/home_render.py`, `domain/frontend/layout_registry.py`, `domain/frontend/tests/__init__.py`, `domain/frontend/tests/test_content_slots.py`, `domain/frontend/tests/test_home_render.py`, `domain/frontend/tests/test_layout_registry.py` | C2/C3; P10→P9 exception contract | Ready: frontend 85 tests and CMS 86 tests pass | Not ready: P10/P9 dependency decision required | Not granted |

### 6.2 Excluded paths

Keep all of the following outside proposed groups unless separately authorized:

- `.claude/settings.json`;
- `sps2/evidence/P10-EVIDENCE.json`;
- `.sps/evidence/P17/` and `.sps/tasks/p17/`;
- `.sps/audits/README.md`, `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md`, `sps2/evidence/P5-EVIDENCE.json`, `sps2/governance/attribution.py`, `sps2/requirements/P5-REQUIREMENTS.json`;
- `sps2/decisions/LEGACY-PATH-DEFINITION-DECISIONS.json` and `sps2/decisions/LEGACY-SCOPE-DECISIONS.json`;
- all reports;
- all generated `__pycache__` files;
- Claude’s concurrent Round 21A files: `scripts/check-update.ps1`, `scripts/check-update.sh`, `sps2/p17/scrub.py`, and `sps2/tests/test_p17_security.py`.

### 6.3 Commit ordering

If later authorized:

1. C3 governance/planning first, after identifier compatibility is resolved.
2. C2 gate implementation and tests, consuming C3.
3. C1 updater safety, after the legacy exception contract is recorded.
4. D1 Home implementation, after the P10→P9 dependency contract is recorded.

Do not combine governance transitions, publication, or approval with implementation commits.

## 7. Verification Results

| Command | Exit code | Result |
|---|---:|---|
| `git status --porcelain=v1 --branch`; `git diff --cached --name-status` | 0 | Baseline captured; staged diff empty. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v domain.seo.tests.test_isolation sps2.tests.test_updater_safety sps2.tests.test_p10_runtime_gate` | 1 | 353 tests: 4 SEO failures, 1 PowerShell skip, otherwise passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v domain.frontend.tests.test_content_slots domain.frontend.tests.test_home_render domain.frontend.tests.test_layout_registry` | 0 | 85 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v domain.cms.tests.test_assets domain.cms.tests.test_audit domain.cms.tests.test_content domain.cms.tests.test_isolation domain.cms.tests.test_publishing domain.cms.tests.test_rbac domain.cms.tests.test_ssrf_redirects domain.cms.tests.test_xss_protection` | 0 | 86 tests passed. |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v sps2.tests.test_p17_security` | 0 | 65 tests passed; concurrent Round 21A work is currently healthy. |
| `bash sps2/tools/validate-sps2.sh` | 1 | 78 passed, 1 failed, 0 missed; negative suite 27/27. |
| `bash sps2/tools/validate-p3.sh` | 1 | 66 passed, 2 failed, 0 missed; negative suite 18/18. |
| `bash sps2/tools/validate-p4.sh` | 1 | 57 passed, 3 failed, 0 missed; negative suite 22/22. |
| `python3 sps2/tools/check_sps2.py decision <each decisions/*.json>` | 0 per existing contract | 40 total `bad decision_id` errors across eight files. |
| `bash -n` on six modified Bash scripts | 0 each | Syntax valid. |
| `git diff --check` | 0 | No whitespace errors. |

PowerShell runtime execution remains unavailable (`pwsh` absent), so PowerShell behavior is not verified.

## 8. User Decisions Required

1. Approve or reject the fixed-baseline, blob-pinned legacy exception for the eight DEC-7201 files.
2. Approve or reject the explicit P10→P9 dependency exception for the four import sites.
3. Choose the historical decision-ID strategy: legacy compatibility, governed supersession, or exception registry.
4. Separately authorize staging/commit for C1, C2, C3, and/or D1.
5. Separately decide `.claude/settings.json`, stale P10 evidence, SPEC-2, P17 preservation, report preservation, installer redesign, and CI hardening.

## 9. Items Intentionally Not Changed

No source, test, schema, decision, evidence, inventory, settings, CI, validator, report, or generated file was changed. The only intended side effect is this new report.

No staging, commit, push, fetch, pull, deploy, publication, approval, inventory regeneration, backend-manifest creation, cleanup, reset, stash, revert, branch switch, install, dependency installation, or network access occurred.

## 10. Final Worktree and Side-Effect Verification

At report creation:

- staged diff remains empty;
- the 20 pre-existing tracked modifications remain;
- all pre-existing untracked files remain;
- the only new audit artifact is this report;
- no concurrent-agent work was overwritten or reconciled by deletion.

## 11. Limitations

- No independent external agent reviewed this plan.
- PowerShell runtime behavior was not executed because `pwsh` is unavailable.
- Remote state was not queried.
- The proposed exception IDs and file names are placeholders; the User decision record must assign the authoritative governance identity.
- This plan does not authorize implementation, even though it is implementation-ready.
