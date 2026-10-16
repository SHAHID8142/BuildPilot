#!/usr/bin/env python3
"""SPS 2.0 P2 research-record validator.

Validates structured research state: source integrity, capability extraction
rules, interoperability honesty, and decision/evidence integrity.

Emits 'ERR\t<message>' per violation; nothing when clean.
Usage: check_p2.py <kind> <json-file>
  kind: sources | capability | interop | requirements | evidence | decision | handoff
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

from datetime import datetime, timezone

# The predicate is obtained behind the same fail-closed guard as check_sps2.py.
# An unguarded import here would terminate the process with an EMPTY stdout and
# a traceback on stderr when the policy is missing or malformed; stdout
# emptiness is the success signal for assert_clean in validate-p2.sh, which
# discards stderr via `2>/dev/null`, so that would be scored as a PASS. Capture
# the reason and report it as a controlled ERR line from main() instead.
#
# The broad `Exception` clause is deliberate: any failure to obtain the
# predicate must fail closed with a visible ERR line rather than a silent
# empty-stdout pass, including policy shapes this guard does not enumerate.
# KeyboardInterrupt/SystemExit derive from BaseException, not Exception.
ATTRIBUTION_ERROR = None
try:
    import attribution as _ATTRIBUTION  # noqa: E402
    AGENT = _ATTRIBUTION.AGENTISH
except Exception as _ex:
    AGENT = None
    ATTRIBUTION_ERROR = "%s: %s" % (type(_ex).__name__, _ex)

RECS = {"KEEP", "ADAPT", "REWRITE", "REPLACE", "RESEARCH_FURTHER",
        "REJECT", "DEFER"}
STATUSES = {"IMPLEMENTED", "NOT_IMPLEMENTED", "UNVERIFIED"}
SUPPORT = {"native", "adapter", "partial", "external", "unavailable",
           "unknown"}
HARNESSES = {"Claude Code", "Codex", "Cline", "OpenCode", "Cursor", "Gemini",
             "Copilot", "Other"}
RESULTS = {"PASS", "FAIL", "SKIP", "BLOCKED"}


def _dup(ids):
    return sorted({i for i in ids if ids.count(i) > 1})


def _approval(e, tag, ap):
    if ap.get("state") != "APPROVED":
        return
    who = (ap.get("decided_by") or "").strip()
    if not who:
        e.append("%s: APPROVED without decided_by" % tag)
    elif AGENT.search(who):
        e.append("%s: APPROVED attributed to non-user %r" % (tag, who))


def sources(d):
    """Sources must have a URL, a rank, an access date and a relevance note."""
    e = []
    for s in d.get("sources", []):
        sid = s.get("source_id", "<no id>")
        if not re.fullmatch(r"SRC-\d{3}", str(sid)):
            e.append("%s: bad source_id" % sid)
            continue
        if not (s.get("url") or "").startswith(("http://", "https://")):
            e.append("%s: missing or non-http url" % sid)
        r = s.get("source_rank")
        if not isinstance(r, int) or not 1 <= r <= 6:
            e.append("%s: source_rank must be an int 1..6 (got %r)" % (sid, r))
        if r in (5, 6) and "SIGNAL_ONLY" not in (s.get("relevance") or ""):
            e.append("%s: low-rank source must be marked SIGNAL_ONLY" % sid)
        acc = s.get("accessed")
        try:
            datetime.strptime(acc, "%Y-%m-%d")
        except Exception:
            e.append("%s: accessed must be YYYY-MM-DD (got %r)" % (sid, acc))
        if not (s.get("relevance") or "").strip():
            e.append("%s: relevance must state why it was consulted" % sid)
    d2 = _dup([s.get("source_id") for s in d.get("sources", [])])
    if d2:
        e.append("duplicate source IDs: %s" % d2)
    for c in d.get("conflicts", []):
        if not c.get("resolution"):
            e.append("%s: conflict has no recorded resolution" % c.get("id"))
    return e


def capability(d):
    """Extracted capabilities need evidence, valid taxonomy, and no registry leak."""
    e = []
    known = set(d.get("known_source_ids") or [])
    for c in d.get("capabilities", []):
        cid = c.get("capability_id", "<no id>")
        if not re.fullmatch(r"CAP-\d{3}", str(cid)):
            e.append("%s: bad capability_id" % cid)
            continue
        rec = c.get("sps_recommendation")
        if rec not in RECS:
            e.append("%s: recommendation %r not in taxonomy %s"
                     % (cid, rec, sorted(RECS)))
        st = c.get("status")
        if st not in STATUSES:
            e.append("%s: invalid status %r" % (cid, st))
        ev = c.get("evidence") or []
        if not ev:
            e.append("%s: FABRICATED_CAPABILITY - no evidence at all" % cid)
        elif st == "IMPLEMENTED" and not ev:
            e.append("%s: IMPLEMENTED without evidence" % cid)
        for x in ev:
            if known and x not in known:
                e.append("%s: cites unknown source %r" % (cid, x))
        if st == "UNVERIFIED" and rec != "RESEARCH_FURTHER":
            e.append("%s: UNVERIFIED status must be RESEARCH_FURTHER (got %r)"
                     % (cid, rec))
        if c.get("confidence") not in {"HIGH", "MEDIUM", "LOW"}:
            e.append("%s: invalid confidence %r" % (cid, c.get("confidence")))
        for h in (c.get("harness_scope") or []):
            if h not in HARNESSES:
                e.append("%s: unsupported harness %r" % (cid, h))
        if c.get("in_production_registry"):
            e.append("%s: research capability leaked into the production registry"
                     % cid)
    d2 = _dup([c.get("capability_id") for c in d.get("capabilities", [])])
    if d2:
        e.append("duplicate capability IDs: %s" % d2)
    return e
def interop(d):
    """No unsupported harness, no invalid support class, no universal claim."""
    e = []
    for r in d.get("records", []):
        name = r.get("capability", "<no capability>")
        sup = r.get("support") or {}
        for h, v in sup.items():
            if h not in HARNESSES:
                e.append("%s: unsupported harness %r" % (name, h))
            if v not in SUPPORT:
                e.append("%s/%s: invalid support value %r" % (name, h, v))
        if not sup:
            e.append("%s: no support recorded for any harness" % name)
        if r.get("confidence") not in {"HIGH", "MEDIUM", "LOW"}:
            e.append("%s: invalid confidence %r" % (name, r.get("confidence")))
        if (r.get("confidence") or "").upper() == "HIGH" \
           and not (r.get("basis") or "").strip():
            e.append("%s: HIGH confidence without a stated basis" % name)
        if "universal" in json.dumps(r).lower():
            e.append("%s: claims universality without evidence" % name)
    if not d.get("records"):
        e.append("interop matrix is empty")
    return e


def requirements(d):
    e = []
    for r in d.get("requirements", []):
        rid = r.get("requirement_id", "<no id>")
        if not re.fullmatch(r"REQ-[A-Z0-9]+-\d{2,}", str(rid)):
            e.append("%s: bad requirement_id" % rid)
            continue
        if not (r.get("acceptance_criteria") or []):
            e.append("%s: acceptance_criteria empty (MISSING_REQUIREMENT)" % rid)
            continue
        impl = r.get("implementation") or {}
        if impl.get("verified") and not impl.get("evidence"):
            e.append("%s: implementation.verified without evidence "
                     "(UNVERIFIED_IMPLEMENTATION)" % rid)
        ver = r.get("verification") or {}
        if ver.get("state") == "VERIFIED" and not ver.get("evidence"):
            e.append("%s: VERIFIED without evidence" % rid)
        if ver.get("state") == "VERIFIED" and ver.get("method") == "AGENT" \
           and (r.get("risk") or "") in ("HIGH", "CRITICAL"):
            e.append("%s: AGENT verification alone insufficient for %s risk"
                     % (rid, r.get("risk")))
        _approval(e, rid, r.get("approval") or {})
    d2 = _dup([r.get("requirement_id") for r in d.get("requirements", [])])
    if d2:
        e.append("duplicate requirement IDs: %s" % d2)
    return e


def evidence(d):
    e = []
    for r in d.get("records", []):
        rid = r.get("evidence_id", "<no id>")
        if not re.fullmatch(r"EV-[A-Z0-9]+-\d{3,}", str(rid)):
            e.append("%s: bad evidence_id" % rid)
            continue
        if r.get("result") not in RESULTS:
            e.append("%s: invalid result %r" % (rid, r.get("result")))
            continue
        if r.get("result") == "PASS" and not (r.get("observed_result") or "").strip():
            e.append("%s: PASS with empty observed_result" % rid)
        if r.get("result") in ("SKIP", "BLOCKED") \
           and len(r.get("observed_result") or "") < 20:
            e.append("%s: SKIP/BLOCKED without a stated reason" % rid)
        acc = r.get("timestamp")
        try:
            # Accept a full ISO timestamp; staleness is judged on the date part.
            datetime.strptime(str(acc)[:10], "%Y-%m-%d")
            if datetime.now(timezone.utc).year - int(str(acc)[:4]) > 2:
                e.append("%s: STALE_RESEARCH record from %s" % (rid, acc))
        except Exception:
            e.append("%s: timestamp must be ISO prefixed YYYY-MM-DD (got %r)"
                     % (rid, acc))
    d2 = _dup([r.get("evidence_id") for r in d.get("records", [])])
    if d2:
        e.append("duplicate evidence IDs (append-only violation): %s" % d2)
    return e


def decision(d):
    e = []
    for x in d.get("decisions", []):
        did = x.get("decision_id", "<no id>")
        if not re.fullmatch(r"DEC-\d{4}", str(did)):
            e.append("%s: bad decision_id" % did)
            continue
        if not x.get("reason") or not x.get("evidence"):
            e.append("%s: decision missing reason or evidence" % did)
        if x.get("status") == "ACTIVE" \
           and (x.get("approval") or {}).get("state") != "APPROVED":
            e.append("%s: ACTIVE without user approval" % did)
        _approval(e, did, x.get("approval") or {})
    d2 = _dup([x.get("decision_id") for x in d.get("decisions", [])])
    if d2:
        e.append("duplicate decision IDs: %s" % d2)
    return e


def handoff(d):
    e = []
    for h in d.get("handoffs", []):
        hid = h.get("handoff_id", "<no id>")
        if not h.get("next_allowed_action") or not h.get("forbidden_next_action"):
            e.append("%s: handoff must state next AND forbidden actions" % hid)
        for k in ("completed", "not_completed", "blockers"):
            if not isinstance(h.get(k), list):
                e.append("%s: %s must be a list" % (hid, k))
        if h.get("user_approval") == "APPROVED" \
           and "APPROVED" not in (h.get("current_state") or ""):
            e.append("%s: approval state contradicts current_state" % hid)
    return e


MAP = {"sources": sources, "capability": capability, "interop": interop,
       "requirements": requirements, "evidence": evidence,
       "decision": decision, "handoff": handoff}

# The collection each kind is required to carry. Every handler reads its
# records with a bare d.get(<key>, []), so an ABSENT key made the handler
# iterate an empty list, emit nothing and exit 0. validate-p2.sh:34-41 scores
# an empty stdout as a clean PASS, so such a document was reported as valid
# without ever being checked. check_sps2.py already guarded this shape via its
# _records() helper; this mirrors that contract so the two cannot drift.
REQUIRED_COLLECTIONS = {
    "sources": "sources",
    "capability": "capabilities",
    "interop": "records",
    "requirements": "requirements",
    "evidence": "records",
    "decision": "decisions",
    "handoff": "handoffs",
}


def _check_collection(d, kind, e):
    """Report a missing or non-list collection for ``kind`` as ERR messages.

    A missing key and a non-list value are both structural failures: each makes
    the per-record checks vacuous while stdout stays empty, which the shell
    harness cannot distinguish from success.

    Returns True when the collection is usable, so the caller can skip the
    per-record handler. Running the handler against a non-list would raise
    TypeError (e.g. iterating None), which escapes main() and leaves stdout
    empty -- the very false-PASS this guard exists to prevent.
    """
    key = REQUIRED_COLLECTIONS.get(kind)
    if key is None:
        return True
    if key not in d:
        e.append("document missing %r collection" % key)
        return False
    if not isinstance(d.get(key), list):
        e.append("%r must be a list" % key)
        return False
    # A present, correctly-typed list of NON-OBJECT elements is the third shape
    # that makes the per-record checks vacuous: each handler calls .get() on the
    # element, raises AttributeError, escapes main(), and leaves stdout empty --
    # which the shell harness scores as a PASS. check_sps2.py already reports
    # this ("<key>[i] is not an object"); mirror it so the siblings agree.
    for i, item in enumerate(d.get(key)):
        if not isinstance(item, dict):
            e.append("%s[%d] is not an object" % (key, i))
            return False
    return True


def main():
    if len(sys.argv) != 3:
        print("usage: check_p2.py <kind> <json-file>")
        return 2
    kind, path = sys.argv[1], sys.argv[2]
    if kind not in MAP:
        print("unknown kind: %s" % kind)
        return 2
    if ATTRIBUTION_ERROR is not None:
        # Fail visibly. stdout must NOT be empty here: validate-p2.sh scores an
        # empty stdout as a clean PASS.
        print("ERR\tattribution policy unavailable: %s" % ATTRIBUTION_ERROR)
        return 0
    try:
        data = json.load(open(path))
    except Exception as ex:
        print("ERR\tnot valid JSON: %s" % ex)
        return 0
    if not isinstance(data, dict):
        # Valid JSON of the wrong top-level type (a list, string, number,
        # boolean or null) would make the handlers call .get() on a non-mapping
        # and raise AttributeError. That escapes this function entirely, so
        # stdout stays empty, and validate-p2.sh scores an empty stdout as a
        # clean PASS. Fail visibly instead, matching check_sps2.py.
        print("ERR\t%s: top-level document must be an object" % kind)
        return 0
    structural = []
    usable = _check_collection(data, kind, structural)
    for msg in structural:
        print("ERR\t%s" % msg)
    if not usable:
        # The per-record handler would raise on a structurally invalid
        # collection; the ERR above already reports the document as unclean.
        return 0
    for msg in MAP[kind](data):
        print("ERR\t%s" % msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())