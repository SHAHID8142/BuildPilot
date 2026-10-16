# P2 Comparative Architectural Audit

Phase: roadmap P2 (audit phase 06). Research only. No implementation.
Companions: `P2-CAPABILITY-EXTRACTION.json`, `P2-INTEROPERABILITY-MATRIX.json`,
`P2-SOURCES.json`.

---

## 1. Primary research question

> What is the strongest architecture SPS 2.0 can build by combining the best
> demonstrated ideas from existing agentic-development systems without inheriting
> their unnecessary coupling, vendor lock-in, global-state assumptions, weak
> enforcement, or duplicated functionality?

Answered below in six evidence-backed claims.

---

## 2. Claim 1 — Portability has a real primitive: AGENTS.md

**Evidence**: SRC-014. AGENTS.md is stewarded by the Linux Foundation's Agentic AI
Foundation and lists Codex, Cursor, Gemini CLI, Copilot, opencode, Zed, Aider,
goose, Devin, Junie, Amp, Windsurf and more.

Every harness independently invented its own instruction file
(`.clinerules/`, `.cursorrules`, `CLAUDE.md`, `GEMINI.md`, `.windsurfrules`).
AGENTS.md is the convergence point, and Cline already autodetects several of the
competing formats (SRC-011).

**Decision**: SPS adopts AGENTS.md as its project-local instruction surface. It
does not create a seventh format.

---

## 3. Claim 2 — "Supports every harness" is packaging, not parity

**Evidence**: SRC-001 shows ECC ships fourteen harness directories. No source
demonstrates that hooks fire identically, that skills behave identically, or that
enforcement is equivalent across them.

Cursor limits rules explicitly: they do not affect Cursor Tab, and User Rules are
not applied to Inline Edit (SRC-010). Claude Code cloud sessions read only a
subset of settings — `~/.claude/` is not read at all (SRC-004).

**Decision**: SPS records support per capability per harness with explicit
confidence, and treats `unknown` as a first-class state that blocks any
"universal" claim.

---

## 4. Claim 3 — Enforcement is where harnesses differ most, and where SPS is strongest

**Evidence**: Claude Code offers Auto mode (a classifier model reviews actions),
Manual mode (read-only until approved), a sandboxed bash tool, a working-directory
boundary, and ConfigChange hooks for auditing or blocking settings changes
(SRC-006). Codex adds `allow_managed_hooks_only` in `requirements.toml`, letting
admins ignore user, project and session hook configs (SRC-008), plus a security
CLI emitting SARIF for CI severity policy (SRC-009). Cursor has Team Rules with
managed enforcement (SRC-010).

**Decision**: SPS keeps its Phase 02-04 enforcement model, already agent-neutral
and stronger than prompt-level instruction: a validator that *refuses the
transition*. Capability-installation and global-scope approval are
user-attributable and cannot be inferred (proved in P1 by negative cases C, G, N,
G2).

**Architectural rule learned**: hook availability must never be load-bearing for
governance. Where hooks are absent the validator still blocks. Hooks are an
*optimisation*, not the enforcement layer. This directly addresses the legacy
---

## 5. Claim 4 — The MCP registry is provenance, not security

**Evidence**: SRC-012 states the registry "delegates security scanning" to
package registries and downstream aggregators, that host applications should not
consume it directly, and that it is in preview. Namespace verification via
DNS/GitHub challenge is real and useful.

SRC-013 supplies the actual threat model: confused deputy, token passthrough,
SSRF, session hijacking, prompt injection, impersonation, local server compromise,
OAuth URL validation, stdio transport risks, scope minimisation — with the
explicit anti-pattern of publishing every scope in `scopes_supported`.

**Decision**: adopt reverse-DNS namespace provenance. Reject the registry as a
trust control (CAP-024). SPS must evaluate MCP security itself, using the SRC-013
taxonomy, with minimal initial scope and incremental elevation.

---

## 6. Claim 5 — A persona catalogue is not an orchestration system

**Evidence**: SRC-003 (agency-agents, 570 commits) is markdown personas organised
by division, plus `divisions.json` and `tools.json`. There is no scheduler,
dispatcher, dependency graph, gate or evidence capture.

By contrast SRC-015 documents a real orchestration system: a lead agent that plans
then spawns parallel subagents with independent context windows, writing artefacts
to the filesystem, and evaluating against discrete checkpoints.

**Decision**: role definitions are not orchestration. Worth taking from a persona
catalogue is the *vocabulary* of specialist roles. Worth taking from SRC-015 is
the artefact and checkpoint pattern.

**Confidence note**: the reported 90.2% uplift is a **vendor-internal**
measurement on an internal eval — a real signal, not an independent benchmark.

---

---

## 8. Comparative scoring

