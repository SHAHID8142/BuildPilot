# P8 Threat Model — CMS 2.0

**Author**: implementation agent (design author, not a User; not an approval)
**Date**: 2026-10-06
**Scope**: Roadmap P8 CMS 2.0 only. Does not authorise P8 implementation.
**Prerequisite**: P8 Phase 1 requirements approved (commit `8452102`).
**Companion**: `sps2/governance/P8-ARCHITECTURE.json`

---

## 1. What P8 introduces

P8 introduces a **CMS 2.0** with:
- Role-based access control (Super Admin / Admin)
- Content and section model with draft/publish lifecycle
- Unified asset picker (upload, existing media, external URL)
- Preview and publishing workflow
- Append-only audit history
- Project-local, isolated, rollback-safe architecture

P8 is the first SPS 2.0 phase to introduce **user-facing operations** (content creation, publishing, media upload) and **external content fetching** (asset picker external URL). This significantly expands the attack surface.

---

## 2. Assets

| Asset | Owner | Protected by |
|---|---|---|
| Content store | SPS 2.0 project | RBAC + validation + atomic writes |
| Section/layout definitions | Super Admin | RBAC (Super Admin only) |
| Asset store | SPS 2.0 project | Validation + SSRF prevention + size limits |
| Audit log | SPS 2.0 project | Append-only + HMAC signatures |
| User/role assignments | Super Admin | RBAC (Super Admin only) |
| Feature flag | SPS 2.0 project | Project-local state |

---

## 3. Threat actors and failure modes

| Actor / source | Failure mode | Risk |
|---|---|---|
| Admin user | Attempts to modify layout or section structure | Structural integrity breach |
| Admin user | Attempts self-promotion to Super Admin | Privilege escalation |
| External attacker | Malicious file upload (malware, executable) | System compromise |
| External attacker | SSRF via external URL asset picker | Internal network access |
| External attacker | Path traversal in asset storage | Unauthorized file access |
| External attacker | Stored XSS via content injection | Session hijacking |
| External attacker | Content injection via unsanitized fields | Data corruption |
| External attacker | Audit log tampering | Repudiation |
| External attacker | Race condition in publishing | Inconsistent state |
| External attacker | Resource exhaustion (large uploads, many requests) | Denial of service |
| External attacker | Decompression bomb via upload | Denial of service |
| External attacker | Secret leakage via audit or logs | Credential exposure |
| External attacker | Rollback abuse (unauthorized rollback) | Data loss |
| External attacker | Cross-project state access | Isolation breach |
| External attacker | Administrator abuse (Super Admin misconduct) | Governance failure |

---

## 4. Trust boundaries

1. **Super Admin vs Admin boundary** — Admin must never gain Super Admin privileges.
2. **Content vs structure boundary** — Admin edits content; Super Admin edits structure.
3. **Project-local boundary** — P8 state must not leave the repository.
4. **External URL boundary** — External content must be validated, sanitized, and stored locally.
5. **Audit boundary** — Audit log is append-only and tamper-evident.
6. **Feature flag boundary** — P8 can be deactivated without modifying SPS2 core.

---

## 5. Privilege escalation risks

| Threat | Mitigation |
|---|---|
| Admin self-promotes to Super Admin | Role changes require Super Admin; no self-service role modification |
| Admin modifies layout/section | Layout/section operations require Super Admin role |
| Admin deletes content | Content deletion requires Super Admin role |
| Admin rolls back revisions | Rollback requires Super Admin role |
| Admin exports audit logs | Audit export requires Super Admin role |
| Admin administers users/roles | User/role administration requires Super Admin role |

**Machine-testable invariant**: Every operation checks the caller's role against the permission matrix. An operation attempted by an unauthorised role is rejected with a controlled message.

---

## 6. Authorization bypass risks

| Threat | Mitigation |
|---|---|
| Direct API access bypassing UI checks | All authorization is server-side; UI is not trusted |
| Role spoofing | Role is determined from authenticated session, not user input |
| Session fixation | Session tokens are cryptographically random |
| CSRF | All state-changing operations require CSRF tokens |
| IDOR (Insecure Direct Object Reference) | Every object access checks role + ownership |

---

## 7. SSRF risks (external URL asset picker)

| Threat | Mitigation |
|---|---|
| Internal network scanning | Block private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16) |
| DNS rebinding | Resolve DNS and validate IP before fetching; re-validate on redirect |
| Redirect to internal network | Follow redirects with limit (max 5); re-validate each hop |
| Protocol smuggling | Allow only http/https schemes |
| Slowloris | Enforce timeout (30 seconds max) |
| Large response | Enforce size limit (10 MB max) |
| Decompression bomb | Enforce decompression limit (max 10x expansion) |

---

## 8. Malicious upload risks

| Threat | Mitigation |
|---|---|
| Executable file upload | Validate file type against allowlist (images, documents only) |
| Filename path traversal | Sanitize filenames; store with generated IDs, not user-supplied names |
| Large file upload | Enforce size limit (10 MB max) |
| MIME type spoofing | Validate content-type AND file magic bytes |
| Decompression bomb | Enforce decompression limit (max 10x expansion) |
| Malware | No virus scanning in stdlib; record limitation explicitly |

