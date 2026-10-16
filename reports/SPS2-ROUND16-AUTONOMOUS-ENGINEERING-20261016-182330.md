# SPS2 ROUND 16 — AUTONOMOUS ENGINEERING, SECURITY HARDENING, GATE CORRECTNESS, AND INDEPENDENT VERIFICATION

Report time: 2026-10-16T18:23:30+06:00 (suffix `20261016-182330`).  
Repository: `SHAHID8142/Shahid-Master-Skill`.  
Scope: verify and complete the authorized P10 gate and updater-safety work, design—not implement—the installer preservation fix, reconcile governance, run offline verification, and produce this report. No commit, push, publication, approval, backend manifest, CI change, or Git mutation was authorized or performed.

**Provenance note.** A later-suffixed historical report,
`reports/SPS2-ROUND17-R15-DEFECT-RESOLUTION-20261016-182229.md`, already
existed when this report was created. It was preserved unchanged. This Round 16
report independently re-verifies the live state rather than relying on that
report. No supported mechanism was available in this session to invoke Claude as
a separate agent; no independent-agent review is claimed.

## 1. Executive summary

- **Verified:** the three P10 gate defects R15-001, R15-002, and R15-003 are resolved in the live tree and covered by behavioral tests.
- **Verified:** the three updater defects R15-004, R15-007, and R15-008 are resolved in Bash and PowerShell paths; relevant mirrors are byte-identical.
- **Verified:** the focused P10/updater suite passed 333 tests with one expected PowerShell-environment skip; all 597 `sps2` module tests passed with two skips.
- **Verified:** the real P10 gate remains read-only and correctly exits `1` with `OVERALL: FAIL`; seven required prerequisites remain unmet.
- **High-risk defect remains:** `install.sh` and `install.ps1` remove managed global destinations before replacement without a verified backup/restore transaction. This was not changed because installer global-write policy remains deferred.
- **Governance:** `user_approval` remains `null`, publication remains draft, inventory digest values remain the authorized values, and `domain/backend/operations.json` remains absent.
- **No source file was changed by this report session.** The only expected worktree addition is this new report.

## 2. Verified baseline

At audit start:

