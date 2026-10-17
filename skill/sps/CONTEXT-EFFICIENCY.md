# Context Efficiency (token-saving law)

## Goals

Fix the requested slice quickly without burning context on whole-repo reads or
narration.

## Hard rules

1. **Surgical scope** — touch only what the task requires (Karpathy guidelines).
2. **Narrow reads** — prefer Grep / path glob / line-offset reads; read a full
   file only when evidence shows it is necessary.
3. **Progressive skill load** — load specialist skills only for active domains.
4. **Lean skill bodies** — keep hot instructions short; put deep refs in linked
   files loaded on demand.
5. **Disk memory over chat** — persist state in `./.sps/handoff.md` instead of
   relying on long threads.
6. **Optional output compression** — if a caveman/terse skill is installed and
   the user wants it, use it; never strip required evidence.

## Anti-patterns

- Reading every section file to change one navbar link
- Loading all taste skills "just in case"
- Rewriting unrelated files for style
- Dumping huge file contents into chat when a citation/path suffices
