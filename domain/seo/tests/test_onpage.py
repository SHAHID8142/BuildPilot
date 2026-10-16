"""Unit and security tests for P9 On-Page Structural Hierarchy and Internal Link Graph Engine.

Covers REQ-P9-04:
- Heading extraction and hierarchy evaluation
- Single-H1 rule enforcement
- Heading-level jump detection (e.g. H1 -> H3)
- Empty headings and headings with nested child tags
- Internal vs external link classification
- URL normalization and tracking parameter removal
- Static broken-link detection against known routes
- Explicit exclusion of live network probing (LINK_NETWORK_CHECK_SKIPPED)
- Generic and empty anchor text diagnostics
- Duplicate internal link target tracking
- Unsafe URI scheme and SSRF protection
- Malicious HTML attribute input resilience
- Deterministic analysis results
"""
from __future__ import annotations

import unittest

from domain.seo.onpage import (
    OnPageHTMLParser,
    analyze_headings,
    analyze_links,
    analyze_onpage,
)


class TestHeadingHierarchyAnalysis(unittest.TestCase):
    """Test heading extraction and structural hierarchy rules."""

    def test_valid_heading_hierarchy(self) -> None:
        html = """
        <html>
        <body>
            <h1>Main Page Title</h1>
            <p>Intro paragraph</p>
            <h2>Section 1: Introduction</h2>
            <p>Details</p>
            <h3>Subsection 1.1: Context</h3>
            <p>Sub details</p>
            <h2>Section 2: Architecture</h2>
            <p>Arch details</p>
        </body>
        </html>
        """
        res = analyze_headings(html)
        self.assertEqual(res.h1_count, 1)
        self.assertEqual(len(res.headings), 4)
        self.assertEqual(res.headings[0].level, 1)
        self.assertEqual(res.headings[0].text, "Main Page Title")
        self.assertEqual(res.headings[1].level, 2)
        self.assertEqual(res.headings[2].level, 3)
        self.assertEqual(res.headings[3].level, 2)
        self.assertEqual(len(res.issues), 0, f"Expected 0 issues, got: {res.issues}")

    def test_heading_no_h1_detected(self) -> None:
        html = """
        <div>
            <h2>Section Without H1</h2>
            <h3>Subsection</h3>
        </div>
        """
        res = analyze_headings(html)
        self.assertEqual(res.h1_count, 0)
        issue_codes = [i.code for i in res.issues]
        self.assertIn("HEADING_NO_H1", issue_codes)
        self.assertIn("HEADING_STARTS_WITHOUT_H1", issue_codes)

    def test_heading_multiple_h1_detected(self) -> None:
        html = """
        <div>
            <h1>First H1 Title</h1>
            <p>Some text</p>
            <h1>Second H1 Title</h1>
        </div>
        """
        res = analyze_headings(html)
        self.assertEqual(res.h1_count, 2)
        issue_codes = [i.code for i in res.issues]
        self.assertIn("HEADING_MULTIPLE_H1", issue_codes)

    def test_heading_level_skips(self) -> None:
        # H1 directly to H3 (skipping H2)
        html = """
        <div>
            <h1>Main Title</h1>
            <h3>Jumped to H3</h3>
            <h5>Jumped to H5</h5>
        </div>
        """
        res = analyze_headings(html)
        skip_issues = [i for i in res.issues if i.code == "HEADING_LEVEL_SKIPPED"]
        self.assertEqual(len(skip_issues), 2)
        self.assertIn("skipped <h2", skip_issues[0].message)

    def test_heading_step_down_is_not_flagged(self) -> None:
        # Decreasing heading depth (H3 -> H2 -> H1) is valid closing of sections
        html = """
        <div>
            <h1>Main</h1>
            <h2>Section 1</h2>
            <h3>Subsection 1.1</h3>
            <h2>Section 2</h2>
        </div>
        """
        res = analyze_headings(html)
        skip_issues = [i for i in res.issues if i.code == "HEADING_LEVEL_SKIPPED"]
        self.assertEqual(len(skip_issues), 0)

    def test_empty_heading_detected(self) -> None:
        html = """
        <div>
            <h1>Real Title</h1>
            <h2>   </h2>
        </div>
        """
        res = analyze_headings(html)
        issue_codes = [i.code for i in res.issues]
        self.assertIn("HEADING_EMPTY", issue_codes)

    def test_heading_with_nested_child_tags(self) -> None:
        html = """
        <h1>Welcome <span>to</span> <em>Our</em> <a href="/">Platform</a>!</h1>
        """
        res = analyze_headings(html)
        self.assertEqual(len(res.headings), 1)
        self.assertEqual(res.headings[0].text, "Welcome to Our Platform!")

    def test_malformed_unclosed_headings(self) -> None:
        html = """
        <h1>Unclosed Title
        <h2>Next Section Unclosed
        <p>Paragraph</p>
        """
        res = analyze_headings(html)
        self.assertEqual(len(res.headings), 2)
        self.assertEqual(res.headings[0].level, 1)
        self.assertEqual(res.headings[0].text, "Unclosed Title")
        self.assertEqual(res.headings[1].level, 2)
        self.assertEqual(res.headings[1].text, "Next Section Unclosed")


