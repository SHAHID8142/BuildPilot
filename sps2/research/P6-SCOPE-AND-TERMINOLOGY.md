# P6 — Technology Research: Scope and Terminology

Authoritative source: `.sps/architecture/SPS2-ROADMAP.md`, section **P6 — Technology Research**.

Decisions resolving the blocking questions:

- **D-P6-1** — P6 means the **roadmap** definition: Technology Research.
- **D-P6-2** — Runtime activation is **NOT APPROVED**.

This document converts `AUDIT-P6-READINESS-AND-DECISION.md` into the
authoritative P6 scope and separates six things that must never be conflated.

---

## 1. The six distinct layers

### 1.1 Roadmap-defined P6 research (IN SCOPE NOW)

The research gate that blocks use of an unresearched technology.
Roadmap deliverables: **workflow**, **cache schema**, **readiness evaluator**.
Roadmap acceptance: selection for a technology with `readiness != SUFFICIENT`
is rejected. Roadmap forbidden: auto-accepting `INSUFFICIENT` readiness.

### 1.2 Previously completed P2 research (DONE — NOT P6)

P2 produced capability intelligence and audits under `sps2/research/`:
`P2-CAPABILITY-MATRIX.json`, `P2-ECOSYSTEM-MAP.md`, `P2-SOURCES.json`,
`P2-CMS-SEO-AUDIT.md`, `P2-SECURITY-AUDIT.md` and related files. DEC-0011 to
DEC-0015 record its decisions.

**P2 research is not P6 research.** P2 investigated *what exists*. P6 builds
the *gate that refuses to proceed without sufficiency*. P2 already created the
empty cache mechanism; P6 populates it and evaluates it. Neither replaces the
other.

### 1.3 Unresolved research gaps (CARRIED, NOT CLOSED BY P6)

`CONF-001` — LCP and INP numeric thresholds. P6 re-attempted retrieval; see
section 4. It remains **UNRESOLVED**. P6 records evidence; it does not close
conflicts, because closing one is a User decision.

### 1.4 Technology readiness evaluation (IN SCOPE NOW)

A pure-logic evaluator over the research cache. It classifies readiness and
**refuses** to treat anything below `SUFFICIENT` as selectable.

### 1.5 Future production implementation (NOT IN SCOPE)

Building CMS, SEO, vertical slices, deployment. That is roadmap P8 onward and
requires its own approvals. P6 produces findings and recommendations only.

### 1.6 Future runtime activation (EXPLICITLY NOT APPROVED)

Per D-P6-2, not implemented and not designed here: no `ACTIVE` or `INSTALLED`
lifecycle, no resident runtime, no supervisor or daemon, no background process,
no global runtime binding, no automatic activation, no machine-global install.

---

## 2. Explicit discrepancies — recorded, not reconciled

These are **not** silently reconciled. The roadmap numbering and the executed
history use the same numbers for different work.

| Roadmap phase | Roadmap title | Executed here as | Status |
|---|---|---|---|
| P1 | Repository Foundation | P1 Repository Foundation | aligned |
| P2 | Core Orchestration & Governance | P2 Capability Intelligence (research) | **numbering conflict** |
| P3 | Agent Interoperability | P3 Production Capability (promotion) | **numbering conflict** |
| P4 | Capability Discovery | P4 Production Promotion | **numbering conflict** |
| P5 | Dynamic Skill Selection | P5 Implementation / Integration | **partial overlap** |
| P6 | Technology Research | this phase | **authoritative** per D-P6-1 |

Consequences recorded rather than resolved:

- Roadmap P3 (real adapters, portability suite) is **not** satisfied. Only the
  `generic` adapter exists at maturity `DECLARED`.
---

## 3. P6 boundaries

Permitted: research records, cache entries with attributed evidence, the
readiness evaluator, the research workflow description, P6 governance records,
validators and tests.

Forbidden: installing any dependency, skill, MCP, CLI or package; promoting any
capability; creating runtime lifecycle semantics; modifying machine-global
state; modifying legacy SPS files; inventing LCP/INP thresholds; inferring
missing technology facts; self-approving P6; starting P7.

**No technology fact may be inferred from model knowledge.** If a fact was not
observed in an attributed source, it is recorded `UNKNOWN` and the readiness
classification reflects that.

---

## 4. CONF-001 — P6 retrieval attempt

P6 re-attempted the retrieval that P2 could not complete.

- Attempt 1, `web.dev/articles/vitals`: retrieved successfully, but the numeric
  threshold table was **again absent** from the static content. The page
  confirms the Core Web Vitals set is LCP, CLS and INP, and is a Google
  initiative (last updated 2024-10-31).
- Attempt 2, `web.dev/articles/defining-core-web-vitals-thresholds` (the
  official methodology page, last updated 2025-05-07): retrieved successfully.

From attempt 2, **verbatim**:

- CLS good: "we conclude that, while many origins meet the 0.05 threshold, the
  slightly less stringent CLS threshold of **0.1** strikes a better balance
  between quality of experience and achievability."
- CLS poor: "For a **0.25** threshold, roughly 20% of phone origins, and 18% of
  desktop origins, would be classified as 'poor'. This falls in our target
  range of 10-30%, so we concluded that 0.25 is an acceptable 'poor' threshold."
- CLS mid-point: "levels of shift from **0.15** and higher were consistently
  perceived as disruptive, while shifts of 0.1 and lower were noticeable but
  not excessively disruptive."

**Result: CLS is now independently confirmed from a rank-1 official source and
agrees with SRC-017. LCP and INP numeric thresholds were still not observed**;
their derivation sections fall outside the retrieved content.

**CONF-001 therefore remains UNRESOLVED for LCP and INP.** P6 does not close it.
No LCP or INP figure is recorded anywhere in this phase.

---

## 5. Readiness classification vocabulary

| Level | Meaning | Selectable? |
|---|---|---|
| `SUFFICIENT` | all ten coverage areas covered, with a source of rank <= 4 | yes |
| `PARTIAL` | some coverage, or only weak sources | **no** |
| `INSUFFICIENT` | evidence exists but is inadequate, or a conflict blocks it | **no** |
| `UNRESEARCHED` | no research entry exists | **no** |

Only `SUFFICIENT` may be selected. This mirrors the gate already defined in
`sps2/research/cache.json` and is enforced by the P6 readiness evaluator.
- Roadmap P5's "staleness monitor (report-only)" is partially realised through
  `staleness` fields and validators, not as a named component.
- Roadmap P7 (project-local state and memory) is **not started** and is
  explicitly out of scope here.

Reconciling the numbering is a User decision and is **not** assumed.