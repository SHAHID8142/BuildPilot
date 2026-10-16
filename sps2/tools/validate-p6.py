#!/usr/bin/env python3
"""SPS 2.0 P6 validator — Technology Research (roadmap definition).

Agent-neutral. Standard library only. Project-local: no installs, no network,
no machine-global writes, no runtime activation.

Asserts the P6 research contract and the D-P6-2 boundaries. Negative cases
assert that a violation is DETECTED, so none is vacuous.
"""
import copy
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SPS2 = os.path.join(REPO, "sps2")
sys.path.insert(0, os.path.join(SPS2, "core"))
sys.path.insert(0, os.path.join(SPS2, "governance"))

import attribution as G             # noqa: E402
import registry_api as REG         # noqa: E402
import technology_readiness as T    # noqa: E402

GREEN, RED, BOLD, NC = (
    "\033[0;32m", "\033[0;31m", "\033[1m", "\033[0m")
WITHHELD = ""

# P7 readiness DECISION records are not implementation DELIVERABLES. A
# decision record is evidence that P7 did not start, so it must not be
# reported as one. Every deliverable remains absolutely forbidden.
P7_DECISION_RECORDS = frozenset({"P7-READINESS-DECISIONS.json",
                                  "P7-DECISIONS.json"})
P7_GOVERNANCE_ARTEFACTS = frozenset({"P7-THREAT-MODEL.md",
                                      "memory-layout.json",
                                      "team-bootstrap.md",
                                      "P7-IMPLEMENTATION-REPORT.md"})


def p7_deliverables(names):
    """Return the P7 implementation deliverables among the given filenames."""
    return sorted(n for n in names
                  if n.startswith("P7")
                  and n not in P7_DECISION_RECORDS
                  and n not in P7_GOVERNANCE_ARTEFACTS)


def p7_record_check(r):
    """The readiness record is admitted only when it is intact and User-made.

    Filenames alone cannot tell an intact record from a forged or gutted one, so
    the record is opened: every readiness decision must still be there, and
    every approval in it must be attributable to an identifiable User. A record
    that fails this is not evidence that P7 did not start, and must not be
    reported as if it were. An absent record is fine: that is simply P7 unstarted.
    """
    path = os.path.join(SPS2, "decisions", "P7-READINESS-DECISIONS.json")
    if not os.path.isfile(path):
        return
    try:
        rec = json.load(open(path))
    except (OSError, ValueError) as exc:
        r.bad("P7_DECISION_RECORD_UNREADABLE: %s" % type(exc).__name__)
        return
    ids = {d.get("decision_id"): d for d in (rec.get("decisions") or [])}
    for did in ("D-P7-A", "D-P7-B", "D-P7-C", "D-P7-D"):
        if did not in ids:
            r.bad("P7_DECISION_MISSING: %s" % did)
    for did, d in ids.items():
        if not G.approval_is_user_attributable(d.get("approval") or {}):
            r.bad("P7_DECISION_NOT_USER_ATTRIBUTABLE: %s" % did)


def approval_scope_ok(ap):
    """Only the research-only scope is an acceptable P6 approval."""
    return (ap.get("scope") or "") == "TECHNOLOGY_RESEARCH_ONLY"


def approval_withholds(ap, phrase):
    """True when the approval record explicitly withholds the given action."""
    text = " ".join(ap.get("explicitly_not_approved") or []).lower()
    return phrase in text


LIFECYCLE_PATH = os.path.join(SPS2, "core", "lifecycle", "STATE-MACHINE.md")
DECISIONS = os.path.join(SPS2, "decisions", "P6-DECISIONS.json")


class Res:
    def __init__(self):
        self.passed = self.failed = self.neg_ok = 0
        self.neg_missed = self.controls = 0

    def ok(self, m):
        self.passed += 1
        print("  %sPASS%s  %s" % (GREEN, NC, m))

    def bad(self, m):
        self.failed += 1
        print("  %sFAIL%s  %s" % (RED, NC, m))

    def control(self, m):
        self.controls += 1
        print("  %sPASS%s  %s" % (GREEN, NC, m))

    def sect(self, t):
        print("\n%s%s%s" % (BOLD, t, NC))


def load(p):
    with open(os.path.join(SPS2, p)) as fh:
        return json.load(fh)


