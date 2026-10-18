# Changelog

## 4.4.0

- **Five MAJOR audit findings fixed** (three independent external audits —
  DeepSeek, opencode, workbuddy — then re-derived and verified in-repo):
  - **Lesson consent**: `sps-lesson.sh send` now previews every lesson that
    will be published (names, target repo, branch) and requires a typed
    `yes` before anything leaves the machine; `--yes` for non-interactive
    use. USER-GUIDE's "nothing is sent" claims now describe the real flow.
  - **Uninstall completeness**: deletion allowlist covers all 34 installer
    sync roots (was 19); the completion banner reports a truthful count of
    cleaned roots instead of claiming everything was removed.
  - **Codegen injection**: `gen_law_test.py --approved-by` is validated
    fail-fast (single line, safe charset, ≤80 chars); 8 adversarial
    regression tests; a reviewer name can no longer inject Python into the
    generated test.
  - **Provenance enforcement**: shipped skills (`sps`, `sps-cms`, `sps-seo`)
    are pinned in a committed store (`.sps/provenance-store.json`);
    `check --strict` now **fails** on any drift, a missing store, or a
    shipped skill absent from the store — the README receipt is
    machine-checked, not report-only.
  - **Manifest dual anchor**: both governance manifests are anchored by a
    module constant + a CI-checked anchors file
    (`framework/sps2/governance/manifest-anchors.env`) + a cross-check test;
    a coordinated tamper must now edit four independently-reviewed surfaces.
