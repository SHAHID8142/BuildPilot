# SPS2 Completion C8 — Governance Audit

**Date:** 2026-10-17 (Asia/Dhaka)  
**Agent:** Codex governance-audit subagent; compiled by Codex  
**Mode:** Read-only  
**Status:** `NEEDS_REVIEW` — Claude cross-review pending; no policy disposition made.

## Preservation baseline

- Branch: `build/roadmap-p3-completion`
- HEAD: `c49f3852e1c31d0136269c80fe58201b059af3ec`
- Worktree: 40 modified tracked paths, 26 untracked porcelain entries, 0 staged, 0 stashes.
- The audit reports no file edits. Protected hashes checked against the C0–C3 report still match.

## Findings

1. **Manifest integrity does not establish approval.** The DEC-7301 and DEC-7302 manifest hashes match their helper constants, and the legacy pin check reports no integrity violations. However, `sps2/governance/legacy_exceptions.py:228-247` grants exemptions when those pins pass, and `import_exceptions.py:174-184` loads its manifest as an allowlist without checking the disputed decisions or correction sidecar. The sidecar at `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS-CORRECTION-20261017.md:48-56,66-70,91-108` says DEC-7301/2/3 are unapproved and dependent tooling must fail closed. If that sidecar reflects the authoritative User instruction, the helpers have a fail-open mismatch. Hash equality proves file integrity only, not User authorization. **Disposition requires User confirmation of the authority source; no manifest/helper change is authorized by this audit.**

2. **Approval-date validation is inconsistent.** `attribution.py:144-162` requires a date, but the general checkers (`check_sps2.py:117-128`, `check_p3.py:237-240`, `check_p2.py:58-64`) accept an `APPROVED` record with `decided_by: "User"` and no date. The decision schema at `decision.schema.json:61-84` requires only `approval.state`; the other fields are optional. A probe of that fixture produced no checker errors while the shared predicate rejected it. A future common contract must also preserve supported legacy fields such as `approved_by` / `approved_on` used by P4 records. **User direction is needed on the required date and accepted legacy forms before changing the contract.**

3. **Identifier compatibility is uneven.** The shared decision schema and `check_sps2.py` / `check_p3.py` accept the shared DEC/D-P pattern, while `check_p2.py:221-226` remains DEC-only. Current P2 records use DEC IDs, so this does not explain the current P2 failures. DEC-7303 is disputed and says new IDs must use DEC IDs; adopting that proposal would require separating historical D-P compatibility from new-ID policy. **Do not extend or ratify the proposal without User disposition.**

4. **The live dynamic-import scan still has a violation.** The current scan reports eight allowlisted imports and a dynamic `domain.seo` import at `sps2/tools/p10_runtime_gate.py:1944`. The test at `sps2/tests/test_round26_governance_contracts.py:284-307` checks the approved-import count but not that the violation list is empty, so its pass does not prove a clean scan. Add an explicit scanner-success assertion only after the P10 import remedy and exception policy are decided; those decisions remain User-gated under disputed DEC-7302.

5. **Validator failures require classification, not suppression.** Current reported validator results are foundation 79/4, P2 68/9, P3 66/10, P4 57/11, and P5 44/1 (passed/failed). Foundation’s four failures are the updater/checker paths excluded by DEC-7301. P2/P3/P4/P5 include legacy-path deltas; P3 also sees `.sps/` governance changes. P4 reports `P7_ARTIFACT_CREATED` for `decisions/P7-DECISIONS.json` and `memory`, although both are tracked at HEAD. That conflicts with the C0–C3 report’s description of P7 artifacts as absent; correct the report description at the next authorized report update. Do not change baselines or expected artifacts to clear these failures.

6. **Some prior findings are stale.** The targeted governance and attribution suites currently report 106 tests passed, 0 failed; the previously reported attribution-fixture failure was not reproduced. `ResourceWarning`s appeared in the focused run. The live scanner violation remains. The validator counts above supersede older Round 27 counts.

## Command evidence from the read-only addendum

The focused suite was run as:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest \
  sps2.tests.test_round26_governance_contracts \
  sps2.tests.test_attribution_policy
```

Exit 0: 106 tests, 0 failures; `ResourceWarning`s for temporary directories were emitted.

The five validator command forms were:

```sh
set -o pipefail; bash sps2/tools/validate-sps2.sh 2>&1 | rg 'FAIL|INVALID|passed|failed|legacy protection'
set -o pipefail; bash sps2/tools/validate-p2.sh 2>&1 | rg 'FAIL|INVALID|passed|failed|legacy'
set -o pipefail; bash sps2/tools/validate-p3.sh 2>&1 | rg 'FAIL|INVALID|passed|failed|legacy'
set -o pipefail; bash sps2/tools/validate-p4.sh 2>&1 | rg 'FAIL|INVALID|passed|failed|legacy|DUPLICATE'
set -o pipefail; python3 -B sps2/tools/validate-p5.py 2>&1 | rg 'FAIL|INVALID|passed|failed|legacy'
```

Each exited 1 with the counts recorded in Finding 5. Identifier check: `python3 -B sps2/tools/check_p2.py decision sps2/decisions/P2-DECISIONS.json` exited 0. The undated-approval case used a temporary synthetic record and subprocess calls to `check_sps2.py`, `check_p3.py`, `check_p2.py`, plus the shared predicate; each checker exited 0 with empty stdout while the predicate returned false. The import scanner probe returned `ok=False`, eight approved imports, and the violation at `p10_runtime_gate.py:1944`. No temporary repository files were retained.

## Recommended bounded follow-up

- Claude should cross-check this report against the live files and append a verdict/evidence to `reports/SPS2-COMPLETION-COORDINATION.md`.
- Keep DEC-7301/2/3, correction-sidecar authority, baseline scope, P7 artifact history, and P10 import disposition in `BLOCKED_USER` until the User decides them.
- Propose a separate code-owned fix for checker date consistency only after the common approval contract and legacy date fields are specified.
- Treat the P10 scanner-success assertion as a verification follow-up; do not make it pass by editing a manifest or weakening the gate.
- No source, schema, CI, baseline, manifest, decision record, P10 file, or approval record was changed.

## Readiness boundary

This audit is not a release approval. The latest recorded P10 gate remains 9 PASS / 5 FAIL / 2 BLOCKED, exit 1; release readiness remains **NOT READY**.
