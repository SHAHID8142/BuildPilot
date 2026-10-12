#!/usr/bin/env python3
"""P17 ordered plan generation and persistence (REQ-P17-02).

Every accepted task carries an ordered plan with at least one step before any
execution. The plan is persisted to project-local state as a separate artefact
from the record, digested over its canonical serialisation, and gated: the
plan must be approved (GATE-P17-3 per-task approval) before execution starts.

Canonical form: json.dumps with sort_keys=True and fixed separators, so the
plan digest is reproducible byte for byte across runs and machines.

Standard library only.
"""
import hashlib
import json
import os

from . import scrub, state

STEP_ID_RE = state.STEP_ID_RE


class PlanError(Exception):
    """Plan generation or persistence failed."""


def canonical_bytes(plan):
    return json.dumps(plan, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def plan_digest(plan):
    return hashlib.sha256(canonical_bytes(plan)).hexdigest()


def _step(step_id, description, capabilities):
    return {
        "step_id": step_id,
        "description": description,
        "required_capabilities": sorted(set(capabilities or [])),
        "agent_id": None,
        "status": "PENDING",
        "depends_on": [],
        "output_summary": None,
    }


def build(goal, required_capabilities, acceptance_command):
    """Build the ordered plan for a task.

    Slice 1 plan shape (narrow, deterministic, one step per acceptance
    command): a single ordered step that performs the task under the
    selected agent and is judged by the objective acceptance command. The
    step declares the capabilities selection needs, so selection stays
    deterministic from the plan rather than from free-form intent.
    """
    capabilities = sorted(set(required_capabilities or []))
    description = "Execute task goal under the selected agent: %s" % goal
    if acceptance_command:
        description += " (acceptance: %s)" % " ".join(acceptance_command)
    step = _step("STEP-1", description, capabilities)
    return {
        "plan_version": "p17.plan/v1",
        "task_id": None,
        "created_at": state.now(),
        "approval_gated": True,
        "gate": "GATE-P17-3",
        "steps": [step],
    }


def persist(task_id, plan, root=None):
    """Write plan.json to project-local state; return ref + digest."""
    if not plan.get("steps"):
        raise PlanError("refusing to persist a plan with no steps")
    for index, step in enumerate(plan["steps"], start=1):
        if not STEP_ID_RE.match(step.get("step_id", "")):
            raise PlanError("step %d has a malformed step_id %r"
                            % (index, step.get("step_id")))
        if not (step.get("description") or "").strip():
            raise PlanError("step %d has a blank description" % index)
    scrub.assert_clean(plan, "plan for %s" % task_id)
    plan = dict(plan)
    plan["task_id"] = task_id
    path = os.path.join(state.task_dir(task_id, root), "plan.json")
    payload = canonical_bytes(plan)
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "wb") as handle:
        handle.write(payload)
    return {
        "ref": "plan.json",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "path": path,
    }


def verify_digest(task_id, root=None):
    """Recompute the plan digest from disk (SEC-P17-11 integrity)."""
    path = os.path.join(state.task_dir(task_id, root), "plan.json")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()
