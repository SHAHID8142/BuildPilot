# Plan-First Zero-Code Gate (hard law)

Every build starts with a written plan. **Zero code is written before the plan
is approved.** No scaffolding, no "quick prototype", no "just a folder".

## The Gate

1. Discovery completes (goals, stack, CMS, auth, mobile, deploy, roles).
2. Agent writes `./.sps/plan.md` from [templates/plan.md](../templates/plan.md).
3. Agent presents the plan summary + open questions to the user.
4. **Stop.** No code, no files, no installs until the user approves the plan
   (or explicitly says what to change).
5. On approval: stamp `plan.md` status `approved`, then build section-by-section
   per [SECTION-DOD.md](SECTION-DOD.md).

## What the plan must contain

- Goal + success criteria (measurable)
- Stack with Known / Assumed / Unverified labels
- Page/section inventory in build order (one section at a time)
- CMS plan: foundation first, per-section coupling
- Design direction + taste skill selection (see SKILL-ROUTER.md)
- SEO + Lighthouse target per section
- Deploy target + readiness steps
- Mobile behavior policy (low-end dual path when needed)
- Subagent plan per section (which agents run in parallel)
- Verification plan per section (tests, round-trips, Lighthouse)

## Abort conditions

Do not write code if:

1. `./.sps/plan.md` is missing for a build request
2. Plan is not approved (status != `approved`)
3. Plan has open `Unknown` items that block the current section
4. User asked for a plan first and the plan was rejected

## Exceptions

- **Tier 1 quick-fix** (bug fix, copy edit, single-file tweak) may skip the
  full plan file, but still requires a 5-line quick-fix approval packet
  ([APPROVAL-PACKETS.md](APPROVAL-PACKETS.md)).
- **Read-only Q&A** never needs the gate.
- `/sps audit` and `/sps sync` are read/remediate workflows; sync remediation
  still uses the gate when it adds new sections.

## Memory

After approval, write the approved plan summary into `./.sps/handoff.md` and
record the decision in `./.sps/changelog-sps.md`.