# SPS Project Plan

Status: approved
Approved by: User (GATE-P17-2)
Approved date: 2026-10-10

- **Plan ID:** PLAN-P17-001
- **Phase:** Roadmap P17 — Master Agent Execution Backbone
- **Gate:** GATE-P17-2 (security review and implementation-plan approval)
- **Template:** skills/sps/templates/plan.md (adapted; web-build sections marked N/A with reasons)
- **Governing artifacts:** sps2/requirements/P17-REQUIREMENTS.json (REQ-P17-01..14, SEC-P17-01..11, GATE-P17-1..3); sps2/decisions/P17-DECISIONS.json (D-P17-1, D-P17-2, D-P17-3, D-P17-APPROVAL); sps2/schemas/p17-task-record.schema.json (sps2.p17-task-record/v1); .sps/architecture/SPS2-ROADMAP.md (P17 section)
- **Standing bounds:** IMPLEMENTED != VERIFIED != APPROVED; local-only; Python standard library only; no dependency installation; no public deployment, network exposure, or autonomous execution (D-P17-2)
- **Revision:** 2 — 2026-10-10 security-review remediation. The filesystem-confinement treatment is corrected: controls are reclassified into preventive controls, detection/audit controls, and guarantees that cannot be provided; real-agent CLI execution is disabled by default; a new plan-level gate (GATE-P17-4, §17) governs any future real-agent enablement.
- **Approved:** GATE-P17-2 APPROVED by the User on 2026-10-10 after security review, recorded as D-P17-GATE-P17-2-APPROVAL in `sps2/decisions/P17-DECISIONS.json`. Approval authorizes Slice 1 implementation within the exact boundaries of this plan. It does NOT authorize real-agent execution: GATE-P17-4 remains OPEN and GATE-P17-3 remains OPEN.

## 1. Goal & success criteria

- **Goal:** Implement the first vertical slice of the Master Agent Task Runner: a local, stdlib-only CLI that accepts a task, produces an ordered plan, discovers authorized CLI agents at runtime, selects one deterministically with recorded rationale, executes under the P17 execution security contract, verifies the result independently, and preserves an auditable task record and evidence — with fail-closed behavior for every defined failure mode.
- **Success criteria (measurable, one per line):**
  - AC-1: `python3 -m sps2.p17 plan --task-file <file>` creates a `TASK-P17-NNNN` record with an ordered plan (>= 1 step); malformed or credential-bearing input is rejected with exit 2 and no partial record.
  - AC-2: `discover` records an availability snapshot for every allowlist entry by runtime probe; a documented-but-absent tool is reported `available: false`, never assumed.
  - AC-3: Selection is deterministic — the same requirement and discovery snapshot yield the same selected agent and the same SHA-256 selection fingerprint across 100 consecutive runs.
  - AC-4: Execution of a test-double agent under a bounded timeout captures stdout, stderr, and the verbatim exit status; a test double that exceeds the timeout is terminated via process-group kill and recorded with outcome `TIMEOUT`.
  - AC-5: A test double that exits 0 while the acceptance command fails yields task status `FAILED` — never `VERIFIED` (independence negative test).
  - AC-6: Each of the 12 enumerated failure modes produces an explicit, auditable outcome and a non-zero top-level exit (0 = VERIFIED only).
  - AC-7: The full negative security suite for SEC-P17-01..11 passes; no test invokes a real agent CLI (test doubles only).
  - AC-8: Task records conform to `sps2.p17-task-record/v1` (validated by the ambient ajv in the test suite; runtime performs the structural self-check).
  - AC-9: The implementation imports only the Python standard library and intra-repository modules (AST-based import scan passes; project isolation validator passes over the new surface).
  - AC-10: The implementation binds no socket and makes no outbound network request (import scan + code review negative test).
  - AC-11: Real-agent CLI execution is **disabled by default**; the only executable paths in slice 1 are repository-local test doubles; any attempt to execute a real agent while disabled is rejected before any spawn with an explicit "real-agent execution disabled (GATE-P17-4)" outcome and exit 2.
  - AC-12: No repository artifact claims that test-double success proves or demonstrates real-agent isolation; the negative suite asserts the disabled-by-default switch and the pipeline's completeness against test doubles only.

## 2. Stack

| Layer | Choice | Known / Assumed / Unverified |
|---|---|---|
| Runtime | System `python3`, standard library only | Known — python3 present; stdlib-only is a standing constraint (REQ-P17-12) |
| Language | Python | Known |
| CLI | `python3 -m sps2.p17 <plan\|discover\|run\|verify\|status>` | Known — stdlib `argparse` |
| State | Project-local JSON under `.sps/tasks/p17/` | Known — `.sps/tasks/` is the established task-state directory (PHASE-NN-TASKS.md precedent) |
| Executor | `subprocess` (argv-only, `start_new_session`, process-group kill) | Known on POSIX; **Windows unsupported in slice 1** (documented limitation) |
| Schema validation | Ambient ajv 8.20.0 in the **test suite only**; runtime performs structural self-checks | Known — ajv is ambient tooling at `~/node_modules`, not a runtime dependency |
| Agent interface | Explicit authorized executable allowlist (initial: `opencode`) | Unverified until runtime probe at execution time (REQ-P17-03) |
| Agent execution | Repository-local test doubles only in slice 1; real-agent execution **disabled by default** (GATE-P17-4) | Real-agent filesystem isolation is **not provided** by the current constraint set (§13 SEC-P17-05, §17) |
| Deploy | **NONE — forbidden** (SEC-P17-01) | — |
| Test tooling | `unittest` (stdlib) + ambient ajv for schema cases | Known |

## 3. Section inventory (build order) — implementation slices

One slice at a time. Each slice ships code + tests together, then stops for review. Slices S1–S8 are the implementation; S9 is the demonstration.

| # | Slice | Implements | Depends on | Files |
|---|---|---|---|---|
| S1 | Task intake + strict validation + task-ID minting | REQ-P17-01 | — | `sps2/p17/__init__.py`, `__main__.py`, `intake.py`, `state.py` |
| S2 | Ordered plan builder, persistence, plan digest | REQ-P17-02 | S1 | `sps2/p17/plan.py` |
| S3 | Runtime agent discovery + snapshot | REQ-P17-03 | S1 | `sps2/p17/discovery.py`, `sps2/p17/allowlist.json` |
| S4 | Deterministic selection + rationale + fingerprint | REQ-P17-04 | S3 | `sps2/p17/selection.py` |
| S5 | Confinement: path containment, realpath, boundary snapshots | REQ-P17-06 | — (pure path logic, testable immediately) | `sps2/p17/confinement.py` |
| S6 | Executor: argv-only, bounded timeout, process-group kill, transcripts, digests | REQ-P17-05 | S4, S5 | `sps2/p17/execution.py` |
| S7 | Secret scrubbing applied to all recorded artefacts | REQ-P17-07 | S2 | `sps2/p17/scrub.py` |
| S8 | Independent acceptance-command verification | REQ-P17-08 | S5, S6 | `sps2/p17/verification.py` |
| S9 | Fail-closed orchestration, record assembly, evidence, recovery, CLI demo | REQ-P17-09/10/11/13/14 | S1–S8 | `sps2/p17/record.py`, completion of `__main__.py`, `sps2/tests/test_p17_security.py`, `sps2/tests/test_p17_endtoend.py`, `sps2/tests/fixtures/p17/*` |

