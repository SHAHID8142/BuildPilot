# AUDIT-PHASE-07 — P3 Capability Engine, Project Selection and Incident Closure

**Status:** `COMPLETE / VERIFIED / APPROVED`
**Approved by:** User (explicit instruction, 2026-10-03)
**Approval scope:** P3 capability engine + project selection, **including the
documented INCIDENT-P3-001 security closure**.
**Roadmap phase:** P3 (audit phase 07; phases 01-06 exist)
**Date:** 2026-10-03
**Baseline:** `9cc67a7` (P2 approval transition)

**Bounded approval.** Credential revocation is recorded as
`USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED`. Forensic checkpoint `a7767cf`
is `PRESERVED_BY_USER_DECISION` and was **not** purged. This approval
confers **no approval of P4**.

---

## 1. Gate check (all passed before any change)

P1 `APPROVED`; P2 `APPROVED` with `approval_scope.type = RESEARCH_AND_AUDIT`;
P3 `NOT_STARTED` (zero P3 files); working tree `CLEAN` at `9cc67a7`; all six
existing validators passing; legacy diff against `c11da27` empty.

## 2. What P3 implemented

| Artefact | Purpose |
|---|---|
| `sps2/capability/engine.py` | `promote()` gate, `rank()`, `apply_forced_choice()`, `select()`, determinism fingerprint |
| `sps2/capability/registry.json` | Production registry: 5 promoted, 9 deferred/rejected |
| `sps2/project/SELECTION-P3-0001.json` | Project-local selection record produced by the engine |
| `sps2/tools/check_p3.py` | Behavioural validator (registry, selection, gate, records) |
| `sps2/tools/validate-p3.sh` | 9 sections + cases A-O + 2 positive controls |

## 3. Promotion gate

30+ named rules. Rejects: missing fields, bad IDs, malformed lifecycle, unknown
security presented as safe, `FACT` overstatement, permissive licence without
evidence, undeclared licence behind an active state, `COMPATIBLE` without a basis,
non-agent-neutral core, stale without review, stale-as-active, agent-attributed
approval, approval without a decider, lifecycle without approval, global without
authorisation, verification without evidence, fabricated or unclassified
provenance, unknown source references, research-only leakage, malformed records.

## 4. Ranking

Weights: requirement fit 30, compatibility 20, security 20, licence 10,
freshness 8, maintenance 5, provenance confidence 5, verification 2.
**Popularity and recency contribute zero points** and only break exact ties.

Proven: 24 permutations -> 1 fingerprint. A candidate scoring 46.50 with 10,000,000
stars ranked below one scoring 77.80 with 0 stars.

## 5. Forced user choice

An explicit choice moves to rank 1 and records its prior rank. It is refused with
`MANDATORY_SAFECY_CONSTRAINT` when security is `VULNERABLE` or `SUSPECTED_RISK`,
scope is unauthorised `GLOBAL`, or lifecycle is `REJECTED`/`REMOVED`.

## 6. Registry composition

Promoted 5: promotion-gate, deterministic-ranking, forced-user-choice,
staleness-model (governance) and seo-cls-threshold-verifier (seo).

All are project-authored, pure-Python, standard-library-only code whose security
is assessable by static review of in-repository source. The SEO entry carries
`fact_class: FACT` because CLS thresholds were confirmed verbatim in SRC-017;
every other entry is `EVIDENCE` because it rests on this repository's own review.

Deferred 7, rejected 2. Notably deferred: LCP/INP thresholds, CMS content
modelling, the ECC skill library, ECC continuous learning, the agency-agents
persona corpus, the Gemini CLI adapter. Rejected: the ECC desktop dashboard and
the MCP registry as a security control.

## 7. Research gaps preserved

CONF-001 (`LCP`/`INP` thresholds) remains `UNRESOLVED`; CAP-028 remains
`UNVERIFIED` / `RESEARCH_FURTHER`; CMS content modelling and SEO beyond technical
fundamentals remain `RESEARCH_FURTHER`. All asserted by the validator.

## 8. Honest limitations

- **No repository LICENSE file exists.** Capability records state
  `KNOWN_PERMISSIVE` only for project-authored source with explicit evidence; no
  third-party licence was assumed.
- **Provenance is static**, not runtime. `runtime_tracing: false` is asserted.
- **No capability is VERIFIED or ACTIVE.** P3 built the mechanism; verification is
  a later phase. All five remain `CANDIDATE` with `verification: UNVERIFIED`.
- **The security status of the five promoted entries is `VERIFIED_SAFE` only in
  the sense of static review of in-repository source.** No third-party code was
  analysed or executed.

## 9. Validation results

| Validator | Result |
|---|---|
| `validate-p3.sh` | 53 checks, 0 failed, 18 negative/positive controls |
| `validate-p2.sh` | 69 checks, 0 failed, 22 negatives |
| `validate-sps2.sh` | 73 checks, 0 failed, 25 negatives |
| `validate-governance.sh` | 53/53 |
| `validate-control.sh` | 49/49 + 8 negatives |
| `validate-capability.sh` | 55/55 + 16 negatives |
| `lint-sps.sh` | PASS |

Six real validator defects were found and **fixed**, not worked around
(`sps2/tasks/P3-TASKS.md`).

## 10. Protection

Legacy diff against `c11da27`: **empty**. Legacy `.sps/` governance untouched.
No machine-global write. No dependency installed, vendored or locked. No emoji.
No secret introduced.

## 11. Phase state

**P3: `COMPLETE / VERIFIED / APPROVED`** (2026-10-03, explicit user instruction)

Approval is bounded and machine-enforced by `validate-p3.sh` section 3, which
asserts: user attribution on every approval; P4 recorded `NOT_APPROVED`;
revocation recorded as `USER_ATTESTED`; checkpoint `a7767cf` still present; no
capability promoted past `CANDIDATE`; every capability still `PROJECT_LOCAL`.

**P4: `NOT_STARTED / NOT_APPROVED`.** Not begun.