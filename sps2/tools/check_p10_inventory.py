#!/usr/bin/env python3
"""P10 Section Inventory Contract Validator (sps2.p10-section-inventory/v1).

WHAT THIS TOOL IS
    A CONTRACT-SPECIFIC STRUCTURAL VALIDATOR. It encodes, by hand, the subset of
    rules in sps2/schemas/p10-section-inventory.schema.json that this validator
    understands, and applies those rules to a P10 section inventory document.

    It is NOT a general JSON Schema Draft 2020-12 implementation. It does not
    interpret "$ref" chains, "oneOf"/"anyOf"/"allOf" combinators generically,
    "if"/"then"/"else", "$defs" inheritance, "unevaluatedProperties", numeric or
    length keywords it was not written for, or any other part of the draft. It
    never claims full draft compliance.

    Precedent: this mirrors the approach P9 already ships in
    domain/seo/audit.py::validate_audit_report_schema, a hand-written stdlib
    subset validator for sps2/schemas/p9-audit.schema.json.

    Standard library only. No network. No installs. Reads two files, writes none.

WHAT THIS TOOL DOES NOT PROVE (runtime obligations, NOT implemented here)
    Passing this tool establishes document structure and field constraints ONLY.
    It does NOT establish, and must never be cited as evidence of:
      * User approval authenticity, or that the named decider is the User;
      * existence or authenticity of any source_ref;
      * existence of any P8 Section, ContentType, or Asset record;
      * membership of the P10 layout registry (REQ-P10-02);
      * uniqueness of section_id or route ACROSS sections;
      * consistency with P9 route derivation in domain/seo/audit.py;
      * correctness of runtime backend/data dependency declarations;
      * existence or authenticity of any acceptance or test evidence;
      * derivation from genuine CMS state.
    Those are obligations of the mandatory fail-closed runtime validation gate
    (REQ-P10-09, REQ-P10-17), which is specified but NOT implemented.

FAIL-CLOSED BEHAVIOUR
    If the schema changes beyond the subset this validator understands, the
    validator reports a schema-contract incompatibility and exits non-zero
    rather than silently passing. It never downgrades to "skipped".

Usage:
    check_p10_inventory.py [--inventory PATH] [--schema PATH] [--self-test]

Exit codes:
    0  every implemented check passed
    1  inventory violates an implemented rule
    2  tooling/usage error, missing or unreadable file, or schema-contract
       incompatibility (the validator cannot faithfully check what it is given)
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
import tempfile
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SPS2 = os.path.dirname(HERE)
REPO = os.path.dirname(SPS2)

DEFAULT_SCHEMA = os.path.join(SPS2, "schemas", "p10-section-inventory.schema.json")
DEFAULT_INVENTORY = os.path.join(SPS2, "requirements", "P10-SECTION-INVENTORY.json")

EXPECTED_SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"
EXPECTED_SCHEMA_ID = "sps2.p10-section-inventory/v1"
# Mandated by the approved slice contract; cross-checked against the schema on load.
SLICE_ROUTE_PATTERN = "^/[a-z0-9/-]*$"

INVENTORY_STATES = (
    "INCOMPLETE_PLANNING",
    "COMPLETE_AWAITING_USER_APPROVAL",
    "COMPLETE_VERIFIED_USER_APPROVED",
)
PROVENANCE_CLASSES = (
    "USER_DECISION",
    "DERIVED",
    "P9_OWNED_REFERENCE",
    "UNDECLARED_PENDING",
)
INVENTORY_REQUIRED = ("inventory_id", "inventory_state", "complete", "sections")
INVENTORY_ALLOWED = (
    "$comment", "inventory_id", "inventory_state", "complete", "notes",
    "provenance", "sections", "user_approval",
)
# REQ-P10-17 criterion 2 fields, plus the structural completeness marker.
SECTION_REQUIRED = (
    "section_completeness", "section_id", "purpose", "route",
    "cms_content_types", "layout_id", "assets", "backend_data_dependencies",
    "seo_requirements", "acceptance_test_requirements",
)
SECTION_DATA_FIELDS = SECTION_REQUIRED[1:]
SECTION_COMPLETENESS = ("INCOMPLETE", "COMPLETE")
SCALAR_FIELDS = ("section_id", "purpose", "route", "layout_id")
LIST_FIELDS = ("cms_content_types", "assets", "backend_data_dependencies",
               "acceptance_test_requirements")
SEO_FIELD = "seo_requirements"

FIELD_ENVELOPE_PROPS = {
    "user_decision_field": {"provenance", "value", "user_decision_ref", "note"},
    "derived_scalar_field": {"provenance", "source_ref", "value", "note"},
    "unresolved_scalar_field": {"provenance", "value", "reason_unresolved"},
    "user_decision_list_field": {"provenance", "values", "user_decision_ref", "note"},
    "derived_list_field": {"provenance", "source_ref", "values", "note"},
    "unresolved_list_field": {"provenance", "values", "reason_unresolved"},
    "p9_reference_field": {"provenance", "references", "note"},
}
PROVENANCE_ALLOWED = {"provenance": PROVENANCE_CLASSES}


def is_nonblank(value) -> bool:
    """Mirror of $defs/non_blank_string: a string with >=1 non-whitespace char."""
    return isinstance(value, str) and len(value) >= 1 and re.search(r"\S", value) is not None


class SchemaContractError(Exception):
    """The schema is missing, unreadable, or beyond this validator's subset."""


