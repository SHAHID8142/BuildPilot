# SPS — Phase 01: Baseline Forensic Audit

**Auditor role:** Forensic software architect / repository auditor (read-only)
**Date of audit:** 2026-10-03
**Repository audited:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`
**Declared version:** 4.0.0 (`skills/sps/VERSION`)
**Audit mode:** Read-only. No source, config, dependency, or state was modified.
**Files created by this audit:** this report only.

> **Scope note.** This report records *what exists today*, not what should be built.
> Nothing in this document is an implementation instruction.

---

## 0. Evidence Method & Confidence

Every classification is tagged with one of:

`VERIFIED` (concrete file/line/command-output evidence) · `PARTIAL` (some evidence, incomplete coverage) ·
`MISSING` (searched, no evidence found) · `BROKEN` (evidence exists but is contradictory or non-functional) ·
`UNKNOWN` (cannot be proven from the repository) · `N/A`

**Commands actually executed during this audit** (all read-only, none state-changing):

| Command | Result |
|---|---|
| `bash -n` on all 13 shell scripts | All OK (syntax valid) |
| `bash scripts/lint-sps.sh` | `== SPS lint PASSED ==` |
| CI `version-sanity` logic replicated locally | All 4 checks OK |
| `diff -rq scripts skills/sps/scripts` | Identical (mirrors in sync) |
| `find`/`grep` term-frequency sweeps | Used for absence claims |

**Commands deliberately NOT executed** (would mutate machine state, prohibited by Phase 01):
`install.sh`, `uninstall.sh`, `get-sps.sh`, `scripts/sps-update.sh`, `scripts/bootstrap-sps.sh`,
`scripts/smoke-sps.sh`, `scripts/sps-doctor.sh --fix`. Their *code* was read and audited statically instead.

**Limits of this audit**
- The working copy is **not a Git repository** (`fatal: not a git repository`). No commit history, branch,
  blame, or remote could be inspected. History-dependent claims are `UNKNOWN`.
- No dependency manifest exists at repo root, so no third-party code could be verified present/absent.
- Runtime LLM behaviour cannot be proven from static files; anything depending on agent compliance is
  classified `PARTIAL` and flagged as *instruction-only*.

---

## 1. Repository Baseline

### 1.1 What SPS actually is

`VERIFIED` — SPS is **not an application and not a framework**. It is a *prompt-and-script distribution system*
for AI coding agents, in two layers:

| Layer | Nature | Location |
|---|---|---|
| **Instruction layer** (LLM-dependent) | Markdown laws/policies read by the agent | `skills/sps/*.md`, `skills/sps-cms/*.md`, `plugins/.../SKILL.md` |
| **Machinery layer** (deterministic) | Bash/PowerShell installers, updaters, health checks | `install.sh`, `uninstall.sh`, `get-sps.sh`, `scripts/*` |
| **Template layer** | Files copied into user projects | `skills/sps/templates/*`, `skills/sps-cms/templates/*` |

There is **no runtime, no daemon, no orchestrator process, no scheduler**. Behaviour is enforced almost
entirely by instructing the LLM. This is the single most important architectural fact in this report.

### 1.2 Platform targets

`VERIFIED`

| Target | Mechanism | Evidence |
|---|---|---|
| macOS / Linux | `install.sh`, `get-sps.sh`, `uninstall.sh` | shebang `#!/usr/bin/env bash`; 432/71/240 LOC |
| Windows | `install.ps1`, `get-sps.ps1`, `uninstall.ps1` | 13 `.ps1` files, 18.4 KB installer |
| CI on `ubuntu-latest` | `.github/workflows/sps-ci.yml` | 3 jobs |

Note: `install.sh` uses **bash-only** constructs (`[[ ]]`, arrays, `${var//}`), so it is not POSIX `sh` compatible.

### 1.3 Agents currently supported

`VERIFIED` — 13 install targets in `install.sh` `build_agent_args()` (lines 142-158):
`claude-code, cursor, codex, antigravity, antigravity-cli, windsurf, github-copilot, opencode, cline, roo, kiro-cli, amp, universal`.

Host adapters exist for **8** of these: `skills/sps/hosts/{claude,cursor,codex,copilot,antigravity,windsurf,opencode,generic}.md`.
`cline, roo, kiro-cli, amp` have **no dedicated adapter** — they fall through to `generic.md`.

Sync paths cover **17** filesystem roots (`install.sh` lines 32-50). These are host-guessing directory layouts
written unconditionally, not host detection — `detect_hosts()` (lines 107-114) only *prints* status and never
gates the sync.

### 1.4 Install / invoke / update / uninstall

**Install** `VERIFIED`
```
get-sps.sh -> git clone -> install.sh
  1. detect_hosts()            (print only)
  2. npx skills add "$REPO" -g --copy -y --agent <13 targets>
  3. ~28 more npx skills add   (hardcoded GitHub list)
  4. Claude plugins + Trail of Bits (only if `claude` CLI present)
  5. Context7 MCP   (only if `claude` CLI present, --scope project)
  6. graphify       (only if uv or pip present)
  7. seed_global_memory()  -> ~/.sps/personal-defaults.md, global-mistakes.md, learned/INDEX.md
  8. sync_core_skill()      -> cp -R sps + sps-cms into all 17 SYNC_PATHS
  9. write_manifest()       -> ~/.sps/install-manifest.env
```
Exit policy (lines 423-432): succeeds if `~/.claude/skills/sps/SKILL.md` **and** `~/.cursor/skills/sps/SKILL.md`
both exist, even if every optional skill failed. This is a deliberate "mirrors healthy" heuristic.

**Invoke** `PARTIAL` — No `commands/` directory exists anywhere in the repo (verified by `find -type d -name commands`
-> empty). `/sps`, `/sps audit`, `/sps sync`, `/sps doctor` are declared only as *text* in
`skills/sps/SKILL.md` frontmatter (line 5) and body. Whether each host actually registers these as slash
commands is host-dependent and `UNKNOWN`. `sps-doctor.sh` "Doctor" mode explicitly allows running the script
instead of the command.

**Update** `VERIFIED` — `check-update.sh` fetches `skills/sps/VERSION` from `raw.githubusercontent.com`, compares
semver, caches 24 h in `~/.sps/update-state.env`, exits `0/1/2`. `sps-update.sh` then `git pull --ff-only`,
falling back to **`git reset --hard origin/$BRANCH`**, then re-runs `install.sh --yes`, then doctor.
Both `get-sps.sh:52` and `sps-update.sh:106` contain that hard reset.

**Uninstall** `VERIFIED` — reads the manifest, `npx skills remove` (28 skills), `rm -rf` across ~20 path patterns
per skill, then a redundant second pass over 10 default sync paths, then Claude plugins, marketplaces,
Context7 MCP, graphify, and finally `rm -rf ~/.sps` unless `--keep-personal`.

### 1.5 Configuration, project state, memory

| Concern | Location | Status |
|---|---|---|
| Install manifest | `~/.sps/install-manifest.env` | `VERIFIED` (`install.sh:221-244`) |
| Update cache | `~/.sps/update-state.env` | `VERIFIED` |
| Personal defaults | `~/.sps/personal-defaults.md` | `VERIFIED` |
| Global mistakes | `~/.sps/global-mistakes.md` | `VERIFIED` |
| Learned topics | `~/.sps/learned/INDEX.md` | `VERIFIED` |
| Source clone | `~/.sps/src/Shahid-Personal-SkillSet` | `VERIFIED` |
| **Project state** | `./.sps/` | `VERIFIED` (13 templates in `skills/sps/templates/`) |
| **Project root locks** | `AGENTS.md` / `GEMINI.md` / `CLAUDE.md` | `VERIFIED` in `bootstrap-sps.sh:113-126` |

### 1.6 Deterministic vs LLM-dependent vs hardcoded vs discovered

| Category | Members |
|---|---|
| **Deterministic** | install, sync, uninstall, version compare, lint, smoke, doctor, bootstrap file copy, version stamping |
| **LLM-dependent** | every "hard law", all gates, discovery, planning, section DoD, approval, audit scoring, research-before-design, CMS coupling |
| **Hardcoded** | ~28 skill names + GitHub URLs (`install.sh:340-368`), 17 sync paths, 13 agents, Lighthouse thresholds (Perf >=90 / SEO 100 / A11y 100 / BP 100), asset budgets, taste-skill default, `sps-cms` mandatory |
| **Dynamically discovered** | **almost nothing** — only host *printing*, CLI-presence checks (`claude`/`uv`/`pip`), and a registry-slug lookup pattern in `LOGO-SOURCES.md` |

**This asymmetry is the root architectural finding**: the system is deterministic about *installing its own files*
and non-deterministic about *everything it governs after install*.

---

## 2. Repository Integrity Anomalies (observed, NOT fixed)

| # | Finding | Severity | Evidence |
|---|---|---|---|
| I-1 | **Not a Git repository.** No `.git` | High | `git status` -> `fatal: not a git repository` |
| I-2 | **Four version drift points.** `sps-cms/package.json` = **1.4.0** vs `skills/sps-cms/VERSION` = **2.3.0**; `plugin.json` = **2.0.0**; `marketplace.json` = **2.0.0**; core = 4.0.0 | Medium | Direct file reads |
| I-3 | **Orphan debug artifacts at root**: `test_claude.sh`, `test_timeout.sh`, `test_uiux.sh`, `.test.out`, `.tmp.test_file` — not referenced by CI or lint | Medium | `ls`; `.test.out` contains real CLI output "No plugins installed" |
| I-4 | `CATALOG.md` documents 3 install profiles (`core`/`full`/`minimal`) — **contradicts** 4.0.0 "single unified install" | Medium | `CATALOG.md:17-21` vs `README.md:59` |
| I-5 | `CATALOG.md` lists `hallmark` as primary anti-slop skill — contradicts `design-taste-frontend` v2 routing | Medium | `CATALOG.md:28` vs `SKILL-ROUTER.md:22` |
| I-6 | Inconsistent `sps-cms` repo slug across 4 files: `SHAHID8142/sps-cms` vs `SHAHID8142/Shahid-Personal-SkillSet` | Low | `CMS-COUPLING.md:19` vs `SKILL-ROUTER.md:71` |
| I-7 | `compute_total_steps()` **defined twice** (lines 116 and 136) in `install.sh` — identical body, harmless but a code smell | Low | Source read |
| I-8 | `uninstall.sh` MANAGED_SKILLS default contains `taste-skill`, which `install.sh` never installs | Low | Cross-file comparison |
| I-9 | **Project lock is broken in this very repo**: `./.sps/` exists but `AGENTS.md`/`GEMINI.md`/`CLAUDE.md` are all **absent**, and `.sps/plan.md` is **missing** | High | `ls` -> No such file |
| I-10 | `.sps/profile.md` has empty `Skill version:`, `Name:`, `Goal:`; `.sps/handoff.md` empty; `.sps/audit-report.md` is an untouched template | Medium | File reads |
| I-11 | CI `version-sanity` checks only `skills/sps/VERSION`; drift in I-2 is structurally undetectable by CI | Medium | `.github/workflows/sps-ci.yml:41-53` |
| I-12 | `bootstrap-sps.sh` **auto-applies updates** (lines 138-142) — a bootstrap that mutates global machine state, contrary to its documented purpose | Medium | Source read |
| I-13 | No `commands/` directory despite slash commands being the documented interface | Medium | `find -type d -name commands` -> empty |

---

## 3. Capability Map

Status legend: `V`=VERIFIED, `P`=PARTIAL, `M`=MISSING, `B`=BROKEN, `U`=UNKNOWN, `N/A`.
**"Instr." = instruction-only (no deterministic enforcement).**

### 3.1 Core orchestration

| Capability | Status | Evidence | Location | Notes |
|---|---|---|---|---|
| Agent control | P | Lock + host adapters | `SKILL.md:26`, `PROFILE-SCOPING.md:44-51` | Instr.; `agent.md` records host |
| Agent instruction system | V | 13 law files + frontmatter | `skills/sps/*.md` | Loaded by LLM, not by code |
| Workflow orchestration | P | 4 modes (build/audit/sync/doctor) | `SKILL.md:46-70` | Instr. |
| Task management | P | Per-section todo template | `TODO-FORMAT.md`, `templates/section-todo.example.md` | Instr.; no live tracker |
| Planning | P | Plan gate + template | `PLAN-GATE.md`, `templates/plan.md` | Instr.; strongest control |
| Execution control | P | Abort conditions (9) | `APPROVAL-PACKETS.md:107-118` | Instr. |
| Verification | P | Recipes + DoD + Lighthouse gate | `VERIFICATION-RECIPES.md`, `SECTION-DOD.md:53-58` | Instr.; agent self-reports |
| Approval gates | P | Tier1/Tier2 + batch + manual loop | `APPROVAL-PACKETS.md` | Instr.; bypassable via `batch approve` |
| Conversation flow | M | — | — | No mechanism |
| User interaction | P | Discovery "grill", `grill-me` skill | `SKILL.md:29`, `SKILL-ROUTER.md:32` | Instr.; skill not bundled |
| Stop conditions | P | 4 plan abort + 9 chunk abort | `PLAN-GATE.md:29-36` | Instr. |
| Failure handling | P | Lane failure rules | `SUBAGENT-PLAYBOOK.md:50-56` | Instr.; re-run in-lane |
| Retry handling | M | — | — | "retry" appears only in installer error text |
| Rollback handling | M | One checklist line | `VERIFICATION-RECIPES.md:51` | Deploy recipe only |

### 3.2 Multi-agent system

| Capability | Status | Evidence | Location | Notes |
|---|---|---|---|---|
| Agent discovery | U | — | — | No runtime discovery of agents |
| Agent registry | M | — | — | No registry structure exists |
| Agent roles | V | 10-role checklist | `ROLE-MATRIX.md:15-26` | Instr.; strong |
| Specialist agents | P | 5 lanes | `SUBAGENT-PLAYBOOK.md:8-16` | Names only; not implemented |
| Subagents | P | Playbook + plan template | `SUBAGENT-PLAYBOOK.md`, `templates/plan.md:66-70` | Instr. |
| Parallel execution | P | Lane model | `SUBAGENT-PLAYBOOK.md` | Instr.; host-dependent |
| Sequential execution | V | One-section-in-flight rule | `SUBAGENT-PLAYBOOK.md:20-21` | Instr. |
| Delegation | P | Handoff format | `SUBAGENT-PLAYBOOK.md:39-48` | Text template |
| Agent handoff | P | Single-writer + 5-min window | `WORKSPACE-HYGIENE.md:18-28` | Instr.; time heuristic |
| Agent-to-agent comms | M | — | — | No mechanism beyond markdown |
| Shared project state | V | `./.sps/` + `agent.md` | `PROFILE-SCOPING.md:14-31` | Real files, LLM-managed |
| Conflict handling | P | Orchestrator decides ownership | `SUBAGENT-PLAYBOOK.md:51-56` | Instr. |
| Result aggregation | P | Convergence gate | `SUBAGENT-PLAYBOOK.md:36-37` | Instr. |
| Manager/supervisor agent | P | Orchestrator role | `SKILL.md` (whole file) | Single in-session agent |

### 3.3 Skill system

| Capability | Status | Evidence | Location | Notes |
|---|---|---|---|---|
| Skill discovery | P | Domain detection + table lookup | `SKILL-ROUTER.md:6-16` | Table-based, not discovery |
| Skill installation | V | 28 `npx skills add` calls | `install.sh:338-368` | Deterministic, global `-g` |
| Skill selection | P | One primary + one secondary | `SKILL-ROUTER.md:8-11` | Fixed table |
| Skill ranking | M | — | — | No scoring/quality ranking |
| Skill validation | P | Install exit codes + lint greps | `install.sh:172-192`, `lint-sps.sh` | Validates install, not content |
| Skill compatibility detection | P | Manual matrix | `CAPABILITY-MATRIX.md:12-22` | No detection code |
| Skill versioning | P | `VERSION` files + manifest | `skills/*/VERSION` | **BROKEN for sps-cms** (I-2) |
| Skill lifecycle | M | — | — | No create/deprecate/archive flow |
| Skill removal | V | CLI + path sweep | `uninstall.sh:141-175` | Deterministic |
| Skill update | V | Pull + reinstall | `sps-update.sh` | Reinstalls all |
| Project-local skills | M | — | — | All installs use global `-g` |
| Global skills | V | `-g` everywhere | `install.sh:338-368` | Everything global |
| Dynamic skill selection | M | — | — | **Contradicts requirement 8** |
| Skill fallback | V | Explicit fallback chain | `SKILL-ROUTER.md:16`, `CAPABILITY-MATRIX.md:33-39` | Good coverage |
| Skill conflict resolution | V | Conflict ban list | `SKILL-ROUTER.md:41-50` | Instr. |

### 3.4 MCP system

| Capability | Status | Evidence | Location | Notes |
|---|---|---|---|---|
| MCP discovery | M | — | — | `.mcp.json` is an empty stub |
| MCP selection | M | — | — | No logic |
| MCP installation | P | Context7 only | `install.sh:272-282` | Claude-only, project scope |
| MCP validation | M | "already exists" check | `install.sh:276` | Idempotency only |
| MCP lifecycle | M | Install + uninstall | `install.sh:274`, `uninstall.sh:194-196` | context7 only |
| Project-local MCPs | P | `--scope project` | `install.sh:274` | Single MCP |
| MCP compatibility | P | Matrix column | `CAPABILITY-MATRIX.md:12-16` | Manual "Strong/Varies" |
| MCP failure handling | P | "Never assume MCP" | `CAPABILITY-MATRIX.md:44` | Documented, not coded |
### 3.5 Research system

| Capability | Status | Evidence | Location | Notes |
|---|---|---|---|---|
| Technology research | P | "Research before design" | `DESIGN-GATE.md:14-16` | Design-scoped only |
| Documentation research | P | Context7 or "official docs fetch" | `SKILL-ROUTER.md:39` | No protocol |
| Best-practice research | P | Design Research Packet template | `DESIGN-GATE.md:23-34` | Template only |
| Open-source project research | M | — | — | No GitHub search capability |
| GitHub research | M | — | — | Grep for GitHub-search = 0 |
| skill.sh research | M | — | — | Grep = 0; appears only as an install channel in `sps-cms/README.md:57` |
| MCP discovery (research) | M | — | — | No discovery mechanism |
| Version compatibility research | M | — | — | No mechanism |
| Security research | P | Trail of Bits skills | `SKILL-ROUTER.md:36` | External plugin, not bundled |
| Architecture research | P | Alternatives in examples | `EXAMPLES.md:12` | One example line |

### 3.6 Project state

| Capability | Status | Evidence | Location | Notes |
|---|---|---|---|---|
| Project memory | V | `.sps/` + 13 templates | `PROFILE-SCOPING.md:14-31` | Bootstrap verified |
| Project instructions | V | Root mirrors | `PROJECT-ROOT-MIRRORS.md` | 3 files |
| Project plan | V | `plan.md` template | `templates/plan.md` | 10 sections |
| Task list | V | `section-todos/` | `TODO-FORMAT.md` | Per-section files |
| Decisions | V | `changelog-sps.md` | `templates/changelog-sps.md` | Append-only |
| Requirements | P | Inside plan/profile | `templates/plan.md:7-11` | No dedicated requirements doc |
| Architecture records | V | `architecture.md` | `templates/architecture.md` | 7 lines only |
| Agent handoff records | V | `handoff.md` | `templates/handoff.md` | Single template |
| Verification records | P | Embedded in handoff | `templates/handoff.md:35-38` | No dedicated file |
| Audit records | V | `audit-report.md` | `templates/audit-report.md` | 100-point scored |
| Changelog | V | Repo + project | `CHANGELOG.md`, `templates/changelog-sps.md` | Both exist |
| Progress tracking | P | Status column | `templates/section-registry.md` | Status enum only |

### 3.7 Developer workflow

| Capability | Status | Evidence | Location | Notes |
|---|---|---|---|---|
| Git integration | P | Installer/update use git | `get-sps.sh`, `sps-update.sh` | **SPS's own git only — no user-project git integration** |
| Commit checkpoints | M | — | — | Zero mentions in `skills/` |
| Diff inspection | M | — | — | No mention |
| Testing | V | `lint-sps.sh` + `smoke-sps.sh` | `scripts/` | For SPS itself, not target projects |
| Linting | V | grep-based lint | `lint-sps.sh` (121 checks) | Verifies text presence, not correctness |
| Formatting | M | — | — | No formatter config |
| Build verification | P | DoD item 23 | `SECTION-DOD.md:86` | Instr. |
## 4. Audit Against Master Requirements

### 5. Universal Project Discovery

`PARTIAL` — discovery exists as an *instruction* ("Mandatory Discovery… Grill until complete on goals, stack, CMS,
auth, mobile policies, multi-agent roles, deploy targets", `SKILL.md:29`) with per-stack prompt templates in
`PROJECT-TEMPLATES.md` (7 archetypes) and audit checks B1-B4.

| Discovery area | Status | Evidence |
|---|---|---|
| project type / application type | P | `PROJECT-TEMPLATES.md` archetypes; audit B1 |
| target users | P | `EXAMPLES.md:10` only |
| business requirements | P | `EXAMPLES.md:14` business-outcome role |
| technical requirements | P | `templates/plan.md:13-23` stack table |
| functional requirements | M | Success criteria = one line in plan §1 |
| non-functional requirements | M | Only Lighthouse numbers |
| platforms | P | Deploy target in plan §7 |
| deployment target | P | `templates/plan.md:56-59` |
| integrations | M | No integration checklist |
| authentication requirements | P | `sps-cms` discovery grill; plan stack table |
| authorization requirements | M | Role field in code only |
| database requirements | P | `sps-cms/METHOD-CARD.md:22-26` DB engine grill |
| CMS requirements | V | `CMS-COUPLING.md`, `sps-cms` |
| SEO requirements | M | 1 DoD line (see §13) |
| accessibility requirements | P | DoD item 8 + Lighthouse A11y 100 |
| analytics requirements | P | `sps-cms/GLOBAL-SETTINGS.md` GA4/GTM/Pixel |
| monitoring requirements | M | — |
| security requirements | P | DoD item 21 (one line) |
| performance requirements | V | `MOBILE-LOW-END.md`, `ASSET-BUDGET.md`, Lighthouse gate |
| legal/compliance requirements | M | Only a logo trademark note (`LOGO-SOURCES.md:43`) |

**Finding:** discovery is asymmetric — strong on stack/CMS/deploy/performance, essentially absent for
integration, monitoring, legal/compliance, and non-functional requirements.

### 6. Planning System Audit (15 required steps)

`PARTIAL` — `PLAN-GATE.md` + `templates/plan.md` implement the gate shape but not the full chain.

| # | Required step | Status | Evidence |
|---|---|---|---|
| 1 | Understand the request | P | Discovery grill, `SKILL.md:29` |
| 2 | Ask missing questions | P | `SKILL.md:29` "Grill until complete" |
| 3 | Identify ambiguities | P | `ANTI-HALLUCINATION.md:36-48` Known/Assumed/Unverified; Karpathy block |
| 4 | Identify dependencies | M | No dependency analysis in plan template |
| 5 | Research required technologies | M | Not a plan-gate step (see §7) |
| 6 | Research current best practices | M | Only `DESIGN-GATE.md` for design |
| 7 | Discover relevant skills | P | Router consulted per chunk, not at plan time |
| 8 | Discover relevant MCPs | M | — |
| 9 | Evaluate alternatives | P | One example (`EXAMPLES.md:12`); not gate-required |
| 10 | Produce architecture plan | V | `PLAN-GATE.md:18-27` + `templates/plan.md` |
| 11 | Produce task breakdown | P | Section inventory + `TODO-FORMAT.md`; no dependency order |
| 12 | Identify acceptance criteria | V | `templates/plan.md:9-11` measurable criteria |
| 13 | Identify verification criteria | V | `templates/plan.md:72-77` |
| 14 | Obtain user approval | V | `PLAN-GATE.md:10-12` explicit stop |
| 15 | Execute only after approval | P | Instr.; `plan.md` status self-reported by LLM |

**Deterministic enforcement of step 15: NONE.** No script reads `.sps/plan.md` status. The `approved` string is
written by the agent, so the gate is honour-system, not enforced.

### 7. Technology Learning / Research Gate

### 8. Dynamic Skill Discovery Audit

`MISSING` — **This is the most significant gap against the stated target behaviour.**

Desired: *"Choose the best appropriate skill for the current task, project, technology, and context rather than
permanently forcing one skill."* Current reality is the **exact opposite**:

| Required capability | Status | Evidence |
|---|---|---|
| Discover skills dynamically | M | `SKILL-ROUTER.md` is a static 20-row table |
| Search GitHub | M | Grep for GitHub-search behaviour = 0 |
| Search skill.sh | M | Grep = 0; appears only as install channel in `sps-cms/README.md:57` |
| Search other sources | M | No search protocol |
| Evaluate quality / maintenance | M | No criteria exist |
| Evaluate popularity / recency | M | No criteria exist |
| Evaluate compatibility | P | `CAPABILITY-MATRIX.md` is host-level, not skill-level |
| Evaluate security / licence | M | Only "Review third-party skills" (`README.md:231`) |
| Evaluate documentation | M | No criteria |
| Compare multiple candidates | M | — |
| Select best candidate | M | Table lookup, not selection |
| Install project-locally | M | All installs are global `-g` |
| Record the decision | P | Approval packet has a "Skills selected" field |
| Remove when no longer required | M | Only whole-stack uninstall |
| Prevent unnecessary global install | M | `install.sh` installs all 28 globally, always |

**Root cause:** `SKILL-ROUTER.md` and `install.sh` together hardcode a permanent preference set. Changing it
requires editing Markdown and re-running the installer. The "one primary per domain" table is a **static
allow-list**, and `SKILL-GOVERNANCE.md:35` explicitly promotes `design-taste-frontend` as "the only default taste
operator" — a permanent hardcoded preference by design.

Internal tension: `SKILL-ROUTER.md:11-14` *does* say "if a required skill is missing, try install… or give the user
exact manual install steps". That is the only adaptive path, and it triggers on **absence only** — never on
quality, fit, or context.

### 9. Project-Local Resource Audit

`PARTIAL` — project state is project-local; **skills and MCPs are global by design.**

| Resource | Current location | Scope | Flag |
|---|---|---|---|
| Project memory | `./.sps/*.md` | **Local** | OK |
| Project instructions | `./AGENTS.md`, `GEMINI.md`, `CLAUDE.md` | **Local** | OK |
| Plans | `./.sps/plan.md` | **Local** | OK |
| Task lists | `./.sps/section-todos/` | **Local** | OK |
| Architecture | `./.sps/architecture.md` | **Local** | OK |
| CMS debt / foundation | `./.sps/cms-*.md` | **Local** | OK |
| Design system | `./.sps/design-system.md` | **Local** | OK |
| Agent handoff | `./.sps/handoff.md`, `agent.md` | **Local** | OK |
| Audit reports | `./.sps/audit-report.md` | **Local** | OK |
| Changelog | `./.sps/changelog-sps.md` | **Local** | OK |
| **Skills (28)** | `~/.claude/skills/`, `~/.cursor/skills/`, … 17 roots | **GLOBAL** | **VIOLATION** |
| **MCP (Context7)** | project scope via CLI, but one fixed global choice | Mixed | Concern |
| Install manifest | `~/.sps/install-manifest.env` | Global | Acceptable (machine-level) |
| Update cache | `~/.sps/update-state.env` | Global | Acceptable |
| Personal defaults | `~/.sps/personal-defaults.md` | Global | By design, approval-gated |
| Global mistakes | `~/.sps/global-mistakes.md` | Global | By design |
| Learned topics | `~/.sps/learned/INDEX.md` | Global | By design |
### 10. User Approval Gate Audit

`PARTIAL` — **approval is extensively specified but never enforced.** No code path checks for approval.

| Approval area | Status | Enforcement | Evidence |
|---|---|---|---|
| requirements | P | Instr. | Discovery grill, no gate |
| architecture | P | Instr. | Tier2 packet field |
| technology selection | M | None | Not a packet field |
| skill selection | P | Instr. | `APPROVAL-PACKETS.md:46-48` |
| MCP selection | M | None | No packet field |
| implementation plan | V | Instr. | `PLAN-GATE.md:10-12` |
| task execution | P | Instr. | Tier1/Tier2 |
| major architectural changes | P | Instr. | "major sections" route to Tier2 |
| scope changes | M | None | No rule |
| deployment | P | Instr. | DoD item 25 |
| destructive operations | M | None | **No rule at all** |

**Deterministic enforcement: NONE.** Per the brief's four categories: approval is **consistently specified but
inconsistently enforced** — 100% suggestion in instruction text, with three explicit bypasses:

1. `APPROVAL-PACKETS.md:72-77` — `batch approve` lets the agent run consecutive sections unattended.
2. `APPROVAL-PACKETS.md:11-13` + `PLAN-GATE.md:38-42` — Tier 1 quick-fixes bypass the plan gate entirely.
3. `SKILL.md:63-64` — read-only Q&A carve-out skips the whole session boot.

Counter-evidence: `hosts/antigravity.md:12-28` defines a 7-point "boot refusal" instructing the agent to *stop
coding* if checks fail — the strongest approval-adjacent control in the system, and still instruction-only.

**Destructive-operation gap is notable:** the *installer* performs `rm -rf ~/.sps` and `git reset --hard`, but
`APPROVAL-PACKETS.md` has no rule requiring user approval for destructive file or VCS operations in a project.

### 11. Vertical-Slice / Section Completion Audit

`VERIFIED` (as a concept) — **SPS genuinely understands this.** It is its strongest differentiator.

`CMS-COUPLING.md:8-13`: *"A section is **incomplete** until its storefront UI **and** CMS controls for that
section ship together. Storefront-only delivery is forbidden."* Reinforced by `cms-debt.md`, `/sps sync`, and
audit checks H1/H2 (16 of 100 points).

Coverage of the 16 required section layers:

| Layer | Status | Evidence |
|---|---|---|
| frontend | V | `SECTION-DOD.md:37` |
| CMS model | V | `CMS-COUPLING.md:38` |
| editable fields | V | `content-model.md` field matrix |
| permissions | M | Role field in code, no DoD item |
| backend/API | P | Tier2 packet field |
| database | P | `sps-cms/METHOD-CARD.md` step 2 |
| validation | P | DoD item 21 |
| media | V | `cms-foundation.md`, upload rules |
| integration | M | — |
| preview | P | `cms-foundation.md` "Preview / read path" |
| error handling | V | DoD item 6 |
| testing | V | DoD items 10-11 |
| accessibility | V | DoD item 8 + Lighthouse 100 |
| SEO | P | DoD item 9 (one line) |
| performance | V | Lighthouse gate + asset budget |
| security | P | DoD item 21 (one line) |
| verification | V | DoD §8 + round-trip proof |

**Caveat:** dependency-awareness is **flat, not graph-based**. `SECTION-DOD.md` is a 29-item checklist with
### 12. CMS Requirement Audit

`PARTIAL` — Deep and opinionated, but skewed to *client editor experience*, thin on *governance*.

| Requirement | Status | Evidence |
|---|---|---|
| CMS detection | V | Discovery grill; mandatory `sps-cms` |
| CMS architecture | V | `sps-cms/METHOD-CARD.md` 6-step loop; adapters for 9 stacks |
| content modelling | V | `cms.config.ts` template; polymorphic collections |
| editable fields | V | `data-sps-key` law (`sps-cms/SKILL.md:84-88`) |
| locked fields | P | Brand-locked exception (`CMS-COUPLING.md:50-51`) |
| developer-controlled fields | M | No explicit tier concept |
| client-controlled fields | V | Core premise |
| roles | P | `admin`/`editor` in `auth-helper.ts`; role hardcoded to `'admin'` on creation |
| permissions | M | No permission matrix |
| Super Admin / Admin | M | Not modelled separately |
| preview | P | `cms-foundation.md` field; no preview-mode doc |
| publishing | P | `status` column exists in SQL |
| draft state | P | `status DEFAULT 'published'` — draft not first-class |
| validation | P | Upload validation only |
| media library | V | `sps_media` table; `MediaUploader.tsx` |
| direct uploads | V | Upload rules in `SECURITY-AND-BACKUPS.md` |
| external image URL import | M | — |
| image optimization | M | Asset budget mentions WebP/AVIF, not a CMS pipeline |
| asset metadata | M | — |
| asset replacement | V | DoD item 4; roundtrip gate 4 |
| asset deletion | V | DoD item 4 |
| content versioning | M | **No version table, no history** |
| audit logs | M | **Not present** |
| API integration | V | 5 universal API templates |
| frontend synchronization | V | `AUTO-SYNC-PROTOCOL.md` single-source-of-truth |
| cache invalidation | M | `AUTO-SYNC-PROTOCOL.md:27` *asserts* "zero frontend cache clearance is needed" — unverified |
| deployment readiness | P | Not CMS-specific |

**Engineering findings in `sps-cms` templates:**

1. **`auth-helper.ts:8` hardcodes a default session secret:**
   `process.env.ADMIN_SESSION_SECRET || 'sps-cms-default-super-secure-secret-key-32chars!'`
   A deployment that forgets the env var runs with a **publicly known key**. Most severe code-level finding.
2. **`auth-helper.ts:12` ignores the `role` parameter**, always encoding `'admin'`.
3. **`SECURITY-AND-BACKUPS.md` contradicts itself on upload size:** 10MB image / 50MB video (line 28) vs
   `sps-cms/SKILL.md:100` "a 15MB cap".
4. Backup claims "**encrypted**/compressed JSON snapshot" (`SECURITY-AND-BACKUPS.md:39`) with no encryption
   mechanism, key management, or restore-integrity verification described.
