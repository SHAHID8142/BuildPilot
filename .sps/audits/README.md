# Audits & Known-Issue Register

Index of audit reports plus the standing register of known issues discovered but
**deliberately not fixed** (Phase 02 §18 — document, do not fix).

---

## Audit Reports

| Phase | Report | Type | Status |
|---|---|---|---|
| `PHASE-01` | [`../../AUDIT-PHASE-01-BASELINE-FORENSIC.md`](../../AUDIT-PHASE-01-BASELINE-FORENSIC.md) | Read-only forensic audit | `VERIFIED` |
| `PHASE-02` | [`../../AUDIT-PHASE-02-GOVERNANCE-IMPLEMENTATION.md`](../../AUDIT-PHASE-02-GOVERNANCE-IMPLEMENTATION.md) | Governance implementation report | `APPROVED` (User, 2026-10-03) |
| `PHASE-03` | [`../../AUDIT-PHASE-03-ENFORCEMENT-CONTROL.md`](../../AUDIT-PHASE-03-ENFORCEMENT-CONTROL.md) | Enforcement & control foundation | `APPROVED` (User, 2026-10-03) |
| `PHASE-04` | [`../../AUDIT-PHASE-04-DISCOVERY-CAPABILITY-ARCHITECTURE.md`](../../AUDIT-PHASE-04-DISCOVERY-CAPABILITY-ARCHITECTURE.md) | Discovery & capability architecture | `APPROVED` (User, 2026-10-03) |
| `PHASE-05` | [`../../AUDIT-PHASE-05-SPS2-ARCHITECTURE.md`](../../AUDIT-PHASE-05-SPS2-ARCHITECTURE.md) | SPS 2.0 architecture & migration planning | `APPROVED` (User, 2026-10-03) |
| P1–P16 | — | SPS 2.0 roadmap (`.sps/architecture/SPS2-ROADMAP.md`) | `NOT_STARTED` — P1 needs a new explicit instruction |
| `SPEC-2` | [`../../AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md`](../../AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md) | Read-only observation — Git remote/push discrepancy vs `DEC-0001`/`DEC-0002` | `NOT APPROVED` — records facts only; awaits User decision D1–D5 |

> **Report-vs-state note.** Reports are point-in-time artefacts: the Phase 02 report states
> its approval was pending because that was true when written. `.sps/STATE.md` and the decision
> records are the live state. Reports are deliberately left unmodified so their original
> claims remain auditable.

> **Index note.** This file previously contained a duplicate, stale table that still claimed
> `PHASE-03` was `NOT_STARTED` and omitted `PHASE-04`/`PHASE-05`. It was consolidated during the
> Phase 05 approval transition (`EV-P05-010`). `.sps/STATE.md` remains authoritative.

The legacy SPS-format report template remains at `.sps/audit-report.md` (untouched).
It is a **different** artefact: a per-project 100-point alignment score, not a phase report.

---

## Known-Issue Register

Phase 01 findings re-verified during Phase 02. **None were fixed.** Severity reflects
impact if left unaddressed, not urgency imposed by this phase.

