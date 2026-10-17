# SPS2 Completion C11 — Legacy Findings Revalidation

**Audit time:** 2026-10-17 12:50 +06  
**Agent:** Codex C11 read-only audit  
**Repository:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`  
**Verdict:** **NEEDS USER DECISIONS / PARTIAL** — some older claims are stale after later committed safeguards; other risks remain current in the worktree or as unresolved policy/provenance questions. No remediation was attempted.

## Scope and preservation

Read the completion backlog and coordination log, then the prior C8–C10 audits, the P1–P4 remediation/review reports, the old end-to-end readiness report, the Round 19B and Round 20B audits, the backup QA reports, and the tracked DEC-0031 transcription. This report covers backup-manifest staleness/provenance, attribution self-approval, dead-checker false-PASS, CI test discovery, DEC-0001/push history and related authorization traceability, and overlaps with C5–C9.

Start snapshot: branch `build/roadmap-p3-completion`; HEAD `c49f3852e1c31d0136269c80fe58201b059af3ec`; 42 tracked paths with worktree status, 27 untracked porcelain entries (197 expanded untracked files), 0 staged paths, 0 stashes. The existing worktree is preserved. No `.sps/` path was written. Only this timestamped report was created by this audit. No tests, validator suites, installer/uninstaller, network command, CI run, or destructive operation was run.

## Findings register

| ID | Older claim | Live classification | Owner / boundary | Result |
|---|---|---|---|---|
| C11-01 | The local backup manifest is stale against the live worktree. | **CURRENT** | Preservation/provenance; no code fix | Reproduced: 614 manifest entries, 595 hashes match and 19 differ. The manifest hash matches the value in the QA reports. It is a point-in-time recovery source, not a current-state verification manifest. |
| C11-02 | The backup manifest proves provenance/current completeness. | **UNVERIFIED / NOT ESTABLISHED** | User-owned preservation provenance | A matching manifest-file digest establishes that the same manifest was read; it does not authenticate who created the backup, its authority, or whether it is safe to restore over today’s worktree. Earlier reports describe it as a verified backup, but this audit did not inspect or authenticate the source archive. |
| C11-03 | `Self (self-approved)` passes the User-attribution predicate. | **CURRENT** | Attribution behavior is technical; acceptability/change is policy-gated | Reproduced: current predicate returns `True`; current test explicitly pins this behavior. The token `self` is deliberately excluded to preserve legitimate names such as `Jane Self`. A string heuristic cannot authenticate a real person. |
| C11-04 | Dead or silent checkers can make the named negative controls pass. | **STALE for cited controls in current HEAD** | Repairs are in committed validators; broader uncited controls unverified | Current HEAD’s P2/foundation/P3 wrappers fail on non-zero checker exit; P4’s cited negative controls require zero exit and a recognized verdict. The prior exact false-PASS path is not present at those sites. This is a source inspection, not an injected crash test; no claim is made about every checker/control in the repository. |
| C11-05 | `MIN_TESTS=500` alone lets an entire test module disappear without failing CI. | **STALE as stated; residual limits CURRENT** | CI/module baseline; changes require User authorization | Current committed workflow discovers tracked test files, checks a committed 28-module manifest, and checks that each discovered module actually ran tests. The old 26-module/558-test margin is historical and was not recomputed. The 500 floor remains and can miss test loss within modules if the module still runs and the total remains above 500. |
| C11-06 | New local SPS2 tests are all included in CI. | **CURRENT gap in the worktree** | CI/tracking/commit boundary is User-gated | Inventory: 35 `test_*.py` files under `domain/` and `sps2/`; 28 are tracked and listed in the manifest, while seven are untracked and absent from `git ls-files` discovery. A CI job from a clean checkout cannot run untracked files. Current local full-matrix counts in C0–C3 were not rerun here. |
| C11-07 | DEC-0001 still says local-only while a remote/push history exists. | **CURRENT** | User decision / incident disposition | `origin` is configured locally; local reflogs contain six timestamped `update by push` entries (three for `main`, three for `build/roadmap-p3-completion`), including an update to `c49f3852…` on 2026-10-16. DEC-0001’s local-only wording remains in `.sps/STATE.md`; the discrepancy audit still says the issue is recorded only and awaits User decisions. No live remote inspection was made. |
| C11-08 | No in-repo authorization instrument exists for commits `238c9e4` and `cdcbca8`. | **STALE in the narrow sense; provenance gap CURRENT** | User-only provenance decision | Tracked `sps2/decisions/PHASE3-COMMIT-AUTHORIZATION-TRANSCRIPTION-DECISIONS.json` contains DEC-0031 and transcribes the two scopes. It expressly says the sole narrative source is untracked and contains no verbatim User authorization; it asks whether that is sufficient. The record does not authorize a push. |
| C11-09 | Older installer/updater findings are all separate unresolved issues. | **PARTLY DUPLICATED** | See C5/C6/C7; no execution authorized | C5 already covers updater/check-update/bootstrap symlink, version comparison, cache, malformed-version, parity, and hash-provenance findings. Do not duplicate them. Installer unsafe defaults/data-loss findings remain a separate C6 scope; uninstaller path confinement remains C7. The dynamic P10 import is already recorded in C9. |
| C11-10 | P5 requirement/evidence edits lack a locating authorization instrument. | **UNVERIFIED; traceability gap remains open** | User/policy authorization provenance | The older readiness report identifies the gap. DEC-0031 covers only the two migration commits, and the attribution decision record expressly says P5 approval/verification state was not changed or authorized by it. The relevant P5 files remain modified in the worktree. This audit did not locate a specific authorizing User message or a separate record for those edits; absence in the inspected record set does not prove that no conversational authorization exists. |

## Evidence and exact commands

Commands below were run from the repository root; all are local/read-only. No remote was contacted.

### Backup manifest

1. `wc -l /var/folders/c8/kgc8r31x3b1fzwkd14nq0g_40000gn/T/shahid-online-backup-5xTEqSUu/manifest-v2.sha256` → **614**.
2. `shasum -a 256 /var/folders/c8/kgc8r31x3b1fzwkd14nq0g_40000gn/T/shahid-online-backup-5xTEqSUu/manifest-v2.sha256` → `be3e8cc43b7ee5a63fc34ee9f6a1b329ffe278515ee9bc2f7022a42392d916b5`, matching prior QA reports.
3. `set -o pipefail; shasum -a 256 -c /var/folders/c8/kgc8r31x3b1fzwkd14nq0g_40000gn/T/shahid-online-backup-5xTEqSUu/manifest-v2.sha256 | awk '/: OK$/{ok++} /: FAILED$/{bad++} END{printf "OK=%d FAILED=%d\n",ok,bad; if (bad) exit 1}'` → exit **1**, **595 OK / 19 FAILED**.
4. The 19 differing paths are `.sps/agent.md`, `.sps/handoff.md`, `.sps/plan.md`, `domain/seo/tests/test_isolation.py`, `scripts/check-update.ps1`, `scripts/check-update.sh`, `skills/sps/scripts/check-update.ps1`, `skills/sps/scripts/check-update.sh`, `sps2/governance/import_exceptions.py`, `sps2/tests/test_check_update_safety.py`, `sps2/tests/test_round26_governance_contracts.py`, `sps2/tools/check_p3.py`, `sps2/tools/check_sps2.py`, `sps2/tools/p10_runtime_gate.py`, `sps2/tools/rollback_seo.py`, `sps2/tools/validate-p2.sh`, `sps2/tools/validate-p4.sh`, `sps2/tools/validate-p5.py`, and `sps2/tools/validate-sps2.sh`.

The previous QA comparison reported 598/614 with 16 differences; the three `.sps/` paths account for the increase in this audit. The backup is useful as an older recovery point but should not be treated as a mirror of the current tree or restored wholesale over it.

### Attribution predicate

1. `sed -n '140,180p' sps2/governance/attribution.py` and `rg -n -C 2 'Self \\(self-approved\\)|self-approved|Jane Self' sps2/tests/test_attribution_policy.py` → predicate requires `APPROVED`, a non-agent-looking nonempty decider, and a date; the regression test explicitly expects `Self (self-approved)` to pass and protects `Jane Self` from false rejection.
2. `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=sps2/governance python3 -B -c 'import attribution; samples=[{"state":"APPROVED","decided_by":"Self (self-approved)","decided_on":"2026-10-13"},{"state":"APPROVED","decided_by":"Jane Self","decided_on":"2026-10-13"},{"state":"APPROVED","decided_by":"Claude","decided_on":"2026-10-13"}]; print([(x["decided_by"], attribution.approval_is_user_attributable(x), attribution.reason_not_attributable(x)) for x in samples])'` → self-approved string **True**, `Jane Self` **True**, `Claude` **False**. `-B` and `PYTHONDONTWRITEBYTECODE=1` avoided bytecode writes.

This reproduces the predicate, not the identity of any real approver. Changing the approved attribution semantics or revisiting the surname exception is a User/policy decision; do not add `self` to the global denylist as an automatic repair.

### Dead-checker paths

1. `git show HEAD:sps2/tools/validate-p2.sh | sed -n '34,53p'` → `assert_clean` captures the checker status and fails when non-zero; empty output passes only after exit zero.
2. `git show HEAD:sps2/tools/validate-sps2.sh | sed -n '38,58p'` → same fail-closed status check.
3. `git show HEAD:sps2/tools/validate-p3.sh | sed -n '112,128p'` → record/handoff checker calls fail on non-zero status.
4. `git show HEAD:sps2/tools/validate-p4.sh | sed -n '121,134p'` → the negative control fails on non-zero status and on a missing `PROMOTED`/`NOT_PROMOTED` verdict before evaluating the expected non-promotion result.

This is limited static verification of the cited paths. I did not execute or inject a dead checker into the validator scripts. CI and baseline changes are not proposed.

### Test discovery and minimum count

1. `find domain sps2 -name 'test_*.py' -print | sort | wc -l` → **35** worktree test modules.
2. `git ls-files 'test_*.py' '**/test_*.py' | wc -l` → **28** tracked modules.
3. `wc -l .github/expected-test-modules.txt` → **28** expected modules.
4. `comm -23 <(git ls-files 'test_*.py' '**/test_*.py' | sed -e 's/\.py$//' -e 's|/|.|g' | sort -u) <(sort -u .github/expected-test-modules.txt)` and `comm -13 <(git ls-files 'test_*.py' '**/test_*.py' | sed -e 's/\.py$//' -e 's|/|.|g' | sort -u) <(sort -u .github/expected-test-modules.txt)` → no output; tracked discovery and manifest sets match.
5. Untracked module inventory: `find domain sps2 -type f -name 'test_*.py' -print | sort | while IFS= read -r p; do git ls-files --error-unmatch "$p" >/dev/null 2>&1 || printf '%s\n' "$p"; done` → `domain/frontend/tests/test_content_slots.py`, `domain/frontend/tests/test_home_render.py`, `domain/frontend/tests/test_layout_registry.py`, `sps2/tests/test_check_update_safety.py`, `sps2/tests/test_p10_runtime_gate.py`, `sps2/tests/test_round26_governance_contracts.py`, and `sps2/tests/test_updater_safety.py`.
6. `sed -n '100,215p' .github/workflows/sps-ci.yml` → CI uses `git ls-files` discovery, requires the committed expected-module manifest, verifies each expected module is discovered, and greps test-run output to ensure every discovered module ran at least one test. It retains `MIN_TESTS=500`.

The guard prevents accidental loss of a listed whole module while its manifest remains unchanged. It does not authenticate a simultaneous change to the manifest, enforce an exact test count inside each module, or include the seven untracked worktree modules. The old “331 CI-invisible tests” count is not revalidated here; this audit verifies the seven module files, not their test-case count.

### DEC-0001, local push history, and authorization traceability

1. `git remote -v` → `origin https://github.com/SHAHID8142/Shahid-Master-Skill.git` for fetch and push.
2. `git reflog show origin/main --date=iso-strict --format='%gD %gs %H'` → three local entries labeled `update by push` on 2026-10-04.
3. `git reflog show origin/build/roadmap-p3-completion --date=iso-strict --format='%gD %gs %H'` → three entries labeled `update by push`: 2026-10-12 (`788bf8a…`), 2026-10-16 14:25 (`ef59f9e…`), and 2026-10-16 15:07 (`c49f385…`).
4. `git rev-parse HEAD '@{upstream}'` → both local names resolve to `c49f3852e1c31d0136269c80fe58201b059af3ec`; this is a cached local ref comparison, not a live remote query.
5. `rg -n -C 2 'DEC-0001|DEC-0002' .sps/STATE.md` → DEC-0001 remains recorded as `APPROVED / KEEP_LOCAL_ONLY`, and DEC-0002 says its identity obligation is not yet due because of that local-only premise.
6. `git ls-files --error-unmatch sps2/decisions/PHASE3-COMMIT-AUTHORIZATION-TRANSCRIPTION-DECISIONS.json` → tracked. `git status --short -- sps2/decisions/PHASE3-COMMIT-AUTHORIZATION-TRANSCRIPTION-DECISIONS.json reports/SPS2-PHASE3-DECISION-EXECUTION-20261016-082741.md` → DEC-0031 record is tracked; the narrative source is untracked.
7. `rg -n -C 2 'PROVENANCE LIMITATION|NO verbatim|not authority to push|unresolved_questions' sps2/decisions/PHASE3-COMMIT-AUTHORIZATION-TRANSCRIPTION-DECISIONS.json` → DEC-0031 explicitly identifies the source report's missing verbatim User wording, says it originates no approval, and does not authorize a push.
8. `rg -n 'Awaiting User decision|not approved|D1|D5' AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md` → the discrepancy document remains a recorded audit awaiting User decisions, not an amendment to DEC-0001/0002.
9. `rg -n -i -C 2 'P5-REQUIREMENTS|P5-EVIDENCE|P5 edits|P5-03 approval' sps2/decisions .sps/decisions reports/SPS2-FINAL-END-TO-END-READINESS-20261016-091500.md` → the old report records the P5 authorization traceability gap; DEC-0031 does not cover P5 files; the tracked attribution decision explicitly excludes changing P5-03 approval/verification state. No P5-specific User authorization source was established in this bounded recheck.

