#!/usr/bin/env python3
"""SPS 2.0 P1 structured-state check engine.

Validates JSON records against the P1 contracts. Emits one 'ERR\t<message>'
line per violation on stdout; emits nothing when the input is clean.

Usage: check_sps2.py <kind> <json-file>
  kind: requirement | capability | evidence | decision | handoff | action

Pure module: reads one file, writes nothing.
"""
import json
import re
import sys
import os
# Agent-name tokens come from the single authoritative policy
# (sps2/governance/attribution_policy.json) via attribution.py.
# SPEC-2 consolidation: this module must not keep its own token list.
_GOVERNANCE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "governance")
if _GOVERNANCE not in sys.path:
    sys.path.insert(0, _GOVERNANCE)

# A failure to import attribution (missing module) or to build its AGENTISH
# predicate (missing, malformed, or empty policy) happens at IMPORT time.
# Left unguarded it produced a traceback on stderr with empty stdout, and the
# stdout-based harness (validate-sps2.sh's assert_clean) treats empty stdout as
# a PASS. Capture the reason here and report it as a controlled ERR line from
# main() instead, so the failure is visible and cannot be mistaken for clean.
#
# The predicate fails CLOSED: it never degrades to an empty token set, because
# that would let every agent-authored approver identity through unnoticed.
ATTRIBUTION_ERROR = None
try:
    import attribution as _ATTRIBUTION  # noqa: E402
    AGENT = _ATTRIBUTION.AGENTISH
except Exception as _ex:
    # Any failure to obtain the attribution predicate fails CLOSED here.
    #
    # ImportError: attribution.py absent/unimportable.
    # OSError (incl. FileNotFoundError): attribution_policy.json absent.
    # ValueError (incl. json.JSONDecodeError): policy malformed/empty, or
    #   valid JSON of a non-object top-level type.
    # AttributeError/TypeError/KeyError (incl. from a policy shape this guard
    #   does not enumerate): deliberately caught by the broad `Exception`
    #   clause, because an uncaught exception here would terminate the process
    #   with an EMPTY stdout and a traceback on stderr. stdout emptiness is the
    #   success signal for assert_clean in validate-sps2.sh, which discards
    #   stderr via `2>/dev/null`; an empty stdout would therefore be scored as
    #   a PASS. Catching broadly guarantees a non-empty ERR line instead.
    #   KeyboardInterrupt/SystemExit derive from BaseException, not Exception,
    #   so real interrupts still propagate.
    AGENT = None
    ATTRIBUTION_ERROR = "%s: %s" % (type(_ex).__name__, _ex)

RESULTS = {"PASS", "FAIL", "SKIP", "BLOCKED"}
SEC = {"VERIFIED_SAFE", "REVIEWED_LOW_RISK", "SUSPECTED_RISK",
       "VULNERABLE", "UNKNOWN"}


def _dup(ids):
    return sorted({i for i in ids if ids.count(i) > 1})


def _records(d, e, key):
    """Return the dict records in collection ``key``.

    Structural failures are reported as ERR messages instead of raising.
    A missing collection key and a non-list collection are both reported:
    an absent key previously made the collection checks vacuous, and the
    shell harness treats empty stdout as a pass.
    """
    if key not in d:
        e.append("document missing %r collection" % key)
        return []
    items = d.get(key)
    if not isinstance(items, list):
        e.append("%r must be a list" % key)
        return []
    ok = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            e.append("%s[%d] is not an object" % (key, i))
        else:
            ok.append(item)
    return ok


def _as_dict(e, tag, field, val):
    """Return ``val`` if it is a dict, else report it and return {}."""
    if val is None or isinstance(val, dict):
        return val or {}
    e.append("%s: %s must be an object" % (tag, field))
    return {}


def _as_str(val):
    """Return a strippable string for ``val``, or "" when it is not one."""
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    return ""


