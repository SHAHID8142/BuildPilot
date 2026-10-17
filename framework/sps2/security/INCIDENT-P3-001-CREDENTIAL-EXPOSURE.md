# INCIDENT-P3-001 — Credential Exposure in `.claude/settings.json`

**Incident ID:** `INCIDENT-P3-001`
**Status:** `CONTAINED_IN_WORKING_TREE / REVOCATION_EXTERNAL_ACTION_REQUIRED`
**Detected:** 2026-10-03 during P3 pre-commit review
**Investigated:** 2026-10-03 (this remediation pass)
**Severity:** HIGH (live production credential written into a tracked file)

| **Revocation** | **REPORTED REVOKED BY USER (2026-10-03)** — user-attested; **not independently verified** by this agent (`EV-SEC-011`, `EV-SEC-012`) |

> The credential value is **never** reproduced in this record. It is referenced
> only by fingerprint: SHA-256 `6ebcb3ea914cea56…`, length 73 characters.

---

## 1. Summary

A live `ANTHROPIC_AUTH_TOKEN` value was written into the git-tracked file
`.claude/settings.json`. The write was performed by the **agent harness**
(Cline), not by the SPS 2.0 implementation. The value was detected during P3
pre-commit review and **excluded from the P3 commit**.

## 2. Affected artefacts

| Artefact | Status |
|---|---|
| `.claude/settings.json` (working tree) | **CONTAINED** — token key removed |
| Git index | **CLEAN** — never staged |
| `HEAD` / any SPS 2.0 commit | **CLEAN** — never committed |
| Legacy repository | **CLEAN** — no match |
| Build/artifact files | **CLEAN** — no build directories exist |
| Cline checkpoint ref `refs/cline/checkpoints/1791003785510_kp0kg/18` | **EXPOSED, unreachable from HEAD** |

## 3. Facts (observed)

- **F1** The working-tree file contained `env.ANTHROPIC_AUTH_TOKEN`, a 73-character
  value, before remediation. *(pre-remediation inspection)*
- **F2** The committed version of the file is `{"enabledPlugins": {}}` — it has
  never contained an `env` block. *(§4.2)*
- **F3** `git rev-list --all` yields 25 commits; **none** contains the value.
- **F4** `git log --all -S 'sk-or-v1'` returns **no commits**.
- **F5** Exactly one dangling commit, `a7767cf`, contains the value. Its subject is
  `On main: cline checkpoint session=1791003785510_kp0kg run=18`, dated
  2026-10-03 22:17:40 +0600.
- **F6** `git merge-base --is-ancestor a7767cf HEAD` returns non-zero: the commit
  is **not reachable from HEAD** and belongs to no branch.
- **F7** Of the three Cline checkpoint refs (5, 7, 18), only ref `18` contains the
  value.
- **F8** No SPS 2.0 or legacy file instructs any agent to write this value.
  The only occurrence of the string `ANTHROPIC_AUTH_TOKEN` inside `sps2/` is in
  this incident's own evidence record, which names the credential class only.
- **F9** The value was removed from the working tree on 2026-10-03 by deleting
  only the `ANTHROPIC_AUTH_TOKEN` key. The other five settings were preserved.

## 4. Git forensics

### 4.1 Working tree
Tracked, modified, never staged. Before remediation it contained the credential.

### 4.2 Index and HEAD
```
index  contains token: False
HEAD   contains token: False
```
The committed file is exactly:
```json
{
  "enabledPlugins": {}
}
```

### 4.3 P3 commit
`34c473ae3eaf6fbb4f991a70d200de3a6d8a3c6b` — the token is **absent**. It was
excluded with `git reset` before staging.

### 4.4 History
No reachable commit contains the value. One **dangling** checkpoint commit does.

## 5. Containment performed

