#!/usr/bin/env python3
"""P17 task intake and strict task validation (REQ-P17-01).

Intake is the trust boundary: invalid input must never reach plan generation
or execution. Every failure here is an explicit rejection with a non-zero exit
and no partial record is created.

Validated, and rejected when not satisfied:
  - the input parses as JSON and contains only known fields (strict: unknown
    fields are rejected, not ignored);
  - goal is a non-blank string;
  - required_capabilities is a list of unique non-blank strings;
  - acceptance.command is a non-empty argv array of non-blank strings - a
    shell string is never accepted;
  - acceptance.command[0] must NOT be an allowlisted agent executable: the
    verifying command may not be the agent being verified (SEC-P17-07
    structural independence);
  - acceptance.command[0] must resolve on PATH or be a repository-internal
    path inside the project boundary;
  - every path-like acceptance argument resolves inside the project boundary
    (PREVENTIVE P2, at intake time rather than at execution time);
  - expected_exit_status is an integer (default 0);
  - timeout_seconds is an integer >= 1;
  - the input contains no credential-like material: credential-bearing input
    is rejected, never stored (SEC-P17-06).

Standard library only.
"""
import json
import os
import shutil

from . import confinement, discovery, scrub

ALLOWED_TASK_FIELDS = {"goal", "required_capabilities", "acceptance",
                       "timeout_seconds"}
DEFAULT_TIMEOUT_SECONDS = 300
MAX_TIMEOUT_SECONDS = 3600


class IntakeRejected(Exception):
    """Task input was rejected. Fail closed; nothing is persisted."""


def load_task_file(path):
    if not os.path.exists(path):
        raise IntakeRejected("task file not found: %s" % path)
    if not os.path.isfile(path):
        raise IntakeRejected("task file is not a regular file: %s" % path)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except ValueError as exc:
        raise IntakeRejected("task file %s is not valid JSON: %s" % (path, exc))
    except OSError as exc:
        raise IntakeRejected("task file %s could not be read: %s" % (path, exc))
    if not isinstance(data, dict):
        raise IntakeRejected("task file %s must contain a JSON object" % path)
    return data


def validate(task, boundary, allowlist):
    """Validate and normalise a task definition; raise IntakeRejected.

    allowlist is the allowlist IN EFFECT for this run (not necessarily the
    default one), so the structural-independence check below applies to
    exactly the executables this run could ever invoke.
    """
    unknown = sorted(set(task) - ALLOWED_TASK_FIELDS)
    if unknown:
        raise IntakeRejected(
            "unknown task field(s) %s; accepted fields are %s"
            % (",".join(unknown), ",".join(sorted(ALLOWED_TASK_FIELDS))))

    if scrub.classify(json.dumps(task)):
        raise IntakeRejected(
            "task input contains credential-like material and is rejected, "
            "not stored; secrets must never appear in task input")

    goal = task.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        raise IntakeRejected("goal is missing or blank")

    capabilities = task.get("required_capabilities", [])
    if not isinstance(capabilities, list):
        raise IntakeRejected("required_capabilities must be a list")
    for item in capabilities:
        if not isinstance(item, str) or not item.strip():
            raise IntakeRejected(
                "required_capabilities entries must be non-blank strings")
    if len(set(capabilities)) != len(capabilities):
        raise IntakeRejected("required_capabilities contains duplicates")

    acceptance = task.get("acceptance")
    if not isinstance(acceptance, dict):
        raise IntakeRejected("acceptance is required and must be an object")
    command = acceptance.get("command")
    if not isinstance(command, list) or not command:
        raise IntakeRejected(
            "acceptance.command is required and must be a non-empty argv array")
    for index, token in enumerate(command):
        if not isinstance(token, str) or not token.strip():
            raise IntakeRejected(
                "acceptance.command[%d] is blank" % index)
    if any(isinstance(token, str) and
           (";" in token or "&&" in token or "|" in token or "`" in token or
            "$(" in token)
           for token in command):
        raise IntakeRejected(
            "acceptance.command contains shell metacharacters; argv-only "
            "execution is required (no shell string is ever accepted)")

    expected = acceptance.get("expected_exit_status", 0)
    if isinstance(expected, bool) or not isinstance(expected, int):
        raise IntakeRejected("acceptance.expected_exit_status must be an integer")

    timeout = task.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        raise IntakeRejected("timeout_seconds must be an integer >= 1")
    if timeout > MAX_TIMEOUT_SECONDS:
        raise IntakeRejected("timeout_seconds must be <= %d" % MAX_TIMEOUT_SECONDS)

    # SEC-P17-07: the acceptance command may never be the agent being verified.
    agent_ids = {entry.get("agent_id") for entry in allowlist.get("agents", [])}
    if command[0] in agent_ids:
        raise IntakeRejected(
            "acceptance.command[0] %r is an allowlisted agent executable; the "
            "verifying command may not be the agent being verified "
            "(SEC-P17-07 structural independence)" % command[0])

    resolved_zero = shutil.which(command[0])
    if resolved_zero is None:
        candidate = confinement.resolve(command[0], boundary)
        if not confinement.inside_boundary(candidate, boundary):
            raise IntakeRejected(
                "acceptance.command[0] %r is neither a resolvable executable "
                "nor a path inside the project boundary" % command[0])

    # PREVENTIVE P2 at intake: no acceptance argument may point outside.
    try:
        confinement.check_argv_paths(command, boundary, base=boundary,
                                     exempt=(0,))
    except confinement.ConfinementViolation as exc:
        raise IntakeRejected("acceptance command rejected: %s" % exc.detail)

    return {
        "goal": goal.strip(),
        "required_capabilities": sorted(set(capabilities)),
        "acceptance": {"command": list(command),
                       "expected_exit_status": expected},
        "timeout_seconds": timeout,
    }
