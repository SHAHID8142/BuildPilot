# Codex Security Hardening Implementation Plan — 2026-10-16 17:25:29 +06:00

## 1. Executive Summary

This is a read-only, implementation-ready security plan. It does not implement any change. It verifies that the prior audit’s CI and installer findings remain true at the current baseline and adds a detailed hardening strategy for GitHub Actions, external dependencies, installer/updater recovery, and regression testing.

The most urgent risks are:

1. `scripts/bootstrap-sps.sh` can automatically invoke `sps-update.sh --yes`, whose failure path can hard-reset the installed source clone.
2. Installation and updates can delete or overwrite destination directories and source clones without a verified backup.
3. CI and installers execute mutable third-party code: GitHub Actions are tag-pinned, while 26 external skill installs and several Claude plugins/packages are unpinned.
4. CI has no explicit workflow permissions or concurrency control.

The proposed sequence is to eliminate data-loss and unsafe default execution first, then reduce CI and installer supply-chain exposure, and finally improve diagnostics and long-term provenance. No local governance validator is proposed for CI; the prior User decision declining validators-in-CI is preserved.

## 2. Verified Baseline

- Branch: `build/roadmap-p3-completion`
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`
- Remote: `origin` → `https://github.com/SHAHID8142/Shahid-Master-Skill.git`
- Upstream: `origin/build/roadmap-p3-completion` at the same commit
- Worktree: dirty, with no staged files
- Prior report: `reports/CODEX-INDEPENDENT-REPOSITORY-AUDIT-20261016-171338.md`
- Prior report SHA-256: `43169ce1be4f5b2758d51d9e3eb45c65387d5aa4b16303c730082f5728eff5ee`

The target files for this plan were clean relative to HEAD:

```text
.github/workflows/sps-ci.yml
scripts/smoke-sps.sh
install.sh
get-sps.sh
scripts/sps-update.sh
scripts/check-update.sh
get-sps.ps1
scripts/update-sps.ps1
```

Claude’s active P10/Home-slice work has advanced since the prior report. The status now includes additional frontend/Home-slice files and newer reports. Their contents were not inspected or modified. Any implementation must recheck Git status immediately before editing.

## 3. Findings Confirmed from the Previous Audit

### SH-01 — CI lacks explicit permissions, concurrency control, and SHA pinning

- Status: Verified and unchanged.
- Evidence: `.github/workflows/sps-ci.yml:3-6`, `.github/workflows/sps-ci.yml:13-17`, `.github/workflows/sps-ci.yml:38-39`, `.github/workflows/sps-ci.yml:75-80`, `.github/workflows/sps-ci.yml:93-101`.
- Current behavior: Push and pull requests run without a `permissions:` or `concurrency:` block. Six `uses:` entries use mutable version tags; none is SHA-pinned.
- Impact: Excessive default token permissions and mutable action tags increase CI compromise and redundant-run risk.
- Confidence: High.

### SH-02 — CI smoke can execute network-dependent installer code

- Status: Verified and unchanged.
- Evidence: `.github/workflows/sps-ci.yml:27-32`; `scripts/smoke-sps.sh:73-108`; `install.sh:337-401`.
- Current behavior: CI sets `npm_config_yes=true` and runs smoke. Smoke invokes `install.sh --agents '*' --yes` in an isolated `HOME`, but the installer invokes `npx skills add`, Claude plugins, Context7, and graphify from external sources.
- Impact: CI correctness depends on mutable upstream content. A compromised source can execute arbitrary code in CI.
- Confidence: High.

### SH-03 — Installer executes unpinned external sources

- Status: Verified and unchanged.
- Evidence: `install.sh:337-368` contains 27 `npx skills add` calls: one local core install and 26 external skill-source installs. `install.sh:370-401` adds unpinned Claude marketplaces/plugins, Context7, and graphify.
- Current behavior: External repositories and packages are referenced by owner/name or URL, not immutable commit SHA, package version, and integrity digest.
- Impact: Mutable upstream content can alter installed behavior or execute installer code.
- Confidence: High.

### SH-04 — Updaters can discard local source changes

- Status: Verified and unchanged.
- Evidence: `get-sps.sh:46-52`; `scripts/sps-update.sh:101-107`; `get-sps.ps1:39-47`; `scripts/update-sps.ps1:64-72`.
- Current behavior: A failed fast-forward falls back to `git reset --hard origin/$BRANCH`. There is no dirty-worktree check or backup.
- Impact: Uncommitted user changes in the installed source clone can be irreversibly lost.
- Confidence: High.

### SH-05 — Bootstrap can trigger an unattended destructive update

