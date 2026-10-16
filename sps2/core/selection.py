#!/usr/bin/env python3
"""SPS 2.0 P5 deterministic project-local capability selection.

Agent-neutral. Standard library only. No network, no global writes.

Selection is deterministic: identical input yields an identical ordering and an
identical fingerprint. Popularity and recency remain TIE-BREAKERS_ONLY and can
never outrank an evidence-weighted score difference.

Only capabilities with a recorded promotion decision of PROMOTED_TO_PRODUCTION
are eligible. Selection cannot promote anything; it can only choose among what
the gate already promoted.
"""
import hashlib
import importlib.util
import os

from registry_api import capabilities, promoted

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

_ENGINE = None


def _engine():
    """Load the ranking engine once. Pure logic, no side effects."""
    global _ENGINE
    if _ENGINE is None:
        path = os.path.join(REPO, "sps2", "capability", "engine.py")
        spec = importlib.util.spec_from_file_location("sps2_engine", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _ENGINE = mod
    return _ENGINE


def eligible(reg=None):
    """Return the promoted capabilities that are eligible for selection."""
    return promoted(reg)


def select(requirement, reg=None):
    """Return a deterministic, fully explained selection.

    Only promoted capabilities are considered. A capability with an
    unresolved blocking gate is never eligible, so a deferred candidate such as
    CAP-P03-005 can never be selected.
    """
    reg = reg if reg is not None else None
    pool = eligible(reg)
    ranked = _engine().rank(pool, requirement or {})
    for r in ranked:
        r["eligibility"] = "PROMOTED"
        r["selection_reason"] = r.get("explanation", "")
    return ranked


def fingerprint(ranks):
    """Stable fingerprint of an ordering, used to prove determinism."""
    payload = "|".join("%s:%s" % (r["capability_id"], r["score"])
                       for r in ranks)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def selection_record(selection_id, requirement, reg=None, note=None):
    """Build a complete, auditable selection record.

    Every ranked entry carries its score, its full breakdown, the contributing
    weights and an explanation. Nothing is summarised away.
    """
    ranks = select(requirement, reg)
    all_caps = capabilities(reg)
    known = {c["capability_id"]: c for c in all_caps}
    excluded = []
    for c in all_caps:
        cid = c["capability_id"]
        if cid in known and cid not in {r["capability_id"] for r in ranks}:
            pa = c.get("promotion_assessment") or {}
            excluded.append({
                "capability_id": cid,
                "name": c.get("name"),
                "lifecycle_state": c.get("lifecycle_state"),
                "recommendation": pa.get("recommendation"),
                "blocking_gates": pa.get("blocking_gates"),
                "promotion_decision": pa.get("promotion_decision"),
                "exclusion_reason": (
                    "not promoted: blocked by gate(s) %s"
                    % ",".join(pa.get("blocking_gates") or [])
                    if pa.get("blocking_gates") else
                    "not promoted to production"),
            })
    return {
        "schema": "sps2.selection/v1",
        "selection_id": selection_id,
        "generated_by": "sps2/core/selection.py",
        "agent_neutral": True,
        "scope": "PROJECT_LOCAL",
        "requirement": requirement or {},
        "popularity_role": "TIE_BREAKER_ONLY",
        "recency_role": "TIE_BREAKER_ONLY",
        "ranking": ranks,
        "ranking_fingerprint": fingerprint(ranks),
        "excluded_from_selection": excluded,
        "approval": {
            "state": "PENDING_USER_APPROVAL",
            "note": "Selection is computed, not approved. No capability was "
                    "promoted by this record.",
        },
        "note": note or "",
    }