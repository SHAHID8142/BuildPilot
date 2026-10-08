# SPS 2.0 — Implementation Roadmap

**Phase:** `PHASE-05` · **Status:** `AWAITING_USER_APPROVAL`
Each phase is isolated, independently approvable, independently revertible. **Not started.**

Every phase specifies: objective · dependencies · scope · **forbidden scope** · deliverables · acceptance
criteria · verification · approval gate · rollback.

---

## P1 — Repository Foundation

- **Objective:** Create the SPS 2.0 repository skeleton, CI, and version/provenance rules.
- **Dependencies:** Phase 05 approval.
- **Scope:** repo tree, README, VERSION, LICENCE, `.github/workflows`, lint baseline.
- **Forbidden:** any SPS behaviour; any migration of legacy files.
- **Deliverables:** valid structure; CI running; `docs/adr/0001-record-architecture-decisions.md`.
- **Acceptance:** CI green on an empty framework; core validator passes with **no adapter installed**.
- **Verification:** CI run captured as evidence. **Approval:** user.
- **Rollback:** delete the new repository — nothing else exists yet.

## P2 — Core Orchestration & Governance

- **Objective:** Port the validated Phase 02–04 governance layer.
- **Dependencies:** P1. **Scope:** `core/`, `governance/`.
- **Forbidden:** capability discovery; domain subsystems; adapters beyond `generic`.
- **Deliverables:** JSON Schemas; migrated validators; conformance suite.
- **Acceptance:** every Phase 02–04 negative case still passes; no vendor string in `core/`.
- **Verification:** conformance suite ≥ 24 negative cases, all rejected. **Approval:** user.
- **Rollback:** revert to P1 tag.

## P3 — Agent Interoperability

- **Objective:** Prove portability with real adapters.
- **Dependencies:** P2. **Scope:** `core/adapters/` contract + adapters.
- **Forbidden:** adapters adding or weakening core rules.
- **Deliverables:** `contract.schema.json`; adapters; conformance test.
- **Acceptance:** deleting **all** adapters leaves core validators passing; a fresh agent can resume the
  project from `.sps/` alone.
- **Verification:** portability suite (4 criteria, `SPS2-AGENT-INTEROPERABILITY.md` §7). **Approval:** user.
- **Rollback:** delete adapters; core unaffected.

## P4 — Capability Discovery

- **Objective:** Implement discovery/evaluation/ranking with **no** installation yet.
- **Dependencies:** P2, P3. **Scope:** `capability/`.
- **Forbidden:** any installation; any global write; live network in CI.
- **Deliverables:** discovery engine; ranking; registry schema; threat model.
- **Acceptance:** ≥2 candidates per domain; every criterion scored or explicitly `UNKNOWN`; security
  `UNKNOWN` blocks activation.
- **Verification:** negative suite. **Approval:** user before installation capability is enabled.
- **Rollback:** disable discovery; registry stays empty.

## P5 — Dynamic Skill Selection

- **Objective:** Recommend → approve → install **project-locally** → verify → re-evaluate.
- **Dependencies:** P4. **Forbidden:** global install without explicit user authorisation.
- **Deliverables:** selection workflow; provenance records; staleness monitor (report-only).
- **Acceptance:** a selection is reproducible from the registry alone; global install rejected without
  user authorisation.
- **Verification:** negative tests for global-scope abuse and self-approval. **Approval:** user (L3).
- **Rollback:** deactivate capabilities; retain registry history.

## P6 — Technology Research

- **Objective:** Research gate blocking use of an unresearched technology.
- **Dependencies:** P4. **Forbidden:** auto-accepting `INSUFFICIENT` readiness.
- **Deliverables:** workflow; cache schema; readiness evaluator.
- **Acceptance:** selection for a technology with `readiness != SUFFICIENT` is rejected.
- **Verification:** negative test. **Approval:** user.
- **Rollback:** disable gate; advisory only.

## P7 — Project-Local State & Memory

- **Objective:** Consolidate project memory; retire global memory.
- **Dependencies:** P2, P3. **Forbidden:** writing state outside the project.
- **Deliverables:** memory layout; team bootstrap; isolation validator.
- **Acceptance:** two projects remain isolated; a new teammate understands the project from the repo alone.
- **Verification:** isolation tests + onboarding dry run. **Approval:** user.
- **Rollback:** revert memory layout.

## P8 — CMS 2.0

- **Objective:** CMS with Super Admin / Admin separation and a unified asset picker.
- **Dependencies:** P5, P6, P7. **Scope:** `domain/cms/`; roles; content/section model; media; preview;
  publishing; audit history.
- **Forbidden:** copying `KI-01` (hardcoded secret); exposing layout controls to Admins.
- **Deliverables:** architecture + reference implementation + schema.
- **Acceptance:** Super Admin keeps structural control; Admin cannot break layout; asset picker supports
  upload / existing media / external URL (validated, fetched, optimised, stored locally).
- **Verification:** role-permission tests; vertical-slice integration test.
- **Approval:** user; **security review mandatory**.
- **Rollback:** feature flag; removable without touching the core.

## P9 — SEO 2.0

