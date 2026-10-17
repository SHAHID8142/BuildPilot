# SPS2 INDEPENDENT REVIEW — CODEX MASTER MISSION RESULTS

Report time: 2026-10-17T07:20:36+06 (suffix 20261017-072036)
Reviewer: Claude (independent agent), read-only mission.
Subject: the Codex master mission documented in
`reports/SPS2-MASTER-RESUME-BASELINE-20261017-001717.md` and
`reports/SPS2-MASTER-IMPLEMENTATION-AND-REVIEW-PACKAGE-20261017-002434.md`,
plus Codex's own follow-up self-verification
`reports/SPS2-MASTER-RESULTS-VERIFICATION-AND-DECISION-PACKAGE-20261017-071058.md`
(discovered during this review; assessed in §9).

**Controlling instruction honored throughout: DEC-7301, DEC-7302, and
DEC-7303 are treated as UNAPPROVED. Nothing in this report infers
approval from the decision record's `approval.state` fields, agent
messages, or test outcomes.** No file was edited, staged, committed,
pushed, deployed, published, or cleaned by this review. The only
filesystem change is this report.

---

## 0. Verification method

Every claim below is labeled:

- **[VERIFIED]** — I ran the check myself against the live repository in
  this session (07:11–07:20 +06).
- **[REPORTED]** — taken from Codex's reports; I did not independently
  reproduce it (or could not).

## 1. Q1 — Are Codex's reported results supported by the repository and evidence?

**Yes — every quantitative claim I tested reproduced exactly.** [VERIFIED]

| Codex claim | My independent run | Match |
|---|---|---|
| HEAD `c49f3852…`, 64 porcelain (39 modified tracked + 25 untracked), 0 staged, 0 stashes | identical | ✅ |
| 1,041 tests / 0 failures / 0 errors / 2 skips | `Ran 1041 tests … OK (skipped=2)` over all modules | ✅ |
| P10 gate: exit 1, overall FAIL, 9 PASS / 5 FAIL / 2 BLOCKED, 5 unresolved semantics | identical; FAIL = published-only-content, slice-id-uniqueness, evidence-authenticity, approval-authenticity, req-p10-07-reconciliation; BLOCKED = exposure-declaration, p9-deployment-audit | ✅ |
| validate-sps2.sh 78/4 | identical | ✅ |
| validate-p2 68/9, validate-p3 66/10, validate-p4 57/11, validate-p5 43/1 (all exit 1) | identical | ✅ |
| 5 updater mirror pairs byte-identical | `cmp` all 5 pairs | ✅ |
| Manifest canonical hashes `71a054df…` / `d8dd5039…` | match (previously recomputed in Round 27) | ✅ |
| 614-file pre-mission snapshot, 0 mismatches | re-ran full comparison: 614 checked, 0 bad, 0 missing | ✅ |
| Report hashes `3d214f2f…` / `241cb38b…` | match | ✅ |
| P17: two records `AWAITING_USER_APPROVAL`, others verified/approved | 13 task records: 2 AWAITING (TASK-P17-0003/0004), 10 APPROVED; 10 evidence records PASS | ✅ |
| P10 inventory `COMPLETE_AWAITING_USER_APPROVAL`, `user_approval: null` | matches gate output detail | ✅ |
| `.claude/settings.json` empty vs HEAD `{"enabledPlugins": {}}` | confirmed | ✅ |
| Backup branch on origin at `728dea6e…` | confirmed via `git ls-remote` (earlier this session) | ✅ |

**Discrepancies found (all minor, none change a conclusion):**

