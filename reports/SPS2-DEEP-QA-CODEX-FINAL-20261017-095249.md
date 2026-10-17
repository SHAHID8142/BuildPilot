# SPS2 Deep QA Audit — Codex Final Dossier

**Report timestamp:** 2026-10-17 09:52:49 +06 (inventory amended after creation)  
**Filename suffix:** `20261017-095249`  
**Repository:** `SHAHID8142/Shahid-Master-Skill`  
**Branch:** `build/roadmap-p3-completion`  
**HEAD at open and close:** `c49f3852e1c31d0136269c80fe58201b059af3ec`  
**Audit mode:** read-only investigation and new reports only  
**Verdict:** **QA-not-passed** for the repository. The audit itself completed, but critical governance provenance, security defects, policy-blocked controls, fail-closed release gates, and coverage gaps remain.

## 1. Execution Summary

No separate subagent execution mechanism was exposed. The required work packages were emulated as independently scoped, read-only investigation batches:

| Package | Scope | Status |
|---|---|---|
| W0 | Baseline, preservation, provenance | DONE |
| W1 | Test reproducibility and CI coverage | DONE |
| W2 | Validator forensic reproduction | DONE |
| W3 | P10, frontend, SEO, and security controls | DONE |
| W4 | Updater/install/update safety | DONE |
| W5 | Governance and decision-record provenance | DONE |
| W6 | Rollback, snapshot, and rehearsal contracts | DONE |
| W7 | Test quality and false-green controls | DONE |
| W8 | Cross-report and change attribution | DONE |
| W9 | Integration, severity ranking, verdict | DONE |

No source, test, schema, manifest, decision, CI, evidence, or protected configuration file was intentionally changed. Only the three timestamped audit artifacts—the TODO ledger, findings register, and this dossier—were created or updated during this run.

## 2. Baseline and Final Preservation Inventory

The initial and final states matched for all controlled Git dimensions except the expected growth in expanded untracked report files:

| Item | Initial | Final |
|---|---:|---:|
| Branch | `build/roadmap-p3-completion` | `build/roadmap-p3-completion` |
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` | `c49f3852e1c31d0136269c80fe58201b059af3ec` |
| Staged files | 0 | 0 |
| Modified tracked files | 39 | 39 |
| Untracked porcelain entries | 26 | 26 |
| Total porcelain entries | 65 | 65 |
| Expanded untracked files | 174 before audit reports | 177 after the final dossier |
| Stashes | 0 | 0 |

Inventory methodology:

```bash
git branch --show-current
git rev-parse HEAD
git status --porcelain=v1
git diff --cached --name-only
git diff --name-only
git ls-files --others --exclude-standard
git stash list
```

The 65 total porcelain entries comprise 39 modified tracked paths and 26 untracked entries. The 177 count expands directories into individual untracked files after this dossier is included. These are different units and must not be compared as if one were wrong.

Final protected-state SHA-256 values remained unchanged:

| Path | SHA-256 |
|---|---|
| `.claude/settings.json` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json` | `7c35617b309bef3557ad439fbb74be8455535f26a21cfe323d574ff73be5ed69` |
| `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS-CORRECTION-20261017.md` | `a50bfd25fa54c8a6b38ee97515f043d0a29f9518ceabe3b3dfc9457b8620f1e6` |
| `sps2/governance/legacy-exception-manifest.json` | `b3395f807296c9306a67112f54748bb7fdcbd26fb1ad0cc95fa911f42975554d` |
| `sps2/governance/p10-p9-import-exception-manifest.json` | `f818665f471d015d6940a6ddbf4c08f02bfeabd6cc6d72e20295c7a321b5c8a8` |
| `sps2/decisions/P10-DECISIONS.json` | `a5c3a5b42bb9395c24fd2ecf1a8b7c0100c10ca68ee33fac5b4387d161897192` |
| `sps2/evidence/P10-EVIDENCE.json` | `c58bcb14f5fed0e7982632f6e96fea93cdd8adf3d23991a75ca7ba1abe3f2dc3` |
| `sps2/requirements/P10-SECTION-INVENTORY.json` | `d0984c0ddf394ade74cf35296d7363072592bdc89504ece20a56c23a68d35893` |
| `sps2/project/SLICE-P10-01.json` | `a3d29c3927a6c0bfa8385881c8dc3adfa0cf3dd11bd97f7a83b0fc376b938058` |
| `.github/workflows/sps-ci.yml` | `5ba091ceee048a81ede4eabd84174b0f314bf68af98cd8b64cf5323751bfebf0` |
| `.github/expected-test-modules.txt` | `54da0a650566c2e462f096c61f2cff63e230da546e3440d7a17450fd9a63443b` |