- Status: Newly verified in this round.
- Evidence: `scripts/bootstrap-sps.sh:131-143`.
- Current behavior: A project bootstrap performs an update check and, when an update is available, automatically runs `scripts/sps-update.sh --yes`.
- Impact: An unattended bootstrap can chain into an updater that can hard-reset the installed source clone. This is a data-loss and unsafe-execution risk.
- Confidence: High.

### SH-06 — Installation overwrites global destinations without backup

- Status: Verified and unchanged.
- Evidence: `install.sh:32-50`; `install.sh:194-243`; `install.sh:246-270`; `install.sh:307-311`.
- Current behavior: The installer writes logs, manifests, memory files, and skill directories under `$HOME`; `sync_core_skill` runs `rm -rf` on `sps` and `sps-cms` destinations before copying. `--yes` skips the interactive confirmation.
- Impact: Existing global skills and personal state can be overwritten or removed without a verified recovery copy.
- Confidence: High.

### SH-07 — Installer disables or weakens safety controls

- Status: Newly verified in this round.
- Evidence: `install.sh:14-20`.
- Current behavior: The installer sets `GIT_SSH_COMMAND` with `StrictHostKeyChecking=no`, sets `GIT_CLONE_PROTECTION_ACTIVE=false`, and exports `npm_config_yes=true`.
- Impact: Host-key verification and Git local-clone protection are weakened; npm operations are auto-approved. The exact Git protection semantics should be verified for the supported Git versions, but disabling named safety controls is not a safe default.
- Confidence: High that the settings exist; Medium that all Git-version consequences are fully understood.

## 4. CI Hardening Plan

### C-01 — Add least-privilege workflow permissions

- File/location: `.github/workflows/sps-ci.yml`, insert after the `on:` block at lines 3-6.
- Current behavior: No `permissions:` block is present.
- Proposed behavior: Add workflow-wide `permissions: contents: read`. If a future job needs another scope, declare that scope at the job level with justification.
- Security benefit: Reduces `GITHUB_TOKEN` blast radius and blocks accidental package, deployment, or repository writes.
- Compatibility risk: Low. Current jobs only checkout and run tests/lint. A future job requiring `packages: write` or `id-token: write` must be explicitly reviewed.
- Required tests: Static workflow validation that `permissions` exists, equals `contents: read`, and no job grants broader scopes without an approved exception.
- Rollback: Remove the `permissions:` block in one revert.
- User authorization: Yes, because CI is modified.

### C-02 — Add concurrency control

- File/location: `.github/workflows/sps-ci.yml`, after the trigger block at lines 3-6.
- Current behavior: Push and pull-request events can run redundant concurrent workflows.
- Proposed behavior: Add `concurrency: group: ${{ github.workflow }}-${{ github.ref }}` and `cancel-in-progress: true`.
- Security benefit: Reduces runner load and limits overlapping runs during rapid pushes.
- Compatibility risk: A superseded commit’s run may be cancelled before completion. This is acceptable because there is no deployment job.
- Required tests: Push two commits rapidly to a disposable branch; verify the earlier run is cancelled and the latest run completes.
- Rollback: Remove the `concurrency:` block.
- User authorization: Yes.

### C-03 — Pin all GitHub Actions to verified commit SHAs

- File/location: `.github/workflows/sps-ci.yml:13-17`, `:38-39`, `:75-80`, `:93-101`.
- Current behavior:
  - `actions/checkout@v4`
  - `actions/setup-node@v4`
  - `actions/setup-python@v5`
- Proposed behavior: Replace each mutable tag with the full 40-character commit SHA and preserve the intended version in a comment, for example `owner/repo@<VERIFIED-40-HEX-SHA> # v4`. Do not invent or use an unverified SHA.
- Security benefit: Prevents a moved or compromised tag from changing executed action code.
- Compatibility risk: Low if the verified SHA corresponds to the same major version already used. Future updates require a deliberate SHA change.
- Required tests: Static action-pinning check; successful workflow run on a disposable branch; compare action logs to expected versions.
- Rollback: Revert to existing tags only with User authorization, because rollback weakens supply-chain control.
- User authorization: Yes.

### C-04 — Verify action identity and intended version before pinning

- Scope: `actions/checkout`, `actions/setup-node`, and `actions/setup-python`.
- Required process:
  1. Record the current tag, desired major version, owner/repository, and reason for the version.
  2. During a separately authorized network round, resolve the tag through the official GitHub repository. For annotated tags, record both the tag object and the dereferenced commit. A safe read-only command pattern is `git ls-remote <official-repo-url> refs/tags/<version> 'refs/tags/<version>^{}'`; the `^{}` result is the commit to pin.
  3. Cross-check the result against the official release page or GitHub API response.
  4. Record owner/repository, tag, tag-object SHA, commit SHA, verification command, verifier, date, and release-notes reference in a reviewable provenance file or PR description.
  5. Do not trust a comment, a third-party mirror, or an unverified URL.
