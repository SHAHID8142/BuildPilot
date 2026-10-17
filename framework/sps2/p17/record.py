#!/usr/bin/env python3
"""P17 task record assembly and structural self-check (REQ-P17-10 / SEC-P17-11).

The task record conforms to framework.sps2.p17-task-record/v1
(framework/sps2/schemas/p17-task-record.schema.json). Because the implementation is
standard-library only, there is no JSON Schema engine at runtime: this module
re-implements the schema's STRUCTURAL subset (required properties, enumerated
values, patterns, array constraints, and the lifecycle-state conditionals)
and refuses to write a record that violates it. Fail closed.

Full Draft 2020-12 validation of generated records is a test-suite concern and
runs against the ambient ajv; it is not a runtime dependency.

WHAT THIS MODULE CANNOT DO (SEC-P17-11): prove that a transcript exists at its
referenced path, that a digest matches its artefact, that verification was
genuinely independent, that secrets are absent, or that an approval is a real
User act. `verify_integrity` recomputes digests on demand; authenticity remains
a runtime gate obligation.

Standard library only.
"""
import hashlib
import os
import re

from . import scrub, state

STATUSES = ("PLANNED", "AWAITING_USER_APPROVAL", "IN_PROGRESS", "BLOCKED",
            "FAILED", "VERIFIED", "REJECTED")
OUTCOMES = ("COMPLETED", "FAILED", "TIMEOUT", "KILLED")
RESULTS = ("PASS", "FAIL", "BLOCKED")
VERIFIERS = ("OBJECTIVE_COMMAND", "INDEPENDENT_AGENT", "USER")
APPROVAL_STATES = ("APPROVED", "REJECTED")
PRE_EXECUTION_STATUSES = ("PLANNED", "AWAITING_USER_APPROVAL")

TASK_ID_RE = re.compile(r"^TASK-P17-\d{4}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_ROOT = ("task_id", "status", "goal", "plan", "agent_selection",
                 "created_at", "updated_at", "digests")
ALLOWED_ROOT = set(REQUIRED_ROOT) | {
    "required_capabilities", "execution", "verification", "approval",
    "blocked_reason",
}


class RecordInvalid(Exception):
    """The record violates the structural contract; it is not written."""

    def __init__(self, violations):
        self.violations = list(violations)
        super(RecordInvalid, self).__init__(
            "task record violates framework.sps2.p17-task-record/v1: %s"
            % "; ".join(self.violations))


def _blank(value):
    return not (value or "").strip()


