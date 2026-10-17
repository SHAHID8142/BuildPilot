#!/usr/bin/env python3
"""Secret-safety scanner. Reports metadata ONLY; never prints a secret value.

Patterns are matched, and only the path, line number and a truncated SHA-256
fingerprint are emitted. The matched text is never included in output.

Usage: scan_secrets.py <root> [--quiet]
Exit:  0 clean | 1 secret-like value detected | 2 tooling unavailable
"""
import hashlib
import os
import re
import sys

# Credential-shaped patterns. Deliberately narrow to avoid flagging ordinary
# prose or test fixtures that merely mention a variable name.
PATTERNS = [
    ("ANTHROPIC_AUTH_TOKEN_ASSIGNMENT",
     re.compile(r'ANTHROPIC_AUTH_TOKEN"?\s*[:=]\s*"?([A-Za-z0-9_\-]{16,})')),
    ("OPENROUTER_KEY",
     re.compile(r'\b(sk-or-v1-[A-Za-z0-9]{32,})\b')),
    ("ANTHROPIC_SK_KEY",
     re.compile(r'\b(sk-ant-[A-Za-z0-9\-_]{20,})\b')),
]
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
# Files that legitimately contain credential-SHAPED test data. The values are
# synthetic by construction; skipping them keeps the signal-to-noise ratio
# usable. Listed explicitly so the exemption is auditable, not silent.
# Matched by absolute path suffix so the exemption holds from any scan root.
SELF_REFERENTIAL_SUFFIXES = (
    "/security/scan_secrets.py",
    "/security/test-secret-safety.sh",
    # Contains a SYNTHETIC credential-shaped string as a negative-test fixture
    # (case N14, which must be detectable to prove gate C rejects embedded
    # secrets). Exempted explicitly, never by a blanket skip.
    "/tools/validate-p4.sh",
)


def is_self_referential(path):
    p = path.replace("\\", "/")
    return any(p.endswith(sfx) for sfx in SELF_REFERENTIAL_SUFFIXES)
# Documentation and governance may name a credential class without holding one.
ALLOW_MARKERS = ("credential class", "NEVER include", "not shown",
                 "redacted", "INCIDENT-P3-001")


def fingerprint(v):
    return hashlib.sha256(v.encode()).hexdigest()[:16]


def scan(root, quiet=False):
    findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if is_self_referential(os.path.abspath(p)):
                continue
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            for name, rx in PATTERNS:
                for m in rx.finditer(text):
                    # group(1) when present, else the whole match; either way
                    # only a fingerprint is emitted, never the value itself.
                    val = m.group(1) if m.groups() else m.group(0)
                    line = text[:m.start()].count("\n") + 1
                    findings.append((p, line, name, fingerprint(val)))
    if not quiet:
        if findings:
            for p, line, name, fp in findings:
                print("SECRET_LIKE %s:%d pattern=%s sha256_16=%s"
                      % (p, line, name, fp))
        else:
            print("clean: no credential-shaped value found under %s" % root)
    return findings


def main():
    if len(sys.argv) < 2:
        print("usage: scan_secrets.py <root> [--quiet]")
        return 2
    findings = scan(sys.argv[1], "--quiet" in sys.argv[2:])
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())