# SPS2 ROUND 18 — CONSOLIDATION AND READINESS

Report time: 2026-10-16T18:37:24+06:00 (suffix 20261016-183724)
Mission: consolidation round — no new fixes, no new policy. Audit the
worktree for regressions and overlapping edits, re-run the full offline
verification battery, verify gate + digests + updater safety + renderer
**together**, and produce the final integrated manifest, test matrix, and
unresolved-risk list. Items 7–10 of the mission (installer backup, stale
evidence, D-P10 renames, publication/commit/CI) were left untouched as
instructed.

---

## 1. Regression & overlap audit: CLEAN

Every file fingerprinted at the end of Round 17 (report §6) was re-hashed
this round and **matches exactly** — no regression, no overlapping edit, no
drift since Round 17:

| File | Round 17 SHA-256 | Round 18 | Status |
|---|---|---|---|
| `sps2/tools/p10_runtime_gate.py` | `99d55ffb…` | `99d55ffb…` | MATCH |
| `sps2/tests/test_p10_runtime_gate.py` | `f585e1b4…` | `f585e1b4…` | MATCH |
| `sps2/tests/test_updater_safety.py` | `d51c20dd…` | `d51c20dd…` | MATCH |
| `get-sps.ps1` | `3b3b084d…` | `3b3b084d…` | MATCH |
| `scripts/sps-update.sh` | `ba90bfbf…` | `ba90bfbf…` | MATCH |
| `scripts/update-sps.ps1` | `fc207b82…` | `fc207b82…` | MATCH |

Additional continuity checks against earlier rounds:
- **CMS files** identical to the Round 15 audit fingerprints (§5.4 of the
  Round 15 reconciliation report): `content.json` `c46a0012…`,
  `content_types.json` `6635ed4d…`, `revisions.jsonl` `54a0eeaa…`. The
  digest values written under DEC-7202 therefore still bind the *same* CMS
  state — no silent content drift.
- **Slice** `sps2/project/SLICE-P10-01.json` identical to the Round 15
  fingerprint (`a3d29c39…`); **P10 evidence** identical (`c58bcb14…`) —
  the stale-evidence wording (R15-009) is preserved untouched, as ordered.
- `install.sh` / `install.ps1` untouched (backup/restore proposal remains
  unimplemented, as ordered).
- Git: HEAD `c49f3852…` unchanged; **0 staged; 0 stashes**; 33 porcelain
  entries — the same set as Round 17's end state (16 modified tracked + 17
  untracked paths). The working tree diff is 592 insertions / 81 deletions
  across 16 tracked files, unchanged in shape from Round 17.

## 2. Full offline regression battery (re-run this round)

| Suite | Command | Result |
|---|---|---|
| P10 gate | `python3 -B -m unittest sps2.tests.test_p10_runtime_gate` | **Ran 320 tests, OK** |
| Updater safety | `python3 -B -m unittest sps2.tests.test_updater_safety` | **Ran 13 tests, OK (skipped=1, pwsh unavailable)** |
| Frontend (render + slots + layout) | `python3 -B -m unittest domain.frontend.tests.test_home_render domain.frontend.tests.test_content_slots domain.frontend.tests.test_layout_registry` | **Ran 85 tests, OK** |
| **Total** | | **418 tests, 0 failures, 1 environmental skip** |

## 3. Governance validators (full sweep)

- **Inventory**: `P10-SECTION-INVENTORY.json` → **0 ERR**.
- **Decisions** (16 files): 0 ERR on all Round-12-era and newer records
  (P10-GATE-SEMANTICS-ADOPTION, P10-ROUND12-USER-DECISIONS,
  P10-DELEGATED-DECISIONS, SPS2-ROUND16-USER-DECISIONS, ATTRIBUTION-POLICY,
  LEGACY-*, PHASE3-COMMIT-AUTHORIZATION-TRANSCRIPTION, REMOTE-PUSH-AUTHORIZATION).
  14 files show ERRs — **verified pre-existing at HEAD** (spot-compared
  P17/P4/P9/ROADMAP-P3/P7-READINESS: HEAD count == worktree count for each)
  and of the known classes: `D-P10-*`/legacy ids predating the `DEC-\d{4}`
  rule (the issue the User's 2026-10-09 approval explicitly kept out of
  scope), and OPEN-DECISION-* records which are open questions by design.
- **Evidence** (11 files): P1/P2/P3/P9/P10/P17/ROADMAP/SEC-INCIDENT → 0 ERR;
  P3-APPROVAL (5), P4 (1), P5 (1), SEC-P3-CLOSURE (8) — all verified
  identical at HEAD in Round 17; unchanged this round.

## 4. Integrated verification — gate + digests + updater + renderer together

