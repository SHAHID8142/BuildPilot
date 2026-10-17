# SPS2 ROUND 15 — READ-ONLY VERIFICATION & RECONCILIATION AUDIT

Report time: 2026-10-16T17:57:20+06:00 (suffix 20261016-175720)
Role: independent repository auditor. Round 15 was **strictly read-only**:
every check below was an inspection, a read-only test run, or an in-memory
computation. The only file created is this report.

---

## 1. Executive summary

- The Round 14 gate-semantics implementation is **present and behaves as
  reported**. All six DEC-7112 semantics were independently re-inspected at
  source level and probed with adversarial read-only inputs. **No DEFECT
  found.** Two non-blocking observations are recorded (§4, §10).
- The real gate **FAILS honestly**: exit 1, `OVERALL: FAIL`, 9 of 16 required
  controls failing/blocked, 0 integrity problems, exactly as Round 14
  reported. Every remaining failure is a real, named prerequisite (draft
  content, no gate_record, null approval, null inventory digests, missing
  backend manifest, no history, no build, no observed bind).
- Test suites re-run clean: gate **308 OK**, renderer **36 OK**,
  slots+layout **49 OK**; governance validators emit **0 ERR lines**.
- Both canonical digests were **independently recomputed in memory** (a
  from-scratch reimplementation, not the gate's own helper) and match the
  gate's values exactly; recomputation is stable across runs. The stored
  inventory values are **null** — correctly failing closed, and correctly
  not written by this audit.
- The updater-safety workstream (8 tracked files + 1 untracked test module)
  was audited separately: the diffs are **safety-hardening** (dirty-tree
  refusal, removal of `git reset --hard` / `rm -rf` / `Remove-Item -Recurse`
  fallbacks, removal of bootstrap auto-update). Its 8-test suite passes
  (1 skipped: `pwsh` unavailable). **Its changes are NOT hereby approved,
  certified, or declared complete** — §8 records observations and limits.
- No discrepancy between the Round 14 report and the observed repository
  state was found, except one immaterial labeling nuance (§7, finding G-3).

## 2. Scope and authorization boundary

Authorized (executed): repository status/branch/HEAD/diff inspection; reading
Round 12–14 reports, decisions, schemas, evidence, slice, gate, renderer, and
test files; running existing local non-destructive test suites and read-only
validators; in-memory digest recomputation for comparison only; separate
inspection of the updater-safety workstream; creating exactly this one new
timestamped report.

Not authorized (and **not done**): any file edit outside this report; writing
digest values; changing `user_approval` or publication state; creating
evidence records or the backend manifest; any git state change (stage,
commit, push, fetch, pull, branch, stash, reset, revert); running installers,
updaters, bootstrap scripts, cleanup scripts, or network-dependent commands;
CI changes; auto-fixing findings.

Checks NOT RUN and why:
- **Updater/installer scripts were never executed** (e.g. `bash get-sps.sh`,
  `sps-update.sh --yes`, `install.sh`) — §1 forbids running commands that may
  reset, overwrite, delete, or quarantine files, and they perform network
  fetches. Their behavior was audited by diff/source inspection plus the
  workstream's own test module, which executes them only inside per-test
  temp directories against synthetic repositories.
- **`pwsh`-dependent test** skipped by the module itself (`pwsh` unavailable
  on this machine) — recorded, not a failure.
- No CI inspection beyond reading repo files (no CI changes authorized to
  evaluate by execution).

## 3. Worktree status (initial and final — identical except this report)

VERIFIED FACT — captured at audit start and re-captured at audit end:

| Item | Value |
|---|---|
| Branch | `build/roadmap-p3-completion` (matches expected) |
| HEAD | `c49f3852e1c31d0136269c80fe58201b059af3ec` (short `c49f385` — matches the reported baseline; not assumed, verified via `git rev-parse`) |
| Staged files | **0** (start and end) |
| Stashes | **0** |
| Porcelain entries | 32 (start) → 32 (end, +1 report line inside the already-untracked `reports/` dir, which is a single untracked entry either way) |
| Modified tracked files | 16: `.claude/settings.json`, `.sps/audits/README.md`, the 8 updater-script files, `sps2/decisions/P10-DECISIONS.json`, `sps2/evidence/P5-EVIDENCE.json`, `sps2/governance/attribution.py`, `sps2/requirements/P10-SECTION-INVENTORY.json`, `sps2/requirements/P5-REQUIREMENTS.json`, `sps2/schemas/p10-slice.schema.json` |
| Untracked | `.sps/evidence/P17/`, `.sps/tasks/p17/`, `AUDIT-SPEC2-GIT-REMOTE-AND-PUSH-DISCREPANCY.md`, `domain/cms/data/`, `domain/frontend/`, `reports/`, 6 decision/evidence/slice files, `sps2/tests/test_p10_runtime_gate.py`, `sps2/tests/test_updater_safety.py`, `sps2/tools/p10_runtime_gate.py` |

Round 14 status claims re-verified against reality:
- `sps2/tools/p10_runtime_gate.py` and `sps2/tests/test_p10_runtime_gate.py`
  are **untracked** — VERIFIED (both appear as `??` in porcelain).
- `domain/backend/operations.json` does **not exist** (`ls domain/backend/`
  → "No such file or directory") — consistent with the gate's honest
  req-p10-07 FAIL.
- The updater workstream is **8 modified tracked files** (verified by
  `git diff --stat -- <paths>`: 161 insertions, 63 deletions across
  `get-sps.ps1/.sh`, `scripts/bootstrap-sps.sh`, `scripts/sps-update.sh`,
  `scripts/update-sps.ps1`, and their three `skills/sps/scripts/` mirrors)
  plus untracked `sps2/tests/test_updater_safety.py` (211 lines) — matches
  the Round 14 report's count, re-verified rather than assumed.

## 4. Round 14 implementation findings — six semantics, individually

All findings cite `sps2/tools/p10_runtime_gate.py` (gate) or
`sps2/tests/test_p10_runtime_gate.py` (tests). Each was verified by source
inspection AND independent read-only probes with inputs the test suite does
not contain.

### A. evidence-freshness — VERIFIED
- Offset requirement: `_parse_rfc3339_utc` (:2056) rejects `None` on
  timezone-naive input (:2073-2074). Probed: `Z` → parsed; `+06:00` →
  correctly normalized to UTC; bare `2026-10-16T12:00:00` → **None (rejected)**;
  empty/None/non-string/invalid-calendar (`2026-13-45T99:99:99Z`) → None;
  fractional seconds accepted. VERIFIED.
- No maximum-age window: the control body (:2149-2193) contains no age
  comparison; PASS detail states the policy. Probed: the dated fixture's
  PASS path involves only parseability. Consistent with the explicit Round 14
  authorization. VERIFIED.
- `timestamp` fallback honored (real evidence record uses `timestamp: "2026-10-16T17:00:00+06:00"`, :12 of P10-EVIDENCE.json). VERIFIED.
- Minor observation (non-blocking): `_gate_now()` (:2078) is **dead code** —
  defined "so tests can freeze the clock" but never called, because with no
  maximum-age window no clock comparison exists. Harmless; removing it would
  be an edit (not authorized). Labeled: OBSERVATION.

### B. evidence-authenticity — VERIFIED
- `gate_record` required per record; absence → FAIL "existence is not
  authenticity" (:2263-2271). VERIFIED (source + real gate output).
- SHA-256 recomputation over every claimed `inputs`/`outputs` entry;
  contradiction FAILs naming record, field, claimed and actual values
  (:2259-2262). VERIFIED (source + tamper tests).
- Path resolution: claimed paths resolve against the slice document's
  directory (`origin`, :2224) and are bounded by `_canonical_within`
  (realpath on both sides — defeats `../` traversal AND symlink escape,
  :1136-1153). Probed: absolute path `/etc/hosts` → FAIL "outside the
  allowed root"; `../../../../etc/hosts` → FAIL "outside"; symlink pointing
  outside the root → FAIL "outside"; symlink resolving **inside** the root
  with a matching digest → PASS (realpath containment is the boundary, and
  the digest still has to match the link target's bytes). VERIFIED.
- Malformed locators (blank path), unreadable/missing files, foreign
  algorithm prefixes (`md5:…`), non-string/null claims, case-mismatched
  prefix (`SHA256:…`) all fail. VERIFIED by probe.
- Duplicate JSON keys in a hand-written evidence file: Python's `json.loads`
  silently last-wins, so only the surviving claim is cross-checked. Probed:
  the surviving (wrong) claim was still caught and FAILed. Labeled:
  OBSERVATION (non-blocking) — the cross-check cannot see a claim that
  duplicate-key parsing erased, but any surviving contradiction still fails.
- Content integrity vs cryptographic authenticity: PASS detail states "NOT
  cryptographic authenticity (no signatures, no trust root)" (:2281-2282);
  UNRESOLVED_SEMANTICS entry 2 (:93-96) records the same. No trust root
  exists in the repository. VERIFIED — the distinction is preserved, not
  collapsed.

### C. cms-state-digest — VERIFIED
- Canonicalization: `json.dumps(sort_keys=True, ensure_ascii=False,
  separators=(",",":")).encode("utf-8")` (:1990-1999) — sorted keys, UTF-8,
  no insignificant whitespace. Independently reimplemented in this audit's
  probe and produced identical values. VERIFIED.
- File membership: exactly `content.json`, `content_types.json`,
  `revisions.jsonl` under `domain/cms/data/` (:2130-2138), each combined
  with its repo-relative realpath so identical contents in two files cannot
  cancel (:2051-2052). VERIFIED.
- JSONL parsing: line-delimited, blank lines skipped, malformed line →
  fail-closed with line number (:2027-2046). VERIFIED (this was the Round 14
  bug fix; re-verified against the real `revisions.jsonl`, which parses).
- Null → FAIL (:2294-2300); mismatch → FAIL naming both values (:2304-2310).
  VERIFIED (source + real gate output: stored null → FAIL).

### D. p8-contract-digest — VERIFIED
- Input set: exactly `content_types.json` (:2141-2146). Disjointness from
  the CMS set verified: p8 ⊂ cms (proper subset, single file) — a content
  edit changes only the cms digest; a type-contract edit changes both,
  which is the intended asymmetry ("content edit does not invalidate the
  type contract" — the reverse direction is necessarily coupled since the
  contract file is also CMS state). VERIFIED as matching the adopted design.
- Null → FAIL; mismatch → FAIL. VERIFIED (source + real gate output).

### E. req-p10-07-reconciliation — VERIFIED
- Manifest path `domain/backend/operations.json` (:1987, :2371); missing
  manifest → FAIL (fail-closed) — VERIFIED against reality (file absent,
  gate output FAILs).
- Probed edge cases: malformed JSON → FAIL; valid JSON but `operations` not
  a list → FAIL; non-dict/non-name entries → FAIL ("N manifest operation(s)
  carry no usable name"); **duplicate manifest names** → FAIL (set semantics
  collapse the duplicate AND the malformed-count catches the second entry:
  probe showed "manifest operations absent from declaration: ['op-a']; 1
  manifest operation(s) carry no usable name" — the duplicate is never
  silently accepted); empty-vs-empty (existing manifest, empty declared) →
  PASS exactly as the adopted design specifies; phantom declared ops → FAIL
  (test-covered); undeclared manifest ops → FAIL (test-covered). VERIFIED.
- Honesty limit stated in the PASS detail: "self-declared code… consistency,
  not real-world completeness" (:2402-2404). VERIFIED.

### F. approval-state-interaction — VERIFIED
- Full matrix probed (9 combinations):
  - `COMPLETE_VERIFIED_USER_APPROVED` + null approval → **FAIL** ("a gate
    pass alone is never sufficient") — the design's key negative case.
  - terminal + set approval whose basis contains "fresh" → PASS (coherence
    only, with explicit UQ-ATT-2 caveat in the detail).
  - terminal + set approval, basis lacking "fresh" (e.g. bare D-P10-8
    carry-over) → **FAIL** — APPROVAL-MECHANISM: OPTION A enforced.
  - terminal + approval missing `basis` → FAIL. terminal + non-object
    approval → FAIL.
  - non-terminal states (`COMPLETE_AWAITING_USER_APPROVED`,
    `INCOMPLETE_PLANNING`, unknown/None) + null approval → PASS (coherent
    pre-transition).
  - non-terminal + set approval → **FAIL** (incoherent).
- Read-only: AST scan of the whole gate module found **zero** write-call
  sites (`write`, `writelines`, `write_text`, `remove`, `unlink`, `rmtree`,
  `rename`, `mkdir`, `makedirs`) — the gate performs no filesystem writes
  at all, so it cannot create or modify approval state. VERIFIED.
- No User approval was fabricated or applied by this audit: `user_approval`
  remains `null` in the slice (:51) and inventory (:12). VERIFIED.

## 5. Test commands and actual results (all re-run this audit)

| Command | Result | Exit |
|---|---|---|
| `python3 -B -m unittest sps2.tests.test_p10_runtime_gate` | **Ran 308 tests, OK** (recounted; matches Round 14's claim) | 0 |
| `python3 -B -m unittest domain.frontend.tests.test_home_render` | **Ran 36 tests, OK** | 0 |
| `python3 -B -m unittest domain.frontend.tests.test_content_slots domain.frontend.tests.test_layout_registry` | **Ran 49 tests, OK** | 0 |
| `python3 -B -m unittest sps2.tests.test_updater_safety -v` | **Ran 8 tests, OK (skipped=1** — `pwsh` unavailable**)** | 0 |
| `python3 -B sps2/tools/check_sps2.py evidence sps2/evidence/P10-EVIDENCE.json` | 0 ERR lines | 0 (validator always exits 0; stdout inspected) |
| `python3 -B sps2/tools/check_sps2.py decision` × 3 (ADOPTION, ROUND12, DELEGATED) | 0 ERR lines each | 0 |

INFERENCE (evidence, not proof): the suites passing supports the
implementation's correctness but does not prove complete coverage; the
probes in §4 covered edge cases beyond the suite (absolute paths, symlinks,
duplicate manifest names, the nine-cell approval matrix).

## 6. Real gate output and control-by-control results

Command: `python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json`
→ **exit 1**; `OVERALL: FAIL (required controls failing: 9; integrity
problems: 0; required controls: 16)`. JSON payload re-parsed to recount
(16 controls; 5 `unresolved_semantics`; no integrity problems). Recounted
from actual current output — not carried over from Round 14:

| Control | Result | Honest-failure check |
|---|---|---|
| schema-structural | PASS | — |
| slice-required-fields | PASS | — |
| evidence-references | PASS | — |
| layout-slot-conformance | PASS | — |
| published-only-content | **FAIL** | ✓ draft content / publication precondition still fails |
| exposure-declaration | BLOCKED | ✓ no observed bind |
| slice-id-uniqueness | FAIL | ✓ no authoritative history |
| evidence-freshness | PASS | (genuine: real record is offset-dated) |
| evidence-authenticity | **FAIL** | ✓ EV-P10-001 carries no gate_record |
| inventory-preconditions | PASS | — |
| approval-authenticity | **FAIL** | ✓ approval null |
| p9-deployment-audit | BLOCKED | ✓ no build directory |
| cms-state-digest | **FAIL** | ✓ stored digest null |
| p8-contract-digest | **FAIL** | ✓ stored digest null |
| req-p10-07-reconciliation | **FAIL** | ✓ backend manifest absent |
| approval-state-interaction | PASS | (genuine: coherent pre-transition state) |

The gate did not pass and was not made to pass. VERIFIED FACT.

## 7. Read-only digest recomputation (§5 of the mission)

Method: a **from-scratch reimplementation** of the contract in the audit
probe (canonical JSON sorted keys/UTF-8/no-whitespace; JSONL line-parsed;
each file combined with its repo-relative path; SHA-256 → `sha256:<hex>`) —
not a call of the gate's own helper — then cross-checked against the gate
helper. All computed in memory; **nothing written anywhere**.

- `cms_state_digest` = `sha256:b35f7aba68eca4e7c9b688ae979891330f2f3d08c2b4250ce855c55943f7e38e`
  over `domain/cms/data/{content.json, content_types.json, revisions.jsonl}`.
- `p8_contract_digest` = `sha256:ee6bb68f04f0eb468f0fd6eafaaea0b68639b88199e207c7a76ef57e10bbf217`
  over `domain/cms/data/content_types.json`.
- Reproducible: stable across repeated runs; independent reimplementation
  and gate helper agree on both values. VERIFIED.
- Input sets disjoint as intended: VERIFIED (p8 set is the single contract
  file; cms set is the three state files).
- Stored values: `provenance.cms_state_digest` = **null**,
  `provenance.p8_contract_digest` = **null** (P10-SECTION-INVENTORY.json
  :9-10). Status: **null → the controls fail closed, correctly.** No
  mismatch exists to report because nothing is recorded yet.
- Missing files/ambiguity: none encountered; all three CMS files parse.
- The recomputed values appear in this report as audit evidence only; they
  were **not** written to the inventory, evidence, decisions, or any other
  file (writing them requires separate authorization; DEC-7112 explicitly
  withholds it).

## 8. Updater-safety workstream — separate audit findings

Treated as an independent workstream; **nothing here implies approval,
completeness, safety certification, or authorization.** Audited by diff and
source inspection only (execution NOT RUN — see §2).

VERIFIED FACTS (from `git diff`):
1. **Auto-update-on-bootstrap removed**: both `bootstrap-sps.sh` copies lost
   the session-start block that ran `check-update.sh` and auto-applied
   `sps-update.sh --yes` when an update was available.
2. **Destructive fallbacks removed**: `git reset --hard origin/$BRANCH`
   after a failed `pull --ff-only` is gone from all three updaters (bash ×2
   mirrors + PowerShell); `rm -rf "$REPO_DIR"` before clone is gone from
   both bash installers/updaters; `Remove-Item -Recurse -Force $repoDir` is
   gone from the PowerShell updater.
3. **Dirty-tree preservation added**: bash and PowerShell updaters now run
   `git status --porcelain=v1` first and **refuse to update** (exit 1) when
   local changes exist or the worktree cannot be verified; a non-git
   destination is refused rather than deleted ("preserve me" semantics).
4. **Failure paths no longer mutate**: fetch/checkout/pull failures now exit
   with "source left unchanged" instead of falling back to reset.
5. Mirror parity: `scripts/sps-update.sh` and
   `skills/sps/scripts/sps-update.sh` are byte-identical (diff-verified),
   as are the bootstrap mirrors.

Test module `sps2/tests/test_updater_safety.py` (8 tests, all pass, 1
skipped for missing `pwsh`):
- **Behavioral, not just textual**: 4 tests execute `get-sps.sh` /
  `sps-update.sh` (via `subprocess`, 15s timeout) inside per-test temp dirs
  against synthetic dirty repositories and non-git destinations, asserting
  non-zero exit, the refusal message, and that the sentinel file survives.
  The dirty-source and non-git-destination refusals are genuinely exercised
  end-to-end. VERIFIED.
- 3 tests are textual scans asserting the absence of `git reset --hard`,
  `rm -rf "$REPO_DIR"`, and `Remove-Item -Recurse -Force $repoDir` — weaker
  (a string scan can be evaded), but they complement, not replace, the
  behavioral tests. OBSERVATION.
- Side effects/network: behavioral tests set `HOME`/`PATH`/`SPS_REPO_DIR`
  into temp dirs, fake `node`/`npx` on `PATH`, and the refusal happens
  **before** any network call (test names say so; the diff's guard sits
  before the fetch/clone blocks). The PowerShell dirty-source test is
  skipped here (no `pwsh`). One test runs `git init` — inside a temp dir
  only. No test touches the real repository state or reaches the network
  before the refusal point. VERIFIED within the limits stated.

Specific risk items from the mission checklist:
- Automatic update execution: **removed** from bootstrap (was present at
  HEAD); `sps-update.sh --yes` still exists as an explicit user-invoked
  auto mode, and `install.sh --yes` is invoked by the updater after the
  source update (unattended-install flag present in that path — flagged as
  an OBSERVATION for the workstream's own review; not audited further
  because `install.sh` itself is unmodified at HEAD and out of diff scope).
- `git reset --hard` / destructive recursive deletion / fallback cleanup:
  **absent** from all diffs (asserted by the textual tests too).
- Dirty-tree checks / preservation: **present**, behaviorally tested.
- Backup/recovery behavior: **none exists** — the new posture is
  refuse-and-leave-unchanged rather than backup-then-proceed. Acceptable
  but worth the User knowing: there is no rollback path if an update itself
  misbehaves after a clean tree is accepted. OBSERVATION.
- Global installation overwrite/consent: out of audited diff scope
  (`install.sh` unmodified); NOT VERIFIED.
- Unsafe `GIT_SSH_COMMAND` settings: **none found** in any audited file.
- Disabled Git clone protection (`safe.directory` etc.): **none found**.
- Unattended npm flags: `node`/`npx` are only *required/preconditioned*
  (`have node || have npx` check); no `npm install -g` or `-y` npm flag
  found in the audited diffs. NOT VERIFIED for `install.sh` (unmodified,
  out of scope).

Suggested next actions for this workstream (for the User/workstream owner;
**not executed here**): (a) run the suite on a machine with `pwsh` to cover
the skipped PowerShell behavioral test; (b) decide whether the textual
no-reset assertions should also cover `git checkout -- .`, `git clean`, and
`git restore`; (c) record a decision-record for the workstream (currently no
governance record covers these eight modified tracked files — see §9, G-1).

## 9. Governance and scope check

- **Publication deferred**: VERIFIED — Round 12 transcription record carries
  `PUBLICATION: DEFER` verbatim; CMS content still `draft` (probe: slice
  `required_status: "published"` is the build bar, not a publication claim;
  gate still FAILs published-only-content).
- **`user_approval` null**: VERIFIED — null in slice (:51), inventory (:12);
  no approval record created anywhere this audit.
- **Inventory digest writes require separate authorization**: VERIFIED —
  DEC-7112 `explicitly_not_approved_by_this_record` still lists it; values
  remain null; this audit computed but did not write them.
- **Backend manifest creation not authorized**: VERIFIED — directory and
  file absent; no attempt made.
- **Commit/push not authorized**: VERIFIED — 0 staged, 0 stashes, HEAD
  unchanged start-to-end.
- **Gate read-only**: VERIFIED — AST-level zero write-call sites (§4F).
- **DEC-7112 authenticity limitations in force**: VERIFIED —
  `standing_bounds.authenticity_limit` intact; gate's UNRESOLVED_SEMANTICS
  entry 2 and PASS details restate it.
- **One authorization ≠ adjacent authorization**: no decision record was
  amended; no authorization inferred beyond Round 15's own text.

Discrepancies found:
- **G-1 (NEEDS CLARIFICATION, workstream-level):** the 8 modified tracked
  updater files and untracked `test_updater_safety.py` have **no governance
  record** authorizing their modification (no decision record in the
  untracked decision set covers them; `sps2/decisions/P10-DECISIONS.json` is
  modified but its diff concerns P10, not installers). This is a governance
  gap for that workstream, not for P10 — documented, not reconciled.
- **G-2 (VERIFIED, informational):** `sps2/requirements/P10-SECTION-INVENTORY.json`
  shows a 95-line diff vs HEAD. This predates this session's work (present
  in the session-start snapshot) and belongs to the pre-existing user
  modification set; its digests are null and its state is
  `COMPLETE_AWAITING_USER_APPROVAL` — consistent with all Round 12–14
  records. No action taken.
- **G-3 (VERIFIED, immaterial):** the Round 14 report's §8 said "8 modified
  tracked files… appear modified… not this round's work." The count is
  correct for the updater set specifically, but the total modified-tracked
  count is 16 (8 updater + 8 pre-existing SPS2-side). The Round 14 wording
  could be misread as 16; the underlying facts it reports are accurate.
  Documented here rather than editing the Round 14 report (reports are
  never overwritten).

## 10. Findings ranked by severity

No DEFECT-severity finding was identified in the Round 14 implementation or
the P10 governance state.

1. **MEDIUM (governance gap, other workstream):** G-1 — updater-safety
   changes to 8 tracked files exist with no recorded authorizing decision.
   Files: `get-sps.ps1/.sh`, `scripts/{bootstrap-sps.sh,sps-update.sh,update-sps.ps1}`,
   `skills/sps/scripts/{bootstrap-sps.sh,sps-update.sh,update-sps.ps1}`,
   `sps2/tests/test_updater_safety.py`. Needs a User decision (ratify or
   revert) before any commit authorization.
2. **LOW (coverage):** PowerShell behavioral test skipped where `pwsh` is
   absent (`sps2/tests/test_updater_safety.py:177`); textual-scan tests
   (:161-175) are evadable. Suggested additions in §8.
3. **LOW (dead code):** `_gate_now()` unused (`p10_runtime_gate.py:2078`);
  harmless; removal would be an edit (not authorized in a read-only round).
4. **LOW (parsing semantics):** duplicate JSON keys in a hand-edited
   evidence file are last-wins before the authenticity cross-check sees
   them (`json.loads` behavior; gate :2108). Surviving contradictions still
   fail; a fully deterministic parser is a possible future hardening.
5. **OBSERVATION (by design, needs User action to lift):** the six honest
   gate failures (§6) each map to a withheld authorization: publication,
   gate-record emission for real evidence, fresh User approval, inventory
   regeneration, backend manifest, slice-id history source.

## 11. What remains unresolved

- All five `UNRESOLVED_SEMANTICS` entries (locator grammar; no trust root →
  content-integrity only; self-declared human attribution / UQ-ATT-2;
  manifest absent; transition requires an authorized tool run).
- The six honest gate FAIL/BLOCKED prerequisites (§6 table).
- UQ-ATT-2 (a `decided_by: "User"` field does not authenticate a human).
- CONF-001 and other pre-existing open items untouched this round.
- The updater-safety workstream's authorization status (G-1).
- Whether/when to regenerate the inventory with the two recomputed digest
  values (values exist only in this report's §7 as audit evidence).

## 12. Recommended next actions (none executed; each labeled)

**Requiring separate User authorization:**
1. Ratify or reject the updater-safety workstream via a decision record
   (resolves G-1) before any commit grant.
2. Authorize an inventory regeneration to write the two recomputed digests
   (lifts 2 gate FAILs) — the values are in §7; the write itself is
   explicitly withheld by DEC-7112 until granted.
3. Publication decision (still DEFER) — lifts `published-only-content`.
4. Fresh explicit User approval act at actual completion
   (APPROVAL-MECHANISM: OPTION A) — lifts `approval-authenticity`; never to
   be manufactured by an agent.
5. Commit/push grant for the accumulating untracked P10 work (still
   `NOT AUTHORIZED`; survives only in the working tree).

**Not requiring new authorization (for a future implementation round):**
6. Emit a `gate_record` (sps2.p10-gate-record/v1) inside real evidence
   records when the harness produces real evidence — the format is now
   implemented and cross-checked; authoring real evidence is part of the
   already-specified harness work.
7. Remove the dead `_gate_now()` and optionally harden duplicate-key
   parsing (trivial code changes requiring an implementation grant).
8. Upstream suggestions to the updater workstream (§8 items a–c) — for that
   workstream's owner; this audit expresses no approval of them.

## 13. Side-effect verification

- Git: HEAD identical before/after (`c49f3852…`); staged count 0→0; stash
  count 0→0; porcelain entry count 32→32 (the only new file is this report,
  inside the already-untracked `reports/` directory). No fetch, pull, push,
  branch, switch, reset, revert, clean, or stash was executed.
- Files: the audit created exactly one file — this report. No source, test,
  decision, schema, inventory, evidence, CMS, configuration, or governance
  file was modified. Digest computations were in-memory only; probes ran in
  `tempfile.mkdtemp()` sandboxes (self-cleaned by the OS/user temp policy;
  no repository path touched).
- Tests/validators executed are read-only (verified by the suite's own
  `TestNoRepositoryMutation` passing and by the validators' design); the
  updater-safety suite was run but touches only its own temp fixtures.
- File permissions and line endings: untouched (no `chmod`, no writes).

---

*Round 15 consumed exactly: read-only verification and reconciliation. The
gate still honestly fails; nothing was fixed, approved, staged, committed,
published, or regenerated. Awaiting the User's next instruction.*
