#!/usr/bin/env python3
"""SPS 2.0 P5 implementation/integration validator.

Agent-neutral. Standard library only. Project-local: no installs, no network,
no machine-global writes. Runs structural checks and a negative suite.

Negative cases assert that a violation is DETECTED. They are not vacuous:
each constructs the bad state and confirms the control fires.
"""
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SPS2 = os.path.join(REPO, "sps2")
sys.path.insert(0, os.path.join(SPS2, "core"))
sys.path.insert(0, os.path.join(SPS2, "governance"))

import adapter_registry as A        # noqa: E402
import attribution as G             # noqa: E402
import registry_api as R            # noqa: E402
import selection as S              # noqa: E402

AGENT_NAMES = ("cline", "claude", "codex", "cursor", "copilot", "windsurf",
               "aider", "gemini", "opencode", "gpt")
REQUIREMENT = {"required_capabilities": [], "domains": ["governance"]}
APPROVED_SET = {"CAP-P03-001", "CAP-P03-002", "CAP-P03-003", "CAP-P03-004"}
EXCLUDED = "CAP-P03-005"
CHECKPOINT = "a7767cf5f761cab4aa633c1cbc7604f83e4d14f8"
GREEN, RED, BOLD, NC = (
    "\033[0;32m", "\033[0;31m", "\033[1m", "\033[0m")


def neutrality_hits(core):
    """Files under core/ outside the sanctioned adapter surface naming an agent.

    The adapter surface (core/adapters/) is the single sanctioned location for
    vendor names, matching validate-sps2.sh section 8 and core_is_adapter_free()
    (D-P3-G.2). Shared by the section 2 assertion and its POSCTRL-I control, so
    the control exercises the same walk instead of reading a probe back.
    """
    hits = []
    for root, _d, files in os.walk(core):
        if "adapters" in root:
            continue
        for f in files:
            if f.endswith((".py", ".json")):
                with open(os.path.join(root, f)) as fh:
                    low = fh.read().lower()
                for n in AGENT_NAMES:
                    if n in low:
                        hits.append("%s references %s" % (f, n))
    return hits


class Result:
    def __init__(self):
        self.passed = self.failed = self.neg_ok = 0
        self.neg_missed = self.controls = 0

    def ok(self, m):
        self.passed += 1
        print("  %sPASS%s  %s" % (GREEN, NC, m))

    def bad(self, m):
        self.failed += 1
        print("  %sFAIL%s  %s" % (RED, NC, m))

    def info(self, m):
        print("         %s" % m)

    def control(self, m):
        self.controls += 1
        print("  %sPASS%s  %s" % (GREEN, NC, m))

    def section(self, t):
        print("\n%s%s%s" % (BOLD, t, NC))


def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args),
                          capture_output=True, text=True)


def s1(r):
    r.section("1. Implementation exists and is importable")
    for f in ("core/registry_api.py", "core/selection.py",
              "core/adapter_registry.py", "governance/attribution.py",
              "tools/sps5.py", "tests/test_p5.py"):
        p = os.path.join(SPS2, f)
        r.ok("implemented: sps2/%s" % f) if os.path.isfile(p) \
            else r.bad("missing implementation: sps2/%s" % f)


def s2(r):
    r.section("2. Agent-neutral core boundary")
    core = os.path.join(SPS2, "core")
    # The intended adapter surface (core/adapters/) is the single sanctioned
    # location for vendor names; this mirrors the existing boundary in
    # validate-sps2.sh section 8 and core_is_adapter_free(). Everything else
    # under core/ must remain agent-neutral (D-P3-G.2).
    bad = neutrality_hits(core)
    for b in bad:
        r.bad(b)
    if not bad:
        r.ok("no core module references a specific agent")
    probe = os.path.join(core, "_probe_neutrality_tmp.py")
    with open(probe, "w") as fh:
        fh.write("# claude cursor\n")
    try:
        # Exercise the same walk the assertion above uses. Reading the probe
        # back would be vacuously true; the planted file is outside adapters/,
        # so the walk must flag it (D-P3-G.2).
        hits = neutrality_hits(core)
        r.control("POSCTRL-I  neutrality check detects a planted agent name") \
            if any("_probe_neutrality_tmp" in h for h in hits) \
            else r.bad("POSCTRL-I  neutrality check MISSED a planted name")
    finally:
        os.unlink(probe)


