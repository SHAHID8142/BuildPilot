#!/usr/bin/env python3
"""SPS 2.0 team bootstrap onboarding dry-run validator.

Agent-neutral. Standard library only. Project-local.

Proves mechanically that a fresh agent can understand the project
from the repository alone, per roadmap P7 acceptance criterion:
"a new teammate understands the project from the repo alone."

Checks:
1. team-bootstrap.md exists and is readable
2. Every Step section in the bootstrap has a corresponding repository artifact
3. The memory layout is present and valid (correct schema, non-empty)
4. The isolation validator passes (two projects isolated)
5. No step requires machine-global state or external dependencies
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SPS2 = os.path.join(REPO, "sps2")
MEMORY = os.path.join(SPS2, "memory")

GREEN = "\033[0;32m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"


def check_bootstrap_readable():
    """team-bootstrap.md exists and is readable."""
    bp = os.path.join(MEMORY, "team-bootstrap.md")
    if not os.path.isfile(bp):
        return False, "BOOTSTRAP_MISSING"
    body = open(bp).read()
    if len(body) < 200:
        return False, "BOOTSTRAP_TOO_SHORT"
    if "##" not in body:
        return False, "BOOTSTRAP_NO_SECTIONS"
    return True, "bootstrap readable with sections"


def check_bootstrap_steps():
    """Every Step section references at least one repo artifact."""
    bp = os.path.join(MEMORY, "team-bootstrap.md")
    if not os.path.isfile(bp):
        return False, "BOOTSTRAP_MISSING"
    body = open(bp).read()
    # Extract each Step section: heading through next ### or end
    step_sections = re.split(r'^### Step \d+:', body, flags=re.MULTILINE)
    step_sections = step_sections[1:]  # skip pre-first-step text
    if not step_sections:
        return False, "BOOTSTRAP_NO_STEPS"
    errors = []
    for section in step_sections:
        # First line is the step title; rest is the description
        lines = section.strip().splitlines()
        title = lines[0].strip() if lines else ""
        description = section.lower()
        has_artifact = False
        for root, dirs, files in os.walk(SPS2):
            for d in dirs:
                if d.lower() in description and len(d) > 3:
                    has_artifact = True
                    break
            for f in files:
                if f.lower() in description and len(f) > 3:
                    has_artifact = True
                    break
            if has_artifact:
                break
        if not has_artifact:
            # Action-only steps (e.g. "run the validator") are OK
            if any(phrase in description for phrase in
                   ["read this", "run the", "execute", "follow the"]):
                has_artifact = True
        if not has_artifact:
            errors.append("STEP_NO_ARTIFACT: %s" % title[:60])
    if errors:
        return False, "; ".join(errors)
    return True, "%d steps all map to repository artifacts" % len(step_sections)


def check_memory_layout():
    """Memory layout is present and valid: correct schema, non-empty."""
    lp = os.path.join(MEMORY, "memory-layout.json")
    if not os.path.isfile(lp):
        return False, "MEMORY_LAYOUT_MISSING"
    try:
        l = json.load(open(lp))
        if l.get("schema") != "sps2.memory-layout/v1":
            return False, "MEMORY_LAYOUT_SCHEMA_INVALID"
        # Count meaningful sections in the layout
        sections = [k for k in l.keys()
                    if k not in ("schema", "record_id", "generated",
                                  "purpose", "project")]
        if len(sections) < 3:
            return False, "MEMORY_LAYOUT_TOO_SMALL"
        return True, "memory layout valid: %d sections" % len(sections)
    except (json.JSONDecodeError, OSError) as exc:
        return False, "MEMORY_LAYOUT_CORRUPT: %s" % type(exc).__name__


def check_isolation_validator():
    """Isolation validator exists and passes."""
    iv = os.path.join(SPS2, "tools", "isolation_validator.py")
    if not os.path.isfile(iv):
        return False, "ISOLATION_VALIDATOR_MISSING"
    import subprocess
    result = subprocess.run(
        [sys.executable, iv],
        capture_output=True, text=True,
        cwd=REPO, timeout=30)
    if result.returncode != 0:
        return False, "ISOLATION_VALIDATOR_FAILED: %s" % result.stdout.strip()
    return True, "isolation validator passes"


def check_no_machine_global():
    """No bootstrap step requires machine-global state."""
    bp = os.path.join(MEMORY, "team-bootstrap.md")
    if not os.path.isfile(bp):
        return False, "BOOTSTRAP_MISSING"
    body = open(bp).read().lower()
    for bad in ("/usr/local", "/etc/", "~/.sps", "global install",
                "machine-global", "sudo "):
        if bad in body:
            return False, "BOOTSTRAP_REQUIRES_GLOBAL: %s" % bad
    return True, "no machine-global requirement"


def main():
    print("%sSPS 2.0 Team Bootstrap Onboarding Dry-Run Validator%s"
          % (BOLD, NC))
    checks = [
        ("Bootstrap readable", check_bootstrap_readable),
        ("Bootstrap steps map to artifacts", check_bootstrap_steps),
        ("Memory layout valid", check_memory_layout),
        ("Isolation validator passes", check_isolation_validator),
        ("No machine-global requirement", check_no_machine_global),
    ]
    all_ok = True
    for label, fn in checks:
        ok, msg = fn()
        if ok:
            print("  %sPASS%s  %s: %s" % (GREEN, NC, label, msg))
        else:
            print("  %sFAIL%s  %s: %s" % (RED, NC, label, msg))
            all_ok = False

    print("")
    if all_ok:
        print("%sONBOARDING DRY-RUN VALID: 0 failures%s" % (GREEN, NC))
        return 0
    print("%sONBOARDING DRY-RUN INVALID%s" % (RED, NC))
    return 1


if __name__ == "__main__":
    sys.exit(main())