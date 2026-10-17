#!/usr/bin/env python3
"""Isolated tests for the P10 Runtime Validation Gate (REQ-P10-09, Phase A).

THESE TESTS USE SYNTHETIC FIXTURES ONLY, created inside per-test temporary
directories. A passing test here is NOT real runtime evidence and does NOT mean
the gate passes against a real slice, nor that any runtime verification has ever
succeeded. Every fixture is invented. The real repository contains no P10 slice
document at all, and the gate has never been run against a real build.

The suite verifies fail-closed behaviour: every control must fail, block, or
report UNIMPLEMENTED when its input is missing, malformed, draft, unknown,
contradictory, agent-attributed, vacuous, or out of bounds -- and the overall
verdict must never be PASS while any required control is absent, duplicated,
renamed, demoted, malformed, failed, blocked or unimplemented.

Run:  python3 -B -m unittest framework.sps2.tests.test_p10_runtime_gate
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from framework.sps2.tools.p10_runtime_gate import (  # noqa: E402
    BLOCKED,
    EXIT_FAILED,
    EXIT_OK,
    FAIL,
    PASS,
    REQUIRED_CONTROL_IDS,
    UNIMPLEMENTED,
    UNRESOLVED_SEMANTICS,
    ControlResult,
    GateReport,
    _SliceSchemaValidator,
    _SchemaUnsupported,
    _content_type_fields,
    _json_equal,
    check_approval_authenticity,
    check_approval_state_interaction,
    check_cms_state_digest,
    check_evidence_authenticity,
    check_evidence_freshness,
    check_evidence_references,
    check_exposure_declaration,
    check_inventory_preconditions,
    check_layout_slot_conformance,
    check_p8_contract_digest,
    check_p9_deployment_audit,
    check_published_only_content,
    check_req_p10_07_reconciliation,
    check_schema_structural,
    check_slice_id_uniqueness,
    check_slice_required_fields,
    main,
    run_gate,
)

HOME_CT = {
    "id": "c64e3d79694e49eebd6c09ee58a53c87",
    "name": "home",
    "fields": [
        {"name": "heading", "type": "text", "required": True},
        {"name": "body", "type": "text", "required": True},
    ],
    "created_at": "2026-10-13T00:00:00+00:00",
    "updated_at": "2026-10-13T00:00:00+00:00",
}

OTHER_CT = {
    "id": "ct-other",
    "name": "other",
    "fields": [{"name": "title", "type": "text", "required": True}],
}

PUBLISHED_CONTENT = {
    "id": "content-published",
    "type_id": HOME_CT["id"],
    "title": "Heading",
    "body": "Body",
    "status": "published",
    "author_id": "user",
    "created_at": "2026-10-13T00:00:00+00:00",
    "updated_at": "2026-10-13T00:00:00+00:00",
    "published_at": "2026-10-13T00:01:00+00:00",
}

DRAFT_CONTENT = dict(PUBLISHED_CONTENT, id="content-draft", status="draft", published_at=None)

USER_APPROVAL = {
    "required": True,
    "state": "APPROVED",
    "decided_by": "User",
    "decided_at": "2026-10-13",
    "basis": "Explicit User authorization.",
}

AGENT_APPROVAL = dict(USER_APPROVAL, decided_by="ChatGPT")

MINIMAL_HTML = (
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    "<title>Home</title>\n"
    '<link rel="canonical" href="https://example.com/">\n'
    '<meta name="description" content="Home">\n'
    "</head>\n<body>\n<h1>Heading</h1>\n<p>Body</p>\n</body>\n</html>\n"
)
MINIMAL_SITEMAP = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    "<url><loc>https://example.com/</loc></url>\n</urlset>\n"
)
MINIMAL_ROBOTS = "User-agent: *\nDisallow:\n"


def _valid_slice(slice_id: str = "SLICE-P10-01", layout_id: str = "home-default") -> dict:
    """A fully declared slice fixture that IS valid against the authoritative schema.

    `evidence_references` carries a non-empty entry because the schema sets
    minItems: 1. Whether that path resolves is a SEPARATE control
    (`evidence-references`) and is never established here.
    """
    return {
        "slice_id": slice_id,
        "section_id": "home",
        "route": "/",
        "cms_content_references": [
            {
                "content_id": PUBLISHED_CONTENT["id"],
                "field_slots": ["heading", "body"],
                "required_status": "published",
            }
        ],
        "layout_id": layout_id,
        "axis_contracts": {
            "frontend": {"renderer_entry_point": "x", "produces": "static_html_document"},
            "cms": {"consumption_boundary": "P8_SAFE_OUTPUT"},
            "backend": {
                "exposure_class": "LOCAL_NON_NETWORK_EXPOSED",
                "state_changing_operations": [],
            },
            "data": {"data_dependencies": []},
            "validation": {"schema_validation": True, "reparse_validation": True},
            "assets": {"asset_references": []},
            "seo": {"audit_mode": "P9_DEPLOYMENT_AUDIT", "expected_exit_code": 0},
            "tests": {"test_entry_point": "t.py"},
        },
        "acceptance_state": "DRAFT",
        "evidence_references": ["evidence.json"],
    }


def _inventory(state: str = "COMPLETE_AWAITING_USER_APPROVAL", complete: bool = True) -> dict:
    return {
        "inventory_id": "P10-SECTION-INVENTORY-v1",
        "inventory_state": state,
        "complete": complete,
        "provenance": {"generated_at": "2026-10-13", "generator": "test fixture"},
        "user_approval": None,
        "sections": [
            {
                "section_completeness": "COMPLETE",
                "section_id": {"provenance": "USER_DECISION", "value": "home"},
            }
        ],
    }


class GateFixtureCase(unittest.TestCase):
    """Base: provides an isolated temp workspace. Synthetic fixtures only."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="p10-gate-test-")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name: str, data) -> str:
        """Write a fixture. A str is written RAW so malformed JSON stays malformed."""
        path = name if os.path.isabs(name) else os.path.join(self.tmp, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            if isinstance(data, str):
                fh.write(data)
            else:
                json.dump(data, fh)
        return path

    def write_raw(self, name: str, text: str) -> str:
        """Write raw (non-JSON-encoded) text, e.g. deliberately malformed JSON."""
        return self.write(name, text)

    def make_build(self, name: str, *, html=False, robots=False, sitemap=False) -> str:
        path = os.path.join(self.tmp, name)
        os.makedirs(path, exist_ok=True)
        if html:
            with open(os.path.join(path, "index.html"), "w", encoding="utf-8") as fh:
                fh.write(MINIMAL_HTML)
        if robots:
            with open(os.path.join(path, "robots.txt"), "w", encoding="utf-8") as fh:
                fh.write(MINIMAL_ROBOTS)
        if sitemap:
            with open(os.path.join(path, "sitemap.xml"), "w", encoding="utf-8") as fh:
                fh.write(MINIMAL_SITEMAP)
        return path


# ==============================================================================
# A. CRITICAL-1 — REQUIRED-CONTROL COMPLETENESS
# ==============================================================================


def _all_pass_report(omit: str = "", rename: bool = False) -> GateReport:
    report = GateReport()
    for cid in REQUIRED_CONTROL_IDS:
        if cid == omit:
            continue
        report.add(ControlResult(cid if not rename else cid + "-x", "REQ", PASS, "ok"))
    return report


class TestRequiredControlCompleteness(unittest.TestCase):
    """The overall verdict is computed against REQUIRED_CONTROL_IDS, not against
    whichever controls happened to run. An omitted control never leaves the
    denominator."""

    def test_empty_report_is_not_an_overall_pass(self) -> None:
        report = GateReport()
        self.assertEqual(len(report.results), 0)
        self.assertNotEqual(report.overall, PASS)
        self.assertEqual(report.overall, FAIL)

    def test_five_pass_nine_missing_is_not_a_pass(self) -> None:
        """Exact scenario from the independent review: a handful of PASS results
        and every other required control absent."""
        report = GateReport()
        for cid in REQUIRED_CONTROL_IDS[:5]:
            report.add(ControlResult(cid, "REQ", PASS, "ok"))
        self.assertEqual(len(report.results), 5)
        self.assertEqual(len(report.missing_required), len(REQUIRED_CONTROL_IDS) - 5)
        self.assertNotEqual(report.overall, PASS)

    def test_omitting_each_required_control_individually_blocks_pass(self) -> None:
        """LOW-2 non-vacuity: every single omission must be detected."""
        for cid in REQUIRED_CONTROL_IDS:
            with self.subTest(omitted=cid):
                report = _all_pass_report(omit=cid)
                self.assertIn(cid, report.missing_required)
                self.assertNotEqual(report.overall, PASS)

    def test_all_required_controls_present_and_passing_is_a_pass(self) -> None:
        # The positive control for the invariant: it is reachable, so the
        # negative assertions above are not vacuously true.
        self.assertEqual(_all_pass_report().overall, PASS)

    def test_renamed_required_control_is_detected(self) -> None:
        report = _all_pass_report(rename=True)
        self.assertEqual(len(report.missing_required), len(REQUIRED_CONTROL_IDS))
        self.assertNotEqual(report.overall, PASS)

    def test_unknown_control_cannot_satisfy_a_renamed_one(self) -> None:
        report = GateReport()
        for cid in REQUIRED_CONTROL_IDS:
            report.add(ControlResult(cid + "-renamed", "REQ", PASS, "ok"))
        report.add(ControlResult("totally-unknown-control", "REQ", PASS, "ok"))
        self.assertEqual(report.overall, FAIL)
        self.assertIn("unknown controls reported", " ".join(report.integrity_problems))

    def test_duplicate_required_control_is_rejected(self) -> None:
        report = _all_pass_report()
        report.add(ControlResult("schema-structural", "REQ", PASS, "again"))
        self.assertIn("schema-structural", report.duplicate_required)
        self.assertNotEqual(report.overall, PASS)

    def test_required_control_demoted_to_not_required_blocks_pass(self) -> None:
        report = GateReport()
        for cid in REQUIRED_CONTROL_IDS:
            report.add(
                ControlResult(cid, "REQ", PASS, "ok", required=(cid != "slice-required-fields"))
            )
        self.assertIn("slice-required-fields", report.demoted_required)
        self.assertNotEqual(report.overall, PASS)

    def test_malformed_result_values_fail_closed(self) -> None:
        for bogus in ("pass", "PASSED", "OK", True, None, 1, "BLOCKED ", ""):
            with self.subTest(result=bogus):
                report = _all_pass_report()
                report.results[0] = ControlResult(
                    report.results[0].control_id, "REQ", bogus, "bad"
                )
                self.assertNotEqual(report.overall, PASS)

    def test_every_verdict_downgrade_prevents_pass(self) -> None:
        """Where feasible: changing any required control's verdict to a non-PASS
        must prevent an overall PASS."""
        for cid in REQUIRED_CONTROL_IDS:
            for verdict in (FAIL, BLOCKED, UNIMPLEMENTED):
                with self.subTest(control=cid, verdict=verdict):
                    report = _all_pass_report()
                    for r in report.results:
                        if r.control_id == cid:
                            r.result = verdict
                    self.assertNotEqual(report.overall, PASS)

    def test_blank_control_id_is_malformed(self) -> None:
        report = _all_pass_report()
        report.add(ControlResult("   ", "REQ", PASS, "blank"))
        self.assertNotEqual(report.overall, PASS)

    def test_unhashable_result_is_reported_malformed_not_crashed(self) -> None:
        for bogus in ([], {}, set(), [1, 2]):
            with self.subTest(result=bogus):
                report = _all_pass_report()
                report.results[0].result = bogus
                self.assertEqual(report.overall, FAIL)
                self.assertTrue(report.malformed_results)

    def test_non_string_control_id_is_reported_malformed_not_crashed(self) -> None:
        for bogus in (None, 5, 1.5, b"x", ["a"], ("a",), {}, True):
            with self.subTest(control_id=bogus):
                report = GateReport()
                for cid in REQUIRED_CONTROL_IDS:
                    report.add(ControlResult(cid, "REQ", PASS, "ok"))
                report.add(ControlResult(bogus, "REQ", PASS, "bad"))
                self.assertEqual(report.overall, FAIL)
                self.assertTrue(report.malformed_results)
                # Must not raise while serialising either.
                self.assertIn("malformed_results", report.to_dict())

    def test_non_string_control_id_does_not_collide_with_a_required_one(self) -> None:
        """A non-string control_id must neither satisfy a required id nor
        hide inside the denominator."""
        report = _all_pass_report()
        report.results[0].control_id = None
        self.assertNotIn("None", report.missing_required)
        self.assertEqual(report.overall, FAIL)
        self.assertTrue(report.malformed_results)
        self.assertIn("None", " ".join(report.unknown_controls))

    def test_report_dict_exposes_completeness(self) -> None:
        payload = _all_pass_report(omit="cms-state-digest").to_dict()
        self.assertIn("cms-state-digest", payload["missing_required_controls"])
        self.assertEqual(payload["required_control_ids"], list(REQUIRED_CONTROL_IDS))
        self.assertEqual(payload["overall"], FAIL)

    def test_run_gate_output_is_never_a_pass_in_practice(self) -> None:
        """run_gate itself always reports every required control in Phase A."""
        tmp = tempfile.mkdtemp(prefix="p10-completeness-")
        try:
            slice_path = os.path.join(tmp, "s.json")
            with open(slice_path, "w", encoding="utf-8") as fh:
                json.dump(_valid_slice(), fh)
            inv_path = os.path.join(tmp, "i.json")
            with open(inv_path, "w", encoding="utf-8") as fh:
                json.dump(_inventory(), fh)
            report = run_gate(
                slice_path=slice_path, inventory_path=inv_path,
                content_types=[HOME_CT], content_records=[PUBLISHED_CONTENT],
                slice_id_history=[], build_dir=None, approval=USER_APPROVAL,
            )
            self.assertEqual(report.missing_required, [])
            self.assertEqual(report.duplicate_required, [])
            self.assertEqual(report.integrity_problems, [])
            self.assertEqual(report.overall, FAIL)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestCliFailClosedOnOmission(unittest.TestCase):
    """End-to-end: the CLI exit status must never be 0 for a non-PASS verdict."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="p10-cli-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _p(self, name, data):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(data if isinstance(data, str) else json.dumps(data))
        return path

    def test_cli_exits_non_zero_when_a_control_is_omitted(self) -> None:
        import framework.sps2.tools.p10_runtime_gate as gate_mod

        real_run = gate_mod.run_gate

        def truncated(**kwargs):
            report = real_run(**kwargs)
            trimmed = GateReport()
            for r in report.results:
                if r.control_id != "cms-state-digest":
                    trimmed.add(r)
            return trimmed

        gate_mod.run_gate = truncated
        try:
            with redirect_stdout(io.StringIO()):
                rc = main([
                    "--slice", self._p("s.json", _valid_slice()),
                    "--inventory", self._p("i.json", _inventory()),
                    "--content-types", self._p("ct.json", [HOME_CT]),
                    "--content", self._p("c.json", [PUBLISHED_CONTENT]),
                    "--slice-id-history", self._p("h.json", []),
                    "--json",
                ])
        finally:
            gate_mod.run_gate = real_run
        self.assertEqual(rc, EXIT_FAILED)

    def test_subprocess_exit_code_is_one_for_a_synthetic_slice(self) -> None:
        slice_path = self._p("s.json", _valid_slice())
        inv = self._p("i.json", _inventory())
        ct = self._p("ct.json", [HOME_CT])
        content = self._p("c.json", [PUBLISHED_CONTENT])
        hist = self._p("h.json", [])
        proc = subprocess.run(
            [sys.executable, "-B", os.path.join(REPO_ROOT, "framework", "sps2", "tools", "p10_runtime_gate.py"),
             "--slice", slice_path, "--inventory", inv, "--content-types", ct,
             "--content", content, "--slice-id-history", hist, "--json"],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        self.assertEqual(proc.returncode, EXIT_FAILED)
        self.assertEqual(json.loads(proc.stdout)["overall"], FAIL)


# ==============================================================================
# B. CRITICAL-2 — REAL STRUCTURAL SCHEMA VALIDATION
# ==============================================================================


class TestSchemaStructuralEnforcement(GateFixtureCase):
    """Structural conformance must be established by actually enforcing the
    applicable constraints, never by required-key presence alone."""

    def setUp(self) -> None:
        super().setUp()
        self.valid = _valid_slice()

    def test_valid_slice_passes_structural_control(self) -> None:
        r = check_schema_structural(_valid_slice())
        self.assertEqual(r.result, PASS)
        self.assertIn("STRUCTURAL", r.detail)

    def test_trailing_newline_pattern_bypass_is_rejected(self) -> None:
        """JSON Schema mandates ECMA-262, where '$' asserts END OF INPUT. Python's
        '$' also matches before a trailing newline, so '^...$' patterns must be
        evaluated at ECMA-262 fidelity or a trailing '\\n' is accepted."""
        doc = _valid_slice()
        for field in ("slice_id", "route", "layout_id"):
            with self.subTest(field=field):
                doc = _valid_slice()
                doc[field] = doc[field] + "\n"
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_trailing_newline_on_pattern_values_is_rejected(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"].update({
            "exposure_class": "NETWORK_EXPOSED_PRODUCTION",
            "security_authorization": {
                "controls": ["AUTHENTICATION"], "authorized_by_role": "USER",
                "authorized_at": "2026-10-13\n", "authorization_reference": "ref",
            },
        })
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_leading_and_trailing_whitespace_route_is_rejected(self) -> None:
        for bad in (" /home", "/home ", "\n/home", "/home\t"):
            with self.subTest(route=bad):
                doc = _valid_slice()
                doc["route"] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_non_object_slice_fails_structural(self) -> None:
        self.assertEqual(check_schema_structural(["not", "an", "object"]).result, FAIL)

    def test_missing_required_property_fails_structural(self) -> None:
        doc = _valid_slice()
        del doc["layout_id"]
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    # -- the five malformed values named in the review ----------------------

    def test_invalid_slice_id_fails_structural(self) -> None:
        for bad in ("slice-p10-01", "SLICE-P10-1", "SLICE-P10-001", "SLICE-P10-ab", "SLICE-10-01", ""):
            with self.subTest(slice_id=bad):
                doc = _valid_slice()
                doc["slice_id"] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_invalid_route_fails_structural(self) -> None:
        for bad in ("Home/Page", "home", "/Home", "/home_page", "/home?x=1", "/home page"):
            with self.subTest(route=bad):
                doc = _valid_slice()
                doc["route"] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_wrong_cms_content_references_type_fails_structural(self) -> None:
        for bad in ("content-1", {}, 0, None, True):
            with self.subTest(value=bad):
                doc = _valid_slice()
                doc["cms_content_references"] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_invalid_layout_id_fails_structural(self) -> None:
        for bad in ("Home_Default", "1home", "home default", "-home", "", "home_default"):
            with self.subTest(layout_id=bad):
                doc = _valid_slice()
                doc["layout_id"] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_invalid_acceptance_state_fails_structural(self) -> None:
        for bad in ("DELIVERED", "approved", "COMPLETE", "", 0, None, ["DRAFT"]):
            with self.subTest(acceptance_state=bad):
                doc = _valid_slice()
                doc["acceptance_state"] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_wrong_scalar_types_fail_structural(self) -> None:
        for key, bad in (("slice_id", 1), ("section_id", 1), ("route", 7), ("layout_id", 3)):
            with self.subTest(field=key):
                doc = _valid_slice()
                doc[key] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    # -- additionalProperties, enums, nested required ------------------------

    def test_unknown_top_level_property_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["sneaky_extra"] = 1
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_unknown_axis_contract_property_fails_structural(self) -> None:
        for axis in ("frontend", "cms", "backend", "data", "validation",
                     "assets", "seo", "tests"):
            with self.subTest(axis=axis):
                doc = _valid_slice()
                doc["axis_contracts"][axis]["sneaky"] = 1
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_missing_required_status_fails_structural(self) -> None:
        doc = _valid_slice()
        del doc["cms_content_references"][0]["required_status"]
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_non_published_required_status_fails_structural(self) -> None:
        for bad in ("draft", "preview", "archived", "PUBLISHED", None):
            with self.subTest(required_status=bad):
                doc = _valid_slice()
                doc["cms_content_references"][0]["required_status"] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_empty_field_slots_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["cms_content_references"][0]["field_slots"] = []
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_empty_cms_content_references_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["cms_content_references"] = []
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_empty_evidence_references_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["evidence_references"] = []
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_non_string_evidence_reference_fails_structural(self) -> None:
        for bad in ([{}], [123], [None]):
            with self.subTest(value=bad):
                doc = _valid_slice()
                doc["evidence_references"] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_boolean_enum_true_is_not_accepted_as_one(self) -> None:
        # Python's True == 1 must not satisfy enum: [true].
        doc = _valid_slice()
        doc["axis_contracts"]["data"]["project_local"] = 1
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_boolean_enum_zero_is_not_accepted_as_false(self) -> None:
        # Python's False == 0 must not satisfy enum: [0].
        doc = _valid_slice()
        doc["axis_contracts"]["seo"]["expected_exit_code"] = True
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_non_boolean_validation_flag_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["validation"]["schema_validation"] = "yes"
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_wrong_nullable_string_type_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["observed_bind_address"] = 12345
        doc["rollback_reference"] = 42
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_nullable_strings_accept_null(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["observed_bind_address"] = None
        doc["rollback_reference"] = None
        self.assertEqual(check_schema_structural(doc).result, PASS)

    def test_bad_axis_enum_fails_structural(self) -> None:
        cases = [
            ("frontend", "produces", "react_app"),
            ("frontend", "encoding_contract", "NONE"),
            ("cms", "consumption_boundary", "RAW"),
            ("seo", "audit_mode", "LOCAL"),
        ]
        for axis, key, bad in cases:
            with self.subTest(axis=axis, key=key):
                doc = _valid_slice()
                doc["axis_contracts"][axis][key] = bad
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_missing_state_changing_operations_fails_structural(self) -> None:
        doc = _valid_slice()
        del doc["axis_contracts"]["backend"]["state_changing_operations"]
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_malformed_state_changing_operation_fails_structural(self) -> None:
        cases = [
            [{"operation": "op"}],
            [{"operation": "op", "required_controls": []}],
            [{"operation": "op", "required_controls": ["AUTHENTICATION", "AUTHENTICATION"]}],
            [{"operation": "op", "required_controls": ["NOPE"]}],
            [{"operation": "", "required_controls": ["AUTHENTICATION"]}],
            [{"operation": "op", "required_controls": ["AUTHENTICATION"], "extra": 1}],
        ]
        for ops in cases:
            with self.subTest(ops=ops):
                doc = _valid_slice()
                doc["axis_contracts"]["backend"]["state_changing_operations"] = ops
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_min_length_constraints_fail_structural(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["tests"]["test_entry_point"] = ""
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    # -- conditionals ---------------------------------------------------------

    def _authorise(self, doc, role="USER", when="2026-10-13", controls=None):
        doc["axis_contracts"]["backend"].update({
            "exposure_class": "NETWORK_EXPOSED_PRODUCTION",
            "security_authorization": {
                "controls": controls if controls is not None else ["AUTHENTICATION"],
                "authorized_by_role": role,
                "authorized_at": when,
                "authorization_reference": "ref",
            },
        })

    def test_network_exposure_without_authorization_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["exposure_class"] = "NETWORK_EXPOSED_PRODUCTION"
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_network_exposure_agent_authorized_fails_structural(self) -> None:
        doc = _valid_slice()
        self._authorise(doc, role="AGENT")
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_network_exposure_duplicate_controls_fails_structural(self) -> None:
        doc = _valid_slice()
        self._authorise(doc, controls=["AUTHENTICATION", "AUTHENTICATION"])
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_network_exposure_empty_reference_fails_structural(self) -> None:
        doc = _valid_slice()
        self._authorise(doc)
        doc["axis_contracts"]["backend"]["security_authorization"]["authorization_reference"] = ""
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_network_exposure_unknown_control_fails_structural(self) -> None:
        doc = _valid_slice()
        self._authorise(doc, controls=["FIREWALL"])
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_network_exposure_malformed_date_fails_structural(self) -> None:
        for bad in ("not-a-date", "2026-13-01", "2026-02-30", "13/10/2026", ""):
            with self.subTest(authorized_at=bad):
                doc = _valid_slice()
                self._authorise(doc, when=bad)
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_valid_network_exposure_is_structurally_valid(self) -> None:
        # The conditional itself must be reachable, so the negative tests above
        # are not vacuous.
        doc = _valid_slice()
        self._authorise(doc)
        self.assertEqual(check_schema_structural(doc).result, PASS)

    def test_approved_without_user_approval_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["acceptance_state"] = "APPROVED"
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_approved_with_null_user_approval_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["acceptance_state"] = "APPROVED"
        doc["user_approval"] = None
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_agent_attributed_user_approval_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["acceptance_state"] = "APPROVED"
        doc["user_approval"] = {
            "decided_by": "ChatGPT", "decided_by_role": "AGENT", "decided_at": "2026-10-13",
        }
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_incomplete_user_approval_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["acceptance_state"] = "APPROVED"
        doc["user_approval"] = {"decided_by": "User"}
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_user_approval_extra_property_fails_structural(self) -> None:
        doc = _valid_slice()
        doc["acceptance_state"] = "APPROVED"
        doc["user_approval"] = {
            "decided_by": "User", "decided_by_role": "USER",
            "decided_at": "2026-10-13", "agent_note": "x",
        }
        self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_user_approval_malformed_date_fails_structural(self) -> None:
        for bad in ("13 Oct 2026", "2026-02-30", "", "not-a-date"):
            with self.subTest(decided_at=bad):
                doc = _valid_slice()
                doc["acceptance_state"] = "APPROVED"
                doc["user_approval"] = {
                    "decided_by": "User", "decided_by_role": "USER", "decided_at": bad,
                }
                self.assertEqual(check_schema_structural(doc).result, FAIL)

    def test_valid_user_approval_is_structurally_valid(self) -> None:
        doc = _valid_slice()
        doc["acceptance_state"] = "APPROVED"
        doc["user_approval"] = {
            "decided_by": "User", "decided_by_role": "USER", "decided_at": "2026-10-13",
        }
        self.assertEqual(check_schema_structural(doc).result, PASS)

    # -- separation of axes ---------------------------------------------------

    def test_structural_pass_does_not_satisfy_published_only(self) -> None:
        draft = _valid_slice()
        draft["cms_content_references"][0]["content_id"] = DRAFT_CONTENT["id"]
        self.assertEqual(check_schema_structural(draft).result, PASS)
        self.assertEqual(check_published_only_content(draft, [DRAFT_CONTENT]).result, FAIL)


class TestValidatorFailClosed(GateFixtureCase):
    """Meta-tests: the validator must never silently ignore an applicable
    constraint, and must not be fooled by the document under test."""

    def test_unknown_keyword_is_blocked_not_ignored(self) -> None:
        for keyword, frag in (("contains", {}), ("not", {}), ("maxLength", 5),
                              ("patternProperties", {}), ("dependentRequired", {}),
                              ("$defs", {}), ("unevaluatedProperties", False)):
            with self.subTest(keyword=keyword):
                schema = {"type": "object", "properties": {"a": {"type": "string"}},
                          keyword: frag}
                with self.assertRaises(Exception) as ctx:
                    _SliceSchemaValidator(schema).errors({"a": "x"})
                self.assertIn(keyword, str(ctx.exception))

    def test_external_ref_is_refused_and_never_fetched(self) -> None:
        schema = {"$ref": "https://example.com/other.json#/a"}
        with self.assertRaises(Exception) as ctx:
            _SliceSchemaValidator(schema).errors({})
        self.assertIn("$ref", str(ctx.exception))

    def test_unresolvable_ref_is_refused(self) -> None:
        with self.assertRaises(Exception) as ctx:
            _SliceSchemaValidator({"$ref": "#/nope"}).errors({})
        self.assertIn("$ref", str(ctx.exception))

    def test_internal_ref_is_resolved(self) -> None:
        schema = {
            "type": "object",
            "properties": {"a": {"$ref": "#/$defs/pos"}},
            "$defs": {"pos": {"type": "integer"}},
        }
        # $defs is not a supported keyword, so the whole schema is refused rather
        # than partially honoured.
        with self.assertRaises(Exception):
            _SliceSchemaValidator(schema).errors({"a": 1})

    def test_unimplemented_format_is_blocked_not_ignored(self) -> None:
        schema = {"type": "object", "properties": {"e": {"type": "string", "format": "email"}}}
        with self.assertRaises(Exception) as ctx:
            _SliceSchemaValidator(schema).errors({"e": "x@y.z"})
        self.assertIn("format", str(ctx.exception))

    def test_date_format_is_enforced_strictly(self) -> None:
        schema = {"type": "object", "properties": {"d": {"type": "string", "format": "date"}}}
        validator = _SliceSchemaValidator(schema)
        self.assertEqual(validator.errors({"d": "2026-10-13"}), [])
        for bad in ("2026-02-30", "2026-13-01", "13/10/2026", "2026-10-13T00:00:00Z", "",
                    "2026-10-13\n", " 2026-10-13", "2026-1-3", "2026-10-13\r"):
            with self.subTest(value=bad):
                self.assertNotEqual(validator.errors({"d": bad}), [])

    def test_pattern_using_a_wildcard_dot_is_blocked_not_approximated(self) -> None:
        """ECMA-262 '.' excludes every line terminator; Python's excludes only \\n.
        Such a pattern cannot be reproduced exactly, so it is BLOCKED."""
        schema = {"type": "object", "properties": {"s": {"type": "string", "pattern": "^a.c$"}}}
        with self.assertRaises(Exception) as ctx:
            _SliceSchemaValidator(schema).errors({"s": "abc"})
        self.assertIn("pattern", str(ctx.exception))

    def test_pattern_without_a_wildcard_dot_is_accepted(self) -> None:
        schema = {"type": "object",
                  "properties": {"s": {"type": "string", "pattern": r"^[a-z0-9/-]+$"}}}
        self.assertEqual(_SliceSchemaValidator(schema).errors({"s": "/home"}), [])
        self.assertNotEqual(_SliceSchemaValidator(schema).errors({"s": "/Home"}), [])

    def test_malformed_keyword_values_block_not_crash_or_pass(self) -> None:
        """A known keyword with a malformed value must BLOCK, never be
        silently skipped (which would report a document CONFORMANT)."""
        cases = [
            ({"type": "object", "properties": {"a": {"type": ["string", "bogus"]}}},
             {"a": "x"}, "type"),
            ({"type": "object", "properties": {"a": {"type": "bogus"}}},
             {"a": "x"}, "type"),
            ({"type": "object", "properties": {"a": {"type": 5}}},
             {"a": "x"}, "type"),
            ({"type": "object", "properties": "not-an-object"},
             {}, "properties"),
            ({"type": "object", "properties": {"a": {"type": "string",
                                                     "minLength": "5"}}},
             {"a": "x"}, "minLength"),
            ({"type": "object", "properties": {"a": {"type": "string",
                                                     "minLength": -5}}},
             {"a": "x"}, "minLength"),
            ({"type": "object", "properties": {"a": {"type": "array",
                                                     "minItems": "3"}}},
             {"a": []}, "minItems"),
            ({"type": "object", "properties": {"a": {"type": "array",
                                                     "uniqueItems": 1}}},
             {"a": [1, 1]}, "uniqueItems"),
            ({"type": "object", "properties": {"a": {"type": "array",
                                                     "uniqueItems": "true"}}},
             {"a": [1, 1]}, "uniqueItems"),
            ({"type": "object", "allOf": "not-a-list"}, {}, "allOf"),
            ({"type": "object", "allOf": [5]}, {}, "allOf"),
            ({"type": "object", "required": "not-a-list"}, {}, "required"),
            ({"type": "object", "enum": "not-a-list"}, {}, "enum"),
        ]
        for schema, instance, keyword in cases:
            with self.subTest(keyword=keyword, schema=schema):
                with self.assertRaises(Exception) as ctx:
                    _SliceSchemaValidator(schema).errors(instance)
                self.assertIn(keyword, str(ctx.exception))

    def test_if_then_else_is_supported(self) -> None:
        """`else` is implemented, so it must not be reported as an
        unsupported keyword."""
        schema = {
            "type": "object",
            "properties": {"a": {"type": "integer"}},
            "if": {"properties": {"a": {"const": 1}}, "required": ["a"]},
            "then": {"required": []},
            "else": {"properties": {"b": {"type": "string"}}},
        }
        self.assertEqual(_SliceSchemaValidator(schema).errors({"a": 2}), [])

    def test_tuple_form_items_is_blocked(self) -> None:
        schema = {"type": "array", "items": [{"type": "string"}]}
        with self.assertRaises(Exception) as ctx:
            _SliceSchemaValidator(schema).errors(["a"])
        self.assertIn("items", str(ctx.exception))

    def test_schema_valued_additional_properties_is_blocked(self) -> None:
        schema = {"type": "object", "additionalProperties": {"type": "string"}}
        with self.assertRaises(Exception) as ctx:
            _SliceSchemaValidator(schema).errors({"a": "x"})
        self.assertIn("additionalProperties", str(ctx.exception))

    def test_absent_additional_properties_is_not_read_as_false(self) -> None:
        # An `if` branch declares `properties` without declaring
        # additionalProperties; it must not be treated as a closed object.
        schema = {
            "type": "object",
            "properties": {"state": {"enum": ["A", "B"]}, "other": {"type": "integer"}},
            "if": {"properties": {"state": {"const": "A"}}, "required": ["state"]},
            "then": {"required": ["other"]},
        }
        errors = _SliceSchemaValidator(schema).errors({"state": "A", "other": 1})
        self.assertEqual(errors, [])
        errors = _SliceSchemaValidator(schema).errors({"state": "A"})
        self.assertNotEqual(errors, [])

    def test_validator_still_matches_the_authoritative_schema(self) -> None:
        """Drift guard: if the schema changes, coverage must be re-audited."""
        with open(os.path.join(REPO_ROOT, "framework", "sps2", "schemas", "p10-slice.schema.json"),
                  encoding="utf-8") as fh:
            schema = json.load(fh)
        self.assertEqual(schema["properties"]["slice_id"]["pattern"], r"^SLICE-P10-[0-9]{2}$")
        self.assertEqual(schema["properties"]["route"]["pattern"], r"^/[a-z0-9/-]*$")
        self.assertEqual(schema["properties"]["layout_id"]["pattern"], r"^[a-z][a-z0-9-]*$")
        self.assertEqual(
            schema["properties"]["cms_content_references"]["items"]["properties"]
            ["required_status"]["enum"], ["published"])
        self.assertFalse(schema.get("$defs"), "new $defs require re-auditing the validator")

    def test_unsupported_keyword_in_an_unreached_branch_still_blocks(self) -> None:
        """The static pre-pass must refuse an unenforced keyword even in a branch
        this instance never takes; otherwise the gate would report CONFORMANT
        while an unenforced constraint sits in the schema."""
        schema = {
            "type": "object",
            "properties": {"state": {"enum": ["A", "B"]}},
            "allOf": [{
                "if": {"properties": {"state": {"const": "A"}}, "required": ["state"]},
                "then": {"properties": {"state": {"not": {}}}},
            }],
        }
        with self.assertRaises(Exception) as ctx:
            _SliceSchemaValidator(schema).errors({"state": "B"})  # then-branch unreached
        self.assertIn("not", str(ctx.exception))

    def test_unsupported_keyword_on_an_absent_property_still_blocks(self) -> None:
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}, "b": {"type": "string", "maxLength": 3}},
        }
        with self.assertRaises(Exception) as ctx:
            _SliceSchemaValidator(schema).errors({"a": "x"})  # 'b' absent entirely
        self.assertIn("maxLength", str(ctx.exception))

    def test_internal_ref_resolution_is_actually_enforced(self) -> None:
        """A $ref that resolves to the WRONG node must change the outcome, so the
        resolver cannot be replaced by a no-op."""
        schema = {
            "type": "object",
            "properties": {"a": {"$ref": "#/$defs/positive"}},
            "$defs": {"positive": {"type": "integer", "minimum": 1}},
        }
        # '$defs' itself is unsupported, so the whole schema is refused first.
        with self.assertRaises(Exception):
            _SliceSchemaValidator(schema).errors({"a": 1})

    def test_internal_ref_to_a_defined_subschema_is_enforced(self) -> None:
        schema = {
            "type": "object",
            "properties": {"a": {"$ref": "#/definitions/positive"}},
            "definitions": {"positive": {"type": "integer"}},
        }
        # 'definitions' is unsupported -> BLOCKED, never silently partial.
        with self.assertRaises(Exception):
            _SliceSchemaValidator(schema).errors({"a": "not-an-int"})

    def test_non_dict_properties_in_a_schema_blocks(self) -> None:
        """A malformed `properties` value must BLOCK rather than raise an
        AttributeError that kills the whole gate."""
        for bad in ("not-an-object", 5, [], None, True):
            with self.subTest(properties=bad):
                schema = {"type": "object", "properties": bad}
                with self.assertRaises(Exception) as ctx:
                    _SliceSchemaValidator(schema).errors({})
                self.assertIn("properties", str(ctx.exception))

    def test_ref_resolving_to_a_wrong_but_supported_target_is_detected(self) -> None:
        """Two refs pointing at different targets must produce different verdicts;
        proves the resolved target is the one actually applied."""
        base = {
            "type": "object",
            "properties": {
                "as_string": {"$ref": "#/properties/target_string"},
                "target_string": {"type": "string"},
            },
        }
        validator = _SliceSchemaValidator(base)
        self.assertEqual(validator.errors({"as_string": "ok"}), [])
        self.assertNotEqual(validator.errors({"as_string": 5}), [])

    def test_every_schema_keyword_is_supported_by_the_validator(self) -> None:
        """No keyword may exist in the authoritative schema that the validator
        cannot enforce; if one appears, the gate must report BLOCKED, not pass."""
        with open(os.path.join(REPO_ROOT, "framework", "sps2", "schemas", "p10-slice.schema.json"),
                  encoding="utf-8") as fh:
            schema = json.load(fh)
        seen = set()
        applicators = {"properties", "items", "allOf", "if", "then", "else"}

        def walk(node, in_properties_map=False):
            if isinstance(node, dict):
                for key, value in node.items():
                    # Under `properties`, the keys are PROPERTY NAMES, not
                    # keywords, and must not be collected as schema keywords.
                    if not in_properties_map:
                        seen.add(key)
                    walk(value, in_properties_map=(key == "properties"))
            elif isinstance(node, list):
                for element in node:
                    walk(element)

        walk(schema)
        from framework.sps2.tools.p10_runtime_gate import _SUPPORTED_KEYWORDS

        unsupported = {
            k for k in seen
            if k not in _SUPPORTED_KEYWORDS and not k.startswith("__")
        }
        self.assertEqual(unsupported, set(), f"unenforced schema keywords: {unsupported}")


# ==============================================================================
# C. HIGH-1 — PUBLISHED-ONLY ENFORCEMENT
# ==============================================================================


class TestPublishedOnlyContent(GateFixtureCase):
    def test_published_content_passes(self) -> None:
        doc = _valid_slice()
        r = check_published_only_content(doc, [PUBLISHED_CONTENT])
        self.assertEqual(r.result, PASS)
        self.assertIn("content-published", r.detail)

    def test_draft_content_is_rejected(self) -> None:
        doc = _valid_slice()
        doc["cms_content_references"][0]["content_id"] = DRAFT_CONTENT["id"]
        r = check_published_only_content(doc, [DRAFT_CONTENT])
        self.assertEqual(r.result, FAIL)
        self.assertIn("not published", r.detail)

    def test_missing_content_is_rejected(self) -> None:
        r = check_published_only_content(_valid_slice(), [])
        self.assertEqual(r.result, FAIL)
        self.assertIn("does not exist", r.detail)

    def test_missing_references_fail(self) -> None:
        doc = _valid_slice()
        del doc["cms_content_references"]
        self.assertEqual(check_published_only_content(doc, []).result, FAIL)

    # -- caller-controlled input cannot disable the published-only rule ------

    def test_missing_required_status_fails_closed(self) -> None:
        doc = _valid_slice()
        del doc["cms_content_references"][0]["required_status"]
        r = check_published_only_content(doc, [PUBLISHED_CONTENT])
        self.assertEqual(r.result, FAIL)
        self.assertIn("required_status", r.detail)

    def test_null_required_status_fails_closed(self) -> None:
        doc = _valid_slice()
        doc["cms_content_references"][0]["required_status"] = None
        self.assertEqual(check_published_only_content(doc, [PUBLISHED_CONTENT]).result, FAIL)

    def test_wrong_required_status_fails_closed(self) -> None:
        for bad in ("draft", "preview", "archived", "BOGUS", "Published"):
            with self.subTest(required_status=bad):
                doc = _valid_slice()
                doc["cms_content_references"][0]["required_status"] = bad
                self.assertEqual(check_published_only_content(doc, [PUBLISHED_CONTENT]).result, FAIL)

    def test_draft_content_rejected_even_with_wrong_required_status(self) -> None:
        """The sharpest bypass test: the record's real status is consulted
        unconditionally, never gated on the author's required_status value."""
        for declared in ("draft", "preview", "archived", "BOGUS", None):
            with self.subTest(required_status=declared):
                doc = _valid_slice()
                doc["cms_content_references"][0]["content_id"] = DRAFT_CONTENT["id"]
                doc["cms_content_references"][0]["required_status"] = declared
                r = check_published_only_content(doc, [DRAFT_CONTENT])
                self.assertEqual(r.result, FAIL)
                self.assertIn("not published", r.detail)

    def test_missing_required_status_with_draft_content_fails_closed(self) -> None:
        doc = _valid_slice()
        doc["cms_content_references"][0]["content_id"] = DRAFT_CONTENT["id"]
        del doc["cms_content_references"][0]["required_status"]
        self.assertEqual(check_published_only_content(doc, [DRAFT_CONTENT]).result, FAIL)

    def test_every_non_published_record_status_is_rejected(self) -> None:
        for status in ("draft", "preview", "archived", "banana", None, "", "PUBLISHED"):
            with self.subTest(status=status):
                doc = _valid_slice()
                record = dict(PUBLISHED_CONTENT, status=status)
                r = check_published_only_content(doc, [record])
                self.assertEqual(r.result, FAIL)
                self.assertIn("not published", r.detail)

    def test_record_with_missing_status_key_fails_closed(self) -> None:
        doc = _valid_slice()
        record = dict(PUBLISHED_CONTENT)
        del record["status"]
        r = check_published_only_content(doc, [record])
        self.assertEqual(r.result, FAIL)

    def test_every_reference_is_checked_not_just_the_first(self) -> None:
        doc = _valid_slice()
        doc["cms_content_references"].append({
            "content_id": DRAFT_CONTENT["id"],
            "field_slots": ["heading"],
            "required_status": "published",
        })
        r = check_published_only_content(doc, [PUBLISHED_CONTENT, DRAFT_CONTENT])
        self.assertEqual(r.result, FAIL)
        self.assertIn("content-draft", r.detail)

    def test_non_dict_reference_fails_closed(self) -> None:
        doc = _valid_slice()
        doc["cms_content_references"].append("not-an-object")
        self.assertEqual(check_published_only_content(doc, [PUBLISHED_CONTENT]).result, FAIL)

    def test_missing_content_id_does_not_resolve_to_an_id_less_record(self) -> None:
        """A reference with no usable content_id must not be satisfied by a record
        that itself carries no id."""
        doc = _valid_slice()
        del doc["cms_content_references"][0]["content_id"]
        r = check_published_only_content(doc, [{"status": "published"}])
        self.assertEqual(r.result, FAIL)
        self.assertIn("no usable content_id", r.detail)

    def test_blank_content_id_is_rejected(self) -> None:
        for bad in ("", "   ", None, 0, []):
            with self.subTest(content_id=bad):
                doc = _valid_slice()
                doc["cms_content_references"][0]["content_id"] = bad
                r = check_published_only_content(doc, [PUBLISHED_CONTENT])
                self.assertEqual(r.result, FAIL)
                self.assertIn("no usable content_id", r.detail)


# ==============================================================================
# D. HIGH-2 — EXPOSURE AND OBSERVED BIND ADDRESS
# ==============================================================================


class TestExposureDeclaration(GateFixtureCase):
    def test_local_exposure_is_blocked_not_pass(self) -> None:
        """A declaration is not an observation. Phase A cannot observe a real bind,
        so the control BLOCKS and the gate can never report an overall PASS."""
        r = check_exposure_declaration(_valid_slice())
        self.assertEqual(r.result, BLOCKED)
        self.assertNotEqual(r.result, PASS)

    def test_missing_exposure_fails(self) -> None:
        doc = _valid_slice()
        del doc["axis_contracts"]["backend"]["exposure_class"]
        self.assertEqual(check_exposure_declaration(doc).result, FAIL)

    def test_unknown_exposure_class_fails(self) -> None:
        """An unrecognised class must never be treated as 'some non-network surface'."""
        for bogus in ("PUBLIC_INTERNET", "NETWORK_EXPOSED", "network_exposed_production",
                      "LOCAL", "local_non_network_exposed"):
            with self.subTest(exposure_class=bogus):
                doc = _valid_slice()
                doc["axis_contracts"]["backend"]["exposure_class"] = bogus
                r = check_exposure_declaration(doc)
                self.assertEqual(r.result, FAIL)
                self.assertIn("not a permitted value", r.detail)

    # -- observed bind reconciliation ---------------------------------------

    def _with_observed(self, observed):
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["observed_bind_address"] = observed
        return doc

    def test_local_with_wildcard_observed_bind_fails(self) -> None:
        for observed in ("0.0.0.0:80", "0.0.0.0", "::", "*", "::0"):
            with self.subTest(observed=observed):
                r = check_exposure_declaration(self._with_observed(observed))
                self.assertEqual(r.result, FAIL)
                self.assertIn("contradictory", r.detail)

    def test_local_with_public_ip_observed_bind_fails(self) -> None:
        for observed in ("203.0.113.7:443", "8.8.8.8:80", "192.0.2.10:3000"):
            with self.subTest(observed=observed):
                self.assertEqual(
                    check_exposure_declaration(self._with_observed(observed)).result, FAIL)

    def test_local_with_malformed_observed_bind_fails(self) -> None:
        for observed in ("not-an-address", "   ", "host:port", "999.999.999.999:80", "::x"):
            with self.subTest(observed=observed):
                self.assertNotEqual(
                    check_exposure_declaration(self._with_observed(observed)).result, PASS)

    def test_missing_observed_address_is_blocked(self) -> None:
        r = check_exposure_declaration(_valid_slice())
        self.assertEqual(r.result, BLOCKED)
        self.assertIn("no observation is present", r.detail)

    def test_null_observed_address_is_blocked(self) -> None:
        r = check_exposure_declaration(self._with_observed(None))
        self.assertEqual(r.result, BLOCKED)

    def test_contradictory_declaration_and_observation_fails(self) -> None:
        doc = self._with_observed("127.0.0.1:8080")
        doc["axis_contracts"]["backend"]["exposure_class"] = "NETWORK_EXPOSED_PRODUCTION"
        doc["axis_contracts"]["backend"]["security_authorization"] = {
            "controls": ["AUTHENTICATION"], "authorized_by_role": "USER",
            "authorized_at": "2026-10-13", "authorization_reference": "x",
        }
        r = check_exposure_declaration(doc)
        self.assertEqual(r.result, FAIL)
        self.assertIn("contradictory", r.detail)

    def test_valid_local_observation_is_still_only_synthetic_evidence(self) -> None:
        """A loopback-shaped string is still an AUTHOR ASSERTION. The schema
        declares observed_bind_address runtime-populated only, so the gate blocks
        and never treats it as a result."""
        r = check_exposure_declaration(self._with_observed("127.0.0.1:8080"))
        self.assertEqual(r.result, BLOCKED)
        self.assertNotEqual(r.result, PASS)
        self.assertIn("declaration, not an observation", r.detail)

    def test_loopback_without_port_is_blocked_not_passed(self) -> None:
        r = check_exposure_declaration(self._with_observed("127.0.0.1"))
        self.assertEqual(r.result, BLOCKED)

    def test_agent_authorization_on_local_surface_fails(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["security_authorization"] = {
            "controls": ["AUTHENTICATION"], "authorized_by_role": "AGENT",
            "authorized_at": "2026-10-13", "authorization_reference": "x",
        }
        r = check_exposure_declaration(doc)
        self.assertEqual(r.result, FAIL)
        self.assertIn("contradictory", r.detail)

    # -- network branch ------------------------------------------------------

    def test_network_exposure_without_authorisation_fails(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["exposure_class"] = "NETWORK_EXPOSED_PRODUCTION"
        r = check_exposure_declaration(doc)
        self.assertEqual(r.result, FAIL)
        self.assertIn("security_authorization", r.detail)

    def test_network_exposure_agent_authorised_fails(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["exposure_class"] = "NETWORK_EXPOSED_PRODUCTION"
        doc["axis_contracts"]["backend"]["security_authorization"] = {
            "controls": ["AUTHENTICATION"], "authorized_by_role": "AGENT",
            "authorized_at": "2026-10-13", "authorization_reference": "x",
        }
        r = check_exposure_declaration(doc)
        self.assertEqual(r.result, FAIL)
        self.assertIn("USER", r.detail)

    def test_network_exposure_user_authorised_still_fails_closed(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["exposure_class"] = "NETWORK_EXPOSED_PRODUCTION"
        doc["axis_contracts"]["backend"]["security_authorization"] = {
            "controls": ["AUTHENTICATION"], "authorized_by_role": "USER",
            "authorized_at": "2026-10-13", "authorization_reference": "x",
        }
        r = check_exposure_declaration(doc)
        self.assertEqual(r.result, FAIL)
        self.assertIn("OBSERVED bind", r.detail)

    def test_network_exposure_with_public_observed_bind_fails_closed(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"].update({
            "exposure_class": "NETWORK_EXPOSED_PRODUCTION",
            "observed_bind_address": "203.0.113.7:443",
            "security_authorization": {
                "controls": ["AUTHENTICATION"], "authorized_by_role": "USER",
                "authorized_at": "2026-10-13", "authorization_reference": "x",
            },
        })
        self.assertEqual(check_exposure_declaration(doc).result, FAIL)


# ==============================================================================
# E. MEDIUM-1 / MEDIUM-2 — EVIDENCE PATH BOUNDARY AND VALIDITY CLAIMS
# ==============================================================================


class TestEvidenceReferences(GateFixtureCase):
    def _doc(self, refs):
        doc = _valid_slice()
        doc["evidence_references"] = refs
        return doc

    def test_missing_references_fail(self) -> None:
        self.assertEqual(check_evidence_references(self._doc([]), self.tmp).result, FAIL)

    def test_unresolved_reference_fails(self) -> None:
        r = check_evidence_references(
            self._doc(["does-not-exist.json"]), self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, FAIL)
        self.assertIn("do not resolve", r.detail)

    def test_malformed_reference_fails(self) -> None:
        self.assertEqual(check_evidence_references(self._doc(["   "]), self.tmp).result, FAIL)

    def test_resolvable_reference_passes(self) -> None:
        self.write("evidence.json", {"axis": "frontend", "passed": True})
        r = check_evidence_references(
            self._doc(["evidence.json"]), self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, PASS)

    def test_pass_detail_does_not_claim_authenticity(self) -> None:
        self.write("evidence.json", {"ok": True})
        r = check_evidence_references(
            self._doc(["evidence.json"]), self.tmp, allowed_root=self.tmp)
        self.assertIn("PATH RESOLUTION ONLY", r.detail)
        self.assertIn("not authenticity", r.detail)

    # -- boundary ------------------------------------------------------------

    def test_external_absolute_path_is_not_evidence(self) -> None:
        for ref in ("/etc/hosts", "/etc/passwd", "/private/etc/hosts"):
            with self.subTest(ref=ref):
                r = check_evidence_references(self._doc([ref]), self.tmp)
                self.assertNotEqual(r.result, PASS)
                self.assertIn("unsupported evidence reference form", r.detail)

    def test_dotdot_traversal_is_rejected(self) -> None:
        r = check_evidence_references(
            self._doc(["../" * 12 + "etc/hosts"]), self.tmp, allowed_root=self.tmp)
        self.assertNotEqual(r.result, PASS)

    def test_symlink_escape_is_rejected(self) -> None:
        link = os.path.join(self.tmp, "innocent-looking.json")
        try:
            os.symlink("/etc/hosts", link)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unsupported on this platform")
        r = check_evidence_references(
            self._doc(["innocent-looking.json"]), self.tmp, allowed_root=self.tmp)
        self.assertNotEqual(r.result, PASS)

    def test_path_resolving_outside_allowed_root_is_rejected(self) -> None:
        inside = tempfile.mkdtemp(prefix="p10-inside-")
        self.addCleanup(shutil.rmtree, inside, True)
        with open(os.path.join(inside, "evidence.json"), "w", encoding="utf-8") as fh:
            json.dump({"ok": True}, fh)
        # A RELATIVE reference that traverses out of the allowed root. Absolute
        # forms are refused earlier, by a different rule.
        r = check_evidence_references(
            self._doc([os.path.join(os.path.relpath(inside, self.tmp), "evidence.json")]),
            self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, FAIL)
        self.assertIn("outside the allowed root", r.detail)

    def test_real_repository_evidence_resolves_against_repo_root(self) -> None:
        candidates = [
            os.path.join("framework", "sps2", "evidence", name)
            for name in sorted(os.listdir(os.path.join(REPO_ROOT, "framework", "sps2", "evidence")))
        ] if os.path.isdir(os.path.join(REPO_ROOT, "framework", "sps2", "evidence")) else []
        candidates = [c for c in candidates if c.endswith(".json")]
        self.assertTrue(candidates, "no in-repo evidence record available to test against")
        r = check_evidence_references(self._doc([candidates[0]]), REPO_ROOT,
                                      allowed_root=REPO_ROOT)
        self.assertEqual(r.result, PASS)

    def test_real_repository_evidence_outside_root_is_rejected(self) -> None:
        doc = self._doc(["../../../../../../etc/hosts"])
        r = check_evidence_references(doc, REPO_ROOT, allowed_root=REPO_ROOT)
        self.assertEqual(r.result, FAIL)


class TestEvidenceValidityClaimsRemainUnimplemented(GateFixtureCase):
    """MEDIUM-2: existence is not authenticity and not freshness.

    Updated for the DEC-7112 implementation (Round 14 authorization): both
    controls are now IMPLEMENTED, but existence alone still satisfies neither —
    an evidence file without dated records fails freshness, and a record
    without a gate_record fails authenticity. The controls keep preventing an
    overall PASS whenever their evidence is absent or thin."""

    def test_freshness_fails_without_a_dated_record(self) -> None:
        # The fixture evidence ({"ok": true}) has no records at all.
        self.write("evidence.json", {"ok": True})
        r = check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, FAIL)
        self.assertFalse(r.permits_pass)

    def test_authenticity_fails_without_a_gate_record(self) -> None:
        # A record that exists but carries no gate_record: existence is not
        # authenticity (DEC-7112 design #2).
        self.write("evidence.json", {"records": [
            {"evidence_id": "EV-P10-999", "result": "PASS",
             "generated_at": "2026-10-16T00:00:00+00:00"}
        ]})
        r = check_evidence_authenticity(_valid_slice(), self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, FAIL)
        self.assertIn("no gate_record", r.detail)

    def test_both_are_required_controls(self) -> None:
        self.assertIn("evidence-freshness", REQUIRED_CONTROL_IDS)
        self.assertIn("evidence-authenticity", REQUIRED_CONTROL_IDS)

    def test_unresolved_semantics_state_the_evidence_limitation(self) -> None:
        joined = " ".join(UNRESOLVED_SEMANTICS)
        self.assertIn("evidence_references locator grammar", joined)
        self.assertIn("no trust root", joined)


# ==============================================================================
# F. HIGH-3 — NON-VACUOUS P9 DEPLOYMENT AUDIT
# ==============================================================================


class TestP9DeploymentAuditNonVacuity(GateFixtureCase):
    def test_absent_build_dir_is_blocked_not_pass(self) -> None:
        r = check_p9_deployment_audit(_valid_slice(), None)
        self.assertEqual(r.result, BLOCKED)
        self.assertNotEqual(r.result, PASS)

    def test_nonexistent_build_dir_is_blocked(self) -> None:
        r = check_p9_deployment_audit(_valid_slice(), os.path.join(self.tmp, "nope"))
        self.assertEqual(r.result, BLOCKED)

    def test_unreadable_slice_document_cannot_pass_the_audit(self) -> None:
        build = self.make_build("complete", html=True, robots=True, sitemap=True)
        r = check_p9_deployment_audit(None, build)
        self.assertNotEqual(r.result, PASS)

    def test_empty_build_dir_is_blocked_not_pass(self) -> None:
        """THE VACUITY CASE: audit_directory() returns exit 0 for an empty
        directory, so exit code alone must never become a PASS."""
        build = self.make_build("empty")
        r = check_p9_deployment_audit(_valid_slice(), build)
        self.assertNotEqual(r.result, PASS)
        self.assertEqual(r.result, BLOCKED)
        self.assertIn("vacuous", r.detail)

    def test_html_only_is_blocked(self) -> None:
        build = self.make_build("html-only", html=True)
        r = check_p9_deployment_audit(_valid_slice(), build)
        self.assertNotEqual(r.result, PASS)
        self.assertIn("robots.txt", r.detail)
        self.assertIn("sitemap.xml", r.detail)

    def test_html_and_robots_but_no_sitemap_is_blocked(self) -> None:
        build = self.make_build("no-sitemap", html=True, robots=True)
        r = check_p9_deployment_audit(_valid_slice(), build)
        self.assertNotEqual(r.result, PASS)
        self.assertIn("sitemap.xml", r.detail)

    def test_html_and_sitemap_but_no_robots_is_blocked(self) -> None:
        build = self.make_build("no-robots", html=True, sitemap=True)
        r = check_p9_deployment_audit(_valid_slice(), build)
        self.assertNotEqual(r.result, PASS)
        self.assertIn("robots.txt", r.detail)

    def test_empty_robots_and_sitemap_are_blocked(self) -> None:
        build = self.make_build("empty-files", html=True, robots=True, sitemap=True)
        for name in ("robots.txt", "sitemap.xml"):
            with open(os.path.join(build, name), "w", encoding="utf-8") as fh:
                fh.write("")
        r = check_p9_deployment_audit(_valid_slice(), build)
        self.assertNotEqual(r.result, PASS)
        self.assertIn("empty", r.detail)

    def test_wrong_audit_mode_is_rejected(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["seo"]["audit_mode"] = "P10_LOCAL_RECHECK"
        build = self.make_build("complete2", html=True, robots=True, sitemap=True)
        r = check_p9_deployment_audit(doc, build)
        self.assertEqual(r.result, FAIL)
        self.assertIn("audit_mode", r.detail)

    def test_complete_synthetic_fixture_is_not_reported_as_a_real_audit(self) -> None:
        """A hand-built directory establishes gate LOGIC ONLY. The control may
        reach PASS, but the result must never claim to be a real audit, and the
        reported digest must be surfaced rather than discarded."""
        build = self.make_build("complete3", html=True, robots=True, sitemap=True)
        r = check_p9_deployment_audit(_valid_slice(), build)
        self.assertEqual(r.result, PASS)
        self.assertIn("audited_artifacts_digest=", r.detail)
        self.assertIn("NOT evidence that a real P10 slice passed", r.detail)

    def test_build_from_a_different_slice_is_rejected(self) -> None:
        """The audit must cover THIS slice's own output. A build directory
        carrying some other slice's page must not satisfy the control."""
        build = self.make_build("other-slice", html=True, robots=True, sitemap=True)
        doc = _valid_slice()
        doc["route"] = "/the-declared-slice-route"
        r = check_p9_deployment_audit(doc, build)
        self.assertEqual(r.result, FAIL)
        self.assertIn("does not contain the declared route", r.detail)

    def test_nested_index_html_satisfies_a_trailing_slash_route(self) -> None:
        build = os.path.join(self.tmp, "nested")
        os.makedirs(os.path.join(build, "home"))
        with open(os.path.join(build, "home", "index.html"), "w", encoding="utf-8") as fh:
            fh.write(MINIMAL_HTML)
        for name, body in (("robots.txt", MINIMAL_ROBOTS), ("sitemap.xml", MINIMAL_SITEMAP)):
            with open(os.path.join(build, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        doc = _valid_slice()
        doc["route"] = "/home/"
        r = check_p9_deployment_audit(doc, build)
        self.assertNotIn("does not contain the declared route", r.detail)

    def test_nested_non_index_html_derives_its_own_route(self) -> None:
        """The declared-route derivation must match the P9 audit's OWN
        derivation (framework/domain/seo/audit.py): a subdirectory page derives
        '/blog/post', NOT '/blog/'."""
        build = os.path.join(self.tmp, "nested-non-index")
        os.makedirs(os.path.join(build, "blog"))
        with open(os.path.join(build, "blog", "post.html"), "w", encoding="utf-8") as fh:
            fh.write(MINIMAL_HTML)
        for name, body in (("robots.txt", MINIMAL_ROBOTS), ("sitemap.xml", MINIMAL_SITEMAP)):
            with open(os.path.join(build, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        doc = _valid_slice()
        doc["route"] = "/blog/post"
        r = check_p9_deployment_audit(doc, build)
        self.assertNotIn("does not contain the declared route", r.detail)
        # And the collapsed form must NOT be derivable from it.
        doc["route"] = "/blog/"
        self.assertIn("does not contain the declared route",
                      check_p9_deployment_audit(doc, build).detail)

    def test_deeply_nested_page_derives_the_full_route(self) -> None:
        build = os.path.join(self.tmp, "deep")
        os.makedirs(os.path.join(build, "a", "b", "c"))
        with open(os.path.join(build, "a", "b", "c", "page.html"),
                  "w", encoding="utf-8") as fh:
            fh.write(MINIMAL_HTML)
        for name, body in (("robots.txt", MINIMAL_ROBOTS), ("sitemap.xml", MINIMAL_SITEMAP)):
            with open(os.path.join(build, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        doc = _valid_slice()
        doc["route"] = "/a/b/c/page"
        self.assertNotIn("does not contain the declared route",
                         check_p9_deployment_audit(doc, build).detail)

    def test_flat_html_satisfies_a_non_trailing_slash_route(self) -> None:
        """p10_to_p9_contract: a flat '{name}.html' derives '/{name}' with NO
        trailing slash."""
        build = self.make_build("flat", robots=True, sitemap=True)
        with open(os.path.join(build, "home.html"), "w", encoding="utf-8") as fh:
            fh.write(MINIMAL_HTML)
        doc = _valid_slice()
        doc["route"] = "/home"
        r = check_p9_deployment_audit(doc, build)
        self.assertNotIn("does not contain the declared route", r.detail)

    def test_root_index_html_derives_the_root_route(self) -> None:
        """The contract's '{name}.html' wording is degenerate for a root
        index.html; the only coherent reading is the root route '/'."""
        build = self.make_build("root", html=True, robots=True, sitemap=True)
        doc = _valid_slice()
        doc["route"] = "/"
        r = check_p9_deployment_audit(doc, build)
        self.assertNotIn("does not contain the declared route", r.detail)

    def test_trailing_slash_and_flat_routes_are_not_interchangeable(self) -> None:
        """'the two forms never derive the same route' per the contract."""
        build = os.path.join(self.tmp, "disambiguate")
        os.makedirs(os.path.join(build, "home"))
        with open(os.path.join(build, "home", "index.html"), "w", encoding="utf-8") as fh:
            fh.write(MINIMAL_HTML)
        for name, body in (("robots.txt", MINIMAL_ROBOTS), ("sitemap.xml", MINIMAL_SITEMAP)):
            with open(os.path.join(build, name), "w", encoding="utf-8") as fh:
                fh.write(body)
        doc = _valid_slice()
        doc["route"] = "/home"  # only '/home/' is derivable from home/index.html
        r = check_p9_deployment_audit(doc, build)
        self.assertIn("does not contain the declared route", r.detail)


# ==============================================================================
# G. MEDIUM-3 — CONTENT vs CONTENTTYPE IDENTIFIERS
# ==============================================================================


class TestLayoutSlotConformance(GateFixtureCase):
    def test_valid_content_to_contenttype_relationship_is_recognised(self) -> None:
        """The correct relationship: Content.type_id -> ContentType.id.
        content_id names a CONTENT, never a ContentType."""
        r = check_layout_slot_conformance(_valid_slice(), [HOME_CT], [PUBLISHED_CONTENT])
        self.assertEqual(r.result, PASS)
        self.assertIn("heading", r.detail)

    def test_content_id_naming_a_contenttype_id_is_rejected(self) -> None:
        """The defect that was fixed: a slice whose content_id is a ContentType id
        used to PASS. It must now fail closed."""
        doc = _valid_slice()
        doc["cms_content_references"][0]["content_id"] = HOME_CT["id"]
        r = check_layout_slot_conformance(doc, [HOME_CT], [PUBLISHED_CONTENT])
        self.assertEqual(r.result, FAIL)
        self.assertIn("no Content record", r.detail)

    def test_missing_content_record_fails_closed_with_reason(self) -> None:
        r = check_layout_slot_conformance(_valid_slice(), [HOME_CT], [])
        self.assertEqual(r.result, FAIL)
        self.assertIn("cannot be established", r.detail)

    def test_content_without_type_id_fails_closed(self) -> None:
        record = dict(PUBLISHED_CONTENT)
        del record["type_id"]
        r = check_layout_slot_conformance(_valid_slice(), [HOME_CT], [record])
        self.assertEqual(r.result, FAIL)
        self.assertIn("no usable type_id", r.detail)

    def test_dangling_contenttype_reference_fails_closed(self) -> None:
        record = dict(PUBLISHED_CONTENT, type_id="ct-nonexistent")
        r = check_layout_slot_conformance(_valid_slice(), [HOME_CT], [record])
        self.assertEqual(r.result, FAIL)
        self.assertIn("dangling", r.detail)

    def test_mismatched_contenttype_is_rejected(self) -> None:
        """The gate must use Content.type_id, not the first ContentType that
        happens to satisfy the layout."""
        record = dict(PUBLISHED_CONTENT, type_id=OTHER_CT["id"])
        r = check_layout_slot_conformance(_valid_slice(), [HOME_CT, OTHER_CT], [record])
        self.assertEqual(r.result, FAIL)
        self.assertIn("ct-other", r.detail)

    def test_empty_contenttype_collection_fails_closed(self) -> None:
        r = check_layout_slot_conformance(_valid_slice(), [], [PUBLISHED_CONTENT])
        self.assertEqual(r.result, FAIL)
        self.assertIn("no ContentType collection", r.detail)

    def test_none_contenttype_collection_fails_closed(self) -> None:
        r = check_layout_slot_conformance(_valid_slice(), None, [PUBLISHED_CONTENT])
        self.assertEqual(r.result, FAIL)

    def test_none_content_record_collection_fails_closed(self) -> None:
        r = check_layout_slot_conformance(_valid_slice(), [HOME_CT], None)
        self.assertEqual(r.result, FAIL)

    def test_unknown_layout_fails_closed(self) -> None:
        r = check_layout_slot_conformance(
            _valid_slice(layout_id="no-such-layout"), [HOME_CT], [PUBLISHED_CONTENT])
        self.assertEqual(r.result, FAIL)
        self.assertIn("did not resolve", r.detail)

    def test_missing_layout_id_fails(self) -> None:
        doc = _valid_slice()
        doc["layout_id"] = ""
        self.assertEqual(check_layout_slot_conformance(doc, [HOME_CT], [PUBLISHED_CONTENT]).result, FAIL)

    def test_declared_slot_absent_from_contenttype_fails(self) -> None:
        doc = _valid_slice()
        doc["cms_content_references"][0]["field_slots"] = ["NOT_A_SLOT"]
        r = check_layout_slot_conformance(doc, [HOME_CT], [PUBLISHED_CONTENT])
        self.assertEqual(r.result, FAIL)
        self.assertIn("absent from", r.detail)

    def test_all_references_are_checked_not_just_the_first(self) -> None:
        doc = _valid_slice()
        doc["cms_content_references"].append({
            "content_id": "content-does-not-exist",
            "field_slots": ["heading"],
            "required_status": "published",
        })
        r = check_layout_slot_conformance(doc, [HOME_CT], [PUBLISHED_CONTENT])
        self.assertEqual(r.result, FAIL)

    def test_cross_control_identifier_semantics_agree(self) -> None:
        """The same fixture must satisfy BOTH controls. They previously read the
        same field as two different entity types."""
        doc = _valid_slice()
        self.assertEqual(check_layout_slot_conformance(doc, [HOME_CT], [PUBLISHED_CONTENT]).result, PASS)
        self.assertEqual(check_published_only_content(doc, [PUBLISHED_CONTENT]).result, PASS)


# ==============================================================================
# H. LOW-1 — DEC-7112 SEMANTICS (implemented under the Round 14 authorization)
# ==============================================================================


def _sha256_file(path: str) -> str:
    with open(path, "rb") as fh:
        return "sha256:" + hashlib.sha256(fh.read()).hexdigest()


def _canonical_digest_of(value) -> str:
    """The gate's own canonical-JSON digest, for building fixture claims."""
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class TestDec7112DigestControls(GateFixtureCase):
    """DEC-7112 designs #3/#4: canonical JSON + SHA-256, recomputed by the gate,
    fail-closed on null or mismatch. The inventory's recorded value is written
    only by an authorized regeneration — the tests never write one into the
    real inventory."""

    def _inv(self, cms=None, p8=None) -> dict:
        inv = _inventory()
        inv["provenance"]["cms_state_digest"] = cms
        inv["provenance"]["p8_contract_digest"] = p8
        return inv

    def _cms_files(self):
        """A synthetic CMS state set in the temp workspace."""
        content = self.write("content.json", [{"id": "c1", "title": "t"}])
        types = self.write("content_types.json", [HOME_CT])
        revs = self.write("revisions.jsonl", "{\"id\": \"r1\"}\n")
        return content, types, revs

    def test_null_digest_fails_closed(self) -> None:
        for control, key in ((check_cms_state_digest, "cms_state_digest"),
                             (check_p8_contract_digest, "p8_contract_digest")):
            with self.subTest(control=control.__name__):
                r = control(self._inv())
                self.assertEqual(r.result, FAIL)
                self.assertIn("null", r.detail)
                self.assertFalse(r.permits_pass)

    def test_missing_provenance_fails_closed(self) -> None:
        self.assertEqual(check_cms_state_digest({}).result, FAIL)
        self.assertEqual(check_p8_contract_digest(None).result, FAIL)
        self.assertEqual(check_cms_state_digest({"provenance": "x"}).result, FAIL)

    def test_mismatch_fails_and_names_both_values(self) -> None:
        inv = self._inv(cms="sha256:" + "0" * 64)
        r = check_cms_state_digest(inv)
        self.assertEqual(r.result, FAIL)
        self.assertIn("mismatch", r.detail)
        self.assertIn("sha256:" + "0" * 64, r.detail)

    def test_non_string_digest_claim_fails(self) -> None:
        r = check_cms_state_digest(self._inv(cms=12345))
        self.assertEqual(r.result, FAIL)

    def test_matching_digest_passes_against_the_real_repo_state(self) -> None:
        """Compute the canonical digest over the REAL repository CMS files and
        inject it into a fixture inventory. If the real files change, this test
        fails — that is the control working (state changed); regenerate the
        value only via an authorized inventory regeneration."""
        import framework.sps2.tools.p10_runtime_gate as gate_mod
        cms_actual, err = gate_mod._canonical_state_digest(gate_mod._cms_state_paths())
        self.assertEqual(err, "")
        p8_actual, err = gate_mod._canonical_state_digest(gate_mod._p8_contract_paths())
        self.assertEqual(err, "")
        inv = self._inv(cms=cms_actual, p8=p8_actual)
        self.assertEqual(check_cms_state_digest(inv).result, PASS)
        self.assertEqual(check_p8_contract_digest(inv).result, PASS)

    def test_content_edit_changes_the_digest(self) -> None:
        """Tampering: editing a CMS file flips the recomputed digest."""
        content, types, revs = self._cms_files()
        # Point the gate's path helpers at the synthetic set via monkeypatching
        # the module-level path lists is intrusive; instead verify the digest
        # function itself is content-sensitive.
        import framework.sps2.tools.p10_runtime_gate as gate_mod
        d1, _ = gate_mod._canonical_state_digest([content, types, revs])
        with open(content, "w", encoding="utf-8") as fh:
            json.dump([{"id": "c1", "title": "t"}], fh)
        d2, _ = gate_mod._canonical_state_digest([content, types, revs])
        self.assertEqual(d1, d2, "identical logical content (re-serialised) must digest identically")
        with open(content, "w", encoding="utf-8") as fh:
            fh.write("tampered")
        d3, _ = gate_mod._canonical_state_digest([content, types, revs])
        self.assertNotEqual(d1, d3)

    def test_key_reordering_does_not_change_the_digest(self) -> None:
        """Canonicalization: sorted keys mean reordered keys still pass. Two
        files at the SAME path (sequentially re-written) with reordered keys
        and different whitespace digest identically."""
        import framework.sps2.tools.p10_runtime_gate as gate_mod
        a = self.write("canonical.json", None)
        with open(a, "w", encoding="utf-8") as fh:
            fh.write('{"b": 1, "a": 2}')
        d1, _ = gate_mod._canonical_state_digest([a])
        with open(a, "w", encoding="utf-8") as fh:
            fh.write('{\n  "a": 2,\n  "b": 1\n}')
        d2, _ = gate_mod._canonical_state_digest([a])
        self.assertEqual(d1, d2)

    def test_unreadable_state_file_fails_closed(self) -> None:
        import framework.sps2.tools.p10_runtime_gate as gate_mod
        bad = self.write_raw("bad.json", "{ not json")
        digest, err = gate_mod._canonical_state_digest([bad])
        self.assertIsNone(digest)
        self.assertIn("malformed JSON", err)

    def test_digests_are_deliberately_separate(self) -> None:
        """Design #4: a content edit must not invalidate the type contract and
        vice versa — the two digests cover disjoint file sets."""
        import framework.sps2.tools.p10_runtime_gate as gate_mod
        cms_paths = gate_mod._cms_state_paths()
        p8_paths = gate_mod._p8_contract_paths()
        self.assertNotEqual(set(cms_paths), set(p8_paths))
        self.assertEqual(set(p8_paths) - set(cms_paths), set())  # contract ⊆ state files

    def test_recomputed_digests_of_the_real_state_are_stable(self) -> None:
        import framework.sps2.tools.p10_runtime_gate as gate_mod
        d1, _ = gate_mod._canonical_state_digest(gate_mod._cms_state_paths())
        d2, _ = gate_mod._canonical_state_digest(gate_mod._cms_state_paths())
        self.assertIsNotNone(d1)
        self.assertEqual(d1, d2)
        self.assertTrue(d1.startswith("sha256:"))


class TestDec7112ReqP10_07Reconciliation(GateFixtureCase):
    """DEC-7112 design #5: set-compare declared operations against the backend
    operation manifest. Missing manifest fails closed."""

    def test_missing_manifest_fails_closed(self) -> None:
        # The real repository now ships operations.json (P10 completion,
        # commit 1279cd6), so the missing-manifest scenario is exercised in
        # an isolated root where the manifest does not exist.
        with mock.patch(
            "framework.sps2.tools.p10_runtime_gate._repo_root", return_value=self.tmp
        ):
            r = check_req_p10_07_reconciliation(_valid_slice())
        self.assertEqual(r.result, FAIL)
        self.assertIn("fail-closed", r.detail)
        self.assertIn("operations.json", r.detail)

    def test_unreadable_slice_fails(self) -> None:
        self.assertEqual(check_req_p10_07_reconciliation(None).result, FAIL)

    def test_non_list_declaration_fails(self) -> None:
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["state_changing_operations"] = "none"
        self.assertEqual(check_req_p10_07_reconciliation(doc).result, FAIL)

    def _reconcile_with_manifest(self, declared, manifest):
        root = Path(self.tmp)
        (root / "framework" / "domain" / "backend").mkdir(parents=True, exist_ok=True)
        (root / "framework" / "domain" / "backend" / "operations.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        doc = _valid_slice()
        doc["axis_contracts"]["backend"]["state_changing_operations"] = declared
        with mock.patch("framework.sps2.tools.p10_runtime_gate._repo_root", return_value=str(root)):
            return check_req_p10_07_reconciliation(doc)

    def test_schema_conformant_operation_objects_match_manifest(self) -> None:
        declared = [{"operation": "save", "required_controls": ["AUTHENTICATION"]}]
        manifest = {"operations": [{"name": "save", "required_controls": ["AUTHENTICATION"]}]}
        result = self._reconcile_with_manifest(declared, manifest)
        self.assertEqual(result.result, PASS)
        self.assertIn("declared state_changing_operations=['save']", result.detail)

    def test_undeclared_manifest_operation_fails(self) -> None:
        declared = [{"operation": "save", "required_controls": ["AUTHENTICATION"]}]
        manifest = {
            "operations": [
                {"name": "save", "required_controls": ["AUTHENTICATION"]},
                {"name": "delete", "required_controls": ["AUTHORIZATION"]},
            ]
        }
        result = self._reconcile_with_manifest(declared, manifest)
        self.assertEqual(result.result, FAIL)
        self.assertIn("manifest operations absent from declaration: ['delete']", result.detail)

    def test_phantom_declared_operation_fails(self) -> None:
        declared = [
            {"operation": "save", "required_controls": ["AUTHENTICATION"]},
            {"operation": "delete", "required_controls": ["AUTHORIZATION"]},
        ]
        manifest = {"operations": [{"name": "save", "required_controls": ["AUTHENTICATION"]}]}
        result = self._reconcile_with_manifest(declared, manifest)
        self.assertEqual(result.result, FAIL)
        self.assertIn("declared operations absent from manifest: ['delete']", result.detail)

    def test_malformed_declared_operation_fails_closed(self) -> None:
        for declared in (
            ["save"],
            [{"required_controls": ["AUTHENTICATION"]}],
            [{"operation": "   ", "required_controls": ["AUTHENTICATION"]}],
            [{"operation": "save"}],
            [{"operation": "save", "required_controls": []}],
            [{"operation": "save", "required_controls": "AUTHENTICATION"}],
            [{"operation": "save", "required_controls": [""]}],
        ):
            with self.subTest(declared=declared):
                result = self._reconcile_with_manifest(
                    declared, {"operations": [{"name": "save"}]}
                )
                self.assertEqual(result.result, FAIL)
                self.assertIn("malformed operation entries", result.detail)

    def test_malformed_manifest_operation_fails_closed(self) -> None:
        declared = [{"operation": "save", "required_controls": ["AUTHENTICATION"]}]
        for operations in (
            [None],
            [{"operation": "save"}],
            [{"name": "   "}],
            [{"name": "save"}],
            [{"name": "save", "required_controls": []}],
            [{"name": "save", "required_controls": "AUTHENTICATION"}],
            [{"name": "save", "required_controls": [""]}],
        ):
            with self.subTest(operations=operations):
                result = self._reconcile_with_manifest(
                    declared, {"operations": operations}
                )
                self.assertEqual(result.result, FAIL)
                self.assertIn("malformed operation entries", result.detail)

    def test_non_list_manifest_fails_closed_without_reconciliation(self) -> None:
        declared = [{"operation": "save", "required_controls": ["AUTHENTICATION"]}]
        result = self._reconcile_with_manifest(declared, "save")
        self.assertEqual(result.result, FAIL)
        self.assertIn("missing, unreadable, or carries no operations[] array", result.detail)


class TestDec7112ApprovalStateInteraction(GateFixtureCase):
    """DEC-7112 design #6 + APPROVAL-MECHANISM: OPTION A — the two-locus
    coherence machine. The gate stays read-only throughout."""

    def test_pre_transition_state_is_coherent(self) -> None:
        r = check_approval_state_interaction(_inventory())
        self.assertEqual(r.result, PASS)
        self.assertIn("never writes", r.detail)

    def test_non_terminal_state_with_set_approval_is_incoherent(self) -> None:
        inv = _inventory()
        inv["user_approval"] = {"decided_by": "User"}
        r = check_approval_state_interaction(inv)
        self.assertEqual(r.result, FAIL)
        self.assertIn("incoherent", r.detail)

    def test_terminal_state_with_null_approval_is_refused(self) -> None:
        """THE negative case from the adopted design: gate-pass + null approval
        is refused — a gate pass alone is never sufficient."""
        inv = _inventory(state="COMPLETE_VERIFIED_USER_APPROVED")
        r = check_approval_state_interaction(inv)
        self.assertEqual(r.result, FAIL)
        self.assertIn("never sufficient", r.detail)

    def test_unreadable_inventory_fails(self) -> None:
        self.assertEqual(check_approval_state_interaction(None).result, FAIL)


class TestControlResultVocabulary(GateFixtureCase):
    """Kept from LOW-1: the result vocabulary still blocks pass in isolation."""

    def test_non_pass_results_block_in_isolation(self) -> None:
        self.assertFalse(ControlResult("x", "REQ", UNIMPLEMENTED, "d").permits_pass)
        self.assertFalse(ControlResult("x", "REQ", BLOCKED, "d").permits_pass)
        self.assertFalse(ControlResult("x", "REQ", FAIL, "d").permits_pass)
        self.assertTrue(ControlResult("x", "REQ", PASS, "d").permits_pass)


class TestDec7112EvidenceFreshness(GateFixtureCase):
    """DEC-7112 design #1 as amended by Round 14: parseable RFC 3339 timestamp
    required; NO maximum-age window — age alone never fails a record."""

    def _evidence(self, *records) -> None:
        self.write("evidence.json", {"records": list(records)})

    def _dated(self, **overrides) -> dict:
        rec = {
            "evidence_id": "EV-P10-100",
            "result": "PASS",
            "generated_at": "2020-01-01T00:00:00+00:00",
            "observed_result": "something observed",
        }
        rec.update(overrides)
        return rec

    def test_dated_record_passes_regardless_of_age(self) -> None:
        """THE Round 14 policy: a 2020 timestamp passes in 2026 — no window."""
        self._evidence(self._dated())
        r = check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, PASS)
        self.assertIn("No maximum-age window", r.detail)

    def test_missing_timestamp_fails(self) -> None:
        rec = self._dated()
        del rec["generated_at"]
        self._evidence(rec)
        r = check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, FAIL)
        self.assertIn("EV-P10-100", r.detail)

    def test_unparseable_timestamp_fails(self) -> None:
        self._evidence(self._dated(generated_at="not-a-date"))
        self.assertEqual(
            check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp).result,
            FAIL)

    def test_naive_timestamp_without_offset_fails(self) -> None:
        """An offset-less timestamp cannot be placed on a timeline without
        guessing a timezone; the gate does not guess."""
        self._evidence(self._dated(generated_at="2026-10-16T12:00:00"))
        r = check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, FAIL)
        self.assertIn("offset", r.detail)

    def test_z_suffix_timestamp_is_accepted(self) -> None:
        self._evidence(self._dated(generated_at="2026-10-16T12:00:00Z"))
        self.assertEqual(
            check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp).result,
            PASS)

    def test_timestamp_field_fallback(self) -> None:
        """The evidence schema's own `timestamp` field is honoured when
        generated_at is absent."""
        self._evidence({"evidence_id": "EV-P10-101", "result": "BLOCKED",
                        "timestamp": "2026-10-16T17:00:00+06:00"})
        self.assertEqual(
            check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp).result,
            PASS)

    def test_one_undated_record_fails_the_whole_control(self) -> None:
        self._evidence(self._dated(), self._dated(evidence_id="EV-P10-102",
                                                  generated_at=None))
        r = check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, FAIL)
        self.assertIn("EV-P10-102", r.detail)

    def test_non_string_timestamp_fails(self) -> None:
        self._evidence(self._dated(generated_at=20261016))
        self.assertEqual(
            check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp).result,
            FAIL)

    def test_unresolvable_evidence_reference_fails(self) -> None:
        r = check_evidence_freshness(_valid_slice(), self.tmp, allowed_root=self.tmp)
        self.assertEqual(r.result, FAIL)
        self.assertIn("does not resolve", r.detail)


class TestDec7112EvidenceAuthenticity(GateFixtureCase):
    """DEC-7112 design #2: the gate-record cross-check. The gate recomputes
    digests of the artifacts a gate_record claims; contradiction fails, naming
    the field. Content integrity + provenance recording, nothing more."""

    def setUp(self) -> None:
        super().setUp()
        self.artifact = self.write("artifact.txt", "deterministic artifact bytes")
        self.artifact_digest = _sha256_file(self.artifact)

    def _record(self, **overrides) -> dict:
        rec = {
            "evidence_id": "EV-P10-200",
            "result": "PASS",
            "generated_at": "2026-10-16T00:00:00+00:00",
            "gate_record": {
                "schema": "sps2.p10-gate-record/v1",
                "producing_command": "python3 -B framework/sps2/tools/p10_runtime_gate.py --slice x",
                "emitting_tool_version": "p10_runtime_gate Phase A",
                "utc_timestamp": "2026-10-16T00:00:00Z",
                "inputs": {"artifact.txt": self.artifact_digest},
            },
        }
        rec.update(overrides)
        return rec

    def _gate_record(self, **overrides) -> dict:
        record = {
            "schema": "sps2.p10-gate-record/v1",
            "producing_command": "python3 -B framework/sps2/tools/p10_runtime_gate.py --slice x",
            "emitting_tool_version": "p10_runtime_gate Phase A",
            "utc_timestamp": "2026-10-16T00:00:00Z",
            "inputs": {"artifact.txt": self.artifact_digest},
        }
        record.update(overrides)
        return record

    def _run(self, *records) -> Any:
        self.write("evidence.json", {"records": list(records)})
        return check_evidence_authenticity(_valid_slice(), self.tmp, allowed_root=self.tmp)

    def test_consistent_gate_record_passes(self) -> None:
        r = self._run(self._record())
        self.assertEqual(r.result, PASS)
        self.assertIn("NOT cryptographic authenticity", r.detail)

    def test_digest_mismatch_fails_naming_the_field(self) -> None:
        """THE tampering case: the artifact changed after the gate_record was
        written; the recomputed digest contradicts the claim."""
        with open(self.artifact, "w", encoding="utf-8") as fh:
            fh.write("tampered bytes")
        r = self._run(self._record())
        self.assertEqual(r.result, FAIL)
        self.assertIn("gate_record.inputs", r.detail)
        self.assertIn(self.artifact_digest, r.detail)

    def test_foreign_digest_claim_fails(self) -> None:
        incomplete = self._record()["gate_record"]
        incomplete["inputs"] = {"artifact.txt": "md5:deadbeef"}
        r = self._run(self._record(gate_record=incomplete))
        self.assertEqual(r.result, FAIL)
        self.assertIn("invalid sha256 digest claim", r.detail)

    def test_path_outside_allowed_root_fails(self) -> None:
        incomplete = self._record()["gate_record"]
        incomplete["inputs"] = {"../../../../etc/hosts": "sha256:" + "0" * 64}
        r = self._run(self._record(gate_record=incomplete))
        self.assertEqual(r.result, FAIL)
        self.assertIn("outside", r.detail)

    def test_unreadable_claimed_path_fails(self) -> None:
        incomplete = self._record()["gate_record"]
        incomplete["inputs"] = {"no-such-artifact.txt": "sha256:" + "0" * 64}
        r = self._run(self._record(gate_record=incomplete))
        self.assertEqual(r.result, FAIL)
        self.assertIn("unreadable", r.detail)

    def test_non_object_gate_record_fails(self) -> None:
        r = self._run(self._record(gate_record="trust me"))
        self.assertEqual(r.result, FAIL)
        self.assertIn("no gate_record", r.detail)

    def test_record_without_gate_record_fails(self) -> None:
        rec = self._record()
        del rec["gate_record"]
        r = self._run(rec)
        self.assertEqual(r.result, FAIL)
        self.assertIn("existence is not authenticity", r.detail)

    def test_gate_record_schema_is_required_and_exact(self) -> None:
        for schema in (None, "", "sps2.p10-gate-record/v2"):
            with self.subTest(schema=schema):
                record = self._gate_record(schema=schema)
                result = self._run(self._record(gate_record=record))
                self.assertEqual(result.result, FAIL)
                self.assertIn("incomplete or malformed gate_record", result.detail)

    def test_producing_command_and_tool_version_are_required(self) -> None:
        overrides = [
            {"producing_command": None},
            {"producing_command": "   "},
            {"emitting_tool_version": None},
            {"emitting_tool_version": ""},
        ]
        for override in overrides:
            with self.subTest(override=override):
                result = self._run(self._record(gate_record=self._gate_record(**override)))
                self.assertEqual(result.result, FAIL)
                self.assertIn("incomplete or malformed gate_record", result.detail)

    def test_utc_timestamp_must_be_parseable_and_zero_offset(self) -> None:
        for timestamp in (None, "", "not-a-date", "2026-10-16T00:00:00",
                          "2026-10-16T06:00:00+06:00", "2026-10-16T00:00:00-00:00"):
            with self.subTest(timestamp=timestamp):
                record = self._gate_record(utc_timestamp=timestamp)
                result = self._run(self._record(gate_record=record))
                self.assertEqual(result.result, FAIL)
                self.assertIn("utc_timestamp", result.detail)

    def test_gate_record_requires_at_least_one_digest_claim(self) -> None:
        for claims in (None, {}, {"inputs": {}}, {"outputs": {}}):
            with self.subTest(claims=claims):
                record = self._gate_record()
                record.pop("inputs", None)
                record.pop("outputs", None)
                if isinstance(claims, dict):
                    record.update(claims)
                result = self._run(self._record(gate_record=record))
                self.assertEqual(result.result, FAIL)
                self.assertIn("no usable inputs/outputs digest claims", result.detail)

    def test_malformed_digest_claims_fail_closed(self) -> None:
        bad_digests = (
            None,
            17,
            "",
            "sha256",
            "md5:deadbeef",
            "sha256:" + "A" * 64,
            "sha256:" + "0" * 63,
        )
        for claimed in bad_digests:
            with self.subTest(claimed=claimed):
                record = self._gate_record(inputs={"artifact.txt": claimed})
                result = self._run(self._record(gate_record=record))
                self.assertEqual(result.result, FAIL)
                self.assertIn("invalid sha256 digest claim", result.detail)

    def test_symlink_escape_in_a_claimed_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="p10-gate-escape-") as outside:
            outside_path = Path(outside) / "secret.txt"
            outside_path.write_bytes(b"outside")
            link = Path(self.tmp) / "escape.txt"
            os.symlink(outside_path, link)
            record = self._gate_record(inputs={"escape.txt": _sha256_file(outside_path)})
            result = self._run(self._record(gate_record=record))
            self.assertEqual(result.result, FAIL)
            self.assertIn("outside the allowed root", result.detail)

    def test_outputs_claims_are_cross_checked_too(self) -> None:
        out = self.write("out.html", "<html></html>")
        complete = self._record()["gate_record"]
        complete["outputs"] = {"out.html": _sha256_file(out)}
        r = self._run(self._record(gate_record=complete))
        self.assertEqual(r.result, PASS)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("<html>mutated</html>")
        mutated = self._record()["gate_record"]
        mutated["outputs"] = {"out.html": _sha256_file(self.artifact)}
        r = self._run(self._record(gate_record=mutated))
        self.assertEqual(r.result, FAIL)
        self.assertIn("gate_record.outputs", r.detail)

    def test_control_never_writes_anything(self) -> None:
        """The authenticity cross-check is read-only over the claimed paths."""
        before = open(self.artifact, "rb").read()
        self._run(self._record())
        self.assertEqual(open(self.artifact, "rb").read(), before)

    def test_demoted_control_permits_pass_but_still_blocks_the_overall_verdict(self) -> None:
        """required=False makes a single control non-blocking on its own, but the
        required-control denominator still catches the demotion."""
        self.assertTrue(ControlResult("x", "REQ", FAIL, "d", required=False).permits_pass)
        report = GateReport()
        for cid in REQUIRED_CONTROL_IDS:
            report.add(
                ControlResult(cid, "REQ", PASS, "ok", required=(cid != "cms-state-digest"))
            )
        self.assertNotEqual(report.overall, PASS)


# ==============================================================================
# I. Remaining controls + orchestration
# ==============================================================================


class TestSliceRequiredFields(GateFixtureCase):
    def test_all_eight_axes_pass(self) -> None:
        self.assertEqual(check_slice_required_fields(_valid_slice()).result, PASS)

    def test_missing_axis_fails(self) -> None:
        doc = _valid_slice()
        del doc["axis_contracts"]["seo"]
        r = check_slice_required_fields(doc)
        self.assertEqual(r.result, FAIL)
        self.assertIn("seo", r.detail)

    def test_absent_axis_contracts_fails(self) -> None:
        self.assertEqual(check_slice_required_fields({"slice_id": "SLICE-P10-01"}).result, FAIL)


class TestInventoryPreconditions(GateFixtureCase):
    def test_complete_inventory_passes(self) -> None:
        self.assertEqual(check_inventory_preconditions(_inventory()).result, PASS)

    def test_missing_field_fails(self) -> None:
        inv = _inventory()
        del inv["sections"]
        self.assertEqual(check_inventory_preconditions(inv).result, FAIL)

    def test_complete_true_without_generator_fails(self) -> None:
        inv = _inventory()
        inv["provenance"]["generator"] = "   "
        self.assertEqual(check_inventory_preconditions(inv).result, FAIL)

    def test_complete_true_with_incomplete_section_fails(self) -> None:
        inv = _inventory()
        inv["sections"][0]["section_completeness"] = "INCOMPLETE"
        self.assertEqual(check_inventory_preconditions(inv).result, FAIL)

    def test_awaiting_user_approval_state_is_observed_not_failed(self) -> None:
        r = check_inventory_preconditions(_inventory())
        self.assertEqual(r.result, PASS)
        self.assertIn("COMPLETE_AWAITING_USER_APPROVAL", r.detail)

    def test_claims_verified_state_fails_closed(self) -> None:
        r = check_inventory_preconditions(_inventory(state="COMPLETE_VERIFIED_USER_APPROVED"))
        self.assertEqual(r.result, FAIL)
        self.assertIn("does not certify", r.detail)

    def test_malformed_inventory_fails(self) -> None:
        self.assertEqual(check_inventory_preconditions("not-json-object").result, FAIL)

    def test_truthy_non_boolean_complete_is_not_a_demotion_escape(self) -> None:
        for bogus in (1, "true", "yes", []):
            with self.subTest(complete=bogus):
                inv = _inventory()
                inv["complete"] = bogus
                inv["sections"] = []
                inv.pop("provenance", None)
                r = check_inventory_preconditions(inv)
                self.assertEqual(r.result, FAIL)
                self.assertIn("not a boolean", r.detail)

    def test_malformed_section_entries_fail_closed_without_crashing(self) -> None:
        """A section that cannot name itself (null/string/absent
        section_id) must fail closed, whether or not it is marked
        COMPLETE, instead of crashing on .get()."""
        for section in ({"section_id": None, "section_completeness": "INCOMPLETE"},
                        {"section_id": "home", "section_completeness": "INCOMPLETE"},
                        {"section_completeness": "INCOMPLETE"},
                        "not-a-dict"):
            with self.subTest(section=section):
                inv = _inventory()
                inv["sections"] = [section]
                r = check_inventory_preconditions(inv)
                self.assertEqual(r.result, FAIL)

    def test_complete_section_with_unusable_section_id_fails(self) -> None:
        """NEW-5 residual: a section marked COMPLETE must still be able to
        name itself; completeness is not established otherwise."""
        for identifier in (None, "home", 5, []):
            with self.subTest(section_id=identifier):
                inv = _inventory()
                inv["sections"] = [
                    {"section_id": identifier, "section_completeness": "COMPLETE"}
                ]
                r = check_inventory_preconditions(inv)
                self.assertEqual(r.result, FAIL)
                self.assertIn("no usable section_id", r.detail)

    def test_complete_false_is_observed_without_requiring_sections(self) -> None:
        inv = _inventory(complete=False)
        inv["sections"] = []
        inv.pop("provenance", None)
        self.assertEqual(check_inventory_preconditions(inv).result, PASS)


class TestApprovalAuthenticity(GateFixtureCase):
    """The decision-record approval path: a slice that makes no approval claim
    of its own, so the separately supplied approval is attributed under the
    pre-existing contract. Slice binding is covered by
    TestApprovalAuthenticitySliceBinding."""

    def test_user_approval_passes(self) -> None:
        self.assertEqual(check_approval_authenticity(_valid_slice(), USER_APPROVAL).result, PASS)

    def test_agent_attributed_approval_fails(self) -> None:
        self.assertEqual(check_approval_authenticity(_valid_slice(), AGENT_APPROVAL).result, FAIL)

    def test_null_approval_fails(self) -> None:
        self.assertEqual(check_approval_authenticity(_valid_slice(), None).result, FAIL)

    def test_malformed_approval_fails(self) -> None:
        self.assertEqual(
            check_approval_authenticity(_valid_slice(), ["not", "a", "dict"]).result, FAIL)

    def test_missing_decision_date_fails(self) -> None:
        r = check_approval_authenticity(
            _valid_slice(), {"state": "APPROVED", "decided_by": "User"})
        self.assertEqual(r.result, FAIL)


class TestApprovalAuthenticitySliceBinding(GateFixtureCase):
    """D-1: REQ-P10-09 c.6 makes THIS gate responsible for rejecting
    agent-attributed approval, and the slice schema's $comment assigns that
    obligation here ("that user_approval reflects a real User decision rather
    than an agent assertion"). An approval belonging to a different record
    cannot discharge it. Before the fix, this control judged only the CLI
    `--approval` object and never read the slice's own user_approval, so a
    slice could claim an agent approved it and still be reported PASS."""

    UNRELATED_DECISION_APPROVAL = {
        "required": True,
        "state": "APPROVED",
        "decided_by": "User",
        "decided_on": "2026-10-08",
        "basis": "P10 / P11 Security Sequencing (D-P10-1) - an unrelated decision.",
    }

    def _slice_claiming(self, decided_by: str) -> dict:
        """A schema-conformant APPROVED slice whose own approval names `decided_by`.

        The slice schema permits exactly {decided_by, decided_by_role,
        decided_at} and forbids any other property, so this is the real shape
        and no `state` key is smuggled in.
        """
        doc = _valid_slice()
        doc["acceptance_state"] = "APPROVED"
        doc["user_approval"] = {
            "decided_by": decided_by,
            "decided_by_role": "USER",
            "decided_at": "2026-10-14",
        }
        return doc

    def test_agent_attributed_slice_approval_is_rejected(self) -> None:
        """Requirement 1: the slice's OWN agent-attributed approval must fail."""
        for agent in ("opencode", "ChatGPT", "Claude", "copilot", "gpt"):
            with self.subTest(decided_by=agent):
                result = check_approval_authenticity(
                    self._slice_claiming(agent), self.UNRELATED_DECISION_APPROVAL)
                self.assertEqual(result.result, FAIL)
                self.assertIn("by an agent, not a user", result.detail)

    def test_unrelated_cli_approval_cannot_override_an_invalid_slice_approval(self) -> None:
        """Requirement 2 + the exact reported false-PASS, end to end through run_gate."""
        doc = self._slice_claiming("opencode")
        self.assertEqual(check_schema_structural(doc).result, PASS,
                         "fixture must be schema-valid for this to be a real false-PASS")
        report = run_gate(
            slice_path=self.write("slice-agent-approved.json", doc),
            inventory_path=self.write("inventory.json", _inventory()),
            content_types=[HOME_CT],
            content_records=[PUBLISHED_CONTENT],
            slice_id_history=[],
            build_dir=None,
            approval=self.UNRELATED_DECISION_APPROVAL,
        )
        by_id = {r.control_id: r for r in report.results}
        self.assertEqual(by_id["approval-authenticity"].result, FAIL)
        self.assertIn("by an agent, not a user", by_id["approval-authenticity"].detail)

    def test_unrelated_decision_approval_cannot_rescue_a_missing_slice_approval(self) -> None:
        """Requirement 3, missing/null flavour: an APPROVED slice with no approval
        of its own fails closed; a valid record for something else cannot stand
        in for it."""
        doc = _valid_slice()
        doc["acceptance_state"] = "APPROVED"
        doc["user_approval"] = None
        result = check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL)
        self.assertEqual(result.result, FAIL)
        self.assertIn("can never substitute", result.detail)

    def test_unrelated_decision_approval_cannot_rescue_an_invalid_slice_approval(self) -> None:
        """Requirement 3, invalid flavour: distinct from the missing/null case —
        the slice DOES carry a record, it is simply not attributable."""
        for label, decider, date in (("blank decider", "   ", "2026-10-14"),
                                     ("no date", "Maryam", None),
                                     ("non-string decider", 5, "2026-10-14")):
            with self.subTest(invalid=label):
                doc = self._slice_claiming("Maryam")
                doc["user_approval"]["decided_by"] = decider
                if date is None:
                    del doc["user_approval"]["decided_at"]
                else:
                    doc["user_approval"]["decided_at"] = date
                self.assertEqual(
                    check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL).result,
                    FAIL)

    def test_valid_slice_level_approval_passes(self) -> None:
        """Requirement 4: a correctly attributed slice approval behaves per contract.

        The verdict alone is not evidence of binding — a pre-fix gate also returns
        PASS here. The detail names which subject was judged, so this asserts the
        subject too; otherwise this test would survive a full revert of the fix.
        """
        result = check_approval_authenticity(
            self._slice_claiming("Maryam"), self.UNRELATED_DECISION_APPROVAL)
        self.assertEqual(result.result, PASS)
        self.assertIn("the slice's own user_approval", result.detail)

    def test_valid_slice_approval_governs_even_when_the_cli_record_is_invalid(self) -> None:
        """Requirement 4, second thread: the call site is pinned by a test that
        does not depend on the negative case. A valid slice approval must still
        be judged on the slice when the unrelated supplied record is unusable."""
        doc = self._slice_claiming("Maryam")
        for bad_record in ({"state": "APPROVED", "decided_by": "ChatGPT",
                            "decided_at": "2026-10-13"}, None, "not-an-object", 7):
            with self.subTest(cli_record=bad_record):
                result = check_approval_authenticity(doc, bad_record)
                self.assertEqual(result.result, PASS,
                                 "the slice's own approval governs; the supplied "
                                 "record neither rescues nor vetoes it")
                self.assertIn("the slice's own user_approval", result.detail)

    def test_missing_or_malformed_slice_approval_fails_closed(self) -> None:
        """Requirement 5."""
        doc = _valid_slice()
        doc["acceptance_state"] = "APPROVED"
        for label, value in (("null", None), ("a string", "opencode"), ("a list", ["x"])):
            with self.subTest(user_approval=label):
                doc["user_approval"] = value
                self.assertEqual(
                    check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL).result,
                    FAIL)
        del doc["user_approval"]
        self.assertEqual(
            check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL).result, FAIL)

    def test_blank_decider_and_missing_date_on_the_slice_fail_closed(self) -> None:
        """An APPROVED slice still owes a real decider and a decision date."""
        for decider, date in (("   ", "2026-10-14"), ("", "2026-10-14"),
                              ("Maryam", None), ("Maryam", "")):
            with self.subTest(decided_by=decider, decided_at=date):
                doc = self._slice_claiming("Maryam")
                doc["user_approval"]["decided_by"] = decider
                if date is None:
                    del doc["user_approval"]["decided_at"]
                else:
                    doc["user_approval"]["decided_at"] = date
                self.assertEqual(
                    check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL).result,
                    FAIL)

    def test_slice_supplied_state_is_overridden_not_trusted(self) -> None:
        """A slice must not launder itself into APPROVED by carrying a forged
        `state` key; the slice's own acceptance_state governs. The forged key
        is overridden, so the judgement is made against DRAFT and fails."""
        for decider in ("opencode", "Maryam"):
            with self.subTest(decided_by=decider):
                doc = self._slice_claiming(decider)
                doc["acceptance_state"] = "DRAFT"
                doc["user_approval"]["state"] = "APPROVED"
                result = check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL)
                self.assertEqual(result.result, FAIL)
                self.assertIn("'DRAFT', not APPROVED", result.detail)

    def test_slice_approval_must_be_actually_approved(self) -> None:
        """A non-APPROVED slice carrying an approval record is fail-closed."""
        doc = self._slice_claiming("Maryam")
        doc["acceptance_state"] = "IN_PROGRESS"
        self.assertEqual(
            check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL).result, FAIL)

    def test_absent_acceptance_state_with_a_record_fails_closed(self) -> None:
        """A record with no lifecycle state to support it is not an approval;
        absence must never be read as APPROVED."""
        doc = self._slice_claiming("Maryam")
        del doc["acceptance_state"]
        result = check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL)
        self.assertEqual(result.result, FAIL)
        self.assertIn("NOT_APPROVED", result.detail)

    def test_non_USER_decided_by_role_is_rejected_without_a_sibling_control(self) -> None:
        """REQ-P10-09 c.6 requires decided_by_role=USER. This control applies the
        rule itself rather than relying on schema-structural's enum to catch it.

        Case sensitivity is pinned deliberately: a `str(role).upper()` comparison
        would accept "user" and silently widen the authority, so exact match is
        asserted here alongside the non-string shapes."""
        for role in ("AGENT", "agent", "USER_AGENT", "", "user", "User", "USER ",
                     " USER", None, ["USER"], {}, True, 1):
            with self.subTest(decided_by_role=role):
                doc = self._slice_claiming("Maryam")
                if role is None:
                    del doc["user_approval"]["decided_by_role"]
                else:
                    doc["user_approval"]["decided_by_role"] = role
                result = check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL)
                self.assertEqual(result.result, FAIL)
                self.assertIn("decided_by_role", result.detail)

    def test_the_caller_slice_document_is_never_mutated(self) -> None:
        """The control derives a private view; the caller's document and the
        supplied record must come back byte-identical, so no later control can be
        influenced by this one."""
        doc = self._slice_claiming("Maryam")
        record = dict(self.UNRELATED_DECISION_APPROVAL)
        before_doc = json.loads(json.dumps(doc))
        before_record = json.loads(json.dumps(record))
        check_approval_authenticity(doc, record)
        self.assertEqual(doc, before_doc)
        self.assertEqual(record, before_record)
        self.assertNotIn("state", doc["user_approval"])

    def test_hostile_slice_scalar_does_not_raise(self) -> None:
        """Any hostile scalar must fail closed, never escape as a traceback.

        FAIL is the contract, not merely "not PASS": BLOCKED or UNIMPLEMENTED
        would both hide a hole here."""
        for value in ("opencode", 5, True, [], b"x", {"decided_by": "opencode"}):
            with self.subTest(user_approval=value):
                doc = _valid_slice()
                doc["acceptance_state"] = "APPROVED"
                doc["user_approval"] = value
                self.assertEqual(
                    check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL).result,
                    FAIL)

    def test_non_string_decider_on_the_slice_fails_closed(self) -> None:
        """The shape trust-boundary still applies to the slice's own approval."""
        for value in (5, True, ["User"], {"name": "User"}, b"User", 1.5):
            with self.subTest(decided_by=value):
                doc = self._slice_claiming("User")
                doc["user_approval"]["decided_by"] = value
                result = check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL)
                self.assertEqual(result.result, FAIL)
                self.assertIn("not a string", result.detail)

    def test_unrelated_record_path_is_unchanged_where_the_contract_permits(self) -> None:
        """Requirement 6: a slice asserting no approval of its own still has its
        separately supplied decision-record approval attributed as before."""
        doc = _valid_slice()
        self.assertEqual(doc["acceptance_state"], "DRAFT")
        self.assertIsNone(doc.get("user_approval"))
        self.assertEqual(
            check_approval_authenticity(doc, self.UNRELATED_DECISION_APPROVAL).result, PASS)
        self.assertEqual(
            check_approval_authenticity(doc, dict(self.UNRELATED_DECISION_APPROVAL,
                                                  decided_by="ChatGPT")).result, FAIL)

    def test_unreadable_slice_falls_back_to_the_supplied_record(self) -> None:
        """A slice that cannot be read makes no approval claim, so the supplied
        record is judged; the gate must still not raise."""
        self.assertEqual(check_approval_authenticity(None, self.UNRELATED_DECISION_APPROVAL).result,
                         PASS)
        self.assertEqual(check_approval_authenticity(None, None).result, FAIL)

    def test_required_control_inventory_is_unchanged(self) -> None:
        """The fix must not add, drop, rename or REORDER any control. The exact
        tuple is pinned rather than a count, so a rename-and-replace at constant
        size cannot slip through."""
        self.assertEqual(REQUIRED_CONTROL_IDS, (
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
        ))