- **Objective:** Build a real SEO subsystem (legacy has **none** — only a phantom dependency).
- **Dependencies:** P8, P5. **Scope:** technical SEO, metadata, canonical, robots, sitemap, structured
  data, OG/social, headings, internal linking, image SEO, CWV, redirects, URL architecture, pagination,
  i18n/local/ecommerce as applicable, pre-deployment audit.
- **Forbidden:** shipping without a pre-deployment audit step.
- **Deliverables:** methodology, validator, audit tool.
- **Acceptance:** every listed dimension has a check or an explicit N/A rationale.
- **Verification:** SEO validator + audit report as evidence. **Approval:** user.
- **Rollback:** advisory; disabling must not break builds.

## P10 — Vertical-Slice Frontend/Backend

- **Objective:** Every completed section is functional, editable, connected, tested, SEO-aware.
- **Dependencies:** P8, P9. **Scope:** `domain/frontend/`, `domain/backend/`, `domain/shared/`.
- **Forbidden:** "frontend now, CMS later" sequencing.
- **Deliverables:** slice schema; per-slice DoD; integration harness.
- **Acceptance:** a section is not done until frontend + CMS + backend + data + validation + assets +
  SEO + tests pass together.
- **Verification:** slice conformance suite. **Approval:** user per slice.
- **Rollback:** per-slice revert.

## P11 — Security Controls

- **Objective:** Machine-checkable security controls against agent drift.
- **Dependencies:** P2, P4, P8. **Scope:** `domain/security/`; dependency scanning; permission budgets;
  secret detection; complexity/dead-code thresholds; state-location enforcement.
- **Forbidden:** claiming a control with no negative test.
- **Deliverables:** security validators; drift detectors; pre-commit hooks.
- **Acceptance:** each control has a negative test that fails when violated.
- **Verification:** negative suite. **Approval:** user; security review mandatory.
- **Rollback:** controls are additive; disabling reverts to Phase 01 behaviour.

## P12 — Testing

- **Objective:** Verification contract, independence, evidence integration.
- **Dependencies:** P2, P10, P11. **Scope:** `domain/testing/`; verifier classes; independence rules;
  CI matrix.
- **Forbidden:** treating agent self-assessment as independent verification.
- **Deliverables:** verification contract; CI matrix; evidence integration.
- **Acceptance:** HIGH/CRITICAL work cannot be signed off by an agent alone.
- **Verification:** independence enforcement tests. **Approval:** user.
- **Rollback:** revert CI matrix.

## P13 — Deployment Readiness

- **Objective:** Deployment and rollback readiness with evidence.
- **Dependencies:** P9–P12. **Scope:** `domain/deployment/`; build/verify/env validation; rollback.
- **Forbidden:** deploying without a verified rollback path.
- **Deliverables:** deployment checklist; rollback contract; preview verification.
- **Acceptance:** `rollback_verified: true` required for CRITICAL actions.
- **Verification:** deployment drill in a non-production environment.
- **Approval:** user; Level 4 HARD_GATE.
- **Rollback:** the rollback contract itself.

## P14 — Migration Execution

- **Objective:** Execute the migration matrix against legacy.
- **Dependencies:** P1–P13. **Scope:** import `KEEP`/`REFACTOR` per matrix with provenance.
- **Forbidden:** copying `NEVER COPY` or unreviewed `RESEARCH FIRST` items.
- **Deliverables:** migrated framework; `legacy/MANIFEST.md`; parity report.
- **Acceptance:** every migrated artefact has origin, licence, disposition and validation record.
- **Verification:** parity tests vs Phase 02–04 behaviour. **Approval:** user, per batch.
- **Rollback:** revert to the legacy-final tag; SPS 2.0 is additive.

## P15 — Compatibility Testing

- **Objective:** Prove portability across agents and platforms.
- **Dependencies:** P3, P14. **Scope:** agent × OS × project-shape matrix; adapter conformance.
- **Forbidden:** claiming support for an untested combination.
- **Deliverables:** compatibility matrix with evidence per cell.
- **Acceptance:** core passes with zero adapters; unknown agent degrades to `generic`.
- **Verification:** automated portability suite + documented manual cells. **Approval:** user.
- **Rollback:** mark unsupported cells explicitly rather than failing silently.

## P16 — Production Hardening

- **Objective:** Release readiness for team adoption.
- **Dependencies:** P1–P15. **Scope:** performance; release process; documentation; runbook; support.
- **Forbidden:** releasing with an unresolved `NEVER COPY` or unmitigated `CRITICAL` finding.
- **Deliverables:** release checklist; runbook; support process; final audit.
- **Acceptance:** all gates green; all `RESEARCH FIRST` resolved; no open `CRITICAL`.
- **Verification:** full CI + final security review + final audit. **Approval:** user; Level 4.
- **Rollback:** release rollback procedure.

---

## Sequencing

```
P1 foundation -> P2 core+governance
                  |-> P3 interop
                  |-> P4 discovery -> P5 selection -> P6 research
                  |-> P7 memory
P5+P6+P7 -> P8 CMS -> P9 SEO -> P10 vertical slices
P2+P4+P8 -> P11 security
P2+P10+P11 -> P12 testing
P9..P12 -> P13 deployment
P1..P13 -> P14 migration -> P15 compatibility -> P16 hardening
```

**P1–P2 are the critical path.** Nothing later can be validated before the governance core exists and is
proven portable.