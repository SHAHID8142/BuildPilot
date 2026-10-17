"""Unit and security tests for P9 Media & Image SEO Engine.

Covers REQ-P9-05:
- <img> element extraction and attribute parsing
- Missing alt, empty alt, and descriptive alt text evaluation
- Decorative image exemption via aria-hidden="true" or role="presentation"
- Layout stability (explicit width/height or style aspect-ratio) for CLS prevention
- Image filename analysis (descriptive, lowercase, hyphenated, non-hash)
- CMS Asset entity validation integration
- Safe HTML parsing and malicious attribute/injection resilience
- Dangerous schemes (javascript:) and SSRF private IP defenses
- Deterministic analysis diagnostics
"""
from __future__ import annotations

import unittest

from framework.domain.cms.model import Asset
from framework.domain.seo.media import (
    analyze_image_filename,
    analyze_image_tag,
    analyze_media,
    render_image_tag,
    validate_asset_seo,
)


class TestImageExtractionAndAltText(unittest.TestCase):
    """Test image tag parsing and alt attribute quality rules."""

    def test_valid_image_extraction_with_descriptive_alt(self) -> None:
        html = """
        <div>
            <img src="/images/modern-architecture.jpg" alt="Modern sustainable building facade" width="800" height="600" />
        </div>
        """
        res = analyze_media(html)
        self.assertEqual(res.total_images, 1)
        self.assertEqual(res.missing_alt_count, 0)
        self.assertEqual(res.missing_dimensions_count, 0)
        self.assertEqual(len(res.images), 1)

        img = res.images[0]
        self.assertEqual(img.src, "/images/modern-architecture.jpg")
        self.assertEqual(img.alt, "Modern sustainable building facade")
        self.assertEqual(img.width, 800)
        self.assertEqual(img.height, 600)
        self.assertFalse(img.is_decorative)

        # No critical or warning issues for perfect image markup
        serious_issues = [i for i in res.issues if i.severity.value in ("CRITICAL", "WARNING")]
        self.assertEqual(len(serious_issues), 0, f"Unexpected issues: {serious_issues}")

    def test_missing_alt_attribute(self) -> None:
        html = '<img src="/images/banner.jpg" width="400" height="200" />'
        res = analyze_media(html)
        self.assertEqual(res.missing_alt_count, 1)
        issue_codes = [i.code for i in res.issues]
        self.assertIn("IMAGE_ALT_MISSING", issue_codes)

    def test_empty_alt_attribute_non_decorative(self) -> None:
        html = '<img src="/images/banner.jpg" alt="" width="400" height="200" />'
        res = analyze_media(html)
        self.assertEqual(res.missing_alt_count, 1)
        issue_codes = [i.code for i in res.issues]
        self.assertIn("IMAGE_ALT_EMPTY", issue_codes)

    def test_decorative_image_exemption(self) -> None:
        # aria-hidden="true" with empty alt
        html1 = '<img src="/images/divider.svg" alt="" aria-hidden="true" width="100" height="10" />'
        res1 = analyze_media(html1)
        self.assertEqual(res1.decorative_count, 1)
        self.assertEqual(res1.missing_alt_count, 0)
        self.assertNotIn("IMAGE_ALT_MISSING", [i.code for i in res1.issues])
        self.assertNotIn("IMAGE_ALT_EMPTY", [i.code for i in res1.issues])

        # role="presentation" with omitted alt
        html2 = '<img src="/images/divider.svg" role="presentation" width="100" height="10" />'
        res2 = analyze_media(html2)
        self.assertEqual(res2.decorative_count, 1)
        self.assertEqual(res2.missing_alt_count, 0)
        self.assertNotIn("IMAGE_ALT_MISSING", [i.code for i in res2.issues])

    def test_decorative_image_with_non_empty_alt_advisory(self) -> None:
        html = '<img src="/images/divider.svg" alt="A decorative line" aria-hidden="true" width="100" height="10" />'
        res = analyze_media(html)
        self.assertEqual(res.decorative_count, 1)
        issue_codes = [i.code for i in res.issues]
        self.assertIn("IMAGE_DECORATIVE_HAS_ALT", issue_codes)

    def test_generic_and_filename_alt_text_diagnostics(self) -> None:
        # Generic alt
        html1 = '<img src="/images/product.jpg" alt="photo" width="200" height="200" />'
        res1 = analyze_media(html1)
        self.assertIn("IMAGE_ALT_GENERIC", [i.code for i in res1.issues])

        # Filename as alt
        html2 = '<img src="/images/product.jpg" alt="product.jpg" width="200" height="200" />'
        res2 = analyze_media(html2)
        self.assertIn("IMAGE_ALT_FILENAME", [i.code for i in res2.issues])

        # Overly long alt
        long_alt = "x" * 160
        html3 = f'<img src="/images/product.jpg" alt="{long_alt}" width="200" height="200" />'
        res3 = analyze_media(html3)
        self.assertIn("IMAGE_ALT_TOO_LONG", [i.code for i in res3.issues])


