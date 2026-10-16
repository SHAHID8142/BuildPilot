# P4 PRE-P5 DECISION-READINESS REPORT

**Generated:** 2026-10-04
**Repository state:** `main` @ `85407eb`, no remote configured, nothing pushed
**P4:** APPROVED · **P5:** NOT_STARTED / NOT_APPROVED

This report records what was inspected, what was found, and which decisions
remain yours. **No decision was taken on your behalf.** No licence was chosen,
no capability was promoted, and P5 was not started.

---

## 1. Licence options requiring your decision

**Current state:** `UNRESOLVED`. No `LICENSE`, `LICENCE` or `COPYING` file
exists anywhere in the repository. Recorded as `PENDING_USER_DECISION` in
`sps2/decisions/OPEN-DECISION-LICENCE.json` (`DEC-0023`).

### Repository facts that bear on the choice

| Fact | Value |
|---|---|
| Licence file present | No |
| Root manifest licence field | None |
| Vendored third-party code | None found |
| Dependency manifests | `skills/sps-cms/package.json` only |
| `skills/sps-cms` declares | `"license": "MIT"`, author `SHAHID8142`, upstream repo URL |

> **The one thing that can invalidate a permissive choice:**
> `skills/sps-cms` already declares MIT and points at an upstream repository.
> If that component is a copy of someone else's project rather than your own
> original work, you may not hold the right to relicense it. This must be
> settled before any permissive licence is applied to the whole repository.

### Options

| Option | Type | Key consequence for this repository |
|---|---|---|
| **MIT** | Permissive | Broad reuse with attribution. No patent grant. Consistent with the existing `sps-cms` MIT declaration. |
| **Apache-2.0** | Permissive | Adds an express patent grant plus patent-retaliation. Stricter NOTICE discipline on redistribution. |
| **BSD-3-Clause** | Permissive | MIT plus a no-endorsement clause. No patent grant. |
| **MPL-2.0** | Weak copyleft | Modified files stay MPL and must be published. Higher compliance burden. |
| **GPL-3.0** | Strong copyleft | Any distributed derivative must be GPL and open-sourced. Viral. |
| **AGPL-3.0** | Strong copyleft | As GPL, plus source publication for network use. Strictest listed. |
| **None (all rights reserved)** | Proprietary | The current legal default, and a valid deliberate choice. Gate D keeps blocking; P4's outcome is unchanged. |

**Effect of choosing:** a licence unblocks **gate D only**. It does **not**
promote anything. **Gate H** (explicit production approval) is independent and
---

## 2. Recommended treatment of `.claude/settings.json`

**State: `PENDING_USER_DECISION`** in
`sps2/decisions/OPEN-DECISION-CLAUDE-SETTINGS.json` (`DEC-0024`).
**No treatment was applied.** The file was neither modified nor deleted.

### What inspection found

Inspection read **key names and presence only**. No credential value was
printed, hashed, logged or transmitted, and no provider-side verification was
attempted.

| Finding | Value |
|---|---|
| Tracked in HEAD | Yes |
| Committed content at HEAD | `{"enabledPlugins": {}}` — **no env block, no credential** |
| Working-tree file present | **No** (deleted by the harness, unstaged) |
| Commits touching the path | 1 (`10ab67a`, the pre-remediation baseline) |
| Commits holding a credential in this path | **1** |
| That commit | **`a7767cf`** — the forensic checkpoint you ordered preserved |
| Baseline `10ab67a` holds a credential | **No** |

### Material correction

The working assumption carried through P4 — that the credential was committed
to the repository — is true for **exactly one commit**, `a7767cf`, which is the
preserved forensic checkpoint. Both the baseline commit and current HEAD hold a
credential-free file.

The exposure surface is therefore:

1. **one deliberately preserved commit**, and
2. **the working tree**, which the harness rewrites at will.

### Options

