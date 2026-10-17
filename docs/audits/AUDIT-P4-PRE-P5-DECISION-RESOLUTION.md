# P4 PRE-P5 DECISION RESOLUTION REPORT

**Generated:** 2026-10-04
**Repository state:** `main` @ `a549145`, no remote configured, nothing pushed
**P4:** APPROVED · **P5:** NOT_STARTED / NOT_APPROVED · **Promotion:** 0 of 5

Three of the four outstanding decisions were resolved. **The licence remains an
explicit user decision and was NOT made on your behalf.**

---

## 1. `skills/sps-cms` provenance finding

**Finding: `UNKNOWN`** (leaning project-authored).

Recorded in `sps2/decisions/PROVENANCE-SPS-CMS.json`.

### Evidence pointing to project authorship

- `package.json`: author `SHAHID8142`, licence `MIT`, repo `github.com/SHAHID8142/sps-cms.git`
- `README.md` footer: `MIT (c) SHAHID8142`, linking to that same account
- The parent repo self-identifies as `github.com/SHAHID8142/Shahid-Personal-SkillSet`
  in `get-sps.sh`, `scripts/sps-update.sh`, `scripts/update-sps.ps1` — same owner
- `INSTALL.md`/`README.md` fetch from `raw.githubusercontent.com/SHAHID8142/sps-cms/`
  — self-referential
- No `forked from` / `based on` / `adapted from` / `vendored` / `derived from`
  anywhere across 56 files
- No `@license`, `@preserve` or `SPDX-License` header anywhere
- No vendored or minified third-party library. The earlier "React from" hits were
  prose fragments in template files, **not** third-party headers
- WordPress / Sanity / Contentful appear only as supported CMS targets and
  comparison tables, never as sources of code
- `AUTO-SYNC-PROTOCOL.md` describes database record sync inside the CMS, not
  source-code sync from upstream

### Why it is `UNKNOWN` and not `VERIFIED_PROJECT_AUTHORED`

- Git history for this path is a **single atomic import** in baseline `10ab67a`
  (56 files, 3939 insertions, all additions). There is no authoring history.
- **All provenance evidence is self-declared** by the party that would benefit
  from a permissive licence. Self-declaration cannot establish ownership.
- I could not confirm `SHAHID8142` is your account — that needs external
  verification, which I deliberately did not perform.
- I could not confirm the local content matches the upstream repository, so it
  is unknown whether this copy came from upstream, from a different licence
  state, or was written independently.

**To upgrade this to `VERIFIED_PROJECT_AUTHORED`, one confirmation from you
suffices:** that `SHAHID8142` is your account, and that `skills/sps-cms` is your
own original work or was taken from a repository you control under the MIT terms
it already declares.

**If confirmed:** the finding upgrades, and the licence becomes a straightforward
choice — the component's existing MIT would be consistent with a repo-wide MIT or
Apache-2.0.
**If not confirmed:** the component is MIXED or third-party and must be excluded
from the repo licence or relicensed separately.

---

## 2. Licence status

**`PENDING_USER_DECISION`. No licence was chosen, inferred, or installed.
---

## 3. `.claude/settings.json` final state

**Treatment A + C applied** as instructed. Resolved in
`sps2/decisions/OPEN-DECISION-CLAUDE-SETTINGS.json`.

| Check | Result |
|---|---|
| HEAD blob verified credential-free **before** restoring | Yes — only `enabledPlugins`, no `env` block |
| `git restore` executed | Yes |
| File present | Yes |
| Matches HEAD | Yes |
| Working-tree status | **Clean** |
| Credential keys | **none** |

**Guard retained permanently:** `validate-p4.sh` §12b checks the **committed
blob at HEAD**, so a credential can never be published by a future commit
regardless of what the harness writes. `POSCTRL-E` proves the guard is not
vacuous.

No credential value was read, printed, hashed, logged or transmitted at any point.
No provider-side probe was performed.

---

## 4. Checkpoint `a7767cf`

**`PRESERVED_BY_USER_DECISION` — intact and unmodified.**

- `git cat-file -t a7767cf...` → `commit`
- SHA unchanged: `a7767cf5f761cab4aa633c1cbc7604f83e4d14f8`
- No history rewrite, reflog expiry, garbage collection or force-push
- Not deleted

It remains the only credential-bearing commit, and P3 reports that explicitly:

```
WARN  PRESERVED_CHECKPOINT_HOLDS_CREDENTIAL: a7767cf5f761
      (accepted by user decision; removal would require a forbidden history rewrite)
PASS  no commit outside the preserved checkpoint contains a credential
```

