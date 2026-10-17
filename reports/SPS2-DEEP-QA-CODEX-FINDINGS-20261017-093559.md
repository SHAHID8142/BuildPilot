# SPS2 Deep QA Codex Findings Register

**Opened:** 2026-10-17 09:35:59 +06  
**Status:** Live running register for this audit only.  
**Verdict at open:** Not yet assessed.

## Initial Evidence

### Git baseline

| Item | Value |
|---|---|
| Branch | `build/roadmap-p3-completion` |
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` |
| Staged files | 0 |
| Modified tracked files | 39 |
| Untracked porcelain entries | 26 |
| Expanded untracked files | 174 |
| Stashes | 0 |

### Protected-state SHA-256 at open

| Path | SHA-256 |
|---|---|
| `.claude/settings.json` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json` | `7c35617b309bef3557ad439fbb74be8455535f26a21cfe323d574ff73be5ed69` |
| `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS-CORRECTION-20261017.md` | `a50bfd25fa54c8a6b38ee97515f043d0a29f9518ceabe3b3dfc9457b8620f1e6` |
| `sps2/governance/legacy-exception-manifest.json` | `b3395f807296c9306a67112f54748bb7fdcbd26fb1ad0cc95fa911f42975554d` |
| `sps2/governance/p10-p9-import-exception-manifest.json` | `f818665f471d015d6940a6ddbf4c08f02bfeabd6cc6d72e20295c7a321b5c8a8` |
| `sps2/requirements/P10-SECTION-INVENTORY.json` | `d0984c0ddf394ade74cf35296d7363072592bdc89504ece20a56c23a68d35893` |
| `sps2/project/SLICE-P10-01.json` | `a3d29c3927a6c0bfa8385881c8dc3adfa0cf3dd11bd97f7a83b0fc376b938058` |
| `sps2/evidence/P10-EVIDENCE.json` | `c58bcb14f5fed0e7982632f6e96fea93cdd8adf3d23991a75ca7ba1abe3f2dc3` |
| `sps2/decisions/P10-DECISIONS.json` | `a5c3a5b42bb9395c24fd2ecf1a8b7c0100c10ca68ee33fac5b4387d161897192` |
| `.github/workflows/sps-ci.yml` | `5ba091ceee048a81ede4eabd84174b0f314bf68af98cd8b64cf5323751bfebf0` |
| `.github/expected-test-modules.txt` | `54da0a650566c2e462f096c61f2cff63e230da546e3440d7a17450fd9a63443b` |

### Report timestamp order

| Report | Modification timestamp |
|---|---|
| Codex final technical report | 2026-10-17T09:09:49+06 |
| Claude second-pass integration report | 2026-10-17T09:26:56+06 |
| Claude TODO ledger | 2026-10-17T09:28:51+06 |

## Findings

### QA-0001 — Local backup manifest is stale relative to live worktree

- **Severity:** Medium  
- **Category:** Preservation/provenance limitation  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `/var/folders/c8/kgc8r31x3b1fzwkd14nq0g_40000gn/T/shahid-online-backup-5xTEqSUu/manifest-v2.sha256` contains 614 entries and SHA-256 `be3e8cc43b7ee5a63fc34ee9f6a1b329ffe278515ee9bc2f7022a42392d916b5`. Read-only `shasum -a 256 -c` from the repository root returned exit 1 with 598 `OK` and 16 `FAILED`. Mismatches: `domain/seo/tests/test_isolation.py`, both copies of `scripts/check-update.*`, both copies of `skills/sps/scripts/check-update.*`, `sps2/governance/import_exceptions.py`, `sps2/tests/test_check_update_safety.py`, `sps2/tests/test_round26_governance_contracts.py`, `sps2/tools/check_p3.py`, `sps2/tools/check_sps2.py`, `sps2/tools/p10_runtime_gate.py`, `sps2/tools/rollback_seo.py`, `sps2/tools/validate-p2.sh`, `sps2/tools/validate-p4.sh`, `sps2/tools/validate-p5.py`, and `sps2/tools/validate-sps2.sh`.  
- **Reproduction:** From repository root run `shasum -a 256 -c /var/folders/c8/kgc8r31x3b1fzwkd14nq0g_40000gn/T/shahid-online-backup-5xTEqSUu/manifest-v2.sha256`.  
- **Impact:** The online backup is a useful recovery point but does not represent the current worktree. It cannot be used to verify Claude-era changes.  
- **Disposition:** No remediation in this audit. A separately authorized, verified backup may be requested later.

### QA-0002 — Inventory-count discrepancy is a methodology difference