5. No password hashing exists at all — the admin model is a single hardcoded credential path.

### 13. SEO Requirement Audit

`PARTIAL` — one checklist line plus an external skill. Measured term coverage in `skills/sps/` core:

| Item | Files matching | Verdict |
|---|---|---|
| crawlability / indexing | 0 | `MISSING` |
| `robots.txt` / `sitemap.xml` | 0 | `MISSING` |
| canonical URLs | 6 (mostly "canonical paths" false positives) | `PARTIAL` — 1 real use |
| metadata / titles / descriptions | — | `PARTIAL` — `SECTION-DOD.md:51` |
| headings / semantic HTML | 0 direct | `PARTIAL` — via external skills |
| image alt text | 1 | `PARTIAL` — DoD item 13 |
| structured data | 3 | `PARTIAL` — DoD line |
| Open Graph | 1 | `PARTIAL` — DoD line |
| social images / internal linking / URL structure | 0 | `MISSING` |
| redirects / broken links / duplicate content / pagination | 0 | `MISSING` |
| international SEO / hreflang | 0 | `MISSING` in core (i18n exists as translation, not SEO) |
| Core Web Vitals | 1 (Lighthouse scores, not CWV metrics) | `PARTIAL` |
### 14. Code Quality Audit

`PARTIAL` — enforced for SPS itself; **not transferred to target projects**.

