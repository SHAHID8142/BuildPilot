# SPS2 ROUND 17 — R15 DEFECT RESOLUTION & CONTINUED ENGINEERING

Report time: 2026-10-16T18:22:29+06:00 (suffix 20261016-182229)
Mission: continue the SPS2 engineering mission — resolve R15 findings R15-001/002/003
(P10 gate), R15-004/007/008 (updater safety), complete the installer
backup/restore analysis, verify everything offline, and report. No commit,
push, publication, approval, or backend-manifest action authorized or taken.

**Important provenance note.** During this round it became evident that most
of the Priority-1 and Priority-2 fixes were already present in the working
tree before this session's first edit: the gate tool's mtime was 18:14 and
the test module's 18:19, while this round began ~18:20. Another session or
agent working the same mission evidently applied the core fixes in the
minutes between the Round 16 report (18:06) and this round's start. This
round therefore **independently verified every fix at source and behavioral
level** (rather than assuming them), completed the two fixes that were still
missing, ran the full verification battery, and reports the combined state.
No work is claimed that this session did not perform or verify.

---

## 1. Priority 1 — P10 gate and schema (R15-001, R15-002, R15-003): RESOLVED

All three defects are fixed in `sps2/tools/p10_runtime_gate.py` and covered
by tests in `sps2/tests/test_p10_runtime_gate.py`. Each was verified by
direct probe this round, not assumed.

### R15-001 — schema/gate operations type divergence: RESOLVED (VERIFIED)

The adopted contract (Round 12 decision package §5.5, adopted by DEC-7112;
schema `sps2/schemas/p10-slice.schema.json` `state_changing_operations.items`)
defines declared operations as **objects** with required `operation`
(non-empty string) and `required_controls` (non-empty unique enum array).
The gate's reconciliation now follows the schema:

- `sps2/tools/p10_runtime_gate.py:2411-2421` — declared entries are read as
  objects: `operation.get("operation")` with `_nonblank` validation;
  non-object entries and unusable names are collected as
  `malformed_declarations` instead of being compared as strings.
- Manifest side unchanged and correct: `operations[].name` at
  :2433-2443.
