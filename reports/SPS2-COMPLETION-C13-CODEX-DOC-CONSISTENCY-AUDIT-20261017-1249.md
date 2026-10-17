# SPS2 Completion C13 — Documentation Consistency Audit

**Timestamp:** 2026-10-17 12:49 +06 (Asia/Dhaka)  
**Agent:** Codex C13 read-only audit  
**Status:** `NEEDS_REVIEW` — findings are documented; no document or governance correction was applied.  
**Scope:** Current operator-facing documentation and project reports for P7 phase status, P10 implementation/publication status, test and validator results, and approval boundaries.

## Method and limits

Read the completion backlog and the C4, C8, C9, and C10 reports first. Then inspected the root P7 readiness audit, current C0–C3 evidence, relevant SPS2 reports, P10 evidence/requirements/inventory text, current P10 slice/CMS state, and the five normative files named in prior audits. Checked file presence for the P7 and P10 deliverables named below.

This was documentation and file-presence review only. No product tests or validators were run. No source, `.sps/`, decision, evidence, requirements, inventory, approval, baseline, or historical report was edited. The only intended write from this audit is this new timestamped report. Existing modified and untracked work was preserved.

## Summary

- The completion backlog and current checkpoint report correctly keep release readiness **NOT READY**, record the P10 gate as **9 PASS / 5 FAIL / 2 BLOCKED (exit 1)**, and distinguish implementation artifacts from verified completion.
- Several older records still present once-current absence/status statements as if they were current. The clearest examples are the root P7 readiness snapshot and P10 inventory/evidence prose. Preserve their historical provenance; use an additive reconciliation or a User-authorized governance correction.
- The current P10 content remains `draft` with `published_at: null`, and the slice's `user_approval` remains null. Publication and approval boundaries must remain in force.
- Five modified normative documents currently say DEC-7301/DEC-7302 authorized or approved changes, while the correction sidecar and C8 audit treat DEC-7301/2/3 as unapproved/disputed. Do not rewrite or rely on those statements as User authorization without resolving the authority question.

## Findings and proposed disposition

### C13-01 — P7 root audit is a historical snapshot with stale present-tense status

**Files and claims:**

- `AUDIT-P7-READINESS-AND-DECISION.md:6` says `P7 NOT STARTED / NOT APPROVED`.
- The same file at lines 82–84 says the memory layout, team bootstrap, and isolation validator are absent; lines 149–151 repeat that absence claim.
- C10 reports those roadmap deliverables are tracked at HEAD: `sps2/memory/memory-layout.json`, `sps2/memory/team-bootstrap.md`, and `sps2/tools/isolation_validator.py`. It also reports repository records for P7 prerequisite decisions, implementation authorization, and completion approval dated 2026-10-04/05. These are repository-record facts, not independent authentication of the underlying User messages.

**Classification:** `SAFE_REPORT_ONLY` for an additive current-status reconciliation. The root audit is dated 2026-10-04 and its recorded HEAD predates P7 implementation; its historical snapshot should not be rewritten. C10 already provides a current reconciliation. If the root audit is linked as current operator guidance, add a clear link to the reconciliation at an authorized report-update checkpoint.

**Safe wording:** “The 2026-10-04 audit records the pre-authorization state. Later repository records show P7 authorization/completion and the three roadmap deliverables present at HEAD; approval authenticity is not independently established by this file audit.” Do not state that the present P7 state is unapproved solely from the old snapshot.

### C13-02 — P10 inventory and evidence contain stale implementation-presence claims

**Confirmed current file presence:** `domain/frontend/home_render.py`, `domain/frontend/layout_registry.py`, `domain/frontend/tests/test_home_render.py`, `domain/cms/data/content_types.json`, `domain/cms/data/content.json`, `domain/cms/data/revisions.jsonl`, `sps2/tools/p10_runtime_gate.py`, `sps2/tests/test_p10_runtime_gate.py`, and `sps2/project/SLICE-P10-01.json` are present. C9 records a live gate execution with exit 1 and 9/5/2. This establishes artifact presence and an observed failing gate run; it does not establish authorization, functional correctness, publication, or readiness.

**Claims requiring reconciliation:**

- `sps2/requirements/P10-SECTION-INVENTORY.json:2` says the runtime gate “is specified but NOT implemented and has NOT been executed.” Both implementation-file absence and never-executed claims are stale. The gate is present, and C9 records its execution.
- `sps2/requirements/P10-SECTION-INVENTORY.json:99` says the Home renderer and REQ-P10-07/REQ-P10-09 do not exist and says runtime-gate checks are not claimed to exist. A renderer file, the requirements document/IDs, and the runtime-gate file exist. Whether all corresponding acceptance requirements are implemented or verified remains unestablished.
- `sps2/requirements/P10-SECTION-INVENTORY.json:103` says there are “Zero sections enumerated” although the `sections` array contains a Home entry. It also says the layout registry, populated P8 CMS state, and slice contracts do not exist; the current tree contains those artifacts. This note conflates historical planning/provenance with present file state.
- `sps2/evidence/P10-EVIDENCE.json:23` says “no P10 implementation exists (unauthorized).” That absolute presence claim is stale. The same line’s no-build, unpublished-content, and no-complete-slice-gate-pass limitations remain consistent with C9’s evidence.
- `sps2/requirements/P10-REQUIREMENTS.json` retains per-requirement `REQUIREMENTS_ONLY` / `implementation.state: NOT_STARTED` values (for example lines 78–87 and 99–109). These may be intended as formal phase/approval status rather than simple file-presence claims; the correct status semantics are not established by this audit.

