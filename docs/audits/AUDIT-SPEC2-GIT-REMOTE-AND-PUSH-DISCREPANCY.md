# AUDIT-SPEC2 — Git remote and push discrepancy: recorded, not resolved

Audit date: 2026-10-15
Auditor: implementation agent (**not** a User; this record is **not** an approval)
HEAD at audit: `788bf8a` — branch `build/roadmap-p3-completion`
Status: **RECORDED ONLY — NOT APPROVED. Awaiting User decision D1–D5.**
Type: read-only observation. Indexed as `KI-15` in [`.sps/audits/README.md`](.sps/audits/README.md).
Supersedes: none. `DEC-0001` and `DEC-0002` remain in force and are **not** amended or reversed.

> **Why this is an audit and not a decision record.** Every file in `.sps/decisions/` must carry
> `**Decided by:** User` (enforced by `.sps/tools/validate-governance.sh` when `.sps/STATE.md`
> records an `APPROVED` phase). This record documents a discrepancy and requests a decision; it
> decides nothing, so it cannot honestly claim User attribution. Placing it here keeps that
> distinction explicit rather than fabricating an approval.

---

## Purpose

The approver-policy consolidation surfaced a discrepancy between what `DEC-0001` and `DEC-0002`
record about this repository's Git remote and push authorisation, and what the local repository
state actually is. This record states the verified facts and the unresolved disposition. It changes
nothing.

## 1. Directly verified local facts

All read-only. No network was contacted.

| # | Fact | How verified |
|---|---|---|
| F1 | A remote **is** configured: `origin` → `https://github.com/SHAHID8142/Shahid-Master-Skill.git` (fetch and push) | `git remote -v` |
| F2 | Repo-local identity is still the placeholder: `user.name = SPS Governance (local)`, `user.email = sps-governance@local.invalid` | `git config --local user.name/user.email` |
| F3 | Commit authorship: 98 of 99 commits are the placeholder; 1 is `Cline <cline@local>`. **No commit carries a natural-person identity.** | `git log --format='%an <%ae>' \| sort \| uniq -c` |
| F4 | `.git/logs/refs/remotes/origin/main` contains **three** `update by push` entries, all authored by the placeholder, timestamps `1791111562`, `1791113759`, `1791120368` (+0600) | `cat .git/logs/refs/remotes/origin/main` |
| F5 | `.git/logs/refs/remotes/origin/build/roadmap-p3-completion` contains **one** `update by push` entry, timestamp `1791794222` (+0600), also by the placeholder | `cat .git/logs/refs/remotes/origin/build/roadmap-p3-completion` |
| F6 | Local `HEAD` (`788bf8a`) is byte-identical to `origin/build/roadmap-p3-completion` | `git rev-parse HEAD` vs `git rev-parse origin/...` |
| F7 | No pre-existing record names this remote: `grep -rl 'Shahid-Master-Skill'` over `*.md`, `*.json`, `*.sh` returns **zero** hits once **this record itself** is excluded from the result | repository-wide grep, excluding this file || F8 | No record in `.sps/decisions/` or `sps2/decisions/` authorises a remote or a push | full read of both decision directories |

## 2. Recorded statements that conflict with those facts

| # | Record | Recorded statement | Actual | Status |
|---|---|---|---|---|
| C1 | `DEC-0001:37` | `git remote -v` returns empty — `REMOTE_NOT_CONFIGURED` | F1 | **Stale / contradicted** |
| C2 | `DEC-0001:52` | Decision `KEEP_LOCAL_ONLY` — do not configure or add a remote at this stage | F1 | **Contradicted** |
| C3 | `DEC-0001:60-62` | `PUSH_SKIPPED: NO_REMOTE_CONFIGURED` remains the correct push result; no push may be attempted and no remote may be invented until the User issues a new explicit instruction | F4, F5 — four pushes recorded | **Contradicted**; no such instruction found (F8) |
| C4 | `DEC-0002:75-85` | Standing obligation to replace the placeholder identity; *"becomes due the moment a remote is added or the repository is shared"* | F1 + F4/F5 — the trigger condition is met | **Obligation is DUE and NOT discharged** (F2) |
| C5 | `HANDOFF-CURRENT.md:205`, `.sps/STATE.md:86-88,148`, `AUDIT-PHASE-03-ENFORCEMENT-CONTROL.md:51`, `PHASE-04-EVIDENCE.json:166,210`, `AUDIT-ROADMAP-P3-SECONDARY-REVIEW.md:311` and two further audit reports | No remote configured / nothing pushed | F1, F4, F5 | **Stale** (these are point-in-time reports) |