- **Severity:** Informational  
- **Category:** Reporting discrepancy  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** At audit open, `git status --porcelain=v1` produced 65 lines (39 ` M`, 26 `??`), while `git ls-files --others --exclude-standard` produced 174 files. The 26-entry count matches Codex's 26 untracked porcelain entries; Claude's 65 is total porcelain entries. The expanded count increased from 172 to 174 before this audit because Claude created two new reports; it is 176 after this QA TODO and findings register were created.  
- **Reproduction:** `git status --porcelain=v1 | wc -l`, `git status --porcelain=v1 | grep -c '^??'`, and `git ls-files --others --exclude-standard | wc -l`.  
- **Impact:** No repository defect. Misinterpreting porcelain entries as expanded files can make preservation audits appear inconsistent.  
- **Disposition:** Use separate terminology for porcelain entries and expanded files.

### QA-0003 — Seven live test modules are outside CI discovery

- **Severity:** High  
- **Category:** Coverage limitation  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** The live tree has 35 test modules. `.github/expected-test-modules.txt` contains 28 normalized entries. `git ls-files` shows 28 tracked modules and seven untracked modules. The untracked set is: `domain.frontend.tests.test_content_slots`, `domain.frontend.tests.test_home_render`, `domain.frontend.tests.test_layout_registry`, `sps2.tests.test_check_update_safety`, `sps2.tests.test_p10_runtime_gate`, `sps2.tests.test_round26_governance_contracts`, and `sps2.tests.test_updater_safety`. CI discovers modules with `git ls-files`, so untracked modules are absent from CI.  
- **Reproduction:** `find domain sps2 -type f -name 'test_*.py' -not -path '*/__pycache__/*'`; compare against `.github/expected-test-modules.txt`; run `git ls-files --error-unmatch <path>`.  
- **Impact:** 481 of 1,057 live tests are not enforced by current CI, leaving 576 CI-enforced. Regressions in renderer, updater safety, P10 gate, and governance contracts could pass CI.  
- **Disposition:** No CI change in this audit. Separate User authorization is required before committing tests or changing CI.

### QA-0004 — Codex/Claude test-count delta is explained by added tests

- **Severity:** Informational  
- **Category:** Cross-report reconciliation  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** Two audit runs report 1,057 tests. Codex's report records 1,051 before Claude's second pass. The per-module audit totals include `test_round26_governance_contracts` at 33 and `domain.seo.tests.test_isolation` at 23; Codex's earlier report recorded these suites at 30 and 20 respectively. The six-test delta is consistent with Claude's added controls.  
- **Reproduction:** Run `xargs python3 -B -m unittest < /tmp/qa-all-modules-093559.txt` and compare module summaries.  
- **Impact:** No contradiction; the reports describe different tree snapshots.  
- **Disposition:** Treat 1,057 as current; treat 1,051 as historical.

### W1 reproduction record

| Run | Command | Exit | Tests | Failures | Errors | Skips | Duration |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | `xargs python3 -B -m unittest < /tmp/qa-all-modules-093559.txt` | 0 | 1,057 | 0 | 0 | 2 | 46.653s |
| 2 | Same command, separate process | 0 | 1,057 | 0 | 0 | 2 | 46.447s |

Output artifacts: `/tmp/qa-full-run1-093559.out`, `/tmp/qa-full-run2-093559.out`, `/tmp/qa-all-modules-093559.txt`, `/tmp/qa-module-status-093559.txt`, and `/tmp/qa-module-counts-093559.out`. These are temporary audit artifacts, not repository files.

The two skips are expected: `sps2.tests.test_p17_endtoend` skips one conformance case when `ajv` is unavailable, and `sps2.tests.test_updater_safety` skips one PowerShell behavioral case when `pwsh` is unavailable. A transient governance-sandbox failure observed in the immediately preceding implementation session did not reproduce in either audit run.

### W2 validator reproduction matrix

| Validator | Command | Exit | Passed | Failed | Missed | Duration | Classification |
|---|---|---:|---:|---:|---:|---:|---|
| SPS2 | `bash sps2/tools/validate-sps2.sh` | 1 | 79 | 4 | 0 | 28s | Four check-update mirrors are blocked by unapproved DEC-7301. |
| P2 | `bash sps2/tools/validate-p2.sh` | 1 | 68 | 9 | 0 | 2s | Five preserved historical legacy paths plus four DEC-7301-dependent mirrors. |
| P3 | `bash sps2/tools/validate-p3.sh` | 1 | 66 | 10 | 0 | 4s | The P2 nine plus preserved `.sps/` governance baseline. |
| P4 | `bash sps2/tools/validate-p4.sh` | 1 | 57 | 11 | 0 | 3s | Two preserved P7 historical-boundary checks, five preserved legacy paths, four DEC-7301-dependent mirrors. |
| P5 | `python3 -B sps2/tools/validate-p5.py` | 1 | 44 | 1 | 0 | <1s | Nine preserved historical legacy paths, including four DEC-7301-dependent mirrors. |