class TestSliceIdUniqueness(GateFixtureCase):
    def test_unique_id_passes_against_an_authoritative_history(self) -> None:
        r = check_slice_id_uniqueness(_valid_slice("SLICE-P10-01"), ["SLICE-P10-02"])
        self.assertEqual(r.result, PASS)

    def test_reused_id_fails(self) -> None:
        r = check_slice_id_uniqueness(_valid_slice("SLICE-P10-01"), ["SLICE-P10-01"])
        self.assertEqual(r.result, FAIL)
        self.assertIn("already appears", r.detail)

    def test_absent_history_fails_closed(self) -> None:
        r = check_slice_id_uniqueness(_valid_slice("SLICE-P10-01"), None)
        self.assertEqual(r.result, FAIL)
        self.assertIn("cannot be established", r.detail)

    def test_empty_history_fails_closed(self) -> None:
        """An empty history proves exactly as little as an absent one; it must not
        be read as proof of uniqueness."""
        r = check_slice_id_uniqueness(_valid_slice("SLICE-P10-01"), [])
        self.assertEqual(r.result, FAIL)
        self.assertIn("cannot be established", r.detail)


class TestFailClosedOrchestration(GateFixtureCase):
    def _fixture(self, **kw) -> dict:
        kwargs = dict(
            inventory_path=self.write("inventory.json", _inventory()),
            content_types=[HOME_CT],
            content_records=[PUBLISHED_CONTENT],
            slice_id_history=[],
            build_dir=None,
            approval=USER_APPROVAL,
        )
        kwargs.setdefault("slice_path", self.write("slice-default.json", _valid_slice()))
        kwargs.update(kw)
        return kwargs

    def test_unreadable_slice_fails_dependent_controls(self) -> None:
        bad = self.write_raw("slice-broken.json", "{ broken")
        report = run_gate(**self._fixture(slice_path=bad))
        by_id = {r.control_id: r for r in report.results}
        self.assertEqual(by_id["schema-structural"].result, FAIL)
        self.assertEqual(by_id["evidence-references"].result, FAIL)
        self.assertEqual(by_id["published-only-content"].result, FAIL)

    def test_non_utf8_slice_document_fails_closed_without_crashing(self) -> None:
        path = os.path.join(self.tmp, "latin1.json")
        with open(path, "wb") as fh:
            fh.write(b'{"slice_id": "\xc9\xff"}')
        report = run_gate(**self._fixture(slice_path=path))
        self.assertEqual(report.overall, FAIL)
        by_id = {r.control_id: r for r in report.results}
        self.assertEqual(by_id["schema-structural"].result, FAIL)

    def test_report_never_passes_without_real_prerequisites(self) -> None:
        # The real repository now ships an (empty) operations.json (P10
        # completion, commit 1279cd6), which would let req-p10-07 reconcile
        # honestly. This test's scenario is "no real prerequisites at all",
        # so it runs in an isolated root where the manifest is absent —
        # keeping the fail-closed reconciliation expectation intact.
        with mock.patch(
            "framework.sps2.tools.p10_runtime_gate._repo_root", return_value=self.tmp
        ):
            report = run_gate(**self._fixture())
        self.assertEqual(report.overall, FAIL)
        failed_ids = {r.control_id for r in report.failures}
        # approval-state-interaction is NOT in this list: the fixture inventory
        # (COMPLETE_AWAITING_USER_APPROVAL, user_approval null) is a coherent
        # pre-transition state under DEC-7112 design #6, so that control
        # honestly PASSes while every substantive prerequisite is still absent.
        for cid in ("p9-deployment-audit", "cms-state-digest", "p8-contract-digest",
                    "req-p10-07-reconciliation", "evidence-freshness",
                    "evidence-authenticity", "exposure-declaration"):
            self.assertIn(cid, failed_ids)

    def test_every_required_control_is_reported(self) -> None:
        report = run_gate(**self._fixture())
        reported = [r.control_id for r in report.results]
        for cid in REQUIRED_CONTROL_IDS:
            self.assertIn(cid, reported)
        self.assertEqual(report.missing_required, [])
        self.assertEqual(report.duplicate_required, [])

    def test_no_duplicate_results_are_emitted(self) -> None:
        report = run_gate(**self._fixture())
        ids = [r.control_id for r in report.results]
        self.assertEqual(len(ids), len(set(ids)))


