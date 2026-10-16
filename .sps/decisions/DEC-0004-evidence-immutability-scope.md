# DEC-0004 — Evidence immutability is detection-based, not prevention-based

- **Date:** 2026-10-03
- **Status:** Active
- **Approval:** `APPROVED`
- **Phase / Task:** `PHASE-03` / `PHASE-03-T04`
- **Evidence:** `EV-P03-006`
- **Supersedes:** none

---

## Decision

Implement the immutable-evidence principle as **structural detection** plus **git
tamper-evidence**, and explicitly **do not** claim true immutability.

Enforced by `validate-control.sh`: unique evidence IDs, mandatory `result` enum, and non-empty
verbatim `actual` for every `PASS`. Git history provides the tamper-evidence layer.

## Reason

The brief requires that an agent cannot fail a test, modify the evidence, make the failure
disappear, and report success — "without leaving traceable history".

True immutability would require signed commits, an append-only external anchor, or a
write-once store. None of those exist here, and building a distributed signing or anchoring
system would be over-implementation for an architectural phase (§23 forbids a service,
daemon, or new dependency).

**What is honestly achievable now:** any tampering is *detectable* — by structural checks and
by `git diff`/`git log`. What is **not** achievable now: prevention. An agent with write
access can rewrite a file before it is ever committed.

This limitation is recorded rather than papered over.

## Evidence

`EV-P03-006` — CASE F injects a fixture with a duplicate evidence ID, an invalid `result`
enum value, and a `PASS` record whose captured output was erased. The validator detected all
three signals. Suite result: 8 negative cases correctly rejected, 0 missed.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| GPG-sign every evidence commit | Requires key management; adds friction; not verifiable by a third party without the key |
| Append evidence to an external service | Forbidden by §23 (no new service/daemon); also breaks tool-agnostic and offline use |
| Claim immutability is achieved | Would be a false claim — the precise `DECLARED` vs `IMPLEMENTED` failure Phase 01 **F-9** identified |
| Rely on git alone | Git detects post-commit tampering but not pre-commit rewriting, and does not validate record structure |

## Approval

**Required:** yes — this bounds a core Phase 03 guarantee.
**Status:** `APPROVED`
**Decided by:** User (explicit user approval, 2026-10-03)
**Approval basis:** Phase 03 implementation and verification were independently reviewed and accepted.

The user explicitly approved this decision on 2026-10-03, accepting evidence immutability as
**detection-based, not prevention-based**.

### What this approval does and does not settle

| Question | Status |
|---|---|
| Are structural append-only checks enforced? | **Yes** — Level 2, negative-tested (CASE F) |
| Does git provide tamper-evidence for committed records? | **Yes** — detection |
| Is pre-commit rewriting prevented? | **No** — out of scope, honestly recorded |
| Should signed/anchored evidence be built later? | **Open** — a future phase decision |

**Standing limitation (unchanged by this approval):** an agent with write access can still
rewrite an evidence file *before* commit. This remains a Known Limitation of Phase 03 and is
recorded as such in `AUDIT-PHASE-03-ENFORCEMENT-CONTROL.md` §22 item 2.