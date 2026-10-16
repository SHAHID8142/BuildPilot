---
name: universal-build-orchestrator
description: >
  Claude plugin entry point for `/sps`. Use when the user asks to build,
  design, implement, fix, refactor, test, or deploy software and wants the
  project-scoped `/sps` workflow: discovery first, always-written memory,
  anti-hallucination checks, low-end mobile gates, role-based routing,
  section-by-section approvals, and capability-aware verification.
---

This file is the Claude-specific entry point for `/sps`.

The canonical workflow lives in `skills/sps/SKILL.md`. Follow that file as the
source of truth.

## Claude host notes

- Claude can use richer plugin and MCP integrations than many other hosts.
- Use those capabilities when available, but do not rewrite the core workflow
  around Claude-only features.
- Project-local rules still win over global defaults.
- Write `./.sps/agent.md` with host = Claude Code at session boot.
- Keep the `/sps` lock active once the project has `./.sps/`.

## Required behavior

1. Load the canonical `/sps` workflow from `skills/sps/SKILL.md`.
2. Follow the scoped memory rules from `skills/sps/PROFILE-SCOPING.md`.
3. Follow anti-hallucination and mobile/low-end gates from
   `skills/sps/ANTI-HALLUCINATION.md` and `skills/sps/MOBILE-LOW-END.md`.
4. Read `skills/sps/hosts/claude.md` for Claude-specific notes.
5. Support `/sps audit` via `skills/sps/AUDIT.md` when requested.
6. Route to the best available specialist stack without claiming that every
   host behaves the same way.
7. Use Claude-only enhancers only when they genuinely help and do not conflict
   with the chosen portable workflow.
