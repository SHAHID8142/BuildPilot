# SPS2 / BuildPilot — P10 Runtime Gate Completion Report

- **Date**: 2026-10-17
- **Branch**: `build/roadmap-p3-completion`
- **Commit**: `1279cd6` — "P10 completion: publish, build, approval, gate-record — 15 PASS / 1 by-design BLOCKED"
- **Mandate**: "finish all task make it fully ready to use ASAP but do not left anything make it perfect from every aspect."

---

## 1. What this work was

Driving the P10 runtime gate (16 fail-closed controls,
`framework/sps2/tools/p10_runtime_gate.py`) from its post-re-baseline state of
**9 PASS / 5 FAIL / 2 BLOCKED** to its maximum honest state, by executing the
remedies approved in the user-decision packet (reports/SPS2-USER-DECISION-PACKET-20261017-130047.md).

## 2. Remedies executed (in order)

1. **Published CMS content** — `PublishingService(store, rbac).publish('super_admin', '60e51f0536cb413e86e96ff6f750846a')`. Content transitioned draft→published with real `published_at`; transition recorded in `revisions.jsonl`. Note: `author_id` remains the provisional draft author string; this is disclosed, not hidden.
2. **Real local build** — `build_home_slice()` emitted `index.html`, `robots.txt`, `sitemap.xml` into `framework/sps2/project/SLICE-P10-01-build/`. P9 deployment audit re-run: **PASS, exit 0** (14 passed / 1 warning / 0 critical).
3. **Slice-ID history** — `framework/sps2/project/SLICE-ID-HISTORY.json` created as a **bare JSON list** (gate requires `isinstance(data, list)`), one entry: SLICE-P10-01, issued 2026-10-13, ACTIVE.
4. **Backend operations manifest** — `framework/domain/backend/operations.json` created (`sps2.backend-operations/v1`, `operations: []` — the authorized empty-case representation per REQ-P10-07).
5. **User approval recorded on the slice** — `acceptance_state` DRAFT→APPROVED; `user_approval = {decided_by: "User", decided_by_role: "USER", decided_at: "2026-10-17"}`. A `basis` field was attempted first and **removed** after the schema rejected it (`additionalProperties: false` on `user_approval`); the rationale lives in the decision ledger, not the slice.
6. **Gate record attached** — `EV-P10-001` in `framework/sps2/evidence/P10-EVIDENCE.json` now carries a `sps2.p10-gate-record/v1` record with `producing_command`, `emitting_tool_version`, RFC3339-UTC `utc_timestamp`, and 6 input + 3 output `sha256:` claims.
7. **Inventory digests regenerated** — `cms_state_digest` and `p8_contract_digest` in `P10-SECTION-INVENTORY.json` recomputed (digests cover canonical JSON of content **combined with repo-relative path**, so the restructure legitimately changed them; regeneration is the authorized update path).

## 3. Ordering correction (honesty note)

The gate_record was initially attached **before** the inventory digest
regeneration, which made one input claim stale
(`29c9b754…` vs actual `5e151898…`) and the gate failed
gate-record cross-check. Fixed by recomputing **all** input/output claims fresh
and refreshing the timestamp — the correct ordering is: all state changes
first, gate_record last. Final gate run shows **zero cross-check contradictions**.

## 4. Final gate state

| Result | Count | Detail |
|---|---|---|
| PASS | **15** | all runtime controls |
| FAIL | **0** | — |
| BLOCKED | **1** | `exposure-declaration` — **by design** |

### Why exposure-declaration is by-design BLOCKED

- REQ-P10-09 c.7 / D-P10-1 forbid any network exposure in Phase A.
- The schema declares `observed_bind_address` **RUNTIME-POPULATED ONLY**.
- No component produces exposure observations, so the declaration can never be
  evidence-backed in Phase A. Tests confirm even loopback-shaped author strings
  BLOCK. The control is doing exactly what it was built to do: refuse to accept
  a declaration that cannot be proven. This is the fail-closed property working,
  not a defect.

## 5. Full verification sweep (post-change)

| Check | Result |
|---|---|
| Test matrix (28 modules, `.github/expected-test-modules.txt`) | **28/28 pass** |
| validate-sps2 | 80/0 ✅ |
| validate-p2 | 69/0 ✅ |
| validate-p3 | 68/0 ✅ |
| validate-p4 | 58/2 — **pre-existing** `P7_ARTIFACT_CREATED` ×2 (identical at baseline commit 0f75af0; not introduced here) |
| validate-p5 | 47/0 ✅ |
| validate-p6 | 68/1 — **pre-existing** `GLOBAL_PATH_REFERENCED` (docstring sentence "we do NOT touch `~/.sps`" trips a naive substring scan) |
| validate-p7-readiness | 30/0 ✅ |
| **P10 runtime gate** | **15 PASS / 1 by-design BLOCKED** |

## 6. Remaining known items (all disclosed, none hidden)

1. **exposure-declaration BLOCKED** — by-design, unresolvable in Phase A (see §4).
2. **validate-p4 ×2** — pre-existing, identical at baseline.
3. **validate-p6 ×1** — pre-existing naive-substring false positive.
4. **Provisional author_id** in published CMS content — disclosed in §2.1.
5. `inventory_state` was deliberately **not** transitioned to
   `COMPLETE_VERIFIED_USER_APPROVED` while any control remains BLOCKED; the
   approval-state-interaction control passes as-is.

## 7. Verification

Per the standing second-opinion directive, an independent verification subagent
was launched over this commit (recomputing gate results, all sha256 claims,
CMS publish provenance, build artifacts, slice schema, history format, digest
derivations, gate-record well-formedness, 28-module matrix, and a
check-weakening diff scan of `a036efb..1279cd6`). Its verdict is recorded in
the conversation; this report is written before its result is incorporated —
if the verdict is REJECTED on any point, a follow-up report will record the
correction.

## 8. Artifacts in commit 1279cd6

- `framework/domain/backend/operations.json` (new)
- `framework/sps2/project/SLICE-ID-HISTORY.json` (new)
- `framework/sps2/project/SLICE-P10-01-build/{index.html,robots.txt,sitemap.xml}` (new)
- `framework/sps2/project/SLICE-P10-01.json` (approval)
- `framework/sps2/evidence/P10-EVIDENCE.json` (gate_record)
- `framework/sps2/requirements/P10-SECTION-INVENTORY.json` (digests)
- `framework/domain/cms/data/{content.json,revisions.jsonl}` (publish)
- `CLAUDE.md` (BUPT alias)
