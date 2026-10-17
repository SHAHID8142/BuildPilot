#!/usr/bin/env python3
"""P17 Task Runner CLI - Slice 1 + Slice 2 lifecycle integrity.

Pipeline, every stage failing closed:

    plan -> approve -> [gate] -> run -> verify -> status

Slice 2 additions, each individually enforced before any subprocess is
created:
  * fail-closed CLI: malformed JSON, invalid records, state errors and
    filesystem errors produce a controlled non-zero exit with a named stage,
    a scrubbed message and never a traceback (S2-1);
  * approval binding: the approval records the digests of the exact task and
    plan content approved; `run` recomputes and compares both before spawn
    (S2-2);
  * complete integrity: every artefact whose digest is recorded is recomputed
    by `verify`, including the verification evidence artefact and the
    acceptance transcripts (S2-3);
  * per-task run lock: a second concurrent run is rejected, never merged
    (S2-4);
  * atomic intake: a failed plan leaves no orphan directory and no duplicate
    or reused identifier (S2-5);
  * bounded capture: streams go to disk, at most 8 MiB per stream is retained
    in the transcript, the original-stream digest is preserved and truncation
    is explicit (S2-6);
  * attempt journal and explicit recovery: attempt-start is persisted BEFORE
    spawn, attempt-finish after; a stale in-flight attempt blocks the task
    until an explicit --resume acknowledges it (S2-7).

Exactly-once execution is NOT claimed: the journal and the run lock make
duplicate execution detectable and rejected, and recovery is always explicit.

REAL-AGENT EXECUTION IS DISABLED BY DEFAULT: a production-purpose allowlist is
refused before any probe or process spawn while GATE-P17-4 is OPEN. Only
repository-local test doubles run, and test-double results are not evidence of
real-agent isolation.

Exit codes: 0 success / VERIFIED, 1 terminal task failure, 2 rejection before
execution (invalid input, missing authorisation, approval binding mismatch,
lock held, no eligible agent, disabled real-agent execution, stale attempt
awaiting explicit recovery, confinement rejection).

Standard library only. No network. No shell. No server. No deployment.
"""
import argparse
import hashlib
import json
import os
import sys

if __package__ in (None, ""):  # pragma: no cover - direct-execution guard
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))))

from framework.sps2.p17 import (confinement, discovery, execution, intake, plan as
                      plan_mod, record, scrub, selection as selection_mod,
                      state, verification)

EXIT_OK = 0
EXIT_TASK_FAILED = 1
EXIT_REJECTED = 2

PRE_EXECUTION = ("AWAITING_USER_APPROVAL",)
RESUMABLE = ("FAILED", "BLOCKED")


def _log(stage, message):
    sys.stdout.write("[%s] %s\n" % (stage, message))
    sys.stdout.flush()


def _error(stage, message):
    """Emit a scrubbed, controlled error. Never a traceback, never a secret."""
    clean, _ = scrub.scrub(str(message))
    sys.stderr.write("[%s] ERROR: %s\n" % (stage, clean.splitlines()[0][:400]))
    sys.stderr.flush()


def _root(args):
    return os.path.abspath(args.root) if getattr(args, "root", None) \
        else state.DEFAULT_ROOT


def _load_allowlist(args, root):
    """Resolve the allowlist in effect. Data only, never a code path."""
    if getattr(args, "allowlist", None):
        path = os.path.abspath(args.allowlist)
        try:
            data = state.read_json(path)
        except Exception as exc:
            raise discovery.DiscoveryError(
                "allowlist %s is not valid JSON: %s" % (path, exc))
        if not isinstance(data, dict) or not isinstance(data.get("agents"), list):
            raise discovery.DiscoveryError(
                "allowlist %s has no 'agents' list" % path)
        data.setdefault("purpose", "test")
        return data, path
    return discovery.load_allowlist(root), discovery.allowlist_path(root)


# ------------------------------------------------------------ approval bind --
def _binding_digests(task_id, root=None):
    """Digests of the exact task and plan content under approval."""
    task_dir = state.task_dir(task_id, root)
    plan_path = os.path.join(task_dir, "plan.json")
    task_path = os.path.join(task_dir, "task.json")
    digests = {}
    for name, path in (("plan_sha256", plan_path),
                       ("task_sha256", task_path)):
        digests[name] = state.sha256_file(path) if os.path.exists(path) else None
    return digests


def _check_binding(task_id, approval, root=None):
    """S2-2: recompute and compare the approved digests. Empty means OK."""
    problems = []
    for key in ("plan_sha256", "task_sha256"):
        recorded = approval.get(key)
        if recorded is None:
            problems.append(
                "approval does not record %s; an approval from before "
                "digest binding was implemented cannot authorise execution"
                % key)
            continue
        actual = _binding_digests(task_id, root).get(key)
        if actual is None:
            problems.append("%s cannot be recomputed: the approved artefact is "
                            "missing" % key)
        elif actual != recorded:
            problems.append("%s changed after approval (approved %s, on disk %s)"
                            % (key, recorded[:12], actual[:12]))
    return problems


