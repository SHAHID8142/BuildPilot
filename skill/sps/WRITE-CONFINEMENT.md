# Write Confinement Law (Project-Only Writes)

**Law:** the agent writes ONLY inside the current project directory.
No agent-private memory, no home-directory state, no writes outside the
project — except the explicit allowlist below.

## The rule

1. **Project is the only writable root.** All persistent state — memory,
   handoffs, todos, reports, learned lessons, scratch files — goes under
   `./` (the project), primarily `./.sps/` and `./reports/`.
2. **Forbidden targets.** The agent must not write to: its own memory
   directories (`~/.claude/...`, auto-memory, `CLAUDE.md` memory files in
   the home directory), `~/.sps/`, other projects' directories, or any
   absolute path outside the project root. If a tool offers "remember
   this across sessions", decline and write the fact into `./.sps/`
   instead — the project's own memory is the memory.
3. **Allowlist (the only outside-project writes permitted):**
   - Git **push** to the project's own remote (when the user's push policy
     authorizes it).
   - Installer/tooling scripts whose documented job is to install into
     home directories (install.sh/uninstall.sh) — run only when the user
     asked for install/uninstall work.
   - Temporary files: use the system temp directory (`/tmp` or equivalent)
     for throwaway artifacts, and delete them when done. Never store
     anything in `/tmp` that the project needs later.
4. **Reads are unrestricted.** This law confines WRITES, not reads.
5. **Cross-session knowledge.** Anything the next session must know goes
   into `./.sps/handoff.md` (or `./.sps/` docs) — not into agent memory.
   If a fact is sensitive or personal, it still lives in the project's
   `.sps/` (the project is private by default), or not at all.
6. **Violation self-check.** Before any Write/Edit outside `./`, the agent
   asks: "Is this in the allowlist?" If not, it writes inside the project
   instead and says so.
