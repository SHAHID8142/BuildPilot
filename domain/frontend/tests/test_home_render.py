"""Integration tests for the P10 Home slice renderer and static build path.

These tests exercise the REAL implementation (domain.frontend.home_render)
against the REAL CMS inputs in domain/cms/data/ where relevant, plus
synthetic fixtures for failure modes the real data cannot express.

What these tests DO establish: fail-closed behavior, output-safety encoding,
structural reparse assertions, draft-vs-published handling, deterministic
byte-identical builds, the P9 artifact shape, and zero network/state-changing
surface.

What these tests DO NOT establish: cryptographic authenticity, human
authentication, production accessibility conformance (DEC-7103 deliberately
asserts structural checks only), deployment readiness (D-P10-1: nothing is
served), or a REQ-P10-09 gate pass. A passing suite here is implementation
verification, not slice approval.

Run:  python3 -B -m unittest domain.frontend.tests.test_home_render
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import tempfile
import unittest
from pathlib import Path

from domain.cms.output_safety import encode_for_html
from domain.frontend.home_render import (
    DEFAULT_CANONICAL_DOMAIN,
    DRAFT_POLICY_FAIL,
    DRAFT_POLICY_NOINDEX_PREVIEW,
    HomeBuildError,
    build_home_slice,
    find_content_record,
    render_home_document,
    validate_home_document,
)
from domain.seo.audit import audit_directory

REPO_ROOT = Path(__file__).resolve().parents[3]
SLICE_PATH = REPO_ROOT / "sps2" / "project" / "SLICE-P10-01.json"
CONTENT_PATH = REPO_ROOT / "domain" / "cms" / "data" / "content.json"
CONTENT_TYPES_PATH = REPO_ROOT / "domain" / "cms" / "data" / "content_types.json"

HOME_CT_ID = "c64e3d79694e49eebd6c09ee58a53c87"
HOME_CONTENT_ID = "60e51f0536cb413e86e96ff6f750846a"


def _load(path: Path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _slice(**overrides):
    doc = _load(SLICE_PATH)
    doc.update(overrides)
    return doc


def _published_content(**overrides):
    record = {
        "id": HOME_CONTENT_ID,
        "type_id": HOME_CT_ID,
        "title": "Build Smarter. Deliver with Confidence.",
        "body": "Bring planning, development, verification, and delivery into one structured workflow.",
        "status": "published",
        "published_at": "2026-10-16T00:00:00+00:00",
    }
    record.update(overrides)
    return record


class HomeRendererStructuralTests(unittest.TestCase):
    """Stage 3/4 behavior: rendering, reparse assertions, fail-closed inputs."""

    def test_renders_real_cms_values_through_approved_adapter(self):
        content = _load(CONTENT_PATH)
        cts = _load(CONTENT_TYPES_PATH)
        doc = render_home_document(_slice(), content, cts, draft_policy="noindex_preview")
        self.assertIn("<h1>", doc)
        # The real title, HTML-encoded exactly once, must appear.
        self.assertIn(encode_for_html(_load(CONTENT_PATH)[0]["title"]), doc)
        # No raw double-encoded artifact (the adapter encodes once, not twice).
        self.assertNotIn("&amp;amp;", doc)

    def test_document_structure_exactly_one_h1_no_jumps(self):
        content = [_published_content()]
        cts = _load(CONTENT_TYPES_PATH)
        doc = render_home_document(_slice(), content, cts)
        findings = validate_home_document(doc)
        self.assertEqual(findings, [], f"unexpected structural findings: {findings}")

    def test_reparse_flags_two_h1s(self):
        bad = "<html lang='en'><body><h1>a</h1><h1>b</h1></body></html>"
        codes = [f.code for f in validate_home_document(bad)]
        self.assertIn("H1_COUNT", codes)

    def test_reparse_flags_heading_jump(self):
        bad = "<html lang='en'><body><h1>a</h1><h3>c</h3></body></html>"
        codes = [f.code for f in validate_home_document(bad)]
        self.assertIn("HEADING_JUMP", codes)

    def test_reparse_flags_unclosed_and_missing_lang_and_viewport(self):
        # Truncated document: h1/body/html never closed.
        bad = '<html><body><h1>a'
        codes = [f.code for f in validate_home_document(bad)]
        self.assertIn("UNCLOSED_ELEMENTS", codes)
        bad2 = "<html><body><h1>a<p>b</body></html>"
        codes2 = [f.code for f in validate_home_document(bad2)]
        self.assertIn("MISMATCHED_TAGS", codes2)
        self.assertIn("LANG_MISSING", codes)
        self.assertIn("VIEWPORT_MISSING", codes)

    def test_published_document_declares_lang_and_viewport(self):
        content = [_published_content()]
        cts = _load(CONTENT_TYPES_PATH)
        doc = render_home_document(_slice(), content, cts)
        self.assertIn('<html lang="en">', doc)
        self.assertIn('name="viewport"', doc)


class HomeRendererFailClosedTests(unittest.TestCase):
    """Missing/invalid required fields and malformed inputs abort, never render."""

    def _cts(self):
        return _load(CONTENT_TYPES_PATH)

    def test_unknown_route_aborts(self):
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(_slice(route="/about"), [_published_content()], self._cts())
        self.assertIn("route", str(ctx.exception))

    def test_unknown_layout_aborts(self):
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(
                _slice(layout_id="other-layout"), [_published_content()], self._cts()
            )
        self.assertIn("layout", str(ctx.exception))

    def test_missing_content_record_aborts(self):
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(_slice(), [{"id": "other", "type_id": HOME_CT_ID}], self._cts())
        self.assertIn("not found", str(ctx.exception))

    def test_duplicate_content_id_aborts(self):
        dup = _published_content()
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(_slice(), [dup, dict(dup)], self._cts())
        self.assertIn("duplicate", str(ctx.exception))

    def test_content_type_mismatch_aborts(self):
        record = _published_content(type_id="other-type")
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(_slice(), [record], self._cts())
        self.assertIn("ContentType", str(ctx.exception))

    def test_missing_required_field_aborts(self):
        record = _published_content(title="")
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(_slice(), [record], self._cts())
        self.assertIn("slot resolution failed", str(ctx.exception))
        self.assertIn("MISSING_VALUE", str(ctx.exception))

    def test_non_string_field_aborts(self):
        record = _published_content(body=42)
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(_slice(), [record], self._cts())
        self.assertIn("INVALID_VALUE", str(ctx.exception))

    def test_missing_type_definition_aborts(self):
        record = _published_content(type_id="ghost-type")
        cts = [{"id": "unrelated", "name": "x", "fields": []}]
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(_slice(), [record], cts)
        self.assertIn("ContentType definition was not found", str(ctx.exception))

    def test_multiple_content_references_aborts(self):
        doc = _slice()
        doc["cms_content_references"] = [
            {"content_id": HOME_CONTENT_ID, "field_slots": ["heading", "body"], "required_status": "published"},
            {"content_id": "another", "field_slots": ["heading"], "required_status": "published"},
        ]
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(doc, [_published_content()], self._cts())
        self.assertIn("exactly one", str(ctx.exception))


class HomeOutputSafetyTests(unittest.TestCase):
    """HTML escaping and the no-raw-content-path rule."""

    def test_malicious_title_is_encoded_not_interpreted(self):
        record = _published_content(
            title="<script>alert('xss')</script>",
            body="<img src=x onerror=alert(1)>",
        )
        doc = render_home_document(_slice(), [record], _load(CONTENT_TYPES_PATH))
        self.assertNotIn("<script>", doc)
        self.assertNotIn("<img", doc)
        self.assertIn(encode_for_html("<script>alert('xss')</script>"), doc)

    def test_attribute_breakout_via_heading_is_encoded(self):
        record = _published_content(title='"><img src=x onerror=alert(1)>')
        doc = render_home_document(_slice(), [record], _load(CONTENT_TYPES_PATH))
        self.assertNotIn("<img", doc)
        self.assertIn("&quot;&gt;", doc)

    def test_ampersands_and_quotes_round_trip_encoded_once(self):
        record = _published_content(title="A & B < C > D \" E ' F", body="x & y")
        doc = render_home_document(_slice(), [record], _load(CONTENT_TYPES_PATH))
        self.assertIn("A &amp; B &lt; C &gt; D &quot; E &#x27; F", doc)


class HomeDraftPublishedTests(unittest.TestCase):
    """Draft-versus-published handling: a draft never silently becomes a route."""

    def _cts(self):
        return _load(CONTENT_TYPES_PATH)

    def test_default_policy_aborts_on_draft(self):
        record = _published_content(status="draft", published_at=None)
        with self.assertRaises(HomeBuildError) as ctx:
            render_home_document(_slice(), [record], self._cts())
        self.assertIn("draft", str(ctx.exception))
        self.assertIn("aborts", str(ctx.exception))

    def test_preview_policy_marks_noindex_and_excludes_from_sitemap(self):
        record = _published_content(status="draft", published_at=None)
        tmp = Path(tempfile.mkdtemp())
        try:
            result = build_home_slice(
                _slice(), [record], self._cts(), tmp,
                draft_policy=DRAFT_POLICY_NOINDEX_PREVIEW,
            )
            self.assertTrue(result.draft_preview)
            self.assertEqual(result.sitemap_url_count, 0)
            doc = (tmp / "index.html").read_text(encoding="utf-8")
            self.assertIn("noindex", doc)
            self.assertIn("nofollow", doc)
            sitemap = (tmp / "sitemap.xml").read_text(encoding="utf-8")
            self.assertNotIn(HOME_CONTENT_ID, sitemap)
        finally:
            shutil.rmtree(tmp)

    def test_published_build_includes_route_in_sitemap(self):
        record = _published_content(slug="home")
        tmp = Path(tempfile.mkdtemp())
        try:
            result = build_home_slice(
                _slice(), [record], self._cts(), tmp,
            )
            self.assertFalse(result.draft_preview)
            self.assertEqual(result.sitemap_url_count, 1)
            sitemap = (tmp / "sitemap.xml").read_text(encoding="utf-8")
            self.assertIn("home", sitemap)
        finally:
            shutil.rmtree(tmp)

    def test_real_cms_data_is_draft_and_default_build_aborts(self):
        # The REAL repository content is draft: the default build must abort.
        content = _load(CONTENT_PATH)
        with self.assertRaises(HomeBuildError):
            build_home_slice(_slice(), content, self._cts(), tempfile.mkdtemp())


class HomeBuildShapeTests(unittest.TestCase):
    """Build artifact shape, determinism, and the P9 audit boundary."""

    def setUp(self):
        self._tmps = []

    def _tmp(self):
        t = tempfile.mkdtemp()
        self._tmps.append(t)
        return Path(t)

    def tearDown(self):
        for t in self._tmps:
            shutil.rmtree(t, ignore_errors=True)

    def _build(self, build_dir, content=None):
        return build_home_slice(
            _slice(),
            content if content is not None else [_published_content(slug="home")],
            _load(CONTENT_TYPES_PATH),
            build_dir,
        )

    def test_artifact_set_is_exactly_p9_contract_shape(self):
        out = self._tmp()
        result = self._build(out)
        self.assertEqual(
            sorted(p.name for p in out.iterdir()),
            ["index.html", "robots.txt", "sitemap.xml"],
        )
        self.assertEqual(result.route, "/")
        self.assertEqual(result.layout_id, "home-default")

    def test_route_maps_to_index_html_deterministically(self):
        out = self._tmp()
        self._build(out)
        doc = (out / "index.html").read_text(encoding="utf-8")
        self.assertIn("<h1>", doc)
        # The P9 audit's route derivation for index.html is "/" - the audit
        # must agree with the build (p10_to_p9_contract canonical_route_mapping).
        rep = audit_directory(out, mode="deployment")
        routes = [
            c.get("target_url")
            for dim in rep.to_dict()["dimensions"]
            for c in dim.get("checks", [])
            if c.get("target_url")
        ]
        self.assertTrue(any(r.endswith("example.com/") or r.endswith("example.com") for r in routes))

    def test_identical_inputs_byte_identical_outputs(self):
        out1, out2 = self._tmp(), self._tmp()
        self._build(out1)
        self._build(out2)
        for name in ("index.html", "robots.txt", "sitemap.xml"):
            self.assertEqual(
                (out1 / name).read_bytes(),
                (out2 / name).read_bytes(),
                f"{name} not deterministic",
            )

    def test_robots_and_sitemap_generated_through_p9_engines(self):
        out = self._tmp()
        self._build(out)
        robots = (out / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("User-agent: *", robots)
        self.assertIn("Sitemap: https://example.com/sitemap.xml", robots)
        sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn('xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"', sitemap)

    def test_p9_deployment_audit_exits_zero_on_published_build(self):
        out = self._tmp()
        self._build(out)
        rep = audit_directory(out, mode="deployment")
        self.assertEqual(rep.exit_code, 0)
        self.assertIsNotNone(rep.to_dict().get("audited_artifacts_digest"))

    def test_build_writes_nothing_outside_declared_dir(self):
        out = self._tmp()
        parent = out.parent
        before = sorted(p.name for p in parent.iterdir())
        self._build(out)
        after = sorted(p.name for p in parent.iterdir())
        self.assertEqual(before, after)


class HomeNoNetworkNoBackendTests(unittest.TestCase):
    """DEC-7101 boundary: no socket, no server, no state-changing operations."""

    def test_renderer_module_imports_no_socket_server_subprocess(self):
        # AST-based scan: imports and attribute calls only, so prose in
        # docstrings/comments cannot false-positive (the module's docstring
        # legitimately states that it uses NO such primitive).
        import ast
        import domain.frontend.home_render as hr
        tree = ast.parse(open(hr.__file__, encoding="utf-8").read())
        banned_modules = {"socket", "subprocess", "http", "urllib", "ftplib",
                          "telnetlib", "smtplib", "asyncio", "multiprocessing"}
        banned_attrs = {"socket", "HTTPServer", "system", "popen", "urlopen"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    self.assertNotIn(root, banned_modules, f"forbidden import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                self.assertNotIn(root, banned_modules, f"forbidden import-from: {node.module}")
            elif isinstance(node, ast.Attribute):
                self.assertNotIn(node.attr, banned_attrs, f"forbidden attribute: {node.attr}")

    def test_build_performs_no_network_io(self):
        # Fail the test if any socket is created during a full build.
        created = []
        real_socket = socket.socket

        class _Spy(real_socket):  # type: ignore[misc,valid-type]
            def __init__(self, *args, **kwargs):
                created.append(1)
                raise AssertionError("network socket created during build")

        content = [_published_content(slug="home")]
        tmp = Path(tempfile.mkdtemp())
        try:
            socket.socket = _Spy
            try:
                build_home_slice(
                    _slice(), content, _load(CONTENT_TYPES_PATH), tmp
                )
            finally:
                socket.socket = real_socket
            self.assertEqual(created, [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_slice_declares_no_state_changing_operations(self):
        doc = _load(SLICE_PATH)
        self.assertEqual(doc["axis_contracts"]["backend"]["state_changing_operations"], [])
        self.assertEqual(doc["axis_contracts"]["backend"]["exposure_class"], "LOCAL_NON_NETWORK_EXPOSED")
        self.assertEqual(doc["axis_contracts"]["data"]["data_dependencies"], [])


class HomeEvidenceBoundaryTests(unittest.TestCase):
    """Absent/invalid evidence and gate integration: honest, not manufactured."""

    def test_slice_evidence_reference_resolves(self):
        ref = _load(SLICE_PATH)["evidence_references"][0]
        target = (SLICE_PATH.parent / ref).resolve()
        self.assertTrue(target.is_file(), f"evidence reference does not resolve: {ref}")

    def test_evidence_placeholder_is_blocked_not_pass(self):
        evidence = _load(REPO_ROOT / "sps2" / "evidence" / "P10-EVIDENCE.json")
        self.assertEqual(evidence["records"][0]["result"], "BLOCKED")
        self.assertEqual(evidence["closure"]["state"], "NOT_CLOSED")

    def test_slice_is_draft_with_null_approval(self):
        doc = _load(SLICE_PATH)
        self.assertEqual(doc["acceptance_state"], "DRAFT")
        self.assertIsNone(doc["user_approval"])

    def test_real_gate_runs_against_real_slice_and_fails_closed(self):
        # The actual runtime gate, actual slice, actual exit code. The gate
        # MUST fail (draft content, no approval, unimplemented semantics);
        # a PASS here would indicate manufactured evidence.
        import subprocess
        import sys
        proc = subprocess.run(
            [sys.executable, "-B", str(REPO_ROOT / "sps2" / "tools" / "p10_runtime_gate.py"),
             "--slice", str(SLICE_PATH)],
            capture_output=True, text=True, cwd=REPO_ROOT,
        )
        self.assertEqual(proc.returncode, 1, "gate must fail closed on the real draft slice")
        self.assertIn("OVERALL: FAIL", proc.stdout)
        # The three controls this implementation genuinely satisfies must pass.
        for control in ("schema-structural", "slice-required-fields", "layout-slot-conformance"):
            self.assertRegex(proc.stdout, rf"\[PASS\s*\] {control}\b")

    def test_find_content_record_identity_is_by_id_not_position(self):
        first = _published_content(id="a")
        second = _published_content(id=HOME_CONTENT_ID)
        found = find_content_record([first, second], HOME_CONTENT_ID)
        self.assertEqual(found["id"], HOME_CONTENT_ID)


if __name__ == "__main__":
    unittest.main()
