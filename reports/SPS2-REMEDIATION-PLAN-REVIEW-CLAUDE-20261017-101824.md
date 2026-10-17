# SPS2 REMEDIATION PLANNING — CLAUDE INDEPENDENT INSPECTION AND ADVERSARIAL REVIEW

Report time: 2026-10-17T10:18:24+06 (suffix 20261017-101824)
Owner: Claude (independent reviewer of the remediation plan)
Branch: `build/roadmap-p3-completion` · HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`
Mode: PLAN AND REVIEW ONLY. No file edits, no staging/commits/pushes, no network or
remote mutation, no CI changes, no deployment/publication/merge/release. DEC-7301/7302/7303
treated as UNAPPROVED throughout; the disputed Round 26 record and its sidecar untouched
(`7c35617b…` / `a50bfd25…` verified intact before and after inspection); P10 gates and
validator baselines untouched.

**Worktree recheck before inspection:** 65 porcelain entries (39 M + 26 ??), HEAD unchanged, 0 staged, 0 stashes.
**Worktree recheck after inspection:** identical (65 / `c49f3852e1c3` / `7c35617b…`). The only
writes in this window are this report. No concurrent agent activity observed.

**Codex plan availability:** no Codex remediation-plan report dated 2026-10-17 exists in
`reports/` as of this report's timestamp (newest prior artifacts remain my QA trio at
10:03). The most recent plan-shaped artifact is `reports/CODEX-SECURITY-HARDENING-PLAN-20261016-172529.md`
(Oct 16), which covers installer SSH defaults (SH-07/P0-6) and uninstaller cleanup (I-10)
but predates the deep-QA findings and does not cover scanner evasion or snapshot/rollback
guarantees. This review therefore (a) reviews the Oct 16 plan where it overlaps, and (b)
supplies the missing independent plan-level analysis for all four packages, so the User
has a complete, reviewable basis either way. If Codex's new plan lands later, this report's
per-package structure applies to it directly.

---

## PACKAGE 1 — Scanner evasion hardening

**Affected files/functions:** `sps2/governance/import_exceptions.py` — `_is_dynamic_import` (lines 105-121), `_contains_domain_seo_string` (124-140), `scan_import_exceptions` (142+). Tests: `sps2/tests/test_round26_governance_contracts.py`.

**Confirmed defects (reproduced this round, temp fixtures only):**
1. Bare-name rebind: `from importlib import import_module; f = import_module; f('domain.seo.audit')` — MISSED. `_is_dynamic_import` never follows `Assign`/`AnnAssign` dataflow.
2. `getattr` rebind: `m = getattr(importlib, 'import_module'); m('domain.seo.audit')` — MISSED. The code comment at line 112 claims this is covered; it is not.
3. Subscript: `il.__dict__['import_module']('domain.seo.audit')` — MISSED (callable is a `Subscript`).
4. Controls confirmed working: direct `importlib.import_module`, aliased `il.import_module`, `__import__`, `from importlib import import_module` used directly as the callable.

**Hypotheses (not confirmed as exploitable, listed for completeness):** `exec`/`eval` string imports (out of scanner scope today; flagging all `exec` would balloon the FP surface); `importlib.reload`; `pkgutil`/`__import__` via `functools.partial` chains. None reproduced against the live gate path; treat as future hardening candidates, not blockers.

**Demonstrated failure scenario:** any Python file in the tree can invoke a forbidden dynamic `domain.seo` import through form 1-3 and `scan_import_exceptions` returns `ok=true` with zero violations — the DEC-7302 exception-manifest control is silently bypassed (my QA finding QA-C-002; Codex QA-0021 confirmed and extended).

**Proposed minimal change (no policy expansion — detection only):**
- In `_is_dynamic_import`, extend the callable predicate: flag a call when the callable is an `Attribute` named `import_module` (existing), a `Name` named `import_module` or `__import__` (existing), **or** a `Call`/`Subscript` expression **whose result feeds the call** — practically: flag any call whose `func` is itself a `Call` node containing the string `import_module` (covers `getattr(importlib,'import_module')(...)`), and any call whose `func` is a `Subscript` whose slice is the constant `"import_module"` (covers `__dict__['import_module'](...)`).
- For the bare-name rebind: add a lightweight pre-pass over the module AST collecting `Assign`/`AnnAssign` targets bound to a recognized dynamic-loader expression (`Name import_module`, the `getattr`/subscript forms), then treat calls through those names as dynamic. This is ~15 lines; no third-party dependency; no manifest/schema change.
- Do NOT flag every `getattr` — only `getattr(<expr>, "import_module")` (constant second arg) to keep the FP surface narrow; a non-constant second arg (`getattr(importlib, x)`) should fail closed only when the result is later called AND the file already contains a `domain.seo` string — otherwise leave to the pre-pass above. (Simpler accepted alternative: flag `getattr` with a non-constant second arg unconditionally; slightly higher FP risk, simpler audit. Recommend the simpler variant: fail-closed beats clever.)
- Fix the line-112 comment to describe what is actually implemented (comments must not overclaim — that gap is how QA-0021 escaped).

**Tests needed (all in the existing round26 test module):** four new negative tests, one per missed form, each asserting a violation is produced naming the file and line; one positive control that a local function coincidentally named `import_module` called with a `domain.seo` string is still flagged (documenting the accepted FP); one test that the existing 8 approved imports still pass; one comment-accuracy test is NOT recommended (string-pinning comments is brittle — instead the four evasion tests are the contract).

**Risks:** (1) FP growth: any benign `getattr(x, "import_module")` is now flagged — acceptable, none exists in the tree today (verified: `grep -rn "import_module" --include="*.py" | grep -v test | grep -v import_exceptions` shows only the gate's legitimate flagged site and the scanner itself). (2) The pre-pass must not flag calls through names bound from *non*-loader sources — binding only to recognized loader expressions keeps this tight. (3) Governance entanglement: hardening the scanner must be explicitly recorded as security-only, NOT as DEC-7302 ratification (Codex decision item 8; my final report §7 item 14).

**Rollback approach:** single-file change plus test additions; revert the one file. The scanner has no persisted state; no migration.

**Acceptance criteria:** all four evasion forms produce violations in tests; live `scan_import_exceptions` on the real tree still returns exactly the one known gate violation at `p10_runtime_gate.py:1944` and the 8 approved imports; round26 suite green; no manifest or decision-record change.

---

## PACKAGE 2 — Installer SSH host-key verification

**Affected files:** `install.sh` line 15 (`export GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=no"`); adjacent lines 16-18 (`GIT_CLONE_PROTECTION_ACTIVE=false`, `npm_config_yes=true` — same hardening class, same commit).

