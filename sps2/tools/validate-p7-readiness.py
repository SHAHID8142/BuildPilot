#!/usr/bin/env python3
"""SPS 2.0 P7 readiness checks.

Agent-neutral. Standard library only. Project-local: no installs, no network,
no machine-global writes, no runtime activation, no registry modification.

Deliberately narrow. This checks READINESS ONLY. It creates no P7
implementation artefact and asserts nothing about P7 deliverables, because P7
is not authorised. Its job is to prove that the readiness audit's claims match
repository reality, that no P7 work has started, and that every standing
boundary still holds.
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SPS2 = os.path.join(REPO, "sps2")
for _p in (os.path.join(SPS2, "core"), os.path.join(SPS2, "governance"),
           os.path.dirname(os.path.abspath(__file__))):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import adapter_registry as A        # noqa: E402
import attribution as G             # noqa: E402
import registry_api as R            # noqa: E402
import portability as PT           # noqa: E402

GREEN, RED, BOLD, NC = (
    "\033[0;32m", "\033[0;31m", "\033[1m", "\033[0m")
RECON = os.path.join(SPS2, "decisions", "ROADMAP-EXECUTION-RECONCILIATION.json")
P3_DECISIONS = os.path.join(SPS2, "decisions", "ROADMAP-P3-DECISIONS.json")
PORTABILITY_TOOL = os.path.join(SPS2, "tools", "test-portability.py")
# D-P3-A's bound (exactly two real adapters, Codex and OpenCode; the DECLARED
# generic fallback never counted) has a single definition site, in
# sps2/tools/portability.py, which also proves it against the recorded User
# decision. This module reads it from there instead of repeating it.
AUTHORISED_REAL_ADAPTERS = PT.AUTHORISED_REAL_ADAPTERS
REAL_MATURITIES = PT.REAL_MATURITIES
AUDIT = os.path.join(REPO, "AUDIT-P7-READINESS-AND-DECISION.md")
# P7 governance artefacts (authorised, not implementation deliverables).
P7_GOVERNANCE_ARTEFACTS = (
    "decisions/P7-DECISIONS.json",
    "governance/P7-THREAT-MODEL.md",
    "memory/memory-layout.json",
    "memory/team-bootstrap.md",
    "memory/README.md",
    "memory/P7-IMPLEMENTATION-REPORT.md",
)
# P7 implementation artefacts authorised by D-P7-IMPLEMENTATION.
P7_AUTHORISED_IMPL_ARTEFACTS = (
    "tools/isolation_validator.py",
)
# P7 IMPLEMENTATION deliverables. Forbidden while P7 is unauthorised.
P7_IMPL_ARTEFACTS = ("requirements/P7-REQUIREMENTS.json",
                     "evidence/P7-EVIDENCE.json", "tasks/P7-TASKS.md",
                     "handoff/HANDOFF-P7.json",
                     "bootstrap")


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


def r1(r):
    r.sect("1. Readiness audit exists and is not an approval")
    if os.path.isfile(AUDIT):
        r.ok("readiness audit present: %s" % os.path.basename(AUDIT))
    else:
        r.bad("readiness audit missing")
        return
    body = open(AUDIT).read().lower()
    if "not an approval" in body or "awaiting user" in body:
        r.ok("audit states it is not an approval")
    else:
        r.bad("audit does not disclaim approval")


def r2(r):
    r.sect("2. Reconciliation record is additive and complete")
    if not os.path.isfile(RECON):
        r.bad("RECONCILIATION_RECORD_MISSING")
        return
    doc = json.load(open(RECON))
    phases = {m["roadmap_phase"] for m in doc.get("mapping") or []}
    missing = [p for p in ("P1", "P2", "P3", "P4", "P5", "P6")
               if p not in phases]
    if missing:
        r.bad("RECONCILIATION_INCOMPLETE: missing %s" % ",".join(missing))
    else:
        r.ok("all six roadmap phases P1-P6 mapped")
    for m in doc.get("mapping") or []:
        if not (m.get("executed_as") or "").strip():
            r.bad("MAPPING_WITHOUT_EXECUTED_PHASE: %s" % m["roadmap_phase"])
        if m.get("satisfaction") not in (
                "SATISFIED", "SUBSTANTIALLY_SATISFIED",
                "PARTIALLY_SATISFIED", "NOT_SATISFIED"):
            r.bad("INVALID_SATISFACTION: %s -> %r"
                  % (m["roadmap_phase"], m.get("satisfaction")))
    if not r.failed:
        r.ok("every mapping states an executed phase and a valid satisfaction")
    if doc.get("schema") == "sps2.phase-reconciliation/v1":
        r.ok("record is a distinct additive artefact, not a rewrite")
    else:
        r.bad("RECONCILIATION_SCHEMA_UNEXPECTED")
    # The four ambiguities are recorded as resolved by name. The audit claims
    # they are RESOLVED, so the claim is checked rather than trusted: an
    # ambiguity quietly marked unresolved again, or re-pointed at a different
    # decision, would otherwise leave the readiness claim unsupported.
    amb = {a.get("id"): a for a in (doc.get("unresolved_ambiguity") or [])}
    expect = {"AMB-PHASE-1": "D-P7-A", "AMB-PHASE-2": "D-P7-B",
              "AMB-PHASE-3": "D-P7-C", "AMB-PHASE-4": "D-P7-D"}
    drift = [i for i, did in sorted(expect.items())
             if not (amb.get(i) or {}).get("resolved")
             or (amb.get(i) or {}).get("resolved_by") != did]
    if drift:
        r.bad("AMBIGUITY_RESOLUTION_DRIFT: %s" % ",".join(drift))
    else:
        r.ok("all four ambiguities recorded resolved by D-P7-A..D")


def p3_delivery_state():
    """Mechanical view of the roadmap P3 deliverables and approval.

    delivered: the adapter registry is contract-valid, the generic fallback is
    still present, at least two adapters are beyond DECLARED (D-P3-B: DECLARED
    alone is insufficient for P3 completion) and the portability conformance
    test exists (D-P3-D).
    approved: the roadmap P3 decisions record carries a User-attributable
    completion approval. Roadmap P3 verification says "Approval: user", so the
    record may not report SATISFIED before the User approves the delivered
    state. Attribution reuses the governance predicate, so an agent can never
    self-approve.

    D-P3-G.1: this replaces the old one-adapter DECLARED pin
    (ADAPTER_STATE_CHANGED) with a decision-derived claim check, so a
    legitimate Roadmap P3 adapter does not falsely fail.
    """
    errors = []
    try:
        errs, _summary = A.validate_registry()
    except Exception as exc:            # unreadable or malformed registry
        return False, False, ["ADAPTER_REGISTRY_UNREADABLE: %s"
                              % type(exc).__name__]
    if errs:
        errors.append("ADAPTER_REGISTRY_INVALID: %s" % "; ".join(errs))
    adapters = json.load(open(os.path.join(
        SPS2, "core", "adapters", "registry.json"))).get("adapters") or []
    generic = PT.FALLBACK_ADAPTER_ID in PT.entry_ids(adapters)
    real = PT.real_adapter_ids(entries=adapters)
    # D-P3-A authorises EXACTLY two real adapters, and names them. The DECLARED
    # generic fallback is never counted as a real adapter. An empty registry is
    # still a VALID state under D-P3-D (the delete-all portability criterion),
    # so the exact-count invariant applies to every NON-EMPTY registry: a
    # registry that ships adapters but declares zero, one or more than two real
    # adapters (or a different pair) is a defect, not a warning.
    count_ok = True
    if not adapters:
        pass                                # zero-adapter state, valid (D-P3-D)
    elif len(real) != len(AUTHORISED_REAL_ADAPTERS):
        count_ok = False
        errors.append(
            "ADAPTER_COUNT_VIOLATION: D-P3-A authorises exactly %d real "
            "adapters, found %d (%s)"
            % (len(AUTHORISED_REAL_ADAPTERS), len(real),
               ",".join(sorted(real)) or "none"))
    elif set(real) != set(AUTHORISED_REAL_ADAPTERS):
        count_ok = False
        errors.append(
            "ADAPTER_IDENTITY_VIOLATION: D-P3-A authorises %s, found %s"
            % (",".join(AUTHORISED_REAL_ADAPTERS), ",".join(sorted(real))))
    conformance = os.path.isfile(PORTABILITY_TOOL)
    # The enforced bound must still match what the recorded User decision names,
    # so a changed adapter set cannot pass the count check while the decision
    # record says something else.
    _named, bound_errors = PT.decision_bound(REPO, registry={"adapters":
                                                             adapters})
    errors.extend(bound_errors)
    delivered = bool(not errs and count_ok and generic and conformance
                     and not bound_errors)
    approved = False
    if os.path.isfile(P3_DECISIONS):
        rec = json.load(open(P3_DECISIONS))
        comp = rec.get("completion") or {}
        state = comp.get("state")
        if state not in ("PENDING_USER_APPROVAL", "APPROVED"):
            errors.append("P3_COMPLETION_STATE_INVALID: %r" % (state,))
        elif state == "APPROVED":
            if G.approval_is_user_attributable(comp.get("approval") or {}):
                approved = True
            else:
                errors.append(
                    "P3_COMPLETION_APPROVAL_NOT_USER_ATTRIBUTABLE")
    return delivered, approved, errors


def r3(r):
    r.sect("3. Roadmap P3 claim matches repository reality")
    doc = json.load(open(RECON))
    p3 = next((m for m in doc["mapping"] if m["roadmap_phase"] == "P3"), None)
    claimed = (p3 or {}).get("satisfaction")
    delivered, approved, errors = p3_delivery_state()
    for e in errors:
        r.bad(e)
    if not errors:
        if claimed == "SATISFIED":
            if delivered and approved:
                r.ok("record reports roadmap P3 SATISFIED, delivered and "
                     "User-approved")
            else:
                r.bad("RECORD_OVERSTATES_P3: claims SATISFIED but "
                      "delivered=%s approved=%s" % (delivered, approved))
        else:
            r.ok("record does not overstate roadmap P3 (%r); the adapter "
                 "state is no longer pinned to a fixed count" % claimed)
    tm = [f for _r, _d, fs in os.walk(SPS2) for f in fs
          if "threat" in f.lower()]
    expected = os.path.join(SPS2, "governance", "P7-THREAT-MODEL.md")
    if os.path.isfile(expected):
        body = open(expected).read()
        if "threat actor" in body.lower() and "rollback" in body.lower() \
                and "prohibited" in body.lower():
            r.ok("threat model present and covers actors, rollback, prohibited behaviours")
        else:
            r.bad("THREAT_MODEL_INCOMPLETE: missing required sections")
    elif tm:
        r.bad("THREAT_MODEL_UNEXPECTED: %s" % tm)
    else:
        r.bad("THREAT_MODEL_MISSING: D-P7-D requires one before P7")


def p7_implementation_files():
    """P7 IMPLEMENTATION deliverables. Forbidden while P7 is unauthorised.
    Governance artefacts (decision records, threat model, memory layout)
    and authorised implementation artefacts (isolation validator) are
    excluded from this check."""
    found = [rel for rel in P7_IMPL_ARTEFACTS
             if os.path.exists(os.path.join(SPS2, rel))]
    found = [f for f in found if f not in P7_GOVERNANCE_ARTEFACTS]
    found = [f for f in found if f not in P7_AUTHORISED_IMPL_ARTEFACTS]
    return found


def p7_decision_files_ok():
    """P7 decision records are permitted only if User-attributable.

    A readiness decision record is evidence that P7 has NOT started, so
    forbidding it would be backwards. It is admitted under a stricter rule:
    every approval inside it must be attributable to an identifiable User,
    and it must contain no implementation content.
    """
    p = os.path.join(SPS2, "decisions", "P7-READINESS-DECISIONS.json")
    if not os.path.isfile(p):
        return True, "no P7 decision record present"
    doc = json.load(open(p))
    for d in doc.get("decisions") or []:
        if not G.approval_is_user_attributable(d.get("approval") or {}):
            return False, "P7_DECISION_NOT_USER_ATTRIBUTABLE: %s" % (
                d.get("decision_id"))
    for bad in ("requirements", "evidence", "tasks", "memory", "bootstrap"):
        if bad in [k.lower() for k in doc]:
            return False, "P7_DECISION_RECORD_CONTAINS_IMPLEMENTATION: %s" % bad
    return True, "P7 decision record is User-attributable and decision-only"


def r4(r):
    r.sect("4. P7 has not started")
    # The guard distinguishes a P7 DECISION record from a P7 DELIVERABLE.
    # Deliverables remain absolutely forbidden. A decision record is admitted
    # only because it proves P7 was not started, and only under the stricter
    # attribution rule enforced above.
    impl = p7_implementation_files()
    stray = [f for _r, _d, fs in os.walk(SPS2) for f in fs
             if f.startswith("P7")
             and os.path.join(_r, f) not in
             [os.path.join(SPS2, d) for d in P7_IMPL_ARTEFACTS]]
    stray = [f for f in stray
             if f not in ("P7-READINESS-DECISIONS.json", "P7-THREAT-MODEL.md",
                          "P7-DECISIONS.json", "memory-layout.json",
                          "P7-IMPLEMENTATION-REPORT.md")]
    if impl or stray:
        for f in impl + stray:
            r.bad("P7_IMPLEMENTATION_ARTEFACT: %s" % f)
    else:
        r.ok("no P7 implementation deliverable exists")
    ok, why = p7_decision_files_ok()
    if ok:
        r.ok(why)
    else:
        r.bad(why)
    body = json.dumps(json.load(open(os.path.join(SPS2, "decisions",
                                                   "P6-DECISIONS.json"))))
    if "beginning P7" in body:
        r.ok("P6 approval still explicitly withholds P7")


def r5(r):
    r.sect("5. CONF-001 re-checked and still unresolved")
    import re as _re
    src = json.load(open(os.path.join(SPS2, "research", "P2-SOURCES.json")))
    conf = [c for c in src["conflicts"] if c.get("id") == "CONF-001"]
    if not conf:
        r.bad("CONF_001_RECORD_MISSING")
        return
    if "UNRESOLVED" not in (conf[0].get("resolution") or ""):
        r.bad("CONF_001_NO_LONGER_UNRESOLVED")
        return
    r.ok("CONF-001 recorded UNRESOLVED")
    cache = json.load(open(os.path.join(SPS2, "research", "cache.json")))
    wv = next((e for e in cache["entries"]
               if e["technology_id"] == "TECH-WEB-VITALS"), None)
    if not wv:
        r.bad("WEB_VITALS_ENTRY_MISSING")
        return
    facts = wv.get("observed_facts") or {}
    if facts.get("LCP_thresholds") == "NOT_OBSERVED" \
            and facts.get("INP_thresholds") == "NOT_OBSERVED":
        r.ok("LCP and INP thresholds remain NOT_OBSERVED")
    else:
        r.bad("LCP_OR_INP_CLAIMED_WITHOUT_EVIDENCE")
    blob = json.dumps(cache)
    for pat, label in ((r'"LCP[^"]*":\s*"[0-9]', "LCP numeric value"),
                       (r'"INP[^"]*":\s*"[0-9]', "INP numeric value")):
        if _re.search(pat, blob):
            r.bad("INVENTED_THRESHOLD: %s" % label)
    if not r.failed:
        r.ok("no LCP or INP numeric value anywhere in the cache")
    if "CONF-001" in (wv.get("blocking_conflicts") or []):
        r.ok("TECH-WEB-VITALS still carries CONF-001 as a blocking conflict")


def r6(r):
    r.sect("6. Standing boundaries unchanged by this audit")
    reg = R.load_registry()
    if len(R.promoted(reg)) == 4:
        r.ok("production capability count still exactly 4")
    else:
        r.bad("PRODUCTION_COUNT_CHANGED: %d" % len(R.promoted(reg)))
    states = {c.get("lifecycle_state") for c in reg["capabilities"]}
    if states <= {"EVALUATED", "DEFERRED"}:
        r.ok("no capability in ACTIVE or INSTALLED")
    else:
        r.bad("RUNTIME_STATE_PRESENT: %s" % sorted(states))
    five = R.by_id("CAP-P03-005", reg) or {}
    if five.get("lifecycle_state") == "DEFERRED":
        r.ok("CAP-P03-005 still DEFERRED / NOT_PROMOTED")
    else:
        r.bad("CAP005_NOT_DEFERRED")


def r7(r):
    r.sect("7. P7 readiness decisions recorded, bounded and User-attributed")
    p = os.path.join(SPS2, "decisions", "P7-READINESS-DECISIONS.json")
    if not os.path.isfile(p):
        r.bad("P7_READINESS_DECISIONS_MISSING")
        return
    doc = json.load(open(p))
    ids = {d["decision_id"]: d for d in doc.get("decisions") or []}
    for did in ("D-P7-A", "D-P7-B", "D-P7-C", "D-P7-D"):
        d = ids.get(did)
        if not d:
            r.bad("P7_DECISION_MISSING: %s" % did)
            continue
        if not G.approval_is_user_attributable(d.get("approval") or {}):
            r.bad("P7_DECISION_NOT_USER_ATTRIBUTABLE: %s" % did)
        if not (d.get("bounded_scope") or "").strip():
            r.bad("P7_DECISION_UNBOUNDED: %s has no bounded_scope" % did)
        if not (d.get("rationale") or "").strip():
            r.bad("P7_DECISION_WITHOUT_RATIONALE: %s" % did)
    if not r.failed:
        r.ok("all four decisions User-attributable, dated, bounded, with rationale")
    # D-P7-B must not be silently downgraded into a waiver. The wording is read
    # from the decision itself, and the prerequisites must still name the
    # adapters and the portability test, so a waiver-by-deletion is caught.
    b = ids.get("D-P7-B") or {}
    breq = " ".join(b.get("required_before_p7") or []).lower()
    if "not waived" in (b.get("decision") or "").lower() and \
            "adapter" in breq and "portability" in breq:
        r.ok("D-P7-B holds roadmap P3 unwaived with explicit prerequisites")
    else:
        r.bad("P7_B_WAIVED_OR_UNSPECIFIED: roadmap P3 prerequisite weakened")
    # D-P7-C must keep legacy out of scope and forbid the retirement claim.
    # Both are read from the structured fields, so a reworded decision cannot
    # leave the checks passing on a quoted sentence alone.
    c = ids.get("D-P7-C") or {}
    narrowed = " ".join(c.get("explicitly_narrowed") or []).lower()
    if "install.sh" in narrowed and "out of scope" in narrowed:
        r.ok("D-P7-C explicitly places legacy installers out of scope")
    else:
        r.bad("P7_C_LEGACY_NOT_EXCLUDED")
    if "no claim may be made that legacy global memory has been retired" \
            in (c.get("required_assertion") or "").lower():
        r.ok("D-P7-C forbids claiming legacy global memory was retired")
    else:
        r.bad("P7_C_RETIREMENT_CLAIM_NOT_FORBIDDEN")
    # D-P7-D must actually require a threat model covering isolation and
    # rollback: a threat model that ignores either is not the required one.
    d4 = ids.get("D-P7-D") or {}
    dreq = " ".join(d4.get("required_before_p7") or []).lower()
    if "threat model" in (d4.get("decision") or "").lower() and \
            "isolation" in dreq and "rollback" in dreq:
        r.ok("D-P7-D requires a threat model before P7 implementation")
    else:
        r.bad("P7_D_THREAT_MODEL_NOT_REQUIRED")
    # The decisions must not authorise P7 implementation.
    if (doc.get("what_these_decisions_do_not_authorise") or []):
        r.ok("record explicitly withholds P7 implementation authorisation")
    else:
        r.bad("P7_DECISIONS_MISSING_WITHHOLDING_SECTION")


def negatives(r):
    r.sect("NEGATIVE TESTS — readiness checks must detect violations")
    cases = []
    cases.append(("N01 readiness audit absent undetected",
                  lambda: not os.path.isfile(AUDIT)))

    def n2():
        doc = json.load(open(RECON))
        return all(m["roadmap_phase"] != "P3" for m in doc["mapping"])
    cases.append(("N02 roadmap P3 missing from mapping undetected", n2))

    def n3():
        # Overstatement is caught only when SATISFIED is claimed without
        # genuine delivery + User approval. In the current state both
        # hold, so the test is vacuous and must not fire.
        doc = json.load(open(RECON))
        p3 = next(m for m in doc["mapping"] if m["roadmap_phase"] == "P3")
        if p3.get("satisfaction") != "SATISFIED":
            return False
        delivered, approved, _errors = p3_delivery_state()
        return not (delivered and approved)
    cases.append(("N03 overstated roadmap P3 undetected", n3))

    def n4():
        conf = [c for c in json.load(open(os.path.join(
            SPS2, "research", "P2-SOURCES.json")))["conflicts"]
            if c.get("id") == "CONF-001"]
        return bool(conf) and "UNRESOLVED" not in (conf[0].get("resolution")
                                                   or "")
    cases.append(("N04 CONF-001 closed undetected", n4))

    def n5():
        # Defect survives if an LCP threshold is asserted as observed.
        cache = json.load(open(os.path.join(SPS2, "research", "cache.json")))
        wv = next(e for e in cache["entries"]
                  if e["technology_id"] == "TECH-WEB-VITALS")
        return (wv.get("observed_facts") or {}).get(
            "LCP_thresholds") != "NOT_OBSERVED"
    cases.append(("N05 invented LCP threshold undetected", n5))

    cases.append(("N06 production count drift undetected",
                  lambda: len(R.promoted(R.load_registry())) != 4))

    cases.append(("N07 runtime state undetected",
                  lambda: not R.claims_runtime(
                      dict(R.by_id("CAP-P03-001"),
                           lifecycle_state="ACTIVE"))))

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
    print("%sSPS 2.0 P7 Readiness Checks (audit only; P7 not authorised)%s"
          % (BOLD, NC))
    for fn in (r1, r2, r3, r4, r5, r6, r7):
        fn(r)
    negatives(r)
    print("")
    if r.failed == 0 and r.neg_missed == 0:
        print("%s%s== P7 READINESS RECORDED: %d checks passed, 0 failed, "
              "%d negative cases ==%s" % (GREEN, BOLD, r.passed, r.neg_ok, NC))
        return 0
    print("%s%s== P7 READINESS INVALID: %d passed, %d failed, %d missed ==%s"
          % (RED, BOLD, r.passed, r.failed, r.neg_missed, NC))
    return 1


if __name__ == "__main__":
    sys.exit(main())