# ---------------------------------------------------------------------------
# Schema integrity: fail closed if the contract drifts beyond the subset.
# ---------------------------------------------------------------------------

def load_schema(path: str) -> dict:
    if not os.path.isfile(path):
        raise SchemaContractError("schema not found: %s" % path)
    try:
        with open(path, encoding="utf-8") as fh:
            schema = json.load(fh)
    except (OSError, ValueError) as exc:
        raise SchemaContractError("schema unreadable or not valid JSON: %s (%s)" % (path, exc))
    if not isinstance(schema, dict):
        raise SchemaContractError("schema must be a JSON object: %s" % path)

    uri = schema.get("$schema")
    if uri != EXPECTED_SCHEMA_URI:
        raise SchemaContractError(
            "schema $schema is %r; this validator implements %r" % (uri, EXPECTED_SCHEMA_URI))
    sid = schema.get("$id")
    if sid != EXPECTED_SCHEMA_ID:
        raise SchemaContractError(
            "schema $id is %r; this validator implements %r" % (sid, EXPECTED_SCHEMA_ID))

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        raise SchemaContractError("schema has no $defs object; cannot verify $defs subset")

    # Enums the implemented rules depend on.
    def enum_at(container, key, label):
        parts = key.split(".")
        node = container
        for part in parts[:-1]:
            if not isinstance(node, dict) or part not in node:
                raise SchemaContractError("schema is missing %s (%s)" % (label, key))
            node = node[part]
        if not isinstance(node, dict) or parts[-1] not in node:
            raise SchemaContractError("schema is missing %s (%s)" % (label, key))
        enum = node[parts[-1]]
        if not isinstance(enum, list) or not enum:
            raise SchemaContractError("schema %s has no usable enum" % label)
        return tuple(enum)

    states = enum_at(schema, "properties.inventory_state.enum", "inventory_state")
    if states != INVENTORY_STATES:
        raise SchemaContractError(
            "inventory_state enum changed to %r; validator implements %r" % (states, INVENTORY_STATES))
    prov = enum_at(schema, "$defs.provenance_class.enum", "provenance_class")
    if prov != PROVENANCE_CLASSES:
        raise SchemaContractError(
            "provenance_class enum changed to %r; validator implements %r" % (prov, PROVENANCE_CLASSES))
    comp = enum_at(schema, "$defs.section.properties.section_completeness.enum",
                   "section_completeness")
    if comp != SECTION_COMPLETENESS:
        raise SchemaContractError(
            "section_completeness enum changed to %r; validator implements %r"
            % (comp, SECTION_COMPLETENESS))

    role = enum_at(schema, "properties.user_approval.properties.decided_by_role.enum",
                   "decided_by_role")
    if role != ("USER",):
        raise SchemaContractError(
            "decided_by_role enum changed to %r; validator implements ('USER',)" % (role,))

    # Route pattern is read from the schema, then checked against the value the
    # approved slice contract mandates; disagreement means drift.
    route_pat = defs.get("route_string", {}).get("pattern") if isinstance(defs.get("route_string"), dict) else None
    if not isinstance(route_pat, str):
        raise SchemaContractError("schema $defs/route_string.pattern missing or not a string")
    try:
        re.compile(route_pat)
    except re.error as exc:
        raise SchemaContractError("schema route pattern is not a valid regex: %s" % exc)
    if route_pat != SLICE_ROUTE_PATTERN:
        raise SchemaContractError(
            "route_string.pattern is %r but the approved slice contract mandates %r"
            % (route_pat, SLICE_ROUTE_PATTERN))

    # non_blank_string must remain a string with minLength>=1 and a \S pattern.
    nb = defs.get("non_blank_string")
    if not isinstance(nb, dict) or nb.get("type") != "string" or nb.get("minLength", 0) < 1 \
            or "pattern" not in nb:
        raise SchemaContractError(
            "schema $defs/non_blank_string no longer matches the shape this validator implements")

    # Required-field arrays must match the implemented subset exactly.
    root_req = tuple(schema.get("required", ()))
    if root_req != INVENTORY_REQUIRED:
        raise SchemaContractError(
            "root required changed to %r; validator implements %r" % (root_req, INVENTORY_REQUIRED))
    sec = defs.get("section")
    if not isinstance(sec, dict):
        raise SchemaContractError("schema $defs/section missing")
    sec_req = tuple(sec.get("required", ()))
    if sec_req != SECTION_REQUIRED:
        raise SchemaContractError(
            "section required changed to %r; validator implements %r" % (sec_req, SECTION_REQUIRED))
    if schema.get("additionalProperties") is not False or sec.get("additionalProperties") is not False:
        raise SchemaContractError(
            "this validator relies on additionalProperties:false at root and section; schema changed")

    # Envelope property sets must match, or the strict-property checks drift.
    for name, expected in FIELD_ENVELOPE_PROPS.items():
        node = defs.get(name)
        if not isinstance(node, dict):
            raise SchemaContractError("schema $defs/%s missing" % name)
        got = set(node.get("properties", {}).keys())
        if got != expected:
            raise SchemaContractError(
                "schema $defs/%s properties changed to %r; validator implements %r"
                % (name, sorted(got), sorted(expected)))
        if node.get("additionalProperties") is not False:
            raise SchemaContractError(
                "schema $defs/%s no longer sets additionalProperties:false" % name)
        req = set(node.get("required", ()))
        if not req.issubset(expected):
            raise SchemaContractError(
                "schema $defs/%s requires unknown properties %r" % (name, sorted(req - expected)))

    # user_approval shape.
    ua = schema["properties"].get("user_approval")
    if not isinstance(ua, dict) or set(ua.get("required", ())) != \
            {"decided_by", "decided_by_role", "decided_at", "basis"}:
        raise SchemaContractError("schema user_approval required set changed")
    if ua.get("additionalProperties") is not False:
        raise SchemaContractError("schema user_approval no longer sets additionalProperties:false")

    return schema


