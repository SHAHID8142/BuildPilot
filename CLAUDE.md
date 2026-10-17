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

## BUPT alias
"BUPT" is the User's shortcut for this project's SPS skill: when the User says
"load bupt" (or any variant), read `skill/sps/SKILL.md` and operate as the SPS
workflow from `skill/sps/`. Same thing as `/sps`.
