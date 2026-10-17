# Decisions and Approval Boundaries

## User delegation and its limits

The user said they want Codex to make project decisions on their behalf and repeated that instruction. The project records this as **delegated operational judgment**: Codex may choose safe task ordering and proceed with already authorized engineering work. It is not a User-authored approval or evidence of identity, ratification, publication, deployment, or release. Do not write “the User approved” for a decision made by Codex.

## Recorded Codex operational decisions

The source is `reports/SPS2-DELEGATED-DECISIONS-20261017.md`. Its scope, not this summary, controls:

- Correct C4 snapshot/rollback defects, including a bounded regular-file target fix, while preserving snapshots and avoiding P10 gates/import manifests.
- Implement Packages 2/3 code fixes, accept visible validator failures, and do not change/re-pin validator baselines or exception manifests. Do not run real install/uninstall.
- Leave DEC-7301/2/3 unapproved and preserve their records, manifests, Round 26 correction sidecar, and decision history.
- Refactor/remove the P10 dynamic import only if existing behavior can be preserved and tests prove isolation; if no safe path exists, leave P10 blocked.
- Prepare local P10 evidence/fixes only; no publication, slice approval, exposure, deployment, or READY claim.
- Preserve seven untracked test modules and prepare a CI/manifest proposal only; no CI/baseline change without separate authorization.
- Treat DEC-0032 only as a one-operation branch-push authorization; no general push authorization and no remote operation.
- Fix the narrow attribution predicate to reject `Self (self-approved)` as User proof while preserving legitimate names such as `Jane Self`; do not rewrite historical approvals or claim identity authentication. Treat P5 provenance as unverified unless evidence is found.
- Preserve `.claude/settings.json`; leave provenance unresolved.
- Safe factual documentation may be corrected only when it does not change governance meaning or imply approval.

## Protected areas and actions

Do not modify unless a fresh, explicit instruction authorizes the exact change:

- CI workflows and expected-module files.
- Validator baselines, exception manifests, gate thresholds, or suppression logic.
- DEC-7301, DEC-7302, DEC-7303, Round 26 decision record/correction sidecar, disputed approval records, or historical governance.
- P10 decisions/evidence/requirements/inventory/slice/gate semantics or publication/approval state.
- `.claude/settings.json` and other user-owned provenance files.
- Remote repositories, push history, deployment environments, production services, or releases.
- Staging, committing, pushing, merging, publishing, deploying, or releasing.

Also do not run a real installer/uninstaller during safety verification. Use isolated temporary fixtures.

## Approval and readiness queue

The user decision packet `reports/SPS2-USER-DECISION-PACKET-20261017-130047.md` lists D1–D12. The older packet says several matters are `BLOCKED_USER`; the later delegated operating decision resolves only bounded code work and conservative preservation choices. It does not ratify disputed decisions or create missing evidence. Reconcile status with both records without rewriting history.

| Packet item | Subject | Current disposition |
|---|---|---|
| D1 | C4 correction scope | Bounded code correction was operationally authorized and implemented; repair has Codex review PASS, Claude re-review unavailable. Do not treat this as blanket approval of all P9/rollback behavior. |
| D2 | Packages 2/3 and legacy-validator consequence | Codex delegated decision permits code fixes while accepting visible validator failures; no baseline/manifest edits and no real install/uninstall. Older packet/backlog still says blocked; reconcile the status as an operational decision, not a User-authored policy ratification. |
| D3 | DEC-7301 updater exception | Remains UNAPPROVED; do not adopt or edit its exception manifest. Four foundation validator failures must remain visible. |
| D4 | DEC-7302 Home/P9 import groups | Remains UNAPPROVED; no manifest or scanner exception changes. The dynamic P10 import remains a policy-sensitive blocker. |
| D5 | DEC-7303 decision-ID compatibility | Remains UNAPPROVED; do not standardize validators or schemas through a governance change. |
| D6 | Round 26 record and correction sidecar | Preserve both byte-for-byte; do not annotate, replace, or claim disputed approvals as valid. |
| D7 | P10 dynamic import | A behavior-preserving refactor is conditionally authorized; if it cannot be done without changing the gate/manifest or approved-decision policy, leave it blocked. |
| D8 | P10 readiness/publication/approval | No approval, publication, deployment, or READY claim. Required authentic evidence and controls are missing; obtain them only from legitimate sources and approvers. |
| D9 | Seven untracked test modules / CI coverage | Preserve and document. Claude’s audit counted 35 modules: 28 tracked/in the module manifest, 7 untracked; its name-level count for those seven was 486 tests. CI and expected-module list edits remain unauthorized; prepare proposal only. |
| D10 | DEC-0001 and push history | Recognize only DEC-0032 (`ef59f9e`)’s one verbatim-authorized branch push; it does not cover the other five reflog entries (three `main` pushes on 10-04, one branch push on 10-12, two branch pushes on 10-16). `.sps/STATE.md:73` still says KEEP_LOCAL_ONLY. No broader push authority or remote operation. |
| D11 | Attribution and P5 provenance | Narrow code fix is authorized: reject literal `Self (self-approved)` as User proof while preserving “Jane Self.” A string cannot authenticate identity; do not change historical approvals. DEC-0031 lacks verbatim User text; P5 source authorization remains unverified. |
| D12 | `.claude/settings.json` provenance | Claude observed the worktree file as 0 bytes versus `{"enabledPlugins": {}}` at HEAD. Preserve the current user-owned file unchanged; do not overwrite, stage, or delete it. |

Open protected/human prerequisites include:

1. DEC-7301/2/3 ratification or rejection and their provenance. Keep unapproved until an authentic decision exists.
2. Round 26 attribution/correction disposition and `.claude/settings.json` provenance.
3. DEC-0001 versus local push reflogs, recognizing only the single DEC-0032 operation; other history remains uncertain.
4. Authentic P5 requirement/evidence authorization, if needed for a claim.
5. CI/test-module inclusion policy and any change to expected-module inventory.
6. P10 publication/approval, authentic gate evidence, exposure/bind observation, deployment audit inputs, backend operations manifest, actual build output, test execution, rollback rehearsal, and missing gate controls.
7. Any production deployment, publication, or release decision and credentials/approvals required by project policy.

Agents may prepare evidence and decision options; they cannot create the underlying authority or evidence by editing files.

## Stop and escalation rules

- If an engineering fix depends on changing a protected record/baseline/gate, stop and document the smallest concrete choice needed.
- If behavior cannot be preserved or test evidence is inadequate, leave the item blocked/deferred with a precise reason.
- If a local agent/model/runtime is unavailable, record exact failure and ask for a viable environment only if needed; do not claim the task was reviewed.
- If user files changed concurrently, preserve and rebaseline. Never resolve ownership by resetting or overwriting.
- A red validator is evidence to report, not permission to weaken it.
- P10 or release stays **NOT READY** while any mandatory control fails/blocks or authentic evidence/approval is missing.