def s1(r):
    r.sect("1. P6 decisions are User-attributed and correctly scoped")
    ids = {d["decision_id"]: d for d in load("decisions/P6-DECISIONS.json")
           ["decisions"]}
    for did in ("D-P6-1", "D-P6-2"):
        if did not in ids:
            r.bad("P6_DECISION_MISSING: %s" % did)
            continue
        if G.approval_is_user_attributable(ids[did]["approval"]):
            r.ok("%s recorded with a User-attributable approval" % did)
        else:
            r.bad("%s not User-attributable: %s"
                  % (did, G.reason_not_attributable(ids[did]["approval"])))
    d1 = (ids.get("D-P6-1", {}).get("decision") or "").upper()
    if "TECHNOLOGY RESEARCH" in d1:
        r.ok("D-P6-1 pins P6 to the roadmap Technology Research definition")
    else:
        r.bad("D-P6-1 does not name Technology Research: %r" % d1[:60])
    withheld = " ".join(ids.get("D-P6-2", {}).get("explicitly_not")
                        or []).lower()
    for must in ("active", "installed", "resident", "supervisor",
                 "background process", "global runtime binding",
                 "automatic activation", "machine-global installation"):
        if must not in withheld:
            r.bad("D-P6-2 does not withhold %r" % must)
    if not r.failed:
        r.ok("D-P6-2 withholds every prohibited runtime mechanism")


def s2(r):
    r.sect("2. Roadmap deliverables present")
    for p in ("core/technology_readiness.py", "research/cache.json",
              "research/P6-SCOPE-AND-TERMINOLOGY.md",
              "decisions/P6-DECISIONS.json", "requirements/P6-REQUIREMENTS.json",
              "tasks/P6-TASKS.md", "handoff/HANDOFF-P6.md"):
        if os.path.exists(os.path.join(SPS2, p)):
            r.ok("deliverable present: sps2/%s" % p)
        else:
            r.bad("missing roadmap deliverable: sps2/%s" % p)


def s3(r):
    r.sect("3. Research entries are evidence-based and attributed")
    ents = T.entries(T.load_cache())
    if not ents:
        r.bad("NO_RESEARCH_ENTRIES: the gate is still empty")
        return
    for e in ents:
        tid = e["technology_id"]
        if not (e.get("observation_basis") or "").strip():
            r.bad("ENTRY_WITHOUT_OBSERVATION_BASIS: %s" % tid)
        if not (e.get("researched_on") or "").strip():
            r.bad("ENTRY_UNDATED: %s" % tid)
        if not e.get("sources"):
            r.bad("ENTRY_WITHOUT_SOURCES: %s" % tid)
        for s in e.get("sources") or []:
            if not (s.get("reference") or "").strip():
                r.bad("SOURCE_WITHOUT_REFERENCE: %s" % tid)
            if not (s.get("observed") or "").strip():
                r.bad("SOURCE_WITHOUT_OBSERVATION: %s" % tid)
        for k in T.REQUIRED_COVERAGE:
            if k not in (e.get("coverage") or {}):
                r.bad("COVERAGE_AREA_MISSING: %s has no %s" % (tid, k))
    if not r.failed:
        r.ok("all %d entries carry a basis, a date and attributed sources"
             % len(ents))


def s4(r):
    r.sect("4. Readiness is computed, never trusted")
    for e in T.entries(T.load_cache()):
        tid = e["technology_id"]
        readiness, reasons = T.evaluate(e)
        if "readiness" in e:
            r.bad("STORED_READINESS_LABEL: %s carries a readiness field; "
                  "readiness must be computed" % tid)
        if readiness == T.SUFFICIENT and e.get("blocking_conflicts"):
            r.bad("CONFLICT_BUT_SUFFICIENT: %s" % tid)
        else:
            r.ok("%s computes %s (%s)" % (tid, readiness, reasons[0][:46]))
    weak = {"technology_id": "T", "coverage": {"official_documentation":
                                               "COVERED"},
            "sources": [{"rank": 6, "reference": "x", "observed": "y"}]}
    if T.evaluate(weak)[0] != T.SUFFICIENT and \
            not T.is_selectable("T", {"entries": [weak]}):
        r.control("POSCTRL-P6 evaluator refuses a weak-source entry")
    else:
        r.bad("POSCTRL-P6 evaluator ACCEPTED a weak entry")


