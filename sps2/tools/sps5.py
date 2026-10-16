#!/usr/bin/env python3
"""SPS 2.0 P5 implementation/integration CLI.

Agent-neutral entry point. Standard library only. Project-local writes only:
it never touches a machine-global location and never installs anything.

Subcommands:
  select    Generate the project-local selection record and wire the
            selection link into the capability registry trace.
  verify    Re-check trace integrity, determinism and the adapter boundary.
  report    Print a machine-readable P5 integration summary.
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "sps2", "core"))
sys.path.insert(0, os.path.join(REPO, "sps2", "governance"))

import adapter_registry as A        # noqa: E402
import attribution as G             # noqa: E402
import registry_api as R            # noqa: E402
import selection as S              # noqa: E402

# The governance layer supplies the stricter approval predicate. The core stays
# agent-neutral and never learns what an agent name is.
APPROVER_OK = G.approval_is_user_attributable

PROJECT = os.path.join(REPO, "sps2", "project")
SELECTION_PATH = os.path.join(PROJECT, "SELECTION-P5-0001.json")

REQUIREMENT = {
    "id": "REQ-P5-SELECTION",
    "description": "Project-local selection among production-promoted "
                   "governance capabilities.",
    "required_capabilities": ["CAP-P03-001", "CAP-P03-002", "CAP-P03-003",
                              "CAP-P03-004"],
    "domains": ["governance"],
}


def _dump(obj, path):
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2)
        fh.write("\n")


def cmd_select(_args):
    """Generate the selection record and wire the selection trace link."""
    reg = R.load_registry()
    rec = S.selection_record("SELECTION-P5-0001", REQUIREMENT, reg,
                             note="P5 project-local selection over the four "
                                  "capabilities carrying explicit User "
                                  "production-promotion approval. CAP-P03-005 "
                                  "is excluded because it was never promoted.")
    _dump(rec, SELECTION_PATH)

    # Wire the selection link so the trace chain closes. This records that a
    # selection exists; it does not promote, install or activate anything.
    chosen = {r["capability_id"] for r in rec["ranking"]}
    for c in reg["capabilities"]:
        cid = c["capability_id"]
        if cid in chosen:
            c["selection"] = {
                "selection_id": rec["selection_id"],
                "project_local": True,
                "rank": next(r["rank"] for r in rec["ranking"]
                             if r["capability_id"] == cid),
                "ranking_fingerprint": rec["ranking_fingerprint"],
            }
        else:
            c["selection"] = {
                "selection_id": None,
                "project_local": True,
                "excluded_reason": next(
                    (e["exclusion_reason"]
                     for e in rec["excluded_from_selection"]
                     if e["capability_id"] == cid), "not promoted"),
            }
    _dump(reg, R.registry_path())

    print("selection written:", os.path.relpath(SELECTION_PATH, REPO))
    print("fingerprint:", rec["ranking_fingerprint"])
    for r in rec["ranking"]:
        print("  rank%d %-13s score=%s" % (r["rank"], r["capability_id"],
                                           r["score"]))
    for e in rec["excluded_from_selection"]:
        print("  excluded %-13s %s" % (e["capability_id"],
                                       e["exclusion_reason"]))
    return 0


def cmd_verify(_args):
    """Re-check trace integrity, determinism and the adapter boundary."""
    problems = []
    informational = []
    reg = R.load_registry()

    promoted_ids = {c["capability_id"] for c in R.promoted(reg)}
    for c in R.capabilities(reg):
        cid = c["capability_id"]
        _checks, missing = R.trace(c, APPROVER_OK)
        if missing:
            if cid in promoted_ids:
                # A promoted capability must be fully traceable.
                problems.append("TRACE_INCOMPLETE: %s missing %s"
                                % (cid, ",".join(missing)))
            else:
                # A deferred candidate is EXPECTED to have an incomplete
                # trace. That is the correct state, not a defect.
                informational.append("EXPECTED_INCOMPLETE_TRACE: %s missing %s"
                                     % (cid, ",".join(missing)))
        if R.claims_runtime(c):
            problems.append("RUNTIME_CLAIM_WITHOUT_TRANSITION: %s state=%s"
                            % (cid, c["lifecycle_state"]))

    # Determinism: repeated selection must produce the same fingerprint.
    f1 = S.fingerprint(S.select(REQUIREMENT, reg))
    f2 = S.fingerprint(S.select(REQUIREMENT, R.load_registry()))
    if f1 != f2:
        problems.append("NONDETERMINISTIC_SELECTION: %s != %s" % (f1, f2))

    errs, _summary = A.validate_registry()
    problems.extend(errs)
    for off in A.core_is_adapter_free():
        problems.append("CORE_DEPENDS_ON_ADAPTER: %s" % off)

    for p in problems:
        print("PROBLEM:", p)
    for i in informational:
        print("INFO:", i)
    print("determinism fingerprint:", f1, "stable" if f1 == f2 else "UNSTABLE")
    print("problem count:", len(problems))
    return 1 if problems else 0


def cmd_report(_args):
    reg = R.load_registry()
    out = {
        "schema": "sps2.p5-report/v1",
        "scope": "PROJECT_LOCAL",
        "agent_neutral": True,
        "counts": R.counts(reg),
        "promoted": [c["capability_id"] for c in R.promoted(reg)],
        "deferred": [
            {"capability_id": c["capability_id"],
             "lifecycle_state": c.get("lifecycle_state"),
             "recommendation": (c.get("promotion_assessment") or {})
             .get("recommendation"),
             "blocking_gates": (c.get("promotion_assessment") or {})
             .get("blocking_gates")}
            for c in R.deferred(reg)],
        "trace": {},
        "runtime_claims": [c["capability_id"] for c in R.capabilities(reg)
                           if R.claims_runtime(c)],
    }
    for c in R.capabilities(reg):
        checks, missing = R.trace(c, APPROVER_OK)
        out["trace"][c["capability_id"]] = {
            "complete": not missing, "missing": missing,
            "lifecycle_state": c.get("lifecycle_state"),
        }
    _errs, summary = A.validate_registry()
    out["adapters"] = summary
    print(json.dumps(out, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(prog="sps5", description=__doc__)
    sub = ap.add_subparsers(dest="cmd")
    for name, fn in (("select", cmd_select), ("verify", cmd_verify),
                     ("report", cmd_report)):
        p = sub.add_parser(name)
        p.set_defaults(fn=fn)
    args = ap.parse_args()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