| Item | Status | Evidence |
|---|---|---|
| strict typing | P | DoD "zero typecheck blockers"; no tsconfig in repo |
| linting | V | `lint-sps.sh` (121 grep checks) |
| formatting | M | No formatter config anywhere |
| dead-code elimination | P | DoD item 19 |
| dependency hygiene | M | — |
| unit tests | M | **No test framework**; `smoke-sps.sh` is shell assertions |
| integration tests | M | — |
| E2E tests | M | `webapp-testing` skill external, not bundled |
| pre-commit hooks | M | Zero mentions of `pre-commit`/`husky`/`lint-staged` |
| CI | V | `.github/workflows/sps-ci.yml` — **for SPS only** |
| CD | M | `deploy-to-vercel` external; no CD pipeline |
| environment validation | P | DoD item 24 |
| API documentation | M | — |
| API versioning | M | — |
| staging | M | Zero mentions in `skills/` |
| rollback | P | 1 line (`VERIFICATION-RECIPES.md:51`) |

**Critical gap:** the CI workflow builds and lints **SPS's own Markdown**, not any project SPS governs. A target
project receives no CI/CD scaffolding from SPS — only an instruction to "run tests, typecheck, lint".

Also note `lint-sps.sh` verifies **text presence, not correctness**. Example: it asserts `install.sh` contains the
string `karpathy-guidelines` (line 106) — it cannot detect that the install step fails in practice. A passing lint
is therefore weak evidence of system health.

