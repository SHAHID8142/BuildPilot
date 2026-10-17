# Codex Independent Repository Audit — 2026-10-16 17:13:38 +06:00

## 1. Executive Summary

This was an independent, read-only repository audit. The tracked CI-equivalent Python suite is healthy at the audited baseline: 570 tests ran with one skip and passed in 57.756 seconds. The repository also has substantial fail-closed negative coverage in local P2/P3/P4/P5/P6/P7/P10-inventory validators.

However, repository-wide integrity remains at risk from stale canonical governance state, an unresolved remote/identity conflict, broad and unpinned CI/installer supply-chain surfaces, schema/validator divergence in P8, and several important checks that exist only outside CI. The intentionally red portability suite remains red and must not be treated as a new regression without a User-approved remediation decision.

Claude Code was actively changing P10-related work during this audit. New P10 files appeared after the initial baseline. This audit did not read or modify those files and did not attempt P10 implementation, gate analysis, or Home-slice completion.

## 2. Baseline: Branch, HEAD, and Worktree

- Repository working directory: `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`
- Initial branch: `build/roadmap-p3-completion`
- Initial HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`
- Remote: `origin` → `https://github.com/SHAHID8142/Shahid-Master-Skill.git`
- Upstream: `origin/build/roadmap-p3-completion` at the same commit
- Initial working tree was dirty.

Initial modified tracked files:

```text
.claude/settings.json
.sps/audits/README.md
sps2/decisions/P10-DECISIONS.json
sps2/evidence/P5-EVIDENCE.json
sps2/governance/attribution.py
sps2/requirements/P10-SECTION-INVENTORY.json
sps2/requirements/P5-REQUIREMENTS.json
sps2/schemas/p10-slice.schema.json
```

Initial untracked areas included active P17 evidence/tasks, P10 delegated decisions/tests/tools, `domain/cms/data/`, `domain/frontend/`, all existing `reports/` files, and legacy decision records. No file was staged at the start.

Recent HEAD history:

```text
c49f385 SPS2: fix Version sanity - use fixed-string grep (-qF) for the four literal version guards
ef59f9e SPS2: record DEC-0032 - one authorized push of build/roadmap-p3-completion to origin...
f060703 SPS2: sync the module manifest with the newly tracked P17 gate regression module...
c0a1767 SPS2: record DEC-0031 transcription of the Phase 3 commit authorization...
f059f39 SPS2: register the P7 zero-adapter readiness (D-17) unit tests...
```

## 3. Scope and Exclusions

### In Scope

- Repository architecture, boundaries, ownership, and duplicate responsibilities.
- CI/CD reliability and security.
- Test discovery, CI coverage, local validator coverage, and safe execution.
- Governance, decision integrity, approval attribution, evidence, and schemas.
- Security and safe-execution review of installers, updaters, validators, and P17.
- Documentation and operational reproducibility.
- Maintainability and technical debt.

### Exclusions and Deliberate Non-Actions

- No production code, tests, schemas, governance policy, CI workflow, or documentation was changed.
- No commit, push, fetch, pull, deploy, publish, dependency install, or remote operation was performed.
- No destructive cleanup was run.
- No smoke test was run because `scripts/smoke-sps.sh` can invoke `npx`, install external skills, and access the network.
- No exploit payload was executed.
- No P10 decision package or Home-slice implementation work was duplicated.
- Detailed P10 gate semantics and active P10 artifacts were intentionally left to Claude's active P10 workstream.

## 4. Architecture Inventory

### Major Areas

| Area | Responsibility | Evidence |
|---|---|---|
| Legacy root | SPS 1.x skill, installers, automation, templates, and documentation | `README.md`, `skills/`, `scripts/`, `install.sh`, `get-sps.sh` |
| `sps2/core` | Agent-neutral registry, selection, adapter boundary, and technology readiness primitives | `sps2/core/SPEC.md`, `sps2/core/registry_api.py`, `sps2/core/adapter_registry.py` |
| `sps2/governance` | Governance schemas, attribution policy, threat models, and phase policies | `sps2/governance/SCHEMAS/`, `sps2/governance/attribution.py` |
| `sps2/tools` | Phase validators, promotion gates, SEO tooling, rollback tools, and P10 runtime gate | `sps2/tools/validate-*.sh`, `sps2/tools/validate-*.py`, `sps2/tools/seo_audit.py` |
| `sps2/p17` | Controlled local subprocess runner with allowlist, pinning, scrubbing, and evidence capture | `sps2/p17/*.py`, `sps2/p17/allowlist.json` |
| `domain/cms` | Headless CMS model, validation, persistence, RBAC, publishing, audit, rollback | `domain/cms/*.py` |
| `domain/seo` | SEO metadata, sitemap, structured data, CWV, audit, and isolation logic | `domain/seo/*.py` |
| `domain/frontend` | P10 presentation/layout composition; currently untracked active work | `domain/frontend/*.py`, `domain/frontend/tests/*.py` |
| `.sps` | Legacy/canonical project-state records, audits, governance docs, and validators | `.sps/STATE.md`, `.sps/GOVERNANCE.md`, `.sps/tools/` |
| `reports/` | Point-in-time audit and execution reports; currently untracked | 18 pre-existing reports at baseline |