- Security benefit: Ensures the pinned SHA is the intended upstream commit.
- Compatibility risk: Low; a wrong SHA should fail review or workflow execution.
- Required tests: Provenance review plus disposable-branch workflow run.
- Rollback: Reject the PR before merge.
- User authorization: Yes for network verification and CI implementation.

### C-05 — Separate deterministic offline checks from network installer integration

- File/location: `.github/workflows/sps-ci.yml:8-32`; `scripts/smoke-sps.sh:19-31`, `:39-70`, `:73-108`.
- Current behavior: One `lint-and-smoke` job runs lint and the full smoke script. Smoke calls `check-update.sh`, which can use `curl`, and invokes the full installer, which uses `npx` and external services.
- Proposed behavior:
  1. Rename the default job to `lint-and-offline-smoke`.
  2. Add an explicit offline smoke mode that runs lint, shell syntax checks, PowerShell syntax when available, and project bootstrap in a temporary directory, while skipping update checks and installer integration.
  3. Keep the current full smoke as a separate `installer-integration` job, initially `workflow_dispatch`-only.
  4. Re-enable scheduled or default integration execution only after every external source and package is pinned and integrity-verified.
- Security benefit: Default CI stops executing mutable remote code while preserving the stronger integration check as an explicit opt-in.
- Compatibility risk: Full installer smoke will no longer run on every push unless separately enabled. This is a deliberate risk tradeoff and must be documented.
- Required tests: Offline smoke passes in CI and locally; integration smoke passes only in an authorized network environment; static check proves default CI does not invoke the integration path.
- Rollback: Restore the original single smoke job only with User authorization.
- User authorization: Yes.

### C-06 — Pin and verify every external dependency and source

- File/location: `install.sh:337-368` for 26 external `npx skills add` calls; `install.sh:370-391` for Claude marketplaces/plugins and Context7; `install.sh:396-401` for graphify; `install.sh:14-20` for npm/Git environment settings.
- Current behavior: Skill sources use mutable owner/name or GitHub URLs. npm, Claude plugins, and graphify are not pinned to exact versions or digests.
- Proposed behavior:
  1. Create an installer source lock/manifest containing source type, canonical upstream URL, selected version or full commit SHA, expected package integrity, purpose, and verification evidence.
  2. For Git-based skills, pre-clone into a temporary staging directory, fetch and checkout the exact full commit SHA, verify the resolved SHA, then install from that local staged directory.
  3. For npm packages, record exact package name/version and npm integrity; use a generated lockfile rather than an unpinned `npx` resolution.
  4. For Claude marketplaces/plugins, determine whether the CLI supports immutable revisions. If not, stage a verified copy or defer that source until a safe mechanism exists.
  5. For graphify, pin the exact package version and hashes for the selected package manager.
  6. Remove `GIT_CLONE_PROTECTION_ACTIVE=false`; set SSH host checking to a safer policy or require a prepared known-hosts file; keep npm auto-approval only for an explicitly verified lockfile.
- Security benefit: Removes mutable remote code execution from the default installer path.
- Compatibility risk: High. Some CLIs may not support commit pinning, and exact upstream versions must be verified before selection. Do not invent versions.
- Required tests: Lockfile schema/static checks; offline staging from local fixture repositories; integrity mismatch rejection; one authorized integration install per source class.
- Rollback: Restore prior installer behavior only with User authorization.
- User authorization: Yes.

### C-07 — Prevent secret and sensitive-environment leakage

- File/location: `.github/workflows/sps-ci.yml:27-32`; `install.sh:181-190`, `:272-282`, `:307-311`.
- Current behavior: CI has no repository secrets. Installer output is appended to `$HOME/.sps/install.log`; external command output can be echoed.
- Proposed behavior:
  1. Do not add secrets to CI for current checks.
  2. Require explicit `::add-mask::` for any future secret.
  3. Never log full environment dumps or command lines containing credentials.
  4. Scrub credential-shaped values from installer logs before writing, or write only command status and sanitized summaries.
  5. Keep `GIT_TERMINAL_PROMPT=0`; do not put tokens in URLs or logs.
- Security benefit: Prevents accidental credential disclosure through CI or user logs.
- Compatibility risk: Over-aggressive redaction can make failures hard to diagnose; retain sanitized error classes and statuses.
- Required tests: Unit tests with fake credentials verify redaction; static check rejects `env`, `printenv`, or `set` redirection into logs; integration test reviews sanitized logs.
- Rollback: Revert logging changes while preserving no-secret CI policy.
- User authorization: Yes for implementation.

