#!/usr/bin/env python3
"""SPS 2.0 P4 hardened production promotion gate.

Each candidate is evaluated against eleven independent gates (A-K). A gate
either PASSES or FAILS with a named reason. Nothing is asserted: every result
is computed from the capability record and repository state.

Design rule: production promotion requires ALL applicable gates to pass. A
single failed gate blocks promotion. A failed gate is never worked around by
weakening the gate.

Secret-safe: no credential value is ever read, printed or stored.
"""
import json
import os
import re
import subprocess
import sys
# Agent-name tokens come from the single authoritative policy
# (framework/sps2/governance/attribution_policy.json) via attribution.py.
# SPEC-2 consolidation: this module must not keep its own token list.
_GOVERNANCE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "governance")
if _GOVERNANCE not in sys.path:
    sys.path.insert(0, _GOVERNANCE)
import attribution as _ATTRIBUTION  # noqa: E402


# framework/sps2/capability/promotion_gates.py -> up 3 levels reaches the repository root.
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

AGENTISH = _ATTRIBUTION.AGENTISH
CAP_ID = re.compile(r'^CAP-P03-\d{3}$')
SECRET_RX = re.compile(r'sk-or-v1-[A-Za-z0-9]{32,}|sk-ant-[A-Za-z0-9\-_]{20,}')
LIFECYCLE = {"RESEARCHED", "CANDIDATE", "EVALUATED", "APPROVED", "INSTALLED",
             "VERIFIED", "ACTIVE", "STALE", "REVIEW_REQUIRED", "INVALIDATED",
             "REJECTED", "DEFERRED", "REMOVED"}
TYPES = {"DEV_TOOL", "SEO_TOOL", "SKILL", "LIBRARY"}
TAXONOMY = {"GOVERNANCE", "SEO", "SECURITY", "CMS", "MCP", "TESTING",
            "DEPLOYMENT", "CONTEXT"}
SECURITY_OK = {"VERIFIED_SAFE", "REVIEWED_LOW_RISK"}
LICENCE_KNOWN = {"KNOWN_PERMISSIVE", "KNOWN_COPYLEFT", "KNOWN_PROPRIETARY"}


def repository_has_licence():
    """FACT: does this repository declare a licence? Checked, never assumed."""
    try:
        names = subprocess.run(["git", "-C", REPO, "ls-files"],
                               capture_output=True, text=True).stdout.split()
    except Exception:
        return False
    return any(re.fullmatch(r'(LICEN[SC]E|COPYING)(\.\w+)?', n, re.I)
               for n in names)


def implementation_exists(cap):
    """FACT: does a concrete implementation artefact exist on disk?

    A Markdown research note is documentation, not an implementation.
    """
    rel = (cap.get("provenance") or {}).get("repository_relative_path") or ""
    if not rel:
        return False
    if not rel.endswith((".py", ".sh", ".js", ".ts")):
        return False
    return os.path.isfile(os.path.join(REPO, rel))


def unresolved_conflicts(cap):
    """FACT: does an open research conflict touch this capability?"""
    out = []
    if cap.get("domain") == "SEO":
        try:
            p = os.path.join(REPO, "framework", "sps2", "research", "P2-SOURCES.json")
            for c in json.load(open(p)).get("conflicts", []):
                if "UNRESOLVED" in (c.get("resolution") or ""):
                    out.append(c.get("id", "unknown"))
        except Exception:
            pass
    return out


def known_research_refs():
    """FACT: which research references actually resolve in the P2 source set?"""
    try:
        p = os.path.join(REPO, "framework", "sps2", "research", "P2-SOURCES.json")
        data = json.load(open(p))
        ids = {s["source_id"] for s in data.get("sources", [])}
        ids.update(c["id"] for c in data.get("conflicts", []))
        return ids
    except Exception:
        return set()