# ------------------------------------------------------------------- intake --
def _write_evidence(task_id, command, expected, verdict, detail, exit_status,
                    root, test_name=None):
    """Write an EV-P17-NNN evidence record (GOVERNANCE.md section 4)."""
    evidence_id = state.next_evidence_id(root)
    payload = {
        "id": evidence_id,
        "task": task_id,
        "command": " ".join(command) if isinstance(command, list) else str(command),
        "expected": expected,
        "actual": detail,
        "result": verdict,
        "timestamp": state.now(),
        "file": "framework/sps2/p17/verification.py, framework/sps2/p17/execution.py",
        "test": test_name or "p17 run (test doubles only)",
        "commit": "UNCOMMITTED_WORKING_TREE",
        "note": ("Objective evidence only. This record does not establish "
                 "real-agent isolation: real-agent execution is disabled "
                 "(GATE-P17-4 OPEN)."),
    }
    state.write_json(os.path.join(state.evidence_root(root),
                                  "%s.json" % evidence_id), payload)
    return evidence_id


# --------------------------------------------------------------------------
# plan  (S2-5: atomic intake)
# --------------------------------------------------------------------------
def cmd_plan(args):
    root = _root(args)
    stage = "intake"
    try:
        state.ensure_dirs(root)
        allowlist, allowlist_file = _load_allowlist(args, root)
        raw = intake.load_task_file(args.task_file)
        task = intake.validate(raw, root, allowlist)
    except intake.IntakeRejected as exc:
        _error(stage, str(exc))
        return EXIT_REJECTED
    except discovery.DiscoveryError as exc:
        _error(stage, str(exc))
        return EXIT_REJECTED
    _log(stage, "task input validated (goal %d chars, %d required capabilities)"
         % (len(task["goal"]), len(task["required_capabilities"])))

    # Discovery and selection happen BEFORE any artefact is written, so a
    # failure here cannot leave a partially created task.
    stage = "discovery"
    try:
        snapshot = discovery.discover(allowlist, cwd=root, root=root,
                                 allowlist_file=allowlist_file)
    except (discovery.DiscoveryError, execution.ExecutionError) as exc:
        _error(stage, str(exc))
        return EXIT_REJECTED
    _log(stage, "probed %d allowlist entr%s, %d available (purpose=%s)"
         % (snapshot["probed_count"], "y" if snapshot["probed_count"] == 1
            else "ies", snapshot["available_count"],
            snapshot["allowlist_purpose"]))

    stage = "selection"
    selection, _ordered, excluded = selection_mod.select(
        allowlist, snapshot, task["required_capabilities"])
    if selection is None:
        _error(stage, "no available agent satisfies the required capabilities; "
                      "excluded: %s"
               % "; ".join("%s (%s)" % (e["agent_id"], e["reason"])
                           for e in excluded))
        return EXIT_REJECTED
    _log(stage, selection["selection_rationale"])

    # S2-5: allocate a monotonic identifier under the intake lock, then write
    # every artefact; any failure removes the directory and reports the result.
    stage = "plan"
    try:
        task_id = state.allocate_task_id(root)
    except state.StateError as exc:
        _error(stage, "could not allocate a task identifier: %s" % exc)
        return EXIT_REJECTED
    _log("plan", "allocated %s" % task_id)

    plan_doc = plan_mod.build(task["goal"], task["required_capabilities"],
                              task["acceptance"]["command"])
    plan_doc["allowlist_source"] = os.path.relpath(
        allowlist_file, root) if allowlist_file.startswith(root) \
        else allowlist_file
    try:
        plan_ref = plan_mod.persist(task_id, plan_doc, root)
        state.write_json(os.path.join(state.task_dir(task_id, root),
                                      "task.json"), {
            "task_id": task_id,
            "goal": task["goal"],
            "required_capabilities": task["required_capabilities"],
            "acceptance": task["acceptance"],
            "timeout_seconds": task["timeout_seconds"],
            "created_at": state.now(),
        })
        doc = record.planned_record(
            task_id, task["goal"], task["required_capabilities"],
            {"steps": plan_doc["steps"], "sha256": plan_ref["sha256"]},
            snapshot, selection, root)
        doc["status"] = "AWAITING_USER_APPROVAL"
        record.write(task_id, doc, root)
    except Exception as exc:
        ok, detail = state.discard_task_dir(task_id, root)
        if ok:
            _error(stage, "task %s was not created and its partial state was "
                          "removed: %s" % (task_id, exc))
        else:
            # Cleanup failure is never hidden.
            _error(stage, "task %s was not created AND cleanup failed: %s (%s)"
                  % (task_id, detail, exc))
        return EXIT_REJECTED
    _log("plan", "persisted %s (%d steps, sha256 %s...)"
         % (plan_ref["ref"], len(plan_doc["steps"]), plan_ref["sha256"][:12]))
    _log("record", "%s written, status AWAITING_USER_APPROVAL (GATE-P17-3 "
                   "per-task approval required before run)" % task_id)
    _log("next", "approve: python3 -m framework.sps2.p17 approve --task-id %s "
                 "--basis \"...\"" % task_id)
    return EXIT_OK


