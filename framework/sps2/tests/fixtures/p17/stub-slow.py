#!/usr/bin/env python3
"""P17 repository-local TEST DOUBLE (slow). This is not an agent.

Used only by the Slice 1 timeout and process-termination tests. It sleeps far
longer than any bounded timeout the tests allow, so the caller's timeout must
fire and the whole process group must be terminated and reaped.

It also exposes a child process, so the test can show that termination reaches
the entire process tree rather than only the direct child.

Standard library only. No network. No real agent behaviour of any kind.
"""
import subprocess
import sys
import time

VERSION = "p17-stub-slow 1.0.0 (repository-local test double, not an agent)"
SLEEP_SECONDS = 300


def main(argv):
    if "--version" in argv:
        print(VERSION)
        return 0
    # Spawn a child that would outlive the parent, to prove tree termination.
    child = subprocess.Popen(
        [sys.executable, "-c",
         "import time; print('stub-slow: grandchild started', flush=True); "
         "time.sleep(%d)" % SLEEP_SECONDS],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("stub-slow: grandchild pid %d" % child.pid, flush=True)
    print("stub-slow: sleeping %ds; the bounded timeout must terminate this "
          "process group" % SLEEP_SECONDS, flush=True)
    time.sleep(SLEEP_SECONDS)
    print("stub-slow: this line must never be reached", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
