# SPS Project Handoff & State
Read this to understand the current project context, completed tasks, and next steps.

## Required skill
- `/sps` required for this project: **yes**

## SPS version
- Skill version: 4.1.0

## Active agent
- See `./.sps/agent.md`
- Host:

## Current phase
- Discovery / planning / implementation / verification / audit:

## Latest audit
- Date:
- Score: /100
- Band:
- Report: ./.sps/audit-report.md
- Waiting for user choice:

## Approved sections
- 

## Waiting for approval
- 

## Mobile / low-end status
- Policy: minimal unless user approved richer
- Last responsive check:
- Lag risks remaining:

## Verification status
- Verified:
- How verified:
- Still manual / Unverified:

## Evidence
- Known:
- Assumed:
- Unverified:

## Current status
- 

## Conversation log
<!-- Rolling log: keep ONLY the last 5 entries; oldest -> .sps/archive/log-YYYY-MM.md (CONTEXT-BUDGET.md) -->
- 2026-10-17 (session 5c): CI green on 945ecce. User-reported hover-on-touch failure fixed: MOBILE-LOW-END 'Hover/touch law (hard guard)' + DESIGN-GATE cross-ref + law-checker marker (commit 101effe, pushed). Legal/consent checklist audit (Gemini list, 8 sections, wf_366a6347-b5b) launched; gaps to close on completion.
- 2026-10-17 (session 5b): Master-checklist audit wf_42b5fe5f-2e8 COMPLETE (115 agents, 4.6M tokens): 106 raw gaps, 96 confirmed real, ALL closed — SECTION-DOD 28-50 (security/session/data/observability/privacy laws), VERIFICATION-RECIPES (test isolation, load/stress, PITR, cleanup gate), DESIGN-GATE Copy laws, MOBILE-LOW-END minify/HTTP2, sps-seo (og-image/llms.txt/GSC/SPF-DKIM-DMARC). Law-checker extended to 15+7 new markers with 2 negative tests. Battery 1104/2 skipped, all validators green. Commits a392faf + 223603b/26f71e1/ffd124b ready for ONE batched push.
- 2026-10-17 (session 5): T-17 delivered — robust legacy-skill handling in install.sh: backup-before-replace to ~/.sps/backups/<skill>/ (last 3 kept, per-host stamp hash), VERSION detection, upgrade report ~/.sps/last-upgrade.txt, restore path printed. VERSION bumped 4.0.0 -> 4.1.0 (CHANGELOG/README/templates/SKILL.md stamped). Manifest re-pinned (install.sh, CHANGELOG.md, README.md; self-hash updated). Battery 1102 passed/2 skipped; legacy check PASS; law check PASS; p4 2 fails = documented pre-existing (P7_ARTIFACT_CREATED x2). Master-checklist audit wf_42b5fe5f-2e8 in final verify phase; T-17 adversarial verifier running. One batched push pending audit results.
- 2026-10-17 (session 4): T-12/T-14/T-15 delivered: TOOL-CONSENT.md (law 17, renumber Auto-Update to 18), COMPANY-LIFECYCLE.md (kickoff -> platform research -> G1 confirm -> lifecycle plan -> build -> delivery -> after-sale 1mo all-type + 1mo free SEO), skill-search.sh mirror fix for CI 'Script mirrors in sync' failure on 122c9e7. Battery: 1091 passed/2 skipped; smoke PASSED (4 optional third-party installs fail upstream); manifest 22/22 verified. Report: reports/SPS2-SESSION-4-LAWS-LIFECYCLE-CONSENT-20261017-221639.md. Second-opinion workflow wf_db59c97b-2d1 run on the batch. One batched commit+push per DEPLOY-BUDGET law.

## Lessons (auto-appended by the learning system)
- Ordering: attach gate_record LAST, after every state change — earlier claims go stale otherwise (MIST-20261017-001).
- Read the schema before adding fields; additionalProperties:false is common (MIST-20261017-002).
- After any restructure, recheck every hardcoded path depth (2 occurrences: MIST-20261017-003/004; promotion proposal PROP-20261017-path-derivation awaiting ratification).