# --------------------------------------------------------------------------
# approve  (S2-2: bind the approval to what was approved)
# --------------------------------------------------------------------------
def cmd_approve(args):
    root = _root(args)
    task_id = args.task_id
    try:
        doc = record.load(task_id, root)
    except record.RecordInvalid as exc:
        _error("approve", str(exc))
        return EXIT_REJECTED
    if doc.get("status") not in PRE_EXECUTION:
        _error("approve", "task %s is in status %s and is not awaiting "
                          "approval; refusing to alter it"
               % (task_id, doc.get("status")))
        return EXIT_REJECTED
    if doc.get("approval") is not None:
        _error("approve", "task %s already carries an approval" % task_id)
        return EXIT_REJECTED
    if not (args.basis or "").strip():
        _error("approve", "an explicit approval basis is required; approval is "
                          "a deliberate act and is never inferred")
        return EXIT_REJECTED
    state_ = "REJECTED" if args.reject else "APPROVED"
    approval = {
        "decided_by": "User",
        "decided_by_role": "USER",
        "decided_at": state.today(),
        "basis": args.basis.strip(),
        "state": state_,
    }
    if not args.reject:
        # Bind to the exact content being approved.
        digests = _binding_digests(task_id, root)
        if digests.get("plan_sha256") is None or \
                digests.get("task_sha256") is None:
            _error("approve", "the task or plan artefact is missing, so the "
                              "approval cannot be bound to it; refusing")
            return EXIT_REJECTED
        approval["plan_sha256"] = digests["plan_sha256"]
        approval["task_sha256"] = digests["task_sha256"]
    # The approved record schema permits the approval object in the record
    # only from IN_PROGRESS onward; before execution the authoritative
    # approval lives in this project-local sidecar, which `run` checks.
    state.write_json(os.path.join(state.task_dir(task_id, root),
                                  "approval.json"), approval)
    if args.reject:
        doc["approval"] = _record_approval(approval)
        doc["status"] = "REJECTED"
        doc["updated_at"] = state.now()
        try:
            record.write(task_id, doc, root)
        except record.RecordInvalid as exc:
            _error("approve", "record rejected: %s" % exc)
            return EXIT_REJECTED
        _log("approve", "%s REJECTED by the User; recorded in the task record"
             % task_id)
        return EXIT_OK
    _log("approve", "%s approval recorded (decided_by=User, "
                    "decided_by_role=USER, state=APPROVED, bound to plan %s "
                    "and task %s)"
         % (task_id, approval["plan_sha256"][:12], approval["task_sha256"][:12]))
    _log("approve", "bound digests are recomputed before execution; any "
                    "change to the approved task or plan blocks the run")
    return EXIT_OK


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------
# The approved task-record schema's approval object is closed
# (additionalProperties: false). Only these fields may appear inside the
# record; the Slice 2 binding digests live in the project-local sidecar.
RECORD_APPROVAL_FIELDS = ("decided_by", "decided_by_role", "decided_at",
                          "basis", "state")


def _record_approval(approval):
    """Project only the schema-permitted approval fields into the record."""
    return {k: approval.get(k) for k in RECORD_APPROVAL_FIELDS}


def _approval_sidecar(task_id, root):
    path = os.path.join(state.task_dir(task_id, root), "approval.json")
    if not os.path.exists(path):
        return None
    try:
        return state.read_json(path)
    except Exception:
        return None


def cmd_run(args):
    """S2-4: take the per-task lock before anything else happens."""
    root = _root(args)
    task_id = args.task_id
    try:
        lock = state.run_lock(task_id, root)
        lock.__enter__()
    except state.StateError as exc:
        # Includes LockUnavailable (another run holds it) and a platform that
        # cannot provide locking at all: both fail closed, before any spawn.
        _error("lock", str(exc))
        return EXIT_REJECTED
    try:
        return _run_locked(args, root, task_id)
    finally:
        lock.__exit__(None, None, None)