**Real-agent execution is not part of any slice.** Slices S1–S9 build and verify the complete pipeline against repository-local test doubles. Executing a real agent CLI is disabled by default and requires GATE-P17-4 (§17) — a reviewed, prevention-proven isolation mechanism explicitly enabled by the User — before it is even possible, and GATE-P17-3 per-task approval before any specific task runs.

## 4. CMS plan

**N/A — no CMS in this build.** The Task Runner is a local CLI subsystem; no content model, admin shell, or storefront is involved.

## 5. Design direction

**N/A — no UI in this build.** The interface is a command-line surface only.

## 6. SEO & Lighthouse target

**N/A — no web surface.** Nothing is deployed or served (SEC-P17-01).

## 7. Deploy

**FORBIDDEN.** Local-only execution: no public server, no public network exposure, no deployment, no release step (SEC-P17-01, D-P17-2). The rollback story is file deletion (see §15).

## 8. Mobile behavior

**N/A — no UI.**

## 9. Subagent plan

**Single-agent only (UQ-P17-03, RESOLVED: D-P17-6, 2026-10-10).** Slice 1 executes one agent process per task. Parallel specialist lanes (skills/sps/SUBAGENT-PLAYBOOK.md) are explicitly out of scope for slice 1 and require a later User decision. The build of slice 1 itself is performed by the primary agent; no parallel subagents are used.

## 10. Verification plan

- **Unit / negative security suite:** `sps2/tests/test_p17_security.py` — the SEC-P17-01..11 matrix in §13 is the test specification; every row becomes at least one test case.
- **End-to-end:** `sps2/tests/test_p17_endtoend.py` — a full task lifecycle against test doubles, producing a schema-valid `VERIFIED` task record with digests and evidence.
- **Schema conformance:** ambient ajv 8.20.0 (Draft 2020-12, strict) validates generated task records against `sps2/schemas/p17-task-record.schema.json` in the test suite.
- **Regression:** `bash sps2/tools/validate-sps2.sh` (normal + `--negative`), `python3 sps2/tools/check_sps2.py requirement …`, `python3 sps2/tools/isolation_validator.py`, P8/P9 `unittest` discovery — all must remain at their current baselines after implementation.
- **Manual check loop:** the User reviews the demonstration record and evidence before GATE-P17-3 approval (per-task approval packet).

## 11. Architecture and execution flow (Report A)

**Pipeline (every stage fails closed; any failure aborts with an explicit, recorded outcome):**

```
intake → validate → plan → [GATE-P17-3: explicit USER approval] → discover → select
      → [real-agent execution enabled? — default NO (GATE-P17-4)]
      → confine+execute (bounded, captured; test doubles in slice 1)
      → verify (independent) → record → evidence
```

**Modules (all new, all additive, zero existing files modified):**

| Module | Responsibility |
|---|---|
| `sps2/p17/__main__.py` | CLI dispatch: `plan`, `discover`, `run`, `verify`, `status` |
| `sps2/p17/intake.py` | Task intake from CLI argument or task file; strict validation; credential-like input rejection; `TASK-P17-NNNN` minting |
| `sps2/p17/plan.py` | Ordered plan builder; persistence; SHA-256 plan digest |
| `sps2/p17/discovery.py` | Allowlist-driven runtime discovery: `shutil.which` path resolution + bounded `--version` probe; discovery snapshot |
| `sps2/p17/selection.py` | Deterministic selection with recorded rationale and fingerprint (algorithm mirrors `sps2/core/selection.py::fingerprint`: SHA-256 over `agent_id:score` joins — pattern reuse, not module reuse; the P5 engine ranks the capability registry, a different domain) |
| `sps2/p17/confinement.py` | Path containment: `os.path.realpath` resolution against the project boundary; before/after boundary-tree snapshots |
| `sps2/p17/execution.py` | Argv-only subprocess execution (`shell=False`); `start_new_session=True`; bounded timeout with `os.killpg(SIGKILL)`; stdout/stderr capture to transcript files; verbatim exit status; transcript digests; **real-agent execution switch — disabled by default, enabled only by recorded GATE-P17-4 enablement state** |
| `sps2/p17/verification.py` | Independent acceptance-command verification (separate code path, own record, own subprocess) |
| `sps2/p17/scrub.py` | Pattern-based secret scrubbing applied to every recorded artefact before write |
| `sps2/p17/record.py` | Task-record assembly + structural self-check (lifecycle rules of the schema; full JSON Schema validation is a test-suite concern via ambient ajv) |
| `sps2/p17/state.py` | Project-local persistence under `.sps/tasks/p17/<TASK-P17-NNNN>/` |
| `sps2/p17/allowlist.json` | **The authoritative executable allowlist — data, not code paths** (REQ-P17-13) |

**Task state layout (created at runtime, never by the implementation):**

```
.sps/tasks/p17/<TASK-P17-NNNN>/
  record.json        # schema-conformant task record
  plan.json          # serialized ordered plan (digested)
  stdout.log         # captured agent stdout (digested, scrubbed)
  stderr.log         # captured agent stderr (digested, scrubbed)
  verification.json  # independent verification record + evidence reference
  evidence/          # verification evidence artefacts (EV-P17-NNN per .sps/GOVERNANCE.md §4)
  state.json         # implementation sidecar: retry bookkeeping, stage markers
                     # (retry state is runtime bookkeeping, deliberately NOT in the
                     #  schema-conformant record — the approved schema is fixed)
.sps/p17/real-agent-execution.json # real-agent execution enablement state:
                                     # {enabled: false, gate: "GATE-P17-4",
                                     #  decision_ref: null, mechanism: null,
                                     #  reviewed_at: null} — created DISABLED by the
                                     #  implementation; flippable only by recorded
                                     #  User enablement (GATE-P17-4, §17)
.sps/tasks/p17/usage.log   # append-only usage observation (UQ-P17-04 recommendation)
.sps/evidence/P17/EV-P17-NNN.json   # evidence records (GOVERNANCE.md §4 fields)
```

