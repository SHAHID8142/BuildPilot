# P2 Security Audit — Agent, Skill and MCP

Phase: roadmap P2 (audit phase 06). Research only. No security code was written.

---

## 1. Headline finding

The official MCP Registry **does not scan server code**. SRC-012 states plainly
that it "delegates security scanning" to underlying package registries and
downstream aggregators, and that host applications should consume aggregators
rather than the registry directly.

Implication: a namespace-verified MCP server is **provenance-verified, not
security-verified**. CAP-024 -> `REJECT` as a trust control. SPS must evaluate MCP
security itself.

## 2. Attack taxonomy (SRC-013, official specification)

Documented classes, recorded verbatim in name:

| Class | Core risk |
|---|---|
| Confused deputy | Proxy obtains authorisation codes without user consent |
| Token passthrough | Tokens passed to unintended recipients |
| SSRF | Server coerced into internal network requests |
| Session hijacking | Session state stolen or reused |
| Prompt injection | Untrusted content instructs the agent |
| Impersonation | Attacker poses as a legitimate party |
| Local MCP server compromise | Malicious local server gains host privileges |
| OAuth authorisation URL validation | Tokens leaked to redirect targets |
| stdio transport in proxies | Arbitrary process spawning |
| Scope minimisation | Over-broad scopes inflate blast radius |

## 3. Provenance model — the transferable part

SRC-012: reverse-DNS namespaces (`io.github.user/server`) verified via DNS or
GitHub challenge. Only the legitimate owner of the account or domain can publish
under that namespace.

CAP-023 -> **ADAPT**. SPS provenance should bind publisher identity to a verifiable
identifier, mirroring this. This is the strongest provenance primitive available
in the ecosystem and costs nothing to adopt.

## 4. Least privilege

SRC-013 prescribes progressive scope minimisation: a minimal initial scope (e.g.
`mcp:tools-basic`) containing only low-risk discovery and read operations, with
incremental elevation via targeted `WWW-Authenticate` challenges.

Named anti-patterns: publishing all scopes in `scopes_supported`; wildcard or
omnibus scopes; bundling unrelated privileges to pre-empt prompts; returning the
entire scope catalog in every challenge; treating claimed token scopes as
authorisation without server-side checks.

CAP-026 -> **KEEP**. This maps directly onto the SPS capability-permission model
established in P1.

## 5. Harness-native controls observed

From SRC-006 (Claude Code, official):

- **Auto mode**: a separate classifier model reviews actions and blocks those it
  judges unsafe; explicit user ask/deny rules still apply and organisations can
  disable it.
- **Manual mode**: starts read-only, prompts before edit or execute.
- **Sandboxed bash**: filesystem and network isolation reduces prompts.
- **Working-directory boundary**: file tools prompt when reading or writing
  outside the start folder — explicitly *a prompt*, so an approved Bash command
  can still write anywhere the user account can.
- **Prompt fatigue mitigation**: allowlisting frequent safe commands per user.
- **Cloud push restrictions**: the proxy rejects branch deletions and non-branch
  pushes; repository branch protection still applies.
- **Audit logging and OpenTelemetry**; ConfigChange hooks can audit or block
  settings changes during a session.

**CAP-006, CAP-007, CAP-008, CAP-009 -> ADAPT.**

Honest caveat from SRC-006 itself: the working-directory boundary is a permission
---

## 6. Agent-agnostic threat mapping

| Threat | Static validation | Runtime validation | Approval | Gating | Evidence |
|---|---|---|---|---|---|
| Malicious skill content | yes | partial | required to install | capability | source provenance |
| Malicious MCP server | manifest/schema checks | tool permission limits | required | scope | namespace + review |
| Prompt injection in untrusted content | no | yes | no | treat as data | blocked execution |
| Secret exposure | yes (pattern scan) | yes | yes for secret access | no | redaction check |
| Tool permission escalation | yes | yes | yes | least privilege | scope log |
| Supply-chain substitution | yes (pinning) | no | required | no | hash/version record |
| Hook abuse | yes | yes | yes | no | hook config audit |
| Approval bypass | yes | yes | n/a | validator refusal | gate refusal record |

**Design conclusion**: only the **first** column can be reliably automated
statically. Everything requiring judgement of untrusted runtime content needs
either least-privilege scoping or explicit human approval. SPS must never claim
static validation is sufficient.

## 7. Untrusted-input discipline applied in P2 itself

Consistent with the brief's source-security rule:

- No install script, package installer, shell snippet, binary, MCP server, hook or
  plugin from any external source was executed.
- All repositories were inspected **statically** over HTTPS.
- No external file was copied into SPS 2.0.
- ECC's `ecc_dashboard.py`, hooks and scripts were read as text only.

## 8. Open findings (not remediated in P2)

| Finding | Status |
|---|---|
| Legacy `KI-01` hardcoded CMS auth-secret fallback | **Open, untouched** — out of P2 scope |
| Phase 01 findings generally | **Open** — remediation deferred |
| ECC secret-handling review | Not performed (would require source audit) |

## 9. OWASP reference

SRC-020 is the OWASP GenAI Security Project (the Top 10 for LLM Applications has
grown into this broader project). Consulted at project level for taxonomy
framing; individual risk entries were **not** enumerated in P2 and are not claimed
(CAP-033, confidence MEDIUM).

## 10. Recommendations

1. Treat namespace verification as provenance only, never as security clearance.
2. Implement progressive scope elevation from the first MCP capability.
3. Require user approval for capability installation regardless of security score.
4. Never describe prompt-based boundaries as OS-level containment.
5. Static validation is necessary, never sufficient.
6. Close `KI-01` in a dedicated remediation phase, not inside research.
prompt, **not** an OS-level guarantee. SPS must not describe it as containment.