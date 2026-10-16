# AUDIT-PHASE-05 — SPS 2.0 Repository Architecture & Migration Planning

**Phase:** `PHASE-05` · **Date:** 2026-10-03
**Repository:** legacy SPS (preserved) · **Status:** `COMPLETE` · `VERIFIED` · **`AWAITING_USER_APPROVAL`**

> **Planning only.** No SPS 2.0 implementation, no legacy modification, no install, no remote.

---

## 1. Executive Summary

Forensic analysis of the legacy system plus a complete migration architecture for SPS 2.0 as an
**orchestration and control framework** rather than a single skill.

| Deliverable | Path |
|---|---|
| Repository architecture (22 concerns) | `.sps/architecture/SPS2-REPOSITORY-ARCHITECTURE.md` |
| Data flow (control + capability) | `.sps/architecture/SPS2-DATA-FLOW.md` |
| Agent interoperability | `.sps/architecture/SPS2-AGENT-INTEROPERABILITY.md` |
| Global vs project-local | `.sps/architecture/SPS2-GLOBAL-VS-LOCAL.md` |
| Migration matrix (39 components) | `.sps/architecture/SPS2-MIGRATION-MATRIX.md` |
| Roadmap (16 isolated phases) | `.sps/architecture/SPS2-ROADMAP.md` |
| Requirements (17) / Evidence (8) | `.sps/requirements/`, `.sps/evidence/` (PHASE-05) |
| Decisions | `.sps/decisions/DEC-0007-new-repository-and-no-emoji.md` |

### Three findings that change the plan

1. **There is no SEO skill.** `SKILL-ROUTER.md:27` names an "`seo` skill (fallback)" — it does not
   exist (`skills/seo` absent; 0 seo-named files). SEO is a **phantom dependency**, so SEO 2.0 is
   `REWRITE`, not migration.
2. **Legacy is a distribution product, not a composition product.** 27 globally-installed skills
   across 17 sync roots and 34 global writes. SPS 2.0 inverts that model.
3. **The governance layer is the reusable asset.** The 4 validators with 24 negative cases built in
   Phases 02–04 are the highest-value legacy artefact (10 components `KEEP`).

---

## 2. Forensic findings — legacy system as measured

| Model | Measurement |
|---|---|
| Repository | 188 files: `skills/` 116, `.sps/` 37, `scripts/` 9 |
| **SPS core skill** | 50 Markdown + 10 other — **doc-dominated** |
| **CMS skill** | 19 Markdown + 37 code (Astro/React/SQL/PHP/Python) |
| **SEO** | **absent** — router references a non-existent skill |
| Installation | 27 `npx skills add` (all global); 34 global writes; 17 sync roots |
| Skill routing | `SKILL-ROUTER.md` 20-row static `domain -> skill` table |
| Skill governance | one permanent taste operator (`SKILL-GOVERNANCE.md:35`) |
| Memory | project-local `.sps/` (26 md, 7 json) + global `~/.sps/` |
| Host adapters | 8 in `skills/sps/hosts/` |
| Update | `check-update.sh` 107 + `sps-update.sh` 133 LOC |
| Uninstall | `uninstall.sh` 240 LOC, path-guessing `rm -rf` sweeps |
| Validation | 4 validators: lint 121, governance 52, control 49+8 neg, capability 54+16 neg |
| Emoji | **155 occurrences / 29 files**; icon libraries: **0** |
| Approval | instruction-only in legacy skills; machine-enforced only in Phases 02–04 |
| CMS workflow | law docs + template code; `data-sps-key` marker coupling |
| Agent assumptions | global `curl | bash` installer; 8 adapters; no core/adapter split |

**Execution flow:** `/sps` -> agent reads Markdown laws -> looks up a static table -> invokes a
globally-installed skill -> optionally writes `.sps/`. No selection evaluation, no security gate,
no machine-checked phase gate.

---

## 3. Old vs new repository strategy

| | Legacy SPS | SPS 2.0 |
|---|---|---|
| Shape | distribution (fixed global stack) | composition (select per project) |
| Scope | global machine | project-local by default |
| Laws | Markdown read by an agent | JSON Schemas + deterministic validators |
| Routing | static table | evaluated selection pipeline |
| Memory | mixed project/global | project-local only |
| Reversibility | in-place edits | new repo; `checkout` is full rollback |

Legacy is preserved unmodified and tagged `legacy-final` (`DEC-0007`).

---

## 4. Migration strategy

39 components: `KEEP` 10 · `REFACTOR` 8 · `REWRITE` 6 · `REPLACE` 4 · `ARCHIVE` 4 · `DEPRECATE` 1 ·
`RESEARCH FIRST` 5 · `NEVER COPY` 1.

- **Reusable as-is:** governance model, validators, evidence model, approval discipline, capability
  model, project-local `.sps/`, `data-sps-key` convention, changelog, root lock files.
- **Must be replaced:** skill router, hardcoded skill list, global installers, uninstaller, packaging.
- **Never copied:** the `auth-helper.ts` hardcoded-secret fallback (`KI-01`).
- **Revalidate before reuse:** whole CMS skill, MCP integration, PowerShell parity, admin UI templates.