**Confirmed defect:** host-key checking is globally disabled for every Git SSH operation in the installer process (verified live at `install.sh:15`). Exploit scenario: first-contact or on-path MITM during the SSH clone path serves a backdoored repository; with `StrictHostKeyChecking=no` the host key is accepted silently and the clone proceeds to execute install-time code (`npx skills add`, plugins). Practical preconditions: the victim must use the SSH remote path and the attacker must hold a network position; the curl-pipe entry point (`get-sps.sh` over HTTPS) is separately exposed but out of this package's scope.

**Hypothesis (Codex SH-07, partially confirmed):** `GIT_CLONE_PROTECTION_ACTIVE=false` disables fsync/rename protection on the local clone — consequence is durability, not direct RCE; Medium confidence on exact Git-version semantics, matching Codex's own Medium rating. Not independently reproduced (would require controlled Git-version testing); treat as a hardening candidate with the same commit, not a separately proven defect.

**Proposed minimal change:** replace line 15 with accept-new behavior: `export GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=accept-new"`. This preserves unattended installs (new hosts auto-accepted on first contact — the legitimate bootstrap case) while refusing any host whose key later changes (the MITM/compromise signal). Optionally gate even that behind `--yes` (interactive runs get full `yes` prompting). Lines 16-18: drop `GIT_CLONE_PROTECTION_ACTIVE=false` entirely (restore Git default) and remove `npm_config_yes` export in favor of explicit flags at each call site — or, if call-site churn is too large for the minimal scope, leave 16-18 for a follow-up and change only line 15. Recommend: line 15 in this package; 16-18 documented as follow-up.

**Tests needed:** static test asserting `install.sh` contains no `StrictHostKeyChecking=no` (and, if 16-18 included, no `GIT_CLONE_PROTECTION_ACTIVE`); a bash-syntax check; no network test possible offline — the accept-new behavior itself needs one authorized interactive verification post-implementation (documented as a manual acceptance step, not automatable here).