### 4.1 Real P10 gate (read-only)
`python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json`
→ **exit 1, OVERALL: FAIL — 9 PASS / 5 FAIL / 2 BLOCKED**, 5
unresolved_semantics. Failing: published-only-content (draft),
slice-id-uniqueness, evidence-authenticity (no gate_record),
approval-authenticity (null approval), req-p10-07-reconciliation (manifest
absent). Blocked: exposure-declaration, p9-deployment-audit. Every failure
maps to an explicitly withheld authorization — the gate is honest.

### 4.2 Inventory digests recomputed fresh and MATCH
Independently recomputed (canonical JSON, sorted keys, UTF-8, JSONL
line-parsed, path-bound) →
`cms_state_digest` = `sha256:b35f7aba68eca4e7c9b688ae979891330f2f3d08c2b4250ce855c55943f7e38e` ✓
`p8_contract_digest` = `sha256:ee6bb68f04f0eb468f0fd6eafaaea0b68639b88199e207c7a76ef57e10bbf217` ✓
both equal the stored values. **The two previously-null controls
(cms-state-digest, p8-contract-digest) now PASS against the live CMS state.**
`user_approval` still `null`; `inventory_state` still
`COMPLETE_AWAITING_USER_APPROVAL`.

### 4.3 Updater safety (integrated)
Mirror parity identical (`diff -rq scripts skills/sps/scripts`); 5/5 bash
scripts pass `bash -n`; zero occurrences of `git reset --hard`,
`rm -rf "$REPO_DIR"`, `Remove-Item -Recurse -Force $repoDir`, or bootstrap
auto-update across all eight ratified files. `pwsh` remains unavailable →
the one behavioral PowerShell test stays skipped (environmental).

### 4.4 Renderer (end-to-end, in-memory only — nothing written)
Real slice + real CMS data through the real renderer:
- `draft_policy="fail"` (the default): draft content → **FAILED CLOSED** with
  `HomeBuildError stage 3 (build): content '60e51f05…' is status 'draft',
  not 'published'` — exactly the fail-closed behavior HOME-ACC-06 requires.
- `draft_policy="noindex_preview"` (deterministic error-state preview):
  renders 1,557 bytes, `validate_home_document` → **no issues** (`[]`),
  `noindex` present, no script injection.
- This closes the loop with the gate: `published-only-content` FAILs at the
  gate for the same reason the renderer refuses to build — the content is
  draft. The two systems agree.

## 5. Final integrated file manifest (untracked P10 workstream + ratified workstream)

**P10 gate workstream (User-authorized Round 14; untracked):**
| File | Role | SHA-256 (first 16) |
|---|---|---|
| `sps2/tools/p10_runtime_gate.py` | 16-control runtime gate, all DEC-7112 semantics implemented | `99d55ffb8c8af8f5` |
| `sps2/tests/test_p10_runtime_gate.py` | 320-test contract suite | `f585e1b4b8a90780` |
| `sps2/project/SLICE-P10-01.json` | Home slice (DRAFT, approval null) | `a3d29c3927a6c0bf` |
| `sps2/evidence/P10-EVIDENCE.json` | EV-P10-001 (BLOCKED; stale wording preserved) | `c58bcb14f5fed0e7` |
| `sps2/requirements/P10-SECTION-INVENTORY.json` | digests written under DEC-7202 | `d0984c0ddf394ade` |
| `sps2/decisions/P10-GATE-SEMANTICS-ADOPTION.json` | DEC-7112 | (Round 15 §2.4) |
| `sps2/decisions/P10-ROUND12-USER-DECISIONS.json` | DEC-7111 verbatim transcription | `5d7f8782fbd5212a` |
| `sps2/decisions/P10-DELEGATED-DECISIONS.json` | DEC-7101..7110 | `5fd70bdbcff7a761` |
| `sps2/decisions/SPS2-ROUND16-USER-DECISIONS.json` | DEC-7201/7202/7203 | `c7f430d94a2ac20a` |
| `domain/frontend/` (7 modules + 3 test modules) | renderer, slots, layout registry | (85 tests OK) |
| `domain/cms/data/` (3 files) | Home content, content types, revisions | `c46a0012…`/`6635ed4d…`/`54a0eeaa…` |

**Updater-safety workstream (ratified DEC-7201; 8 tracked modified + 1 untracked):**
| File | SHA-256 (first 16) |
|---|---|
| `get-sps.sh` | `3b3e4fcfd7ac6e09` |
| `get-sps.ps1` | `3b3b084dfcc7efd4` |
| `scripts/bootstrap-sps.sh` (+ mirror) | `8139065418a8e24d` |
| `scripts/sps-update.sh` (+ mirror) | `ba90bfbfe6f57fd6` |
| `scripts/update-sps.ps1` (+ mirror) | `fc207b82ea549c49` |
| `sps2/tests/test_updater_safety.py` | `d51c20dd98dda505` |

