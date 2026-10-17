# SPS2 C12 — Deferred P1/P4 Residual Assessment

**Timestamp:** 2026-10-17 12:48:04 +06  
**Reviewer:** Codex subagent `c12_residual_assessment`  
**Mode:** Bounded, read-only static assessment; no tests, probes, or implementation run.  
**Repository:** `/Users/maryamahad/Desktop/Shahid-Personal-SkillSet-main`  
**Branch / HEAD observed:** `build/roadmap-p3-completion` / `c49f3852e1c31d0136269c80fe58201b059af3ec`  
**Scope:** C12 only: R-1 scanner dataflow residuals and R-2 regular-file snapshot destination. No Packages 2/3 or governance decisions.

## Sources inspected

- `reports/SPS2-PROJECT-COMPLETION-BACKLOG-20261017.md`
- `reports/SPS2-COMPLETION-C4-CODEX-REVIEW-20261017-121735.md`
- `reports/SPS2-REMEDIATION-IMPLEMENTATION-P1-P4-20261017-103753.md`
- `reports/SPS2-REMEDIATION-REVIEW-P1-P4-CLAUDE-20261017-111759.md`
- Current `sps2/governance/import_exceptions.py`, `sps2/tools/rollback_seo.py`, `sps2/tests/test_round26_governance_contracts.py`, `domain/seo/tests/test_isolation.py`, and repository call sites for `create_snapshot` / `restore_snapshot`.

## Summary recommendation

- **R-1: DEFER.** The gap remains in the implementation, but the known shapes are absent from the live tree. Supporting them safely requires a more explicit scope/dataflow model and positive plus false-positive tests. The current scanner also has known broad matching behavior, so increasing inference without a defined model risks expanding false positives. This is optional hardening, not a P10 or release-readiness prerequisite established by current evidence.
- **R-2: BOUNDED FIX RECOMMENDED, after the C4 snapshot repair scope is approved.** A small early destination-type guard can prevent a regular file from being moved aside and left as `.previous-<pid>` after snapshot creation raises. The condition remains reachable through the public `snapshot_dir` argument or a filesystem collision, although current in-repository callers use the default location. Keep this inside a separately authorized Package 4 correction; do not treat it as a complete fix for the other C4 snapshot/restore findings.
- Neither recommendation touches Packages 2/3, exception policy, DEC-7301/2/3, validator baselines, P10 decisions/evidence, CI, or release state. No governance decision is required to describe either proposal. The prior Packages 1/4 implementation authorization does not automatically authorize this new patch under the backlog's C12 boundary; obtain explicit User authorization before implementation if scope is not already renewed.

## R-1 — Scanner dataflow forms

### Current status and live relevance

**Still current.** In `sps2/governance/import_exceptions.py`:

- `_dynamic_loader_names` collects only `Assign` / `AnnAssign` nodes and only direct `Name` targets (`:127-145`). Tuple/list unpacking targets and `NamedExpr` (walrus) bindings are not collected.
- A container target such as `loaders["k"] = ...` is not a `Name`, and later lookups under an arbitrary key do not identify the loader (`:105-145`).
- A `getattr` call is recognized only when its second argument is the literal constant string `"import_module"` (`:111-119`). A name-bound or computed attribute string is not recognized.

The scanner's current tests cover direct `importlib` usage, aliased `importlib`, simple rebinding, constant `getattr`, subscript access to the literal key `"import_module"`, and a local function named `import_module` (`sps2/tests/test_round26_governance_contracts.py:355-412`). They do not cover the four residual shapes above. The inspected live dynamic-loader use is the known `importlib.import_module("domain.seo.audit")` in `sps2/tools/p10_runtime_gate.py:1942-1946`, which matches the currently supported form and remains detected as the known violation. Static search did not reveal a live use of the deferred tuple/walrus/container/nonconstant-getattr shapes.

### Minimal future scope if the User chooses hardening

Files:

1. `sps2/governance/import_exceptions.py` — add deliberately bounded, documented AST recognition for the selected residual forms; do not silently turn this into general Python dataflow analysis.
2. `sps2/tests/test_round26_governance_contracts.py` — add one positive synthetic source fixture per supported shape and negative/near-miss fixtures.

Required behavior/tests:

- A tuple unpack that assigns a recognized loader to one name must make a subsequent forbidden call detectable.
- A walrus assignment of a recognized loader must make a subsequent forbidden call detectable if the explicitly selected scope supports that Python construct.
- A container save/reload should only be supported for a narrowly defined constant-key, same-scope shape; do not claim arbitrary container or interprocedural tracking.
- A nonconstant `getattr` argument should only be supported where a bounded, statically resolvable string form is defined. Dynamic runtime values cannot be proven statically and should remain documented as out of scope.
- Preserve detection of existing forms and benign unrelated dynamic imports. Include negative cases for unrelated computed arguments, unknown container keys, and a shadowed/local function where practical. The existing local-name false-positive is currently codified at test line 405; changing that behavior is a separate scanner contract decision and must not be smuggled into residual hardening.
- Assert the live scan's exact current classification remains unchanged: the known P10 violation stays detected, and no new exception is added.

