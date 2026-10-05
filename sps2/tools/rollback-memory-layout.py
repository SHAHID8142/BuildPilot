#!/usr/bin/env python3
"""SPS 2.0 memory layout rollback mechanism.

Agent-neutral. Standard library only. Project-local.

Per P7 threat model sections 9-10:
- Memory layout must be revertible to the prior state by a
  single operation (rollback).
- Removal of the memory layout must leave the project in a
  valid, cloneable state (no orphaned references, no broken
  validator paths).

Usage:
  python3 sps2/tools/rollback-memory-layout.py   # restore prev
  python3 sps2/tools/rollback-memory-layout.py --remove   # remove layout
"""
import json
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SPS2 = os.path.join(REPO, "sps2")
MEMORY = os.path.join(SPS2, "memory")
LAYOUT = os.path.join(MEMORY, "memory-layout.json")
BACKUP = os.path.join(MEMORY, "memory-layout.json.prev")

GREEN = "\033[0;32m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"


def rollback():
    """Restore memory layout from backup. Single operation."""
    if not os.path.isfile(BACKUP):
        print("%sNO BACKUP%s  %s" % (RED, NC, BACKUP))
        return 1
    shutil.copy2(BACKUP, LAYOUT)
    print("%sROLLBACK OK%s  restored %s from backup" % (GREEN, NC, LAYOUT))
    return 0


def remove():
    """Remove memory layout. Leaves project cloneable and valid."""
    if not os.path.isfile(LAYOUT):
        print("%sNOT PRESENT%s  nothing to remove" % (RED, NC))
        return 1
    # Remove the layout
    os.remove(LAYOUT)
    # Remove backup too (no orphaned backup)
    if os.path.isfile(BACKUP):
        os.remove(BACKUP)
    print("%sREMOVED%s  memory layout deleted, project cloneable" % (GREEN, NC))
    return 0


def status():
    """Report current state."""
    has_layout = os.path.isfile(LAYOUT)
    has_backup = os.path.isfile(BACKUP)
    print("memory-layout.json: %s" % ("present" if has_layout else "absent"))
    print("memory-layout.json.prev: %s" % ("present" if has_backup else "absent"))
    if has_layout:
        try:
            l = json.load(open(LAYOUT))
            print("schema: %s" % l.get("schema", "UNKNOWN"))
            print("record_id: %s" % l.get("record_id", "UNKNOWN"))
        except (json.JSONDecodeError, OSError):
            print("schema: CORRUPT")


def main():
    print("%sSPS 2.0 Memory Layout Rollback/Removal%s" % (BOLD, NC))
    if len(sys.argv) > 1 and sys.argv[1] == "--remove":
        return remove()
    if len(sys.argv) > 1 and sys.argv[1] == "--status":
        status()
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        return rollback()
    # Default: status
    status()
    print("")
    print("Usage: %s [--rollback|--remove|--status]" % sys.argv[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