class TestCLIExitSemantics(GateFixtureCase):
    def _write_valid_slice_and_evidence(self):
        self.write("evidence.json", {"ok": True})
        return self.write("slice.json", _valid_slice())

    def test_cli_exits_non_zero_on_realistic_slice(self) -> None:
        slice_path = self._write_valid_slice_and_evidence()
        rc = main([
            "--slice", slice_path, "--inventory", self.write("inventory.json", _inventory()),
            "--content-types", self.write("content_types.json", [HOME_CT]),
            "--content", self.write("content.json", [PUBLISHED_CONTENT]),
            "--slice-id-history", self.write("hist.json", []), "--json",
        ])
        self.assertEqual(rc, EXIT_FAILED)

    def test_cli_exits_non_zero_on_unreadable_slice(self) -> None:
        rc = main([
            "--slice", self.write("slice.json", "{ not json"),
            "--inventory", self.write("inventory.json", _inventory()), "--json",
        ])
        self.assertEqual(rc, EXIT_FAILED)

    def test_cli_exits_non_zero_on_external_evidence_reference(self) -> None:
        doc = _valid_slice()
        doc["evidence_references"] = ["/etc/hosts"]
        rc = main([
            "--slice", self.write("slice.json", doc),
            "--inventory", self.write("inventory.json", _inventory()),
            "--content-types", self.write("content_types.json", [HOME_CT]),
            "--content", self.write("content.json", [PUBLISHED_CONTENT]),
            "--slice-id-history", self.write("hist.json", []), "--json",
        ])
        self.assertEqual(rc, EXIT_FAILED)

    def test_cli_reports_json_report(self) -> None:
        slice_path = self._write_valid_slice_and_evidence()
        buf = io.StringIO()
        with redirect_stdout(buf):
            main([
                "--slice", slice_path, "--inventory", self.write("inventory.json", _inventory()),
                "--content-types", self.write("content_types.json", [HOME_CT]),
                "--content", self.write("content.json", [PUBLISHED_CONTENT]),
                "--slice-id-history", self.write("hist.json", []), "--json",
            ])
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["overall"], FAIL)
        self.assertTrue(payload["structural_validity_is_not_substantive_completion"])
        self.assertGreaterEqual(len(payload["unresolved_semantics"]), 5)
        self.assertEqual(payload["missing_required_controls"], [])

    def test_cli_works_from_an_alternate_working_directory(self) -> None:
        other = tempfile.mkdtemp(prefix="p10-cwd-")
        self.addCleanup(shutil.rmtree, other, True)
        slice_path = self._write_valid_slice_and_evidence()
        proc = subprocess.run(
            [sys.executable, "-B", os.path.join(REPO_ROOT, "framework", "sps2", "tools", "p10_runtime_gate.py"),
             "--slice", slice_path,
             "--inventory", os.path.join(REPO_ROOT, "framework", "sps2", "requirements", "P10-SECTION-INVENTORY.json"),
             "--json"],
            capture_output=True, text=True, cwd=other,
        )
        self.assertEqual(proc.returncode, EXIT_FAILED)
        self.assertEqual(json.loads(proc.stdout)["overall"], FAIL)