**Risks:** (1) Known-hosts absent + non-interactive CI: `accept-new` still succeeds (that is its purpose), so CI smoke is unaffected. (2) Users with a legitimately changed host key now fail loudly — that is the intended safety signal. (3) Legacy pathspec: `install.sh` is inside the legacy pathspec and currently baseline-clean **at HEAD** — but it is already modified in the worktree? No: verified `install.sh` is NOT in the 39 modified files; it is baseline-clean, so editing it creates a new legacy-diff failure under the c11da27-baseline validators (P2/P3/P4/P5). This is the same policy blocker documented in my second-pass report (W1 F-3). **The plan must therefore pair this edit with an explicit User authorization to accept the new legacy-diff failure, or with a User decision to advance the legacy baseline (my QA finding QA-C-012).** Implementation without one of those two decisions will turn 4 green validators red-er and violate the no-weakening constraint in spirit.

**Rollback approach:** single-line revert.

**Acceptance criteria:** line 15 uses `accept-new` (or stricter); static negative test green; `bash -n` clean; the legacy-diff consequence either accepted by explicit User decision or baseline decision recorded BEFORE implementation.

---

## PACKAGE 3 — Uninstaller path confinement

**Affected files:** `uninstall.sh` — the `remove_agent_skill` path array and `rm -rf "$p"` (lines 73-101), the manifest reader (118-137), and the SYNC_PATHS loop (152-178).

**Confirmed defects (all verified live this round):**
1. `SYNC_PATHS` values from the user-writable `$HOME/.sps/install-manifest.env` flow into `rm -rf "$dest_root/sps"` and `rm -rf "$dest_root/sps-cms"` with zero validation — a manifest line `SYNC_PATHS=/` yields `rm -rf /sps` (and the loop at line 167 iterates manifest AND default arrays together, so poisoning *adds* targets rather than replacing them).
2. `remove_agent_skill` deletes CWD-relative paths (`./.claude/skills/$name` etc.) — running the uninstaller from any directory containing a matching subtree deletes it; combined with skill names from the manifest (`MANAGED_SKILLS`), a poisoned manifest controls both the name and the base path.
3. No confirmation or plan mode: every `rm -rf` is immediate.

**Hypothesis (not separately reproduced):** `npx skills remove "${MANAGED_SKILLS[@]}" -g -y` passes manifest-controlled names to a networked CLI — injection risk depends on the CLI's argument handling; treat as unverified, note in the plan.

**Demonstrated failure scenario:** attacker (or a buggy installer run) writes `SYNC_PATHS=/` into `~/.sps/install-manifest.env`; the next uninstall run executes `rm -rf /sps /sps-cms` plus all default sync paths — privilege-independent destruction of any path the user can delete.

**Proposed minimal change (no behavior change for legitimate installs):**
1. Add a `confine_dest()` helper: reject any `dest_root` that (a) is not absolute, (b) is `/` or a mount root, (c) resolves outside the set { `$HOME`, `$PWD`, repo root } after `realpath`, or (d) contains `..`. Apply it to every element of `SYNC_PATHS` and to every path in `remove_agent_skill` before `rm -rf`.
2. Drop CWD-relative candidates (`./...`) from the built-in path arrays (they serve no install flow the installer writes; the installer only writes `$HOME/...` targets — verified in `install.sh:28-45`).
3. Make the manifestfed arrays *replace* rather than supplement: current line 167 `for dest_root in "${SYNC_PATHS[@]}" "${DEFAULT_SYNC_PATHS[@]}"` should iterate defaults only when `SYNC_PATHS` is empty (the code already has that intent at 164-166; the loop contradicts it — one-line fix).
4. Optional but recommended: `--dry-run`/plan mode printing every path that would be deleted, defaulting to plan mode unless `--apply` (mirrors Codex I-10; the minimal version is the confinement helper + replace-fix; plan mode can ride along if the User wants the fuller change).

**Tests needed:** bash fixture tests (temp `$HOME`): poisoned manifest (`SYNC_PATHS=/`, `SYNC_PATHS=../../`, relative value) → refused with non-zero exit and no deletion; benign manifest → unchanged behavior; `./`-relative deletion no longer reachable; loop-replace semantics; `bash -n`. All runnable offline in temp dirs.

