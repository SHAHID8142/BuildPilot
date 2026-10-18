<div align="center">

# 🏗️ BuildPilot

### Your AI agent writes code. BuildPilot makes it keep its promises.

**A foreman for coding agents** — Claude Code, Cursor, Codex, and 30+ more.

**Version:** 4.4.0 · 1,258 tests · MIT · `SHAHID8142/BuildPilot`

</div>

---

## The problem you've already lived

You've done this. Everyone has:

```text
YOU:      Build me a landing page with a contact form.

AGENT:    On it! Building now...

AGENT:    Done! ✅ I created 14 files, refactored your router,
          upgraded three dependencies, and added a dark mode
          toggle you didn't ask for.

YOU:      ...I just wanted a landing page.

AGENT:    (new session)  Sorry, what landing page?
```

The agent freelanced. It skipped your intent, invented scope, and remembered
none of it. And "done" was just a word it said.

**BuildPilot is the fix.** It's a skill your coding agent follows — a foreman
that stands between your request and the agent's hands:

```text
YOU:      Build me a landing page with a contact form.

AGENT:    Before I build anything, three questions:
          1. What pages, exactly?          → you answer
          2. Contact form → where does it send?  → you answer
          3. CMS for editing text later?   → you answer

          Here is the written plan. I stop here.

          ⏸️  GATE 1 — nothing gets built until you approve.

YOU:      Approved. (but change the headline style)

AGENT:    Plan updated. Building page 1 of 5...

          ⏸️  GATE 2 — section 1 done. Proof: [test output]
          [screenshot] [CMS admin wired to it]. Approve to continue?
```

Same agent. Same model. Different behavior — because it's following a
foreman, not vibes.

---

## Install in 30 seconds

**Mac / Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.sh | bash -s -- --yes
```

**Windows (PowerShell):**

```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.ps1))) -Yes
```

Then open your project, type **`/sps`**, and answer the kickoff questions.
That's the whole onboarding.

```bash
# Check the install is healthy:
bash ~/.sps/src/BuildPilot/scripts/sps-doctor.sh

# Update later (same one-liner, or):
bash ~/.sps/src/BuildPilot/scripts/sps-update.sh --yes

# Uninstall (add --keep-personal to save your project memory):
bash ~/.sps/src/BuildPilot/uninstall.sh --yes
```

> **Trust note:** the installer fetches 26 third-party skills via `npx skills add`
> with auto-yes, installs 11 Claude plugins from 4 marketplaces, adds the
> Context7 MCP server and the graphify CLI, uses `StrictHostKeyChecking=accept-new`
> for its git operations (unknown hosts accepted on first use; changed host keys
> rejected), and refreshes the managed `sps`/`sps-cms`/`sps-seo` skill directories
> (overwriting local edits in those paths; a timestamped backup is kept in
> `~/.sps/backups/`). You are asked once, before any of this runs: answer
> interactively, pass `--yes` to consent, or pass `--no-extras` for a core-only
> install. Review `install.sh` before running it in a sensitive environment.

---

## The contract your agent signs

Every BuildPilot run is bound by five promises. Not suggestions — machine-
checked laws, with a referee (`framework/`) that fails the agent's work if
any promise is broken:

| # | The promise | What enforces it |
|---|---|---|
| 1 | **No code before a plan you approved.** | The plan gate — a hard stop, every time |
| 2 | **Every section ends in proof, not claims.** | Product-proof gate: test output, screenshot, or boot log — attached, or the handoff fails |
| 3 | **CMS sites ship whole.** | Storefront + admin controls land in the same section, or the section is marked incomplete |
| 4 | **It remembers.** | All project memory lives in `.sps/` inside *your* project — the only thing ever sent is a lesson you explicitly confirm via `sps-lesson.sh send` |
| 5 | **Mistakes can't quietly return.** | A rule broken twice gets an auto-generated regression test that lives in the test suite forever |

And the promise to *you*, outside the machine: **`/sps` never pushes,
publishes, or deploys without your explicit yes.**

---

## What a gate looks like

This is a real approval stop. The agent cannot move on until you answer:

> ### ⏸️ G1 — Plan approval
> **What you're deciding:** do you approve this plan before any code is written?
>
> **The plan in one breath:** a 5-page online shop with a photo gallery and a
> contact form; you can edit the text yourself.
>
> **Your options:**
> - ✅ **Approve** — building starts exactly as planned
> - ✏️ **Change something** — tell us what to adjust (cheap now, expensive later)
> - ❓ **Ask first** — we'd rather explain twice than build once wrong

*(Projects can opt into plain-language mode — `language: plain` in
`.sps/agent.md` — and every gate is written like the above: 8th-grade words,
one-line "what you're deciding" summary. The technical default is unchanged.)*

---

## With vs. without

| | Without BuildPilot | With BuildPilot |
|---|---|---|
| Getting started | "Just start coding" vibes | Kickoff questions → written plan → **your approval** |
| Mid-build | Agent freelances for hours | Hard stop at every section; you steer |
| "Is it done?" | Agent's word for it | Tests + validators + proof it runs |
| Next week | Agent remembers nothing | Full project memory in `.sps/` |
| CMS work | Storefront now, admin "later" | Both ship together or the section isn't done |
| Mistakes | Silently repeat | Second rejection → auto-generated regression test |

---

## The workflow in one picture

```
 Discover          Plan            Build (section by section)         Handoff