def violations(doc):
    """Return the list of structural violations (empty when conformant)."""
    problems = []
    if not isinstance(doc, dict):
        return ["record is not an object"]
    for key in REQUIRED_ROOT:
        if key not in doc:
            problems.append("missing required property %r" % key)
    for key in doc:
        if key not in ALLOWED_ROOT:
            problems.append("additional property %r is not allowed" % key)
    if doc.get("status") not in STATUSES:
        problems.append("status %r is not an allowed value" % doc.get("status"))
    if not TASK_ID_RE.match(doc.get("task_id") or ""):
        problems.append("task_id %r does not match TASK-P17-NNNN"
                        % doc.get("task_id"))
    if _blank(doc.get("goal")):
        problems.append("goal is blank")
    plan = doc.get("plan")
    if not isinstance(plan, list) or not plan:
        problems.append("plan must be a non-empty array")
    else:
        for index, step in enumerate(plan, start=1):
            if not isinstance(step, dict):
                problems.append("plan step %d is not an object" % index)
                continue
            for key in ("step_id", "description", "required_capabilities",
                        "status"):
                if key not in step:
                    problems.append("plan step %d missing %r" % (index, key))
            if _blank(step.get("description")):
                problems.append("plan step %d has a blank description" % index)
    selection = doc.get("agent_selection")
    if not isinstance(selection, dict):
        problems.append("agent_selection must be an object")
    else:
        for key in ("discovered_at", "available_agents"):
            if key not in selection:
                problems.append("agent_selection missing %r" % key)
        agents = selection.get("available_agents")
        if not isinstance(agents, list) or not agents:
            problems.append("agent_selection.available_agents must be non-empty")
    digests = doc.get("digests")
    if not isinstance(digests, dict) or not HEX64_RE.match(
            digests.get("plan_sha256") or ""):
        problems.append("digests.plan_sha256 must be a 64-hex digest")
    for key in ("created_at", "updated_at"):
        if _blank(doc.get(key)):
            problems.append("%s is blank" % key)

    execution = doc.get("execution")
    verification = doc.get("verification")
    approval = doc.get("approval")
    status = doc.get("status")

    # Lifecycle conditionals (mirrors of the schema's allOf entries).
    if status in PRE_EXECUTION_STATUSES:
        for name, value in (("execution", execution),
                            ("verification", verification),
                            ("approval", approval)):
            if value is not None:
                problems.append("%s is a %s state and must not carry %s"
                                % (status, status, name))
    if status in ("IN_PROGRESS", "FAILED") and execution is None:
        problems.append("%s requires an execution record" % status)
    if status == "BLOCKED" and _blank(doc.get("blocked_reason")):
        problems.append("BLOCKED requires a non-blank blocked_reason")
    if status == "VERIFIED":
        if verification is None:
            problems.append("VERIFIED requires a verification record")
        elif verification.get("result") != "PASS":
            problems.append("VERIFIED requires verification.result PASS")
    if status == "REJECTED":
        if approval is None:
            problems.append("REJECTED requires an approval record")
        elif approval.get("state") != "REJECTED":
            problems.append("REJECTED requires approval.state REJECTED")

    if execution is not None:
        if execution.get("outcome") not in OUTCOMES:
            problems.append("execution.outcome %r is not allowed"
                            % execution.get("outcome"))
        if not isinstance(execution.get("command"), list) or not execution.get(
                "command"):
            problems.append("execution.command must be a non-empty argv array")
        try:
            if int(execution.get("timeout_seconds", 0)) < 1:
                problems.append("execution.timeout_seconds must be >= 1")
        except (TypeError, ValueError):
            problems.append("execution.timeout_seconds must be an integer")
        if execution.get("outcome") == "COMPLETED":
            if not execution.get("ended_at"):
                problems.append("a COMPLETED execution requires ended_at")
            if execution.get("exit_status") is None:
                problems.append("a COMPLETED execution requires exit_status")

    if verification is not None:
        if verification.get("result") not in RESULTS:
            problems.append("verification.result %r is not allowed"
                            % verification.get("result"))
        if verification.get("verifier") not in VERIFIERS:
            problems.append("verification.verifier %r is not allowed"
                            % verification.get("verifier"))
        if _blank(verification.get("independence_statement")):
            problems.append("verification requires an independence statement")
    return problems


def write(task_id, doc, root=None):
    """Validate structurally and fail closed; then persist atomically."""
    problems = violations(doc)
    if problems:
        raise RecordInvalid(problems)
    scrub.assert_clean(doc, "task record for %s" % task_id)
    path = os.path.join(state.task_dir(task_id, root), "record.json")
    state.write_json(path, doc)
    return path


def load(task_id, root=None):
    """Load a record, failing closed on a missing OR malformed file."""
    path = os.path.join(state.task_dir(task_id, root), "record.json")
    if not os.path.exists(path):
        raise RecordInvalid(["no record for %s at %s" % (task_id, path)])
    try:
        return state.read_json(path)
    except ValueError as exc:            # malformed JSON: never a crash
        raise RecordInvalid(["record for %s is malformed JSON (%s)"
                             % (task_id, exc)])
    except OSError as exc:               # unreadable file: never a crash
        raise RecordInvalid(["record for %s could not be read (%s)"
                             % (task_id, exc)])


def planned_record(task_id, goal, capabilities, plan_ref, discovery_snapshot,
                   selection, root=None):
    """Assemble the initial PLANNED record."""
    return {
        "task_id": task_id,
        "status": "PLANNED",
        "goal": goal,
        "required_capabilities": sorted(set(capabilities or [])),
        "plan": plan_ref.get("steps", []),
        "agent_selection": {
            "discovered_at": discovery_snapshot.get("discovered_at", state.now()),
            "available_agents": [
                {
                    "agent_id": probe["agent_id"],
                    "available": bool(probe.get("available")),
                    "version": probe.get("version"),
                    "probe_method": probe.get("probe_method"),
                    "probed_at": probe.get("probed_at", state.now()),
                }
                for probe in discovery_snapshot.get("agents", [])
            ],
            "selected_agent": (selection or {}).get("selected_agent"),
            "selection_rationale": (selection or {}).get("selection_rationale"),
            "selection_fingerprint": (selection or {}).get("selection_fingerprint"),
            "selected_at": state.now() if selection else None,
        },
        "created_at": state.now(),
        "updated_at": state.now(),
        "digests": {
            "plan_sha256": plan_ref["sha256"],
            "stdout_sha256": None,
            "stderr_sha256": None,
            "evidence_sha256": None,
        },
    }