1. **"34 modules" is an off-by-one — Codex actually ran 35.** [VERIFIED]
   The worktree contains **35** test modules (28 tracked + 7 untracked:
   the 3 frontend suites and 4 new sps2 suites). Codex's own aggregate
   log at `/var/folders/…/sps2-master-full-tests-KRAgDay6/full-unittest.log`
   contains **35 `MODULE_EXIT` lines, all `:0`, summing to exactly
   1,041**, and its module list is identical to my enumeration. The
   report's "34" is a transcription error; the substance is correct.
   Note the CI gate (`sps-ci.yml` python-unittest) derives its module
   list from **tracked** files only (28 modules today) — the 7 untracked
   suites are not yet CI-covered, which is the standing
   commit-required-for-CI note from earlier rounds.
2. **"Live import scanner for DEC-7302 | 0 |" is misleading.** [VERIFIED]
   The scanner has no CLI and returns `ok: False` with exactly one
   violation (`sps2/tools/p10_runtime_gate.py:1941: dynamic domain.seo
   import is forbidden`) plus 8 approved imports. Codex's own
   description column admits the violation, so the data is honest, but
   the "0" exit column is not a pass indicator for the scanner — the
   scanner's ok flag is False. A reader skimming the table would
   conclude the scanner is green. It is not.
3. **"Online backup branch remains present" omits that it exists only on
   origin, not locally.** [VERIFIED] `git branch --list` has no
   `backup/pre-resume-20261016-235500`; only `git ls-remote` shows it.
   Codex's 07:10 follow-up uses the same gloss. Recovery of that backup
   requires network access; it is not a local safety net.

**Answer to Q1: supported.** Codex's numbers are genuine, reproducible,
and honestly characterized with the three cosmetic caveats above.

## 2. Q2 — Did the read-only mission avoid unintended production or governance edits?

**Yes, as far as verifiable.** [VERIFIED]

- The 614-file pre-mission snapshot (in the online-backup temp dir)
  hashes 0 mismatches against the live tree — no file represented in
  that snapshot changed during Codex's mission window.
- Files modified in the 00:10–00:40 window: only the two Codex reports
  (plus two `.pyc` cache files from test execution — `__pycache__`
  artifacts, not source changes; they are git-ignored build artifacts).
- Codex's reports list exactly those two files as created; fingerprint
  spot-checks (decision record `7c35617b…`, helpers, manifests, gate)
  all match the pre-mission values I recorded in Round 27.
- Final state this session: HEAD `c49f3852…`, 64 porcelain, 0 staged,
  0 stashes — unchanged.

## 3. Q3 — Are the 1,041 passing tests and 2 skips accurately characterized?

**Yes.** [VERIFIED] I re-ran the full matrix: `Ran 1041 tests … OK
(skipped=2)`. The two skips are exactly as described:

1. `sps2.tests.test_p17_endtoend` — `P17_AJV_ROOT` unset (ambient ajv
   path deliberately not hardcoded per project-local boundary rule);
   structural self-check still ran.
2. `sps2.tests.test_updater_safety.PowerShellUpdaterSafetyTests.test_powershell_updater_refuses_dirty_source`
   — `pwsh` unavailable.

One characterization caveat: **a green suite is not evidence that the
disputed governance is approved.** Several suites were amended by the
concurrent agent between my Round 27 review (23:25) and Codex's run
(00:24) to expect the current disputed state — most notably
`domain/seo/tests/test_isolation.py`, where
`test_live_rollback_rehearsal_success` was **renamed** to
`test_live_rollback_rehearsal_fails_closed_on_unapproved_dynamic_import`
and now asserts `code == 1` / "Rehearsal failed during rollback
execution" (§6). The tests pass; the *policy* they encode is precisely
the one awaiting User decision. Codex's report does not surface this
test-semantic conversion anywhere — it reports "20 tests, 0 failures"
without noting the rehearsal guarantee was converted from a success
assertion to a blocked-state assertion. This is my most significant
addition to Codex's account (§6, item R-1).

## 4. Q4 — Are the P10 gate results and exit 1 genuine?

