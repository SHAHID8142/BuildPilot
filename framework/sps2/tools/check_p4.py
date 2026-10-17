#!/usr/bin/env python3
"""SPS 2.0 P4 gate checker. Runs the hardened gate on a single capability.

Usage: check_p4.py <capability.json> [--promote]
Prints GATE_RESULTS then PROMOTED or NOT_PROMOTED with blocking gates.
Never prints a secret: values are never echoed, only gate reasons.
"""
import importlib.util
import json
import os
import sys

CAP = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "capability")
spec = importlib.util.spec_from_file_location(
    "pg", os.path.join(CAP, "promotion_gates.py"))
pg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pg)


def main():
    if len(sys.argv) < 2:
        print("usage: check_p4.py <capability.json>")
        return 2
    try:
        cap = json.load(open(sys.argv[1]))
    except Exception as ex:
        print("GATE_ERROR\tnot valid JSON: %s" % ex)
        return 0
    results, blocking = pg.evaluate(cap)
    print("GATE_RESULTS")
    for k in sorted(results):
        print("  %s %-14s %s" % (k, results[k]["gate"],
                                   "PASS" if results[k]["pass"] else "FAIL"))
    if "--promote" in sys.argv:
        if blocking:
            print("NOT_PROMOTED\tblocking=%s" % ",".join(blocking))
        else:
            print("PROMOTED")
    else:
        print("BLOCKING\t%s" % (",".join(blocking) if blocking else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())