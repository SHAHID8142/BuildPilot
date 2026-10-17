# T-19 Plan: Nightly Skill-Ecosystem Scan

## Goal
Automated nightly check for better-maintained skills per routed domain.
Report-only — never installs (TOOL-CONSENT.md), zero CI minutes (DEPLOY-BUDGET.md).

## Approach (per approved design)
1. scripts/ecosystem-scan.sh (+ mirror): 13-domain scan — upstream freshness,
   candidate search (GitHub + skills.sh, throttled), 6 vetting gates
   (recency ≤90d, not archived, repo age ≥30d, stars ≥50 | installs ≥200,
   license present, SKILL.md red-flag screen), conflict-ban rejects.
   Output: dated report reports/ecosystem/ + stdout REPORT_FILE/PROPOSALS_COUNT.
2. .github/workflows/ecosystem-scan.yml: cron "17 3 * * *" + workflow_dispatch,
   commits report with [skip ci] (verified: sps-ci.yml is the only workflow and
   has no path filters, so the trailer fully suppresses it), deduped tracking
   issue (label ecosystem-scan), max-3-issues cap, 90-day artifact.
3. ecosystem-domains.tsv (+ mirror): the 13 routed domains from SKILL-ROUTER.md.

## Gates
- Section DoD applies (script ≤500 lines, no stubs, cleanup gate)
- Manifest pinning by orchestrator after build (new scripts/ files)
- Live smoke: real scan run must produce a complete 13-domain report
- Full battery + validators + CI before merge

## Out of scope
- Any auto-install path (permanently — the scan proposes, humans dispose)