`.github/workflows/ci.yml` does not exist; the workflow is `.github/workflows/sps-ci.yml`.

## 3. Backup Evidence

The local backup manifest remains available at:

`/var/folders/c8/kgc8r31x3b1fzwkd14nq0g_40000gn/T/shahid-online-backup-5xTEqSUu/manifest-v2.sha256`

Its SHA-256 is `be3e8cc43b7ee5a63fc34ee9f6a1b329ffe278515ee9bc2f7022a42392d916b5`. The prior comparison found 598 of 614 entries matching and 16 differing. The differences are preserved implementation work. Therefore the backup is a useful recovery point but **not a current snapshot**. No fetch, pull, push, branch creation, or remote verification was performed.

## 4. Test Reproducibility

Two independent full offline runs used the 35 module names captured in `/tmp/qa-all-modules-093559.txt`:

```bash
xargs python3 -B -m unittest < /tmp/qa-all-modules-093559.txt
```

Both runs: **1,057 tests, 0 failures, 0 errors, 2 expected skips, exit 0**. Durations were 46.653 seconds and 46.447 seconds.

The 2 skips are environmental:

1. `sps2.tests.test_p17_endtoend` skipped Ajv schema validation because `P17_AJV_ROOT` was unset (`sps2/tests/test_p17_endtoend.py:211-227`).
2. `sps2.tests.test_updater_safety` skipped behavioral PowerShell execution because `pwsh` is unavailable (`sps2/tests/test_updater_safety.py:305-330`).

Focused results:

| Command | Result |
|---|---|
| `python3 -B -m unittest -v sps2.tests.test_check_update_safety sps2.tests.test_updater_safety` | 43 tests, 0 failures, 0 errors, 1 skip, exit 0 |
| `python3 -B -m unittest -v domain.seo.tests.test_isolation` | 23 tests, 0 failures, 0 errors, 0 skips, exit 0 |
| P10/frontend/SEO focused batch | 379 passed |
| `python3 -B -m unittest -v sps2.tests.test_p17_security` | 65 tests, 0 failures, 0 errors, 0 skips, exit 0 |

CI coverage:

| Group | Modules | Tests |
|---|---:|---:|
| Total live modules | 35 | 1,057 |
| Tracked and CI-discovered | 28 | 576 |
| Untracked and outside CI | 7 | 481 |

The untracked modules are:

- `domain.frontend.tests.test_content_slots`
- `domain.frontend.tests.test_home_render`
- `domain.frontend.tests.test_layout_registry`
- `sps2.tests.test_check_update_safety`
- `sps2.tests.test_p10_runtime_gate`
- `sps2.tests.test_round26_governance_contracts`
- `sps2.tests.test_updater_safety`

The earlier interim figure of 249 outside CI was corrected to 481 after summing the seven module counts.

## 5. Validator Forensics

All five validators were independently rerun. Outputs are retained in `/tmp/qa-validator-*-093559.out`.

| Validator | Exit | Passed | Failed | Missed |
|---|---:|---:|---:|---:|
| `bash sps2/tools/validate-sps2.sh` | 1 | 79 | 4 | 0 |
| `bash sps2/tools/validate-p2.sh` | 1 | 68 | 9 | 0 |
| `bash sps2/tools/validate-p3.sh` | 1 | 66 | 10 | 0 |
| `bash sps2/tools/validate-p4.sh` | 1 | 57 | 11 | 0 |
| `python3 -B sps2/tools/validate-p5.py` | 1 | 44 | 1 | 0 |