### 15. Database / Backend Audit

`PARTIAL` — only two schema files; almost all DB concerns absent.

| Item | Status | Evidence |
|---|---|---|
| indexing | P | 2 `CREATE INDEX` in `sqlite-schema.sql:29-30`; not discussed as a rule |
| connection pooling | M | 0 occurrences |
| N+1 prevention | M | 0 occurrences |
| migrations | P | Mentioned once (`sps-cms/METHOD-CARD.md:63`); no migration tooling |
| migration testing | M | — |
| backups | P | JSON snapshot claim; no scheduling/retention |
| point-in-time recovery | M | — |
| foreign keys | P | 4 files mention; **no `FOREIGN KEY` in `sqlite-schema.sql`** |
| cascade rules | M | — |
| idempotency | M | 0 occurrences |
| graceful shutdown | M | — |
| soft deletes | M | 0 occurrences; `status` column used instead |
| transaction handling | M | 0 occurrences |
| validation | P | Upload-side only |
| error handling | P | Generic; no DB error taxonomy |
| API security | P | Upload guards only |

`DATABASE-ADAPTERS.md` (90 lines) covers MySQL/Postgres/SQLite/D1 connections. The two schema files are
**illustrative templates, not production migrations** — `CREATE TABLE IF NOT EXISTS`, no versioning, no down path,
no FK constraints.