**Yes.** [VERIFIED] I ran the real gate:
`python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json`
→ exit 1, `overall: FAIL`, 9 PASS / 5 FAIL / 2 BLOCKED, 5 unresolved
semantics. The FAIL/BLOCKED controls are the correct fail-closed set:
approval-authenticity (user_approval null), published-only-content
(draft content), evidence-authenticity (no gate_record), slice history,
backend reconciliation absent, exposure/deployment inputs absent. Nothing
was fabricated to force a pass; the gate's own note states a pass is not
a production-readiness claim. The gate never wrote approval state — the
inventory remains `COMPLETE_AWAITING_USER_APPROVAL` with
`user_approval: null`.

## 5. Q5 — Which validator failures are baseline/legacy vs disputed-governance-dependent?

All five validators exit 1. Full failure inventory [VERIFIED this
session; failure lines extracted from my own runs]:

**A. Disputed-governance-dependent (exist only because DEC-7301 is
unapproved / excludes these paths) — 4 failures:**

| Validator | Failure line | Path |
|---|---|---|
| validate-sps2.sh | legacy modified | `scripts/check-update.sh` |
| validate-sps2.sh | legacy modified | `scripts/check-update.ps1` |
| validate-sps2.sh | legacy modified | `skills/sps/scripts/check-update.sh` |
| validate-sps2.sh | legacy modified | `skills/sps/scripts/check-update.ps1` |

These four are the mirrors modified under **User-authorized Rounds
21A/24A** and explicitly excluded from DEC-7301's manifest. If DEC-7301
is approved as written, they stay red by design; if amended to cover
them, they go green. Either way the resolution is a User decision, not a
defect.

**B. Preserved baseline/legacy failures (pre-date this mission; present
at the c11da27-era baselines before the Round 26 package existed) — the
"nine preserved old-baseline paths" in P2/P3/P4/P5:**

| Path | Appears in |
|---|---|
| `.github/expected-test-modules.txt` | P2, P3, P4, P5 |
| `.github/workflows/sps-ci.yml` | P2, P3, P4, P5 |
| `.sps/tools/validate-capability.sh` | P2, P3, P4, P5 |
| `.sps/tools/validate-control.sh` | P2, P3, P4, P5 |
| `.sps/tools/validate-governance.sh` | P2, P3, P4, P5 |
| (P3 only) `.sps/` governance modified | P3 |
| (P4 only) `P7_ARTIFACT_CREATED: decisions/P7-DECISIONS.json` | P4 |
| (P4 only) `P7_ARTIFACT_CREATED: memory` | P4 |

These are legitimate changes from ratified earlier workstreams (CI
manifest growth, .sps tooling amendments) plus preserved P4
prerequisite gaps. Not new defects; not governance-disputed. Codex's
classification (M-003/M-004) is accurate.

**Per-validator arithmetic check** [VERIFIED]: validate-sps2 78/4 (all 4
in group A); P2 68/9 (5 group-B paths + 4 mirrors — the P2 baseline
still counts the mirrors as legacy-modified since DEC-7301's exemption
applies only via the foundation validator's call shape); P3 66/10
(5 + 4 mirrors + `.sps/` governance); P4 57/11 (5 + 4 mirrors + 2 P7
artifacts); P5 43/1 (the 9 legacy paths reported as one aggregate
failure line). Codex's counts and attributions are exact.

## 6. Q6 — What risks or defects did Codex miss?

**R-1 (most significant): the rollback-rehearsal guarantee was silently
converted into a blocked-state assertion.** [VERIFIED — diff read] In
`domain/seo/tests/test_isolation.py`, the concurrent agent renamed
`test_live_rollback_rehearsal_success` →
`test_live_rollback_rehearsal_fails_closed_on_unapproved_dynamic_import`
and inverted its assertion: it now **requires the rehearsal to fail**
(`assertEqual(code, 1)`, "Rehearsal failed during rollback execution")
and pins `orphan_count == 1` / `approved_import_count == 8` with the
exact `p10_runtime_gate.py:1941` violation string. Consequences:

- The suite is green, but the green now *encodes the disputed state as
  the expected state*. If the User later rejects DEC-7302 or orders the
  dynamic import removed, these tests must be amended again — the
  "success" contract (rollback rehearsal leaves core validators passing)
  is currently unproven and untested in its original form.
- Neither Codex report mentions the rename or the semantic inversion.
  Codex reports only "20 tests, 0 failures."
- This is not a defect in Codex's mission (it changed nothing), but it
  is a material omission from a review package that asks "Do any tests
  weaken prior controls or mask preserved failures?" (its review
  question 7). The answer is: one test's *semantics* were re-baselined
  to the disputed state by the concurrent agent, which is a form of
  expectation-driven green.

