# SPS 2.0 — Agent Interoperability

**Phase:** `PHASE-05` · **Status:** `AWAITING_USER_APPROVAL`

**Goal:** the core system is portable; agents are clients. No vendor lock-in.

---

## 1. The separation principle

```
┌─────────────────────────────────────────┐
│  SPS 2.0 CORE + GOVERNANCE               │   agent-neutral, portable
│  lifecycle · protocols · gates · schemas │
└─────────────────────────────────────────┘
                    ▲
                    │  one-way
┌─────────────────────────────────────────┐
│  ADAPTERS (optional, thin, per-agent)    │   replaceable, disposable
└─────────────────────────────────────────┘
```

**Rule:** the core **may not** import, reference, or branch on a specific agent. Adapters translate; they do
not govern. If a vendor is removed, only its adapter directory is deleted.

---

## 2. What an adapter may and may not do

| MAY | MUST NOT |
|---|---|
| Render core rules as slash commands | Add, weaken, or reinterpret a rule |
| Map core file paths to agent conventions | Move canonical state outside the project |
| Declare agent capabilities | Assume capabilities it has not verified |
| Provide a convenience prompt | Duplicate the lifecycle state machine |
| Be absent entirely | Be required for the system to function |

---

## 3. Portable representation of each concept

| Concept | Portable form | Agent-specific form (adapter only) |
|---|---|---|
| Rules / laws | `.sps/GOVERNANCE.md` + JSON Schema | `CLAUDE.md`, `GEMINI.md`, slash commands |
| Memory / state | `.sps/` files + JSON | Agent "memory" (non-authoritative) |
| Tasks | `.sps/tasks/` | Host task tool (mirror) |
| Approval | `.sps/decisions/` + approval record | Chat reply (must be recorded, not trusted) |
| Capabilities | `.sps/capabilities/registry.json` | Bundled skill defaults (non-authoritative) |
| Tools / MCP | `.sps/mcp/` | Host MCP settings (project-scoped) |
| Handoff | `.sps/handoff/*.md` (12+ fields) | Host context (regenerated from file) |
| Validation | `.sps/tools/*.sh` | — |

**Slash commands are optional.** The canonical interface is the repository; commands are a convenience.

---

## 4. Adapter contract (`core/adapters/contract.schema.json`)

An adapter MUST declare:

| Field | Meaning |
|---|---|
| `agent_id` | Stable identifier |
| `detection` | How presence is detected (files / CLI), read-only |
| `capabilities` | `skills`, `mcp`, `shell`, `subagents`, `browser`, `structured_questions` |
| `supports` | Which core features are natively available |
| `fallbacks` | Behaviour when a capability is missing |
| `writes_global_state` | MUST be `false` unless explicitly approved |
| `author` | Who maintains it |

If an adapter cannot be verified (never run in CI), it is marked `EXPERIMENTAL` and the core falls back to the
generic path.

---

## 5. Non-compliant / instruction-bypassing agents

Phase 01 **F-1**: SPS can *tell* an agent to do something but cannot reliably *prevent* it. The answer is not
"instruct harder" — it is **machine-checkable rejection**.

| Anti-pattern | Machine-checkable control |
|---|---|
| Ignores project rules | Validator reads `.sps/` only; missing state fails the gate |
| Dead code | Dead-code / unused-export check in CI |
| Oversized or duplicated files | File-size + duplication thresholds |
| Ignores existing abstractions | Import/architecture boundary checks |
| Uses its own preferred skill | Capability registry is the only authority; unregistered skill = violation |
| Stores memory outside the project | State-location validator |
| Bypasses instruction | Pre-commit + post-task validators; gate refuses transition |
| Duplicates functionality | Similarity/duplication detection |
| Excessive permissions | Permission budget check on capability + MCP records |

**Target:** `INSTRUCTION → VALIDATION → REJECTION`, never `INSTRUCTION → HOPE`.

---

## 6. Target agents

| Agent | Adapter need | Risk |
|---|---|---|
| Claude Code | plugin + commands | moderate |
| Cursor | rules + skills | moderate |
| Codex | AGENTS.md + skills | low |
| Gemini / Antigravity | GEMINI.md mirror + boot refusal | **high** (measured: does not reliably auto-load skills) |
| OpenCode | AGENTS.md | low |
| Others | generic adapter | low |

The generic adapter must be sufficient on its own — an unknown agent must still get correct behaviour from
repository state alone.

---

## 7. Verification of portability

A candidate SPS 2.0 build is **portable** only if:
1. The core test suite passes with **no adapter installed**.
2. Deleting every adapter directory does not break any core validator.
3. A fresh agent, given only `.sps/` + `docs/`, can determine phase, task, next and forbidden actions.
4. No core file references a vendor name (enforced by a grep-based CI check).