# SPS2 Completion-Record Addendum — 2026-10-18 (B14 Final Operator Handoff)

**Type:** B14 — final operator handoff / updated completion record (dossier addendum).
**Author:** Claude (build manager), under the User's standing directive.
**Supersedes (in status only):** the 2026-10-17 dossier snapshot in `SPS2-PROJECT-COMPLETION-RECORD/` (files 00–05), which recorded **IN PROGRESS / NOT READY FOR RELEASE**. The dossier files themselves are preserved byte-for-byte as historical record — same rule as the dossier's own "do not rewrite governance history." This addendum updates the state; where this addendum and a dossier file disagree, this addendum's dated evidence (below) is current.
**Live state at writing:** branch `main`, HEAD `56e74ee48afabdd70ff6d0240f0e650f638813ef` (merge of PR #7, merged 2026-10-17T22:01:30Z), working tree clean (0 porcelain entries, 0 staged, 0 stashes).

---

## 1. What changed since the dossier's 2026-10-17 snapshot

The dossier was written against branch `build/roadmap-p3-completion`, HEAD `c49f3852…`, with an 83-entry dirty worktree and no CI. Since then, in sequence:

1. **Repo restructure:** `sps2/` → `framework/sps2/` (with `framework/domain/{cms,frontend,seo}/`). All dossier file-02 hash paths that reference `sps2/…` are stale as paths; the governed content moved and was re-pinned under the new layout.
2. **PRs #1–#7 merged to `main`** (2026-10-17T18:40Z → 22:01Z): v4.1.0 hard laws/legal gate/lesson channel → v4.2.0 → user guide + README refresh (PR #4) → T-19 ecosystem scan + **v4.3.0** stamp (PR #5) → T-20 lessons→validators + T-23 directory hygiene (PR #6) → **PR #7: T-24..T-37 hardening batch + audit fixes** (commit `a6a675f`: "12 agents, 4 external-CLI audits" — codexx, codex, opencode, plus 6 Claude audits).
3. **Roadmap T-19..T-37 completed** (all recorded finished 2026-10-17/18 in `.sps/task-queue.md`): backup/restore (T-24/T-26), secrets CI gate (T-25), real Windows CI smoke (T-27), kickoff-proof (T-28), skill-provenance pinning (T-29), docs-drift checker (T-30), product-proof gate (T-31), consent-gated hooks (T-32), lesson auto-proposals (T-33), self-verification law (T-34), plain-language mode (T-35), client bootstrap (T-36), weekly self-audit (T-37). T-38/T-39 **deferred by the User** (2026-10-18).
4. **6-layer audit wave** (commit `a6a675f`): all BLOCKER/MAJOR findings fixed — including two BLOCKERs (sps-status.sh date crash; isolation_validator scanning zero files), injection hardening in gen_law_test.py, p4/p6 validator false-positive fixes (T-22), and the CI validator-battery job.
5. **User ratification (2026-10-18):** R1–R5 all ratified via explicit interactive choice (`framework/sps2/decisions/DEC-USER-RATIFICATION-20261018.md`) — DEC-7301 (+7305), DEC-7302, DEC-7303, path-derivation rules, and the p4 documented-red policy (DEC-7304). This supersedes the disputed Round 26 APPROVED/User fields **for DEC-7301/7302/7303**.

## 2. Fresh verification evidence (run 2026-10-18, this session)

| Check | Command | Result |
|---|---|---|
| HEAD | `git rev-parse HEAD` | `56e74ee48afabdd70ff6d0240f0e650f638813ef` (branch `main`) |
| Expected modules | `grep -c "" .github/expected-test-modules.txt` | **51** |
| Full battery | `PYTHONPATH=. python3 -m unittest` over the 51 modules | **Ran 1236 tests in 66.710s — OK (skipped=3)** (0 failures, 0 errors) |
| Law check | `PYTHONPATH=. python3 framework/sps2/tools/check_laws.py .` | `== LAW CHECK: all machine-checkable laws hold ==`, exit **0** |
| Mirror parity | `diff -rq scripts skill/sps/scripts` | no output, exit **0** (byte-identical) |
| Docs drift | `python3 framework/sps2/tools/check_docs_drift.py` | clean (5 docs scanned), exit **0** |
| Secret scan | `bash scripts/secret-scan.sh` | `clean — no secret-shaped values in tracked files, diff, or agent/MCP configs`, exit **0** |
| Hygiene | `bash scripts/sps-hygiene.sh check` | exit **0**; reports 1 root-stray: `.secrets-allowlist` ("no determinable home"). This is the T-25 secrets-gate allowlist file, intentional at repo root; the checker's home-detection rule does not recognize it. Cosmetic finding, not a leak. |
| Worktree | `git status --porcelain \| wc -l` / `git stash list` | **0 / 0** — fully clean, unlike the dossier's 83-entry snapshot |
| Manifest | `framework/sps2/governance/legacy-exception-manifest.json` | **57 pinned exceptions** (`exception_count: 57`), re-pinned via the DEC-7301/DEC-7305 ordering law |
| CI on PR #7 | `gh pr view 7` | MERGED; statusCheckRollup **13 entries, all SUCCESS**, spanning 7 distinct jobs: secret scan, Lint + smoke, **Windows installer + doctor smoke**, Version sanity, PowerShell syntax, Python unit tests, **Validator battery** |
| windows-smoke workflow | `gh run list --workflow=windows-smoke.yml` | `success` on `main` (2026-10-17T22:01:32Z) and on the PR branch |
| P10 runtime gate | `p10_runtime_gate.py --slice framework/sps2/project/SLICE-P10-01.json --slice-id-history … --build-dir …` | **OVERALL: FAIL (required controls failing: 1; integrity 0; required controls: 16), exit 1** — the single failure is `[BLOCKED] exposure-declaration` (REQ-P10-09 c.7 / D-P10-1): no observed bind exists because Phase A has no network exposure; the fail-closed control correctly refuses an unprovable declaration. 15 of 16 controls PASS. |

## 3. B0–B14 disposition (dossier file 03 backlog)

Status vocabulary per the dossier. `DONE` requires evidence for the exact item, dated today.

| ID | Item | Status now | Evidence / basis |
|---|---|---|---|
| B0 | Rebaseline | **DONE (superseded baseline)** | Dossier checkpoint was its own DONE; today's rebaseline: `main` @ `56e74ee`, tree clean 0/0/0. The 83-entry dirty snapshot is obsolete. |
| B1 | Reconcile older backlog/decision packet | **DONE** | Reconciled through the ratification record + this addendum; historical rows untouched. |
| B2 | C4 repair cross-review (Claude) | **DONE (superseded)** | The 2026-10-18 audit wave (commit `a6a675f`) included 6 Claude audits + 3 external-CLI audits; the C4-surface blockers found (isolation_validator zero-file scan) were fixed and the full battery passes. Gateway unavailability is moot. |
| B3 | C5 cross-review closure | **DONE (superseded)** | Same audit wave; updater/bootstrap suites pass inside the 1236-test battery (`test_check_update_safety`, `test_updater_safety` in the 51-module list). |
| B4 | P10 dynamic import reassessment | **RESOLVED BY RATIFICATION (not by refactor)** | The importlib dynamic import remains at `framework/sps2/tools/p10_runtime_gate.py:1944`, governed by the 4-group exception manifest (`p10-p9-import-exception-manifest.json`, DEC-7302). No behavior-preserving refactor was made; instead **the User ratified DEC-7302 on 2026-10-18** (R2), converting the disputed-exception blocker into an approved exception. Gate/manifest not weakened; gate still fail-closed. |
| B5 | Narrow attribution predicate fix | **PARTIAL — superseded by design decision; do NOT claim done** | Verified in `framework/sps2/tests/test_attribution_policy.py`: legitimate names ("Jane Self", "Nora Script", "Autonomous Council") are NOT rejected (test line 391-394), and "Agent (self-approved)" (the POSCTRL-G fixture) IS rejected via the token "Agent" (line 403-405). **However**, the literal `"Self (self-approved)"` decider is **accepted by design** (test line 407-424: "currently accepted by design; if this fails, 'self' became a token and the open decision record must be resolved"). B5's original exit condition — reject literal self-approval as evidence — is therefore NOT met; the predicate's behavior was pinned by a later design decision with an open decision record, not by the B5 fix. 68 tests in the attribution suite pass. Residual: the open decision record on the `Self`-referent token remains user-owned. |
| B6 | Package 2 installer SSH host-key | **DONE** | `install.sh:19` / `install.ps1:9`: `GIT_SSH_COMMAND` uses `-oBatchMode=yes -oStrictHostKeyChecking=accept-new` (first-use accept, changed-key reject). Covered by CI "Windows installer + doctor smoke" (SUCCESS). |
| B7 | Package 3 uninstaller confinement | **DONE** | `uninstall.sh` `safe_rm()` (line 119) and `uninstall.ps1` `Remove-ConstrainedItem()` (line 85) confine deletions to allowlisted roots and reject symlinked/traversal targets. |
| B8 | C10/P7 validator revalidation | **DONE** | T-22 closed: p4 P7 authorization gate + tokenize-based p6 scan removed the false positives; all validators green in CI's Validator-battery job and locally. |
| B9 | R-1 scanner residual (tuple unpack, walrus, container storage, dynamic getattr) | **DEFERRED (unchanged)** | No new in-tree reproducer or bounded high-value hardening case has appeared; deferral basis unchanged from the dossier. |
| B10 | Protected decision/provenance queue | **PARTIALLY RESOLVED — residual BLOCKED_USER** | **Resolved 2026-10-18:** DEC-7301/7302/7303 ratified (R1–R3, `DEC-USER-RATIFICATION-20261018.md`), superseding the disputed Round 26 fields for those three decisions. **Still user-owned and unresolved:** the broader Round 26 attribution/correction disposition beyond 7301-7303, `.claude/settings.json` provenance (file currently 27 bytes, `{"enabledPlugins": {}}`), P5 source-authorization provenance, and the DEC-0001/DEC-0032 push-history reconciliation (only the single DEC-0032 push is recognized; `.sps/STATE.md` KEEP_LOCAL_ONLY tension remains). |
| B11 | CI/test discovery for untracked modules | **DONE** | Superseded by user-approved CI evolution: `.github/expected-test-modules.txt` now pins **51 modules** (was 28 tracked + 7 untracked = 35); CI runs the deterministic module list with MIN_TESTS 1000; the 1236-test battery runs from exactly this list locally and in CI. |
| B12 | Authentic P10 prerequisites | **BLOCKED_USER (partially advanced)** | Advanced since the dossier: slice history (`SLICE-ID-HISTORY.json`), real build output (`SLICE-P10-01-build/` with index.html/robots.txt/sitemap.xml), gate_record with fresh digests, published CMS content, and a 15/16-PASS gate run now exist. **Still missing/blocked:** the final explicit User approval act (`user_approval` is `null`; inventory_state `COMPLETE_AWAITING_USER_APPROVAL`), an observed exposure/bind declaration (no component produces one in Phase A — by-design BLOCKED), and post-Phase-A operational evidence. The gate correctly remains **FAIL / exit 1** and must not be waived. |
| B13 | Final verification after implementation | **DONE (offline scope; P10 honestly red)** | Today's evidence in §2: 1236 tests OK (3 skips), check_laws exit 0, mirrors identical, docs-drift clean, secret-scan clean, hygiene exit 0 (1 cosmetic stray noted), CI 13/13 SUCCESS incl. Windows smoke + validator battery. P10 gate recorded as FAIL exit 1 with the single by-design BLOCK — kept visible, not suppressed. |
| B14 | Final operator handoff | **DONE — this report** | Complete handoff below. |

## 4. Readiness verdict — both products, stated separately

### 4.1 The SKILL (`skill/sps/`, distributed product) — **WORKING / READY FOR USE as a skill**

- Version **4.3.0** (`skill/sps/VERSION`), stamped across VERSION/CHANGELOG/README/templates/SKILL.md.
- Install/update/uninstall lifecycle hardened (Packages 2/3 + C5 fixes), mirrors byte-identical, provenance-pinned (T-29), doctor + backup/restore + hooks shipped.
- CI: 13/13 checks SUCCESS on the merge commit, including a **real Windows installer + doctor smoke** on `windows-latest` and the validator battery. Law check, docs-drift, secret-scan, hygiene all clean locally at HEAD.
- 1236-test battery green. Task queue T-19..T-37 complete; T-38/T-39 user-deferred.
- Honest limits: PowerShell runtime validation beyond the CI smoke is CI-only; third-party skill supply chain remains trust-on-review (per the product brief's trust boundary); the `Self (self-approved)` attribution token question is pinned by design with an open decision record.

### 4.2 The framework (`framework/sps2/`) — **NOT READY by design (release gate intact)**

- P10 runtime gate: **OVERALL FAIL, exit 1** — 15/16 controls PASS; the single BLOCK (`exposure-declaration`) is by-design fail-closed (REQ-P10-09 c.7 / D-P10-1): no Phase A network exposure exists, so no observed bind can exist, so the control refuses the declaration. This is the gate working correctly, not a regression.
- `P10-SECTION-INVENTORY.json` remains `COMPLETE_AWAITING_USER_APPROVAL` with `user_approval: null`; the transition requires a full gate PASS **and** a fresh explicit User approval act. Neither has occurred. The inventory's own `$comment` correctly states structural validity is not authority.
- Remaining to flip the framework verdict: a real exposure observation (post-Phase-A work) **and** the explicit User approval act. No agent may fabricate either. Until then the framework stays NOT READY, and that is the correct state.

**One-sentence verdict for operators:** the `/sps` skill is a working, hardened, CI-proven v4.3.0 product you can install and use today; the SPS2 framework's P10 release gate is intentionally and correctly still red pending real-world exposure evidence and an explicit User approval act — do not ship it as "released."

## 5. Remaining user-owned actions

1. **B12 / P10 approval act:** explicit User decision to transition the inventory (APPROVAL-MECHANISM OPTION A) — only after a full gate PASS, which in turn requires the exposure control to be satisfiable (Phase B / real bind observation).
2. **B10 residuals:** Round 26 broader attribution disposition; `.claude/settings.json` provenance; P5 authorization provenance; DEC-0001 vs DEC-0032 push-history reconciliation.
3. **B5 residual:** the open decision record on the `Self`-referent attribution token (accept-by-design vs reject) — user-owned policy choice.
4. **B9:** R-1 scanner residual remains deferred absent a reproducer.
5. **External audits:** the 2026-10-18 wave used codexx/codex/opencode + Claude audits; no DeepSeek (or other named external-model) audit is recorded anywhere in the repo — if one was expected, it is still **pending/not started**.
6. **T-38/T-39:** deferred by the User — build only on real demand.

## 6. Safe operator commands (verified at HEAD `56e74ee`)

```bash
PYTHONPATH=. python3 -m unittest $(grep -v '^#' .github/expected-test-modules.txt | tr '\n' ' ')   # 1236 tests
PYTHONPATH=. python3 framework/sps2/tools/check_laws.py .                                          # exit 0
python3 framework/sps2/tools/check_docs_drift.py                                                    # exit 0
bash scripts/secret-scan.sh                                                                         # exit 0
bash scripts/sps-hygiene.sh check                                                                   # exit 0 (1 cosmetic stray)
diff -rq scripts skill/sps/scripts                                                                  # exit 0
# P10 gate (expected FAIL exit 1 until approval act + exposure evidence):
PYTHONPATH=. python3 framework/sps2/tools/p10_runtime_gate.py \
  --slice framework/sps2/project/SLICE-P10-01.json \
  --slice-id-history framework/sps2/project/SLICE-ID-HISTORY.json \
  --build-dir framework/sps2/project/SLICE-P10-01-build
```

## 7. Provenance note

This addendum was produced in a single read/write session confined to `reports/` (this file) and the dossier `README.md` index append. No file in `SPS2-PROJECT-COMPLETION-RECORD/` other than `README.md` was modified; `.github/*`, `framework/sps2/governance/*`, `.sps/*`, `skill/sps/`, and `scripts/` were read-only. Working tree was clean before and after.
