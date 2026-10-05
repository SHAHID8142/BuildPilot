#!/usr/bin/env python3
"""SPS 2.0 Roadmap P3 portability operation (D-P3-D, D-P3-A).

One implementation of the delete-all / rollback operation, shared by its
consumers instead of being re-derived by each of them:

- `plan_delete_all` / `apply_delete_all` define what an adapter is for
  deletion purposes and perform the removal;
- `verify_zero_adapter_state` proves the resulting state is structurally valid
  with zero adapters, and `verify_delivered_state` proves the delivered state;
- `run_core_validators` holds the single list of core validators that must stay
  green across adapter removal;
- `rehearse` performs the whole cycle on an ISOLATED COPY: snapshot, delete
  all, verify the zero-adapter state, run every core validator, restore the
  snapshot, verify the delivered state again. The live working tree is never
  modified;
- `AUTHORISED_REAL_ADAPTERS` is the single definition site of the D-P3-A bound,
  and `decision_bound()` proves it still matches the recorded User decision, so
  the enforced set cannot silently drift from `ROADMAP-P3-DECISIONS.json`.

Agent-neutral. Standard library only. Project-local: no install, no network, no
machine-global write, no runtime activation, no capability promotion. It never
imports, executes or requires any agent; the adapter set is data, never
behaviour.

Usage:
    python3 sps2/tools/portability.py                  # rehearse (default; safe)
    python3 sps2/tools/portability.py --apply --root DIR --confirm
    python3 sps2/tools/portability.py --verify         # delivered-state check

Exit: 0 valid | 1 failure | 2 tooling unavailable.
"""
import argparse
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
if SPS2 not in sys.path:
    sys.path.insert(0, os.path.join(REPO, "sps2", "core"))

import adapter_registry as A        # noqa: E402

ADAPTERS_REL = os.path.join("sps2", "core", "adapters")
REGISTRY_NAME = "registry.json"
CONTRACT_NAME = "contract.schema.json"
SURFACE_README_NAME = "README.md"
DECLARATION_NAME = "adapter.json"

# D-P3-D: "Delete all adapters means deletion of all per-agent adapter
# entries/directories. The core-owned adapter contract and registry remain. An
# empty adapter registry [] is valid and must be accepted by the portability
# test." These three files are therefore never part of a deletion plan.
CORE_OWNED_FILES = (SURFACE_README_NAME, CONTRACT_NAME, REGISTRY_NAME)

# D-P3-A: "Implement real adapters for exactly two low-risk targets: Codex and
# OpenCode", bounded to "Two adapters only. Adding any further adapter requires
# a new decision." The DECLARED generic fallback is never a real adapter. This
# is the ONLY definition site of the bound: both enforcement points import it
# from here instead of repeating the pair, and `decision_bound()` checks it
# against the recorded decision.
AUTHORISED_REAL_ADAPTERS = ("codex", "opencode")
REAL_MATURITIES = ("EXPERIMENTAL", "VERIFIED")
FALLBACK_ADAPTER_ID = "generic"
BOUND_DECISION_ID = "D-P3-A"

P3_DECISIONS_REL = os.path.join("sps2", "decisions", "ROADMAP-P3-DECISIONS.json")

ZERO_ADAPTER_NOTE = ("Zero-adapter portability state: every adapter directory "
                     "and entry is deleted; the core-owned contract and "
                     "registry remain (D-P3-D).")