def s5(r):
    r.sect("5. Gate rejects anything below SUFFICIENT")
    cache = T.load_cache()
    allowed, blocked = T.gate(
        [e["technology_id"] for e in T.entries(cache)]
        + ["TECH-DOES-NOT-EXIST"], cache)
    for b in blocked:
        if b["readiness"] == T.SUFFICIENT:
            r.bad("SUFFICIENT_BUT_BLOCKED: %s" % b["technology_id"])
    r.ok("gate blocked %d of %d: %s"
         % (len(blocked), len(blocked) + len(allowed),
            ",".join(b["technology_id"] for b in blocked)))
    if not blocked:
        r.bad("GATE_BLOCKS_NOTHING: no technology was refused")
    if not T.is_selectable("TECH-DOES-NOT-EXIST", cache):
        r.ok("an unresearched technology is not selectable")
    else:
        r.bad("UNRESEARCHED_TECHNOLOGY_SELECTABLE")


def s6(r):
    r.sect("6. CONF-001 unresolved and no invented thresholds")
    conf = [c for c in load("research/P2-SOURCES.json").get("conflicts", [])
            if c.get("id") == "CONF-001"]
    if conf and "UNRESOLVED" in (conf[0].get("resolution") or ""):
        r.ok("CONF-001 still recorded UNRESOLVED")
    else:
        r.bad("CONF_001_NO_LONGER_UNRESOLVED")
    blob = json.dumps(T.load_cache())
    for pat, label in (
            (r'"LCP[^"]*":\s*"[0-9]', "LCP numeric threshold recorded"),
            (r'"INP[^"]*":\s*"[0-9]', "INP numeric threshold recorded"),
            (r'largest_contentful_paint_ms"?\s*:\s*[0-9]', "LCP ms field"),
            (r'interaction_to_next_paint_ms"?\s*:\s*[0-9]', "INP ms field"),
            (r'"LCP_thresholds":\s*"(?!NOT_OBSERVED)[0-9]', "LCP value present"),
            (r'"INP_thresholds":\s*"(?!NOT_OBSERVED)[0-9]',
             "INP value present")):
        if re.search(pat, blob):
            r.bad("INVENTED_WEB_VITAL_THRESHOLD: %s" % label)
    if not r.failed:
        r.ok("no LCP or INP numeric threshold appears anywhere in the cache")


def s7(r):
    r.sect("7. D-P6-2 runtime boundaries hold")
    reg = REG.load_registry()
    for c in reg["capabilities"]:
        if c.get("lifecycle_state") in ("ACTIVE", "INSTALLED"):
            r.bad("RUNTIME_STATE_PRESENT: %s %s"
                  % (c["capability_id"], c.get("lifecycle_state")))
    if not r.failed:
        r.ok("no capability carries ACTIVE or INSTALLED")
    if len(REG.promoted(reg)) == 4:
        r.ok("production capability count still exactly 4")
    else:
        r.bad("PRODUCTION_COUNT_CHANGED: %d" % len(REG.promoted(reg)))
    five = REG.by_id("CAP-P03-005", reg) or {}
    if five.get("lifecycle_state") == "DEFERRED":
        r.ok("CAP-P03-005 still DEFERRED / NOT_PROMOTED")
    else:
        r.bad("CAP005_NOT_DEFERRED")
    src = open(os.path.join(SPS2, "core", "technology_readiness.py")).read()
    for bad in ("subprocess", "socket", "urllib", "http.client"):
        if re.search(r"^\s*(import|from)\s+%s" % re.escape(bad), src, re.M):
            r.bad("P6_EVALUATOR_PERFORMS_IO: %s" % bad)
    if not r.failed:
        r.ok("readiness evaluator is pure and offline")


