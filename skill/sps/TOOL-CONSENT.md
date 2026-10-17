# Tool Consent Law (No Silent Installs)

**Law:** before invoking any tool, the agent verifies it exists. A missing
tool stops the task path that needs it — the agent never installs silently.

**Scope.** "Tool" means anything the agent would install or invoke as an
executable dependency: CLI binaries (`pwsh`, `gh`, `npx`, `uv`), linters,
browser drivers, MCP servers, global skills/packages. NOT covered: built-in
agent capabilities (file read/write, grep, its own subagents), tools already
available in the environment, and the pre-approved exceptions below.

## The rule

1. **Check before use.** Before calling a tool/command (`pwsh`, `gh`, `npx`,
   `uv`, a linter, a browser driver, …), verify availability
   (`command -v <tool>` / equivalent). Do not assume.
2. **Missing tool = stop + disclose + ask.** State, in one short block:
   - **What** tool is missing (exact name/version if known)
   - **Why** the task needs it (which step cannot run without it)
   - **What installation involves** (command, scope: global/local, size,
     any security considerations)
   Then ask for explicit consent and WAIT. Do not run the installer in the
   same turn as the request.
3. **No workarounds that bypass consent.** Reimplementing a missing tool's
   function in a script to avoid asking is a violation — that is an
   unapproved install by another name. If a safe fallback exists that uses
   already-available tools, name it and let the user choose.
4. **After approval:** install, then **report the outcome** — success
   (with version) or the exact failure. If installation fails, do not
   retry variants without asking again.
5. **If consent is declined:** the task path that needs the tool stops.
   Name the consequence (what will remain undone / which fallback was
   chosen), record the refusal in `.sps/installs.md`, and move on — do not
   nag, do not re-ask in the same session for the same tool+purpose.
6. **Pre-approved exceptions (no prompt needed):** tools already declared
   in the project's plan/approved stack, and package managers executing
   *already-declared* dependencies (e.g. `pip`/`npm` installing from the
   project's lockfile during a normal build), and the bundled SPS skills'
   own updater (`scripts/sps-update.sh --yes`). Anything outside that
   scope — new global tools, new system packages, new CLI binaries —
   requires the consent gate.
7. **Record it.** Consented installs AND refusals are noted in
   `.sps/installs.md` (tool, version, date, why, outcome) — a project file,
   not a session-refreshed one — so later sessions don't re-ask and can
   audit what entered the environment.
