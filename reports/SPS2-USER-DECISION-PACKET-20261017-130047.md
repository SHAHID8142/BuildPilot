# SPS2 User Decision Packet — Completion and Readiness Blockers

**Timestamp:** 2026-10-17 13:00:47 +06  
**Mode:** Read-only planning and decision packet only.  
**Scope:** Current completion backlog, coordination log, and C4–C13 audit evidence.  
**Status:** No decision in this packet is approved, rejected, implemented, or ratified by this report. Silence is not approval.

## 1. Live Worktree Context

At packet creation, the live state was:

| Item | Value |
|---|---|
| Branch | `build/roadmap-p3-completion` |
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` |
| Staged files | 0 |
| Modified tracked paths | 42 |
| Untracked porcelain entries | 27 |
| Total porcelain entries | 69 |
| Expanded untracked files | 198 |
| Stashes | 0 |

The counts differ from C0/C1 because later workflow and concurrent `.sps/` work occurred. All existing work was preserved. No source, CI, baseline, governance, approval, P10, `.sps/`, coordination-log, or existing-report file was edited for this packet.

Protected-state hashes remained:

| Path | SHA-256 |
|---|---|
| `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS.json` | `7c35617b309bef3557ad439fbb74be8455535f26a21cfe323d574ff73be5ed69` |
| `sps2/decisions/SPS2-ROUND26-CONTRACT-DECISIONS-CORRECTION-20261017.md` | `a50bfd25fa54c8a6b38ee97515f043d0a29f9518ceabe3b3dfc9457b8620f1e6` |
| `sps2/governance/legacy-exception-manifest.json` | `b3395f807296c9306a67112f54748bb7fdcbd26fb1ad0cc95fa911f42975554d` |
| `sps2/governance/p10-p9-import-exception-manifest.json` | `f818665f471d015d6940a6ddbf4c08f02bfeabd6cc6d72e20295c7a321b5c8a8` |
| `.github/workflows/sps-ci.yml` | `5ba091ceee048a81ede4eabd84174b0f314bf68af98cd8b64cf5323751bfebf0` |
| `.github/expected-test-modules.txt` | `54da0a650566c2e462f096c61f2cff63e230da546e3440d7a17450fd9a63443b` |

## 2. Evidence Base

This packet uses the following current reports as evidence. Their presence and hashes were checked; their checks were not all rerun here.

| Source | SHA-256 |
|---|---|
| `reports/SPS2-PROJECT-COMPLETION-BACKLOG-20261017.md` | `6596c14e818799450d056b432d26d47a198ba0404547c9c04e3f9e0e1c63b408` |
| `reports/SPS2-COMPLETION-C4-CODEX-REVIEW-20261017-121735.md` | `af327da22bcd3083edcfc24cda0a10c341fb6f34728bfa29e6be24e7acae581e` |
| `reports/SPS2-COMPLETION-C5-CODEX-AUDIT-20261017-123100.md` | `48094e11948ce84dd04864e95dcccf2d1eb34503f232899d901a6db04af3975c` |
| `reports/SPS2-COMPLETION-C8-CODEX-GOVERNANCE-AUDIT-20261017-1239.md` | `a95ce7e305578f111b17b9d3cf5a05c48ba9a552088ba997a963c9b0336c8070` |
| `reports/SPS2-COMPLETION-C9-CODEX-P10-READINESS-AUDIT-20261017-1243.md` | `1467b90f73e2523b7f1b97a2a6641eab63dcd6f521c658c3967ca4db78ed777d` |
| `reports/SPS2-COMPLETION-C10-CODEX-AUDIT-20261017-124611.md` | `07a89a23b9ab661f8acc715b415fe6e9527b77c3db1a41d828d5caff5aae04b7` |
| `reports/SPS2-COMPLETION-C11-CODEX-LEGACY-FINDINGS-AUDIT-20261017-125019.md` | `73b334ddb1b4b6919f1bbcff9605ed919ea6850b4da2af5c13809581191b20c5` |
| `reports/SPS2-COMPLETION-C12-RESIDUAL-ASSESSMENT-20261017-124804.md` | `58fa0ea96f9595c6306d9750e2b3b835f322df952604236d4f9ad4274a97c74b` |
| `reports/SPS2-COMPLETION-C13-CODEX-DOC-CONSISTENCY-AUDIT-20261017-1249.md` | `01422f475d3b75548633b1657491235751981bef56789ac1ed5c2d8a8d93fe85` |

Current C4–C13 audit states are `NEEDS_REVIEW`, with independent Claude cross-review pending. C6 and C7 remain `BLOCKED_USER`.

The disputed Round 26 record still contains `APPROVED / User` fields for DEC-7301/7302/7303. The correction sidecar says those fields are unauthenticated and repudiated, treats all three as **UNAPPROVED**, and preserves the subject record byte-for-byte. A decision-record field or manifest hash does not authenticate User approval.

## 3. Decision Queue

### D1 — C4 Package 4 correction scope

**Decision needed:** whether to authorize a bounded correction for the snapshot/rollback defects found in C4, and whether R-2 is included.

**Why:** C4 reports rollback ownership/symlink risks, snapshot publication/restore failure windows, restore-manifest allowlist gaps, partial mutation, and a duplicate `tearDown` warning. C12 recommends deferring scanner R-1 but narrowly fixing the regular-file snapshot-destination case.

**Options and consequences:**

1. **Approve narrow C4/R-2 correction:** reject non-directory or symlink snapshot destinations before moving anything; preserve the occupant; add focused tests. This removes one data-loss/residue path but does not make the larger rollback surface complete.
2. **Approve broader C4 correction:** address publication/restore windows, restore allowlisting, partial mutation, ownership/symlink boundaries, and test cleanup. This is safer but larger and requires a detailed implementation/review plan.
3. **Defer:** preserve known defects in reports. Rollback and snapshot guarantees remain incomplete and cannot support a readiness PASS.

**Blocked if no decision:** C4 remains unresolved; rollback/snapshot guarantees cannot be certified; related P10 readiness evidence remains incomplete.

**Evidence/authorization needed:** explicit approval of the selected scope; preservation baseline; focused tests; independent review. Do not bundle with Packages 2/3 or governance decisions.

### D2 — Packages 2/3 legacy-baseline policy

**Decision needed:** how to treat validator-visible legacy diffs caused by implementing installer SSH host-key verification (Package 2) and uninstaller path confinement (Package 3).

**Why:** `install.sh`, `install.ps1`, `uninstall.sh`, and `uninstall.ps1` are tracked/clean legacy paths protected by the current fail-closed validators. Editing them would create new `legacy modified:` failures in the validator matrix.

**Options and consequences:**

1. **Accept new legacy diffs:** authorize implementation and explicitly accept the resulting validator failures until a separately approved baseline/exception policy exists. Security fixes proceed, but validators remain red and cannot be presented as green.
2. **Amend/re-pin the legacy baseline or exception manifest:** authorize a precise, reviewed baseline change covering only the installer/uninstaller files needed. Validators can become coherent after implementation, but this is a governance/baseline change and must not conceal unrelated diffs.
3. **Do not implement:** retain fail-closed protection. Installer SSH and uninstaller path-confinement risks remain blocked.

**Blocked if no decision:** C6 and C7 remain `BLOCKED_USER`; installer/uninstaller remediation cannot proceed without weakening controls.

**Evidence/authorization needed:** explicit User choice of option; exact files/scope; tests; independent review; no real install/uninstall execution. Any baseline or manifest edit requires separate explicit authorization.

### D3 — DEC-7301: eight-path updater exception

**Decision needed:** ratify, reject, or amend the proposed fixed-baseline, content-and-mode-pinned exception for exactly eight DEC-7201 updater files.

**Why:** The implementation and manifest exist, but the disputed Round 26 approval is not valid evidence. The correction sidecar treats DEC-7301 as unapproved. C5 confirms the four foundation-validator failures are exactly the check-update mirror paths excluded by the manifest.

**Options and consequences:**

1. **Ratify as proposed:** preserve the eight-path exception and fail-closed behavior for all other legacy paths; the four check-update mirrors remain excluded and their validator failures require a separate decision.
2. **Amend:** define whether the four check-update mirrors are included, excluded, separately pinned, or otherwise handled. This may resolve the four foundation failures but must not silently add a ninth path or weaken integrity checks.
3. **Reject:** remove or disable the disputed exception through a separately authorized fail-closed transition. Legacy-diff failures and updater provenance remain unresolved until a replacement policy is chosen.

**Blocked if no decision:** DEC-7301 remains unapproved; four validator failures remain governance-dependent; updater exception adoption cannot be claimed.

**Evidence/authorization needed:** explicit User decision; fresh recompute of the eight paths, modes, hashes, manifest hash, and mirror states; independent review. Do not rely on the disputed approval fields.

### D4 — DEC-7302: four Home/P9 import groups

**Decision needed:** ratify, reject, or amend the proposed exception for exactly four Home-to-P9 file/module/symbol groups.

**Why:** The manifest and shared scanner exist, but DEC-7302 is unapproved. C8 reports eight manifest-approved imports and one dynamic violation at `sps2/tools/p10_runtime_gate.py:1944`. C4 also reports scanner residual and false-positive risks.

**Options and consequences:**

1. **Ratify as proposed:** recognize only the exact four groups; retain strict alias/duplicate/star/module/dynamic-import and path containment rules; amend P9 rollback semantics to acknowledge the owned dependency.
2. **Amend:** change the groups or scanner behavior only with a revised manifest and tests. This is a policy change and must preserve fail-closed behavior.
3. **Reject:** remove or disable the exception through a separately authorized transition. Home/P9 isolation and rollback behavior remain unresolved.

**Blocked if no decision:** DEC-7302 remains unapproved; the dynamic P10 import disposition remains blocked; rollback rehearsal cannot be declared successful.

**Evidence/authorization needed:** explicit User decision; fresh manifest/path/lstat/containment verification; positive and negative scanner tests; independent review. Manifest integrity is not approval.

### D5 — DEC-7303: historical decision-ID compatibility

**Decision needed:** ratify, reject, or amend compatibility-only acceptance of historical `D-P<phase>-*` identifiers.

**Why:** Current behavior is uneven: shared schema/checkers accept the DEC/D-P pattern, while `check_p2.py` remains DEC-only. DEC-7303 is unapproved, so this cannot be silently standardized.

**Options and consequences:**

1. **Ratify compatibility-only:** preserve historical IDs/provenance, require new IDs to use `DEC-####`, make schema and validators agree, and retain duplicate/approval checks without changing exit semantics.
2. **Reject:** restore DEC-only policy through an authorized schema/validator change, preserving historical records but potentially failing historical IDs.
3. **Amend:** define a different compatibility pattern or validator subset; require positive/negative and duplicate-ID tests.