class TestFalsePassRegression(GateFixtureCase):
    """The gate must never treat a non-discriminating signal as proof."""

    def test_check_sps2_exit_status_is_never_used_as_proof(self) -> None:
        # Documented repository quirk: check_sps2.py main() returns 0 for
        # unparseable JSON. The gate asserts its OWN behaviour instead: an
        # unreadable document fails closed.
        bad = self.write_raw("bad.json", "{ not json")
        report = run_gate(
            slice_path=bad,
            inventory_path=self.write("inventory.json", _inventory()),
            content_types=[], content_records=[], slice_id_history=[],
            build_dir=None, approval=USER_APPROVAL,
        )
        self.assertEqual(report.overall, FAIL)
        by_id = {r.control_id: r for r in report.results}
        self.assertEqual(by_id["schema-structural"].result, FAIL)

    def test_empty_build_directory_is_not_treated_as_proof(self) -> None:
        build = self.make_build("vacuous")
        self.assertTrue(os.path.isdir(build))
        self.assertEqual(os.listdir(build), [])
        self.assertEqual(check_p9_deployment_audit(_valid_slice(), build).result, BLOCKED)


class TestNoRepositoryMutation(GateFixtureCase):
    def test_gate_only_reads_repository(self) -> None:
        def digest(path):
            with open(path, "rb") as fh:
                return hashlib.sha256(fh.read()).hexdigest()

        inv_path = os.path.join(REPO_ROOT, "framework", "sps2", "requirements", "P10-SECTION-INVENTORY.json")
        dec_path = os.path.join(REPO_ROOT, "framework", "sps2", "decisions", "P10-DECISIONS.json")
        before = (digest(inv_path), digest(dec_path))
        report = run_gate(
            slice_path=self.write("slice.json", _valid_slice()),
            inventory_path=inv_path,
            content_types=[HOME_CT],
            content_records=[DRAFT_CONTENT],
            slice_id_history=[],
            build_dir=None,
            approval=USER_APPROVAL,
        )
        by_id = {r.control_id: r for r in report.results}
        self.assertEqual(by_id["published-only-content"].result, FAIL)
        self.assertEqual(report.overall, FAIL)
        self.assertEqual(before, (digest(inv_path), digest(dec_path)),
                         "gate must not mutate repository files")