### C-08 — Validate hardening without weakening existing protections

- Proposed validation:
  1. Static workflow checks for permissions, concurrency, full-SHA action pins, and no forbidden broad token scopes.
  2. Existing lint, version sanity, PowerShell syntax, and deterministic Python unittest jobs remain unchanged.
  3. New offline smoke runs in default CI.
  4. Existing full smoke remains available as manual integration validation.
  5. Disposable-branch workflow run compares job names, test count, minimum-test guard, manifest guard, and exit behavior before/after.
  6. No local governance validator is added to CI.
- Security benefit: Confirms supply-chain reduction without reducing test integrity.
- Compatibility risk: Low.
- Required tests: See Phase 5.
- Rollback: Revert the CI PR as one unit.
- User authorization: Yes.

## 5. Installer and Updater Hardening Plan

### I-01 — Remove unattended auto-update execution

- File/location: `scripts/bootstrap-sps.sh:131-143`.
- Current behavior: Bootstrap detects an available update and automatically runs `scripts/sps-update.sh --yes`.
- Proposed behavior: Print the update command and exit normally. Updates must be a separate, explicit user action.
- Security benefit: Prevents an unattended bootstrap from chaining into remote fetch and destructive reset behavior.
- Compatibility risk: Users will no longer receive silent automatic updates.
- Required tests: Unit test with a fake update checker confirms notification without invoking updater; integration test confirms no network operation in offline bootstrap.
- Rollback: Restore auto-update only with explicit User authorization.
- User authorization: Yes.

### I-02 — Fail closed on dirty source worktrees

- File/location: `get-sps.sh:46-52`; `scripts/sps-update.sh:101-107`; `get-sps.ps1:39-47`; `scripts/update-sps.ps1:64-72`.
- Current behavior: A failed fast-forward falls back to `git reset --hard origin/$BRANCH` with no dirty-tree check.
- Proposed behavior:
  1. Before fetch, run `git status --porcelain=v1`.
  2. If dirty, stop with exit code and instructions.
  3. Permit continuation only with a new explicit `--discard-local-changes` flag after a verified backup.
  4. Apply the same policy to PowerShell mirrors.
- Security benefit: Prevents silent loss of user modifications.
- Compatibility risk: Users with intentionally dirty installed clones must choose a new explicit path.
- Required tests: dirty/clean tree, failed fast-forward, backup success, backup failure, explicit discard flag.
- Rollback: Revert flag and checks; no destructive operation should be restored as default.
- User authorization: Yes.

### I-03 — Pin the source repository revision

- File/location: `get-sps.sh:16-19`, `:46-60`; `scripts/sps-update.sh:18-20`, `:95-112`; `scripts/check-update.sh:16`.
- Current behavior: Bootstrap and updater default to mutable `main`. Version checks fetch `main/skills/sps/VERSION`.
- Proposed behavior:
  1. Introduce a release manifest identifying the verified source repository and immutable commit SHA.
  2. Default installation and updates to that verified revision.
  3. Require an explicit command or configuration change to move to a new revision.
  4. Fetch the exact SHA, verify `git rev-parse HEAD` equals the expected SHA, and only then install.
  5. Do not treat a mutable tag as sufficient unless tag immutability and signing are separately guaranteed.
- Security benefit: Prevents silent upstream changes from controlling local installation.
- Compatibility risk: Updates become deliberate rather than automatic.
- Required tests: clean/dirty source, expected SHA, wrong SHA, unavailable SHA, offline behavior.
- Rollback: Revert to branch behavior only with User authorization.
- User authorization: Yes.

### I-04 — Replace destructive source-update fallbacks

- File/location and current destructive paths:
  - `get-sps.sh:50-52`: failed pull → `git reset --hard`.
  - `get-sps.sh:58`: missing clone path → `rm -rf "$REPO_DIR"` before clone.
  - `scripts/sps-update.sh:105-106`: failed pull → `git reset --hard`.
  - `scripts/sps-update.sh:110`: missing clone path → `rm -rf "$REPO_DIR"` before clone.
  - `get-sps.ps1:44-46`: failed pull → hard reset.
  - `get-sps.ps1:52`: missing clone path → recursive force delete.
  - `scripts/update-sps.ps1:70-71`: failed pull → hard reset.
  - `scripts/update-sps.ps1:75`: missing clone path → recursive force delete.