def _run_locked(args, root, task_id):
    stage = "record"
    try:
        doc = record.load(task_id, root)
    except record.RecordInvalid as exc:
        _error(stage, str(exc))
        return EXIT_REJECTED

    resume = bool(getattr(args, "resume", False))

    # SEC-P17-10 / S2-2: no execution without a recorded, bound User approval.
    stage = "authorisation"
    approval = _approval_sidecar(task_id, root)
    if not approval or approval.get("state") != "APPROVED" \
            or approval.get("decided_by_role") != "USER" \
            or approval.get("decided_by") != "User":
        _error(stage, "no recorded User approval for %s; execution requires "
                      "approval.state=APPROVED with decided_by_role=USER "
                      "(GATE-P17-3). Nothing was executed." % task_id)
        return EXIT_REJECTED
    problems = _check_binding(task_id, approval, root)
    if problems:
        _error(stage, "approval binding check failed for %s: %s. Nothing was "
                      "executed." % (task_id, "; ".join(problems)))
        return EXIT_REJECTED
    _log(stage, "approval present and bound to the approved task and plan")

    stage = "state"
    status = doc.get("status")
    if status not in PRE_EXECUTION:
        if not (resume and status in RESUMABLE):
            _error(stage, "task %s is in status %s; run requires "
                          "AWAITING_USER_APPROVAL (or an explicit --resume "
                          "from %s)" % (task_id, status, "/".join(RESUMABLE)))
            return EXIT_REJECTED
        _log(stage, "explicit --resume accepted from terminal status %s" % status)

    # S2-7: a started-but-unfinished attempt means a previous run died between
    # spawn and record write. Its side effects are unknown, so the task is
    # BLOCKED until recovery is explicitly acknowledged - and even then the
    # task is never machine-verified (Slice 3, rule 5).
    stage = "journal"
    recovered_uncertain = None
    stale = state.incomplete_attempt(task_id, root)
    if stale:
        if not resume:
            reason = ("recovery required: attempt %s started at %s and never "
                      "finished; a previous run may have produced unrecorded "
                      "side effects, so this task is not re-executed "
                      "automatically. Re-run with --resume to acknowledge the "
                      "interruption, which marks attempt %s aborted."
                      % (stale.get("attempt"), stale.get("at"),
                         stale.get("attempt")))
            _error(stage, reason)
            doc["status"] = "BLOCKED"
            doc["blocked_reason"] = reason
            doc["approval"] = _record_approval(approval)
            doc["updated_at"] = state.now()
            try:
                record.write(task_id, doc, root)
            except record.RecordInvalid:
                pass
            return EXIT_REJECTED
        state.record_attempt(task_id, {
            "attempt": stale.get("attempt"), "phase": "aborted",
            "at": state.now(), "acknowledged_by": "--resume",
            "note": "prior attempt inferred killed; side effects unknown"}, root)
        recovered_uncertain = stale.get("attempt")
        _log(stage, "recovered: attempt %s marked aborted by explicit --resume; "
                    "its outcome was never journaled, so this task cannot be "
                    "machine-verified" % stale.get("attempt"))

    stage = "retry"
    journal = state.stage_state(task_id, root)
    attempts_used = state.attempts_used(task_id, root)
    retry_bound = int(journal.get("retry_bound", state.RETRY_BOUND))
    if attempts_used >= retry_bound:
        _error(stage, "retry bound exhausted (%d/%d durable attempts); refusing "
                      "to execute again" % (attempts_used, retry_bound))
        doc["status"] = "FAILED"
        doc["execution"] = {
            "agent_id": (doc.get("agent_selection") or {}).get("selected_agent")
                         or "(none)",
            "command": ["(no subprocess created)"],
            "timeout_seconds": _timeout_from_task(task_id, root),
            "working_directory": "(none)",
            "started_at": doc.get("updated_at"),
            "ended_at": state.now(),
            "outcome": "KILLED",
            "exit_status": None,
            "stdout_ref": None, "stderr_ref": None,
            "environment_policy": "EXPLICIT_ALLOWLIST",
        }
        doc["approval"] = _record_approval(approval)
        doc["updated_at"] = state.now()
        try:
            record.write(task_id, doc, root)
        except record.RecordInvalid as exc:
            _error(stage, "record rejected: %s" % exc)
            return EXIT_REJECTED
        return EXIT_TASK_FAILED
    attempt_number = attempts_used + 1

    stage = "discovery"
    try:
        allowlist, allowlist_file = _load_allowlist(args, root)
        snapshot = discovery.discover(allowlist, cwd=root, root=root,
                                 allowlist_file=allowlist_file)
    except (discovery.DiscoveryError, execution.ExecutionError) as exc:
        _error(stage, str(exc))
        return EXIT_REJECTED
    _log(stage, "re-discovered: %d/%d available"
         % (snapshot["available_count"], snapshot["probed_count"]))

    stage = "selection"
    selection, _ordered, excluded = selection_mod.select(
        allowlist, snapshot, doc.get("required_capabilities") or [])
    if selection is None:
        _error(stage, "no eligible agent; %s"
               % "; ".join("%s (%s)" % (e["agent_id"], e["reason"])
                           for e in excluded))
        doc["agent_selection"] = {
            "discovered_at": snapshot["discovered_at"],
            "available_agents": [
                {"agent_id": p["agent_id"], "available": bool(p["available"]),
                 "version": p.get("version"),
                 "probe_method": p.get("probe_method"),
                 "probed_at": p.get("probed_at")} for p in snapshot["agents"]],
            "selected_agent": None, "selection_rationale": None,
            "selection_fingerprint": None, "selected_at": None,
        }
        doc["status"] = "BLOCKED"
        doc["blocked_reason"] = ("no allowlisted agent satisfied the required "
                                 "capabilities at runtime")
        doc["updated_at"] = state.now()
        try:
            record.write(task_id, doc, root)
        except record.RecordInvalid:
            pass
        return EXIT_REJECTED
    _log(stage, "selected %s (fingerprint %s)"
         % (selection["selected_agent"], selection["selection_fingerprint"][:12]))

    stage = "confinement"
    agent_path = selection["resolved_path"]
    workspace = confinement.workspace_for(task_id, root)
    timeout_seconds = args.timeout or _timeout_from_task(task_id, root)
    agent_argv = [agent_path, "--task", task_id, "--goal", doc["goal"]]
    try:
        confinement.check_argv_paths(agent_argv, root, base=workspace,
                                     exempt=(0,))
    except confinement.ConfinementViolation as exc:
        _error(stage, "%s: %s. Nothing was spawned." % (exc.kind, exc.detail))
        doc["status"] = "BLOCKED"
        doc["blocked_reason"] = "%s: %s" % (exc.kind, exc.detail)
        doc["updated_at"] = state.now()
        try:
            record.write(task_id, doc, root)
        except record.RecordInvalid:
            pass
        return EXIT_REJECTED
    _log(stage, "runner-mediated path checks passed; workspace %s "
                "(cwd is NOT a security boundary)" % os.path.relpath(workspace, root))

    # S2-7: persist the attempt BEFORE the subprocess exists, so a crash
    # between here and the record write is detectable.
    state.record_attempt(task_id, {
        "attempt": attempt_number, "phase": "started", "at": state.now(),
        "agent_id": selection["selected_agent"],
        "selection_fingerprint": selection["selection_fingerprint"],
        "argv_sha256": hashlib.sha256(
            "\x1f".join(agent_argv).encode("utf-8")).hexdigest(),
        "allowlist_source": os.path.relpath(allowlist_file, root),
        "purpose": allowlist.get("purpose"),
        "resume": resume,
    }, root)
    _log("journal", "attempt %d/%d started (persisted before spawn)"
         % (attempt_number, retry_bound))

    stage = "execution"
    task_dir = state.task_dir(task_id, root)
    # The runner's own capture scaffolding exists before the audit window, so
    # the boundary diff attributes only changes made by the executed process.
    capture_dir = os.path.join(task_dir, "capture")
    execution.prepare_capture(capture_dir)
    before = confinement.snapshot_tree(root, confinement.AUDIT_SKIP_DIRS)
    watch_dirs = []
    for watch in (getattr(args, "watch_path", None) or []):
        path = os.path.abspath(watch)
        if not os.path.isdir(path):
            _error(stage, "watch path %s is not a directory" % watch)
            return EXIT_REJECTED
        watch_dirs.append(path)
    watch_before = [(p, confinement.snapshot_tree(p, confinement.AUDIT_SKIP_DIRS))
                    for p in watch_dirs]
    # P17 executable pinning: re-verify the resolved executable's
    # SHA-256 immediately before spawning it. Discovery recorded the
    # digest when it resolved the allowlisted name INSIDE the trusted
    # roots; a change here means the binary was substituted between
    # discovery and execution. Fail closed: nothing is spawned, the
    # attempt is journaled as aborted, and the outcome is an auditable
    # BLOCKED. This detects substitution between those two moments. It
    # does NOT close the residual window between this check and the
    # exec syscall; no unprivileged stdlib-only mechanism can.
    try:
        verified_digest = discovery.verify_unchanged(
            agent_path, selection.get("executable_sha256"),
            selection["selected_agent"])
    except discovery.DiscoveryError as exc:
        state.record_attempt(task_id, {"attempt": attempt_number,
                                       "phase": "aborted", "at": state.now(),
                                       "note": "executable verification "
                                               "refused"}, root)
        _error(stage, "%s. Nothing was spawned." % exc)
        doc["status"] = "BLOCKED"
        doc["blocked_reason"] = "EXECUTABLE_VERIFICATION_REFUSED: %s" % exc
        doc["updated_at"] = state.now()
        try:
            record.write(task_id, doc, root)
        except record.RecordInvalid:
            pass
        return EXIT_REJECTED
    try:
        result = execution.run_once(
            agent_argv, cwd=workspace, timeout_seconds=timeout_seconds,
            env=execution.build_environment(workspace),
            capture_dir=capture_dir)
    except execution.ExecutionError as exc:
        state.record_attempt(task_id, {"attempt": attempt_number,
                                       "phase": "aborted", "at": state.now(),
                                       "note": "execution error"}, root)
        _error(stage, str(exc))
        return EXIT_TASK_FAILED
    after = confinement.snapshot_tree(root, confinement.AUDIT_SKIP_DIRS)
    watch_after = [(p, confinement.snapshot_tree(p, confinement.AUDIT_SKIP_DIRS))
                   for p in watch_dirs]
    watch_pairs = list(zip(watch_dirs, [b for _, b in watch_before],
                           [a for _, a in watch_after]))
    violations = confinement.audit_boundary(
        root, workspace, before, after, watch_pairs,
        owned_prefixes=(os.path.relpath(capture_dir, root),))
    if violations:
        _log(stage, "DETECTED %d boundary change(s) outside the workspace "
                    "(detection, not prevention: the write already happened)"
             % len(violations))
        for violation in confinement.assert_no_secret_paths(violations):
            _log("confinement", "%s %s" % (violation["change"],
                                           violation["path"]))

    # S2-6: bounded transcripts; raw streams are deleted once digested.
    transcripts = {}
    cleanup_failures = []
    for stream, name in (("stdout", "stdout.log"), ("stderr", "stderr.log")):
        transcripts[stream] = execution.transcribe(
            result["%s_full" % stream], os.path.join(task_dir, name))
        ok, detail = execution.discard_capture(result["%s_full" % stream])
        if not ok:
            cleanup_failures.append(detail)
    if result.get("owned_capture_dir"):
        try:
            os.rmdir(result["owned_capture_dir"])
        except OSError:
            pass
    for stream in ("stdout", "stderr"):
        meta = transcripts[stream]
        if meta["truncated"]:
            _log(stage, "%s truncated: retained %d of %d bytes (cap %d); "
                        "original-stream sha256=%s"
                 % (stream, meta["retained_bytes"], meta["original_stream_bytes"],
                    meta["cap_bytes"], meta["original_stream_sha256"][:12]))
        if cleanup_failures:
            _error(stage, "capture cleanup failure: %s" % "; ".join(cleanup_failures))
            state.record_attempt(task_id, {"attempt": attempt_number,
                                           "phase": "aborted", "at": state.now(),
                                           "note": "capture cleanup failed"},
                                 root)
            return EXIT_TASK_FAILED

    if result["timed_out"]:
        outcome = "TIMEOUT"
        _log(stage, "TIMEOUT after %ds; process group terminated (%s); "
                    "exit_status null" % (timeout_seconds,
                                          ", ".join(result["killed_with"])
                                          or "signalled"))
    elif result["exit_status"] == 0:
        outcome = "COMPLETED"
        _log(stage, "COMPLETED exit_status=0; transcript stdout %d bytes, "
                    "stderr %d bytes" % (transcripts["stdout"]["bytes"],
                                         transcripts["stderr"]["bytes"]))
    else:
        outcome = "FAILED"
        _log(stage, "FAILED exit_status=%r recorded verbatim (a non-zero agent "
                    "exit is an explicit outcome, never a pass)"
             % (result["exit_status"],))
    state.record_attempt(task_id, {
        "attempt": attempt_number, "phase": "finished", "at": state.now(),
        "outcome": outcome, "exit_status": result["exit_status"],
        "timed_out": result["timed_out"]}, root)

    execution_block = {
        "agent_id": selection["selected_agent"],
        "command": agent_argv,
        "timeout_seconds": timeout_seconds,
        "working_directory": os.path.relpath(workspace, root),
        "started_at": state.now(),
        "ended_at": state.now(),
        "outcome": outcome,
        "exit_status": result["exit_status"],
        "stdout_ref": transcripts["stdout"]["ref"],
        "stderr_ref": transcripts["stderr"]["ref"],
        "environment_policy": "EXPLICIT_ALLOWLIST",
    }

    doc["agent_selection"] = {
        "discovered_at": snapshot["discovered_at"],
        "available_agents": [
            {"agent_id": p["agent_id"], "available": bool(p["available"]),
             "version": p.get("version"),
             "probe_method": p.get("probe_method"),
             "probed_at": p.get("probed_at")} for p in snapshot["agents"]],
        "selected_agent": selection["selected_agent"],
        "selection_rationale": selection["selection_rationale"],
        "selection_fingerprint": selection["selection_fingerprint"],
        "selected_at": state.now(),
    }
    doc["execution"] = execution_block
    doc["approval"] = _record_approval(approval)
    doc["digests"]["stdout_sha256"] = transcripts["stdout"]["sha256"]
    doc["digests"]["stderr_sha256"] = transcripts["stderr"]["sha256"]
    doc["updated_at"] = state.now()
    state.log_usage({
        "task_id": task_id, "agent_id": selection["selected_agent"],
        "resolved_path": agent_path, "version": selection.get("version"),
        "resolution_mode": selection.get("resolution_mode"),
        "executable_sha256": verified_digest,
        "outcome": outcome, "exit_status": result["exit_status"],
        "timeout_seconds": timeout_seconds, "at": state.now(),
        "attempt": attempt_number,
        "stdout_truncated": transcripts["stdout"]["truncated"],
        "allowlist_source": os.path.relpath(allowlist_file, root),
        "note": "local usage observation only (D-P17-7); no network call",
    }, root)

    if outcome != "COMPLETED":
        doc["status"] = "FAILED"
        try:
            record.write(task_id, doc, root)
        except record.RecordInvalid as exc:
            _error("record", "record rejected: %s" % exc)
            return EXIT_REJECTED
        _log("record", "%s recorded with status FAILED (outcome %s); "
                       "verification not attempted" % (task_id, outcome))
        return EXIT_TASK_FAILED

    stage = "verification"
    try:
        command = args.acceptance or _acceptance_from_task(task_id, root)
        expected = _expected_from_task(task_id, root)
    except SystemExit as exc:
        _error(stage, str(exc))
        return EXIT_REJECTED
    try:
        acceptance = verification.run_acceptance(command, expected, workspace,
                                                 timeout_seconds, task_id, root)
    except verification.VerificationError as exc:
        _error(stage, str(exc))
        return EXIT_TASK_FAILED
    _log(stage, "acceptance %s: %s" % (acceptance["verdict"], acceptance["detail"]))

    # S2-3: digests for every artefact, in the integrity sidecar.
    sidecar = state.read_integrity(task_id, root)
    for stream in ("stdout", "stderr"):
        meta = transcripts[stream]
        sidecar["%s_original_sha256" % stream] = meta["original_stream_sha256"]
        sidecar["%s_original_bytes" % stream] = meta["original_stream_bytes"]
        sidecar["%s_truncated" % stream] = meta["truncated"]
        sidecar["%s_omitted_bytes" % stream] = meta["omitted_bytes"]
    for stream in ("stdout", "stderr"):
        meta = acceptance["transcripts"][stream]
        sidecar["acceptance_%s_sha256" % stream] = meta["sha256"]
        sidecar["acceptance_%s_original_sha256" % stream] = \
            meta["original_stream_sha256"]
        sidecar["acceptance_%s_truncated" % stream] = meta["truncated"]
    sidecar["capture_note"] = (
        "Original stream BYTES are not retained: each is digested in full, "
        "then deleted. The transcript holds the scrubbed prefix up to the "
        "cap plus an explicit [TRUNCATED] marker. This is bounded evidence, "
        "not the full original stream.")
    sidecar["written_at"] = state.now()
    state.write_integrity(task_id, sidecar, root)

    evidence_id = _write_evidence(task_id, command,
                                  "exit status %r" % expected,
                                  acceptance["verdict"], acceptance["detail"],
                                  acceptance["exit_status"], root)
    evidence_ref = verification.persist(
        task_id, command, expected, acceptance["verdict"], acceptance["detail"],
        acceptance["exit_status"],
        acceptance["transcripts"]["stdout"]["ref"],
        acceptance["transcripts"]["stderr"]["ref"], evidence_id, root)
    doc["verification"] = verification.record_block(
        task_id, command, expected, acceptance["verdict"], evidence_id)
    doc["digests"]["evidence_sha256"] = evidence_ref["sha256"]

    if violations:
        doc["status"] = "FAILED"
        doc["verification"]["result"] = "FAIL"
        final = EXIT_TASK_FAILED
        _log("record", "confinement violation recorded; task FAILED despite "
                       "agent exit 0 (detection, not prevention)")
    elif recovered_uncertain is not None:
        # Slice 3, rule 5: an uncertain earlier attempt can never be cancelled
        # out by a later successful one. The acceptance result of THIS attempt
        # is still recorded truthfully, but the task as a whole stays below
        # VERIFIED and needs a human decision.
        doc["status"] = "BLOCKED"
        doc["blocked_reason"] = (
            "recovered after attempt %s, whose outcome was never journaled: "
            "that attempt's external side effects are uncertain, so this task "
            "is not machine-verified and requires human confirmation"
            % recovered_uncertain)
        final = EXIT_TASK_FAILED
        _log("record", "attempt %s recovered; task BLOCKED below VERIFIED "
                       "(acceptance this attempt: %s)"
             % (recovered_uncertain, acceptance["verdict"]))
    elif acceptance["verdict"] == "PASS":
        doc["status"] = "VERIFIED"
        final = EXIT_OK
        _log("record", "%s VERIFIED candidate (agent exit 0 AND acceptance "
                       "PASS); verifying artefact integrity before claiming it"
             % task_id)
    elif acceptance["verdict"] == "FAIL":
        doc["status"] = "FAILED"
        final = EXIT_TASK_FAILED
        _log("record", "%s FAILED: acceptance FAIL even though the agent "
                       "exited 0 (independence held)" % task_id)
    else:
        doc["status"] = "BLOCKED"
        doc["blocked_reason"] = acceptance["detail"]
        final = EXIT_TASK_FAILED
        _log("record", "%s BLOCKED: acceptance could not be judged" % task_id)

    doc["updated_at"] = state.now()
    try:
        record.write(task_id, doc, root)
    except record.RecordInvalid as exc:
        _error("record", "record rejected: %s" % exc)
        return EXIT_REJECTED

    # S2-3: artefact integrity and acceptance success are DISTINCT checks.
    # VERIFIED is only claimed when every recorded artefact verifies.
    if doc["status"] == "VERIFIED":
        report = record.verify_integrity(task_id, root)
        if report["findings"]:
            doc["status"] = "FAILED"
            doc["blocked_reason"] = "artefact integrity check failed: %s" % (
                "; ".join(f["kind"] + " " + str(f.get("artefact", ""))
                          for f in report["findings"]))
            doc["verification"]["result"] = "FAIL"
            doc["updated_at"] = state.now()
            try:
                record.write(task_id, doc, root)
            except record.RecordInvalid as exc:
                _error("record", "record rejected: %s" % exc)
                return EXIT_REJECTED
            _log("record", "VERIFIED WITHDRAWN: %s"
                 % doc["blocked_reason"])
            return EXIT_TASK_FAILED
        _log("record", "%s VERIFIED: acceptance PASS and every recorded "
                       "artefact digest re-verified (%s)"
             % (task_id, ", ".join(report["checked"])))
    _log("evidence", "%s written (%s)" % (evidence_id, evidence_ref["ref"]))
    _log("usage", "appended to .sps/tasks/p17/usage.log (local only)")
    return final