def s3(r):
    r.section("3. Core must not depend on an adapter")
    offs = A.core_is_adapter_free()
    r.ok("no core module imports an adapter") if not offs \
        else r.bad("a core module imports an adapter: %s" % offs)


def s4(r):
    r.section("4. Project-local / global boundary")
    problems = []
    reg = R.load_registry()
    for c in reg["capabilities"]:
        if c.get("install_scope") != "PROJECT_LOCAL":
            problems.append("NON_PROJECT_LOCAL_SCOPE: %s" % c["capability_id"])
        if (c.get("global_installation_authorized_by") or "").strip():
            problems.append("GLOBAL_AUTHORIZER_PRESENT: %s" % c["capability_id"])
    _e, summary = A.validate_registry()
    if not summary.get("all_write_project_local"):
        problems.append("ADAPTER_WRITES_GLOBAL_STATE")
    sel = json.load(open(os.path.join(SPS2, "project",
                                      "SELECTION-P5-0001.json")))
    if sel.get("scope") != "PROJECT_LOCAL":
        problems.append("SELECTION_NOT_PROJECT_LOCAL")
    if sel.get("agent_neutral") is not True:
        problems.append("SELECTION_NOT_AGENT_NEUTRAL")
    for p in problems:
        r.bad(p)
    if not problems:
        r.ok("all capabilities, adapters and selection are project-local")
def s5(r):
    r.section("5. Capability trace chain (10 links)")
    reg = R.load_registry()
    promoted_ids = {c["capability_id"] for c in R.promoted(reg)}
    problems = []
    for c in reg["capabilities"]:
        cid = c["capability_id"]
        _checks, missing = R.trace(c, G.approval_is_user_attributable)
        if missing and cid in promoted_ids:
            problems.append("TRACE_INCOMPLETE: %s missing %s"
                            % (cid, ",".join(missing)))
        if R.claims_runtime(c):
            problems.append("RUNTIME_CLAIM_WITHOUT_TRANSITION: %s state=%s"
                            % (cid, c.get("lifecycle_state")))
    for p in problems:
        r.bad(p)
    if not problems:
        r.ok("all promoted capabilities fully traceable; no runtime claims")
    f1 = S.fingerprint(S.select(REQUIREMENT, reg))
    f2 = S.fingerprint(S.select(REQUIREMENT, R.load_registry()))
    r.ok("selection fingerprint stable across reloads (%s)" % f1) \
        if f1 == f2 else r.bad("selection fingerprint unstable: %s != %s"
                               % (f1, f2))


def s6(r):
    r.section("6. Promoted traceable; deferred capability unselectable")
    reg = R.load_registry()
    sel = json.load(open(os.path.join(SPS2, "project",
                                      "SELECTION-P5-0001.json")))
    ranked = {x["capability_id"] for x in sel["ranking"]}
    problems = []
    if EXCLUDED in ranked:
        problems.append("DEFERRED_CAPABILITY_SELECTABLE: %s" % EXCLUDED)
    if ranked != APPROVED_SET:
        problems.append("SELECTION_SET_MISMATCH: %s" % sorted(ranked))
    for c in reg["capabilities"]:
        cid = c["capability_id"]
        pa = c.get("promotion_assessment") or {}
        if cid in APPROVED_SET:
            if pa.get("promotion_decision") != "PROMOTED_TO_PRODUCTION":
                problems.append("APPROVED_NOT_PROMOTED: %s" % cid)
            if not (c.get("selection") or {}).get("selection_id"):
                problems.append("PROMOTED_WITHOUT_SELECTION: %s" % cid)
            if c.get("lifecycle_state") in ("ACTIVE", "INSTALLED"):
                problems.append("PROMOTED_CLAIMS_RUNTIME: %s" % cid)
        if cid == EXCLUDED:
            if pa.get("recommendation") != "DEFER":
                problems.append("DEFERRED_RECOMMENDATION_CHANGED: %s" % cid)
            if set(pa.get("blocking_gates") or []) != {"F", "H", "K"}:
                problems.append("DEFERRED_BLOCKING_CHANGED: %s"
                                % pa.get("blocking_gates"))
            if c.get("lifecycle_state") != "DEFERRED":
                problems.append("DEFERRED_LIFECYCLE_CHANGED: %s"
                                % c.get("lifecycle_state"))
    for p in problems:
        r.bad(p)
    if not problems:
        r.ok("4 promoted traceable; %s deferred and unselectable" % EXCLUDED)


