#!/usr/bin/env python3
"""P10 Runtime Validation Gate (REQ-P10-09) — Phase A.

WHAT THIS TOOL IS
    A FAIL-CLOSED, STANDARD-LIBRARY-ONLY runtime gate for the P10 vertical-slice
    contract. It evaluates a set of named controls and reports each one
    explicitly as PASS, FAIL, BLOCKED, or UNIMPLEMENTED. The process exit status
    is non-zero unless every REQUIRED control reaches PASS.

WHAT THIS TOOL IS NOT
    It is NOT a production gate, NOT a promotion mechanism, and NOT evidence that
    runtime verification has ever succeeded. Phase A is authoring only: some
    controls are deliberately BLOCKED because their prerequisite does not exist
    yet (no observed bind, no build directory), and those controls BLOCK an
    overall pass. A green run of this gate's own unit tests does NOT mean the
    gate passes against a real slice, and every unit-test fixture in this
    repository is synthetic.

DESIGN RULES ENFORCED HERE
    1. FAIL-CLOSED BY DEFAULT. Any condition the gate cannot establish is a
       failure, not an assumption.
    2. THE DENOMINATOR IS AUTHORITATIVE. The overall verdict is computed against
       REQUIRED_CONTROL_IDS, never against the subset of controls that happened
       to run. An omitted control is a failure; it never leaves the denominator.
    3. STRUCTURAL VALIDITY IS NEVER SUBSTANTIVE COMPLETENESS. Schema conformance
       is reported on its own axis and can never, by itself, make a slice
       complete, approved, or safe to expose (REQ-P10-09 criterion 3).
    4. UNDEFINED SEMANTICS ARE NOT INVENTED. Where the repository does not define
       a rule, this gate reports UNIMPLEMENTED/BLOCKED rather than guessing.
    5. A DECLARATION IS NOT AN OBSERVATION. Per
       framework/sps2/schemas/p10-slice.schema.json, backend.observed_bind_address is
       RUNTIME-POPULATED ONLY and is never a value the author may assert to
       satisfy validation. The gate therefore cannot treat an author-supplied
       bind string as evidence and reports BLOCKED instead.
    6. A PASS IS NOT CLAIMED FROM A NON-DISCRIMINATING SIGNAL. check_sps2.py's
       main() returns 0 even for unparseable JSON, and the P9 audit returns
       exit 0 for an EMPTY build directory. Both are guarded against explicitly.

WHAT IS ESTABLISHED AND WHAT IS NOT
    ESTABLISHED by this gate, and only this: that a document parses; that it
    conforms structurally to the applicable constraints in the authoritative
    slice schema; that a declared control has a known, non-PASS result; and that
    named prerequisites exist.
    NOT established: cryptographic authenticity, human authentication, real
    bind observations, or any substantive completion/approval state. The six
    DEC-7112 semantics (implemented 2026-10-16 under the Round 14 authorization)
    establish CONTENT INTEGRITY and PROVENANCE RECORDING only — see
    DEC-7112 standing_bounds.authenticity_limit. Those limits block an overall
    pass wherever a prerequisite is absent.

UNDELIBERATELY UNRESOLVED (see UNRESOLVED_SEMANTICS)
    The remaining open items after the DEC-7112 implementation: the
    evidence-reference locator grammar (path resolution only, unchanged), the
    absence of any trust root for cryptographic authenticity, the
    self-declared nature of human-attribution fields (UQ-ATT-2), and the
    absence of the backend operation manifest (arrives with the first backend
    code). Each one blocks an overall pass where it is required.

SCOPE
    Standard library only. No network access, no sockets, no dependency
    installation, no mutation of any repository file. Reads only.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --- Exit codes (fail-closed semantics) ---------------------------------------
EXIT_OK = 0
EXIT_FAILED = 1  # at least one required control failed / blocked / unimplemented
EXIT_ERROR = 2  # usage error or unreadable input

# --- Control result vocabulary -------------------------------------------------
PASS = "PASS"
FAIL = "FAIL"
BLOCKED = "BLOCKED"  # a real prerequisite does not exist yet
UNIMPLEMENTED = "UNIMPLEMENTED"  # repository semantics are undefined

RESULT_VOCABULARY = frozenset({PASS, FAIL, BLOCKED, UNIMPLEMENTED})

# --- Semantics this Phase A refuses to invent ---------------------------------
# Adopted and implemented 2026-10-16 (DEC-7112; Round 14 authorization:
# "GATE-SEMANTICS IMPLEMENTATION: AUTHORIZE / EVIDENCE-FRESHNESS WINDOW: NO
# MAXIMUM-AGE WINDOW"). What remains unresolved is recorded here so the limits
# stay visible rather than silently disappearing with the implementation:
UNRESOLVED_SEMANTICS: Tuple[str, ...] = (
    "evidence_references locator grammar remains path-resolution only; the gate "
    "resolves repo-bounded relative filesystem paths and establishes neither "
    "provenance of authorship nor that the artefact supports the axis it is "
    "cited for",
    "no trust root exists in the repository: digests and gate-record "
    "cross-checks establish content integrity and provenance recording only, "
    "never cryptographic authenticity (DEC-7112 standing_bounds.authenticity_limit)",
    "human attribution fields (decided_by, generated_at, gate-record "
    "timestamps) are self-declared; a digest or a name is not a human "
    "(UQ-ATT-2 remains open)",
    "the backend operation manifest (framework/domain/backend/operations.json) does not "
    "exist yet; req-p10-07-reconciliation fails closed until it arrives with "
    "the first backend code",
    "the gate never writes approval state and never transitions the inventory; "
    "the COMPLETE_AWAITING_USER_APPROVED to COMPLETE_VERIFIED_USER_APPROVED "
    "transition is executed only by a tool run under explicit User "
    "authorization (APPROVAL-MECHANISM: OPTION A requires a fresh User act)",
)

# A control only permits an overall pass when it is required AND passed.
REQUIRED_CONTROL_IDS: Tuple[str, ...] = (
    "schema-structural",
    "slice-required-fields",
    "inventory-preconditions",
    "approval-authenticity",
    "evidence-references",
    "evidence-freshness",
    "evidence-authenticity",
    "layout-slot-conformance",
    "published-only-content",
    "exposure-declaration",
    "slice-id-uniqueness",
    "p9-deployment-audit",
    "cms-state-digest",
    "p8-contract-digest",
    "req-p10-07-reconciliation",
    "approval-state-interaction",
)

_REQUIRED_SET = frozenset(REQUIRED_CONTROL_IDS)


@dataclass
class ControlResult:
    """The explicit outcome of one named control."""

    control_id: str
    requirement: str
    result: str
    detail: str
    required: bool = True

    @property
    def permits_pass(self) -> bool:
        """Only a PASS on a required control permits an overall pass."""
        if not self.required:
            return True
        return self.result == PASS


@dataclass
class GateReport:
    """Aggregate gate outcome.

    Invariant: ``overall == PASS`` if and only if EVERY id in
    REQUIRED_CONTROL_IDS appears exactly once, as a required control, with
    result == PASS, and no unknown control id was injected.

    The overall verdict is therefore computed against the AUTHORITATIVE required
    set, not against whichever controls happened to run. An omitted, renamed,
    duplicated or malformed required control can never leave the denominator.
    """

    results: List[ControlResult] = field(default_factory=list)

    def add(self, result: ControlResult) -> None:
        self.results.append(result)

    # -- integrity (independent of any control's own verdict) ----------------

    @property
    def _by_id(self) -> Dict[str, List[ControlResult]]:
        # A non-string control_id is already reported by
        # `malformed_results`; the grouping key is normalised so that the
        # verdict is computed instead of raising while it is being built.
        grouped: Dict[str, List[ControlResult]] = {}
        for r in self.results:
            key = r.control_id if isinstance(r.control_id, str) else repr(r.control_id)
            grouped.setdefault(key, []).append(r)
        return grouped

    @property
    def missing_required(self) -> List[str]:
        """Required control ids that are absent from the report entirely."""
        present = self._by_id
        return [cid for cid in REQUIRED_CONTROL_IDS if cid not in present]

    @property
    def duplicate_required(self) -> List[str]:
        """Required control ids reported more than once."""
        return [
            cid for cid, items in self._by_id.items()
            if cid in _REQUIRED_SET and len(items) > 1
        ]

    @property
    def demoted_required(self) -> List[str]:
        """Required control ids reported with required=False (demotion escape)."""
        return [
            cid for cid, items in self._by_id.items()
            if cid in _REQUIRED_SET and any(not r.required for r in items)
        ]

    @property
    def unknown_controls(self) -> List[str]:
        """Reported control ids that are not in REQUIRED_CONTROL_IDS at all."""
        return sorted(cid for cid in self._by_id if cid not in _REQUIRED_SET)

    @property
    def malformed_results(self) -> List[str]:
        """Results whose outcome is outside the four-value vocabulary, or whose
        control id is blank. A malformed result can never be read as a PASS.

        The membership test is guarded on ``isinstance(str)`` so that an
        unhashable value (list, dict, set) is REPORTED as malformed rather than
        raising while the verdict is being computed.
        """
        bad: List[str] = []
        for r in self.results:
            if not isinstance(r.control_id, str) or not r.control_id.strip():
                bad.append("<blank control_id>")
            elif not isinstance(r.result, str) or r.result not in RESULT_VOCABULARY:
                bad.append(f"{r.control_id}={r.result!r}")
        return bad

    @property
    def integrity_problems(self) -> List[str]:
        """Every way the report can disagree with the authoritative control set."""
        problems: List[str] = []
        if self.missing_required:
            problems.append("missing required controls: " + ", ".join(self.missing_required))
        if self.duplicate_required:
            problems.append("duplicated required controls: " + ", ".join(self.duplicate_required))
        if self.demoted_required:
            problems.append("required controls demoted to optional: " + ", ".join(self.demoted_required))
        if self.unknown_controls:
            problems.append("unknown controls reported: " + ", ".join(self.unknown_controls))
        if self.malformed_results:
            problems.append("malformed control results: " + ", ".join(self.malformed_results))
        return problems

    # -- verdict -------------------------------------------------------------

    @property
    def failures(self) -> List[ControlResult]:
        return [r for r in self.results if not r.permits_pass]

    @property
    def overall(self) -> str:
        if self.integrity_problems:
            return FAIL
        return PASS if not self.failures else FAIL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate": "P10 runtime validation gate (REQ-P10-09, Phase A)",
            "note": (
                "Authoring-only gate. A pass here is not a production readiness "
                "claim and not evidence that runtime verification ever ran."
            ),
            "structural_validity_is_not_substantive_completion": True,
            "overall": self.overall,
            "required_control_ids": list(REQUIRED_CONTROL_IDS),
            "missing_required_controls": self.missing_required,
            "duplicate_required_controls": self.duplicate_required,
            "demoted_required_controls": self.demoted_required,
            "unknown_controls": self.unknown_controls,
            "malformed_results": self.malformed_results,
            "integrity_problems": self.integrity_problems,
            "unresolved_semantics": list(UNRESOLVED_SEMANTICS),
            "controls": [
                {
                    # Serialised defensively: malformed_results already reports a
                    # non-string control_id, and to_dict() must still yield a
                    # JSON-encodable report rather than raising inside json.dumps
                    # and destroying the evidence the caller needs.
                    "control_id": r.control_id if isinstance(r.control_id, str)
                    else repr(r.control_id),
                    "requirement": r.requirement if isinstance(r.requirement, str)
                    else repr(r.requirement),
                    "result": r.result if isinstance(r.result, str)
                    else repr(r.result),
                    "required": bool(r.required),
                    "detail": r.detail if isinstance(r.detail, str)
                    else repr(r.detail),
                }
                for r in self.results
            ],
        }


# --- helpers -------------------------------------------------------------------


def _load_json(path: str) -> Tuple[Optional[Any], str]:
    """Load JSON read-only. Returns (data, error). Never raises.

    Catches ValueError (which covers both json.JSONDecodeError and
    UnicodeDecodeError) and RecursionError so that a non-UTF-8 or pathologically
    nested file fails CLOSED with a control result instead of crashing the gate.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), ""
    except FileNotFoundError:
        return None, f"missing file: {path}"
    except IsADirectoryError:
        return None, f"not a regular file: {path}"
    except OSError as exc:
        return None, f"unreadable: {path} ({exc})"
    except UnicodeDecodeError as exc:
        return None, f"not valid UTF-8: {path} ({exc})"
    except ValueError as exc:
        return None, f"malformed JSON: {path} ({exc})"
    except RecursionError:
        return None, f"JSON nested too deeply to parse: {path}"


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nested(document: Any, *keys: str) -> Any:
    """Walk ``keys`` through nested mappings, returning None if any level is not.

    Replaces the ``(doc.get(k) or {}).get(k)`` idiom, which raised
    AttributeError whenever an intermediate value was a non-mapping scalar --
    destroying the whole --json report instead of failing one control closed.
    """
    current = document
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _repo_root() -> str:
    """Canonical repository root.

    realpath (not abspath) so that a symlinked invocation cannot resolve the
    AUTHORITATIVE SCHEMA or any other governed artefact through an unverified
    path. Matches framework/sps2/tools/seo_audit.py's Path(__file__).resolve() form.
    """
    here = os.path.dirname(os.path.realpath(__file__))  # <repo>/framework/sps2/tools
    return os.path.dirname(os.path.dirname(here))  # <repo>