Reflogs are local evidence that local refs were updated with the reason `update by push`; without network access this audit cannot verify current GitHub refs, remote ownership, or who initiated each push. The six ref-update entries are not asserted to be six independently authorized human actions. No authorization instrument for these push events was located in the inspected decision material. This remains User-only disposition; do not amend decisions or change the remote/configuration.

## Cross-task boundaries and next decisions

- C5 already audits updater/bootstrap/check-update defects and the DEC-7301 hash-provenance issue. Keep those findings there; C11 did not rerun their probes.
- Installer/global auto-yes/destructive sync concerns are distinct from C5 and remain under C6’s authorization boundary. Uninstaller path confinement remains C7. No installer/uninstaller was executed.
- The P10 dynamic import and gate consequences are already captured in C9; C11 did not rerun the scanner.
- C8’s DEC-7301/7302/7303, correction-sidecar authority, and baseline questions remain User-gated. A passing hash check is not proof of approval.
- Decisions needed before this audit’s open items can be called resolved: (1) disposition of DEC-0001 and the push history, including DEC-0002’s identity trigger; (2) whether DEC-0031’s explicitly limited, agent-authored transcription is enough or the User will provide the original authorization basis; (3) whether the User can identify/provide the authorization basis for the P5 requirement/evidence edits; (4) the desired handling of self-asserted “self-approved” labels while preserving legitimate surname behavior; and (5) whether/when the seven untracked test modules should become part of the durable/CI-tested project, alongside the approved module/test-count policy.

No source, CI, baseline, governance, decision, manifest, P10, evidence, or `.sps/` file was edited. No fix, approval, staging, commit, push, deployment, publication, merge, or release is authorized by this report. Project and release readiness remain **NOT READY** under the completion backlog.