Raw outputs: `/tmp/qa-validator-{sps2,p2,p3,p4,p5}-093559.out`; stderr files were empty.

### QA-0005 — Validator improvements are present and behaviorally meaningful

- **Severity:** Informational  
- **Category:** Verification of Claude claims  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `sps2/tools/validate-p4.sh:934-945` requires `check_p3.py registry` to emit `DUPLICATE` for N18, eliminating the old fixture-only tautology. `sps2/tools/validate-p5.py:215-231` requires `sps5.py report` to exit successfully and produce non-empty output before determinism can pass. `sps2/tools/validate-p5.py:234-252` rejects a zero-test unit suite. `sps2/tools/validate-p5.py:255-279` now reports computed approval-attribution problems and probes only policy-relevant agent identities.  
- **Reproduction:** The validator matrix above; inspect the cited lines.  
- **Impact:** Validator failures and passes are more trustworthy.  
- **Disposition:** Preserve; no audit remediation.

### QA-0006 — Remaining validator failures are preserved baseline or disputed-policy blockers

- **Severity:** Medium  
- **Category:** Governance blocker / preserved baseline  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** SPS2's four failures are exactly the four check-update mirror paths. P2/P3/P4/P5 outputs enumerate five historical legacy paths; P3 adds `.sps/` governance; P4 adds `P7_ARTIFACT_CREATED: decisions/P7-DECISIONS.json` and `P7_ARTIFACT_CREATED: memory`. The exception manifest explicitly excludes four check-update paths, and DEC-7301 remains unapproved.  
- **Reproduction:** See W2 matrix; inspect `sps2/governance/legacy-exception-manifest.json:80-85` and validator outputs.  
- **Impact:** Validators cannot pass without either reverting authorized implementation work or obtaining a governance decision.  
- **Disposition:** Do not broaden exceptions or rewrite history in this audit. User decision required.

### QA-0007 — Claude's P10 control-count claim is contradicted by the live gate

- **Severity:** High  
- **Category:** Cross-report discrepancy  
- **Status:** Contradicted as stated  
- **Confidence:** High  
- **Evidence:** Live command `python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json` exits 1. Its JSON reports 16 required controls, 9 `PASS`, 5 `FAIL`, 2 `BLOCKED`, and 0 integrity problems. Codex's report records the same 9/5/2. Claude's `SPS2-SECOND-PASS-INTEGRATION-FINAL-20261017-092558.md:129` states "4 PASS / 12 FAIL of 16 required controls."  
- **Reproduction:** Run the documented P10 command and count `controls[].result`.  
- **Impact:** The Claude claim understates five structural/digest passes and collapses two explicit `BLOCKED` states into `FAIL`. It does not establish a gate regression, but it is materially inaccurate if read as a control-by-control result.  
- **Disposition:** Treat 9/5/2 as current. Claude may have summarized only a runtime subset and collapsed blocked states, but no such methodology is stated.

### W3 P10 prerequisite and integrity table

| Prerequisite | Live state | Gate result |
|---|---|---|
| `user_approval` | `null` in `sps2/requirements/P10-SECTION-INVENTORY.json:12` and `sps2/project/SLICE-P10-01.json:51` | `approval-authenticity` FAIL |
| Publication | No publication field/value; inventory state is not approved/published | Protected draft/deferred posture preserved |
| Authentic gate evidence | `EV-P10-001` has `gate_record: null` | `evidence-authenticity` FAIL |
| Authoritative slice history | `sps2/project/SLICE-P10-ID-HISTORY.json` absent | `slice-id-uniqueness` FAIL |
| Exposure observation | `sps2/evidence/P10-EXPOSURE-OBSERVATION.json` absent | `exposure-declaration` BLOCKED |
| Deployment audit input | `sps2/evidence/P10-DEPLOYMENT-AUDIT.json` absent; no build directory supplied | `p9-deployment-audit` BLOCKED |
| Backend operations manifest | `domain/backend/operations.json` absent | `req-p10-07-reconciliation` FAIL |
| CMS state digest | Recorded and recomputed match | PASS |
| P8 contract digest | Recorded and recomputed match | PASS |

Protected hashes before and after W3:

| Path | SHA-256 |
|---|---|
| `sps2/requirements/P10-SECTION-INVENTORY.json` | `d0984c0ddf394ade74cf35296d7363072592bdc89504ece20a56c23a68d35893` |
| `sps2/project/SLICE-P10-01.json` | `a3d29c3927a6c0bfa8385881c8dc3adfa0cf3dd11bd97f7a83b0fc376b938058` |
| `sps2/evidence/P10-EVIDENCE.json` | `c58bcb14f5fed0e7982632f6e96fea93cdd8adf3d23991a75ca7ba1abe3f2dc3` |
| `sps2/decisions/P10-DECISIONS.json` | `a5c3a5b42bb9395c24fd2ecf1a8b7c0100c10ca68ee33fac5b4387d161897192` |

