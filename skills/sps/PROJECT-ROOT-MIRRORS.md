# Project Root Mirrors

Some hosts ignore skills unless project root instruction files exist
(especially Antigravity / Gemini). When bootstrapping `/sps` in a project,
create or update short mirrors that point to `./.sps/` and `/sps` laws.

## Required mirrors (create if missing; do not overwrite rich existing docs blindly)

Append a clear SPS lock block if the file already exists and is project-owned:

- `AGENTS.md` — universal agents
- `GEMINI.md` — Antigravity / Gemini CLI
- `CLAUDE.md` — Claude Code

## Lock block (English)

```markdown
## /sps lock
This project uses `/sps` as the master workflow.
Read `./.sps/profile.md`, `./.sps/handoff.md`, and the SPS Method Card before
building. Do not replace `/sps` with a host-default scaffolding workflow.
CMS-enabled sections must ship storefront + CMS controls together.
```

## Also

- Keep detailed rules in `./.sps/` (source of truth)
- Host root files stay short and point inward


## Antigravity-specific `GEMINI.md` (preferred full block)

When creating `GEMINI.md` on Antigravity hosts, prefer this fuller block:

```markdown
## /sps lock (required)

This project is under `/sps` orchestration. Antigravity must NOT use a host-default
scaffold workflow instead of `/sps`.

Before any code:
1. Read `./.sps/profile.md` and `./.sps/handoff.md`
2. Read the SPS Method Card from the installed `sps` skill (`METHOD-CARD.md`)
3. Follow CMS-coupled section delivery when CMS is enabled
4. Stop for approval after each section Definition of Done

Commands: `/sps` · `/sps audit` · `/sps sync` · `/sps doctor`
```
