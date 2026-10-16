# SPS2 Round 26 — Approved Governance Contract Implementation

Timestamp: 2026-10-16 23:33:53 +06:00  
Status: implementation and verification complete. No staging, commit, push, publication, approval-state transition, CI change, installer execution, or remote operation occurred.  
Authorization basis: User Round 26 message received 2026-10-16 at `2026-10-16T23:15:04+06:00`, approving DEC-7301, DEC-7302, and DEC-7303 and separately authorizing decision-record creation, implementation, and the enumerated requirement, threat-model, schema, and validator changes.

## 1. Executive Summary

Implemented and locally verified the three approved Round 25 contracts:

1. **DEC-7301** — fixed-baseline, content-and-mode-pinned exception for exactly eight updater files, with explicit exclusion of all four check-update mirrors and shared use by the foundation, P2, P3, P4, and P5 legacy checks.
2. **DEC-7302** — exact four-group Home/P9 import exception, shared fail-closed scanner, manifest integrity checks, and explicit P9 rollback amendment.
3. **DEC-7303** — historical `D-P*` compatibility only, with all new decisions required to use `DEC-####`, schema/validator agreement, and unchanged duplicate, approval, and exit-code rules.

The broad offline regression suite passed **739 tests, 0 failures, 0 skips**. The focused matrix including P10, updater, frontend, CMS, P9 isolation, attribution, and the new contract suite passed **569 tests, 0 failures, 1 expected PowerShell skip**. The real P10 gate remains correctly blocked with **9 PASS, 5 FAIL, 2 BLOCKED**.

One new unauthorized dynamic `domain.seo` import was found in `sps2/tools/p10_runtime_gate.py:1941`. It is intentionally left unchanged because fixing it is outside the Round 26 scope. The shared scanner keeps it visible.

## 2. Verified Baseline and Fresh Pins

At implementation start and final verification:

