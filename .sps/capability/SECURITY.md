# Capability Security & MCP Evaluation

**Phase:** `PHASE-04` · **Status:** `AWAITING_USER_APPROVAL`

> Capability discovery is itself a **supply-chain risk**. This gate exists because an agent
> that can discover and install capabilities can be induced to install something hostile.

---

## 1. Threat model (§13)

| Threat | Example | Control |
|---|---|---|
| Malicious capability | Skill with a hidden payload | Security gate + provenance |
| Malicious MCP | Tool harvesting env vars | MCP-specific evaluation (§5) |
| Abandoned repository | Unmaintained, now attacker-owned | Maintenance status required |
| Compromised package | Legitimate name, new malicious release | Version pinning + `review_due` |
| Typosquatting | `vercel-react-best-pratices` | Official-source check |
| Suspicious install script | Post-install download | Install-method inspection required |
| Excessive permissions | MCP requesting broad filesystem access | Permission budget check |
| Unknown maintainer | Anonymous, unverifiable | Trust level recorded |
| Untrusted download source | HTTP, random mirror | Source rank (§16 of the model) |
| Dependency vulnerabilities | Transitive deps | Recorded as `UNKNOWN` unless checked |
| Licence risk | Copyleft in a proprietary project | Licence compatibility check |

---

## 2. Security status — the UNKNOWN rule

**An unknown security status is not a safe security status.**

| `security_status` | Meaning | Installable? |
|---|---|---|
| `VERIFIED_SAFE` | Reviewed against evidence | Yes, after approval |
| `REVIEWED_LOW_RISK` | Reviewed; residual risk accepted | Yes, after approval |
| `SUSPECTED_RISK` | Signals observed | **No** |
| `VULNERABLE` | Advisory or issue confirmed | **No** |
| `UNKNOWN` | Not assessed | **No** — treated as unsafe |

**Rule:** presenting `UNKNOWN` as `VERIFIED_SAFE`, or any safe-equivalent, is a validation
failure (`CASE C`). This is the single most important rule in this document: an agent must
never launder ignorance into assurance.

---

## 3. Security evaluation contract (§7 criteria 5, 10)

Every candidate must record:

| Field | Meaning |
|---|---|
| `security_status` | Enum above — never optimistically defaulted |
| `security_evidence` | What was actually checked, with source and date |
| `install_method_reviewed` | Install scripts/hooks inspected? yes/no/unknown |
| `permissions_required` | Filesystem/network/credential scope |
| `network_access` | Outbound destinations |
| `credentials_required` | Secrets needed, and their handling |
| `maintainer_known` | Named maintainer, or `UNKNOWN` |
| `repository_url` | Official repository, verified not a typosquat |
| `licence` | Licence identifier, or `UNKNOWN` |
| `dependency_count` | Direct dependencies, or `UNKNOWN` |

**Uninstall/rollback method must also be recorded before installation** — a capability that
cannot be removed cleanly is not eligible.

---

## 4. Gates by action class

From `CONTROL-MODEL.md` §4 action classes:

| Action | Minimum gate |
|---|---|
| `READ`, `ANALYZE` | None |
| `EXECUTE` | Evaluation + verification |
| `WRITE` | Approval required |
| `INSTALL` | **Level 3** — security gate + user approval + project-local method |
| `DELETE`, `DESTRUCTIVE` | **Level 4** — rollback plan + user approval |
| `DEPLOY`, `PUBLISH` | **Level 4** — user approval + rollback |

---

## 5. MCP evaluation contract (§14)

MCP servers are capabilities of type `MCP`. They are **never** assumed safe or necessary.

| Field | Purpose |
|---|---|
| `mcp_name` | Server name |
| `transport` | stdio / http / sse |
| `source_url` | Where obtained |
| `maintainer` | Named owner or `UNKNOWN` |
| `permissions` | Tools and resources exposed |
| `data_access` | What project/user data it can read |
| `network_access` | Outbound calls |
| `credentials_required` | Tokens/keys needed |
| `install_mechanism` | Exact command or manual steps |
| `project_local_feasible` | Can it run without global config? |
| `rollback` | How to remove |
| `trust_level` | `VERIFIED` / `PARTIAL` / `UNTRUSTED` |
| `trust_evidence` | Basis for that level |

**Rules:**
1. **No MCP is installed during Phase 04.** Installing requires a separately approved action.
2. `trust_level: UNTRUSTED` or `UNKNOWN` blocks installation (`CASE L`).
3. An MCP requiring global config to function is a **material decision** — it triggers the
   no-assumption rule (`ENFORCEMENT.md` §3) and must not be done silently.
4. Every MCP must have a stated `rollback` before approval.

---

## 6. Project-local activation (§4)

Default lifecycle is strictly local:

```
discover -> evaluate -> approve -> install LOCALLY -> record LOCALLY -> use LOCALLY
```

Global installation is **exceptional**:
- Requires explicit user request.
- Passes the same security and approval gates.
- Must record `global_installation_authorized_by`.

**Absolute prohibitions** (machine-checked):
- No modification of global skill directories, global MCP config, global agent config, shell
  profiles, global package config, or OS config without explicit future approval (`CASE D`,
  `CASE N`).
- No silent installation of anything.

The validator checks that no project-local capability record declares a global install scope
without a matching user authorization field.