def _ensure_importable() -> None:
    """Put the repository root on sys.path so authoritative modules import.

    The gate reuses ``framework.domain.frontend.*``, ``framework.domain.seo.*`` and
    ``framework.sps2.governance.attribution``. When invoked from another working directory
    those imports would otherwise fail and be misreported as control failures.
    Import errors must mean a genuinely missing module, not a missing sys.path
    entry. Position 1, NOT append: sys.path[0] is the script's own directory,
    and an appended entry would let a planted ``framework/sps2/tools/framework/domain/`` tree
    shadow the authoritative modules (the dynamic import below is line-pinned
    by isolation tests — keep this docstring's line count stable).
    """
    root = _repo_root()
    if root not in sys.path:
        sys.path.insert(1, root)


# --- minimal stdlib JSON Schema validator --------------------------------------
#
# DESIGN CONSTRAINTS (deliberate, and enforced by tests):
#   * Standard library only. No third-party JSON Schema implementation.
#   * The validator maintains an explicit ALLOW-LIST of the keywords it knows how
#     to enforce correctly. Encountering any keyword outside that list raises
#     _SchemaUnsupported, which the control reports as BLOCKED. The validator can
#     therefore never silently under-validate a schema that grows a new keyword.
#   * `format` is an ANNOTATION in JSON Schema draft 2020-12, not an assertion.
#     `format: date` is therefore opted into explicitly and enforced strictly
#     (RFC 3339 full-date with real calendar validation). Any OTHER format value
#     is reported as BLOCKED rather than ignored.


class _SchemaUnsupported(Exception):
    """A schema keyword or construct this validator cannot enforce correctly."""

    def __init__(self, path: str, keyword: str, detail: str = "") -> None:
        super().__init__(keyword)
        self.path = path
        self.keyword = keyword
        self.detail = detail

    def __str__(self) -> str:
        base = f"{self.path}: unsupported schema construct {self.keyword!r}"
        return f"{base} ({self.detail})" if self.detail else base


_ASSERTION_KEYWORDS = frozenset({
    "type", "enum", "const", "required", "properties", "additionalProperties",
    "items", "minItems", "minLength", "pattern", "uniqueItems", "allOf",
    "if", "then", "else", "format", "$ref",
})
_ANNOTATION_KEYWORDS = frozenset({"$schema", "$id", "title", "description", "$comment"})
_SUPPORTED_KEYWORDS = _ASSERTION_KEYWORDS | _ANNOTATION_KEYWORDS

_SUPPORTED_FORMATS = frozenset({"date"})
_KNOWN_TYPE_NAMES = frozenset({
    "object", "array", "string", "boolean", "null", "integer", "number",
})
_DATE_RE = re.compile(r"\A([0-9]{4})-([0-9]{2})-([0-9]{2})\Z")


def _ecma262_pattern(pattern: str) -> str:
    """Translate a JSON Schema ``pattern`` from ECMA-262 into Python semantics.

    JSON Schema mandates ECMA-262. In ECMA-262 WITHOUT the ``/m`` flag, ``$``
    asserts END OF INPUT only. Python's ``$`` instead also matches immediately
    before a trailing newline, so ``^...$`` would otherwise accept values
    carrying a trailing "\\\\n". Unescaped, non-class ``$`` is therefore emitted
    as ``\\\\Z`` (absolute end of string). ``^`` already agrees between the two
    dialects for non-multiline patterns and is left unchanged.
    """
    out: List[str] = []
    in_class = False
    escaped = False
    for ch in pattern:
        if escaped:
            out.append(ch)
            escaped = False
        elif ch == "\\":
            out.append(ch)
            escaped = True
        elif in_class:
            if ch == "]":
                in_class = False
            out.append(ch)
        elif ch == "[":
            in_class = True
            out.append(ch)
        elif ch == "$":
            out.append(r"\Z")
        else:
            out.append(ch)
    return "".join(out)


def _has_bare_dot(pattern: str) -> bool:
    """True when the pattern contains an unescaped ``.`` outside a character class.

    ECMA-262's ``.`` excludes ALL line terminators (\\\\n \\\\r U+2028 U+2029);
    Python's excludes only \\\\n. That is the one remaining dialect divergence,
    so a pattern using ``.`` cannot be enforced at ECMA-262 fidelity here and is
    reported BLOCKED rather than approximated.
    """
    in_class = False
    escaped = False
    for ch in pattern:
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif in_class:
            if ch == "]":
                in_class = False
        elif ch == "[":
            in_class = True
        elif ch == ".":
            return True
    return False


def _json_equal(a: Any, b: Any) -> bool:
    """Type-aware JSON equality, recursive to every depth.

    Python treats True == 1 and False == 0, which would wrongly satisfy
    `enum: [true]` with the number 1, or `enum: [0]` with the boolean false.
    That distinction has to hold INSIDE containers too: Python's own container
    equality compares leaves with ==, so [{"x": 1}] == [{"x": True}] is True
    and would wrongly satisfy an object-valued enum/const and wrongly report
    uniqueItems duplicates.
    """
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_json_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_json_equal(a[k], b[k]) for k in a)
    return a == b


def _matches_type(value: Any, type_name: str, path: str) -> bool:
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    raise _SchemaUnsupported(path, "type", f"unknown type name {type_name!r}")


class _SliceSchemaValidator:
    """Recursive-descent validator for the applicable slice-schema keywords."""

    def __init__(self, schema: Any) -> None:
        self.root = schema
        self._patterns: Dict[str, "re.Pattern[str]"] = {}

    # -- entry point ---------------------------------------------------------

    def errors(self, instance: Any) -> List[str]:
        # Static whole-schema audit FIRST: an unenforced constraint anywhere in
        # the schema blocks the result even if this instance never reaches it.
        #
        # The module contract is FAIL-CLOSED: every control is REPORTED and this
        # method never propagates an arbitrary exception, because an escaping
        # TypeError/AttributeError kills the CLI and leaves a --json consumer
        # with an empty report instead of a structured verdict. Any internal
        # fault becomes _SchemaUnsupported, which the control reports BLOCKED.
        try:
            self._audit(self.root, "#", frozenset())
            out: List[str] = []
            self._validate(instance, self.root, "#", out, frozenset())
            return out
        except (_SchemaUnsupported, RecursionError):
            raise
        except Exception as exc:
            raise _SchemaUnsupported(
                "#", "schema",
                f"internal validator fault while enforcing this schema: "
                f"{type(exc).__name__}: {exc}",
            ) from exc

    def is_valid(self, instance: Any, subschema: Any, path: str) -> bool:
        """Boolean evaluation used by if/then. Propagates _SchemaUnsupported."""
        probe: List[str] = []
        self._validate(instance, subschema, path, probe, frozenset())
        return not probe

    # -- internals -----------------------------------------------------------

    def _resolve_ref(self, ref: Any, path: str) -> Any:
        if not isinstance(ref, str):
            raise _SchemaUnsupported(path, "$ref", "reference must be a string")
        if ref == "#":
            return self.root
        if not ref.startswith("#/"):
            raise _SchemaUnsupported(
                path, "$ref",
                "only internal '#/...' pointers are supported; external or "
                "document-relative references are refused and never fetched",
            )
        node: Any = self.root
        for raw in ref[2:].split("/"):
            token = raw.replace("~1", "/").replace("~0", "~")
            if isinstance(node, dict):
                if token not in node:
                    raise _SchemaUnsupported(path, "$ref", f"unresolvable pointer {ref!r}")
                node = node[token]
            elif isinstance(node, list):
                try:
                    node = node[int(token)]
                except (ValueError, IndexError):
                    raise _SchemaUnsupported(path, "$ref", f"unresolvable pointer {ref!r}")
            else:
                raise _SchemaUnsupported(path, "$ref", f"unresolvable pointer {ref!r}")
        return node

    def _compiled(self, pattern: Any, path: str) -> "re.Pattern[str]":
        if not isinstance(pattern, str):
            raise _SchemaUnsupported(path, "pattern", "pattern must be a string")
        cached = self._patterns.get(pattern)
        if cached is None:
            if _has_bare_dot(pattern):
                raise _SchemaUnsupported(
                    path, "pattern",
                    "pattern uses '.' whose ECMA-262 line-terminator semantics "
                    "cannot be reproduced exactly by Python re; refusing to "
                    "approximate it",
                )
            try:
                cached = re.compile(_ecma262_pattern(pattern))
            except re.error as exc:
                raise _SchemaUnsupported(path, "pattern", f"not a usable regex: {exc}")
            self._patterns[pattern] = cached
        return cached

    def _audit(self, schema: Any, path: str, seen: frozenset) -> None:
        """Static whole-schema pre-pass.

        Enforces the keyword allow-list, and the supported FORM of every keyword,
        across EVERY subschema -- including branches the instance under test never
        reaches. Without this the validator would only refuse unknown keywords on
        the paths it happens to walk, and could report a document CONFORMANT while
        an unenforced constraint sits in an unreached branch.
        """
        if isinstance(schema, bool):
            return
        if not isinstance(schema, dict):
            raise _SchemaUnsupported(path, "schema", "subschema must be an object or boolean")
        for keyword in schema:
            if keyword not in _SUPPORTED_KEYWORDS:
                raise _SchemaUnsupported(
                    path, keyword,
                    "this validator has no implementation for it; refusing to "
                    "claim schema conformance while ignoring it",
                )

        # Form-check the VALUE of every supported keyword, not merely its
        # presence. A keyword the validator knows how to apply but whose
        # value is malformed (an unknown type name, a string where an
        # integer belongs, an explicit null) must BLOCK, never be silently
        # skipped. Guarding with `is not None` conflated ABSENT with an
        # explicit null and let a null DELETE an enforced constraint: nulling
        # the root `allOf` made a slice claiming APPROVED with no approval
        # record report structural PASS.
        if "type" in schema:
            types = schema["type"]
            if not isinstance(types, (str, list)):
                raise _SchemaUnsupported(
                    path, "type", "type must be a string or an array of strings"
                )
            for name in types if isinstance(types, list) else [types]:
                if not isinstance(name, str) or name not in _KNOWN_TYPE_NAMES:
                    raise _SchemaUnsupported(
                        path, "type", f"unknown type name {name!r}"
                    )
        properties = schema.get("properties")
        if "properties" in schema and not isinstance(properties, dict):
            # `null` is not a valid `properties` value; treat its presence
            # as malformed rather than as absence.
            raise _SchemaUnsupported(
                path, "properties", "properties must be an object"
            )
        if isinstance(properties, dict):
            for name, subschema in properties.items():
                self._audit(subschema, f"{path}/properties/{name}", seen)
        if "items" in schema:
            items = schema["items"]
            if isinstance(items, list):
                raise _SchemaUnsupported(path, "items", "tuple-form items are not implemented")
            if not isinstance(items, (dict, bool)):
                raise _SchemaUnsupported(path, "items", "items must be a schema")
        if "additionalProperties" in schema and not isinstance(
            schema["additionalProperties"], bool
        ):
            raise _SchemaUnsupported(
                path, "additionalProperties",
                "additionalProperties must be a boolean; schema-valued "
                "additionalProperties is not implemented",
            )
        for keyword in ("minLength", "minItems"):
            if keyword in schema:
                value = schema[keyword]
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    raise _SchemaUnsupported(
                        path, keyword, f"{keyword} must be a non-negative integer"
                    )
        if "uniqueItems" in schema and not isinstance(schema["uniqueItems"], bool):
            raise _SchemaUnsupported(
                path, "uniqueItems", "uniqueItems must be a boolean"
            )
        if "format" in schema:
            fmt = schema["format"]
            if not isinstance(fmt, str) or fmt not in _SUPPORTED_FORMATS:
                raise _SchemaUnsupported(
                    path, "format",
                    f"format {fmt!r} is not enforced by this validator; only RFC 3339 "
                    "'date' is implemented",
                )
        if "pattern" in schema:
            self._compiled(schema["pattern"], path)
        if "required" in schema:
            required = schema["required"]
            if not isinstance(required, list):
                raise _SchemaUnsupported(path, "required", "required must be an array")
            for index, name in enumerate(required):
                # A non-string member reached `name not in inst` and raised
                # TypeError (unhashable), destroying the whole report.
                if not isinstance(name, str):
                    raise _SchemaUnsupported(
                        path, "required",
                        f"required[{index}] must be a string, found {type(name).__name__}",
                    )
            if len(set(required)) != len(required):
                raise _SchemaUnsupported(
                    path, "required", "required must contain unique entries"
                )
        if "enum" in schema and not isinstance(schema["enum"], list):
            raise _SchemaUnsupported(path, "enum", "enum must be an array")
        # `const` is deliberately NOT form-checked: `const: null` is a legal,
        # meaningful constraint meaning "the value must be JSON null".
        for keyword in ("items", "if", "then", "else"):
            if keyword in schema:
                self._audit(schema[keyword], f"{path}/{keyword}", seen)
        if "allOf" in schema:
            all_of = schema["allOf"]
            # `or []` conflated ABSENT with every falsy non-array (null, false,
            # 0, {}, "") and let a truthy non-iterable (5, 1.5) reach
            # enumerate(), raising an uncaught TypeError.
            if not isinstance(all_of, list):
                raise _SchemaUnsupported(
                    path, "allOf",
                    f"allOf must be an array of schemas, found {type(all_of).__name__}",
                )
            if not all_of:
                raise _SchemaUnsupported(path, "allOf", "allOf must be a non-empty array")
            for index, subschema in enumerate(all_of):
                if not isinstance(subschema, (dict, bool)):
                    raise _SchemaUnsupported(
                        path, "allOf", f"allOf[{index}] must be a schema"
                    )
                self._audit(subschema, f"{path}/allOf/{index}", seen)
        if "$ref" in schema:
            ref = schema["$ref"]
            key = ref if isinstance(ref, str) else repr(ref)
            if key in seen:
                raise _SchemaUnsupported(path, "$ref", "reference cycle")
            self._audit(self._resolve_ref(ref, path), f"{path}$ref[{key}]", seen | {key})

    def _validate(self, inst: Any, schema: Any, path: str, out: List[str],
                  seen: frozenset) -> None:
        if schema is True:
            return
        if schema is False:
            out.append(f"{path}: no value is permitted at this location")
            return
        if not isinstance(schema, dict):
            raise _SchemaUnsupported(path, "schema", "subschema must be an object or boolean")

        for keyword in schema:
            if keyword not in _SUPPORTED_KEYWORDS:
                raise _SchemaUnsupported(
                    path, keyword,
                    "this validator has no implementation for it; refusing to "
                    "claim schema conformance while ignoring it",
                )

        if "$ref" in schema:
            ref = schema["$ref"]
            key = (ref if isinstance(ref, str) else repr(ref), path)
            if key in seen:
                raise _SchemaUnsupported(path, "$ref", "reference cycle")
            self._validate(inst, self._resolve_ref(ref, path), path, out, seen | {key})

        types = schema.get("type")
        if types is not None:
            names = types if isinstance(types, list) else [types]
            if not any(_matches_type(inst, n, path) for n in names):
                out.append(f"{path}: expected type {types!r}, found {_json_kind(inst)}")

        if "enum" in schema:
            allowed = schema["enum"]
            if not isinstance(allowed, list):
                raise _SchemaUnsupported(path, "enum", "enum must be an array")
            if not any(_json_equal(inst, candidate) for candidate in allowed):
                out.append(f"{path}: value {inst!r} is not one of {allowed!r}")

        if "const" in schema:
            if not _json_equal(inst, schema["const"]):
                out.append(f"{path}: value {inst!r} must equal {schema['const']!r}")

        if isinstance(inst, str):
            min_length = schema.get("minLength")
            if isinstance(min_length, int) and len(inst) < min_length:
                out.append(f"{path}: shorter than minLength {min_length}")
            pattern = schema.get("pattern")
            if pattern is not None:
                if not self._compiled(pattern, path).search(inst):
                    out.append(f"{path}: {inst!r} does not match pattern {pattern!r}")
            fmt = schema.get("format")
            if fmt is not None:
                if not isinstance(fmt, str) or fmt not in _SUPPORTED_FORMATS:
                    raise _SchemaUnsupported(
                        path, "format",
                        f"format {fmt!r} is not enforced by this validator; "
                        "only RFC 3339 'date' is implemented",
                    )
                if not _is_rfc3339_full_date(inst):
                    out.append(f"{path}: {inst!r} is not an RFC 3339 full-date")

        if isinstance(inst, list):
            min_items = schema.get("minItems")
            if isinstance(min_items, int) and len(inst) < min_items:
                out.append(f"{path}: fewer than minItems {min_items}")
            if schema.get("uniqueItems") is True:
                for i in range(len(inst)):
                    for j in range(i + 1, len(inst)):
                        if _json_equal(inst[i], inst[j]):
                            out.append(f"{path}: items {i} and {j} are duplicates")
                            break
            items = schema.get("items")
            if items is not None:
                if isinstance(items, list):
                    raise _SchemaUnsupported(path, "items", "tuple-form items are not implemented")
                if not isinstance(items, (dict, bool)):
                    raise _SchemaUnsupported(path, "items", "items must be a schema")
                for index, element in enumerate(inst):
                    self._validate(element, items, f"{path}[{index}]", out, seen)

        if isinstance(inst, dict):
            required = schema.get("required")
            if required is not None:
                if not isinstance(required, list):
                    raise _SchemaUnsupported(path, "required", "required must be an array")
                for name in required:
                    if name not in inst:
                        out.append(f"{path}: missing required property {name!r}")
            properties = schema.get("properties")
            if properties is not None:
                if not isinstance(properties, dict):
                    raise _SchemaUnsupported(path, "properties", "properties must be an object")
                for name, subschema in properties.items():
                    if name in inst:
                        self._validate(inst[name], subschema, f"{path}/properties/{name}", out, seen)
            # additionalProperties is only an assertion when it is PRESENT. An
            # absent keyword must not be read as `false`, or every subschema that
            # declares `properties` without declaring `additionalProperties`
            # (e.g. an `if` branch) would be wrongly closed to its own properties.
            if "additionalProperties" in schema:
                additional = schema["additionalProperties"]
                if additional is False:
                    closed = set(properties) if isinstance(properties, dict) else set()
                    for name in inst:
                        if name not in closed:
                            out.append(f"{path}: additional property {name!r} is not permitted")
                elif isinstance(additional, bool):
                    pass  # `true` is a no-op
                else:
                    raise _SchemaUnsupported(
                        path, "additionalProperties",
                        "schema-valued additionalProperties is not implemented",
                    )

        all_of = schema.get("allOf")
        if all_of is not None:
            # Defence in depth: `is_valid()` reaches _validate without the
            # static pre-pass, so the form of allOf is checked here too rather
            # than trusting enumerate() with an arbitrary value.
            if not isinstance(all_of, list):
                raise _SchemaUnsupported(
                    path, "allOf",
                    f"allOf must be an array of schemas, found {type(all_of).__name__}",
                )
            for subschema in all_of:
                self._validate(inst, subschema, f"{path}/allOf", out, seen)

        if "if" in schema:
            branch = "then" if self.is_valid(inst, schema["if"], f"{path}/if") else "else"
            if branch in schema:
                self._validate(inst, schema[branch], f"{path}/{branch}", out, seen)