- **Attribution predicate** (B5): literal self-attestations ("Self
  (self-approved)", "self", "me", "myself") are rejected as User-attributable
  evidence; real names containing "Self" (e.g. "Jane Self") remain protected
  per DEC-0027.
- **Hygiene**: `.secrets-allowlist` recognized as a legitimate root config
  (was a false ROOT-STRAY that would have fired the weekly audit).
- Battery: 1,258 tests, 0 failures. 52 test modules. 57 pinned manifest
  exceptions. Three external audit reports preserved in `reports/`.

## 4.3.0

- **Nightly skill-ecosystem scan** (`scripts/ecosystem-scan.sh` +
  `.github/workflows/ecosystem-scan.yml`): 13 routed domains checked against
  GitHub + skills.sh; 6 supply-chain vetting gates before any candidate is
  proposed; report-only (never installs — Tool Consent law); dated reports
  committed with `[skip ci]` (zero CI minutes); deduped tracking issue.
- **/sps lesson review** (first-class command): per-lesson workflow with
  Problem/Rule/Applies-to display and approve/reject/edit adoption
  (shipped late 4.2.0 cycle, stamped here).
- **/sps status** dashboard: branch, task queue, handoff, after-sale clocks,
  pending lessons, unpushed commits.
- **USER-GUIDE.md**: human walkthrough (install, gates, approvals, lessons,
  safety model).
- Governance: manifest at 32 pinned paths; main branch protection (4 required
  checks); R1–R5 ratified by the User (DEC-USER-RATIFICATION-20261018).

## 4.2.0

- **Legal & compliance gate** (`LEGAL-COMPLIANCE.md`): 8 conditional sections
  (agreements, consent, privacy, payments, comms/marketing, IP/licensing,
  AI governance, accessibility/sector/incident) from a 49-item adversarial
  audit; scoped at kickoff, walked at Phase 4 pre-delivery.
- **File-splitting law** (`FILE-SPLITTING.md`): 300-line soft / 500-line hard
  caps per source file, 8 splitting rules, enforced at the cleanup gate.
- **Step-by-step user guidance** (`USER-GUIDANCE.md`, hard law 15): external
  platform actions one step at a time; secrets never pasted in chat.
- **Cross-project lesson channel** (`LESSONS.md` + `scripts/sps-lesson.sh`):
  capture lessons in client projects, send as PRs to BuildPilot, adopt only
  after user approval. Never auto-sent, never auto-merged.
- **Universal host support**: `install.sh --agents '*'` covers 30+ agents
  (added Goose, Crush, TRAE, Junie, Zed, OpenClaw, Droid, Qoder, Warp, and
  more); 6 new host adapters; SKILL.md names the full Agent Skills registry.
- Hover/touch law: hover-gated content banned as the sole access path.
- Governance: legacy manifest at 25 pinned exceptions; main branch
  protection with 4 required CI checks.

## 4.1.0

- **Robust legacy-skill handling (T-17)**: `install.sh` now backs up existing
  `sps`/`sps-cms`/`sps-seo` skill dirs to `~/.sps/backups/<skill>/` (last 3 kept)
  before replacing them; detects the previously installed VERSION; writes an
  upgrade report to `~/.sps/last-upgrade.txt` (printed at the end of the run);
  backup stamps include a per-host hash so concurrent host syncs never collide;
  restore path printed with the report. Applies to both fresh installs and
  `sps-update.sh` (which delegates to `install.sh`).
- **Machine law-checker in CI**: `framework/sps2/tools/check_laws.py` turns the
  prose laws (context budgets, rolling log, DoD gap items, hard-law core,
  design-gate craft laws, G1/G2 gates, hardcoded-config ban) into CI gates with
  a non-vacuous negative test suite (`test_law_checker.py`).
- **Design craft laws**: DESIGN-GATE absorbed the Gemini UI/UX deep-research
  list (typography/color/space/components/motion/forms/power-user laws +
  anti-slop ban list), machine-checked by the law-checker.
- **Context-budget law**: `.sps/` hot files have size budgets (CONTEXT-BUDGET.md),
  doctor-enforced and law-checker-enforced; rolling conversation log.
- **Company lifecycle + Tool Consent law (17)** + session-4 audit-gap items in
  SECTION-DOD / HANDOFF-CHECKPOINT / VERIFICATION-RECIPES.
## 4.0.0

- **Single unified installer**: one command installs the complete stack — no
  `minimal`/`core`/`full` profiles (`install.sh`, `install.ps1`, `get-sps.*`
  simplified; updaters reinstall everything; manifest writes `PROFILE=all`)
- **Plan-First Zero-Code Gate**: new `PLAN-GATE.md` + `templates/plan.md` — write `./.sps/plan.md`, present it, zero code until user approval (hard law #5)
- **One-Section-One-Go delivery**: `SECTION-DOD.md` rewritten (29 checks) — UI + CMS + content + SEO + Lighthouse (Perf ≥90, SEO/A11y/BP 100) + deploy-readiness + manual check loop per section
- **`sps-cms` mandatory CMS engine** (no fallback); CMS-COUPLING law updated
- **Skill Router v2**: `design-taste-frontend` (taste-skill v2) as primary taste skill; old taste family (`gpt-taste`, `high-end-visual-design`, `minimalist-ui`, `industrial-brutalist-ui`, `image-to-code`, `redesign-existing-projects`, `stitch-design-taste`, `full-output-enforcement`) de-routed; `verification-before-completion` single-skill only
- **+13 catalog skills** (single unified stack — profile vocabulary retired): `agent-browser`, `ai-seo`, `copywriting`, `deploy-to-vercel`, `verification-before-completion`, `firecrawl`, `supabase`, `supabase-postgres-best-practices`, `prisma-database-setup`, `prisma-client-api`, `prisma-cli`, `vercel-react-native-skills`, `sleek-design-mobile-apps`, `fact-check`
- **Parallel subagent playbook**: `SUBAGENT-PLAYBOOK.md` — CMS/UI/content/test lanes, write serialization, evidence-before-claims, review agent
- **Auto-update system**: `scripts/check-update.sh` (24h-cached, offline-safe, semver compare) + rewritten `scripts/sps-update.sh` (preserves selected agents from manifest, `--check/--yes/--force`) + PowerShell mirrors `check-update.ps1` / `update-sps.ps1`; session-start auto-apply; CI version-sanity job (VERSION stamp, mirror sync, PS1 array balance)
- **Doctor v2**: `sps-doctor.sh` checks managed skills + update status; new `--fix` auto-repair via forced reinstall
- **Antigravity hardening**: boot refusal now 7 checks incl. plan gate; Karpathy behavioral block injected into `GEMINI.md`
- fix: `install.ps1` unbalanced array literal; version drift between README/templates/`.sps`

## 3.0.2

- inlined hard-law core in `SKILL.md` (mandatory on all hosts)
- two-tier approval packets (Tier 1 quick-fix vs Tier 2 architecture)
- batch approval mode + `/sps release-lock` / `/sps unlock` procedure
- standardized `SPS:SECTION` / `SPS:CMS_FIELDS` / `SPS:READS_FROM` markers
- multi-agent write serialization
- fix: scripts missing in skill install; audit template synced with AUDIT.md
  scoring; dynamic VERSION stamping in templates; read-only Q&A carve-out

## 3.0.1

- core install now includes **Karpathy guidelines** (`karpathy-guidelines`)
- full profile adds **Trail of Bits** marketplace + security plugins (Claude)
- Antigravity harden: stronger host adapter, boot refusal if mirrors missing,
  richer `GEMINI.md` lock template in bootstrap

## 3.0.0

Breaking workflow release focused on CMS-coupled delivery and multi-agent reliability.

- hard **CMS-coupled section delivery** (storefront + CMS together); `/sps sync` for debt
- foundation-first build order + discovery grill for team/multi-agent + deploy method
- portable **DESIGN-GATE** (no eyebrows, seamless gaps, palette, research-before-design)
- **SECTION-DOD**, role matrix, todo format, workspace hygiene, context efficiency
- **Skill Router** with install-or-instruct protocol; `/sps` remains sole orchestrator
- **METHOD-CARD** + project root mirrors for Antigravity/Claude/Cursor lock-in
- expanded host adapters (Windsurf, Copilot, OpenCode family, generic)
- installer sync paths / agent expansion for more skills-compatible agents
- enhanced `.sps` templates: content-model, cms-foundation, cms-debt, design-system, registry
- audit checklist updated for CMS debt, mirrors, design-gate, deploy/team
- honest portability claim: skills-compatible coding agents, not every internet agent

## 2.6.0

- simplified install profiles to two primaries: `core` (recommended default) and
  `full`
- `balanced` now aliases to `core`; `minimal` remains as an optional `/sps`-only
  alias for power users
- updated installer menus, docs, and smoke tests for the simpler model

## 2.5.0

- added one-command bootstrap: `get-sps.sh` / `get-sps.ps1` clones or pulls the
  repo into `~/.sps/src/...` then installs
- redesigned installer UX with banner, host detection, interactive profile menu,
  progress counters, and a success card with next steps
- added `scripts/sps-doctor.sh` and `scripts/sps-update.sh`
- documented the curl one-liner as the recommended install path

## 2.4.0

- added scored SPS audit checklist with `/100` total and Strong/Mixed/Weak/Critical bands
- required writing the full audit report to `./.sps/audit-report.md` on every audit
- added `skills/sps/templates/audit-report.md` and bootstrap support for it
- added GitHub Actions CI workflow `.github/workflows/sps-ci.yml` to run
  `scripts/lint-sps.sh` and `scripts/smoke-sps.sh` on push and pull requests

## 2.3.0

- made legacy/first-contact onboarding mandatory: if a project never used
  `/sps`, bootstrap memory, audit the existing codebase against SPS rules, and
  deliver an SPS Audit Report before building
- expanded `AUDIT.md` into a full alignment audit with Pass / Fail / Warnings,
  evidence labels, remediation order, and explicit next-step choices
- added worked example for old projects that never used `/sps`

## 2.2.0

- added project bootstrap helper (`scripts/bootstrap-sps.sh`) and
  `skills/sps/templates/` for deterministic `.sps/` creation
- added `scripts/lint-sps.sh` regression checks and `scripts/smoke-sps.sh`
- added thin host adapters under `skills/sps/hosts/` for Cursor, Codex,
  Antigravity, and Claude
- added `/sps audit` read-only mode (`AUDIT.md`)
- added mistake → rule promotion flow (`MISTAKE-PROMOTION.md`)
- added approval abort conditions and default asset weight budgets
- added worked examples (`EXAMPLES.md`) and SPS version stamping (`VERSION`)
- hardened uninstallers to clear mirrored `/sps` sync paths from the install
  manifest and default mirror roots
- added `scripts/check-powershell.ps1` for Windows parse checks when `pwsh`
  is available

## 2.1.0

- added hard anti-hallucination rules and Known / Assumed / Unverified labeling
- added mandatory always-write memory contract, including `./.sps/agent.md` for
  active host identity and a project `/sps` lock
- added low-end mobile hard gate: minimal mobile by default, no fancy/laggy
  phone effects unless explicitly approved
- updated approval packets and verification recipes to require mobile evidence
  and anti-hallucination checks
- refreshed profile/handoff templates and Claude plugin adapter for the stronger
  boot checklist

## 2.0.0

- rewrote `skills/sps/SKILL.md` into a capability-aware, project-scoped master workflow
- added reference docs for capability detection, install profiles, profile scoping, skill governance, project templates, approval packets, verification recipes, and logo sourcing
- replaced the old "works identically everywhere" story with explicit support levels and fallbacks
- introduced `minimal`, `balanced`, and `full` install profiles
- added stronger cross-agent default skills such as `web-design-guidelines`, `vercel-react-best-practices`, `vercel-composition-patterns`, and `webapp-testing`
- standardized brand/logo sourcing around `theSVG`
- updated the Claude plugin entrypoint and metadata to match the new behavior
- updated installers and repo templates to respect project-only vs personal-default rule scoping
- made installers target all agents explicitly via the Skills CLI, sync `/sps` into shared Gemini/Antigravity locations, and write an install manifest for robust uninstall
- changed uninstallers to remove installed skills through the Skills CLI first, then perform legacy/manual path cleanup, with full removal as the default behavior
- added direct `/sps` mirroring into Claude, Cursor, Codex, universal-agent, and Gemini/Antigravity skill roots so local installs do not depend on host auto-detection
- added noninteractive uninstall flags, isolated npm/npx cache handling, and nonzero installer exit codes for automation-safe smoke testing
