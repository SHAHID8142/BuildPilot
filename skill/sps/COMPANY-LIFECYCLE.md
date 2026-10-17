# Company Project Lifecycle (Kickoff → Delivery → After-Sale)

The standard agent workflow for every client job. It runs end-to-end but
STOPS at the two mandatory user gates — **G1** (platform/change-list
confirmation, below) and **G2** (lifecycle-plan approval, Phase 2) — no
exception. Delivery additionally requires the user's go before any deploy.

## Phase 0 — Kickoff discovery (agent collects, user answers)

The agent opens every project by asking ONE consolidated questionnaire and
does not build anything until it is answered. Required answers:

1. **Project goal** — what the site/app must do, in the client's words.
2. **Deploy target** — where it will be deployed (Vercel / shared hosting
   / cPanel / VPS / Cloudflare / other) and who owns the account/domain.
3. **Stack constraints** — required or banned technologies.
4. **Content** — who provides it (client copy/images vs agent drafts),
   language(s), RTL needs.
5. **CMS** — enabled? (If yes: `sps-cms` ships with the section, never after.)
6. **Brand** — logo, colors, references to like / avoid.
7. **Contacts & integrations** — forms, WhatsApp, analytics, tracking IDs.
8. **Auth** — login/user accounts needed? If yes: what data, what roles.
9. **Mobile policy** — mobile-first, desktop-only, or responsive parity;
   low-end device support expectations.
10. **Multi-agent roles** — if other agents/people touch the repo, who does
    what; single-agent assumption otherwise.
11. **Timeline & budget constraints** — if any.
12. **After-sale acknowledgment** — confirm the standard policy applies
    (see Phase 6): 1 month all-type support + 1 month free SEO.

Missing answers are asked once more, batched; anything still unknown is
recorded in `.sps/profile.md` as `Assumed` and flagged at G1.

## Phase 1 — Platform research & compatibility assessment (agent works)

The agent researches the user's chosen deploy target and produces a written
assessment in `.sps/platform-assessment.md`:

- **Platform facts** — runtime support, build requirements, limits
  (serverless vs long-running, upload caps, DB options, HTTPS/domain setup).
- **Compatibility verdict** — fits as-is / fits with changes / poor fit.
- **Required changes** — concrete list: config, adapters, stack swaps,
  hosting-specific constraints (e.g. PHP version, Node version, writable
  dirs, cron for backups).
- **Improvements the platform enables** — e.g. edge caching, image CDN.
- **Risks & costs** — anything that will bite later (lock-in, cold starts,
  bandwidth limits).

## GATE 1 (G1) — User confirmation (mandatory stop)

Present the assessment: target, verdict, every required change, every
assumption made during kickoff. The user explicitly confirms the platform
and the change list before any code is written. Changes the user rejects
are renegotiated here — not silently dropped or silently implemented.

## Phase 2 — Structured lifecycle plan

Write `./.sps/plan.md` covering the FULL lifecycle through delivery:

1. Foundation (repo, stack, deploy pipeline skeleton, environments)
2. CMS foundation (if enabled — before any storefront section)
3. Sections (each with storefront + CMS + proof they connect)
4. QA gates (tests, a11y, performance, mobile-low-end, SEO audit)
5. Deployment (pipeline, rollback path, post-deploy smoke)
6. Handoff (docs, credentials transfer, client walkthrough)
7. **After-sale window** (Phase 6 below, dated from delivery)

The plan follows the standard Plan Gate — **GATE 2 (G2, mandatory stop)**:
present the plan → user approval → only then build.

## Phase 3 — Build (section loop)

Standard `/sps` section-by-section construction: plan gate per section,
CMS-coupled delivery, design gate, Section DoD, verification checkpoint
before each hand-back.

## Phase 4 — Pre-delivery gate

Full battery green + live deploy smoke + client-acceptance walkthrough.
The handoff checkpoint (HANDOFF-CHECKPOINT.md) records PASS on the final
deployed state — not just on the local build.

**Legal & compliance gate:** walk [LEGAL-COMPLIANCE.md](LEGAL-COMPLIANCE.md)
section by section; every applicable item is PASS or N/A-with-reason. The
applicable sections were scoped at kickoff (Phase 0); new surfaces added
during the build extend the scope. Legal documents are drafted as templates
and flagged for the client's counsel — never presented as legal advice.

## Phase 5 — Delivery

- Deployment live on the client's target, verified by URL.
- Handoff pack: what was built, how to use the admin/CMS, how to deploy
  updates, credentials transferred securely, rollback instructions.
- Delivery date recorded in `.sps/handoff.md` — it starts the after-sale clock.

## Phase 6 — After-sale service (company policy, mandatory)

Every completed job includes, dated from delivery:

1. **One month of after-sale support — ANY request type.** Bug fixes,
   debugging, content edits, small design tweaks, configuration help:
   all covered, no category exclusions. Response expectation: acknowledged
   same day, fix or concrete next-step within 48h.
2. **One month of free SEO.** Technical SEO audit + fixes (indexing,
   metadata, sitemap/robots, structured data, CWV static checks) via the
   `sps-seo` standard, run at delivery and again at the end of the month
   with a before/after report.

Operational rules:

- The agent tracks the window in `.sps/after-sale.md` (delivery date,
  support end date, SEO end date, request log).
- Requests are triaged: fix immediately (covered) vs new scope (outside
  the month or beyond a tweak) — the agent says which is which BEFORE
  doing the work, and new scope gets its own mini-plan and approval.
- At day 30: send the closing report (requests handled, SEO before/after)
  and offer the paid continuation options. Nothing continues silently.

## Non-negotiables across all phases

- No code before G1 + plan approval. No deploy without the user's go.
- Every phase ends with evidence, not claims (HANDOFF-CHECKPOINT law).
- CI/CD minutes are budgeted (DEPLOY-BUDGET law): batch, verify locally,
  deploy once.