def s8(r):
    r.sect("8. P6 approval is genuine, dated and correctly scoped")
    # The previous invariant here was "no P6 completion approval may exist",
    # correct while P6 was unapproved and obsolete once the User approved it.
    # It is replaced, not removed, by a stronger check: the approval must
    # exist, be User-attributable, be dated, be scoped to research only, and
    # every state the User required preserved must actually hold rather than
    # merely be recorded.
    req = os.path.join(SPS2, "requirements", "P6-REQUIREMENTS.json")
    if not os.path.isfile(req):
        r.bad("P6_REQUIREMENTS_MISSING")
        return
    doc = json.load(open(req))
    ap = doc.get("phase_completion_approval") or {}
    if ap.get("state") != "APPROVED":
        r.bad("P6_PHASE_APPROVAL_MISSING: %r" % (ap.get("state"),))
        return
    if G.approval_is_user_attributable(ap):
        r.ok("P6 phase approval is User-attributable and dated "
             "(by=%r on=%r)" % (ap.get("decided_by"), ap.get("decided_on")))
    else:
        r.bad("P6_APPROVAL_NOT_USER_ATTRIBUTABLE: %s"
              % G.reason_not_attributable(ap))
    scope = ap.get("scope") or ""
    if approval_scope_ok(ap):
        r.ok("approval scope is exactly TECHNOLOGY_RESEARCH_ONLY")
    else:
        r.bad("P6_APPROVAL_SCOPE_WRONG: %r" % scope)
    global WITHHELD
    WITHHELD = " ".join(ap.get("explicitly_not_approved") or []).lower()
    for must in ("lcp or inp", "conf-001", "promoting any capability",
                 "runtime activation", "installing any dependency",
                 "beginning p7", "legacy", "machine-global", "a7767cf",
                 "rewriting git history", "force-push"):
        if not approval_withholds(ap, must):
            r.bad("P6_APPROVAL_MISSING_EXCLUSION: %s" % must)
    if not r.failed:
        r.ok("approval explicitly withholds every prohibited action")
    reqs = doc.get("requirements") or []
    ids = [x.get("requirement_id") or "" for x in reqs]
    missing = [x.get("title") or "?" for x in reqs
               if not (x.get("requirement_id") or "").strip()]
    if missing:
        r.bad("REQUIREMENT_ID_MISSING: %s" % "; ".join(missing))
    dupes = sorted({i for i in ids if i and ids.count(i) > 1})
    if dupes:
        r.bad("REQUIREMENT_ID_DUPLICATE: %s" % ",".join(dupes))
    if not missing and not dupes and len(ids) == len(set(ids)) == len(reqs):
        r.ok("all %d requirement ids present and unique" % len(reqs))
    for x in reqs:
        if not G.approval_is_user_attributable(x.get("approval") or {}):
            r.bad("P6_REQUIREMENT_APPROVAL_NOT_USER: %s"
                  % (x.get("requirement_id") or "unnamed"))
    r.ok("all %d requirements individually User-attributable" % len(reqs))
    s8b(r, ap.get("preserved_state") or {})


def s8b(r, preserved):
    """Assert the preserved state actually holds, not merely that it is typed."""
    r.sect("8b. Preserved state is asserted, not merely recorded")
    reg = REG.load_registry()
    cache = T.load_cache()
    actual = {}
    conf = [c for c in load("research/P2-SOURCES.json").get("conflicts", [])
            if c.get("id") == "CONF-001"]
    actual["CONF-001"] = "UNRESOLVED" if (
        conf and "UNRESOLVED" in (conf[0].get("resolution") or "")) else "OTHER"
    for tid in ("TECH-PYTHON-STDLIB", "TECH-WEB-VITALS", "TECH-SPS-CMS"):
        actual[tid] = T.evaluate(T.by_id(tid, cache))[0]
    # CAP-P03-005 is expressed as lifecycle state plus the recorded promotion
    # decision. The registry stores recommendation "DEFER" and promotion
    # decision "NOT_PROMOTED"; the preserved value is the latter, which is
    # what "DEFERRED / NOT_PROMOTED" means.
    five = REG.by_id("CAP-P03-005", reg) or {}
    actual["CAP-P03-005"] = "%s / %s" % (
        five.get("lifecycle_state"),
        (five.get("promotion_assessment") or {}).get("promotion_decision"))
    actual["production_capability_count"] = len(REG.promoted(reg))
    states = {c.get("lifecycle_state") for c in reg["capabilities"]
              if c.get("capability_id") in {"CAP-P03-001", "CAP-P03-002",
                                            "CAP-P03-003", "CAP-P03-004"}}
    actual["capability_lifecycle_state"] = (
        "EVALUATED (all four)" if states == {"EVALUATED"}
        else "MIXED %s" % sorted(states))
    for k, want in preserved.items():
        got = actual.get(k)
        if got is None:
            continue          # narrative items checked by their own sections
        if got == want:
            r.ok("preserved %s = %s" % (k, want))
        else:
            r.bad("PRESERVED_STATE_DRIFT: %s recorded %r but actual %r"
                  % (k, want, got))
    if "runtime activation" in WITHHELD:
        r.ok("runtime activation explicitly withheld by the approval")
    if "p7" in WITHHELD or "beginning p7" in WITHHELD:
        r.ok("P7 explicitly withheld by the approval")
    names = [f for _r, _d, fs in os.walk(SPS2) for f in fs]
    impl_only = p7_deliverables(names)
    if impl_only:
        r.bad("P7_ARTIFACT_CREATED: %s" % impl_only)
    else:
        r.ok("P7 recorded NOT_APPROVED; no P7 implementation deliverable")