- Branch: `build/roadmap-p3-completion`.
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`.
- Upstream: `origin/build/roadmap-p3-completion`.
- Staged paths: none.
- Stashes: none.
- Tracked modified paths: 16.
- Untracked status entries: 17, including the already-untracked `reports/` directory.

Initial modified tracked paths:

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

Important untracked work included:

```text
domain/cms/data/
domain/frontend/
reports/
sps2/decisions/LEGACY-PATH-DEFINITION-DECISIONS.json
sps2/decisions/LEGACY-SCOPE-DECISIONS.json
sps2/decisions/P10-DELEGATED-DECISIONS.json
sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json
sps2/decisions/P10-ROUND12-USER-DECISIONS.json
sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json
sps2/evidence/P10-EVIDENCE.json
sps2/project/SLICE-P10-01.json
sps2/tests/test_p10_runtime_gate.py
sps2/tests/test_updater_safety.py
sps2/tools/p10_runtime_gate.py
```

## 3. Preservation manifest

These SHA-256 fingerprints were captured from the live files after all safe tests and before report creation. They match the values recorded in the checkpoint and Round 17 report for the implementation files.

```text
99d55ffb8c8af8f5c002d9165614b5f89171c5e1405d8972d3e938cd718d0e4b  sps2/tools/p10_runtime_gate.py
f585e1b4b8a90780bc9420b6ed35fde90f308ee8bd00f6d4310d5ad1aa46fbd5  sps2/tests/test_p10_runtime_gate.py
d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b  sps2/tests/test_updater_safety.py
ba90bfbfe6f57fd6cdd15712c5f598affb09998f434d5823a0eb31dec9d5fde2  scripts/sps-update.sh
ba90bfbfe6f57fd6cdd15712c5f598affb09998f434d5823a0eb31dec9d5fde2  skills/sps/scripts/sps-update.sh
fc207b82ea549c49843249f8d0501e1ca2dfd4a999c4482447cda86c605eb1ad  scripts/update-sps.ps1
fc207b82ea549c49843249f8d0501e1ca2dfd4a999c4482447cda86c605eb1ad  skills/sps/scripts/update-sps.ps1
8139065418a8e24d0dd4e09d99eb4b3e8e7432f3f4e47115e1470d09fc362b18  scripts/bootstrap-sps.sh
8139065418a8e24d0dd4e09d99eb4b3e8e7432f3f4e47115e1470d09fc362b18  skills/sps/scripts/bootstrap-sps.sh
3b3e4fcfd7ac6e096a23ee28f598774e9eefcdad7b2b574c27d2c5caf216783f  get-sps.sh
3b3b084dfcc7efd4e9d36a1b9fa301bc72a4bcfd187e17f258259cc4d69657af  get-sps.ps1
713c5df3c6d8c82e579597940e3bd8a61400c46ab7c88a33496d27cffe8ecd69  sps2/schemas/p10-slice.schema.json
a3d29c3927a6c0bfa8385881c8dc3adfa0cf3dd11bd97f7a83b0fc376b938058  sps2/project/SLICE-P10-01.json
c58bcb14f5fed0e7982632f6e96fea93cdd8adf3d23991a75ca7ba1abe3f2dc3  sps2/evidence/P10-EVIDENCE.json
d0984c0ddf394ade74cf35296d7363072592bdc89504ece20a56c23a68d35893  sps2/requirements/P10-SECTION-INVENTORY.json
415d31712ccc287ec8180a215b0e6eab1a69f26ca9c59ae0b1660c78f4b8d08c  install.sh
3d55ddde720d5962cd050633a399ace59cd6535a880dee327562afc3f1891f7d  install.ps1
```

## 4. Task ledger

| Task | Owner | Status | Files affected | Authorization basis | Tests | Findings / remaining risk |
|---|---|---|---|---|---|---|
| A1 Baseline and preservation | Codex | COMPLETE | None | User authorized safe local tests and report | Git status, HEAD, fingerprints | No conflict observed. |
| B1 R15-001 operation reconciliation | Pre-existing work; Codex verified | VERIFIED | `sps2/tools/p10_runtime_gate.py`, `sps2/tests/test_p10_runtime_gate.py` | Round 12/DEC-7112 adopted object contract | 333-test focused suite | Resolved. |
| B2 R15-002 gate-record completeness | Pre-existing work; Codex verified | VERIFIED | Same as B1 | Round 14 / DEC-7112 | Same as B1 | Resolved; no cryptographic trust root is claimed. |
| B3 R15-003 malformed operation fail-closed | Pre-existing work; Codex verified | VERIFIED | Same as B1 | DEC-7112 | Same as B1 | Resolved. |
| B4 R15-004 PowerShell safety-before-network | Pre-existing work; Codex verified | VERIFIED | `scripts/update-sps.ps1`, mirror | DEC-7201 updater-safety ratification | Focused suite; static PowerShell inspection | `pwsh` unavailable, so runtime PowerShell test skipped. |
| B5 R15-007 clone-failure wording | Pre-existing work; Codex verified | VERIFIED | `get-sps.ps1`, updater PowerShell copies | DEC-7201 | Focused suite | Resolved. |
| B6 R15-008 Bash `cd` guard | Pre-existing work; Codex verified | VERIFIED | `scripts/sps-update.sh`, mirror | DEC-7201 | Focused suite; `bash -n` | Resolved. |
| C1 Installer preservation design | Codex | DESIGN ONLY | None | Global-write/installer policy deferred | Static source inspection, no execution | Requires User authorization. |
| D1 Governance reconciliation | Codex | PARTIAL | None | Evidence update not authorized | Read-only validators | Stale P10 evidence remains unchanged. |
| D2 Independent verification | Codex | COMPLETE within session limits | None | User authorized safe tests | See §10 | No separate Claude invocation was available. |
| E1 Report | Codex | COMPLETE | This report only | User required new report | Existence/readability check | Expected one new file. |

## 5. P10 gate defect resolution

### R15-001 — operation representation: VERIFIED RESOLVED

The adopted schema contract represents declared operations as objects. The
schema defines the backend `state_changing_operations` items at
`sps2/schemas/p10-slice.schema.json:153`; the Home slice declares an empty array
at `sps2/project/SLICE-P10-01.json:24`.

The gate now:

- requires each declared entry to be an object (`sps2/tools/p10_runtime_gate.py:2417-2424`);
- reads the declared name from `operation` (`sps2/tools/p10_runtime_gate.py:2421-2424`);
- requires non-empty `required_controls` (`sps2/tools/p10_runtime_gate.py:2425-2434`);
- requires each manifest entry to be an object with non-empty `name` and controls (`sps2/tools/p10_runtime_gate.py:2449-2467`);
- fails closed before reconciliation when either side is malformed (`sps2/tools/p10_runtime_gate.py:2468-2474`);
- set-compares names and reports both phantom and undeclared operations (`sps2/tools/p10_runtime_gate.py:2475-2485`).

Regression coverage includes under-declaration, over-declaration, malformed
declared entries, malformed manifest entries, and non-list manifests at
`sps2/tests/test_p10_runtime_gate.py:1843-1906`.

### R15-002 — gate-record completeness: VERIFIED RESOLVED

`check_evidence_authenticity` now requires a complete
`sps2.p10-gate-record/v1` object:

- required non-blank fields: `schema`, `producing_command`, `emitting_tool_version`, and `utc_timestamp` (`sps2/tools/p10_runtime_gate.py:2235-2238`);
- exact schema/version match (`sps2/tools/p10_runtime_gate.py:2240-2243`);
- parseable RFC 3339 UTC timestamp with zero-offset spelling (`sps2/tools/p10_runtime_gate.py:2245-2253`);
- at least one meaningful SHA-256 input/output claim (`sps2/tools/p10_runtime_gate.py:2256-2298`);
- digest syntax validation (`sps2/tools/p10_runtime_gate.py:2270-2277`);
- recomputation and contradiction reporting (`sps2/tools/p10_runtime_gate.py:2284-2294`);
- repository-root containment (`sps2/tools/p10_runtime_gate.py:2278-2283`).

The control explicitly states that this is content integrity and provenance
recording, not cryptographic authenticity or human authorization
(`sps2/tools/p10_runtime_gate.py:2321-2326`). That distinction is correct and
was preserved.

Adversarial tests cover missing fields, wrong schema/version, malformed
timestamps, missing digest claims, malformed digests, traversal/symlink escape,
and output tampering at `sps2/tests/test_p10_runtime_gate.py:2029-2198`.

### R15-003 — malformed operations silently ignored: VERIFIED RESOLVED

The gate no longer filters invalid entries into an apparently valid set. It
collects malformed declared and manifest entries separately and returns `FAIL`
before any set comparison (`sps2/tools/p10_runtime_gate.py:2468-2474`). Tests
assert failures for non-objects, blank names, missing controls, empty controls,
wrong control types, and blank control strings
(`sps2/tests/test_p10_runtime_gate.py:1867-1900`).

## 6. Updater-safety defect resolution

### R15-004 — PowerShell safety checks before network: VERIFIED RESOLVED

In both `scripts/update-sps.ps1` and its byte-identical mirror, the dirty-tree
and non-Git refusal block runs before the update checker/network path:

- source-status failure exits at `scripts/update-sps.ps1:38-42`;
- dirty source exits at `scripts/update-sps.ps1:43-49`;
- non-Git destination exits at `scripts/update-sps.ps1:50-53`;
- only then does `Checker` run at `scripts/update-sps.ps1:56-65`.

Static tests assert this ordering at
`sps2/tests/test_updater_safety.py:188-199`. Runtime PowerShell execution was
skipped because `pwsh` is unavailable.

### R15-007 — clone-failure wording: VERIFIED RESOLVED

The PowerShell clone failure now says the destination “may be partially
created” instead of claiming it is unchanged
(`scripts/update-sps.ps1:116-120`). `get-sps.ps1` uses the same accurate wording
in its clone-failure path. The test at
`sps2/tests/test_updater_safety.py:201-206` checks both updater copies and
`get-sps.ps1`.

### R15-008 — Bash `cd` failure: VERIFIED RESOLVED

Both Bash updater copies guard the directory change before reinstall:

```bash
if ! cd "$REPO_DIR"; then
  bad "Cannot enter the updated source directory; reinstall stopped."
  exit 1