# =============================================================================
# Round 2 fail-closed regression suite.
#
# Every test here FAILS against the defective behaviour it targets. Each asserts
# a specific STRUCTURED status (PASS/FAIL/BLOCKED/UNIMPLEMENTED) or the exact
# exception class -- never a bare assertRaises(Exception), which would let an
# unrelated crash satisfy the test.
#
# All fixtures are synthetic. A PASS here is gate logic over a hand-built
# fixture and is NOT runtime verification.
# =============================================================================


class TestMalformedAllOfIsBlockedNotCrashed(unittest.TestCase):
    """M-1: `enumerate(schema.get("allOf") or [])` conflated absent with every
    falsy non-array and let a truthy non-iterable reach enumerate()."""

    NON_ARRAY = (5, 1.5, True, 1, -1, 2.0, {"a": {"type": "object"}})

    def test_non_array_all_of_raises_schema_unsupported_not_type_error(self):
        for value in self.NON_ARRAY:
            with self.subTest(allOf=value):
                try:
                    _SliceSchemaValidator({"type": "object", "allOf": value}).errors({"a": "x"})
                except _SchemaUnsupported as exc:
                    self.assertIn("allOf", str(exc))
                except TypeError as exc:  # the defect
                    self.fail(f"allOf={value!r} raised TypeError, not _SchemaUnsupported: {exc}")
                else:
                    self.fail(f"allOf={value!r} was silently accepted")

    def test_falsy_non_array_all_of_is_not_read_as_absent(self):
        """null/false/0/{}/"" used to report structural PASS."""
        for value in (None, False, 0, {}, ""):
            with self.subTest(allOf=value):
                try:
                    _SliceSchemaValidator({"type": "object", "allOf": value}).errors({"a": "x"})
                except _SchemaUnsupported as exc:
                    self.assertIn("allOf", str(exc))
                else:
                    self.fail(f"allOf={value!r} was silently read as absent")

    def test_empty_all_of_is_rejected(self):
        """meta-schema `schemaArray` has minItems 1."""
        with self.assertRaises(_SchemaUnsupported) as ctx:
            _SliceSchemaValidator({"type": "object", "allOf": []}).errors({"a": "x"})
        self.assertIn("allOf", str(ctx.exception))

    def test_valid_all_of_is_still_accepted(self):
        schema = {"type": "object", "allOf": [{"type": "object"},
                                              {"properties": {"a": {"type": "string"}}}]}
        self.assertEqual(_SliceSchemaValidator(schema).errors({"a": "x"}), [])

    def test_nested_all_of_is_audited_before_any_instance_reaches_it(self):
        with self.assertRaises(_SchemaUnsupported) as ctx:
            _SliceSchemaValidator(
                {"type": "object", "properties": {"a": {"allOf": 5}}}).errors({})
        self.assertIn("allOf", str(ctx.exception))

    def test_validate_never_iterates_an_unvalidated_all_of(self):
        with self.assertRaises(_SchemaUnsupported) as ctx:
            _SliceSchemaValidator({"type": "object"})._validate(
                {"a": "x"}, {"allOf": 5}, "#", [], frozenset())
        self.assertIn("allOf", str(ctx.exception))


