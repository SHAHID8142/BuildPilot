# Skill Router

`/sps` remains the only orchestrator. Do **not** install Superpowers (or similar)
as a second orchestrator by default.

## Dynamic selection (research-before-route)

The map below is the OFFLINE DEFAULT, not a lock. Per [DYNAMIC-SKILLS.md](DYNAMIC-SKILLS.md):
before a significant chunk, run a bounded ecosystem research pass
(`bash scripts/skill-search.sh <domain>`, GitHub, skills.sh) — if a better-maintained
or newer skill exists, propose the swap in the section packet and auto-update the
installed skill (`npx skills add <owner>/<repo> --skill <name> -g -y`). Bundled SPS
skills update via `scripts/sps-update.sh --yes`. Read any new skill's SKILL.md before
first use; conflict bans below still apply regardless of origin.

## Protocol (every chunk)

1. Detect job domains (UI, review, React, CMS, security, test, backend, …)
2. Pick **one primary** skill per domain from the table below
3. Optional **one secondary** if it adds distinct value
4. If a required skill is missing:
   - **Tool Consent gate first** ([TOOL-CONSENT.md](TOOL-CONSENT.md)): state what
     skill is missing, why the chunk needs it, and what installation involves,
     then get the user's explicit consent BEFORE installing. Never install
     silently; never run the installer in the same turn as the request.
   - After consent, install with the host's supported method (`npx skills`,
     plugin marketplace, copy into skills dir, or this repo's installer) and
     record it in `.sps/installs.md`.
   - If the user declines or install fails, stop and give the user exact manual
     install steps; use the table's Fallback column meanwhile and say so.
4b. **User-action chunks** (anything requiring the user to act on an external
    platform — API keys, DNS, OAuth, dashboard settings) follow the
    step-by-step law ([USER-GUIDANCE.md](USER-GUIDANCE.md)): one step at a
    time, wait for confirmation, never ask for full secrets in chat.
5. Invoke only the selected skills
6. If unavailable, use SPS fallback docs + expert persona and say so

## Default map (portable core)

| Domain | Primary | Secondary | Fallback if missing |
|---|---|---|---|
| Anti-slop / taste | `design-taste-frontend` (taste-skill v2) | `hallmark` (build) → `impeccable` (critique/polish) | DESIGN-GATE.md |
| UI review / a11y | `web-design-guidelines` | host a11y skill | DESIGN-GATE + manual a11y list |
| React quality | `vercel-react-best-practices` | `vercel-composition-patterns` | stack best practices in repo |
| Testing | `webapp-testing` | Playwright / `agent-browser` for live checks | VERIFICATION-RECIPES.md |
| Lighthouse / live verify | `agent-browser` | — | manual Lighthouse run |
| SEO | **`sps-seo` (bundled, synced by installer)** | `ai-seo` (fallback) | SEO checklist in SECTION-DOD |
| Content / copy | `copywriting` (SPS drafts, user edits) | `fact-check` | copy in content-model.md |
| Mobile app (RN) | `vercel-react-native-skills` | `sleek-design-mobile-apps` | — |
| Backend / DB | `supabase` + `prisma-*` (when stack matches) | vendor docs | stack best practices |
| Deploy | `deploy-to-vercel` (when Vercel target) | — | deploy steps in plan.md |
| Discovery | `grill-me` | SPS discovery questions | PROFILE-SCOPING.md |
| Surgical behavior | `karpathy-guidelines` | — | CONTEXT-EFFICIENCY.md |
| Hallucination gate | `verification-before-completion` | `fact-check` | ANTI-HALLUCINATION.md |
| Token efficiency | `caveman` (opt-in lite) | `context-mode` (Claude Code only) | CONTEXT-EFFICIENCY.md + CONTEXT-BUDGET.md |
| Security | Trail of Bits `differential-review` + `static-analysis` (Claude) | host security review | security checks in SECTION-DOD |
| CMS engine | **`sps-cms` (bundled, synced by installer) — mandatory** | — | (required; not optional) |
| Logos | `theSVG` | official brand source | LOGO-SOURCES.md |
| Docs / library APIs | Context7 MCP when available | — | official docs fetch |