**Risks:** (1) A user who legitimately synced to a non-`$HOME` root would now be refused — acceptable; the installer itself only writes `$HOME`-based defaults (verified). (2) Legacy pathspec: `uninstall.sh` is baseline-clean at HEAD and inside the pathspec — same policy consequence as Package 2; requires the same explicit User decision before implementation. (3) Changing the loop semantics alters behavior for anyone who *relied* on supplement semantics — no evidence such a user exists; note in the plan.

**Rollback approach:** single-file revert; deletion is destructive so the real protection is the pre-implementation backup step (Codex P0-4) — recommend any implementation round begin by snapshotting the three scripts it touches.

**Acceptance criteria:** all four poison fixtures refused; benign path behavior byte-identical for default installs; `bash -n` clean; fixture suite green; legacy-diff consequence pre-authorized.

---

## PACKAGE 4 — Snapshot and rollback guarantees

**Affected files:** `sps2/tools/rollback_seo.py` — `create_snapshot` (234-261), `restore_snapshot` (263-328), `execute_rollback` (330-393), `execute_rehearsal` (395+). Tests: `domain/seo/tests/test_isolation.py`.

**Confirmed defects (reproduced this round where noted):**
1. **`create_snapshot` is not atomic** (docstring claims "Atomically"; per-file copy into the live snapshot dir, manifest written last). Confirmed by code inspection. Failure: interruption mid-copy → snapshot dir without manifest → later restore fails closed (missing manifest) — safe by accident, but a rehearsal that snapshots then crashes leaves an unusable recovery artifact and the docstring lies about the guarantee.
2. **Deletion set exceeds the P9 allowlist** (CONFIRMED by live probe this round): `get_p9_files` globs **everything** under `domain/seo/` (line 111-113) — my probe showed `domain/seo/user_notes_NOT_p9.txt` and `domain/seo/experiments/scratch_NOT_p9.py` are deleted by `execute_rollback`, despite `P9_ALLOWLIST_PATTERNS` declaring only `domain/seo` + `seo_audit.py` as the P9 surface and the module docstring promising "remove only allowlisted P9 files while preserving unrelated state." The snapshot happens to capture and restore them (verified: restore exit 0, user file returned), so the damage is recoverable — but the contract "preserve unrelated state" is violated for anything inside `domain/seo/`, and the post-rollback orphan scan makes the whole rollback exit 1 in fixtures without the manifest, muddying attribution.
3. **`f.unlink()` at line 362 has no error handling** — one unlink failure (permissions, race) aborts the loop mid-deletion with a traceback: partial rollback, exit via exception rather than the fail-closed message path. Confirmed by inspection; not separately provoked (would require a permission-rigged fixture — hypothesis-grade but structurally evident).
4. **`shutil.rmtree(seo_dir, ignore_errors=True)` after unlink** (line 370) can silently leave the `domain/seo` directory if a race recreates a file mid-rmtree — minor, fail-open on directory removal only (files already removed), noted for completeness.

**Confirmed NON-defects (probed this round, important for scoping):**
- Restore containment **does** catch dest-parent symlinks escaping the project root (probe: `domain/seo` → symlink outside root → restore exits 1 with "Snapshot path escapes project root").
- Restore through a symlink **inside** the root writes to the symlink target (exit 0) — within-root redirection only; acceptable, but worth a comment/test pin so a future refactor doesn't silently change it.

**Hypotheses (Codex QA-0019 residuals, not re-verified this round):** manifest shape/timestamp laxity; source regular-file checks; TOCTOU between digest check and copy. All remain deferred-risk items; none blocks this package's minimal scope.

