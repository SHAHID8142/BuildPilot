# DEC-0002 — Repo-local Git identity; no machine-global identity change

- **Date:** 2026-10-03
- **Status:** Active
- **Approval:** `APPROVED`
- **Phase / Task:** `PHASE-02` / `PHASE-02-T02`
- **Evidence:** `EV-P02-003`
- **Supersedes:** none

---

## Decision

Configure the commit identity using `git config --local` only, writing to `.git/config`
inside this repository. Do **not** set `git config --global`.

Identity used:

- `user.name` = `SPS Governance (local)`
- `user.email` = `sps-governance@local.invalid`

The `.invalid` TLD is reserved by RFC 2606 and can never resolve, so the address cannot
accidentally reach a real mailbox.

## Reason

Git refuses to commit without an identity, but §16 forbids changing machine-global state.
Setting a global identity would modify the user's machine configuration for every other
repository on it — a side effect well outside this task's scope.

A repo-local identity satisfies both constraints: commits work, and nothing outside the
repository changes.

The placeholder value is deliberately obviously non-personal. It is **not** an attempt to
impersonate the user, and the user should replace it with their own identity before any
commit is published to a shared remote.

## Evidence

`EV-P02-003` — identity set locally; `git config --global --get user.name` confirmed
**still unset** after the change, proving no global state was modified.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| `git config --global user.name/user.email` | §16 forbids machine-global changes; would affect every repo on the machine. |
| Use the user's real name/email | Not supplied, and guessing personal identity details would be worse than a clear placeholder. |
| Pass `-c user.name=...` per commit | Works, but leaves the repo unconfigured for future agents, who would hit the same error. A repo-local config is self-documenting for the next agent. |
| Commit with `--allow-empty` / bypass identity | Produces unattributable or malformed commits. |

## Approval

**Required:** yes — the identity should be the user's own before publishing.
**Status:** `APPROVED`
**Decision:** `DEFER_IDENTITY_UPDATE`
**Decided by:** User (explicit user approval, 2026-10-03)
**Approval basis:** Phase 02 implementation and verification were independently reviewed and accepted.

The user explicitly resolved this as `DEFER_IDENTITY_UPDATE`: keep the current repository-local
placeholder identity for now, and replace it before the repository is published or shared
externally.

### What this decision does and does not settle

| Question | Status |
|---|---|
| May the placeholder identity be used for local commits? | **Yes** — approved. |
| Is the placeholder the *final* identity? | **No** — deferred. |
| Must it change before external publication? | **Yes** — a standing obligation. |
| When must it change? | Before the repository is published or shared externally. |

### Standing obligation (carried forward)

This deferral creates a **precondition that has not yet been discharged**. Any future phase
that publishes, pushes, or shares this repository externally MUST first replace the identity:

```bash
git config --local user.name "Your Name"
git config --local user.email "you@example.com"
```

Because `DEC-0001` resolves to `KEEP_LOCAL_ONLY`, no push can occur under current instructions,
so the obligation is not yet due. It becomes due the moment a remote is added or the repository
is shared.

**Note on provenance:** the Phase 02 report describes this decision as pending. That was
accurate when written. This record supersedes that status; the report is left unmodified
because reports are point-in-time artefacts, not live state.