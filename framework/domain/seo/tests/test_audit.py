"""Unit, security, schema, and CLI tests for P9 Pre-Deployment SEO Audit Engine.

Covers REQ-P9-09:
- Pre-deployment audit orchestrating all 16+ roadmap dimensions (REQ-P9-01..08)
- 19 dimension entries matching P9 architecture matrix (>= 16 dimensions required by schema)
- Dual-mode execution:
    * advisory mode: reports findings without failing build (exit code 0)
    * deployment mode: enforces non-zero exit code (exit code 1) on CRITICAL defects
- Schema conformance:
    * JSON report conforms strictly to framework/sps2/schemas/p9-audit.schema.json
    * Formal EV-SEO-* evidence record conforms to framework/sps2/governance/SCHEMAS/evidence.schema.json
- Deterministic SHA-256 artifact digest of audited files/routes
- Strict preservation of CONF-001 boundary:
    * CLS uses only verified thresholds (<= 0.1 Good, > 0.25 Poor)
    * LCP and INP strictly reported as NOT_APPLICABLE with exact authorized rationale:
      "Unobserved research threshold per CONF-001; numeric thresholds not established. No synthetic thresholds permitted."
    * Zero numeric thresholds for LCP or INP anywhere in code or diagnostics
- Pure Python standard library only; zero network requests.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from framework.domain.seo.audit import (
    audit_directory,
    build_evidence_record,
    render_audit_markdown,
    run_seo_audit,
    validate_audit_report_schema,
)
from framework.domain.seo.cwv import CONF_001_NA_RATIONALE
from framework.domain.seo.model import (
    AuditCheck,
    AuditDimension,
    AuditReport,
    AuditSummary,
    RedirectRule,
)
from framework.sps2.tools.seo_audit import main as cli_main


# Sample HTML snippets for testing
VALID_HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Clean Example Page for Pre-Deployment SEO Audit Testing</title>
  <meta name="description" content="This is a valid, well-formed meta description conforming strictly to character length recommendations between 50 and 160 characters.">
  <link rel="canonical" href="https://example.com/about">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "About SPS",
    "url": "https://example.com/about"
  }
  </script>
</head>
<body>
  <header>
    <h1>About SPS System</h1>
  </header>
  <main>
    <h2>Our Architecture</h2>
    <p>We provide standard compliance and security verification.</p>
    <a href="/about">About SPS</a>
    <img src="/images/diagram.png" alt="Architecture diagram showing components" width="800" height="600">
  </main>
</body>
</html>"""

PAGE_WITH_CRITICAL_DEFECTS = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <!-- Missing title and description -->
  <!-- Broken canonical with SSRF IP -->
  <link rel="canonical" href="http://127.0.0.1/admin">
</head>
<body>
  <!-- Missing H1 and sequence jump -->
  <h2>Section Heading Without Preceding H1</h2>
  <h4>Deep Jump Without Intermediate H3</h4>
  <!-- Unsized image with generic alt -->
  <img src="/assets/IMG_1234.png" alt="image">
  <!-- JavaScript void link -->
  <a href="javascript:void(0)">Click me</a>
</body>
</html>"""

PAGE_WITH_WARNING_ONLY = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Short Title</title>
  <meta name="description" content="Too short">
  <link rel="canonical" href="https://example.com/warning">
</head>
<body>
  <h1>Warning Test Page</h1>
  <p>Some text</p>
  <img src="/assets/good-photo.jpg" alt="A descriptive alt text for this photo" width="400" height="300">
</body>
</html>"""

SAMPLE_ROBOTS_TXT = """User-agent: *
Allow: /
Disallow: /admin
Sitemap: https://example.com/sitemap.xml
"""

SAMPLE_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://example.com/about</loc>
    <lastmod>2026-10-07T00:00:00Z</lastmod>
  </url>
