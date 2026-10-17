"""P8 CMS stored XSS / output safety regression tests.

Tests for plain-text content safety. Content.body is PLAIN TEXT ONLY.
These tests verify that attacker-controlled body content cannot become
executable HTML/script through the P8 API/service boundary.
"""
from __future__ import annotations

import tempfile
import unittest

from framework.domain.cms.output_safety import (
    encode_for_html,
    validate_plain_text,
    get_content_with_safe_output,
)
from framework.domain.cms.api import CMSAPI


class TestPlainTextContentSafety(unittest.TestCase):
    """Test plain-text content safety."""

    def test_script_payload_encoded(self) -> None:
        """<script> payload is encoded."""
        payload = "<script>alert('xss')</script>"
        encoded = encode_for_html(payload)
        self.assertNotIn("<script>", encoded)
        self.assertIn("&lt;script&gt;", encoded)

    def test_event_handler_attributes_encoded(self) -> None:
        """Event-handler attributes are encoded."""
        payload = '<img src="x" onerror="alert(1)">'
        encoded = encode_for_html(payload)
        self.assertNotIn("<img", encoded)
        self.assertIn("&lt;img", encoded)

    def test_javascript_url_encoded(self) -> None:
        """javascript: URLs are neutralized by HTML encoding."""
        payload = '<a href="javascript:alert(1)">click</a>'
        encoded = encode_for_html(payload)
        # The HTML tags are encoded, preventing interpretation as markup
        self.assertNotIn("<a ", encoded)
        self.assertNotIn("<a>", encoded)
        self.assertIn("&lt;a ", encoded)
        # The javascript: string remains as text but is not executable
        # because it's inside an HTML-encoded attribute value
        self.assertIn("javascript:alert(1)", encoded)

    def test_dangerous_html_encoded(self) -> None:
        """Dangerous HTML is encoded."""
        payload = '<div onmouseover="alert(1)">hover</div>'
        encoded = encode_for_html(payload)
        self.assertNotIn("<div", encoded)
        self.assertIn("&lt;div", encoded)

    def test_encoded_obfuscated_payload(self) -> None:
        """Encoded/obfuscated payloads are encoded."""
        # HTML entity encoded script
        payload = "&lt;script&gt;alert(1)&lt;/script&gt;"
        encoded = encode_for_html(payload)
        # Should be double-encoded
        self.assertNotIn("<script>", encoded)

    def test_benign_text_unchanged(self) -> None:
        """Benign ordinary text remains valid."""
        text = "Hello, this is a normal blog post about technology."
        result = validate_plain_text(text)
        self.assertEqual(result, text)

    def test_multiline_text_valid(self) -> None:
        """Multiline text is valid."""
        text = "Line 1\nLine 2\nLine 3"
        result = validate_plain_text(text)
        self.assertEqual(result, text)

    def test_special_characters_valid(self) -> None:
        """Characters such as <, >, &, quotes are valid plain text."""
        text = '5 < 10 & 3 > 1 "quoted" \'single\''
        result = validate_plain_text(text)
        self.assertEqual(result, text)

    def test_special_characters_encoded_for_output(self) -> None:
        """Special characters are encoded for HTML output."""
        text = '5 < 10 & 3 > 1 "quoted"'
        encoded = encode_for_html(text)
        self.assertIn("&lt;", encoded)
        self.assertIn("&gt;", encoded)
        self.assertIn("&amp;", encoded)
        self.assertIn("&quot;", encoded)

    def test_content_with_safe_output(self) -> None:
        """get_content_with_safe_output encodes body for safe output."""
        content = {
            "id": "c1",
            "title": "Test",
            "body": "<script>alert(1)</script>",
            "status": "draft",
        }
        safe = get_content_with_safe_output(content)
        self.assertNotIn("<script>", safe["body"])
        self.assertIn("&lt;script&gt;", safe["body"])

    def test_non_string_body_rejected(self) -> None:
        """Non-string body is rejected."""
        with self.assertRaises(ValueError):
            validate_plain_text(123)

    def test_empty_string_valid(self) -> None:
        """Empty string is valid plain text."""
        result = validate_plain_text("")
        self.assertEqual(result, "")

    def test_unicode_text_valid(self) -> None:
        """Unicode text is valid plain text."""
        text = "Hello 世界 مرحبا"
        result = validate_plain_text(text)
        self.assertEqual(result, text)


class TestAPIContentSafety(unittest.TestCase):
    """Test that the API enforces plain-text content safety."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.api = CMSAPI(data_dir=self.tmpdir)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_content_stored_as_plain_text(self) -> None:
        """Content is stored as plain text (not interpreted as HTML)."""
        ct = self.api.create_content_type(
            "super_admin", "Blog Post", [{"name": "title", "type": "string", "required": True}]
        )
        # Store content with HTML-like content
        content = self.api.create_content(
            "admin", ct["id"], "Test", "<script>alert(1)</script>", "user1"
        )
        # Content should be stored as-is (plain text)
        self.assertEqual(content["body"], "<script>alert(1)</script>")

    def test_content_retrieval_returns_plain_text(self) -> None:
        """Content retrieval returns plain text."""
        ct = self.api.create_content_type(
            "super_admin", "Blog Post", [{"name": "title", "type": "string", "required": True}]
        )
        content = self.api.create_content(
            "admin", ct["id"], "Test", "Normal text content", "user1"
        )
        retrieved = self.api.get_content(content["id"])
        self.assertEqual(retrieved["body"], "Normal text content")

    def test_raw_api_vs_safe_output_boundary(self) -> None:
        """Verify the distinction between raw API and safe output.

        get_content() is a plain-text data API — it returns raw body.
        get_content_with_safe_output() is the HTML-safe output API —
        it returns HTML-encoded body.

        Consumers targeting HTML must use get_content_with_safe_output()
        or encode_for_html() to prevent stored XSS.
        """
        ct = self.api.create_content_type(
            "super_admin", "Blog Post", [{"name": "title", "type": "string", "required": True}]
        )
        # Store content with HTML-like payload
        payload = "<script>alert('xss')</script>"
        content = self.api.create_content(
            "admin", ct["id"], "Test", payload, "user1"
        )

        # Raw API returns plain text (not encoded)
        raw = self.api.get_content(content["id"])
        self.assertEqual(raw["body"], payload)

        # Safe output API returns HTML-encoded text
        safe = get_content_with_safe_output(raw)
        self.assertNotEqual(safe["body"], payload)
        self.assertNotIn("<script>", safe["body"])
        self.assertIn("&lt;script&gt;", safe["body"])

        # Verify the raw API is NOT safe for direct HTML injection
        # (This is why get_content_with_safe_output exists)
        self.assertIn("<script>", raw["body"])  # Raw is dangerous for HTML
        self.assertNotIn("<script>", safe["body"])  # Safe is not


if __name__ == "__main__":
    unittest.main()
