#!/usr/bin/env python3
"""SPS 2.0 Roadmap P3 portability conformance test (D-P3-D, D-P3-E).

Agent-neutral. Standard library only. Project-local: no installs, no network,
no machine-global writes. The delete-all exercise of section 3 is delegated to
`portability.py`, which runs it on an ISOLATED COPY of the repository in a temp
directory, so the working tree is never modified; the adapter surface is
hash-compared before and after.

The mechanics live in `portability.py`, not here: what an adapter is for
deletion purposes, which core validators must stay green, and the single
definition site of the D-P3-A adapter bound that both this suite and
`validate-p7-readiness.py` import.

Sections:
  1. Adapter surface is contract-conformant and mirrored (D-P3-A..C)
  2. Core stays agent-neutral outside adapters/ (verification criterion 4)
  3. Zero-adapter portability on an isolated copy, and its restore
     (criteria 1 and 2)
  4. Fresh-agent resume checklist executed mechanically (criterion 3)

Scope note: the zero-adapter exercise runs every sps2-scoped suite listed in
`portability.CORE_VALIDATORS` (phase validators, unit tests, mutation suites,
secret safety, emoji scan). `check_sps2.py` is a library invoked by
`validate-sps2.sh`, so it runs as part of the sps2 foundation entry; the .sps
governance suite and the history-credential check read no adapter state and are
run as part of the normal-state suite instead.

Exit: 0 valid | 1 failure | 2 tooling unavailable.
"""
import copy
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPS2 = os.path.dirname(HERE)
REPO = os.path.dirname(SPS2)
for _p in (os.path.join(SPS2, "core"), os.path.join(SPS2, "governance"), HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import adapter_registry as A        # noqa: E402
import attribution as G             # noqa: E402
import portability as PT           # noqa: E402

ADAPTERS = os.path.join(SPS2, "core", "adapters")
REGISTRY = os.path.join(ADAPTERS, "registry.json")
RESUME = os.path.join(SPS2, "RESUME.md")
P3_DECISIONS = os.path.join(SPS2, "decisions", "ROADMAP-P3-DECISIONS.json")
P7_DECISIONS = os.path.join(SPS2, "decisions", "P7-READINESS-DECISIONS.json")
RECON = os.path.join(SPS2, "decisions", "ROADMAP-EXECUTION-RECONCILIATION.json")
EVIDENCE = os.path.join(SPS2, "evidence", "ROADMAP-P3-EVIDENCE.json")

# The answers a fresh agent must be able to obtain from the checklist
# (D-P3-E). The historical four are kept; the rest were missing and are now
# required, so the resume deliverable cannot silently regress to phase/task/
# next/forbidden alone.
RESUME_ANSWERS = ("What P3 is", "What was authorised", "Adapters delivered",
                  "Current phase", "Current task", "Next allowed action",
                  "What remains", "Forbidden actions", "Authoritative records",
                  "Rollback")

# The same vendor list the existing neutrality guards use.
VENDORS = ("cline", "claude", "codex", "cursor", "copilot", "windsurf",
           "aider", "gemini", "opencode", "gpt")

# Contract schema property names; mirrors "additionalProperties": false.
ALLOWED_KEYS = {"agent_id", "display_name", "maturity", "writes_global_state",
                "detection", "capabilities", "supports", "fallbacks",
                "maintainer", "verified_by"}

GREEN, RED, BOLD, NC = ("\033[0;32m", "\033[0;31m", "\033[1m", "\033[0m")


class Res:
    def __init__(self):
        self.passed = self.failed = self.controls = 0

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


def vendor_hits(root):
    """Files under root naming a vendor, excluding the adapter surface."""
    hits = []
    for r, _d, files in os.walk(root):
        if "adapters" in r:
            continue
        for f in files:
            if not f.endswith((".py", ".json")):
                continue
            p = os.path.join(r, f)
            try:
                with open(p, encoding="utf-8", errors="replace") as fh:
                    low = fh.read().lower()
            except OSError:
                continue
            for v in VENDORS:
                if v in low:
                    hits.append("%s references %r"
                                % (os.path.relpath(p, REPO), v))
    return hits


def resume_sources(text):
    return [ln.split("SOURCE:", 1)[1].strip()
            for ln in text.splitlines() if ln.startswith("SOURCE:")]


def resume_inventory(text):
    """Adapter inventory rows of the resume checklist: id -> maturity."""
    rows = {}
    for line in text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip().strip("`").strip()
                 for c in s.strip("|").split("|")]
        if len(cells) < 2:
            continue
        aid, maturity = cells[0], cells[1]
        if maturity in PT.REAL_MATURITIES or maturity == "DECLARED":
            if aid and set(aid) - set("-: "):
                rows[aid] = maturity
    return rows