# ---------------------------------------------------------------------------
# Inventory validation (the implemented subset).
# ---------------------------------------------------------------------------

def validate_inventory(doc, route_pat: str = SLICE_ROUTE_PATTERN) -> list:
    errors: list = []

    def err(where, msg):
        errors.append("%s: %s" % (where, msg))

    if not isinstance(doc, dict):
        return ["$: inventory must be a JSON object, found %s" % type(doc).__name__]

    # --- root required / additionalProperties ---
    for key in INVENTORY_REQUIRED:
        if key not in doc:
            err("$", "missing required property '%s'" % key)
    for key in sorted(doc):
        if key not in INVENTORY_ALLOWED:
            err("$", "unexpected property '%s' is not permitted" % key)

    # --- inventory_id ---
    iid = doc.get("inventory_id")
    if iid is not None and (not isinstance(iid, str)
                            or re.fullmatch(r"P10-SECTION-INVENTORY-v[0-9]+", iid) is None):
        err("$.inventory_id", "must match '^P10-SECTION-INVENTORY-v[0-9]+$', found %r" % (iid,))

    # --- inventory_state ---
    state = doc.get("inventory_state")
    if state is not None and state not in INVENTORY_STATES:
        err("$.inventory_state", "%r is not one of %s" % (state, list(INVENTORY_STATES)))

    # --- complete must be a real boolean ---
    complete = doc.get("complete")
    if "complete" in doc and not isinstance(complete, bool):
        err("$.complete", "must be a boolean, found %s" % type(complete).__name__)

    # --- provenance (required once complete) ---
    prov = doc.get("provenance")
    if complete is True:
        if not isinstance(prov, dict):
            err("$.provenance", "required when complete is true")
        elif not is_nonblank(prov.get("generator")):
            err("$.provenance.generator",
                "required non-blank string when complete is true, found %r"
                % (prov.get("generator"),))
    if prov is not None and not isinstance(prov, dict):
        err("$.provenance", "must be an object, found %s" % type(prov).__name__)
    elif isinstance(prov, dict):
        for key in sorted(prov):
            if key not in ("generator", "generated_at", "cms_state_digest", "p8_contract_digest"):
                err("$.provenance", "unexpected property '%s'" % key)
        if "generated_at" in prov and not _is_iso_date(prov["generated_at"]):
            err("$.provenance.generated_at", "must be an ISO date, found %r" % (prov["generated_at"],))
        for dig in ("cms_state_digest", "p8_contract_digest"):
            if dig in prov and prov[dig] is not None and not is_nonblank(prov[dig]):
                err("$.provenance.%s" % dig, "must be null or a non-blank string")

    # --- user_approval: presence tied to state; content shape ---
    approval = doc.get("user_approval")
    if approval is not None and not isinstance(approval, dict):
        err("$.user_approval", "must be null or an object, found %s" % type(approval).__name__)
        approval = None
    if isinstance(approval, dict):
        for key in ("decided_by", "decided_by_role", "decided_at", "basis"):
            if key not in approval:
                err("$.user_approval", "missing required property '%s'" % key)
        for key in sorted(approval):
            if key not in ("decided_by", "decided_by_role", "decided_at", "basis"):
                err("$.user_approval", "unexpected property '%s'" % key)
        if not is_nonblank(approval.get("decided_by")):
            err("$.user_approval.decided_by",
                "must be a non-blank string, found %r" % (approval.get("decided_by"),))
        if approval.get("decided_by_role") != "USER":
            err("$.user_approval.decided_by_role",
                "must be 'USER' (only the User may approve), found %r"
                % (approval.get("decided_by_role"),))
        if not is_nonblank(approval.get("basis")):
            err("$.user_approval.basis",
                "must be a non-blank string, found %r" % (approval.get("basis"),))
        if "decided_at" in approval and not _is_iso_date(approval["decided_at"]):
            err("$.user_approval.decided_at", "must be an ISO date, found %r"
                % (approval["decided_at"],))

    # --- lifecycle consistency (mirrors the schema's top-level allOf rules) ---
    if state == "COMPLETE_AWAITING_USER_APPROVAL":
        if complete is not True:
            err("$.complete",
                "must be true when inventory_state is COMPLETE_AWAITING_USER_APPROVAL, found %r"
                % (complete,))
        if approval is not None:
            err("$.user_approval",
                "must be null while awaiting User approval; an approval record contradicts this state")
    if state == "INCOMPLETE_PLANNING" and approval is not None:
        err("$.user_approval",
            "must be null in INCOMPLETE_PLANNING; recording approval against planning data "
            "is not permitted")
    if state == "COMPLETE_VERIFIED_USER_APPROVED":
        if approval is None:
            err("$.user_approval", "required when inventory_state is COMPLETE_VERIFIED_USER_APPROVED")
        if complete is not True:
            err("$.complete", "must be true when inventory_state is COMPLETE_VERIFIED_USER_APPROVED")

    # --- sections ---
    sections = doc.get("sections")
    if sections is not None and not isinstance(sections, list):
        err("$.sections", "must be an array, found %s" % type(sections).__name__)
        sections = None
    if isinstance(sections, list):
        if complete is True and len(sections) == 0:
            err("$.sections", "must contain at least one section when complete is true")
        if complete is True:
            for idx, sec in enumerate(sections):
                if isinstance(sec, dict) and sec.get("section_completeness") != "COMPLETE":
                    err("$.sections[%d].section_completeness" % idx,
                        "must be 'COMPLETE' when the inventory declares complete, found %r"
                        % (sec.get("section_completeness"),))
        for idx, sec in enumerate(sections):
            errors.extend(_validate_section(sec, "$.sections[%d]" % idx, route_pat))

    # --- cross-item uniqueness is a RUNTIME obligation, reported not enforced ---
    if isinstance(sections, list):
        ids = [s.get("section_id", {}).get("value") for s in sections
               if isinstance(s, dict) and isinstance(s.get("section_id"), dict)]
        routes = [s.get("route", {}).get("value") for s in sections
                  if isinstance(s, dict) and isinstance(s.get("route"), dict)]
        dup_ids = sorted({v for v in ids if v is not None and ids.count(v) > 1})
        dup_routes = sorted({v for v in routes if v is not None and routes.count(v) > 1})
        if dup_ids or dup_routes:
            errors.append(
                "WARNING (not enforced by this tool, RUNTIME gate obligation): duplicate section_id "
                "%s and/or duplicate route %s" % (dup_ids or "none", dup_routes or "none"))
    return errors