class TestLinkGraphAnalysis(unittest.TestCase):
    """Test link extraction, classification, normalization, and diagnostics."""

    def test_internal_vs_external_classification(self) -> None:
        html = """
        <div>
            <a href="/about">About Us</a>
            <a href="contact">Contact</a>
            <a href="https://mysite.com/services">Services</a>
            <a href="https://external.com/partner">Partner</a>
            <a href="https://google.com">Google</a>
        </div>
        """
        res = analyze_links(html, base_url="https://mysite.com", current_path="/")
        self.assertEqual(len(res.internal_links), 3)
        self.assertEqual(len(res.external_links), 2)

        internal_hrefs = [l.href for l in res.internal_links]
        self.assertIn("/about", internal_hrefs)
        self.assertIn("contact", internal_hrefs)
        self.assertIn("https://mysite.com/services", internal_hrefs)

        external_hrefs = [l.href for l in res.external_links]
        self.assertIn("https://external.com/partner", external_hrefs)
        self.assertIn("https://google.com", external_hrefs)

    def test_url_normalization_and_tracking_param_removal(self) -> None:
        html = """
        <div>
            <a href="/blog///post-1/?utm_source=twitter&utm_medium=cpc&author=alice">Post 1</a>
        </div>
        """
        res = analyze_links(html, base_url="https://mysite.com")
        self.assertEqual(len(res.internal_links), 1)
        norm_url = res.internal_links[0].normalized_url
        self.assertEqual(norm_url, "/blog/post-1?author=alice")
        self.assertNotIn("utm_source", norm_url)
        self.assertNotIn("utm_medium", norm_url)

    def test_broken_internal_links_against_known_routes(self) -> None:
        known = ["/", "/about", "/products", "/contact"]
        html = """
        <div>
            <a href="/">Home</a>
            <a href="/about">About</a>
            <a href="/missing-page">Missing</a>
            <a href="/products/unknown-item">Unknown Product</a>
        </div>
        """
        res = analyze_links(html, base_url="https://mysite.com", known_routes=known)
        self.assertEqual(len(res.broken_links), 2)
        broken_hrefs = [l.href for l in res.broken_links]
        self.assertIn("/missing-page", broken_hrefs)
        self.assertIn("/products/unknown-item", broken_hrefs)

        broken_issues = [i for i in res.issues if i.code == "LINK_BROKEN_INTERNAL_ROUTE"]
        self.assertEqual(len(broken_issues), 2)

    def test_network_check_skipped_when_no_known_routes(self) -> None:
        html = """<a href="/about">About Us</a>"""
        res = analyze_links(html, base_url="https://mysite.com", known_routes=None)
        # Verify machine-readable notice confirming network probing was excluded
        notice = [i for i in res.issues if i.code == "LINK_NETWORK_CHECK_SKIPPED"]
        self.assertEqual(len(notice), 1)
        self.assertIn("Live HTTP link verification skipped", notice[0].message)

    def test_generic_and_empty_anchor_text(self) -> None:
        html = """
        <div>
            <a href="/page-1">click here</a>
            <a href="/page-2">Read More</a>
            <a href="/page-3"></a>
            <a href="/page-4">Detailed Guide on SEO</a>
            <a href="/page-5"><img src="icon.png" alt="Accessible Icon"></a>
        </div>
        """
        res = analyze_links(html, base_url="https://mysite.com")
        issue_codes = [i.code for i in res.issues]
        self.assertIn("LINK_GENERIC_ANCHOR_TEXT", issue_codes)
        self.assertIn("LINK_EMPTY_ANCHOR_TEXT", issue_codes)

        # Page 5 with img alt must NOT have empty anchor text
        link5 = [l for l in res.internal_links if l.href == "/page-5"][0]
        self.assertEqual(link5.anchor_text, "Accessible Icon")

    def test_duplicate_internal_link_targets(self) -> None:
        html = """
        <div>
            <a href="/about">About</a>
            <a href="/about">Learn More About Us</a>
            <a href="/about#team">Meet Team</a>
        </div>
        """
        res = analyze_links(html, base_url="https://mysite.com")
        dup_issues = [i for i in res.issues if i.code == "LINK_DUPLICATE_INTERNAL_TARGET"]
        self.assertTrue(len(dup_issues) > 0)
        self.assertIn("/about", dup_issues[0].message)

    def test_unsafe_schemes_rejected(self) -> None:
        html = """
        <div>
            <a href="javascript:alert('xss')">Exploit</a>
            <a href="data:text/html;base64,...">Data URL</a>
            <a href="file:///etc/passwd">Local File</a>
        </div>
        """
        res = analyze_links(html, base_url="https://mysite.com")
        unsafe_issues = [i for i in res.issues if i.code == "LINK_UNSAFE_SCHEME"]
        self.assertEqual(len(unsafe_issues), 3)

    def test_ssrf_private_and_loopback_links(self) -> None:
        html = """
        <div>
            <a href="http://127.0.0.1:8080/admin">Admin</a>
            <a href="http://169.254.169.254/latest/meta-data/">Cloud Meta</a>
        </div>
        """
        res = analyze_links(html, base_url="https://mysite.com")
        private_issues = [i for i in res.issues if i.code == "LINK_PRIVATE_IP_REJECTED"]
        self.assertEqual(len(private_issues), 2)