| Action | Result |
|---|---|
| Removed `env.ANTHROPIC_AUTH_TOKEN` from the working tree | Done |
| Preserved the other five `env` settings | Done |
| Added `.claude/settings.local.json` to `sps2/.gitignore` as a prevention measure | Done |
| Added `sps2/security/scan_secrets.py` (metadata-only scanner) | Done |
| Added `sps2/security/test-secret-safety.sh` (synthetic-fixture negative test) | Done |

## 5a. Ineffective measure observed (not adopted)

A `.claude` entry appeared in the **root** `.gitignore` during this session. It
was **not authored by this remediation**; its provenance is unattributed.

It is also **ineffective**: `.gitignore` does not apply to already-tracked paths,
and `.claude/settings.json` is tracked (`git ls-files .claude` returns it). The
rule therefore protects nothing and could mislead a future reader into believing
the path is protected.

It was **not committed** and is left unmodified in the working tree. Making it
effective would require `git rm --cached .claude/settings.json`, which changes
tracking state and belongs to a user decision, not to incident containment.

The protection actually applied by this remediation is the
`settings.local.json` entry in `sps2/.gitignore` plus the scanner, both validated.

## 6. Remediation NOT performed, and why

| Action | Reason |
|---|---|
| Deleting the Cline checkpoint ref | **Stop condition.** Destructive Git object removal was not authorised. Reported instead. |
| Rewriting Git history | Not required: no reachable history contains the value. |
| Revoking the credential | `REVOCATION_EXTERNAL_ACTION_REQUIRED` — no credential-management API is available here, and this agent must not invent or rotate credentials. |
| Reverting `.claude/settings.json` to HEAD | Would destroy five active session settings. Selective removal was used instead. |
| Modifying `~/.claude`, `~/.config` or global Git config | Out of scope and prohibited without evidence. |

## 7. Residual risk

1. **The credential remains valid.** It was removed from disk, not revoked. Anyone
   who obtained it retains access. **This is the dominant risk.**
2. **A dangling Git object still contains it** and is recoverable locally via the
   Cline checkpoint ref. It is not pushed and not reachable from `HEAD`, so the
   risk is local-only unless the repository is published with reflogs.
3. **The harness may rewrite the file.** Removal is not durable while the harness
   manages this path. Detection must be re-run after any future session.
4. **Scanner coverage is pattern-based.** Absence of a pattern match is not proof
   that no other credential shape exists.

## 8. Next actions (for the user)

1. ~~Revoke the exposed `ANTHROPIC_AUTH_TOKEN` at the provider.~~ **Done, per
   user report (2026-10-03).** This agent cannot verify provider-side state.
2. Decide whether to purge the Cline checkpoint ref locally (`a7767cf`). It is
   the only remaining location holding the value.
3. Re-run `bash sps2/security/test-secret-safety.sh` and
   `python3 sps2/security/scan_secrets.py .` after any future session.
4. Before publishing, confirm no checkpoint refs or reflogs are included.

## 9. Evidence

`EV-P3-010` (initial detection) and `EV-SEC-001` … `EV-SEC-016` in
`sps2/evidence/SEC-P3-INCIDENT-EVIDENCE.json`.

## 10. Post-revocation verification (2026-10-03)

| Surface | Result |
|---|---|
| Working tree `.claude/settings.json` | Credential key **absent**; 5 unrelated settings preserved |
| Git index | `enabledPlugins` only — **no credential** |
| `HEAD` | `enabledPlugins` only — **no credential** |
| 19 commits reachable from `main` | **0** contain the real credential |
| 3 commits | Contain the **synthetic** test fixture (self-referential test, by design) |
| 1 off-main harness checkpoint (`a7767cf`) | **Still contains the credential**; retained, not modified |

**Revocation status:** reported revoked by the user. This agent could **not**
independently verify it: the value was removed from disk during containment, so
no validity probe could be run without re-exposing and transmitting it, which
this agent is not authorised to do. Recorded as **USER-ATTESTED**, not verified.