def _is_iso_date(value) -> bool:
    if not isinstance(value, str) or len(value) != 10 or value[4] != "-" or value[7] != "-":
        return False
    y, m, d = value[:4], value[5:7], value[8:]
    try:
        return date(int(y), int(m), int(d)).isoformat() == value
    except ValueError:
        return False


def _validate_section(sec, path: str, route_pat: str) -> list:
    errors: list = []

    def err(where, msg):
        errors.append("%s: %s" % (where, msg))

    if not isinstance(sec, dict):
        return ["%s: section must be an object, found %s" % (path, type(sec).__name__)]

    for key in SECTION_REQUIRED:
        if key not in sec:
            err(path, "missing required property '%s'" % key)
    for key in sorted(sec):
        if key not in SECTION_REQUIRED:
            err(path, "unexpected property '%s' is not permitted" % key)

    comp = sec.get("section_completeness")
    if comp is not None and comp not in SECTION_COMPLETENESS:
        err("%s.section_completeness" % path, "%r is not one of %s"
            % (comp, list(SECTION_COMPLETENESS)))

    for fname in SCALAR_FIELDS:
        if fname in sec:
            errors.extend(_validate_field(sec[fname], "%s.%s" % (path, fname), "scalar", route_pat))
    for fname in LIST_FIELDS:
        if fname in sec:
            errors.extend(_validate_field(sec[fname], "%s.%s" % (path, fname), "list", route_pat))
    if SEO_FIELD in sec:
        errors.extend(_validate_field(sec[SEO_FIELD], "%s.%s" % (path, SEO_FIELD), "seo", route_pat))

    # A section declared COMPLETE may carry no UNDECLARED_PENDING field.
    if comp == "COMPLETE":
        for fname in SECTION_DATA_FIELDS:
            node = sec.get(fname)
            if isinstance(node, dict) and node.get("provenance") == "UNDECLARED_PENDING":
                err("%s.%s" % (path, fname),
                    "is UNDECLARED_PENDING but the section is declared COMPLETE")
    return errors