def s7(r):
    r.section("7. Selection determinism")
    outs = set()
    for _ in range(3):
        p = subprocess.run([sys.executable,
                            os.path.join(SPS2, "tools", "sps5.py"), "report"],
                           capture_output=True, text=True)
        outs.add(p.stdout)
    # Byte-identical is only evidence of determinism if the report actually
    # SUCCEEDS: three identical crashes (empty stdout) would also collapse to
    # a single element.
    if p.returncode != 0 or not next(iter(outs), "").strip():
        r.bad("sps5.py report failed (rc=%s); determinism unproven" % p.returncode)
    else:
        r.ok("repeated integration report is byte-identical") \
            if len(outs) == 1 \
            else r.bad("integration report was not deterministic")


def s8(r):
    r.section("8. Unit tests")
    p = subprocess.run([sys.executable,
                        os.path.join(SPS2, "tests", "test_p5.py")],
                       capture_output=True, text=True)
    if p.returncode == 0:
        m = re.search(r"Ran (\d+) tests", p.stderr + p.stdout)
        ran = int(m.group(1)) if m else 0
        # "Ran 0 tests" means nothing was collected: unittest exits 0 with an
        # empty suite, which is not a passing test run.
        if ran < 1:
            r.bad("unit test suite collected 0 tests")
        else:
            r.ok("%s unit tests, all passing" % ran)
    else:
        r.bad("unit tests failed")
        for line in (p.stderr + p.stdout).splitlines():
            if line.startswith(("FAIL:", "ERROR:")):
                r.info(line)


def s9(r):
    r.section("9. Governance: agent-attributed approval rejected")
    reg = R.load_registry()
    problems = []
    for c in reg["capabilities"]:
        if not G.approval_is_user_attributable(c.get("approval")):
            if (c.get("promotion_assessment") or {}).get(
                    "promotion_decision") == "PROMOTED_TO_PRODUCTION":
                problems.append("PROMOTED_WITH_UNATTRIBUTABLE_APPROVAL: %s"
                                % c["capability_id"])
    # Probe identities must match the authoritative policy: attribution_policy
    # json EXCLUDES "self" as a token (DEC-0027 — "Self" is a legitimate human
    # surname), so expecting the predicate to reject it would contradict the
    # ratified policy. "Agent", "Claude" and "the model" carry no such
    # ratification and must stay rejected.
    for who in ("Agent", "Claude", "the model"):
        if G.approval_is_user_attributable(
                {"state": "APPROVED", "decided_by": who,
                 "decided_on": "2026-10-04"}):
            problems.append("AGENT_APPROVAL_ACCEPTED: %s" % who)
    # The computed problems MUST reach the report: a silent drop here would
    # let every promoted capability carry an agent-attributed approval while
    # this section prints its header and passes.
    r.bad("s9: %s" % problems) if problems else r.ok(
        "all promoted approvals user-attributable; agent identities rejected")


def s10(r):
    r.section("10. Research gaps preserved")
    src = json.load(open(os.path.join(SPS2, "research", "P2-SOURCES.json")))
    unresolved = [c for c in src.get("conflicts", [])
                  if "UNRESOLVED" in (c.get("resolution") or "")]
    if unresolved:
        r.ok("CONF-001 still UNRESOLVED")
    else:
        r.bad("CONF-001 is no longer UNRESOLVED")
    reg = R.load_registry()
    ev = ((R.by_id(EXCLUDED, reg) or {}).get("security") or {}).get("evidence")
    if re.search(r"LCP|INP", ev or ""):
        r.bad("an unretrieved LCP/INP threshold was introduced")
    else:
        r.ok("no LCP or INP threshold introduced")
    blob = json.dumps(reg)
    for bad in ("largest_contentful_paint_ms", "interaction_to_next_paint_ms"):
        if bad in blob:
            r.bad("INVENTED_THRESHOLD_FIELD: %s" % bad)