### 16. Security Audit

`PARTIAL` — **upload hardening only; the application-security surface is almost entirely absent.**

Term search across `skills/` for `csrf|xss|sql injection|rate limit|cors|csp|mfa|2fa|bcrypt|password hash|row level|rls`
returned **zero matches**.

| Item | Status | Evidence |
|---|---|---|
| authentication | P | `auth-helper.ts` (cookie token, AES-256-GCM) |
| authorization | M | No role/permission enforcement beyond a type union |
| server-side access control | M | — |
| RLS | M | — |
| SQL injection | M | Not addressed |
| XSS | M | — |
| CSRF | M | Cookie auth without a CSRF control — **and absent** |
| secure file uploads | V | `SECURITY-AND-BACKUPS.md` whitelist + MIME + traversal + size |
| secret management | **BROKEN** | `auth-helper.ts:8` hardcoded fallback secret |
| password hashing | M | No passwords exist; no hashing |
| email verification | M | — |
| secure tokens | P | AES-GCM token; default key flaw above |
| CORS / rate limiting / webhook verification / secure logging | M | — |
| dependency vulnerabilities | M | `README.md:231` "review third-party skills" only |
### 17. Performance Audit

`PARTIAL` — strong on mobile/low-end discipline, weak on general web performance.

| Item | Status | Evidence |
|---|---|---|
| caching / CDN / code splitting / minification | M | — |
| script optimization | M | — |
| pagination / skeleton loading / debouncing | M | — |
| unnecessary rerender prevention | M | Delegated to external `vercel-react-best-practices` |
| image optimization | P | `ASSET-BUDGET.md:10` AVIF/WebP preference |
| WebP/AVIF | P | `ASSET-BUDGET.md:10` |
| lazy loading | P | `ASSET-BUDGET.md:11` "lazy-load below the fold" |
| font optimization | P | `ASSET-BUDGET.md:16` ≤2 families/weights, subset |
| API compression | M | — |
| Lighthouse | V | `SECTION-DOD.md:53-58` thresholds + evidence requirement |
| Core Web Vitals | P | Implied by Lighthouse, not measured directly |
| load testing / stress testing | M | — |

