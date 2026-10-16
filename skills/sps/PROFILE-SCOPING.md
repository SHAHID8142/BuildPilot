# Profile Scoping

The entire `/sps` memory model depends on strict scoping and always-write
discipline.

## Priority order

1. Session-only instruction
2. Project profile: `./.sps/profile.md`
3. Personal defaults: `~/.sps/personal-defaults.md`

Project rules always beat global defaults.

## Required project memory files

Every `/sps` project must keep these files current:

| File | Purpose |
|---|---|
| `./.sps/profile.md` | Project-only rules, stack, mobile policy, `/sps` lock |
| `./.sps/handoff.md` | Phase, approvals, verification evidence, next steps |
| `./.sps/mistakes.md` | Project-local mistakes only |
| `./.sps/agent.md` | Active host identity, capabilities, version stamp, `/sps` lock |
| `./.sps/audit-report.md` | Latest scored SPS alignment audit report |

Bootstrap from `skills/sps/templates/` or run:

```bash
bash scripts/bootstrap-sps.sh /path/to/project
```

## Always-write rules

Write or update memory:

1. at session boot
2. after discovery answers are settled
3. after an options recommendation is approved
4. after every approved section / chunk
5. after verification / handoff

Do not leave durable decisions only in chat.

## `/sps` lock

Once `./.sps/` exists for a project:

- `/sps` is required for build, design, implement, fix, refactor, test, and
  deploy work in that project
- specialist skills may assist, but `/sps` remains the orchestrator
- record the lock in both `profile.md` and `agent.md`

## Active agent identity

`./.sps/agent.md` must always state:

- which host is active now
- SPS skill version stamp
- that `/sps` is required
- which capabilities were detected
- how the workflow will fall back if a capability is missing

Refresh this file whenever the host changes or a new session starts.
Read the matching file under `skills/sps/hosts/` for host-specific notes.

## Scope types

### Project-only

Use for anything that belongs to one repo, product, or client only:
- fonts
- spacing scale
- brand colors
- section order
- CMS choice
- storefront choice
- ERP choice
- animation style
- mobile simplifications
- deployment constraints
- `/sps` lock for this project

### Personal default

Use only when the user explicitly says the rule should apply across future
projects:
- preferred package manager
- preferred commit style
- preferred review style
- frequently preferred stacks

### Session-only

Use for temporary directions that should not be written into long-term memory:
- "keep this task minimal"
- "skip animation for now"
- "focus on mobile first in this chat"

## Write rules

- Do not write to `~/.sps/personal-defaults.md` without explicit approval.
- Do not copy one project's design or stack rules into another project.
- When in doubt, treat the rule as project-only.
- Never invent memory facts. If unknown, leave the field blank or mark
  Unverified.

## Suggested project profile shape

```markdown
# SPS Project Profile

## Required skill
- `/sps` required for this project: yes

## Project identity
- Name:
- Goal:
- Users:

## Mobile / performance policy
- Mobile default: minimal
- Richer mobile motion allowed: no
- Performance priority: speed | balanced | motion-heavy

## Project-only rules
- Typography:
- Colors:
- Motion:
- Stack:
- CMS:
- Storefront:
- ERP / admin:

## Explicit approvals
-

## Explicit rejections
-
```
