# Shahid Personal SkillSet — Product Brief (PRD-style)

**Document status:** Source-grounded draft; not yet validated as an authoritative product PRD by the product owner.  
**Prepared:** 2026-10-17 (Asia/Dhaka)  
**Product:** Shahid Personal SkillSet (`/sps`)  
**Product version stated in repository README:** 4.0.0

> This brief summarizes what the repository currently says the product is and does. It is not a promise that every listed capability has been independently tested on every supported host. Statements tagged **Open** need a product-owner decision or evidence.

## 1. Product purpose

Shahid Personal SkillSet is a portable, installable set of instructions and skills for skills-compatible coding agents. It guides an agent through building and improving software projects in deliberate steps, with project memory, planning, verification, and approval checkpoints. When a project uses a CMS, it requires the agent to connect the user-facing experience to the corresponding administrative editing controls.

The product is intended to make coding-agent work more consistent, reviewable, and honest about what has and has not been verified. It is not described as a standalone application or as a general-purpose chatbot.

## 2. Problem and intended outcome

### Problem addressed

Coding agents can lose project context between sessions, make changes before goals are clear, leave CMS editing controls behind the interface, or report completion without sufficient verification. SPS provides a repeatable workflow and domain skills to reduce those risks.

### Intended outcome

A user can install SPS into a compatible coding-agent environment, invoke `/sps` in a project, and receive a structured workflow that captures project context, plans work, implements bounded changes, verifies them, and pauses at required approval points.

This outcome describes the product concept. It does not mean this repository’s separate SPS2 remediation and release-readiness effort is complete; that effort is currently recorded as **in progress**, with P10/release readiness **NOT READY** in the completion dossier.

## 3. Users and use cases

### Intended users (inferred from repository documentation)

- Developers who use skills-compatible coding agents to build or maintain projects.
- Project owners who want a persistent record of decisions, plans, and handoffs across agent sessions.
- Teams or individuals building websites and applications that need coordinated UI, CMS, testing, SEO, backend, mobile, or deployment work.

These user groups are inferred from the README and skill documentation; official personas and market positioning are **Open**.

### Main jobs to be done

1. Start or continue a project with project-specific context and constraints available to the agent.
2. Audit an existing project against SPS practices before proposing remediation.
3. Plan and implement changes in bounded pieces with verification and approval checkpoints.
4. Keep CMS-backed content and controls aligned with the user-facing section.
5. Check SPS installation and host integration, or update/synchronize a project’s workflow.

## 4. Product concept and user workflow

### Product model

SPS is a repository-distributed toolkit made of agent instructions/skills, workflow references, shell and PowerShell scripts, templates, and installer/update/uninstaller tooling. It is not a hosted service or standalone end-user application in the materials reviewed. The user invokes it through a supported coding-agent host; the host performs project work using its available tools.

The repository describes this typical `/sps` workflow:

1. Discover the project goal, technology stack, CMS, authentication, mobile requirements, team roles, and deployment target.
2. Create or refresh `.sps/` project memory and applicable root instruction mirrors.
3. Write a plan and stop for user approval before code changes, according to the plan gate.
4. If a CMS is in use, establish the CMS foundation and build each section with its corresponding CMS controls.
5. Work section by section, verify the result, and pause at required approval boundaries.
6. Record handoff and project memory so a later session can continue with evidence.

The exact flow depends on the host agent and project. The capability matrix is the source for host-specific differences.

## 5. User-facing entry points

The README and skill documentation describe these commands or modes:

| Command | Documented purpose |
|---|---|
| `/sps` | Start or continue the normal build workflow |
| `/sps audit` | Audit/score an existing project against SPS rules |
| `/sps sync` | Address CMS debt in a project where the site exists but CMS controls are missing |
| `/sps cms-sync` / `/sps couple` | CMS/storefront synchronization or coupling modes named by the skill documentation |
| `/sps doctor` | Check installation, host, and skill health |
| `/sps release-lock` / `/sps unlock` | Release the project workflow lock, as documented by the skill |

The README’s quick command table only lists `/sps`, `/sps audit`, `/sps sync`, and `/sps doctor`; the additional modes above are described in skill documentation. Exact command availability can differ by installation and host; verify it with the installed skill and doctor tooling.

## 6. Capability scope

### Included according to repository documentation