**Positive:** `ASSET-BUDGET.md` gives concrete, testable budgets (hero ≤200KB mobile, inline ≤120KB, icons ≤20KB,
≤2 font families, 0–1 animation libraries) with explicit Fail conditions — unusually concrete for an instruction layer.

### 18. Accessibility Audit

`PARTIAL` — the goal is stated but operational detail is external.

| Item | Status | Evidence |
|---|---|---|
| WCAG | M | **0 occurrences of "WCAG"**; "A11y AA" asserted without citation (`SECTION-DOD.md:49`) |
| contrast | P | `ROLE-MATRIX.md:24` one question |
| keyboard navigation | P | `VERIFICATION-RECIPES.md:13`; touch targets in `MOBILE-LOW-END.md` |
| semantic HTML | P | Implied; not specified |
| ARIA | M | **0 real occurrences** (4 grep hits were substrings of "various"/"primary") |
| focus management | M | 0 occurrences |
| form accessibility | M | — |
| language attributes (`lang=`) | M | 0 occurrences |
| text scaling | M | 0 occurrences |
| reduced motion | V | `prefers-reduced-motion` — `MOBILE-LOW-END.md`, `SECTION-DOD.md:49` |
| screen reader support | M | 0 occurrences |
| accessible error states | P | DoD item 6 (generic states) |
| accessible loading states | M | 0 occurrences |

