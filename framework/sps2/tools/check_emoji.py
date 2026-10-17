#!/usr/bin/env python3
"""SPS 2.0 P4 no-emoji validator.

Rejects real emoji. Avoids false positives from documentation that merely
DESCRIBES the rule, and from the self-referential test file that contains a
synthetic emoji fixture. Exemptions are explicit and auditable, never silent.
"""
import os
import re
import sys

# Emoji blocks: pictographs, dingbats, misc symbols, variation selectors.
EMOJI = re.compile(
    '[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF'
    '\U0000FE0F\U0001F1E6-\U0001F1FF]')

# Files that legitimately CONTAIN an emoji as test data or rule documentation.
# Listed explicitly so the exemption is auditable rather than hidden.
EXEMPT_SUFFIXES = (
    "/tools/check_emoji.py",          # contains the emoji regex itself
    "/governance/policies/NO-EMOJI.md",  # documents the rule
)
SELF_TEST = "/tests/"


def is_exempt(path):
    p = path.replace("\\", "/")
    if any(p.endswith(sfx) for sfx in EXEMPT_SUFFIXES):
        return True
    # A self-test fixture directory is exempt only when the file itself declares
    # it, so a stray emoji elsewhere in tests/ is still caught.
    if SELF_TEST in p:
        try:
            head = open(path, encoding="utf-8", errors="replace").read(2048)
        except Exception:
            return False
        return "emoji_test_fixture" in head
    return False


def scan(root):
    """Return (findings, scanned). findings are (relpath, lineno) pairs."""
    findings, scanned = [], 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in {".git", "node_modules", "__pycache__"}]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if is_exempt(os.path.abspath(p)):
                continue
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            scanned += 1
            for i, line in enumerate(text.splitlines(), 1):
                if EMOJI.search(line):
                    findings.append((os.path.relpath(p, root), i))
    return findings, scanned


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    findings, scanned = scan(root)
    for rel, line in findings:
        print("EMOJI_VIOLATION %s:%d" % (rel, line))
    print("scanned=%d violations=%d" % (scanned, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())