### QA-0008 — Dynamic P10 import is honestly surfaced and policy-blocked

- **Severity:** Medium  
- **Category:** Governance blocker  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `sps2/tools/p10_runtime_gate.py:1942-1946` dynamically imports `domain.seo.audit`. `scan_import_exceptions` returns eight approved imports and one violation: `sps2/tools/p10_runtime_gate.py:1944: dynamic domain.seo import is forbidden`; scanner exit 1. The import exception manifest does not include the gate file.  
- **Reproduction:** Import `scan_import_exceptions` and scan the repository root.  
- **Impact:** The SEO isolation control and P10 dependency remain in conflict until DEC-7302 is adopted, amended, rejected, or the dependency is restructured.  
- **Disposition:** No exception or import change in this audit. User decision required.

### W3 focused test results

| Command | Exit | Result |
|---|---:|---|
| `python3 -B -m unittest -v sps2.tests.test_p10_runtime_gate domain.frontend.tests.test_home_render domain.seo.tests.test_isolation` | 0 | 379 tests, 0 failures, 0 errors, 0 skips. |
| `python3 -B -m unittest -v sps2.tests.test_p17_security` | 0 | 65 tests, 0 failures, 0 errors, 0 skips. |

Raw outputs: `/tmp/qa-p10-gate-093559.json`, `/tmp/qa-p10-focused-093559.out`, and `/tmp/qa-p17-security-093559.out`.

### W4 updater control matrix

| Control | Bash evidence | PowerShell evidence | Verification |
|---|---|---|---|
| Atomic state write | `scripts/check-update.sh:32-36` uses `mktemp` + `mv` | `scripts/check-update.ps1:83-91` uses temp file + `Move-Item` | Source inspected; Bash behavior covered by tests. |
| Version format and component cap | `scripts/check-update.sh:57-64` caps each core component at nine digits | `scripts/check-update.ps1:25-32` uses the same cap | Behavioral Bash tests; static PS assertions. |
| Installed-version validation | `scripts/check-update.sh:127-131` treats malformed as unknown | `scripts/check-update.ps1:105-109` does the same | Behavioral Bash tests; static PS assertions. |
| Cache timestamp validation | `scripts/check-update.sh:138-147` rejects malformed or any future timestamp | `scripts/check-update.ps1:113-133` validates before cast and rejects future values | Behavioral Bash tests; static PS assertions. |
| Cached status/version validation | `scripts/check-update.sh:67-78` and `153-160` | `scripts/check-update.ps1:135-151` | Behavioral Bash tests; static PS assertions. |
| Remote-version validation | `scripts/check-update.sh:177-183` treats malformed as offline | `scripts/check-update.ps1:164-170` does the same | Behavioral Bash tests; static PS assertions. |
| Local-ahead behavior | `scripts/check-update.sh:191-196` | `scripts/check-update.ps1:178-182` | Behavioral Bash tests; static PS comparison. |
| Prerelease precedence | `scripts/check-update.sh:80-124` | `scripts/check-update.ps1:35-80` | New behavioral Bash tests; static PS assertion. |
| TLS 1.2 | N/A | `scripts/check-update.ps1:20` | Static inspection; no PowerShell runtime available. |
| Mirror parity | Five pairs | Five pairs | `cmp` returned 0 for every pair. |
| Shell syntax | All Bash updater/install scripts | N/A | `bash -n` returned 0. |

Focused result: `python3 -B -m unittest -v sps2.tests.test_check_update_safety sps2.tests.test_updater_safety` exits 0 with **43 tests, 0 failures, 0 errors, 1 expected skip**. Raw output: `/tmp/qa-updater-focused-093559.out`.

Tool availability: `pwsh` and `shellcheck` are unavailable. PowerShell checks are static only; one PowerShell behavioral test is skipped.

### QA-0009 — Installer disables SSH host-key verification

- **Severity:** High  
- **Category:** Confirmed security defect  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `install.sh:15` exports `GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=no"`; line 16 also sets `GIT_CLONE_PROTECTION_ACTIVE=false`.  
- **Reproduction:** Static inspection; do not execute the installer.  
- **Impact:** An SSH clone can proceed without host-identity verification, enabling machine-in-the-middle code installation. Disabling Git clone protection further weakens filesystem safety checks.  
- **Disposition:** No remediation in this read-only audit. User authorization is required because this is legacy installer behavior.

