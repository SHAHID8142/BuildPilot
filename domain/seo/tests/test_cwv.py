"""Unit and security tests for P9 Core Web Vitals & Layout Stability Engine.

Covers REQ-P9-07:
- Automated CLS verification using ONLY approved researched thresholds:
    * CLS <= 0.1 (Good / Pass)
    * CLS > 0.25 (Poor / Critical)
    * 0.1 < CLS <= 0.25 (Needs Improvement / Warning)
- Invalid / malformed CLS handling (negative, NaN, inf, non-numeric)
- Missing CLS input handling (observed_cls=None)
- Static layout-shift prevention:
    * Image dimension integration/reuse from domain.seo.media
    * Font-display analysis (@font-face missing font-display or using auto/block, font link without display=swap)
- Explicit LCP and INP gap representation:
    * Strictly machine-readable NOT_APPLICABLE findings
    * Exact approved N/A rationale per CONF-001
    * Zero invented numeric thresholds
- Rejection of attempts to supply synthetic/invented LCP or INP thresholds
- Deterministic dictionary serialization and deserialization
- Resilience against malformed/malicious HTML and CSS payloads
"""
from __future__ import annotations

import math
import unittest

from domain.seo.cwv import (
    CLS_GOOD_THRESHOLD,
    CLS_POOR_THRESHOLD,
    CONF_001_NA_RATIONALE,
    analyze_cwv,
    analyze_font_display_css,
    analyze_font_display_html,
    analyze_static_shift_prevention,
    assert_no_invented_thresholds,
    evaluate_cls,
    evaluate_inp,
    evaluate_lcp,
    validate_cwv_config,
)
from domain.seo.model import (
    CWVAnalysisResult,
    ValidationSeverity,
)


class TestCLSEvaluation(unittest.TestCase):
    """Test automated Cumulative Layout Shift evaluation against approved boundaries."""

    def test_cls_good_threshold(self) -> None:
        # CLS <= 0.1 is Good / Pass
        for val in (0.0, 0.05, 0.099, 0.1):
            res = evaluate_cls(val)
            self.assertEqual(res.status, "PASS", f"Value {val} should be PASS")
            self.assertEqual(res.observed_value, val)
            self.assertEqual(len([i for i in res.issues if i.severity == ValidationSeverity.CRITICAL]), 0)
            self.assertEqual(len([i for i in res.issues if i.severity == ValidationSeverity.WARNING]), 0)
            self.assertTrue(any(i.code == "CWV_CLS_GOOD" for i in res.issues))

    def test_cls_needs_improvement_boundary(self) -> None:
        # 0.1 < CLS <= 0.25 is Needs Improvement / Warning
        for val in (0.101, 0.15, 0.20, 0.25):
            res = evaluate_cls(val)
            self.assertEqual(res.status, "NEEDS_IMPROVEMENT", f"Value {val} should be NEEDS_IMPROVEMENT")
            self.assertEqual(res.observed_value, val)
            self.assertTrue(any(i.code == "CWV_CLS_NEEDS_IMPROVEMENT" for i in res.issues))
            self.assertTrue(any(i.severity == ValidationSeverity.WARNING for i in res.issues))
            self.assertEqual(len([i for i in res.issues if i.severity == ValidationSeverity.CRITICAL]), 0)

    def test_cls_poor_threshold(self) -> None:
        # CLS > 0.25 is Poor / Critical / Fail
        for val in (0.251, 0.30, 0.50, 1.2):
            res = evaluate_cls(val)
            self.assertEqual(res.status, "FAIL", f"Value {val} should be FAIL")
            self.assertEqual(res.observed_value, val)
            self.assertTrue(any(i.code == "CWV_CLS_POOR" for i in res.issues))
            self.assertTrue(any(i.severity == ValidationSeverity.CRITICAL for i in res.issues))

    def test_cls_missing_input(self) -> None:
        # observed_cls=None represents lack of runtime measurement
        res = evaluate_cls(None)
        self.assertEqual(res.status, "NOT_APPLICABLE")
        self.assertIsNone(res.observed_value)
        self.assertTrue(any(i.code == "CWV_CLS_NOT_PROVIDED" for i in res.issues))
        self.assertTrue(any(i.severity == ValidationSeverity.INFO for i in res.issues))

    def test_cls_negative_value_rejected(self) -> None:
        res = evaluate_cls(-0.05)
        self.assertEqual(res.status, "FAIL")
        self.assertTrue(any(i.code == "CWV_CLS_INVALID" and i.severity == ValidationSeverity.CRITICAL for i in res.issues))

    def test_cls_nan_and_inf_rejected(self) -> None:
        for bad_val in (float("nan"), float("inf"), float("-inf")):
            res = evaluate_cls(bad_val)
            self.assertEqual(res.status, "FAIL")
            self.assertTrue(any(i.code == "CWV_CLS_INVALID" and i.severity == ValidationSeverity.CRITICAL for i in res.issues))

    def test_cls_non_numeric_type_rejected(self) -> None:
        # Passing string or invalid type
        res = evaluate_cls("0.05")  # type: ignore[arg-type]
        self.assertEqual(res.status, "FAIL")
        self.assertTrue(any(i.code == "CWV_CLS_INVALID" and i.severity == ValidationSeverity.CRITICAL for i in res.issues))


