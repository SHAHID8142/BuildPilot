#!/usr/bin/env python3
"""SPS 2.0 P5 project-local capability registry access.

Agent-neutral by construction: this module contains no reference to any
specific coding agent, imports nothing outside the Python standard library,
and performs no network access and no machine-global writes.

It is the single read path the integration layer uses to reach the capability
registry, and it exposes the full provenance-to-verification trace chain so a
capability can never be consumed without its justification.
"""
import json
import re
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# The ordered trace every capability must remain followable through.
TRACE_CHAIN = [
    "capability", "provenance", "security", "licence", "evidence",
    "requirements", "approval", "selection", "implementation", "verification",
]

# Lifecycle states that assert the capability is actually running. The core
# must never assert these on a capability's behalf.
RUNTIME_STATES = {"INSTALLED", "ACTIVE"}


class RegistryError(Exception):
    """Raised when the registry cannot be read or is structurally unusable."""


def registry_path():
    return os.path.join(REPO, "sps2", "capability", "registry.json")


def load_registry(path=None):
    """Load the project-local capability registry. Read-only."""
    p = path or registry_path()
    try:
        with open(p) as fh:
            reg = json.load(fh)
    except (OSError, ValueError) as exc:
        raise RegistryError("registry unreadable: %s" % type(exc).__name__)
    if not isinstance(reg, dict) or not isinstance(reg.get("capabilities"),
                                                  list):
        raise RegistryError("registry is not a capability document")
    return reg


def capabilities(reg=None):
    """Return the capability list, validating it is a list of objects."""
    reg = reg if reg is not None else load_registry()
    caps = reg.get("capabilities")
    if not isinstance(caps, list):
        raise RegistryError("capabilities is not a list")
    for c in caps:
        if not isinstance(c, dict):
            raise RegistryError("capability entry is not an object")
    return caps


def by_id(capability_id, reg=None):
    """Return one capability, or None. Never fabricates a missing record."""
    for c in capabilities(reg):
        if c.get("capability_id") == capability_id:
            return c
    return None


def promoted(reg=None):
    """Capabilities whose computed promotion decision is PROMOTED.

    This reads the recorded decision. It does not re-evaluate the gate and it
    does not promote anything.
    """
    out = []
    for c in capabilities(reg):
        pa = c.get("promotion_assessment") or {}
        if pa.get("promotion_decision") == "PROMOTED_TO_PRODUCTION":
            out.append(c)
    return out


def deferred(reg=None):
    """Capabilities explicitly classified as not promoted."""
    out = []
    for c in capabilities(reg):
        pa = c.get("promotion_assessment") or {}
        if pa.get("recommendation") in ("DEFER", "REJECT"):
            out.append(c)
    return out


def approval_is_user_attributable(approval):
    """Core-neutral approval attribution check.

    The core deliberately does NOT know what an agent name looks like. It only
    requires an APPROVED state with a non-empty decider and a date. The
    agent-attribution control lives in governance/attribution.py and is
    injected as a stricter predicate by the integration layer.
    """
    a = approval or {}
    if a.get("state") != "APPROVED":
        return False
    who = (a.get("decided_by") or "").strip()
    return bool(who) and bool((a.get("decided_on") or "").strip())


def trace(cap, approver_ok=None):
    """Return the provenance-to-verification trace for one capability.

    Every link must resolve to a real value. An unresolved link is reported as
    False rather than being silently treated as satisfied.

    `approver_ok` is an optional stricter approval predicate supplied by the
    governance layer. When omitted, the core-neutral check is used.
    """
    check_approval = approver_ok or approval_is_user_attributable
    sel = cap.get("selection") or {}
    checks = {
        "capability": bool(cap.get("capability_id")) and bool(cap.get("name")),
        "provenance": bool((cap.get("provenance") or {}).get("origin")),
        "security": bool((cap.get("security") or {}).get("evidence")),
        "licence": bool((cap.get("licence_evidence") or "").strip()),
        "evidence": bool(cap.get("evidence")),
        "requirements": bool(cap.get("linked_requirements")),
        "approval": bool(check_approval(cap.get("approval"))),
        "selection": bool(sel.get("selection_id")),
        "implementation": bool((cap.get("provenance") or {})
                               .get("repository_relative_path")),
        "verification": bool((cap.get("verification") or {}).get("evidence")),
    }
    missing = [k for k in TRACE_CHAIN if not checks.get(k)]
    return checks, missing


def claims_runtime(cap):
    """True if the record asserts an installed or active runtime state.

    The integration layer must refuse to treat such a record as merely
    integrated, because runtime activation needs its own approved transition.
    """
    return cap.get("lifecycle_state") in RUNTIME_STATES


def counts(reg=None):
    reg = reg if reg is not None else load_registry()
    c = reg.get("counts") or {}
    return {
        "total": c.get("total"),
        "promoted": c.get("promoted"),
        "candidate": c.get("candidate"),
        "deferred": c.get("deferred"),
    }