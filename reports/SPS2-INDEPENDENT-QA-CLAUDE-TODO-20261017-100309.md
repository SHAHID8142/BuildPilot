# SPS2 INDEPENDENT QA (CLAUDE LEAD) — TODO LEDGER

Ledger time: 2026-10-17T09:56:18+06 (suffix 20261017-095618), statuses finalized at 20261017-100309
Owner: Claude (independent adversarial QA lead)
Branch: `build/roadmap-p3-completion` · HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`
Mode: strictly read-only. No source/test/validator/manifest/CI/doc/governance edits; no git mutations; new timestamped reports only.

## Baseline at open (independently captured)

| Item | Value |
|---|---|
| Branch | `build/roadmap-p3-completion` |
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` |
| Staged | 0 · Stashes: 0 |
| Porcelain total | 65 (39 modified tracked + 26 untracked entries) |
| Subject record SHA-256 | `7c35617b309bef35…` (intact at open and close) |
| Correction sidecar SHA-256 | `a50bfd25fa54c8a…` (intact at open and close) |
| Import-exception manifest SHA-256 | `f818665f471d015d…` |
| Concurrent activity | none during audit (only `.DS_Store` mtime changed; all report files land in `reports/`, itself untracked) |

## TODO queue

| ID | Package | Method | Status |
|---|---|---|---|
| C0 | Live baseline + integrity + count-methodology reconciliation | direct | DONE |
| C1 | Test-matrix reproduction (2×), module enumeration, CI coverage | direct (subagent mechanism unavailable in this session; executed as independent inline batches with fresh commands) | DONE |
| C2 | Validator re-runs ×5, repaired-control inspection, negative probes in temp fixtures | direct | DONE |
| C3 | P10 gate re-run + count reconciliation + scanner evasion probes | direct | DONE |
| C4 | Updater/mirror/installer/uninstaller verification | direct | DONE |
| C5 | Rollback/snapshot/rehearsal safeguard verification | direct | DONE |
| C6 | Governance/provenance sweep (DEC-73xx refs, hashes, settings.json) | direct | DONE |
| C7 | Codex deep-QA findings challenge (all Critical/High; sample Medium) | direct | DONE |
| C8 | Test-quality / coverage / documentation-claims audit | direct | DONE |
| C9 | Integration verdict + deliverables | direct | DONE |

Note on method: this session exposes no separate subagent-execution mechanism, so
every work package was executed directly with independently derived commands
(fresh module enumeration, fresh temp-fixture probes) rather than by trusting
either prior report's method or output. Findings were reproduced, not copied.

## Key evidence pointers (full detail in findings + final reports)

- Full matrix ×2: `Ran 1057 tests … OK (skipped=2)`, exit 0 both runs (38.9s / 39.1s).
- P10 gate JSON: 16 required controls, 9 PASS / 5 FAIL / 2 BLOCKED, 0 integrity problems, exit 1.
- Validators: 79/4, 68/9, 66/10, 57/11, 44/1 — all exit 1; failure lists extracted line-by-line.
- Scanner evasion CONFIRMED by temp-fixture probe: rebind/getattr/subscript forms all MISSED (control: direct/aliased forms DETECTED).
- Validator baseline split discovered and documented: validate-sps2.sh uses `--baseline c49f3852` (HEAD) → 4 failures; validate-p2/p3/p4/p5 use `--baseline c11da27` (older) → 9/10/11/1 failures. Both behave as their contracts specify; this explains the long-standing count asymmetry.
- P5's 9-path legacy failure list includes `.github/*` and `.sps/tools/*` files that are identical to HEAD but differ from the older c11da27 baseline — a baseline-age artifact, not live tampering.