def _validate_field(node, path: str, kind: str, route_pat: str) -> list:
    errors: list = []

    def err(msg):
        errors.append("%s: %s" % (path, msg))

    if not isinstance(node, dict):
        return ["%s: must be an object with a provenance envelope, found %s"
                % (path, type(node).__name__)]

    prov = node.get("provenance")
    if prov is None:
        return ["%s: missing required property 'provenance'" % path]
    if prov not in PROVENANCE_CLASSES:
        err("provenance %r is not one of %s" % (prov, list(PROVENANCE_CLASSES)))
        return errors

    allowed, required = _envelope_for(prov, kind)
    for key in sorted(node):
        if key not in allowed:
            err("unexpected property '%s' is not permitted" % key)
    for key in required:
        if key not in node:
            err("missing required property '%s' for provenance %s" % (key, prov))

    if prov == "DERIVED":
        if "source_ref" in node and not is_nonblank(node["source_ref"]):
            err("source_ref must be a non-blank string, found %r" % (node["source_ref"],))
        if kind in ("scalar", "list") and "source_ref" not in node:
            err("DERIVED requires source_ref naming the authoritative source")

    if prov == "UNDECLARED_PENDING":
        key = "values" if kind == "list" else "value"
        if key in node and node[key] is not None:
            err("%s must be null while UNDECLARED_PENDING, found %r; unknown information "
                "may never be represented as a resolved or empty value" % (key, node[key]))
        if "reason_unresolved" in node and not is_nonblank(node["reason_unresolved"]):
            err("reason_unresolved must be a non-blank string, found %r"
                % (node["reason_unresolved"],))

    if prov in ("USER_DECISION", "DERIVED"):
        if kind == "scalar" and "value" in node and not is_nonblank(node["value"]):
            err("value must be a non-blank string, found %r" % (node["value"],))
        if kind == "list":
            if "values" in node:
                if not isinstance(node["values"], list):
                    err("values must be an array, found %s" % type(node["values"]).__name__)
                else:
                    for i, v in enumerate(node["values"]):
                        if not is_nonblank(v):
                            err("values[%d] must be a non-blank string, found %r" % (i, v))
                    if len(node["values"]) != len(set(map(str, node["values"]))):
                        err("values must be unique (uniqueItems)")
        if "user_decision_ref" in node and node["user_decision_ref"] is not None \
                and not is_nonblank(node["user_decision_ref"]):
            err("user_decision_ref must be null or a non-blank string, found %r"
                % (node["user_decision_ref"],))

    # P9-owned references: at least one, each non-blank. Applies to the
    # P9_OWNED_REFERENCE class specifically, not to USER_DECISION/DERIVED.
    if prov == "P9_OWNED_REFERENCE":
        if "references" in node:
            refs = node["references"]
            if not isinstance(refs, list) or len(refs) < 1:
                err("references must be a non-empty array of P9-owned contract identifiers, "
                    "found %r" % (refs,))
            else:
                for i, v in enumerate(refs):
                    if not is_nonblank(v):
                        err("references[%d] must be a non-blank string, found %r" % (i, v))

    # Route format applies only to a resolved route.
    if path.endswith(".route") and prov in ("USER_DECISION", "DERIVED"):
        v = node.get("value")
        if isinstance(v, str) and re.fullmatch(route_pat, v) is None:
            err("route value %r does not match the approved pattern %s" % (v, route_pat))
    return errors