def _task_sidecar(task_id, root):
    path = os.path.join(state.task_dir(task_id, root), "task.json")
    if not os.path.exists(path):
        return {}
    try:
        return state.read_json(path)
    except Exception:
        return {}


def _acceptance_from_task(task_id, root):
    data = _task_sidecar(task_id, root)
    command = (data.get("acceptance") or {}).get("command")
    if not command:
        raise SystemExit("acceptance command is unknown for %s" % task_id)
    return command


def _expected_from_task(task_id, root):
    data = _task_sidecar(task_id, root)
    return int((data.get("acceptance") or {}).get("expected_exit_status", 0))


def _timeout_from_task(task_id, root):
    data = _task_sidecar(task_id, root)
    try:
        value = int(data.get("timeout_seconds", 300))
    except (TypeError, ValueError):
        return 300
    return value if value >= 1 else 300


# --------------------------------------------------------------------------
# verify / status / discover
# --------------------------------------------------------------------------
def cmd_verify(args):
    root = _root(args)
    report = record.verify_integrity(args.task_id, root)
    if not report["findings"]:
        _log("verify", "%s: no findings; checked %s"
             % (args.task_id, ", ".join(report["checked"]) or "nothing"))
        _log("verify", "note: an intact digest proves bytes were not altered, "
                       "not that they are the right bytes")
        return EXIT_OK
    for finding in report["findings"]:
        _error("verify", "%s %s %s" % (finding["kind"],
                                       finding.get("artefact", ""),
                                       finding.get("detail", "")))
    return EXIT_TASK_FAILED