def _approval(e, tag, ap):
    """Approval may only ever be attributed to a user."""
    if not isinstance(ap, dict):
        e.append("%s: approval must be an object" % tag)
        return
    if ap.get("state") != "APPROVED":
        return
    who = _as_str(ap.get("decided_by")).strip()
    if not who:
        e.append("%s: APPROVED without decided_by" % tag)
    elif AGENT.search(who):
        e.append("%s: APPROVED attributed to non-user %r" % (tag, who))


def requirement(d):
    e = []
    reqs = _records(d, e, "requirements")
    for r in reqs:
        rid = r.get("requirement_id", "<no id>")
        if not re.fullmatch(r"REQ-[A-Z0-9]+-\d{2,}", str(rid)):
            e.append("%s: bad requirement_id" % rid)
            continue
        # NOTE: acceptance_criteria is a list in the real records (a plain
        # string in P2). This stays a truthiness test on purpose: coercing it
        # through a dict guard would newly flag all 98 requirements.
        if not (r.get("acceptance_criteria") or []):
            e.append("%s: acceptance_criteria empty (MISSING_REQUIREMENT)" % rid)
            continue
        if not r.get("objective"):
            e.append("%s: missing objective" % rid)
        impl = _as_dict(e, rid, "implementation", r.get("implementation"))
        if impl.get("verified") and not impl.get("evidence"):
            e.append("%s: implementation.verified without evidence "
                     "(UNVERIFIED_IMPLEMENTATION)" % rid)
        if impl.get("state") == "COMPLETE" and not impl.get("refs"):
            e.append("%s: implementation COMPLETE without refs" % rid)
        ver = _as_dict(e, rid, "verification", r.get("verification"))
        if ver.get("state") == "VERIFIED" and not ver.get("evidence"):
            e.append("%s: VERIFIED without evidence" % rid)
        if ver.get("state") == "VERIFIED" and ver.get("method") == "AGENT" \
           and (r.get("risk") or "") in ("HIGH", "CRITICAL"):
            e.append("%s: AGENT verification alone is insufficient for %s risk"
                     % (rid, r.get("risk")))
        _approval(e, rid, r.get("approval"))
    dup = _dup([r.get("requirement_id") for r in reqs])
    if dup:
        e.append("duplicate requirement IDs: %s" % dup)
    return e


def capability(d):
    e = []
    caps = _records(d, e, "capabilities")
    for c in caps:
        cid = c.get("capability_id", "<no id>")
        if not re.fullmatch(r"CAP-[A-Z0-9]+-\d{3,}", str(cid)):
            e.append("%s: bad capability_id" % cid)
            continue
        sc = _as_dict(e, cid, "security", c.get("security")).get("status")
        if sc not in SEC:
            e.append("%s: invalid security status %r" % (cid, sc))
            continue
        if sc in {"SUSPECTED_RISK", "VULNERABLE", "UNKNOWN"} \
           and c.get("install_scope") == "GLOBAL":
            e.append("%s: security %s blocks GLOBAL install" % (cid, sc))
            continue
        if c.get("install_scope") == "GLOBAL":
            who = _as_str(c.get("global_installation_authorized_by")).strip()
            if not who:
                e.append("%s: GLOBAL scope without user authorization" % cid)
            elif AGENT.search(who):
                e.append("%s: GLOBAL authorized by non-user %r" % (cid, who))
        comp = _as_dict(e, cid, "compatibility", c.get("compatibility"))
        if comp.get("agent_neutral") and comp.get("agent_specific_dependency"):
            e.append("%s: claims agent_neutral with dependency %r"
                     % (cid, comp.get("agent_specific_dependency")))
        st = _as_dict(e, cid, "staleness", c.get("staleness"))
        if st.get("state") == "STALE" and st.get("review_due") is None:
            e.append("%s: STALE without review_due" % cid)
        if c.get("lifecycle_state") in ("VERIFIED", "ACTIVE") \
           and not ((_as_dict(e, cid, "verification",
                              c.get("verification")).get("evidence")) or []):
            e.append("%s: lifecycle %s without evidence"
                     % (cid, c.get("lifecycle_state")))
        _approval(e, cid, c.get("approval"))
    dup = _dup([c.get("capability_id") for c in caps])
    if dup:
        e.append("duplicate capability IDs: %s" % dup)
    return e


