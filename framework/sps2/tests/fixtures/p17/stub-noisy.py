#!/usr/bin/env python3
"""P17 repository-local TEST DOUBLE (noisy). This is not an agent.

Emits a configurable volume of stdout so Slice 2 can prove BOUNDED capture:
the executor must never buffer the whole stream in memory, the transcript
keeps at most the cap, the truncation is marked explicitly, and the digest of
the ORIGINAL stream is retained even though the original bytes are deleted.

Behaviour is taken from the goal string, as with the other doubles:

    stub-mode:noise=<bytes>     write <bytes> of stdout

Standard library only. No network. No real agent behaviour of any kind.
"""
import sys

VERSION = "p17-stub-noisy 1.0.0 (repository-local test double, not an agent)"
CHUNK = 64 * 1024


def main(argv):
    if "--version" in argv:
        print(VERSION)
        return 0
    if "--help" in argv:
        print(VERSION)
        print("usage: stub-noisy.py --task <id> --goal stub-mode:noise=<bytes>")
        return 0
    goal = ""
    for index, token in enumerate(argv):
        if token == "--goal" and index + 1 < len(argv):
            goal = argv[index + 1]
    volume = 1024
    if goal.startswith("stub-mode:noise="):
        try:
            volume = int(goal.split("=", 1)[1])
        except ValueError:
            volume = 1024
    payload = "x" * CHUNK
    written = 0
    out = sys.stdout
    while written < volume:
        out.write(payload)
        written += CHUNK
    out.flush()
    sys.stderr.write("stub-noisy: emitted %d bytes of stdout\n" % volume)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