def cmd_status(args):
    root = _root(args)
    try:
        doc = record.load(args.task_id, root)
    except record.RecordInvalid as exc:
        _error("status", str(exc))
        return EXIT_REJECTED
    # S2-1: a structurally invalid record is reported, never printed as if it
    # were usable state.
    problems = record.violations(doc)
    if problems:
        _error("status", "task %s does not conform to the approved record "
                         "contract: %s" % (args.task_id,
                                           "; ".join(problems)[:300]))
        return EXIT_REJECTED
    _log("status", "task_id      %s" % doc["task_id"])
    _log("status", "status       %s" % doc["status"])
    _log("status", "goal         %s" % doc["goal"])
    sel = doc.get("agent_selection") or {}
    _log("status", "selected     %s" % (sel.get("selected_agent") or "(none)"))
    _log("status", "fingerprint  %s"
         % (sel.get("selection_fingerprint") or "(none)"))
    ex = doc.get("execution")
    if ex:
        _log("status", "execution    %s exit_status=%r"
             % (ex["outcome"], ex["exit_status"]))
    ver = doc.get("verification")
    if ver:
        _log("status", "verification %s by %s (evidence %s)"
             % (ver["result"], ver["verifier"], ver["evidence_ref"]))
    _log("status", "digests      plan=%s stdout=%s stderr=%s evidence=%s"
         % tuple((doc.get("digests") or {}).get(k) or "(none)"
                 for k in ("plan_sha256", "stdout_sha256", "stderr_sha256",
                           "evidence_sha256")))
    journal = state.stage_state(args.task_id, root)
    started = [a for a in (journal.get("attempts") or [])
               if a.get("phase") == "started"]
    _log("status", "attempts     %d started / bound %s (exactly-once is NOT "
                   "claimed)" % (len(started),
                                 journal.get("retry_bound", state.RETRY_BOUND)))
    _log("status", "NOTE         real-agent execution is disabled "
                   "(GATE-P17-4 OPEN); this record covers test doubles only")
    return EXIT_OK


