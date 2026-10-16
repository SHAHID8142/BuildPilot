# DEC-0007 — SPS 2.0 is a new repository; legacy is preserved unmodified

- **Date:** 2026-10-03
- **Status:** Active
- **Approval:** `APPROVED`
- **Phase / Task:** `PHASE-05` / `PHASE-05-T02`
- **Evidence:** `EV-P05-002`
- **Supersedes:** none

---

## Decision

SPS 2.0 will be built in a **new repository**. The legacy SPS repository is preserved
unmodified as an immutable reference, tagged `legacy-final`. Nothing is redesigned in place.

## Reason

Three forces make in-place redesign untenable:

1. **Provenance.** Phase 02–04 built a validated governance layer on top of the legacy tree. A
   redesign would destroy the only working proof that the governance model is enforceable.
2. **Blast radius.** The legacy tree mixes a distributed skill, global installers, 34 machine
   writes and 4 audit reports. Restructuring it in place makes every change ambiguous.
3. **Reversibility.** A new repository keeps `git checkout` as a complete rollback mechanism.
   In-place work has no revert boundary until the very end.

Additionally, the legacy and SPS 2.0 architectures are structurally different: legacy is
*distribution* (install a fixed global stack), SPS 2.0 is *per-project composition* (select
capabilities into a project). That is a different product, not a refactor.

## Evidence

`EV-P05-002` — migration matrix classifies 39 legacy components across 8 disposition classes,
identifying what is reusable (governance/validators, `KEEP` = 10) versus what must be replaced
(installers/router/hardcoded skill list, `REWRITE`/`REPLACE` = 10).

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Redesign legacy in place | No revert boundary; destroys validated governance; mixes distribution and composition concerns |
| Branch legacy and evolve it | Branches inherit 4 audit reports and global-install assumptions as permanent baggage |
| Fork legacy, delete later | Fork is acceptable *only* if legacy stays frozen; we recommend a fresh repo + explicit `legacy/` import manifest, which is more honest about provenance |
| Greenfield with no legacy reference | Loses the working validators and the CMS code that took real effort to write |

## Approval

**Required:** yes — this constrains all of SPS 2.0.
**Status:** `APPROVED`
**Decided by:** User (explicit user approval, 2026-10-03)
**Approval basis:** User reviewed the Phase 05 planning report, architecture, migration strategy, repository separation strategy, global-vs-project-local model, and discrepancies, and approved Phase 05.

**Consequence if approved:** no SPS 2.0 file may be created in this repository. The planning
artefacts in `.sps/architecture/` are the *only* SPS 2.0 content that lives here.

---

# DEC-0008 — No-emoji becomes a global, project-overridable rule

- **Date:** 2026-10-03
- **Status:** Active
- **Approval:** `APPROVED`
- **Phase / Task:** `PHASE-05` / `PHASE-05-T03`
- **Evidence:** `EV-P05-003`
- **Supersedes:** none

---

## Decision

SPS 2.0 ships a **global default of no emoji** across UI, buttons, labels, documentation, code
comments, generated copy and status indicators. Emoji are permitted only when the user explicitly
authorises them **for a specific project**. Icon selection is project-aware, not globally pinned.

## Reason

Phase 01 measured **155 emoji across 29 files** in this repository — including user-facing
`LiveEditorOverlay.tsx` (17), `InquiriesInbox.tsx` (9) and `AdminLayout.tsx` (9) — and
`sps-cms/SKILL.md:95-96` *mandates* flag emoji in admin UI. That is the defect to correct.

But the correction must not over-correct: pinning one icon library globally would recreate the
permanent-preference failure of `SKILL-GOVERNANCE.md:35` (Phase 01 F-2). Icon libraries are
therefore treated as **selectable capabilities**, chosen through the same evaluation pipeline as
any other capability.

## Evidence

`EV-P05-003` — emoji scan re-measured at 155 occurrences across 29 files; icon libraries
(Lucide / Phosphor / Heroicons / Radix) appear in 0 files, so no icon policy exists either.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Allow emoji freely | Preserves the measured 155-occurrence problem |
| Ban emoji permanently, no override | Over-rigid; the user must remain able to authorise per project |
| Pin Lucide globally | Recreates the permanent-vendor-preference failure (F-2) in a new place |
| Treat icon libraries as capabilities | **Adopted** — consistent with dynamic selection |

## Approval

**Required:** yes — this is a global behavioural rule.
**Status:** `APPROVED`
**Decided by:** User (explicit user approval, 2026-10-03)
**Approval basis:** User reviewed the Phase 05 planning report, architecture, migration strategy, repository separation strategy, global-vs-project-local model, and discrepancies, and approved Phase 05.

**Note:** the 155 legacy emoji remain. Removing them is remediation work, out of Phase 05 scope.