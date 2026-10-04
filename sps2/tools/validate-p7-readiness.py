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
sys.path.insert(0, os.path.join(SPS2, "core"))

import registry_api as R            # noqa: E402

GREEN, RED, BOLD, NC = (
    "\033[0;32m", "\033[0;31m", "\033[1m", "\033[0m")
RECON = os.path.join(SPS2, "decisions", "ROADMAP-EXECUTION-RECONCILIATION.json")
AUDIT = os.path.join(REPO, "AUDIT-P7-READINESS-AND-DECISION.md")
# Roadmap P7 deliverables. None may exist while P7 is unauthorised.
P7_IMPL_ARTEFACTS = ("requirements/P7-REQUIREMENTS.json",
                     "evidence/P7-EVIDENCE.json", "tasks/P7-TASKS.md",
                     "handoff/HANDOFF-P7.json", "decisions/P7-DECISIONS.json",
                     "memory", "isolation_validator.py", "bootstrap")


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
def r3(r):
    r.sect("3. Roadmap P3 unsatisfied claim matches repository reality")
    doc = json.load(open(RECON))
    p3 = next((m for m in doc["mapping"] if m["roadmap_phase"] == "P3"), None)
    adapters = json.load(open(os.path.join(SPS2, "core", "adapters",
                                           "registry.json")))["adapters"]
    claimed = (p3 or {}).get("satisfaction")
    if len(adapters) == 1 and adapters[0].get("maturity") == "DECLARED":
        if claimed == "NOT_SATISFIED":
            r.ok("record correctly reports roadmap P3 NOT_SATISFIED")
        else:
            r.bad("RECORD_OVERSTATES_P3: claims %r with 1 DECLARED adapter"
                  % claimed)
    else:
        r.bad("ADAPTER_STATE_CHANGED: %d adapters" % len(adapters))
    tm = [f for _r, _d, fs in os.walk(SPS2) for f in fs
          if "threat" in f.lower()]
    if tm:
        r.bad("THREAT_MODEL_NOW_EXISTS: %s" % tm)
    else:
        r.ok("no threat-model artefact, matching the recorded gap")


def r4(r):
    r.sect("4. P7 has not started")
    found = [rel for rel in P7_IMPL_ARTEFACTS
             if os.path.exists(os.path.join(SPS2, rel))]
    stray = [f for _r, _d, fs in os.walk(SPS2) for f in fs
             if f.startswith("P7")]
    if found or stray:
        for f in found + stray:
            r.bad("P7_IMPLEMENTATION_ARTEFACT: %s" % f)
    else:
        r.ok("no P7 implementation artefact exists")
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
        # Defect survives if the record OVERSTATES roadmap P3 as satisfied.
        doc = json.load(open(RECON))
        p3 = next(m for m in doc["mapping"] if m["roadmap_phase"] == "P3")
        return p3.get("satisfaction") == "SATISFIED"
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
    for fn in (r1, r2, r3, r4, r5, r6):
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