┌─────────┐    ┌─────────┐    ┌──────────────────────────────┐    ┌─────────┐
│ goals    │    │ written │    │  section 1 → ⏸️ you approve  │    │ proof + │
│ stack    │ →  │ + stop  │ →  │  section 2 → ⏸️ you approve  │ →  │ backup +│
│ CMS/auth │    │ ⏸️ YOU  │    │  section 3 → ⏸️ you approve  │    │  unlock │
│ deploy   │    │  DECIDE │    │  (storefront + CMS together) │    │         │
└─────────┘    └─────────┘    └──────────────────────────────┘    └─────────┘
                     ▲                                            │
                     └────────── your project memory (.sps/) ─────┘
```

---

## Don't take the README's word for it

Every claim above has a command behind it. Run them yourself:

| Claim | Prove it with |
|---|---|
| "Secrets get a pattern-based gate" | `bash scripts/secret-scan.sh` — scans every push, CI blocks the merge (pattern scanner with a reviewed allowlist — not a guarantee; review what you push) |
| "Third-party skills can't be tampered with" | `bash scripts/sps-provenance.sh check --strict` — shipped skills are pinned in the committed store `.sps/provenance-store.json`; CI fails on any drift |
| "The rules are actually enforced" | `python3 framework/sps2/tools/check_laws.py .` — the referee's own report card |
| "Docs never rot" | `python3 framework/sps2/tools/check_docs_drift.py` — every command in the docs must exist, or this fails |
| "Your work is backed up" | `bash scripts/sps-backup.sh snapshot` — rolling snapshots of your project memory |
| "1,258 tests" | `PYTHONPATH=. python3 -m unittest $(cat .github/expected-test-modules.txt \| tr '\n' ' ')` — count them yourself |

---

## Commands you'll actually use

| Command | What it does |
|---|---|
| `/sps` | Start / continue the build workflow |
| `/sps status` | One-glance dashboard: branch, queue, support clocks, pending lessons |
| `/sps audit` | Score the project against SPS rules |
| `/sps doctor` | Check install / host / skill health |
| `/sps sync` | Fix **CMS debt** |
| `/sps lesson review` | Review lessons from client projects; approve them into permanent rules |
| `/sps unlock` | Final handoff (alias: `release-lock`) |

More modes live in the skill itself (`/sps cms-sync` and `/sps couple` are
aliases of sync). New to the skill? The one-page cheat sheet is at
[`skill/sps/CHEAT-SHEET.md`](skill/sps/CHEAT-SHEET.md).

---

## How to talk to your agent (what to type, when)

You never need special syntax — plain sentences work. But these phrasings
trigger exactly the right behavior at each stage:

**Starting a project** (in your project folder, with your agent open):

```text
/sps                                          ← start the workflow
Build me a <what>, for <who>, deployed to <where>.   ← then answer the kickoff questions
That's all the answers                        ← done with the questionnaire
Confirm the platform                          ← your yes at the platform gate
Approve the plan                              ← your yes before any code is written
```

**While it builds** — you're the foreman's boss, every section stops for you:

```text
Approve                                       ← yes to this section as shown
Request changes: <what to change>             ← it fixes and re-asks
Batch approve                                 ← let low-risk sections run without stopping
Why?                                          ← it must explain before continuing
I'll do that step now                         ← you're on an external step (API key, DNS)
```

**Checking and steering:**

```text
/sps status                                   ← "where am I?" — branch, queue, clocks
/sps audit                                    ← score the project against the rules
Stop. Let's discuss.                          ← full stop, nothing proceeds until you resume
```

**When something's wrong:**

```text
/sps doctor                                   ← install/host feels broken — run this first
Here's what I saw: <paste the error>          ← report exactly what happened
Capture a lesson: <what went wrong>           ← turn a mistake into a permanent rule
```

**Finishing:**

```text
/sps unlock                                   ← project done; final handoff
```

> Two habits worth keeping: never paste real secrets into the chat (put them
> in `.env` yourself, masked in conversation), and when you don't understand
> a gate, ask — "explain what you're deciding" — rather than approving blind.

---

## Handy scripts (copy-paste, run from the repo root)

Everyday maintenance — all safe, read-only unless noted:

```bash
# Project dashboard — branch, queue, pending lessons, support clocks
bash scripts/sps-status.sh