def verify_integrity(task_id, root=None):
    """SEC-P17-11: recompute digests and re-check structural completeness.

    Reports mismatches and missing artefacts. Detection of corruption is not a
    claim of authenticity: an intact digest proves bytes were not altered, not
    that the bytes are the right ones.
    """
    report = {"task_id": task_id, "findings": [], "checked": []}
    try:
        doc = load(task_id, root)
    except RecordInvalid as exc:
        report["findings"].append({"kind": "INCOMPLETE_RECORD", "detail": str(exc)})
        return report

    problems = violations(doc)
    if problems:
        report["findings"].append({"kind": "INCOMPLETE_RECORD",
                                   "detail": "; ".join(problems)})

    task_dir = state.task_dir(task_id, root)
    digests = doc.get("digests") or {}
    plan_path = os.path.join(task_dir, "plan.json")
    if os.path.exists(plan_path):
        with open(plan_path, "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
        report["checked"].append("plan.json")
        if actual != digests.get("plan_sha256"):
            report["findings"].append({
                "kind": "INTEGRITY_MISMATCH", "artefact": "plan.json",
                "detail": "recorded %s but on-disk %s"
                          % (digests.get("plan_sha256"), actual)})
    else:
        report["findings"].append({"kind": "MISSING_ARTEFACT",
                                   "artefact": "plan.json",
                                   "detail": "recorded plan digest but no file"})

    for key, name in (("stdout_sha256", "stdout.log"),
                      ("stderr_sha256", "stderr.log")):
        expected = digests.get(key)
        path = os.path.join(task_dir, name)
        if not expected:
            continue
        if not os.path.exists(path):
            report["findings"].append({"kind": "MISSING_ARTEFACT",
                                       "artefact": name,
                                       "detail": "digest recorded, file absent"})
            continue
        with open(path, "rb") as handle:
            actual = hashlib.sha256(handle.read()).hexdigest()
        report["checked"].append(name)
        if actual != expected:
            report["findings"].append({
                "kind": "INTEGRITY_MISMATCH", "artefact": name,
                "detail": "recorded %s but on-disk %s" % (expected, actual)})

    # Slice 2: every artefact whose digest is recorded must be recomputed.
    # The verification evidence artefact is recorded in the record itself.
    evidence_digest = digests.get("evidence_sha256")
    evidence_path = os.path.join(task_dir, "evidence",
                                 "verification-output.json")
    if evidence_digest:
        if not os.path.exists(evidence_path):
            report["findings"].append({"kind": "MISSING_ARTEFACT",
                                       "artefact": evidence_path,
                                       "detail": "evidence digest recorded, "
                                                 "artefact absent"})
        else:
            actual = state.sha256_file(evidence_path)
            report["checked"].append("evidence/verification-output.json")
            if actual != evidence_digest:
                report["findings"].append({
                    "kind": "INTEGRITY_MISMATCH",
                    "artefact": "evidence/verification-output.json",
                    "detail": "recorded %s but on-disk %s"
                              % (evidence_digest, actual)})

    # Acceptance transcripts and original-stream digests live in the
    # integrity sidecar (the record schema has no field for them and must not
    # be amended by implementation code).
    sidecar = state.read_integrity(task_id, root)
    # The attempt journal is part of the trustworthiness of the record: an
    # untrustworthy journal means the execution history cannot be relied on.
    try:
        state.stage_state(task_id, root)
        report["checked"].append("state.json")
    except state.StateError as exc:
        report["findings"].append({"kind": "UNTRUSTWORTHY_JOURNAL",
                                   "artefact": "state.json",
                                   "detail": str(exc)})
    for key, name in (("acceptance_stdout_sha256", "acceptance-stdout.log"),
                      ("acceptance_stderr_sha256", "acceptance-stderr.log")):
        expected = sidecar.get(key)
        path = os.path.join(task_dir, "evidence", name)
        if not expected:
            if os.path.exists(path):
                report["findings"].append({
                    "kind": "INCOMPLETE_RECORD", "artefact": name,
                    "detail": "acceptance transcript present but its digest is "
                              "not recorded"})
            continue
        if not os.path.exists(path):
            report["findings"].append({"kind": "MISSING_ARTEFACT",
                                       "artefact": "evidence/" + name,
                                       "detail": "digest recorded, file absent"})
            continue
        actual = state.sha256_file(path)
        report["checked"].append("evidence/" + name)
        if actual != expected:
            report["findings"].append({
                "kind": "INTEGRITY_MISMATCH", "artefact": "evidence/" + name,
                "detail": "recorded %s but on-disk %s" % (expected, actual)})
    return report