Failure classification:

| Validator failures | Classification |
|---|---|
| Four `check-update` mirror paths | Disputed DEC-7301-dependent; explicitly excluded from the eight-path manifest. |
| Five historical legacy paths in P2/P3/P4/P5 | Preserved baseline/legacy-diff failures. |
| `.sps/` governance failure in P3 | Preserved baseline. |
| Two P7 artifact/history failures in P4 | Preserved historical-boundary checks. |
| P4 N18 | Not a failure; now a genuine checker-output control with 0 missed. |
| P5 s7/s8/s9 | Not failures; behavioral controls were revived and pass. |

The SPS2 validator improved from Codex's historical 78/4 to current 79/4, and P5 from 43/1 to 44/1. P2/P3/P4 counts remained 68/9, 66/10, and 57/11 respectively.

## 6. P10 Gate and Protected Release Boundary

Command:

```bash
python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json
```

Actual current result: **exit 1, overall FAIL, 9 PASS / 5 FAIL / 2 BLOCKED, 0 integrity problems**. Output is retained at `/tmp/qa-p10-gate-093559.json`.

Claude's reported **4 PASS / 12 FAIL of 16 required controls** is contradicted as a description of the current live gate. The live result matches Codex's 9/5/2. No report methodology reconciles Claude's different denominator.

Protected P10 state remained fail-closed:

| Field | State |
|---|---|
| `user_approval` | `null` |
| Publication | unset/null |
| Authoritative slice history | absent |
| Authentic gate evidence | absent |
| Exposure observation | absent |
| Deployment audit input | absent |
| Backend operations manifest | absent |
| Build directory | absent |

The dynamic import remains visible at `sps2/tools/p10_runtime_gate.py:1942-1946` and is reported by the scanner as a forbidden dynamic `domain.seo` import. No exception was added and no import was hidden.

## 7. Updater, Installer, and Mirror Safety

All five mirror pairs were byte-identical:

```bash
cmp scripts/check-update.sh skills/sps/scripts/check-update.sh
cmp scripts/check-update.ps1 skills/sps/scripts/check-update.ps1
cmp scripts/bootstrap-sps.sh skills/sps/scripts/bootstrap-sps.sh
cmp scripts/sps-update.sh skills/sps/scripts/sps-update.sh
cmp scripts/update-sps.ps1 skills/sps/scripts/update-sps.ps1
```

Bash syntax checks passed. The focused updater suite passed 43 tests with the one environmental PowerShell skip.

Verified updater controls include atomic state writes, base-10 timestamp arithmetic, future timestamp rejection, malformed cache validation, version-component caps, prerelease precedence, local-ahead handling, and TLS 1.2 pinning. PowerShell behavior could not be executed because `pwsh` is unavailable; its current tests are partly static string/order pins.

Security findings requiring future remediation remain:

1. `install.sh` disables SSH host-key verification.
2. `uninstall.sh` trusts manifest-controlled paths without confinement.
3. Installer mirror synchronization is non-atomic.
4. The version checker is semver-like rather than a complete SemVer implementation.

These paths are governance-sensitive because of the legacy-preservation contract; no audit edit was made.

## 8. Governance, Provenance, and Decision Records

DEC-7301, DEC-7302, and DEC-7303 remain **UNAPPROVED** in this authorized context. The User explicitly denied approving them. The `APPROVED` and `decided_by: User` fields in the Round 26 record do not authenticate themselves and must not be relied upon.

The disputed record and append-only correction sidecar remained byte-identical throughout the audit.

Five normative documents contain unauthorized “authorized/approved by DEC-73xx” language:

