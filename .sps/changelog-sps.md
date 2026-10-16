# SPS changelog

Decision and approval events recorded per PLAN-GATE.md (memory step, run after plan approval).

## 2026-10-10 — P17 GATE-P17-2 approved (Slice 1 authorized)

- **Event:** GATE-P17-2 APPROVED by the User after security review of the revised implementation plan.
- **Plan:** `.sps/plan.md` (PLAN-P17-001, Revision 2) — status stamped `approved` per PLAN-GATE.md step 5.
- **Security-review remediation incorporated:** filesystem-confinement controls reclassified into preventive controls (runner-mediated only), detection/audit controls (explicitly not prevention), and guarantees that cannot be provided under unprivileged stdlib-only Python; real-agent execution disabled by default; new plan-level gate GATE-P17-4 defined with prevention-proving negative tests, mechanism security review, and explicit User enablement as prerequisites.
- **Decisions recorded** (in `sps2/decisions/P17-DECISIONS.json`): D-P17-4 (UQ-P17-01 — initial allowlist `["opencode"]`), D-P17-5 (UQ-P17-02 — objective acceptance-command verification only for Slice 1), D-P17-6 (UQ-P17-03 — single-agent execution only in Slice 1), D-P17-7 (UQ-P17-04 — project-local usage log), D-P17-GATE-P17-2-APPROVAL.
- **Authorized:** Slice 1 implementation within the exact boundaries of the approved plan, test doubles only.
- **Not authorized:** real-agent CLI execution (GATE-P17-4 remains OPEN; enablement state DISABLED), any real task (GATE-P17-3 remains OPEN), allowlist extension beyond `opencode`, deployment or network exposure.
- **Status axes:** IMPLEMENTED != VERIFIED != APPROVED. At the time of this approval nothing in P17 was implemented, verified, or approved as an outcome.

## 2026-10-10 — P17 Slice 1 implemented (within D-P17-GATE-P17-2-APPROVAL)

- **Event:** Slice 1 implementation, end-to-end demonstration, and validator integration delivered under the existing GATE-P17-2 approval. No new decision was created or altered.
- **Delivered:** 12 implementation modules plus the full CLI (`plan`/`approve`/`run`/`verify`/`status`/`discover`); deterministic agent selection with recorded rationale; bounded capture; independent objective acceptance verification; per-task evidence records; negative security suite.
- **Tests:** P17 security 60/60; end-to-end 2/2 with ajv (1 stated skip without it).
- **Validator:** `sps2/tools/validate-sps2.sh` gained section 12 (P17) and negative CASE Q; check count 76 → 77.

## 2026-10-10 — P17 Slice 2: lifecycle integrity and failure recovery

- **Event:** Slice 2 delivered under the existing GATE-P17-2 approval. No new decision; no change to any approval state or gate.
- **Delivered:** fail-closed CLI; approval binding; complete integrity verification (evidence artefact + acceptance transcripts); per-task run lock; atomic intake with monotonic task-id allocation; bounded capture with explicit truncation; durable attempt journal with retry bound and stale-attempt detection. Lifecycle suite added at 36 tests.
- **Tests:** P17 lifecycle 36/36; full matrix green (security 60, e2e 2, P8 86, P9 220, P10 conforms + 47 self-tests, isolation validator at its pre-existing baseline with zero P17 findings).

## 2026-10-10 — P17 Slice 3: validator integration and recovery hardening

- **Event:** Slice 3 delivered under the existing GATE-P17-2 approval. No new decision; no change to any approval state or gate.
- **Delivered:** the lifecycle suite is now executed by `sps2/tools/validate-sps2.sh` in normal validation mode (check count 77 → 78; `--negative` behaviour unchanged at 27 cases). Recovery hardening added after an audit that found four real defects, each proven by a failing test before the fix:
  1. attempt-journal read errors previously returned a fresh journal, silently resetting the retry bound and erasing attempt history — now fails closed (`state.validate_journal`);
  2. `verify` ignored the journal entirely — it now reports `UNTRUSTWORTHY_JOURNAL`;
  3. a task recovered from an attempt whose outcome was never journaled could reach VERIFIED merely because a later attempt succeeded — the recovery verdict is now capped at BLOCKED with a recorded reason;
  4. retry-bound enforcement and evidence/attempt-history preservation across resumes were unproven — now covered by regression tests.
