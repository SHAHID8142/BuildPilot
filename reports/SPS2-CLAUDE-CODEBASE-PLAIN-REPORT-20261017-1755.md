# SPS2 FULL CODEBASE REPORT — PLAIN-LANGUAGE HONEST ASSESSMENT (CLAUDE)

Report time: 2026-10-17T17:55+06
Author: Claude (independent reviewer). Method: direct read of repository structure, sps2/README, P10 requirements/gate help, dossier current-state file, backlog, installer, skill tree, git history and status. Every point below is grounded in files present at HEAD `c49f3852e1c31d0136269c80fe58201b059af3ec`, branch `build/roadmap-p3-completion`.

## 1. What we are building — two separate things

**SPS (the product), v4.0.0** — `skills/sps/` (28 docs), `skills/sps-cms/`, `plugins/`, installers (`install.sh`/`install.ps1`, `get-sps.sh`/`get-sps.ps1`, `uninstall.sh`/`uninstall.ps1`), `scripts/` (doctor, updater, check-update). An instruction/skill set installed into AI coding agents. `/sps` gives the agent a disciplined workflow: discovery → plan + approval gate → one section at a time → per-section approval → persistent `.sps/` memory → evidence-honest reporting. CMS sections must ship storefront + admin controls together. 8 host adapters under `skills/sps/hosts/`.

**SPS2 (the framework), v0.1.0-foundation** — `sps2/` + `domain/` = 239 of 452 tracked files. A from-scratch agent-neutral orchestration framework with formal governance: JSON-schema decisions, evidence records, fail-closed validators, a 16-control P10 runtime gate, adapters (generic/codex/opencode, declared/experimental), one-way core/adapters dependency rule. Its own README states it is NOT the legacy SPS and nothing in `sps2/` may depend on the product.

## 2. Why

Product: fix real agent failure modes — lost context, coding before approval, false completion claims, uneditable CMS pages.
Framework: rebuild the idea with stricter, machine-checked engineering governance.

## 3. Current state (facts, all verified in-tree)

- Product is documented, installed-by-design, CI-backed (`.github/workflows/sps-ci.yml`: lint+smoke, version sanity, PowerShell syntax). 112 commits.
- SPS2 is NOT releasable by its own gate: P10 = 9 PASS / 5 FAIL / 2 BLOCKED, exit 1 (reconfirmed by C9 audit and dossier). The 5 failures: `published-only-content` (content.json is `status: draft`, `published_at: null`), `slice-id-uniqueness` (no history file), `evidence-authenticity` (EV-P10-001 is a governance placeholder, result BLOCKED, no gate_record), `approval-authenticity` (slice `user_approval: null`), `req-p10-07-reconciliation`. The 2 blocks: `exposure-declaration` (no observed bind address mechanism exists), `p9-deployment-audit` (no build output; renderer entry points say `PLACEHOLDER-NOT-BUILT`).
- Test suite: 35 modules, 1,075 tests OK / 2 environmental skips (re-verified 2026-10-17). Validators fail-closed: 79/4, 68/9, 66/10, 57/11, 44/1.
- Worktree: 83 porcelain entries, 0 staged, 0 stashes; untracked trees expand to ~222 files (reports/, dossier, loop/, domain/cms/data, domain/frontend, sps2 decisions/evidence, .sps additions).
- Known doc debt: CATALOG.md:17-21,33 still lists core/full/minimal profiles + "Trail of Bits (full profile)" vs unified install (README.md:56-59, install.sh PROFILE=all). CHANGELOG 4.0.0 internally mixed (lines 12-13 profile bullets vs 3-7 unified announcement).
- Installer trust surface (verified in code): `GIT_SSH_COMMAND` with `-oStrictHostKeyChecking=no` (install.sh:15, install.ps1:9), `npm_config_yes=true` (install.sh:17), 27 `npx skills add ... -y` third-party installs (install.sh:338-368), `rm -rf` mirror refresh (install.sh:255,262).

## 4. What could be added next (concrete, code-based)

1. CATALOG.md/CHANGELOG profile-wording reconciliation (docs-only).
2. README disclosure of installer trust behavior (docs-only; proposed wording exists in reports/SPS2-CLAUDE-PRD-REVIEW-20261017-1735.md R-1..R-6).
3. The five failing P10 controls each name their missing artifact: publish content (User approval required — DEC-7203 records PUBLICATION: DEFER), produce a real build, authoritative slice-ID history, authentic evidence with gate_record, slice approval.
4. Packages 2/3 security fixes (installer SSH, uninstaller confinement) — blocked on User decision because they touch validator baselines.
5. Commit/stage the 222 untracked files (largest operational risk).
6. P10 gate coverage gap C9-08: required-control list lacks test-execution and rollback-rehearsal controls (REQ-P10-09/16 obligations currently unenforced by the gate itself).

## 5. Gaps, risks, possibly-missed items

- Nothing committed; all recent work untracked. One destructive git command loses it.
- Approval deadlock is by design: publication/exposure/release require explicit User approval; none exists in any record. SPS2 cannot move without User decisions.
- DEC-7301/7302/7303 recorded but UNAPPROVED; one historical record falsely attributed User approval (corrected sidecar exists, hash-verified). Treat approval provenance with suspicion.
- Installer supply-chain exposure as above (relevant if anyone besides the owner runs it).
- PowerShell scripts never runtime-verified in this environment (pwsh unavailable) — UNCERTAIN, flagged.
- Two-worlds confusion: nothing at repo top level explains product vs framework split; only sps2/README and the dossier say it.
- P10 gate code (`sps2/tools/p10_runtime_gate.py`) and its test are untracked with unresolved authorization provenance (C9-10) — UNCERTAIN.
- Whether SPS2 can ever pass its gate is genuinely open: remaining controls need real runtime artifacts (built site, published content) that do not exist anywhere in the tree — UNCERTAIN.

## 6. Bottom line

The product is real, tested, and shippable after small doc fixes. The framework is an honest, well-guarded construction site that cannot pass its own gate until the User makes explicit decisions (publish content, authorize build/exposure, resolve DEC-730x). The repo needs a commit before anything else.

Constraints honored: read-only assessment; no edits to source, CI, baselines, governance, approvals, `.sps/`, P10 records; nothing staged/committed/pushed; P10/release readiness remains NOT READY; no approval claimed or inferred.