fi
```

See `scripts/sps-update.sh:139-142`; the mirror is byte-identical. This prevents
an unintended installer invocation from the previous working directory.

### Additional safety boundaries verified

- Bootstrap no longer auto-applies updates: the auto-update block was removed from both bootstrap copies; see the diff for `scripts/bootstrap-sps.sh` and `skills/sps/scripts/bootstrap-sps.sh`.
- Bash updater safety runs before the network checker: `scripts/sps-update.sh:72-99`.
- Non-Git destinations are refused rather than deleted: `scripts/sps-update.sh:83-86`; `scripts/update-sps.ps1:112-115`.
- Fetch, checkout, and pull failures exit rather than continue: `scripts/sps-update.sh:118-131`.
- No destructive `git reset --hard` or recursive-delete fallback remains in the inspected updater/bootstrap paths.
- `get-sps.sh` and `get-sps.ps1` also remove destructive reset/delete fallbacks and fail closed on fetch, checkout, pull, and clone failures.
- PowerShell `Set-Location` at `scripts/update-sps.ps1:125` is protected by the script-level `$ErrorActionPreference = "Stop"` at `scripts/update-sps.ps1:11`. This is an inference from PowerShell semantics, not a runtime observation.

## 7. Installer preservation analysis and required decision

### Verified current risk

`install.sh` creates the destination, then removes and replaces managed skills:

- `rm -rf "$dest_root/sps"` followed by copy at `install.sh:254-259`;
- optional `rm -rf "$dest_root/sps-cms"` followed by copy at `install.sh:262-263`.

`install.ps1` performs the equivalent Windows operations:

- `Remove-Item -Recurse -Force $dest` followed by copy at `install.ps1:175-177`;
- optional CMS removal/copy at `install.ps1:181-182`.

This is a **verified data-preservation defect** if the destination contains user
modifications or if copy fails after removal. The installer was not executed.

### Proposed transactional design

1. **Pre-flight validation:** canonicalize source and destination; reject symlink escape, path traversal, same source/destination, and destinations outside consented roots.
2. **Consent:** interactive mode must explicitly identify every managed path that will be replaced. Noninteractive replacement must require explicit `--yes` plus a separate replacement consent flag unless the User chooses a weaker policy.
3. **Dirty detection:** inspect existing managed destinations for unknown files, modified manifest-listed files, or missing expected files. Classify as clean, managed-only, or dirty.
4. **Staging:** copy the incoming tree to a temporary sibling directory; verify required files and hashes/manifest before touching the destination.
5. **Backup:** move or copy the existing destination to a timestamped backup directory; write a rollback manifest containing original relative paths, types, modes, byte sizes, and SHA-256 hashes.
6. **Atomic replacement where supported:** rename the existing destination to backup, rename staging into place, then fsync/close files where practical. If the second rename fails, restore backup by rename and fail closed.
7. **Failure recovery:** on any copy, verification, or rename failure, restore the backup and remove only the temporary staging path created by this run. Never delete the backup automatically after a failed run.
8. **Recovery command:** provide an idempotent restore command driven by the backup manifest and verify restored hashes before reporting success.
9. **Log and manifest preservation:** keep install logs and install manifests outside the replaced skill directory, or preserve/merge them as separate versioned artifacts.
10. **Cross-platform parity:** implement equivalent behavior and test names in Bash and PowerShell; keep primary and mirror scripts byte-identical where required.

**Status:** design only. This changes deferred global-write/installer policy and
requires explicit User authorization before implementation.

## 8. Governance and evidence reconciliation

### Protected state: VERIFIED

- Inventory state: `COMPLETE_AWAITING_USER_APPROVAL` (`sps2/requirements/P10-SECTION-INVENTORY.json:4`).
- `user_approval`: `null` (`sps2/requirements/P10-SECTION-INVENTORY.json:12`).
- `cms_state_digest`: `sha256:b35f7aba68eca4e7c9b688ae979891330f2f3d08c2b4250ce855c55943f7e38e` (`sps2/requirements/P10-SECTION-INVENTORY.json:9`).
- `p8_contract_digest`: `sha256:ee6bb68f04f0eb468f0fd6eafaaea0b68639b88199e207c7a76ef57e10bbf217` (`sps2/requirements/P10-SECTION-INVENTORY.json:10`).
- The real gate recomputed and matched both digest values.
- `domain/backend/operations.json` remains absent, so REQ-P10-07 reconciliation correctly fails closed.
- No publication or approval transition occurred.

### DEC-7201/7202/7203 provenance

`sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json` and
`reports/SPS2-ROUND16-RATIFICATION-AND-DIGEST-REGENERATION-20261016-180627.md`
record ratification of the updater-safety workstream, the two inventory digest
writes, and standing constraints. This session did not alter those records.

### R15-009 — stale P10 evidence: UNRESOLVED, USER DECISION REQUIRED

`sps2/evidence/P10-EVIDENCE.json` currently says the gate tool/test module are
untracked with “no recorded decision authorizes their creation or their
tracking.” It also says “no P10 implementation exists.” The Round 14 report and
the live tree show that the gate implementation exists and was authorized for
the six DEC-7112 semantics, while commit/tracking remains unauthorized.

No evidence field was changed because evidence correction requires explicit
User authorization. Proposed factual replacement, without changing `result`,
approval, publication, or closure semantics:

```json
"governance_discrepancy": "The P10 runtime gate tool (sps2/tools/p10_runtime_gate.py) and test module (sps2/tests/test_p10_runtime_gate.py) exist in the working tree and remain UNTRACKED. The Round 14 report records User authorization for implementing the six adopted DEC-7112 gate semantics and identifies these two files. This records implementation provenance only; it is not a runtime PASS, not a publication approval, not a user approval, and not authorization to stage or commit.",
"blocked_reason": "BLOCKED is this record's permanent result class until real runtime evidence replaces it: no Home build output exists, the referenced Home Content is unpublished (PUBLICATION: DEFER), user approval is null, the backend operation manifest is absent, and the runtime gate has not returned an overall PASS. The Round 14-authorized gate implementation exists but does not by itself establish runtime verification."
```

### R15-010 — inventory state provenance: UNRESOLVED

The inventory is modified relative to HEAD, but Git cannot establish which agent
or round made the original transition. DEC-7202 now authorizes the two digest
values, and both recompute correctly. Attribution of the earlier state
transition remains a separate forensic question and was not inferred or written.

## 9. Real P10 gate control-by-control result

Command:

```bash
python3 -B -m sps2.tools.p10_runtime_gate --slice sps2/project/SLICE-P10-01.json
```

Actual exit: `1`. Overall: `FAIL`; 7 required controls failed; 0 integrity problems; 16 required controls evaluated.

| Control | Result | Reason |
|---|---|---|
| `schema-structural` | PASS | Slice conforms to every applicable enforced schema constraint. |
| `slice-required-fields` | PASS | All eight axis contracts are declared. |
| `evidence-references` | PASS | Relative evidence reference resolves inside the repository; path containment only. |
| `layout-slot-conformance` | PASS | `home-default` consumed slots exactly match declared slots. |
| `published-only-content` | FAIL | Referenced Home Content is `draft`; publication remains deferred. |
| `exposure-declaration` | BLOCKED | No observed loopback/file-socket/no-socket bind exists. |
| `slice-id-uniqueness` | FAIL | No authoritative slice-ID history was supplied. |
| `evidence-freshness` | PASS | Timestamp parses with offset; datedness is not truthfulness. |
| `evidence-authenticity` | FAIL | Evidence has no complete `gate_record`. |
| `inventory-preconditions` | PASS | Pre-approval state and null approval are coherent. |
| `approval-authenticity` | FAIL | Approval is null. |
| `p9-deployment-audit` | BLOCKED | No build directory/output was supplied. |
| `cms-state-digest` | PASS | Recomputed digest matches the authorized recorded value. |
| `p8-contract-digest` | PASS | Recomputed digest matches the authorized recorded value. |
| `req-p10-07-reconciliation` | FAIL | Backend operations manifest is absent. |
| `approval-state-interaction` | PASS | Null approval is coherent before the guarded transition. |

These failures are legitimate fail-closed prerequisites, not gate regressions.

## 10. Commands executed and verification results

| Command | Result |
|---|---|
| `git status --porcelain=v1 --branch`; `git rev-parse --abbrev-ref HEAD`; `git rev-parse HEAD`; `git diff --cached --name-status` | Baseline captured; HEAD and branch as above; no staged paths. |
| `python3 -m pytest -q sps2/tests/test_p10_runtime_gate.py sps2/tests/test_updater_safety.py` | Exit 1: pytest is not installed. No dependency was installed. |
| `python3 -B -m unittest sps2.tests.test_p10_runtime_gate sps2.tests.test_updater_safety` | Exit 0; 333 tests; 1 skip (`pwsh` unavailable); 2 resource warnings. |
| `python3 -B -m sps2.tools.p10_runtime_gate --slice sps2/project/SLICE-P10-01.json` | Exit 1; real gate correctly FAIL as detailed in §9. |
| `python3 -B -m unittest discover -s domain/frontend/tests -t . -p 'test_*.py'` | Exit 0; 85 tests. |
| `python3 -B -m unittest discover -s domain -t . -p 'test_*.py'` | Exit 1: `domain` is not importable for unittest discovery; environment/discovery issue, not a product assertion. |
| `python3 -B -m unittest discover -s domain/cms/tests -t . -p 'test_*.py'` | Exit 0; 86 tests. |
| `python3 -B -m unittest discover -s domain/seo/tests -t . -p 'test_*.py'` | Exit 1; 220 tests; 4 failures, all tied to dirty legacy paths/orphan-reference assumptions in the current worktree. |
| `python3 -B -m unittest discover -s sps2/tests -t . -p 'test_*.py'` | Exit 1: `sps2/tests` is not importable for unittest discovery; environment/discovery issue, not a product assertion. |
| Explicit 11-module `sps2.tests.*` invocation | Exit 0; 597 tests; 2 skips. |
| `bash -n` on both bootstrap copies, both Bash updater copies, and `get-sps.sh` | Exit 0 for all five. |
| `cmp -s` for Bash updater, PowerShell updater, and bootstrap mirrors | Exit 0 for all three. |
| `diff -rq scripts skills/sps/scripts` | Exit 0; mirror tree identical. |
| `git diff --check` | Exit 0. |
| `bash scripts/lint-sps.sh` | Exit 0. |
| `python3 -B sps2/tools/check_sps2.py decision sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json` | Exit 0; no `ERR` lines. |
| `python3 -B sps2/tools/check_sps2.py decision sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json` | Exit 0; no `ERR` lines. |
| `python3 -B sps2/tools/check_sps2.py decision sps2/decisions/P10-ROUND12-USER-DECISIONS.json` | Exit 0; no `ERR` lines. |
| `python3 -B sps2/tools/check_sps2.py decision sps2/decisions/P10-DELEGATED-DECISIONS.json` | Exit 0; no `ERR` lines. |
| `python3 -B sps2/tools/check_sps2.py decision sps2/decisions/P10-DECISIONS.json` | Process exit 0, but 10 `ERR` lines: legacy `D-P10-*` IDs fail the current decision-ID pattern. |
| `python3 -B sps2/tools/check_sps2.py evidence sps2/evidence/P10-EVIDENCE.json` | Exit 0; no `ERR` lines. |
| `python3 -B sps2/tools/check_sps2.py inventory ...` | Exit 2; `inventory` is not a supported kind. Historical claims using that kind could not be reproduced. |

The first combined `sps2` module attempt failed once because a zsh variable was
named `modules`, which is read-only in this shell. It was rerun with
`test_modules`; this was a command-shell issue, not a repository failure.

## 11. Findings ranked by severity and confidence

| ID | Severity | Confidence | Status | Finding |
|---|---|---|---|---|
| F-001 | High | High | VERIFIED DEFECT | Installer removes managed global destinations before a verified replacement/backup exists (`install.sh:254-263`, `install.ps1:175-182`). A failed copy can lose user modifications. Requires User decision. |
| F-002 | Medium | High | VERIFIED | P10 evidence contains stale authorization/implementation wording (`sps2/evidence/P10-EVIDENCE.json`). Requires User decision. |
| F-003 | Medium | High | VERIFIED ENVIRONMENT RISK | SEO isolation tests fail against the intentionally dirty shared worktree. This can mask product regressions if broad suite results are read without distinguishing worktree sensitivity. |
| F-004 | Low | High | VERIFIED LIMITATION | PowerShell updater runtime behavior was not exercised because `pwsh` is unavailable; static and mirror checks passed. |
| F-005 | Low | High | VERIFIED GOVERNANCE RISK | `check_sps2.py` always exits 0, even for controlled `ERR` output; tests pin this behavior (`sps2/tests/test_attribution_policy.py:948-988`). Consumers must inspect stdout. Changing it requires coordination. |
| F-006 | Low | High | VERIFIED | `P10-DECISIONS.json` has ten legacy `D-P10-*` IDs rejected by the current decision-ID validator. Renaming recorded IDs would rewrite governance history and requires a User decision. |
| F-007 | Informational | High | VERIFIED EXPECTED | Real P10 gate exits 1 with seven legitimate prerequisites unmet. |

No Critical-severity finding was verified in the authorized scope.

## 12. Independent review findings and counterexamples

No independent Claude agent was available through a supported mechanism. A
second-pass Codex review checked the live implementation against source, tests,
and real-gate behavior rather than copying summary claims.

Counterexamples checked:

1. A declared operation as a string must fail; it does.
2. A manifest operation absent from the declaration must fail; it does.
3. A declared operation absent from the manifest must fail; it does.
4. A gate record with only one required field must fail; it does.
5. A nonzero-offset timestamp must fail; it does.
6. A malformed SHA-256 claim must fail; it does.
7. A claimed path outside the repository root must fail; it does.
8. A modified output artifact must contradict its digest claim; it does.
9. A missing manifest must fail even for empty declared operations; it does.

These checks are independent of the original implementer only in the limited
sense that this session re-derived and reran them; they are not a separate-agent
review.

## 13. Initial-versus-final file fingerprints and worktree status

The implementation/test fingerprints listed in §3 were unchanged during this
session. No pre-existing tracked or untracked file was overwritten, deleted,
moved, staged, or committed.

Final status before this report was identical to the initial status. Because
`reports/` was already an untracked directory, adding this single report is not
expected to add a new porcelain status entry; it adds one file inside the
already-untracked `reports/` tree. Immediate post-report verification is recorded
in §15.

## 14. Remaining risks and limitations

- No network operation was performed, so external installer behavior and remote source integrity remain unverified.
- No installer or updater was executed against the real environment.
- PowerShell runtime coverage is skipped without `pwsh`.
- The SEO suite is worktree-sensitive in the current shared dirty tree.
- No separate independent agent review occurred.
- `pytest` is unavailable; verification used the repositories' standard-library `unittest` entry points.
- Governance validators are stdout-based; process exit 0 does not mean “no errors.”
- The inventory transition’s original attribution remains unresolved.

## 15. Exact decisions needed from the User

1. **Installer preservation implementation:** authorize the transactional backup/restore design in §7, including consent, dirty detection, staging, backup manifest, atomic replacement, recovery command, and cross-platform parity. This overlaps the deferred global-write policy and must not be inferred from prior authorization.
2. **P10 evidence factual correction:** authorize the exact replacement text in §8 for `governance_discrepancy` and `blocked_reason`, or provide preferred wording. This should not change `result`, approval, publication, or closure semantics.
3. **`check_sps2.py` exit-code contract:** decide whether to preserve the documented always-zero/stdout-based contract or coordinate a breaking exit-code change with its consumers and tests.
4. **Legacy `D-P10-*` decision IDs:** choose whether to preserve historical IDs with a validator compatibility exception, migrate IDs with an explicit governance-history plan, or leave the visible validator errors as an accepted boundary.
5. **Optional forensic attribution:** authorize a separate investigation if the original inventory-state transition must be attributed beyond the now-authorized digest values.
6. **Optional Git handling:** staging/commit remains unauthorized; a separate explicit grant is required if these working-tree changes should be preserved in Git history.

## 16. Items intentionally not changed

- No production source, test, schema, decision, inventory, evidence, CMS, configuration, CI, or historical report was changed by this session.
- No installer, uninstaller, bootstrap, updater, or CI smoke command was executed.
- No dependency was installed.
- No network repository was accessed.
- No file was staged, committed, pushed, fetched, pulled, reset, reverted, stashed, switched, cleaned, or deleted.
- No publication state was changed.
- No `user_approval` was created or changed.
- No inventory digest was regenerated.
- No backend operations manifest was created.
- No historical report was overwritten.

## 17. Coordination notes for Claude’s active P10 work

- The P10 gate fixes are confined to the runtime gate and its test module; the six adopted DEC-7112 semantics were not broadened.
- The schema, slice, inventory, evidence, decisions, renderer, CMS data, and frontend tests were treated as pre-existing P10 work and preserved.
- The backend operations manifest remains intentionally absent.
- The installer preservation design does not touch P10 files.
- Any P10 publication, approval transition, inventory regeneration, backend manifest creation, or Git tracking still requires a fresh, explicit User decision.

## 18. Final side-effect verification

Expected final worktree delta from this session:

```text
NEW FILE: reports/SPS2-ROUND16-AUTONOMOUS-ENGINEERING-20261016-182330.md
```

All other pre-existing modifications and untracked paths remain preserved. The
post-write verification command checks that this file is nonempty and that the
staged diff remains empty.

## 19. Limitations and unverified areas

- The report does not certify production readiness.
- The report does not prove human identity or approval authenticity.
- The report does not verify network installer behavior.
- The report does not establish attribution for every historical working-tree change.
- The report does not claim the real P10 gate passes; it correctly fails.

Stop here. No further implementation or Git action was taken.