def cmd_discover(args):
    root = _root(args)
    try:
        allowlist, allowlist_file = _load_allowlist(args, root)
        snapshot = discovery.discover(allowlist, cwd=root, root=root,
                                 allowlist_file=allowlist_file)
    except (discovery.DiscoveryError, execution.ExecutionError) as exc:
        _error("discover", str(exc))
        return EXIT_REJECTED
    _log("discover", "allowlist %s (purpose=%s)"
         % (os.path.relpath(allowlist_file, root), allowlist.get("purpose")))
    for probe in snapshot["agents"]:
        _log("discover", "%-24s available=%-5s version=%s%s"
             % (probe["agent_id"], probe["available"],
                probe.get("version") or "-",
                "" if probe["available"] else " (%s)" % (probe.get("note") or "")))
    return EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python3 -m framework.sps2.p17",
        description="P17 Master Agent Task Runner, Slice 1 + Slice 2 (test "
                    "doubles only; real-agent execution disabled by default, "
                    "GATE-P17-4 OPEN).")
    parser.add_argument("--root", default=None,
                        help="project root (defaults to the repository)")
    sub = parser.add_subparsers(dest="command")

    p_plan = sub.add_parser("plan", help="intake, validate, plan, discover, select")
    p_plan.add_argument("--task-file", required=True)
    p_plan.add_argument("--allowlist", default=None)
    p_plan.set_defaults(func=cmd_plan)

    p_approve = sub.add_parser("approve", help="record the User's per-task approval")
    p_approve.add_argument("--task-id", required=True)
    p_approve.add_argument("--basis", required=True)
    p_approve.add_argument("--reject", action="store_true")
    p_approve.set_defaults(func=cmd_approve)

    p_run = sub.add_parser("run", help="execute an approved task (test doubles)")
    p_run.add_argument("--task-id", required=True)
    p_run.add_argument("--allowlist", default=None)
    p_run.add_argument("--timeout", type=int, default=None)
    p_run.add_argument("--acceptance", nargs="+", default=None)
    p_run.add_argument("--resume", action="store_true",
                       help="acknowledge a stale in-flight attempt or retry "
                            "from a terminal non-verified state")
    p_run.add_argument("--watch-path", action="append", default=None,
                       help="external directory to include in the "
                            "post-execution DETECTION diff (never prevention)")
    p_run.set_defaults(func=cmd_run)

    p_verify = sub.add_parser("verify", help="re-check digests and completeness")
    p_verify.add_argument("--task-id", required=True)
    p_verify.set_defaults(func=cmd_verify)

    p_status = sub.add_parser("status", help="print the recorded task state")
    p_status.add_argument("--task-id", required=True)
    p_status.set_defaults(func=cmd_status)

    p_discover = sub.add_parser("discover", help="probe the allowlist (read-only)")
    p_discover.add_argument("--allowlist", default=None)
    p_discover.set_defaults(func=cmd_discover)
    return parser


def main(argv=None):
    """S2-1: a controlled boundary. No traceback ever escapes; no unexpected
    failure is ever converted into success."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return EXIT_REJECTED
    try:
        return args.func(args)
    except KeyboardInterrupt:                      # pragma: no cover
        _error("interrupted", "no partial success is claimed")
        return EXIT_TASK_FAILED
    except record.RecordInvalid as exc:
        _error("state", "the task record is not usable: %s" % exc)
        return EXIT_REJECTED
    except state.StateError as exc:
        _error("state", str(exc))
        return EXIT_REJECTED
    except ValueError as exc:
        # Malformed JSON anywhere in project-local state.
        _error("state", "malformed state could not be parsed: %s" % exc)
        return EXIT_REJECTED
    except OSError as exc:
        _error("filesystem", "a project-local file could not be used: %s" % exc)
        return EXIT_REJECTED
    except Exception as exc:                       # unexpected: never success
        _error("unexpected", "unhandled %s (no traceback, no partial success "
                              "claimed); nothing is reported as complete"
               % type(exc).__name__)
        return EXIT_TASK_FAILED


if __name__ == "__main__":
    sys.exit(main())