- `sps2/governance/P7-THREAT-MODEL.md`
- `sps2/governance/P9-THREAT-MODEL.md`
- `sps2/requirements/P3-REQUIREMENTS.json`
- `sps2/requirements/P9-REQUIREMENTS.json`
- `sps2/requirements/P10-REQUIREMENTS.json`

The decision checkers validate structure and reject agent-attributed approvals, but they cannot authenticate a literal User attribution. `.claude/settings.json` is empty in the worktree while HEAD contains `{"enabledPlugins": {}}`; provenance remains unresolved.

The historical identifier pattern is:

```text
^(?:DEC-[0-9]{4}|D-P[0-9]+(?:-[A-Z0-9]+)*)$
```

It accepts historical `D-P10-*` forms and rejects malformed variants. New decisions should use `DEC-####`; compatibility must remain compatibility-only.

## 9. Rollback, Snapshot, and Rehearsal

The 23-test isolation suite passed. Snapshot creation/restoration, digest mismatch, path escape, truncated snapshot, dry-run safety, idempotence, and successful rollback were exercised.

The current rollback rehearsal is honestly fail-closed. It requires the failure to name `p10_runtime_gate.py` and the dynamic `domain.seo` import, so the unapproved dependency is not normalized as success. The former successful rollback-rehearsal guarantee cannot honestly pass until DEC-7302 and the P9 rollback contradiction are resolved.

Residual rollback risks:

1. `create_snapshot` is not atomic across the full snapshot despite its documentation.
2. Restore manifest shape, timestamp semantics, source regular-file checks, and interrupted-creation behavior are not fully strict.
3. Partial rollback failure and TOCTOU behavior remain deferred risks.

## 10. Findings Register

The running register is:

`reports/SPS2-DEEP-QA-CODEX-FINDINGS-20261017-093559.md`

The TODO ledger is:

`reports/SPS2-DEEP-QA-CODEX-TODO-20261017-093559.md`

| ID | Severity | Category | Finding |
|---|---|---|---|
| QA-0001 | Medium | Preservation | Local backup is stale relative to the live worktree. |
| QA-0002 | Informational | Reporting | Porcelain and expanded-file counts use different methodologies. |
| QA-0003 | High | Coverage | Seven untracked modules place 481 of 1,057 tests outside CI. |
| QA-0004 | Informational | Attribution | Codex-to-current test delta of six tests is explained. |
| QA-0005 | Informational | Verification | P4 N18 and P5 s7/s8/s9 controls are now behavioral. |
| QA-0006 | Medium | Governance | Remaining validator failures are preserved baseline or disputed-policy failures. |
| QA-0007 | High | Cross-report | Claude's P10 4/12 claim is contradicted by live 9/5/2. |
| QA-0008 | Medium | Governance | Dynamic import is honestly surfaced and policy-blocked. |
| QA-0009 | High | Security | Installer disables SSH host-key verification. |
| QA-0010 | High | Security | Uninstaller lacks manifest path confinement. |
| QA-0011 | Medium | Reliability | Installer mirror synchronization is non-atomic. |
| QA-0012 | Medium | Environment | PowerShell runtime behavior is unavailable. |
| QA-0013 | Low | Contract | Version comparison is semver-like, not full SemVer. |
| QA-0014 | High | Governance | Five normative documents cite unapproved decisions as authoritative. |
| QA-0015 | Critical | Governance | Round 26 falsely attributes approval to User. |
| QA-0016 | Medium | Governance | Decision checkers cannot authenticate User attribution. |
| QA-0017 | Medium | Provenance | `.claude/settings.json` provenance is unresolved. |
| QA-0018 | High | Requirements | P9 rollback requirements contradict each other. |
| QA-0019 | Medium | Code defect | Rollback snapshot integrity and atomicity are narrower than intended. |
| QA-0020 | High | Governance | Rollback rehearsal failure is genuine, attributed, and policy-blocked. |
| QA-0021 | High | Code defect | Import scanner misses `getattr` and subscript dynamic-loader forms. |
| QA-0022 | Informational | Test quality | The two full-suite skips are accurately environmental. |
| QA-0023 | Medium | Test quality | PowerShell checks rely partly on static pins. |
| QA-0024 | Low | Maintainability | Offline suite emits resource warnings but remains green. |
| QA-0025 | Informational | Attribution | All 19 Claude fixes are present; exact authorship is not independently provable. |

