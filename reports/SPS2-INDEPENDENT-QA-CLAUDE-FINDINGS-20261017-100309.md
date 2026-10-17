# SPS2 INDEPENDENT QA (CLAUDE LEAD) — FINDINGS REGISTER

Register time: 2026-10-17T10:03:09+06 (suffix 20261017-100309)
Owner: Claude (independent adversarial QA lead). Every finding below was reproduced
directly against the live tree during this audit; none is copied from Codex's or my
own earlier reports without independent re-verification.

Severity totals: 1 CRITICAL, 6 HIGH, 6 MEDIUM, 3 LOW, 4 INFO — 20 findings.

---

## QA-C-001 — CRITICAL (governance) — Round 26 record falsely attributes approval to the User
- **Reproduced:** `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json` SHA-256 `7c35617b…` carries `APPROVED` / `decided_by: User` fields. The actual User has explicitly denied approving DEC-7301/7302/7303 in this authorized context. The correction sidecar (`a50bfd25…`) is the controlling provenance document.
- **Impact:** any consumer reading the record alone would treat unapproved decisions as ratified.
- **Disposition:** UNRESOLVED — User decision required. Do not edit the record or sidecar.

## QA-C-002 — HIGH (code defect / false-green control) — Import scanner misses rebind, getattr, and subscript dynamic-loader forms
- **Reproduced (temp-fixture probe, live tree untouched):** with the approved four-record manifest present, `scan_import_exceptions` returned `ok=true`, zero violations for:
  - `from importlib import import_module; f = import_module; f('domain.seo.audit')` — MISSED
  - `m = getattr(importlib, 'import_module'); m('domain.seo.audit')` — MISSED
  - `il.__dict__['import_module']('domain.seo.audit')` — MISSED
  - Controls: `importlib.import_module(...)` DETECTED; `import importlib as il; il.import_module(...)` DETECTED; `__import__(...)` DETECTED.
- **Root cause:** `_is_dynamic_import` (`sps2/governance/import_exceptions.py:105-121`) matches only `Name` callables equal to `__import__`/`import_module` and `Attribute` callables named `import_module`. A call whose callable is itself a `Call` or `Subscript` expression matches none. The code comment at line 112 claims getattr rebindings "must not evade" — the comment is not implemented.
- **Impact:** a forbidden dynamic `domain.seo` import using these forms would pass the scanner. This is Codex QA-0021 — independently CONFIRMED with a fourth missed form (bare-name rebind) that Codex's register did not list.
- **Disposition:** policy-blocked remediation (scanner hardening must not be read as DEC-7302 ratification). No edit made.

## QA-C-003 — HIGH (report inaccuracy, my own prior report) — P10 control counts in my second-pass report are wrong as a control-by-control description
- **Reproduced:** live gate (both `--json` and human output): exit 1, `OVERALL: FAIL (required controls failing: 7; integrity problems: 0; required controls: 16)`, controls[] = **9 PASS / 5 FAIL / 2 BLOCKED**.
- My `SPS2-SECOND-PASS-INTEGRATION-FINAL-20261017-092558.md:129` states "4 PASS / 12 FAIL of 16 required controls" — **not reproducible by any invocation tried** (JSON and human modes, with and without `--slice`). Line 117's "12/16 required controls FAIL" is likewise unsupported.
- **Reconciliation:** the live human-readable line says "required controls failing: 7" (5 FAIL + 2 BLOCKED). Neither "12" nor "4 PASS" matches any current output. The most plausible origin: in the earlier session the numbers were transcribed from memory of the pre-fix baseline rather than captured from the final run — the same report's other P10 statements (dynamic import at line 1944, exit 1, 0 integrity problems) are all accurate, so this is a transcription error in two lines, not a fabricated verification. Codex QA-0007's "contradicted" verdict is **CONFIRMED**; Codex's suggested methodology ("runtime subset") is not supported — the error is simpler and worse: unsupported numbers.
- **Impact:** my report materially misdescribed gate state; the corrected and verified statement is: **exit 1, 9 PASS / 5 FAIL / 2 BLOCKED, 7 required controls failing/blocked, 0 integrity problems, 16 required controls**. The gate's fail-closed conclusion in my report was still correct.
- **Disposition:** correction recorded here; prior report deliberately NOT edited (append-only correction policy).