**Blocked if no decision:** identifier policy remains inconsistent; any change would risk adopting the disputed proposal without authority.

**Evidence/authorization needed:** explicit User decision; current schema/validator/test inventory; positive, negative, malformed, and duplicate-ID cases; confirmation that exit-code semantics remain unchanged.

### D6 — Round 26 record and correction sidecar

**Decision needed:** select the final disposition of the disputed Round 26 subject record and the append-only correction sidecar.

**Why:** The subject record falsely attributes approval to the User. The sidecar preserves the subject record and repudiates that attribution, but it does not approve, reject, or replace the three proposals.

**Options and consequences:**

1. **Preserve both unchanged:** retain the historical record and correction sidecar as the current provenance boundary. This is safest but leaves the approval-shaped fields in the historical record.
2. **Preserve and annotate further:** add another explicitly authorized, append-only correction or pointer if additional clarification is needed. This avoids rewriting history but adds governance artifacts.
3. **Supersede via a properly authorized record:** create a new record that explicitly states the User's actual choices for D3–D5 and supersedes the disputed approval attribution. This is cleaner only after the User decides; it must not delete or rewrite the historical record.

**Blocked if no decision:** disputed attribution remains the controlling provenance boundary; any new artifact must continue to state DEC-7301/7302/7303 as unapproved.

