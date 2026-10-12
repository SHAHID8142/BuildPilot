# SPS Project Handoff & State
Read this to understand the current project context, completed tasks, and next steps.

## Required skill
- `/sps` required for this project: **yes**

## SPS version
- Skill version:

## Active agent
- See `./.sps/agent.md`
- Host:

## Current phase
- Discovery / planning / implementation / verification / audit:

## Latest audit
- Date:
- Score: /100
- Band:
- Report: ./.sps/audit-report.md
- Waiting for user choice:

## Approved sections
- 

## Waiting for approval
- 

## Mobile / low-end status
- Policy: minimal unless user approved richer
- Last responsive check:
- Lag risks remaining:

## Verification status
- Verified:
- How verified:
- Still manual / Unverified:

## Evidence
- Known:
- Assumed:
- Unverified:

## Current status
- 

## Conversation log
- 

## P17 — Master Agent Execution Backbone (SPS 2.0 roadmap)

Handoff contract per .sps/GOVERNANCE.md §6 (12 fields). No hidden memory required to continue.

1. **Task performed:** deliver P17 Slices 1-3 under the GATE-P17-2 approval - Slice 1 implementation, Slice 2 lifecycle integrity and failure recovery, Slice 3 validator integration and recovery hardening - plus fail-closed executable pinning that closes the ambient-PATH-order hijack (an allowlisted name is never resolved against the ambient PATH). Test doubles only; no real agent CLI was ever probed or invoked.
2. **Completed:** governance foundation (roadmap P17, requirements, decisions, approved task-record schema, plan stamped `approved`); **Slice 1** - 12 implementation modules plus the full CLI (`plan`/`approve`/`run`/`verify`/`status`/`discover`), allowlist gating, bounded capture, evidence records, security and end-to-end suites wired into the validator; **Slice 2** - lifecycle integrity (per-task run lock, atomic intake, bounded capture, durable attempt journal, extended integrity verification) with a 36-test lifecycle suite; **Slice 3** - recovery hardening plus lifecycle-suite integration into `sps2/tools/validate-sps2.sh`. Real-agent execution remains disabled by default; GATE-P17-2 approved and recorded; UQ-P17-01..04 resolved (D-P17-4..7). **Executable pinning (hardening)** - fail-closed resolution: an allowlisted name resolves only via an explicit absolute `pinned_path` or a name lookup confined to the allowlist's configured `trusted_roots`; the ambient PATH is never consulted; the resolved executable's SHA-256 is recorded at discovery and re-verified immediately before spawning, which detects substitution between those two moments. A missing or invalid pin, a pin that escapes the trusted roots, or a malformed `trusted_roots` declaration all fail closed (an unresolvable entry is recorded unavailable with an explicit reason, excluded from selection, and the run is BLOCKED - never a silent skip, never an execution).
3. **Not completed:** real-agent execution (GATE-P17-4 OPEN; enablement state DISABLED); any real task (GATE-P17-3 OPEN); allowlist extension beyond `opencode`; exactly-once execution (NOT claimed - the journal and run lock make duplicates detectable, not impossible); OS-level filesystem confinement (NOT provided); elimination of the residual TOCTOU window between the pre-spawn digest check and the exec syscall (NOT provided - no unprivileged stdlib-only mechanism can, and none is claimed); P10 inventory population (blocked on UQ-P10-05, P10 scope, untouched).
4. **Files changed:** Slice 1 - `sps2/p17/` (12 modules + `allowlist.json`), `.sps/p17/real-agent-execution.json`, `sps2/tests/test_p17_security.py`, `sps2/tests/test_p17_endtoend.py`, `sps2/tests/fixtures/p17/*`, `sps2/tools/validate-sps2.sh` (sections 11-12, CASE P/Q). Slice 2/3 - `sps2/p17/state.py`, `execution.py`, `record.py`, `confinement.py`, `discovery.py`, `verification.py`, `__main__.py`, `sps2/tests/test_p17_lifecycle.py`, `sps2/tests/fixtures/p17/stub-noisy.py`, `sps2/tools/validate-sps2.sh` (lifecycle suite). Governance - `.sps/architecture/SPS2-ROADMAP.md`, `sps2/requirements/P17-REQUIREMENTS.json`, `sps2/decisions/P17-DECISIONS.json`, `sps2/schemas/p17-task-record.schema.json`, `.sps/plan.md`, `.sps/handoff.md`, `.sps/changelog-sps.md`. Pinning hardening - `sps2/p17/discovery.py` (`resolve_entry`, `verify_unchanged`, `_trusted_roots`, `executable_digest`), `sps2/p17/selection.py` (`executable_sha256`, `resolution_mode`), `sps2/p17/__main__.py` (pre-spawn `verify_unchanged`, `EXECUTABLE_VERIFICATION_REFUSED`, `allowlist_file` passed to every `discover()` call), `sps2/tests/test_p17_pinning.py` (new, 23 tests), `sps2/tests/test_p17_security.py` (ratified `trusted_roots` test configuration, one additive line), `sps2/tests/test_p17_lifecycle.py` and `sps2/tests/fixtures/p17/test-allowlist.json` (`trusted_roots`), `sps2/tools/validate-sps2.sh` (pinning suite wired into section 12). Repo hygiene - `.gitignore` (root Python bytecode rules `__pycache__/`, `*.py[cod]`).
5. **Tests executed:** `python3 sps2/tests/test_p17_security.py`; `python3 sps2/tests/test_p17_lifecycle.py`; `python3 sps2/tests/test_p17_endtoend.py` (with and without `P17_AJV_ROOT`); `python3 sps2/tests/test_p17_pinning.py`; `bash sps2/tools/validate-sps2.sh` and `--negative`; P8 and P9 suites; `python3 sps2/tools/check_p10_inventory.py` and `--self-test`; `python3 sps2/tools/isolation_validator.py`.
6. **Tests passed:** P17 security 60/60; P17 lifecycle 44/44 (stable over repeated runs); P17 end-to-end 2/2 with the supplied ajv, 2/2 with 1 stated skip without it; P17 pinning 23/23; main validator 79 checks passed / 0 failed / 27 negative cases enforced, and 27/27 in `--negative` mode; P8 86/86; P9 220/220; P10 inventory conforms and its self-test is 47/47.
7. **Tests failed:** no P17 test failures. Pre-existing and unrelated, NOT introduced by P17: isolation validator `evidence/P9-EVIDENCE.json` EXTERNAL_STATE_REFERENCE (3 failures, 5 passed / 3 failed / 1 missed, zero P17 findings); `check_sps2.py` `DEC-\d{4}` decision-ID format mismatch (affects all `D-P<N>-<X>` records equally).
8. **Known risks:** filesystem confinement of an executed process is NOT provided by unprivileged stdlib-only Python. Only runner-mediated prevention (argv containment) and post-execution detection exist. See `.sps/plan.md` §13 SEC-P17-05 and §17. Slice 3 added a deliberate conservative cap: a task recovered from an attempt whose outcome was never journaled is recorded BLOCKED and can never reach VERIFIED, because the earlier attempt's external side effects are unknown; it requires human confirmation. The pre-spawn digest check detects substitution between discovery and execution but does NOT eliminate the residual TOCTOU window to the exec syscall; no unprivileged stdlib-only mechanism can, and none is claimed. P17 runtime task and evidence records are intentionally NOT committed: `record.json` records stdout/stderr digests that `verify` re-checks against `*.log` files, and the repository `.gitignore` rule `*.log` excludes those transcripts, so committed records would fail integrity verification on a fresh clone.
9. **Unresolved questions:** UQ-P17-01..04 resolved at GATE-P17-2. UQ-P10-05 and UQ-P10-06 remain open (P10 scope). GATE-P17-4 and GATE-P17-3 remain open. Open governance question: whether P17 runtime records should be version-controlled at all given the `*.log` integrity dependency described in field 8.
10. **Decisions made:** D-P17-1, D-P17-2, D-P17-3, D-P17-APPROVAL, D-P17-4, D-P17-5, D-P17-6, D-P17-7, D-P17-GATE-P17-2-APPROVAL (all in `sps2/decisions/P17-DECISIONS.json`). All nine remain `APPROVED` with `decided_by: User`; none was created, altered, or withdrawn by Slices 2 or 3, which proceeded within the existing D-P17-GATE-P17-2-APPROVAL scope.
11. **Next recommended action:** review the staged P17 commit plan (P3 adapter, P10 research, P17 governance/implementation/tests/validator as separate commits, with the 86 runtime records and 73 bytecode files excluded), then commit in dependency order. The executable-pinning suite is now wired into `validate-sps2.sh` section 12 and fails the validator on a non-zero exit. Real-agent execution stays disabled until GATE-P17-4 is approved with a prevention-proven isolation mechanism.
12. **User approval required:** yes - GATE-P17-4 (real-agent enablement) and GATE-P17-3 (per-task execution) are User decisions and remain OPEN; a User decision is also required on the runtime-record commit policy in field 8.
