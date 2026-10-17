# SPS Loop — a Karpathy-style agent loop

A minimal agent loop for this repository, in Andrej Karpathy's sense: an LLM calling
tools in a loop — "a pipeline with LLM calls at each step, some if statements, and a
loop" — with a human kept firmly in the loop, per his stated preference against fully
autonomous runs.

## The loop (exactly three moving parts)

```
while queue not empty and no STOP file:
    1. PICK    — read the next task from QUEUE.md (first unchecked box)
    2. RUN     — one bounded `claude -p` work package with tool access
    3. CHECK   — human gate: you review the output, then keep/skip/stop
```

That's it. No scheduler, no daemon, no autonomous mode. Each iteration is one bounded
work package; you approve each one before the next starts. This matches both
Karpathy's minimal-loop design and this project's own SPS rules (plan gate, per-section
approval, one bounded task at a time).

## Files

| File | Purpose |
|---|---|
| `loop/QUEUE.md` | The task queue. One `- [ ]` checkbox per task, most important first. |
| `loop/STATE.md` | Append-only iteration log (what ran, result, human decision). |
| `loop/STOP` | Create this file to halt the loop after the current iteration. |
| `loop/sps-loop.sh` | The driver script. |

## Usage

```bash
bash loop/sps-loop.sh              # interactive: shows each task, waits for you
bash loop/sps-loop.sh --max 3      # run at most 3 iterations
bash loop/sps-loop.sh --auto       # skip the pre-task confirm (post-task gate remains)
```

Per iteration the script:

1. Prints the next `- [ ]` task from `QUEUE.md`.
2. Asks you to confirm (unless `--auto`).
3. Runs `claude -p` with a work-package prompt that carries the project's standing
   constraints verbatim (no commit/push/release, preserve work, fail-closed gates,
   report to `reports/`).
4. Appends the outcome to `loop/STATE.md`, marks the task `- [x]` only after you
   confirm the result is good.

## Hard rules baked into every iteration prompt

- One bounded task. Do not start another.
- Nothing staged, committed, pushed, merged, released, or deployed.
- Preserve all existing work; no reset/clean/stash/revert/delete.
- Never claim approval, gate passage, or release readiness that evidence does not show.
- New timestamped report under `reports/`; append-only coordination-log entry.

## Stopping

`Ctrl-C` anytime, or `touch loop/STOP` before the next iteration starts. The loop
never runs more than `--max` iterations (default 1).