- Branch: `build/roadmap-p3-completion`
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`
- Staged diff: empty
- Initial tracked modified paths: 22
- Initial untracked porcelain entries: 18

Fresh inspection found authorized updater work had changed after Round 25:

| Item | Round 25 value | Fresh implementation value |
|---|---:|---:|
| `scripts/sps-update.sh` blob | `ffe2cf6a149565a7ee7543d9bd9091e3d19bb3f2` | `b0e5b8a88480d9cec48b7b03426ed0ea05e4d0a8` |
| `skills/sps/scripts/sps-update.sh` blob | `ffe2cf6a149565a7ee7543d9bd9091e3d19bb3f2` | `b0e5b8a88480d9cec48b7b03426ed0ea05e4d0a8` |
| `sps2/tests/test_updater_safety.py` SHA-256 | `d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b` | `e33af7dcafec03022cf98be2be6ba51d022481604a5b2027e2164b2abce2b59f` |
| Legacy manifest canonical SHA-256 | `sha256:6daa14045f3f6759782c77ffff89ca93edc2a22a3a2095aff30174cf7ca5fe36` | `sha256:71a054df3f0fa884dae450d2bd7a586318c6bbb3624e0138fbf9442916a8891d` |
| Import manifest canonical SHA-256 | `sha256:71d7830ab6748f7c6755d0657f24b0a2075e170c48ba5a6890909a8c46f7ca49` | `sha256:d8dd50395689de0325c29fd55ea959205bee17b9a606b84b236fd3f044f22448` |

The eight updater paths, modes, worktree blobs, and SHA-256 values were recomputed as instructed. The four Home/P9 file/module/symbol groups were re-verified by AST inspection. The Round 25 import groups were unchanged.

## 3. Decision Records and Manifests

Created exactly one new decision wrapper containing the three separately identified decisions:

- `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json`
  - SHA-256: `7c35617b309bef3557ad439fbb74be8455535f26a21cfe323d574ff73be5ed69`
  - DEC-7301, DEC-7302, and DEC-7303 were rechecked as available immediately before creation.
  - Approval attribution is `User`; `decided_at` is `2026-10-16T23:15:04+06:00`.

Created the two integrity-pinned manifests:

| Manifest | Canonical SHA-256 | File SHA-256 |
|---|---|---|
| `sps2/governance/legacy-exception-manifest.json` | `sha256:71a054df3f0fa884dae450d2bd7a586318c6bbb3624e0138fbf9442916a8891d` | `b3395f807296c9306a67112f54748bb7fdcbd26fb1ad0cc95fa911f42975554d` |
| `sps2/governance/p10-p9-import-exception-manifest.json` | `sha256:d8dd50395689de0325c29fd55ea959205bee17b9a606b84b236fd3f044f22448` | `f818665f471d015d6940a6ddbf4c08f02bfeabd6cc6d72e20295c7a321b5c8a8` |

Canonicalization is UTF-8, sorted keys, `,`/`:` separators, `ensure_ascii=false`, no insignificant whitespace, no floats, and no trailing newline. Both helpers parse first, canonicalize, and compare SHA-256 before accepting the manifest.

The DEC-7301 manifest contains exactly eight exceptions and explicitly excludes:

```text
scripts/check-update.ps1
scripts/check-update.sh
skills/sps/scripts/check-update.ps1
skills/sps/scripts/check-update.sh
```

The updater test artifact is evidence only and is not a ninth path exception.

## 4. Implementation Detail

### DEC-7301

- Added `sps2/governance/legacy_exceptions.py`.
- The checker requires an exact manifest shape, canonical hash, exactly eight unique contained paths, regular non-symlink worktree files, exact worktree blob, SHA-256, mode, and a stage-0 blob equal to either the authority baseline or the expected worktree blob.
- Added lexical path containment and `realpath` containment checks. A test found and fixed a symlink-resolution bypass in the first implementation.
- Added `sps2/governance/legacy-exception-manifest.json`.
- Updated `sps2/tools/validate-sps2.sh`, `validate-p2.sh`, `validate-p3.sh`, `validate-p4.sh`, and `validate-p5.py` to use the shared checker while retaining their historical baselines and scopes. P2/P3/P4/P5 explicitly exclude `sps2/`, as their original checks did.
- Amended only the conflicting legacy wording in `REQ-P3-08`, `REQ-P9-10`, `REQ-P10` roadmap bounds, P7 threat model, and P9 threat model. Historical D-P7-C and historical P2 evidence were not rewritten.

### DEC-7302

- Added `sps2/governance/import_exceptions.py`.
- Added `sps2/governance/p10-p9-import-exception-manifest.json` with exactly four groups.
- Replaced divergent logic in `domain/seo/isolation.py` and `sps2/tools/rollback_seo.py` with the shared scanner.
- The scanner rejects module imports, aliased module imports, star imports, unlisted files/modules/symbols, duplicate source symbols, dynamic `domain.seo` imports, syntax errors, symlinked files, traversal, and outside-root paths. Local aliases of approved source symbols remain allowed.
- Rollback status now reports approved imports separately from violations.
- Amended P9 rollback wording to classify the four Home dependencies as owned and to state that P9 removal is coordinated and no longer guarantees Home remains buildable until migration.

### DEC-7303

- Added `sps2/governance/decision_identifiers.py` with:

```text
^(?:DEC-[0-9]{4}|D-P[0-9]+(?:-[A-Z0-9]+)*)$
```

- Changed `sps2/governance/SCHEMAS/decision.schema.json`, `sps2/tools/check_sps2.py`, and `sps2/tools/check_p3.py` to use the exact same anchored pattern.
- Preserved duplicate-ID checks, attribution and approval rules, and validator exit semantics.

## 5. Files Changed by Round 26

### New authorized files

```text
sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json
sps2/governance/legacy-exception-manifest.json
sps2/governance/p10-p9-import-exception-manifest.json
sps2/governance/legacy_exceptions.py
sps2/governance/import_exceptions.py
sps2/governance/decision_identifiers.py
sps2/tests/test_round26_governance_contracts.py
reports/SPS2-ROUND26-CONTRACT-IMPLEMENTATION-20261016-233353.md
```

### Authorized tracked modifications

```text
domain/seo/isolation.py
domain/seo/tests/test_isolation.py
sps2/governance/P7-THREAT-MODEL.md
sps2/governance/P9-THREAT-MODEL.md
sps2/governance/SCHEMAS/decision.schema.json
sps2/requirements/P3-REQUIREMENTS.json
sps2/requirements/P9-REQUIREMENTS.json
sps2/requirements/P10-REQUIREMENTS.json
sps2/tests/test_attribution_policy.py
sps2/tools/check_p3.py
sps2/tools/check_sps2.py
sps2/tools/rollback_seo.py
sps2/tools/validate-p2.sh
sps2/tools/validate-p3.sh
sps2/tools/validate-p4.sh
sps2/tools/validate-p5.py
sps2/tools/validate-sps2.sh
```

Test changes were limited to dependencies required by the isolated checker fixture and to preserving the new fail-closed contract without weakening its controls.

## 6. Commands and Verification Results

All Python commands used `PYTHONDONTWRITEBYTECODE=1`.

| Command | Exit | Result |
|---|---:|---|
| `python3 -m unittest -v sps2.tests.test_round26_governance_contracts` | 0 | 28 tests, 0 failures |
| Focused P10/updater/frontend/CMS/P9/attribution matrix | 0 | 569 tests, 0 failures, 1 skip (`pwsh` unavailable) |
| Broad frontend/CMS/SEO/P10/contract matrix | 0 | 739 tests, 0 failures, 0 skips |
| `python3 -m unittest -v sps2.tests.test_updater_safety sps2.tests.test_check_update_safety` | 0 | 35 tests, 0 failures, 1 PowerShell skip |
| `bash -n` for eight relevant Bash files | 0 | all passed |
| `cmp` for five mirror pairs | 0 | all byte-identical |
| `git diff --check` | 0 | no whitespace errors |
| `bash sps2/tools/validate-sps2.sh` | 1 | 78 passed, 4 failed; failures are the four non-exempt check-update mirrors |
| `bash sps2/tools/validate-p2.sh` | 1 | negative suite passed; 9 preserved legacy failures from concurrent/unrelated paths |
| `bash sps2/tools/validate-p3.sh` | 1 | negative suite passed; 9 preserved legacy failures plus pre-existing `.sps` governance failure |
| `bash sps2/tools/validate-p4.sh` | 1 | negative suite passed; 2 pre-existing P7 artifact failures plus 9 preserved legacy failures |
| `python3 sps2/tools/validate-p5.py` | 1 | 43 passed, 1 failed; failure is nine preserved legacy paths |
| Real `sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json` | 1 | overall FAIL; 9 PASS, 5 FAIL, 2 BLOCKED |
| Decision-ID inventory scan | 0 | 80 records, 80 unique, 0 invalid, 0 duplicates |
| `check_sps2.py decision` over 27 decision files | 0 | new Round 26 file clean; pre-existing errors remain visible |
| `check_p3.py records decisions` over 27 decision files | 0 | new Round 26 file clean; pre-existing errors remain visible |

### Real P10 gate controls

| Control | Result |
|---|---|
| schema-structural | PASS |
| slice-required-fields | PASS |
| evidence-references | PASS |
| layout-slot-conformance | PASS |
| published-only-content | FAIL — content is draft |
| exposure-declaration | BLOCKED — no observed bind |
| slice-id-uniqueness | FAIL — no authoritative history |
| evidence-freshness | PASS |
| evidence-authenticity | FAIL — no gate_record |
| inventory-preconditions | PASS |
| approval-authenticity | FAIL — approval null |
| p9-deployment-audit | BLOCKED — no build directory |
| cms-state-digest | PASS |
| p8-contract-digest | PASS |
| req-p10-07-reconciliation | FAIL — backend operations manifest absent |
| approval-state-interaction | PASS |

The real gate result is expected and was not altered to pass.

## 7. Governance and Protected Boundaries

Verified after implementation:

- `sps2/project/SLICE-P10-01.json:51` has `"user_approval": null`.
- `sps2/requirements/P10-SECTION-INVENTORY.json:12` has `"user_approval": null`.
- CMS publication remains draft.
- `domain/backend/operations.json` remains absent.
- No CI workflow was changed.
- No inventory digest was regenerated.
- No decision was self-approved; the record transcribes the User's explicit Round 26 authorization.
- No historical D-P7-C record was rewritten.
- No historical P2 evidence was edited.
- No staging, commit, push, fetch, pull, reset, clean, stash, publication, deployment, installer execution, dependency installation, or network access occurred.

## 8. Remaining Risks and Unresolved Items

1. **Unapproved dynamic P10 import.** `sps2/tools/p10_runtime_gate.py:1941` dynamically imports `domain.seo.audit`. DEC-7302 does not authorize it. The scanner reports it and the rollback rehearsal remains blocked. A separate User decision is required to remove it or amend the exception.
2. **Preserved validator failures.** The four modified check-update mirrors and other concurrent/unrelated changes intentionally remain visible. They were not added to the eight-path exception.
3. **PowerShell runtime coverage.** `pwsh` is unavailable, so one updater test skipped. Static and mirror checks ran; runtime PowerShell behavior was not verified.
4. **No independent-agent review.** No separate agent reviewed this implementation. The second pass in this round was Codex self-verification and must not be represented as independent-agent review.
5. **Post-commit behavior.** Synthetic tests cover fixed-baseline behavior after content is staged/committed in temporary repositories. The real repository remains unstaged by prohibition.

## 9. Final Worktree and Side-Effect Verification

At final pre-report verification:

- Branch: `build/roadmap-p3-completion`
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`
- Staged diff: empty
- Tracked modified paths: 39
- Untracked porcelain entries: 25