### Boundary Observations

- `sps2/core` is intentionally agent-neutral and does not import adapters. `sps2/core/adapter_registry.py:112-137` enforces textual import isolation.
- The `domain/` layer is not documented in `sps2/README.md:17-30`, despite being a major executable area.
- `sps2/tools/seo_audit.py:18-23` imports `domain.seo.audit`; `domain/seo/audit.py` references SPS2 schemas. This is a deliberate tool/domain relationship, but the ownership contract is not centralized.
- `domain/cms/rollback.py:21-63` reads `sps2/project/LOCAL-STATE.json`, creating a cross-area runtime flag dependency.
- P10 runtime tooling imports `domain.frontend.layout_registry`, but detailed P10 boundaries were not audited to avoid overlapping Claude's active work.
- Core governance documentation placeholders remain in `sps2/core/gates/GATES.md`, `sps2/core/lifecycle/STATE-MACHINE.md`, and `sps2/core/protocols/PROTOCOLS.md`; enforcement currently lives outside these placeholder docs.

## 5. Test Discovery and CI Coverage

### CI Test Gate

`.github/workflows/sps-ci.yml:83-218` runs a deterministic tracked-file module list with Python 3.12. It:

- refuses zero test modules;
- requires at least 500 executed tests;
- compares discovered modules to `.github/expected-test-modules.txt`;
- checks each module for at least one executed test;
- intentionally excludes the red `sps2/tools/test-portability.py`.

At audit time:

- tracked test modules: 28;
- untracked test modules: 3;
- manifest difference: none;
- actual CI-equivalent run: 570 tests, one skip, exit 0.

Tracked modules span CMS, SEO, attribution, P5, P7, P17, and shell-validator policy tests. The untracked modules were:

```text
domain/frontend/tests/test_content_slots.py
domain/frontend/tests/test_layout_registry.py
sps2/tests/test_p10_runtime_gate.py
```

These are expected to be active work, but they are invisible to CI until tracked. They must not be added to CI automatically without coordination and authorization.

### Local-Only Checks

The following checks exist but are not in CI:

- `sps2/tools/validate-sps2.sh`
- `sps2/tools/validate-p2.sh`
- `sps2/tools/validate-p3.sh`
- `sps2/tools/validate-p4.sh`
- `sps2/tools/validate-p5.py`
- `sps2/tools/validate-p6.py`
- `sps2/tools/validate-p7-readiness.py`
- `sps2/tools/check_p10_inventory.py --self-test`
- `sps2/tools/test-portability.py`
- `sps2/tools/test-history-credential-check.py`

DEC-0032 records that validators-in-CI was explicitly declined in the same User session that authorized one push. Therefore this report does not recommend silently adding validators to CI.

## 6. CI/CD Reliability and Security Findings

### F-01 — CI lacks explicit permissions, action pinning, and concurrency

- Severity: High
- Category: CI/CD security
- Confidence: High
- Type: Verified risk
- Evidence: `.github/workflows/sps-ci.yml:3-14`, `.github/workflows/sps-ci.yml:38-39`, `.github/workflows/sps-ci.yml:74-80`, `.github/workflows/sps-ci.yml:93-101`
- Observed: The workflow has no `permissions:` block, no `concurrency:` control, and invokes `actions/checkout@v4`, `actions/setup-node@v4`, and `actions/setup-python@v5` by mutable tags.
- Impact: A compromised action tag or excessive default token permissions could alter repository state or exfiltrate workflow context. Broad push/pull triggers also allow redundant concurrent runs.
- Likelihood: Low to medium, but impact is high.
- Recommendation: Add least-privilege `permissions: contents: read`, pin actions to full commit SHAs, and add a concurrency group. This is not a validator-in-CI change and still requires explicit authorization because it modifies CI.
- User authorization required: Yes.

### F-02 — CI smoke can install unpinned external skills from the network

- Severity: High
- Category: CI/CD supply chain
- Confidence: High
- Type: Verified risk
- Evidence: `.github/workflows/sps-ci.yml:27-32`; `scripts/smoke-sps.sh:73-107`; `install.sh:337-368`
- Observed: CI sets `npm_config_yes=true` and runs smoke. Smoke can invoke `install.sh`, which invokes `npx skills add` against many external repositories without commit or version pinning.
- Impact: CI correctness depends on mutable upstream content and npm registry behavior. A compromised upstream can execute arbitrary installer code in CI.
- Likelihood: Low, but impact is high.
- Recommendation: Split offline deterministic smoke from installer integration smoke; pin every external source; cache dependencies only with integrity controls. Do not silently weaken the smoke check.
- User authorization required: Yes.

