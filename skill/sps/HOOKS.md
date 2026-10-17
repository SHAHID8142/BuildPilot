# Hook-Enforced Laws (T-32)

Hooks wire a fast subset of the SPS law checks into Claude Code's
PreToolUse/PostToolUse lifecycle, so violations are blocked or flagged at
write-time — **outside model context** — instead of being caught only when
`framework/sps2/tools/check_laws.py` is later invoked. A blocked write never
reaches the model.

## What the hooks enforce

- **PreToolUse (Write|Edit), blocking:** the CONTEXT-BUDGET law. A write that
  would push an `.sps/` hot file (`handoff.md`, `task-queue.md`, `plan.md`,
  `profile.md`, `agent.md`, `audit-report.md`) over its line/byte budget is
  denied (exit 2 + JSON `deny` decision) with the exact over-budget numbers
  and the archive-to-`.sps/archive/` remedy in the reason.
- **PostToolUse (Write|Edit), non-blocking warnings only:** a fast targeted
  subset of `check_laws.py` — dod-22 junk filenames, dod-24 hardcoded
  env-config in `framework/domain/**/*.py`, and the real post-write
  context-budget of `.sps/` hot files. Warnings surface as a `systemMessage`
  and never block a write.

The full checker (`check_laws.py`) stays the source of truth; hooks are fast
single-file subsets, so a hook pass is not a substitute for a full run
(`bash scripts/sps-lawlog.sh run` or CI).

## Consent gate (TOOL-CONSENT law)

Installing hooks changes Claude Code's write-time behavior, so it is treated
as a tool install under `skill/sps/TOOL-CONSENT.md`: **nothing auto-installs.**
`install` refuses without the explicit `--yes` flag; piped or EOF stdin never
counts as consent. Consented installs can be noted in `.sps/installs.md`.

## Usage

    bash scripts/sps-hooks.sh install --yes     # wire hooks into .claude/settings.json
    bash scripts/sps-hooks.sh install --yes --force   # re-install / refresh
    bash scripts/sps-hooks.sh status            # report-only, always exit 0
    bash scripts/sps-hooks.sh remove            # strip only its own entries

`install` merges into the project-local `.claude/settings.json` (created if
missing) and preserves all pre-existing keys and other hooks. Every entry it
writes carries the marker `"_spsHook": "sps-law-gate"`; `remove` deletes only
entries matching that marker. Double install without `--force` is refused.

## Files

- `scripts/sps-hooks.sh` — consent-gated manager (install/status/remove)
- `scripts/sps-hook-gate.sh` — the hook entrypoint settings.json points to
  (keeps settings a one-liner per hook); mirrored byte-identically in
  `skill/sps/scripts/` per the mirror law.

## Fail-open contract

The gate script never breaks a normal write: missing `python3`, a malformed
hook payload, or an unknown mode exits 0 silently. Blocking happens only for
the one law wired to PreToolUse (context-budget on `.sps/` files).