def _envelope_for(prov: str, kind: str):
    if prov == "USER_DECISION":
        return (FIELD_ENVELOPE_PROPS["user_decision_list_field"]
                if kind == "list" else FIELD_ENVELOPE_PROPS["user_decision_field"],
                {"provenance", "values"} if kind == "list" else {"provenance", "value"})
    if prov == "DERIVED":
        return (FIELD_ENVELOPE_PROPS["derived_list_field"] if kind == "list"
                else FIELD_ENVELOPE_PROPS["derived_scalar_field"],
                {"provenance", "source_ref", "values"} if kind == "list"
                else {"provenance", "source_ref", "value"})
    if prov == "P9_OWNED_REFERENCE":
        return FIELD_ENVELOPE_PROPS["p9_reference_field"], {"provenance", "references"}
    return (FIELD_ENVELOPE_PROPS["unresolved_list_field"] if kind == "list"
            else FIELD_ENVELOPE_PROPS["unresolved_scalar_field"],
            {"provenance", "values"} if kind == "list" else {"provenance", "value"})


def load_inventory(path: str):
    if not os.path.isfile(path):
        raise SchemaContractError("inventory not found: %s" % path)
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        raise SchemaContractError("inventory unreadable or not valid JSON: %s (%s)" % (path, exc))


# ---------------------------------------------------------------------------
# Self-test (uses only temp files; never writes inside the repository).
# ---------------------------------------------------------------------------

def _valid_section(route="/ok", sid="SEC-1"):
    def sc(v):
        return {"provenance": "USER_DECISION", "value": v}

    def dl(vals):
        return {"provenance": "DERIVED", "source_ref": "p8:fixture", "values": vals}
    return {
        "section_completeness": "COMPLETE", "section_id": sc(sid), "purpose": sc("A purpose"),
        "route": sc(route), "cms_content_types": dl(["t1"]), "layout_id": sc("hero"),
        "assets": dl(["a1"]), "backend_data_dependencies": dl(["d1"]),
        "seo_requirements": {"provenance": "P9_OWNED_REFERENCE", "references": ["p9:metadata"]},
        "acceptance_test_requirements": dl(["per_slice_dod"]),
    }


def _valid_approval():
    return {"decided_by": "User", "decided_by_role": "USER", "decided_at": "2026-10-09",
            "basis": "explicit User approval in session"}


def _base_inventory():
    return {"$comment": "self-test fixture", "inventory_id": "P10-SECTION-INVENTORY-v1",
            "inventory_state": "INCOMPLETE_PLANNING", "complete": False,
            "provenance": {"generator": "self-test"}, "user_approval": None, "sections": []}


def _complete_inventory():
    return {"inventory_id": "P10-SECTION-INVENTORY-v1",
            "inventory_state": "COMPLETE_VERIFIED_USER_APPROVED", "complete": True,
            "provenance": {"generator": "self-test"},
            "user_approval": _valid_approval(), "sections": [_valid_section()]}