**Top-level exit codes:** `0` = task `VERIFIED`; `1` = task reached a terminal failure outcome (`FAILED`, `TIMEOUT`, confinement violation, acceptance `FAIL`); `2` = rejected before execution (invalid input, credential-like input, off-allowlist request, missing authorization / open approval gate, no eligible agent, ambiguous executable, **real-agent execution disabled (GATE-P17-4)**). Every non-zero exit is accompanied by a written record naming the failing stage.

## 12. Authoritative allowlist recommendation (Report B — resolves UQ-P17-01 by RECOMMENDATION, not decision)

**UQ-P17-01 status: RESOLVED (D-P17-4, 2026-10-10) by explicit User approval of this plan under the approval-checklist mechanism in §"Approval".** The recommendation below was approved as the initial authoritative allowlist. Approving it does not enable real-agent invocation: entries from a production-purpose allowlist are neither probed nor executed while GATE-P17-4 is OPEN (§17).

**Recommended initial allowlist: `["opencode"]` — one executable.**

Evidence for each candidate (PATH-resolution only — `command -v` resolves paths and executes nothing; no agent CLI was invoked):

| Executable | Repo adapter declared? | Present in environment? | Verdict |
|---|---|---|---|
| `opencode` | **Yes** — `sps2/core/adapters/registry.json`, maturity EXPERIMENTAL, `detection.cli: ["opencode"]` | **Yes** — `/Users/maryamahad/.opencode/bin/opencode` | **In initial allowlist** — the only executable satisfying both repository evidence and availability evidence |
| `codex` | Yes — adapter declared, `detection.cli: ["codex"]` | **No** — absent from PATH | Excluded from initial allowlist: availability cannot be demonstrated in this environment; at runtime, discovery would probe and report `available: false` (fail-closed) if it is ever added |
| `claude` | **No** — no adapter in the registry | Yes — `/Users/maryamahad/.local/bin/claude` | Excluded: observation of availability is not authorization; no repository declaration exists. Adding it is a later User decision |
| `copilot` | **No** — no adapter in the registry | Yes — VS Code globalStorage `copilotCli/copilot` | Excluded: repo-undeclared, and it is an interactive VS Code extension CLI, not a task-runner CLI. Later User decision |
| `generic` | Yes — but DECLARED fallback *descriptor*, not an executable | N/A | Never eligible: it is a capability descriptor with no `detection.cli` and no executable; it cannot be probed or executed |

**For every proposed executable (per the task directive):**

- **Why it belongs:** `opencode` is the intersection of (a) an explicit repository declaration with detection metadata (`sps2/core/adapters/registry.json`) and (b) demonstrated presence in this environment. It is also the environment the repository's own OpenCode adapter targets. Narrow-by-default: one executable minimizes the execution surface for slice 1 (single-agent scope, UQ-P17-03 open).
- **How runtime availability is checked (never assumed):** (1) `shutil.which("opencode")` resolves the path — no execution; (2) a bounded probe `subprocess.run([resolved_path, "--version"], timeout=10, capture_output=True)` records version and responsiveness; (3) failure, timeout, or non-zero probe exit ⇒ `available: false`. A tool documented in the repository but absent at runtime is reported unavailable and can never be selected (REQ-P17-03).
- **How identity/path is recorded:** the discovery snapshot stores `agent_id`, the **resolved absolute path** (`os.path.realpath` of the `shutil.which` result), `version`, `probe_method` (`VERSION_FLAG`), and `probed_at` (ISO-8601 UTC). The executor runs **exactly the discovered path** — no PATH re-resolution between discovery and execution (no path-drift window).
- **How unsupported or ambiguous executables fail closed:** (a) any executable name not in `allowlist.json` ⇒ rejected with exit 2 before any probe or spawn; (b) names containing path separators, shell metacharacters, or absolute paths ⇒ rejected (allowlist entries are bare executable names, matched exactly); (c) allowlisted but unavailable ⇒ excluded from selection; if no allowlisted agent is eligible ⇒ explicit `BLOCKED` outcome, exit 2, no fallback, ever; (d) probe failure/timout ⇒ `available: false`, recorded.
- **How provider-limit circumvention is avoided:** the executor invokes only the user's own CLI session with the user's own ambient authentication. The codebase contains no account lists, no credential injection, no rotation logic, and no quota-evasion mechanism (asserted structurally by a negative test over `allowlist.json` and the implementation surface). Hitting a provider limit surfaces as the agent's own error in stderr ⇒ recorded verbatim as `FAILED` or `BLOCKED` — never retried beyond the recorded bound, never evaded (SEC-P17-03, REQ-P17-14).

**Allowlist governance:** `allowlist.json` is data. Extending it (e.g., adding `claude` or `codex` later) is a User decision recorded in `sps2/decisions/P17-DECISIONS.json`, not a code change the agent may make unilaterally.

## 13. Execution security design — SEC-P17-01..11 (Report C — the security test matrix)

Each boundary: threat/failure scenario ⇒ preventive control ⇒ required negative test ⇒ expected exit/status ⇒ evidence. All tests use repo-local test doubles under `sps2/tests/fixtures/p17/`; **no test invokes a real agent CLI**.

**SEC-P17-01 — Local-only execution**
- Threat: the harness gains network or deployment capability (socket bind, outbound request, publish action).
- Control: no socket, HTTP, or deployment APIs exist in the implementation; the only external interaction is spawning the allowlisted local CLI and the acceptance command.
- Negative test: AST-based import/attribute scan over `sps2/p17/` asserting no `socket`, `http.*`, `urllib`, `ftplib`, `smtplib`, or deploy/publish references; plus a CLI flag test — any network/deploy-style flag is rejected.
- Expected: exit 2 for the flag case; scan clean; zero sockets ever bound.
- Evidence: scan output recorded as EV-P17-NNN; code reference for the absence of network APIs.

**SEC-P17-02 — Authorized executables**
- Threat: an off-allowlist executable is invoked, or a documented-but-absent tool is silently assumed available.
- Control: `allowlist.json` is the single source of truth; every invocation resolves against it; availability is probed at runtime per execution.
- Negative tests: (a) request an off-allowlist executable ⇒ exit 2, nothing spawned; (b) run with `opencode` removed from PATH in an isolated test environment ⇒ discovery reports `available: false` ⇒ selection finds no eligible agent ⇒ explicit `BLOCKED`, exit 2.
- Expected: exit 2 in both cases; explicit records.
- Evidence: discovery snapshot; test output.