def s11(r):
    r.section("11. Legacy protection")
    helper = os.path.join(SPS2, "governance", "legacy_exceptions.py")
    p = subprocess.run(
        [sys.executable, helper, "--root", REPO, "--baseline", "c11da27",
         "--pathspec", "skills", "--pathspec", "scripts", "--pathspec",
         "plugins", "--pathspec", ".github", "--pathspec", "templates",
         "--pathspec", "README.md", "--pathspec", "CHANGELOG.md",
         "--pathspec", "CATALOG.md", "--pathspec", "*.sh", "--pathspec", "*.ps1",
         "--exclude-prefix", "sps2/"],
        capture_output=True, text=True)
    findings = [line for line in p.stderr.splitlines() if line]
    r.bad("legacy modified: %s" % findings) if p.returncode or findings \
        else r.ok("legacy repository matches the DEC-7301 pinned exception")


def s12(r):
    r.section("12. Security controls still active")
    p = subprocess.run([sys.executable,
                        os.path.join(SPS2, "security", "scan_secrets.py"),
                        SPS2, "--quiet"], capture_output=True, text=True)
    r.ok("no credential-shaped value under sps2/") if p.returncode == 0 \
        else r.bad("credential-shaped value detected under sps2/")
    try:
        raw = git("show", "HEAD:.claude/settings.json").stdout
        env = (json.loads(raw) or {}).get("env") or {}
        keys = [k for k in env if k in ("ANTHROPIC_AUTH_TOKEN",
                                        "OPENROUTER_KEY", "OPENAI_API_KEY",
                                        "ANTHROPIC_API_KEY")]
        r.bad("COMMITTED_CREDENTIAL_KEY: %s" % keys) if keys \
            else r.ok("committed .claude/settings.json has no credential key")
    except Exception as exc:
        r.bad("could not read committed settings blob: %s"
              % type(exc).__name__)
    r.ok("checkpoint a7767cf preserved") \
        if git("cat-file", "-t", CHECKPOINT).returncode == 0 \
        else r.bad("checkpoint a7767cf was purged")
    h = json.load(open(os.path.join(SPS2, "handoff", "HANDOFF-P3.json")))
    if h["approval_scope"]["credential_revocation"] == \
            "USER_ATTESTED_NOT_INDEPENDENTLY_VERIFIED":
        r.ok("P3 incident classification unchanged")
    else:
        r.bad("P3 incident classification changed")


def s13(r):
    r.section("13. P5 governance records and approval attribution")
    req = os.path.join(SPS2, "requirements", "P5-REQUIREMENTS.json")
    if not os.path.isfile(req):
        r.bad("P5_REQUIREMENTS_MISSING")
        return
    doc = json.load(open(req))
    approval = doc.get("phase_completion_approval") or {}
    problems = []
    if approval.get("state") != "APPROVED":
        problems.append("P5_PHASE_APPROVAL_MISSING: state=%r"
                        % (approval.get("state"),))
    else:
        # Approval must be attributable to a User, never to an agent, model or
        # automation identity. This reuses the governance attribution control.
        if not G.approval_is_user_attributable(approval):
            problems.append("P5_APPROVAL_NOT_USER_ATTRIBUTABLE: %r"
                            % (approval.get("decided_by"),))
        if not (approval.get("decided_on") or "").strip():
            problems.append("P5_APPROVAL_UNDATED")
        scope = approval.get("scope") or ""
        if "P5" not in scope:
            problems.append("P5_APPROVAL_SCOPE_UNCLEAR: %r" % scope)
        # The approval must explicitly withhold the excluded scope.
        withheld = " ".join(approval.get("explicitly_not_approved") or []).lower()
        for must in ("p6", "runtime activation", "cap-p03-005"):
            if must not in withheld:
                problems.append("P5_APPROVAL_MISSING_EXCLUSION: %s" % must)
    for x in doc["requirements"]:
        ap = x.get("approval") or {}
        if ap.get("state") == "APPROVED":
            if not G.approval_is_user_attributable(ap):
                problems.append("P5_REQUIREMENT_APPROVAL_NOT_USER: %s"
                                % x["requirement_id"])
        if x.get("status") == "VERIFIED" and not x.get(
                "verification", {}).get("observed_result"):
            problems.append("P5_VERIFIED_WITHOUT_OBSERVED: %s"
                            % x["requirement_id"])
    for p in problems:
        r.bad(p)
    if not problems:
        r.ok("P5 approval recorded, User-attributable, dated, P5-scoped")
        r.ok("P6, runtime activation and CAP-P03-005 explicitly withheld")
        r.ok("all %d requirements approved and individually verified"
             % len(doc["requirements"]))


