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

## Install model

One unified install — no `core`/`full`/`minimal` profiles (README and both
installers are authoritative; installer manifests use `PROFILE=all`). Every
documented skill is installed; `/sps` routes specialists per task.

Historical note: this catalog previously described `core`/`full`/`minimal`
profiles; that vocabulary is retired as of 4.0.0 (see CHANGELOG.md).

## Domain router (summary)

| Domain | Primary | Secondary |
|---|---|---|
| Orchestration | `/sps` | — |
| Anti-slop UI | `hallmark` | `impeccable` |
| UI review | `web-design-guidelines` | a11y host skill |
| React | `vercel-react-best-practices` | `vercel-composition-patterns` |
| Testing | `webapp-testing` | Playwright |
| Surgical/token | `karpathy-guidelines` | SPS CONTEXT-EFFICIENCY |
| Security | Trail of Bits | host security review |
| CMS | SPS CMS-COUPLING + `/sps sync` | — |
| Logos | `theSVG` | official assets |

See `skills/sps/SKILL-ROUTER.md` for install-or-instruct protocol and conflict bans.
