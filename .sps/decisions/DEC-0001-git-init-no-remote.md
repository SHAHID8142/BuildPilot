# DEC-0001 — Initialise Git locally without configuring a remote

- **Date:** 2026-10-03
- **Status:** Active
- **Approval:** `APPROVED`
- **Phase / Task:** `PHASE-02` / `PHASE-02-T01`
- **Evidence:** `EV-P02-001`, `EV-P02-002`, `EV-P02-008`
- **Supersedes:** none

---

## Decision

Initialise a new local Git repository on branch `main` with **no remote configured**, and
create a clearly identifiable pre-remediation baseline commit
(`chore(governance): establish pre-remediation baseline`).

## Reason

Phase 01 finding **F-10** established that the working copy had no Git provenance, so no
future change could be attributed, reverted, or reviewed. Remediation work in later phases
requires a verifiable starting point.

Before initialising, the state was confirmed rather than assumed: no `.git` in this
directory, no `.git` in any parent directory up to `/`, not a worktree, not a nested
repository. There was therefore **no history to lose**, and nothing was overwritten.

A remote was deliberately **not** configured because §4 forbids inventing a remote URL,
creating a GitHub repository automatically, or pushing to an unknown destination. Local
provenance is sufficient for Phase 02.

## Evidence

- `EV-P02-001` — pre-init checks all returned "not a git repository".
- `EV-P02-002` — `git init --initial-branch=main` succeeded; branch = `main`.
- `EV-P02-008` — 153 paths staged; secret-path scan returned no matches.
- `git remote -v` returns empty — `REMOTE_NOT_CONFIGURED`.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Add a remote pointing at the upstream URL referenced in README | §4 forbids inventing/guessing a remote URL. No remote was ever configured on this copy, so the URL cannot be confirmed as *this* repository's. |
| Create a GitHub repository automatically | §4 explicitly forbids this. |
| Skip Git entirely, use plain file-based provenance | Loses diffing, blame, atomic rollback and tamper evidence. §2 requires Git provenance. |
| Commit existing orphan debug artefacts into the baseline, then clean up | Would encode temporary junk into permanent history. They remain tracked and are registered as a known issue instead. |

## Approval

**Required:** yes — remote/push decisions are the user's.
**Status:** `APPROVED`
**Decision:** `KEEP_LOCAL_ONLY` — do not configure or add a remote at this stage.
**Decided by:** User (explicit user approval, 2026-10-03)
**Approval basis:** Phase 02 implementation and verification were independently reviewed and accepted.

The user reviewed the Phase 02 report and commit, then explicitly resolved this decision as
`KEEP_LOCAL_ONLY`. The repository therefore remains local-only, which satisfies §4
("local Git provenance even if remote push is impossible").

**Consequence:** `PUSH_SKIPPED: NO_REMOTE_CONFIGURED` remains the correct push result for
this repository. No push may be attempted, and no remote may be invented, until the user
issues a new explicit instruction.

**Note on provenance:** the Phase 02 report describes this decision as pending. That was
accurate when written. This record supersedes that status; the report is left unmodified
because reports are point-in-time artefacts, not live state.