**Evidence/authorization needed:** explicit User disposition and, for any new record, verbatim or precisely referenced User authorization. No agent may fabricate or infer approval.

### D7 — P10 dynamic-import disposition

**Decision needed:** remove/refactor, block, or explicitly except the dynamic `domain.seo.audit` import at `sps2/tools/p10_runtime_gate.py:1944`.

**Why:** The scanner reports it as a forbidden dynamic P9 import. It can make rollback fail after allowlisted P9 files are deleted, so converting it into a passing result without policy authority would hide a real boundary issue.

**Options and consequences:**

1. **Remove or refactor:** make the dependency explicit/static or otherwise eliminate the forbidden dynamic form. This is preferred if behavior can be preserved without an exception, but requires focused isolation and rollback tests.
2. **Retain and block:** keep the scanner/gate fail closed and document that P10 cannot pass until the dependency is resolved. This is truthful but blocks rollback rehearsal and P10 readiness.
3. **Explicit exception:** amend DEC-7302 or create a separately approved narrow exception. This requires the User to change policy; it must not be implemented as a silent scanner bypass.

**Blocked if no decision:** the scanner remains failing; rollback rehearsal cannot be certified; P10 readiness remains blocked.

**Evidence/authorization needed:** explicit policy choice; current dependency behavior; regression tests for isolation, rollback, and gate behavior; independent review.