def inventory_drift(rows, entries):
    """Checklist rows that disagree with the live adapter registry."""
    live = {a.get("agent_id"): a.get("maturity") for a in entries}
    drift = []
    for aid, maturity in sorted(rows.items()):
        if live.get(aid) != maturity:
            drift.append("%s: checklist %s, registry %s"
                         % (aid, maturity, live.get(aid)))
    for aid in sorted(live):
        if aid not in rows:
            drift.append("%s: in registry, absent from the checklist" % aid)
    return drift


def s1(r):
    r.sect("1. Adapter surface is contract-conformant and mirrored")
    for label in PT.CORE_OWNED_FILES:
        if os.path.isfile(os.path.join(ADAPTERS, label)):
            r.ok("present: sps2/core/adapters/%s" % label)
        else:
            r.bad("ADAPTER_SURFACE_FILE_MISSING: %s" % label)
    if not os.path.isfile(REGISTRY):
        return
    try:
        reg = A.load_registry()
    except Exception as exc:
        r.bad("ADAPTER_REGISTRY_UNREADABLE: %s" % type(exc).__name__)
        return
    errs, summary = A.validate_registry(reg)
    if errs:
        for e in errs:
            r.bad("REGISTRY_CONTRACT_VIOLATION: %s" % e)
    else:
        r.ok("registry contract-valid: %d adapters %s"
             % (summary["adapters"], summary["ids"]))
    entries = {a.get("agent_id"): a for a in reg.get("adapters") or []}
    dirs = sorted(d for d in os.listdir(ADAPTERS)
                  if os.path.isdir(os.path.join(ADAPTERS, d)))
    for d in dirs:
        mirror = os.path.join(ADAPTERS, d, "adapter.json")
        if not os.path.isfile(mirror):
            r.bad("ADAPTER_DIR_WITHOUT_DECLARATION: %s" % d)
            continue
        try:
            with open(mirror) as fh:
                entry = json.load(fh)
        except ValueError as exc:
            r.bad("ADAPTER_DECLARATION_MALFORMED: %s (%s)" % (d, exc))
            continue
        if entry.get("agent_id") != d:
            r.bad("ADAPTER_ID_MISMATCH: dir %s declares %r"
                  % (d, entry.get("agent_id")))
        extra = sorted(set(entry) - ALLOWED_KEYS)
        if extra:
            r.bad("ADAPTER_DECLARATION_UNKNOWN_FIELDS: %s -> %s" % (d, extra))
        aerrs = A.validate_adapter(entry)
        if aerrs:
            r.bad("ADAPTER_DECLARATION_INVALID: %s -> %s"
                  % (d, "; ".join(aerrs)))
        if entries.get(d) != entry:
            r.bad("ADAPTER_MIRROR_DRIFT: %s differs from its registry entry" % d)
        else:
            r.ok("mirrored declaration matches registry: %s" % d)
    undeclared = sorted(set(entries) - set(dirs))
    if undeclared:
        r.bad("REGISTRY_ENTRY_WITHOUT_ADAPTER_DIR: %s" % undeclared)
    gen = entries.get(PT.FALLBACK_ADAPTER_ID) or {}
    if gen.get("maturity") == "DECLARED" and PT.FALLBACK_ADAPTER_ID in dirs:
        r.ok("generic fallback intact (DECLARED) and mirrored")
    else:
        r.bad("GENERIC_FALLBACK_CHANGED_OR_MISSING")
    real = sorted(a.get("agent_id") for a in entries.values()
                  if a.get("maturity") in PT.REAL_MATURITIES)
    # D-P3-A authorises EXACTLY two real adapters and names them; the DECLARED
    # generic fallback is never counted. An empty registry remains valid under
    # D-P3-D, so this invariant applies to every non-empty registry.
    if not entries:
        r.ok("zero-adapter registry accepted as valid (D-P3-D)")
    elif len(real) != len(PT.AUTHORISED_REAL_ADAPTERS):
        r.bad("ADAPTER_COUNT_VIOLATION: D-P3-A authorises exactly %d real "
              "adapters, found %d (%s)"
              % (len(PT.AUTHORISED_REAL_ADAPTERS), len(real),
                 ", ".join(real) or "none"))
    elif set(real) != set(PT.AUTHORISED_REAL_ADAPTERS):
        r.bad("ADAPTER_IDENTITY_VIOLATION: D-P3-A authorises %s, found %s"
              % (", ".join(PT.AUTHORISED_REAL_ADAPTERS), ", ".join(real)))
    else:
        r.ok("exactly the two authorised real adapters (D-P3-A): %s" % real)
    # The enforced bound is a single constant (portability.py); it must still
    # match what the recorded User decision names, so the constant cannot drift
    # away from ROADMAP-P3-DECISIONS.json without failing here.
    named, bound_errors = PT.decision_bound(REPO, registry=reg)
    if bound_errors:
        for e in bound_errors:
            r.bad(e)
    else:
        r.ok("enforced adapter bound matches the recorded %s decision: %s"
             % (PT.BOUND_DECISION_ID, ", ".join(named)))