- **Deliberate conservative consequence of (3):** an uncertain earlier attempt can never be cancelled out automatically. Lifting that cap requires a human-confirmation step that the approved schema does not express; it was not added, and the schema was not amended.
- **Tests:** P17 lifecycle 44/44, stable across repeated runs; security 60/60; validator 78 checks / 27 negative cases; `--negative` 27/27.
- **Repository hygiene:** root `.gitignore` gained `__pycache__/` and `*.py[cod]` (45 bytecode files under `domain/` were previously untracked-but-not-ignored). P17 runtime task and evidence records remain uncommitted by decision.

## 2026-10-12 — P17 executable pinning (fail-closed resolution)

- **Event:** fail-closed executable pinning delivered under the existing GATE-P17-2 approval. No new decision; no change to any approval state or gate; no approved governance artifact was modified.
- **Weakness closed:** allowlist selection previously resolved an allowlisted NAME against the ambient PATH (`shutil.which`), so a same-named executable placed earlier in PATH could shadow the approved one (a PATH-order hijack). Resolution is now confined: an allowlisted name resolves **only** via an explicit absolute `pinned_path` or a name lookup confined to the allowlist's configured `trusted_roots`; the ambient PATH is never consulted.
- **Delivered:** `discovery.resolve_entry` (pinned-path and trusted-root modes, with `_trusted_roots` validation), `discovery.executable_digest` and `discovery.verify_unchanged` (SHA-256 recorded at discovery and re-verified immediately before spawning), `selection` carries `executable_sha256` and `resolution_mode`, and `__main__` calls `verify_unchanged` immediately before `run_once` (mismatch → `EXECUTABLE_VERIFICATION_REFUSED`, exit 2, nothing spawned). The usage log records `resolution_mode` and `executable_sha256`.
- **Residual limitation (NOT eliminated):** the pre-spawn digest check detects substitution **between discovery and execution** but does NOT close the residual TOCTOU window between that check and the `exec` syscall; no unprivileged stdlib-only mechanism can, and none is claimed. This is a detection control, not a prevention guarantee, and it does not satisfy GATE-P17-4's requirement for a reviewed preventive isolation mechanism.
- **Fail-closed behaviour:** a missing `trusted_roots`, a malformed (non-list / empty / non-directory) declaration, a pin that is missing / not a regular file / not executable / outside the trusted roots, or a resolution that escapes the trusted roots all fail closed. An unresolvable entry is recorded `available: false` with an explicit `resolution_error`, excluded from selection, and the run is BLOCKED (plan §12(c) semantics) — never a silent skip, never an execution.
- **Test configuration ratified:** `test_p17_security.py`'s `write_allowlist` gained one additive line declaring `trusted_roots: [FIXTURES]` (no assertion weakened or removed); the lifecycle harness and the fixture allowlist declare `trusted_roots` likewise (the fixture uses a relative `"."`, resolved against the allowlist's own directory for portability). The production `sps2/p17/allowlist.json` was deliberately left WITHOUT `trusted_roots`: it is refused before probing while GATE-P17-4 is OPEN, so it needs none to function; adding them before GATE-P17-4 opens is a User decision.
- **Validator:** `sps2/tools/validate-sps2.sh` section 12 now also runs the pinning suite and fails the validator on a non-zero exit (check count 78 → 79; `--negative` unchanged at 27 cases). Ajv remains opt-in via `P17_AJV_ROOT`.
- **Tests:** P17 pinning 23/23; security 60/60; lifecycle 44/44; end-to-end 2/2 (1 stated skip without ajv); main validator 79 checks / 27 negative cases; P6 69/0; P7 30/0.
- **Real-agent execution:** remains DISABLED (`enabled: false`, `decision_ref: null`); GATE-P17-3 and GATE-P17-4 remain OPEN. No real agent CLI was probed or invoked.

## Open gates (unchanged by Slices 1-3 and the pinning hardening)

- **GATE-P17-3 OPEN** — no real task has been executed.
- **GATE-P17-4 OPEN** — real-agent execution remains DISABLED in `.sps/p17/real-agent-execution.json` (`enabled: false`, `decision_ref: null`). Enabling it requires a prevention-proven isolation mechanism, a mechanism security review, and explicit User approval.
- No exactly-once execution is claimed, and no OS-level filesystem confinement is claimed.
