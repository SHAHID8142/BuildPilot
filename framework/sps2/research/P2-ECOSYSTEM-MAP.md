# P2 Ecosystem Map

Phase: roadmap P2 (audit phase 06). Research only.
Sources: 20 (see `P2-SOURCES.json`). Access date 2026-10-03.
Every external system was inspected **statically**. No external code was executed.

---

## 1. Map summary

Six families of system, with the mechanism that actually differentiates them:

| Family | Representative | Primary contribution |
|---|---|---|
| Harness optimisation systems | ECC | Breadth: per-harness dirs, skills, hooks, instincts |
| Persona catalogues | agency-agents | Role vocabulary, no runtime |
| Multi-agent orchestration | Anthropic research system | Lead + parallel subagents, artefact pattern |
| Harness-native tooling | Claude Code, Codex, Cursor, Cline, OpenCode | Enforcement: permissions, sandbox, managed policy |
| Protocol layer | MCP, MCP Registry | Integration surface + provenance (not security) |
| Standards | AGENTS.md | Portable project-local instructions |

---

## 2. ECC (SRC-001, SRC-002)

**Observed, not assumed.** 3,043 commits, MIT licence. The directory tree
contains `.claude/`, `.codex/`, `.cursor/`, `.gemini/`, `.opencode/`, `.zed/`,
`.kiro/`, `.trae/`, `.qwen/`, `.kimi/`, `.hermes/`, `.agents/`, `.pi/`,
`.vscode/`, `.adal/`, `.openclaw/`, `.codebuddy/` alongside `agents/`, `skills/`,
`hooks/`, `rules/`, `contexts/`, `schemas/`, `manifests/`, `mcp-configs/`,
`commands/`, `workflows/`, `plugins/`, `tests/`, `scripts/`,
`legacy-command-shims/`.

- **Hooks**: `hooks/hooks.json` defines `PreToolUse`, `PostToolUse`, `Stop`.
- **Memory**: `hooks/memory-persistence/` and `hooks/strategic-compact/` with
  `session-start.js`, `session-end.js`, `pre-compact.js`, `evaluate-session.js`.
- **Learning**: `skills/continuous-learning/` (v1 Stop-hook pattern extraction)
  and `skills/continuous-learning-v2/`, described as instinct-based learning with
  confidence scoring.
- **Agents**: concrete reviewer and build-resolver files per language
  (`go-reviewer.md`, `rust-build-resolver.md`, `pytorch-build-resolver.md`, ...).
- **MCP**: `mcp-configs/mcp-servers.json` plus a root `.mcp.json`.

**Key judgement — cross-harness support is NOT parity.** Fourteen harness
directories prove *packaging* breadth. They do not establish that hooks fire
identically, that skills behave identically, or that enforcement is equivalent.
P2 recorded no such claim (CAP-014 -> `RESEARCH_FURTHER`).

**Weaknesses**: the Tkinter desktop dashboard (`ecc_dashboard.py`) is irrelevant
to an agent-neutral framework -> **REJECT** (CAP-036). Instinct-based learning
produces unverifiable rules by default -> **REWRITE** (CAP-012).

---

## 3. agency-agents (SRC-003)

570 commits, MIT. **This is not an orchestration runtime.** It is a corpus of
markdown agent personas organised by division (`engineering/`, `security/`,
`testing/`, `research/`, `marketing/`, ...) with `divisions.json` and `tools.json`.

No scheduler, no dispatcher, no dependency graph, no gate, no evidence capture.
The repository describes agents as having "personality, processes, and proven
deliverables" — a prompt-level concept.

**Judgement**: useful as *requirement vocabulary* (which roles exist), worthless
as an architecture to copy -> **REWRITE** (CAP-017). This corrects a common
misconception that a large agent catalogue constitutes an orchestration system.

---

## 4. Harness-native enforcement (SRC-004 … SRC-011)

| Harness | Project-local surface | Global surface | Enforcement primitive |
|---|---|---|---|
| Claude Code | `.claude/settings.json`, `.claude/skills/` | `~/.claude/` | Auto/Manual permission modes, sandboxed bash, ConfigChange hooks |
| Codex | `.codex/`, `AGENTS.md`, `requirements.toml` | `~/.codex/` | `allow_managed_hooks_only`, sandbox modes, security CLI |
| Cursor | `.cursor/rules/*.mdc`, nested `AGENTS.md` | User Rules | 4 rule types, Team Rules precedence |
| Cline | `.clinerules/`, `.cline/rules/`, `AGENTS.md` | global rules dir | Conditional path rules |
| OpenCode | `opencode.json`, `.opencode/` | `~/.config/opencode/` | Managed config highest precedence |

**Cross-cutting finding**: every harness reimplements config precedence
differently. That is exactly what an agent-neutral control layer should
abstract — but SPS must *not* pretend the semantics are identical.

Cursor's rule model is the most expressive documented (4 types: `alwaysApply`,
`globs`, `description`). Cline's is the most portable (`.clinerules/` plus
autodetection of `.cursorrules`, `.windsurfrules`, `AGENTS.md`).
---

## 5. AGENTS.md — the portability primitive (SRC-014)

Now stewarded by the **Agentic AI Foundation under the Linux Foundation**. Claims
60k+ open-source projects. Listed supported agents include Codex, Cursor, Gemini
CLI, Copilot, Aider, goose, opencode, Zed, Devin, Junie, Amp, Windsurf,
Augment, RooCode, Kilo Code.

Rules: no required fields; nested files allowed; **the closest file to the edited
file wins**; explicit user chat prompts override everything.

**Judgement**: the strongest existing portability primitive. SPS should adopt it
rather than invent a competing instruction file -> **ADAPT** (CAP-001, CAP-002).

---

## 6. MCP (SRC-012, SRC-013)

The registry provides provenance: reverse-DNS namespaces
(`io.github.user/server`) verified by DNS or GitHub challenge. It states plainly
that it **delegates security scanning** to package registries and downstream
aggregators, that host applications should consume aggregators rather than the
registry directly, and that it is in preview.

The security specification enumerates concrete attack classes: confused deputy,
token passthrough, SSRF, session hijacking, prompt injection, impersonation,
local MCP server compromise, OAuth URL validation, stdio transport in proxies,
and scope minimisation.

**Judgement**: adopt namespace provenance (**ADAPT**) and the attack taxonomy
(**KEEP**); **REJECT** the registry as a security control (CAP-024) because it is
documented as not scanning code.

---

## 7. What was NOT studied

Recorded so the gaps are explicit rather than implied:

- Full enumeration of ECC's skills corpus.
- Gemini CLI's own configuration documentation — both URLs tried returned HTTP
  404. AGENTS.md integration is confirmed only indirectly via SRC-014.
- Codex's advanced configuration reference — SRC-008 is a 15-line pointer, not the
  reference itself.
- Copilot feature depth beyond AGENTS.md support.
- MCP aggregator implementations.
- Concrete CMS products — Contentful returned HTTP 429.

None of these were guessed. They are `RESEARCH_FURTHER` or simply absent claims.