| ID | Finding | Status after Phase 02 | Severity | Notes |
|---|---|---|---|---|
| `KI-01` | **F-3** hardcoded session-secret fallback in `skills/sps-cms/templates/auth/auth-helper.ts` | `OPEN` | **High** | Secret remediation — out of scope. Verified as a **placeholder** literal, not a live credential (see EV-P02-005). |
| `KI-02` | **F-1** determinism inversion — every "hard law" is Markdown | `MITIGATED` | High | Partially mitigated by the maturity model; not fixed. |
| `KI-03` | **F-2** dynamic skill discovery absent; hardcoded global allow-list | `OPEN` | High | Explicitly out of scope for Phase 02. |
| `KI-04` | **F-4** all 28 third-party skills unbundled → capability `UNKNOWN` | `OPEN` | High | Depends on target environment assumptions. |
| `KI-05` | **I-3** orphan debug artifacts at repo root | `OPEN` | Low | `test_claude.sh`, `test_timeout.sh`, `test_uiux.sh` still tracked. `.tmp.test_file` now gitignored. Deletion is out of scope. |
| `KI-06` | **I-13** no `commands/` directory despite slash-command interface | `OPEN` | Medium | Command scaffolding is orchestration work. |
| `KI-07` | **F-8** version drift across 5 version markers | `OPEN` | Medium | Confirmed exactly: sps 4.0.0 / sps-cms VERSION 2.3.0 / sps-cms package.json 1.4.0 / plugin.json 2.0.0 / marketplace.json 2.0.0. Versioning redesign out of scope. |
| `KI-08` | **I-4 / I-5** `CATALOG.md` contradicts current installer and router | `OPEN` | Low | Doc cleanup out of scope for a governance phase. |
| `KI-09` | **F-9** `lint-sps.sh` asserts string presence, not behaviour | `OPEN` | Medium | Confirmed: `require_text()` is a `grep -Eq` wrapper. Not fixed; the maturity model forces explicit levels instead. |
| `KI-10` | `sps-cms` upload-size contradiction (10MB/50MB vs 15MB) | `OPEN` | Low | Found during Phase 02; CMS work out of scope. |
| `KI-11` | `auth-helper.ts` ignores `role` param, always encodes `admin` | `OPEN` | Medium | Security remediation out of scope. |
| `KI-12` | `AUTO-SYNC-PROTOCOL.md` asserts "zero cache clearance needed" | `OPEN` | Low | Unverified claim; needs a CDN-caching test to settle. |
| `KI-13` | `bootstrap-sps.sh` auto-applies updates (global state mutation) | `OPEN` | Medium | Discovered in Phase 01; changing installer behaviour is out of scope. |
| `KI-14` | `install.ps1` defines `compute_total_steps` twice? (`install.sh`) | `OPEN` | Low | Cosmetic duplicate function in `install.sh` (lines 116 & 136). Not fixed. |
| `KI-15` | Repository has a configured Git remote and four recorded pushes, contradicting `DEC-0001`; `DEC-0002`'s placeholder-identity obligation is due and undischarged | `OPEN` | **High** | Found during SPEC-2 (approver-policy consolidation) 2026-10-15. Verified read-only from local git state; no remote, config, history or branch was changed. Full record, evidence and the five open decisions (D1–D5): [`AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md`](../../AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md). **Not fixed by design** — remediation is not authorized and requires a User decision. |
| `KI-16` | Migrating the legacy `.sps/tools/` validators to the canonical agent-name policy trips two approved P3/P4 "legacy untouched" controls | `OPEN` - control disposition decided, underlying requirement question still open | **Medium** | Found during SPEC-2 2026-10-15. `sps2/tools/validate-p3.sh` reports 66 passed / 2 failed and `validate-p4.sh` 57 passed / 3 failed. **Control disposition decided by `DEC-0028` (2026-10-15, User APPROVED): the three legacy-protection controls are PRESERVED UNCHANGED.** The agent-attribution behaviour of those validators was already reconciled with the canonical policy because they consume it; the residual failures are accurate reports that legacy governance files were modified. Narrowing the pathspec would redefine "legacy paths" in REQ-P3-08, which is APPROVED and VERIFIED, so it was NOT done. No approved control or requirement was weakened; the operative User-attribution controls are the exact-equality checks in `validate-p3.sh` and `validate-p4.sh`, all untouched. **Remaining decision:** whether to amend REQ-P3-08 to enumerate legacy paths explicitly (see UQ-ATT-1 in `sps2/decisions/ATTRIBUTION-POLICY-DECISIONS.json`). Until then these two validators stay red by design. |

---

## Phase 01 Discrepancies Found During Phase 02 Verification

Phase 01 was treated as evidence, not truth. Full detail in
`.sps/evidence/PHASE-02-EVIDENCE.json` → `phase01_discrepancies`.

| ID | Finding | Phase 01 said | Verified reality | Resolution |
|---|---|---|---|---|
| `DISC-01` | F-3 | secret at `auth-helper.ts:8` | literal is on **line 9** | Documented; line ref corrected here. Issue itself still `OPEN`. |
| `DISC-02` | F-8 | version drift exists | **Confirmed exactly**, all 5 markers | Registered as `KI-07`. |
| `DISC-03` | F-10 | not a Git repository | **Confirmed** (no `.git`, no parent, not worktree) | **Resolved** by `DEC-0001`. |
| `DISC-04` | F-9 | lint asserts string presence | **Confirmed** by reading `require_text()` | Mitigated by maturity model; still `OPEN` as `KI-09`. |
| `DISC-05` | I-3 | orphan artifacts unreferenced | **Partially disputed** — `.tmp.test_file` now gitignored; the 3 `.sh` files remain | Registered as `KI-05`. |
| `DISC-06` | — (Phase 02 self-deviation) | — | Brief §2 (create `.gitignore`) and §3 (baseline = state *before* Phase 02) conflict for `.gitignore` | Hardening committed **inside** baseline `10ab67a`; disclosed, confined to 1 file. |

### DISC-06 detail — baseline ordering deviation

The Phase 02 brief contains an ordering conflict:

- **§2** instructs creating an appropriate `.gitignore` *before* the baseline commit.
- **§3** requires the baseline to represent the repository "exactly as it exists
  **BEFORE** Phase 02 changes."

For `.gitignore` these cannot both hold. Resolution: the hardened `.gitignore` was
committed **inside** baseline `10ab67a` rather than in the governance commit.

Rationale: committing a baseline with *unprotected* ignore rules would risk committing
secrets before protection existed. §12 treats secret safety as the higher-severity concern,
so protection was applied first.

Impact verified as negligible: `git diff HEAD -- skills/ scripts/ plugins/ install.sh
uninstall.sh get-sps.sh .github/` is **empty** — no application, skill, installer, or CI
file differs from the pre-Phase-02 state. The baseline still faithfully represents the
original code for all remediation purposes.

---

## Rules for future phases

1. Register any newly discovered issue here **before** fixing it, so scope is explicit.
2. Do not fix an issue whose category is out of scope for the current phase.
3. When an issue is fixed, update its status **and** link the evidence record ID.
4. Never delete a row — supersede it and record why (mirrors the decision-record rule).