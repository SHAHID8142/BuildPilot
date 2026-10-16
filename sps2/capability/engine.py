#!/usr/bin/env python3
"""SPS 2.0 P3 production capability promotion gate + selection engine.

Pure logic. No network, no installs, no machine-global writes.

Promotion gate: a capability may enter the PRODUCTION registry only when every
required field is present, structurally valid and evidence-backed. Deterministic:
the same input always yields the same verdict and the same ordered reasons.

Selection engine: ranks candidates using evidence-backed factors. Popularity and
recency are TIE-BREAKERS ONLY and can never outrank an evidence factor. Every
ranking emits an explanation. A forced user choice overrides automatic ranking,
subject to mandatory safety constraints that cannot be waived.
"""
import re
import os
import sys
# Agent-name tokens come from the single authoritative policy
# (sps2/governance/attribution_policy.json) via attribution.py.
# SPEC-2 consolidation: this module must not keep its own token list.
_GOVERNANCE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "governance")
if _GOVERNANCE not in sys.path:
    sys.path.insert(0, _GOVERNANCE)
import attribution as _ATTRIBUTION  # noqa: E402


LIFECYCLE = ["RESEARCHED", "CANDIDATE", "EVALUATED", "APPROVED", "INSTALLED",
             "VERIFIED", "ACTIVE", "STALE", "REJECTED", "DEFERRED", "REMOVED"]
SECURITY = ["VERIFIED_SAFE", "REVIEWED_LOW_RISK", "SUSPECTED_RISK", "VULNERABLE",
            "UNKNOWN"]
COMPAT = ["COMPATIBLE", "INCOMPATIBLE", "UNKNOWN"]
LICENCE = ["KNOWN_PERMISSIVE", "KNOWN_COPYLEFT", "KNOWN_PROPRIETARY",
           "UNDECLARED", "NOT_APPLICABLE"]
APPROVAL = ["NOT_REQUIRED", "PENDING_USER_APPROVAL", "APPROVED", "REJECTED"]
SCOPE = ["PROJECT_LOCAL", "GLOBAL"]
CONFIDENCE = ["HIGH", "MEDIUM", "LOW"]
FACT = ["FACT", "EVIDENCE", "INFERENCE", "UNKNOWN"]

# Mandatory safety constraints: a forced user choice CANNOT override these.
NON_OVERRIDABLE_SECURITY = {"VULNERABLE", "SUSPECTED_RISK"}

AGENTISH = _ATTRIBUTION.AGENTISH

CAP_ID = re.compile(r"^CAP-SPS-\d{3}$")

REQUIRED = ["capability_id", "name", "type", "domain", "purpose", "version",
            "source", "provenance", "licence", "security", "compatibility",
            "staleness", "install_scope", "evidence", "confidence",
            "lifecycle_state", "approval", "verification", "selection_policy"]


def _has(x, key):
    return isinstance(x, dict) and x.get(key) not in (None, "", [], {})