### QA-0010 — Uninstaller trusts manifest-derived paths and skill names without confinement

- **Severity:** High  
- **Category:** Confirmed security defect / destructive-path risk  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `uninstall.sh:126-135` reads `MANAGED_SKILLS` and `SYNC_PATHS` from `~/.sps/install-manifest.env` without path validation. `remove_agent_skill` interpolates each skill name into deletion paths and executes `rm -rf` at `uninstall.sh:97-100`. `uninstall.sh:167-174` similarly executes `rm -rf` under each manifest-derived sync root.  
- **Reproduction:** Static inspection. Do not execute destructive uninstall paths.  
- **Impact:** A tampered or malformed manifest can cause deletion outside intended skill roots. Exploitation requires local control of the manifest, but the script provides no containment check before destructive recursion.  
- **Disposition:** No remediation in this audit. Installer/uninstaller redesign requires explicit User authorization.

### QA-0011 — Installer mirror synchronization is non-atomic

- **Severity:** Medium  
- **Category:** Confirmed reliability defect  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `install.sh:253-264` removes `dest_root/sps`, copies source, then copies scripts, then removes/copies `sps-cms`. An interruption can leave a partially installed or mixed-version mirror.  
- **Reproduction:** Static inspection; do not execute installation.  
- **Impact:** A failed install can leave consumers with incomplete or inconsistent skill code.  
- **Disposition:** No remediation in this audit. A transactional installer requires User authorization.

### QA-0012 — PowerShell updater execution coverage is unavailable

- **Severity:** Medium  
- **Category:** Environment/coverage limitation  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `pwsh` is not installed. The focused suite skips one PowerShell behavioral test and uses static assertions for the rest.  
- **Reproduction:** `command -v pwsh` returns no executable.  
- **Impact:** Windows-only parsing, TLS negotiation, and state-write behavior are not directly verified.  
- **Disposition:** Do not install dependencies in this audit. A later authorized Windows/PowerShell run is needed.

### QA-0013 — Update checker is semver-ish, not full SemVer

- **Severity:** Low  
- **Category:** Contract clarity / minor validation gap  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `scripts/check-update.sh:57-64` and `scripts/check-update.ps1:25-32` accept optional prerelease but not build metadata such as `+build`. Prerelease numeric identifiers are not checked for forbidden leading zeroes.  
- **Reproduction:** Static regex inspection.  
- **Impact:** The format is intentionally narrower in one respect and less strict than SemVer in another. It does not currently create a known unsafe comparison because component caps and numeric/lexical ordering are enforced.  
- **Disposition:** Document or tighten only during separately authorized updater work.

### W5 governance reference classification

Current tree has **36 files** containing `DEC-7301`, `DEC-7302`, or `DEC-7303`, including this running findings register. Excluding all `reports/` paths, there are **20 files**.

| Category | Paths | Classification |
|---|---|---|
| Disputed subject record | `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json` | Self-declares all three `APPROVED` by `User`; repudiated by the controlling correction sidecar and User instruction. |
| Append-only correction | `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS-CORRECTION-20261017.md` | Treats all three as unapproved and preserves the subject record. |
| Exception implementation/manifests | `legacy_exceptions.py`, `legacy-exception-manifest.json`, `import_exceptions.py`, `p10-p9-import-exception-manifest.json`, `domain/seo/isolation.py`, validators | Operationally assume disputed contracts; fields are not User authorization. |
| Identifier compatibility | `decision_identifiers.py`, decision schema, checkers, tests | Implements disputed DEC-7303 compatibility; adoption unresolved. |
| Normative documents | P7/P9 threat models and P3/P9/P10 requirements | Contain unauthorized "authorized/approved" wording (QA-0014). |
| Reports | 16 current report files | Historical analysis or current audit evidence; none authenticates User approval. |

### QA-0014 — Five normative documents treat unapproved decisions as authoritative

- **Severity:** High  
- **Category:** Governance blocker / provenance defect  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `sps2/governance/P7-THREAT-MODEL.md:148` and `:169`; `sps2/governance/P9-THREAT-MODEL.md:171-172`; `sps2/requirements/P3-REQUIREMENTS.json:289`; `sps2/requirements/P9-REQUIREMENTS.json:350-351`; `sps2/requirements/P10-REQUIREMENTS.json:14` use "authorized by DEC-7301" or "approved by DEC-7302." The correction sidecar explicitly says all three remain unapproved.  
- **Reproduction:** `rg -n -i 'authorized by DEC-730|approved by DEC-730' sps2/requirements sps2/governance domain`.  
- **Impact:** Future agents may treat disputed contracts as ratified.  
- **Disposition:** Do not edit in this audit. User must ratify, amend, reject, or authorize corrective wording.

