# SPS2 PRD-STYLE PRODUCT BRIEF — INDEPENDENT REVIEW (CLAUDE)

Report time: 2026-10-17T17:35+06
Reviewer: Claude (independent, read-only)
Review subject: `SPS2-PROJECT-COMPLETION-RECORD/00-PRODUCT-BRIEF-PRD-STYLE.md` (209 lines, draft status line at :3)
Verification method: four parallel read-only verification subagents (installer/lifecycle, skill-doc commands/workflow/principles, catalog/changelog/license/repo-map, SPS2-separation) plus reviewer's direct reads of README.md, CATALOG.md, CHANGELOG.md (head), and the brief itself.
Live state at review: branch `build/roadmap-p3-completion`, HEAD `c49f3852e1c31d0136269c80fe58201b059af3ec`.

## Verdict: **NEEDS REVISION**

The brief is substantially accurate — every verified claim about the product model, workflow, commands, principles, host support, SPS2 separation, and the README-vs-CATALOG profile conflict checked out with exact citations. But it has **two material omissions** (trust-boundary-relevant installer behavior; a nonexistent path in the repo map), **one internal tension it under-reports** (CHANGELOG 4.0.0's own profile vocabulary), and **one Windows behavioral asymmetry it states too broadly**. All are fixable with bounded wording changes; none invalidates the brief's overall structure or conclusions.

## 1. Claims verified TRUE (with citations)

### 1.1 Version, license, host support
- Version 4.0.0: `README.md:3`, `CHANGELOG.md:3`, `skills/sps/VERSION:1`; CI enforces consistency (`.github/workflows/sps-ci.yml:45-52`).
- MIT: `LICENSE:1,3` — "MIT License", "Copyright (c) 2026 SHAHID8142".
- Host table: `README.md:134-144` — Claude Code Best; Cursor/Codex High; Antigravity/Gemini Medium; Windsurf/Copilot/OpenCode Medium; other skills-compatible Varies; generic chatbots "No | Out of scope". Corroborated by `skills/sps/CAPABILITY-MATRIX.md:14-22`. (README uses "Best"; the matrix uses "Strong" for Claude Code — same intent, different wording; minor.)
- Antigravity boot-refusal: `README.md:130`, `skills/sps/METHOD-CARD.md:24-27`, `skills/sps/hosts/antigravity.md:12-27`.

### 1.2 Commands
All eight documented commands are covered by the brief: `/sps` (README.md:82; METHOD-CARD.md:42), `/sps audit` (README.md:83; SKILL.md:55), `/sps sync` (README.md:84; SYNC.md:1,3), `/sps cms-sync` / `/sps couple` (SKILL.md:5-6,58; SYNC.md:3 — aliases, documented only in skill docs, exactly as the brief says), `/sps doctor` (README.md:85; SKILL.md:61), `/sps release-lock` / `/sps command` — `/sps release-lock`/`/sps unlock` (SKILL.md:67; APPROVAL-PACKETS.md:99; SKILL.md frontmatter :5-6). README's table has exactly four rows (README.md:80-85) — the brief's framing is correct.
- No command in the brief is undocumented; no documented command is omitted.

### 1.3 Workflow and principles
- Discovery → memory/mirrors → plan gate ("zero code before user approval", SKILL.md:30, PLAN-GATE.md:1-2) → CMS foundation first (CMS-COUPLING.md "Foundation before first section") → per-section loop with round-trip proof (CMS-COUPLING.md items 4-7) → approval pause per section (CMS-COUPLING.md item 9; README.md:108) → handoff/memory (SKILL.md:27; PLAN-GATE.md "Memory").
- All nine principles the brief lists exist in skill docs: evidence honesty (SKILL.md:28; ANTI-HALLUCINATION.md:7,24-26), plan-first (PLAN-GATE.md:1-2), persistent context (CONTEXT-EFFICIENCY.md rule 5), bounded delivery (SKILL.md:30; SECTION-DOD.md:5), CMS completeness (CMS-COUPLING.md "Storefront-only delivery is forbidden"), user control (APPROVAL-PACKETS.md:85-89), quality/performance (SKILL.md:32,38,41; SECTION-DOD.md items 7-8; ASSET-BUDGET.md:10-16), surgical workspace handling (SKILL.md:39; WORKSPACE-HYGIENE.md), host-aware behavior (SKILL.md:16,82; hosts/*.md).
- Initial-payload budget is real and precise: **1.5 MB** max initial payload (SKILL.md:38); per-asset budgets in `skills/sps/ASSET-BUDGET.md:10-16` (hero ≤ 200 KB, inline image ≤ 120 KB, icons ≤ 20 KB, fonts ≤ 2 families/2 weights).

### 1.4 Lifecycle
- Global install default + agent selection: `install.sh:23,83` (`AGENTS="*"`, `--agents`), `install.ps1:2`; get-sps passes options through (`get-sps.sh:85`).
- Sync into 17 (bash) / 11 (PowerShell) agent skill dirs: `install.sh:32-50`, `install.ps1:35-47`; manifest `~/.sps/install-manifest.env` (install.sh:26) and log (install.sh:56).
- `npx skills add ... -g -y` for ~27 third-party skills: install.sh:338-368; install.ps1:231-262.
- Claude marketplace/plugins + Context7 when `claude` present: install.sh:370-394, 274; Graphify via `uv`/`pip`: install.sh:396-404.
- Updater: `scripts/check-update.sh:16,185` (raw VERSION fetch), `scripts/sps-update.sh:109-134` (fetch/clone + `bash ./install.sh --yes`), PowerShell twins.
- Session-start auto-update: `skills/sps/SKILL.md:42,77` — run check-update (24h cache), auto-apply via `sps-update.sh --yes`.
- `PROFILE=all` in manifests: install.sh:234, install.ps1:154.
- Doctor: `scripts/sps-doctor.sh:2-4,56-100` + `--fix` (lines 12-14, 127-142).
- Uninstall `--keep-personal` / `-KeepPersonal`: uninstall.sh:27-30,216-223; uninstall.ps1:11,188-191. Both uninstall scripts exist at repo root.

### 1.5 The documented conflict (§12) is real
- Unified side: `README.md:56-59` ("No profiles, no minimal/full choice"), `CHANGELOG.md:3-7` (unified installer, `PROFILE=all`), installers have no profile flag (install.sh:62-79 usage; CI fails if `--profile` reappears, sps-ci.yml:61-66).
- Profiles side: `CATALOG.md:17-21` (core/full/minimal), `CATALOG.md:33` ("Trail of Bits (full profile)").
- Bonus check the brief's §12 list did not need to include but I verified: `skills/sps/INSTALL-PROFILES.md:1-5` has been rewritten to the unified model ("one installer and one install… No profiles") despite its legacy filename, and `PROFILE-SCOPING.md` concerns `.sps/profile.md` memory scoping, not install profiles. So the conflict is confined to CATALOG.md (plus the CHANGELOG internal tension below) — the brief's §12 is complete on the skill-doc side.

### 1.6 SPS2 separation (§14) and status
- "In progress" + "NOT READY": `SPS2-PROJECT-COMPLETION-RECORD/README.md:6,25`; `02-CURRENT-STATE-AND-EVIDENCE.md:4,29-30`; `05-DECISIONS-AND-APPROVAL-BOUNDARIES.md:74`. Backlog uses task-level vocabulary (TODO/IN_PROGRESS/…) — nuance, not inaccuracy.
- The brief is correctly recorded as unapproved: dossier README.md:38 ("Draft; not product-owner approved").
- Ratification open question (§13) is consistent with `05-DECISIONS-AND-APPROVAL-BOUNDARIES.md:5,44-46,55-65` (delegation ≠ ratification; DEC-7301/2/3 remain UNAPPROVED).
- No product/SPS2 conflation found in §1-13; §14 is dedicated to the separation.

## 2. Material omissions / inaccuracies requiring revision

### R-1 (material omission, trust boundary): installer trust-relevant behavior not disclosed
The brief's §6 describes install behavior but omits three behaviors a reader must know to evaluate the product's trust boundary:
- **SSH host-key checking disabled**: `install.sh:15` and `install.ps1:9` — `export GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=no"`, plus `GIT_CLONE_PROTECTION_ACTIVE=false` (install.sh:16).
- **Auto-yes npm**: `install.sh:17` / `install.ps1:10` — `export npm_config_yes=true`, combined with `-y` on every `npx skills add` (install.sh:338-368): ~27 third-party skills install with no per-skill consent.
- **Destructive mirror refresh**: `rm -rf "$dest_root/sps"` / `sps-cms` before every copy (install.sh:255,262; install.ps1:176,181 Remove-Item -Recurse -Force) across 17 user-level skill dirs — silently overwrites local customizations.
Also omitted but favorable: `sps-update.sh:63-75` refuses to update a dirty source worktree; `check-update.sh:57-65,197-201` validates remote VERSION as strict semver.
**Proposed wording** (append to §6 "Installation footprint" paragraph, after the "Review the install log…" sentence):
> "Specific installer behaviors relevant to trust review: the installers set `GIT_SSH_COMMAND` with `-oStrictHostKeyChecking=no` (install.sh:15, install.ps1:9) and `npm_config_yes=true` (install.sh:17, install.ps1:10), so git operations skip SSH host-key verification and ~27 third-party skills are fetched via `npx skills add … -y` without per-skill consent. Each install refreshes the managed `sps`/`sps-cms` skill directories with `rm -rf` (install.sh:255,262), overwriting local customizations in those paths. The updaters refuse to run against a dirty source worktree (scripts/sps-update.sh:63-75) and validate the remote VERSION string as strict semver (scripts/check-update.sh:57-65)."

### R-2 (inaccuracy, over-broad claim): optional-failure tolerance is bash-only
Brief §6: "Some optional skill additions can fail while the core mirrors still install successfully." True for bash (install.sh:181-192 `step()` continues; install.sh:421-428 exits 0 when Claude+Cursor mirrors healthy) but **false for PowerShell**: `install.ps1:345-347` exits 1 if any optional step failed.
**Proposed wording** (replace the sentence in §6):
> "On macOS/Linux, some optional skill additions can fail while the core mirrors still install successfully (install.sh:181-192, 421-428). On Windows PowerShell, the installer still continues past optional failures but exits non-zero if any optional step failed (install.ps1:345-347) — doctor output is the reliable status signal on both platforms."

### R-3 (material omission): `tests/` does not exist
Brief §11 repo map lists "`tests/` and CI configuration". There is **no root `tests/` directory**; loose root-level scripts `test_claude.sh`, `test_timeout.sh`, `test_uiux.sh` exist instead, and CI lives at `.github/workflows/sps-ci.yml` (Lint+smoke / Version sanity / PowerShell syntax jobs). The SPS2 test suite lives under `sps2/tests/` and `domain/seo/tests/` (remediation-side, not product).
**Proposed wording** (replace the §11 bullet):
> "- Root-level smoke/lint scripts (`test_claude.sh`, `test_timeout.sh`, `test_uiux.sh`, `scripts/lint-sps.sh`, `scripts/smoke-sps.sh`) and CI configuration at `.github/workflows/sps-ci.yml` — automated checks; their current coverage and gate status must be verified from current evidence. (There is no root `tests/` directory.)"

### R-4 (under-reported tension): CHANGELOG 4.0.0 retains profile vocabulary
§12 correctly identifies the CATALOG conflict but misses that the **CHANGELOG 4.0.0 entry itself** still says "**Core profile +5 skills**" / "**Full profile +8 skills**" (`CHANGELOG.md:12-13`) and "preserves install profile/agents from manifest" (:15) — internal tension inside the very entry announcing profile removal.
**Proposed wording** (add to §12 second bullet):
> "- The 4.0.0 changelog entry itself retains profile vocabulary: `CHANGELOG.md:12-13` bullets are labeled 'Core profile +5 skills' / 'Full profile +8 skills' and :15 says the updater 'preserves install profile/agents from manifest', despite the same entry announcing profile removal (`CHANGELOG.md:3-7`)."

### R-5 (minor): §14 relative link ambiguity
"[the completion dossier](README.md)" resolves correctly inside the dossier folder but can be misread as the root product README, which the brief cites heavily elsewhere.
**Proposed wording**: change link text/target to `[the completion dossier](./README.md)` with a parenthetical: "(the dossier's own index, `SPS2-PROJECT-COMPLETION-RECORD/README.md` — not the product README)".

### R-6 (minor, optional): uninstall default is destructive
§8/§10 mention `--keep-personal` but not that **default uninstall deletes `~/.sps` including personal memory** (uninstall.sh:5,216-218; interactive prompt requires typing `yes` unless `--yes`). One clause would close this.
**Proposed wording** (§8 after "uninstall commands"):
> "By default uninstall removes `~/.sps` including personal memory; `--keep-personal` / `-KeepPersonal` retains it (uninstall.sh:216-223, uninstall.ps1:188-191)."

## 3. Items verified but NOT requiring revision (recorded for completeness)
- install.ps1's 11 sync roots vs install.sh's 17 — parity gap, not a brief inaccuracy (brief doesn't claim parity).
- README "Best" vs matrix "Strong" for Claude Code — cosmetic wording difference.
- `PROFILE=all` claim, doctor `--fix`, get-sps pass-through, manifest/log paths — all confirmed.
- Dossier "in progress"/"NOT READY" wording — accurate at project level.
- No approval or readiness claim exists anywhere for the brief; the brief's own status line is accurate.

## 4. Constraints observed
Read-only review: no PRD/source/catalog/CI/baseline/governance/approval/`.sps/`/P10/release-artifact edits; nothing staged, committed, pushed, deployed, published, merged, or released; no tests run (per instruction). The brief is NOT approved by this review, and P10/release readiness remains NOT READY. DEC-7301/7302/7303 remain unapproved; the disputed Round 26 record untouched.