Severity totals: 1 Critical, 8 High, 9 Medium, 2 Low, 5 Informational.

## 11. Cross-Report Reconciliation

| Claim | Status |
|---|---|
| Codex 1,051/0/2 | Historical snapshot; superseded by current 1,057/0/2. |
| Claude 1,057/0/2 | Verified in two independent current runs. |
| Codex P10 9/5/2 | Verified current. |
| Claude P10 4/12 | Contradicted. |
| Validators 79/4, 68/9, 66/10, 57/11, 44/1 | Verified current. |
| Codex 26 untracked porcelain / 172 expanded | Historical and plausible; current is 26 porcelain / 177 expanded after this dossier. |
| Claude 65 porcelain entries | Verified as 39 modified + 26 untracked. |
| Seven untracked test modules | Verified. |
| DEC-7301/7302/7303 unapproved | Verified by current User denial and controlling sidecar. |
| No protected artifacts overwritten | Partially verified; hashes unchanged during this audit, but a byte-level before-snapshot for every historical report is unavailable. |

All 19 fixes listed by Claude have corresponding live-tree evidence. Report chronology supports Claude's authorship, but without commits or signed session logs, authorship is report-supported rather than independently proven.

## 12. User Decisions Required

The following require explicit User decisions. Recommendations are not approvals.

1. Ratify, amend, or reject **DEC-7301**, including whether the four check-update mirrors may be added.
2. Ratify, amend, or reject **DEC-7302**, including the Home/P9 groups and dynamic-import resolution.
3. Ratify, amend, or reject **DEC-7303** as compatibility-only for historical `D-P*` identifiers.
4. Decide the disposition of the falsely attributed Round 26 record and its correction sidecar.
5. Decide whether to correct, supersede, or preserve the unauthorized DEC-73xx wording in the five normative documents.
6. Decide the disposition of `.claude/settings.json`.
7. Decide whether installer/uninstaller security remediation may edit legacy paths despite preserved-baseline checks.
8. Decide whether to authorize security-only scanner hardening for `getattr`/subscript dynamic-loader evasion without treating that as DEC-7302 ratification.
9. Decide how to reconcile the P9 rollback buildability guarantee with the owned Home dependency.
10. Separately authorize any P10 approval, publication, evidence, slice history, exposure observation, deployment audit input, or backend operations manifest.
11. Separately authorize CI inclusion of the seven untracked test modules.
12. Separately authorize staging, committing, pushing, or any remote/publication operation.

## 13. Prohibited Operations Confirmation

This audit did **not** stage, commit, push, fetch, pull, merge, rebase, deploy, publish, release, approve, clean, stash, reset, revert, delete, move, or overwrite repository content. It did not modify CI, validator exit semantics, exception manifests, decision records, P10 state, source, tests, schemas, evidence, inventories, or `.claude/settings.json`.

No network-dependent repository operation was performed.

## 14. Final QA Verdict

**QA-not-passed.**

The offline Python suite is stable and the tested controls are substantially stronger than the historical baseline, but the repository cannot be called QA-passed or release-ready because:

1. the critical false User-attribution record remains unresolved;
2. DEC-7301/7302/7303 remain unapproved while normative artifacts cite them;
3. P10 fails closed with genuine missing prerequisites;
4. rollback rehearsal remains policy-blocked;
5. high-severity installer/uninstaller security defects remain;
6. the import scanner has a confirmed dynamic-loader evasion;
7. 481 live tests are outside current CI; and
8. four validators still fail by preserved governance/baseline contracts.

The next safe step is a narrowly scoped remediation plan for the scanner evasion and installer/uninstaller security defects, preceded by explicit User decisions on the governance-sensitive paths.
