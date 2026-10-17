# Learning System — BuildPilot Self-Improvement Loop

**Design law: the system PROPOSES, the user RATIFIES.** A self-learning system
that rewrites its own checks without a decision record is exactly the
check-weakening failure the fail-closed gates exist to prevent. Learned rules
therefore enter through the same decisions-ledger mechanism as every other
governance change (DEC-7201, DEC-7301, DEC-7304, DEC-7305, …).

## Components

| Component | File | What it does |
|---|---|---|
| Mistake ledger | `mistakes.jsonl` | Append-only structured failure records: what broke, root cause, detection signal, resolution, status. Fail-closed: unparseable lines are reported, never dropped. |
| Pattern detector | `learn.py patterns` | Groups by category; classes appearing ≥ 2× are flagged as promotion candidates. |
| Promotion proposals | `proposals/*.json` | Auto-drafted decision records with `status: AWAITING_USER_RATIFICATION`. They change **nothing** by themselves. |
| Evidence index | `evidence-index.json` | Queryable index over `reports/` (90+ reports) so a future session asks "what failed last time and why" instead of re-discovering. |

## Usage

```bash
L=framework/sps2/learning/learn.py

# After any failure is diagnosed:
python3 $L record --category <class> --summary "..." \
  --root_cause "..." --detection_signal "..." --resolution "..."

# What classes are repeating?
python3 $L patterns

# At >=2 occurrences, draft a promotion proposal (awaiting ratification):
python3 $L propose <category>

# Evidence retrieval:
python3 $L index
python3 $L query APPROVED
python3 $L list
```

## The loop

1. **Record** — every diagnosed failure becomes a ledger entry.
2. **Detect** — repeated classes surface automatically on the next `record`.
3. **Propose** — at threshold, a proposal document is drafted (never applied).
4. **Ratify** — the user approves; the rule lands in `rules.md` (project scope)
   or `~/.sps/personal-defaults.md` (personal scope, explicit approval only),
   and contributing entries are marked `promoted`.
5. **Index** — reports stay queryable so judgment accumulates across sessions.

## Rules (ratified)

_Nothing ratified yet. Proposals live in `proposals/` awaiting the user._

## Honesty guarantees

- The ledger never rewrites history: entries are append-only; status transitions
  (`open → resolved → promoted`) are the only mutations.
- Proposals never modify checks, validators, thresholds, or defaults.
- The evidence index stores digests (`sha256_16`) so stale indexes are detectable.
- Threshold promotion requires the same user attribution law as everything else:
  an agent cannot ratify its own rule (`AGENTISH` policy applies).