class TestOnPageUnifiedAnalysis(unittest.TestCase):
    """Test full document on-page structural analysis."""

    def test_analyze_onpage_combined(self) -> None:
        html = """<!DOCTYPE html>
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Engineering Hub</h1>
            <h2>Architecture</h2>
            <p>Welcome to SPS 2.0. <a href="/architecture">Read Docs</a>.</p>
            <a href="/missing">Broken Link</a>
        </body>
        </html>
        """
        known = ["/", "/architecture"]
        result = analyze_onpage(
            html_content=html,
            base_url="https://example.com",
            known_routes=known,
        )
        self.assertEqual(result.headings.h1_count, 1)
        self.assertEqual(len(result.headings.headings), 2)
        self.assertEqual(len(result.links.internal_links), 2)
        self.assertEqual(len(result.links.broken_links), 1)
        self.assertEqual(result.links.broken_links[0].href, "/missing")

    def test_deterministic_diagnostics(self) -> None:
        html = "<h1>Title</h1><h3>Jump</h3><a href='/a'>click here</a>"
        res1 = analyze_onpage(html)
        res2 = analyze_onpage(html)

        dict1 = res1.to_dict()
        dict2 = res2.to_dict()
        self.assertEqual(dict1, dict2)


if __name__ == "__main__":
    unittest.main()