## 3. Evidence and confidence

- **F4/F5 are strong evidence that pushes occurred.** Remote-tracking reflogs are written locally by
  `git receive-pack`/`git push` updates and record `update by push` explicitly. They are a reliable
  local record of a push to that remote.
- **What the reflog does *not* establish:** it is a local record. It does not independently prove the
  remote accepted, retained, or still holds the objects, and no remote state was queried. Confidence
  that **pushes were issued**: high. Confidence about the **current remote-side contents**: not
  established, and deliberately not asserted.
- **F6 is arithmetic, not inference:** two local object names are equal.

## 4. What remains unknown

1. Whether the remote's current contents still match what was pushed; no network access was used.
2. Whether the repository was intended to have this remote, or the remote was added deliberately and
   simply never recorded. F7 shows it is undocumented either way.
3. Whether `SHAHID8142/Shahid-Master-Skill.git` is the project's intended upstream. `DEC-0001:43`
   declined to use "the upstream URL referenced in README", while
   `PROVENANCE-SPS-CMS.json:22` records the project as `github.com/SHAHID8142/Shahid-Personal-SkillSet`
   — **a different repository name**.
4. Whether any party outside the User has seen the published commits.

## 5. What requires a future User decision

| # | Question |
|---|---|
| D1 | Is `KEEP_LOCAL_ONLY` still intended? If not, should `DEC-0001` be superseded by a decision that ratifies the remote retroactively? |
| D2 | Should the `DEC-0002` placeholder identity be replaced now (repo-local `git config --local`), given the obligation is due? |
| D3 | Should the remote be retained, repointed, or removed? Note that removing it does **not** un-push; the 99 commits remain published. |
| D4 | Should commit authorship be rewritten to a real identity? This would require a history rewrite and a force-push to an already-published remote, and would destroy the tamper-evidence property `DEC-0001` was created to establish. **Not recommended.** |
| D5 | `.sps/tools/validate-capability.sh` **hard-fails** on any configured remote (`if git remote \| grep -q .; then fail`). Cite the check by command, not line number, because the line moves whenever that file is edited: `grep -n 'git remote' .sps/tools/validate-capability.sh`. By contrast `sps2/tools/validate-sps2.sh` warns and `.sps/tools/validate-governance.sh` passes. Should that control be reconciled with D1? |

## 6. Actions explicitly NOT authorised and NOT taken

No Git remote was added, removed, renamed, or repointed. No Git configuration was written. No commit,
amortisation, amend, rebase, tag, or branch was created or altered. Nothing was pushed, deployed, or
published. No network request was made. `DEC-0001` and `DEC-0002` were **not** edited, superseded, or
reversed — their original text and approval state are untouched. No approval was recorded on the
User's behalf.

## 7. Bearing on the approver-policy work

Git authorship **cannot** serve as approver provenance in this repository, and must not be used as a
migration input: 98 of 99 commits are a placeholder string and the single exception is an agent
identifier (`Cline`). Adopting it as an approver signal would launder a placeholder into apparent
authority. This finding does **not** change any recommendation about the agent-name token policy.

---

## Evidence

- `git remote -v`
- `git config --local user.name` / `user.email`
- `git log --format='%an <%ae>' | sort | uniq -c | sort -rn`
- `cat .git/logs/refs/remotes/origin/main`, `cat .git/logs/refs/remotes/origin/build/roadmap-p3-completion`
- `git rev-parse HEAD` / `git rev-parse origin/build/roadmap-p3-completion`
- `grep -rl 'Shahid-Master-Skill' --include='*.md' --include='*.json' --include='*.sh' .`
  `  | grep -v AUDIT-SPEC2-GIT-REMOTE`   # this record quotes the URL, so it must be excluded

**Outcome:** nothing decided. This record requests User decisions D1–D5 and grants no
approval. It is deliberately not written as `**Decided by:** User`, because nothing here
was decided by the User.