class TestLayoutStabilityAndCLS(unittest.TestCase):
    """Test explicit dimensions and aspect-ratio rules for CLS layout stability."""

    def test_missing_layout_dimensions(self) -> None:
        html = '<img src="/images/hero.jpg" alt="Hero banner" />'
        res = analyze_media(html)
        self.assertEqual(res.missing_dimensions_count, 1)
        self.assertIn("IMAGE_DIMENSIONS_MISSING", [i.code for i in res.issues])

    def test_explicit_attributes_satisfy_layout_dimensions(self) -> None:
        html = '<img src="/images/hero.jpg" alt="Hero banner" width="1200" height="630" />'
        res = analyze_media(html)
        self.assertEqual(res.missing_dimensions_count, 0)
        self.assertNotIn("IMAGE_DIMENSIONS_MISSING", [i.code for i in res.issues])

    def test_aspect_ratio_style_satisfies_layout_dimensions(self) -> None:
        html = '<img src="/images/hero.jpg" alt="Hero banner" style="aspect-ratio: 16 / 9; width: 100%;" />'
        res = analyze_media(html)
        self.assertEqual(res.missing_dimensions_count, 0)
        self.assertTrue(res.images[0].has_aspect_ratio)
        self.assertNotIn("IMAGE_DIMENSIONS_MISSING", [i.code for i in res.issues])

    def test_style_dimensions_satisfy_layout_stability(self) -> None:
        html = '<img src="/images/hero.jpg" alt="Hero banner" style="width: 800px; height: 600px;" />'
        res = analyze_media(html)
        self.assertEqual(res.missing_dimensions_count, 0)
        self.assertNotIn("IMAGE_DIMENSIONS_MISSING", [i.code for i in res.issues])


class TestImageFilenameAnalysis(unittest.TestCase):
    """Test filename best practices, unreadable hash detection, and casing rules."""

    def test_descriptive_lowercase_hyphenated_filename(self) -> None:
        issues = analyze_image_filename("/assets/images/clean-energy-solutions.jpg")
        self.assertEqual(len(issues), 0)

    def test_unreadable_hash_like_filenames_detected(self) -> None:
        # MD5 hex hash
        issues1 = analyze_image_filename("e4d909c290d0fb1ca068ffaddf22cbd0.jpg")
        self.assertTrue(any(i.code == "IMAGE_FILENAME_HASH_LIKE" for i in issues1))

        # SHA-256 hex hash
        issues2 = analyze_image_filename("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad.png")
        self.assertTrue(any(i.code == "IMAGE_FILENAME_HASH_LIKE" for i in issues2))

        # UUID
        issues3 = analyze_image_filename("123e4567-e89b-12d3-a456-426614174000.webp")
        self.assertTrue(any(i.code == "IMAGE_FILENAME_HASH_LIKE" for i in issues3))

        # Camera raw ID
        issues4 = analyze_image_filename("IMG_4092.JPG")
        self.assertTrue(any(i.code == "IMAGE_FILENAME_HASH_LIKE" for i in issues4))

    def test_uppercase_spaces_and_underscores_diagnostics(self) -> None:
        # Uppercase
        issues1 = analyze_image_filename("Hero-Banner.jpg")
        self.assertTrue(any(i.code == "IMAGE_FILENAME_UPPERCASE" for i in issues1))

        # Spaces
        issues2 = analyze_image_filename("hero banner final.jpg")
        self.assertTrue(any(i.code == "IMAGE_FILENAME_SPACES" for i in issues2))

        # Underscores
        issues3 = analyze_image_filename("hero_banner_final.jpg")
        self.assertTrue(any(i.code == "IMAGE_FILENAME_UNDERSCORES" for i in issues3))

        # Too short / generic
        issues4 = analyze_image_filename("a.jpg")
        self.assertTrue(any(i.code == "IMAGE_FILENAME_NOT_DESCRIPTIVE" for i in issues4))