## Token-consumption controls (always on)

1. **Context budget on `.sps/`** ([CONTEXT-BUDGET.md](CONTEXT-BUDGET.md)) —
   biggest single saver: a resuming agent reads `handoff.md` (≤150 lines),
   not an unbounded ledger. Doctor enforces.
2. **Narrow reads** (CONTEXT-EFFICIENCY.md): grep + line-offset reads, cite
   `file:line`, filter tool output (`| tail`/`| grep`) before it enters the
   conversation.
3. **MCP servers worth running** (install only via the Tool Consent gate):
   - **Context7** — library docs pulled on demand instead of reading vendored
     docs or guessing (already wired by the installer when claude CLI exists).
   - **Serena** (`uvx --from git+https://github.com/oraios/serena serena`)
     — symbol-level code retrieval; returns the function, not the file.
     Recommended for repos >50k lines.
   - A **git MCP** (e.g. `@modelcontextprotocol/server-git`) when the agent
     makes many small git queries — avoids repeated `git log/show` output
     dumps. Skip if bash usage is already disciplined.
4. **Never** load a full specialist skill for a one-line change in its
   domain; use the fallback column instead.

## Conflict ban

Do not auto-combine:
- hallmark + design-taste-frontend + Anthropic frontend-design + ui-ux-pro-max
- multiple scroll/motion systems
- multiple testing frameworks for the same step
- Superpowers workflow as a parallel orchestrator
- gpt-taste / high-end-visual-design / minimalist-ui / industrial-brutalist-ui
  as default taste (style variants load ONLY on explicit user direction)
- `verification-before-completion` + other superpowers skills (single skill only)

## Full-profile enhancers

Claude-only or heavy tools (ui-ux-pro-max, engineering-skills, Trail of Bits full
suite, Firecrawl, Caveman, Handoff, context-mode) stay optional at runtime.
Prefer them only when the host supports them and the chunk needs them.


## Install commands (ensure protocol)

Every skill below is part of the single unified install. Commands shown are for
manual repair when a skill is missing.

Taste-skill v2 — install ONLY the taste skill, not the other 11 repo variants:
```bash
npx skills add Leonxlnx/taste-skill --skill design-taste-frontend -g -y
```

sps-cms (mandatory CMS engine — bundled in this repo, synced by installer):
```bash
npx skills add SHAHID8142/Shahid-Personal-SkillSet --skill sps-cms -g -y
```

sps-seo (technical SEO standard — bundled in this repo, synced by installer):
```bash
npx skills add SHAHID8142/Shahid-Personal-SkillSet --skill sps-seo -g -y
```

Karpathy:
```bash
npx skills add https://github.com/forrestchang/andrej-karpathy-skills --skill karpathy-guidelines -g -y
```

Verification gate (single skill only, never the full superpowers repo):
```bash
npx skills add https://github.com/obra/superpowers --skill verification-before-completion -g -y
```

Live verification / Lighthouse:
```bash
npx skills add https://github.com/vercel-labs/agent-browser -g -y
```

SEO + copy:
```bash
npx skills add https://github.com/coreyhaines31/marketingskills --skill ai-seo -g -y
npx skills add https://github.com/coreyhaines31/marketingskills --skill copywriting -g -y
```

Deploy (when Vercel target):
```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill deploy-to-vercel -g -y
```

Discovery / token efficiency:
```bash
npx skills add https://github.com/mattpocock/skills --skill grill-me -g -y
npx skills add https://github.com/mattpocock/skills --skill caveman -g -y
```

Trail of Bits (full / Claude):
```bash
claude plugin marketplace add trailofbits/skills
claude plugin install differential-review@trailofbits --scope user
claude plugin install static-analysis@trailofbits --scope user
claude plugin install ask-questions-if-underspecified@trailofbits --scope user
claude plugin install insecure-defaults@trailofbits --scope user
```