Mitigating: Lighthouse **Accessibility: 100** is a hard gate (`SECTION-DOD.md:56`), which would surface many
issues empirically — but only if the host can run a browser (`CAPABILITY-MATRIX.md` rates browser support as
"Varies" for most hosts).

### 19. UI / Design System Audit

`PARTIAL` — strong taste rules, thin system rules.

| Item | Status | Evidence |
|---|---|---|
| typography | P | `design-system.md` template field; font budget in `ASSET-BUDGET.md` |
| spacing | P | 2 files; "seamless sections / minimal gaps" |
| responsive design | V | `MOBILE-LOW-END.md` breakpoints 320/375/768/1024 |
### 20. Global No-Emoji Policy Audit

`MISSING` — **The policy does not exist in any form.**

Evidence:
- The string **"emoji" appears in 0 files** across the entire repository.
- **No icon library is named anywhere**: 0 occurrences of `lucide`, `phosphor`, `heroicons`, `radix`.
- No rule exists requiring user authorization before emoji use.
- No guidance for choosing an icon library based on project or context.

**The repository actively violates the policy it is supposed to enforce.** A code scan found **155 emoji
characters across 29 files**. Highest concentrations:

| Count | File |
|---|---|
| 17 | `skills/sps-cms/templates/visual-editor/LiveEditorOverlay.tsx` |
| 15 | `skills/sps-cms/scripts/doctor.sh` |
| 14 | `skills/sps-cms/scripts/doctor.ps1` |
| 12 | `skills/sps-cms/README.md` |
| 9 | `skills/sps-cms/templates/admin-ui/InquiriesInbox.tsx` |
| 9 | `skills/sps-cms/templates/admin-ui/AdminLayout.tsx` |
| 8 | `skills/sps-cms/scripts/install.sh` |

These are largely **user-facing UI templates shipped to client websites** (`LiveEditorOverlay.tsx`,
`InquiriesInbox.tsx`, `AdminLayout.tsx`), plus console output in installer scripts.

Compounding factor: `sps-cms/SKILL.md:95-96` **explicitly mandates emoji in user-facing admin UI**:
`Form fields render language tabs: [ 🇺🇸 EN | 🇧🇩 BN | 🇸🇦 AR (RTL) ]` and
`clicking [ ✨ Auto-Translate ]`. These are directives to *produce* emoji, directly contradicting "NO EMOJI BY DEFAULT".

Related: `ASSET-BUDGET.md:12` says "Icon / logo SVG — prefer SVG" — the only icon-adjacent rule, and it concerns
file format, not library selection or emoji policy.

### 21. Copy / Content Audit

`PARTIAL` — anti-slop rules exist; truthfulness and conversion rules do not.

| Rule | Status | Evidence |
|---|---|---|
| fake metrics | M | No explicit rule |
| fake testimonials | M | **0 occurrences of "testimonial"** |
| fabricated claims | P | `ANTI-HALLUCINATION.md:7-13` bans invented facts |
| placeholder text | M | Only "no fake dummy buttons" (`SKILL.md:32`) |
| vague headlines | M | — |
| generic AI copy | P | `DESIGN-GATE.md:17-19` rejects AI-slop layouts, card spam, badge clutter |
| unnecessary content | M | — |
| repetitive cards | P | "card spam" ban (`DESIGN-GATE.md:19`) |
| excessive marketing clichés | V | `SKILL.md:32` "no purple-on-dark clichés" |
| default framework titles | M | — |
| conversion principles | M | **No conversion/CRO guidance anywhere** |
| trust principles | M | **No trust-building guidance** |

**Scope note on `ANTI-HALLUCINATION.md`:** its bans target the **agent's own claims** ("tests passed", "build
succeeded", "deployed"), not **copy the agent writes into the product**. This is an engineering-honesty control,
not a content-truthfulness control. A product could ship invented statistics and still satisfy
`ANTI-HALLUCINATION.md` as written.

### 22. Agent Orchestration Audit (Manager/Supervisor Model)

`PARTIAL` — the topology exists as a **documented concept**, not as an implementation.

Current architecture is a **single in-session orchestrator** (`/sps`) that *role-plays* specialist concerns.
`SUBAGENT-PLAYBOOK.md` names 5 lanes plus 2 optional:

| Required agent | Status | Evidence |
|---|---|---|
| SPS ORCHESTRATOR | P | `SKILL.md` (whole file) — the only real agent |
| Research Agent | M | No such agent; only DESIGN-GATE research packet |
| Architecture Agent | M | No such agent; plan template section only |
| Frontend Agent | P | Lane role `ui-agent` (`SUBAGENT-PLAYBOOK.md:10`) — a role, not an agent |
| Backend Agent | M | No lane |
| Database Agent | P | Optional `db-agent` mentioned (`SUBAGENT-PLAYBOOK.md:59-60`) — name only |
| CMS Agent | P | Lane role `cms-agent` (`SUBAGENT-PLAYBOOK.md:9`) |
| SEO Agent | P | Merged into `content-agent` (`SUBAGENT-PLAYBOOK.md:12`) |
| Security Agent | P | Role-matrix row (`ROLE-MATRIX.md:22`) — a checklist question |
| QA Agent | P | Lane role `test-agent` (`SUBAGENT-PLAYBOOK.md:13`) |
| Performance Agent | P | Role-matrix row (`ROLE-MATRIX.md:25`); asset budgets |
| Accessibility Agent | P | Role-matrix row (`ROLE-MATRIX.md:24`) |
## 23. Consolidated Status Summary

