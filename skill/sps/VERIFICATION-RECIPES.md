# Verification Recipes

Use the strongest realistic recipe the current host supports.
Never claim a check that was not run.

## Frontend / component change

Check:
- lint / type errors
- render correctness
- responsive states at 320 / 375 / 768 / 1024+
- keyboard / focus states
- reduced-motion behavior if animated
- mobile path is minimal or explicitly approved richer
- no hover-only critical actions

## Full-stack feature

Check:
- lint / type errors
- critical happy path
- error / loading / empty states
- auth / permission handling
- build or runtime sanity

## CMS / content-model change

Check:
- schema or model validity
- preview / rendering path
- missing content fallback
- SEO field coverage if applicable
- **round-trip**: edit in admin → content layer/API → storefront visible change
- seed/demo media replace/hide/delete path
- no untracked hardcoded bypass for claimed-controllable fields

## Storefront / checkout change

Check:
- price / cart correctness
- checkout / payment edge states
- inventory or order assumptions
- mobile checkout flow

## Deploy / infrastructure change

Check:
- config validity
- build output
- environment variables
- rollback path
- deployment-specific smoke test

## Mobile / responsiveness

Check:
- 320px
- 375px
- 768px
- laptop widths
- touch behavior
- whether hover-only interactions are removed or replaced
- whether the mobile path avoids fancy / laggy effects

## Low-end performance

Check:
- animation count and weight
- image / asset weight against ASSET-BUDGET defaults
- layout thrash risk
- whether a simpler mobile path is needed
- whether continuous loops or heavy blur/shadow stacks were removed on mobile

## Asset budget

Check:
- mobile hero weight
- autoplay / video background policy
- motion library count on mobile
- whether desktop-only rich assets are correctly gated

## Runtime performance (backend/full-stack work)

Check:
- no N+1 query patterns in list/detail views (grep loops containing queries)
- no unbounded queries (missing LIMIT/pagination on user-facing lists)
- no repeated identical API calls from the client (dedupe/cache)
- expensive queries cached server-side where a repeat pattern exists
- API payloads compressed (gzip/brotli at the server/proxy tier)
- DB connections pooled (no per-request connect storms under load)
- heavy work (emails, thumbnails, exports) runs in a background queue,
  not inside the request cycle
- long-running handlers can't pile up (timeouts on outbound calls)
- service-down behavior: app degrades with a user-safe message, not a hang
- client loops debounced (input/search handlers don't fire per keystroke);
  re-renders driven by state changes, not whole-list recompute

## Test-isolation & pre-deploy testing

Check:
- system time is mocked in tests that touch dates/deadlines (no flaky
  midnight/timezone tests)
- third-party APIs are mocked/stubbed in the test suite (no live network
  in CI); contract smoke against the real API is a separate, explicit step
- E2E smoke (real browser or full-stack request round-trip) passes before
  any deploy
- load and stress pass before launch: expected peak traffic sustained with
  headroom; the breaking point is known, not discovered in production
- migration rollback tested (down-migration runs clean before the up is
  trusted); backup restore rehearsed (point-in-time recovery proven once
  per project, not assumed)

## Anti-hallucination review

Check:
- every “done” claim has evidence
- Known / Assumed / Unverified are labeled
- no invented files, APIs, packages, or host capabilities
- `./.sps/agent.md`, `profile.md`, and `handoff.md` were updated
- SPS version stamp is present in `agent.md`

## Handoff summary

Always state:
- what was verified
- how it was verified
- what remains manual or unverified
- active agent host
- SPS version
- that `/sps` remains required for this project

## Cleanup / ship gate

Check:
- dead code and unused imports from the slice
- consistent naming and file split
- no circular imports between modules (import graph is acyclic)
- no `console.log` / debug statements or TODO/FIXME markers left in
  shipped source
- no stubbed functions pretending to be done (implemented or feature-flagged)
- lockfile pinned and committed; unused dependencies pruned
- markers for next agent
- secrets not introduced
- workspace hygiene (no duplicate assets)
