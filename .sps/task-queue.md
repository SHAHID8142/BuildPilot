# Task Queue

## doing


## queued (oldest first)
- [x] id: T-21 task: Write proper README.md for the repo — finished: 2026-10-18 (already delivered in PR #4: README refreshed to live facts + USER-GUIDE.md linked; no further work)
- [x] id: T-20 task: Lessons→validators automation — finished: 2026-10-18 (sps-lawlog.sh ledger, gen_law_test.py with --approved-by human gate + injection hardening, check_generated_tests.py GENERATED_TEST_UNREVIEWED; PR #6 merged 5a0920b; injection vuln caught by second-opinion verifier and re-exploit-verified blocked)

## queued (oldest first)
- (empty — all received tasks finished; law-checker + design-craft batches pushed af84a39/407b515, CI watching)

- [x] id: T-23 task: Directory-hygiene law + automatic check — finished: 2026-10-18 (DIRECTORY-HYGIENE.md placement law, sps-hygiene.sh check/fix with quarantine; PR #6 merged 5a0920b)
## done
- [x] id: T-19 task: Nightly skill-ecosystem scan — finished: 2026-10-18 (scripts/ecosystem-scan.sh + tsv + mirrors, .github/workflows/ecosystem-scan.yml, v4.3.0, manifest 33 exceptions; PR #5 merged CI-green 137716a; second-opinion caught report .md-extension bug)
- [x] id: T-12 task: Dynamic skill-selection redesign + CMS/SEO hardening (folded: T-13, T-14, T-15, T-17) — finished: 2026-10-17 sessions 4-5 (SKILL-ROUTER dynamic selection, sps-update.sh, COMPANY-LIFECYCLE.md, TOOL-CONSENT.md, install.sh backup/upgrade; commits 122c9e7…509e32b)
- [x] id: T-18 task: .sps memory-budget law + token-reduction rules/MCP guidance — finished: 2026-10-17 (CONTEXT-BUDGET.md, doctor enforcement, SKILL-ROUTER token-controls, commit 8ef6025)
- [x] id: T-16 task: Second-opinion verification of the batch + timestamped session report — finished: 2026-10-17 (workflow wf_db59c97b-2d1: 12 confirmed findings, all fixed in-batch)
- [x] id: T-13 task: CMS skill robustness hardening (received mid-T-12; part of T-12 scope per user message) — finished: 2026-10-17 (H1-H6 in skill/sps-cms/SKILL.md)
- [x] id: T-11 task: Second-opinion verifier fixes (fail-closed manifest guard, stale test contracts, evidence honesty, mirror sync) — finished: 2026-10-17, commit 85cd8b3 + pending
- [x] id: T-10 task: P10 completion + Packages 2/3 + sps-seo + learning system — finished: 2026-10-17

---

## T-22 (queued): Fix pre-existing p4/p6 validator false-positives
- p4 `P7_ARTIFACT_CREATED` fires on `decisions/P7-DECISIONS.json` + `memory/`,
  which exist legitimately under ratified D-P7-IMPLEMENTATION — the forbidden
  list predates P7 authorisation. Validator should admit artifacts covered by a
  recorded authorisation decision (and still forbid anything outside it).
- p4/p6 `GLOBAL_PATH_REFERENCED` fires on a docstring in
  `framework/sps2/tests/test_check_update_safety.py:21` that *states tests do
  not touch* `~/.sps`. Grep should skip comment/docstring lines.
- Both failures pre-exist on origin/main (reproduced in a clean worktree);
  CI is unaffected (runs check_laws + unittest only).
- Requires re-pinning validate-p4.sh / validate-p6.py in the manifest.

---

---

## T-24 (queued): Client .sps/ backup + unpushed-main warning
- Auto-snapshot .sps/ at every gate (G1, G2, section approvals, handoff) into
  a rolling backup (last N kept) inside the project.
- sps-doctor warns loudly when local main has unpushed commits older than 1 day.
- User-approved 2026-10-18 (roadmap hardening discussion).

## T-25 (queued): Secrets-leak CI gate
- CI job scans every push for key patterns (sk_live_, AKIA, ghp_, xoxb-, -----BEGIN
  PRIVATE KEY-----, etc.); blocks merge on hit; allowlist for test fixtures.
- User-approved 2026-10-18.

## T-26 (queued): sps-restore one-command rollback
- Pick from ~/.sps/backups/ (last 3 kept) and restore bundled skills; verify
  restored state with doctor. 
- User-approved 2026-10-18.

## T-27 (queued): Real Windows CI smoke job
- GitHub Actions windows-latest job actually RUNS install.sh flow via pwsh
  (get-sps.ps1 + install.ps1) in a sandboxed HOME, not just syntax-check.
- User-approved 2026-10-18.

## T-28 (queued): Kickoff-proof check + user cheat sheet
- Handoff/doctor verifies .sps/ contains recorded kickoff answers before
  Phase 4 starts (proves questions were asked, not just gates trusting it).
- One-page cheat sheet of user commands linked from kickoff first message.
- User-approved 2026-10-18.

---

## T-29 (queued): Skill-provenance gate
- Pin sha256 of every installed third-party skill at install time; sps-doctor
  flags drift on later runs (upstream tamper detection).
- Lower priority until third-party skills are actually installed, but the
  mechanism lands now. User-approved 2026-10-18 (8-item hardening list).

---

## T-30 (queued): Docs-drift checker
- Machine check that every command in USER-GUIDE.md / README.md / SKILL.md
  exists in scripts/ with matching flags (docs can silently rot otherwise).
- Found in hardening gap-scan 2026-10-18.