### 23.1 By requirement area (§5–§22)

| Area | Status | One-line reason |
|---|---|---|
| 5. Universal project discovery | PARTIAL | Strong on stack/CMS/deploy; absent for integration, monitoring, legal |
| 6. Planning system | PARTIAL | Gate + template exist; research/dependency steps missing |
| 7. Technology learning gate | **MISSING** | No gate requires reading docs before choosing a tech |
| 8. Dynamic skill discovery | **MISSING** | Static hardcoded table; contradicts target behaviour |
| 9. Project-local resources | PARTIAL | State is local; all 28 skills are global |
| 10. User approval gate | PARTIAL | Extensively specified, zero deterministic enforcement, 3 bypasses |
| 11. Vertical-slice completion | VERIFIED | CMS-coupling law is real and central; flat checklist though |
| 12. CMS requirements | PARTIAL | Deep editor UX; no versioning, audit logs, permissions |
| 13. SEO requirements | **MISSING** (effectively) | 1 checklist line + unbundled external skill |
| 14. Code quality | PARTIAL | Enforced for SPS itself, not for target projects |
| 15. Database / backend | PARTIAL | 2 illustrative schemas; pooling/N+1/transactions absent |
| 16. Security | PARTIAL | Upload hardening only; hardcoded secret is BROKEN |
| 17. Performance | PARTIAL | Excellent mobile budgets; no caching/CDN/splitting |
| 18. Accessibility | PARTIAL | Goal + Lighthouse gate; no WCAG/ARIA detail |
| 19. UI / design system | PARTIAL | Strong taste doctrine; no tokens/dark mode/icons |
| 20. No-emoji policy | **MISSING** | Zero policy; repo itself uses 155 emoji |
| 21. Copy / content | PARTIAL | Anti-slop present; no truthfulness/conversion rules |
| 22. Manager/supervisor agents | PARTIAL | 4 of 14 nodes real; single agent role-plays the rest |

### 23.2 Counts

| Category | Count |
|---|---|
| Capabilities assessed | ~130 |
| VERIFIED | ~35 |
| PARTIAL | ~62 |
| MISSING | ~30 |
| BROKEN | 2 (`sps-cms` versioning, `auth-helper` secret) |
| UNKNOWN | 1 (agent runtime discovery) |

---

## 24. Top Findings for the Reviewing Architect

**F-1 — Determinism inversion (architectural).** SPS is deterministic about installing its own files and
non-deterministic about everything it governs. Every "hard law" is Markdown. No mechanism can *reject*
non-compliant output.

**F-2 — Dynamic skill discovery is absent, and hardcoded preference is the design.**
`SKILL-ROUTER.md` + `SKILL-GOVERNANCE.md:35` + `install.sh:340-368` together make a permanent global allow-list.
Changing the preferred skill requires editing Markdown and re-running the installer — the precise opposite of the
target behaviour in requirement 8.

**F-3 — A hardcoded fallback secret ships in a template** (`skills/sps-cms/templates/auth/auth-helper.ts:8`).
Deployments missing `ADMIN_SESSION_SECRET` run with a publicly known key. Highest-severity code finding.

**F-4 — Every external dependency is unbundled, so most specialist capability is UNKNOWN.**
28 third-party skills, Trail of Bits security, `ai-seo`, `web-design-guidelines`, `webapp-testing` are referenced by
name only. `SKILL-ROUTER.md:27,36` delegates SEO and security entirely to skills absent from this repository.
A clean-room environment would lose SEO, security, testing, and React-quality guidance.

**F-5 — SEO and the no-emoji policy are the two complete absences.** Both are named requirements with zero
implementation, and the repository actively contradicts the emoji principle (155 emoji, plus
`sps-cms/SKILL.md:95-96` mandating flags in client UI).

**F-6 — Approval and gates are honour-system.** No script validates `.sps/plan.md` status, no gate is machine-checked,
and three explicit bypasses exist (`batch approve`, Tier-1 exemption, read-only carve-out).

**F-7 — This repository violates its own rules.** `./.sps/` exists but `AGENTS.md`/`GEMINI.md`/`CLAUDE.md` are absent
(breaking the `/sps` lock and audit item A5), `.sps/plan.md` is missing, `profile.md`/`handoff.md` are empty, and
5 orphan debug artifacts sit at root — contra `WORKSPACE-HYGIENE.md`.

**F-8 — Version drift is structurally invisible to CI.** `sps-cms/package.json` (1.4.0) vs `sps-cms/VERSION` (2.3.0),
plus `plugin.json` and `marketplace.json` both at 2.0.0. CI validates only `skills/sps/VERSION`.

**F-9 — Lint quality is shallow.** `lint-sps.sh` asserts string presence in Markdown. It proves the docs *say* the
right things, not that the system *does* them. A green lint is weak evidence.

**F-10 — The working copy is not a Git repository**, so no history, blame, or provenance could be verified, and
release/integrity claims resting on git are unverifiable here.

---

## 25. Explicitly NOT Done in This Phase

Per the read-only mandate, the following were **not** performed:

- No source, config, documentation, or dependency was modified.
- Nothing was installed, uninstalled, updated, renamed, deleted, or refactored.
- No skill, plugin, or MCP was installed. No agent or global machine configuration was changed.
- No Git configuration was changed. (The repository is not a Git repo in any case.)
- No memory file or project state file was created or edited.
- **No fix was applied to any finding** — including the hardcoded secret (F-3), which is reported, not patched.
- Existing `.sps/audit-report.md` was **not** overwritten; this report uses a new unique filename.

**Only one file was created:** `AUDIT-PHASE-01-BASELINE-FORENSIC.md` (this document).

---

## 26. Handoff to Reviewing Architect

**Verified working today:** install/uninstall/update machinery (bash syntax valid, mirrors in sync), lint suite
(passes), version-stamp consistency for the core skill, project-memory bootstrap, and the CMS-coupled section
delivery concept.

**Highest-confidence concerns to weigh first:**
1. `auth-helper.ts:8` hardcoded secret (F-3) — concrete, exploitable-if-deployed.
2. Absence of any dynamic skill discovery (F-2) — contradicts the stated target architecture.
3. Instruction-only enforcement of every gate (F-1, F-6).
4. Complete absence of SEO methodology and the no-emoji policy (F-5).
5. Repository self-violation and version drift (F-7, F-8).

**Deliberately not ranked as "must fix".** This phase establishes evidence only; prioritisation and remediation
design belong to the reviewing architect.

**Recommended next step:** validate or refute F-1 through F-4 against the actual target requirements before any
implementation planning begins. Several findings (F-4 in particular) depend on which third-party skills are
assumed present in the target environment — a question only the reviewer can settle.

---

*End of Phase 01 Baseline Forensic Audit. No remediation performed.*