- A master `/sps` orchestrator and plan-first workflow.
- Persistent project memory under `.sps/`, plus short root-level instruction mirrors where required.
- A curated skill stack covering design, CMS, frontend, testing, SEO/copy, deployment, backend, mobile, and research.
- CMS coupling guidance requiring editable content and admin controls to be delivered with the related user-facing section.
- A scored alignment audit, project bootstrap templates/memory, and handoff/mistake-tracking guidance.
- Audit, sync, doctor, and release-lock guidance/tools.
- Install, update, and uninstall flows for macOS/Linux and Windows PowerShell.
- Host capability documentation, including varying support levels and optional host-specific integrations.

This is a documented capability list, not a fresh verification of every installer path, third-party skill, integration, or host.

### Installation footprint and external dependencies

The installer documents a global install by default and accepts an agent selection. It synchronizes SPS skill files into supported agent skill directories, writes an install manifest and logs under the user’s `~/.sps` directory, and invokes external tooling such as `npx skills` to fetch skills from third-party repositories. When Claude Code is detected, the installer also attempts Claude marketplace/plugins and Context7 setup; when Python tooling is available, it attempts Graphify setup. Some optional skill additions can fail while the core mirrors still install successfully. Review the install log and doctor output rather than assuming every optional integration succeeded.

The updater can contact GitHub to check the remote version, fetch or clone the repository, and rerun the installer. The skill currently instructs session-start update checks and auto-application when an update is available. These operations have network access and may change the user’s global agent skill installation. Treat this as a material product behavior and validate it on the target host before relying on it.

### Outside the stated scope

- Generic chatbots without skills/workflow support.
- A guarantee of identical behavior across all coding agents or third-party tools.
- A claim that all generated project code is correct or secure without project-specific verification.

## 7. Product principles and requirements

The following requirements are transcribed or summarized from the repository’s SPS skill documentation:

- **Evidence honesty:** label uncertain claims and do not invent project facts or verification results.
- **Plan before implementation:** capture the plan and obtain required approval before code changes.
- **Persistent context:** maintain project memory and handoffs across sessions.
- **Bounded delivery:** implement in reviewable chunks and verify before claiming completion.
- **CMS completeness:** for CMS-enabled projects, deliver the user-facing section and its editable CMS controls together.
- **User control:** stop at required approval gates and honor project-specific constraints.
- **Quality and performance:** follow applicable design, accessibility, mobile, asset-budget, testing, and verification guidance.
- **Surgical workspace handling:** preserve unrelated work and avoid broad destructive cleanup.
- **Host-aware behavior:** disclose or accommodate capability differences between agent hosts.

The skill contains operational limits (for example, a stated initial-payload budget); projects must validate those limits against their own requirements and the applicable skill version.

## 8. Installation and lifecycle

The README presents a unified install for macOS/Linux and Windows PowerShell, a doctor check, update commands, and uninstall commands. The documented lifecycle is:

`install → check health → use/update → uninstall (optionally retain personal memory)`

The README also describes an update check in the orchestrator workflow. Whether unattended update behavior is appropriate for a particular user or organization is an **Open** product-policy question and should be decided explicitly; do not infer consent to change this policy from the documentation alone.

The root `LICENSE` identifies the repository as MIT-licensed. Third-party skills, plugins, and dependencies may have their own licenses and terms; the project materials reviewed here do not establish a consolidated license inventory for those components.

## 9. Compatibility and operating assumptions

The README calls Claude Code the strongest-supported host, lists Cursor and Codex as high support, and describes Antigravity/Gemini and several other agent families as medium or varying support. Generic chatbots are out of scope. Refer to `skills/sps/CAPABILITY-MATRIX.md` for current documented details.

**Assumption:** users have an installed coding-agent host capable of loading the relevant skill/instruction files and invoking slash commands. The repository does not promise that every host exposes identical tools or integrations.

### Trust and security boundary

SPS supplies workflow guidance and installation tooling; it cannot guarantee that an agent, host, external skill, plugin, or generated project code is safe. The README itself advises reviewing third-party skills before trusting them. Users should review the current installer, requested host integrations, and third-party skill sources before installation in sensitive environments. The product documentation does not define a full threat model or security support policy (**Open**).

## 10. Success measures and acceptance criteria

