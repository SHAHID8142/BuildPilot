#!/usr/bin/env python3
"""SPS 2.0 P6 technology-readiness evaluator.

Roadmap P6 deliverable: a readiness evaluator that gates technology use.

Agent-neutral by construction. Standard library only. No network access, no
installation, and no machine-global writes. Pure logic over an explicit cache.

The rule comes from sps2/research/cache.json: a technology must not be
selected until a research entry exists with readiness SUFFICIENT. This module
computes that readiness rather than trusting a stored label, so a stale or
optimistic cache entry cannot pass.

Deliberately absent, per User decision D-P6-2: any notion of a runtime, a
resident process, installation, or an ACTIVE/INSTALLED lifecycle.
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# Mirrors cache.json gate.sufficiency_requires.
REQUIRED_COVERAGE = (
    "official_documentation", "current_version", "compatibility",
    "ecosystem", "recommended_practices", "security_considerations",
    "relevant_tooling", "mcp_tool_availability", "testing_approach",
    "deployment_implications",
)

# A source of rank <= 4 is required to establish sufficiency.
STRONGEST_ACCEPTABLE_RANK = 4

SUFFICIENT = "SUFFICIENT"
PARTIAL = "PARTIAL"
INSUFFICIENT = "INSUFFICIENT"
UNRESEARCHED = "UNRESEARCHED"

READINESS = (SUFFICIENT, PARTIAL, INSUFFICIENT, UNRESEARCHED)

# Only SUFFICIENT may be selected. Everything else is blocked.
SELECTABLE = (SUFFICIENT,)


class CacheError(Exception):
    """Raised when the research cache cannot be read or is malformed."""


def cache_path():
    return os.path.join(REPO, "sps2", "research", "cache.json")


def load_cache(path=None):
    p = path or cache_path()
    try:
        with open(p) as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        raise CacheError("research cache unreadable: %s" % type(exc).__name__)
    if not isinstance(doc, dict) or not isinstance(doc.get("entries"), list):
        raise CacheError("research cache is not a cache document")
    return doc


def entries(cache=None):
    cache = cache if cache is not None else load_cache()
    out = []
    for e in cache["entries"]:
        if not isinstance(e, dict):
            raise CacheError("research entry is not an object")
        if not (e.get("technology_id") or "").strip():
            raise CacheError("research entry has no technology_id")
        out.append(e)
    return out


def by_id(technology_id, cache=None):
    """Return one entry, or None. Never fabricates a missing record."""
    for e in entries(cache):
        if e.get("technology_id") == technology_id:
            return e
    return None

def evaluate(entry):
    """Return (readiness, ordered_reasons). Deterministic and explanatory.

    The label is computed from the evidence, never read from a stored field.
    """
    if entry is None:
        return UNRESEARCHED, ["UNRESEARCHED: no research entry exists"]

    coverage = entry.get("coverage") or {}
    if not isinstance(coverage, dict):
        return INSUFFICIENT, ["MALFORMED: coverage is not an object"]

    missing = [k for k in REQUIRED_COVERAGE
               if str(coverage.get(k, "")).strip().upper() != "COVERED"]
    ranks = _ranks(entry)
    best = min(ranks) if ranks else None

    # An unresolved conflict hard-blocks the technology. This is what stops
    # an SEO threshold gap from ever becoming selectable.
    if entry.get("blocking_conflicts"):
        return INSUFFICIENT, [
            "BLOCKED_BY_UNRESOLVED_CONFLICT: %s"
            % ",".join(entry["blocking_conflicts"])]

    if best is None:
        return INSUFFICIENT, ["NO_SOURCES: entry cites no ranked source"]
    if best > STRONGEST_ACCEPTABLE_RANK:
        return PARTIAL, [
            "WEAK_SOURCES_ONLY: best rank %d exceeds %d"
            % (best, STRONGEST_ACCEPTABLE_RANK)]
    if missing:
        return PARTIAL, ["COVERAGE_INCOMPLETE: missing %s" % ",".join(missing)]

    reasons = [
        "all %d coverage areas COVERED" % len(REQUIRED_COVERAGE),
        "strongest source rank %d <= %d" % (best, STRONGEST_ACCEPTABLE_RANK),
    ]
    if entry.get("researched_by_agent"):
        reasons.append("note: researched by an agent, User review pending")
    return SUFFICIENT, reasons


def is_selectable(technology_id, cache=None):
    """True only when the computed readiness is SUFFICIENT."""
    readiness, _reasons = evaluate(by_id(technology_id, cache))
    return readiness in SELECTABLE


def gate(technology_ids, cache=None):
    """Return (allowed, blocked) for a proposed set of technologies."""
    cache = cache if cache is not None else load_cache()
    allowed, blocked = [], []
    for t in technology_ids:
        readiness, reasons = evaluate(by_id(t, cache))
        if readiness in SELECTABLE:
            allowed.append({"technology_id": t, "readiness": readiness})
        else:
            blocked.append({"technology_id": t, "readiness": readiness,
                            "reasons": reasons})
    return allowed, blocked


def summary(cache=None):
    cache = cache if cache is not None else load_cache()
    counts = {SUFFICIENT: 0, PARTIAL: 0, INSUFFICIENT: 0, UNRESEARCHED: 0}
    detail = []
    for e in entries(cache):
        readiness, reasons = evaluate(e)
        counts[readiness] = counts.get(readiness, 0) + 1
        detail.append({"technology_id": e.get("technology_id"),
                       "readiness": readiness, "reasons": reasons})
    return {"total": len(entries(cache)), "counts": counts, "detail": detail}

def _ranks(e):
    """Source ranks cited by an entry, coerced to ints where possible."""
    out = []
    for s in e.get("sources") or []:
        if isinstance(s, dict) and s.get("rank") is not None:
            try:
                out.append(int(s["rank"]))
            except (TypeError, ValueError):
                continue
    return out