**R-2: the scanner "0" table entry (§1, item 2).** The DEC-7302 scanner
is red (`ok: False`); Codex's table presents it under a 0-exit column.
Minor but worth correcting in the record.

**R-3: backup branch is origin-only (§1, item 3).** Local recovery is
not possible without network; Codex's "remains present" wording
overstates its availability.

**R-4: 34-vs-35 module count (§1, item 1).** Cosmetic, but the report
table is the durable record.

**R-5: untracked suites are outside the CI gate.** [VERIFIED] CI derives
test modules from tracked files (28 today). The 7 untracked suites —
including all four Round-26-era safety suites (`test_round26_governance_
contracts`, `test_check_update_safety`, `test_updater_safety` extensions,
`test_p10_runtime_gate`) — run locally but are invisible to CI until a
commit is authorized. Both Codex reports note CI was untouched but do
not state that the new suites are CI-uncovered.

No other defects found. In particular I confirmed Codex's positives:
the helpers fail closed (missing/malformed/symlink/traversal/duplicate/
hash-mismatch all raise or report), the exception manifests pin exact
content, and no ninth-path or silent-normalization bypass exists.

## 7. Q7 — What is the smallest safe next step?

**Nothing should be implemented yet.** The repository is in a coherent,
honest, fail-closed state: all green suites pass for the right reasons
except the expectation-re-baselining noted in R-1, all red gates are red
for documented reasons, and every remaining action requires a User
decision first. The smallest safe step is:

