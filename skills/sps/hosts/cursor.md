# Cursor host adapter for `/sps`

Canonical workflow: `../SKILL.md` + `../METHOD-CARD.md`.

## Cursor notes

- Prefer Cursor-native tools (shell, file edits, browser MCP if configured)
- Do not assume Claude plugin marketplaces exist
- Invoke `/sps` explicitly for orchestrated work
- Maintain `AGENTS.md` lock block
- Use Skill Router; try install missing skills; otherwise instruct the user
- Write `./.sps/agent.md` with Host: Cursor and VERSION

## Required behavior

1. Follow canonical `/sps` steps including CMS coupling when enabled
2. Keep anti-hallucination + mobile + design gate + hygiene active
3. Surgical context reads (CONTEXT-EFFICIENCY.md)
4. Fall back cleanly when MCP/browser tooling is unavailable
