# SPS2 Completion C9 — P10 Readiness Audit

**Timestamp:** 2026-10-17 12:43 +06 (Asia/Dhaka)  
**Agent:** Codex audit subagent  
**Mode:** Read-only; one new report created, no other repository writes  
**Audit status:** `NEEDS_REVIEW` (independent Claude review pending)  
**Readiness verdict:** **NOT READY**. The live P10 gate exits 1 with required controls failing and blocked. No approval, publication, build, deployment, or release is claimed.

## Scope and evidence sources

Read the completion backlog and shared coordination log first, then inspected the live P10 runtime gate, slice schema and requirements, P10 evidence, section inventory, P10 decision records, CMS data, frontend/SEO integration, the shared import-exception scanner, and P9 rollback flow. This report does not update the backlog or coordination log; the parent task will serialize those updates.

## Preservation snapshot

At audit baseline (2026-10-17 12:42 +06): branch `build/roadmap-p3-completion`, HEAD `c49f3852e1c31d0136269c80fe58201b059af3ec`; 42 modified tracked paths, 27 untracked porcelain entries (193 expanded untracked files), 0 staged paths, and 0 stashes. P10 gate/schema/inventory/evidence files were already modified or untracked before this report. No tests, rollback rehearsal, build, network operation, publication, or destructive operation was run.

Key current worktree hashes captured before the report:

| Path | SHA-256 |
|---|---|
| `sps2/tools/p10_runtime_gate.py` | `48af749e393945c4e981f42ba5510f053ff9fa91eaf8c65108dbbbe08bfcfa66` |
| `sps2/tests/test_p10_runtime_gate.py` | `f585e1b4b8a90780bc9420b6ed35fde90f308ee8bd00f6d4310d5ad1aa46fbd5` |
| `sps2/project/SLICE-P10-01.json` | `a3d29c3927a6c0bfa8385881c8dc3adfa0cf3dd11bd97f7a83b0fc376b938058` |
| `sps2/evidence/P10-EVIDENCE.json` | `c58bcb14f5fed0e7982632f6e96fea93cdd8adf3d23991a75ca7ba1abe3f2dc3` |
| `sps2/requirements/P10-REQUIREMENTS.json` | `84fbfb5c2622026325a34878cd1cea694f1738984bf29423e219bc2fbf920de7` |
| `sps2/requirements/P10-SECTION-INVENTORY.json` | `d0984c0ddf394ade74cf35296d7363072592bdc89504ece20a56c23a68d35893` |
| `sps2/decisions/P10-DECISIONS.json` | `a5c3a5b42bb9395c24fd2ecf1a8b7c0100c10ca68ee33fac5b4387d161897192` |
| `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json` | `c7f430d94a2ac20a2c5c83afe04300907d8b92d248696902f4f281f694052d20` |

## Safe checks run

1. `PYTHONDONTWRITEBYTECODE=1 python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json`  
   **Exit 1.** `overall=FAIL`; 16 required controls, 9 PASS / 5 FAIL / 2 BLOCKED; no missing, duplicate, demoted, unknown, malformed, or integrity-problem controls.

   - **PASS (9):** `schema-structural`, `slice-required-fields`, `inventory-preconditions`, `evidence-references`, `evidence-freshness`, `layout-slot-conformance`, `cms-state-digest`, `p8-contract-digest`, `approval-state-interaction`.
   - **FAIL (5):** `published-only-content`, `slice-id-uniqueness`, `evidence-authenticity`, `approval-authenticity`, `req-p10-07-reconciliation`.
   - **BLOCKED (2):** `exposure-declaration`, `p9-deployment-audit`.

2. Read-only shared scanner probe:

   ```sh
   PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
   from sps2.governance.import_exceptions import scan_import_exceptions
   r = scan_import_exceptions('.')
   print('ok=', r.get('ok'))
   print('approved_count=', len(r.get('approved', [])))
   print('violation_count=', len(r.get('violations', [])))
   for item in r.get('violations', []): print('VIOLATION', item)
   PY
   ```

   Process exit 0; scanner result `ok=False`, 8 manifest-approved imports and 1 violation: `sps2/tools/p10_runtime_gate.py:1944: dynamic domain.seo import is forbidden`.

