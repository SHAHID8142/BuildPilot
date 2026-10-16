# Capability Model — Phase 04

**Status:** `AWAITING_USER_APPROVAL` · **Extends:** `.sps/control/` (Phase 03)

> **Core principle.** Replace *hardcoded skill preference → always the same skill* with
> *project requirement → discover → evaluate → select → install project-locally → record
> provenance → verify*. SPS must answer: for THIS project, THIS stack, THIS constraint set —
> what capabilities are appropriate, why, from where, how trustworthy, and how to verify them.

**This phase builds the mechanism, not a marketplace.** No discovery engine, no network calls,
no installation.

---

## 1. Audit of the existing hardcoded architecture (§8)

Measured from the repository, not assumed:

| Hardcoding site | Evidence | Effect |
|---|---|---|
| `skills/sps/SKILL-ROUTER.md` | 20-row static `Domain → Primary/Secondary/Fallback` table (line 20) | Selection is a lookup, not a judgement |
| Same file, line 9 | "Pick **one primary** skill per domain from the table below" | Fixed preference per domain |
| `skills/sps/SKILL-GOVERNANCE.md` line 35 | "`design-taste-frontend` is **the only default taste operator**" | Permanent vendor preference by design |
| `install.sh` | **27** `npx skills add` calls, **34** `-g` (global) flags | All installs global, regardless of project |
| `install.sh:338-368` | GitHub URLs hardcoded per skill | No trust/quality evaluation before install |

**Where the current architecture prevents dynamic selection — precisely:**

1. Selection is by **domain table lookup**, so project context cannot influence the outcome.
2. Preferences are **permanent** (`SKILL-GOVERNANCE.md:35`) — no re-evaluation trigger exists.
3. Installation is **global-first** (`-g`), violating the project-local principle (§4).
4. There is **no provenance record** — nothing records why a capability was chosen, by whom,
   from which source, at which version, or how to remove it.
5. There is **no candidate comparison** — a single named primary is presented per domain.
6. There is **no security/maintenance/licence evaluation** before installation.

**Conclusion:** the current system cannot satisfy §7's "justify selection" because it never
compares alternatives. It does not *forbid* dynamic selection but provides no mechanism for it.

**The existing system is NOT removed in Phase 04.** Migration is planned, not executed —
see `MIGRATION.md`.

---

## 2. Claim taxonomy (§6)

Every capability fact must be one of four classes. Never mix them.

| Class | Meaning | Example | Auto-verifiable? |
|---|---|---|---|
| `FACT` | Directly observed | "the package version is 1.2.3" | Sometimes |
| `EVIDENCE` | Backed by a captured source | "version 1.2.3 read from registry API on `<date>`" | Yes, via the recorded source |
| `INFERENCE` | Reasoned, not observed | "this library likely supports Astro 5" | **No** — must be labelled |
| `UNKNOWN` | Not established | "maintainer response time is UNKNOWN" | No |

**Rule:** `UNKNOWN` must never be silently upgraded to `FACT`. A capability whose security
status is `UNKNOWN` **is not secure** — see `SECURITY.md` §2.

---

## 3. Capability lifecycle (§9)

Extends the Phase 03 model rather than duplicating it.

```
DISCOVERED -> RESEARCHING -> EVALUATED -> PROPOSED -> PENDING_USER_APPROVAL
  -> APPROVED -> INSTALLING -> INSTALLED -> VERIFIED -> ACTIVE
                                                    ↓
                              DEPRECATED <-------------┤
                                  ↓                   ↓
                               REMOVED          REJECTED / FAILED
```

| State | Means | May be set by |
|---|---|---|
| `DISCOVERED` | Candidate found; nothing evaluated | Agent |
| `RESEARCHING` | Research in progress | Agent |
| `EVALUATED` | Scored against project criteria | Agent |
| `PROPOSED` | Recommended, awaiting a decision | Agent |
| `PENDING_USER_APPROVAL` | Decision requested | Agent (request only) |
| `APPROVED` | **User** accepted | **User only** |
| `INSTALLING` / `INSTALLED` | Local activation | Agent, after approval |
| `VERIFIED` | Evidence proves it works | Agent, with evidence |
| `ACTIVE` | In use for a project requirement | Agent |
| `DEPRECATED` | Superseded or unsafe | Agent |
| `REJECTED` / `FAILED` / `REMOVED` | Terminal | Agent (post-approval for removal) |

**Mapping to Phase 03:** lifecycle stage mirrors the Phase 03 lifecycle; the `status` field
carries the Phase 02 status. This registry is **not** a third state machine — the three axes
remain independent (`CONTROL-MODEL.md` §2).

---

## 4. Selection pipeline (§2)

```
project requirement
  -> identify domain/technology
  -> RESEARCH GATE (is the technology understood? else research first)
  -> discover candidates (>=2, or record why only one exists)
  -> evaluate each against section 7 criteria
  -> security + maintenance + licence gate
  -> compatibility check (technology/framework/agent)
  -> quality comparison
  -> SELECT with recorded justification
  -> PROPOSE -> user approval (Level 3)
  -> install PROJECT-LOCALLY
  -> record provenance
  -> VERIFY
  -> ACTIVE
  -> re-evaluate on staleness trigger
```

**Rules:**
- A selection without at least one recorded evaluation is invalid (`CASE E`).
- A selection for an unresearched technology is invalid (`CASE F`).
- Popularity and recency are **tie-breakers only**, never primary justification.

---

## 5. Source priority (§16)

| Rank | Source | Weight |
|---|---|---|
| 1 | Official documentation | Authoritative for behaviour |
| 2 | Official repository | Authoritative for code/version |
| 3 | Official package registry | Version + integrity metadata |
| 4 | Maintainer docs/changelog | Intent and direction |
| 5 | High-quality independent technical source | Corroboration |
| 6 | Community discussion | Signal only — **never establishes correctness** |

**Rule:** community popularity alone must never establish correctness. Every selected source
is recorded with its rank and URL.

---

## 6. Staleness (§17)

| Field | Purpose |
|---|---|
| `researched_at` | When the research was performed |
| `version_checked` | Version observed at research time |
| `source_checked` | Source consulted |
| `last_verified` | Last evidence-backed verification |
| `review_due` | When re-evaluation is required |

**Re-evaluation triggers** (no automatic updating is implemented):
1. `review_due` passes.
2. Project stack or version changes.
3. A security advisory affects the capability.
4. Verification fails, or `ACTIVE` behaviour changes.
5. The user requests re-evaluation.

**Rule:** a stale capability must not be presented as current without re-verification
(`CASE J`). Staleness is reported, never auto-fixed.

---

## 7. No-emoji (§18)

Unless the user explicitly authorises emoji for a specific project:
- Do not use emoji in generated UI, as icons, or as icon recommendations.
- Prefer an appropriate **icon library**.
- **Do not assume one icon library is universally best** — the selection system may evaluate
  icon libraries by project requirement, through the same pipeline as any other capability.

Phase 01 measured **155 emoji across 29 files** in this repository. Recorded as a known issue;
remediation is out of Phase 04 scope.

---

## 8. Agent neutrality (§3, §15)

The capability model depends on **no specific agent**. It uses portable artifacts only:
Markdown, JSON, plain shell. Slash commands are **not** a mandatory dependency.

See `AGENT-INTEROP.md` for how any agent consumes the registry.
---