class TestMalformedRequiredIsBlockedNotCrashed(unittest.TestCase):
    """M-1b: an unhashable `required` member reached `name not in inst`."""

    def test_non_string_required_member_is_blocked(self):
        for value in (["a", []], ["a", {}], [5], [None], [True], [1.5], [[]], [{}]):
            with self.subTest(required=value):
                schema = {"type": "object", "required": value,
                          "properties": {"a": {"type": "string"}}}
                try:
                    _SliceSchemaValidator(schema).errors({"a": "x"})
                except _SchemaUnsupported as exc:
                    self.assertIn("required", str(exc))
                except TypeError as exc:  # the defect
                    self.fail(f"required={value!r} raised TypeError: {exc}")
                else:
                    self.fail(f"required={value!r} was silently accepted")

    def test_duplicate_required_entries_are_blocked(self):
        with self.assertRaises(_SchemaUnsupported) as ctx:
            _SliceSchemaValidator({"type": "object", "required": ["a", "a"],
                                   "properties": {"a": {"type": "string"}}}).errors({"a": "x"})
        self.assertIn("required", str(ctx.exception))


class TestNullValuedKeywordsAreBlockedNotIgnored(unittest.TestCase):
    """L-1/L-1b: `is not None` could not distinguish ABSENT from an explicit
    null, so one null DELETED an enforced constraint and flipped a rejecting
    document to PASS."""

    NULLABLE_BY_DESIGN = ("const",)  # `const: null` is a legal constraint

    def test_const_null_stays_legal(self):
        """Guard against over-correction."""
        v = _SliceSchemaValidator({"const": None})
        self.assertEqual(v.errors(None), [])
        self.assertIn("must equal None", v.errors("x")[0])

    def test_null_valued_keyword_is_blocked(self):
        for keyword in ("type", "required", "minItems", "minLength", "pattern",
                        "uniqueItems", "format", "allOf", "enum", "items",
                        "additionalProperties", "properties"):
            with self.subTest(keyword=keyword):
                schema = {"type": "object", "properties": {"a": {"type": "string"}}}
                schema[keyword] = None
                with self.assertRaises(_SchemaUnsupported) as ctx:
                    _SliceSchemaValidator(schema).errors({"a": "x"})
                self.assertIn(keyword, str(ctx.exception))

    def test_null_keyword_in_an_unreached_branch_still_blocks(self):
        """L-1b: the static pre-pass must cover what only _validate caught."""
        for keyword in ("enum", "additionalProperties", "type", "required", "allOf"):
            with self.subTest(keyword=keyword):
                schema = {
                    "type": "object",
                    "properties": {"state": {"enum": ["A"]}},
                    "if": {"properties": {"state": {"const": "B"}}, "required": ["state"]},
                    "then": {"properties": {"other": {keyword: None}}},
                }
                with self.assertRaises(_SchemaUnsupported) as ctx:
                    _SliceSchemaValidator(schema).errors({"state": "A"})
                self.assertIn(keyword, str(ctx.exception))