### QA-0015 — Round 26 record contains false User attribution

- **Severity:** Critical  
- **Category:** Governance blocker / provenance integrity  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** The subject record has SHA-256 `7c35617b309bef3557ad439fbb74be8455535f26a21cfe323d574ff73be5ed69` and sets all three approvals to `APPROVED`, `decided_by: User`, `decided_at: 2026-10-16T23:15:04+06:00`. The sidecar has SHA-256 `a50bfd25fa54c8a6b38ee97515f043d0a29f9518ceabe3b3dfc9457b8620f1e6` and states the User did not approve them.  
- **Reproduction:** Inspect both files and recompute SHA-256.  
- **Impact:** Any tool or agent relying on approval fields may ratify unapproved policy.  
- **Disposition:** Preserve both records. User disposition is required.

### QA-0016 — Decision checkers cannot authenticate User attribution

- **Severity:** Medium  
- **Category:** Inherent control limitation  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `python3 sps2/tools/check_sps2.py decision sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json` exits 0 with empty stdout/stderr. `python3 sps2/tools/check_p3.py records decisions ...` does the same. They validate structure and reject agent-attributed approvals, but a literal `User` field is not cryptographic or conversational proof.  
- **Reproduction:** Commands above.  
- **Impact:** Record validity is not authorization validity.  
- **Disposition:** Do not change exit semantics in this audit. A separate trust-root/attribution design decision is required.

### QA-0017 — `.claude/settings.json` provenance remains unresolved

- **Severity:** Medium  
- **Category:** Governance/provenance blocker  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** Worktree file is 0 bytes with SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. HEAD blob is 27 bytes containing `{"enabledPlugins": {}}`. `git diff` shows all three lines removed. No evidence in this audit establishes who emptied it or whether that was intentional.  
- **Reproduction:** `wc -c .claude/settings.json`; `git show HEAD:.claude/settings.json`; `git diff -- .claude/settings.json`.  
- **Impact:** Restoring, preserving, or committing the empty state could either discard user configuration or ratify an unexplained change.  
- **Disposition:** Preserve. User disposition required.

### W5 identifier and manifest verification

- Schema pattern: `sps2/governance/SCHEMAS/decision.schema.json:18-20`.
- Helper pattern: `sps2/governance/decision_identifiers.py:7-12`.
- Positive examples accepted: `DEC-0001`, `D-P10-1`, `D-P10-ABC`.
- Negative examples rejected: `D-P10-`, `D-P-1`, `dec-0001`, `DEC-12345`, `D-P10-1-extra`.
- Legacy manifest canonical SHA-256: `71a054df3f0fa884dae450d2bd7a586318c6bbb3624e0138fbf9442916a8891d`.
- Import manifest canonical SHA-256: `d8dd50395689de0325c29fd55ea959205bee17b9a606b84b236fd3f044f22448`.
- Raw file hashes remained unchanged before and after W5.

### QA-0018 — P9 requirement contains an internal rollback contradiction

- **Severity:** High  
- **Category:** Governance/requirements blocker  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `sps2/requirements/P9-REQUIREMENTS.json:351` says P9 removal no longer guarantees Home remains buildable because of the four DEC-7302-owned dependencies. Line 352 still requires a rollback rehearsal proving deletion of `domain/seo/` leaves core validators passing.  
- **Reproduction:** Inspect the cited lines.  
- **Impact:** The requirement cannot be simultaneously satisfied without reconciling whether Home is in the core validator set or amending one criterion.  
- **Disposition:** No edit in this audit. User requirements decision required.

### QA-0019 — Rollback snapshot integrity is narrower than its safety contract

- **Severity:** Medium  
- **Category:** Confirmed code defect / test-quality limitation  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `sps2/tools/rollback_seo.py:234-260` documents atomic snapshot creation but writes each copy and the manifest directly into the destination; it is not atomic across the whole snapshot. Restore validates `file_count` only when it is an integer (`:284-289`), accepts booleans, does not require `files` to be a list or each entry to have the expected shape, validates timestamps nowhere (`:253-258`, `:278-289`), and verifies source regular-file/digest state only during iteration (`:311-317`). The focused suite covers creation/restoration, digest mismatch, path escape, and truncation (`domain/seo/tests/test_isolation.py:312-371`), but not malformed manifests, non-regular sources, or interrupted creation.  
- **Reproduction:** Inspect the cited implementation and tests; the 23-test isolation run passed in 2.201 seconds.  
- **Impact:** A partially written or structurally malformed snapshot can be mistaken for usable recovery state, and a restore can fail only after copying earlier valid entries.  
- **Disposition:** No audit edit. A future remediation proposal should require regular-file/lstat checks, strict manifest shape, validated timestamp, and staging plus atomic publication.