The repository does not define a formal product analytics or adoption metric. The following are proposed acceptance checks derived from documented behavior, not approved KPIs:

1. A supported installation path completes and the doctor reports actionable host/skill status.
2. The agent can discover and preserve project goals, constraints, and handoff context in `.sps/`.
3. A new implementation plan is presented before code changes when the plan gate applies.
4. CMS-enabled section work includes corresponding editable controls and evidence of connection.
5. The agent reports test/verification evidence accurately, including failures, skips, and host limitations.
6. Uninstall behavior follows the selected memory-retention option and does not remove unrelated project data.
7. Host capability claims match the maintained capability matrix and reproducible checks.
8. Install/update behavior, global filesystem changes, and optional integration outcomes are clearly disclosed and verifiable.

Formal thresholds, supported-version policy, and release criteria are **Open**.

## 11. Repository map (orientation)

- `README.md` — user-facing overview, quick start, commands, compatibility, and safety notes.
- `skills/sps/` — orchestrator, method card, gates, workflow rules, and host capability documentation.
- `skills/` — included skill packages and their supporting resources.
- `scripts/` — installation support, health checks, lint/smoke/bootstrap, and related tooling.
- `get-sps.sh`, `get-sps.ps1`, uninstall scripts — documented entry points for installation lifecycle.
- `tests/` and CI configuration — automated checks; their current coverage and gate status must be verified from current evidence.
- `SPS2-PROJECT-COMPLETION-RECORD/` — this remediation effort’s goal, evidence, backlog, workflow, and approval boundaries; it is not itself the product specification.

This map is a high-level orientation, not an exhaustive architecture inventory.

## 12. Documentation consistency and known conflict

The current repository documents two different install models:

- The root `README.md`, `install.sh`, `install.ps1`, and 4.0.0 changelog describe one unified install with no minimal/full profiles; installer manifests use `PROFILE=all`.
- `CATALOG.md` still lists `core`, `full`, and `minimal` profiles, and describes Trail of Bits as a full-profile option.

The available 4.0.0 installer/changelog materials point to the unified model as the intended current behavior, but the catalog conflict remains unresolved documentation debt. This brief does not treat the product-owner’s intended policy as settled. Align the catalog and any related references, then verify installer behavior, before using install profiles as a product requirement.

## 13. Open product questions

These details were not established by the repository materials reviewed for this draft:

- Who is the primary customer/user, and which use case has priority?
- Which hosts and versions are officially supported, and what support levels mean in practice?
- What is the contribution and third-party skill review policy, and how are upstream skill versions pinned or reviewed?
- Should session-start update checks apply updates automatically, ask first, or be configurable? What exact network requests and global changes should users expect?
- What is the formal release acceptance bar (test matrix, security review, supported OS/host matrix)?
- What are the privacy/data-handling commitments, if any? Do any components collect or transmit usage data beyond update/install requests?
- Where should users report bugs and receive support?
- Which success measures should be tracked, and should any telemetry exist?
- Who can ratify product policy and governance records for this project?
- Which install model is authoritative: unified bundle or selectable profiles? Resolve the `README`/installer versus `CATALOG.md` discrepancy.

Do not silently fill these gaps with assumptions. Record decisions in the appropriate authoritative project record when the owner establishes them.

## 14. Relationship to the SPS2 completion effort

This brief describes the **SPS product** based on repository documentation. The SPS2 completion dossier tracks a **separate engineering/remediation effort** to verify and address repository findings and establish honest release readiness. Completing this brief does not complete that backlog, approve governance changes, or make P10/release gates ready.

See [the completion dossier](README.md), especially its current-state evidence, finite backlog, and decision boundaries.

## Source basis

- `README.md` in the repository root.
- `skills/sps/SKILL.md` and `skills/sps/METHOD-CARD.md`.
- `skills/sps/CAPABILITY-MATRIX.md` for host-specific claims.
- `skills/sps/PLAN-GATE.md`, `skills/sps/SECTION-DOD.md`, and `skills/sps/ASSET-BUDGET.md` for workflow and quality requirements.
- `CHANGELOG.md`, `CATALOG.md`, `LICENSE`, `install.sh`, `install.ps1`, and update/doctor scripts for version, licensing, packaging, and lifecycle behavior.
- Other linked workflow documents where requirements are described.

Claims in this brief should be rechecked against those files whenever the product documentation changes.
