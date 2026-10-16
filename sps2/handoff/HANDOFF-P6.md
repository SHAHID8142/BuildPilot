# HANDOFF-P6 — Technology Research

Phase: **P6 — Technology Research** (authoritative roadmap definition, per D-P6-1).
Status: **IMPLEMENTED, VERIFIED and APPROVED** (User, 2026-10-04).
Approval scope: `TECHNOLOGY_RESEARCH_ONLY`.

P6 was not self-approved. The recorded approval was given explicitly by the
User in session and is attributable to them.

---

## 1. What was built

| Roadmap deliverable | Artefact |
|---|---|
| Research workflow | `sps2/research/P6-SCOPE-AND-TERMINOLOGY.md` |
| Cache schema | `sps2/research/cache.json` (`sps2.research/v1`, populated) |
| Readiness evaluator | `sps2/core/technology_readiness.py` |

The gate rule already existed from P1 and was honoured, not reinvented:
*a technology must not be selected until a research entry exists with
readiness SUFFICIENT*.

## 2. Research findings

Three technologies researched. Readiness is **computed** from evidence by the
evaluator, never read from a stored label.

| Technology | Readiness | Selectable | Why |
|---|---|---|---|
| TECH-PYTHON-STDLIB | SUFFICIENT | yes | 10/10 coverage, sources rank 2 |
| TECH-WEB-VITALS | INSUFFICIENT | **no** | blocked by unresolved CONF-001 |
| TECH-SPS-CMS | PARTIAL | **no** | 6 of 10 coverage areas researched |

An unresearched technology is `UNRESEARCHED` and not selectable.

## 3. CONF-001 — re-attempted, still unresolved

- `web.dev/articles/vitals` retrieved: numeric table **again absent**.
- `web.dev/articles/defining-core-web-vitals-thresholds` retrieved: CLS figures
  obtained **verbatim** from a rank-1 official source and they **agree with
  SRC-017**, independently confirming the P2 record.
- **LCP and INP thresholds remain NOT OBSERVED** after two further attempts.

No LCP or INP figure is recorded anywhere in this repository. CONF-001 remains
UNRESOLVED, and P6 does not close it: closing a conflict is a User decision.

## 4. D-P6-2 boundaries held

No ACTIVE lifecycle, no INSTALLED lifecycle, no resident runtime, no supervisor
or daemon, no background process, no global runtime binding, no automatic
activation, no machine-global installation. All four production capabilities
remain `EVALUATED`. CAP-P03-005 remains `DEFERRED / NOT_PROMOTED`. P7 not
started.

## 5. Record-integrity and validator work

- The obsolete P5 invariant "no `P6*` artefact may exist" was **replaced** with
  a phase-aware invariant that permits P6 only under a User-attributed
  decision and additionally asserts runtime, promotion count, CAP-005 deferral
  and P7 absence. It checks strictly more than the invariant it replaced.
- `governance/attribution.py` previously required `decided_on`, which the
  repository's own decision records do not use. Corrected to accept `decided_at`
  as well. Attribution is still judged on WHO and WHEN.

## 6. What the approval does NOT permit

The approval is limited to the completed P6 research work. It explicitly
withholds: inventing LCP or INP thresholds, resolving CONF-001, promoting any
capability, runtime activation, installing anything, beginning P7, legacy
modification, machine-global changes, purging checkpoint a7767cf, rewriting
history, and force-pushing. P7 remains NOT_APPROVED and NOT_STARTED.

## 7. Remaining decisions for a future phase

1. Approve or rework the six P6 requirements.
2. Whether to close CONF-001 now that CLS is independently confirmed but LCP
   and INP are still not observed. It cannot be closed on CLS alone.
3. Whether to fund further research on TECH-SPS-CMS (currently PARTIAL) or on
   any technology intended for roadmap P8.
4. Whether the roadmap-versus-executed numbering discrepancy should be
   reconciled, and how.

## 7. Statement of restraint

Nothing was installed. Nothing was activated. No capability was promoted. No
LCP or INP threshold was invented. No legacy file was modified. No machine
global state was written. No P7 work was started. The credential was not read,
printed, hashed or transmitted.

**Stopping here and awaiting User approval.**