### F-03 — CI and local Python versions differ

- Severity: Low
- Category: CI reliability
- Confidence: High
- Type: Verified observation
- Evidence: `.github/workflows/sps-ci.yml:98-101`; local run used Python 3.14
- Observed: CI pins Python 3.12; the local audit suite ran under Python 3.14 and still passed.
- Impact: Local/CI parity is good but not guaranteed across future standard-library behavior changes.
- Recommendation: Consider a small Python version matrix only after confirming cost/value.
- User authorization required: No for planning; yes for CI changes.

## 7. Governance and Decision-Integrity Findings

### F-04 — Canonical `.sps/STATE.md` is materially stale

- Severity: High
- Category: Governance documentation
- Confidence: High
- Type: Verified defect
- Evidence: `.sps/STATE.md:3-8`, `.sps/STATE.md:19-40`, `.sps/STATE.md:82-116`, `.sps/STATE.md:141-150`
- Observed: `.sps/STATE.md` calls itself canonical, says the current phase is Phase 05, says P1–P16 are not started, says no remote exists, and says nothing was pushed. The live repository contains SPS2 phases P1–P9/P10/P17 artifacts, a configured remote, and pushed branch history.
- Impact: A fresh agent following the documented read order can start from false state and make incorrect governance decisions.
- Recommendation: Require a User-approved reconciliation that either updates `.sps/STATE.md` or explicitly marks it as a legacy point-in-time record and names the current SPS2 state entry point.
- User authorization required: Yes.

### F-05 — Remote, push, and identity decisions remain inconsistent

- Severity: High
- Category: Governance and provenance
- Confidence: High
- Type: Verified unresolved policy conflict
- Evidence: `git remote -v`; `.sps/decisions/DEC-0001-git-init-no-remote.md:37-62`; `.sps/decisions/DEC-0002-local-git-identity.md:73-85`; `sps2/decisions/REMOTE-PUSH-AUTHORIZATION-DECISIONS.json`; `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md:25-48`
- Observed: `origin` is configured. DEC-0001 still says no remote and no push. DEC-0032 narrowly authorized one push of `build/roadmap-p3-completion` and explicitly leaves the wider D1–D5 conflict open. DEC-0002 makes identity replacement due before external sharing, but local identity remains `SPS Governance (local) <sps-governance@local.invalid>`.
- Impact: Future push/publication decisions can cite contradictory authority. Commit provenance remains placeholder-based.
- Recommendation: Do not resolve silently. The User must decide the remote policy, historical push disposition, identity policy, and whether DEC-0002 is now enforceable.
- User authorization required: Yes.

### F-06 — Approval attribution is a heuristic, not authenticated identity

- Severity: Medium
- Category: Governance integrity
- Confidence: High
- Type: Verified limitation / unresolved policy question
- Evidence: `sps2/governance/attribution.py:140-177`; `sps2/governance/SCHEMAS/decision.schema.json:78-87`
- Observed: Attribution requires `APPROVED`, a non-empty `decided_by`, a date, and a denylist match. It cannot prove that free text corresponds to the human User.
- Impact: A fabricated but non-agent-like identity can pass the implemented check. This is a structural limitation, not evidence of an actual fabricated approval.
- Recommendation: Ask the User to define the required identity mechanism (attestation format, signed approval, out-of-band confirmation, or accepted limitation). Do not alter policy or records in this audit.
- User authorization required: Yes.

### F-07 — Decision schema permits `APPROVED` without attribution fields

- Severity: Medium
- Category: Schema quality
- Confidence: High
- Type: Verified schema risk
- Evidence: `sps2/governance/SCHEMAS/decision.schema.json:61-88`
- Observed: `approval.state: APPROVED` is valid with only `state`; `decided_by`, `decided_at`, and `basis` are optional. No conditional requires them when state is `APPROVED`.
- Impact: Some validators catch this for specific records, but the normative schema alone accepts an unattributed approval.
- Recommendation: Add a policy-approved conditional requiring attribution fields for `APPROVED`, while deciding how legacy and open-decision records are treated.
- User authorization required: Yes.

### F-08 — Open-decision records use an ungoverned custom shape

- Severity: Medium
- Category: Governance schema consistency
- Confidence: High
- Type: Verified defect/risk
- Evidence: `sps2/decisions/OPEN-DECISION-LICENCE.json:2-9`; `sps2/decisions/OPEN-DECISION-CLAUDE-SETTINGS.json:2-8`; `sps2/governance/SCHEMAS/decision.schema.json:47-88`
- Observed: Files declare `sps2.open-decision/v1`, but no corresponding schema was found. States include `APPROVED` and `RESOLVED_APPLIED`, which are not in the decision schema enum. Licence approval is represented by top-level fields rather than the schema's `approval` object.
- Impact: Decision status and approval semantics are not uniformly machine-checkable.
- Recommendation: Ask the User whether to formalize an open-decision schema or migrate these records to the canonical decision schema without changing meaning.
- User authorization required: Yes.

