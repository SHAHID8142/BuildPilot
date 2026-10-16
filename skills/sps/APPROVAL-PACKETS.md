# Approval Packets & Batch Modes

Before building each section, component, or chunk, send an appropriate tier approval packet.
Do not proceed until the user approves (or batch mode is enabled).
Build work additionally requires the plan gate first ([PLAN-GATE.md](PLAN-GATE.md)).

---

## 1. Two-Tier Packet System

### Tier 1: Compact Quick-Fix Packet (Small Edits, Bug Fixes, Tweaks)
Use for small bug fixes, styling adjustments, copy edits, or single-file changes
(the only category allowed to skip the full plan gate):

```markdown
### Quick-Fix Approval Packet
- **Target / Section:** (e.g. Header phone number alignment)
- **Proposed Change:** (1-2 sentences)
- **Affected Files:** (list of files)
- **Risk / Side Effects:** None / minimal
- **Proceed?** (Reply 'yes' / 'go ahead')
```

---

### Tier 2: Full Architecture Packet (Major Sections, Pages, Schema)
Use for major sections, new collections, database migrations, or redesigns:

```markdown
## Approval Packet (Tier 2)

Section:
Purpose:

Required skill:
- `/sps` orchestrating: yes
- Method card read: yes

Active agent:
- Host:

Role stack:
- Primary engineering/design role:
- ROLE-MATRIX roles:

Skills selected (router):
- Primary per domain:
- Secondary (optional):

This chunk covers:
- frontend / UI:
- backend / data:
- CMS / content (inventory + admin UI + wire):
- CMS round-trip proof plan:
- storefront / ERP / admin:
- accessibility:
- performance & mobile behavior: minimal / dual / richer (user-approved)
- workspace hygiene & cleanup gate plan:

Evidence:
- Known / Assumed / Unverified:

Memory updates after approval:
- profile / handoff / content-model / section-todos / registry:

Next action after approval:
- ...
```

---

## 2. Batch Approval Mode (B3)

If the user explicitly states `batch approve`, `approve all remaining sections`, or runs `/sps approve --batch`:
1. The agent may execute multiple low-risk sections consecutively without stopping after every single sub-step.
2. The agent MUST still respect Section DoD, CMS round-trips, and memory file updates for each section.
3. Stop immediately if an error, breaking change, or ambiguity occurs.

---

## 3. Manual Check Loop (per section)

After a section ships and its approval packet is accepted:

1. The user checks the section live: storefront + CMS admin + mobile viewport.
2. The user gives feedback (change requests or OK).
3. On change requests: agent fixes, re-runs verification (tests + Lighthouse),
   resubmits the updated packet.
4. Only after the user confirms OK does the next section start.

The section is not "done" until the manual check passes. See
[SECTION-DOD.md](SECTION-DOD.md) item 29.

---

## 4. Release `/sps` Lock Procedure (B3)

If the user wishes to exit `/sps` orchestrator mode or handover the repository cleanly:
- Command: `/sps release-lock` or `/sps unlock`
- Action:
  1. Remove `./.sps/lock.json`
  2. Comment out the hard-lock block in `GEMINI.md`, `AGENTS.md`, `CLAUDE.md` with timestamp.
  3. Write final summary to `./.sps/handoff.md`.

---

## 5. Abort Conditions

Do **not** start coding the chunk if any of these are true:
1. `./.sps/agent.md` is missing or has no active host
2. `/sps` lock is missing from project memory or root mirrors when required
3. Required discovery answers are still unknown for this chunk
4. Build request without an approved `./.sps/plan.md` (PLAN-GATE)
5. CMS-enabled project and this UI chunk has no CMS inventory + admin plan
6. UI chunk lacks responsive + mobile behavior notes
7. Asset budget would be exceeded without explicit approval
8. Todo list for the chunk is missing
9. The packet claims verification that has not happened
