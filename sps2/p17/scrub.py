#!/usr/bin/env python3
"""P17 secret scrubbing (SEC-P17-06 / REQ-P17-07).

Preventive control: task input containing credential-like material is
REJECTED at intake, not stored.

Detection control: transcripts and captured output are scrubbed with
pattern matching before they are written to disk or referenced as evidence.

This is pattern-based scrubbing, not a proof of absence. The documented
limitation (plan section 13, SEC-P17-06) is deliberate: scrubbing is the
defence in depth behind the minimal explicit environment (which stops
secrets reaching the process at all) and intake rejection. A pattern list
cannot guarantee that no secret of an unlisted shape is present.

The second line of defence for credential safety is that the executor passes
a minimal, explicitly constructed environment, so inherited environment
secrets never reach the process. This module covers what does get produced.

Standard library only.
"""
import re

# Deliberately narrow, high-signal shapes. Each pattern carries a label so
# the scrub report can say what class was removed without echoing the value.
PATTERNS = [
    ("private-key-block", re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.DOTALL)),
    ("provider-token", re.compile(
        r"\b(?:sk-[A-Za-z0-9_\-]{12,}|ghp_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,}"
        r"|xox[baprs]-[A-Za-z0-9\-]{10,}|AKIA[0-9A-Z]{16}"
        r"|AIza[0-9A-Za-z_\-]{20,}|sk-ant-[A-Za-z0-9_\-]{12,}|npm_[A-Za-z0-9]{16,})")),
    ("bearer-token", re.compile(r"\b[Bb]earer\s+[A-Za-z0-9._\-]{16,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}")),
    ("url-credentials", re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s/:@]+:[^\s/@]+@")),
    ("assignment", re.compile(
        r"(?i)\b(api[_-]?key|apikey|access[_-]?key|secret[_-]?key|secret|token"
        r"|password|passwd|credential|auth[_-]?token)\b\s*[:=]\s*"
        r"[\"']?[A-Za-z0-9_\-./+=]{8,}[\"']?")),
    ("env-assignment", re.compile(
        r"(?im)^([A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)"
        r"[A-Z0-9_]*\s*=\s*).+$")),
    ("pem-body", re.compile(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
                            re.DOTALL)),
]


def classify(text):
    """Return the sorted list of secret-pattern classes present in text."""
    if not text:
        return []
    found = set()
    for label, pattern in PATTERNS:
        if pattern.search(text):
            found.add(label)
    return sorted(found)


def scrub(text):
    """Return (scrubbed_text, classes_removed).

    Replacement text is a fixed marker. The original value is never echoed
    into any record, log, transcript, or evidence file.
    """
    if text is None:
        return None, []
    if not isinstance(text, str):
        text = str(text)
    removed = classify(text)
    if not removed:
        return text, []
    out = text
    for _, pattern in PATTERNS:
        if label_is_env(pattern):
            out = pattern.sub(lambda m: m.group(1) + "[REDACTED]", out)
        else:
            out = pattern.sub("[REDACTED]", out)
    return out, removed


def label_is_env(pattern):
    return pattern.pattern.startswith("(?im)^([A-Z]")


def scrub_obj(obj):
    """Recursively scrub every string in a JSON-serialisable structure.

    Returns (scrubbed_obj, classes_removed_union).
    """
    removed = set()
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            if isinstance(key, str):
                key2, kc = scrub(key)
                removed.update(kc)
            else:
                key2 = key
            result[key2], vc = scrub_obj(value)
            removed.update(vc)
        return result, sorted(removed)
    if isinstance(obj, list):
        result = []
        for value in obj:
            item, vc = scrub_obj(value)
            result.append(item)
            removed.update(vc)
        return result, sorted(removed)
    if isinstance(obj, str):
        text, classes = scrub(obj)
        removed.update(classes)
        return text, sorted(removed)
    return obj, []


def assert_clean(obj, where):
    """Raise if any secret pattern survives in a structure about to be stored.

    This is the fail-closed gate on write: storage is refused rather than
    attempted when a secret pattern is detected.
    """
    _, classes = scrub_obj(obj)
    if classes:
        raise SecretLeak(where, classes)
    return True


class SecretLeak(Exception):
    """A secret pattern survived into a structure about to be persisted."""

    def __init__(self, where, classes):
        self.where = where
        self.classes = list(classes)
        super(SecretLeak, self).__init__(
            "refusing to persist %s: secret pattern(s) %s detected (values "
            "withheld)" % (where, ",".join(self.classes)))