**SEC-P17-03 — Provider compliance**
- Threat: quota/limit circumvention via account rotation or credential sharing.
- Control: no account, credential, or rotation mechanism exists anywhere in the implementation (structural absence); the executor uses the user's own ambient CLI authentication only.
- Negative test: structural assertion that `allowlist.json` and the implementation contain no account/credential/rotation fields or logic; a simulated provider-limit error from a test double is recorded verbatim as `FAILED`/`BLOCKED` with no retry beyond the bound.
- Expected: mechanism absent; limit ⇒ explicit outcome, exit 1.
- Evidence: test output; code reference for absence of rotation logic.

**SEC-P17-04 — Process control**
- Threat: runaway process; lost or unattributable output; exit status misreported.
- Control: bounded `timeout_seconds` (minimum 1, from the task record); `start_new_session=True` so the agent runs in its own process group; on `TimeoutExpired` ⇒ `os.killpg(pgid, SIGKILL)` and reap; stdout/stderr captured to transcript files with SHA-256 digests; exit status recorded verbatim.
- Negative tests: (a) `stub-slow.py` (sleeps 60s) with a 2-second timeout ⇒ outcome `TIMEOUT`, process group confirmed dead (no orphans), `exit_status: null`; (b) test double exiting 3 ⇒ `exit_status: 3` recorded verbatim, task `FAILED`.
- Expected: (a) exit 1, outcome TIMEOUT; (b) exit 1, outcome COMPLETED with exit_status 3.
- Evidence: execution record with digests; timeout test output including process-liveness assertion.

**SEC-P17-05 — Directory confinement (corrected classification — Rev 2)**

This boundary is explicitly **NOT "complete filesystem confinement."** The controls are classified into three categories, and the categories are not interchangeable:

- Threat: the executed process writes outside the authorized project directory, including via `../` traversal, a symlink inside the workspace pointing outside, or an internally constructed path.

- **Preventive controls — what these actually prevent (runner-mediated actions only):**
  - (P1) argv-only execution with `shell=False` — prevents shell interpretation and shell injection via the runner.
  - (P2) pre-execution path containment — every argv element that is or looks like a path (absolute, or containing `/`, `./`, `../`) is resolved with `os.path.realpath` and must fall inside the project boundary (the repository root), else the command is rejected before any process is spawned. This prevents the RUNNER from passing an escaping path argument. It does not constrain the agent process once spawned.
  - (P3) minimal explicit environment (see SEC-P17-06) — prevents secret inheritance; an environment control, not a filesystem control.
  - (P4) `cwd` set to the task workspace — convenience and relative-path default only. **`cwd` is not a security boundary and is never claimed to be one.**

- **Detection and audit controls — what these detect after the fact (not prevention):**
  - (D1) post-execution boundary-tree audit — file-tree snapshots (paths + mtimes) of the boundary are taken before and after execution; any creation or modification outside the task workspace ⇒ `CONFINEMENT_VIOLATION`, an explicit auditable failure.
  - (D2) transcript capture with SHA-256 digests — attributes everything the process printed.
  - **Detection is not prevention:** when D1 fires, the outside write has already happened. D1 fails the task and preserves the audit trail; it does not block the write. Post-execution detection is never described as, and never substituted for, prevention.

- **Guarantees that CANNOT be provided by the current implementation (Python standard library only, unprivileged POSIX host):**
  - (G1) OS-level filesystem confinement of the agent process: the standard library provides no `chroot` (requires privileges), no namespaces, and no seccomp facility.
  - (G2) Prevention of writes outside the authorized workspace by the agent process itself: once spawned, the agent process runs with the OS user's ordinary write permissions; P1–P4 do not confine it.
  - **Consequence:** because G1/G2 cannot be provided under the current constraints, **real-agent execution is disabled by default** (GATE-P17-4, §17). Slice 1 executes repository-local test doubles only. The standard-library-only constraint is kept, and the limitation is documented here rather than the security guarantee being weakened.

- Negative tests: (a) argv containing `../` escape ⇒ pre-execution rejection, exit 2, **no process spawned** (asserted) — proves prevention of *runner-mediated* escape only; (b) symlink inside the workspace resolving outside the boundary ⇒ rejection at realpath resolution, exit 2 — likewise runner-mediated prevention; (c) `stub-escape.py` writes outside the boundary via an internally constructed path (not an argv path) ⇒ pre-execution checks pass, the post-hoc audit **detects** the write ⇒ `CONFINEMENT_VIOLATION`, exit 1, explicit record — this test proves detection works; its documentation and assertions must not describe the write as "blocked" or "prevented"; (d) any attempt to execute a real agent while real-agent execution is disabled ⇒ rejected before any spawn, exit 2, explicit "real-agent execution disabled (GATE-P17-4)" outcome — prevention by disablement.
- Expected: (a),(b),(d) exit 2; (c) exit 1 with violation record.
- Evidence: test output; violation record; the disabled-by-default rejection record.

**SEC-P17-06 — Credentials**
- Threat: API keys or secrets appear in plans, logs, transcripts, or evidence; unrestricted credential access.
- Control: (1) intake rejects task input containing credential-like material (REQ-P17-01); (2) the execution environment is constructed with an explicit minimal policy (`EXPLICIT_ALLOWLIST`: only `PATH`, `LANG`, and the task workspace variables — never the parent environment, so inherited secrets are not passed through); (3) pattern-based scrubbing (known provider token prefixes, `key=`/`token=`/`password=` assignment shapes, high-entropy long tokens) is applied to every artefact before any write; (4) secrets are referenced by location only, never stored (GOVERNANCE.md §7).
- Negative tests: (a) task input containing a fake token (a test value, not a real secret) ⇒ intake rejection, exit 2, nothing stored; (b) a test double that echoes a fake token ⇒ the stored transcript shows the redacted form, and the digest covers the scrubbed bytes; (c) environment-policy test asserts only the allowlisted environment entries reach the child process.
- Expected: (a) exit 2; (b),(c) pass with redaction/allowlist assertions.
- Evidence: scrubbed transcript; test output.
- **Documented limitation:** scrubbing is heuristic (pattern + entropy), not a proof of absence. The structural controls are (1) and (2) — the executor never receives secrets by default; scrubbing is the second line of defense, not the primary one.

