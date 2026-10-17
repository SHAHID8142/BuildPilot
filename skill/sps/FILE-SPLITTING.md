# Code File Splitting Law (anti-monolith)

Large files are the quiet killer of AI-assisted codebases: they blow the
agent's context budget, produce worse edits (the model sees less of the
file), make reviews unreadable, and turn every merge into a conflict.
This law applies to every file the agent writes — code, styles, config.

## Hard limits (per shipped source file)

| Type | Soft limit (refactor first) | Hard cap (never exceed) |
|---|---|---|
| Source code (ts/js/py/php…) | 300 lines | 500 lines |
| React/Vue/Svelte components | 200 lines | 350 lines |
| CSS / stylesheets | 300 lines | 500 lines (then split per component/page) |
| Config files | 100 lines | 200 lines |
| SQL migrations | — | one concern per migration file |

Exceeding a soft limit is allowed only with a written reason in the
approval packet (e.g. a single cohesive parser with high split cost).
The hard cap has no override — split before shipping.

## Splitting rules

1. **Split by responsibility, not by size alone.** One file = one job:
   a component renders, a hook holds behavior, a util is pure logic,
   a type file declares types. If you can name the file's job in one
   sentence, the split is right; if you need "and", it's two files.
2. **Extract in this order**: (a) pure helpers/utils, (b) types and
   constants, (c) sub-components, (d) hooks/composables, (e) data/API
   access, (f) styles. Each extraction is mechanical and testable.
3. **Colocation beats indirection**: split files live next to their
   feature (feature folder), not in a global `utils/` dumping ground.
   A `utils/index.ts` with 40 unrelated exports is a monolith with
   extra steps.
4. **No orphan splits**: every extracted file is imported and used in
   the same section; splitting is not an excuse for dead code.
5. **Public behavior unchanged**: a split refactor passes the same
   tests before and after — it rides along with a section, never
   breaks one.
6. **Styles split per component/page**; a global stylesheet beyond the
   cap splits by route/component, keeping only tokens/reset global.
7. **When touching a legacy monolith**: you are not required to split
   the whole file, but any function/component you substantially rewrite
   (>20 lines changed) is extracted if it pushes the file past the hard
   cap. Leave the file better than you found it, one extraction at a
   time.
8. **New files over patched sprawl**: if a file needs a second `// ----
   SECTION ----` banner comment, that's the split boundary announcing
   itself — split there.

## Agent self-check (runs at cleanup gate)

- `wc -l` on every file touched this section; anything over the soft
  limit gets a line in the approval packet justifying it.
- Any file over the hard cap fails the section DoD (cleanup gate).
- Grep for banner comments (`// ----`, `/* ====`) as split markers.

## Why these numbers

LLM agents degrade on large files in two ways: narrow reads miss
cross-references, and full reads eat the context budget that the task
needs (CONTEXT-EFFICIENCY.md). ~300 lines fits a single screen-range
read with room for surrounding evidence; 500 lines is where edits start
colliding with unseen code. The limits are guidance tuned for agent
editing, not dogma — the written-reason escape hatch exists for the
legitimately-cohesive big file.