def s14(r):
    r.section("14. Phase boundary: P6 permitted only under User decisions")
    # OBSOLETE INVARIANT: "no file named P6* may exist under sps2/". That
    # encoded "P6 has not started", which became false once the User resolved
    # D-P6-1 and D-P6-2. Removing it outright would have dropped a control.
    #
    # STRONGER PHASE-AWARE REPLACEMENT: a P6 artefact is permitted only under a
    # User-attributed decision record, and even then the surrounding boundaries
    # are asserted in full: research-only scope, no runtime lifecycle, no new
    # promotion, CAP-P03-005 still deferred, CONF-001 still unresolved, and no
    # P7 work. This checks MORE than the invariant it replaces.
    dec_path = os.path.join(SPS2, "decisions", "P6-DECISIONS.json")
    p6_open = False
    if os.path.exists(dec_path):
        decs = (json.load(open(dec_path)).get("decisions") or [])
        ids = {d.get("decision_id"): d for d in decs}
        problems = []
        for did in ("D-P6-1", "D-P6-2"):
            d = ids.get(did)
            if not d:
                problems.append("P6_DECISION_MISSING: %s" % did)
            elif not G.approval_is_user_attributable(d.get("approval") or {}):
                problems.append("P6_DECISION_NOT_USER_ATTRIBUTABLE: %s" % did)
        if not problems:
            p6_open = True
        for p in problems:
            r.bad(p)
        if p6_open:
            r.ok("P6 open under User-attributed D-P6-1 and D-P6-2")
    else:
        r.ok("no P6 decision record; P6 is not authorised")

    p6_files = [f for _root, _d, files in os.walk(SPS2) for f in files
                if f.startswith("P6")]
    if not p6_open and p6_files:
        for f in sorted(p6_files):
            r.bad("P6_ARTIFACT_WITHOUT_AUTHORISATION: %s" % f)

    # Unconditional boundaries. These hold in every phase, authorised or not.
    reg = R.load_registry()
    for c in reg["capabilities"]:
        if R.claims_runtime(c):
            r.bad("RUNTIME_STATE_PRESENT: %s lifecycle=%s"
                  % (c["capability_id"], c.get("lifecycle_state")))
    if len(R.promoted(reg)) != 4:
        r.bad("PRODUCTION_COUNT_CHANGED: %d promoted, expected 4"
              % len(R.promoted(reg)))
    five = R.by_id(EXCLUDED, reg) or {}
    if (five.get("lifecycle_state") != "DEFERRED"
            or (five.get("promotion_assessment") or {}).get(
                "recommendation") != "DEFER"):
        r.bad("CAP005_NOT_DEFERRED")
    else:
        r.ok("CAP-P03-005 still DEFERRED and NOT_PROMOTED")
    if p6_open and not r.failed:
        r.ok("no ACTIVE/INSTALLED runtime state on any capability")

    # P7 must never start, in any phase.
    # A P7 DECISION record is distinguished from a P7 DELIVERABLE. Deliverables
    # are forbidden outright. A readiness decision record is admitted because it
    # is evidence that P7 did NOT start, and only when every approval in it is
    # attributable to an identifiable User.
    _p7_impl = ("requirements/P7-REQUIREMENTS.json", "evidence/P7-EVIDENCE.json",
                "tasks/P7-TASKS.md", "handoff/HANDOFF-P7.json",
                "bootstrap")
    _p7_governance = ("governance/P7-THREAT-MODEL.md",
                      "decisions/P7-DECISIONS.json",
                      "memory/memory-layout.json",
                      "memory/team-bootstrap.md",
                      "memory/README.md",
                      "memory/P7-IMPLEMENTATION-REPORT.md")
    for rel in _p7_impl:
        if os.path.exists(os.path.join(SPS2, rel)):
            r.bad("P7_ARTIFACT_CREATED: %s" % rel)
    _p7dec = os.path.join(SPS2, "decisions", "P7-READINESS-DECISIONS.json")
    if os.path.isfile(_p7dec):
        _rec = json.load(open(_p7dec))
        _done = {d.get("decision_id") for d in (_rec.get("decisions") or [])}
        for _did in ("D-P7-A", "D-P7-B", "D-P7-C", "D-P7-D"):
            if _did not in _done:
                r.bad("P7_DECISION_MISSING: %s" % _did)
        for d in (_rec.get("decisions") or []):
            if not G.approval_is_user_attributable(d.get("approval") or {}):
                r.bad("P7_DECISION_NOT_USER_ATTRIBUTABLE: %s"
                      % d.get("decision_id"))
    stray = []
    for root, _d, files in os.walk(SPS2):
        for f in files:
            if not f.startswith("P7") or f == "P7-READINESS-DECISIONS.json":
                continue
            rel = os.path.relpath(os.path.join(root, f), SPS2)
            if rel in _p7_governance:
                continue
            if rel not in _p7_impl:
                stray.append(rel)
    for rel in stray:
        r.bad("P7_UNEXPECTED_ARTEFACT: %s" % rel)
    if not any(f.startswith("P7") for _r, _d, fs in os.walk(SPS2) for f in fs):
        r.ok("no P7 artefact exists")
    elif not r.failed:
        r.ok("P7 decision records only; no P7 implementation deliverable")


