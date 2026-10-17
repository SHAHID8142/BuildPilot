# BuildPilot (`/sps`)

**Version:** 4.0.0 · **Repo:** `SHAHID8142/BuildPilot` (private)

BuildPilot tells your coding agent **how to build a project step by step** — with
memory, approvals, and (when you use a CMS) **storefront + admin controls
together**.

It works on **skills-compatible coding agents** (Claude Code, Cursor, Codex,
Antigravity, Windsurf, Copilot, OpenCode, and similar).
It does **not** work the same on every tool, and it is **not** for ChatGPT-style
chatbots.

---

## What is in this repository (two things, clearly separated)

| | The **skill** (`skill/`) | The **framework** (`framework/`) |
|---|---|---|
| What | Installable instructions your agent follows | A rulebook + referee that machine-checks agent work |
| Use it | `curl … get-sps.sh \| bash`, then type `/sps` in any project | Not user-installable yet — under construction, see its own gate |
| Status | ✅ Working, v4.0.0, 1,075 tests pass | 🚧 In progress — release gate NOT READY by design |
| Formerly | `skills/` | `sps2/` + `domain/` |

The skill is what you use today. The framework is a stricter, machine-verified
rebuild that agents must pass like an exam before work counts as done.

---

## Quick start (one-command install)

### Mac / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.sh | bash -s -- --yes
```

### Windows (PowerShell)

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.ps1))) -Yes
```

### Check install

```bash
bash ~/.sps/src/BuildPilot/scripts/sps-doctor.sh
```

### Update

```bash
curl -fsSL https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.sh | bash -s -- --yes
# or, after a session-start auto-check:
bash ~/.sps/src/BuildPilot/scripts/sps-update.sh --yes
```

### Uninstall

```bash
bash ~/.sps/src/BuildPilot/uninstall.sh --yes
# keep personal memory:
bash ~/.sps/src/BuildPilot/uninstall.sh --keep-personal --yes
```

Windows: `uninstall.ps1` / `uninstall.ps1 -KeepPersonal -Yes`

> **Trust note:** the installer fetches ~27 third-party skills via `npx skills add`
> with auto-yes, sets `StrictHostKeyChecking=no` for its git operations, and
> refreshes the managed `sps`/`sps-cms` skill directories (overwriting local edits
> in those paths). Review `install.sh` before running it in a sensitive environment.

---

## One installer — everything included

There is a **single unified install**: `/sps` + the complete curated skill stack.
No profiles, no minimal/full choice — one command installs everything:

- `/sps` orchestrator + plan gate + auto-update system
- Design taste (`design-taste-frontend` v2 + `hallmark` + `impeccable`)
- **`sps-cms`** (mandatory CMS engine)
- React/performance (`vercel-react-best-practices`, `vercel-composition-patterns`)
- Testing (`webapp-testing`), live verify + Lighthouse (`agent-browser`)
- SEO + copy (`ai-seo`, `copywriting`, `fact-check`)
- Deploy (`deploy-to-vercel`)
- **`karpathy-guidelines`** + **`verification-before-completion`** + `grill-me` + `caveman`
- Backend (`supabase`, `supabase-postgres-best-practices`, `prisma-*`)
- Mobile (`vercel-react-native-skills`, `sleek-design-mobile-apps`)

---

## Commands

| Command | What it does |
|---|---|
| `/sps` | Start / continue the normal build workflow |
| `/sps audit` | Score the project against SPS rules |
| `/sps sync` | Fix **CMS debt** |
| `/sps doctor` | Check install / host / skill health |

More modes (documented in the skill itself): `/sps cms-sync` / `/sps couple`
(aliases of sync), `/sps release-lock` / `/sps unlock` (final handoff).

---

## The workflow in one breath

Discover (goals, stack, CMS, auth, mobile, roles, deploy) → write `.sps/` memory +
root mirrors → **plan → stop → your approval** → CMS foundation → one section at a
time (storefront + CMS controls + proof they connect) → **stop for your approval →
next section** → handoff.

## Host compatibility

| Host | Support |
|---|---|
| Claude Code | **Best** — full stack + plugins/MCP extras |
| Cursor / Codex | High |
| Antigravity / Gemini | Medium — must respect `/sps` locks in `GEMINI.md` / `AGENTS.md` (boot refusal if missing) |
| Windsurf / Copilot / OpenCode family | Medium |
| Other skills-compatible agents | Varies |
| Generic chatbots | No — out of scope |

See `skill/sps/CAPABILITY-MATRIX.md` for details.

## Safety

- Review third-party skills before trusting them.
- `/sps` never pushes, publishes, or deploys without your explicit approval.
- Project memory lives in `.sps/` inside your project; nothing is sent anywhere.

---

## Repository layout

```
BuildPilot/
├── README.md            ← you are here
├── skill/               ← the product (installable)
│   ├── sps/             ← /sps orchestrator + workflow docs + hosts/
│   └── sps-cms/         ← CMS engine skill
├── framework/           ← the machine-verified governance framework (in progress)
│   ├── sps2/            ← gates, validators, decisions, evidence
│   └── domain/          ← sample site the gates check against
├── scripts/             ← doctor, updater, lint, smoke
├── docs/                ← historical phase audits (docs/audits), dev tests
├── reports/             ← append-only work reports
├── loop/                ← Karpathy-style human-gated task loop (driver for agents)
├── install.sh / .ps1    ← installers
├── get-sps.sh / .ps1    ← one-line bootstrap
└── uninstall.sh / .ps1  ← uninstallers
```

## License

MIT — see `LICENSE`. Third-party skills installed by the installer carry their own
licenses and terms.