- Proposed behavior:
  1. Never hard-reset or delete by default.
  2. On failed fast-forward, stop and provide recovery instructions.
  3. If the destination exists but is not a Git worktree, stop; do not delete it automatically.
  4. Require `--discard-local-changes` plus verified backup for any destructive continuation.
- Security benefit: Removes irreversible default data-loss paths.
- Compatibility risk: Existing broken or partial installs may require manual recovery.
- Required tests: dirty tree, clean tree, failed fetch, failed pull, non-Git destination, interrupted update, explicit discard path.
- Rollback: Restore old fallback only with explicit User authorization.
- User authorization: Yes.

### I-05 — Require explicit consent and dry-run for global writes

- File/location: `install.sh:32-50`, `:194-243`, `:246-270`, `:307-311`, `:320-325`.
- Current behavior: The installer defines many `$HOME` destinations, writes global files, deletes existing `sps` and `sps-cms` destinations, and `--yes` bypasses the interactive prompt.
- Proposed behavior:
  1. Add `--plan` as the default or strongly recommended mode, printing every write/delete destination.
  2. Require explicit `--apply --global` for machine-global writes.
  3. Validate destination roots are absolute, non-empty, inside the intended user profile, not `/`, and not symlink escapes.
  4. Record planned operations in a machine-readable manifest before execution.
- Security benefit: Gives the user an auditable consent boundary and prevents accidental global mutation.
- Compatibility risk: Existing automation using `--yes` will need a migration path.
- Required tests: plan-only makes no writes; apply without consent fails; unexpected destination rejected; symlink escape rejected; manifest matches actual operations.
- Rollback: Restore old default only with User authorization.
- User authorization: Yes.

### I-06 — Verify and back up destinations before replacement

- File/location: `install.sh:246-270`.
- Current behavior: `sync_core_skill` removes `$dest_root/sps` and `$dest_root/sps-cms` before copying and performs no backup.
- Proposed behavior:
  1. Snapshot each destination before replacement into a timestamped backup directory.
  2. Record file paths, modes, SHA-256 digests, and source/destination in a manifest.
  3. Verify the backup manifest before deleting the original.
  4. On installation failure, provide a restore command or automatically restore only if rollback was explicitly requested.
  5. Retain at least the previous known-good backup.
- Security benefit: Makes global replacement recoverable and tamper-evident.
- Compatibility risk: Large destinations may consume disk; backup failures must stop installation rather than continue destructively.
- Required tests: backup success/failure, restore success/failure, interrupted replacement, digest mismatch, no backup space.
- Rollback: Restore from the created backup manifest.
- User authorization: Yes.

### I-07 — Provide a verified offline core installation

- File/location: `install.sh:337-341` for current local core install via `npx`; `install.sh:246-270` for direct local sync capability.
- Current behavior: Even the core skill install uses `npx skills add`, so installation is not fully offline.
- Proposed behavior:
  1. Add `--offline-core` mode.
  2. Copy only repository-local `skills/sps` and `skills/sps-cms` to staged destinations.
  3. Verify source file digests against a repository manifest.
  4. Skip every external skill, plugin, package, MCP, and update check.
  5. Run post-install verification from local files only.
- Security benefit: Provides a safe fallback when upstreams are unavailable and avoids remote execution.
- Compatibility risk: Optional curated skills will be absent; the command output must state this clearly.
- Required tests: offline install succeeds with network disabled; no `npx`, `curl`, `git fetch`, plugin, or package command is invoked; destination verification passes.
- Rollback: Restore from destination backup.
- User authorization: Yes.

### I-08 — Make upstream failure and invalid input fail closed

- File/location: `get-sps.sh:44-60`; `scripts/sps-update.sh:95-124`; `install.sh:249-268`, `:327-404`.
- Current behavior: Missing source warns and continues in some paths; optional external install failures can be ignored if core mirrors exist; version can be `unknown`.
- Proposed behavior:
  1. Validate required source files, version, release manifest, and destination prerequisites before any destructive operation.
  2. On network failure, either fail closed or proceed only in explicitly requested offline-core mode.
  3. On invalid digest/revision/source, stop before staging replacement.
  4. Use a staging directory and verify all copied files before replacing live destinations.
  5. Never report success when optional components fail unless the command explicitly selected an optional-only mode.
- Security benefit: Prevents partial, untrusted, or misleading installs.
- Compatibility risk: Existing tolerant behavior changes; failures become more explicit.
- Required tests: invalid manifest, missing VERSION, unavailable network, digest mismatch, partial staging, interrupted install.
- Rollback: Restore from backup manifest.
- User authorization: Yes.

### I-09 — Improve recovery diagnostics without leaking secrets