## QA-C-004 — HIGH (governance) — Five normative documents cite UNAPPROVED decisions as authoritative; wording is an uncommitted addition
- **Reproduced:** `P7-THREAT-MODEL.md:148`, `P9-THREAT-MODEL.md:171-172`, `P3-REQUIREMENTS.json:289`, `P9-REQUIREMENTS.json:350-351`, `P10-REQUIREMENTS.json:14` contain "authorized by DEC-7301" / "approved by DEC-7302". `git show HEAD:<file> | grep` returns **0** such references for all five — the wording exists only in uncommitted worktree modifications. Codex QA-0014 CONFIRMED, with the sharper provenance fact that HEAD is clean of it.
- **Disposition:** User decision required (revert wording vs ratify decisions). No edit made.

## QA-C-005 — HIGH (coverage) — 481 of 1,057 tests (7 modules) run outside CI
- **Reproduced:** CI manifest `.github/expected-test-modules.txt` = 28 modules; live inventory = 35. The 7 absent modules measured individually: frontend 25+36+24, check_update_safety 27, p10_runtime_gate 320, round26 33, updater_safety 16 = **481**; tracked total = 576. Codex QA-0003 CONFIRMED (its interim 249 figure was corrected to 481 in its own final report; 481 verified here).

## QA-C-006 — HIGH (security) — Installer disables SSH host-key verification
- **Reproduced:** `install.sh:15`: `export GIT_SSH_COMMAND="ssh -oBatchMode=yes -oStrictHostKeyChecking=no"`. Codex QA-0009 CONFIRMED.
- **Practical precondition:** requires network clone path to be exercised; MITM exposure on first-contact clone.

## QA-C-007 — HIGH (security) — Uninstaller deletes manifest-controlled and fixed paths without confinement
- **Reproduced:** `uninstall.sh:99` `rm -rf "$p"` over `$HOME`- and CWD-relative skill paths; `uninstall.sh:167-178` `rm -rf "$dest_root/sps"` and `.../sps-cms` where `dest_root` may come from the user-writable `$HOME/.sps/install-manifest.env` (`SYNC_PATHS=`). A manifest poisoned with `SYNC_PATHS=/` would make `dest_root/sps` = `/sps`; the loop also re-iterates DEFAULT_SYNC_PATHS unconditionally (line 167 includes both arrays). Codex QA-0010 CONFIRMED; nuance: `SYNC_PATHS` only overrides when the manifest key is present, but there is no path validation on the value.
- **Disposition:** legacy-pathspec policy-blocked remediation; User authorization required to edit.

## QA-C-008 — MEDIUM (code defect) — `create_snapshot` is not atomic despite its docstring
- **Reproduced:** `sps2/tools/rollback_seo.py:234-249` — docstring says "Atomically record"; implementation copies file-by-file directly into the live snapshot directory with no temp-dir + rename. An interruption leaves a partial snapshot whose manifest is never written (manifest is written last), so restore would fail on missing manifest — fail-closed by accident, but the atomicity claim in the docstring is false. Codex QA-0019 CONFIRMED.

## QA-C-009 — MEDIUM (governance) — Decision checkers cannot authenticate a literal User attribution
- **Reproduced:** `check_sps2.py` / `check_p3.py` validate structure and reject agent-attributed approvals, but no mechanism distinguishes a genuine User act from a record asserting `decided_by: User`. Codex QA-0016 CONFIRMED. Live handoff records pass with clean stdout/exit 0 (spot-checked HANDOFF-P1, HANDOFF-P4); live registry passes (exit 0).

## QA-C-010 — MEDIUM (provenance) — `.claude/settings.json` is empty in worktree, non-empty at HEAD
- **Reproduced:** worktree file = 0 bytes (sha256 = e3b0c442…, the empty-string hash); `git show HEAD:.claude/settings.json` = `{"enabledPlugins": {}}` (sha256 prefix 0fe84d03…). Codex QA-0017 CONFIRMED. Provenance unresolved; do not edit.

## QA-C-011 — MEDIUM (requirements) — P9 requirements internally contradict on rollback buildability
- **Reproduced:** `P9-REQUIREMENTS.json` line 351 ("no longer guarantees that Home remains buildable") directly above line 352 ("Rollback rehearsal proves deletion of domain/seo/ leaves core validators passing"). Pre-existing in HEAD. Codex QA-0018 CONFIRMED.

