# /sps Audit Mode

Use this file for:

1. explicit `/sps audit` requests
2. **legacy project onboarding** when a project has never used `/sps` before
3. any read-only compliance check against SPS rules

## Goal

Inspect the current project, compare it to SPS rules, score alignment out of
100, write the full report to `./.sps/audit-report.md`, and show the same
report to the user. Do not implement fixes until the user approves a
remediation path.

## CMS debt

If CMS is enabled or suspected, also write/update `./.sps/cms-debt.md` and
recommend `/sps sync` for remediation.

## When audit is mandatory

Treat the project as **legacy / first SPS contact** when any of these are true:

- `./.sps/` does not exist
- `./.sps/profile.md` exists but has no real project identity / rules filled in
- handoff shows the project has never completed an SPS discovery or audit
- the user says this is an old project and wants SPS alignment

On first SPS contact:

1. Bootstrap `./.sps/` from templates (or `scripts/bootstrap-sps.sh`)
2. Write active host + SPS version into `./.sps/agent.md`
3. Lock `/sps` as required for this project
4. Run the full scored alignment audit below
5. Write the full report to `./.sps/audit-report.md`
6. Save a short summary + score into `./.sps/handoff.md`
7. **Stop and show the report before building anything**

Even if the user asked to “build X”, the first response on a legacy project is
the audit report plus a choice of next actions.

## Required investigation

Do not invent the project. Read evidence from:

1. repo structure (package manifests, app folders, CMS/config files)
2. main UI entry routes / layouts / components when present
3. styling / motion / asset usage patterns
4. existing README or docs if present
5. `./.sps/` memory after bootstrap

If something cannot be verified, mark it **Unverified** and do not award full
points for that item.

## Scored checklist (100 points)

Score every item as:

- **Pass** = full points
- **Warning** = half points (rounded down)
- **Fail** or **Unverified with risk** = 0 points

| ID | Category | Check | Points |
|---|---|---|---|
| A1 | Memory | `.sps/` bootstrapped | 3 |
| A2 | Memory | `/sps` lock present | 3 |
| A3 | Memory | `agent.md` has host + version stamp | 3 |
| A4 | Memory | profile / handoff usable | 2 |
| A5 | Memory | root mirrors (`AGENTS.md`/`GEMINI.md`/`CLAUDE.md`) point to `/sps` | 3 |
| B1 | Understanding | project type inferred with evidence | 4 |
| B2 | Understanding | stack detected with evidence | 4 |
| B3 | Understanding | CMS / storefront / ERP / admin checked | 4 |
| B4 | Understanding | deploy target/method + team/multi-agent notes | 4 |
| C1 | Honesty | no fake certainty in the report | 3 |
| C2 | Honesty | Known / Assumed / Unverified filled | 3 |
| D1 | Mobile | responsive approach present or planned | 6 |
| D2 | Mobile | no hover-only critical action risk (or mitigated) | 4 |
| D3 | Mobile | no heavy / laggy mobile motion risk (or mitigated) | 6 |
| D4 | Mobile | dual path decision recorded when needed | 3 |
| E1 | Assets | media risks + workspace hygiene reviewed | 5 |
| E2 | Assets | autoplay / weight policy reviewed | 3 |
| F1 | Quality | lint/test/build scripts exist or absence noted | 4 |
| F2 | Quality | deployability blockers stated | 3 |
| F3 | Quality | accessibility basics reviewed | 3 |
| H1 | CMS | if CMS enabled: foundation present or debt listed | 8 |
| H2 | CMS | if CMS enabled: no silent storefront-only “done” sections (debt tracked) | 8 |
| H3 | Design | design-gate risks noted (eyebrows/separators/palette/slop) | 4 |
| G1 | Workflow | remediation can continue section-by-section / `/sps sync` | 4 |
| G2 | Workflow | top remediation chunks ordered by risk | 3 |

**Total = 100**

If CMS is not part of the project, award H1/H2 full points only when the audit
explicitly proves CMS is out of scope (not when CMS was simply ignored).

### Score bands

| Score | Band | Meaning |
|---|---|---|
| 90–100 | Strong | Aligned enough to proceed carefully |
| 70–89 | Mixed | Proceed only with explicit remediation plan |
| 40–69 | Weak | Fix Fail items before major feature work |
| 0–39 | Critical | Stabilize basics first |

## Output + file write (required)

1. Show the report in chat.
2. Write the **same full report** to `./.sps/audit-report.md` (overwrite latest).
3. Update `./.sps/handoff.md` with score, band, date, and waiting choice.

```markdown
## SPS Audit Report

Date:
Project status: legacy first contact | existing SPS project
Scope: full alignment | focused
Active agent:
SPS version:

### Score
- Total: 72/100
- Band: Mixed
- Pass points:
- Warning points:
- Fail / unpaid points:

### Scored checklist
| ID | Result | Points awarded | Notes |
|---|---|---|---|
| A1 | Pass | 3 | ... |
| D3 | Fail | 0 | ... |

### Project snapshot
- Type:
- Stack (Known/Assumed/Unverified):
- CMS / storefront / ERP / admin:
- UI surfaces reviewed:

### Pass
- ...

### Fail
- ...

### Warnings
- ...

### Evidence
- Known:
- Assumed:
- Unverified:

### Recommended remediation order
1. ...
2. ...
3. ...

### Choose next step
1. Remediate Fail items section-by-section under `/sps`
2. Continue my original request after accepting this baseline
3. Audit only — do nothing else yet
4. Ask discovery questions before any remediation
```

## Rules

- Read-only until the user chooses a next step
- Prefer evidence over opinion
- Always compute and show the `/100` score
- Always write `./.sps/audit-report.md`
- Mark Unverified items clearly
- Do not silently start coding after the report
- Update `./.sps/handoff.md` with:
  - audit date
  - score + band
  - project status
  - top Fail / Warning counts
  - path to `./.sps/audit-report.md`
  - waiting-for-user choice
- For explicit `/sps audit` on an already-SPS project, still produce the scored
  report and write `audit-report.md`
