## /sps lock
This project uses `/sps` as the master workflow.
Read `./.sps/profile.md`, `./.sps/handoff.md`, and the SPS Method Card before
building. Do not replace `/sps` with a host-default scaffolding workflow.
Build work requires an approved `./.sps/plan.md` (zero code before plan approval).
CMS-enabled sections must ship storefront + CMS controls together (engine: sps-cms).
Each section ends with a user manual check before the next section starts.

## Session hard laws (binding on every agent in this repo)
- **Task queue:** finish the current task first; new tasks are queued to
  `./.sps/task-queue.md`, never started mid-task (skill/sps/TASK-QUEUE.md).
- **Write confinement:** write only inside this project directory — no
  agent-private memory, no home-dir writes (skill/sps/WRITE-CONFINEMENT.md).
- **Handoff checkpoint:** no hand-back until the verification checkpoint in
  skill/sps/HANDOFF-CHECKPOINT.md records PASS on the final state.
- **Deploy budget:** batch all fixes, validate locally, push/CI once
  (skill/sps/DEPLOY-BUDGET.md). CI minutes are a budget.
- **Tool consent:** verify a tool exists before invoking it; a missing tool
  stops the task — disclose what/why/install-scope and get explicit consent,
  never silent installs (skill/sps/TOOL-CONSENT.md).
- **Company lifecycle:** client jobs run the kickoff → platform research →
  G1 confirm → plan → build → delivery → after-sale workflow in
  skill/sps/COMPANY-LIFECYCLE.md (1 month all-type support + 1 month free
  SEO standard on every completed job).

## Skill alias (BUPT / BuildPilot)
"BUPT" and "BuildPilot" are the User's shortcuts for this project's SPS skill:
when the User says "load bupt", "load BuildPilot", "load the BuildPilot", or
any variant — with or without the word "SPS" — read `skill/sps/SKILL.md` and
operate as the SPS workflow from `skill/sps/`. Same thing as `/sps`. Never
ask the User to repeat it with a different name; the alias is already enough.
