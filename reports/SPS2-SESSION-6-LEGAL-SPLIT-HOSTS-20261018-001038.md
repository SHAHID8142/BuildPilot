# SPS2 Session 6 Report — Legal Gate, File-Splitting Law, Step-by-Step Guidance, Universal Hosts

Date: 2026-10-18 · Branch: build/roadmap-p3-completion · Commits: 999fa65 → 6ebd2d8 → d2cafd3 → 62eb70c

## Delivered

### 1. Legal & compliance gate (LEGAL-COMPLIANCE.md — NEW)
72-agent adversarial audit of the Gemini legal/consent checklist: **49 confirmed / 15 refuted / 12 already covered**. All 49 folded into an 8-section conditional gate (agreements, consent, privacy, payments, comms, IP, AI governance, accessibility/sector/incident). Scoped at kickoff (Phase 0), walked at Phase 4 pre-delivery; templates flagged for client counsel, never legal advice. AUP was the one item missing from the draft — added.

### 2. File-splitting law (FILE-SPLITTING.md — NEW)
300 soft / 500 hard lines (source), 200/350 (components), 300/500 (CSS), 100/200 (config); 8 splitting rules; hard cap fails Section DoD. Wired as SKILL.md law 10, SECTION-DOD item 17, check_laws.py.

### 3. Step-by-Step User Guidance (USER-GUIDANCE.md — NEW)
One step at a time for external platform actions; never batch steps; never guess UI labels; **secrets stay secret** (masked keys, real values go into .env by the user). SKILL.md hard law 15; SKILL-ROUTER step 4b.

### 4. Universal host support
- install.sh `--agent '*'` now covers the full skills-CLI registry: 30+ hosts (added goose, crush, trae, junie, zed, openclaw, droid, qoder, kilo, warp, devin, replit, grok, openhands, rovodev, zcode, adal, augment, continue)
- SYNC_PATHS extended with each host's skills dir
- 6 new host adapters: goose, crush, trae, junie, zed, openclaw
- SKILL.md host list names the full Agent Skills-standard registry

### 5. Skill best-practices audit (user request)
- Official rule: SKILL.md < 500 lines, description truncated at 1536 chars, split reference material into files
- Verdict: **compliant** — sps/SKILL.md 91 lines, sps-cms 150, sps-seo 178; descriptions 630/553/543 chars; heavy content already split into reference files (progressive disclosure); no changes needed

### 6. Incident: legacy-manifest ordering slip
install.sh edited without re-pinning → sps2 validator red (13 fails). Fixed per DEC-7305: blob+SHA-256 re-pinned, self-hash updated (d88a1e8d…). Lesson: the ordering law applies at **every** edit of a pinned file, not just at batch commit time.

## Verification
- Battery: 1104 tests OK (2 skipped)
- Validators: p2 (69✓), p3 (68✓), p5 (47✓), sps2 (80✓/27 negative), check_laws PASS, lint-sps PASS, legacy exit=0
- CI: pushed after local green (DEPLOY-BUDGET: 3 commits, one batched push each)

## Self-improvement system (user request, pending interview)
User wants lessons learned in OTHER projects using BuildPilot to flow back into BuildPilot automatically. Existing building blocks: MISTAKE-PROMOTION.md (2-strike promotion, project-only), .sps/mistakes.md, check-update/sps-update scripts. Interview scheduled with user to spec the cross-project channel.
