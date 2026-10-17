# AUDIT-PHASE-04 — Discovery & Capability Architecture

**Phase:** `PHASE-04` · **Date:** 2026-10-03
**Repository:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main` · **Branch:** `main`
**Status:** `COMPLETE` · `VERIFIED` · **`AWAITING_USER_APPROVAL`**

> Phase 04 builds the *mechanism* by which SPS decides which capabilities a project needs,
> why, from where, and how trustworthy they are. It does **not** populate that mechanism and
> does not claim the transformation is complete.

---

## 1. Executive Summary

| Delivered | Detail |
|---|---|
| Capability model | 14-state lifecycle mapped onto the Phase 03 model |
| Claim taxonomy | `FACT`/`EVIDENCE`/`INFERENCE`/`UNKNOWN` — never mixed |
| Contracts | capability, research, MCP, project-local install (`SCHEMA.md` §12–§16) |
| Registry | Project-local, **empty by design** (`DEC-0005`) |
| Research cache | Project-local, **empty by design** |
| Security gate | 11-threat model; `UNKNOWN` security **never** reads as safe |
| MCP contract | Evaluated as a capability; nothing installed |
| Provenance | 8-link chain; enforcement reported honestly (`DEC-0006`) |
| Staleness | 5 fields + 5 re-evaluation triggers; no auto-updating |
| No-emoji | Global rule stated; icon libraries are selectable capabilities |
| Migration | 9-stage plan; legacy router **not** removed |
| **Enforcement proof** | `validate-capability.sh`: **52 checks, 16 negative cases, exit 0** |

**Headline:** 16 deliberately-invalid capability records were constructed; **all 16 were
rejected**, and a positive control proves a valid record is still accepted.

**Nothing was discovered, installed, activated, or fabricated.**

---

## 2. Phase 03 Baseline Verification

| Check | Result |
|---|---|
| Branch / commits | `main`; baseline `2fc2b01` |
| Working tree at start | Clean |
| `PHASE-03` | `APPROVED` — User, 2026-10-03 |
| `DEC-0001`..`DEC-0004` | All resolved / approved |
| Phase 03 validator | 49/49 + 8 negative cases, exit 0 |
| **Gate contradiction** | **None.** `PHASE-04` was `NOT_STARTED` / `NOT_APPROVED` — consistent |

This prompt authorised *starting* Phase 04; it did **not** approve it, and Phase 04 is not
self-approved.

---

## 3. Control Model

| Question | Answered by |
|---|---|
| Where is this capability? | Capability lifecycle |
| What condition is it in? | Phase 02 status model |
| How strongly is this rule enforced? | Phase 03 enforcement levels |

Pipeline: requirement → identify domain → **research gate** → discover ≥2 candidates →
evaluate → security/licence gate → compatibility → compare → select with justification →
propose → **user approval** → install project-locally → record provenance → verify → active
→ re-evaluate on trigger.

---

## 4. Capability Lifecycle

`DISCOVERED → RESEARCHING → EVALUATED → PROPOSED → PENDING_USER_APPROVAL → APPROVED →
INSTALLING → INSTALLED → VERIFIED → ACTIVE`, plus `DEPRECATED`, `REJECTED`, `FAILED`,
`REMOVED`. `APPROVED` may be set **only by the user**.

---

## 5. Claim Taxonomy

Every capability fact is `FACT`, `EVIDENCE`, `INFERENCE`, or `UNKNOWN`; an `UNKNOWN` is never
silently upgraded. A capability with `security_status: UNKNOWN` **is not secure** — the single
most important honesty rule in this phase.

---

## 6. Security Evaluation

11 threats (malicious, abandoned, compromised, typosquatting, install-script, permission,
maintainer, source, dependency, licence). Five security statuses; `UNKNOWN`,
`SUSPECTED_RISK` and `VULNERABLE` all **block installation**.

---

## 7. Project-Local Activation

`PROJECT_LOCAL` is the default. Global install requires an explicit **user** authorizer plus
the same gates. The validator rejects an unauthorized global scope (CASE D) and one authorized
by an agent (CASE N).

---

## 8. Technology Research Gate

Ten required areas; `SUFFICIENT` requires all ten `COVERED` **and** a source of rank ≤ 4. An
`INSUFFICIENT` technology cannot satisfy a selection (CASE F).

---

## 9. Provenance Contract

requirement → discovery → research → evaluation → user decision → installation → verification
→ usage.

| Layer | Status |
|---|---|
| Structural completeness | `ENFORCED` |
| Chain ordering | `VALIDATED` |
| Truthful recording | `DOCUMENTED` |
| Runtime tracking | `DECLARED` — **not implemented** |

---

## 10. Agent Interoperability

Markdown + JSON + `bash`/`python3` only. Slash commands are **not** a mandatory dependency.
No proprietary memory, context, or directory mechanism is used. An `AGENT_NEUTRAL` claim
carrying an agent-specific dependency is rejected (CASE I).

---

## 11. Audit of Existing Hardcoded Routing

Measured, not assumed:

| Site | Measurement | Consequence |
|---|---|---|
| `SKILL-ROUTER.md` | 20-row static `Domain → Primary/Secondary/Fallback` map | Selection is lookup, not judgement |
| `SKILL-ROUTER.md:9` | "Pick **one primary** skill per domain from the table" | Fixed preference per domain |
| `SKILL-GOVERNANCE.md:35` | "`design-taste-frontend` is **the only default taste operator**" | Permanent vendor preference |
| `install.sh` | **27** `npx skills add` calls, **34** `-g` global flags | All installs global, ignoring project |
| `install.sh:338-368` | Hardcoded GitHub URLs | No trust/quality evaluation before install |

**Six specific blockers to dynamic selection:** table-lookup selection; permanent preferences
with no re-evaluation trigger; global-first installation; no provenance record; no candidate
comparison; no security/maintenance/licence evaluation.

**The legacy router is NOT removed.** Migration is staged (`PROVENANCE.md` §6): stages 0–2 done,
3–8 deferred.

---

## 12. Validation Results

| Command | Result |
|---|---|
| `bash scripts/lint-sps.sh` | `== SPS lint PASSED ==`, exit 0 |
| `bash .sps/tools/validate-governance.sh` | 50/50, exit 0 |
| `bash .sps/tools/validate-control.sh` | 49/49 + 8 negative cases, exit 0 |
| `bash .sps/tools/validate-capability.sh` | **52/52 + 16 negative cases, exit 0** |
| `jq empty` × 4 JSON files | valid |
| Source diff | **empty** — no application/skill/installer file touched |
| `git remote -v` | empty — no remote exists |

### Negative tests — CASE A–N

| Case | Invalid state | Result |
|---|---|---|
| 0 | valid baseline (positive control) | **ACCEPTED** |
| A | no provenance | REJECTED |
| B | no source | REJECTED |
| C | UNKNOWN security rendered SAFE | REJECTED |
| D | GLOBAL install unauthorized | REJECTED |
| E | selection without evaluation | REJECTED |
| F | selection without SUFFICIENT research | REJECTED |
| G | APPROVED with no decider | REJECTED |
| G2 | APPROVED by agent | REJECTED |
| H | VERIFIED without evidence | REJECTED |
| I | AGENT_NEUTRAL with agent-specific dep | REJECTED |
| J | STALE presented as current | REJECTED |
| K | UNKNOWN presented as known | REJECTED |
| L | untrusted MCP installed | REJECTED |
| M | replaces ACTIVE without approval | REJECTED |
| N | GLOBAL authorized by agent | REJECTED |

`16 cases correctly rejected, 0 missed.`

---

## 13. Files Changed

**Created:** `.sps/capability/{CAPABILITY-MODEL,SECURITY,PROVENANCE}.md`,
`.sps/capability/registry/PHASE-04-CAPABILITIES.json`, `.sps/research/PHASE-04-RESEARCH.json`,
`.sps/requirements/PHASE-04-REQUIREMENTS.json`, `.sps/evidence/PHASE-04-EVIDENCE.json`,
`.sps/tasks/PHASE-04-TASKS.md`, `.sps/decisions/DEC-0005-*.md`, `DEC-0006-*.md`,
`.sps/tools/validate-capability.sh`, `.sps/tools/.cap-fixture.py`,
`AUDIT-PHASE-04-DISCOVERY-CAPABILITY-ARCHITECTURE.md`.

**Modified:** `.sps/SCHEMA.md`, `.sps/STATE.md`, `.sps/handoff/HANDOFF-CURRENT.md`,
`.sps/audits/README.md`.

**Not modified:** `skills/`, `scripts/`, `plugins/`, `.github/`, any installer, or
`SKILL-ROUTER.md` / `SKILL-GOVERNANCE.md`.

---

## 14. Known Limitations

1. **The registry is empty.** The mechanism is proven; content is not populated. Migration
   stages 3+ deferred.
2. **No discovery engine exists** — no network calls, registry scanning, or enumeration.
3. **Provenance is detection-based, not runtime** (`DEC-0006`).
4. **Truthful recording is `DOCUMENTED`, not enforced.** A validator cannot prove honesty.
5. **The legacy router remains authoritative** for every domain.
6. **No capability is installed or verified end-to-end**, because nothing is selected.
7. **155 emoji across 29 files remain** (Phase 01 measurement). The rule is now stated;
   remediation is out of Phase 04 scope.
8. **No CI wiring** for the new validator.
9. **13 requirements and 2 decisions await user approval.**

---

## 15. Discrepancies & Defects Found

**Defects in my own Phase 04 work, found and fixed before commit:**
1. A research-fixture path bug masked CASE H and CASE M (the `CASE F` check fired first via
   `continue`). Fixed by pointing the negative suite at the fixture research file.
2. An over-strict grep against `SECURITY.md` produced a false failure.
3. An empty registry produced no checker output and was wrongly treated as a failure. Fixed so
   emptiness is a recorded, valid state.

**No contradiction between the Phase 03 report and the repository.**

---

## 16. Deferred Findings

All Phase 01 issues remain open: `KI-01` (hardcoded secret — still highest priority) through
`KI-14`. **None were fixed** (§21). No CMS, SEO, backend, frontend, security, performance,
accessibility, CI/CD, or orchestration work was performed.

---

## 17. Unresolved Decisions

| ID | Decision | Status |
|---|---|---|
| `DEC-0005` | Registry starts empty; no capability fabricated | `PENDING_USER_APPROVAL` |
| `DEC-0006` | Provenance is detection-based, not runtime | `PENDING_USER_APPROVAL` |

Open questions: authorise migration stage 3 (live research)? Which domain first for a
shadow-run? Wire the validator into CI?

---

## 18. Phase 05 Recommendation

**Not started. Requires explicit user approval.**

1. Approve/reject Phase 04, `DEC-0005`, `DEC-0006`.
2. Wire the capability validator into CI.
3. Authorise migration stage 3 — populate the research cache for one technology.
4. Authorise a shadow-run evaluation for one domain against the legacy router.
5. Separately, address `KI-01` (still the highest-severity open item).

**Do not begin Phase 05 without explicit approval.**

---

*End of Phase 04 report. Nothing was installed, discovered, or fabricated. Phase 05 not started.*