**SEC-P17-07 — Independent verification**
- Threat: the executing agent establishes its own success by exiting 0 or by self-reporting.
- Control: acceptance is judged solely by the **acceptance command from the task definition**, executed by a structurally separate verifier code path (`verification.py`), in its own subprocess, with its own record. **Structural independence rule for slice 1: the acceptance command's executable may not be an allowlisted agent executable** — the verifying command cannot be the agent being verified. The verifier's `independence_statement` is a required field. The agent's exit code is recorded in `execution` but is never consulted for acceptance.
- Negative tests: (a) test double exits 0 while the acceptance command exits non-zero ⇒ task status `FAILED`, verification `result: FAIL`, never `VERIFIED`; (b) a task whose acceptance command is an allowlisted agent executable ⇒ intake rejection, exit 2.
- Expected: (a) exit 1; (b) exit 2.
- Evidence: verification record with independence statement; task record status.

**SEC-P17-08 — Fail-closed behavior**
- Threat: a failure path defaults to pass or continues silently.
- Control: every enumerated failure mode has a defined outcome state, an explicit record naming the failing stage, and a non-zero exit. No path continues to the next step after failure.
- Negative tests (one per mode): invalid task input ⇒ 2; credential-like input ⇒ 2; off-allowlist executable ⇒ 2; missing authorization / open approval gate ⇒ 2 (and see SEC-P17-10); no eligible agent ⇒ 2 (`BLOCKED`); missing executable at runtime ⇒ 2 (`BLOCKED`); timeout ⇒ 1 (`TIMEOUT`); execution failure (non-zero agent exit) ⇒ 1; acceptance-command failure ⇒ 1; confinement violation ⇒ 1; evidence integrity mismatch ⇒ non-zero via `verify`.
- Expected: explicit outcome and non-zero exit for every mode; zero silent-default paths.
- Evidence: the executed negative suite results, recorded as EV-P17-NNN records.

**SEC-P17-09 — No dependency installation**
- Threat: a third-party import enters the implementation.
- Control: standard library + intra-repository imports only; no package manager is ever invoked.
- Negative test: AST-based import walk over `sps2/p17/` asserting every imported module is stdlib (checked against `sys.stdlib_module_names`) or intra-repo; plus the project isolation validator over the new surface.
- Expected: scan clean; isolation validator passes.
- Evidence: scan output; isolation validator output.

**SEC-P17-10 — No premature autonomy**
- Threat: unrestricted command execution, automatic deployment, or approval-gate bypass.
- Control: only allowlist executables are invocable (data-driven); no deploy/publish action exists in the codebase; `run` hard-requires `approval.state = APPROVED` with `decided_by_role = USER` present in the task record — there is no override flag, no batch mode, no environment variable that relaxes it.
- Negative tests: (a) `run` against a record in `AWAITING_USER_APPROVAL` ⇒ exit 2, **nothing spawned** (asserted); (b) code scan asserts no deploy/publish/network functions and no approval-bypass branch exists; (c) `allowlist.json` is asserted to be the only executable source (no hidden fallback list in code); (d) any real-agent execution attempt while the enablement state (`.sps/p17/real-agent-execution.json`) is absent or `enabled: false` ⇒ exit 2 with the explicit disabled outcome — and a state file claiming enablement without a matching recorded GATE-P17-4 decision fails a consistency check (a detectable governance violation).
- Expected: (a) exit 2; (b),(c) clean.
- Evidence: test output; code references.

**SEC-P17-11 — Evidence integrity**
- Threat: undigested, untimestamped, secret-bearing, corrupted, or incomplete records.
- Control: task records conform to `sps2.p17-task-record/v1`; SHA-256 digests cover the plan and all transcripts; ISO-8601 UTC timestamps on every transition; the `verify` subcommand recomputes every digest and re-checks structural completeness on demand.
- Negative tests: (a) tamper with a stored transcript after the fact ⇒ `verify` reports `INTEGRITY_MISMATCH`, non-zero exit; (b) a record missing a required field ⇒ record assembly fails (or `verify` reports `INCOMPLETE_RECORD`), non-zero; (c) the stored `plan.json` digest matches a freshly computed digest of the plan.
- Expected: (a),(b) non-zero with explicit findings; (c) match.
- Evidence: `verify` output; digest records.

**Additional mandated cases (mapped to boundaries):**
- **Recovery after interruption** (REQ-P17-11): stage markers are persisted in `state.json` after every transition. A record left `IN_PROGRESS` with `execution.started_at` but no `ended_at` (simulated) ⇒ the recovery path marks the prior execution `KILLED` (interruption inferred), records the interruption, and continues within the retry bound stored in `state.json`; exceeding the bound ⇒ `FAILED` with `retries exhausted` recorded. Test: simulated interrupted record ⇒ resume produces the explicit outcomes above.
- **No execution when an approval gate is open:** covered by SEC-P17-10(a).
- **Verification result separation from execution output:** covered by SEC-P17-07 — the verification record is a separate object with its own command, result, evidence reference, and independence statement; it is never derived from agent stdout.

## 14. Independent verification design (Report D — resolves UQ-P17-02 by RECOMMENDATION, not decision)

**UQ-P17-02 status: RESOLVED (D-P17-5, 2026-10-10) by explicit User approval of this plan under the approval-checklist mechanism in §"Approval".** Recommendation, now decided: for slice 1, verification is by OBJECTIVE_COMMAND only. An `INDEPENDENT_AGENT` verifier would require a second allowlisted executable and couples directly to UQ-P17-03 (orchestration scope); both are deferred to later User decisions. The recommendation is recorded as a decision in `sps2/decisions/P17-DECISIONS.json` as D-P17-5, on the basis of the User's explicit approval of this plan.

- **Which commands the verifier may execute:** only the acceptance command from the task definition, constrained at intake to (a) an argv array (never a shell string), (b) a first element that is either a repository-internal path inside the project boundary or a non-agent executable on PATH, (c) all path-looking arguments resolving inside the project boundary (same containment rule as agent execution), (d) **never an allowlisted agent executable** (structural independence, SEC-P17-07), (e) bounded timeout and captured output identical to agent execution.
- **How the result is determined:** the verifier compares the acceptance command's actual exit status against `expected_exit_status` from the task definition (default 0) and records `PASS`/`FAIL`/`BLOCKED` with an evidence reference. The agent's own exit code and output are recorded in `execution` and are never inputs to this determination.
- **Separation in the record:** `execution` (agent, its command, outcome, exit status, transcripts) and `verification` (verifier, acceptance command, result, independence statement, evidence reference, timestamp) are distinct objects in the task record; the schema enforces their separation and the lifecycle rule that `VERIFIED` requires `verification.result = PASS`.
- **Evidence:** the verification artefact (captured acceptance output, digested) is stored under `.sps/tasks/p17/<id>/evidence/` and referenced by an `EV-P17-NNN` record with the GOVERNANCE.md §4 fields (`id`, `task`, `command`, `expected`, `actual`, `result`, `timestamp`, `file`, `test`, `commit`).
- **Slice-1 scope:** the acceptance command runs against the test-double workspace; because acceptance commands may never be allowlisted agent executables (above), no acceptance command in slice 1 invokes a real agent. Test-double verification success does not transfer to real-agent execution, which remains disabled (GATE-P17-4).