class TestSecurityAndMalformedHTML(unittest.TestCase):
    """Test protocol defenses, SSRF private IP blocking, and malformed markup."""

    def test_unsafe_schemes_rejected(self) -> None:
        html = '<img src="javascript:alert(1)" alt="Exploit" width="100" height="100" />'
        res = analyze_media(html)
        self.assertIn("IMAGE_UNSAFE_SCHEME", [i.code for i in res.issues])

    def test_ssrf_private_and_loopback_ip_rejected(self) -> None:
        html1 = '<img src="http://127.0.0.1:8080/secret.png" alt="Local" width="100" height="100" />'
        res1 = analyze_media(html1)
        self.assertIn("IMAGE_PRIVATE_IP_REJECTED", [i.code for i in res1.issues])

        html2 = '<img src="http://169.254.169.254/meta.png" alt="AWS Meta" width="100" height="100" />'
        res2 = analyze_media(html2)
        self.assertIn("IMAGE_PRIVATE_IP_REJECTED", [i.code for i in res2.issues])

    def test_malformed_html_attribute_resilience(self) -> None:
        # Tag with quotes and injection payload in attributes
        html = """
        <img src="test\" onerror=\"alert('xss')\"" alt="test\" onload=\"alert(1)\"" width="100" height="100">
        <p>Follow-up content</p>
        """
        res = analyze_media(html)
        self.assertEqual(res.total_images, 1)
        # Verify parser completes cleanly without unhandled exception


class TestCMSAssetIntegration(unittest.TestCase):
    """Test validation of CMS Asset models for media SEO requirements."""

    def test_valid_asset_seo_validation(self) -> None:
        asset = Asset(
            source="upload",
            local_path="public/media/sustainable-architecture.jpg",
            media_type="image/jpeg",
            size_bytes=204800,
            uploaded_by="user_admin",
        )
        issues = validate_asset_seo(
            asset=asset,
            alt_text="Sustainable solar building facade",
            width=1200,
            height=800,
        )
        self.assertEqual(len(issues), 0, f"Unexpected issues: {issues}")

    def test_asset_missing_alt_or_dimensions_flagged(self) -> None:
        asset = Asset(
            source="upload",
            local_path="public/media/building.jpg",
            media_type="image/jpeg",
            size_bytes=204800,
            uploaded_by="user_admin",
        )
        # Missing alt
        issues1 = validate_asset_seo(asset=asset, alt_text=None, width=800, height=600)
        self.assertTrue(any(i.code == "IMAGE_ALT_MISSING" for i in issues1))

        # Missing dimensions
        issues2 = validate_asset_seo(asset=asset, alt_text="Description", width=None, height=None)
        self.assertTrue(any(i.code == "IMAGE_DIMENSIONS_MISSING" for i in issues2))

    def test_non_image_asset_skipped(self) -> None:
        asset = Asset(
            source="upload",
            local_path="public/docs/annual-report.pdf",
            media_type="application/pdf",
            size_bytes=1048576,
            uploaded_by="user_admin",
        )
        issues = validate_asset_seo(asset=asset)
        self.assertEqual(len(issues), 0)


class TestRenderImageTagHelper(unittest.TestCase):
    """Test safe image tag rendering with proper HTML entity escaping."""

    def test_render_image_tag_escaping(self) -> None:
        tag = render_image_tag(
            src="/images/logo.png?v=1&q=2",
            alt='Tom & Jerry "Cartoon"',
            width=400,
            height=300,
            classes="brand-logo responsive",
        )
        self.assertIn('src="/images/logo.png?v=1&amp;q=2"', tag)
        self.assertIn('alt="Tom &amp; Jerry &quot;Cartoon&quot;"', tag)
        self.assertIn('width="400"', tag)
        self.assertIn('height="300"', tag)
        self.assertIn('class="brand-logo responsive"', tag)
        self.assertNotIn("<script", tag)


if __name__ == "__main__":
    unittest.main()
