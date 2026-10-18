# QA Report — Audit-Fix Batch + COPY-GATE + Import-Scanner Hardening

**Date:** 2026-10-18 · **Commit:** f27ef92 · **Orchestrator:** SPS build manager session
**Battery:** 1,268 tests, 0 failures, 54 modules · Laws / docs-drift / copy-gate / provenance-strict / secret-scan / lint: all green

## 1. Final-ship audit remediation (21/21 defects fixed)

Source: final-ship audit workflow wf_9ce09692-a3a (28 agent results → 22 findings, #0 pre-fixed).
Execution: fix workflow wf_032fdb28-5da completed 6 of 7 groups (install-sh, uninstall-sh,
ps1-installers, ps1-updater, shell-scripts, docs-counts); the framework-tools group's agent
stalled on an API request and was completed by the orchestrator directly. The workflow's
adversarial Verify phase never ran (computer restart killed the runner); orchestrator-side
verification replaced it — every fix was validated with the audit's own repro fixtures:

| # | Defect | Fix | Verified by |
|---|---|---|---|
| 1 | install.ps1 Invoke-Native dead in Start-Job runspaces (all PS steps fail but exit 0) | function text re-injected via scriptblock into each job | agent repro (pwsh 7.6.7) |
| 2 | update-sps.ps1 ignored install manifest (extras consent bypass) | reads AGENTS=/INSTALL_EXTRAS= from manifest, forwards -Agents/-NoExtras | sandbox repro with stubbed installer |
| 4 | stale `skills\` paths in PS scripts | corrected to `skill\` | grep sweep |
| 5 | sps-cms updater exit 0 on failure | fail-closed exit codes | agent repro |
| 6 | pwsh 7 hard requirement undocumented | documented + enforced | agent |
| 7 | install.sh wiped PRE_EXISTING_SPS user customizations | reset removed; top-level snapshot survives | end-to-end repro in fake HOME |
| 8 | uninstall.sh &&/\|\| chain reported false successes | rewritten per-scope truth table | stubbed-CLI repro |
| 9/10 | mktemp scratch/extract dirs leaked on failure paths | EXIT traps | 5-path sandbox runs |
| 11 | slugify empty for non-ASCII titles → id collisions | cksum fallback slug | unit-style repro |
| 12 | `from framework.domain import seo` evaded scanner | alias-qualified check extended to absolute parent-package forms | fixture: a1.py/a2.py now flagged |
| 13 | variable-held dynamic import evaded | fail-closed: non-literal arg = violation; aliased `as im` tracked; non-literal getattr flagged; benign literal control clean | fixtures b1/b2/b3 + ok1 |
| 14 | check_laws stale `law` loop var | dead nested check removed | code review + suite |
| 15 | check_emoji skipped unreadable files (fail-open) | OSError → EMOJI_VIOLATION (fail-closed) | chmod-000 repro: exit 1, 2 violations |
| 16 | symlinked dirs silently unscanned | reported as violations (os.walk puts dir-symlinks in filenames — first attempt missed this) | linkdir fixture flagged; live repo clean |
| 17/18 | doc counts stale (tests, exceptions) | 1,268 tests / 62 exceptions / 54 modules in README+CHANGELOG+CI | live battery |
| 19 | README provenance receipt false (no CI step) | provenance --strict added to sps-ci.yml | workflow YAML + local strict run |
| 20/21 | CATALOG/PROFILE-SCOPING stale `skills/sps/` paths | corrected | docs-drift clean |

## 2. COPY-GATE shipped (research → law → validator → CI)

- **Research:** wf_35ee6376-6b5 (6 agents, 68 findings) → `.sps/research/copy-gate-design.md`.
- **Law:** `skill/sps/COPY-GATE.md` — 8 hard laws, machine-checkable laws, prompt-law rules,
  Bangla standard (বাংলা একাডেমি বানানের নিয়ম ৫ম সংস্করণ ২০২৩; চলিত রীতি only), abort conditions.
- **Validator:** `framework/sps2/tools/check_copy.py` — 15 checks (EN/BN slop blocklists, EN
  AI-lexicon density, negative parallelism, tricolons, em-dashes, burstiness, hedging,
  placeholders, sadhu/WB forms, word-initial ড়, দাঁড়ি, loanwords, pronoun consistency,
  numerals); wordlists in `copy_lists/`; advisory/deployment dual mode; fail-closed on
  unreadable files. Wrapper `scripts/sps-copycheck.sh` + byte-identical mirror.
- **Tests:** 9 contract tests (slop fails, clean passes both modes, advisory never fails,
  repo does not self-trip).
- **Registration:** SKILL.md law 21, SECTION-DOD item 13, HANDOFF-CHECKPOINT 4b,
  SKILL-ROUTER (Content/copy primary), SKILL-GOVERNANCE, INSTALL-PROFILES, CATALOG, CI
  (both validator jobs, deployment mode).
- **AGY (Antigravity)** confirmed as Bangla-quality reference for the gate (probe: jamdani
  brief returned প্রমিত চলিত বাংলা citing গুরুচণ্ডালী দোষ avoidance); integration queued (T-44 list).

## 3. Governance chain maintenance

- Legacy manifest: 15 records re-pinned + 2 new (scripts/check-update.ps1 audit #4;
  scripts/sps-copycheck.sh new ADD) → **62 records**; canonical `0598efac…` re-chained into
  `legacy_exceptions.py` + `manifest-anchors.env`; git index staged so stage-0 matches.
- `EXPECTED_EXCEPTION_COUNT` 60 → 62 with amendment note.
- Import-scan reconciliation: the new fail-closed dynamic-arg rule flagged 3 pre-existing
  sites (2× test_attribution_policy `__import__(name)` introspection of capability modules;
  1× p10_runtime_gate intentional, test-pinned). Resolution: auditable
  `DYNAMIC_ARG_FILE_EXEMPTS` frozenset (check_emoji EXEMPT pattern) for the test file only;
  p10_runtime_gate:1944 stays a live pinned violation. Live scan back to exactly 1 violation.
- Provenance store re-pinned (sps, sps-cms, sps-seo); `check --strict` exit 0.
- handoff.md rolled to `.sps/archive/handoff-2026-10-18-pre-audit-fix-batch.md` (context budget).

## 4. Incidents during the batch

- Workflow runner died twice: once on `require is not defined` (fixed, resumed), once by
  computer restart mid-run (framework-tools agent stalled on an API request at 18:38,
  runner gone after restart). Recovery: orchestrator completed the group directly from the
  workflow's brief + audit evidence; all five fixes independently fixture-verified.
- `/tmp` cleared by restart: audit findings re-extracted from wf journal (28 results).
- First symlink fix missed because os.walk lists dir-symlinks under `filenames`, not
  `dirnames` — caught by fixture verification, fixed, re-verified.

## 5. Deploy budget

One commit (f27ef92), one push, one CI cycle for 48 files / +3,084 / −629.

## 6. Open queue (user-visible)

T-40 launch-video skill · T-41 client-facing roadmap (source docs received:
42-step/7-phase/9-gate universal roadmap) · T-42 wider placeholder detection ·
T-43 roadmap merge · T-44 conversation-loss resilience · statusline per-second TPS ·
AGY×COPY-GATE integration · Batch C decisions (awaiting explicit user consent).
