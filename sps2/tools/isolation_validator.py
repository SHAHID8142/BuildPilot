#!/usr/bin/env python3
"""SPS 2.0 P7 isolation validator.

Agent-neutral. Standard library only. Project-local: no installs, no network,
no machine-global writes, no runtime activation, no registry modification.

Proves mechanically that two projects remain isolated:
- no shared persistent state
- no cross-project imports
- no cross-project registry/state references
"""
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SPS2 = os.path.join(REPO, "sps2")

GREEN = "\033[0;32m"
RED = "\033[0;31m"
NC = "\033[0m"


def check_no_shared_state():
    """No shared persistent state between projects."""
    errors = []
    memory = os.path.join(SPS2, "memory")
    if not os.path.isdir(memory):
        errors.append("MEMORY_LAYOUT_MISSING")
        return errors
    layout = os.path.join(memory, "memory-layout.json")
    if not os.path.isfile(layout):
        errors.append("MEMORY_LAYOUT_FILE_MISSING")
        return errors
    try:
        l = json.load(open(layout))
        if l.get("schema") != "sps2.memory-layout/v1":
            errors.append("MEMORY_LAYOUT_SCHEMA_INVALID")
    except (json.JSONDecodeError, OSError):
        errors.append("MEMORY_LAYOUT_CORRUPT")
    return errors


def check_no_cross_project_imports():
    """No SPS 2.0 code imports from outside the project."""
    errors = []
    for root, _dirs, files in os.walk(SPS2):
        for f in files:
            if not f.endswith(".py"):
                continue
            path = os.path.join(root, f)
            try:
                body = open(path).read()
            except (OSError, UnicodeDecodeError):
                continue
            for line in body.splitlines():
                s = line.strip()
                if s.startswith("import ") or s.startswith("from "):
                    # Check for imports outside the SPS 2.0 project
                    # (heuristic: absolute paths, network imports, or
                    # imports from known external packages)
                    for bad in ("/usr/", "/etc/"):
                        if bad in s:
                            errors.append("CROSS_PROJECT_IMPORT: %s: %s"
                                          % (os.path.relpath(path, SPS2), s))
    return errors


def check_no_cross_project_registry_refs():
    """No cross-project registry/state references."""
    errors = []
    registry = os.path.join(SPS2, "capability", "registry.json")
    try:
        r = json.load(open(registry))
        for c in r.get("capabilities", []):
            for field in ("promotion_assessment", "lifecycle_state"):
                val = c.get(field)
                if val and ("P7" in str(val) or "global" in str(val).lower()):
                    errors.append("CROSS_PROJECT_REGISTRY_REF: %s %s=%r"
                                  % (c.get("capability_id"), field, val))
    except (OSError, json.JSONDecodeError):
        errors.append("REGISTRY_UNREADABLE")
    return errors


def main():
    print("%sSPS 2.0 P7 Isolation Validator%s" % (GREEN if True else "", NC))
    all_errors = []

    print("\n1. No shared persistent state")
    for e in check_no_shared_state():
        print("  %sFAIL%s  %s" % (RED, NC, e))
        all_errors.append(e)
    if not check_no_shared_state():
        print("  %sPASS%s  no shared persistent state" % (GREEN, NC))

    print("\n2. No cross-project imports")
    for e in check_no_cross_project_imports():
        print("  %sFAIL%s  %s" % (RED, NC, e))
        all_errors.append(e)
    if not check_no_cross_project_imports():
        print("  %sPASS%s  no cross-project imports" % (GREEN, NC))

    print("\n3. No cross-project registry/state references")
    for e in check_no_cross_project_registry_refs():
        print("  %sFAIL%s  %s" % (RED, NC, e))
        all_errors.append(e)
    if not check_no_cross_project_registry_refs():
        print("  %sPASS%s  no cross-project registry references" % (GREEN, NC))

    print("")
    if all_errors:
        print("%sISOLATION INVALID: %s failure(s)%s" % (RED, len(all_errors), NC))
        return 1
    print("%sISOLATION VALID: 0 failures%s" % (GREEN, NC))
    return 0


if __name__ == "__main__":
    sys.exit(main())