def s2(r):
    r.sect("2. Core stays agent-neutral outside adapters/ (criterion 4)")
    hits = vendor_hits(os.path.join(SPS2, "core"))
    if hits:
        for h in hits:
            r.bad(h)
    else:
        r.ok("no core file outside adapters/ names a vendor")
    offs = A.core_is_adapter_free()
    if offs:
        r.bad("CORE_IMPORTS_ADAPTER: %s" % offs)
    else:
        r.ok("no core module imports an adapter")
    probe = os.path.join(SPS2, "core", "_portability_probe_tmp.json")
    with open(probe, "w") as fh:
        fh.write('{"note": "cline"}\n')
    try:
        caught = any("_portability_probe_tmp" in h
                     for h in vendor_hits(os.path.join(SPS2, "core")))
        if caught:
            r.control("C1 planted vendor name outside adapters/ is detected")
        else:
            r.bad("C1 detection MISSED a planted vendor name")
    finally:
        os.unlink(probe)
    errs, _s = A.validate_registry({"adapters": "not-a-list"})
    if errs:
        r.control("C2 malformed registry shape is rejected")
    else:
        r.bad("C2 malformed registry shape accepted")
    tmp = tempfile.mkdtemp(prefix="sps2-portability-")
    try:
        with open(os.path.join(tmp, "mod.py"), "w") as fh:
            fh.write("from adapters.example import thing\n")
        if A.core_is_adapter_free(tmp):
            r.control("C3 core module importing an adapter is detected")
        else:
            r.bad("C3 adapter import MISSED")
    finally:
        shutil.rmtree(tmp)