The delta from the initial 22 tracked modifications is exactly the 17 authorized tracked files listed above. The delta from the initial untracked set is the seven authorized implementation files; this report is the eighth intentional new file. All pre-existing concurrent work remains present.

Critical preservation hashes:

```text
2ff1bcbd6184bad44cb1ffbebd3929fb08921dd716574dfb85f9966b6bf8ab97  reports/SPS2-ROUND25-AMENDED-GOVERNANCE-PACKAGE-20261016-223101.md
f175ed77f54cea9d5eeb9a92177ca0a05592639fa03f1cda3e3ecd4dd4b8043d  scripts/check-update.sh
ca00fcea56b182d7c4de0e25203df4a399492658cd557be819f75f8547188002  scripts/check-update.ps1
f175ed77f54cea9d5eeb9a92177ca0a05592639fa03f1cda3e3ecd4dd4b8043d  skills/sps/scripts/check-update.sh
ca00fcea56b182d7c4de0e25203df4a399492658cd557be819f75f8547188002  skills/sps/scripts/check-update.ps1
8567049f7d861b7dcbfe33c165d4cfcd2412c34d7e6cb9e487136e39d8b65192  sps2/p17/scrub.py
f3b37405382af8faabb7dfbaf721eae707b40d97edb130658b2b23aded750e65  sps2/tests/test_p17_security.py
5c02e0035ae4c54fd39c606d7c468643dbac9f9f1f3ccb794f98e3fe01af268c  sps2/tests/test_check_update_safety.py
a3d29c3927a6c0bfa8385881c8dc3adfa0cf3dd11bd97f7a83b0fc376b938058  sps2/project/SLICE-P10-01.json
d0984c0ddf394ade74cf35296d7363072592bdc89504ece20a56c23a68d35893  sps2/requirements/P10-SECTION-INVENTORY.json
```

No further implementation, staging, commit, push, publication, approval, or policy change is authorized by this report.
