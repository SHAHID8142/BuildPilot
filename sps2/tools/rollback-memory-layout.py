#!/usr/bin/env python3
"""SPS 2.0 memory layout lifecycle: snapshot, rollback, removal.

Agent-neutral. Standard library only. Project-local.

P7 threat model sections 9, 10 and 17 require that the memory layout be
revertible to its prior state by a single operation, that removal leave
the project valid and cloneable, and that removal leave no orphaned
references.

  snapshot  record the current layout as the rollback point
  rollback  atomically restore that rollback point
  remove    remove every P7 persistent artefact together, so nothing is
            left pointing at a layout that no longer exists
  status    report what is present

Rollback is atomic in the sense the threat model requires: the current
layout is preserved, a temporary file is written, validated, and only then
renamed into place, so an interruption leaves the prior layout intact.

snapshot and rollback are idempotent. remove is idempotent in effect: a
second removal leaves the repository byte-identical, though the tool
removes itself along with the rest of P7 state, so a second run requires
restoring the script first.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SPS2 = os.path.join(REPO, "sps2")
MEMORY = os.path.join(SPS2, "memory")
LAYOUT = os.path.join(MEMORY, "memory-layout.json")
BACKUP = os.path.join(MEMORY, "memory-layout.json.prev")

# Everything P7 persists. Removal clears all of it together: removing only
# the layout would strand the checklist, the docs and the tools, leaving
# references to a file that no longer exists.
P7_ARTEFACTS = [
    "sps2/memory/memory-layout.json",
    "sps2/memory/memory-layout.json.prev",
    "sps2/memory/team-bootstrap.md",
    "sps2/memory/README.md",
    "sps2/memory/P7-IMPLEMENTATION-REPORT.md",
    "sps2/tools/isolation_validator.py",
    "sps2/tools/validate-bootstrap.py",
    "sps2/tools/rollback-memory-layout.py",
]

GREEN, RED, BOLD, NC = (
    "\033[0;32m", "\033[0;31m", "\033[1m", "\033[0m")


def _valid(path):
    """A layout is restorable only if it parses and declares its schema."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return False
    return doc.get("schema") == "sps2.memory-layout/v1"


def snapshot():
    """Record the current layout as the rollback point (idempotent)."""
    if not os.path.isfile(LAYOUT):
        print("%sNO LAYOUT%s  nothing to snapshot" % (RED, NC))
        return 1
    if not _valid(LAYOUT):
        print("%sINVALID LAYOUT%s  refusing to snapshot an unparseable layout"
              % (RED, NC))
        return 1
    shutil.copy2(LAYOUT, BACKUP)
    print("%sSNAPSHOT OK%s  rollback point recorded" % (GREEN, NC))
    return 0


def rollback():
    """Atomically restore the rollback point (idempotent)."""
    if not os.path.isfile(BACKUP):
        print("%sNO ROLLBACK POINT%s  run --snapshot first" % (RED, NC))
        return 1
    if not _valid(BACKUP):
        print("%sINVALID ROLLBACK POINT%s  refusing to restore a corrupt "
              "layout" % (RED, NC))
        return 1
    if os.path.isfile(LAYOUT) and sha(LAYOUT) == sha(BACKUP):
        print("%sNO CHANGE%s  layout already matches the rollback point"
              % (GREEN, NC))
        return 0
    # Preserve what is being replaced, then land the restore via rename so
    # an interruption can never leave a half-written layout in place.
    if os.path.isfile(LAYOUT):
        shutil.copy2(LAYOUT, LAYOUT + ".replaced")
    fd, tmp = tempfile.mkstemp(dir=MEMORY, prefix=".memory-layout-",
                               suffix=".tmp")
    os.close(fd)
    try:
        shutil.copy2(BACKUP, tmp)
        if not _valid(tmp):
            print("%sRESTORE FAILED%s  staged copy did not validate"
                  % (RED, NC))
            return 1
        os.replace(tmp, LAYOUT)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    print("%sROLLBACK OK%s  layout restored from rollback point" % (GREEN, NC))
    return 0


def sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def remove():
    """Remove all P7 persistent state together (idempotent).

    Only files P7 created are touched. Legacy files, the production
    capability registry and every other repository artefact are left
    exactly as they were.
    """
    removed, absent = [], []
    for rel in P7_ARTEFACTS:
        p = os.path.join(REPO, rel)
        if os.path.isfile(p):
            os.remove(p)
            removed.append(rel)
        else:
            absent.append(rel)
    # The replaced-layout sidecar is P7 state too.
    sidecar = LAYOUT + ".replaced"
    if os.path.isfile(sidecar):
        os.remove(sidecar)
        removed.append("sps2/memory/memory-layout.json.replaced")
    for rel in removed:
        print("  removed %s" % rel)
    for rel in absent:
        print("  %s already absent" % rel)
    print("%sREMOVED%s  %d file(s) removed, %d already absent"
          % (GREEN, NC, len(removed), len(absent)))
    return 0


def status():
    present = [r for r in P7_ARTEFACTS
               if os.path.isfile(os.path.join(REPO, r))]
    print("P7 persistent artefacts present: %d of %d"
          % (len(present), len(P7_ARTEFACTS)))
    for rel in P7_ARTEFACTS:
        p = os.path.join(REPO, rel)
        mark = "present" if os.path.isfile(p) else "absent "
        note = ""
        if rel.endswith("memory-layout.json") and os.path.isfile(p):
            note = " (%s)" % ("valid" if _valid(p) else "INVALID")
        print("  %s %s%s" % (mark, rel, note))
    print("rollback point: %s"
          % ("present" if os.path.isfile(BACKUP) else "absent"))


def main():
    print("%sSPS 2.0 Memory Layout Lifecycle%s" % (BOLD, NC))
    mode = sys.argv[1] if len(sys.argv) > 1 else "--status"
    if mode == "--snapshot":
        return snapshot()
    if mode == "--rollback":
        return rollback()
    if mode == "--remove":
        return remove()
    if mode == "--status":
        status()
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
