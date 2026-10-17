#!/usr/bin/env python3
"""P17 independent objective acceptance-command verification (REQ-P17-08).

Acceptance is judged by the acceptance command from the task definition,
executed by this structurally separate verifier module in its own subprocess,
with its own record, its own captured output, and its own evidence artefact.

The executing agent's exit code and its output are recorded in the execution
record and are NEVER inputs to this determination. A test double that exits 0
while the acceptance command fails yields a FAILED task, never VERIFIED.

Verifier constraint (SEC-P17-07): the acceptance command's executable may not
be an allowlisted agent executable. This is enforced at intake (intake.py) so
the verifying command can never be the agent being verified.

Standard library only. No network.
"""
import os

from . import execution, record, scrub, state

VERIFIER = "OBJECTIVE_COMMAND"
INDEPENDENCE_STATEMENT = (
    "Acceptance was judged by the objective acceptance command supplied by "
    "the task definition and executed by framework/sps2/p17/verification.py, which is a "
    "structurally separate code path from framework/sps2/p17/execution.py. The verifying "
    "executable is not an allowlisted agent executable (enforced at intake). "
    "The executing agent's exit code and output are recorded in the execution "
    "record and are not inputs to this result.")


class VerificationError(Exception):
    """Verification could not be performed as specified."""


def run_acceptance(command, expected_exit_status, workspace, timeout_seconds,
                   task_id, root=None):
    """Execute the acceptance command and return its structured result.

    The acceptance streams are captured with the same bounded policy as agent
    execution: transcript digests cover the bytes written, the original stream
    digest is retained in the integrity sidecar, and raw streams are deleted.
    Truncation of the ACCEPTANCE stream makes acceptance unverifiable, so the
    verdict becomes BLOCKED rather than PASS.
    """
    capture_dir = os.path.join(state.task_dir(task_id, root), "capture")
    try:
        result = execution.run_once(list(command), cwd=workspace,
                                    timeout_seconds=timeout_seconds,
                                    capture_dir=capture_dir)
    except execution.ExecutionError as exc:
        raise VerificationError("acceptance command could not be executed: %s"
                                % exc)
    evidence_dir = os.path.join(state.task_dir(task_id, root), "evidence")
    if not os.path.isdir(evidence_dir):
        os.makedirs(evidence_dir)
    transcripts = {}
    cleanup_failures = []
    for stream, name in (("stdout", "acceptance-stdout.log"),
                         ("stderr", "acceptance-stderr.log")):
        transcripts[stream] = execution.transcribe(
            result["%s_full" % stream],
            os.path.join(evidence_dir, name))
        ok, detail = execution.discard_capture(result["%s_full" % stream])
        if not ok:
            cleanup_failures.append(detail)
    if result.get("owned_capture_dir"):
        try:
            os.rmdir(result["owned_capture_dir"])
        except OSError:
            pass
    if cleanup_failures:
        # Cleanup failures are reported, never hidden.
        raise VerificationError(
            "acceptance capture cleanup failed: %s" % "; ".join(cleanup_failures))

    outcome_pass = (not result["timed_out"]
                    and result["exit_status"] == expected_exit_status)
    truncated = transcripts["stdout"]["truncated"] or \
        transcripts["stderr"]["truncated"]
    if result["timed_out"]:
        verdict = "BLOCKED"
        detail = ("acceptance command exceeded its bounded timeout of %ds; "
                  "the result could not be judged" % timeout_seconds)
    elif truncated:
        verdict = "BLOCKED"
        detail = ("acceptance output exceeded the %d byte transcript cap; the "
                  "observed output is incomplete, so acceptance cannot be "
                  "verified and VERIFIED is not permitted"
                  % transcripts["stdout"]["cap_bytes"])
    elif outcome_pass:
        verdict = "PASS"
        detail = "acceptance command exited %r as expected" % (
            result["exit_status"],)
    else:
        verdict = "FAIL"
        detail = ("acceptance command exited %r, expected %r"
                  % (result["exit_status"], expected_exit_status))
    return {
        "verdict": verdict,
        "detail": detail,
        "exit_status": result["exit_status"],
        "timed_out": result["timed_out"],
        "transcripts": transcripts,
    }


def persist(task_id, command, expected_exit_status, verdict, detail,
            exit_status, stdout_ref, stderr_ref, evidence_id, root=None):
    """Write the verification evidence artefact; return its ref and digest."""
    scrub.assert_clean({"command": list(command), "detail": detail},
                       "verification evidence for %s" % task_id)
    payload = {
        "schema": "sps2.p17-verification-output/v1",
        "task_id": task_id,
        "evidence_id": evidence_id,
        "verifier": VERIFIER,
        "command": list(command),
        "expected_exit_status": expected_exit_status,
        "actual_exit_status": exit_status,
        "verdict": verdict,
        "detail": detail,
        "independence_statement": INDEPENDENCE_STATEMENT,
        "stdout_ref": stdout_ref,
        "stderr_ref": stderr_ref,
        "verified_at": state.now(),
        "note": ("Acceptance judgement. This artefact records the verifier's "
                 "output only; it is not evidence that the executing agent "
                 "behaved correctly."),
    }
    task_dir = state.task_dir(task_id, root)
    evidence_dir = os.path.join(task_dir, "evidence")
    if not os.path.isdir(evidence_dir):
        os.makedirs(evidence_dir)
    state.write_json(os.path.join(evidence_dir, "verification-output.json"),
                     payload)
    import hashlib
    path = os.path.join(evidence_dir, "verification-output.json")
    with open(path, "rb") as handle:
        return {"ref": "evidence/verification-output.json",
                "sha256": hashlib.sha256(handle.read()).hexdigest()}


def record_block(task_id, command, expected_exit_status, verdict, evidence_id,
                 verified_at=None):
    """Build the schema-conformant verification object for the task record."""
    return {
        "verifier": VERIFIER,
        "acceptance_command": list(command),
        "result": verdict,
        "independence_statement": INDEPENDENCE_STATEMENT,
        "evidence_ref": evidence_id,
        "verified_at": verified_at or state.now(),
    }