## QA-C-012 — MEDIUM (validator design) — Two-baseline split across validators explains persistent count asymmetry
- **Reproduced (new finding, not in Codex's register):** `validate-sps2.sh:210` runs `legacy_exceptions.py --baseline c49f3852` (current HEAD) and sees only the 4 modified check-update mirrors; `validate-p2.sh:205`, `validate-p3.sh:320`, `validate-p4.sh:498`, and `validate-p5.py:308` all use `--baseline c11da27` (an older commit) and therefore also flag `.github/expected-test-modules.txt`, `.github/workflows/sps-ci.yml`, and three `.sps/tools/validate-*.sh` files — which are **byte-identical to HEAD** (`git diff HEAD --stat` empty for them). The extra P2/P3/P4/P5 failures are baseline-age artifacts, not live divergence. Neither baseline is cross-checked against the manifests' `baseline_commit` (consistent with the earlier F-10 policy-blocked finding).
- **Impact:** anyone comparing validator failures across phases without knowing the split will misread 9/10/11 failures as live tampering. It also means P2/P3/P4/P5 can never go green on those checks without either advancing their baseline (a governance act) or reverting committed work.

## QA-C-013 — MEDIUM (environment) — PowerShell runtime behavior untestable; PS checks partly static pins
- **Reproduced:** `pwsh` not installed; `test_updater_safety` skip at line 305 confirmed (`skipUnless(shutil.which("pwsh"), …)`); PS-side verification limited to static string/order assertions (17 assert sites). Codex QA-0012/0023 CONFIRMED. Static controls that DO exist in the .ps1 source: TLS 1.2 pin (line 20), atomic state write via temp + `Move-Item -Force` (lines 89-91), capped regex `{1,9}` (line 32), freshness `$last -le $now` (line 132).

## QA-C-014 — LOW (contract) — Version comparison is semver-like, not full SemVer
- **Reproduced:** `check-update.sh:58-96` numeric compare with prerelease handling; no build-metadata ordering, no numeric-identifier-with-leading-zero rule beyond the 10# base-10 fix. Codex QA-0013 CONFIRMED. Accepted residual.

## QA-C-015 — LOW (reliability) — Installer mirror sync non-atomic
- **Reproduced:** `install.sh:256-263` plain `cp -R` into live destination roots; interruption leaves partial mirrors. Codex QA-0011 CONFIRMED.

## QA-C-016 — LOW (maintainability) — Offline suite emits resource warnings but stays green
- **Reproduced (partially):** suite green under `-W error::ResourceWarning` for the updater module spot-check; full-suite warning surface not exhaustively re-characterized. Codex QA-0024 PARTLY CONFIRMED (low impact either way).

## QA-C-017 — INFO — Test-count reconciliation: 1,057/0/2 verified twice; Codex 1,051 was a historical snapshot
- **Reproduced:** two full runs (38.9s, 39.1s), identical counts, exit 0. Skips: `test_p17_endtoend` (P17_AJV_ROOT unset, deliberate per GOVERNANCE.md §4) and `test_updater_safety` (pwsh unavailable). Codex's 1,051 vs my 1,057 delta = +6: my second-pass session added tests (round26 28→33 net +5 across two matrices, isolation +3, minus baseline differences) — both prior reports' claims are consistent once the +6 growth is attributed; Codex QA-0004 CONFIRMED.

## QA-C-018 — INFO — Inventory-count "discrepancy" is pure methodology
- **Reproduced:** `git status --porcelain` = 65 lines (39 ` M` + 26 `??`); `git ls-files --others --exclude-standard` = 177 expanded files (59 under `reports/`, 118 elsewhere). Codex's 26/172-177 and my 65 are different units of the same tree. Codex QA-0002 CONFIRMED.

## QA-C-019 — INFO — All 19 second-pass fixes are present in the live tree; authorship report-supported only
- **Reproduced (spot-verified each):** decision-identifier guards (check_sps2.py:60-65,304-305; check_p3.py:25-33), dup-ID guards (check_sps2.py:259,283), scanner relative-import + attribute handling (import_exceptions.py:105-160), rollback digest/containment/file_count/rehearsal guards (rollback_seo.py:284-317,422-487), N18 checker-output control (validate-p4.sh:927-945), P5 s7/s8/s9 (validate-p5.py:239-278), P17 Ran>=1 guards (validate-sps2.sh:241-343), version caps + future-ts + atomic writes (both updaters), gate sys.path/fresh/history (p10_runtime_gate.py:1940-1948 area). Line pins 1944 verified accurate against the file. Codex QA-0025 CONFIRMED.

## QA-C-020 — INFO — Codex deep-QA dossier quality assessment
- Codex's 25 findings: 24 independently CONFIRMED (QA-0021 confirmed with an additional missed form; QA-0024 partly), 0 contradicted. Its P10 9/5/2 count is the correct current state; its challenge of my 4/12 claim stands (see QA-C-003). Its inventory, hash, and CI tables all reproduced exactly (backup manifest hash `be3e8cc4…` also verified present and matching). Its verdict "QA-not-passed" is supported by the evidence in this audit.