class TestSchemaFaultsProduceStructuredReports(unittest.TestCase):
    """M-1: an escaping TypeError destroyed the whole --json report."""

    def _slice_file(self, tmp, evidence=None):
        path = os.path.join(tmp, "slice.json")
        doc = _valid_slice()
        if evidence is not None:
            doc["evidence_references"] = evidence
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(doc, handle)
        return path

    def test_cli_json_survives_a_nul_byte_evidence_reference(self):
        """L-2: was a ValueError traceback with zero bytes of stdout."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self._slice_file(tmp, evidence=["ev\x00.txt"])
            proc = subprocess.run(
                [sys.executable, "-B", os.path.join(REPO_ROOT, "framework/sps2/tools/p10_runtime_gate.py"),
                 "--slice", path, "--json"],
                capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr.count("Traceback"), 0)
        payload = json.loads(proc.stdout)
        self.assertEqual(len(payload["controls"]), len(REQUIRED_CONTROL_IDS))

    def test_nul_byte_evidence_reference_fails_the_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = _valid_slice()
            doc["evidence_references"] = ["ev\x00.txt"]
            result = check_evidence_references(doc, tmp)
        self.assertEqual(result.result, FAIL)
        self.assertIn("NUL", result.detail)


class TestApprovalTrustBoundary(unittest.TestCase):
    """M-3: attribution calls .strip() on unvalidated values, so a non-string
    decided_by/decided_at escaped as an uncaught AttributeError."""

    def test_non_string_decided_by_fails_closed_instead_of_raising(self):
        for value in (5, True, ["User"], {"name": "User"}, b"User", 1.5):
            with self.subTest(decided_by=value):
                approval = {"state": "APPROVED", "decided_by": value,
                            "decided_at": "2026-10-13"}
                result = check_approval_authenticity(_valid_slice(), approval)
                self.assertEqual(result.result, FAIL)
                self.assertIn("not a string", result.detail)

    def test_non_string_decided_at_fails_closed_instead_of_raising(self):
        for field in ("decided_at", "decided_on"):
            for value in (5, [], {}, True):
                with self.subTest(field=field, value=value):
                    approval = {"state": "APPROVED", "decided_by": "User", field: value}
                    self.assertEqual(check_approval_authenticity(_valid_slice(), approval).result, FAIL)

    def test_shape_validation_does_not_weaken_the_authority(self):
        """Only shape is checked here; attribution still decides."""
        user = {"state": "APPROVED", "decided_by": "User", "decided_at": "2026-10-13"}
        self.assertEqual(check_approval_authenticity(_valid_slice(), user).result, PASS)
        agent = {"state": "APPROVED", "decided_by": "opencode", "decided_at": "2026-10-13"}
        self.assertEqual(check_approval_authenticity(_valid_slice(), agent).result, FAIL)
        undated = {"state": "APPROVED", "decided_by": "User"}
        self.assertEqual(check_approval_authenticity(_valid_slice(), undated).result, FAIL)

    def test_pass_detail_does_not_claim_a_validated_decision_date(self):
        """D3 truthfulness: attribution only checks non-blankness."""
        user = {"state": "APPROVED", "decided_by": "User", "decided_at": "not-a-date"}
        result = check_approval_authenticity(_valid_slice(), user)
        self.assertEqual(result.result, PASS)
        self.assertNotIn("with a decision date", result.detail)
        self.assertIn("does not validate the decision date", result.detail)

    def test_null_and_absent_decider_still_fail(self):
        for approval in ({"state": "APPROVED", "decided_by": None, "decided_at": "2026-10-13"},
                         {"state": "APPROVED", "decided_at": "2026-10-13"}):
            self.assertEqual(check_approval_authenticity(_valid_slice(), approval).result, FAIL)


class TestHostileScalarsNeverEscapeAControl(unittest.TestCase):
    """M-3': the `(doc.get(k) or {}).get(k)` idiom raised on any scalar."""

    def test_scalar_axis_contracts_does_not_raise(self):
        for value in ("x", 5, True, [], b"x"):
            with self.subTest(axis_contracts=value):
                doc = _valid_slice()
                doc["axis_contracts"] = value
                self.assertNotEqual(check_exposure_declaration(doc).result, PASS)
                self.assertNotEqual(
                    check_p9_deployment_audit(doc, None).result, PASS)
                self.assertNotEqual(check_req_p10_07_reconciliation(doc).result, PASS)

    def test_scalar_evidence_references_does_not_raise(self):
        for value in (5, 1.5, True, {}, "x"):
            with self.subTest(evidence_references=value):
                doc = _valid_slice()
                doc["evidence_references"] = value
                # Implemented semantics (DEC-7112): a malformed reference list
                # FAILS the control, it never raises and never passes.
                self.assertEqual(check_evidence_freshness(doc).result, FAIL)
                self.assertEqual(check_evidence_authenticity(doc).result, FAIL)

    def test_scalar_inventory_provenance_does_not_raise(self):
        for value in (5, "x", [], True):
            with self.subTest(provenance=value):
                # Implemented semantics (DEC-7112): a malformed provenance block
                # FAILS closed (no digest to compare), it never raises.
                self.assertEqual(check_cms_state_digest({"provenance": value}).result,
                                 FAIL)
                self.assertEqual(check_p8_contract_digest({"provenance": value}).result,
                                 FAIL)

    def test_non_list_slice_id_history_fails_closed(self):
        doc = _valid_slice()
        self.assertEqual(check_slice_id_uniqueness(doc, 5).result, FAIL)

    def test_non_string_build_dir_is_blocked(self):
        result = check_p9_deployment_audit(_valid_slice(), 5)
        self.assertEqual(result.result, BLOCKED)