- Probe (this round): declared
  `[{"operation":"save","required_controls":["AUTHENTICATION"]}]` vs manifest
  `{"operations":[{"name":"save"}]}` → **PASS** with
  `declared state_changing_operations=['save'] matches the manifest's ['save']`.
  The R15 probe's spurious FAIL (`manifest operations absent from
  declaration: ['save']`) is gone.

One representational nuance was checked and is genuinely **not ambiguous**
under the adopted contract: the schema's `required_controls` field is part
of the *declaration* contract (what controls the operation requires), while
the manifest side compares by *name* only. The reconciliation set-compare is
name-based per DEC-7112 design #5 ("set-compare declared vs manifest");
`required_controls` is schema-validated, not reconciled. No policy was
invented; the object-vs-string question has exactly one adopted answer
(objects), now enforced.

### R15-002 — incomplete gate records accepted: RESOLVED (VERIFIED)

`check_evidence_authenticity` now enforces the full documented gate-record
contract (`sps2/tools/p10_runtime_gate.py:2232-2254`):

- required non-blank fields: `schema`, `producing_command`,
  `emitting_tool_version`, `utc_timestamp` (:2236-2238);
- `schema` must equal `sps2.p10-gate-record/v1` exactly (:2240-2243);
- `utc_timestamp` must be a parseable RFC 3339 timestamp **whose raw text
  ends in `Z`/`z`/`+00:00`/`-00:00`** (:2245-2250) — a literal-zero-offset
  requirement, so `2026-10-16T06:00:00+06:00` FAILS even though it denotes
  the same instant as `2026-10-16T00:00:00Z`. This matches the field's name
  (`utc_timestamp`) and the test contract
  (`test_utc_timestamp_must_be_parseable_and_zero_offset`,
  `sps2/tests/test_p10_runtime_gate.py:2109-2118`). Note the earlier
  implementation wrote the check as
  `parsed.astimezone(utc).utcoffset() != timedelta(0)`, which is **vacuous**
  (always false after conversion) — the raw-suffix check is the real
  enforcement;
- at least one usable `inputs`/`outputs` digest claim
  (`claims_present`, :2252-2265, enforced at the tail of the loop).

Probes (this round): a `gate_record` with only `{"inputs": {...}}` → **FAIL**
"missing schema, producing_command, emitting_tool_version, utc_timestamp";
`+06:00` timestamp → **FAIL**. The R15 probe's spurious PASS is gone.

### R15-003 — malformed declared operations silently ignored: RESOLVED (VERIFIED)

- `sps2/tools/p10_runtime_gate.py:2444-2450` — any
  `malformed_declarations` or `malformed_manifest_entries` → **FAIL**
  "REQ-P10-07 malformed operation entries (fail-closed)" naming each entry
  and index.
- Probe (this round): declared `["save"]` (string, not object) against a
  valid manifest → **FAIL** with "malformed operation entries". The R15
  probe's silent-omission PASS is gone.
- The dead mid-function reference `if malformed:` at the old :2462 (a
  `NameError` reachable whenever a delta existed) and the stale
  `declared_ops`/`manifest_ops` PASS-detail references are **gone**; the
  delta branch (:2456-2464) and PASS detail (:2465-2471) now use
  `declared_names`/`manifest_names` consistently.

### Real-gate impact

None of the three fixes changes the real gate's verdict: the Home slice's
`state_changing_operations` is `[]` and EV-P10-001 has no `gate_record`, so
`req-p10-07-reconciliation` still FAILs (manifest absent, fail-closed) and
`evidence-authenticity` still FAILs (no gate_record to check) — both
correctly. The fixes close *latent* fail-open paths for the first nonempty
backend operation and the first real evidence record.

## 2. Priority 2 — updater safety (R15-004, R15-007, R15-008): RESOLVED

### R15-004 — PowerShell network check before safety refusal: RESOLVED (VERIFIED)

`scripts/update-sps.ps1:38-54` (and its byte-identical mirror
`skills/sps/scripts/update-sps.ps1`) now perform the full safety gate —
dirty-worktree refusal, unverifiable-worktree refusal, non-git-destination
refusal — **before** `Checker` is invoked (:56-65). Ordering verified by
source inspection and by the new regression test
`test_powershell_updater_checks_source_safety_before_update_network`
(`sps2/tests/test_updater_safety.py:188-199`), which asserts the refusal
strings appear before the offline message in both mirror copies. Bash
ordering was already correct and gained its own ordering test
(`test_bash_updater_checks_source_safety_before_network`, :168-170).

### R15-007 — "destination left unchanged" overstatement: RESOLVED (VERIFIED, completed this round)

- `scripts/update-sps.ps1:118` + mirror already carried the corrected
  message ("the destination may be partially created. Inspect it and remove
  it manually if needed."), covered by
  `test_powershell_clone_failure_does_not_claim_destination_is_unchanged`.
- **Fixed this round:** `get-sps.ps1:75` still said "Clone failed;
  destination left unchanged." — Git clone can leave a partial directory.
  Changed to the same accurate wording as the updater. The regression test
  was extended to cover `get-sps.ps1` (now iterates
  `(PS_UPDATER, MIRROR_PS_UPDATER, PS_BOOTSTRAP)`,
  `sps2/tests/test_updater_safety.py:201-206`). Note `get-sps.ps1` has **no
  mirror** under `skills/sps/scripts/` (verified by listing); it is the
  standalone remote-fetch bootstrap, so no parity copy was needed.
- `get-sps.sh` has no clone-failure claim at all (`git clone` failure falls
  through to `set -euo pipefail`); nothing to fix there.

### R15-008 — unchecked `cd "$REPO_DIR"`: RESOLVED (VERIFIED)

`scripts/sps-update.sh:140-143` + byte-identical mirror now guard the
reinstall entry: `if ! cd "$REPO_DIR"; then bad "Cannot enter the updated
source directory; reinstall stopped."; exit 1; fi`. Covered by
`test_bash_updater_stops_on_source_directory_change_failure`
(`sps2/tests/test_updater_safety.py:172-177`), which asserts the guard and
message in both bash mirrors. PowerShell equivalent was already safe
(`Set-Location` under `$ErrorActionPreference = "Stop"`).

### Mirror parity and test coverage

- `diff -rq scripts skills/sps/scripts` → identical (all three mirror pairs
  byte-identical; also asserted by
  `test_updater_mirrors_are_byte_identical`, :208-215).
- Updater suite is now **13 tests, 12 OK / 1 skipped** (`pwsh` unavailable —
  R15-006's runtime-coverage gap remains structurally open on this machine;
  the skip is recorded, not hidden).
- R15-006 residual (NOT fully resolved, by limitation): PowerShell checks
  beyond the ordering/clone-message assertions are still partly textual, and
  the behavioral PowerShell test remains `pwsh`-gated. `pwsh` is not
  installed here; this is an environmental limit, not a code defect.

## 3. Priority 3 — installer backup/restore analysis (R15-005): ANALYZED; PROPOSED, NOT IMPLEMENTED

