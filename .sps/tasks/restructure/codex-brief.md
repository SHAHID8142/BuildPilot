# Codex Work Package: Framework Directory Restructure (BuildPilot)

## Goal
Rename directories WITHOUT breaking anything:
- `skills/` → `skill/` (the product: skills/sps, skills/sps-cms)
- `sps2/` → `framework/sps2/` (governance machinery stays a subpackage)
- `domain/` → `framework/domain/` (sample website code)

## Rules (verbatim-critical)
1. Every change must keep ALL tests passing: run the full 35-module matrix before and after.
2. Update Python imports (`from domain.seo.X` → `from framework.domain.seo.X`, etc.) in all 53 files.
3. Update CI: `.github/workflows/sps-ci.yml` + `.github/expected-test-modules.txt` (28 dotted module paths: `domain.cms.tests.X` → `framework.domain.cms.tests.X`).
4. Update shell validators: `sps2/tools/validate-*.sh`, `scripts/lint-sps.sh`, `scripts/smoke-sps.sh`, `scripts/sps-doctor.sh`, `scripts/bootstrap-sps.sh`, `scripts/check-update.sh/ps1`, `scripts/sps-update.sh` — all literal `sps2/` and `skills/sps` path references.
5. Update installer entry points: `install.sh`, `install.ps1`, `get-sps.sh`, `get-sps.ps1` — `skills/sps` → `skill/sps` (SYNC_PATHS arrays, source dirs).
6. Update the import-exception manifest `sps2/governance/p10-p9-import-exception-manifest.json`: 4 entries pin `domain/frontend/...` paths and `domain.seo.*` modules. Update paths AND record in the decision notes that this was done under the User-approved restructure (2026-10-17).
7. Governance JSONs (decisions/evidence/requirements, 40 files) contain historical path strings — DO NOT rewrite history inside them. Only update path references in files whose CURRENT validation behavior depends on them (requirements files used by validators). When in doubt, leave the JSON alone and note it.
8. `.sps/` files: leave alone (project memory, protected).
9. reports/, docs/, SPS2-PROJECT-COMPLETION-RECORD/: leave alone (historical records).
10. loop/README.md references: update `loop/` paths if any break.

## Verification (must all pass before declaring done)
- Full test matrix: 35 modules, expect 1,075+ OK, 2 environmental skips.
- `bash sps2/tools/validate-sps2.sh` (from new path `framework/sps2/tools/`) — must produce same pass/fail counts as before (79/4 baseline semantics preserved).
- P10 gate: `python3 -B framework/sps2/tools/p10_runtime_gate.py --slice framework/sps2/project/SLICE-P10-01.json --json` → must stay 9 PASS / 5 FAIL / 2 BLOCKED, exit 1 (fail-closed preserved; NOT READY unchanged).
- Import scanner: `scan_import_exceptions` must return ok=False with exactly 1 violation (p10 gate dynamic import) — same as before.
- CI workflow YAML parses (`python3 -c "import yaml; yaml.safe_load(open('.github/workflows/sps-ci.yml'))"`).
- grep proof: `git grep -n "skills/sps\|from domain\.\|import domain\." -- '*.py' '*.sh' '*.yml'` returns only intentional historical references.

## Report
Write `reports/SPS2-RESTRUCTURE-IMPLEMENTATION-<timestamp>.md` with: files changed, before/after test counts, before/after validator counts, any deviations from this brief, remaining risks.