| Option | Action | Consequence |
|---|---|---|
| **A** | Keep tracked; enforce a committed-blob guard | **Implemented now.** `validate-p4.sh` §12b checks the *committed* blob at HEAD, so no credential can be published by a future commit. `POSCTRL-E` proves the guard is not vacuous. No structural change, no harness disruption. |
| **B** | `git rm --cached` + `.gitignore` | Strongest guarantee — the path can never be committed. Changes repository structure; collaborators lose tracked `enabledPlugins`; may disrupt the harness. Does not affect history. |
| **C** | `git restore` the file | Clears the spurious deletion, restores a credential-free file, leaves the tree clean. No protection against future rewrites. |
| **D** | Rewrite history to purge `a7767cf` | **PROHIBITED** by your standing decision to preserve the checkpoint. Not attempted; recorded only so the option set is complete. |

### Recommendation

**Option A (already implemented) plus Option C.** Together they keep the
harness working, guarantee that no credential can be published in a new commit,
---

## 3. Additional user decisions required before P5

| # | Decision | Blocking | Why it is yours |
|---|---|---|---|
| 1 | Repository licence | Gate **D** | A legal and ownership decision. Cannot be inferred. |
| 2 | `.claude/settings.json` treatment (A/B/C) | Repo hygiene | Options B and C change repository structure or the working tree. |
| 3 | Production promotion approval | Gate **H** | Independent of the licence. **Not** granted by the P4 approval. |
| 4 | `skills/sps-cms` provenance | Licence validity | Determines whether a permissive licence can validly cover the repository. |

**Yes — P5 cannot safely begin yet.** Decisions 1, 2 and 3 are all outstanding.
Decision 4 is a prerequisite to decision 1.
remains unsatisfied, so `0/5 promoted` would still hold immediately after a
licence decision.
## 4. Newly discovered discrepancies

### 4.1 A P3 security check was passing vacuously — most important finding

P3's *"Credential must not be in any reachable commit"* read the token from the
**working-tree** `.claude/settings.json`. Because the harness deleted that
file, the token read as absent and the entire scan was skipped — the check
reported **PASS while verifying nothing**. A false assurance on the single most
important security invariant in the project.

Rewritten to be key-based and to always evaluate every commit. It now reports
the truth:

```
WARN  PRESERVED_CHECKPOINT_HOLDS_CREDENTIAL: a7767cf5f761
      (accepted by user decision; removal would require a forbidden history rewrite)
PASS  no commit outside the preserved checkpoint contains a credential
```

Mutation-tested: whitelisting a second offending commit correctly turns this
into a `FAIL`.

### 4.2 The harness changed the working tree again

`.claude/settings.json` moved from modified to **deleted** between sessions.
It is tracked, so the repository now shows a spurious deletion. Left untouched
per instruction.

### 4.3 `.kilo/worktrees/` appeared

A harness working directory containing a copy of
`skills/sps-cms/GLOBAL-SETTINGS.md` now exists. Not investigated further and not
modified — noted only because it is a new untracked path that a future
`git add -A` could sweep in.

### 4.4 Earlier validator defect, already corrected

The P4 negative suite shared `NP`/`NF` counters with the positive controls, so a
failing control was reported as a missed negative case. Fixed with dedicated
`NNP`/`NNF` counters.

---

## 5. Preserved invariants (unchanged)

- Capability promotion: **0/5**. 4 `REMAIN_CANDIDATE`, 1 `DEFER`.
- `CONF-001 = UNRESOLVED`; no LCP/INP thresholds; no invented SEO claims.
- No fabricated capability provenance.
- P3 incident classification: `USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED`.
  Revocation remains user-attested and was **not** independently verified.
- Checkpoint `a7767cf` preserved. No history rewrite, reflog expiry, garbage
  collection or force-push.
- Legacy repository untouched. No remote, no push, no install, no
  machine-global change.

---

## 6. Stop condition

**P5 was NOT started.** No P5 artefact exists. Work stops here pending your
decisions on items 1-4 in section 3.
