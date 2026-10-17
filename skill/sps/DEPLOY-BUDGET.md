# Deploy Budget Law (Batch, Verify Locally, Deploy Once)

**Law:** CI/CD minutes are a budget. Fixes are BATCHED, validated locally,
and deployed ONCE — never deploy-per-fix.

## The rule

1. **Batch, don't trickle.** When verification finds multiple problems:
   fix ALL of them first, run the full local battery, and push/CI once as
   a single change set. Never push after each individual fix.
2. **Local verification before any remote run.** Everything that can be
   checked locally MUST be checked locally first: full test suite, lint,
   build, validators, smoke scripts. A push is only worth CI minutes when
   every local check is green.
3. **Deploy gates.** A deploy (or any workflow that costs minutes) runs
   only when: (a) all local checks pass, (b) the change set is complete
   (no known pending fix left out), and (c) the user's deploy policy
   authorizes it. If a fix is found during CI, finish the whole batch
   locally before the next push.
4. **One push = one CI run = one verdict.** If CI still fails, fix
   everything found in that run, re-verify locally, then push once more.
   The pattern "push, fail, push, fail" is a budget violation — stop and
   reproduce the failure locally first.
5. **Cheap triggers first.** Prefer local scripts and pre-push hooks over
   CI. Reserve CI for what genuinely needs it (OS matrix, integration).
6. **Report the budget.** In the handoff, state how many CI runs the work
   consumed and why that was the minimum.

## Anti-pattern (forbidden)

> Find bug A → fix A → push → CI fails on bug B → fix B → push → …

## Required pattern

> Find A, B, C → fix A+B+C → full local battery green → single push → CI →
> (if red) fix all findings → local battery green → single push