---

## 5. Global vs project-local strategy

Capabilities, MCP definitions, memory, decisions, evidence, registry and research cache are all
**project-local**. Only the SPS 2.0 core and user-promoted preferences may be global. Global install
is exceptional, requires explicit user authorisation, and is machine-rejected without it (Phase 04
`CASE D`/`N`). Team reproducibility comes from **repository state**, not machine mutation — the
legacy global installer is explicitly not the SPS 2.0 onboarding path.

---

## 6. Agent interoperability strategy

`core/` + `governance/` are agent-neutral; adapters are thin, replaceable and deletable.
**Portability is testable:** the core must pass with *all* adapters removed. Nine anti-pattern ->
control mappings turn agent drift into machine-checkable rejection rather than stronger instructions.

---

## 7. Dynamic skill strategy

requirement -> technology -> task -> candidates -> research + evaluation -> security/licence ->
compatibility -> freshness -> ranking -> **user approval** -> project-local install -> provenance ->
verify -> re-evaluate. Popularity and recency are **tie-breakers only**. Forced user choices always
override automatic selection.

---

## 8. CMS strategy

`Super Admin` keeps structural/developer controls; `Admin` is content-only and **cannot** access
layout or design-system controls. Required: roles, permissions, content/section model, reusable
blocks, media, validation, preview, publishing, rollback, audit history, developer controls. Legacy
CMS is `RESEARCH FIRST` — real code, unverified security posture, known secret defect.

---

## 9. SEO strategy

Legacy SEO does not exist. SEO 2.0 is designed new across all 27 requested dimensions with a
mandatory pre-deployment audit. **No implementation in this phase.**

---

## 10. Memory strategy

Project-local `.sps/` holds config, memory, capabilities, MCP, research, evidence, decisions, tasks
and audits. A new agent must be able to continue from repository state alone.

---

## 11. Git strategy

Legacy preserved; SPS 2.0 in a **new** repository; a remote is created **only** when the user
decides to publish. This repository stays local-only: **no remote created, nothing pushed**.

---

## 12. Roadmap

16 isolated phases (P1 foundation -> P16 production hardening), each with objective, dependencies,
scope, forbidden scope, deliverables, acceptance, verification, approval gate and rollback.
**P1–P2 are the critical path.**

---

## 13. Validation results

| Command | Result | Exit |
|---|---|---|
| `bash scripts/lint-sps.sh` | `== SPS lint PASSED ==` | 0 |
| `bash .sps/tools/validate-governance.sh` | 52/52 | 0 |
| `bash .sps/tools/validate-control.sh` | 49/49 + 8 negative | 0 |
| `bash .sps/tools/validate-capability.sh` | 54/54 + 16 negative | 0 |

Forbidden paths changed: **0**. Installs: **0**. Remotes created: **0**. Pushes: **0**.

---

## 14. Negative-test results

No new validator was introduced (planning only), so no new negative tests were added. The
**existing 24 negative cases** (8 control + 16 capability) still pass — evidence that Phase 05 did
not weaken any existing control.

---

## 15. Discrepancies found

| # | Finding |
|---|---|
| D-1 | **`SKILL-ROUTER.md:27` references a non-existent `seo` skill** — phantom dependency |
| D-2 | `CATALOG.md` documents 3 install profiles that 4.0.0 removed (stale) |
| D-3 | 155 emoji across 29 files; the rule now exists but remediation is out of scope |
| D-4 | Global memory `~/.sps/` still coexists with project-local `.sps/` — deprecated, not removed |

No contradiction between the Phase 01–04 reports and the repository was found.

---

## 16. Decisions created

| ID | Decision | Approval |
|---|---|---|
| `DEC-0007` | SPS 2.0 is a new repository; legacy preserved unmodified | `PENDING_USER_APPROVAL` |
| `DEC-0008` | Global no-emoji rule; icon libraries are selectable capabilities | `PENDING_USER_APPROVAL` |

---

## 17. Files

**Created:** 6 architecture docs, `PHASE-05-REQUIREMENTS.json`, `PHASE-05-EVIDENCE.json`,
`PHASE-05-TASKS.md`, `DEC-0007`/`DEC-0008`, this report.

**Modified:** `.sps/STATE.md`, `.sps/handoff/HANDOFF-CURRENT.md`, `.sps/audits/README.md`.

**Deliberately untouched:** `skills/`, `scripts/`, `plugins/`, `.github/`, every installer, root
lock templates, `README.md`, `CHANGELOG.md`, and every Phase 01–04 artefact.

---

## 18. Explicit non-implementation statement

**No implementation or remediation was performed.** This phase produced architecture and planning
documents only. No SPS 2.0 code was written, no legacy behaviour changed, no dependency installed,
no Git remote created, nothing pushed.

---

## 19. Current phase status and next phase

`PHASE-05` — `COMPLETE` / `VERIFIED` / **`AWAITING_USER_APPROVAL`**.

**Next phase:** roadmap **P1 — Repository Foundation**, requiring a NEW explicit user instruction.

---

*End of Phase 05. Planning only. No implementation performed.*