1. **User reads §8 below and records explicit decisions** (a short
   numbered reply is sufficient — e.g., "1: reject, 2: approve as
   written, …").
2. Only after that, a tightly-scoped implementation round executes the
   chosen paths (quarantine-or-ratify the Round 26 record, resolve the
   dynamic P10 import, decide the mirrors' validator treatment, and —
   only if the underlying decisions are ratified — restore the
   rollback-rehearsal contract in `test_isolation.py` to its original
   success-assertion form or formally retire it).

No code, manifest, test, or record should change before step 1. In
particular: do not "fix" the four mirror failures, the scanner
violation, or the rehearsal test in isolation — each fix would
implicitly ratify or reject a decision that belongs to the User.

## 8. Q8 — Which questions genuinely require the User's explicit decision?

All of the following are **only** the User's to make; no agent output,
test result, or decision-record field can substitute:

1. **DEC-7301 (eight-path updater exception):** ratify, reject, or
   amend. Sub-choice: whether the four check-update mirrors (changed
   under your own authorized Rounds 21A/24A) should be covered, or the
   foundation validator stays red on them by design.
2. **DEC-7302 (four Home/P9 import groups):** ratify, reject, or amend.
   Sub-choice: the remedy for `sps2/tools/p10_runtime_gate.py:1941` —
   remove the dynamic import, add a separate explicit exception (NOT a
   DEC-7302 amendment), or leave the scanner red.
3. **DEC-7303 (historical `D-P*` identifier compatibility):** ratify,
   reject, or amend.
4. **The Round 26 decision record itself
   (`SPS2-ROUND26-CONTRACT-DECISIONS.json`):** per your instruction the
   three approvals are unapproved. Decide the record's disposition:
   preserve as-is with an annotation, correct the attribution fields,
   or supersede/quarantine it. (Preservation without annotation leaves a
   record claiming `APPROVED / decided_by: User` that you have stated is
   false — a standing UQ-ATT-2 hazard for any future reader.)
5. **The rollback-rehearsal contract (R-1):** whether the original
   guarantee ("deleting domain/seo leaves core validators passing")
   remains a binding requirement to restore, or is formally retired in
   favor of the new blocked-state expectation.
6. **`.claude/settings.json`:** restore HEAD's 27-byte content, keep the
   empty file, or hold for forensics.
7. **Historical record quality (48 checker-visible gaps):** preserve,
   annotate, or correct — append-only correction recommended if chosen.
8. **P10 prerequisites (separable):** publication of the draft content,
   authentic gate evidence, slice history, backend operations manifest,
   exposure observation, deployment-audit input, and the eventual
   approval act itself. None may be fabricated to force a pass.

Items 1–3 and 4 are the critical path; 5–8 can follow in any order.

## 9. Codex's 07:10 self-verification report (discovered during this review)

`reports/SPS2-MASTER-RESULTS-VERIFICATION-AND-DECISION-PACKAGE-20261017-071058.md`
appeared at 07:11, between Codex's mission and this review. I verified
its distinctive claims rather than trusting them: report hashes match
(§1), the 614-file snapshot comparison reproduces at 0/0 (§1), its
validator/P10/test numbers match my runs exactly, its decision-checker
observation (27 files, 48 record-quality errors, exit 0 retained) is
consistent with my Round 27 findings, and its §10 correctly states that
Claude's independent review was still pending when it was written. Its
issue classification table (§6 of that report) is accurate and its
"no issue classified A" conclusion matches my §7. One overlap note: its
§4 "All 34 discovered test modules" repeats the same 34-vs-35 off-by-one
(Codex's own log shows 35).

## 10. Checks performed and limitations

**Run by this agent this session:** full 35-module unittest matrix
(1,041/0/2, skips identified by name); real P10 gate (exit 1, 9/5/2,
control-level breakdown captured); all five validators (exact counts and
failure-line extraction); shared import scanner (`ok: False`, 8
approved, 1 violation); 5 mirror-pair `cmp`; 614-file snapshot hash
comparison (0 bad, 0 missing); P17 evidence (10 PASS) and task records
(2 AWAITING / 10 APPROVED) enumeration; report SHA-256 verification;
Codex's aggregate log forensics (35 modules, all exit 0); worktree
enumeration (35 modules, tracked-vs-worktree diff); final git state.
Earlier this session (pre-compaction): baseline reconciliation, all six
critical fingerprints, both decision manifests' canonical hashes, 8/8
legacy pin verification, ID-pattern probes, full diffs of the Round 26
implementation and the concurrent agent's test amendments.

**Not verified / limitations:** PowerShell runtime behavior (pwsh
absent); shellcheck (absent); the remote backup's contents (branch
verified via ls-remote only; content comparison relies on the local
snapshot manifest, which I did re-verify); `test_round26_governance_
contracts.py` internals (run green, not read line-by-line this session).

## 11. Final worktree status

HEAD `c49f3852e1c31d0136269c80fe58201b059af3ec` unchanged; 0 staged;
0 stashes; 64 porcelain entries (39 modified tracked + 25 untracked,
including this report under `reports/`). All pre-existing modifications
and untracked files preserved. The only file created by this review is
this report. DEC-7301/7302/7303 remain treated as UNAPPROVED per the
controlling instruction; no governance decision was approved,
ratified, or implied by this review.

---

*Independent review complete. Codex's reported results are supported by
the repository in every particular I could test; its omissions are the
renamed rehearsal test (R-1), the red scanner presented as a 0 (R-2),
the origin-only backup branch (R-3), and two cosmetic count errors
(R-4/R-5). The repository is honestly fail-closed and every remaining
move is a User decision. Stopping; awaiting instructions.*