def promote(cap, known_sources=None):
    """Return (ok, ordered_reasons). Stable, deterministic, explanatory."""
    r = []
    known_sources = known_sources or set()

    if not isinstance(cap, dict):
        return False, ["MALFORMED: capability is not an object"]

    for f in REQUIRED:
        if not _has(cap, f):
            r.append("MISSING_FIELD: %s" % f)

    cid = cap.get("capability_id")
    if not (isinstance(cid, str) and CAP_ID.match(cid)):
        r.append("INVALID_ID: capability_id must match CAP-SPS-NNN")
    if cap.get("lifecycle_state") not in LIFECYCLE:
        r.append("INVALID_LIFECYCLE: %r" % cap.get("lifecycle_state"))
    if (cap.get("security") or {}).get("status") not in SECURITY:
        r.append("INVALID_SECURITY_STATE: %r"
                 % (cap.get("security") or {}).get("status"))
    if (cap.get("compatibility") or {}).get("status") not in COMPAT:
        r.append("INVALID_COMPATIBILITY: %r"
                 % (cap.get("compatibility") or {}).get("status"))
    if cap.get("licence") not in LICENCE:
        r.append("INVALID_LICENCE_STATE: %r" % cap.get("licence"))
    if cap.get("confidence") not in CONFIDENCE:
        r.append("INVALID_CONFIDENCE: %r" % cap.get("confidence"))
    if cap.get("install_scope") not in SCOPE:
        r.append("INVALID_SCOPE: %r" % cap.get("install_scope"))

    prov = cap.get("provenance") or {}
    if not _has(prov, "origin"):
        r.append("FABRICATED_PROVENANCE: provenance.origin missing")
    if not (isinstance(prov.get("fact_class"), str)
            and prov.get("fact_class") in FACT):
        r.append("UNCLASSIFIED_CLAIM: provenance.fact_class must be FACT, "
                 "EVIDENCE, INFERENCE or UNKNOWN")
    for k in ("source_refs", "research_refs", "evidence_refs"):
        if k in prov and prov[k] and known_sources:
            bad = [x for x in prov[k] if x not in known_sources]
            if bad:
                r.append("UNSUPPORTED_PROVENANCE: %s cites unknown %s" % (bad[0], k))
    if _has(prov, "commit") and not re.match(r"^[0-9a-f]{7,40}$", str(prov["commit"])):
        r.append("UNSUPPORTED_PROVENANCE: commit must be a hex sha")

    sec = cap.get("security") or {}
    if sec.get("status") == "VERIFIED_SAFE" and not _has(sec, "evidence"):
        r.append("UNSUPPORTED_SECURITY: VERIFIED_SAFE without explicit evidence")
    if sec.get("status") == "UNKNOWN" and cap.get("lifecycle_state") in (
            "APPROVED", "INSTALLED", "VERIFIED", "ACTIVE"):
        r.append("UNSUPPORTED_SECURITY: UNKNOWN security cannot back an active state")
    if sec.get("fact_class") == "FACT" \
       and sec.get("status") not in ("VERIFIED_SAFE", "REVIEWED_LOW_RISK"):
        r.append("UNSUPPORTED_SECURITY: FACT classification overstates a "
                 "non-verified state")

    if cap.get("licence") == "KNOWN_PERMISSIVE" \
       and not (cap.get("licence_evidence") or "").strip():
        r.append("MISSING_LICENCE_EVIDENCE: KNOWN_PERMISSIVE requires licence_evidence")
    if cap.get("licence") == "UNDECLARED" and cap.get("lifecycle_state") in (
            "APPROVED", "INSTALLED", "VERIFIED", "ACTIVE"):
        r.append("MISSING_LICENCE_STATE: UNDECLARED licence cannot back an active state")

    comp = cap.get("compatibility") or {}
    if comp.get("status") == "COMPATIBLE" and not _has(comp, "basis"):
        r.append("UNSUPPORTED_COMPATIBILITY: COMPATIBLE without a stated basis")
    if comp.get("status") == "COMPATIBLE" and not comp.get("agent_neutral", False):
        r.append("UNSUPPORTED_COMPATIBILITY: core capabilities must be agent-neutral")

    st = cap.get("staleness") or {}
    if st.get("state") == "STALE" and not st.get("review_due"):
        r.append("STALE_WITHOUT_REVIEW: STALE state requires review_due")
    if st.get("state") == "STALE" and cap.get("lifecycle_state") == "ACTIVE":
        r.append("STALE_AS_ACTIVE: a stale capability must not remain ACTIVE")

    ap = cap.get("approval") or {}
    if ap.get("state") not in APPROVAL:
        r.append("INVALID_APPROVAL_STATE: %r" % ap.get("state"))
    if ap.get("state") == "APPROVED":
        who = (ap.get("decided_by") or "").strip()
        if not who:
            r.append("MISSING_USER_ATTRIBUTION: APPROVED without decided_by")
        elif AGENTISH.search(who):
            r.append("AGENT_ATTRIBUTED_APPROVAL: %r is not a user" % who)
    if cap.get("lifecycle_state") in ("APPROVED", "INSTALLED", "VERIFIED",
                                      "ACTIVE") \
       and ap.get("state") != "APPROVED":
        r.append("MISSING_USER_APPROVAL: lifecycle %s requires APPROVED"
                 % cap.get("lifecycle_state"))

    if cap.get("install_scope") == "GLOBAL":
        who = (cap.get("global_installation_authorized_by") or "").strip()
        if not who:
            r.append("GLOBAL_WITHOUT_AUTHORIZATION: no global authorizer")
        elif AGENTISH.search(who):
            r.append("AGENT_ATTRIBUTED_APPROVAL: global authorizer %r is not a user" % who)

    ver = cap.get("verification") or {}
    if cap.get("lifecycle_state") in ("VERIFIED", "ACTIVE") \
       and not (ver.get("evidence") or []):
        r.append("UNVERIFIED_IMPLEMENTATION: %s without verification evidence"
                 % cap.get("lifecycle_state"))
    if ver.get("state") == "VERIFIED" and not (ver.get("evidence") or []):
        r.append("UNVERIFIED_IMPLEMENTATION: verification VERIFIED without evidence")

    if cap.get("origin") == "RESEARCH_ONLY":
        r.append("RESEARCH_ONLY_LEAK: a research-only record cannot be promoted")
    if cap.get("promoted_from_research_only") is True \
       and cap.get("research_promotion_approved_by") is None:
        r.append("RESEARCH_ONLY_LEAK: research promotion lacks an explicit authorizer")

    return (len(r) == 0), r


