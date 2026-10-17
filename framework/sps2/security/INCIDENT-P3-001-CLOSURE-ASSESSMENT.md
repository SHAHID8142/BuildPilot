# INCIDENT-P3-001 — Closure and Approval-Readiness Assessment

**Incident ID:** `INCIDENT-P3-001`
**Assessment date:** 2026-10-03
**Assessed by:** SPS 2.0 agent (isolated closure pass)
**Scope:** security-incident closure and approval-readiness only. No P4 work.

> The credential value is **never** reproduced in this document. It is referenced
> only by fingerprint: SHA-256 `6ebcb3ea914cea56…`, length 73 characters.

---

## 1. Classification key

| Tag | Meaning |
|---|---|
| **FACT** | Directly observed and reproducible in this repository |
| **USER_ATTESTATION** | Asserted by the user; not independently verified here |
| **INFERENCE** | Reasoned conclusion from verified facts |
| **UNRESOLVED** | Open question; must not be treated as closed |

---

## 2. Incident status

| Field | Value |
|---|---|
| Incident status | **CONTAINED / REVOLUTION_USER_ATTESTED / FORENSIC OBJECT RETAINED** |
| Containment status | **COMPLETE** for the working tree, index and mainline history |
| Revocation status | **`USER_ATTESTED`** |
| Evidence status | **COMPLETE** — 16 records: 11 FACT, 2 INFERENCE, 3 UNRESOLVED |
| P3 approval-readiness | **READY FOR USER APPROVAL** |

---

## 3. Verified state

### 3.1 Credential surfaces — FACT

| Surface | Result |
|---|---|
| `.claude/settings.json` (working tree) | **0** credential-shaped matches; `ANTHROPIC_AUTH_TOKEN` key absent; 5 unrelated `env` settings preserved |
| Git index | **0** matches; contains only `enabledPlugins` |
| `HEAD` | **0** matches; contains only `enabledPlugins` |
| Mainline history (20 commits reachable from `main`) | **0** matches of the real credential |
| Pinned checkpoint `a7767cf` | Retained; its blob hashes to the recorded fingerprint (**matches: True**) |

### 3.2 Synthetic fixture distinguishability — FACT

The negative test uses the literal fixture `sk-or-v1-FAKEFAKEFAKE…`. Its SHA-256
**does not** equal the recorded real-credential fingerprint
(`== FP_REAL` evaluates **False**). The two are therefore provably distinct, and
the scanner distinguishes them by value, not by proximity.

The pinned checkpoint's blob, hashed in memory and compared without being
emitted, **does** match the real fingerprint. This confirms the scanner's
real/fixture discrimination is sound.

### 3.3 Revocation — USER_ATTESTATION

The user states the credential was revoked at the provider on 2026-10-03.

**Recorded limitation.** This agent cannot and did not verify provider-side state.
The credential was removed from disk during containment, so no value was available
to test; a probe would have required transmitting it, which is not authorised and
risks logging the value. **No claim of independent provider verification is made.**

---

## 4. Forensic preservation — FACT

The following were deliberately **not** performed, per instruction:

- dangling checkpoint `a7767cf` **not** purged
- no history rewrite
- no `git reflog expire`, no `gc`, no object deletion
- no force-push, no remote created

The checkpoint is retained deliberately as forensic evidence. Its presence is
recorded, not concealed.

## 4a. Root `.gitignore` condition — UNRESOLVED

The root `.gitignore` gained **2 unattributed lines** during the session:

```
.claude/
.claude/settings.json
```

This is **not SPS-authored work.** It was neither adopted nor broadened by this
closure pass, and it is left uncommitted.

**Effect on current security posture: NONE for the exposed path.**
`.gitignore` does not apply to tracked files, and `.claude/settings.json` is
tracked. The rule cannot protect it.

**Effect on untracked paths: it would ignore future files under `.claude/`.**
That is a side effect, not a remediation. The SPS-authored prevention measure is
the narrower `.claude/settings.local.json` entry in `sps2/.gitignore`.

Making the root rule effective requires `git rm --cached`, which changes tracking
state and is a user decision, not a containment action.

---

## 5. Residual risks

| # | Risk | Severity | Basis |
|---|---|---|---|
| R1 | Credential value still present in pinned checkpoint `a7767cf` | **LOW** (local, unreferenced) | FACT |
| R2 | Revocation not independently verified | **LOW–MEDIUM** | USER_ATTESTATION |
| R3 | Harness may rewrite `.claude/settings.json` | **MEDIUM** | INFERENCE |
| R4 | Scanner is pattern-based; a clean scan is an observed absence, not proof of safety | **LOW** | FACT |
| R5 | Root `.gitignore` rule is unattributed, ineffective for the tracked path, and could mislead a reader | **LOW** | FACT |

**Risk 3 (INFERENCE):** containment is not durable while the harness manages that
path. Re-run `scan_secrets.py` after any future session.

---

## 6. Unresolved decisions (user-owned)

1. Purge or retain checkpoint `a7767cf` as forensic evidence.
2. Whether to `git rm --cached .claude/settings.json` so ignore rules can apply.
3. Whether to accept the unattributed root `.gitignore` lines, keep, or revert.
4. **P3 approval** — explicitly not granted by this assessment.

---

## 7. Approval-readiness

| Criterion | Status |
|---|---|
| Implementation complete | YES (`34c473a`) |
| Validation complete | YES (7 validators + secret-safety suite) |
| Negative tests present | YES (18 P3 controls; 9 secret-safety checks) |
| Evidence recorded | YES (16 incident records) |
| Provenance traceable | YES (static; not runtime — not claimed) |
| Security incident contained | YES |
| Revocation | USER-ATTESTED (limitation recorded) |
| Legacy untouched | YES (diff = 0) |
| Machine-global untouched | YES |
| P3 self-approved | **NO** — correct |

**Conclusion: P3 is ready for a user approval decision.**

## 8. P4 boundary

**P4 MUST NOT START.** No capability was added, promoted, installed or selected.
No CMS, SEO, MCP, installer or selection logic was touched. P4 remains
`NOT_STARTED / NOT_APPROVED`.