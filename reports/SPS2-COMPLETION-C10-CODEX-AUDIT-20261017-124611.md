# SPS2 Completion C10 — Capability Validators and P7 Prerequisites

**Audit date:** 2026-10-17 (Asia/Dhaka)
**Agent:** Codex C10 read-only audit
**Repository:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`
**Verdict:** **NEEDS REVISION** — the P2/P3/P4/P5 validators remain fail-closed on preserved baseline deltas; the P4/P5/P7 phase checks contain stale or incomplete P7 classification; the historical P7 status records need reconciliation. No fixes or governance decisions were made.

## Scope and preservation

Read the completion backlog and coordination log first, then the current P2/P3/P4/P5 and P7 validators, the phase audits and decision records, the legacy exception helper/manifest, and the recorded P7 implementation report. Ran only validators and a focused read-only unit-test command. No source, CI, baseline, manifest, governance, decision, evidence, or P10 file was changed by this audit. The coordination log and backlog were not edited.

Branch and HEAD at both captured snapshots: `build/roadmap-p3-completion` / `c49f3852e1c31d0136269c80fe58201b059af3ec`.

| Snapshot | Tracked modified entries | Untracked porcelain entries | Expanded untracked files | Staged | Stashes |
|---|---:|---:|---:|---:|---:|
| Before report creation | 42 | 27 | 194 | 0 | 0 |
| Expected after this declared report | 42 | 27 | 195 | 0 | 0 |

The `.sps/` changes were a known concurrent Codex memory/report update around 12:39–12:40 +06, confirmed by the parent agent: `.sps/agent.md` and `.sps/handoff.md` modified, `.sps/content-model.md` added, and the P7 classification corrected in the C0–C3 report. I preserved them. No unrecognized path-count change was observed. The P2/P3/P4/P5 validators themselves were already modified in the shared worktree before this C10 report; findings below describe the live versions and do not claim ownership of those edits.

## Commands and results

All four phase validators exited 1. Their negative suites reported zero missed cases.

| Exact command | Exit | Current result |
|---|---:|---|
| `bash sps2/tools/validate-p2.sh` | 1 | P2 invalid: 68 passed / 9 failed / 0 missed; 22 negative cases correctly rejected. The required deliverables and research/approval checks passed; the 9 failures are protected-path deltas below. |
| `bash sps2/tools/validate-p3.sh` — first run during the concurrent `.sps/` update | 1 | 67 passed / 9 failed / 0 missed; 18 negative cases correctly rejected. It reported `.sps/` governance untouched. |
| `bash sps2/tools/validate-p3.sh` — bounded rerun after that update | 1 | 66 passed / 10 failed / 0 missed; 18 negative cases correctly rejected. It reported `.sps/` governance modified in addition to the 9 legacy/baseline paths. This is a state-timing difference, not evidence of deterministic validator behavior across one unchanged tree. |
| `bash sps2/tools/validate-p4.sh` | 1 | P4 invalid: 57 passed / 11 failed / 0 missed; 22 negative cases correctly rejected. The 11 failures are the 9 protected-path deltas plus 2 P7 path-existence findings. |
| `python3 -B sps2/tools/validate-p5.py` | 1 | P5 invalid: 44 passed / 1 failed / 0 missed; the single reported failure groups the same 9 protected-path deltas. Its embedded P5 unit check reported 48 passing tests. |
| `python3 -B sps2/tools/validate-p7-readiness.py` | 0 | 30 checks passed / 0 failed, plus 7 negative cases. This is a false-green for the claim that no P7 implementation deliverables exist; see findings. |
| `python3 -B -m unittest discover -s sps2/tests -p 'test_p7_zero_adapter_readiness.py' -v` | 0 | 3 tests passed. This suite checks the zero-adapter portability condition, not the P7 deliverable-classification defect. |
| `python3 sps2/governance/legacy_exceptions.py --root /Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main --baseline c11da27 --pathspec skills --pathspec scripts --pathspec plugins --pathspec .github --pathspec templates --pathspec README.md --pathspec CHANGELOG.md --pathspec CATALOG.md --pathspec '*.sh' --pathspec '*.ps1' --exclude-prefix sps2/` | 1 | Listed exactly the 9 protected-path deltas below. |

The first and rerun P3 outcomes differ because the shared `.sps/` tree changed during the audit. The parent confirmed that concurrent update. The final P3 state observed after the update is 66/10; the first 67/9 result should not be used as current evidence.

## Classification of the P2/P3/P4/P5 failures

### Protected baseline and legacy-path deltas — expected fail-closed behavior

The helper output and validator failures name these nine paths:

1. `.github/expected-test-modules.txt`
2. `.github/workflows/sps-ci.yml`
3. `.sps/tools/validate-capability.sh`
4. `.sps/tools/validate-control.sh`
5. `.sps/tools/validate-governance.sh`
6. `scripts/check-update.ps1`
7. `scripts/check-update.sh`
8. `skills/sps/scripts/check-update.ps1`
9. `skills/sps/scripts/check-update.sh`

These are tracked modified paths, not missing deliverables. The active DEC-7301 exception manifest pins eight *different* files and explicitly excludes the four `check-update` paths above. The other five are test-discovery/CI or legacy validator files and are not among its pinned exceptions. The current validators therefore correctly fail closed against the pinned `c11da27` baseline. This audit does not determine that any delta is acceptable, and no manifest, CI, or baseline change is proposed as an automatic fix. Acceptance or a new baseline remains User-gated.

P2, P3, and P4 each count the nine paths as nine failed checks. P5 groups the same findings into one failed check. These count-format differences are not additional defects.

### Missing P2/P3/P4/P5 artifacts

The live validator output reports every required P2 and P3 deliverable present and all phase-specific record checks passing. P4 and P5 implementation/record checks also pass apart from the path deltas and P4's two P7 checks. C10 found no missing P2/P3/P4/P5 required artifact that explains the current failures. No empty artifact should be created to change a gate.

## P4/P5 P7 checks and tracked-at-HEAD evidence

`validate-p4.sh` checks `os.path.exists()` for `decisions/P7-DECISIONS.json` and the `memory` directory, then prints `P7_ARTIFACT_CREATED`. Both are tracked at the current HEAD, and the P7 decision/memory files are clean in the current worktree. `git ls-tree -r --name-only HEAD` confirms, among others:

- `sps2/decisions/P7-DECISIONS.json`
- `sps2/memory/P7-IMPLEMENTATION-REPORT.md`
- `sps2/memory/memory-layout.json`
- `sps2/memory/team-bootstrap.md`
- `sps2/tools/isolation_validator.py`
- `sps2/tools/rollback-memory-layout.py`
- `sps2/tools/validate-bootstrap.py`
- `sps2/governance/P7-THREAT-MODEL.md`

The files are not newly untracked or modified by this C10 run. Git history records P7 authorization at `8ae4068` on 2026-10-05 16:04 +06, P7 pre-approval fixes at `91b82e3` on 2026-10-05 20:09 +06, and completion approval at `75585b2` on 2026-10-05 21:15 +06. Therefore:

- The P4 check accurately observes that those paths exist in today's tree.
- Its label `ARTIFACT_CREATED` is not supported as a statement that they were created by this worktree/audit; the check does not compare against a P4 checkpoint or creation diff.
- It also treats a later, explicitly recorded P7 phase as an unconditional P4 failure when running the old P4 validator against the full later tree. That is a phase-context defect for current retrospective validation. The P4 gate must use a documented phase snapshot or a policy-approved, phase-aware rule; simply suppressing these two failures would conceal history and is not recommended.

P5 has the same “P7 must never start, in any phase” framing but a different incomplete allow-list: it checks only P7 requirements/evidence/tasks/handoff/bootstrap as forbidden and places the official memory layout/team-bootstrap/report paths in its governance allow-list. Its scan also does not recognize `tools/isolation_validator.py` as a P7-named file. Thus P5 does not consistently report the tracked P7 implementation artifacts. The live P5 output did not emit a P7 failure; because the legacy failure already existed, it also did not emit the conditional “P7 decision records only” pass message. This is a current-tree vs historical-phase mismatch, not authorization to alter the record.

## P7 prerequisites and historical-artifact status

The repository contains records for all four readiness decisions D-P7-A through D-P7-D, each marked `APPROVED` by User on 2026-10-04. D-P7-B requires roadmap P3 to be completed before P7; `ROADMAP-P3-DECISIONS.json` records its completion state as `APPROVED` on 2026-10-05, with two adapters, the portability test, resume checklist, and evidence listed as delivered. D-P7-D requires the threat model; `sps2/governance/P7-THREAT-MODEL.md` is present. `P7-DECISIONS.json` records explicit P7 implementation authorization and completed-scope approval dated 2026-10-05. The P7 roadmap deliverables are present at HEAD.

These are repository-record facts, not an independent authentication of the underlying User messages. C10 did not ratify any approval. On the face of the repository records, the prerequisite artifacts and approvals were present before the P7 implementation and the P7 deliverables were later approved; there is no file-level prerequisite absence established by this audit.

The root `AUDIT-P7-READINESS-AND-DECISION.md` is a historical snapshot that still carries `P7 NOT STARTED / NOT APPROVED` and “deliverables absent” language. Its latest content change is commit `e743780` at 2026-10-05 15:11 +06, before the P7 implementation authorization and approval commits above. That explains its former status but makes those statements stale for the current tree. The missing item is a current reconciliation/closing status that supersedes that snapshot—not the P7 implementation files themselves. Separate P7 requirements/evidence/tasks/handoff packages are not among the roadmap's three approved deliverables, so their absence is not by itself a C10 blocker.

### Actual P7 validator defect — false green

`validate-p7-readiness.py` prints `no P7 implementation deliverable exists` although the official roadmap deliverables are tracked: `memory/memory-layout.json`, `memory/team-bootstrap.md`, and `tools/isolation_validator.py`. The implementation classifier's `P7_IMPL_ARTEFACTS` list checks only P7 requirements/evidence/tasks/handoff/bootstrap paths. It then explicitly excludes the two memory deliverables by classifying them as governance artifacts; the isolation validator is separately allow-listed. Consequently, the live validator reports **30/0** while not proving the claimed absence. Its negative cases do not plant these actual roadmap deliverables to test this boundary.

This is a real validator/phase-model defect, distinct from the nine baseline failures. P4/P5/P7 currently express incompatible assumptions about whether P7 may exist, and the readiness check conflates “not authorized/not started” with later implementation status. A repair proposal should define separate readiness and implementation/approval modes, use an explicit phase or checkpoint input, and test both a pre-authorization tree with planted deliverables and the currently approved historical tree. Do not change this validator in C10.

## Findings and next actions

1. **Keep P2/P3/P4/P5 fail-closed** on the nine protected baseline paths until the User decides how to handle those deltas. Do not amend the manifest or CI/baseline records to produce green output.
2. **Treat current P3 result as 66/10** after the known `.sps/` update. Record the first 67/9 run only as a pre-update observation.
3. **Repair the P7 phase model in a separate authorized task:** reconcile the historical audit; distinguish existence, introduction time, authorization, implementation, and completion; then add regression fixtures for the official P7 deliverables. Preserve current history and approval records.
4. **Re-run P4/P5/P7 validators only after that bounded change is authorized and reviewed.** P7 readiness's present 30/0 is not evidence that no implementation deliverable exists.

No implementation, suppression, baseline change, approval inference, staging, commit, push, deployment, publication, merge, or release occurred. No P10 or project/release readiness conclusion is changed by C10.