**Reports:** 28 files in `reports/` (this report makes 28); none overwritten.

## 6. Test matrix (cumulative state)

| Area | Tests | Result | Notes |
|---|---|---|---|
| P10 gate contract (incl. all six DEC-7112 semantics, R15-001/002/003 fixes) | 320 | OK | +12 vs Round 14 |
| Updater safety (incl. R15-004/007/008 regressions) | 13 | OK, 1 skip | pwsh behavioral test environmental |
| Renderer / slots / layout | 85 | OK | end-to-end draft fail-closed verified §4.4 |
| Real gate vs real repo | 16 controls | FAIL (honest) | 5 failures = withheld authorizations |
| Digest recomputation | 2 | MATCH | fresh recompute == stored |
| Governance validators | 27 files | 0 new ERR | all ERRs pre-existing at HEAD |
| Bash syntax / lint / mirrors | 5 + 1 + 3 | PASS | |

## 7. Unresolved-risk list

| # | Risk | Severity | Status |
|---|---|---|---|
| 1 | Installer replaces managed skills with no backup/restore (R15-005) | High | **Proposal B1 drafted (Round 17 §3); implementation requires explicit User authorization** |
| 2 | Stale P10 evidence (R15-009): says gate tool untracked/no decision, "no P10 implementation exists" | Medium | Preserved untouched per mission; refresh requires authorization |
| 3 | `pwsh` unavailable → PowerShell behavioral coverage skipped | Low | Environmental; run suite on a pwsh machine |
| 4 | `D-P10-*` decision ids fail the `DEC-\d{4}` validator rule | Low | Pre-existing; renaming forbidden by mission item 9; needs a User decision on validator accommodation |
| 5 | All P10 workstream files + updater workstream are **uncommitted** (0 staged; commit/push NOT AUTHORIZED) | Medium | Work survives only in the working tree |
| 6 | 14 decision + 4 evidence files carry pre-existing validator ERRs (legacy formats) | Low | Documented; no new ERRs introduced |
| 7 | Gate's five remaining failures (publication, approval, gate_record, manifest, history) | By design | Each lifts with its named authorization |
| 8 | No trust root anywhere: all digests/approvals are content-integrity and self-declared attribution (UQ-ATT-2) | Standing | Documented in UNRESOLVED_SEMANTICS |

## 8. Exact decisions needed for the next phase

Ordered by what they unblock:

1. **Commit/push authorization** — the single highest-leverage decision. The
   entire P10 workstream (gate, 320 tests, slice, evidence, decisions,
   renderer, CMS data) plus the ratified updater-safety workstream exist
   only as working-tree changes. A commit grant (scope: which file sets)
   would make the state durable. Until then any accident (checkout, clean,
   disk) loses it.
2. **Installer backup/restore (B1)** — authorize implementing the Round 17
   §3 proposal, or explicitly defer the installer workstream again.
3. **Stale P10 evidence refresh (R15-009)** — authorize updating
   `sps2/evidence/P10-EVIDENCE.json` to reflect the Round 14 gate-semantics
   authorization while preserving the BLOCKED result class (no publication,
   no approval implied).
4. **Publication decision** — still DEFER. Authorizing publication lifts
   `published-only-content` AND unblocks the renderer's default
   fail-closed build path (they fail for the same reason — §4.4).
5. **Fresh explicit User approval act** — only meaningful after the gate
   passes; APPROVAL-MECHANISM: OPTION A stands.
6. **Backend manifest + slice-id history + observed bind + build output** —
   arrive with the first backend code and P9 build work, respectively.
7. **`D-P10-*` validator accommodation** — decide whether the validator
   gains a legacy-id pattern or the records gain a migration note.
8. **`pwsh` environment** — for full PowerShell behavioral coverage.

## 9. Side-effect verification

- This round created exactly **one file**: this report. No source, test,
  decision, evidence, inventory, CMS, schema, CI, or configuration file was
  modified.
- Git: HEAD unchanged (`c49f3852…`), 0 staged, 0 stashes, 33 porcelain
  entries — identical to Round 17's end state plus this report.
- No installer, updater, or bootstrap script was executed. The renderer ran
  in-memory only (no `build_dir` writes; `build_home_slice` was not called).
- No publication, approval, staging, committing, pushing, or CI change.
  Mission items 7–10 honored verbatim.

---

*Round 18: consolidation complete. The worktree is regression-clean against
Round 17, all 418 offline tests pass, governance shows no new errors, the
gate honestly FAILs on five withheld prerequisites, the written digests
match the live CMS state, and the renderer fails closed on draft content in
agreement with the gate. Awaiting the User's next decision.*
