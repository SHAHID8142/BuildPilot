# Capability Matrix

Use this file to decide what `/sps` can safely assume on each host.

## Rule

If a capability is missing, fall back instead of pretending it exists.
Never claim "works on every agent on the internet."

## Support model

| Host | Skills | MCP | Shell / installs | Structured questions | Browser / runtime | Notes |
|---|---|---|---|---|---|---|
| Claude Code | Strong | Strong | Strong | Usually | Strong | Full stack + plugins/MCP extras |
| Cursor | Strong | Strong | Strong | Usually | Strong | Host-native tools; no Claude plugin assumptions |
| Codex | Strong | Varies | Strong | Varies | Varies | Portable skills + shell verification |
| Antigravity / Gemini CLI | Medium | Varies | Medium | Conversational | Varies | Requires root mirrors; easy to skip SPS |
| Windsurf | Medium | Varies | Varies | Varies | Varies | Prefer short pointers to `./.sps/` |
| GitHub Copilot | Medium | Varies | Varies | Varies | Varies | `AGENTS.md` + skills when supported |
| OpenCode / Cline / Roo / Kiro / Amp | Varies | Varies | Varies | Varies | Varies | Use generic adapter |
| Other skills-compatible agents | Varies | Varies | Varies | Varies | Varies | METHOD-CARD + `.sps/` memory |
| Generic chatbots / non-coding agents | No | No | No | No | No | Out of scope |

## v4.0 features on each host

| Host | Plan gate (`plan.md`) | Auto-update (`check-update.sh`) | Parallel subagents | Manual check loop |
|---|---|---|---|---|
| Claude Code | Yes | Yes (session-start) | Yes (SUBAGENT-PLAYBOOK) | Yes |
| Antigravity | Yes (boot refusal #7) | Yes (session-start) | Yes | Yes |
| Codex / Cursor | Yes | Yes (session-start) | Yes | Yes |
| Windsurf / Copilot / others | Yes | Yes (session-start) | Varies | Yes |

## Fallback order

1. Explicit skill invocation
2. Host-native shell/file/planning tools
3. MCP only if configured
4. Plain conversational questioning
5. Manual verification notes

## Hard restrictions

- Never assume Claude plugins on non-Claude hosts
- Never assume MCP/browser automation
- Never assume identical skill directories
- Never claim identical behavior everywhere

## Write host identity every session

Update `./.sps/agent.md` with host, `/sps` required, capabilities, fallbacks, VERSION.