### F-09 — P5 validator reports a false legacy failure for ordinary CI changes

- Severity: Medium
- Category: Governance validator reliability
- Confidence: High
- Type: Verified defect
- Evidence: `sps2/tools/validate-p5.py:279-287`; validator log at `/tmp/sps2-audit-validators-20261016-170506.log:107,146`
- Observed: `validate-p5.py` failed because `.github/expected-test-modules.txt` and `.github/workflows/sps-ci.yml` differ from the historical checkpoint `c11da27`. These are legitimate CI files, not legacy SPS implementation files.
- Impact: A local governance gate can red-flag ordinary CI maintenance and obscure real governance drift.
- Recommendation: Ask the User whether the protected legacy path list should exclude `.github` or whether the checkpoint should be updated under a governed decision.
- User authorization required: Yes.

### F-10 — Local validators are not CI gates by recorded User decision

- Severity: Medium
- Category: Test/governance coverage
- Confidence: High
- Type: Accepted risk / coordination constraint
- Evidence: `.github/workflows/sps-ci.yml:83-218`; `sps2/decisions/REMOTE-PUSH-AUTHORIZATION-DECISIONS.json`, `explicitly_not_approved_by_this_record`
- Observed: CI runs Python unit tests but not the local governance validators. The User explicitly declined validators-in-CI in the recorded session.
- Impact: CI green does not prove all governance controls pass, as demonstrated by the local P5 validator failure.
- Recommendation: Preserve the User decision. Instead, document the exact local command bundle and make its results visible in release evidence.
- User authorization required: No for documentation; yes for CI changes.

## 8. Schema and Validator Findings

### F-11 — P8 content status vocabulary diverges

- Severity: Medium
- Category: Schema/validator correctness
- Confidence: High
- Type: Verified defect
- Evidence: `sps2/schemas/p8-content.schema.json:30-45`; `domain/cms/model.py:52-56`; `domain/cms/validation.py:12-17`; `domain/cms/publishing.py:20-34`; `domain/cms/tests/test_publishing.py:39-45`
- Observed: The schema and `Content` model allow only `draft`, `published`, and `archived`. The standalone validator and publishing workflow also allow and transition to `preview`. A test exercises `preview`.
- Impact: A valid preview record can fail schema validation, while schema-only validation can miss an operational status. This creates inconsistent acceptance results.
- Recommendation: Ask the User whether `preview` is normative. Then update schema, model, validator, and tests together. Do not silently normalize invalid records.
- User authorization required: Yes.

### F-12 — P8 content schema root is unconstrained

- Severity: Medium
- Category: Schema quality
- Confidence: High
- Type: Verified defect
- Evidence: `sps2/schemas/p8-content.schema.json:1-8`
- Observed: The file defines `ContentType`, `Content`, `Section`, and `Revision` under `definitions`, but the root has no `type`, `properties`, `oneOf`, or required discriminator. An empty JSON object is schema-valid.
- Impact: The schema cannot safely validate a complete content document by itself; callers must know which definition to apply.
- Recommendation: Introduce an explicit envelope or separate schemas per entity with a documented selection rule.
- User authorization required: Policy-sensitive; yes.

### F-13 — Governance schemas rely on hand-written validators without a common schema engine

- Severity: Medium
- Category: Schema validation quality
- Confidence: High
- Type: Verified architecture risk
- Evidence: `sps2/p17/record.py:1-20`; `domain/cms/validation.py:1-5`; `python3 -c "import jsonschema"` returned unavailable locally
- Observed: Runtime validation is intentionally stdlib-only and hand-written. Full Draft 2020-12 validation is deferred to optional AJV tests; no common JSON Schema engine is available in the audit environment.
- Impact: Schema and validator divergence is possible and already demonstrable in P8. Error quality and supported keywords vary by module.
- Recommendation: Keep stdlib runtime if required, but add a golden schema-contract test strategy and an explicit list of supported keywords per validator.
- User authorization required: Yes for dependency/CI changes; no for design planning.

## 9. Security and Safe-Execution Findings

### F-14 — Legacy installer is a high-volume unpinned remote code path

- Severity: High
- Category: Supply-chain security
- Confidence: High
- Type: Verified risk
- Evidence: `README.md:16-42`; `get-sps.sh:14-71`; `install.sh:246-270`; `install.sh:337-368`
- Observed: The documented quick start pipes a remote script into Bash. Installer then clones/pulls a branch, removes and rewrites global skill destinations, and installs dozens of external skills via `npx skills add` without commit/version pinning.
- Impact: A changed upstream branch, npm package, or external skill repository can execute arbitrary code on user machines.
- Likelihood: Low, but impact is critical for end users.
- Recommendation: Pin all sources, provide a verifiable offline core install, separate global writes behind explicit consent, and document rollback. This is implementation work requiring User authorization.
- User authorization required: Yes.