</urlset>
"""


class TestAuditEngineBaseline(unittest.TestCase):
    """Test baseline pre-deployment audit execution, dimensions, and CONF-001 preservation."""

    def test_all_16_plus_dimensions_evaluated(self) -> None:
        report = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            robots_txt_content=SAMPLE_ROBOTS_TXT,
            sitemap_xml_content=SAMPLE_SITEMAP_XML,
            canonical_domain="https://example.com",
            mode="advisory",
        )
        # Schema requires minItems: 16. Our architecture matrix specifies 19 dimensions.
        self.assertGreaterEqual(len(report.dimensions), 16)
        self.assertEqual(len(report.dimensions), 19)

        # Every dimension must have an ID, Name, Status, and Checks list
        for dim in report.dimensions:
            self.assertTrue(bool(dim.dimension_id))
            self.assertTrue(bool(dim.dimension_name))
            self.assertIn(dim.status, ("PASS", "WARNING", "FAIL", "NOT_APPLICABLE"))
            self.assertIsInstance(dim.checks, list)
            if dim.status == "NOT_APPLICABLE":
                self.assertTrue(
                    bool(dim.na_rationale and dim.na_rationale.strip()),
                    f"Dimension {dim.dimension_id} is NOT_APPLICABLE but has no na_rationale",
                )

    def test_strict_conf_001_preservation(self) -> None:
        """CONF-001: LCP and INP must be strictly reported as NOT_APPLICABLE with zero synthetic thresholds."""
        report = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            robots_txt_content=SAMPLE_ROBOTS_TXT,
            sitemap_xml_content=SAMPLE_SITEMAP_XML,
            canonical_domain="https://example.com",
            mode="advisory",
        )
        lcp_inp_dims = [d for d in report.dimensions if "LCP" in d.dimension_id]
        self.assertEqual(len(lcp_inp_dims), 1)
        dim = lcp_inp_dims[0]
        self.assertEqual(dim.status, "NOT_APPLICABLE")
        self.assertEqual(dim.na_rationale, CONF_001_NA_RATIONALE)
        self.assertIn("Unobserved research threshold per CONF-001", dim.na_rationale or "")

        for chk in dim.checks:
            self.assertEqual(chk.result, "NA")
            # Verify no invented numeric thresholds in messages
            self.assertFalse(re.search(r"(LCP|INP)\s*[:=]?\s*\d+", chk.message))

    def test_cls_threshold_enforcement(self) -> None:
        """CLS must evaluate against verified thresholds: <= 0.1 Good, > 0.25 Poor."""
        # CLS = 0.05 (Good -> PASS)
        rep_good = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            observed_cls=0.05,
            mode="advisory",
        )
        cls_dim_good = next(d for d in rep_good.dimensions if "CLS" in d.dimension_id)
        self.assertEqual(cls_dim_good.status, "PASS")

        # CLS = 0.20 (Needs improvement -> WARNING)
        rep_warn = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            observed_cls=0.20,
            mode="advisory",
        )
        cls_dim_warn = next(d for d in rep_warn.dimensions if "CLS" in d.dimension_id)
        self.assertEqual(cls_dim_warn.status, "WARNING")

        # CLS = 0.35 (Poor -> FAIL / CRITICAL)
        rep_poor = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            observed_cls=0.35,
            mode="deployment",
        )
        cls_dim_poor = next(d for d in rep_poor.dimensions if "CLS" in d.dimension_id)
        self.assertEqual(cls_dim_poor.status, "FAIL")
        self.assertEqual(rep_poor.exit_code, 1)

    def test_default_specialized_dimensions_na(self) -> None:
        """By default, specialized dimensions (multilingual, local, ecommerce) are NOT_APPLICABLE."""
        report = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            mode="advisory",
        )
        multi_dim = next(d for d in report.dimensions if "i18n" in d.dimension_id)
        local_dim = next(d for d in report.dimensions if "local" in d.dimension_id)
        ecom_dim = next(d for d in report.dimensions if "ecommerce" in d.dimension_id)

        self.assertEqual(multi_dim.status, "NOT_APPLICABLE")
        self.assertTrue(bool(multi_dim.na_rationale))
        self.assertEqual(local_dim.status, "NOT_APPLICABLE")
        self.assertTrue(bool(local_dim.na_rationale))
        self.assertEqual(ecom_dim.status, "NOT_APPLICABLE")
        self.assertTrue(bool(ecom_dim.na_rationale))


class TestDualModeEnforcement(unittest.TestCase):
    """Test advisory mode (exit 0) vs deployment mode (exit 1 on critical defects)."""

    def test_clean_input_both_modes_exit_0(self) -> None:
        rep_adv = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            robots_txt_content=SAMPLE_ROBOTS_TXT,
            sitemap_xml_content=SAMPLE_SITEMAP_XML,
            mode="advisory",
        )
        self.assertEqual(rep_adv.exit_code, 0)
        self.assertEqual(rep_adv.summary.critical, 0)

        rep_dep = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            robots_txt_content=SAMPLE_ROBOTS_TXT,
            sitemap_xml_content=SAMPLE_SITEMAP_XML,
            mode="deployment",
        )
        self.assertEqual(rep_dep.exit_code, 0)
        self.assertEqual(rep_dep.summary.critical, 0)

    def test_critical_defects_advisory_mode_exits_0(self) -> None:
        """Advisory mode reports critical defects but returns exit code 0."""
        rep = run_seo_audit(
            pages={"https://example.com/critical": PAGE_WITH_CRITICAL_DEFECTS},
            mode="advisory",
        )
        self.assertGreater(rep.summary.critical, 0)
        self.assertEqual(rep.exit_code, 0)

    def test_critical_defects_deployment_mode_exits_1(self) -> None:
        """Deployment mode strictly fails with exit code 1 when critical defects exist."""
        rep = run_seo_audit(
            pages={"https://example.com/critical": PAGE_WITH_CRITICAL_DEFECTS},
            mode="deployment",
        )
        self.assertGreater(rep.summary.critical, 0)
        self.assertEqual(rep.exit_code, 1)

    def test_warning_only_deployment_mode_exits_0(self) -> None:
        """Deployment mode does NOT fail on WARNING-only findings."""
        rep = run_seo_audit(
            pages={"https://example.com/warning": PAGE_WITH_WARNING_ONLY},
            mode="deployment",
        )
        self.assertGreater(rep.summary.warnings, 0)
        self.assertEqual(rep.summary.critical, 0)
        self.assertEqual(rep.exit_code, 0)


class TestDeterministicOutput(unittest.TestCase):
    """Test deterministic report IDs, evidence references, and SHA-256 artifact digests."""

    def test_identical_inputs_produce_identical_digest(self) -> None:
        rep1 = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            robots_txt_content=SAMPLE_ROBOTS_TXT,
            sitemap_xml_content=SAMPLE_SITEMAP_XML,
            audit_counter=10,
            evidence_counter=10,
        )
        rep2 = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            robots_txt_content=SAMPLE_ROBOTS_TXT,
            sitemap_xml_content=SAMPLE_SITEMAP_XML,
            audit_counter=20,
            evidence_counter=20,
        )
        self.assertEqual(rep1.audited_artifacts_digest, rep2.audited_artifacts_digest)
        self.assertEqual(len(rep1.audited_artifacts_digest), 64)
        self.assertTrue(re.match(r"^[a-f0-9]{64}$", rep1.audited_artifacts_digest))

    def test_input_mutation_changes_digest(self) -> None:
        rep1 = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            robots_txt_content=SAMPLE_ROBOTS_TXT,
        )
        rep2 = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE + "<!-- extra -->"},
            robots_txt_content=SAMPLE_ROBOTS_TXT,
        )
        self.assertNotEqual(rep1.audited_artifacts_digest, rep2.audited_artifacts_digest)

    def test_audit_id_and_evidence_ref_format(self) -> None:
        rep = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            audit_counter=42,
            evidence_counter=7,
        )
        self.assertTrue(re.match(r"^AUDIT-SEO-[0-9]{8}-0042$", rep.audit_id))
        self.assertEqual(rep.evidence_ref, "EV-SEO-007")


class TestSchemaConformance(unittest.TestCase):
    """Test JSON serialization against framework/sps2/schemas/p9-audit.schema.json rules."""

    def test_valid_report_conforms_to_schema(self) -> None:
        report = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            robots_txt_content=SAMPLE_ROBOTS_TXT,
            sitemap_xml_content=SAMPLE_SITEMAP_XML,
            canonical_domain="https://example.com",
            mode="deployment",
        )
        rep_dict = report.to_dict()
        errors = validate_audit_report_schema(rep_dict)
        self.assertEqual(errors, [])

    def test_round_trip_serialization(self) -> None:
        report = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            mode="advisory",
        )
        rep_dict = report.to_dict()
        restored = AuditReport.from_dict(rep_dict)
        self.assertEqual(restored.audit_id, report.audit_id)
        self.assertEqual(restored.exit_code, report.exit_code)
        self.assertEqual(len(restored.dimensions), len(report.dimensions))
        self.assertEqual(restored.to_dict(), rep_dict)

    def test_schema_validator_catches_invalid_fields(self) -> None:
        # Missing required field
        bad_rep: dict[str, Any] = {
            "timestamp": "2026-10-07T00:00:00Z",
            "mode": "advisory",
            "exit_code": 0,
            "summary": {"total_checks": 1, "passed": 1, "warnings": 0, "critical": 0, "not_applicable": 0},
            "dimensions": [{"dimension_id": "1", "dimension_name": "x", "status": "PASS", "checks": []}] * 16,
            "evidence_ref": "EV-SEO-001",
        }
        errs = validate_audit_report_schema(bad_rep)
        self.assertTrue(any("Missing required top-level property 'audit_id'" in e for e in errs))

        # Invalid audit_id regex
        bad_rep["audit_id"] = "INVALID-ID"
        errs = validate_audit_report_schema(bad_rep)
        self.assertTrue(any("does not match pattern" in e for e in errs))

        # Fewer than 16 dimensions
        bad_rep["audit_id"] = "AUDIT-SEO-20261007-0001"
        bad_rep["dimensions"] = bad_rep["dimensions"][:10]
        errs = validate_audit_report_schema(bad_rep)
        self.assertTrue(any("requires at least 16" in e for e in errs))

        # NOT_APPLICABLE without na_rationale
        bad_rep["dimensions"] = [{"dimension_id": "1", "dimension_name": "x", "status": "NOT_APPLICABLE", "checks": []}] * 16
        errs = validate_audit_report_schema(bad_rep)
        self.assertTrue(any("na_rationale" in e for e in errs))

        # Unexpected property (additionalProperties: false)
        bad_rep["dimensions"] = [{"dimension_id": "1", "dimension_name": "x", "status": "PASS", "checks": []}] * 16
        bad_rep["unexpected_prop"] = "foo"
        errs = validate_audit_report_schema(bad_rep)
        self.assertTrue(any("Unexpected top-level property 'unexpected_prop'" in e for e in errs))


class TestFormalEvidenceRecord(unittest.TestCase):
    """Test formal EV-SEO-* evidence record generation and schema rules."""

    def test_clean_report_evidence_record(self) -> None:
        report = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            mode="deployment",
            evidence_counter=12,
        )
        ev = build_evidence_record(report, command="python3 framework/sps2/tools/seo_audit.py --mode=deployment")
        self.assertEqual(ev["evidence_id"], "EV-SEO-012")
        self.assertEqual(ev["source"], "VALIDATOR")
        self.assertEqual(ev["result"], "PASS")
        self.assertEqual(ev["exit_code"], 0)
        self.assertEqual(ev["relates_to"]["requirement_id"], "REQ-P9-09")
        self.assertTrue(len(ev["observed_result"]) > 0)
        self.assertTrue(re.match(r"^EV-SEO-[0-9]{3,}$", ev["evidence_id"]))

    def test_failed_report_evidence_record(self) -> None:
        report = run_seo_audit(
            pages={"https://example.com/critical": PAGE_WITH_CRITICAL_DEFECTS},
            mode="deployment",
            evidence_counter=99,
        )
        ev = build_evidence_record(report)
        self.assertEqual(ev["result"], "FAIL")
        self.assertEqual(ev["exit_code"], 1)


class TestSpecializedDimensionsEvaluation(unittest.TestCase):
    """Test multilingual, local, and ecommerce evaluation flags."""

    def test_multilingual_enabled_with_valid_hreflang(self) -> None:
        html_with_hreflang = """<!DOCTYPE html>
        <html lang="en">
        <head>
          <title>Global Page</title>
          <link rel="alternate" hreflang="en" href="https://example.com/about">
          <link rel="alternate" hreflang="es" href="https://example.com/es/about">
          <link rel="alternate" hreflang="x-default" href="https://example.com/about">
        </head>
        <body><h1>Hello</h1></body></html>"""

        rep = run_seo_audit(
            pages={"https://example.com/about": html_with_hreflang},
            is_multilingual=True,
            mode="advisory",
        )
        dim = next(d for d in rep.dimensions if "i18n" in d.dimension_id)
        self.assertEqual(dim.status, "PASS")
        self.assertIsNone(dim.na_rationale)

    def test_local_business_enabled_with_valid_schema(self) -> None:
        html_with_local = """<!DOCTYPE html>
        <html>
        <head>
          <title>Local Store</title>
          <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "SPS Local Store",
            "address": {
              "@type": "PostalAddress",
              "streetAddress": "123 Tech Lane",
              "addressLocality": "Austin",
              "addressRegion": "TX",
              "postalCode": "78701",
              "addressCountry": "US"
            }
          }
          </script>
        </head>
        <body><h1>Local Store</h1></body></html>"""

        rep = run_seo_audit(
            pages={"https://example.com/store": html_with_local},
            is_local_business=True,
            mode="advisory",
        )
        dim = next(d for d in rep.dimensions if "local" in d.dimension_id)
        self.assertEqual(dim.status, "PASS")
        self.assertIsNone(dim.na_rationale)

    def test_ecommerce_enabled_with_valid_schema(self) -> None:
        html_with_ecom = """<!DOCTYPE html>
        <html>
        <head>
          <title>Product Page</title>
          <script type="application/ld+json">
          {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "SPS Enterprise Suite",
            "offers": {
              "@type": "Offer",
              "price": "499.00",
              "priceCurrency": "USD",
              "availability": "https://schema.org/InStock"
            }
          }
          </script>
        </head>
        <body><h1>Product</h1></body></html>"""

        rep = run_seo_audit(
            pages={"https://example.com/product": html_with_ecom},
            is_ecommerce=True,
            mode="advisory",
        )
        dim = next(d for d in rep.dimensions if "ecommerce" in d.dimension_id)
        self.assertEqual(dim.status, "PASS")
        self.assertIsNone(dim.na_rationale)


class TestDirectoryAudit(unittest.TestCase):
    """Test directory scanning and auditing."""

    def test_audit_directory_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "about.html").write_text(VALID_HTML_PAGE, encoding="utf-8")
            (tmp_path / "robots.txt").write_text(SAMPLE_ROBOTS_TXT, encoding="utf-8")
            (tmp_path / "sitemap.xml").write_text(SAMPLE_SITEMAP_XML, encoding="utf-8")

            report = audit_directory(tmp_path, mode="deployment", canonical_domain="https://example.com")
            self.assertEqual(report.exit_code, 0)
            self.assertGreaterEqual(len(report.dimensions), 16)
            self.assertTrue(len(report.audited_artifacts_digest) == 64)

    def test_audit_single_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "page.html"
            file_path.write_text(VALID_HTML_PAGE, encoding="utf-8")

            report = audit_directory(file_path, mode="advisory")
            self.assertEqual(report.exit_code, 0)

    def test_audit_nonexistent_directory_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            audit_directory("/nonexistent/path/that/cannot/exist/12345")


class TestAuditMarkdownRendering(unittest.TestCase):
    """Test human-readable markdown generation."""

    def test_render_audit_markdown(self) -> None:
        report = run_seo_audit(
            pages={"https://example.com/about": VALID_HTML_PAGE},
            mode="advisory",
        )
        md = render_audit_markdown(report)
        self.assertIn("# SPS 2.0 SEO Pre-Deployment Audit Report", md)
        self.assertIn("## Summary Metrics", md)
        self.assertIn("## Dimension Breakdown", md)
        self.assertIn(report.audit_id, md)
        self.assertIn(report.evidence_ref, md)


class TestCLIRunner(unittest.TestCase):
    """Test CLI commands and argument combinations via framework/sps2/tools/seo_audit.py."""

    def test_cli_advisory_mode_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "about.html").write_text(VALID_HTML_PAGE, encoding="utf-8")

            exit_code = cli_main([str(tmp_path), "--mode=advisory", "--format=text"])
            self.assertEqual(exit_code, 0)

    def test_cli_deployment_mode_with_critical_defect(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "about.html").write_text(PAGE_WITH_CRITICAL_DEFECTS, encoding="utf-8")

            exit_code = cli_main([str(tmp_path), "--mode=deployment"])
            self.assertEqual(exit_code, 1)

    def test_cli_file_output_and_evidence_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            (tmp_path / "about.html").write_text(VALID_HTML_PAGE, encoding="utf-8")
            out_file = tmp_path / "audit_report.json"
            ev_file = tmp_path / "evidence.json"

            exit_code = cli_main([
                str(tmp_path),
                "--mode=advisory",
                "--format=json",
                "-o", str(out_file),
                "--evidence-out", str(ev_file),
                "--validate-schema",
            ])
            self.assertEqual(exit_code, 0)
            self.assertTrue(out_file.exists())
            self.assertTrue(ev_file.exists())

            # Validate json output contents
            data = json.loads(out_file.read_text(encoding="utf-8"))
            self.assertEqual(data["mode"], "advisory")
            self.assertGreaterEqual(len(data["dimensions"]), 16)

            ev_data = json.loads(ev_file.read_text(encoding="utf-8"))
            self.assertEqual(ev_data["source"], "VALIDATOR")
            self.assertEqual(ev_data["result"], "PASS")

    def test_cli_invalid_target_exits_2(self) -> None:
        exit_code = cli_main(["/definitely/invalid/target/path/98765"])
        self.assertEqual(exit_code, 2)


class TestSecurityAndResilience(unittest.TestCase):
    """Test engine resilience with malformed HTML, script injection, and empty inputs."""

    def test_malformed_html_handling(self) -> None:
        malformed = "<html><head><title>Unclosed title<body><h2>H2 without H1<img src='broken.jpg' alt=''>"
        rep = run_seo_audit(pages={"https://example.com/bad": malformed}, mode="advisory")
        self.assertIsNotNone(rep)
        self.assertGreaterEqual(len(rep.dimensions), 16)

    def test_script_breakout_attempt_in_html(self) -> None:
        breakout = """<!DOCTYPE html><html><head>
        <title>Breakout &lt;/script&gt; Attempt</title>
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "WebPage", "name": "</script><script>alert(1)</script>"}
        </script>
        </head><body><h1>Heading</h1></body></html>"""
        rep = run_seo_audit(pages={"https://example.com/breakout": breakout}, mode="advisory")
        self.assertIsNotNone(rep)

    def test_empty_inputs(self) -> None:
        rep = run_seo_audit(pages={}, mode="advisory")
        self.assertIsNotNone(rep)
        self.assertEqual(len(rep.dimensions), 19)
        self.assertEqual(rep.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
