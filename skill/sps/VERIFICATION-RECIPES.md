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
- markers for next agent
- secrets not introduced
- workspace hygiene (no duplicate assets)