3. Read-only prerequisite checks: searched `sps2/` for a slice-ID-history artifact (no match); `test -e domain/backend/operations.json` exited 1 (missing); searched for repository build/dist/out directories (none found). The gate command supplied no build directory and no history file.

4. No test suites or P9 rollback rehearsal were run. The C0-C3 checkpoint reported the older matrix, but it does not establish current P10 completion; this C9 audit did not rerun that suite.

## Findings and classification

| ID | Finding | Classification / owner |
|---|---|---|
| C9-01 | **Current gate is fail-closed at 9/5/2.** Structural schema, required fields, references, freshness, slot mapping, digest checks, inventory preconditions, and pre-transition state pass. The five failures and two blocks are listed above. | Current; readiness blocker. No gate suppression or baseline change proposed. |
| C9-02 | **The referenced Home content is still draft.** `domain/cms/data/content.json` records `status: "draft"`, `published_at: null`. The gate rejects it for a published route. Round 16 decision DEC-7203 records `PUBLICATION: DEFER` and `USER APPROVAL: NOT GRANTED`; D-P10-8 approves inventory contents only, not the slice or publication. | Current; User-blocked. Do not publish or set slice approval based on the inventory decision. |
| C9-03 | **The evidence is a governance placeholder, not runtime proof.** `EV-P10-001` is dated and covers only a governance-state check; its result is `BLOCKED`, it has no `gate_record`, and the file explicitly says there was no build, P9 audit, runtime gate pass, or P10 test execution. The gate's `evidence-freshness` PASS establishes only that its self-declared timestamp parses. Its evidence-authenticity FAIL is correct. The gate itself states digests establish content integrity/provenance recording only; no trust root or human-authentication mechanism exists. | Current missing evidence; authenticity semantics unresolved/User-blocked. Do not manufacture gate records or claim cryptographic/human authenticity. |
| C9-04 | **Slice-ID uniqueness cannot be established.** `SLICE-P10-01` is present, but no authoritative history was supplied and no history file was found under `sps2/`. The gate intentionally rejects absent or empty history. Search hits in reports/tests are not authoritative history. | Current; blocked on an authoritative source/history and its authorization. |
| C9-05 | **Exposure is declared local but not observed.** The slice declares `LOCAL_NON_NETWORK_EXPOSED`; no runtime `observed_bind_address` is provided, and the gate notes no repository component produces it. It therefore returns BLOCKED. No server/socket was started. | Current; technical observation mechanism missing. Any public/network exposure remains User-authorized only; no exposure is authorized here. |
| C9-06 | **No real P9 deployment audit can run yet.** No build directory was supplied or found. The P10 gate correctly requires non-empty HTML plus root `robots.txt` and `sitemap.xml`, containment, and route identity before invoking P9. The slice's renderer/test entry points still say `PLACEHOLDER-NOT-BUILT`; no build or audit evidence exists. | Current; missing build output and authentic audit evidence. Build/deployment remain outside this audit. |
| C9-07 | **P10's lazy P9 import currently violates the shared isolation scan and affects rollback.** `check_p9_deployment_audit` uses `importlib.import_module("domain.seo.audit")` at `p10_runtime_gate.py:1944-46`; the shared scanner returns `ok=False` for that exact site. `domain/seo/isolation.py:203-210` delegates to that scanner. `rollback_seo.py:231-232` uses the same scanner, and `execute_rollback` performs its zero-orphan check only after deleting the P9 allowlist (`rollback_seo.py:420-462`). With this violation still present, rollback's post-check will return failure after removing P9 files. No rollback was run; a run against the working tree would be destructive. | Current technical interaction; needs a separately scoped, policy-compliant fix or explicit exception decision. DEC-7302/manifest authority remains User-blocked per C8; do not edit the manifest. Other rollback hazards are separately recorded in C4 and remain under review. |
| C9-08 | **The P10 gate's required-control list does not include test-execution or rollback-rehearsal controls.** Its 16 IDs have no `test-execution` or `rollback-rehearsal` control, while REQ-P10-09 requires actual test execution evidence and REQ-P10-16/HOME-ACC-23 require a rollback rehearsal report. The current evidence has neither. A gate pass could therefore omit these explicit obligations unless a separately authorized harness/evidence path is defined and enforced. | Current contract/code coverage gap; proposal for a bounded code-owned repair, after authorization of the untracked gate and C4/C8 review. Not a User policy decision to waive the requirements. |
| C9-09 | **Several absence statements are stale; implementation presence is not proof of completion.** `domain/frontend/home_render.py`, `layout_registry.py`, their tests, and `domain/cms/data/{content_types.json,content.json,revisions.jsonl}` exist now. The inventory/evidence prose still says there is no layout registry/populated CMS state or no P10 implementation/renderer. The gate currently passes layout-slot conformance and both digests, but no P10 tests/build were run here, and the content remains draft. `P10-REQUIREMENTS.json` still labels requirements `REQUIREMENTS_ONLY`/implementation `NOT_STARTED`. | Stale documentation/state claims confirmed by file presence; functional status remains unverified. Reconcile reports and authority before modifying governance artifacts. |
| C9-10 | **Authorization/provenance for untracked P10 gate artifacts is unresolved.** `sps2/tools/p10_runtime_gate.py` and its test are untracked. `P10-EVIDENCE.json` explicitly records that no decision authorizing their creation/tracking was found; P10 decision text scopes prior authorization narrowly and says Phase B/runtime-gate work was not authorized at that point. Later live user direction may affect current scope, but this audit did not establish a specific authorization record for these artifacts. Preserve them and ask the User to resolve provenance; do not delete, stage, or claim approval. | Current governance discrepancy; User decision required. |
| C9-11 | **Inventory approval and slice approval are distinct.** D-P10-8 approves the inventory's contents while intentionally leaving its `user_approval` null and refusing `COMPLETE_VERIFIED_USER_APPROVED` absent real runtime verification. The slice's `user_approval` is also null. The gate's two approval controls correctly fail for the slice and pass only the coherent inventory pre-transition state. | Current; explicit slice approval remains User-blocked until all prerequisites genuinely pass. |