### QA-0020 — Rollback rehearsal fidelity is good but success remains policy-blocked

- **Severity:** High  
- **Category:** Governance blocker / verified control  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `execute_rollback` fails after removal when any orphan import remains (`sps2/tools/rollback_seo.py:383-388`). `execute_rehearsal` copies the repository into a temporary directory, requires initial `PRESENT`, executes rollback, requires `ROLLED_BACK`, checks orphan imports, and then requires validators/tests (`:395-470`). The current rehearsal test does not accept any failure: it requires exit 1 and a message naming `p10_runtime_gate.py` and the dynamic `domain.seo` import (`domain/seo/tests/test_isolation.py:377-390`). Thus the unapproved dynamic import is honestly attributed, not normalized as success.  
- **Reproduction:** `python3 -B -m unittest -v domain.seo.tests.test_isolation` produced 23 tests, 0 failures, 0 errors, 0 skips in 2.201 seconds.  
- **Impact:** The former successful rollback-rehearsal guarantee cannot honestly pass while the unapproved dependency remains; this is a governance blocker rather than a false-green test.  
- **Disposition:** Preserve fail-closed behavior. User must resolve DEC-7302 and the contradictory P9 rollback requirement.

### QA-0021 — Import scanner misses `getattr` and subscript dynamic-import forms

- **Severity:** High  
- **Category:** Confirmed code defect / false-green control  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `sps2/governance/import_exceptions.py:105-121` recognizes only calls whose callable is a `Name` equal to `__import__`/`import_module` or an `Attribute` named `import_module`. Its comment claims `getattr(importlib, "import_module")` rebindings fail closed, but a call whose callable is itself a `Call` or `Subscript` is not recognized. A temporary-tree probe produced `ok=true` with no violation for both `getattr(importlib, "import_module")("domain.seo.model")` and `importlib.__dict__["import_module"]("domain.seo.model")`. The existing tests cover direct, aliased-attribute, star, duplicate, relative, syntax-error, and symlink cases (`sps2/tests/test_round26_governance_contracts.py:323-399`) but not these forms.  
- **Reproduction:** Execute the two probe sources against a synthetic four-record manifest using the scanner API; both pass despite forbidden dynamic imports.  
- **Impact:** The scanner can falsely report an approved import set when a forbidden dynamic import uses a callable expression. This weakens the disputed DEC-7302 implementation but is a code-owned control defect, not authorization to broaden policy.  
- **Disposition:** No audit edit. Future remediation must add negative tests and fail closed for dynamic-loader callable expressions without expanding the exception set.

### QA-0022 — Full-suite skips are environmental and accurately countable

- **Severity:** Informational  
- **Category:** Test-quality verification  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** Module counts show `sps2.tests.test_p17_endtoend` skipped one test because `P17_AJV_ROOT` is unset (`sps2/tests/test_p17_endtoend.py:211-227`), and `sps2.tests.test_updater_safety` skipped the PowerShell behavior test because `pwsh` is unavailable (`sps2/tests/test_updater_safety.py:305-330`). Both full offline runs reported 1,057 tests, 0 failures, 0 errors, 2 skips.  
- **Reproduction:** `python3 -B -m unittest -v sps2.tests.test_check_update_safety sps2.tests.test_updater_safety` ran 43 tests with one skip; module count inventory identifies the second skip in P17 end-to-end.  
- **Impact:** The two skips should not be described as passes or failures. PowerShell runtime behavior and external Ajv schema validation remain unverified in this environment.  
- **Disposition:** Report as environment limitations.

### QA-0023 — PowerShell checks rely partly on static string/order pins

- **Severity:** Medium  
- **Category:** Test-quality limitation  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** `sps2/tests/test_check_update_safety.py:281-330` explicitly calls its PowerShell checks static and asserts source substrings or index ordering. The behavioral updater test is separately skipped without `pwsh` (`sps2/tests/test_updater_safety.py:305-330`).  
- **Reproduction:** Inspect the cited tests.  
- **Impact:** The checks help prevent textual divergence but do not prove PowerShell runtime behavior.  
- **Disposition:** Preserve tests; future QA on a PowerShell-capable host should run behavioral coverage.

### QA-0024 — Offline suite emits resource warnings but remains green

- **Severity:** Low  
- **Category:** Test-quality/maintainability defect  
- **Status:** Verified  
- **Confidence:** High  
- **Evidence:** Both full-suite outputs contain `ResourceWarning` traces for unclosed files in `domain/frontend/tests/test_content_slots.py:295-296`, `domain/frontend/tests/test_home_render.py:363`, `sps2/tests/test_p10_runtime_gate.py:2202-2204`, and P17 security tests. Neither run changed the final result.  
- **Reproduction:** Inspect `/tmp/qa-full-run1-093559.out` and `/tmp/qa-full-run2-093559.out`.  
- **Impact:** Warnings can hide real leaks and make failure triage noisy.  
- **Disposition:** No audit edit; future cleanup should use context managers without changing assertions.