class TestP9FileSetIdentity(unittest.TestCase):
    """M-2: the control used glob.glob(..., recursive=True) while the P9 audit
    uses pathlib.Path.glob, so it could PASS a build the audit never examined."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _build(self, name, files=("index.html",), robots=True, sitemap=True):
        build = os.path.join(self.tmp, name)
        os.makedirs(build, exist_ok=True)
        for rel in files:
            path = os.path.join(build, rel)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(MINIMAL_HTML)
        if robots:
            with open(os.path.join(build, "robots.txt"), "w", encoding="utf-8") as h:
                h.write(MINIMAL_ROBOTS)
        if sitemap:
            with open(os.path.join(build, "sitemap.xml"), "w", encoding="utf-8") as h:
                h.write(MINIMAL_SITEMAP)
        return build

    def test_symlinked_subdir_html_is_invisible_to_the_audited_page_set(self):
        """The audit does not recurse into a symlinked directory."""
        build = self._build("symlinked", files=("index.html",))
        outside = os.path.join(self.tmp, "outside-subdir")
        os.makedirs(outside)
        with open(os.path.join(outside, "extra.html"), "w", encoding="utf-8") as h:
            h.write(MINIMAL_HTML)
        os.symlink(outside, os.path.join(build, "sub"))
        doc = _valid_slice()
        doc["route"] = "/sub/extra"
        result = check_p9_deployment_audit(doc, build)
        self.assertNotEqual(result.result, PASS)
        self.assertIn("does not contain the declared route", result.detail)

    def test_build_whose_only_html_is_behind_a_symlink_does_not_pass(self):
        """The control-level FALSE PASS: the audit saw 0 pages (vacuous exit 0)
        while the gate reported 1 HTML document."""
        build = self._build("symlink-only", files=())
        outside = os.path.join(self.tmp, "outside-only")
        os.makedirs(outside)
        with open(os.path.join(outside, "extra.html"), "w", encoding="utf-8") as h:
            h.write(MINIMAL_HTML)
        os.symlink(outside, os.path.join(build, "sub"))
        doc = _valid_slice()
        doc["route"] = "/sub/extra"
        self.assertNotEqual(check_p9_deployment_audit(doc, build).result, PASS)

    def test_build_dir_name_with_glob_metacharacters_is_enumerated_literally(self):
        """`glob` treats [] as a character class and finds nothing."""
        build = self._build("dist[1]", files=("index.html", "blog/post.html"))
        doc = _valid_slice()
        doc["route"] = "/blog/post"
        result = check_p9_deployment_audit(doc, build)
        self.assertEqual(result.result, PASS)
        self.assertIn("2 HTML document(s)", result.detail)

    def test_star_and_question_marks_in_build_dir_name_are_literal(self):
        for name in ("a*b", "q?x", "{braces}", "build (1)"):
            with self.subTest(build_dir_name=name):
                build = self._build(name)
                self.assertEqual(check_p9_deployment_audit(_valid_slice(), build).result,
                                 PASS)

    def test_nested_blog_post_derives_its_own_route(self):
        build = self._build("blogpost", files=("blog/post.html",))
        doc = _valid_slice()
        doc["route"] = "/blog/post"
        self.assertEqual(check_p9_deployment_audit(doc, build).result, PASS)
        doc["route"] = "/blog/"
        self.assertIn("does not contain the declared route",
                      check_p9_deployment_audit(doc, build).detail)

    def test_valid_complete_nested_build_passes_with_a_truthful_count(self):
        build = self._build("valid-nested",
                            files=("index.html", "about.html", "blog/index.html",
                                   "blog/post.html", "a/b/c/page.html"))
        result = check_p9_deployment_audit(_valid_slice(), build)
        self.assertEqual(result.result, PASS)
        self.assertIn("5 HTML document(s)", result.detail)
        self.assertIn("audited_artifacts_digest=", result.detail)
        self.assertIn("NOT evidence that a real P10 slice passed", result.detail)

    def test_empty_build_is_blocked_even_though_the_audit_exits_zero(self):
        build = self._build("empty-real", files=())
        self.assertEqual(check_p9_deployment_audit(_valid_slice(), build).result, BLOCKED)
        self.assertIn("vacuous", check_p9_deployment_audit(_valid_slice(), build).detail)

    def test_missing_required_artifact_is_blocked_and_named(self):
        for absent in ("robots.txt", "sitemap.xml"):
            with self.subTest(absent=absent):
                build = self._build("missing-" + absent,
                                    robots=absent != "robots.txt",
                                    sitemap=absent != "sitemap.xml")
                result = check_p9_deployment_audit(_valid_slice(), build)
                self.assertEqual(result.result, BLOCKED)
                self.assertIn(absent, result.detail)

    def test_whitespace_only_robots_is_not_accepted_as_present(self):
        build = self._build("ws-robots")
        with open(os.path.join(build, "robots.txt"), "w", encoding="utf-8") as h:
            h.write("   \n\t ")
        self.assertEqual(check_p9_deployment_audit(_valid_slice(), build).result, BLOCKED)

    def test_artifacts_escaping_the_build_boundary_are_refused(self):
        outside = os.path.join(self.tmp, "outside-artifacts")
        os.makedirs(outside)
        bodies = {"index.html": MINIMAL_HTML, "robots.txt": MINIMAL_ROBOTS,
                  "sitemap.xml": MINIMAL_SITEMAP}
        for name, body in bodies.items():
            with open(os.path.join(outside, name), "w", encoding="utf-8") as h:
                h.write(body)
        for link in bodies:
            with self.subTest(link=link):
                build = os.path.join(self.tmp, "escape-" + link.replace(".", "-"))
                os.makedirs(build, exist_ok=True)
                # Everything else is a REAL file inside the build, so the only
                # thing that can trip the containment check is `link`.
                for name, body in bodies.items():
                    if name == link:
                        os.symlink(os.path.join(outside, name), os.path.join(build, name))
                    else:
                        with open(os.path.join(build, name), "w", encoding="utf-8") as h:
                            h.write(body)
                result = check_p9_deployment_audit(_valid_slice(), build)
                self.assertEqual(result.result, FAIL)
                self.assertIn("outside the build directory", result.detail)

    def test_two_files_deriving_one_route_are_rejected(self):
        """The audit keys its page table by route, so a collision drops a page."""
        build = self._build("collide", files=("index.html", ".html"))
        result = check_p9_deployment_audit(_valid_slice(), build)
        self.assertEqual(result.result, FAIL)
        self.assertIn("distinct route", result.detail)

    def test_symlink_cycle_does_not_multiply_routes(self):
        build = self._build("cycle", files=("sub/p.html",))
        os.symlink("..", os.path.join(build, "sub", "up"))
        result = check_p9_deployment_audit(_valid_slice(), build)
        self.assertNotIn("33 HTML document(s)", result.detail)


class TestContentAuthenticity(unittest.TestCase):
    """M-5: the authoritative content_slots verdict was never consulted, so a
    published record exposing no value for a declared slot reported PASS."""

    def _slice(self, slots=("heading", "body")):
        doc = _valid_slice()
        doc["cms_content_references"] = [{"content_id": "C1",
                                          "required_status": "published",
                                          "field_slots": list(slots)}]
        return doc

    def _content(self, **overrides):
        record = {"id": "C1", "type_id": HOME_CT["id"], "status": "published",
                  "title": "Build Smarter", "body": "Real body"}
        record.update(overrides)
        return record

    def test_published_record_with_empty_slot_value_fails(self):
        for overrides, code in (({"title": ""}, "MISSING_VALUE"),
                                ({"body": ""}, "MISSING_VALUE"),
                                ({"title": 12345}, "INVALID_VALUE")):
            with self.subTest(overrides=overrides):
                result = check_layout_slot_conformance(
                    self._slice(), [HOME_CT], [self._content(**overrides)])
                self.assertEqual(result.result, FAIL)
                self.assertIn("MISSING_VALUE" if code == "MISSING_VALUE"
                              else "INVALID_VALUE", result.detail)

    def test_published_record_missing_the_slot_property_fails(self):
        record = self._content()
        del record["body"]
        result = check_layout_slot_conformance(self._slice(), [HOME_CT], [record])
        self.assertEqual(result.result, FAIL)
        self.assertIn("MALFORMED_CONTENT", result.detail)

    def test_fully_resolved_record_still_passes(self):
        result = check_layout_slot_conformance(self._slice(), [HOME_CT], [self._content()])
        self.assertEqual(result.result, PASS)

    def test_declared_slot_outside_the_authorized_mapping_fails(self):
        content_type = dict(HOME_CT)
        content_type["fields"] = HOME_CT["fields"] + [{"name": "subtitle", "type": "text"}]
        result = check_layout_slot_conformance(
            self._slice(slots=("heading", "body", "subtitle")),
            [content_type], [self._content()])
        self.assertEqual(result.result, FAIL)
        self.assertIn("over-declared", result.detail)
        self.assertIn("subtitle", result.detail)

    def test_control_detail_never_leaks_raw_cms_values(self):
        record = self._content(body="SECRET-CANARY-STRING")
        del record["body"]
        result = check_layout_slot_conformance(self._slice(), [HOME_CT], [record])
        self.assertNotIn("SECRET-CANARY-STRING", result.detail)

    def test_pass_detail_states_that_slot_correspondence_is_established(self):
        """D-P10-9 establishes the slot correspondence; the report must reflect it."""
        result = check_layout_slot_conformance(self._slice(), [HOME_CT], [self._content()])
        self.assertEqual(result.result, PASS)
        self.assertIn("D-P10-9 ESTABLISHED", result.detail)
        self.assertIn("set equality", result.detail)
        self.assertIn("order-insensitive", result.detail)
        self.assertNotIn("NOT ESTABLISHED HERE", result.detail)


class TestUniqueRecordIdentity(unittest.TestCase):
    """F1: a draft followed by a published copy of the SAME id made
    published-only-content PASS purely by array order."""

    def _doc(self):
        doc = _valid_slice()
        doc["cms_content_references"] = [{"content_id": "C1",
                                          "required_status": "published",
                                          "field_slots": ["heading"]}]
        return doc

    def _pair(self):
        return [{"id": "C1", "type_id": HOME_CT["id"], "status": "draft",
                 "title": "H", "body": "B"},
                {"id": "C1", "type_id": HOME_CT["id"], "status": "published",
                 "title": "H", "body": "B"}]

    def test_draft_and_published_with_the_same_id_fail_closed(self):
        result = check_published_only_content(self._doc(), self._pair())
        self.assertEqual(result.result, FAIL)
        self.assertIn("duplicate Content id", result.detail)

    def test_duplicate_id_verdict_is_order_independent(self):
        self.assertEqual(check_published_only_content(self._doc(), self._pair()).result, FAIL)
        self.assertEqual(
            check_published_only_content(self._doc(), list(reversed(self._pair()))).result,
            FAIL)

    def test_layout_control_also_rejects_duplicate_ids(self):
        result = check_layout_slot_conformance(self._doc(), [HOME_CT], self._pair())
        self.assertEqual(result.result, FAIL)
        self.assertIn("duplicate Content id", result.detail)

    def test_duplicate_content_type_ids_fail_closed(self):
        other = dict(HOME_CT)
        other["fields"] = [{"name": "heading", "type": "text"}]
        result = check_layout_slot_conformance(self._doc(), [HOME_CT, other], self._pair()[:1])
        self.assertEqual(result.result, FAIL)
        self.assertIn("duplicate ContentType id", result.detail)

    def test_unique_ids_are_unaffected(self):
        unique = [{"id": "C1", "type_id": HOME_CT["id"], "status": "published",
                   "title": "H", "body": "B"}]
        self.assertEqual(check_published_only_content(self._doc(), unique).result, PASS)


class TestJsonEqualityRecursion(unittest.TestCase):
    """F8: Python compares container leaves with ==, so True/1 collided."""

    def test_bool_and_number_do_not_collide_inside_containers(self):
        self.assertFalse(_json_equal([{"x": 1}], [{"x": True}]))
        self.assertFalse(_json_equal({"x": 1}, {"x": True}))
        self.assertFalse(_json_equal([[1]], [[True]]))
        self.assertFalse(_json_equal([1], [True]))

    def test_identical_nested_structures_still_compare_equal(self):
        self.assertTrue(_json_equal([{"x": 1}, {"y": [1, 2]}], [{"x": 1}, {"y": [1, 2]}]))

    def test_json_has_one_number_type(self):
        self.assertTrue(_json_equal([1], [1.0]))


class TestReportSerialization(unittest.TestCase):
    """F6: to_dict emitted raw control_id, so json.dumps raised."""

    def test_malformed_control_id_still_serializes(self):
        report = GateReport()
        for cid in REQUIRED_CONTROL_IDS:
            report.add(ControlResult(cid, "REQ", PASS, "ok"))
        for bogus in ({"a"}, b"x", 1 + 2j, ["x"]):
            with self.subTest(control_id=bogus):
                report.add(ControlResult(bogus, "REQ", PASS, "d"))
        serialized = json.dumps(report.to_dict())  # must not raise
        self.assertEqual(report.overall, FAIL)
        self.assertTrue(report.malformed_results)
        self.assertIn("required_control_ids", serialized)

    def test_report_still_lists_the_authoritative_denominator(self):
        report = GateReport()
        for cid in REQUIRED_CONTROL_IDS:
            report.add(ControlResult(cid, "REQ", PASS, "ok"))
        self.assertEqual(report.to_dict()["required_control_ids"],
                         list(REQUIRED_CONTROL_IDS))
        self.assertEqual(report.overall, PASS)


class TestExposureDiagnosticsAreTruthful(unittest.TestCase):
    """F9a: the FAIL text claimed 'any non-loopback bind is
    NETWORK_EXPOSED_PRODUCTION', contradicting D-P10-1, which also satisfies
    LOCAL_NON_NETWORK_EXPOSED via a project-local file socket or no socket."""

    def _doc(self, bind):
        doc = copy.deepcopy(_valid_slice())
        doc["axis_contracts"]["backend"]["exposure_class"] = "LOCAL_NON_NETWORK_EXPOSED"
        doc["axis_contracts"]["backend"]["observed_bind_address"] = bind
        return doc

    def test_control_never_relabels_an_unclassifiable_bind_as_network_exposed(self):
        for bind in ("8.8.8.8:53", "203.0.113.9", "example.com:443", "unix:/tmp/s.sock",
                     "127.0.0.1:port", "0.0.0.0:8080"):
            with self.subTest(bind=bind):
                detail = check_exposure_declaration(self._doc(bind)).detail
                self.assertNotIn("any non-loopback bind is NETWORK_EXPOSED_PRODUCTION",
                                 detail)

    def test_detail_cites_the_file_socket_and_no_socket_states(self):
        detail = check_exposure_declaration(self._doc("8.8.8.8:53")).detail
        self.assertIn("project-local file socket", detail)
        self.assertIn("no socket at all", detail)

    def test_verdicts_are_unchanged(self):
        for bind in ("127.0.0.1:8000", "localhost:3000", "[::1]:8080"):
            with self.subTest(loopback=bind):
                self.assertEqual(
                    check_exposure_declaration(self._doc(bind)).result, BLOCKED)
        for bind in ("0.0.0.0:8080", "*", "8.8.8.8:53"):
            with self.subTest(public=bind):
                self.assertEqual(check_exposure_declaration(self._doc(bind)).result, FAIL)


class TestFieldExtractionDelegation(unittest.TestCase):
    """F5: the gate kept a second, divergent copy of the authoritative
    extractor instead of delegating."""

    def test_gate_field_names_match_the_authoritative_registry(self):
        from framework.domain.frontend.layout_registry import _extract_field_names
        for content_type in (HOME_CT,
                             {"id": "X", "name": "home",
                              "fields": ["heading", "body"]},
                             {"id": "X", "name": "home", "fields": []}):
            with self.subTest(content_type=content_type):
                self.assertEqual(_content_type_fields(content_type),
                                 set(_extract_field_names(content_type)))

    def test_malformed_content_type_fails_closed(self):
        self.assertIsNone(_content_type_fields({"id": "X", "fields": [{"noname": 1}]}))
        self.assertIsNone(_content_type_fields({"id": "X"}))
        self.assertIsNone(_content_type_fields("not-a-mapping"))


class TestEvidenceBoundaryNotRegressed(unittest.TestCase):
    """The previously-fixed containment must survive the NUL-byte change."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_absolute_traversal_and_symlink_escape_are_still_rejected(self):
        outside = os.path.join(self.tmp, "outside-ev")
        os.makedirs(outside, exist_ok=True)
        secret = os.path.join(outside, "secret.txt")
        with open(secret, "w", encoding="utf-8") as handle:
            handle.write("x")
        os.symlink(secret, os.path.join(self.tmp, "escaped.txt"))
        for ref in ("/etc/passwd", "../../../etc/passwd", "escaped.txt",
                    os.path.abspath(secret), "~/x", "nonexistent.json"):
            with self.subTest(ref=ref):
                doc = _valid_slice()
                doc["evidence_references"] = [ref]
                self.assertEqual(check_evidence_references(doc, self.tmp).result, FAIL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