# Every sps2-scoped core validator, run in both the delivered and the
# zero-adapter state. check_sps2.py is not listed because it is a library
# invoked by validate-sps2.sh section 3, and the .sps governance suite and the
# history-credential check read no adapter state at all; both exclusions are
# documented in test-portability.py.
CORE_VALIDATORS = (
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
COPY_IGNORE = (".kilo", "__pycache__")


# ── surface access ──────────────────────────────────────────────────────────

def adapter_dir(root=None):
    return os.path.join(root or REPO, ADAPTERS_REL)


def registry_path(root=None):
    return os.path.join(adapter_dir(root), REGISTRY_NAME)


def load_registry(root=None):
    with open(registry_path(root)) as fh:
        return json.load(fh)


def adapter_dirs(root=None):
    """Per-agent adapter directories, i.e. everything that is not core-owned."""
    base = adapter_dir(root)
    if not os.path.isdir(base):
        return []
    return sorted(d for d in os.listdir(base)
                  if os.path.isdir(os.path.join(base, d)))


def registry_entries(root=None):
    return list(load_registry(root).get("adapters") or [])


def real_adapter_ids(root=None, entries=None):
    """Ids whose maturity is beyond DECLARED; the DECLARED fallback never is.

    Only string ids are returned, so a malformed entry (a real maturity with no
    `agent_id`) is skipped instead of crashing the count invariant that every
    enforcement point derives from here. Such an entry is still rejected by
    `adapter_registry.validate_adapter`, which reports the missing field.
    """
    source = entries if entries is not None else registry_entries(root)
    return sorted(a.get("agent_id") for a in source
                  if isinstance(a, dict)
                  and a.get("maturity") in REAL_MATURITIES
                  and isinstance(a.get("agent_id"), str) and a.get("agent_id"))


def surface_digest(root=None):
    """Content hash of the adapter surface, order-independent."""
    h = hashlib.sha256()
    base = adapter_dir(root)
    for r, dirs, files in os.walk(base):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(r, f)
            h.update(os.path.relpath(p, base).encode())
            with open(p, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


# ── the D-P3-A bound, derived from the recorded decision ────────────────────

def decision_record(root=None):
    return json.load(open(os.path.join(root or REPO, P3_DECISIONS_REL)))


def decision_by_id(decision_id, root=None):
    for d in decision_record(root).get("decisions") or []:
        if d.get("decision_id") == decision_id:
            return d or {}
    return {}


def decision_text(decision_id, root=None):
    """The full recorded text of one decision, lowercased for matching."""
    d = decision_by_id(decision_id, root)
    approval = d.get("approval") or {}
    return " ".join(str(x) for x in (
        d.get("title"), d.get("decision"), d.get("rationale"),
        d.get("bounded_scope"), approval.get("basis")) if x).lower()


def decision_named_adapters(candidates, decision_id=BOUND_DECISION_ID,
                            root=None):
    """Which of `candidates` the recorded decision text actually names.

    The decision is the authority for the adapter set; this is the only bridge
    from prose to the enforced constant, and it only ever *confirms* the
    constant. It can never widen it: a candidate missing from the decision text
    is not authorised by that text.
    """
    text = decision_text(decision_id, root)
    return sorted(c for c in candidates
                  if isinstance(c, str) and c and c.lower() in text)


def decision_bound(root=None, registry=None):
    """Return (named, errors) for the D-P3-A adapter bound.

    named: the real-adapter set the recorded decision authorises.
    errors: why the enforced constant and the decision disagree, if they do.
    """
    errors = []
    try:
        doc = decision_record(root)
    except (OSError, ValueError) as exc:
        return [], ["%s_RECORD_UNREADABLE: %s"
                    % (BOUND_DECISION_ID, type(exc).__name__)]
    if not any(d.get("decision_id") == BOUND_DECISION_ID
               for d in doc.get("decisions") or []):
        errors.append("%s_RECORD_MISSING" % BOUND_DECISION_ID)
        return [], errors
    doc_adapters = registry_entries(root) if registry is None else \
        list(registry.get("adapters") or []) \
        if isinstance(registry, dict) else list(registry)
    ids = [a.get("agent_id") for a in doc_adapters if isinstance(a, dict)]
    universe = sorted({i for i in list(ids) + list(AUTHORISED_REAL_ADAPTERS)
                       if isinstance(i, str)})
    named = decision_named_adapters(universe, root=root)
    if not named:
        errors.append("%s_NAMES_NO_ADAPTER: none of %s appears in the recorded "
                      "decision" % (BOUND_DECISION_ID, universe))
    elif set(named) != set(AUTHORISED_REAL_ADAPTERS):
        errors.append(
            "%s_BOUND_DRIFT: enforced set %s does not match the adapters the "
            "recorded decision names (%s); a new adapter set requires a new "
            "User decision"
            % (BOUND_DECISION_ID, ", ".join(AUTHORISED_REAL_ADAPTERS),
               ", ".join(named)))
    return named, errors


# ── deletion (D-P3-D) ───────────────────────────────────────────────────────

def plan_delete_all(root=None):
    """What 'delete all adapters' removes, and what it keeps."""
    base = adapter_dir(root)
    dirs = adapter_dirs(root)
    files = []
    for f in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        if os.path.isfile(os.path.join(base, f)) and f not in CORE_OWNED_FILES:
            files.append(f)
    return {
        "dirs": dirs,
        "files": files,
        "entries": [a.get("agent_id") for a in registry_entries(root)],
        "kept": list(CORE_OWNED_FILES),
    }


def apply_delete_all(root=None):
    """Perform the delete-all. DESTRUCTIVE: removes every adapter.

    Callers must either operate on an isolated copy (`rehearse`) or require an
    explicit operator confirmation (`--apply --confirm`). The core-owned
    contract and registry survive, and the registry becomes the already-proven
    valid `{"adapters": []}` state.
    """
    base = adapter_dir(root)
    plan = plan_delete_all(root)
    for d in plan["dirs"]:
        shutil.rmtree(os.path.join(base, d))
    for f in plan["files"]:
        os.unlink(os.path.join(base, f))
    regp = registry_path(root)
    with open(regp) as fh:
        reg = json.load(fh)
    dropped = [a.get("agent_id") for a in (reg.get("adapters") or [])]
    reg["adapters"] = []
    reg["note"] = ZERO_ADAPTER_NOTE
    with open(regp, "w") as fh:
        json.dump(reg, fh, indent=2)
    return {"dirs": plan["dirs"], "files": plan["files"], "entries": dropped,
            "kept": list(CORE_OWNED_FILES)}


def snapshot_surface(root=None, into=None):
    """Byte-for-byte copy of the adapter surface, for the restore leg."""
    dest = into or tempfile.mkdtemp(prefix="sps2-adapter-surface-")
    dest = os.path.join(dest, "adapters")
    shutil.copytree(adapter_dir(root), dest)
    return dest


def restore_surface(snapshot, root=None):
    """Put a snapshotted adapter surface back, exactly as it was."""
    base = adapter_dir(root)
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif name not in CORE_OWNED_FILES:
            os.unlink(p)
    for name in sorted(os.listdir(snapshot)):
        src = os.path.join(snapshot, name)
        dst = os.path.join(base, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    return surface_digest(root)


# ── state verification ──────────────────────────────────────────────────────

def verify_zero_adapter_state(root=None):
    """Errors proving the zero-adapter state is intact and structurally valid."""
    errors = []
    base = adapter_dir(root)
    for name in CORE_OWNED_FILES:
        if not os.path.isfile(os.path.join(base, name)):
            errors.append("CORE_OWNED_FILE_MISSING: %s" % name)
    left = adapter_dirs(root)
    if left:
        errors.append("ADAPTER_DIRECTORY_SURVIVED: %s" % ", ".join(left))
    try:
        reg = load_registry(root)
    except (OSError, ValueError) as exc:
        return errors + ["ADAPTER_REGISTRY_UNREADABLE: %s"
                         % type(exc).__name__]
    if reg.get("adapters") != []:
        errors.append("ADAPTER_REGISTRY_NOT_EMPTIED: %r"
                      % (reg.get("adapters"),))
    # Path-safe validation: the document is passed explicitly, so the live
    # registry is never read on behalf of a copy.
    errs, summary = A.validate_registry(reg)
    errors.extend(errs)
    if summary.get("adapters") != 0:
        errors.append("ADAPTER_REGISTRY_NOT_EMPTY: %d"
                      % summary.get("adapters", -1))
    if A.core_is_adapter_free(os.path.join(root or REPO, "sps2", "core")):
        errors.append("CORE_DEPENDS_ON_ADAPTER_IN_ZERO_ADAPTER_STATE")
    return errors


def verify_delivered_state(root=None):
    """Errors proving the delivered adapter surface is complete and bounded.

    Checks the contract-bound surface: every directory carries a declaration
    equal to its registry entry, the DECLARED fallback is intact, the D-P3-A
    bound holds for a non-empty registry, and the enforced bound still matches
    the recorded decision.
    """
    errors = []
    for name in CORE_OWNED_FILES:
        if not os.path.isfile(os.path.join(adapter_dir(root), name)):
            errors.append("CORE_OWNED_FILE_MISSING: %s" % name)
    try:
        reg = load_registry(root)
    except (OSError, ValueError) as exc:
        return ["ADAPTER_REGISTRY_UNREADABLE: %s" % type(exc).__name__]
    errs, _summary = A.validate_registry(reg)
    errors.extend(errs)
    entries = {a.get("agent_id"): a for a in (reg.get("adapters") or [])}
    for d in adapter_dirs(root):
        mirror = os.path.join(adapter_dir(root), d, DECLARATION_NAME)
        if not os.path.isfile(mirror):
            errors.append("ADAPTER_DIR_WITHOUT_DECLARATION: %s" % d)
            continue
        with open(mirror) as fh:
            entry = json.load(fh)
        if entry != entries.get(d):
            errors.append("ADAPTER_MIRROR_DRIFT: %s" % d)
    undeclared = sorted(set(entries) - set(adapter_dirs(root)))
    if undeclared:
        errors.append("REGISTRY_ENTRY_WITHOUT_ADAPTER_DIR: %s"
                      % ", ".join(undeclared))
    if (entries.get(FALLBACK_ADAPTER_ID) or {}).get("maturity") != "DECLARED":
        errors.append("GENERIC_FALLBACK_CHANGED_OR_MISSING")
    if entries:
        real = real_adapter_ids(root)
        if len(real) != len(AUTHORISED_REAL_ADAPTERS):
            errors.append(
                "ADAPTER_COUNT_VIOLATION: D-P3-A authorises exactly %d real "
                "adapters, found %d (%s)"
                % (len(AUTHORISED_REAL_ADAPTERS), len(real),
                   ", ".join(real) or "none"))
        elif set(real) != set(AUTHORISED_REAL_ADAPTERS):
            errors.append("ADAPTER_IDENTITY_VIOLATION: D-P3-A authorises %s, "
                          "found %s" % (", ".join(AUTHORISED_REAL_ADAPTERS),
                                        ", ".join(real)))
    _named, bound_errors = decision_bound(root, registry=reg)
    errors.extend(bound_errors)
    return errors


def run_core_validators(root, validators=CORE_VALIDATORS, timeout=900):
    """Run every core validator in `root`; return one result per validator."""
    results = []
    for label, cmd, marker in validators:
        try:
            out = subprocess.run(cmd, cwd=root, capture_output=True,
                                 text=True, timeout=timeout)
            blob = (out.stdout or "") + (out.stderr or "")
            ok = out.returncode == 0 and marker in blob and "MISSED" not in blob
            results.append({"label": label, "ok": ok, "rc": out.returncode})
        except (OSError, subprocess.SubprocessError) as exc:
            results.append({"label": label, "ok": False, "rc": -1,
                            "error": type(exc).__name__})
    return results


def copy_tree(root, dest):
    shutil.copytree(root, dest, ignore=shutil.ignore_patterns(*COPY_IGNORE))
    return dest


def rehearse(root=None, validators=CORE_VALIDATORS):
    """Full delete-all rehearsal on an isolated copy. Never touches `root`.

    Sequence: snapshot the surface, copy the tree, delete all adapters in the
    copy, prove the zero-adapter state, run every core validator there, restore
    the snapshot, prove the delivered state came back byte-identical.
    """
    root = root or REPO
    tmp = tempfile.mkdtemp(prefix="sps2-portability-rehearsal-")
    try:
        tree = copy_tree(root, os.path.join(tmp, "tree"))
        snapshot = snapshot_surface(tree, into=os.path.join(tmp, "snapshot"))
        before = surface_digest(tree)
        plan = apply_delete_all(tree)
        zero_errors = verify_zero_adapter_state(tree)
        results = run_core_validators(tree, validators)
        restore_surface(snapshot, tree)
        restored_digest = surface_digest(tree)
        restore_errors = verify_delivered_state(tree)
        if restored_digest != before:
            restore_errors.append("RESTORE_NOT_BYTE_IDENTICAL: %s != %s"
                                  % (restored_digest, before))
        return {
            "plan": plan,
            "zero_state_errors": zero_errors,
            "validators": results,
            "restore_errors": restore_errors,
            "surface_digest": before,
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ── CLI ─────────────────────────────────────────────────────────────────────

def _print_report(report):
    print("%sSPS 2.0 Roadmap P3 portability rehearsal (D-P3-D)%s" % (BOLD, NC))
    plan = report["plan"]
    print("delete-all plan: adapters %s; extra files %s; kept core-owned %s"
          % (", ".join(plan["dirs"]) or "none",
             ", ".join(plan["files"]) or "none", ", ".join(plan["kept"])))
    for e in report["zero_state_errors"]:
        print("  %sFAIL%s  %s" % (RED, NC, e))
    if not report["zero_state_errors"]:
        print("  %sPASS%s  zero-adapter state valid: contract and registry "
              "remain, registry is []" % (GREEN, NC))
    for res in report["validators"]:
        if res["ok"]:
            print("  %sPASS%s  zero-adapter state: %s green" % (GREEN, NC,
                                                                res["label"]))
        else:
            print("  %sFAIL%s  zero-adapter state: %s not green (rc=%s)"
                  % (RED, NC, res["label"], res["rc"]))
    for e in report["restore_errors"]:
        print("  %sFAIL%s  restore: %s" % (RED, NC, e))
    if not report["restore_errors"]:
        print("  %sPASS%s  restore: delivered adapter state recovered "
              "byte-identically and re-validated" % (GREEN, NC))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Roadmap P3 portability operation: rehearse, verify, or "
                    "apply the documented delete-all rollback.")
    ap.add_argument("--root", help="repository root (default: this repository)")
    ap.add_argument("--rehearse", action="store_true",
                    help="rehearse delete-all on an isolated copy (default)")
    ap.add_argument("--verify", action="store_true",
                    help="verify the delivered adapter state only")
    ap.add_argument("--apply", action="store_true",
                    help="DESTRUCTIVE: delete every adapter under --root")
    ap.add_argument("--confirm", action="store_true",
                    help="required with --apply; acknowledges that this removes "
                         "every adapter directory and empties the registry")
    args = ap.parse_args(argv)
    if not os.path.isdir(adapter_dir(args.root)):
        print("  %sFAIL%s  no adapter surface under %s"
              % (RED, NC, adapter_dir(args.root)))
        return 2

    if args.apply:
        if not args.root or not args.confirm:
            print("%s--apply refuses to run without --root and --confirm%s"
                  % (RED, NC))
            return 1
        print("%sdelete-all rollback on %s%s" % (BOLD, adapter_dir(args.root),
                                                 NC))
        plan = apply_delete_all(args.root)
        print("deleted adapters: %s; registry emptied to []; kept %s"
              % (", ".join(plan["dirs"]) or "none",
                 ", ".join(plan["kept"])))
        errors = verify_zero_adapter_state(args.root)
        for e in errors:
            print("  %sFAIL%s  %s" % (RED, NC, e))
        return 1 if errors else 0

    if args.verify:
        if not registry_entries(args.root):
            # The rollback result: the delivered adapter set is gone on purpose,
            # so the applicable invariant is the zero-adapter state.
            errors = verify_zero_adapter_state(args.root)
            for e in errors:
                print("  %sFAIL%s  %s" % (RED, NC, e))
            if errors:
                return 1
            print("  %sPASS%s  zero-adapter (rollback) state valid: contract "
                  "and registry remain, registry is []" % (GREEN, NC))
            return 0
        errors = verify_delivered_state(args.root)
        for e in errors:
            print("  %sFAIL%s  %s" % (RED, NC, e))
        if errors:
            return 1
        print("  %sPASS%s  delivered adapter state valid: %s (fallback %s)"
              % (GREEN, NC, ", ".join(real_adapter_ids(args.root)),
                 FALLBACK_ADAPTER_ID))
        return 0

    before = surface_digest(args.root)
    report = rehearse(args.root)
    _print_report(report)
    if surface_digest(args.root) != before:
        print("  %sFAIL%s  WORKING_TREE_MODIFIED: the rehearsal changed the "
              "live adapter surface" % (RED, NC))
        return 1
    print("  %sPASS%s  live adapter surface untouched by the rehearsal" %
          (GREEN, NC))
    failed = (report["zero_state_errors"] or report["restore_errors"]
              or [v for v in report["validators"] if not v["ok"]])
    if not failed:
        print("%s%s== PORTABILITY REHEARSAL VALID: %d core validators green "
              "with zero adapters, restore verified ==%s"
              % (GREEN, BOLD, len(report["validators"]), NC))
        return 0
    print("%s%s== PORTABILITY REHEARSAL INVALID ==%s" % (RED, BOLD, NC))
    return 1


if __name__ == "__main__":
    sys.exit(main())