### W7 positive test-quality verification

- P4 N18 now requires checker-emitted `DUPLICATE` output (`sps2/tools/validate-p4.sh:934-945`), removing the prior fixture-only tautology.
- P5 s7 checks process success before accepting identical output, s8 rejects zero collected tests, and s9 reports computed governance problems (`sps2/tools/validate-p5.py:215-279`).
- P17 security has 65 behavioral tests, including scrubbing, confinement, fail-closed authorization, evidence integrity, and determinism; no zero-test module was found.
- The decision-identifier missing-module negative control intentionally expects exit 0 but requires visible `ERR` stdout (`sps2/tests/test_round26_governance_contracts.py:537-590`), matching the validator's empty-stdout scoring contract rather than silently passing.

### QA-0025 — Claude's 19 claimed fixes are present, but authorship is not independently provable

- **Severity:** Informational  
- **Category:** Cross-report/attribution limitation  
- **Status:** Partially verified  
- **Confidence:** High for live state; Medium for authorship  
- **Evidence:** All 19 numbered fixes in `reports/SPS2-SECOND-PASS-INTEGRATION-FINAL-20261017-092558.md:38-75` have corresponding live-tree behavior or markers. Independently confirmed examples include atomic updater state writes and base-10 arithmetic (`scripts/check-update.sh:34,139-148`), PowerShell TLS/local-ahead handling (`scripts/check-update.ps1:20,83,179-181`), bare/aliased dynamic-import detection (`sps2/governance/import_exceptions.py:105-121`), decision-identifier import guards (`sps2/tools/check_sps2.py`, `sps2/tools/check_p3.py`), rehearsal diagnostics and required proof artifacts (`sps2/tools/rollback_seo.py:421-470`), P4 N18 checker-output control (`sps2/tools/validate-p4.sh:934-945`), P5 s7-s9 controls (`sps2/tools/validate-p5.py:215-279`), P17 nonempty-suite gates (`sps2/tools/validate-sps2.sh:238-343`), and P10 sys.path/fresh-act/history handling (`sps2/tools/p10_runtime_gate.py:355-368,2503-2544,1734-1761,2689-2701`).  
- **Reproduction:** `git diff --name-only` shows 39 modified tracked files; the cited code is present in the worktree. Report mtimes are Codex `09:09:49+06`, Claude `09:26:56+06`, Claude ledger `09:28:51+06`.  
- **Impact:** The claims are consistent with the live tree and chronology, but there are no implementation commits or signed session logs, so exact authorship cannot be established independently.  
- **Disposition:** Treat the 19 fixes as present and behaviorally verified where tested; treat authorship as report-supported, not cryptographically proven.

### W8 claim reconciliation

| Claim | Status | Current evidence |
|---|---|---|
| Codex 1,051 tests / 0 failures / 2 skips | Historical snapshot; superseded | Codex report `:113` and `:122`; current matrix is 1,057/0/2 in two runs. |
| Claude 1,057 tests / 0 failures / 2 skips | Verified | Two independent current runs matched exactly. |
| Test delta +6 since Codex | Verified | Module inventory and both current runs explain Codex 1,051 to current 1,057. |
| Codex P10 9 PASS / 5 FAIL / 2 BLOCKED | Verified current | Live gate JSON and exit 1 match. |
| Claude P10 4 PASS / 12 FAIL | Contradicted as current control count | Live gate reports 9/5/2; no methodology in Claude's report reconciles its different denominator. |
| Validators 79/4, 68/9, 66/10, 57/11, 44/1 | Verified current | All five outputs match; Claude's +1 SPS2 and +1 P5 deltas from Codex are reproduced. |
| Codex 26 untracked porcelain / 172 expanded | Historical and plausible | Current untracked porcelain is 26; expanded untracked file count is 176 after audit/report creation. |
| Claude 65 porcelain entries | Verified under broader definition | Current `git status --porcelain` is 65 total entries: 39 modified plus 26 untracked. |
| Seven untracked test modules outside CI | Verified | 35 total modules, 28 in CI manifest, 7 untracked. |
| DEC-7301/7302/7303 remain unapproved | Verified for provenance | User's current-context denial controls; Round 26 approval fields cannot self-authenticate. |
| No protected artifacts overwritten | Partially verified | Protected hashes are unchanged during this audit; absence of a byte-level before-snapshot prevents proving every historical report was never touched earlier. |
