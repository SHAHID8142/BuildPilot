#!/usr/bin/env python3
"""P17 deterministic agent selection with recorded rationale (REQ-P17-04).

Determinism contract: the same required capabilities plus the same discovery
snapshot always yield the same selected agent and the same SHA-256 selection
fingerprint. The fingerprint is computed over the ordered candidate list, not
over wall-clock time, environment, or dict ordering, so repeated runs agree
byte for byte (acceptance criterion AC-3).

Selection is impossible when no available agent satisfies the required
capabilities: that is an explicit auditable failure, never an arbitrary
choice and never a fallback to an executable outside the allowlist.

Ordering rule: candidates that satisfy every required capability rank ahead of
those that do not; ties break on agent_id lexicographically. No popularity and
no recency: those are capability-registry concepts and are not inputs here.

Standard library only.
"""
import hashlib


class SelectionError(Exception):
    """Selection could not be performed as specified."""


def fingerprint(ordered):
    """Stable SHA-256 fingerprint over the ordered candidate list."""
    payload = "|".join("%s:%d" % (entry["agent_id"], entry["score"])
                       for entry in ordered)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _capabilities(entry):
    caps = entry.get("capabilities") or []
    return set(caps)


def _satisfies(entry, required):
    return required.issubset(_capabilities(entry))


def select(allowlist, discovery_snapshot, required_capabilities):
    """Return (selection, ordered_candidates, excluded).

    selection is None when no candidate is eligible. excluded explains every
    non-selected allowlist entry and why, so the rationale is complete.
    """
    required = set(required_capabilities or [])
    discovered = {a["agent_id"]: a for a in discovery_snapshot.get("agents", [])}

    ordered = []
    excluded = []
    for entry in allowlist.get("agents", []):
        agent_id = entry["agent_id"]
        probe = discovered.get(agent_id)
        if probe is None:
            excluded.append({"agent_id": agent_id,
                             "reason": "not present in discovery snapshot"})
            continue
        if not probe.get("available"):
            excluded.append({
                "agent_id": agent_id,
                "reason": "unavailable at runtime (probed %s): %s"
                          % (probe.get("probed_at"), probe.get("note")
                             or "not found on PATH"),
            })
            continue
        if not _satisfies(entry, required):
            missing = sorted(required - _capabilities(entry))
            excluded.append({
                "agent_id": agent_id,
                "reason": "missing required capabilities: %s" % ",".join(missing),
            })
            continue
        ordered.append({
            "agent_id": agent_id,
            "score": len(_capabilities(entry) & required),
            "resolved_path": probe.get("resolved_path"),
            "executable_sha256": probe.get("executable_sha256"),
            "resolution_mode": probe.get("resolution_mode"),
            "version": probe.get("version"),
        })

    ordered.sort(key=lambda item: (-item["score"], item["agent_id"]))
    if not ordered:
        return None, ordered, excluded

    chosen = ordered[0]
    others = [o["agent_id"] for o in ordered[1:]]
    rationale = (
        "Selected %s (score %d, satisfying all %d required capabilities: %s). "
        "It was probed available at runtime at %s. "
        "%s"
        % (chosen["agent_id"], chosen["score"], len(required),
           ", ".join(sorted(required)) or "(none)",
           discovered[chosen["agent_id"]].get("probed_at"),
           ("Lower-ranked eligible alternatives: " + ", ".join(others) + ".")
           if others else "No other eligible alternative."))
    selection = {
        "selected_agent": chosen["agent_id"],
        "resolved_path": chosen["resolved_path"],
        "executable_sha256": chosen["executable_sha256"],
        "resolution_mode": chosen["resolution_mode"],
        "version": chosen["version"],
        "selection_rationale": rationale,
        "selection_fingerprint": fingerprint(ordered),
        "excluded": excluded,
    }
    return selection, ordered, excluded
