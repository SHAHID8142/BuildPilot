# Task Queue

## doing
- (integration pass: register test modules, pin new files, compact queue, full sweep, PR + auto-merge on green)

## queued (oldest first)
- (empty — all received tasks finished)

## done
- [x] id: T-19 task: Nightly skill-ecosystem scan — finished: 2026-10-18 (PR #5 merged CI-green)
- [x] id: T-20 task: Lessons→validators automation — finished: 2026-10-18 (sps-lawlog.sh, gen_law_test.py + human gate + injection hardening; PR #6 merged 5a0920b)
- [x] id: T-21 task: Proper README — finished: 2026-10-18 (PR #4)
- [x] id: T-22 task: Fix pre-existing p4/p6 validator false-positives — finished: 2026-10-18 (P7 authorization gate, tokenize-based p6 scan)
- [x] id: T-23 task: Directory-hygiene law + automatic check — finished: 2026-10-18 (DIRECTORY-HYGIENE.md, sps-hygiene.sh; PR #6)
- [x] id: T-24 task: Client .sps/ backup + unpushed-main warning — finished: 2026-10-18 (sps-backup.sh rolling 10, doctor warn() + unpushed check)
- [x] id: T-25 task: Secrets-leak CI gate (+ECC AgentShield scope) — finished: 2026-10-18 (secret-scan.sh, .secrets-allowlist, CI workflow)
- [x] id: T-26 task: sps-restore one-command rollback — finished: 2026-10-18 (preview-before-apply, pre-restore safety copy)
- [x] id: T-27 task: Real Windows CI smoke job — finished: 2026-10-18 (windows-latest pwsh install + structural gate)
- [x] id: T-28 task: Kickoff-proof check + cheat sheet — finished: 2026-10-18 (check_kickoff.py 11 tests, CHEAT-SHEET.md)
- [x] id: T-29 task: Skill-provenance gate — finished: 2026-10-18 (sps-provenance.sh pin/check, 12 skills pinned, doctor wiring)
- [x] id: T-30 task: Docs-drift checker — finished: 2026-10-18 (check_docs_drift.py, 5 docs scanned clean)
- [x] id: T-31 task: Product-verification gate — finished: 2026-10-18 (SECTION-DOD 51, check_product_proof.py 8 tests)
- [x] id: T-32 task: Hook-enforced laws (consent-gated) — finished: 2026-10-18 (sps-hooks.sh install/status/remove, sps-hook-gate.sh, HOOKS.md, 12 tests)
- [x] id: T-33 task: Lesson auto-proposals (human gate preserved) — finished: 2026-10-18 (propose_lessons.py, LESSONS.md section, 19 tests)
- [x] id: T-34 task: Self-verification loop + fresh-context review law — finished: 2026-10-18 (HANDOFF step 4b, SECTION-DOD 52, check_product_proof coverage)
- [x] id: T-35 task: Plain-language mode — finished: 2026-10-18 (PLAIN-LANGUAGE.md, 5 plain-gate templates, plain_language.py, 17 tests)
- [x] id: T-36 task: Client-project bootstrap scaffold — finished: 2026-10-18 (sps-init.sh, kickoff template wired to check_kickoff.py, 7 tests)
- [x] id: T-37 task: Weekly self-audit workflow — finished: 2026-10-18 (weekly-audit.yml cron + anti-spam issue filing, 10 tests)
- [x] id: T-38 task: After-sale clock dashboard — deferred by user 2026-10-18 (build only on real demand)
- [x] id: T-39 task: Third-party skill auto-upgrade — deferred by user 2026-10-18 (conflicts with T-29 pinning; revisit with review-then-apply flow)
- [x] id: T-12 task: Dynamic skill-selection redesign + CMS/SEO hardening — finished: 2026-10-17
- [x] id: T-10 task: P10 completion + Packages 2/3 + sps-seo + learning system — finished: 2026-10-17
- [x] id: T-18 task: .sps memory-budget law + token-reduction rules — finished: 2026-10-17 (commit 8ef6025)
- [x] id: T-11 task: Second-opinion verifier fixes — finished: 2026-10-17 (commit 85cd8b3)
- [ ] id: T-40 task: Launch-video creation skill (research: no video skill installed; candidates = Remotion/ffmpeg-based; needs user consent per TOOL-CONSENT before any install) — queued 2026-10-18
- [ ] id: T-41 task: Full client-project roadmap doc (kickoff → handover → after-sale, one-page total roadmap for clients) — queued 2026-10-18
- [ ] id: T-42 task: Widen placeholder detection in check_copy.py (sample text / your text here / empty alt attributes / repeated filler) — queued 2026-10-18 (user asked about placeholder detection; current COPY_PLACEHOLDER covers lorem/placeholder text/TODO: copy/XXX copy)
- [ ] id: T-43 task: Roadmap source files received at ~/Downloads/gemini argon/ (42-step/7-phase/9-gate universal roadmap, .md + .docx same content + 2 interactive HTML) — merge into T-41 client-facing roadmap; report delivered, awaiting user go
- [ ] id: T-44 task: Conversation-loss resilience (user pain: "when I lose conversation, context is gone") — design + build a durable context-recovery layer so any new agent session reconstructs full working state from disk, not chat history. Candidates: (a) strengthen .sps/handoff.md auto-checkpoint law (already exists — audit why it failed in practice), (b) auto-snapshot per-task state to .sps/evidence/ at every gate, (c) session-start bootstrap that reads handoff + task-queue + provenance and presents "here is where we were" without being asked, (d) transcript-tail export on every pause. Queued 2026-10-18 from user report.