### D8 — P10 readiness evidence and approval path

**Decision needed:** whether and how to proceed toward P10 readiness, including creation of authoritative missing evidence and eventual slice approval.

**Why:** The current gate is fail-closed at 9 PASS / 5 FAIL / 2 BLOCKED, exit 1. Current content is draft with `published_at: null`; slice `user_approval` is null. Missing prerequisites include authoritative publication/approval state, slice-ID history, authentic gate evidence, observed exposure/bind state, deployment-audit input, backend operations manifest, real build output, actual test execution, and rollback rehearsal. The gate also lacks explicit test-execution and rollback-rehearsal controls.

**Options and consequences:**

1. **Do not proceed:** preserve the current fail-closed boundary. P10 and release remain `NOT READY`; no evidence is fabricated.
2. **Prepare evidence only:** authorize implementation/evidence work while keeping publication and slice approval separate. Missing prerequisites can be supplied authentically, but readiness still cannot be claimed until all controls pass.
3. **Proceed to readiness:** authorize the bounded work, supply/authorize authoritative evidence, and request fresh slice approval only after every prerequisite genuinely passes. Publication/deployment remain separate and require their own authorization.

**Blocked if no decision:** P10 remains fail-closed; release readiness cannot truthfully become READY.

**Evidence/authorization needed:** explicit User decisions for evidence creation, publication, exposure, deployment-audit input, backend manifest creation, and slice approval. Authentic sources and fresh validation are required; placeholder or agent-authored claims are insufficient.

### D9 — Seven untracked test modules and CI coverage

**Decision needed:** whether the seven untracked test modules should become durable, CI-tested project assets.

**Why:** A clean checkout cannot run untracked files. Current committed CI discovers 28 tracked modules and checks a 28-module manifest; the following seven are absent from that durable coverage:

- `domain/frontend/tests/test_content_slots.py`
- `domain/frontend/tests/test_home_render.py`
- `domain/frontend/tests/test_layout_registry.py`
- `sps2/tests/test_check_update_safety.py`
- `sps2/tests/test_p10_runtime_gate.py`
- `sps2/tests/test_round26_governance_contracts.py`
- `sps2/tests/test_updater_safety.py`

**Options and consequences:**

1. **Track all seven and update CI discovery/manifest:** durable coverage improves, but CI and expected-module baselines change and later staging/commit/push authorization is required.
2. **Track selected modules:** coverage improves only for selected behavior; the remainder remains local-only and must be documented.
3. **Keep local-only:** preserve the current worktree but CI cannot verify these controls; local test counts cannot be treated as clean-checkout guarantees.

**Blocked if no decision:** CI coverage remains incomplete; any claim that these tests are protected by CI is false.

**Evidence/authorization needed:** explicit CI/baseline decision, module inventory, test counts/skips, and later separate staging/commit/push authorization.

### D10 — DEC-0001 versus push history

**Decision needed:** reconcile `DEC-0001`'s `KEEP_LOCAL_ONLY` decision with local reflog evidence of pushes.