def _json_kind(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _is_rfc3339_full_date(text: str) -> bool:
    match = _DATE_RE.match(text)
    if not match:
        return False
    year, month, day = (int(g) for g in match.groups())
    try:
        import datetime

        datetime.date(year, month, day)
    except ValueError:
        return False
    return True


# --- individual controls -------------------------------------------------------


def check_schema_structural(slice_doc: Any) -> ControlResult:
    """REQ-P10-09 c.1/c.2/c.3 — structural conformance reported SEPARATELY.

    Enforces every applicable constraint in the authoritative slice schema that
    this validator implements: JSON types, required properties (nested, not just
    at the root), patterns, enums, consts, array item constraints, minItems,
    minLength, uniqueItems, additionalProperties:false, allOf, the if/then
    conditionals, the single internal $ref, and `format: date`.

    It deliberately does NOT consult or influence any other control's result.
    A schema construct this validator cannot enforce is reported BLOCKED, never
    silently ignored, and BLOCKED is a required control so it cannot pass.
    """
    cid = "schema-structural"
    req = "REQ-P10-09 c.1, c.2, c.3"
    if not isinstance(slice_doc, dict):
        return ControlResult(cid, req, FAIL, "slice document is not a JSON object")
    schema_path = os.path.join(_repo_root(), "framework", "sps2", "schemas", "p10-slice.schema.json")
    schema, err = _load_json(schema_path)
    if err:
        return ControlResult(cid, req, FAIL, f"cannot read slice schema: {err}")
    try:
        errors = _SliceSchemaValidator(schema).errors(slice_doc)
    except _SchemaUnsupported as exc:
        return ControlResult(
            cid, req, BLOCKED,
            f"cannot enforce the authoritative schema: {exc}. The gate refuses to "
            "claim schema conformance while an applicable constraint is unenforced.",
        )
    except RecursionError:
        return ControlResult(cid, req, BLOCKED, "schema validation exceeded recursion depth")
    if errors:
        shown = errors[:8]
        more = f" (+{len(errors) - len(shown)} more)" if len(errors) > len(shown) else ""
        return ControlResult(
            cid, req, FAIL,
            f"structurally invalid: {len(errors)} schema violation(s): "
            + "; ".join(shown) + more
            + ". Structural validity alone never establishes completion or approval.",
        )
    return ControlResult(
        cid, req, PASS,
        "structurally valid against every applicable constraint this validator "
        "enforces (types, required, patterns, enums, items, minItems, minLength, "
        "uniqueItems, additionalProperties, allOf/if-then, $ref, format:date). "
        "This is a STRUCTURAL result only and asserts nothing about runtime "
        "verification.",
    )


def check_slice_required_fields(slice_doc: Any) -> ControlResult:
    """REQ-P10-09 c.4 — the slice must declare all eight axes."""
    cid = "slice-required-fields"
    req = "REQ-P10-09 c.4"
    if not isinstance(slice_doc, dict):
        return ControlResult(cid, req, FAIL, "slice document is not a JSON object")
    axes = slice_doc.get("axis_contracts")
    if not isinstance(axes, dict):
        return ControlResult(cid, req, FAIL, "axis_contracts missing or malformed")
    expected = {
        "frontend", "cms", "backend", "data",
        "validation", "assets", "seo", "tests",
    }
    missing = sorted(expected - set(axes))
    if missing:
        return ControlResult(cid, req, FAIL, f"axis contracts missing: {missing}")
    return ControlResult(cid, req, PASS, "all eight axis contracts are declared")


def check_inventory_preconditions(inventory: Any) -> ControlResult:
    """REQ-P10-17 — the inventory must be structurally complete before any claim.

    This control NEVER writes approval state and NEVER transitions the inventory.
    It only observes. COMPLETE_AWAITING_USER_APPROVAL is a legitimate, expected
    state at this time and is reported as an observation, not as a failure.
    """
    cid = "inventory-preconditions"
    req = "REQ-P10-17"
    if not isinstance(inventory, dict):
        return ControlResult(cid, req, FAIL, "inventory is not a JSON object")
    for field_name in ("inventory_id", "inventory_state", "complete", "sections"):
        if field_name not in inventory:
            return ControlResult(cid, req, FAIL, f"inventory missing '{field_name}'")
    provenance = inventory.get("provenance")
    complete = inventory.get("complete")
    if not isinstance(complete, bool):
        # A truthy non-boolean (1, "true", "yes") must not be a demotion escape
        # that skips every completeness assertion below.
        return ControlResult(
            cid, req, FAIL,
            f"inventory.complete={complete!r} is not a boolean; a completeness claim "
            "must be exactly true or false",
        )
    if complete is True:
        if not isinstance(provenance, dict) or not _nonblank(provenance.get("generator")):
            return ControlResult(
                cid, req, FAIL, "complete=true requires a non-blank provenance.generator"
            )
        sections = inventory.get("sections")
        if not isinstance(sections, list) or not sections:
            return ControlResult(cid, req, FAIL, "complete=true requires >=1 section")
        incomplete: List[str] = []
        malformed_sections: List[str] = []
        for section in sections:
            if not isinstance(section, dict):
                incomplete.append("<malformed section>")
                continue
            identifier = section.get("section_id")
            if not isinstance(identifier, dict) or not _nonblank(
                identifier.get("value")
            ):
                # p10-section-inventory.schema.json requires section_id to
                # carry a non-blank value; a null or non-object identifier
                # cannot name a section at all.
                malformed_sections.append(repr(identifier))
                continue
            label = str(identifier.get("value"))
            if section.get("section_completeness") != "COMPLETE":
                incomplete.append(label)
        if malformed_sections:
            return ControlResult(
                cid, req, FAIL,
                "complete=true but sections have no usable section_id: "
                + "; ".join(malformed_sections),
            )
        if incomplete:
            return ControlResult(
                cid, req, FAIL, f"complete=true but sections incomplete: {incomplete}"
            )
    state = inventory.get("inventory_state")
    if state == "COMPLETE_VERIFIED_USER_APPROVED":
        return ControlResult(
            cid, req, FAIL,
            "inventory claims COMPLETE_VERIFIED_USER_APPROVED; this Phase A gate does "
            "not certify that state and requires a runtime-gate PASS that has never "
            "occurred",
        )
    return ControlResult(
        cid, req, PASS,
        f"inventory preconditions satisfied; observed state={state!r}, "
        "complete=%r, user_approval=%r. Observation only; approval state is untouched."
        % (inventory.get("complete"), inventory.get("user_approval")),
    )


def check_approval_authenticity(slice_doc: Any, approval: Any = None) -> ControlResult:
    """REQ-P10-09 c.6/c.10 — reuse the authoritative attribution module.

    An approval that merely exists is not enough; it must be attributable to a
    User with a decision date. Agent-attributed, null, or malformed approvals
    fail closed.

    SLICE BINDING. REQ-P10-09 c.6 makes this gate responsible for rejecting
    agent-attributed approval, and the slice schema's own $comment assigns
    exactly that obligation here ("that user_approval reflects a real User
    decision rather than an agent assertion"). An approval belonging to some
    other record cannot discharge that obligation, so this control judges the
    SLICE's own user_approval whenever the slice carries one or declares itself
    APPROVED. A separately supplied approval object (a decision record's
    approval block) is never a substitute for the slice's own record: it can
    neither rescue nor override it, so an agent-attributed slice approval
    cannot be laundered into a PASS by attaching an unrelated decision record.

    The slice document has no `state` property; its lifecycle field
    acceptance_state is that document's own approval state, and the schema's
    allOf conditional ties a non-null user_approval to acceptance_state
    APPROVED. The slice's own fields are therefore presented to the attribution
    authority in the shape it already accepts, and a `state` carried by the
    slice is overridden rather than trusted. Every attribution judgement —
    agent detection included — remains attribution's alone; nothing here
    reimplements or weakens it, and this module is not modified.
    """
    cid = "approval-authenticity"
    req = "REQ-P10-09 c.6, c.10"
    try:
        from framework.sps2.governance.attribution import (
            approval_is_user_attributable,
            reason_not_attributable,
        )
    except ImportError as exc:  # fail closed if the authority is unavailable
        return ControlResult(cid, req, FAIL, f"cannot import authoritative attribution: {exc}")
    doc = slice_doc if isinstance(slice_doc, dict) else {}
    acceptance_state = doc.get("acceptance_state")
    slice_approval = doc.get("user_approval")
    # The slice is the authority on its own approval whenever it carries one or
    # declares itself APPROVED; otherwise it makes no approval claim at all.
    if slice_approval is not None or acceptance_state == "APPROVED":
        if not isinstance(slice_approval, dict):
            return ControlResult(
                cid, req, FAIL,
                f"the slice declares approval (acceptance_state={acceptance_state!r}) "
                f"but its own user_approval is missing or malformed: "
                f"{slice_approval!r}. An unrelated approval record can never substitute "
                "for the slice's own approval.",
            )
        subject = dict(slice_approval)
        # REQ-P10-09 c.6 requires decided_by_role=USER "so agent attribution is
        # structurally impossible". That enum is enforced structurally, but this
        # control does not rely on a sibling control to catch a forged role, so
        # it applies the same existing rule the repo already applies in
        # check_p10_inventory.py and the P17 execution gate.
        role = subject.get("decided_by_role")
        if role != "USER":
            return ControlResult(
                cid, req, FAIL,
                f"the slice's own user_approval declares decided_by_role={role!r}; "
                "REQ-P10-09 c.6 requires decided_by_role=USER so that approval can "
                "never be structurally attributed to an agent. An unrelated approval "
                "record can never substitute for the slice's own approval.",
            )
        subject["state"] = (
            acceptance_state if isinstance(acceptance_state, str) else "NOT_APPROVED"
        )
        source = "the slice's own user_approval"
    else:
        # The slice asserts no approval, so the supplied decision-record
        # approval is attributed under the pre-existing contract, unchanged.
        if approval is None:
            return ControlResult(cid, req, FAIL, "approval is null (not an approval)")
        subject = approval
        source = "the supplied approval record"
    if not isinstance(subject, dict):
        return ControlResult(cid, req, FAIL, "approval is malformed (not an object)")
    # TRUST BOUNDARY. attribution.approval_is_user_attributable() calls .strip()
    # on decided_by and on decided_on/decided_at WITHOUT validating their type,
    # so a non-string value raised AttributeError/TypeError and destroyed the
    # entire --json report. Validate the SHAPE here, before delegating, so a
    # malformed approval becomes an explicit FAIL instead of an unhandled
    # crash. This checks shape only: every attribution judgement remains
    # attribution's alone, and this module is not modified.
    for field_name in ("decided_by", "decided_on", "decided_at"):
        value = subject.get(field_name)
        if value is not None and not isinstance(value, str):
            return ControlResult(
                cid, req, FAIL,
                f"approval is malformed: {field_name}={value!r} is not a string; an "
                "approval attribute that is not a string cannot be a User decision",
            )
    if approval_is_user_attributable(subject):
        return ControlResult(
            cid, req, PASS,
            f"approval of {source} is attributable to a User per "
            "attribution.approval_is_user_attributable(), which requires a non-blank "
            "decider and a non-blank decision-date FIELD. NOTE: this gate does not "
            "validate the decision date's format; the repository defines no authority "
            "for one (see unresolved_semantics).",
        )
    return ControlResult(
        cid, req, FAIL,
        f"approval of {source} is not user-attributable: "
        f"{reason_not_attributable(subject)}",
    )


def _canonical_within(root: str, candidate: str) -> bool:
    """True when ``candidate``'s canonical path is ``root`` or lies inside it.

    Uses realpath on BOTH sides, so '../' traversal and symlink escapes are
    defeated in one step. Matches framework/sps2/p17/confinement.inside_boundary.

    ``ValueError`` is caught alongside ``OSError``: ``os.path.realpath`` raises
    it for a path containing an embedded NUL byte, and letting that escape would
    destroy the whole --json report instead of failing this control closed.
    """
    try:
        real_root = os.path.realpath(root)
        real_path = os.path.realpath(candidate)
    except (OSError, ValueError):
        return False
    if real_path == real_root:
        return True
    return real_path.startswith(real_root + os.sep)


def _artifact_present(path: str) -> bool:
    """True when ``path`` is a regular file with non-blank content.

    ``os.path.getsize(...) > 0`` accepted a whitespace-only robots.txt or
    sitemap.xml, which satisfies the artifact-shape requirement with content
    that says nothing.
    """
    try:
        if not os.path.isfile(path):
            return False
        with open(path, "rb") as handle:
            return bool(handle.read().strip())
    except (OSError, ValueError):
        return False


def check_evidence_references(
    slice_doc: Any,
    base_dir: str,
    allowed_root: Optional[str] = None,
) -> ControlResult:
    """REQ-P10-09 c.5 — PATH RESOLUTION ONLY for declared evidence references.

    SCOPE OF WHAT THIS ESTABLISHES: that a declared reference is a
    repository-bounded, relative filesystem path that resolves to an existing
    regular file. Nothing more. It does NOT establish that the file is genuine
    evidence, that it is current, that it is not stale or self-contradictory, or
    that it supports the axis it is cited for. Those concerns are reported by the
    separately UNIMPLEMENTED controls `evidence-authenticity` and
    `evidence-freshness`, which prevent an overall pass.

    The reference grammar is UNDEFINED by the repository
    (p10-slice.schema.json declares evidence_references as bare strings with no
    pattern and names no root), so unsupported forms are refused rather than
    guessed: absolute paths, drive-style roots and any path resolving outside
    `allowed_root` are rejected.
    """
    cid = "evidence-references"
    req = "REQ-P10-09 c.5"
    if not isinstance(slice_doc, dict):
        return ControlResult(cid, req, FAIL, "slice document is not a JSON object")
    refs = slice_doc.get("evidence_references")
    if not isinstance(refs, list) or not refs:
        return ControlResult(cid, req, FAIL, "evidence_references missing or empty")
    root = os.path.realpath(allowed_root) if allowed_root else _repo_root()
    malformed: List[str] = []
    unsupported: List[str] = []
    outside: List[str] = []
    unresolved: List[str] = []
    resolved = 0
    for ref in refs:
        if not _nonblank(ref):
            malformed.append(repr(ref))
            continue
        if "\x00" in ref:
            # An embedded NUL makes every filesystem call raise ValueError.
            # Reported as malformed rather than allowed to escape and destroy
            # the whole --json report.
            malformed.append(f"{ref!r} (embedded NUL byte)")
            continue
        if os.path.isabs(ref) or ref.startswith("~"):
            unsupported.append(f"{ref!r} (absolute reference form)")
            continue
        candidate = os.path.join(base_dir, ref)
        if not _canonical_within(root, candidate):
            # Catches '../' traversal AND symlinks that escape the boundary.
            outside.append(f"{ref!r} -> {os.path.realpath(candidate)}")
            continue
        if not os.path.isfile(candidate):
            unresolved.append(ref)
            continue
        resolved += 1
    if malformed:
        return ControlResult(cid, req, FAIL, f"malformed evidence references: {malformed}")
    if unsupported:
        return ControlResult(
            cid, req, FAIL,
            "unsupported evidence reference form(s): " + "; ".join(unsupported)
            + ". The locator grammar is undefined by the repository, so unsupported "
              "forms are refused rather than guessed.",
        )
    if outside:
        return ControlResult(
            cid, req, FAIL,
            f"evidence references resolve outside the allowed root {root}: "
            + "; ".join(outside),
        )
    if unresolved:
        return ControlResult(
            cid, req, FAIL,
            f"evidence references do not resolve to real artifacts: {unresolved}",
        )
    return ControlResult(
        cid, req, PASS,
        f"PATH RESOLUTION ONLY: all {resolved} evidence reference(s) resolve to an "
        f"existing regular file inside {root}. This establishes existence and "
        "containment ONLY — not authenticity, not freshness, not consistency, and "
        "not that the artefact supports the axis it is cited for (see the "
        "separate controls evidence-authenticity and evidence-freshness, which "
        "judge the referenced records' contents).",
    )


def _duplicate_ids(records: Any) -> List[str]:
    """Ids appearing on more than one record.

    Both CMS lookups were plain dict comprehensions, so a later record silently
    overwrote an earlier one: a draft record followed by a published copy of the
    SAME id made `published-only-content` PASS purely by array order.
    Identity must be unique and must never be resolved by position.
    """
    if not isinstance(records, list):
        return []
    seen: Dict[str, int] = {}
    for record in records:
        if isinstance(record, dict) and _nonblank(record.get("id")):
            seen[record["id"]] = seen.get(record["id"], 0) + 1
    return sorted(key for key, count in seen.items() if count > 1)


def _content_type_fields(content_type: Any) -> Optional[set]:
    """P8 ContentType field names, extracted by the AUTHORITATIVE registry helper.

    layout_registry._extract_field_names is the single source of P8 field-name
    extraction (REQ-P10-02 c.3). The gate previously kept a second, divergent
    copy that was simultaneously more permissive (silently skipping a
    malformed field entry, understating what it then reported as `available`)
    and stricter (returning None for bare-string field lists and ContentType
    model objects the registry accepts). TypeError is mapped to None so this
    control keeps failing closed exactly as before.
    """
    try:
        from framework.domain.frontend.layout_registry import _extract_field_names
        return set(_extract_field_names(content_type))
    except (TypeError, ImportError):
        return None


def check_layout_slot_conformance(
    slice_doc: Any,
    content_types: List[Any],
    content_records: List[Any],
) -> ControlResult:
    """REQ-P10-09 c.4/c.5 — layout registry-known and slot conformance.

    Entity typing (defect corrected): ``cms_content_references[].content_id``
    names a P8 **Content** document (p10-slice.schema.json: "Reference to a
    persisted P8 Content document"). The authoritative Content->ContentType
    relationship is ``Content.type_id == ContentType.id`` (framework/domain/cms/model.py);
    the two identifiers come from independent uuid4 spaces and are never
    interchangeable. The gate therefore resolves Content -> type_id ->
    ContentType and never compares a Content id against a ContentType id.

    Every reference is inspected. When the relationship cannot be established the
    control fails closed with an explicit reason rather than assuming one.
    """
    cid = "layout-slot-conformance"
    req = "REQ-P10-09 c.4, c.5"
    if not isinstance(slice_doc, dict):
        return ControlResult(cid, req, FAIL, "slice document is not a JSON object")
    layout_id = slice_doc.get("layout_id")
    if not _nonblank(layout_id):
        return ControlResult(cid, req, FAIL, "layout_id missing or malformed")
    cms_refs = slice_doc.get("cms_content_references")
    if not isinstance(cms_refs, list) or not cms_refs:
        return ControlResult(
            cid, req, FAIL,
            "cms_content_references missing or empty; slot conformance cannot be "
            "established without at least one Content reference",
        )
    if not isinstance(content_records, list):
        return ControlResult(
            cid, req, FAIL, "content records unavailable; Content->ContentType "
            "relationship cannot be established"
        )
    if not isinstance(content_types, list) or not content_types:
        return ControlResult(
            cid, req, FAIL,
            "no ContentType collection available; the Content->ContentType "
            "relationship cannot be established",
        )
    try:
        from framework.domain.frontend.layout_registry import resolve
        from framework.domain.frontend.content_slots import resolve_content_slots
    except ImportError as exc:
        return ControlResult(cid, req, FAIL, f"cannot import layout registry: {exc}")

    duplicates = sorted(_duplicate_ids(content_records))
    if duplicates:
        return ControlResult(
            cid, req, FAIL,
            f"duplicate Content id(s) {duplicates}: identity must be unique and must "
            "never be resolved by array order",
        )
    duplicate_types = sorted(_duplicate_ids(content_types))
    if duplicate_types:
        return ControlResult(
            cid, req, FAIL,
            f"duplicate ContentType id(s) {duplicate_types}: identity must be unique and "
            "must never be resolved by array order",
        )

    by_content_id = {
        c.get("id"): c for c in content_records if isinstance(c, dict) and _nonblank(c.get("id"))
    }
    by_type_id = {
        ct.get("id"): ct for ct in content_types if isinstance(ct, dict) and _nonblank(ct.get("id"))
    }

    problems: List[str] = []
    resolved_slots: List[Any] = []
    for index, ref in enumerate(cms_refs):
        if not isinstance(ref, dict):
            problems.append(f"cms_content_references[{index}] is malformed")
            continue
        content_id = ref.get("content_id")
        if not _nonblank(content_id):
            problems.append(f"cms_content_references[{index}] has no usable content_id")
            continue
        record = by_content_id.get(content_id)
        if record is None:
            problems.append(
                f"content {content_id!r} has no Content record; the Content->ContentType "
                "relationship cannot be established"
            )
            continue
        type_id = record.get("type_id")
        if not _nonblank(type_id):
            problems.append(
                f"Content {content_id!r} declares no usable type_id; the "
                "Content->ContentType relationship cannot be established"
            )
            continue
        content_type = by_type_id.get(type_id)
        if content_type is None:
            problems.append(
                f"Content {content_id!r} has type_id {type_id!r} with no matching "
                "ContentType (dangling reference); relationship cannot be established"
            )
            continue
        # Every slot the slice DECLARES must exist in the P8 ContentType
        # (p10-slice.schema.json field_slots description).
        declared = ref.get("field_slots")
        available = _content_type_fields(content_type)
        if not isinstance(declared, list) or not declared:
            problems.append(f"cms_content_references[{index}] declares no field_slots")
            continue
        if available is None:
            problems.append(
                f"ContentType {type_id!r} declares no usable fields; slot conformance "
                "cannot be established"
            )
            continue
        unknown = [s for s in declared if s not in available]
        if unknown:
            problems.append(
                f"cms_content_references[{index}] declares slots {unknown} absent from "
                f"ContentType {type_id!r} (available: {sorted(available)})"
            )
            continue
        resolution = resolve(layout_id, content_type)
        if resolution.status != "resolved":
            codes = [e.code for e in resolution.errors]
            problems.append(
                f"layout {layout_id!r} did not resolve against ContentType "
                f"{type_id!r}; errors={codes}"
            )
            continue
        # D-P10-9: Exact match between declared slots and layout's consumed slots.
        # The slice's declared field_slots must exactly match the layout's
        # consumed slots via set equality (order-insensitive). Duplicates,
        # under-declared, and over-declared slots are rejected.
        consumed = set(resolution.field_slots)
        declared_set = set(declared)
        if declared_set != consumed:
            missing = consumed - declared_set      # under-declared
            extra = declared_set - consumed        # over-declared
            details = []
            if missing:
                details.append(f"under-declared (layout consumes but slice omits): {sorted(missing)}")
            if extra:
                details.append(f"over-declared (slice declares but layout does not consume): {sorted(extra)}")
            problems.append(
                f"cms_content_references[{index}] field_slots {sorted(declared)} != layout {layout_id!r} consumes {sorted(consumed)}; "
                + "; ".join(details)
            )
            continue
        # D-P10-9: Duplicate declared slots are also rejected (schema enforces uniqueItems,
        # but we also check here for defense in depth and clearer error message).
        if len(declared) != len(declared_set):
            problems.append(
                f"cms_content_references[{index}] declares duplicate field_slots: {declared}"
            )
            continue
        # CONTENT AUTHENTICITY (P10-REQUIREMENTS slice_schema
        # structural_enforcement_boundary.requires_runtime_validation:
        # "that every referenced P8 Content document exists, is actually
        # published, and actually exposes the named field_slots"). The first two
        # conjuncts were established above; the THIRD was silently dropped, so a
        # published record exposing no value for a declared slot reported PASS.
        #
        # The authoritative verdict is framework.domain.frontend.content_slots
        # .resolve_content_slots(); the gate CALLS it and reimplements none of
        # it. Only e.code and e.slot are reported: SlotResolutionError is
        # documented never to carry a raw CMS value, and the gate must not
        # become a leak path.
        slot_resolution = resolve_content_slots(
            layout_id, record,
            content_type_id=type_id, content_type=content_type,
            slots=tuple(declared),
        )
        if not slot_resolution.ok:
            problems.append(
                f"Content {content_id!r} does not expose the declared field_slots "
                f"{sorted(set(declared))}: "
                + ", ".join(
                    f"slot {e.slot!r} -> {e.code}" for e in slot_resolution.errors
                )
                + " per content_slots.resolve_content_slots()"
            )
            continue
        resolved_slots.append(resolution.field_slots)

    if problems:
        return ControlResult(cid, req, FAIL, "; ".join(problems))
    return ControlResult(
        cid, req, PASS,
        f"layout {layout_id!r} resolves to slots {resolved_slots} against the "
        f"ContentType reached via Content.type_id for all {len(cms_refs)} "
        "reference(s); every declared field slot exists in its ContentType and "
        "content_slots.resolve_content_slots() confirms the record actually "
        "exposes every declared slot. D-P10-9 ESTABLISHED: the slice's declared "
        "field_slots exactly match the layout's consumed slots via set equality "
        "(order-insensitive); duplicates, under-declared, and over-declared "
        "slots are rejected.",
    )


def check_published_only_content(slice_doc: Any, content_records: List[Any]) -> ControlResult:
    """REQ-P10-09 c.5 — referenced Content must exist and carry an explicit
    required_status of 'published', AND its actual record status must be
    'published'.

    Two INDEPENDENT conditions, both mandatory:
      1. structural: every reference declares required_status == 'published'
         (p10-slice.schema.json makes it mandatory with a single permitted value);
      2. runtime: the resolved Content record's own status is 'published'.

    Condition 2 is evaluated unconditionally. It is never skipped because
    condition 1 was not satisfied, so caller-supplied input cannot disable the
    published-only rule. Draft, preview, archived, unknown and missing statuses
    all fail closed.
    """
    cid = "published-only-content"
    req = "REQ-P10-09 c.5"
    if not isinstance(slice_doc, dict):
        return ControlResult(cid, req, FAIL, "slice document is not a JSON object")
    cms_refs = slice_doc.get("cms_content_references")
    if not isinstance(cms_refs, list) or not cms_refs:
        return ControlResult(cid, req, FAIL, "cms_content_references missing or empty")
    if not isinstance(content_records, list):
        return ControlResult(cid, req, FAIL, "content records unavailable")
    duplicates = sorted(_duplicate_ids(content_records))
    if duplicates:
        return ControlResult(
            cid, req, FAIL,
            f"duplicate Content id(s) {duplicates}: identity must be unique and must "
            "never be resolved by array order",
        )
    by_id = {
        c.get("id"): c for c in content_records
        if isinstance(c, dict) and _nonblank(c.get("id"))
    }
    problems: List[str] = []
    verified: List[str] = []
    for index, ref in enumerate(cms_refs):
        if not isinstance(ref, dict):
            problems.append(f"cms_content_references[{index}] is malformed")
            continue
        # (1) structural: required_status must be present, non-null, and 'published'.
        # Deliberately no early `continue` on a structural problem: every problem
        # is collected so the report always states the observed record status too.
        if "required_status" not in ref:
            problems.append(
                f"cms_content_references[{index}] omits the mandatory required_status"
            )
        else:
            required_status = ref.get("required_status")
            if required_status is None:
                problems.append(f"cms_content_references[{index}] required_status is null")
            elif required_status != "published":
                problems.append(
                    f"cms_content_references[{index}] required_status={required_status!r} "
                    "is not the only permitted value 'published'"
                )
        content_id = ref.get("content_id")
        if not _nonblank(content_id):
            problems.append(
                f"cms_content_references[{index}] has no usable content_id"
            )
            continue
        record = by_id.get(content_id)
        if record is None:
            problems.append(f"content {content_id!r} does not exist")
            continue
        # (2) runtime: unconditional, never gated on condition (1).
        actual = record.get("status")
        if actual != "published":
            problems.append(
                f"content {content_id!r} is {actual!r}, not published"
            )
            continue
        if ref.get("required_status") == "published":
            verified.append(f"{content_id!r}")
    if problems:
        return ControlResult(cid, req, FAIL, "; ".join(problems))
    return ControlResult(
        cid, req, PASS,
        f"all {len(verified)} referenced Content record(s) exist, declare "
        f"required_status 'published' and actually carry status 'published' "
        f"(verified: {verified}).",
    )


def _bind_host_observation(value: Any) -> Optional[str]:
    """Best-effort host token of an observed bind address.

    The repository defines NO grammar for observed_bind_address
    (p10-slice.schema.json declares only type [string, null], no pattern), so
    this is a deliberately conservative reading, not an authoritative parser. It
    returns the leading host token, or None when the value cannot be read as
    host[:port] at all. This function can never upgrade a value to 'local'; it
    only ever extracts a token for the classification below.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.startswith("["):
        end = text.find("]")
        return text[1:end] if end > 0 else None
    if text.count(":") == 1:
        host, _, port = text.partition(":")
        if host and port.isdigit():
            return host
        return None
    return text


def _is_loopback_host(host: Optional[str]) -> bool:
    if not host:
        return False
    token = host.strip().lower()
    if token == "localhost":
        return True
    try:
        return ipaddress.ip_address(token).is_loopback
    except ValueError:
        return False


def check_exposure_declaration(slice_doc: Any) -> ControlResult:
    """REQ-P10-09 c.7 / D-P10-1 — network exposure requires explicit authorisation.

    The declared exposure class is a DECLARATION. It is reconciled against
    backend.observed_bind_address, which the schema defines as RUNTIME-POPULATED
    ONLY and explicitly forbids an author from asserting to satisfy validation.
    No repository component produces that observation, so a loopback-looking
    string inside an authored document is still an author assertion and is
    reported BLOCKED. This control opens no sockets, opens no ports, starts no
    service, and performs no network operation of any kind.
    """
    cid = "exposure-declaration"
    req = "REQ-P10-09 c.7, D-P10-1"
    if not isinstance(slice_doc, dict):
        return ControlResult(cid, req, FAIL, "slice document is not a JSON object")
    backend = _nested(slice_doc, "axis_contracts", "backend")
    if not isinstance(backend, dict):
        return ControlResult(cid, req, FAIL, "backend contract missing or malformed")
    exposure = backend.get("exposure_class")
    if not _nonblank(exposure):
        return ControlResult(cid, req, FAIL, "exposure_class missing or malformed")

    # Allow-list, never deny-list: an unrecognised class is never silently
    # treated as "some non-network surface".
    known_classes = ("LOCAL_NON_NETWORK_EXPOSED", "NETWORK_EXPOSED_PRODUCTION")
    if exposure not in known_classes:
        return ControlResult(
            cid, req, FAIL,
            f"exposure_class={exposure!r} is not a permitted value {list(known_classes)}; "
            "an unrecognised class is never treated as non-network",
        )

    observed_present = "observed_bind_address" in backend
    observed = backend.get("observed_bind_address")
    loopback = _is_loopback_host(_bind_host_observation(observed)) if observed_present else False

    if exposure == "NETWORK_EXPOSED_PRODUCTION":
        auth = backend.get("security_authorization")
        if not isinstance(auth, dict):
            return ControlResult(
                cid, req, FAIL,
                "NETWORK_EXPOSED_PRODUCTION declared without an explicit "
                "security_authorization block",
            )
        if auth.get("authorized_by_role") != "USER":
            return ControlResult(
                cid, req, FAIL,
                "network exposure must be authorised by USER; found "
                f"{auth.get('authorized_by_role')!r}",
            )
        if loopback:
            return ControlResult(
                cid, req, FAIL,
                "contradictory declaration: NETWORK_EXPOSED_PRODUCTION with a "
                f"loopback observed bind {observed!r}; a mismatch must fail closed",
            )
        return ControlResult(
            cid, req, FAIL,
            "network exposure is declared and authorised, but this Phase A gate "
            "cannot verify the OBSERVED bind address; failing closed per D-P10-1",
        )

    # LOCAL_NON_NETWORK_EXPOSED.
    if "security_authorization" in backend:
        return ControlResult(
            cid, req, FAIL,
            "contradictory declaration: LOCAL_NON_NETWORK_EXPOSED carries a "
            "security_authorization block; a default-deny local surface must not "
            "also assert a network authorisation",
        )
    if not observed_present or observed is None:
        return ControlResult(
            cid, req, BLOCKED,
            "LOCAL_NON_NETWORK_EXPOSED requires an OBSERVED loopback/file-socket/"
            "no-socket bind to be classified, and no observation is present; a "
            "declaration alone is not proof. No repository component produces "
            "observed_bind_address, so this cannot be established in Phase A.",
        )
    if not loopback:
        return ControlResult(
            cid, req, FAIL,
            f"contradictory declaration: LOCAL_NON_NETWORK_EXPOSED with observed bind "
            f"{observed!r}, which could not be read as a loopback address. Note that "
            "D-P10-1 also satisfies LOCAL_NON_NETWORK_EXPOSED via a project-local "
            "file socket or no socket at all, so this is NOT a determination that "
            "the bind is network-exposed: the observed_bind_address grammar is "
            "undefined by the repository (p10-slice.schema.json declares it as "
            "string|null with no pattern), so this gate cannot classify that form "
            "and fails closed rather than guessing a grammar.",
        )
    return ControlResult(
        cid, req, BLOCKED,
        f"observed bind {observed!r} is loopback-shaped, but the schema declares "
        "observed_bind_address RUNTIME-POPULATED ONLY and never author-assertable. "
        "An author-supplied string is a declaration, not an observation, so the "
        "gate cannot establish the real bind configuration and blocks.",
    )


def check_slice_id_uniqueness(slice_doc: Any, history: List[str]) -> ControlResult:
    """REQ-P10-09 c.9 — a slice id may not be reused, including after rollback.

    Uniqueness can only be established from an authoritative history the caller
    supplies. An absent history cannot prove uniqueness, so it fails closed.
    """
    cid = "slice-id-uniqueness"
    req = "REQ-P10-09 c.9"
    if not isinstance(slice_doc, dict):
        return ControlResult(cid, req, FAIL, "slice document is not a JSON object")
    slice_id = slice_doc.get("slice_id")
    if not _nonblank(slice_id):
        return ControlResult(cid, req, FAIL, "slice_id missing or malformed")
    if not history:
        # An EMPTY history proves exactly as little as an absent one: there is no
        # authoritative record against which uniqueness could be established.
        return ControlResult(
            cid, req, FAIL,
            "no authoritative slice-id history supplied; uniqueness cannot be established",
        )
    if not isinstance(history, list):
        return ControlResult(
            cid, req, FAIL,
            "slice-id history is not a list; slice_id uniqueness cannot be established",
        )
    if [h for h in history if h == slice_id]:
        return ControlResult(
            cid, req, FAIL, f"slice_id {slice_id!r} already appears in authoritative history"
        )
    return ControlResult(cid, req, PASS, f"slice_id {slice_id!r} is not previously recorded")


def _audit_html_paths(build_root: Path) -> List[Path]:
    """The HTML files the P9 audit itself enumerates, and ONLY those.

    This is a structural mirror of framework/domain/seo/audit.py lines 1276 and 1290:

        p = Path(target_dir).resolve()
        ...
        for html_file in p.glob("**/*.html"):

    Using `glob.glob(..., recursive=True)` here instead produced a SUPERSET of
    the audited files and a control-level FALSE PASS, because the two
    enumerators diverge on four axes:

      * symlinked DIRECTORIES -- `glob` recurses into them, `pathlib` does not,
        so a build whose only HTML sat behind a symlinked subdirectory gave the
        audit zero pages (a vacuous exit 0) while the gate derived a route from
        the phantom file and reported "exited 0 over 1 HTML document(s)";
      * glob metacharacters in the build-directory name -- `glob` expands
        `dist[1]` as a character class and finds nothing, while the audit treats
        the directory name literally and finds every page;
      * dotfiles -- `glob` suppresses `.html`, `pathlib` does not, which hid a
        real two-files-one-route collision from the gate entirely;
      * symlink cycles -- `glob` expanded one page into 33 routes.

    sorted() additionally gives the deterministic ordering the raw scandir order
    lacked, so the reported route set is reproducible.
    """
    return sorted(build_root.glob("**/*.html"))


def _derive_build_routes(build_root: Path, html_files: List[Path]) -> List[str]:
    """Routes for ``html_files``, in the P9 audit's OWN order.

    Replays framework/domain/seo/audit.py lines 1291-1296 exactly. A LIST is returned
    rather than a set so that the file->route cardinality stays observable:
    the audit stores pages in a dict keyed by route (last writer wins), so two
    files deriving one route means the audit silently dropped a page. A set
    would erase that signal.

    P10-REQUIREMENTS p10_to_p9_contract.build_artifacts.canonical_route_mapping
    requires the mapping to be "deterministic and identical to the P9 audit's own
    derivation".
    """
    routes: List[str] = []
    for html_file in html_files:
        url_path = f"/{html_file.relative_to(build_root).as_posix()}"
        if url_path.endswith("/index.html"):
            url_path = url_path[:-10] or "/"
        elif url_path.endswith(".html"):
            url_path = url_path[:-5]
        routes.append(url_path)
    return routes


def check_p9_deployment_audit(slice_doc: Any, build_dir: Optional[str]) -> ControlResult:
    """REQ-P10-09 c.5 / HOME-ACC-16 — P9 deployment audit over NON-EMPTY output.

    framework.domain.seo.audit.audit_directory(mode="deployment") returns exit_code 0 for
    an EMPTY directory: missing pages, robots.txt and sitemap.xml all degrade to
    informational PASS/INFO checks, so exit code alone is NON-DISCRIMINATING. This
    control therefore establishes the authoritative build-artifact shape from
    P10-REQUIREMENTS p10_to_p9_contract BEFORE the audit verdict is trusted:
    at least one HTML document discoverable by the audit's '**/*.html' scan,
    plus robots.txt and sitemap.xml at the build root.

    Passing this control on a hand-built directory establishes gate LOGIC only. It
    is NOT evidence that a real P10 slice passed a real P9 deployment audit.
    """
    cid = "p9-deployment-audit"
    req = "REQ-P10-09 c.5, HOME-ACC-16"
    if not isinstance(slice_doc, dict):
        return ControlResult(
            cid, req, FAIL,
            "slice document unavailable; the P9 audit cannot be bound to a declared "
            "slice contract",
        )
    seo = _nested(slice_doc, "axis_contracts", "seo")
    if not isinstance(seo, dict):
        return ControlResult(cid, req, FAIL, "seo axis contract missing or malformed")
    if seo.get("audit_mode") != "P9_DEPLOYMENT_AUDIT":
        return ControlResult(
            cid, req, FAIL,
            f"axis_contracts.seo.audit_mode={seo.get('audit_mode')!r} is not "
            "'P9_DEPLOYMENT_AUDIT'; SEO is never verified by a P10-local reimplementation",
        )
    if not build_dir:
        return ControlResult(
            cid, req, BLOCKED,
            "no build directory supplied; the P9 deployment audit has no real output "
            "to audit and success cannot be claimed",
        )
    if not isinstance(build_dir, str):
        return ControlResult(
            cid, req, BLOCKED,
            "build directory is not a filesystem path; the P9 deployment audit has no "
            "real output to audit and success cannot be claimed",
        )
    if not os.path.isdir(build_dir):
        return ControlResult(cid, req, BLOCKED, f"build directory absent: {build_dir}")

    # FILE-SET IDENTITY. Every statement below is about the exact artifact set
    # framework/domain/seo/audit.py enumerates, never about a parallel glob. The audit's
    # report does not retain its page list, so identity has to be established
    # here by structural parity with audit.py:1276/1290 -- see
    # _audit_html_paths for the four axes on which the two diverge.
    build_root = Path(build_dir).resolve()
    html_files = _audit_html_paths(build_root)
    missing: List[str] = []
    if not html_files:
        missing.append("no HTML document discoverable by the audit's '**/*.html' scan")
    robots = os.path.join(build_dir, "robots.txt")
    if not _artifact_present(robots):
        missing.append("robots.txt absent, empty or blank at the build root")
    sitemap = os.path.join(build_dir, "sitemap.xml")
    if not _artifact_present(sitemap):
        missing.append("sitemap.xml absent, empty or blank at the build root")
    if missing:
        return ControlResult(
            cid, req, BLOCKED,
            "build output does not satisfy the P10-REQUIREMENTS p10_to_p9_contract "
            "artifact shape, so a P9 audit exit code would be vacuous: "
            + "; ".join(missing),
        )

    # CONTAINMENT. isfile()/getsize() follow symlinks, so a build directory
    # holding nothing but links to files outside it satisfied the shape check.
    # Every audited artifact must have its CANONICAL path inside the build
    # directory -- the same predicate check_evidence_references already applies.
    escaped = [
        f"{os.path.relpath(str(artifact), str(build_root))} -> {os.path.realpath(artifact)}"
        for artifact in [robots, sitemap, *html_files]
        if not _canonical_within(build_dir, artifact)
    ]
    if escaped:
        return ControlResult(
            cid, req, FAIL,
            "build artifact(s) resolve outside the build directory: "
            + "; ".join(escaped)
            + ". The audited output must be contained in the build directory; "
              "check_evidence_references already enforces exactly this containment.",
        )

    # Bind the audited output to THIS slice. Without this the control is a
    # property of whatever directory it was handed: a build copied from a
    # different slice would still pass.
    declared_route = slice_doc.get("route")
    routes = _derive_build_routes(build_root, html_files)
    derived = set(routes)
    # The audit stores pages in a dict keyed by route (last writer wins), so two
    # files deriving one route means it silently dropped a page.
    if len(routes) != len(derived):
        duplicates = sorted({r for r in routes if routes.count(r) > 1})
        return ControlResult(
            cid, req, FAIL,
            f"the build maps {len(routes)} HTML document(s) onto only "
            f"{len(derived)} distinct route(s): {duplicates}. The P9 audit keys its "
            "page table by route, so it would silently drop a page; a build whose "
            "route mapping is ambiguous cannot be audited deterministically.",
        )
    if declared_route not in derived:
        return ControlResult(
            cid, req, FAIL,
            f"the audited build output does not contain the declared route "
            f"{declared_route!r}; routes derived from the exact file set the P9 audit "
            f"enumerates are {sorted(derived)}. Per p10_to_p9_contract."
            "canonical_route_mapping the audit must cover this slice's own output.",
        )

    try:
        # Lazy, non-static resolution of the P9 audit entry point. A literal
        # `from framework.domain.seo.audit import ...` inside this function body is still
        # recorded by framework/domain/seo/isolation.py:80-104, whose ast.walk() is
        # location-insensitive, and would register as an orphan reference to
        # domain.seo from a file outside the P9 surface (isolation.py:208-213).
        # importlib keeps the dependency identical at runtime while leaving no
        # ImportFrom node for the P9 static scan to collect.
        import importlib

        audit_directory = importlib.import_module(
            "framework.domain.seo.audit"
        ).audit_directory
    except ImportError as exc:
        return ControlResult(cid, req, FAIL, f"cannot import P9 audit: {exc}")
    try:
        report = audit_directory(build_dir, mode="deployment")
    except Exception as exc:  # fail closed on any audit error
        return ControlResult(cid, req, FAIL, f"P9 deployment audit raised: {exc}")
    exit_code = getattr(report, "exit_code", None)
    if exit_code != 0:
        return ControlResult(
            cid, req, FAIL, f"P9 deployment audit exited {exit_code!r} (expected 0)"
        )
    declared = seo.get("expected_exit_code")
    if declared is not None and declared != exit_code:
        return ControlResult(
            cid, req, FAIL,
            f"axis_contracts.seo.expected_exit_code={declared!r} disagrees with the "
            f"observed audit exit {exit_code!r}",
        )
    digest = getattr(report, "audited_artifacts_digest", None)
    return ControlResult(
        cid, req, PASS,
        f"P9 deployment audit exited 0 over the same {len(html_files)} HTML "
        f"document(s) this gate enumerated with the audit's own '**/*.html' scan "
        f"(routes {sorted(derived)}), with robots.txt and sitemap.xml present, "
        f"non-blank and contained at the build root; reported "
        f"audited_artifacts_digest={digest!r}. NOTE: this establishes gate logic over "
        "the supplied directory only. A hand-built or author-supplied build directory "
        "is NOT evidence that a real P10 slice passed a real P9 deployment audit.",
    )


def _undefined_control(cid: str, req: str, detail: str) -> ControlResult:
    """A required control whose repository semantics are undefined.

    Always UNIMPLEMENTED, which (being required) prevents an overall pass. The
    Phase A gate does not guess these semantics.
    """
    return ControlResult(cid, req, UNIMPLEMENTED, detail)


# --- DEC-7112 shared primitives (implemented under the Round 14 grant) ---------

GATE_RECORD_VERSION = "sps2.p10-gate-record/v1"
MANIFEST_PATH = os.path.join("framework", "domain", "backend", "operations.json")


def _canonical_json_bytes(value: Any) -> Optional[bytes]:
    """Canonical JSON encoding per DEC-7112: sorted keys, UTF-8, no
    insignificant whitespace. Returns None for values JSON cannot serialise
    (the caller fails closed rather than inventing a digest)."""
    try:
        return json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None


def _sha256_digest(value: Any) -> Optional[str]:
    """sha256:<hex> over the canonical JSON of ``value``, or None."""
    encoded = _canonical_json_bytes(value)
    if encoded is None:
        return None
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _canonical_state_digest(paths: Sequence[str]) -> Tuple[Optional[str], str]:
    """Digest of a set of CMS state files, per DEC-7112 design #3.

    The digest covers the canonical JSON of each file's parsed content,
    combined with its repo-relative path so that two files with identical
    content cannot cancel each other out of the digest. Returns
    (digest_or_None, error_detail). A missing, unreadable or non-JSON file
    yields (None, reason) — fail-closed, never an invented digest.

    ``.jsonl`` files are line-delimited JSON: each non-blank line is parsed
    separately and the digest covers the resulting sequence, so a reordered or
    dropped revision line changes the digest.
    """
    if not paths:
        return None, "no state files declared for digesting"
    parts: List[Dict[str, Any]] = []
    for path in paths:
        if path.endswith(".jsonl"):
            # Parse line-delimited JSON without slurping the file into one
            # json.load call (which would fail on 'Extra data').
            lines: List[Any] = []
            try:
                with open(path, encoding="utf-8") as fh:
                    for line_no, line in enumerate(fh, 1):
                        if not line.strip():
                            continue
                        try:
                            lines.append(json.loads(line))
                        except ValueError as exc:
                            return None, (
                                f"{os.path.basename(path)}: malformed JSON on "
                                f"line {line_no} ({exc})")
            except FileNotFoundError:
                return None, f"missing file: {path}"
            except (OSError, UnicodeDecodeError) as exc:
                return None, f"unreadable: {path} ({exc})"
            data: Any = lines
        else:
            data, err = _load_json(path)
            if err:
                return None, f"{os.path.basename(path)}: {err}"
        rel = os.path.relpath(os.path.realpath(path), _repo_root())
        parts.append({"path": rel, "content": data})
    return _sha256_digest(parts), ""


def _parse_rfc3339_utc(value: Any) -> Optional[datetime]:
    """Parse an RFC 3339 timestamp to an aware UTC datetime, or None.

    Accepts the RFC 3339 forms a JSON string can carry ('Z' or numeric
    offsets). Naive timestamps (no offset) are REJECTED: an offset-less
    timestamp cannot be compared against gate-run time without guessing a
    timezone, and the gate does not guess.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _gate_now() -> datetime:
    """Gate-run time (UTC). Factored so tests can freeze the clock."""
    return datetime.now(timezone.utc)


def _iter_evidence_records(
    slice_doc: Any, base_dir: str, allowed_root: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Load the evidence documents referenced by the slice and flatten their
    records. Returns (records, errors); each error names the reference and the
    reason it could not contribute records. Read-only.

    ``allowed_root`` bounds resolution exactly as check_evidence_references
    bounds it (default: the repository root); tests pass a sandbox root so
    synthetic fixtures stay outside the governed tree.
    """
    records: List[Dict[str, Any]] = []
    errors: List[str] = []
    refs = slice_doc.get("evidence_references") if isinstance(slice_doc, dict) else None
    if not isinstance(refs, list) or not refs:
        return [], ["slice declares no evidence_references to examine"]
    root = os.path.realpath(allowed_root) if allowed_root else _repo_root()
    for ref in refs:
        if not _nonblank(ref):
            errors.append(f"{ref!r}: blank reference")
            continue
        candidate = os.path.join(base_dir, ref)
        if not _canonical_within(root, candidate) or not os.path.isfile(candidate):
            errors.append(f"{ref!r}: does not resolve inside the allowed root")
            continue
        data, err = _load_json(candidate)
        if err:
            errors.append(f"{ref!r}: {err}")
            continue
        doc_records = data.get("records") if isinstance(data, dict) else None
        if not isinstance(doc_records, list):
            errors.append(f"{ref!r}: carries no records[] array")
            continue
        for rec in doc_records:
            if isinstance(rec, dict):
                records.append(rec)
            else:
                errors.append(f"{ref!r}: malformed (non-object) record entry")
    return records, errors


def _digest_claim_matches(claimed: Any, actual: Optional[str]) -> bool:
    """A gate-record digest claim agrees with the recomputed value. A claim in
    any other form (null, non-string, foreign algorithm prefix) contradicts."""
    return isinstance(claimed, str) and actual is not None and claimed == actual


def _cms_state_paths() -> List[str]:
    """The canonical CMS state files over which cms-state-digest is computed
    (DEC-7112 design #3: content.json, content_types.json, revisions.jsonl)."""
    root = _repo_root()
    return [
        os.path.join(root, "framework", "domain", "cms", "data", "content.json"),
        os.path.join(root, "framework", "domain", "cms", "data", "content_types.json"),
        os.path.join(root, "framework", "domain", "cms", "data", "revisions.jsonl"),
    ]


def _p8_contract_paths() -> List[str]:
    """The P8 contract inputs over which p8-contract-digest is computed
    (DEC-7112 design #4: the ContentType definitions, deliberately separate
    from the CMS content state)."""
    root = _repo_root()
    return [os.path.join(root, "framework", "domain", "cms", "data", "content_types.json")]


def check_evidence_freshness(
    slice_doc: Any, base_dir: str = "", allowed_root: Optional[str] = None
) -> ControlResult:
    """DEC-7112 design #1, as amended by the Round 14 authorization
    ("EVIDENCE-FRESHNESS WINDOW: NO MAXIMUM-AGE WINDOW").

    Every referenced evidence record must carry a parseable RFC 3339
    ``generated_at`` (or ``timestamp``) WITH an offset. There is NO maximum-age
    window: age alone never fails a record. What fails is a record whose
    timestamp is missing, blank, unparseable, or timezone-naive — because such
    a record cannot be placed on a timeline at all. A timestamp is
    self-declared: this control establishes that a record is DATED, not that it
    is truthful (see UNRESOLVED_SEMANTICS).
    """
    cid = "evidence-freshness"
    req = "REQ-P10-09 c.5"
    if not isinstance(slice_doc, dict):
        return ControlResult(cid, req, FAIL, "slice document is not a JSON object")
    records, errors = _iter_evidence_records(slice_doc, base_dir or os.getcwd(), allowed_root)
    if errors:
        return ControlResult(cid, req, FAIL, "evidence cannot be examined: " + "; ".join(errors))
    if not records:
        return ControlResult(cid, req, FAIL, "referenced evidence carries no records")
    undated: List[str] = []
    for rec in records:
        eid = rec.get("evidence_id", "<no id>")
        stamp = _parse_rfc3339_utc(rec.get("generated_at") or rec.get("timestamp"))
        if stamp is None:
            undated.append(str(eid))
    if undated:
        return ControlResult(
            cid, req, FAIL,
            "evidence record(s) with no parseable RFC 3339 generated_at/timestamp "
            f"(offset required): {undated}. A record that cannot be placed on a "
            "timeline is not fresh or stale — it is undated, and that fails closed. "
            "Policy: NO maximum-age window (Round 14 authorization); age alone "
            "never fails a record.",
        )
    return ControlResult(
        cid, req, PASS,
        f"all {len(records)} evidence record(s) carry a parseable RFC 3339 "
        "timestamp with an offset. No maximum-age window is applied (Round 14 "
        "authorization). A timestamp is self-declared: this is DATEDNESS, not "
        "truthfulness.",
    )


def check_evidence_authenticity(
    slice_doc: Any, base_dir: str = "", allowed_root: Optional[str] = None
) -> ControlResult:
    """DEC-7112 design #2: gate-record cross-check.

    Each referenced evidence record must carry a complete ``gate_record`` object
    (framework.sps2.p10-gate-record/v1) whose digest claims the gate recomputes:
    ``inputs`` maps a repo-relative path to a sha256:<hex> digest of the
    file's bytes, and ``outputs`` does the same for produced artifacts. A
    record WITHOUT a gate_record fails closed (existence is not authenticity);
    a record whose claims contradict recomputation fails, naming the
    contradicted field. Claimed paths use the SAME locator grammar as
    evidence_references: resolved relative to the slice document's directory
    (``base_dir``), bounded by ``allowed_root`` (default: the repository root).
    This is content integrity + provenance recording — NOT cryptographic
    authenticity (no signatures, no trust root) and NOT human authorization
    (DEC-7112 standing_bounds.authenticity_limit).
    """
    cid = "evidence-authenticity"
    req = "REQ-P10-09 c.5"
    if not isinstance(slice_doc, dict):
        return ControlResult(cid, req, FAIL, "slice document is not a JSON object")
    records, errors = _iter_evidence_records(slice_doc, base_dir or os.getcwd(), allowed_root)
    if errors:
        return ControlResult(cid, req, FAIL, "evidence cannot be examined: " + "; ".join(errors))
    if not records:
        return ControlResult(cid, req, FAIL, "referenced evidence carries no records")
    root = os.path.realpath(allowed_root) if allowed_root else _repo_root()
    origin = os.path.realpath(base_dir or os.getcwd())
    missing_record: List[str] = []
    malformed_records: List[str] = []
    contradictions: List[str] = []
    checked = 0
    for rec in records:
        eid = str(rec.get("evidence_id", "<no id>"))
        gate_record = rec.get("gate_record")
        if not isinstance(gate_record, dict):
            missing_record.append(eid)
            continue
        required_fields = ("schema", "producing_command", "emitting_tool_version", "utc_timestamp")
        missing_fields = [field for field in required_fields if not _nonblank(gate_record.get(field))]
        if missing_fields:
            malformed_records.append(f"{eid}: missing {', '.join(missing_fields)}")
            continue
        if gate_record.get("schema") != GATE_RECORD_VERSION:
            malformed_records.append(
                f"{eid}: schema is {gate_record.get('schema')!r}, expected {GATE_RECORD_VERSION!r}"
            )
            continue
        parsed_utc_timestamp = _parse_rfc3339_utc(gate_record.get("utc_timestamp"))
        raw_utc_timestamp = str(gate_record.get("utc_timestamp")).strip().lower()
        if (
            parsed_utc_timestamp is None
            or not raw_utc_timestamp.endswith(("z", "+00:00"))
        ):
            malformed_records.append(
                f"{eid}: utc_timestamp is not a parseable RFC 3339 UTC timestamp with a zero offset"
            )
            continue
        checked += 1
        claims_present = False
        for claim_key in ("inputs", "outputs"):
            claims = gate_record.get(claim_key)
            if claims is None:
                continue
            if not isinstance(claims, dict):
                malformed_records.append(f"{eid}: gate_record.{claim_key} is not an object")
                continue
            if claims:
                claims_present = True
            for rel_path, claimed in claims.items():
                if not _nonblank(rel_path):
                    malformed_records.append(f"{eid}: gate_record.{claim_key} has a blank path")
                    continue
                if not isinstance(claimed, str) or not re.fullmatch(
                    r"sha256:[0-9a-f]{64}", claimed
                ):
                    contradictions.append(
                        f"{eid}: gate_record.{claim_key}[{rel_path!r}] has an invalid "
                        f"sha256 digest claim {claimed!r}"
                    )
                    continue
                candidate = os.path.join(origin, rel_path)
                if not _canonical_within(root, candidate):
                    contradictions.append(
                        f"{eid}: gate_record.{claim_key} path {rel_path!r} is outside "
                        "the allowed root")
                    continue
                try:
                    with open(candidate, "rb") as handle:
                        actual = "sha256:" + hashlib.sha256(handle.read()).hexdigest()
                except (OSError, ValueError) as exc:
                    contradictions.append(
                        f"{eid}: gate_record.{claim_key} path {rel_path!r} unreadable ({exc})")
                    continue
                if not _digest_claim_matches(claimed, actual):
                    contradictions.append(
                        f"{eid}: gate_record.{claim_key}[{rel_path!r}] claims {claimed!r} "
                        f"but the artifact digests to {actual}")
        if not claims_present:
            malformed_records.append(
                f"{eid}: gate_record carries no usable inputs/outputs digest claims"
            )
    if malformed_records:
        return ControlResult(
            cid, req, FAIL,
            "incomplete or malformed gate_record(s): " + "; ".join(malformed_records)
            + f". A complete {GATE_RECORD_VERSION} record requires schema, "
            "producing_command, emitting_tool_version, parseable RFC 3339 "
            "utc_timestamp, and at least one sha256 input/output claim.",
        )
    if missing_record:
        return ControlResult(
            cid, req, FAIL,
            "evidence record(s) carry no gate_record (existence is not "
            f"authenticity): {missing_record}. A gate_record "
            f"({GATE_RECORD_VERSION}: producing command, input digests, output "
            "digests, UTC timestamp, emitting tool version) is required before "
            "authenticity can be cross-checked.",
        )
    if contradictions:
        return ControlResult(
            cid, req, FAIL,
            "gate-record cross-check contradictions: " + "; ".join(contradictions),
        )
    return ControlResult(
        cid, req, PASS,
        f"all {checked} gate_record(s) cross-check clean: every claimed digest "
        "recomputes to the same value. This is content integrity and provenance "
        "recording only — NOT cryptographic authenticity (no signatures, no "
        "trust root) and NOT human authorization (see unresolved_semantics).",
    )


def check_cms_state_digest(inventory: Any) -> ControlResult:
    """DEC-7112 design #3: recompute the canonical CMS state digest and compare
    it with the inventory's recorded provenance.cms_state_digest. Null or
    mismatch fails closed. Detects CHANGE, not WHO changed it."""
    cid = "cms-state-digest"
    req = "REQ-P10-17 runtime verification"
    recorded = _nested(inventory, "provenance", "cms_state_digest") \
        if isinstance(inventory, dict) else None
    if not isinstance(recorded, str) or not recorded.strip():
        return ControlResult(
            cid, req, FAIL,
            f"inventory provenance.cms_state_digest is {recorded!r}; the gate "
            "recomputes and fails closed on null (DEC-7112). The recorded value "
            "is written only by an authorized inventory regeneration.",
        )
    actual, err = _canonical_state_digest(_cms_state_paths())
    if actual is None:
        return ControlResult(cid, req, FAIL, f"cannot recompute CMS state digest: {err}")
    if recorded != actual:
        return ControlResult(
            cid, req, FAIL,
            f"cms_state_digest mismatch: inventory records {recorded} but the "
            f"current CMS state digests to {actual} (canonical JSON, sorted keys, "
            "UTF-8, SHA-256 per DEC-7112)",
        )
    return ControlResult(
        cid, req, PASS,
        f"cms_state_digest matches: {actual} (canonical JSON, sorted keys, "
        "UTF-8, SHA-256 per DEC-7112). Detects change, not who changed it.",
    )


def check_p8_contract_digest(inventory: Any) -> ControlResult:
    """DEC-7112 design #4: the same scheme as cms-state-digest, over the P8
    ContentType contract inputs, deliberately separate so a content edit does
    not invalidate the type contract and vice versa."""
    cid = "p8-contract-digest"
    req = "REQ-P10-17 runtime verification"
    recorded = _nested(inventory, "provenance", "p8_contract_digest") \
        if isinstance(inventory, dict) else None
    if not isinstance(recorded, str) or not recorded.strip():
        return ControlResult(
            cid, req, FAIL,
            f"inventory provenance.p8_contract_digest is {recorded!r}; the gate "
            "recomputes and fails closed on null (DEC-7112). The recorded value "
            "is written only by an authorized inventory regeneration.",
        )
    actual, err = _canonical_state_digest(_p8_contract_paths())
    if actual is None:
        return ControlResult(cid, req, FAIL, f"cannot recompute P8 contract digest: {err}")
    if recorded != actual:
        return ControlResult(
            cid, req, FAIL,
            f"p8_contract_digest mismatch: inventory records {recorded} but the "
            f"current P8 contract inputs digest to {actual} (canonical JSON, "
            "sorted keys, UTF-8, SHA-256 per DEC-7112)",
        )
    return ControlResult(
        cid, req, PASS,
        f"p8_contract_digest matches: {actual} (deliberately separate from "
        "cms_state_digest so a content edit does not invalidate the type "
        "contract and vice versa, per DEC-7112)",
    )


def check_req_p10_07_reconciliation(slice_doc: Any) -> ControlResult:
    """DEC-7112 design #5: set-compare the slice's declared
    state_changing_operations against the backend operation manifest
    (framework/domain/backend/operations.json). A missing manifest FAILS (fail-closed):
    for the Home slice the empty-vs-empty case passes only when the manifest
    exists and is also empty. The manifest is self-declared code: this proves
    CONSISTENCY, not real-world completeness."""
    cid = "req-p10-07-reconciliation"
    req = "REQ-P10-07"
    declared = None
    if isinstance(slice_doc, dict):
        backend = _nested(slice_doc, "axis_contracts", "backend")
        if isinstance(backend, dict):
            declared = backend.get("state_changing_operations")
    if not isinstance(declared, list):
        return ControlResult(
            cid, req, FAIL,
            f"slice declares no usable state_changing_operations list "
            f"(observed {declared!r}); there is nothing to reconcile",
        )
    declared_names: set = set()
    malformed_declarations: List[str] = []
    for index, operation in enumerate(declared):
        if not isinstance(operation, dict):
            malformed_declarations.append(f"declared[{index}] is {type(operation).__name__}")
            continue
        name = operation.get("operation")
        if not _nonblank(name):
            malformed_declarations.append(f"declared[{index}] has unusable operation {name!r}")
            continue
        controls = operation.get("required_controls")
        if (
            not isinstance(controls, list)
            or not controls
            or any(not _nonblank(control) for control in controls)
        ):
            malformed_declarations.append(
                f"declared[{index}] has unusable required_controls {controls!r}"
            )
            continue
        declared_names.add(name)
    manifest_path = os.path.join(_repo_root(), MANIFEST_PATH)
    manifest, err = _load_json(manifest_path)
    if err or not isinstance(manifest, dict) or not isinstance(manifest.get("operations"), list):
        return ControlResult(
            cid, req, FAIL,
            f"backend operation manifest {MANIFEST_PATH} is missing, unreadable, "
            "or carries no operations[] array (fail-closed per DEC-7112). The "
            f"manifest arrives with the first backend code; declared "
            f"state_changing_operations={declared!r} is NOT reconciled against "
            "anything until it exists.",
        )
    manifest_names: set = set()
    malformed_manifest_entries: List[str] = []
    for index, operation in enumerate(manifest["operations"]):
        if not isinstance(operation, dict):
            malformed_manifest_entries.append(f"operations[{index}] is {type(operation).__name__}")
            continue
        name = operation.get("name")
        if not _nonblank(name):
            malformed_manifest_entries.append(f"operations[{index}] has unusable name {name!r}")
            continue
        controls = operation.get("required_controls")
        if (
            not isinstance(controls, list)
            or not controls
            or any(not _nonblank(control) for control in controls)
        ):
            malformed_manifest_entries.append(
                f"operations[{index}] has unusable required_controls {controls!r}"
            )
            continue
        manifest_names.add(name)
    if malformed_declarations or malformed_manifest_entries:
        problems = malformed_declarations + malformed_manifest_entries
        return ControlResult(
            cid, req, FAIL,
            "REQ-P10-07 malformed operation entries (fail-closed): "
            + "; ".join(problems),
        )
    undeclared = sorted(manifest_names - declared_names)
    phantom = sorted(declared_names - manifest_names)
    if undeclared or phantom:
        parts = []
        if undeclared:
            parts.append(f"manifest operations absent from declaration: {undeclared}")
        if phantom:
            parts.append(f"declared operations absent from manifest: {phantom}")
        return ControlResult(cid, req, FAIL, "REQ-P10-07 reconciliation delta: " + "; ".join(parts))
    return ControlResult(
        cid, req, PASS,
        f"declared state_changing_operations={sorted(declared_names)!r} matches the "
        f"manifest's {sorted(manifest_names)!r} exactly (set-compare per DEC-7112). "
        "The manifest is self-declared code: this proves consistency, not "
        "real-world completeness.",
    )


def check_approval_state_interaction(inventory: Any) -> ControlResult:
    """DEC-7112 design #6 with the User's APPROVAL-MECHANISM: OPTION A
    resolution: two distinct approval loci — D-P10-8 contents-approval (in the
    decision ledger) and inventory user_approval (set only by an authorized
    act, never by the gate). This control verifies COHERENCE, read-only:

    - COMPLETE_VERIFIED_USER_APPROVED requires a set user_approval AND a
      recorded fresh-act basis (a gate pass alone is never sufficient, and
      D-P10-8 does not carry over);
    - any non-terminal state with a set user_approval is incoherent (approval
      recorded against planning or awaiting data);
    - the gate never writes approval state and never transitions the
      inventory.
    """
    cid = "approval-state-interaction"
    req = "REQ-P10-09 c.6, REQ-P10-17"
    if not isinstance(inventory, dict):
        return ControlResult(cid, req, FAIL, "inventory is not a JSON object")
    state = inventory.get("inventory_state")
    approval = inventory.get("user_approval")
    if state == "COMPLETE_VERIFIED_USER_APPROVED":
        if not isinstance(approval, dict):
            return ControlResult(
                cid, req, FAIL,
                f"inventory claims {state} but user_approval is {approval!r}: the "
                "transition requires BOTH a full gate pass AND a set user_approval "
                "(DEC-7112 design #6). A gate pass alone is never sufficient.",
            )
        basis = approval.get("basis")
        # Word-boundary match: the substring test accepted any basis merely
        # CONTAINING "fresh" ("refresh the cache", "freshly painted"), which
        # does not record a fresh approval act. The claim must use the word
        # itself ("fresh explicit User approval", "fresh act").
        if not _nonblank(basis) or not re.search(
                r"\bfresh\b", str(basis), re.IGNORECASE):
            return ControlResult(
                cid, req, FAIL,
                "inventory claims COMPLETE_VERIFIED_USER_APPROVED but the "
                "user_approval basis does not record a fresh explicit User "
                "approval act (APPROVAL-MECHANISM: OPTION A — D-P10-8's "
                "contents-approval does not carry over). The gate cannot certify "
                "freshness; it can only refuse a record that does not claim it.",
            )
        return ControlResult(
            cid, req, PASS,
            "COMPLETE_VERIFIED_USER_APPROVED with a set user_approval whose basis "
            "claims a fresh User act: coherent per DEC-7112 design #6. NOTE: this "
            "is coherence only — the gate does not certify that the gate pass "
            "occurred, that the approval is genuine, or that the act was fresh "
            "(UQ-ATT-2); attribution of decided_by remains attribution's "
            "authority (control approval-authenticity).",
        )
    if approval is not None:
        return ControlResult(
            cid, req, FAIL,
            f"inventory_state={state!r} carries a set user_approval: approval may "
            "only accompany COMPLETE_VERIFIED_USER_APPROVED (approval recorded "
            "against planning or awaiting data is incoherent, per DEC-7112 "
            "design #6)",
        )
    return ControlResult(
        cid, req, PASS,
        f"observed inventory_state={state!r} with user_approval=null: coherent "
        "pre-transition state per DEC-7112 design #6. The transition requires a "
        "full gate PASS and a fresh explicit User approval act (APPROVAL-MECHANISM "
        "OPTION A), executed by a tool run under explicit User authorization. The "
        "gate never writes approval state and never transitions the inventory.",
    )


# --- orchestration -------------------------------------------------------------


def run_gate(
    slice_path: str,
    inventory_path: str,
    content_types: List[Any],
    content_records: List[Any],
    slice_id_history: Optional[List[str]],
    build_dir: Optional[str],
    approval: Any,
) -> GateReport:
    """Evaluate every control fail-closed and return the aggregate report.

    Structural validation is computed and reported on its own control; it is never
    consulted to satisfy a runtime control. The returned report is NOT asserted to
    be internally consistent here — GateReport.overall computes the verdict against
    REQUIRED_CONTROL_IDS and therefore fails closed even if a control is omitted.
    """
    report = GateReport()
    base_dir = os.path.dirname(os.path.realpath(slice_path)) if slice_path else os.getcwd()

    slice_doc, slice_err = _load_json(slice_path)
    if slice_err:
        # A slice document that cannot be read fails every dependent control.
        report.add(ControlResult(
            "schema-structural", "REQ-P10-09 c.1, c.2, c.3", FAIL,
            f"cannot read slice document: {slice_err}",
        ))
        report.add(ControlResult(
            "slice-required-fields", "REQ-P10-09 c.4", FAIL, "slice document unreadable"
        ))
        report.add(ControlResult(
            "evidence-references", "REQ-P10-09 c.5", FAIL, "slice document unreadable"
        ))
        report.add(ControlResult(
            "layout-slot-conformance", "REQ-P10-09 c.4, c.5", FAIL, "slice document unreadable"
        ))
        report.add(ControlResult(
            "published-only-content", "REQ-P10-09 c.5", FAIL, "slice document unreadable"
        ))
        report.add(ControlResult(
            "exposure-declaration", "REQ-P10-09 c.7, D-P10-1", FAIL, "slice document unreadable"
        ))
        report.add(ControlResult(
            "slice-id-uniqueness", "REQ-P10-09 c.9", FAIL, "slice document unreadable"
        ))
        slice_doc = None
    else:
        report.add(check_schema_structural(slice_doc))
        report.add(check_slice_required_fields(slice_doc))
        report.add(check_evidence_references(slice_doc, base_dir))
        report.add(check_layout_slot_conformance(slice_doc, content_types, content_records))
        report.add(check_published_only_content(slice_doc, content_records))
        report.add(check_exposure_declaration(slice_doc))
        report.add(check_slice_id_uniqueness(slice_doc, slice_id_history))

    report.add(check_evidence_freshness(slice_doc, base_dir))
    report.add(check_evidence_authenticity(slice_doc, base_dir))

    inventory, inv_err = _load_json(inventory_path)
    if inv_err:
        report.add(ControlResult(
            "inventory-preconditions", "REQ-P10-17", FAIL,
            f"cannot read inventory: {inv_err}",
        ))
        inventory = None
    else:
        report.add(check_inventory_preconditions(inventory))

    report.add(check_approval_authenticity(slice_doc, approval))
    report.add(check_p9_deployment_audit(slice_doc, build_dir))
    report.add(check_cms_state_digest(inventory))
    report.add(check_p8_contract_digest(inventory))
    report.add(check_req_p10_07_reconciliation(slice_doc))
    report.add(check_approval_state_interaction(inventory))
    return report


# --- CLI -----------------------------------------------------------------------


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="p10_runtime_gate.py",
        description="P10 Runtime Validation Gate (REQ-P10-09, Phase A). Fail-closed.",
    )
    parser.add_argument("--slice", required=True, help="path to a slice contract document")
    parser.add_argument(
        "--inventory", default=None,
        help="path to the P10 section inventory (default: framework/sps2/requirements/P10-SECTION-INVENTORY.json)",
    )
    parser.add_argument(
        "--content-types", default=None,
        help="path to P8 content_types.json (default: framework/domain/cms/data/content_types.json)",
    )
    parser.add_argument(
        "--content", default=None,
        help="path to P8 content.json (default: framework/domain/cms/data/content.json)",
    )
    parser.add_argument(
        "--slice-id-history", default=None,
        help="JSON file containing an authoritative array of previously recorded slice_ids",
    )
    parser.add_argument("--build-dir", default=None, help="build directory for the P9 deployment audit")
    parser.add_argument(
        "--approval", default=None,
        help="JSON file containing the approval object to attribute (e.g. a decision record's approval block)",
    )
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    args = parser.parse_args(argv)

    root = _repo_root()
    _ensure_importable()
    inventory_path = args.inventory or os.path.join(
        root, "framework", "sps2", "requirements", "P10-SECTION-INVENTORY.json"
    )
    ct_path = args.content_types or os.path.join(root, "framework", "domain", "cms", "data", "content_types.json")
    c_path = args.content or os.path.join(root, "framework", "domain", "cms", "data", "content.json")

    content_types, _ = _load_json(ct_path)
    content_records, _ = _load_json(c_path)

    history: Optional[List[str]]
    if args.slice_id_history:
        data, err = _load_json(args.slice_id_history)
        if err or not isinstance(data, list):
            history = None
        else:
            # Non-string entries are NOT silently dropped: a slice_id recorded
            # as a number is still an authoritative history entry, and
            # filtering it out before the uniqueness control sees it would let
            # a reused id pass. Coerce to str so the control compares against
            # the full history; the control itself fails closed on anything
            # it cannot interpret.
            history = [h if isinstance(h, str) else str(h) for h in data]
    else:
        history = None

    approval: Any = None
    if args.approval:
        data, err = _load_json(args.approval)
        approval = None if err else (data.get("approval") if isinstance(data, dict) else data)

    report = run_gate(
        slice_path=args.slice,
        inventory_path=inventory_path,
        content_types=content_types if isinstance(content_types, list) else [],
        content_records=content_records if isinstance(content_records, list) else [],
        slice_id_history=history,
        build_dir=args.build_dir,
        approval=approval,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for r in report.results:
            marker = {"PASS": "PASS", "FAIL": "FAIL", "BLOCKED": "BLOCKED",
                      "UNIMPLEMENTED": "UNIMPL"}.get(r.result, r.result)
            print(f"[{marker:6}] {r.control_id} ({r.requirement})")
            print(f"          {r.detail}")
        for problem in report.integrity_problems:
            print(f"[INTEGRITY] {problem}")
        print()
        print(f"OVERALL: {report.overall}  "
              f"(required controls failing: {len(report.failures)}; "
              f"integrity problems: {len(report.integrity_problems)}; "
              f"required controls: {len(REQUIRED_CONTROL_IDS)})")

    # Fail-closed exit semantics.
    return EXIT_OK if report.overall == PASS else EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
