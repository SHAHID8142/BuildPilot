# Skill Governance

Prefer a small number of strong skills over a noisy pile.

## Status buckets

- **Primary default**
- **Secondary enhancer**
- **Conditional specialist**
- **Host-specific**
- **Deprecated by default**

## Recommended defaults

| Domain | Primary | Secondary | Notes |
|---|---|---|---|
| Orchestration | `/sps` | — | Never dual-orchestrate with Superpowers by default |
| UI taste | `design-taste-frontend` (taste-skill v2) | `hallmark` build → `impeccable` critique | DESIGN-GATE always applies; style variants (gpt-taste, high-end-visual-design, minimalist-ui, brutalist-ui) only on explicit direction |
| UI review | `web-design-guidelines` | host a11y | |
| React | `vercel-react-best-practices` | `vercel-composition-patterns` | |
| Testing | `webapp-testing` | `agent-browser` live checks | |
| SEO | `ai-seo` | SPS `seo` | |
| Content | `copywriting` | fact-check | SPS drafts, user edits |
| Surgical behavior | Karpathy guidelines | CONTEXT-EFFICIENCY | |
| Hallucination gate | `verification-before-completion` | fact-check | single skill only |
| Security | Trail of Bits skills | host review | full profile / when available |
| CMS | **`sps-cms` skill** | SPS CMS-COUPLING docs | mandatory; no market CMS skill replaces coupling law |
| Logos | `theSVG` | official | |

## Conflict policy

Do not automatically combine multiple taste operators, scroll systems, 3D
engines, or orchestrators. See SKILL-ROUTER.md.

Taste family policy: `design-taste-frontend` is the only default taste operator.
`gpt-taste`, `high-end-visual-design`, `minimalist-ui`, `industrial-brutalist-ui`,
`image-to-code`, and `redesign-existing-projects` are conditional specialists —
loaded only when the user explicitly picks that direction (e.g. "make it
brutalist", "redesign this legacy site", "code this Figma export").