def evidence(d):
    e = []
    recs = _records(d, e, "records")
    for r in recs:
        rid = r.get("evidence_id", "<no id>")
        if not re.fullmatch(r"EV-[A-Z0-9]+-\d{3,}", str(rid)):
            e.append("%s: bad evidence_id" % rid)
            continue
        if r.get("result") not in RESULTS:
            e.append("%s: invalid result %r" % (rid, r.get("result")))
            continue
        obs = _as_str(r.get("observed_result"))
        if r.get("result") == "PASS" and not obs.strip():
            e.append("%s: PASS with empty observed_result" % rid)
        if r.get("result") in ("SKIP", "BLOCKED") and len(obs) < 20:
            e.append("%s: SKIP/BLOCKED without a stated reason" % rid)
    dup = _dup([r.get("evidence_id") for r in recs])
    if dup:
        e.append("duplicate evidence IDs (append-only violation): %s" % dup)
    return e


def decision(d):
    e = []
    decs = _records(d, e, "decisions")
    for x in decs:
        did = x.get("decision_id", "<no id>")
        if not re.fullmatch(r"DEC-\d{4}", str(did)):
            e.append("%s: bad decision_id" % did)
            continue
        if not x.get("reason") or not x.get("evidence"):
            e.append("%s: decision missing reason or evidence" % did)
        _approval(e, did, x.get("approval"))
    dup = _dup([x.get("decision_id") for x in decs])
    if dup:
        e.append("duplicate decision IDs: %s" % dup)
    return e


def handoff(d):
    e = []
    for h in _records(d, e, "handoffs"):
        hid = h.get("handoff_id", "<no id>")
        if not h.get("next_allowed_action") or not h.get("forbidden_next_action"):
            e.append("%s: handoff must state next AND forbidden actions" % hid)
        for k in ("completed", "not_completed", "blockers"):
            if not isinstance(h.get(k), list):
                e.append("%s: %s must be a list" % (hid, k))
    return e


def action(d):
    e = []
    for a in _records(d, e, "actions"):
        aid = a.get("action_id", "<no id>")
        if a.get("assumption") == "MATERIAL_DECISION" \
           and _as_dict(e, aid, "approval",
                        a.get("approval")).get("state") != "APPROVED":
            e.append("%s: MATERIAL_DECISION without user approval "
                     "(MISSING_USER_DECISION)" % aid)
        if a.get("install_scope") == "GLOBAL":
            who = _as_str(a.get("global_installation_authorized_by")).strip()
            if not who:
                e.append("%s: GLOBAL install without user authorization" % aid)
            elif AGENT.search(who):
                e.append("%s: GLOBAL authorized by non-user %r" % (aid, who))
        if a.get("risk_level") == "CRITICAL" and not a.get("rollback_method"):
            e.append("%s: CRITICAL action without rollback_method" % aid)
    return e


MAP = {"requirement": requirement, "capability": capability, "evidence": evidence,
       "decision": decision, "handoff": handoff, "action": action}


def main():
    if len(sys.argv) != 3:
        print("usage: check_sps2.py <kind> <json-file>")
        return 2
    kind, path = sys.argv[1], sys.argv[2]
    if kind not in MAP:
        print("unknown kind: %s" % kind)
        return 2
    if ATTRIBUTION_ERROR is not None:
        # Controlled report: an ERR line on stdout (exit 0, no traceback), so
        # the stdout-based harness sees a failure instead of an empty PASS.
        print("ERR\tattribution policy unavailable: %s" % ATTRIBUTION_ERROR)
        return 0
    try:
        data = json.load(open(path))
    except Exception as ex:
        print("ERR\tnot valid JSON: %s" % ex)
        return 0
    if not isinstance(data, dict):
        print("ERR\t%s: top-level document must be an object" % kind)
        return 0
    for msg in MAP[kind](data):
        print("ERR\t%s" % msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