### F-15 — Updaters can discard local changes destructively

- Severity: Medium
- Category: Safe execution
- Confidence: High
- Type: Verified risk
- Evidence: `get-sps.sh:46-60`; `scripts/sps-update.sh:100-112`
- Observed: The installer/updater can `git reset --hard origin/$BRANCH` or `rm -rf "$REPO_DIR"` when update paths fail or the clone is absent.
- Impact: Local modifications or uncommitted work in the installed source clone can be irreversibly lost.
- Likelihood: Low to medium.
- Recommendation: Detect dirty worktrees, require an explicit override, create a backup/patch, and fail closed before destructive Git operations.
- User authorization required: Yes for implementation.

### F-16 — P17 subprocess execution is not OS-confined

- Severity: Medium
- Category: Execution security
- Confidence: High
- Type: Documented limitation / unresolved gate
- Evidence: `sps2/p17/execution.py:36-39`; `sps2/p17/discovery.py:172-252`; P17 decisions state GATE-P17-4 remains open
- Observed: P17 uses argv-only execution, trusted-root resolution, digest pinning, timeouts, minimal environment, and process-tree termination. It explicitly documents that the child is not OS-confined.
- Impact: Runner-mediated controls do not prevent all filesystem/process capabilities of a malicious allowlisted executable. This is not a bypass claim.
- Recommendation: Leave real-agent execution disabled until the User-approved GATE-P17-4 isolation decision is complete. Do not treat post-execution detection as prevention.
- User authorization required: Yes.

## 10. Documentation and Reproducibility Findings

### F-17 — Maintainer documentation understates the actual test/CI model

- Severity: Medium
- Category: Documentation/reproducibility
- Confidence: High
- Type: Verified documentation gap
- Evidence: `README.md:203-211`; `.github/workflows/sps-ci.yml:83-218`; `sps2/README.md:113-122`
- Observed: Root documentation says CI runs lint + smoke, but CI also has a 570-test Python gate. It does not provide a local command that reproduces CI test discovery, nor a consolidated list of local validators and known-red checks.
- Impact: Contributors can mistake green CI for complete validation or run the wrong commands.
- Recommendation: Add a maintainer validation section listing CI commands, local governance commands, intentionally excluded red checks, and prerequisites. No behavioral change required.
- User authorization required: No for docs, but coordinate to avoid conflicts.

### F-18 — SPS2 README still labels the project as P1 awaiting approval

- Severity: Low
- Category: Documentation consistency
- Confidence: High
- Type: Verified stale documentation
- Evidence: `sps2/README.md:3-13`; live decisions/evidence for P1–P9/P17
- Observed: `sps2/README.md` says version `0.1.0-foundation`, status P1, `AWAITING_USER_APPROVAL`, while later phases and approvals exist.
- Impact: New agents may under- or over-claim current maturity.
- Recommendation: Update only after confirming the intended current status and versioning policy.
- User authorization required: Yes because status/version claims are governance-sensitive.

## 11. Maintainability and Technical-Debt Findings

### F-19 — Tracked debug artifact `.test.out`

- Severity: Low
- Category: Repository hygiene
- Confidence: High
- Type: Verified defect
- Evidence: `git ls-files` includes `.test.out`; `git log -- .test.out` points to baseline commit `10ab67a`; file contains Claude CLI plugin output.
- Impact: Machine output is retained as source and can confuse provenance.
- Recommendation: Plan a User-approved removal; do not delete in this audit.
- User authorization required: Yes.

### F-20 — Large modules concentrate multiple responsibilities

- Severity: Low
- Category: Maintainability
- Confidence: Medium
- Type: Inference from measured size and targeted inspection
- Evidence: `sps2/tools/p10_runtime_gate.py` 2,221 lines; `sps2/tools/check_p10_inventory.py` 783 lines; `domain/seo/audit.py` 1,319 lines; `domain/seo/model.py` 1,265 lines; `domain/seo/structured_data.py` 1,015 lines
- Observed: These modules combine parsing, policy, validation, reporting, and CLI behavior. P10 files were not deeply inspected due active-work overlap.
- Impact: Higher review cost and risk of unintended behavior changes.
- Recommendation: Defer refactoring until active P10 work settles. Start with characterization tests and interface extraction only in stable modules.
- User authorization required: Yes for implementation.

### F-21 — Active baseline changed during the audit

- Severity: Informational
- Category: Coordination
- Confidence: High
- Type: Verified event
- Evidence: Status checks at 17:05:06 and 17:07:03
- Observed: These P10 files appeared after the initial baseline and were not present in the initial untracked inventory:

```text
sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json
sps2/decisions/P10-ROUND12-USER-DECISIONS.json
sps2/evidence/P10-EVIDENCE.json
sps2/project/SLICE-P10-01.json
```

