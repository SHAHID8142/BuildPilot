# Workspace Hygiene & Multi-Agent Concurrency

## 1. General Hygiene Laws

Keep the working directory clean, intentional, and free of duplicate assets.

1. **Categorize Drops:** Docs, images, videos, fonts, data, or notes.
2. **Move to Canonical Paths:**
   - `docs/` — briefs and project documents
   - `public/uploads/` — public media assets
   - `src/assets/` — bundled component assets
   - `.sps/` — SPS memory markdown files only (no binary dumps)
3. **No Duplicate Copies:** Use canonical paths; never create copy duplicates "just in case".
4. **Never Commit Secrets:** Keep `.env`, credentials, and private keys strictly untracked.

---

## 2. Multi-Agent Write Serialization (B9)

When multiple coding agents (e.g. Claude Code + Cursor + OpenCode + Antigravity) collaborate on the same repository:

1. **Single-Writer Memory Rule:**
   - Only the active agent writing a chunk may update `./.sps/handoff.md` and `./.sps/agent.md`.
   - The active agent stamps its identifier and timestamp into `./.sps/agent.md`.
2. **Memory Conflict Prevention:**
   - Before executing, the incoming agent MUST read `./.sps/agent.md` and `./.sps/handoff.md` to acquire the latest context state.
   - If `./.sps/agent.md` indicates an ongoing session from another host within the last 5 minutes, verify previous work before overwriting memory.
3. **Atomic File Writes:** Always write memory files completely with deterministic formatting to prevent merge corruptions.