# ── determinism guard ───────────────────────────────────────────────────────
def ranking_fingerprint(ranks):
    """Stable fingerprint of a ranking; used to prove determinism."""
    import hashlib
    payload = "|".join("%s:%s" % (x["capability_id"], x["score"])
                       for x in ranks)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# ── ranking ─────────────────────────────────────────────────────────────────
# Evidence-weighted factors. Popularity and recency are NOT factors: they only
# break ties, and only after every evidence factor is equal.
WEIGHTS = {
    "requirement_fit": 30,
    "compatibility": 20,
    "security": 20,
    "licence": 10,
    "freshness": 8,
    "maintenance": 5,
    "provenance_confidence": 5,
    "verification": 2,
}
SEC_SCORE = {"VERIFIED_SAFE": 1.0, "REVIEWED_LOW_RISK": 0.75,
             "UNKNOWN": 0.25, "SUSPECTED_RISK": 0.1, "VULNERABLE": 0.0}
LIC_SCORE = {"KNOWN_PERMISSIVE": 1.0, "NOT_APPLICABLE": 1.0,
             "KNOWN_COPYLEFT": 0.5, "KNOWN_PROPRIETARY": 0.4,
             "UNDECLARED": 0.2}
FRESH_SCORE = {"CURRENT": 1.0, "UNKNOWN": 0.4, "STALE": 0.1}
MAINT_SCORE = {"ACTIVE": 1.0, "PASSIVE": 0.5, "UNKNOWN": 0.4, "ABANDONED": 0.0}
CONF_SCORE = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}
VERIF_SCORE = {"VERIFIED": 1.0, "UNVERIFIED": 0.4, "FAILED": 0.0}


def _fit(cap, requirement):
    """Deterministic requirement-fit score in [0,1]."""
    tags = set(requirement.get("required_capabilities") or [])
    domains = set(requirement.get("domains") or [])
    score = 0.0
    if cap.get("capability_id") in tags:
        score += 0.6
    if cap.get("domain") in domains:
        score += 0.3
    if cap.get("lifecycle_state") in ("ACTIVE", "VERIFIED", "INSTALLED"):
        score += 0.1
    return min(score, 1.0)


def score_capability(cap, requirement):
    """Return (total, breakdown). The breakdown explains the score."""
    bd = {"requirement_fit": _fit(cap, requirement),
          "compatibility": 1.0 if (cap.get("compatibility") or {}).get("status")
                               == "COMPATIBLE" else 0.0,
          "security": SEC_SCORE.get((cap.get("security") or {}).get("status"), 0.0),
          "licence": LIC_SCORE.get(cap.get("licence"), 0.0),
          "freshness": FRESH_SCORE.get((cap.get("staleness") or {}).get("state"), 0.0),
          "maintenance": MAINT_SCORE.get((cap.get("staleness") or {}).get("maintenance"), 0.0),
          "provenance_confidence": CONF_SCORE.get(cap.get("confidence"), 0.0),
          "verification": VERIF_SCORE.get((cap.get("verification") or {}).get("state"), 0.0)}
    total = round(sum(bd[k] * WEIGHTS[k] for k in WEIGHTS), 4)
    return total, bd


