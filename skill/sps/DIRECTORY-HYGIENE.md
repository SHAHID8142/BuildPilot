# Directory Hygiene (placement law + cleanup duty)

Every file has exactly one home. An agent that creates a file puts it in its
home at creation time; an agent that finds a file outside its home moves it
there (or lists it for the user — see the fix policy below). This applies to
the BuildPilot repo itself AND to every client project built with BuildPilot
(same law, relative to that project's root: its `.sps/`, its `reports/`, its
own tree).

## Canonical placement map (BuildPilot repo)

| File type | Home |
|---|---|
| Session / task / audit reports | `reports/` — timestamped `YYYYMMDD[-n]`, never overwrite (memory law) |
| New shell/python scripts | `scripts/` + byte-identical mirror in `skill/sps/scripts/` (CI: `diff -rq`) |
| Skill documentation | `skill/sps/*.md` |
| Host adapters | `skill/sps/hosts/` |
| Skill templates | `skill/sps/templates/` |
| Session plans | `.sps/plan-*.md` |
| Task tracking | `.sps/task-queue.md` (plus `.sps/tasks/` evidence) |
| Session memory | `.sps/handoff.md`, `.sps/agent.md`, `.sps/profile.md` |
| Generated law regression tests | `framework/sps2/tests/test_law_regress_*.py` |
| Standalone validators / generators | `framework/sps2/tools/` |
| Decision records | `framework/sps2/decisions/DEC-*.md` |
| Lessons | `lessons/inbox/` → `lessons/adopted/` or `lessons/rejected/` |
| Project briefs, audits, dev tests | `docs/` (`docs/audits/`, `docs/dev-tests/`) |
| Framework code + its tests | `framework/sps2/` (`sps2/tests/` for the battery) |
| Loop runner state | `loop/` |
| Temp / scratch files | **NEVER in the repo tree** — system tmp dir, cleaned up before handback |
| Downloaded / extracted archives | **NEVER in the repo tree** — own empty dir outside the tree, untrusted-data rules apply |

Root-of-repo is reserved for: README / LICENSE / VERSION / CHANGELOG /
CATALOG / USER-GUIDE, the host lock mirrors (`AGENTS.md`, `CLAUDE.md`,
`GEMINI.md`), the installer entrypoints (`install.*`, `get-sps.*`,
`uninstall.*`), standard dotfiles, and the standard directories above.
Anything else in root is a stray.

## Client projects (generalized law)

In a client project the same map applies with project-local homes: reports go
to the project's `reports/` (or `.sps/reports/` if no root reports dir
exists), scripts to the project's `scripts/`, briefs and audits to `docs/`,
SPS state to the project's `.sps/`. Client source code lives wherever the
client stack puts it — the law governs agent-created artifacts, not the
client's own architecture. Temp/scratch and downloaded archives are NEVER in
the client tree either.

## Hard rules

1. **One home per file.** Create each file in its canonical home at creation
   time — never "just for now" in root or a sibling dir.
2. **Never overwrite a report.** Reports are timestamped and append-only
   (memory law); a name collision means a new timestamp, not an overwrite.
3. **Script mirrors are byte-identical.** Every `scripts/` script ships with
   a byte-identical `skill/sps/scripts/` copy; CI enforces `diff -rq`.
4. **No scratch in the tree.** Temp files, downloaded archives, and
   throwaway experiments live outside the repo and are removed before
   handback. `*~`, `*.tmp`, `*.bak`, `*.swp`, `#*#`, `.DS_Store`,
   `scratch*`, `tmp*`, `*-copy*` must never be committed.
5. **Cleanup duty.** Before handback the agent removes its own scratch, and
   moves any file it created (or clearly misplaced) into its home. No orphan
   files are left behind.
6. **Found-out-of-home gets moved, not left.** A file whose home is obvious
   is moved as part of the work, not noted and ignored.
7. **Fix policy — safe vs ambiguous.** *Safe moves* (obvious home,
   unambiguous, no uncommitted changes) the agent performs and reports in
   the handoff. *Ambiguous* files (could belong in 2+ homes, or
   user-authored content the agent is unsure about) are LISTED for the user
   — never moved silently, never deleted.
8. **Never delete.** The hygiene check may propose deletions; only the user
   deletes. Automated cleanup moves to quarantine (`.sps/quarantine/`), it
   does not remove.
9. **Untracked work is presumed user work.** Untracked files are flagged,
   and moved only when they match an obvious agent-artifact pattern (e.g.
   `SPS2-*.md` reports) or a clear temp pattern; everything else untracked
   is listed as ambiguous.

## Automatic check

```bash
bash scripts/sps-hygiene.sh        # check — report violations only, exit 0
bash scripts/sps-hygiene.sh fix    # perform safe moves; list ambiguous; exit 2 if ambiguous remain
```

`check` is read-only and safe to run anytime. `fix` prints each move as
`MOVED: <from> -> <to>` and each deferred item as
`AMBIGUOUS: <path> — <reason>`. Run it before handback; paste the output
into the handoff checkpoint.