- Impact: The report's architecture inventory reflects the initial baseline; the final worktree contains additional active P10 files.
- Action: This audit stopped interacting with P10 files, documented the change, and preserved all work.
- User authorization required: Not applicable.

## 12. Commands Executed and Verification Results

| Command | Result | Notes |
|---|---|---:|
| `git branch --show-current`, `git rev-parse HEAD`, `git status --short --branch`, history | Completed | Established dirty baseline |
| `python3 -m unittest -v` with 28 tracked modules under Bash | Exit 0; 570 tests; OK; 1 skip | CI-equivalent suite |
| Initial zsh invocation of the same module list | Exit 1 | Shell word-splitting issue in audit command, not a repository defect |
| `bash sps2/tools/validate-sps2.sh --negative` | Exit 0; 27 passed | 27 negative cases enforced |
| `python3 sps2/tools/validate-p5.py` | Exit 1; 43 passed, 1 failed | F-09 false legacy failure |
| `python3 sps2/tools/validate-p6.py` | Exit 0; 69 passed | 24 negative cases, 1 control |
| `python3 sps2/tools/validate-p7-readiness.py` | Exit 0; 30 passed | 7 negative cases |
| `python3 sps2/tools/check_p10_inventory.py --self-test` | Exit 0; 47 passed | Self-test only; no active P10 decision analysis |
| `bash sps2/tools/validate-p2.sh --negative` | Exit 0; 22 passed | 22 negative cases |
| `bash sps2/tools/validate-p3.sh --negative` | Exit 0; 17 passed | 17 negative/positive controls |
| `bash sps2/tools/validate-p4.sh --negative` | Exit 0; 22 passed | 22 negative cases |
| `bash scripts/lint-sps.sh` | Exit 0 | Passed |
| `bash -n` on root/scripts/sps2 shell scripts | Exit 0 for all checked files | Syntax only |
| `pwsh -NoProfile -File scripts/check-powershell.ps1` | Not run | `pwsh` unavailable locally |
| `python3 sps2/tools/test-portability.py` | Exit 1; 34 passed, 6 failed, 14 controls | Known-red suite; preserved failure |
| `python3 sps2/tools/test-history-credential-check.py` | Exit 0; 4 scenarios passed | Read-only history classification test |
| `jq empty` over all `sps2/**/*.json` | No invalid JSON reported | Syntax only; not schema validation |
| `scripts/smoke-sps.sh` | Not run | Can install packages and access network |
| GitHub Actions run | Not run/contacted | No remote operation authorized |

All commands were read-only or used temporary directories. Repeated `git status --short --branch` checks found no repository modification from the checks.

## 13. Findings Table

| ID | Severity | Confidence | Category | Type | Summary |
|---|---|---|---|---|---|
| F-01 | High | High | CI/CD | Verified risk | No explicit permissions, SHA pinning, or concurrency control |
| F-02 | High | High | CI supply chain | Verified risk | CI smoke can install unpinned external skills |
| F-03 | Low | High | CI reliability | Verified observation | CI/local Python versions differ |
| F-04 | High | High | Governance | Verified defect | Canonical `.sps/STATE.md` is stale and contradicts live state |
| F-05 | High | High | Governance/provenance | Verified unresolved conflict | Remote, push, and identity policies conflict |
| F-06 | Medium | High | Governance integrity | Verified limitation | Approval identity is self-asserted and heuristic |
| F-07 | Medium | High | Schema quality | Verified schema risk | `APPROVED` does not require attribution fields |
| F-08 | Medium | High | Governance schema | Verified defect/risk | Open decisions use an ungoverned custom shape |
| F-09 | Medium | High | Validator reliability | Verified defect | P5 validator falsely treats CI files as legacy modifications |
| F-10 | Medium | High | Test governance | Accepted risk | Local validators are intentionally not CI gates |
| F-11 | Medium | High | Schema correctness | Verified defect | P8 status vocabularies disagree on `preview` |
| F-12 | Medium | High | Schema quality | Verified defect | P8 content schema root accepts empty object |
| F-13 | Medium | High | Schema validation | Verified architecture risk | Hand-written validators lack a common schema contract |
| F-14 | High | High | Security/supply chain | Verified risk | Installer executes many unpinned remote sources |
| F-15 | Medium | High | Safe execution | Verified risk | Updaters can reset/delete local source changes |
| F-16 | Medium | High | Execution security | Documented limitation | P17 has no OS confinement; gate remains open |
| F-17 | Medium | High | Documentation | Verified gap | Maintainer docs omit actual CI/local validation model |
| F-18 | Low | High | Documentation | Verified stale docs | SPS2 README still says P1 awaiting approval |
| F-19 | Low | High | Hygiene | Verified defect | `.test.out` is tracked debug output |
| F-20 | Low | Medium | Maintainability | Inference/risk | Large modules concentrate multiple responsibilities |
| F-21 | Informational | High | Coordination | Verified event | Active P10 files appeared during audit |