def s3(r):
    r.sect("3. Zero-adapter portability on an isolated copy, and its restore "
           "(criteria 1 and 2)")
    before = PT.surface_digest(REPO)
    report = PT.rehearse(REPO)
    plan = report["plan"]
    r.ok("isolated copy prepared: deleted %s; registry emptied to []"
         % (", ".join(plan["dirs"]) or "nothing"))
    if report["zero_state_errors"]:
        for e in report["zero_state_errors"]:
            r.bad("copy: %s" % e)
    else:
        r.ok("copy: empty adapter registry [] accepted as valid; core-owned "
             "contract and registry remain")
    for res in report["validators"]:
        if res["ok"]:
            r.ok("copy: %s green with zero adapters" % res["label"])
        else:
            r.bad("copy: %s not green with zero adapters (rc=%s)"
                  % (res["label"], res["rc"]))
    if report["restore_errors"]:
        for e in report["restore_errors"]:
            r.bad("copy: restore: %s" % e)
    else:
        r.ok("copy: adapter surface restored byte-identically and the "
             "delivered state re-validated (rollback is reversible)")
    if PT.surface_digest(REPO) != before:
        r.bad("WORKING_TREE_MODIFIED: adapter surface changed by the exercise")
    else:
        r.ok("working adapter surface untouched (sha256 unchanged)")


