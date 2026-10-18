# QA Report Addendum — windows-smoke root cause #2: caveman (2026-10-18)

Follow-up to QA-2026-10-18-ci-fix-mirror-pins-full-depth.md.

## What happened after the first fix (381f282)
windows-smoke progressed past fact-check (now installs, `done 5s` — root
cause #1 confirmed fixed in CI), then failed at step 27/29: **caveman**.
Reproduced locally: `npx skills add https://github.com/mattpocock/skills
--skill caveman` → "No matching skills found" (38 skills available).

## Root cause
Upstream author **deliberately deleted** the caveman skill — mattpocock/skills
CHANGELOG: "Remove the caveman and zoom-out skills… caveman was a duplicate
of another skill I was testing and was never meant to be public." Unlike the
fact-check case (depth issue, fixable with --full-depth), this skill no
longer exists anywhere in the repo's history chain reachable by the CLI.

## Fix (commit e766bfc)
- Removed caveman from both installers: extras skill list + ExtrasStep/
  extras_step lines (install.sh, install.ps1).
- Step totals: TotalSteps 28→27 (install.ps1), TOTAL_STEPS 28→27 (install.sh).
- Both installers re-pinned in the legacy manifest; canonical hash chain
  advanced bc770093… → **3e6f298b…** (6th chain advance this session).
- Full battery 1268 OK; governance suites 56 OK; P2 validator 69/0;
  pwsh syntax PASS; bash -n PASS.

## Lesson (proposed for LESSONS.md)
Third-party extras are a moving floor: upstream repos can rename, restructure,
or delete skills at any time. The extras list needs a periodic upstream check
(candidate for the weekly-audit workflow), and each extras failure should be
triaged as: depth issue (→ --full-depth), rename (→ follow the rename), or
deletion (→ remove from our list, as with caveman).