- File/location: `install.sh:181-190`, `:303`, `:307-311`; `scripts/sps-update.sh:121-130`.
- Current behavior: Logs record raw command output tails and point to `$HOME/.sps/install.log`; updater failure diagnostics are limited.
- Proposed behavior:
  1. Write a structured operation log with command, exit status, sanitized error class, source revision, and backup path.
  2. Redact credential-shaped values and environment values.
  3. On failure, print the exact restore command and last safe revision.
  4. Preserve the prior log rather than truncating it until the new operation succeeds.
- Security benefit: Improves recovery while reducing accidental secret exposure.
- Compatibility risk: Log format changes may affect humans or tooling expecting plain text.
- Required tests: failure logging, restore instructions, redaction, log preservation.
- Rollback: Revert logging format only.
- User authorization: Yes.

### I-10 — Audit uninstall and destructive cleanup

- File/location: `uninstall.sh:151-175`, `:177-213`, `:215-223`.
- Current behavior: Uninstall removes mirrored skill directories, graphify paths, and by default `$HOME/.sps`.
- Proposed behavior:
  1. Add plan mode and explicit `--apply`.
  2. Back up before deletion.
  3. Require explicit confirmation for `$HOME/.sps` removal.
  4. Validate every target path before recursive deletion.
- Security benefit: Prevents accidental removal of personal data and arbitrary destination paths.
- Compatibility risk: Existing uninstall automation may need a migration path.
- Required tests: plan-only, backup/restore, keep-personal, unexpected path, interrupted uninstall.
- Rollback: Restore from backup.
- User authorization: Yes.

## 6. Regression-Test Strategy

No tests should be added in this round. The following is the required implementation-phase strategy.

### Static Checks — no network, no filesystem mutation

| ID | Scenario | Expected result |
|---|---|---|
| T-S01 | Workflow permissions | Workflow declares `contents: read`; no unauthorized broader scope |
| T-S02 | Workflow concurrency | Concurrency group exists and cancel behavior is intentional |
| T-S03 | Action pinning | Every `uses:` target resolves to `owner/repo@<40-hex-SHA>` |
| T-S04 | Action provenance | Pin inventory has verified upstream tag, commit, verifier, date, and evidence |
| T-S05 | Offline CI boundary | Default jobs do not invoke installer integration, `npx`, `curl`, or update checks |
| T-S06 | External source lock | Every remote skill/package/plugin has exact source, version/SHA, integrity, and approval metadata |
| T-S07 | Destructive operation policy | No default hard reset, recursive delete, or unattended update |
| T-S08 | Shell/PowerShell syntax | `bash -n` and PowerShell parser checks pass |

### Unit Tests — temporary directories only, no network

| ID | Scenario | Fixture and expected result |
|---|---|---|
| T-U01 | Dirty source worktree | Temporary Git repo with modification; updater exits before fetch/reset |
| T-U02 | Clean source worktree | Temporary clean repo; update proceeds only after source verification |
| T-U03 | Wrong source revision | Expected SHA differs from fetched HEAD; no install or delete occurs |
| T-U04 | Invalid digest | Staged file digest differs; operation fails before destination replacement |
| T-U05 | Missing required configuration | Missing manifest, VERSION, source, or destination config; fail closed |
| T-U06 | Unexpected destination | Destination outside approved roots, empty, `/`, or symlink escape; rejection before deletion |
| T-U07 | Backup creation | Backup manifest records paths, modes, and SHA-256 values; verification passes |
| T-U08 | Backup failure | Disk or manifest failure stops update before destructive step |
| T-U09 | Restore success | Restored files match original manifest digests |
| T-U10 | Restore failure | Restore failure is reported; no false success is printed |
| T-U11 | Offline core mode | Local core copied; all external operations skipped |
| T-U12 | Unattended bootstrap | Update available produces notification only; updater is not invoked |

### Integration Tests — temporary HOME and local/mock remotes, no external network

| ID | Scenario | Fixture and expected result |
|---|---|---|
| T-I01 | Failed network access | Unreachable proxy or mock Git fails; no destination mutation unless offline-core was explicit |
| T-I02 | Invalid/unpinned source | Source lock missing or mutable; installer refuses before execution |
| T-I03 | Interrupted update | Signal after backup but before replacement; next run detects incomplete state and offers recovery |
| T-I04 | Failed install after backup | Restore path returns destinations to verified prior state |
| T-I05 | Offline install end-to-end | Isolated `HOME`, no network, local core only; expected files and manifest verified |
| T-I06 | Clean-tree update end-to-end | Local fixture remote at verified SHA; update succeeds and old backup remains |
| T-I07 | Dirty-tree update end-to-end | Local fixture remote plus dirty clone; update fails and backup is not used to discard changes without consent |