Counts: Critical 0, High 5, Medium 12, Low 3, Informational 1. Total 21.

## 14. Prioritized Remediation Roadmap

### P0 — Immediate Coordination and Safety

1. **Freeze interaction with active P10 files.**
   - Objective: Avoid conflicting with Claude's active P10/Home-slice work.
   - Why: Four P10 files appeared during this audit.
   - Dependencies: Claude's current workstream status.
   - Owner: Audit/coordination workstream.
   - Verification: Fresh Git status and explicit ownership handoff.
   - Type: Coordination only.
   - P10 overlap: Yes.

2. **Require User direction before changing governance state.**
   - Objective: Prevent agents from silently reconciling `.sps/STATE.md`, remote policy, or approvals.
   - Why: Current records are contradictory and normative.
   - Dependencies: User decisions below.
   - Owner: User + governance workstream.
   - Verification: New decision records with explicit scope and attribution.
   - Type: Requires User decision.
   - P10 overlap: No, unless approval mechanism affects P10 gates.

### P1 — Important Correctness, Security, and Governance

1. **Harden CI workflow.**
   - Objective: Least privilege, SHA-pinned actions, concurrency control.
   - Why: Reduces supply-chain and token blast radius.
   - Dependencies: User authorization; exclude validator-in-CI scope.
   - Owner: CI/security workstream.
   - Verification: Workflow schema review, dry-run on authorized branch, action digest diff.
   - Type: Implementation-only after authorization.
   - P10 overlap: Low.

2. **Separate offline smoke from external installer smoke.**
   - Objective: Make CI deterministic and remove unpinned remote installs.
   - Why: Current smoke can execute mutable upstream code.
   - Dependencies: Installer source inventory and User approval.
   - Owner: Release/security workstream.
   - Verification: Offline smoke passes; integration smoke runs only with explicit opt-in and pinned sources.
   - Type: Implementation-only after authorization.
   - P10 overlap: No.

3. **Resolve remote, push, and identity governance.**
   - Objective: One coherent remote/publication policy and attributable identity.
   - Why: DEC-0001, DEC-0002, DEC-0032, and live state conflict.
   - Dependencies: User decisions D1–D5 and identity mechanism.
   - Owner: User + governance workstream.
   - Verification: Superseding records, updated canonical state, no silent history edits.
   - Type: Requires User decision.
   - P10 overlap: Low.

4. **Define approval identity semantics.**
   - Objective: Decide whether approvals require signed/out-of-band identity or explicitly accept attestation.
   - Why: Current `decided_by` is free text.
   - Dependencies: User policy; schema migration plan.
   - Owner: User + governance/schema workstream.
   - Verification: Positive/negative schema and validator cases.
   - Type: Requires User decision.
   - P10 overlap: Potentially high.

5. **Reconcile P8 `preview` status.**
   - Objective: One status vocabulary across schema, model, validator, publishing, and tests.
   - Why: Current records can be valid in one path and invalid in another.
   - Dependencies: User product decision.
   - Owner: P8/schema workstream.
   - Verification: Schema and validator tests for every status and transition.
   - Type: Implementation-only after User decision.
   - P10 overlap: Potentially high because P10 consumes published content.

6. **Fix P5 legacy-protection false positive.**
   - Objective: Stop treating legitimate CI changes as legacy modifications.
   - Why: The control currently fails on ordinary CI maintenance.
   - Dependencies: User-approved protected-path definition.
   - Owner: Governance validator workstream.
   - Verification: Validator passes on CI-only diff and still fails on protected legacy diff.
   - Type: Requires User decision.
   - P10 overlap: No.

### P2 — Coverage, Documentation, and Reliability

1. **Document the complete validation model.**
   - Objective: One reproducible maintainer command list.
   - Why: CI green is not equivalent to all local governance checks.
   - Dependencies: Coordination with active documentation changes.
   - Owner: Docs/QA workstream.
   - Verification: Commands run as documented; expected failures are labeled.
   - Type: Documentation-only.
   - P10 overlap: Low.

2. **Track active test modules only after their workstream completes.**
   - Objective: Bring `domain/frontend` and P10 runtime tests into CI when authorized.
   - Why: They are currently invisible to CI.
   - Dependencies: Claude's P10 completion and module stability.
   - Owner: P10 + CI workstream.
   - Verification: Manifest diff, full suite, per-module guard.
   - Type: Implementation-only after authorization.
   - P10 overlap: Yes.

3. **Normalize open-decision records.**
   - Objective: One schema and status vocabulary for pending, resolved, superseded, and applied decisions.
   - Why: Current custom records bypass canonical validation.
   - Dependencies: User policy and historical-record disposition.
   - Owner: Governance/schema workstream.
   - Verification: Schema validation and status-transition tests.
   - Type: Requires User decision.
   - P10 overlap: Low.

