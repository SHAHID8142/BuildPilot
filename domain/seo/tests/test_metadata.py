"""Tests for P9 SEO metadata, canonical engine, and HTML tag rendering."""
from __future__ import annotations

import unittest

from domain.cms.model import Content
from domain.seo.metadata import (
    generate_metadata_from_content,
    render_html_meta_tags,
    validate_canonical_url,
    validate_metadata,
)
from domain.seo.model import (
    RobotsDirectives,
    SEOMetadata,
    ValidationSeverity,
)


class TestSEOMetadataEngine(unittest.TestCase):
    """Test suite for SEO metadata generation, validation, and rendering."""

    def test_canonical_url_valid_and_normalized(self) -> None:
        raw_url = "HTTPS://Example.COM:443/Blog//Post-1/?utm_source=twitter&category=tech#section2"
        res = validate_canonical_url(raw_url)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.normalized_url, "https://example.com/Blog/Post-1/?category=tech")

        # Verify tracking param was stripped
        codes = [issue.code for issue in res.issues]
        self.assertIn("CANONICAL_TRACKING_PARAM_STRIPPED", codes)
        self.assertIn("CANONICAL_FRAGMENT_STRIPPED", codes)

    def test_canonical_url_rejects_relative_urls(self) -> None:
        res = validate_canonical_url("/path/to/page")
        self.assertFalse(res.is_valid)
        codes = [issue.code for issue in res.issues]
        self.assertIn("CANONICAL_INVALID_SCHEME", codes)
        self.assertIn("CANONICAL_NOT_ABSOLUTE", codes)

    def test_canonical_url_rejects_non_http_schemes(self) -> None:
        for bad_scheme in ["javascript:alert(1)", "file:///etc/passwd", "ftp://ftp.example.com/"]:
            res = validate_canonical_url(bad_scheme)
            self.assertFalse(res.is_valid, f"Failed to reject: {bad_scheme}")
            self.assertTrue(any(i.code == "CANONICAL_INVALID_SCHEME" for i in res.issues))

    def test_canonical_url_ssrf_rejection(self) -> None:
        """Threat Model §5.3: Canonical URLs must reject private/loopback IP targets."""
        blocked_targets = [
            "http://127.0.0.1:8080/admin",
            "http://10.0.0.5/internal",
            "http://172.16.0.1/confidential",
            "http://192.168.1.100/router",
            "http://169.254.169.254/latest/meta-data",
            "http://[::1]/internal",
            "http://localhost:3000/",
        ]
        for target in blocked_targets:
            res = validate_canonical_url(target)
            self.assertFalse(res.is_valid, f"Failed to block SSRF target: {target}")
            codes = [issue.code for issue in res.issues]
            self.assertIn("CANONICAL_PRIVATE_IP_REJECTED", codes)

    def test_metadata_diagnostics_title(self) -> None:
        # Title missing
        meta_missing = SEOMetadata(
            title="",
            description="A perfectly valid meta description that provides ample summary information.",
            canonical_url="https://example.com/test",
        )
        issues = validate_metadata(meta_missing)
        self.assertTrue(any(i.code == "TITLE_MISSING" and i.severity == ValidationSeverity.CRITICAL for i in issues))

        # Title short
        meta_short = SEOMetadata(
            title="Short Title",
            description="A perfectly valid meta description that provides ample summary information.",
            canonical_url="https://example.com/test",
        )
        issues = validate_metadata(meta_short)
        self.assertTrue(any(i.code == "TITLE_TOO_SHORT" and i.severity == ValidationSeverity.WARNING for i in issues))

        # Title excessive length (> 70 chars)
        meta_long = SEOMetadata(
            title="This title is excessively long and stretches well beyond seventy characters in total length",
            description="A perfectly valid meta description that provides ample summary information.",
            canonical_url="https://example.com/test",
        )
        issues = validate_metadata(meta_long)
        self.assertTrue(any(i.code == "TITLE_EXCESSIVE_LENGTH" and i.severity == ValidationSeverity.WARNING for i in issues))

    def test_metadata_diagnostics_description(self) -> None:
        # Description missing
        meta_missing = SEOMetadata(
            title="Acceptable Title For Testing Purposes",
            description="",
            canonical_url="https://example.com/test",
        )
        issues = validate_metadata(meta_missing)
        self.assertTrue(any(i.code == "DESCRIPTION_MISSING" and i.severity == ValidationSeverity.CRITICAL for i in issues))

        # Description exceeds schema limit of 300 chars
        meta_oversized = SEOMetadata(
            title="Acceptable Title For Testing Purposes",
            description="A" * 350,
            canonical_url="https://example.com/test",
        )
        issues = validate_metadata(meta_oversized)
        self.assertTrue(any(i.code == "DESCRIPTION_EXCEEDS_SCHEMA_LIMIT" and i.severity == ValidationSeverity.CRITICAL for i in issues))

    def test_html_tag_rendering_security_escaping(self) -> None:
        """Threat Model §5.1: HTML entity escaping protects against Stored XSS."""
        malicious_meta = SEOMetadata(
            title='Malicious <script>alert("title_xss")</script> & Co',
            description='Injected description "><script>alert("desc_xss")</script>',
            canonical_url="https://example.com/article?page=1&sort=asc",
            robots=RobotsDirectives(index=True, follow=True),
        )

        rendered = render_html_meta_tags(malicious_meta)

        # Raw script tags must NEVER appear in the rendered markup
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("</script>", rendered)
        self.assertNotIn('"><script>', rendered)

        # Escaped versions MUST be present
        self.assertIn("&lt;script&gt;alert(&quot;title_xss&quot;)&lt;/script&gt;", rendered)
        self.assertIn("&quot;&gt;&lt;script&gt;alert(&quot;desc_xss&quot;)&lt;/script&gt;", rendered)
        self.assertIn('<link rel="canonical" href="https://example.com/article?page=1&amp;sort=asc">', rendered)

    def test_model_to_metadata_ingestion_cms_content(self) -> None:
        """Ingestion Interface A: Derives SEO metadata from CMS Content objects."""
        # Test published content
        cms_item = Content(
            type_id="article",
            title="Engineering Safe AI Systems",
            body="Artificial intelligence agents require deterministic boundaries, strict governance, and continuous verification across all operational layers.",
            author_id="admin1",
        )
        cms_item.status = "published"

        meta = generate_metadata_from_content(
            content=cms_item,
            base_url="https://example.com",
            slug="safe-ai",
            site_name="SPS2 Engineering",
        )

        self.assertEqual(meta.title, "Engineering Safe AI Systems")
        self.assertEqual(meta.canonical_url, "https://example.com/safe-ai")
        self.assertTrue(meta.robots.index)
        self.assertTrue(meta.robots.follow)
        self.assertIsNotNone(meta.open_graph)
        self.assertEqual(meta.open_graph.site_name, "SPS2 Engineering")
        self.assertIsNotNone(meta.twitter_card)

    def test_model_to_metadata_ingestion_draft_noindex(self) -> None:
        """Threat Model §5.9: Draft content must automatically receive noindex, nofollow."""
        draft_item = Content(
            type_id="page",
            title="Draft Secret Announcement",
            body="This content is unapproved and currently in drafting status.",
            author_id="author2",
        )
        draft_item.status = "draft"

        meta = generate_metadata_from_content(
            content=draft_item,
            base_url="https://example.com",
            slug="announcement",
        )

        self.assertFalse(meta.robots.index)
        self.assertFalse(meta.robots.follow)
        rendered = render_html_meta_tags(meta)
        self.assertIn('<meta name="robots" content="noindex, nofollow">', rendered)


if __name__ == "__main__":
    unittest.main()