def run_self_test(schema_path: str) -> int:
    try:
        schema = load_schema(schema_path)
    except SchemaContractError as exc:
        print("FAIL  schema contract check: %s" % exc)
        return 1
    route_pat = schema["$defs"]["route_string"]["pattern"]

    results = []

    def expect_valid(label, doc):
        errs = [e for e in validate_inventory(doc) if not e.startswith("WARNING")]
        results.append((label, not errs, errs))

    def expect_invalid(label, doc, must_contain=None):
        errs = [e for e in validate_inventory(doc) if not e.startswith("WARNING")]
        ok = bool(errs)
        if ok and must_contain:
            ok = any(must_contain in e for e in errs)
        results.append((label, ok, errs if not errs else [e for e in errs if must_contain and must_contain in e]))

    # --- schema integrity ---
    results.append(("schema loads and is within the implemented subset", True, []))
    results.append(("missing schema file fails closed",
                    _raises(load_schema, os.path.join(HERE, "__no_such_schema__.json")),
                    []))

    # --- happy paths ---
    expect_valid("current repository skeleton passes",
                 load_inventory(DEFAULT_INVENTORY))
    expect_valid("valid complete approved fixture", _complete_inventory())

    d = _base_inventory(); d["inventory_state"] = "COMPLETE_AWAITING_USER_APPROVAL"
    d["complete"] = True; d["sections"] = [_valid_section()]
    expect_valid("valid awaiting-approval fixture", d)

    # --- negative: lifecycle ---
    d = _base_inventory(); d["inventory_state"] = "BOGUS_STATE"
    expect_invalid("invalid lifecycle state", d, "inventory_state")
    d = _base_inventory(); d["inventory_state"] = "COMPLETE_AWAITING_USER_APPROVAL"
    d["complete"] = False; d["sections"] = [_valid_section()]
    expect_invalid("AWAITING with complete:false", d, "must be true")
    d = _base_inventory(); d["complete"] = True; d["sections"] = []
    expect_invalid("complete:true with empty sections", d, "at least one section")
    d = _base_inventory(); d["complete"] = True; d["sections"] = [_valid_section()]
    d["provenance"] = {}
    expect_invalid("complete:true without generator", d, "generator")
    d = _complete_inventory(); d["complete"] = False
    expect_invalid("VERIFIED with complete:false", d, "must be true")
    d = _complete_inventory(); d["user_approval"] = None
    expect_invalid("VERIFIED without approval record", d, "user_approval")
    d = _base_inventory(); d["user_approval"] = _valid_approval()
    expect_invalid("PLANNING carrying an approval record", d, "must be null")

    # --- negative: required fields ---
    d = _base_inventory(); del d["inventory_id"]
    expect_invalid("missing inventory_id", d, "missing required property")
    for fname in ("section_id", "purpose", "route", "cms_content_types", "layout_id",
                  "assets", "backend_data_dependencies", "seo_requirements",
                  "acceptance_test_requirements"):
        d = _complete_inventory(); del d["sections"][0][fname]
        expect_invalid("missing section field '%s'" % fname, d, "missing required property")

    # --- negative: provenance ---
    d = _complete_inventory(); d["sections"][0]["route"] = {"provenance": "DERIVED", "value": "/ok"}
    expect_invalid("DERIVED without source_ref", d, "source_ref")
    d = _complete_inventory(); d["sections"][0]["assets"]["source_ref"] = "   "
    expect_invalid("DERIVED with whitespace-only source_ref", d, "source_ref")
    d = _complete_inventory(); d["sections"][0]["purpose"]["provenance"] = "INVENTED_CLASS"
    expect_invalid("invalid provenance enum", d, "provenance")
    d = _complete_inventory()
    d["sections"][0]["seo_requirements"] = {"provenance": "P9_OWNED_REFERENCE", "references": []}
    expect_invalid("P9_OWNED_REFERENCE with empty references", d, "non-empty array")
    d = _complete_inventory()
    d["sections"][0]["seo_requirements"] = {
        "provenance": "P9_OWNED_REFERENCE", "references": ["  "]}
    expect_invalid("P9_OWNED_REFERENCE with whitespace reference", d, "non-blank")
    d = _complete_inventory(); d["sections"][0]["assets"]["values"] = []
    d["sections"][0]["assets"] = {"provenance": "UNDECLARED_PENDING", "values": []}
    expect_invalid("UNDECLARED_PENDING with empty list instead of null", d, "must be null")
    d = _complete_inventory()
    d["sections"][0]["layout_id"] = {"provenance": "UNDECLARED_PENDING", "value": "hero"}
    expect_invalid("UNDECLARED_PENDING with a value", d, "must be null")

    # --- negative: route format ---
    for bad in ("NOT A ROUTE ../etc", "/UPPERCASE", "/route with spaces", "no-leading-slash"):
        d = _complete_inventory(); d["sections"][0]["route"] = {"provenance": "USER_DECISION", "value": bad}
        expect_invalid("invalid route %r" % bad, d, "does not match the approved pattern")

    # --- negative: whitespace-only required values ---
    d = _complete_inventory(); d["provenance"]["generator"] = "   "
    expect_invalid("whitespace-only generator", d, "generator")
    d = _complete_inventory(); d["user_approval"]["decided_by"] = "  "
    expect_invalid("whitespace-only decided_by", d, "decided_by")
    d = _complete_inventory(); d["user_approval"]["basis"] = "   "
    expect_invalid("whitespace-only basis", d, "basis")
    d = _complete_inventory(); d["user_approval"]["decided_by"] = ""
    expect_invalid("empty decided_by", d, "decided_by")
    d = _complete_inventory(); d["sections"][0]["purpose"]["user_decision_ref"] = ""
    expect_invalid("empty user_decision_ref", d, "user_decision_ref")

    # --- negative: completeness ---
    d = _base_inventory(); s = _valid_section()
    s["route"] = {"provenance": "UNDECLARED_PENDING", "value": None, "reason_unresolved": "pending"}
    s["section_completeness"] = "COMPLETE"
    d["sections"] = [s]
    expect_invalid("COMPLETE section with an unresolved field", d, "declared COMPLETE")
    d = _base_inventory(); d["complete"] = True
    d["sections"] = [_valid_section()]; d["sections"][0]["section_completeness"] = "INCOMPLETE"
    expect_invalid("complete:true with an INCOMPLETE section", d, "must be 'COMPLETE'")

    # --- negative: approval role / unexpected props ---
    d = _complete_inventory(); d["user_approval"]["decided_by_role"] = "AGENT"
    expect_invalid("decided_by_role AGENT", d, "decided_by_role")
    d = _base_inventory(); d["unexpected_root"] = 1
    expect_invalid("unexpected root property", d, "unexpected property")
    d = _complete_inventory(); d["sections"][0]["rogue"] = 1
    expect_invalid("unexpected section property", d, "unexpected property")
    d = _complete_inventory(); d["sections"][0]["purpose"]["rogue"] = 1
    expect_invalid("unexpected field property", d, "unexpected property")

    # --- malformed JSON / missing files (fail closed, non-zero) ---
    results.append(("malformed inventory JSON fails closed", _raises(load_inventory, _write_temp("{ not json")), []))
    results.append(("missing inventory file fails closed",
                    _raises(load_inventory, os.path.join(HERE, "__no_such_inventory__.json")), []))

    # --- cross-item uniqueness: reported as WARNING, never silently passed ---
    d = _base_inventory(); d["inventory_state"] = "COMPLETE_AWAITING_USER_APPROVAL"; d["complete"] = True
    d["sections"] = [_valid_section(sid="SAME"), _valid_section(sid="SAME")]
    warned = any(e.startswith("WARNING") for e in validate_inventory(d))
    results.append(("duplicate section_id reported as runtime-obligation WARNING", warned, []))

    passed = sum(1 for _, ok, _ in results if ok)
    failed = [r for r in results if not r[1]]
    for label, ok, _ in results:
        print("%s  %s" % ("PASS" if ok else "FAIL", label))
    if failed:
        print("")
        for label, _, errs in failed:
            print("  %s -> %s" % (label, errs or "no error produced"))
    print("")
    print("== P10 INVENTORY SELF-TEST: %d passed, %d failed ==" % (passed, len(failed)))
    return 0 if not failed else 1