def rank(candidates, requirement):
    """Deterministic ranking with a per-candidate explanation."""
    scored = []
    for c in candidates:
        total, bd = score_capability(c, requirement)
        scored.append({
            "capability_id": c.get("capability_id"),
            "name": c.get("name"),
            "score": total,
            "breakdown": {k: round(v, 4) for k, v in bd.items()},
            "contributing_weights": dict(WEIGHTS),
            "explanation": ("%s scored %.2f: fit=%.2f compat=%.2f security=%.2f "
                            "licence=%.2f freshness=%.2f maintenance=%.2f "
                            "provenance=%.2f verification=%.2f"
                            % (c.get("capability_id"), total, bd["requirement_fit"],
                               bd["compatibility"], bd["security"], bd["licence"],
                               bd["freshness"], bd["maintenance"],
                               bd["provenance_confidence"], bd["verification"])),
            "_pop": int((c.get("popularity") or {}).get("stars", 0)),
            "_rec": str(c.get("last_verified") or ""),
        })
    # Score desc; ties by popularity, then recency, then id. Popularity and
    # recency can never outrank a score difference.
    scored.sort(key=lambda x: (-x["score"], -x["_pop"], x["_rec"],
                               x["capability_id"]))
    for i, x in enumerate(scored, 1):
        x["rank"] = i
        x["tie_breaker_used"] = False
        if i > 1 and abs(scored[i - 2]["score"] - x["score"]) < 1e-9:
            x["tie_breaker_used"] = True
            x["tie_breaker_basis"] = "popularity_then_recency"
    for x in scored:
        x.pop("_pop", None)
        x.pop("_rec", None)
    return scored


def apply_forced_choice(ranks, chosen_id, capabilities):
    """A user's explicit choice wins over automatic ranking.

    It CANNOT be overridden when a mandatory safety constraint applies.
    """
    by_id = {c.get("capability_id"): c for c in capabilities}
    target = by_id.get(chosen_id)
    if target is None:
        return ranks, {"forced": False, "reason": "chosen capability not found"}
    sec = (target.get("security") or {}).get("status")
    if sec in NON_OVERRIDABLE_SECURITY:
        return ranks, {"forced": False, "reason":
                       "MANDATORY_SAFECY_CONSTRAINT: security status %s cannot be "
                       "overridden by an explicit user choice" % sec,
                       "capability_id": chosen_id}
    if target.get("install_scope") == "GLOBAL" \
       and not (target.get("global_installation_authorized_by") or "").strip():
        return ranks, {"forced": False, "reason":
                       "MANDATORY_SAFECY_CONSTRAINT: GLOBAL scope lacks user "
                       "authorization", "capability_id": chosen_id}
    if target.get("lifecycle_state") in ("REJECTED", "REMOVED"):
        return ranks, {"forced": False, "reason":
                       "MANDATORY_SAFECY_CONSTRAINT: lifecycle %s is not selectable"
                       % target.get("lifecycle_state"), "capability_id": chosen_id}
    moved = [x for x in ranks if x["capability_id"] == chosen_id]
    rest = [x for x in ranks if x["capability_id"] != chosen_id]
    if not moved:
        return ranks, {"forced": False, "reason": "chosen capability not ranked"}
    was = moved[0]["rank"]
    forced = dict(moved[0])
    forced["rank"] = 1
    forced["forced_by_user"] = True
    forced["original_automatic_rank"] = was
    forced["explanation"] = ("%s moved to rank 1 by explicit user choice "
                             "(automatic rank was %d). The choice was NOT silently "
                             "replaced by a higher-scoring candidate."
                             % (chosen_id, was))
    out = [forced] + rest
    for i, x in enumerate(out, 1):
        x["rank"] = i
    return out, {"forced": True, "capability_id": chosen_id,
                 "original_automatic_rank": was,
                 "reason": "explicit user choice honoured subject to safety constraints"}


def select(candidates, requirement, forced_choice=None):
    """Full pipeline: rank, then apply a forced choice if present."""
    ranks = rank(candidates, requirement)
    forced_info = {"forced": False, "reason": "no forced choice supplied"}
    if forced_choice:
        ranks, forced_info = apply_forced_choice(ranks, forced_choice, candidates)
    return {"ranking": ranks, "forced_choice": forced_info,
            "fingerprint": ranking_fingerprint(ranks), "weights": dict(WEIGHTS),
            "popularity_role": "TIE_BREAKER_ONLY",
            "recency_role": "TIE_BREAKER_ONLY"}