## 2026-10-18 — Session 6: legal gate + file-splitting + user-guidance + universal hosts
- LEGAL-COMPLIANCE.md shipped: 8 sections, 49-item adversarial audit folded in (AUP added)
- FILE-SPLITTING.md (300/500 caps) + USER-GUIDANCE.md (one-step law) as hard laws 15/10
- Universal host support: install.sh --agent '*' = 30+ hosts; 6 new adapters (goose/crush/trae/junie/zed/openclaw)
- install.sh re-pinned in legacy manifest (self-hash d88a1e8d…)
- Commits: 999fa65, 6ebd2d8, d2cafd3 — battery 1104 OK, sps2 80/80
- Skill best-practices verified: all SKILL.md < 500 lines, descriptions < 1536 chars

## 2026-10-18 — Session 6b: cross-project lesson channel (user interview → build)
- User decisions: command+auto-capture / git PR / approve-each / strict template
- LESSONS.md + scripts/sps-lesson.sh (capture/send/review) shipped; law-checked
- Manifest now 25 exceptions (sps-lesson.sh pinned), self-hash a384b6a8…
- Commit d37942d — battery 1105 OK, sps2 80/80

## 2026-10-18 — Session 6c: P3 branch merged to main (PR #1)
- PR #1 merged (30534ba): 123 commits — hard laws, legal gate, lesson channel, universal hosts, T-17
- main branch protection enabled: 4 required CI checks, force-push/deletion blocked
- Local main synced to 30534ba; build/roadmap-p3-completion retained for future work

## 2026-10-18 — Session 6d: /sps lesson review + /sps status shipped (PR #3)
- /sps lesson review: per-lesson workflow (Problem/Rule/Applies-to shown, target verified, approve/reject/edit)
- /sps status: read-only dashboard (branch, queue, handoff, after-sale, version, lessons, unpushed)
- Manifest 28 exceptions (self-hash 216658ce…); all validators + CI green
- Ecosystem-scan design delivered (report-only, GitHub Actions nightly, [skip ci]) — build queued

## Session handoff — 2026-10-18 (wrap-up before user restart)

**Completed this segment:**
- Statusline shipped: `~/.claude/statusline.sh` + registered in `~/.claude/settings.json`
  (model · TPS · context % · cache read/write + hit ratio + warm/TTL · cost · git).
  TPS = last assistant message output tokens / generation dt, 5-min freshness window,
  cached in `~/.claude/.statusline-tps.json` so it persists while idle.
  USER FEEDBACK to address next session: TPS feels delayed — wants per-second real data.
  Claude Code only passes completed-message data to statusline scripts; investigate
  faster refresh / mid-generation approximation on resume.
- Copy research COMPLETE: 5 researchers + synthesizer (wf_35ee6376-6b5, 6 agents).
  Design saved: `.sps/research/copy-gate-design.md` (full COPY-GATE spec: hard laws,
  machine checks incl. EN+BN slop blocklists, burstiness, sadhu-form regex, check_copy.py
  advisory/deployment modes). Raw findings: `.sps/research/copy-research-findings.md`.
- AGY (Antigravity CLI) installed by user; smoke-tested OK; Bangla copywriting probe
  confirmed strong (চলিত রীতি, গুরুচণ্ডালী দোষ, AI-cliché avoidance). User says AGY is
  best for Bangla copywriting — use it as reference/collaborator for COPY-GATE.
- CI green on 7288cc8 (sps-ci, windows-smoke, secret-scan all success).

**PENDING (do not forget — binding "no task left halfway"):**
1. Fix confirmed final-ship-audit findings (wf_9ce09692-a3a journal has 28 results;
   parse from journal.jsonl). CRITICAL: install.sh:398 PRE_EXISTING_SPS wipe;
   uninstall.sh:354 &&/|| chaining; + ~20 more (install.ps1 Invoke-Native/Start-Job,
   import-scanner bypasses, temp-dir leaks, slugify collision, check_laws stale loop var,
   check_emoji fail-open, sps-cms installer exit codes). Each fix → re-pin → battery → push.
2. COPY-GATE implementation from `.sps/research/copy-gate-design.md`:
   skill/sps/COPY-GATE.md + framework/sps2/tools/check_copy.py + scripts/sps-copycheck.sh
   mirror + SKILL.md hard law + check_laws.py markers + SKILL-ROUTER row + tests.
   Consider AGY as Bangla-quality reference. Re-pin provenance after skill changes.
3. Statusline TPS refresh improvement (user request above).
4. Batch C decisions still need explicit user consent (do NOT act): enforce_admins flip
   + 5th required check; verifier hash pinning; README wording.
5. QA report: append audit round + this segment to reports/ as NEW timestamped .md.