# Health check — install, host, and skill integrity (add --fix to repair)
bash scripts/sps-doctor.sh

# Back up your project memory (.sps/) — keeps the last 10 snapshots
bash scripts/sps-backup.sh snapshot

# See all backup snapshots with sizes and ages
bash scripts/sps-backup.sh list
```

Occasional but worth knowing:

```bash
# Scaffold a fresh client project for the SPS workflow (idempotent)
bash scripts/sps-init.sh [target-dir]

# Tidy up stray files — report only (add `fix` to safely move them to quarantine)
bash scripts/sps-hygiene.sh

# Check for updates without changing anything
bash scripts/sps-update.sh --check

# Roll back an installed skill to a previous backup (interactive picker)
bash scripts/sps-restore.sh

# Capture a lesson learned in this project, then send it to BuildPilot
bash scripts/sps-lesson.sh capture "short title"
bash scripts/sps-lesson.sh send          # shows everything first, asks before publishing
```

CI-style checks you can run locally (the same ones GitHub runs on every push):

```bash
# Scan for secret-shaped values before you push
bash scripts/secret-scan.sh

# Verify shipped third-party skills haven't been tampered with
bash scripts/sps-provenance.sh check --strict

# The referee's own report card — are all SPS laws currently satisfied?
python3 framework/sps2/tools/check_laws.py .

# Full smoke test of the skillset
bash scripts/smoke-sps.sh
```

---

## What's in this repository (two things, clearly separated)

| | The **skill** (`skill/`) | The **framework** (`framework/`) |
|---|---|---|
| What | Installable instructions your agent follows | A rulebook + referee that machine-checks agent work |
| Use it | `curl … get-sps.sh \| bash`, then type `/sps` in any project | Not user-installable yet — under construction, see its own gate |
| Status | ✅ Working, v4.4.0 | 🚧 In progress — release gate NOT READY by design |
| Formerly | `skills/` | `sps2/` + `domain/` |

The skill is what you use today. The framework is a stricter, machine-verified
rebuild that agents must pass like an exam before work counts as done.

**New here?** Read the [User Guide](USER-GUIDE.md) — everything a person does:
install, approve work, the lesson loop, safety model. This README is the map;
the guide is the walkthrough.

---

## Host compatibility

| Host | Support |
|---|---|
| Claude Code | **Best** — full stack + plugins/MCP extras |
| Cursor / Codex | High |
| Antigravity / Gemini | Medium — must respect `/sps` locks in `GEMINI.md` / `AGENTS.md` (boot refusal if missing) |
| Windsurf / Copilot / OpenCode family | Medium |
| Other skills-compatible agents | Varies |
| Generic chatbots | No — out of scope |

Works on the Agent Skills-standard registry: Claude Code, Cursor, Codex,
Gemini CLI / Antigravity, Windsurf, OpenCode, GitHub Copilot, Cline, Roo Code,
Kiro, Amp, Goose, Crush, TRAE, Junie, Zed, OpenClaw, and 30+ more.
It does **not** work the same on every tool, and it is **not** for
ChatGPT-style chatbots. Details: `skill/sps/CAPABILITY-MATRIX.md`.

---

## Repository layout

```
BuildPilot/
├── README.md            ← you are here
├── skill/               ← the product (installable)
│   ├── sps/             ← /sps orchestrator + workflow docs + hosts/
│   ├── sps-cms/         ← CMS engine skill
│   └── sps-seo/         ← technical SEO standard
├── framework/           ← the machine-verified governance framework (in progress)
│   ├── sps2/            ← gates, validators, decisions, evidence
│   └── domain/          ← sample site the gates check against
├── scripts/             ← doctor, updater, backup/restore, hygiene, secret-scan
├── docs/                ← historical phase audits (docs/audits), dev tests
├── reports/             ← append-only work reports
├── loop/                ← Karpathy-style human-gated task loop (driver for agents)
├── install.sh / .ps1    ← installers
├── get-sps.sh / .ps1    ← one-line bootstrap
└── uninstall.sh / .ps1  ← uninstallers
```

## License

MIT — see `LICENSE`. Third-party skills installed by the installer carry their
own licenses and terms.