---

## 9. Path traversal risks

| Threat | Mitigation |
|---|---|
| `../` in filenames | Sanitize all user-supplied paths; use pathlib for safe path joining |
| Absolute paths | Reject absolute paths |
| Symlink attacks | Do not follow symlinks; store in dedicated asset directory |

---

## 10. Stored XSS risks

| Threat | Mitigation |
|---|---|
| Script injection in content fields | Sanitize all user-supplied content; escape HTML entities |
| Event handler injection | Strip event handlers (onload, onclick, etc.) |
| JavaScript URLs | Reject javascript: URLs |

---

## 11. Unsafe external content risks

| Threat | Mitigation |
|---|---|
| Malicious external content | Validate content-type; store locally; do not execute |
| External content with embedded scripts | Sanitize before storage |
| External content with tracking pixels | Record limitation; do not claim complete protection |

---

## 12. Audit tampering risks

| Threat | Mitigation |
|---|---|
| Audit log modification | Append-only; no edit/delete API |
| Audit log deletion | Append-only; no delete API |
| Audit log forgery | HMAC-SHA256 chain; each entry signed |
| Audit log repudiation | Include actor, timestamp, before/after state |

---

## 13. Race condition risks

| Threat | Mitigation |
|---|---|
| Concurrent publish operations | Atomic writes (write-temp, validate, rename) |
| Concurrent role changes | Atomic writes; validate before rename |
| Concurrent asset uploads | Atomic writes; unique generated IDs |

---

## 14. Resource exhaustion risks

| Threat | Mitigation |
|---|---|
| Large uploads | Enforce size limit (10 MB max) |
| Many concurrent requests | Rate limiting (to be implemented in Phase 3) |
| Large external URL responses | Enforce size limit (10 MB max) |
| Decompression bombs | Enforce decompression limit (max 10x expansion) |
| Many audit entries | Audit log is append-only; no deletion |

---

## 15. Secret leakage risks

| Threat | Mitigation |
|---|---|
| Hardcoded secrets in code | KI-01 is NEVER COPY; secret detection validator |
| Secrets in audit logs | No credential values in audit entries |
| Secrets in error messages | Controlled error messages; no stack traces |
| Secrets in configuration | All secrets injected via environment variables |

---

## 16. Rollback abuse risks

| Threat | Mitigation |
|---|---|
| Unauthorized rollback | Rollback requires Super Admin role |
| Rollback to malicious state | Rollback creates a new revision; audit log records the rollback |
| Rollback chain corruption | Revisions are immutable; rollback does not delete history |

---

## 17. Tenant/project isolation risks

| Threat | Mitigation |
|---|---|
| Cross-project state sharing | All P8 state is project-local under domain/cms/ |
| Cross-project asset access | Asset paths are project-relative; no absolute paths |
| Cross-project audit access | Audit log is project-local |

---

## 18. Administrator abuse risks

| Threat | Mitigation |
|---|---|
| Super Admin misconduct | Audit log records all Super Admin actions |
| Super Admin privilege abuse | No technical control; governance control (User oversight) |

---

## 19. Safeguards and validation requirements

- P8 validators must pass on the live tree and on every isolated clone
- Role-permission tests must cover every permission in the matrix
- Asset picker tests must cover all three sources and all SSRF preventions
- Audit log tests must verify tamper-evidence
- Secret detection scan must find no hardcoded secrets
- Rollback rehearsal must prove P8 can be removed without modifying SPS2 core
- No P8 implementation artefact may exist while P8 is unauthorised

---

## 20. Explicit prohibited behaviours

- Copying KI-01 (hardcoded secret)
- Exposing layout controls to Admins
- Writing state outside the project
- Modifying SPS2 core, governance, or adapter surfaces
- Installing any dependency, skill, MCP, CLI, or package
- Machine-global state writes
- Promoting or activating any capability
- Resolving CONF-001
- Inventing LCP/INP observations
- Runtime activation of any kind
- P9 or later
- Self-approval of any P8 gate

---

## 21. Acceptance criteria (machine-checkable)

1. Role-permission tests pass for every permission in the matrix
2. Asset picker tests pass for all three sources
3. SSRF prevention tests pass for all blocked IP ranges
4. Audit log tamper-evidence test passes
5. Secret detection scan finds no hardcoded secrets
6. Rollback rehearsal proves P8 can be removed without modifying SPS2 core
7. Production registry byte-identical; legacy diff zero
8. CONF-001 UNRESOLVED; LCP/INP NOT_OBSERVED

---

## 22. Rollback / removal criteria

1. P8 can be deactivated by setting feature flag to false
2. P8 can be removed by deleting domain/cms/
3. Removal leaves SPS2 core validators green
4. No orphaned references after removal
5. Rollback does not touch legacy files or the production registry