def _raises(fn, *args) -> bool:
    try:
        fn(*args)
    except SchemaContractError:
        return True
    except Exception:
        return False
    return False


def _write_temp(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".json", prefix="p10-selftest-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Contract-specific structural validator for the P10 section inventory "
                    "(NOT a general JSON Schema Draft 2020-12 implementation).")
    ap.add_argument("--inventory", default=DEFAULT_INVENTORY,
                    help="inventory document to validate (default: the repository skeleton)")
    ap.add_argument("--schema", default=DEFAULT_SCHEMA,
                    help="inventory contract schema (default: the repository schema)")
    ap.add_argument("--self-test", action="store_true",
                    help="run built-in self-tests using temporary files only")
    args = ap.parse_args(argv)

    try:
        if args.self_test:
            return run_self_test(args.schema)
        schema = load_schema(args.schema)
        doc = load_inventory(args.inventory)
        errors = validate_inventory(doc)
    except SchemaContractError as exc:
        print("ERR\t%s" % exc)
        return 2

    hard = [e for e in errors if not e.startswith("WARNING")]
    warn = [e for e in errors if e.startswith("WARNING")]
    for w in warn:
        print("WARN\t%s" % w)
    if hard:
        for e in hard:
            print("ERR\t%s" % e)
        return 1
    if not warn:
        print("OK  %s conforms to %s (structural subset only)"
              % (os.path.relpath(args.inventory, REPO), schema["$id"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())