Scores are **ordinal judgements from this audit**, not measurements. Each carries
a confidence so a reader can discount it.

| Dimension | Best-evidenced | Score | Confidence | Limitation |
|---|---|---|---|---|
| Agent interoperability | AGENTS.md ecosystem | High | HIGH | Vendor self-listing; parity untested |
| Enforcement / governance | Claude Code + Codex | High | HIGH | Vendor-internal behaviour |
| Skill architecture | Claude Code Agent Skills | High | HIGH | Portable spec, Claude-specific on disk |
| Orchestration | Anthropic research system | High | MEDIUM | Internal eval only |
| Capability breadth | ECC | High | MEDIUM | Per-harness parity unproven |
| Provenance | MCP Registry | Medium | HIGH | In preview; not a security control |
| Memory design | Anthropic artefact pattern | High | MEDIUM | Vendor-internal |
| CMS readiness | Next.js draft mode + ISR | Medium | HIGH | Partial content-delivery evidence only |
| SEO evidence | Google Search Central, web.dev | High | HIGH | CLS verified; LCP/INP unretrieved |
| Project reproducibility | Cline / Claude Code project layers | High | MEDIUM | Global layers still exist |
| Global-state dependence | None (all ship a global layer) | Low | HIGH | Structural limitation |
| Vendor lock-in | OpenCode, AGENTS.md | Medium | MEDIUM | OpenCode remains model-friendly |
| Monolith risk | ECC | Negative | MEDIUM | Large bundled skill corpus |

**Explicit non-conclusion**: no system scored "excellent" overall, because none
combines portability, enforcement, project-locality and non-monolith structure
simultaneously. That is the gap SPS occupies.

---

## 9. Duplication analysis

| Problem | Implementations studied | SPS opportunity |
|---|---|---|
| Project instructions | `.clinerules`, `.cursorrules`, `CLAUDE.md`, `GEMINI.md`, `AGENTS.md` | One project-local surface plus adapter translation |
| Config precedence | Claude 4-level, OpenCode 6-layer, Cursor 3-level | One agent-neutral scope resolver with per-adapter mapping |
| Session state | ECC hooks, Anthropic artefacts, legacy `.sps/STATE.md` | Evidence and handoff artefacts only; no hidden model memory |
| Verification | ECC `verification-loop`, Codex SARIF, Anthropic checkpoints | Validators that block transitions |
| Scope enforcement | Claude permissions, Codex sandbox, MCP scopes | One capability-permission model, minimal initial scope |

**Design rule**: abstract the *problem*, then define one SPS-native mechanism,
rather than choosing one upstream implementation.

---

## 10. Monolith assessment

Is SPS at risk of becoming "hundreds of skills installed everywhere"? The
evidence says yes if it copies ECC's shape: a large bundled skill corpus plus
per-harness global directories.

P2 therefore **rejects** the ECC shape and confirms the P1 architecture:

```text
SPS Core
  -> Capability Registry (project-local, initially empty)
  -> Project Requirements
  -> Capability Selection (research-gated, user-approved where required)
  -> Agent/Harness Adapter (thin, deletable)
  -> Skill / Workflow
  -> Tool / MCP (provenance-checked, least privilege)
  -> Verification (validator blocks without evidence)
  -> Evidence (recorded, reproducible)
  -> Approval (user-only, never inferred)
```

Link-by-link evidence: research gate (SRC-016, SRC-017); provenance (SRC-012);
least privilege (SRC-013); blocking verification (SRC-006, SRC-008, SRC-015);
artefact evidence (SRC-015); project-locality (SRC-004, SRC-011).

---

## 11. Answer, condensed

**Take**: portable project-local instructions (AGENTS.md); a single agent-neutral
control layer that blocks transitions without evidence; least-privilege capability
permissions; filesystem evidence artefacts; namespace-style provenance.

**Reject**: global skill corpora; persona catalogues sold as orchestration;
registries treated as security; auto-learned policy; GUI-first design.

**Refuse to assume**: cross-harness parity; unretrieved numeric thresholds;
documentation implying enforcement.
## 7. Claim 6 — Memory should be an artefact, not a behaviour

**Evidence**: SRC-015 recommends subagents write outputs to the filesystem and
pass lightweight references, explicitly to avoid the "game of telephone". SRC-002
shows ECC implementing session memory as hooks that load state at session start
and save at session end, plus instinct-based continuous learning.

**Decision**: SPS already has the correct shape — evidence records, handoff
documents, explicit state on disk. Continuous learning that auto-writes policy is
**REWRITE**: any learned rule must be a proposal with evidence, requiring user
approval before becoming policy (CAP-012). A system that silently learns new
rules cannot satisfy the "no silent inference" requirement.
defect class where "always verify" was a prompt rather than a gate.