**Classification:** Stale presence wording can be reported safely in a separate audit (`SAFE_REPORT_ONLY`). Editing P10 evidence, inventory, or formal requirement status is `USER_GATED_GOVERNANCE/DECISION`: these artifacts carry provenance, approval, and phase-state semantics, and C9 records that authorization/provenance for the untracked gate artifacts is unresolved. Keep any correction limited to verified facts; do not turn artifact presence into a completion claim.

**Safe factual distinction:** “Some renderer, CMS, slice, and gate artifacts are present. Their authority/provenance and functional completion are unresolved; the current gate is failing/blocked; no built output or publication is established.”

### C13-03 — Normative documents repeat disputed DEC-7301/7302 authority as fact

The following current worktree text says updater exceptions were “authorized by DEC-7301” or Home dependencies were “approved by DEC-7302”:

- `sps2/governance/P7-THREAT-MODEL.md:148`
- `sps2/governance/P9-THREAT-MODEL.md:171–172`
- `sps2/requirements/P3-REQUIREMENTS.json:289`
- `sps2/requirements/P9-REQUIREMENTS.json:350–351`
- `sps2/requirements/P10-REQUIREMENTS.json:14`

C8 identifies the correction sidecar as saying DEC-7301/2/3 are unapproved and notes that matching manifest hashes prove integrity, not approval. These five files are modified in the shared worktree; their edits must be preserved.

**Classification:** `USER_GATED_GOVERNANCE/DECISION`. Do not edit these normative records, ratify the disputed decisions, or cite their wording as proof of User approval until the User resolves the authority source and disposition. An audit report may safely record the contradiction and source references.

### C13-04 — Current P10 publication and approval boundary is accurately recorded

C9 reports `domain/cms/data/content.json` has `status: "draft"`, `published_at: null`; the slice has `user_approval: null`; and Round 16 records `PUBLICATION: DEFER` / `USER APPROVAL: NOT GRANTED`. This audit independently read the current CMS/slice values and confirmed those states. Current completion materials correctly keep P10/release **NOT READY**.

**Classification:** `USER_GATED_GOVERNANCE/DECISION` for any publication, approval, exposure, or change to these recorded boundaries. No documentation correction is proposed to the current status. Keep “inventory approved” separate from “slice approved” and “published.”

### C13-05 — Test and validator counts are correctly time-scoped in the current completion materials

The backlog records the 1,066-test / 2-skip matrix as the 2026-10-17 12:08 verification. C0–C3 records the same count, validators 79/4, 68/9, 66/10, 57/11, 44/1, and the P10 gate 9/5/2. C10 independently records the post-`.sps/`-update P3 result as 66/10 and explains the earlier 67/9 observation as a different tree state. These are dated evidence, not a fresh C13 verification; this audit ran no tests or validators.

Older round reports contain earlier counts and earlier gate states. They are timestamped historical snapshots and should not be mass-edited. The erroneous Claude 4/12 P10 count is explicitly corrected in `reports/SPS2-INDEPENDENT-QA-CLAUDE-FINAL-20261017-100309.md`; use the correction and later 9/5/2 evidence when summarizing present status.

**Classification:** `SAFE_REPORT_ONLY` to add a current, timestamped summary or an explicit “as of” cross-reference. `UNVERIFIED` to present any older count as current without rerunning its exact command on a captured tree. Do not alter test/validator outcomes or declare readiness by changing prose.

### C13-06 — C8’s P7 cross-reference recommendation is stale relative to C0–C3

C8 at line 25 says the C0–C3 report describes P7 artifacts as absent and asks that it be corrected. The current C0–C3 report already says the P7 paths are tracked at HEAD and that the earlier absence characterization was incorrect. File timestamps show C0–C3 was updated after C8. Keep C8 as its historical audit; this report records that its follow-up is already reflected in C0–C3.

**Classification:** `SAFE_REPORT_ONLY`. No additional source edit is needed. If the coordination log is updated later, note that C8’s requested C0–C3 correction is complete.

## Operator guidance

- Treat the completion backlog and C0–C3/C8/C9/C10 reports as dated evidence; use their capture times and later state notes.
- P7 deliverables are present and historical repository records show completion, while the old root audit is pre-implementation history. Do not claim independent authentication of the recorded approvals.
- P10 has partial artifacts, but it is not ready or published: current CMS content is draft, slice approval is null, the gate is 9/5/2 and exits 1, and required build/evidence/runtime prerequisites remain absent or blocked.
- DEC-7301/7302/7303 and associated governance/baseline changes remain disputed/User-gated. A document that repeats an approval claim does not authenticate that approval.
- No test, validator, publication, approval, deployment, release, or protected-record state was changed in this audit.

## Handoff

C13 is a read-only audit checkpoint, not authorization to modify normative requirements, evidence, inventory, approval records, decision sidecars, validator baselines, CI, or release state. Safe next work is limited to additive report/coordination clarification. Any correction to governance-bearing P10 or DEC-730x text must wait for the applicable User decision and preserve the worktree.
