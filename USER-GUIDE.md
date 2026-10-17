# BuildPilot User Guide (for humans)

You don't need to read the skill's internal docs to use BuildPilot. This guide
covers everything a person actually does: install, start a project, approve
work, and use the improvement loop.

---

## 1. Install (one command)

Mac / Linux:
```bash
curl -fsSL https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.sh | bash -s -- --yes
```
Windows (PowerShell):
```powershell
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/SHAHID8142/BuildPilot/main/get-sps.ps1))) -Yes
```

Then open your coding agent in any project and type **`/sps`**. That's the
whole onboarding. `bash ~/.sps/src/BuildPilot/scripts/sps-doctor.sh` checks
the install if anything looks off.

---

## 2. Starting a project — what the agent will ask you

The agent runs a **kickoff questionnaire** (one batch of questions, answered
once): what the site/app must do, where it will be deployed, stack
constraints, who provides content, whether a CMS is needed, brand references,
integrations, auth, mobile expectations, timeline.

After your answers it researches your deploy target and presents a platform
assessment. **You confirm it (G1) before any code is written.** Then you get
a build plan — **you approve it (G2) before the first section.** These two
stops are mandatory; the agent cannot skip them.

---

## 3. During the build — your two jobs

**Approve each section.** Every section arrives as an approval packet: a
5–6 line summary for small fixes, a full packet for new pages/features. You
say approve / request changes. You can also say `batch approve` to let
consecutive low-risk sections run without stopping.

**Answer platform steps.** When the agent needs something only you can do
(create an API key, point DNS, accept OAuth), it gives you **one step at a
time** and waits. You never need to paste full secrets into the chat — mask
them (`sk_live_…abc123`) and put real values into `.env` yourself.

---

## 4. The commands you'll actually use

| Command | When |
|---|---|
| `/sps` | Start or continue building |
| `/sps status` | "Where am I?" — branch, task queue, after-sale clocks, pending lessons |
| `/sps audit` | Score the project against the rules (100 points) |
| `/sps doctor` | Something feels broken — checks install/host/skill health |
| `/sps sync` | An old project has storefront/CMS debt — pay it down |
| `/sps lesson review` | Turn lessons from client projects into permanent rules |
| `/sps release-lock` | Project finished — cleanly remove the workflow lock |

---

## 5. The improvement loop (lessons)

When the agent makes a mistake — or you spot one — in **any** project built
with BuildPilot:

1. Tell the agent, or run:
   `bash scripts/sps-lesson.sh capture "short title"`
2. It fills a strict template with you (what went wrong, the rule that
   prevents it, which doc it belongs to).
3. When ready: `bash scripts/sps-lesson.sh send` — opens a pull request
   against BuildPilot. Nothing is sent automatically.
4. Next time you're in the BuildPilot repo:
   `bash scripts/sps-lesson.sh review` — walk each lesson, approve/reject.
   Approved lessons become permanent rules in the skill, enforced by CI.

---

## 6. After delivery (client work)

Every completed job includes **1 month of all-type support** (bugs, edits,
tweaks — no category exclusions) and **1 month of free SEO** (audit + fixes
at delivery and again at day 30 with a before/after report).
`/sps status` shows the days remaining on both clocks.

---

## 7. Safety model, in plain words

- The agent **never pushes, deploys, or publishes** without your explicit go.
- Project memory lives in `.sps/` inside your project — nothing is sent anywhere.
- Third-party skills are only installed after you consent (the agent must
  ask first, every time).
- Legal documents the agent drafts (privacy policy, terms, refund policy)
  are templates **flagged for your lawyer** — not legal advice.
- The installer overwrites the bundled `sps`/`sps-cms`/`sps-seo` skills on
  update; your project's own files are never touched by updates.

---

## 8. Uninstall

```bash
bash ~/.sps/src/BuildPilot/uninstall.sh --yes            # full removal
bash ~/.sps/src/BuildPilot/uninstall.sh --keep-personal --yes  # keep personal defaults
```
Backups of previously-installed skills live in `~/.sps/backups/` (last 3 kept).