## Stale / current / unverified map

- **Current:** P10 gate result 9/5/2; draft Home content; null slice approval; absent supplied slice history; absent backend operations manifest; no build directory; no observed bind; no evidence gate record; scanner violation; P10 gate/test untracked; rollback post-check shares the scanner.
- **Stale:** statements that the layout registry, persisted CMS content/type data, or any frontend renderer/test files do not exist. Those files exist in the current tree. Their presence does not establish authorization, test success, production readiness, or publication.
- **Unverified:** renderer correctness and runtime behavior, current P10 test results, all-eight-axis implementation, real build output, P9 deployment-mode audit, rollback rehearsal, bind observation, gate-record authenticity, and actual User approval of this slice.
- **User-blocked:** superseding the recorded publication deferral or granting slice approval; resolving authorization/provenance for the untracked gate artifacts; resolving any network exposure; deciding how to establish authoritative slice-ID history and human-authentic evidence. DEC-7301/7302/7303 and baseline/manifest changes remain separately User-gated under the existing backlog.

## Bounded next work after this audit

1. Claude independently reviews this report and confirms or disputes C9-07 through C9-10 without changing the repository.
2. User resolves the P10 gate artifact authorization/provenance and confirms whether the historical publication/approval restrictions remain in force. No agent may infer a reversal from general “finish the project” language.
3. After applicable authorization and independent review, prepare separate proposals for (a) P10/P9 isolation and rollback safety, (b) explicit test-execution/rollback evidence coverage, and (c) stale P10 evidence/inventory wording. Keep governance/manifest edits out of code fixes.
4. Only after actual implementation and authorized evidence exist: run the real P10 suite and gate with authoritative history, evidence, observed exposure, backend manifest, and a real built artifact; run P9 deployment audit and an isolated rollback rehearsal; request fresh User slice approval only after every required check passes.

No action in this audit changes the P10 result or authorizes publication, exposure, deployment, governance edits, or release. Release readiness remains **NOT READY**.
