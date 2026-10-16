# Install — single unified stack

There is **one installer** and **one install**: `/sps` + the complete curated
skill stack. No profiles (no minimal/full/core choice) — one command installs
everything, one command updates, one command uninstalls.

## Install

### Mac / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/SHAHID8142/Shahid-Personal-SkillSet/main/get-sps.sh | bash -s -- --yes
```

Local clone:

```bash
bash install.sh --yes
```

### Windows (PowerShell)

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/SHAHID8142/Shahid-Personal-SkillSet/main/get-sps.ps1))) -Yes
```

## Update

```bash
bash ~/.sps/src/Shahid-Personal-SkillSet/scripts/sps-update.sh --yes   # pulls + reinstalls
# or
curl -fsSL https://raw.githubusercontent.com/SHAHID8142/Shahid-Personal-SkillSet/main/get-sps.sh | bash -s -- --yes
```

Sessions auto-check for updates on start (`scripts/check-update.sh`, cached 24h)
and auto-apply them.

## Uninstall

```bash
bash ~/.sps/src/Shahid-Personal-SkillSet/uninstall.sh --yes
bash ~/.sps/src/Shahid-Personal-SkillSet/uninstall.sh --keep-personal --yes   # keep ~/.sps memory
```

Windows: `uninstall.ps1` / `uninstall.ps1 -KeepPersonal -Yes`

## What gets installed (everything)

- `/sps` orchestrator (all hosts)
- `hallmark`, `impeccable`, `design-taste-frontend` (taste-skill v2)
- `sps-cms` (mandatory CMS engine)
- `webapp-testing`, `web-design-guidelines`
- `vercel-react-best-practices`, `vercel-composition-patterns`
- `karpathy-guidelines`, `verification-before-completion`
- `agent-browser`, `ai-seo`, `copywriting`, `deploy-to-vercel`
- `grill-me`, `caveman`, `fact-check`, `firecrawl`
- `astro-framework`, `webgpu-claude-skill`
- `supabase`, `supabase-postgres-best-practices`
- `prisma-database-setup`, `prisma-client-api`, `prisma-cli`
- `vercel-react-native-skills`, `sleek-design-mobile-apps`
- Claude-only when `claude` CLI present: UI/engineering/marketing/a11y plugins,
  Trail of Bits security plugins, Context7 MCP
- `graphify` when `uv`/`pip` present

Agent install targets (`--agents`): claude-code, cursor, codex, antigravity,
antigravity-cli, windsurf, github-copilot, opencode, cline, roo, kiro-cli, amp,
universal.