4. **Make updater destructive paths fail closed.**
   - Objective: Detect dirty worktrees and preserve local changes before reset/delete.
   - Why: Current updater can destroy local edits.
   - Dependencies: Installer ownership and User approval.
   - Owner: Installer/UX workstream.
   - Verification: Dirty-tree tests, backup/restore tests, no destructive default.
   - Type: Implementation-only after authorization.
   - P10 overlap: No.

### P3 — Long-Term Maintainability

1. **Refactor oversized stable modules incrementally.**
   - Objective: Separate parsing, policy, validation, CLI, and reporting concerns.
   - Why: Reduces review and regression risk.
   - Dependencies: Stable characterization tests; avoid active P10 modules initially.
   - Owner: Maintainability workstream.
   - Verification: No behavior change, tests unchanged or strengthened.
   - Type: Implementation-only after authorization.
   - P10 overlap: Avoid for now.

2. **Add a Python compatibility matrix if justified.**
   - Objective: Catch version-specific standard-library differences.
   - Why: CI and local environments already differ.
   - Dependencies: CI cost approval.
   - Owner: CI workstream.
   - Verification: Matrix results and failure triage policy.
   - Type: Implementation-only after authorization.
   - P10 overlap: No.

3. **Remove tracked debug artifacts under a cleanup decision.**
   - Objective: Remove `.test.out` and prevent recurrence.
   - Why: It is machine output retained as source.
   - Dependencies: User approval because it is tracked.
   - Owner: Repository hygiene workstream.
   - Verification: Git history preserves removal; `git ls-files` no longer includes it.
   - Type: Implementation-only after authorization.
   - P10 overlap: No.

## 15. Explicit User Decisions Required

1. Should `.sps/STATE.md` be updated to current SPS2 state or explicitly reclassified as a legacy point-in-time record, and what is the new canonical entry point?
2. Should the wider remote conflict (D1–D5 from KI-15) be resolved, and what remote/push policy applies after DEC-0032's one-time grant?
3. Should placeholder Git identity now be replaced, and what identity/provenance mechanism is required before publication?
4. What mechanism, if any, must authenticate an approval beyond the current non-agent heuristic?
5. Should `preview` be a normative P8 content status, or should validator/publishing support be removed?
6. Should the P5 protected-legacy path definition exclude `.github`, or should CI changes require a new checkpoint/decision?
7. Should open-decision records be formalized as a separate schema or migrated to the canonical decision schema?
8. Should CI hardening and installer pinning proceed, while preserving the prior decision not to add validators to CI?
9. Should P17 real-agent execution remain disabled until a separately approved OS-isolation gate is satisfied?

## 16. Items Intentionally Not Changed

- No modified tracked file was restored, staged, reverted, or committed.
- No untracked file or directory was deleted, renamed, moved, or quarantined.
- No historical report was modified.
- No P10 decision status, approval attribution, requirement semantics, gate state, or evidence record was changed.
- No known-red portability failure was weakened or hidden.
- No validator was added to CI.
- No dependency file was installed or modified.
- No remote operation was performed.

## 17. Coordination Notes for Claude's Active P10 Work

- This audit did not inspect the contents of the newly appeared P10 decision, evidence, or slice files.
- `sps2/tests/test_p10_runtime_gate.py` and `sps2/tools/p10_runtime_gate.py` were inventoried as untracked files but not deeply analyzed.
- `check_p10_inventory.py --self-test` was run only to verify validator self-tests; no active P10 inventory or decision package was modified.
- Claude should recheck Git status before editing because the worktree changed during this audit.
- Any CI addition of P10 tests or tools should wait until the P10 workstream is complete and separately authorized.

## 18. Final Worktree and Side-Effect Verification

Only one file was created by this audit:

```text
reports/CODEX-INDEPENDENT-REPOSITORY-AUDIT-20261016-171338.md
```

No prior report was overwritten. No file was staged. No commit was made. No push, deploy, publication, or remote contact occurred.

The final status is expected to contain:

- the same eight initially modified tracked files;
- the same pre-existing untracked work;
- the new audit report;
- additional P10 files created by Claude during the audit, disclosed in F-21.

## 19. Limitations and Unverified Areas

- GitHub Actions was not contacted, so this report does not verify a live CI run.
- `scripts/smoke-sps.sh`, PowerShell syntax, and installer behavior were not executed because they can access the network or mutate machine-global state.
- `pwsh` was unavailable, so PowerShell syntax was not independently verified.
- `jsonschema` was unavailable, so full external Draft 2020-12 validation was not performed.
- Security review was static and targeted; absence of a finding is not proof of security.
- The complete 851-line P17 schema and 2,221-line P10 runtime gate were not exhaustively reviewed.
- Detailed P10 decision and Home-slice analysis was intentionally excluded.
- Reports under `reports/` were used only for filename-collision avoidance and baseline context, not as proof of current behavior.

