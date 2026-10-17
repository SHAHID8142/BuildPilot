#!/usr/bin/env python3
"""SPS 2.0 team bootstrap onboarding dry-run validator.

Agent-neutral. Standard library only. Project-local.

Proves the roadmap P7 acceptance criterion mechanically: "a new teammate
understands the project from the repo alone."

The onboarding checklist is only worth anything if a fresh agent can
actually execute it, so this does not merely confirm the file exists.
It performs the checklist: every recorded artifact is resolved, every
recorded digest is recomputed and compared, and each of the seven steps is
checked to name a real, in-project target.

Scratch copies used by the negative tests are created in an OS temporary
directory and always removed. Nothing is written inside the repository.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))  # tools -> sps2 -> framework -> repo root
SPS2 = os.path.join(REPO, "framework", "sps2")
MEMORY = os.path.join(SPS2, "memory")
BOOTSTRAP = os.path.join(MEMORY, "team-bootstrap.md")
LAYOUT = os.path.join(MEMORY, "memory-layout.json")

GREEN, RED, BOLD, NC = (
    "\033[0;32m", "\033[0;31m", "\033[1m", "\033[0m")

# The layout stores bare filenames; the section they sit in implies the
# directory. Resolving them needs that mapping to be explicit, otherwise a
# fresh agent cannot follow the layout without guessing.
SECTION_DIRS = {
    "decision_records": "decisions",
    "evidence_records": "evidence",
    "requirement_records": "requirements",
    "research_entries": "research",
    "handoff_records": "handoff",
    "audit_reports": "audit",
    "task_lists": "tasks",
}
HASHED_SECTIONS = ("decision_records", "evidence_records",
                   "requirement_records", "research_entries",
                   "handoff_records")


class Res:
    def __init__(self, quiet=False):
        self.passed = self.failed = self.neg_ok = self.neg_missed = 0
        self.quiet = quiet

    def ok(self, m):
        self.passed += 1
        if not self.quiet:
            print("  %sPASS%s  %s" % (GREEN, NC, m))

    def bad(self, m):
        self.failed += 1
        if not self.quiet:
            print("  %sFAIL%s  %s" % (RED, NC, m))

    def neg_ok_case(self, m):
        self.neg_ok += 1
        print("  %sPASS%s  %s" % (GREEN, NC, m))

    def neg_missed_case(self, m):
        self.neg_missed += 1
        print("  %sFAIL%s  %s" % (RED, NC, m))

    def sect(self, t):
        print("\n%s%s%s" % (BOLD, t, NC))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_layout():
    with open(LAYOUT, "r", encoding="utf-8") as fh:
        return json.load(fh)


def check_layout_integrity(r, root=None):
    """Every digest the layout records must match the file on disk.

    This is the check a fresh agent relies on: the layout is only a usable
    single source of truth if its recorded digests actually describe the
    repository. A stale or tampered digest means the layout has drifted.
    """
    root = root or REPO
    layout = os.path.join(root, "framework", "sps2", "memory", "memory-layout.json")
    if not os.path.isfile(layout):
        r.bad("MEMORY_LAYOUT_MISSING")
        return
    try:
        with open(layout, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, ValueError) as exc:
        r.bad("MEMORY_LAYOUT_CORRUPT: %s" % type(exc).__name__)
        return
    if doc.get("schema") != "sps2.memory-layout/v1":
        r.bad("MEMORY_LAYOUT_SCHEMA_INVALID: %r" % doc.get("schema"))
        return
    checked = 0
    problems = []
    for section, subdir in SECTION_DIRS.items():
        entries = doc.get(section) or []
        if section in HASHED_SECTIONS:
            for e in entries:
                name, want = e.get("file"), e.get("sha256")
                path = os.path.join(root, "framework", "sps2", subdir, name or "")
                if not name or not want:
                    problems.append("%s/%s: entry missing file or sha256"
                                    % (section, name))
                    continue
                if not os.path.isfile(path):
                    problems.append("%s/%s: file absent" % (section, name))
                    continue
                got = sha256(path)
                if got != want:
                    problems.append("%s/%s: digest drift" % (section, name))
                checked += 1
        else:
            for name in entries:
                path = os.path.join(root, "framework", "sps2", subdir, name)
                if not os.path.isfile(path):
                    problems.append("%s/%s: file absent" % (section, name))
                checked += 1
    for p in problems[:10]:
        r.bad("LAYOUT_INTEGRITY: %s" % p)
    if not problems:
        r.ok("every recorded artifact resolves and every digest matches "
             "(%d verified)" % checked)


def _resolve_target(t):
    """Resolve a step target to a real path, or None.

    The checklist writes some targets repo-relative ("framework/sps2/memory/...")
    and some as a bare tool name ("validate-p6.py"). Both forms are
    legitimate for a fresh agent, so both are resolved rather than
    demanding one style.
    """
    candidates = [os.path.join(REPO, t), os.path.join(SPS2, t),
                  os.path.join(SPS2, "tools", t),
                  os.path.join(REPO, "framework", "sps2", t)]
    for c in candidates:
        p = os.path.normpath(c)
        if os.path.exists(p):
            return p
    # Last resort: locate by basename within the project surface.
    for base, dirs, files in os.walk(SPS2):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        if t in files:
            return os.path.join(base, t)
    return None


def check_bootstrap_steps(r):
    """Each of the seven steps must name a real, in-project target.

    A step is only followed by a fresh agent if the thing it names can be
    found from the repository root. Naming a file that does not exist, or
    pointing outside the project, makes the step unfollowable.
    """
    if not os.path.isfile(BOOTSTRAP):
        r.bad("BOOTSTRAP_MISSING")
        return
    with open(BOOTSTRAP, "r", encoding="utf-8") as fh:
        body = fh.read()
    steps = re.split(r"^### Step \d+:", body, flags=re.MULTILINE)[1:]
    if len(steps) != 7:
        r.bad("BOOTSTRAP_STEP_COUNT: expected 7 steps, found %d"
              % len(steps))
    else:
        r.ok("bootstrap has exactly 7 steps")
    bad = []
    for section in steps:
        lines = section.strip().splitlines()
        title = lines[0].strip() if lines else ""
        targets = re.findall(r"[\w./-]+\.(?:json|py|sh|md)", section)
        if not targets:
            bad.append("STEP_NO_TARGET: %s" % title)
            continue
        for t in targets:
            if _resolve_target(t) is None:
                bad.append("STEP_TARGET_MISSING: %s -> %s" % (title, t))
            elif not _resolve_target(t).startswith(REPO + os.sep):
                bad.append("STEP_ESCAPES_PROJECT: %s -> %s" % (title, t))
    for b in bad[:10]:
        r.bad(b)
    if not bad:
        r.ok("every step names an existing, in-project target")


def check_no_machine_global(r):
    """The checklist must not depend on machine-global state."""
    with open(BOOTSTRAP, "r", encoding="utf-8") as fh:
        body = fh.read().lower()
    offenders = [p for p in ("/usr/local", "/etc/", "~/.sps", "sudo ")
                 if p in body]
    for o in offenders:
        r.bad("BOOTSTRAP_REQUIRES_GLOBAL: %s" % o)
    if not offenders:
        r.ok("checklist requires no machine-global state")


def check_status_accuracy(r):
    """The layout's own status claims must match the recorded decisions.

    A single source of truth that misreports its own phase status is worse
    than no layout: a fresh agent would act on a false picture.
    """
    doc = load_layout()
    p7 = (doc.get("project") or {}).get("p7_status") or ""
    if "NOT_IMPLEMENTED" in p7:
        r.bad("STATUS_STALE: layout claims P7 is NOT_IMPLEMENTED while its "
              "deliverables exist")
    if "APPROVED" in p7 and "NOT_APPROVED" not in p7:
        d = os.path.join(SPS2, "decisions", "P7-DECISIONS.json")
        comp = {}
        if os.path.isfile(d):
            with open(d, "r", encoding="utf-8") as fh:
                comp = json.load(fh).get("completion") or {}
        state = (comp.get("state") or "PENDING_USER_APPROVAL")
        if state != "APPROVED":
            r.bad("STATUS_OVERSTATES: layout claims P7 APPROVED but the "
                  "recorded completion state is %r" % state)
    if not r.failed:
        r.ok("layout status matches the recorded decision state")


def check_isolation_validator(r):
    """The isolation validator must pass on the live tree."""
    iv = os.path.join(SPS2, "tools", "isolation_validator.py")
    if not os.path.isfile(iv):
        r.bad("ISOLATION_VALIDATOR_MISSING")
        return
    res = subprocess.run([sys.executable, iv], capture_output=True,
                         text=True, cwd=REPO, timeout=180)
    if res.returncode != 0:
        r.bad("ISOLATION_VALIDATOR_FAILED")
    else:
        r.ok("isolation validator passes on the live tree")


def negatives(r):
    """Each case breaks the bootstrap's guarantees and requires detection.

    A case passes only when the breakage IS caught. A control case proves
    the unmutated layout is still accepted, so the guards cannot decay into
    a blanket rejection.
    """
    r.sect("NEGATIVE TESTS — each broken guarantee must be detected")
    tmp = tempfile.mkdtemp(prefix="sps2-bootstrap-neg-")
    try:
        base = os.path.join(tmp, "base")
        shutil.copytree(REPO, base,
                        ignore=shutil.ignore_patterns(".git", "__pycache__"))

        def fresh(name):
            root = os.path.join(tmp, name)
            shutil.copytree(base, root)
            return root

        # N01 digest drift must be caught
        root = fresh("n01")
        t = os.path.join(root, "framework", "sps2", "decisions", "P1-DECISIONS.json")
        with open(t, "a", encoding="utf-8") as fh:
            fh.write("\n")
        sub = Res(quiet=True)
        check_layout_integrity(sub, root=root)
        (r.neg_ok_case("N01 digest drift detected -> rejected")
         if sub.failed else
         r.neg_missed_case("N01 digest drift undetected"))

        # N02 a referenced artifact removed
        root = fresh("n02")
        os.remove(os.path.join(root, "framework", "sps2", "decisions",
                               "P1-DECISIONS.json"))
        sub = Res(quiet=True)
        check_layout_integrity(sub, root=root)
        (r.neg_ok_case("N02 missing artifact detected -> rejected")
         if sub.failed else
         r.neg_missed_case("N02 missing artifact undetected"))

        # N03 corrupt layout must be reported, not crash
        root = fresh("n03")
        with open(os.path.join(root, "framework", "sps2", "memory",
                               "memory-layout.json"), "w",
                  encoding="utf-8") as fh:
            fh.write("{ not json at all")
        sub = Res(quiet=True)
        try:
            check_layout_integrity(sub, root=root)
            caught = sub.failed > 0
        except Exception:
            caught = True
        (r.neg_ok_case("N03 corrupt layout detected -> rejected")
         if caught else
         r.neg_missed_case("N03 corrupt layout undetected"))

        # N04 wrong schema must be rejected
        root = fresh("n04")
        lp = os.path.join(root, "framework", "sps2", "memory", "memory-layout.json")
        with open(lp, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        doc["schema"] = "something-else/v9"
        with open(lp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2)
        sub = Res(quiet=True)
        check_layout_integrity(sub, root=root)
        (r.neg_ok_case("N04 wrong schema detected -> rejected")
         if sub.failed else
         r.neg_missed_case("N04 wrong schema undetected"))

        # N05 bootstrap naming a nonexistent target must be rejected
        root = fresh("n05")
        bp = os.path.join(root, "framework", "sps2", "memory", "team-bootstrap.md")
        with open(bp, "r", encoding="utf-8") as fh:
            body = fh.read()
        body = body.replace("framework/sps2/capability/registry.json",
                            "framework/sps2/capability/does-not-exist.json", 1)
        with open(bp, "w", encoding="utf-8") as fh:
            fh.write(body)
        saved = globals()["BOOTSTRAP"]
        globals()["BOOTSTRAP"] = bp
        sub = Res(quiet=True)
        try:
            check_bootstrap_steps(sub)
            caught = sub.failed > 0
        finally:
            globals()["BOOTSTRAP"] = saved
        (r.neg_ok_case("N05 unfollowable step detected -> rejected")
         if caught else
         r.neg_missed_case("N05 unfollowable step undetected"))

        # CONTROL: the unmutated copy must still be fully accepted
        sub = Res(quiet=True)
        check_layout_integrity(sub, root=base)
        if sub.failed:
            r.neg_missed_case("CONTROL clean layout rejected: %d problems"
                              % sub.failed)
        else:
            r.neg_ok_case("CONTROL unmutated layout still accepted (guards "
                          "are not a blanket ban)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    r = Res()
    print("%sSPS 2.0 Team Bootstrap Onboarding Dry-Run%s" % (BOLD, NC))
    r.sect("1. Memory layout integrity (every digest recomputed)")
    check_layout_integrity(r)
    r.sect("2. Team bootstrap steps are followable from the repo alone")
    check_bootstrap_steps(r)
    r.sect("3. Recorded status matches the recorded decisions")
    check_status_accuracy(r)
    r.sect("4. No machine-global dependency")
    check_no_machine_global(r)
    r.sect("5. Isolation validator passes")
    check_isolation_validator(r)
    negatives(r)
    print("")
    if r.failed == 0 and r.neg_missed == 0:
        print("%s%s== ONBOARDING DRY-RUN VALID: %d checks passed, 0 failed, "
              "%d negative cases ==%s" % (GREEN, BOLD, r.passed, r.neg_ok, NC))
        return 0
    print("%s%s== ONBOARDING DRY-RUN INVALID: %d passed, %d failed, "
          "%d missed ==%s" % (RED, BOLD, r.passed, r.failed, r.neg_missed,
                              NC))
    return 1


if __name__ == "__main__":
    sys.exit(main())
