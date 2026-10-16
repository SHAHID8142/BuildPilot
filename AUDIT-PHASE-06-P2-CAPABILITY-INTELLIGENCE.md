# AUDIT-PHASE-06 — P2 Capability Intelligence, Ecosystem Research and Comparative Audit

**Status:** `COMPLETE / VERIFIED / AWAITING_USER_APPROVAL`
**Roadmap phase:** P2 (the next available audit-phase number; phases 01-05 exist)
**Date:** 2026-10-03
**Baseline:** `2eef3d2` (P1 approval transition)

This was a **research and audit phase**. No SPS 2.0 capability was implemented.

---

## 1. Scope performed

- Gate check: P1 APPROVED, working tree clean, all validators passing, legacy diff
  empty, phase numbering confirmed (01-05 exist, therefore 06).
- 20 ranked primary sources collected and inspected **statically**.
- 36 atomic capabilities extracted with evidence, status, confidence and a
  taxonomy recommendation.
- 10 interoperability records across 8 harnesses.
- 5 audit documents written; 1 final report (this file).
- P2 validator created with 22 negative cases and a positive control.
- **Nothing installed. No external code executed. No legacy file touched.**

## 2. Central finding

The ecosystem is rich in *packaging breadth* and poor in *enforcement portability*.
ECC ships fourteen harness directories, but no source demonstrates behavioural
parity between them. Every harness reimplements config precedence differently.
Every harness ships a machine-global layer that risks cross-project contamination.

Meanwhile the one genuinely convergent standard is **AGENTS.md**, now stewarded
under the Linux Foundation's Agentic AI Foundation.

SPS 2.0's position: keep the portable instruction surface, keep validators as the
load-bearing enforcement layer, refuse to assume parity, and never let research
findings leak into the production registry.

## 3. Six claims, each evidence-backed

1. **Portability primitive exists** — AGENTS.md (SRC-014).
2. **Cross-harness support is packaging, not parity** (SRC-001, SRC-004, SRC-010).
3. **Enforcement differs most by harness; SPS is strongest** (SRC-006, SRC-008,
   SRC-009, SRC-010).
4. **MCP registry is provenance, not security** (SRC-012, SRC-013).
5. **A persona catalogue is not an orchestration system** (SRC-003 vs SRC-015).
6. **Memory should be an artefact, not a behaviour** (SRC-002, SRC-015).

## 4. Recommendations issued

| Taxonomy | Count |
|---|---|
| KEEP | 8 |
| ADAPT | 19 |
| REWRITE | 2 |
| REPLACE | 0 |
| RESEARCH_FURTHER | 3 |
| REJECT | 2 |
| DEFER | 2 |
| **Total** | **36** |

`REPLACE` is unused: no system was found to be a strictly superior mechanism for a
capability SPS needs. Recording an empty category is more honest than forcing a
fit.

## 5. Decisions requiring approval

DEC-0011 (adopt AGENTS.md) · DEC-0012 (hooks are never the enforcement layer) ·
DEC-0013 (MCP provenance yes, MCP security no) · DEC-0014 (no unverified numeric
thresholds in verifiers) · DEC-0015 (continuous learning becomes evidence-gated
proposal). All `PENDING_USER_APPROVAL`.

## 6. Discrepancies and honest gaps

| Gap | Handling |
|---|---|
| LCP / INP numeric thresholds not retrieved (CONF-001) | Left `UNRESOLVED`; CAP-028 held at `RESEARCH_FURTHER`; DEC-0014 forbids encoding them |
| CMS content-modelling depth not researched (Contentful returned HTTP 429) | CAP-032 `RESEARCH_FURTHER`; T-10 marked PARTIAL |
| Gemini CLI native docs returned HTTP 404 | Recorded as unstudied; not guessed |
| Codex advanced config reference is a 15-line pointer | Recorded as a pointer, not treated as the reference |
| ECC verification-loop internals not source-audited | Confidence held at MEDIUM; `RESEARCH_FURTHER` |
| Anthropic 90.2% uplift is vendor-internal | Confidence MEDIUM, labelled internal, not presented as independent |
| SEO beyond technical fundamentals not researched | Not claimed |

## 7. Legacy protection

`git diff c11da27 -- skills scripts plugins .github templates README.md CHANGELOG.md CATALOG.md`
is **empty**. Verified before and after P2, and asserted by the validator.

## 8. Machine-global protection

No writes to `~/.claude`, `~/.codex`, `~/.config`, `~/.sps`, no global Git
configuration, no shell profile changes, no PATH changes, no packages, no
installers. Asserted by validator section 7.

## 9. No emoji

All P2 artefacts pass the repository-wide emoji scan.

## 10. Validators

| Validator | Result |
|---|---|
| `validate-p2.sh` (full) | 61 checks, 0 failed, 22 negative cases, 0 missed |
| `validate-p2.sh --negative` | 22 negative cases, 0 missed |
| `validate-sps2.sh` (P1) | 73 checks, 0 failed, 25 negatives |
| `validate-governance.sh` | 53/53 |
| `validate-control.sh` | 49/49 + 8 negatives |
| `validate-capability.sh` | 55/55 + 16 negatives |
| `lint-sps.sh` | PASS |

Three real validator defects were found and **fixed** during P2 (not worked
around): the ISO-timestamp parser, a truncated negative-case argument, and a
missing conflict block. Detection was re-proved after each fix.

## 11. Registry protection

`sps2/capability/registry.json` remains **empty**. All 36 extracted capabilities
carry `in_production_registry: false`, asserted by the validator. Research
findings stay in `sps2/research/`.

## 12. Phase state

**P2: `COMPLETE / VERIFIED / AWAITING_USER_APPROVAL`**

P2 was **not** self-approved. P3 has **not** started. Only the user can approve P2.

---

## Verdict

P2 established an evidence-backed baseline without fabricating anything, without
installing anything, and without touching the legacy repository. The three
deliberate research gaps are recorded as gaps rather than papered over with
assumed values — which is precisely the behaviour SPS 2.0 exists to enforce.