### Manual Verification — controlled environment, explicit authorization

| ID | Scenario | Requirement |
|---|---|---|
| T-M01 | Full installer integration | Run only in disposable VM/container with isolated `HOME`, pinned sources, and reviewed logs |
| T-M02 | Real updater integration | Run only after backup and source-revision checks are implemented |
| T-M03 | CI workflow | Run on disposable branch and compare job outcomes with baseline |
| T-M04 | Recovery drill | Delete staged live destination after backup and restore using documented command |

Static checks are the only tests that can run without network access and without any filesystem mutation. Unit and local integration tests may mutate temporary directories but must never mutate the repository or the real `$HOME`.

## 7. Prioritized Implementation Roadmap

### P0 — Prevent data loss and unsafe execution

| Item | Scope | Dependencies | Expected impact | Complexity | Acceptance | Independent | P10 overlap | User authorization |
|---|---|---|---|---|---|---|---|---|
| P0-1 | Remove bootstrap auto-update (`scripts/bootstrap-sps.sh:131-143`) | None | Prevents unattended destructive update chain | Low | Fake update check notifies but does not invoke updater | Yes | No | Yes |
| P0-2 | Add dirty-tree fail-closed checks to Bash and PowerShell updaters | None | Prevents hard-reset data loss | Medium | Dirty fixture exits before fetch/reset | Yes | No | Yes |
| P0-3 | Remove default hard reset and repository deletion | `get-sps.sh`, `scripts/sps-update.sh`, PowerShell mirrors | Requires explicit recovery path | Medium | Failed update leaves worktree untouched | Yes | No | Yes |
| P0-4 | Add verified destination/source backups before destructive replacement | Installer and updater | Makes recovery possible | High | Backup manifest verifies before delete | Mostly; shared backup helper helps | No | Yes |
| P0-5 | Add global write plan/consent boundary | Installer | Prevents accidental global mutation | High | Plan mode writes nothing; apply requires explicit consent | Yes | No | Yes |
| P0-6 | Remove unsafe Git/npm defaults (`install.sh:14-20`) | Git behavior verification | Restores safer host-key and clone defaults | Medium | Static check rejects unsafe defaults; install still works in authorized test | Yes | No | Yes |

### P1 — Reduce CI and installer supply-chain exposure

| Item | Scope | Dependencies | Expected impact | Complexity | Acceptance | Independent | P10 overlap | User authorization |
|---|---|---|---|---|---|---|---|---|
| P1-1 | Add CI permissions and concurrency | None | Reduces token and redundant-run risk | Low | Static workflow checks pass | Yes | No | Yes |
| P1-2 | Pin GitHub Actions to verified SHAs | Authorized network verification | Removes mutable action execution | Medium | All actions SHA-pinned; disposable workflow passes | Yes | No | Yes |
| P1-3 | Split offline smoke from installer integration | Smoke/installer refactor | Default CI stops remote code execution | Medium | Offline CI passes; integration remains opt-in | Yes | No | Yes |
| P1-4 | Build external source lock and staging installer | Source inventory and CLI capability verification | Removes mutable dependency execution | High | Every remote source pinned and verified | Mostly | No | Yes |
| P1-5 | Add verified offline-core mode | Local source manifest | Safe fallback without network | Medium | Offline install succeeds with no external calls | Yes | No | Yes |

### P2 — Improve reproducibility, diagnostics, and recovery

| Item | Scope | Dependencies | Expected impact | Complexity | Acceptance | Independent | P10 overlap | User authorization |
|---|---|---|---|---|---|---|---|---|
| P2-1 | Structured sanitized operation logs | Installer/updater | Better diagnosis without secret leakage | Medium | Redaction tests pass | Mostly | No | Yes |
| P2-2 | Machine-readable recovery manifest | Backup work | Exact restore instructions | Medium | Restore returns verified state | No; depends on P0-4 | No | Yes |
| P2-3 | Source release manifest and verification workflow | Source pinning | Reproducible installations | Medium | Wrong revision fails closed | No; depends on P1-4 | No | Yes |
| P2-4 | Document installation modes and recovery | Installer/updater changes | Users know safe paths | Low | Docs match behavior | No; depends on implementation | No | Yes |

### P3 — Optional long-term improvements