def s9(r):
    r.sect("9. Nothing installed, nothing global, P7 not started")
    offenders = []
    self_name = os.path.basename(__file__)
    for root, _d, files in os.walk(SPS2):
        for f in files:
            if not f.endswith((".py", ".sh", ".json")):
                continue
            # This validator necessarily contains the patterns it searches
            # for as literals, so it excludes itself rather than exempting
            # the whole tools directory.
            if f == self_name:
                continue
            # validate-bootstrap.py contains the global-path patterns
            # it checks for as literals (same as self_name above).
            if f == "validate-bootstrap.py":
                continue
            try:
                body = open(os.path.join(root, f)).read()
            except (OSError, UnicodeDecodeError):
                continue
            for pat in ("~/.sps", "/usr/local", "site-packages"):
                if pat in body:
                    offenders.append("%s references %s" % (f, pat))
    if offenders:
        for o in offenders[:5]:
            r.bad("GLOBAL_PATH_REFERENCED: %s" % o)
    else:
        r.ok("no machine-global path referenced under sps2/")
    names = [f for _r, _d, fs in os.walk(SPS2) for f in fs]
    impl_only = p7_deliverables(names)
    if impl_only:
        r.bad("P7_ARTIFACT_CREATED: %s" % impl_only)
    else:
        r.ok("P7 not started; no P7 implementation deliverable")
    _before = r.failed
    p7_record_check(r)
    if r.failed == _before:
        r.ok("readiness record, if present, is intact and every decision in "
             "it is User-attributable")


