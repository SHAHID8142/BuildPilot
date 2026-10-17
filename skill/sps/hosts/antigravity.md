# Antigravity / Gemini CLI host adapter for `/sps`

Canonical workflow: `../SKILL.md` + `../METHOD-CARD.md`.

## Why this host fails often

Antigravity may prefer its own scaffolding and skip skills unless project root
mirrors and explicit `/sps` invocation are present. Antigravity (IDE and Desktop
app) does NOT reliably auto-load agent skills — the root-mirror locks and the
Karpathy behavioral block in `GEMINI.md` are the enforcement layer, not skills.

## Boot refusal (hard)

Before writing any project code, verify ALL of:

1. `./.sps/agent.md` exists with Host + VERSION
2. `./.sps/profile.md` and `./.sps/handoff.md` exist
3. `./.sps/plan.md` exists and is `approved` for build work (PLAN-GATE)
4. `GEMINI.md` contains the `/sps lock` block
5. `AGENTS.md` contains the `/sps lock` block
6. `GEMINI.md` contains the Karpathy behavioral block (Think Before Coding,
   Simplicity, Surgical Changes, Goal-Driven Execution)
7. User invoked `/sps` (or `/sps audit` / `/sps sync` / `/sps doctor`)
   OR handoff already shows an active approved chunk

If any check fails: **stop coding**. Create/fix mirrors from
[PROJECT-ROOT-MIRRORS.md](../PROJECT-ROOT-MIRRORS.md), bootstrap `.sps/`,
tell the user to run `/sps`, then continue.

## Required behavior

1. On session boot, read METHOD-CARD + `./.sps/*` before any code.
2. Prefer `~/.gemini/antigravity/skills/sps` (and CLI twin) for the skill body.
3. Do **not** invent a parallel "Antigravity-native" build process.
4. Use plain-markdown discovery and approval packets.
5. CMS coupling, design gate, hygiene, context-efficiency, skill router still apply.
6. If skills are missing, give exact install commands:
   `curl -fsSL https://raw.githubusercontent.com/SHAHID8142/Shahid-Personal-SkillSet/main/get-sps.sh | bash -s -- --yes`
7. Write `./.sps/agent.md` with Host: Antigravity / Gemini CLI and VERSION every session.
8. After every design pivot, update `./.sps/design-system.md` + `changelog-sps.md`.
9. On session start, run `scripts/check-update.sh`; auto-apply updates with
   `scripts/sps-update.sh --yes` and report what changed.

## Forbidden

- Skipping discovery because the host chat UI feels faster
- Storefront-only sections on CMS projects
- Claiming verification that was not run
- Replacing `/sps` with Gemini/Antigravity default scaffolding templates
- Coding when GEMINI.md / AGENTS.md locks are missing
- Coding a build section before `plan.md` is approved
- Stacking multiple taste skills in one session (taste-skill v2 is the only default)