### Risk, compatibility, and disposition

A scanner is not a Python interpreter. Scope-insensitive alias collection can mistake a local assignment or a loader shadowed in another function for a true loader; broad constant propagation can also expand false positives. The current `_contains_domain_seo_string` intentionally treats any `BinOp` inside a recognized loader call as suspicious, and the existing test accepts a local `import_module` false positive (C4 report C4-1). Adding broader name or container inference before defining scope rules could make this worse.

**Disposition: DEFER.** The four residual patterns remain absent from the live tree, and a robust implementation is larger than adding isolated syntax checks. If future code or a concrete threat model requires them, first define supported syntax/scope semantics, then implement the narrow scope above and independently review the positive and negative fixtures. No change to P10 policy or import-exception records is part of this work.

## R-2 — Snapshot target occupied by a regular file

### Current status and live relevance

**Still current.** In `sps2/tools/rollback_seo.py:270-317`, `create_snapshot` writes a completed staging directory, then if `target_snapshot.exists()` moves the target to a `.previous-<pid>` path (`:301-304`). It next publishes the staging directory and calls `shutil.rmtree(previous_snapshot)` (`:305-307`). If the old target was a regular file, `rmtree` raises `NotADirectoryError`. The exception handler cannot restore it because the new target now exists (`:309-314`), and the final `rmtree(..., ignore_errors=True)` does not remove an ordinary file (`:315-317`). Result: the call raises after publishing a new snapshot, while the old file remains under `.previous-<pid>`.

Repository search found the production calls at `rollback_seo.py:412` and `:650`; both call `create_snapshot` with the default destination. Current tests also use the default destination (`domain/seo/tests/test_isolation.py:346-373, 378, 391, 412`). No in-repository caller passes an explicit regular-file destination. The public `snapshot_dir` parameter still permits such a caller, and an unexpected file at the default destination can produce the same condition. This makes the issue low likelihood in current use, not unreachable by contract.

### Minimal future scope if the User chooses the fix

Files:

1. `sps2/tools/rollback_seo.py` — before creating staging or moving anything, inspect an existing target with `lstat`; reject anything that is not an actual directory (including a symlink unless symlink destinations are explicitly designed and tested) with a clear `ValueError` or documented exception. Preserve the occupant and avoid publishing a new snapshot on this invalid destination.
2. `domain/seo/tests/test_isolation.py` — add an isolated temporary-fixture test with a regular file at the requested `snapshot_dir`.

Required behavior/test:

- `create_snapshot(project_root, snapshot_dir=file_path)` fails before moving or overwriting the file.
- Original file bytes and file type remain unchanged; there is no published snapshot directory, `.previous-*` residue, or staging residue.
- Add a symlink-to-file (and, if the destination contract rejects all symlinks, symlink-to-directory) boundary test so the check is based on the directory entry itself and does not follow an outside target.
- Keep the existing valid absent-target and existing-directory behavior intact.

### Risk, compatibility, and disposition

This is a safe, narrow precondition: a snapshot destination must be directory-shaped because the implementation stores a manifest and copied files beneath it. The proposed early rejection changes the error timing/type for an invalid regular-file target; valid callers and the default path remain unaffected. Rejecting symlink destinations may affect a hypothetical external caller that intentionally supplies a directory symlink, but current implementation cleanup already does not safely support that shape; make the contract explicit and test it. Do not unlink or automatically clean up the occupied file, because it may be user data.

**Disposition: BOUNDED FIX RECOMMENDED after package-level C4 scope approval.** This removes the specific residue and misleading “failed after publish” result. However, C4-3 also identifies interruption windows in backup publication/restoration and C4-4 identifies restore validation/partial-write gaps. Fixing R-2 alone must not be represented as making snapshot/rollback safe or complete. Keep it separate from Packages 2/3 and from governance/baseline decisions.

## Checkpoint boundaries

- This is a proposal only. No source, test, `.sps/`, coordination-log, or backlog file was changed by this assessment; no test or mutating probe was run.
- The current P10 gate remains fail-closed at the previously reported 9 PASS / 5 FAIL / 2 BLOCKED; this assessment provides no evidence to change that result.
- Before any implementation: obtain the User's explicit scope decision for a C4 correction package, define whether R-2 is bundled with the broader snapshot repair, and record a pre-change preservation baseline. Then implement one bounded package, run its focused tests, and require independent review.
