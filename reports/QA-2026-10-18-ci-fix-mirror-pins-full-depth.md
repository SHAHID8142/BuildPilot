# QA Report — CI-fix batch: mirror pins + fact-check --full-depth (2026-10-18)

## Trigger
Push 0f17eb4 (audit-fix batch + QA report) failed CI:
- **sps-ci** (run 39139195116): `P2 RESEARCH INVALID: 68 passed, 3 failed` —
  `legacy modified:` skill/sps-cms/scripts/install.ps1, skill/sps/scripts/check-update.ps1,
  skill/sps/scripts/sps-copycheck.sh. Root cause: the audit-fix batch pinned the
  scripts/ copies of these files but not their byte-identical skill/ mirrors.
- **windows-smoke** (run 39139195166): installer died at step 25/29 `fact-check` —
  upstream repo jwynia/agent-skills reorganized; `fact-check` now lives 5 directory
  levels deep (skills/general/research/verification/fact-check) and the
  `npx skills add` scanner's default depth only sees 4 levels → "No matching
  skills found". Reproduced locally; verified `--full-depth` installs it (118
  skills found, 1 installed).

## Fix (one commit: 381f282)
1. Legacy manifest 62 → 65 records: +3 skill/ mirror pins (blobs/sha256/mode
   recorded, DEC-7305 authorization).
2. CHANGELOG.md is itself a pinned exception — its 62→65 edit required its own
   re-pin (caught by test_round26_governance_contracts, fixed in-cycle).
3. install.sh + install.ps1: fact-check step gains `--full-depth` (both are
   pinned exceptions → re-pinned).
4. Canonical hash chain advanced twice more this session:
   0598efac… → 1f85cd4d… → 17b5c073… → **bc770093…** (chained into
   legacy_exceptions.py EXPECTED_MANIFEST_SHA256 + manifest-anchors.env;
   EXPECTED_EXCEPTION_COUNT = 65 with amendment trail in comments).

## Verification
- Full battery: **1268 tests OK** (2 skipped, expected).
- All 13 CI validator steps PASS locally: p2/p3/p4/p5/p6/p7/bootstrap/sps2
  validators, check_laws, check_copy, check_generated_tests, check_docs_drift,
  provenance --strict, lint-sps.
- Governance suites: test_manifest_anchor + test_round26_governance_contracts +
  test_law_checker = 56 tests OK.
- Mirror integrity: diff scripts/ vs skill/sps/scripts/ clean.
- PowerShell syntax check: PASS (pwsh local).

## Deploy budget
Batched into ONE commit + ONE push (381f282) after full local validation.

## Lesson (proposed for LESSONS.md)
When pinning a file that has a byte-identical mirror (scripts/ ↔ skill/*/scripts/),
pin BOTH in the same cycle — the mirror relationship is easy to miss because the
diff sweep pathspec (`*.sh`/`*.ps1` globs) covers both, but only the manifest
records make them legal.
