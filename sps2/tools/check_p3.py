#!/usr/bin/env python3
"""SPS 2.0 P3 validator: tests ACTUAL structured behaviour of the promotion
gate, ranking engine, forced choice, staleness model and selection records.

Pure: reads files, writes nothing.
Usage: check_p3.py <registry|selection|records> <path> [kind]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(os.path.dirname(HERE), "capability")
sys.path.insert(0, CAP)
GOVERNANCE = os.path.join(os.path.dirname(HERE), "governance")
sys.path.insert(0, GOVERNANCE)
import engine  # noqa: E402
from decision_identifiers import DECISION_ID_PATTERN  # noqa: E402

SPS2 = os.path.dirname(CAP)
AGENTISH = engine.AGENTISH
e = []


def err(m):
    e.append(m)


def check_registry(reg):
    caps = reg.get("capabilities") or []
    ids = [c.get("capability_id") for c in caps]
    for i in sorted({x for x in ids if ids.count(x) > 1}):
        err("DUPLICATE_CAPABILITY_ID: %s" % i)

    # P4 superseded the P3 engine gate with the hardened A-K promotion gate.
    # Validate against the CURRENT production gate, not the superseded one.
    pg_path = os.path.join(CAP, "promotion_gates.py")
    if os.path.isfile(pg_path):
        import importlib.util
        _spec = importlib.util.spec_from_file_location("pg", pg_path)
        _pg = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_pg)
        # Since P4 the registry legitimately holds candidates whose promotion
        # is blocked by a gate (currently D and H). The invariant is therefore
        # CONSISTENCY: the stored assessment must match a fresh gate run, and
        # a capability may only be EVALUATED/ACTIVE if the gate unblocked it.
        for c in caps:
            _res, _blocking = _pg.evaluate(c)
            _stored = (c.get("promotion_assessment") or {}).get("blocking_gates")
            if _stored is None:
                err("ASSESSMENT_MISSING: %s" % c.get("capability_id"))
            elif sorted(_stored) != sorted(_blocking):
                err("ASSESSMENT_STALE: %s stored=%s computed=%s"
                    % (c.get("capability_id"), _stored, _blocking))
            if _blocking and c.get("lifecycle_state") in (
                    "EVALUATED", "ACTIVE", "VERIFIED"):
                err("LIFECYCLE_WITHOUT_PROMOTION: %s state=%s blocking=%s"
                    % (c.get("capability_id"), c.get("lifecycle_state"),
                       ",".join(_blocking)))
    else:
        for c in caps:
            ok, reasons = engine.promote(c)
            if not ok:
                err("PROMOTION_GATE_FAIL: %s: %s"
                    % (c.get("capability_id"), "; ".join(reasons)))

    for c in caps:
        if c.get("install_scope") == "GLOBAL":
            err("GLOBAL_SCOPE_PRESENT: %s is not project-local"
                % c.get("capability_id"))
        prov = c.get("provenance") or {}
        for k in ("origin", "commit", "fact_class"):
            if not prov.get(k):
                err("PROVENANCE_INCOMPLETE: %s missing provenance.%s"
                    % (c.get("capability_id"), k))
        if str(c.get("origin", "")).upper() == "RESEARCH_ONLY":
            err("RESEARCH_ONLY_LEAK: %s" % c.get("capability_id"))
    for d in reg.get("deferred") or []:
        if not (d.get("reason") or "").strip():
            err("DEFERRED_WITHOUT_REASON: %s" % d.get("candidate"))
        if d.get("state") not in {"DEFERRED", "REJECTED", "RESEARCH_FURTHER"}:
            err("INVALID_DEFERRED_STATE: %s" % d.get("state"))
    src = json.load(open(os.path.join(SPS2, "research", "P2-SOURCES.json")))
    if not any("UNRESOLVED" in (c.get("resolution") or "")
               for c in src.get("conflicts", [])):
        err("RESEARCH_GAP_LOST: CONF-001 is no longer UNRESOLVED")
    return caps


def check_selection(sel, caps):
    ids = {c["capability_id"] for c in caps}
    ranking = sel.get("ranking") or []
    if not ranking:
        err("SELECTION_EMPTY: no ranking recorded")
    for r in ranking:
        if r["capability_id"] not in ids:
            err("SELECTION_UNKNOWN_CAPABILITY: %s" % r["capability_id"])
        if not (r.get("explanation") or "").strip():
            err("SELECTION_UNEXPLAINED: %s" % r["capability_id"])
        for k in ("breakdown", "contributing_weights"):
            if not r.get(k):
                err("SELECTION_MISSING_%s: %s" % (k.upper(), r["capability_id"]))
    ranks = sorted(r.get("rank") for r in ranking)
    if ranks and ranks != list(range(1, len(ranks) + 1)):
        err("SELECTION_RANK_INVALID: ranks are not 1..n")
    scores = [r.get("score", 0) for r in ranking]
    if scores != sorted(scores, reverse=True):
        err("DETERMINISM_VIOLATION: ranking not ordered by descending score")
    if sel.get("popularity_role") != "TIE_BREAKER_ONLY":
        err("POPULARITY_ROLE_INVALID: popularity must be a tie-breaker only")
    for s in sel.get("selected") or []:
        if s["capability_id"] not in ids:
            err("SELECTED_UNKNOWN: %s" % s["capability_id"])
        if not (s.get("selection_reason") or "").strip():
            err("SELECTED_UNEXPLAINED: %s" % s["capability_id"])
    ap = sel.get("approval") or {}
    if ap.get("state") == "APPROVED":
        who = (ap.get("decided_by") or "").strip()
        if not who or AGENTISH.search(who):
            err("APPROVAL_ATTRIBUTION: %r is not a valid user" % who)
    if not (sel.get("rollback", {}).get("method") or "").strip():
        err("MISSING_ROLLBACK: selection record has no rollback method")
    if sel.get("provenance", {}).get("runtime_tracing") is True:
        err("PROVENANCE_OVERCLAIM: runtime tracing is not implemented")
    if not (sel.get("staleness", {}).get("effect_of_stale") or "").strip():
        err("MISSING_STALENESS_EFFECT: stale behaviour is undefined")
# The collection key each `records` kind is required to carry, mirroring
# check_sps2.py's MAP/_records() dispatch. This mapping is the single source of
# truth for BOTH the unknown-kind guard and the missing-collection guard.
#
# Defect D5: an unrecognised kind fell through to the `else:` handoffs branch,
# inspected the wrong key, emitted NOTHING, and validate-p3.sh:103
# (`[ -z "$OUT" ] && pass`) scored that empty stdout as a PASS. Any kind that
# is not one of these four made `records` mode vacuous.
# Defect D5b: every branch read d.get(<key>, []), so an absent collection was
# indistinguishable from a genuinely empty one and `{}` scored clean for all
# four legitimate kinds.
RECORD_COLLECTIONS = {
    "requirements": "requirements",
    "evidence": "records",
    "decisions": "decisions",
    "handoff": "handoffs",
}


def records_collection(e, d, key, kind):
    """Return the record collection ``key``, reporting structural failures.

    Mirrors check_sps2.py's _records(): an absent key and a non-list value are
    both reported as ERR messages instead of raising. Raising would leave
    stdout empty (a traceback goes to stderr), and empty stdout is the PASS
    signal for validate-p3.sh, so the failure must be visible on stdout.

    A present-but-empty list is deliberately NOT an error: an empty collection
    is legitimate for every one of the four kinds here (all four real P3
    documents are only non-empty by content, not by contract), so it stays
    clean exactly as before.
    """
    if key not in d:
        e.append("%s: document missing %r collection" % (kind, key))
        return []
    items = d.get(key)
    if not isinstance(items, list):
        e.append("%s: %r must be a list" % (kind, key))
        return []
    ok = []
    for i, item in enumerate(items):
        if isinstance(item, dict):
            ok.append(item)
        else:
            # check_sps2.py reports this shape; a non-dict element would make
            # the per-record .get() raise AttributeError and empty stdout.
            e.append("%s: %s[%d] is not an object" % (kind, key, i))
    return ok


def check_records(kind, path):
    d = json.load(open(path))
    if kind == "requirements":
        reqs = records_collection(e, d, "requirements", kind)
        for r in reqs:
            rid = r.get("requirement_id", "<no id>")
            if not re.fullmatch(r"REQ-[A-Z0-9]+-\d{2,}", str(rid)):
                err("%s: bad requirement_id" % rid)
                continue
            if not (r.get("acceptance_criteria") or []):
                err("%s: MISSING_REQUIREMENT" % rid)
            impl = r.get("implementation") or {}
            if impl.get("verified") and not impl.get("evidence"):
                err("%s: UNVERIFIED_IMPLEMENTATION" % rid)
            ver = r.get("verification") or {}
            if ver.get("state") == "VERIFIED" and not ver.get("evidence"):
                err("%s: VERIFIED without evidence" % rid)
            ap = r.get("approval") or {}
            if ap.get("state") == "APPROVED":
                who = (ap.get("decided_by") or "").strip()
                if not who or AGENTISH.search(who):
                    err("%s: approval attributed to a non-user %r" % (rid, who))
        ids = [r.get("requirement_id") for r in reqs]
    elif kind == "evidence":
        recs = records_collection(e, d, "records", kind)
        for r in recs:
            rid = r.get("evidence_id", "<no id>")
            if not re.fullmatch(r"EV-[A-Z0-9]+-\d{3,}", str(rid)):
                err("%s: bad evidence_id" % rid)
                continue
            if r.get("result") not in {"PASS", "FAIL", "SKIP", "BLOCKED"}:
                err("%s: invalid result %r" % (rid, r.get("result")))
            if r.get("result") == "PASS" \
               and not (r.get("observed_result") or "").strip():
                err("%s: PASS with empty observed_result" % rid)
        ids = [r.get("evidence_id") for r in recs]
    elif kind == "decisions":
        decs = records_collection(e, d, "decisions", kind)
        for x in decs:
            did = x.get("decision_id", "<no id>")
            if not re.fullmatch(DECISION_ID_PATTERN, str(did)):
                err("%s: bad decision_id" % did)
                continue
            if not x.get("reason") or not x.get("evidence"):
                err("%s: missing reason or evidence" % did)
            if (x.get("approval") or {}).get("state") == "APPROVED":
                who = (x.get("approval").get("decided_by") or "").strip()
                if not who or AGENTISH.search(who):
                    err("%s: approval attributed to a non-user %r" % (did, who))
        ids = [x.get("decision_id") for x in decs]
    elif kind == "handoff":
        # This branch is now reached ONLY for the explicit kind "handoff".
        # It used to be a bare `else:`, which is what made every unknown kind
        # vacuously "pass": it inspected the wrong key and emitted nothing.
        hs = records_collection(e, d, "handoffs", kind)
        for h in hs:
            if not h.get("next_allowed_action") or not h.get("forbidden_next_action"):
                err("%s: must state next and forbidden actions" % h.get("handoff_id"))
            if h.get("user_approval") == "APPROVED" \
               and "APPROVED" not in (h.get("current_state") or ""):
                err("%s: approval contradicts current_state" % h.get("handoff_id"))
        ids = [h.get("handoff_id") for h in hs]
    else:
        # Unreachable via main() (which rejects unknown kinds before calling
        # here); kept so a future caller cannot silently get a vacuous pass.
        err("unknown records kind %r" % kind)
        return
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        err("duplicate IDs in %s: %s" % (kind, dup))


def main():
    if len(sys.argv) < 2:
        print("usage: check_p3.py <registry|selection|records|gate> ...")
        return 2
    mode = sys.argv[1]
    try:
        if mode == "registry":
            reg = json.load(open(sys.argv[2]))
            # A registry that is not an object, or that carries no 'capabilities'
            # key, makes check_registry iterate an empty list: no violation is
            # emitted, stdout stays empty, and validate-p3.sh:90-91 scores an
            # empty stdout as a PASS. The document would be reported clean
            # without ever being checked. Fail visibly instead, matching
            # check_sps2.py's _records() and check_p2.py's collection guard.
            if not isinstance(reg, dict):
                print("ERR\tregistry must be a JSON object")
                return 0
            if "capabilities" not in reg:
                print("ERR\tregistry missing 'capabilities' collection")
                return 0
            if not isinstance(reg.get("capabilities"), list):
                print("ERR\t'capabilities' must be a list")
                return 0
            check_registry(reg)
        elif mode == "selection":
            reg = json.load(open(sys.argv[2]))
            check_selection(json.load(open(sys.argv[3])),
                            reg.get("capabilities", []))
        elif mode == "records":
            # usage: check_p3.py records <kind> <path>  -> argv = [prog, records, kind, path]
            # argv[2] is the KIND and argv[3] is the PATH. Passing argv[3] as the
            # kind matched no branch in check_records, so no check ran and stdout
            # was always empty; validate-p3.sh scores empty stdout as a PASS, so
            # every P3 record file was being passed vacuously.
            #
            # The argv[2] correction alone left the residue this guard closes:
            # ANY kind outside the four legitimate ones (including a typo, a
            # path, or "") still matched no branch, still emitted nothing, and
            # was still scored as a PASS. Unknown kinds and a missing kind
            # argument are rejected VISIBLY here, on stdout, exit 0 to honour
            # the checker contract (ERR lines on stdout; return 2 only for
            # usage/unknown mode). A silent return would reintroduce D5.
            if len(sys.argv) < 4:
                print("ERR\trecords requires a kind and a path; "
                      "usage: check_p3.py records <%s> <path>"
                      % "|".join(sorted(RECORD_COLLECTIONS)))
                return 0
            kind = sys.argv[2]
            if kind not in RECORD_COLLECTIONS:
                print("ERR\tunknown records kind %r; expected one of: %s"
                      % (kind, ", ".join(sorted(RECORD_COLLECTIONS))))
                return 0
            check_records(kind, sys.argv[3])
        elif mode == "gate":
            ok, reasons = engine.promote(json.load(open(sys.argv[2])))
            for m in reasons:
                print("ERR\t%s" % m)
            print("PROMOTED" if ok else "REJECTED")
            return 0
        else:
            print("unknown mode %s" % mode)
            return 2
    except Exception as ex:
        print("ERR\tnot valid structured input: %s" % ex)
        return 0
    for msg in e:
        print("ERR\t%s" % msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