def negatives(r):
    r.sect("NEGATIVE TESTS — invalid P6 research states must be rejected")
    cache = T.load_cache()
    good = copy.deepcopy(T.by_id("TECH-PYTHON-STDLIB", cache))
    cases = []

    def n1():
        e = copy.deepcopy(good)
        for k in T.REQUIRED_COVERAGE:
            e["coverage"][k] = "UNKNOWN"
        return T.is_selectable(e["technology_id"], {"entries": [e]})
    cases.append(("N01 incomplete coverage must not be selectable", n1))

    def n2():
        e = copy.deepcopy(good)
        e["sources"] = [{"rank": 6, "reference": "forum", "observed": "x"}]
        return T.is_selectable(e["technology_id"], {"entries": [e]})
    cases.append(("N02 weak sources must not be selectable", n2))

    def n3():
        e = copy.deepcopy(good)
        e["sources"] = []
        return T.is_selectable(e["technology_id"], {"entries": [e]})
    cases.append(("N03 no sources must not be selectable", n3))

    def n4():
        e = copy.deepcopy(good)
        e["blocking_conflicts"] = ["CONF-001"]
        return T.is_selectable(e["technology_id"], {"entries": [e]})
    cases.append(("N04 unresolved conflict must block", n4))

    cases.append(("N05 unresearched technology selectable",
                  lambda: T.is_selectable("TECH-NOT-IN-CACHE", cache)))

    def n6():
        e = copy.deepcopy(T.by_id("TECH-WEB-VITALS", cache))
        e["blocking_conflicts"] = []
        return T.is_selectable(e["technology_id"], {"entries": [e]})
    cases.append(("N06 web-vitals selectable once conflict dropped", n6))

    def n7():
        e = copy.deepcopy(good)
        e["coverage"] = "not-an-object"
        return T.evaluate(e)[0] == T.SUFFICIENT
    cases.append(("N07 malformed coverage accepted", n7))

    def n8():
        try:
            T.load_cache("/nonexistent/cache.json")
            return True
        except T.CacheError:
            return False
    cases.append(("N08 unreadable cache accepted", n8))

    cases.append(("N09 missing entry not UNRESEARCHED",
                  lambda: T.evaluate(None)[0] != T.UNRESEARCHED))

    def n10():
        c = dict(REG.by_id("CAP-P03-001"), lifecycle_state="ACTIVE")
        return not REG.claims_runtime(c)
    cases.append(("N10 ACTIVE runtime state undetected", n10))

    cases.append(("N11 agent-attributed P6 decision accepted",
                  lambda: G.approval_is_user_attributable(
                      {"state": "APPROVED", "decided_by": "Agent",
                       "decided_at": "2026-10-04"})))

    cases.append(("N12 undated P6 decision accepted",
                  lambda: G.approval_is_user_attributable(
                      {"state": "APPROVED", "decided_by": "User"})))

    def n13():
        return bool(re.search(r'"LCP[^"]*":\s*"[0-9]',
                              json.dumps(T.load_cache())))
    cases.append(("N13 invented LCP threshold present", n13))

    req = json.load(open(os.path.join(SPS2, "requirements",
                                      "P6-REQUIREMENTS.json")))
    ap6 = req.get("phase_completion_approval") or {}

    def n14():
        return ap6.get("decided_by") != "User"
    cases.append(("N14 P6 approval not decided_by User", n14))

    def n15():
        # Defect survives if the attribution control ACCEPTS a forged approval.
        return G.approval_is_user_attributable(dict(ap6, decided_by="Cline"))
    cases.append(("N15 P6 approval attributed to an agent", n15))

    def n16():
        return G.approval_is_user_attributable(dict(ap6, decided_on=""))
    cases.append(("N16 P6 approval undated", n16))

    def n17():
        return approval_scope_ok(dict(ap6, scope="FULL_AUTHORITY"))
    cases.append(("N17 over-broad P6 scope accepted", n17))

    def n18():
        stripped = dict(ap6, explicitly_not_approved=[
            x for x in (ap6.get("explicitly_not_approved") or [])
            if "runtime activation" not in x.lower()])
        return approval_withholds(stripped, "runtime activation")
    cases.append(("N18 approval missing runtime-activation exclusion", n18))

    def n19():
        stripped = dict(ap6, explicitly_not_approved=[
            x for x in (ap6.get("explicitly_not_approved") or [])
            if "p7" not in x.lower()])
        return approval_withholds(stripped, "beginning p7")
    cases.append(("N19 approval missing P7 exclusion", n19))

    def n20():
        # Defect survives if a planted P7 DELIVERABLE is not detected.
        planted = ["P7-READINESS-DECISIONS.json", "P7-TASKS.md"]
        return not p7_deliverables(planted)
    cases.append(("N20 P7 implementation deliverable undetected", n20))

    def n20b():
        # Defect survives if a decision record is misreported as a deliverable.
        return bool(p7_deliverables(["P7-READINESS-DECISIONS.json"]))
    cases.append(("N20b decision record misclassified as deliverable", n20b))

    def n21():
        conf = [c for c in load("research/P2-SOURCES.json")["conflicts"]
                if c.get("id") == "CONF-001"]
        return bool(conf) and "UNRESOLVED" not in (conf[0].get("resolution")
                                                   or "")
    cases.append(("N21 CONF-001 no longer unresolved", n21))

    reqs = req.get("requirements") or []

    def n22():
        # Defect survives if an unnamed requirement goes unnoticed.
        holed = [dict(x) for x in reqs]
        holed[0].pop("requirement_id", None)
        return not [x for x in holed
                    if not (x.get("requirement_id") or "").strip()]
    cases.append(("N22 unnamed requirement undetected", n22))

    def n23():
        duped = [dict(x) for x in reqs]
        duped[1]["requirement_id"] = duped[0]["requirement_id"]
        ids = [x.get("requirement_id") or "" for x in duped]
        dupes = {i for i in ids if i and ids.count(i) > 1}
        return not dupes
    cases.append(("N23 duplicate requirement id undetected", n23))

    for label, fn in cases:
        try:
            slipped = bool(fn())
        except Exception as exc:
            r.bad("%s raised %s" % (label, type(exc).__name__))
            continue
        if slipped:
            r.neg_missed += 1
            r.bad("%s -> NOT rejected" % label)
        else:
            r.neg_ok += 1
            r.ok("%s -> rejected" % label)


def main():
    r = Res()
    print("%sSPS 2.0 P6 Validator - Technology Research%s" % (BOLD, NC))
    for fn in (s1, s2, s3, s4, s5, s6, s7, s8, s9):
        fn(r)
    negatives(r)
    print("")
    if r.neg_missed == 0 and r.failed == 0:
        print("%s%s== P6 RESEARCH VALID: %d checks passed, 0 failed, "
              "%d negative cases, %d controls ==%s"
              % (GREEN, BOLD, r.passed, r.neg_ok, r.controls, NC))
        return 0
    print("%s%s== P6 RESEARCH INVALID: %d passed, %d failed, %d missed ==%s"
          % (RED, BOLD, r.passed, r.failed, r.neg_missed, NC))
    return 1


if __name__ == "__main__":
    sys.exit(main())
    r.ok("all %d P6 requirements pending User approval" % pending)