Incident classification **`USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED`** — unchanged.
Revocation remains user-attested and was **not** independently verified.

---

## 5. `.kilo/worktrees/` finding and treatment

**Classification: `GENERATED_TOOLING_STATE`. Action taken: none.**

Evidence:

- Nested git repository containing a complete duplicate checkout of this project,
  including its own `.claude` directory
- Name `soft-hair` is a generated random identifier
- Contains build/test output artifacts such as `.test.out`
- The tool ships its own `.kilo/.gitignore`, confirming it manages its own state
- Its `.claude/settings.json` holds only `enabledPlugins` — no `env`, no credential

**It is already excluded** via `.git/info/exclude` line 9 (`.kilo/worktrees/`),
added by the tooling itself. A dry-run `git add -A` stages nothing from it.

**No deletion and no `.gitignore` change.** Because evidence shows it is already
excluded, there is no live hazard and therefore no evidence-based reason to
broaden `.gitignore`.
---

## 6. Production capability registry

**Unchanged, exactly as instructed.**

| Capability | State | Blocking gates |
|---|---|---|
| CAP-P03-001 … CAP-P03-004 | `REMAIN_CANDIDATE` | D, H |
| CAP-P03-005 (SEO) | `DEFER` | D, F, H, K |

**0 of 5 promoted.** Gate H requires explicit user production approval, which was
**not** given. `CONF-001` remains `UNRESOLVED`; no LCP/INP thresholds; no fabricated
SEO capability or provenance.
No LICENSE/LICENCE/COPYING file was created.**

**No conflict was found** that blocks a permissive licence — there is simply no
evidence of third-party derivation. But absence of a conflict is not proof of
clean provenance, so investigation **stopped before applying a licence**, exactly
as instructed.

The licence is doubly yours: it was never yours to delegate, and it is
additionally gated on the provenance confirmation above.

Options remain: MIT · Apache-2.0 · BSD-3-Clause · MPL-2.0 · GPL-3.0 · AGPL-3.0 ·
None (all rights reserved).

**Constraint carried forward:** a licence unblocks **gate D only**. Gate H is
independent, so `0/5 promoted` would still hold immediately after any licence
decision.
## 7. Validator results — all pass, 0 failures

| Validator | Result |
|---|---|
| P4 | 56 checks, 0 failed, 22 negatives, 3 controls |
| P3 | 67 checks, 0 failed, 18 controls |
| P2 | 69 / 0 · 22 negatives |
| P1 | 73 / 0 · 25 negatives |
| governance · control · capability | 53/0 · 49/0 (8 neg) · 55/0 (16 neg) |
| SPS lint | PASS |
| secret-safety | 9 / 0 |
| emoji | 89 files, 0 violations |
| repository secret scan | clean |

## 8. Negative-test results

**P4:** 22 negative cases rejected, **0 missed**, 3 positive controls.

**P3 history-credential mutation test — all 4 required scenarios:**

| Scenario | Expected | Result |
|---|---|---|
| clean history | pass | `rc=0`, correct |
| preserved checkpoint only | pass + classified | `rc=0`, `classified=True` |
| checkpoint + second offender | **fail** | `rc=1`, 2 offenders |
| lone non-checkpoint offender | **fail** | `rc=1` |

Wired permanently into `validate-p3.sh` so it runs on every validation.

Additional mutation tests this stage: agent upgrading provenance to `VERIFIED_*`
→ caught; `UNKNOWN` with stripped evidence limits → caught; agent self-answering
the licence → caught.

---

## 9-13. Files, commit, tree, boundaries

**Changed (7):** `sps2/decisions/PROVENANCE-SPS-CMS.json` (new) ·
`sps2/decisions/OPEN-DECISION-{LICENCE,CLAUDE-SETTINGS}.json` ·
`sps2/tools/test-history-credential-check.py` (new) ·
`sps2/tools/validate-{p3,p4}.sh`

**Commit:** see final report. **Working tree:** clean apart from any harness
changes. **Remote:** none — nothing created, nothing pushed.

**P5 was NOT started.** No P5 artefact exists. No capability was promoted. No
licence was chosen. No legacy file was modified. No dependency, skill, MCP or
external code was installed. No machine-global configuration was changed.

> **Caveat for you:** `.git/info/exclude` is *local* and is not committed or
> shared. A collaborator cloning this repo would **not** inherit the exclusion and
> would see `.kilo/worktrees` as untracked. Committing a shared exclusion is a
> user decision and was not taken. Also note only `.kilo/worktrees` is excluded,
> not `.kilo` itself.

---
