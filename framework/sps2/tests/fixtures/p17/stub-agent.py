#!/usr/bin/env python3
"""P17 repository-local TEST DOUBLE. This is not an agent.

A fake CLI used only by the Slice 1 test suite. It exists so the complete
execution pipeline can be demonstrated without invoking any real agent CLI
(real-agent execution is disabled by default; GATE-P17-4 is OPEN).

Behaviour is controlled by the goal string, which the runner passes verbatim
after --goal. A goal of the form

    stub-mode:<key>=<value>[,<key>=<value>]...

selects a behaviour:

    exit=<n>          exit with status <n> (default 0)
    sleep=<seconds>   sleep, so the caller's bounded timeout fires
    secret=1          print FAKE credential-shaped values, so transcript
                      scrubbing can be demonstrated (these are test values,
                      not real credentials)
    escape-internal=<abs path>
                      attempt to write outside the authorized workspace using
                      an internally constructed path, so post-execution
                      DETECTION can be demonstrated. This is not prevention
                      and is labelled as such everywhere.
    write=<rel path>  write a file inside the workspace

Any other goal is echoed and the double exits 0.

Standard library only. No network. No real agent behaviour of any kind.
"""
import os
import sys
import time

VERSION = "p17-stub-agent 1.0.0 (repository-local test double, not an agent)"


def parse_mode(goal):
    mode = {}
    if goal.startswith("stub-mode:"):
        for part in goal[len("stub-mode:"):].split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                mode[key.strip()] = value.strip()
    return mode


def main(argv):
    if "--version" in argv:
        print(VERSION)
        return 0
    if "--help" in argv:
        print(VERSION)
        print("usage: stub-agent.py --task <id> --goal <text>")
        return 0

    goal = ""
    for index, token in enumerate(argv):
        if token == "--goal" and index + 1 < len(argv):
            goal = argv[index + 1]
    mode = parse_mode(goal)

    print("stub-agent: accepted task %s" % (
        argv[argv.index("--task") + 1] if "--task" in argv else "?"))
    print("stub-agent: goal received: %s" % goal)

    if mode.get("sleep"):
        time.sleep(float(mode["sleep"]))
        print("stub-agent: sleep completed (the bounded timeout should have "
              "terminated this process first)")

    if mode.get("secret"):
        # FAKE, test-only values shaped like credentials so that scrubbing is
        # observable. They are not real credentials and grant nothing.
        print("stub-agent: using api key sk-test-FAKEfakeFAKEfakeFAKE1234567890")
        print("stub-agent: token=ghp_FAKEfakeFAKEfakeFAKEfake1234",
              file=sys.stderr)

    if mode.get("escape-internal"):
        target = mode["escape-internal"]
        try:
            parent = os.path.dirname(target)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
            with open(target, "w", encoding="utf-8") as handle:
                handle.write("escape attempt by test double\n")
            print("stub-agent: wrote outside the workspace at %s" % target)
        except OSError as exc:
            print("stub-agent: escape write failed: %s" % exc, file=sys.stderr)

    if mode.get("write"):
        target = os.path.join(os.environ.get("P17_WORKSPACE", "."),
                              mode["write"])
        try:
            with open(target, "w", encoding="utf-8") as handle:
                handle.write("stub-agent output\n")
            print("stub-agent: wrote %s inside the workspace" % mode["write"])
        except OSError as exc:
            print("stub-agent: workspace write failed: %s" % exc,
                  file=sys.stderr)

    return int(mode.get("exit", "0"))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