def s4(r):
    r.sect("4. Fresh-agent resume checklist executed mechanically "
           "(criterion 3, D-P3-E)")
    if not os.path.isfile(RESUME):
        r.bad("RESUME_CHECKLIST_MISSING: sps2/RESUME.md")
        return
    with open(RESUME, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    sources = resume_sources(text)
    missing = [s for s in sources
               if not os.path.exists(os.path.join(REPO, s))]
    if not sources:
        r.bad("RESUME_CHECKLIST_WITHOUT_SOURCES")
    elif missing:
        r.bad("RESUME_SOURCE_MISSING: %s" % missing)
    else:
        r.ok("all %d resume sources resolve" % len(sources))
    absent_answers = [p for p in RESUME_ANSWERS if p not in text]
    if absent_answers:
        r.bad("RESUME_ANSWER_MISSING: %s" % absent_answers)
    else:
        r.ok("resume checklist answers all %d required questions"
             % len(RESUME_ANSWERS))
    with open(P3_DECISIONS) as fh:
        dec = json.load(fh)
    ids = {d.get("decision_id"): d for d in dec.get("decisions") or []}
    absent = [i for i in ["D-P3-%s" % c for c in "ABCDEFG"] if i not in ids]
    if absent:
        r.bad("P3_DECISION_MISSING: %s" % absent)
    else:
        r.ok("roadmap P3 decisions D-P3-A..G recorded")
    badattr = [i for i, d in sorted(ids.items())
               if not G.approval_is_user_attributable(d.get("approval") or {})]
    if badattr:
        r.bad("P3_DECISION_NOT_USER_ATTRIBUTABLE: %s" % badattr)
    else:
        r.ok("every roadmap P3 decision is User-attributed and dated")
    comp = dec.get("completion") or {}
    if comp.get("state") in ("PENDING_USER_APPROVAL", "APPROVED"):
        r.ok("roadmap P3 completion state: %s" % comp.get("state"))
    else:
        r.bad("P3_COMPLETION_STATE_INVALID: %r" % (comp.get("state"),))
    # The checklist's machine-readable completion state must equal the recorded
    # one, so the resume state cannot go stale behind the decisions record.
    stated = [ln.split("COMPLETION:", 1)[1].strip()
              for ln in text.splitlines() if ln.startswith("COMPLETION:")]
    if comp.get("state") in stated:
        r.ok("resume checklist states the recorded completion state (%s)"
             % comp.get("state"))
    else:
        r.bad("RESUME_COMPLETION_STATE_DRIFT: checklist %s, record %r"
              % (stated or "nothing", comp.get("state")))
    # The checklist's adapter inventory must equal the live registry, so a
    # fresh agent is never told about adapters that do not (or no longer) exist.
    rows = resume_inventory(text)
    try:
        entries = A.load_registry().get("adapters") or []
    except (OSError, ValueError) as exc:
        entries = []
        r.bad("ADAPTER_REGISTRY_UNREADABLE: %s" % type(exc).__name__)
    drift = inventory_drift(rows, entries)
    if not rows:
        r.bad("RESUME_ADAPTER_INVENTORY_MISSING")
    elif drift:
        for d in drift:
            r.bad("RESUME_ADAPTER_INVENTORY_DRIFT: %s" % d)
    else:
        r.ok("resume adapter inventory matches the registry: %s"
             % ", ".join("%s=%s" % kv for kv in sorted(rows.items())))
    with open(P7_DECISIONS) as fh:
        p7ids = {d.get("decision_id")
                 for d in (json.load(fh).get("decisions") or [])}
    if {"D-P7-A", "D-P7-B", "D-P7-C", "D-P7-D"} <= p7ids:
        r.ok("P7 readiness decisions D-P7-A..D still present")
    else:
        r.bad("P7_DECISION_MISSING")
    with open(RECON) as fh:
        recon = json.load(fh)
    if any(m.get("roadmap_phase") == "P3"
           for m in recon.get("mapping") or []):
        r.ok("reconciliation record maps roadmap P3")
    else:
        r.bad("RECONCILIATION_P3_MISSING")
    try:
        with open(EVIDENCE) as fh:
            ev = json.load(fh)
        ev_ids = [x.get("evidence_id") for x in ev.get("records") or []]
    except (OSError, ValueError) as exc:
        ev_ids = []
        r.bad("P3_EVIDENCE_UNREADABLE: %s" % type(exc).__name__)
    if ev_ids and all(str(i).startswith("EV-RP3-") for i in ev_ids):
        r.ok("roadmap P3 evidence records present: %s" % ", ".join(ev_ids))
    elif ev_ids:
        r.bad("P3_EVIDENCE_MISLABELLED: %s" % ev_ids)
    # C4 exercises the SAME existence predicate the assertion above uses, with
    # exactly one deliberately-missing source injected. A hardcoded absent path
    # alone would make this control vacuously true (it can never be present), so
    # the injected list must resolve to exactly the injected entry: the control
    # fails if the predicate misses the missing source OR flags a real one.
    injected = list(sources) + ["sps2/no/such/resume-source.md"]
    detected = [s for s in injected
                if not os.path.exists(os.path.join(REPO, s))]
    if detected == ["sps2/no/such/resume-source.md"]:
        r.control("C4 a missing resume source is detected")
    else:
        r.bad("C4 missing resume source MISSED (detected=%r)" % detected)
    # C5 exercises the SAME drift predicate the inventory assertion uses, with
    # exactly one injected registry change. Without the injection the predicate
    # must report nothing, and with it exactly that one adapter; otherwise the
    # control would be vacuous in either direction.
    injected_registry = copy.deepcopy(entries)
    target = next((a for a in injected_registry
                   if a.get("agent_id") != PT.FALLBACK_ADAPTER_ID), None)
    if target is None:
        r.bad("C5 no real adapter available to inject a maturity drift")
    else:
        original = target.get("maturity")
        target["maturity"] = "VERIFIED"
        detected_drift = inventory_drift(rows, injected_registry)
        if inventory_drift(rows, entries) or \
                not any(d.startswith(target["agent_id"] + ":")
                        for d in detected_drift):
            r.bad("C5 maturity drift MISSED or falsely reported (detected=%r)"
                  % detected_drift)
        else:
            r.control("C5 an injected adapter maturity drift is detected "
                      "(%s %s -> VERIFIED)" % (target["agent_id"], original))


def main():
    r = Res()
    print("%sSPS 2.0 Roadmap P3 Portability Conformance Test%s" % (BOLD, NC))
    print("D-P3-D delete-all exercise; D-P3-E mechanical resume")
    if not os.path.isfile(REGISTRY):
        print("  %sFAIL%s  adapter registry missing; cannot run" % (RED, NC))
        return 2
    for fn in (s1, s2, s3, s4):
        fn(r)
    print("")
    if r.failed == 0:
        print("%s%s== PORTABILITY CONFORMANCE VALID: %d checks passed, "
              "0 failed, %d controls enforced ==%s"
              % (GREEN, BOLD, r.passed, r.controls, NC))
        return 0
    print("%s%s== PORTABILITY CONFORMANCE INVALID: %d passed, %d failed, "
          "%d controls ==%s" % (RED, BOLD, r.passed, r.failed, r.controls, NC))
    return 1


if __name__ == "__main__":
    sys.exit(main())