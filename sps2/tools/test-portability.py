#!/usr/bin/env python3
"""SPS 2.0 Roadmap P3 portability conformance test (D-P3-D, D-P3-E).

Agent-neutral. Standard library only. Project-local: no installs, no network,
no machine-global writes. The delete-all exercise of section 3 runs on an
ISOLATED COPY of the repository in a temp directory, so the working tree is
never modified; the adapter surface is hash-compared before and after.

Sections:
  1. Adapter surface is contract-conformant and mirrored (D-P3-A..C)
  2. Core stays agent-neutral outside adapters/ (verification criterion 4)
  3. Zero-adapter portability on an isolated copy (criteria 1 and 2)
  4. Fresh-agent resume checklist executed mechanically (criterion 3)

Scope note: the zero-adapter exercise runs every sps2-scoped suite (phase
validators, unit tests, mutation suites, secret safety, emoji scan).
.sps/ governance and the history-credential check do not read the adapter
surface and are run as part of the normal-state suite instead.

Exit: 0 valid | 1 failure | 2 tooling unavailable.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SPS2 = os.path.dirname(HERE)
REPO = os.path.dirname(SPS2)
sys.path.insert(0, os.path.join(SPS2, "core"))
sys.path.insert(0, os.path.join(SPS2, "governance"))

import adapter_registry as A        # noqa: E402
import attribution as G             # noqa: E402

ADAPTERS = os.path.join(SPS2, "core", "adapters")
REGISTRY = os.path.join(ADAPTERS, "registry.json")
CONTRACT = os.path.join(ADAPTERS, "contract.schema.json")
ADAPTER_README = os.path.join(ADAPTERS, "README.md")
RESUME = os.path.join(SPS2, "RESUME.md")
P3_DECISIONS = os.path.join(SPS2, "decisions", "ROADMAP-P3-DECISIONS.json")
P7_DECISIONS = os.path.join(SPS2, "decisions", "P7-READINESS-DECISIONS.json")
RECON = os.path.join(SPS2, "decisions", "ROADMAP-EXECUTION-RECONCILIATION.json")
EVIDENCE = os.path.join(SPS2, "evidence", "ROADMAP-P3-EVIDENCE.json")

# Core-owned boundary files: never "an adapter" and must survive the delete-all
# exercise (D-P3-D).
CORE_OWNED = ("README.md", "contract.schema.json", "registry.json")

# The same vendor list the existing neutrality guards use.
VENDORS = ("cline", "claude", "codex", "cursor", "copilot", "windsurf",
           "aider", "gemini", "opencode", "gpt")

# Contract schema property names; mirrors "additionalProperties": false.
ALLOWED_KEYS = {"agent_id", "display_name", "maturity", "writes_global_state",
                "detection", "capabilities", "supports", "fallbacks",
                "maintainer", "verified_by"}

# Suites that must stay green with every adapter deleted.
ZERO_ADAPTER_SUITES = (
    ("sps2 foundation", ["bash", "sps2/tools/validate-sps2.sh"],
     "SPS2 FOUNDATION VALID"),
    ("P2 research", ["bash", "sps2/tools/validate-p2.sh"],
     "P2 RESEARCH VALID"),
    ("P3 production", ["bash", "sps2/tools/validate-p3.sh"],
     "P3 PRODUCTION VALID"),
    ("P4 promotion", ["bash", "sps2/tools/validate-p4.sh"],
     "P4 PROMOTION VALID"),
    ("P5 implementation", ["python3", "sps2/tools/validate-p5.py"],
     "P5 IMPLEMENTATION VALID"),
    ("P6 research", ["python3", "sps2/tools/validate-p6.py"],
     "P6 RESEARCH VALID"),
    ("P7 readiness", ["python3", "sps2/tools/validate-p7-readiness.py"],
     "P7 READINESS RECORDED"),
    ("P5 unit tests", ["python3", "sps2/tests/test_p5.py"], "OK"),
    ("snapshot mutations", ["bash", "sps2/tools/test-snapshot-integrity.sh"],
     "SNAPSHOT MUTATION SUITE"),
    ("phase boundary mutations", ["bash", "sps2/tools/test-phase-boundary.sh"],
     "PHASE BOUNDARY MUTATION SUITE"),
    ("P7 readiness mutations", ["bash",
                                "sps2/tools/test-p7-readiness-mutation.sh"],
     "P7 READINESS MUTATION SUITE"),
    ("secret safety", ["bash", "sps2/security/test-secret-safety.sh"],
     "SECRET-SAFETY TEST PASSED"),
    ("no-emoji", ["python3", "sps2/tools/check_emoji.py", "sps2"],
     "violations=0"),
)

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


def dir_hash(path):
    """Content hash of a directory tree, order-independent."""
    h = hashlib.sha256()
    for r, dirs, files in os.walk(path):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(r, f)
            h.update(os.path.relpath(p, path).encode())
            with open(p, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def s1(r):
    r.sect("1. Adapter surface is contract-conformant and mirrored")
    for p, label in ((CONTRACT, "contract.schema.json"),
                     (REGISTRY, "registry.json"),
                     (ADAPTER_README, "README.md")):
        if os.path.isfile(p):
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
    gen = entries.get("generic") or {}
    if gen.get("maturity") == "DECLARED" and "generic" in dirs:
        r.ok("generic fallback intact (DECLARED) and mirrored")
    else:
        r.bad("GENERIC_FALLBACK_CHANGED_OR_MISSING")
    real = sorted(a.get("agent_id") for a in entries.values()
                  if a.get("maturity") in ("EXPERIMENTAL", "VERIFIED"))
    if len(real) >= 2:
        r.ok("at least two adapters beyond DECLARED (D-P3-A/B): %s" % real)
    else:
        r.bad("REAL_ADAPTERS_INSUFFICIENT: %s" % real)


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
    r.sect("3. Zero-adapter portability on an isolated copy "
           "(criteria 1 and 2)")
    before = dir_hash(ADAPTERS)
    tmp = tempfile.mkdtemp(prefix="sps2-portability-copy-")
    tree = os.path.join(tmp, "tree")
    try:
        shutil.copytree(REPO, tree,
                        ignore=shutil.ignore_patterns(".kilo", "__pycache__"))
        adir = os.path.join(tree, "sps2", "core", "adapters")
        removed = []
        for name in sorted(os.listdir(adir)):
            p = os.path.join(adir, name)
            if os.path.isdir(p):
                shutil.rmtree(p)
                removed.append(name)
            elif name not in CORE_OWNED:
                os.unlink(p)
                removed.append(name)
        regp = os.path.join(adir, "registry.json")
        with open(regp) as fh:
            reg = json.load(fh)
        reg["adapters"] = []
        reg["note"] = ("Zero-adapter portability state: every adapter "
                       "directory and entry is deleted; the core-owned "
                       "contract and registry remain (D-P3-D).")
        with open(regp, "w") as fh:
            json.dump(reg, fh, indent=2)
        r.ok("isolated copy prepared: deleted %s; registry emptied to []"
             % (", ".join(removed) or "nothing"))
        code = (
            "import sys\n"
            "sys.path.insert(0, %r)\n"
            "import adapter_registry as A\n"
            "errs, summary = A.validate_registry()\n"
            "print('EMPTY_REGISTRY_OK' if errs == [] and "
            "summary['adapters'] == 0 else 'EMPTY_REGISTRY_ERR')\n"
            "print('CORE_ADAPTER_FREE' if A.core_is_adapter_free() == [] "
            "else 'CORE_DEPENDS_ON_ADAPTER')\n"
            % os.path.join(tree, "sps2", "core"))
        res = subprocess.run(["python3", "-c", code], cwd=tree,
                             capture_output=True, text=True)
        if "EMPTY_REGISTRY_OK" in res.stdout:
            r.ok("copy: empty adapter registry [] accepted as valid")
        else:
            r.bad("copy: empty adapter registry rejected")
        if "CORE_ADAPTER_FREE" in res.stdout:
            r.ok("copy: core remains adapter-free with zero adapters")
        else:
            r.bad("copy: core depends on an adapter when none exist")
        for label, cmd, marker in ZERO_ADAPTER_SUITES:
            out = subprocess.run(cmd, cwd=tree, capture_output=True,
                                 text=True, timeout=900)
            blob = (out.stdout or "") + (out.stderr or "")
            good = (out.returncode == 0) and (marker in blob) \
                and ("MISSED" not in blob)
            if good:
                r.ok("copy: %s green with zero adapters" % label)
            else:
                r.bad("copy: %s not green with zero adapters (rc=%d)"
                      % (label, out.returncode))
        if before != dir_hash(ADAPTERS):
            r.bad("WORKING_TREE_MODIFIED: adapter surface changed by the "
                  "exercise")
        else:
            r.ok("working adapter surface untouched (sha256 unchanged)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def s4(r):
    r.sect("4. Fresh-agent resume checklist executed mechanically "
           "(criterion 3, D-P3-E)")
    if not os.path.isfile(RESUME):
        r.bad("RESUME_CHECKLIST_MISSING: sps2/RESUME.md")
        return
    with open(RESUME, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    sources = [ln.split("SOURCE:", 1)[1].strip()
               for ln in text.splitlines() if ln.startswith("SOURCE:")]
    missing = [s for s in sources
               if not os.path.exists(os.path.join(REPO, s))]
    if not sources:
        r.bad("RESUME_CHECKLIST_WITHOUT_SOURCES")
    elif missing:
        r.bad("RESUME_SOURCE_MISSING: %s" % missing)
    else:
        r.ok("all %d resume sources resolve" % len(sources))
    for phrase in ("Current phase", "Current task", "Next allowed action",
                   "Forbidden actions"):
        if phrase in text:
            r.ok("resume checklist answers %r" % phrase)
        else:
            r.bad("RESUME_ANSWER_MISSING: %r" % phrase)
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