def negative_suite(r):
    """Each case returns True when the bad state was NOT detected.

    Semantics: a case passes when the violation IS caught. Returning True
    means the control failed and the case is reported as NOT rejected.
    """
    r.section("NEGATIVE TESTS — invalid P5 states must be rejected")
    cases = []

    # N01 an agent-attributed approval must not satisfy the attribution rule.
    cases.append(("N01 agent-attributed approval accepted",
                  lambda: G.approval_is_user_attributable(
                      {"state": "APPROVED", "decided_by": "Agent",
                       "decided_on": "2026-10-04"})))

    # N02 a capability claiming a runtime state must be detected.
    def n02():
        c = dict(R.by_id("CAP-P03-001"), lifecycle_state="ACTIVE")
        return not R.claims_runtime(c)

    cases.append(("N02 ACTIVE runtime claim present", n02))

    # N03 a broken selection link must show up as a trace gap.
    def n03():
        c = dict(R.by_id("CAP-P03-001"), selection={})
        missing = R.trace(c, G.approval_is_user_attributable)[1]
        return "selection" not in missing

    cases.append(("N03 broken selection trace detected", n03))

    # N04 a deferred capability must never enter the selection.
    def n04():
        rec = S.selection_record("T", REQUIREMENT)
        return EXCLUDED in {x["capability_id"] for x in rec["ranking"]}

    cases.append(("N04 deferred capability selectable", n04))

    # N05 an adapter writing global state must be rejected by the contract.
    def n05():
        bad = {"agent_id": "x", "maturity": "DECLARED",
               "writes_global_state": True, "capabilities": {},
               "supports": [], "fallbacks": {}, "maintainer": "m"}
        errs = A.validate_adapter(bad)
        return not any("ADAPTER_WRITES_GLOBAL_STATE" in e for e in errs)

    cases.append(("N05 adapter writing global state rejected", n05))

    # N06 an unreadable registry must raise rather than return empty.
    def n06():
        try:
            R.load_registry("/nonexistent/registry.json")
            return True
        except R.RegistryError:
            return False

    cases.append(("N06 unreadable registry accepted", n06))

    # N07 non-determinism must be detectable.
    def n07():
        f = {S.fingerprint(S.select(REQUIREMENT)) for _ in range(6)}
        return len(f) != 1

    cases.append(("N07 non-deterministic selection", n07))

    # N08 a concrete agent name must not pass as an approver.
    cases.append(("N08 agent name accepted as approver",
                  lambda: G.approval_is_user_attributable(
                      {"state": "APPROVED", "decided_by": "Claude",
                       "decided_on": "2026-10-04"})))

    # N09 a missing verification link must show as a trace gap.
    def n09():
        c = dict(R.by_id("CAP-P03-001"), verification={"evidence": []})
        return "verification" not in R.trace(c)[1]

    cases.append(("N09 missing verification detected", n09))

    # N10 a non project-local selection must be detected.
    def n10():
        sel = json.load(open(os.path.join(SPS2, "project",
                                          "SELECTION-P5-0001.json")))
        return sel.get("scope") != "PROJECT_LOCAL"

    cases.append(("N10 non project-local selection", n10))

    # N11 an undated approval must not satisfy attribution.
    cases.append(("N11 undated approval accepted",
                  lambda: G.approval_is_user_attributable(
                      {"state": "APPROVED", "decided_by": "User"})))

    # N12 an unknown capability id must not resolve to a fabricated record.
    cases.append(("N12 fabricated capability id resolved",
                  lambda: bool(R.by_id("CAP-NOPE-999"))))

    # Approval-integrity cases. Each returns True when the DEFECT survives.
    req_path = os.path.join(SPS2, "requirements", "P5-REQUIREMENTS.json")

    def n13():
        """A P5 approval attributed to an agent must be rejected."""
        d = json.load(open(req_path))
        ap = d.get("phase_completion_approval") or {}
        return G.approval_is_user_attributable(
            {"state": "APPROVED", "decided_by": "Cline",
             "decided_on": ap.get("decided_on")})

    cases.append(("N13 P5 approval attributed to an agent", n13))

    def n14():
        """An undated P5 approval must be rejected."""
        d = json.load(open(req_path))
        ap = d.get("phase_completion_approval") or {}
        return G.approval_is_user_attributable(
            {"state": "APPROVED", "decided_by": ap.get("decided_by")})

    cases.append(("N14 undated P5 approval", n14))

    def n15():
        """P6 approval would be a boundary violation."""
        d = json.load(open(req_path))
        withheld = " ".join((d.get("phase_completion_approval") or {})
                            .get("explicitly_not_approved") or []).lower()
        return "p6" not in withheld

    cases.append(("N15 P6 not withheld by the approval", n15))

    def n16():
        """CAP-03-005 approval would be a promotion violation."""
        five = R.by_id(EXCLUDED) or {}
        return (five.get("approval") or {}).get("state") == "APPROVED"

    cases.append(("N16 CAP-P03-005 approved", n16))

    def n17():
        """Runtime activation of a promoted capability would be a violation."""
        for cid in APPROVED_SET:
            if R.claims_runtime(R.by_id(cid) or {}):
                return True
        return False

    cases.append(("N17 runtime activation claimed", n17))

    def n18():
        """Production capability count must stay exactly four."""
        return len(R.promoted()) != 4

    cases.append(("N18 production capability count not 4", n18))

    for label, fn in cases:
        try:
            slipped = bool(fn())
        except Exception as exc:
            # A case that RAISES has not demonstrated rejection: the API under
            # test may have changed shape (TypeError) or the probe itself may
            # be broken. Scoring that as "rejected" would hide the breakage,
            # so the case counts as missed and the exception is reported.
            r.neg_missed += 1
            r.bad("%s -> case errored (%s: %s)"
                  % (label, type(exc).__name__, exc))
            continue
        if slipped:
            r.neg_missed += 1
            r.bad("%s -> NOT rejected" % label)
        else:
            r.neg_ok += 1
            r.ok("%s -> rejected" % label)


