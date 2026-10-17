## /sps lock (required)

This project is under `/sps` orchestration. Antigravity must NOT use a host-default
scaffold workflow instead of `/sps`.

Before any code:
1. Read `./.sps/profile.md` and `./.sps/handoff.md`
2. Read the SPS Method Card from the installed `sps` skill (`METHOD-CARD.md`)
3. Build work requires an approved `./.sps/plan.md` — zero code before plan approval
4. Follow CMS-coupled section delivery when CMS is enabled (engine skill: sps-cms)
5. Stop for approval after each section Definition of Done; user manually checks each section

Commands: `/sps` · `/sps audit` · `/sps sync` · `/sps doctor`

## SPS behavioral rules (required, Karpathy)

1. Think before coding: state assumptions, enumerate interpretations, ask if ambiguous.
2. Simplicity first: deliver the minimum code the task requires; no speculative features.
3. Surgical changes: edit only what the request requires; never refactor unrelated code.
4. Goal-driven execution: define visible success criteria and verify them before claiming done.
5. Never claim verification that was not actually run (no "should pass").
