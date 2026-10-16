# Shahid Personal SkillSet - Catalog

Curated for cross-agent robustness. `/sps` routes specialists; it does not stack
every skill at once.

## How to use

```text
/sps [your request]
/sps audit
/sps sync
/sps doctor
```

Portable across skills-compatible coding agents. Not identical everywhere.

## Install profiles

- `core` — recommended
- `full` — core + host extras
- `minimal` — `/sps` only

## Domain router (summary)

| Domain | Primary | Secondary |
|---|---|---|
| Orchestration | `/sps` | — |
| Anti-slop UI | `hallmark` | `impeccable` |
| UI review | `web-design-guidelines` | a11y host skill |
| React | `vercel-react-best-practices` | `vercel-composition-patterns` |
| Testing | `webapp-testing` | Playwright |
| Surgical/token | `karpathy-guidelines` (core) | SPS CONTEXT-EFFICIENCY |
| Security | Trail of Bits (full profile) | host security review |
| CMS | SPS CMS-COUPLING + `/sps sync` | — |
| Logos | `theSVG` | official assets |

See `skills/sps/SKILL-ROUTER.md` for install-or-instruct protocol and conflict bans.