class TestLCPAndINPCONF001Boundary(unittest.TestCase):
    """Test strict representation of unobserved LCP and INP metrics under CONF-001."""

    def test_lcp_representation(self) -> None:
        lcp = evaluate_lcp()
        self.assertEqual(lcp.metric_name, "LCP")
        self.assertEqual(lcp.status, "NOT_APPLICABLE")
        self.assertIsNone(lcp.observed_value)
        self.assertIsNone(lcp.threshold_description)
        self.assertEqual(lcp.na_rationale, CONF_001_NA_RATIONALE)
        self.assertEqual(len(lcp.issues), 0)

    def test_inp_representation(self) -> None:
        inp = evaluate_inp()
        self.assertEqual(inp.metric_name, "INP")
        self.assertEqual(inp.status, "NOT_APPLICABLE")
        self.assertIsNone(inp.observed_value)
        self.assertIsNone(inp.threshold_description)
        self.assertEqual(inp.na_rationale, CONF_001_NA_RATIONALE)
        self.assertEqual(len(inp.issues), 0)

    def test_exact_na_rationale_string(self) -> None:
        expected = (
            "Unobserved research threshold per CONF-001; numeric thresholds not established. "
            "No synthetic thresholds permitted."
        )
        self.assertEqual(CONF_001_NA_RATIONALE, expected)

    def test_rejection_of_invented_thresholds_in_function_call(self) -> None:
        # Attempts to pass synthetic LCP or INP threshold kwargs must raise ValueError
        with self.assertRaises(ValueError) as ctx:
            assert_no_invented_thresholds(lcp_threshold=2.5)
        self.assertIn("CONF-001", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            assert_no_invented_thresholds(inp_target=200)
        self.assertIn("CONF-001", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            analyze_cwv(lcp_max=4.0)
        self.assertIn("CONF-001", str(ctx.exception))

    def test_rejection_of_invented_thresholds_in_config(self) -> None:
        bad_config = {
            "site_name": "Test Site",
            "lcp_threshold": 2.5,
            "inp_numeric": 150,
        }
        issues = validate_cwv_config(bad_config)
        self.assertEqual(len(issues), 2)
        for issue in issues:
            self.assertEqual(issue.code, "CWV_CONF_001_VIOLATION")
            self.assertEqual(issue.severity, ValidationSeverity.CRITICAL)
            self.assertIn(CONF_001_NA_RATIONALE, issue.message)

    def test_valid_config_without_invented_thresholds(self) -> None:
        clean_config = {
            "site_name": "Test Site",
            "theme": "dark",
            "trailing_slash": False,
        }
        issues = validate_cwv_config(clean_config)
        self.assertEqual(len(issues), 0)


class TestStaticLayoutShiftPrevention(unittest.TestCase):
    """Test static HTML layout-shift causes (image dimensions and font-display)."""

    def test_images_with_dimensions_pass(self) -> None:
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Title</title></head>
        <body>
            <img src="/logo.png" alt="Company Logo" width="200" height="50" />
            <img src="/banner.jpg" alt="Hero Banner" style="aspect-ratio: 16/9;" />
        </body>
        </html>
        """
        res = analyze_static_shift_prevention(html)
        self.assertEqual(res.total_images_analyzed, 2)
        self.assertEqual(res.images_lacking_dimensions, 0)
        dimension_issues = [i for i in res.issues if i.code == "IMAGE_DIMENSIONS_MISSING"]
        self.assertEqual(len(dimension_issues), 0)

    def test_images_lacking_dimensions_detected(self) -> None:
        html = """
        <div>
            <img src="/hero.jpg" alt="Hero image without dimensions" />
        </div>
        """
        res = analyze_static_shift_prevention(html)
        self.assertEqual(res.total_images_analyzed, 1)
        self.assertEqual(res.images_lacking_dimensions, 1)
        self.assertTrue(any(i.code == "IMAGE_DIMENSIONS_MISSING" for i in res.issues))

    def test_font_display_css_missing(self) -> None:
        css = """
        @font-face {
            font-family: 'OpenSans';
            src: url('/fonts/OpenSans.woff2') format('woff2');
        }
        """
        issues = analyze_font_display_css(css)
        self.assertTrue(any(i.code == "CWV_FONT_DISPLAY_MISSING" for i in issues))

    def test_font_display_css_not_swap(self) -> None:
        css = """
        @font-face {
            font-family: 'Roboto';
            src: url('/fonts/Roboto.woff2') format('woff2');
            font-display: block;
        }
        """
        issues = analyze_font_display_css(css)
        self.assertTrue(any(i.code == "CWV_FONT_DISPLAY_NOT_SWAP" for i in issues))

    def test_font_display_css_swap_and_optional_pass(self) -> None:
        css = """
        @font-face {
            font-family: 'Inter';
            src: url('/fonts/Inter.woff2') format('woff2');
            font-display: swap;
        }
        @font-face {
            font-family: 'Merriweather';
            src: url('/fonts/Merriweather.woff2') format('woff2');
            font-display: optional;
        }
        """
        issues = analyze_font_display_css(css)
        self.assertEqual(len(issues), 0)

    def test_font_display_google_fonts_link_missing_swap(self) -> None:
        html = """
        <html>
        <head>
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700" />
        </head>
        <body><p>Hello</p></body>
        </html>
        """
        issues = analyze_font_display_html(html)
        self.assertTrue(any(i.code == "CWV_FONT_DISPLAY_MISSING" for i in issues))

    def test_font_display_google_fonts_link_with_swap_passes(self) -> None:
        html = """
        <html>
        <head>
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" />
        </head>
        <body><p>Hello</p></body>
        </html>
        """
        issues = analyze_font_display_html(html)
        self.assertEqual(len(issues), 0)

    def test_css_comments_handled_safely(self) -> None:
        css = """
        /* font-display: swap; in comment should not deceive parser */
        @font-face {
            font-family: 'Custom';
            src: url('/font.woff2');
        }
        """
        issues = analyze_font_display_css(css)
        self.assertTrue(any(i.code == "CWV_FONT_DISPLAY_MISSING" for i in issues))


class TestAggregateCWVAnalyzer(unittest.TestCase):
    """Test full aggregate analyze_cwv output, validity, and serialization."""

    def test_perfect_page_cwv_analysis(self) -> None:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Perfect Layout</title>
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter&display=swap" />
        </head>
        <body>
            <img src="/img.png" alt="Test image" width="600" height="400" />
        </body>
        </html>
        """
        res = analyze_cwv(html_content=html, observed_cls=0.04)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.cls.status, "PASS")
        self.assertEqual(res.cls.observed_value, 0.04)
        self.assertEqual(res.lcp.status, "NOT_APPLICABLE")
        self.assertEqual(res.inp.status, "NOT_APPLICABLE")
        self.assertEqual(res.conf_001_status, "UNRESOLVED")
        self.assertEqual(res.static_prevention.images_lacking_dimensions, 0)
        self.assertEqual(res.static_prevention.font_issues_count, 0)

    def test_failing_cwv_due_to_poor_cls(self) -> None:
        res = analyze_cwv(observed_cls=0.35)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.cls.status, "FAIL")
        self.assertTrue(any(i.code == "CWV_CLS_POOR" and i.severity == ValidationSeverity.CRITICAL for i in res.issues))

    def test_serialization_round_trip(self) -> None:
        res = analyze_cwv(
            html_content='<img src="/test.jpg" alt="test" width="100" height="100" />',
            observed_cls=0.08,
        )
        d = res.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["cls"]["status"], "PASS")
        self.assertEqual(d["lcp"]["status"], "NOT_APPLICABLE")
        self.assertEqual(d["inp"]["status"], "NOT_APPLICABLE")
        self.assertEqual(d["conf_001_status"], "UNRESOLVED")

        # Restore from dict
        restored = CWVAnalysisResult.from_dict(d)
        self.assertEqual(restored.cls.status, "PASS")
        self.assertEqual(restored.cls.observed_value, 0.08)
        self.assertEqual(restored.lcp.status, "NOT_APPLICABLE")
        self.assertEqual(restored.inp.status, "NOT_APPLICABLE")
        self.assertEqual(restored.conf_001_status, "UNRESOLVED")


class TestMalformedAndMaliciousPayloads(unittest.TestCase):
    """Test parser safety against malformed, deeply nested, or hostile payloads."""

    def test_unclosed_style_and_tags(self) -> None:
        malformed = "<style>@font-face { font-family: 'Broken'; <script>alert(1)</script>"
        res = analyze_cwv(html_content=malformed, observed_cls=0.02)
        self.assertTrue(res.is_valid)  # Should not crash

    def test_deeply_nested_html(self) -> None:
        nested = "<div>" * 500 + '<img src="/test.png" alt="Deep" width="10" height="10" />' + "</div>" * 500
        res = analyze_cwv(html_content=nested, observed_cls=0.01)
        self.assertTrue(res.is_valid)


if __name__ == "__main__":
    unittest.main()