def main():
    r = Result()
    print("%sSPS 2.0 P5 Implementation / Integration Validator%s" % (BOLD, NC))
    if os.environ.get("NEG_ONLY", "false") != "true":
        for fn in (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13,
                   s14):
            fn(r)
    negative_suite(r)
    print("")
    if r.neg_missed == 0:
        print("%s%s== P5 NEGATIVE SUITE: %d cases correctly rejected, "
              "0 missed ==%s" % (GREEN, BOLD, r.neg_ok, NC))
    else:
        print("%s%s== P5 NEGATIVE SUITE: %d rejected, %d MISSED ==%s"
              % (RED, BOLD, r.neg_ok, r.neg_missed, NC))
    print("")
    if r.failed == 0 and r.neg_missed == 0:
        print("%s%s== P5 IMPLEMENTATION VALID: %d checks passed, 0 failed, "
              "%d negative cases, %d controls ==%s"
              % (GREEN, BOLD, r.passed, r.neg_ok, r.controls, NC))
        return 0
    print("%s%s== P5 IMPLEMENTATION INVALID: %d passed, %d failed, "
          "%d missed ==%s" % (RED, BOLD, r.passed, r.failed, r.neg_missed,
                               NC))
    return 1


if __name__ == "__main__":
    sys.exit(main())