## 15. Implementation sequence and proposed file changes (Report D)

Ordered; each slice ships code + tests together. Dependencies per §3.

**Proposed file-change list — all new files, zero existing files modified:**

| File | Purpose |
|---|---|
| `sps2/p17/__init__.py` | Package marker |
| `sps2/p17/__main__.py` | CLI dispatch (`plan`, `discover`, `run`, `verify`, `status`) |
| `sps2/p17/intake.py` | Task intake, strict validation, credential rejection, task-ID minting |
| `sps2/p17/plan.py` | Ordered plan builder, persistence, plan digest |
| `sps2/p17/discovery.py` | Runtime discovery, bounded probe, discovery snapshot |
| `sps2/p17/selection.py` | Deterministic selection, rationale, fingerprint |
| `sps2/p17/confinement.py` | Path containment, realpath resolution, boundary-tree snapshots |
| `sps2/p17/execution.py` | Argv-only executor, process-group timeout, transcripts, digests |
| `sps2/p17/verification.py` | Independent acceptance-command verification |
| `sps2/p17/scrub.py` | Secret scrubbing |
| `sps2/p17/record.py` | Task-record assembly + structural self-check |
| `sps2/p17/state.py` | Project-local persistence under `.sps/tasks/p17/` |
| `sps2/p17/allowlist.json` | Authoritative executable allowlist (data) — initial content: `["opencode"]` |
| `sps2/tests/test_p17_security.py` | Negative security suite (SEC-P17-01..11 matrix) |
| `sps2/tests/test_p17_endtoend.py` | End-to-end lifecycle test against test doubles |
| `sps2/tests/fixtures/p17/stub-agent.py` | Test double: configurable exit code, output, secret-echo mode, internal-escape mode |
| `sps2/tests/fixtures/p17/stub-slow.py` | Test double: sleeps past the timeout |
| `.sps/plan.md` | **This plan** (written now per the plan-gate convention; stamped `approved` only upon User approval) |

Runtime-created (never by the implementation): `.sps/tasks/p17/**`, `.sps/evidence/P17/**`.

**Rollback:** the slice is purely additive. Rollback = delete `sps2/p17/`, `sps2/tests/test_p17_security.py`, `sps2/tests/test_p17_endtoend.py`, `sps2/tests/fixtures/p17/`, and (if exercised) `.sps/tasks/p17/`, `.sps/evidence/P17/`, plus this plan file. No existing artifact is modified, so no reverse patch is needed and P8/P9/P10 governance is untouched by construction.

## 16. Acceptance and demonstration criteria (Report E)

- The 10 measurable success criteria AC-1..AC-10 in §1, each demonstrated by a named test or command with captured output recorded as `EV-P17-NNN` evidence.
- **Slice-1 demonstration (no real agent):** `test_p17_endtoend.py` drives a complete task — intake, plan, discovery (test double registered in an isolated allowlist), deterministic selection, bounded execution, captured transcripts, independent acceptance-command verification, digesting, evidence — and produces a schema-valid `VERIFIED` task record. The demonstration uses repo-local test doubles only.
- **Real-agent execution:** executing a real task with the actual `opencode` CLI is **not** part of slice 1 and is **disabled by default**. It requires, in order: **GATE-P17-4** (an adequately isolated execution mechanism — prevention-proven by negative tests — reviewed and explicitly enabled by the User; §17) **and then** **GATE-P17-3** (a per-task approval packet presenting the specific task, its ordered plan, and its acceptance command, with explicit User approval recorded in the task record before execution).
- **Non-transferability:** success of the test-double pipeline does **not** prove real-agent isolation. Real-agent filesystem isolation is unproven and, under the current constraint set, not provided; no repository artifact may claim that test-double success demonstrates real-agent isolation.

## 17. Platform limitations and unresolved User decisions (Report F)

**Assumptions and platform limitations (explicit):**
1. **POSIX-only for slice 1** (darwin/linux). Windows is unsupported: `os.killpg`/`start_new_session` have no Windows equivalent in the stdlib; the implementation fails closed with an explicit "unsupported platform" error on Windows.
2. **No OS-level confinement of the executed process.** Unprivileged stdlib-only Python cannot chroot or use namespaces. The SEC-P17-05 controls are preventive only for runner-mediated actions (argv containment) and detective for the agent process itself (post-hoc audit); they do not prevent the executed process from writing outside the authorized workspace. This limitation is documented, not worked around, and it is the reason real-agent execution is disabled by default (GATE-P17-4, below).
3. **Secret scrubbing is heuristic.** Pattern + entropy detection; the primary controls are intake rejection and the minimal explicit environment.
4. **Full JSON Schema validation is a test-suite concern** (ambient ajv). The runtime performs the structural self-check (required fields, enums, lifecycle rules) by hand; the stdlib has no JSON Schema engine, and adding one is forbidden by the stdlib-only constraint.
5. **Version probes execute the allowlisted CLI** with `--version`/`--help` only, bounded to 10 seconds, and occur only inside an approved execution flow — discovery is never a hidden invocation channel.
6. **Task-ID namespace:** `TASK-P17-NNNN` counters are allocated from project-local state (`.sps/tasks/p17/`); allocation is single-writer (one task at a time) in slice 1 — concurrent task intake is out of scope (single-agent scope, UQ-P17-03).

**Real-agent execution gate (GATE-P17-4) — defined by this plan at plan level:**

