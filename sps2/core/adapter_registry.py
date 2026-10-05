#!/usr/bin/env python3
"""SPS 2.0 P5 adapter boundary validation.

Agent-neutral. Standard library only.

The core must never depend on an adapter, and an adapter must never write
machine-global state. This module validates the adapter registry against the
adapter contract without importing, executing or requiring any concrete agent.
It never branches on a specific agent identity.
"""
import json
import os
from collections.abc import Hashable

REPO = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

REQUIRED_FIELDS = ("agent_id", "maturity", "writes_global_state",
                   "capabilities", "supports", "fallbacks", "maintainer")
VALID_MATURITY = {"VERIFIED", "EXPERIMENTAL", "DECLARED"}

CONTRACT_PATH = os.path.join(REPO, "sps2", "core", "adapters",
                            "contract.schema.json")
REGISTRY_PATH = os.path.join(REPO, "sps2", "core", "adapters", "registry.json")


def load_contract(path=None):
    with open(path or CONTRACT_PATH) as fh:
        return json.load(fh)


def load_registry(path=None):
    with open(path or REGISTRY_PATH) as fh:
        return json.load(fh)


def _entry(a):
    """A registry entry coerced to a dict.

    A malformed entry (a bare string, a number, null) has no fields to read, so
    every field access goes through here instead of assuming `.get` exists. The
    entry is still rejected by `validate_adapter`; this only keeps the summary
    that callers render into messages computable instead of fatal.
    """
    return a if isinstance(a, dict) else {}


def validate_adapter(adapter):
    """Return a list of contract violations. Empty list means compliant."""
    errs = []
    if not isinstance(adapter, dict):
        return ["ADAPTER_NOT_AN_OBJECT"]
    for f in REQUIRED_FIELDS:
        if f not in adapter:
            errs.append("MISSING_FIELD: %s" % f)
    aid = adapter.get("agent_id")
    if not isinstance(aid, str) or not aid or \
            not all(c.islower() or c.isdigit() or c == "-"
                    for c in aid):
        errs.append("INVALID_AGENT_ID: %r" % (aid,))
    if adapter.get("maturity") not in VALID_MATURITY:
        errs.append("INVALID_MATURITY: %r" % (adapter.get("maturity"),))
    # The architecture forbids machine-global writes at the adapter boundary.
    if adapter.get("writes_global_state") is not False:
        errs.append("ADAPTER_WRITES_GLOBAL_STATE: %s" % aid)
    det = adapter.get("detection")
    if det is not None:
        if not isinstance(det, dict):
            errs.append("ADAPTER_DETECTION_NOT_AN_OBJECT: %s" % aid)
        elif det.get("read_only") is not True:
            errs.append("ADAPTER_DETECTION_NOT_READ_ONLY: %s" % aid)
    if not isinstance(adapter.get("capabilities"), dict):
        errs.append("CAPABILITIES_NOT_AN_OBJECT: %s" % aid)
    if not isinstance(adapter.get("supports"), list):
        errs.append("SUPPORTS_NOT_A_LIST: %s" % aid)
    if not isinstance(adapter.get("fallbacks"), dict):
        errs.append("FALLBACKS_NOT_AN_OBJECT: %s" % aid)
    return errs


def validate_registry(registry=None):
    """Return (errors, summary). Adapters are validated independently."""
    reg = registry if registry is not None else load_registry()
    errs = []
    adapters = reg.get("adapters")
    if not isinstance(adapters, list):
        return ["ADAPTER_REGISTRY_MALFORMED"], {}
    seen = set()
    for a in adapters:
        errs.extend(validate_adapter(a))
        aid = _entry(a).get("agent_id")
        if not isinstance(aid, Hashable):
            continue        # an unhashable id is reported as INVALID_AGENT_ID
        if aid in seen:
            errs.append("DUPLICATE_ADAPTER_ID: %s" % aid)
        seen.add(aid)
    summary = {
        "adapters": len(adapters),
        # Only usable string ids are listed. A malformed entry has no id to
        # report, and mixing shapes here would break the sort that callers
        # build their messages from; the entry itself is rejected above.
        "ids": sorted(x for x in seen if isinstance(x, str) and x),
        "all_write_project_local": all(
            _entry(a).get("writes_global_state") is False for a in adapters),
        "maturities": sorted({m for m in (_entry(a).get("maturity")
                                          for a in adapters)
                              if isinstance(m, str)}),
    }
    return errs, summary


def core_is_adapter_free(core_dir=None):
    """True if no core module references an adapter implementation.

    The core may declare the adapter boundary but must not depend on one. This
    inspects imports only; it never imports the adapters themselves.
    """
    d = core_dir or os.path.join(REPO, "sps2", "core")
    offenders = []
    for root, _dirs, files in os.walk(d):
        if "adapters" in root:
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            try:
                with open(p) as fh:
                    src = fh.read()
            except OSError:
                continue
            for line in src.splitlines():
                s = line.strip()
                if s.startswith(("import ", "from ")) and \
                        "adapters" in s and "registry_api" not in s:
                    offenders.append("%s: %s" % (f, s))
    return offenders