**Decision: no source change.** `install.sh` and `install.ps1` are **not**
in the DEC-7201 ratified set (verified: the ratification names the eight
updater files + the test module only) and the installer global-write policy
is an explicitly **deferred** workstream (R15 report §3.3 finding R15-005;
"Modifying installer global-write/backup behavior requires explicit User
authorization"). The mission's own rule applies: changes affecting the
deferred global installer-write policy get a detailed patch proposal, source
unchanged.

**Verified current behavior (unchanged from R15 findings):**
- `install.sh:249-269` (`sync_core_skill`): for each sync root,
  `rm -rf "$dest_root/sps"` then `cp -R`; later `rm -rf
  "$dest_root/sps-cms"` then copy. No backup, no transaction, no restore.
  A copy failure after removal leaves the destination missing or partial.
- `install.ps1:165-188` (`Sync-CoreSkill`): `Remove-Item -Recurse -Force
  $dest` then `Copy-Item ... -ErrorAction Stop`, wrapped in
  try/catch that only `note`s failure — same non-transactional shape.
- Manifest overwrite (`install.sh:221-244`, `install.ps1:152-163`) and log
  truncation remain as R15 found them.

**Patch proposal (for User authorization; NOT applied):**

*Proposal B1 — timestamped backup before replacement (minimal, reversible):*
1. In `sync_core_skill`/`Sync-CoreSkill`, before the first `rm -rf`
   /`Remove-Item` per destination, if the destination exists: move it aside
   to `"$dest_root/.sps-backup/sps-<UTC timestamp>"` (bash: `mv "$dest"
   "$backup_dir/"`; PS: `Move-Item`) instead of deleting it. `mv`/`Move-Item`
   on the same volume is atomic enough to shrink the destruction window to
   zero for the *old* tree; the copy then writes into the vacated path.
2. Keep at most the last N=3 backups per skill (delete older by name sort)
   to bound disk use; never delete anything newer than the previous backup.
3. On copy failure: restore the most recent backup back into place (bash:
   `mv` back; PS: `Move-Item -Force`) and exit non-zero with a message
   naming both paths.
4. On success: leave the backup in place (recovery is manual; the installer
   never deletes user data it did not create in this run beyond the bounded
   N).
5. Mirror the same logic in `install.ps1` and keep the two installers
   behaviorally aligned (they currently have no byte-parity requirement —
   different languages — but the *policy* must match).
6. Tests (extend `sps2/tests/test_updater_safety.py` or a new
   `test_installer_safety.py`): backup exists after a successful install to
   a temp sync root; old tree restored after an induced copy failure; N-bound
   enforced; no backup deletion beyond N.
7. Manifest/log truncation: write the new manifest to a temp file and
   `mv` it over the old one only after content is fully written; append
   (with rotation) instead of truncating the install log.

This proposal changes installer global-write behavior and therefore stays a
proposal until the User authorizes it in the deferred workstream.

## 4. Priority 4 — independent verification (all commands and results)

All commands run from the repo root, offline, 2026-10-16 18:20–18:23 +06.

| Check | Command | Result |
|---|---|---|
| P10 gate suite | `python3 -B -m unittest sps2.tests.test_p10_runtime_gate` | **Ran 320 tests, OK** (was 308 pre-fix; +12 new/updated contract tests) |
| Updater safety suite | `python3 -B -m unittest sps2.tests.test_updater_safety` | **Ran 13 tests, OK (skipped=1, pwsh)** |
| Frontend suites | `python3 -B -m unittest domain.frontend.tests.test_home_render domain.frontend.tests.test_content_slots domain.frontend.tests.test_layout_registry` | **Ran 85 tests, OK** |
| Combined | all three modules in one run | **Ran 418 tests, OK (skipped=1)** |
| Real P10 gate (read-only) | `python3 -B sps2/tools/p10_runtime_gate.py --slice sps2/project/SLICE-P10-01.json --json` | **exit 1, OVERALL: FAIL — 9 PASS / 5 FAIL / 2 BLOCKED**; failing: published-only-content (draft), slice-id-uniqueness, evidence-authenticity (no gate_record), approval-authenticity (null), req-p10-07-reconciliation (manifest absent); blocked: exposure-declaration, p9-deployment-audit. All five failures remain real, authorized-withheld prerequisites |
| Bash syntax | `bash -n` on install.sh, uninstall.sh, get-sps.sh, both bootstrap copies, both updater copies | 7/7 OK |
| Lint | `bash scripts/lint-sps.sh` | PASS |
| Mirror parity | `diff -rq scripts skills/sps/scripts` | identical |
| Governance validators | `check_sps2.py decision` on SPS2-ROUND16-USER-DECISIONS, P10-GATE-SEMANTICS-ADOPTION, P10-ROUND12-USER-DECISIONS, P10-DELEGATED-DECISIONS | 0 ERR each |
| Governance validators | `check_sps2.py decision sps2/decisions/P10-DECISIONS.json` | **10 ERR — pre-existing**: the validator requires `DEC-\d{4}` ids; the `D-P10-*` ids predate that rule and the User's 2026-10-09 approval explicitly kept "the check_sps2.py decision-ID issue outside this approval's scope". HEAD version shows the same class of error (6 ERRs); the working tree has 4 more because D-P10-6..9 were added by earlier authorized rounds. Not introduced or worsened in kind by this round; NOT "fixed" here because renaming recorded decision ids would rewrite governance history |
| Governance validators | `check_sps2.py inventory` (P10-SECTION-INVENTORY) | 0 ERR |
| Governance validators | `check_sps2.py evidence` on all 11 evidence files | P1/P2/P3/P9/P10/P17/ROADMAP/SEC-INCIDENT: 0 ERR; P3-APPROVAL (5), P4 (1), P5 (1), SEC-P3-CLOSURE (8) — **all identical at HEAD** (verified by validating `git show HEAD:` copies), i.e. pre-existing legacy-format findings, untouched this round |
| Gate read-only guarantee | AST scan of `sps2/tools/p10_runtime_gate.py` for write-call names | **0 write-call sites** |
| Direct probes | R15-001/002/003 scenarios re-run against the live module | all three now behave per contract (§1 above) |

## 5. Unresolved decisions requiring the User

1. **Installer backup/restore (R15-005)** — patch proposal B1 in §3 awaits
   authorization under the deferred global installer-write workstream.
   Source unchanged.
2. **Stale P10 evidence (R15-009)** — `sps2/evidence/P10-EVIDENCE.json`
   still says the gate tool/tests are untracked with "no recorded decision"
   and that "no P10 implementation exists." The gate-semantics
   implementation is now User-authorized (Round 14) and exists. Updating an
   evidence record requires separate authorization; left untouched.
3. **PowerShell runtime coverage (R15-006 residual)** — needs a `pwsh`
   environment to execute the behavioral PowerShell test; environmental,
   not code.
4. **`D-P10-*` decision-id format** — pre-existing validator/record format
   mismatch, explicitly out of a prior approval's scope; renaming recorded
   ids is a governance-history rewrite and needs a User decision.
5. **Deferred as designed:** publication (DEFER), user approval (NOT
   GRANTED), commit/push (NOT AUTHORIZED), CI (NOT AUTHORIZED), backend
   manifest (arrives with first backend code).

## 6. Side-effect verification

- Files changed **this round** (by this session): exactly two —
  `get-sps.ps1` (one message string, :75) and
  `sps2/tests/test_updater_safety.py` (test scope extended to include
  `PS_BOOTSTRAP`, :201-206). Files changed by the concurrent session before
  this round's edits: the gate tool, gate tests, updater scripts and their
  mirrors (R15-001/002/003/004/008 fixes) — verified, not modified further
  by this session.
- Git: HEAD `c49f3852e1c31d0136269c80fe58201b059af3ec` unchanged; **0
  staged**; **0 stashes**; 33 porcelain entries (32 prior + the Round 16
  decision record created last round; this round adds only this report).
- Nothing staged, committed, pushed, fetched, or pulled. No publication, no
  approval, no `user_approval` change, no inventory change, no backend
  manifest, no CI change. No installer/updater/bootstrap script was
  executed (only `bash -n` syntax checks and test-suite subprocesses in
  temp dirs).
- Fingerprints of the final state (SHA-256):
  - `sps2/tools/p10_runtime_gate.py` `99d55ffb8c8af8f5c002d9165614b5f89171c5e1405d8972d3e938cd718d0e4b`
  - `sps2/tests/test_p10_runtime_gate.py` `f585e1b4b8a90780bc9420b6ed35fde90f308ee8bd00f6d4310d5ad1aa46fbd5`
  - `sps2/tests/test_updater_safety.py` `d51c20dd98dda5051a3c4550cc735c57d7b7075be250f607a13d5bbba85bf02b`
  - `get-sps.ps1` `3b3b084dfcc7efd4e9d36a1b9fa301bc72a4bcfd187e17f258259cc4d69657af`
  - `scripts/sps-update.sh` `ba90bfbfe6f57fd6cdd15712c5f598affb09998f434d5823a0eb31dec9d5fde2`
  - `scripts/update-sps.ps1` `fc207b82ea549c49843249f8d0501e1ca2dfd4a999c4482447cda86c605eb1ad`

---

*Round 17 consumed exactly the authorized engineering scope: the three P10
gate defects are resolved and verified, three updater-safety defects are
resolved and verified (one completed by this session), the installer
backup/restore question is analyzed with a concrete proposal left
unimplemented pending authorization, and everything was re-verified offline.
The gate still honestly FAILs on five real prerequisites; nothing was
published, approved, staged, or committed.*