**Proposed minimal change:**
1. **Atomic snapshot:** copy into `target_snapshot.parent / (".tmp-snapshot-<pid>")`, write the manifest there, then `os.replace`/rename the directory into `target_snapshot` (rename is atomic within a filesystem; the snapshot dir's parent is the same FS by construction). On any error, `shutil.rmtree` the tmp dir. ~10 lines.
2. **Align deletion with the allowlist:** in `get_p9_files`, intersect the `domain/seo` glob with an explicit extension/ownership rule — recommend: delete `*.py` files tracked as part of the P9 surface plus `__pycache__` artifacts; for anything else found under `domain/seo/` (non-.py, or untracked scratch), refuse or move-aside into the snapshot rather than delete. Minimal honest version: keep deleting only files matching the allowlist patterns' intent (`domain/seo/**/*.py`, `seo_audit.py`) and **fail closed with a message listing skipped non-conforming files** instead of deleting them. This restores the docstring's contract.
3. **Wrap the unlink loop:** `try/except OSError` per file → collect failures → return 1 with a partial-rollback message naming the file (fail-closed attribution, consistent with the RB-1 pattern already in the file).
4. **rmtree:** `ignore_errors=False` with try/except, message on failure (one-line change alongside 3).

**Tests needed:** interruption test (monkeypatch `shutil.copy2` to raise mid-copy → assert no `manifest.json` in the *live* snapshot path and tmp cleaned); non-P9-file test (`user_notes.txt` under `domain/seo` → rollback exits nonzero listing it, file intact); unlink-failure test (chmod 000 fixture, skip if running as root); inside-root symlink pin test; all existing 23 isolation tests stay green.

**Risks:** (1) Strictening `get_p9_files` changes rollback behavior for trees with extra files under `domain/seo/` — that is the point, but the rehearsal test's expected messages may need the new skip-list line; keep the change additive to messages, not a contract inversion. (2) The atomic-rename approach requires the snapshot's parent to exist and be same-FS — true by construction; document the assumption. (3) NOT policy-entangled: `rollback_seo.py` is an untracked/modified worktree file outside the legacy pathspec — this package has **no legacy-diff consequence** and is implementable without any governance decision beyond the standing "don't ratify DEC-7302" rule (none of these changes touch the manifest or the gate).

**Rollback approach:** single-file revert; snapshots from the prior schema remain restorable (manifest schema unchanged).

**Acceptance criteria:** interrupted snapshot leaves no partial live snapshot; non-P9 files under `domain/seo/` are preserved and named in output; unlink failure produces a named partial-rollback failure, not a traceback; all 23 isolation tests + 5 new tests green; full matrix still ≥1,057 OK.

---

## CROSS-PACKAGE FINDINGS (adversarial review of the planning premise)

1. **The legacy-diff trap is the plan's biggest hazard.** Packages 2 and 3 touch `install.sh`/`uninstall.sh`, which are baseline-clean at HEAD and inside the legacy pathspec (validate-sps2.sh:211-213). Any edit creates NEW legacy-diff failures under the c11da27-baseline validators. A plan that omits this will fail its own acceptance criteria the moment validators run. Every package-2/3 acceptance section above therefore gates on an explicit pre-implementation User decision: either authorize the new legacy-diff failures, or decide the baseline question (QA-C-012). Packages 1 and 4 have no such entanglement and can proceed independently.
2. **Sequencing:** Package 1 (scanner) and Package 4 (rollback) are safe to implement immediately after User authorization — no governance entanglement beyond recording security-only intent. Packages 2 and 3 must wait for the baseline/legacy decision. Implementing 2/3 first would add validator failures and muddy the security fixes' evaluation.
3. **The Oct 16 plan (CODEX-SECURITY-HARDENING-PLAN) remains directionally sound** for its scope (P0-6 ≈ Package 2, I-10 ≈ Package 3) but predates the scanner-evasion and rollback findings and proposes CI changes outside this round's scope. Nothing in it contradicts this review; its "no tests in this round" stance is superseded — the tests above are required for acceptance.
4. **No ratification drift:** none of the four packages requires or implies DEC-7301/7302/7303 approval; the scanner hardening explicitly must not be recorded as DEC-7302 ratification. The disputed Round 26 record and sidecar remain untouched; hashes re-verified after inspection.
5. **Confirmed vs hypothesis ledger:** Confirmed — scanner misses 4 forms; SSH host-key disabled; uninstaller manifest-fed unconfined `rm -rf` (incl. add-not-replace semantics); CWD-relative deletion; snapshot non-atomicity; deletion set exceeds allowlist (live probe); unlink no error handling. Hypothesis-grade — `GIT_CLONE_PROTECTION` semantics; `npx skills remove` injection; manifest-shape laxity; TOCTOU windows; `exec`-based evasion.

## VERDICT

The remediation package is **plannable and narrowly scoped as four independent units**, with this ordering: **1 → 4 → (User decision) → 2 → 3**. Packages 1 and 4 are implementable with no governance preconditions beyond recording security-only intent; Packages 2 and 3 are security-real but legacy-pathspec-entangled and require the User's explicit baseline/legacy-diff decision first. No implementation has begun, per the round's restrictions. This report is new and timestamped; no earlier report was modified.