| Item | Scope | Dependencies | Expected impact | Complexity | Acceptance | Independent | P10 overlap | User authorization |
|---|---|---|---|---|---|---|---|---|
| P3-1 | Signed releases and provenance attestations | Release infrastructure | Strong supply-chain verification | High | Signature/attestation validation tests | No | No | Yes |
| P3-2 | OS-level installation sandboxing | Platform-specific design | Limits installer blast radius | High | Unauthorized writes fail | No | No | Yes |
| P3-3 | Cross-platform parity test harness | Bash/PowerShell test doubles | Prevents platform-specific safety gaps | High | Matrix covers destructive paths | Mostly | No | Yes |
| P3-4 | Scheduled verified integration smoke | Fully pinned sources | Periodic real-world validation | Medium | Scheduled job passes and failures are visible | No | No | Yes |

## 8. Explicit Authorization Requirements

The following require separate explicit User authorization before implementation:

1. Any modification to `.github/workflows/sps-ci.yml`.
2. Any network access to verify GitHub Actions, repositories, packages, plugins, or release artifacts.
3. Any modification to installers, updaters, uninstallers, bootstrap scripts, smoke scripts, or their tests.
4. Any change to destructive defaults, global write consent, backup retention, or recovery behavior.
5. Any introduction of dependency lockfiles, release manifests, signing, or provenance requirements.
6. Any documentation update describing new install/update behavior.
7. Any addition or re-enablement of network-dependent CI jobs.

The prior User decision declining local governance validators in CI remains binding. This plan does not propose adding those validators to CI.

## 9. Dependencies and Coordination Risks

- Recheck Git status before implementation because Claude’s P10/Home-slice work changed during this analysis.
- Avoid editing `domain/frontend/`, `sps2/tests/test_p10_runtime_gate.py`, `sps2/tools/p10_runtime_gate.py`, active P10 decisions/evidence, or P10 reports.
- CI hardening is independent of P10 unless the expected-test-module manifest is changed; do not change that manifest in this workstream.
- Installer hardening is independent of P10, but shared backup/logging helpers should be introduced only after agreement on ownership and test location.
- Action SHA verification requires a separately authorized network round; no SHA is proposed in this report.
- Exact versions and integrity values for external skills/packages must be verified from canonical upstreams before implementation; none are invented here.
- Installer behavior changes can break existing automation, so a compatibility migration or explicit breaking-change decision is required.

## 10. Items Intentionally Not Changed

- No production code, test, CI workflow, installer, updater, uninstaller, or documentation file was modified.
- No dependency was added or installed.
- No package manager, installer, updater, or smoke test was executed.
- No Git remote was contacted.
- No commit, push, fetch, pull, deploy, or publication occurred.
- No file was staged.
- No governance decision, approval, evidence record, or P10 artifact was changed.
- No historical report was modified, deleted, renamed, or overwritten.
- No untracked file was moved or deleted.

## 11. Commands Executed and Results

All commands were read-only or syntax-only.

| Command / inspection | Result |
|---|---|
| `date`, `git branch --show-current`, `git rev-parse HEAD`, `git log -1 --format=fuller` | Baseline established |
| `git status --short --branch`, `git diff --cached --name-status`, `git diff --name-status`, `git ls-files --others --exclude-standard` | Dirty worktree; no staged files; active P10 changes present |
| Prior report existence, size, and `sha256sum` | 671 lines, 40,830 bytes, SHA-256 shown in Section 2 |
| Read prior report security sections | Prior findings identified for re-verification |
| Read current CI, smoke, installer, bootstrap, update, check-update, PowerShell updater/bootstrap, and uninstall files | Current behavior verified |
| `rg` searches for external operations, destructive paths, and installer-related tests | External/destructive inventory completed |
| `git status --porcelain=v1 -- <target files>` | No target file modified |
| `git diff --check -- <target files>` | Exit 0 |
| `bash -n scripts/smoke-sps.sh install.sh get-sps.sh scripts/sps-update.sh scripts/check-update.sh scripts/bootstrap-sps.sh uninstall.sh` | Exit 0 for each file |
| Static `rg` assertions | No `permissions:`; no `concurrency:`; 6 mutable action uses; 0 SHA-pinned actions; 27 `npx skills add` calls; destructive update paths found in four source files |
| `scripts/smoke-sps.sh`, installer, updater, uninstaller | Not executed because they can access networks, install packages, or mutate filesystems |
| GitHub Actions / remote repository checks | Not contacted |

## 12. Final Git Status and Side-Effect Verification

The only file created by this task is:

```text
reports/CODEX-SECURITY-HARDENING-PLAN-20261016-172529.md
```

No existing file was changed. No prior report was overwritten. No file was staged. No commit, push, fetch, pull, deploy, publication, package installation, or remote operation occurred.

The final status retains:

- the same eight modified tracked files observed at baseline;
- all pre-existing untracked work, including Claude’s active P10/Home-slice files;
- the new timestamped security-hardening plan report.