GATE-P17-4 must pass before any real agent CLI is executed. It is currently **OPEN**, and real-agent execution is **DISABLED by default**. Formal adoption of GATE-P17-4 into the approved governance artifacts (`sps2/requirements/P17-REQUIREMENTS.json` approval gates and the roadmap's per-gate approval note) requires a separate, explicitly authorized governance amendment; it is not adopted by this plan revision, and no approved artifact is modified here.

Conditions — ALL must hold, and each is verified, not asserted:

1. **Required isolation guarantees identified and documented.** For real-agent execution the required guarantee is *prevention* (not detection): the executed process cannot create or modify any file outside the authorized workspace. Read-confinement is required where the platform provides it; if a platform cannot prevent reads outside the workspace, that limitation is recorded explicitly and the task's data sensitivity is weighed at GATE-P17-3.
2. **Negative tests proving prevention.** Tests must demonstrate that attempted access (writes) outside the authorized workspace is **blocked** — the write does not occur — not merely detected afterward. These tests do not exist yet for real agents; they are a prerequisite of enablement, defined here so they cannot be skipped.
3. **Security review of the actual mechanism.** The isolation mechanism as implemented (not a description of intent) must pass security review, recorded with evidence.
4. **Disabled if the platform cannot provide the guarantees.** If no mechanism satisfying condition 2 exists on the platform, the feature stays disabled. Post-execution detection is explicitly not a substitute for prevention.
5. **Explicit User enablement.** Enablement is a deliberate User act, recorded in `sps2/decisions/P17-DECISIONS.json` and in the project-local enablement state (`.sps/p17/real-agent-execution.json`, which references the decision record). The runtime checks this state on every real-agent attempt; a state claiming enablement without a matching decision record fails a consistency check (a detectable governance violation).
6. **Platform assumptions labeled.** If a future mechanism depends on platform features (containers, privileged helpers, sandboxing APIs), those become explicit Known/Assumed/Unverified assumptions in this plan.

**Current status:** under the standing Python-standard-library-only constraint on an unprivileged POSIX host, no mechanism satisfies condition 2 — the standard library provides no chroot, namespace, or seccomp facility. Therefore GATE-P17-4 is OPEN, real-agent execution is DISABLED, and slice 1 verifies the complete pipeline with repository-local test doubles only. If the standard-library-only constraint is ever reconsidered, that is itself a User decision — the constraint is not weakened silently to obtain confinement.

**User decisions recorded at GATE-P17-2 (all four RESOLVED; none self-approved):**
- **UQ-P17-01** (allowlist membership): **RESOLVED** — initial authoritative allowlist `["opencode"]` (§12), recorded as D-P17-4.
- **UQ-P17-02** (verification authority): **RESOLVED** — objective acceptance commands only for slice 1 (§14), recorded as D-P17-5.
- **UQ-P17-03** (orchestration scope): **RESOLVED** — single-agent execution only in slice 1; parallel fan-out is a later increment (§9), recorded as D-P17-6.
- **UQ-P17-04** (usage observation): **RESOLVED** — project-local append-only usage log (agent id, resolved path, version, duration, outcome), no provider API calls (§11), recorded as D-P17-7.
- Extending the allowlist (e.g., `claude`, `codex`) at any later time: User decision via a new decision record.

## 18. GATE-P17-2 readiness assessment (Report G)

**Approved (GATE-P17-2, 2026-10-10) after the Rev 2 security-review remediation.** The security-review finding on filesystem confinement is remediated: §13 SEC-P17-05 now distinguishes preventive controls (runner-mediated only), detection/audit controls (explicitly not prevention), and guarantees that cannot be provided under the current constraints; real-agent execution is disabled by default; and GATE-P17-4 (§17) defines the future enablement gate with prevention-proving negative tests, mechanism security review, and explicit User enablement as prerequisites. All 14 requirements and all 11 security boundaries remain addressed by a plan section, an implementing module, and at least one negative test (traceability matrix in §20). No requirement is unaddressed. The design is additive (zero existing-file modifications), stdlib-only, local-only, and fail-closed by construction. The four UQ recommendations are presented for explicit User decision — not self-approved. Pre-existing, unrelated failures (reported separately, not caused by this plan, out of scope per GOVERNANCE.md §8): the isolation validator's `P9-EVIDENCE.json` EXTERNAL_STATE_REFERENCE finding (3 failures, pre-existing) and the `check_sps2.py` `DEC-\d{4}` decision-ID format mismatch (affects all `D-P<N>-<X>` records equally, pre-existing). This revision created no new findings: it modified only this plan file.

## 19. Working-tree preservation (Report H)

- **Before this task:** `M .sps/architecture/SPS2-ROADMAP.md` (P17 governance foundation), `M sps2/research/cache.json`, `M sps2/tools/portability.py`, `M sps2/tools/validate-sps2.sh` (pre-existing); untracked P10 and P17 governance artifacts.
- **Before this revision:** `.sps/plan.md` existed (Rev 1, untracked); the four `M` files and the untracked P10/P17 governance artifacts as listed above.
- **After this revision:** identical, with `.sps/plan.md` modified in place (Rev 2 — security-review remediation of the confinement classification, real-agent disablement, and GATE-P17-4). It remains the only file changed by this task. Nothing staged; HEAD remains `9a16a9e`.
- **Protected files verified unchanged:** `sps2/requirements/P10-REQUIREMENTS.json` (3dd872a7…), `sps2/schemas/p10-slice.schema.json` (0189d204…), `sps2/schemas/p10-section-inventory.schema.json` (226510f0…), `sps2/requirements/P10-SECTION-INVENTORY.json` (ac8f8aa1…), `sps2/tools/check_p10_inventory.py` (480a6b72…), `sps2/tools/validate-sps2.sh` (91d5e4ae…) — all match their recorded baselines byte-for-byte; `sps2/tools/portability.py` and `sps2/research/cache.json` retain their pre-existing modifications (mtimes predate this session). No P8/P9 artifact was touched.

## 20. Traceability — every requirement and boundary mapped

| Requirement | Plan section | Implementing module | Negative test |
|---|---|---|---|
| REQ-P17-01 task intake | §11, §13 SEC-P17-08 | `intake.py` | invalid input; credential-like input |
| REQ-P17-02 ordered plan | §11 | `plan.py` | plan gate open ⇒ no execution (SEC-P17-10a) |
| REQ-P17-03 runtime discovery | §11, §12 | `discovery.py` | absent tool reported unavailable (SEC-P17-02b) |
| REQ-P17-04 deterministic selection | §11 | `selection.py` | fingerprint stability across 100 runs (AC-3) |
| REQ-P17-05 controlled execution | §11, §13 SEC-P17-04 | `execution.py` | timeout kill; verbatim non-zero exit |
| REQ-P17-06 directory confinement | §13 SEC-P17-05 | `confinement.py` | traversal, symlink (runner-mediated prevention); internal-escape (detection, explicitly labeled) |
| REQ-P17-07 credential safety | §13 SEC-P17-06 | `scrub.py`, `intake.py` | intake rejection; transcript redaction; env policy |
| REQ-P17-08 independent verification | §14 | `verification.py` | exit-0 agent + failing acceptance ⇒ FAILED |
| REQ-P17-09 fail-closed | §13 SEC-P17-08 | all | 12-mode matrix |
| REQ-P17-10 auditable status/evidence | §11, §13 SEC-P17-11 | `record.py`, `state.py` | integrity mismatch; incomplete record |
| REQ-P17-11 failure handling/recovery | §13 (additional cases) | `state.py` | simulated interruption ⇒ explicit resume outcomes |
| REQ-P17-12 stdlib-only | §2, §13 SEC-P17-09 | all | AST import scan; isolation validator |
| REQ-P17-13 no premature autonomy | §13 SEC-P17-10 | `__main__.py`, `allowlist.json` | gate-open run rejected; no bypass branch |
| REQ-P17-14 provider compliance | §12, §13 SEC-P17-03 | `execution.py` | structural absence of rotation; limit ⇒ BLOCKED |

| Boundary | Threat | Control | Test | §13 row |
|---|---|---|---|---|
| SEC-P17-01 | network/deploy capability | none exist in code | import/attribute scan; flag rejection | ✓ |
| SEC-P17-02 | off-allowlist / assumed-available | allowlist data + runtime probe | off-allowlist rejection; absent-agent BLOCKED | ✓ |
| SEC-P17-03 | quota circumvention | structural absence of rotation | structural assertion; limit simulation | ✓ |
| SEC-P17-04 | runaway / lost output | bounded timeout, killpg, capture, verbatim status | stub-slow; exit-3 double | ✓ |
| SEC-P17-05 | boundary escape, symlink | **Preventive (runner-mediated only):** argv containment + realpath; **detective (agent process):** post-hoc tree audit; **not provided:** OS-level confinement of the agent process — real-agent execution disabled by default (GATE-P17-4) | traversal; symlink (prevention of runner-mediated escape); internal-escape (detection, explicitly labeled as such); disabled-rejection | ✓ |
| SEC-P17-06 | secret leakage | intake rejection + minimal env + scrubbing | credential input; echo redaction; env policy | ✓ |
| SEC-P17-07 | self-attestation | separate verifier; non-agent acceptance command | exit-0/failing-acceptance; agent-as-acceptance rejected | ✓ |
| SEC-P17-08 | silent default-to-pass | enumerated outcomes, non-zero exits | 12-mode matrix | ✓ |
| SEC-P17-09 | third-party import | stdlib+intra-repo only | AST import scan | ✓ |
| SEC-P17-10 | autonomy / gate bypass | allowlist-only; hard approval requirement | gate-open run; bypass-branch scan | ✓ |
| SEC-P17-11 | corrupted/incomplete evidence | digests, timestamps, verify subcommand | tamper; incomplete; digest match | ✓ |

**Requirements not addressed: none.** Boundaries not addressed: none.

**GATE-P17-4 note (Rev 2):** REQ-P17-05 and SEC-P17-05 are additionally governed by GATE-P17-4 (§17): real-agent execution requires a reviewed isolation mechanism with negative tests proving attempted access outside the authorized workspace is *blocked* (prevention). Test-double success does not transfer to real-agent isolation, and post-execution detection is not a substitute for prevention. Until GATE-P17-4 passes, the implementation surface is test-double execution only.

## Open questions

1. None outstanding. UQ-P17-01..UQ-P17-04 were resolved by explicit User approval of this plan (GATE-P17-2, 2026-10-10) under the approval-checklist mechanism below, and recorded as D-P17-4 through D-P17-7 in `sps2/decisions/P17-DECISIONS.json`.
2. None other. Routine engineering details (module layout, CLI flag design, file formats, naming) are delegated to the project agent per D-P17-3 and are specified in §11/§15.

## Approval — GATE-P17-2 checklist (Tier 2 approval packet)

Approval of this plan constitutes approval of the following, each line requiring the User's explicit confirmation:

- [x] **Implementation plan** (§11, §15) — architecture, modules, sequence, file-change list, rollback
- [x] **Security test matrix** (§13) — adopted as the definition of the negative suite that must pass before implementation is complete
- [x] **Acceptance criteria** (§1, §16) — AC-1..AC-10 for the first vertical slice
- [x] **Allowlist recommendation (UQ-P17-01)** — initial authoritative allowlist `["opencode"]` (§12)
- [x] **Verification recommendation (UQ-P17-02)** — objective acceptance commands only for slice 1 (§14)
- [x] **Scope recommendation (UQ-P17-03)** — single-agent execution only in slice 1 (§9)
- [x] **Usage-observation recommendation (UQ-P17-04)** — project-local usage log (§11)
- [x] **Platform limitations acknowledged** (§17) — POSIX-only; confinement class documented; scrubbing heuristic; ajv ambient-only
- [x] **Confinement correction acknowledged** (§13 SEC-P17-05, Rev 2) — preventive controls, detection/audit controls, and unprovided guarantees are distinguished; no completeness claim remains
- [x] **Real-agent execution disabled by default** acknowledged; GATE-P17-4 conditions (§17) acknowledged as prerequisites to any real-agent execution
- [x] **Additive-only implementation confirmed** — zero existing files modified; stdlib-only; local-only
- [x] **Conditions remaining under GATE-P17-3** acknowledged (below)

**Approved (GATE-P17-2, 2026-10-10):** this plan's status was stamped `approved` per PLAN-GATE.md step 5. The four checklist recommendation lines were recorded as D-P17-4 through D-P17-7 and the GATE-P17-2 approval as D-P17-GATE-P17-2-APPROVAL in `sps2/decisions/P17-DECISIONS.json`. Slice 1 implementation is authorized within these boundaries (§3). Real-agent execution remains disabled by default (GATE-P17-4 OPEN); GATE-P17-3 remains OPEN and required before any real task execution.

## Conditions remaining under GATE-P17-3 (separate, still OPEN)

1. Explicit User approval of the **first real task** — its full ordered plan and acceptance command presented as a per-task approval packet, recorded in the task record (`approval.state = APPROVED`, `decided_by_role = USER`) before any execution.
2. The **real-agent demonstration** (actual `opencode` CLI) requires **GATE-P17-4 first** (a reviewed, prevention-proven isolation mechanism, explicitly enabled — §17) and **then** GATE-P17-3 per-task approval. Slice 1's demonstration uses test doubles only.
3. Every **HIGH or CRITICAL task** thereafter requires its own explicit User approval.
4. Any **allowlist extension** (adding `claude`, `codex`, or other executables) is a User decision via a new decision record — never an implementation-time choice.
5. **GATE-P17-3 approval alone does not enable real-agent execution.** GATE-P17-4 enablement is a separate, prior act; both gates must pass, in that order, before any real agent CLI runs.

---

**Confirmation (Rev 2):** This revision was prepared under the GATE-P17-2 security-review remediation authorization and modifies `.sps/plan.md` only. No Task Runner implementation code was written; no agent CLI was invoked (availability evidence was gathered by PATH resolution only, which executes nothing); no real task was executed; no dependency was installed; nothing was staged, committed, or pushed; no service was exposed; no open User decision was marked approved. The plan gate remains stopped, awaiting the User's explicit GATE-P17-2 decision on this revised plan.
