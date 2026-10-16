# SPS Method Card (read first)

One-page law card. Host adapters and agents must obey this even when other
host defaults conflict.

## Portability claim

Portable workflow across **skills-compatible coding agents**.
Not identical behavior everywhere. Not for generic chatbots.

## Always

1. `/sps` is the orchestrator when `./.sps/` exists
2. Write memory to `./.sps/` every session and after every approval
3. Discovery before build; research before design
4. **Plan gate before code:** write `./.sps/plan.md`, get approval, zero code before
5. Section-by-section with todos + approval packets
6. CMS-enabled projects: storefront + CMS for the same section together
7. No ship without Section DoD + cleanup gate
8. Surgical context: grep/offset reads; no whole-file by default
9. Honest host capabilities; never invent tools/results
10. Check for SPS updates on session start (auto-apply if available)

## Antigravity / Gemini

If Host is Antigravity/Gemini and `GEMINI.md`/`AGENTS.md` locks are missing:
**boot refusal** — fix mirrors before coding.

## Never

1. Storefront-only "done" when CMS is enabled
2. Eyebrows on public marketing UI (global default)
3. Thin section divider lines / fake separators
4. Duplicate asset copies that clutter the working directory
5. Stack conflicting taste skills
6. Skip `/sps` because the host has another preferred workflow
7. Write code before the plan gate approves `./.sps/plan.md`
8. Skip the manual user check loop after a section ships

## Modes

- `/sps` — build (default)
- `/sps audit` — scored alignment audit
- `/sps sync` — pay CMS/storefront debt on existing projects
- `/sps doctor` — install/host/skill health (script + in-session checks)

## Before coding a chunk

Plan approved → roles → content inventory → todos → approval packet → skills
from router → implement UI+CMS (if CMS) → content + SEO → verify round-trip →
Lighthouse → cleanup → user manual check → fix feedback → next section.
