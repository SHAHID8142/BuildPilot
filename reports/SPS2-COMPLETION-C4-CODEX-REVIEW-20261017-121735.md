# SPS2 C4 Packages 1 and 4 — Codex Read-Only Adversarial Audit

**Timestamp:** 2026-10-17 12:17:35 +06  
**Reviewer:** Codex subagent `p1p4_c4_audit`  
**Verdict:** **NEEDS REVISION** (preliminary Codex audit; Claude's independent review is still pending)  
**Branch / HEAD:** `build/roadmap-p3-completion` / `c49f3852e1c31d0136269c80fe58201b059af3ec`

## Scope and preservation

Read-only review of the current Packages 1 and 4 code and tests, covering scanner coverage and false positives, rollback deletion boundaries, snapshot publication/restore failure windows, and open residuals. The reviewer reports that branch and HEAD matched the baseline and that no files were changed. Only the two permitted focused test modules were run: **65 tests passed, 0 failures**. Python `ResourceWarning`s occurred during teardown.

This review is not User approval for further changes and does not replace Claude's independent review. No implementation is authorized by this report.

## Findings

### C4-1 — Scanner coverage and false-positive gaps

- `sps2/governance/import_exceptions.py:105` tracks selected loader names and simple assignments; an aliased loader import such as `from importlib import import_module as load` is not tracked.
- `sps2/governance/import_exceptions.py:156-171` misses a namespace assembled with `".".join(("domain", "seo", "audit"))`.
- The previously documented R-1 forms remain unsupported: tuple unpacking, walrus assignment, container storage, and non-constant `getattr` arguments.
- The scanner treats any call named `import_module` as a loader, including a local unrelated function. The test at `sps2/tests/test_round26_governance_contracts.py:405` currently codifies that broad behavior. It also flags any `BinOp` anywhere within a recognized call, including unrelated expressions in another argument; benign-call coverage is absent.
- The current live dynamic import at `sps2/tools/p10_runtime_gate.py:1944` is detected and remains the expected violation. Do not change its policy or exception disposition without the User's governance decision.

### C4-2 — Rollback ownership and symlink boundary risks

- `sps2/tools/rollback_seo.py:142` skips all `__pycache__` contents during the ownership check, while `:435-443` later recursively removes the entire `domain/seo` tree. Unowned cache files can therefore be removed; check-then-delete also permits a race.
- `seo_dir.is_dir()` follows a symlink at the `domain/seo` root. Leaf files are checked with `lstat`, but a symlinked root can expose outside `.py` files to the unlink set before recursive removal fails.
- Existing tests cover a leaf symlink and non-Python file, but not a symlinked root or unowned data beneath `__pycache__`.

### C4-3 — Snapshot publication recovery and occupied-target behavior

- If the snapshot target is a regular file, `sps2/tools/rollback_seo.py:301-307` moves it to `.previous-<pid>`, publishes the new directory, then raises when cleanup calls `rmtree` on the old file. The call reports failure despite publishing the new snapshot and leaves the prior file behind.
- A process interruption between moving an old directory aside and publishing staging can leave the target absent and the prior snapshot stranded under `.previous-<pid>`.
- If restoration of that backup fails, `finally` cleanup at `:315-317` may remove the only prior copy.
- Current interruption coverage checks a copy failure before publication but not these publish/restore windows.

### C4-4 — Snapshot restore manifest validation and partial mutation

- `restore_snapshot` checks root containment and digests but does not enforce P9 allowlisted paths (`sps2/tools/rollback_seo.py:351-376`). A manifest with a matching digest for an unrelated in-root file may overwrite it.
- Entries are copied as they are validated; a later invalid entry can leave a partial restore.
- Existing tests cover an outside-root path and a missing first entry, not an unrelated in-root target or a later invalid entry after an earlier valid copy.

### C4-5 — Test warning and governance boundary

- A second `tearDown` definition in `sps2/tests/test_round26_governance_contracts.py` overrides the earlier temporary-directory cleanup, consistent with observed `ResourceWarning`s.
- `domain/seo/isolation.py:203` delegates orphan scanning to the DEC-7302 manifest and legacy checks to DEC-7301. The integration operationally accepts manifest-listed imports; this audit does not ratify those decisions. The live scan still fails closed on the known dynamic import.

## Requested independent Claude review

Claude should independently inspect the cited code and tests, reproduce or reject each finding with exact evidence, and identify any severity or scope correction. Append a review to `reports/SPS2-COMPLETION-COORDINATION.md` only; do not edit source/tests/governance records, do not fix anything, and do not resolve User-only decisions. Specifically answer:

1. Which findings are confirmed, disproved, or need narrower wording? Give exact paths/lines and reproduction details.
2. Does either rollback issue create a data-loss path under reachable inputs, and what minimal test would prove the boundary?
3. Is restore prevalidation/allowlisting a code-owned fix or dependent on a User governance decision? Keep technical correctness separate from policy acceptance.
4. Confirm focused tests and preservation state; report warnings and limitations.
5. Set the independent verdict to `PASS`, `NEEDS REVISION`, or `BLOCKED`. Do not treat the earlier Packages 1/4 Claude PASS as evidence against current findings without checking the live code.