def evaluate(cap, ctx=None):
    """Return (results, blocking_letters). Computed, never asserted."""
    ctx = ctx or {}
    ctx.setdefault("known_research_refs", known_research_refs())
    r = {}
    cid = cap.get("capability_id", "<none>")

    # ── A. Identity ─────────────────────────────────────────────────────────
    a_ok = (bool(CAP_ID.match(str(cid))) and bool(cap.get("version"))
            and cap.get("type") in TYPES
            and cap.get("lifecycle_state") in LIFECYCLE)
    r["A"] = {"gate": "IDENTITY", "pass": a_ok,
              "reason": "id, type, version and lifecycle valid" if a_ok
              else "capability id, type, version or lifecycle invalid"}

    # ── B. Provenance ───────────────────────────────────────────────────────
    prov = cap.get("provenance") or {}
    # A provenance claim must RESOLVE, not merely be non-empty. Either a
    # well-formed source URL or a research reference that exists in the
    # P2 source set. A name that resolves to nothing is a fabricated source.
    url = (prov.get("source_url") or "").strip()
    url_ok = url.startswith(("http://", "https://"))
    refs = prov.get("research_refs") or []
    ref_ok = bool(refs) and all(r in ctx["known_research_refs"] for r in refs)
    rel = (prov.get("repository_relative_path") or "").strip()
    path_ok = bool(rel) and os.path.isfile(os.path.join(REPO, rel))
    b_ok = (bool(prov.get("origin")) and bool(prov.get("commit"))
            and bool(prov.get("fact_class")) and bool(cap.get("evidence"))
            and (url_ok or ref_ok or path_ok))
    if not (url_ok or ref_ok or path_ok):
        reason = ("provenance source does not resolve: no valid source_url, no "
                  "research_ref present in the P2 source set, and no existing "
                  "repository path (refs=%s, path=%s)" % (refs or "absent",
                                                          rel or "absent"))
    elif not b_ok:
        reason = "provenance chain incomplete (origin, commit, fact_class or evidence)"
    else:
        reason = "origin, commit, fact class, evidence and a resolvable source"
    r["B"] = {"gate": "PROVENANCE", "pass": b_ok, "reason": reason}

    # ── C. Security ─────────────────────────────────────────────────────────
    sec = cap.get("security") or {}
    payload = json.dumps(cap)
    c_ok = (sec.get("status") in SECURITY_OK and bool(sec.get("evidence"))
            and not SECRET_RX.search(payload)
            and cap.get("install_scope") == "PROJECT_LOCAL")
    r["C"] = {"gate": "SECURITY", "pass": c_ok,
              "reason": "classified, evidenced, no secret, project-local" if c_ok
              else "security classification or evidence missing, a secret-shaped "
                   "value is embedded, or scope is not PROJECT_LOCAL"}

    # ── D. Licence ──────────────────────────────────────────────────────────
    lic = cap.get("licence")
    repo_licensed = repository_has_licence()
    d_ok = (lic in LICENCE_KNOWN and bool(cap.get("licence_evidence"))
            and repo_licensed)
    if not repo_licensed:
        reason = ("repository declares no LICENSE or COPYING file, so the "
                  "applicable licence is UNRESOLVED; an unresolved licence "
                  "blocks production promotion")
    elif lic not in LICENCE_KNOWN:
        reason = "licence not classified as known"
    else:
        reason = "licence known, evidenced, and repository licence declared"
    r["D"] = {"gate": "LICENCE", "pass": d_ok, "reason": reason,
              "repository_declares_licence": repo_licensed}

    # ── E. Maintenance ──────────────────────────────────────────────────────
    st = cap.get("staleness") or {}
    e_ok = (st.get("maintenance") in {"ACTIVE", "PASSIVE", "UNKNOWN"}
            and bool(st.get("review_due")) and bool(st.get("reevaluation_triggers")))
    r["E"] = {"gate": "MAINTENANCE", "pass": e_ok,
              "reason": "maintenance state, review date and triggers present"
              if e_ok else "maintenance state or review policy missing"}

    # ── F. Verification ──────────────────────────────────────────────────────
    ver = cap.get("verification") or {}
    impl = implementation_exists(cap)
    f_ok = (impl and ver.get("state") == "VERIFIED" and bool(ver.get("evidence"))
            and bool(ver.get("method")) and bool(ver.get("expected_result"))
            and bool(ver.get("observed_result")))
    if not impl:
        reason = ("no executable implementation exists for this capability; a "
                  "verified threshold fact is not an implemented verifier")
    elif ver.get("state") != "VERIFIED":
        reason = "verification state is %r, not VERIFIED" % ver.get("state")
    elif not ver.get("evidence"):
        reason = "verification recorded but carries no evidence reference"
    else:
        reason = "implementation exists and verification is fully evidenced"
    r["F"] = {"gate": "VERIFICATION", "pass": f_ok, "reason": reason,
              "implementation_exists": impl}

# ── G. Requirements ─────────────────────────────────────────────────────
    g_ok = (bool(cap.get("linked_requirements"))
            and bool(cap.get("acceptance_criteria"))
            and cap.get("domain") in TAXONOMY)
    r["G"] = {"gate": "REQUIREMENTS", "pass": g_ok,
              "reason": "linked requirements and acceptance criteria present"
              if g_ok else "no linked requirements, empty acceptance criteria, or "
                           "domain outside the declared taxonomy"}

    # ── H. Approval ─────────────────────────────────────────────────────────
    ap = cap.get("approval") or {}
    h_ok = ap.get("state") == "APPROVED"
    if h_ok:
        who = (ap.get("decided_by") or "").strip()
        h_ok = bool(who) and not AGENTISH.search(who)
    r["H"] = {"gate": "APPROVAL", "pass": h_ok,
              "reason": "explicit User approval recorded" if h_ok
              else "no explicit User approval; production promotion must await a "
                   "User decision"}

    # ── I. Scope ────────────────────────────────────────────────────────────
    i_ok = cap.get("install_scope") == "PROJECT_LOCAL" or bool(
        (cap.get("global_installation_authorized_by") or "").strip())
    r["I"] = {"gate": "SCOPE", "pass": i_ok,
              "reason": "project-local scope honoured" if i_ok
              else "GLOBAL scope without explicit user authorization"}

    # ── J. Staleness ────────────────────────────────────────────────────────
    j_ok = not (st.get("state") == "STALE"
                and cap.get("lifecycle_state") == "ACTIVE") \
        and not (st.get("state") == "STALE" and not st.get("review_due"))
    r["J"] = {"gate": "STALENESS", "pass": j_ok,
              "reason": "no stale-as-active and no stale-without-review" if j_ok
              else "stale capability is ACTIVE or lacks a review date"}

    # ── K. Conflict handling ────────────────────────────────────────────────
    conf = unresolved_conflicts(cap)
    r["K"] = {"gate": "CONFLICTS", "pass": not conf,
              "reason": "no unresolved conflict touches this capability"
              if not conf else
              "unresolved research conflict(s): " + ", ".join(conf),
              "unresolved": conf}

    blocking = sorted(g for g, v in r.items() if not v["pass"])
    return r, blocking


def decide(blocking):
    """Map blocking gates to an honest recommendation. Never inflates.

    Gates D (licence) and H (User approval) are user-resolvable: the
    capability is sound but cannot proceed until the user acts. That is a
    CANDIDATE waiting on a decision, not a deficiency.
    """
    if not blocking:
        return "PROMOTE"
    if "C" in blocking:
        return "REJECT"
    if set(blocking) <= {"D", "H"}:
        return "REMAIN_CANDIDATE"
    return "DEFER"