**Why:** `origin` is configured, and local reflogs record three pushes to `main` and three to `build/roadmap-p3-completion`, including `c49f3852…` on 2026-10-16. The local-only wording remains in `.sps/STATE.md`. Reflogs show local ref updates, not who authorized each push.

**Options and consequences:**

1. **Amend DEC-0001:** authorize remote use under explicit identity/security/push conditions. Future pushes need separate authorization, and past-push provenance still needs disposition.
2. **Ratify past pushes as an incident exception:** record that the prior pushes are accepted while retaining or changing the going-forward policy. This requires actual User authorization and should preserve the historical discrepancy.
3. **Retain local-only going forward:** record the push history as a provenance incident and prohibit future pushes/remotes without new authorization. Remote cleanup, if desired, is a separate risky operation.

**Blocked if no decision:** governance remains contradictory; external publication readiness cannot be claimed; `DEC-0002` identity obligations remain tied to an unresolved premise.

**Evidence/authorization needed:** original authorization for each push if available; explicit User disposition; no live remote mutation. A read-only remote inspection may be proposed separately if needed.

### D11 — Attribution, self-approval, and P5 provenance

**Decision needed:** define acceptable approval attribution and resolve remaining authorization-traceability gaps.

**Why:** The current predicate accepts `Self (self-approved)` as User-attributable, while correctly rejecting known agent names. A string heuristic cannot authenticate a person. Separately, C11 did not locate a specific authorization source for P5 requirement/evidence edits; absence in inspected records does not prove no conversational authorization exists.

**Options and consequences:**

1. **Require stronger attribution:** reject self-asserted approval labels and require authenticated User evidence/date/provenance, while preserving legitimate surnames such as `Jane Self`. This improves trust but may invalidate records made under the current heuristic.
2. **Preserve current behavior:** accept the documented surname-preservation tradeoff and explicitly accept the residual false-attribution risk.
3. **Resolve P5 provenance separately:** User confirms authorization, supplies the original basis, or marks the edits unapproved/disputed. No historical record should be rewritten to manufacture authorization.

**Blocked if no decision:** approval provenance remains unreliable; historical governance gaps cannot be closed truthfully.

**Evidence/authorization needed:** explicit attribution policy, accepted legacy fields/date rules, and User confirmation or denial for the P5 edits. Schema/validator changes require separate authorization.

### D12 — User-owned settings provenance

**Decision needed:** resolve the provenance and intended content of `.claude/settings.json`.

**Why:** The worktree currently marks `.claude/settings.json` modified while the tracked baseline differs. Earlier reports described an empty worktree copy versus `{"enabledPlugins": {}}` at baseline; provenance was unexplained. The current file must be preserved until the User decides.

**Options and consequences:**

1. **Accept current worktree content:** preserve and later track/commit only with explicit authorization.
2. **Restore tracked baseline:** would discard current worktree content and requires explicit, narrowly scoped authorization after backup.
3. **Keep unresolved:** preserve the discrepancy and leave it outside release readiness.

**Blocked if no decision:** user-owned configuration provenance remains unresolved.

**Evidence/authorization needed:** User confirmation of intended content and provenance; fresh hash/status evidence; no blind overwrite.

## 4. Minimum Decision Set for Truthful Readiness

At minimum, the User should decide D2–D11 before a final readiness verdict. D1 and D12 are engineering/provenance decisions that should also be resolved, but D2–D11 directly govern the remaining implementation and P10/release boundary.

Until those decisions exist:

- DEC-7301, DEC-7302, and DEC-7303 remain **UNAPPROVED**.
- Packages 2 and 3 remain **BLOCKED_USER**.
- P10 remains fail-closed and **NOT READY**.
- The repository is not release-ready.
- No agent may force a failing gate green, fabricate evidence, rewrite historical records, stage, commit, push, deploy, publish, or alter CI.

## 5. Required User Authorization Statement

For any selected option, the User should state:

1. The decision ID(s) selected.
2. The exact option or amendment.
3. The exact authorized files/manifests/baselines, if applicable.
4. Whether staging, committing, pushing, publication, deployment, or remote inspection is authorized.
5. Whether each decision is one-time or standing.

General instructions to finish work do not override these explicit governance boundaries.
