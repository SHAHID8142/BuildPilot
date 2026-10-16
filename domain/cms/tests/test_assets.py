"""P8 CMS asset picker tests.

Tests for asset handling including SSRF prevention.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from domain.cms.assets import (
    AssetError,
    SSRFError,
    SizeLimitError,
    ValidationError,
    handle_upload,
    MAX_FILE_SIZE,
)


class TestAssetUpload(unittest.TestCase):
    """Test asset upload handling."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_upload_success(self) -> None:
        """Valid upload succeeds."""
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        asset = handle_upload("test.png", "image/png", data, self.tmpdir, "user1")
        self.assertEqual(asset.source, "upload")
        self.assertEqual(asset.media_type, "image/png")
        self.assertEqual(asset.size_bytes, len(data))

    def test_invalid_upload_rejected(self) -> None:
        """Invalid upload is rejected."""
        data = b"not an image"
        with self.assertRaises(ValidationError):
            handle_upload("test.png", "image/png", data, self.tmpdir, "user1")

    def test_traversal_rejected(self) -> None:
        """Path traversal in filename is rejected."""
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        asset = handle_upload(
            "../../../etc/passwd.png", "image/png", data, self.tmpdir, "user1"
        )
        # Should be sanitized
        self.assertNotIn("..", asset.local_path)

    def test_oversized_upload_rejected(self) -> None:
        """Oversized upload is rejected."""
        data = b"\x00" * (MAX_FILE_SIZE + 1)
        with self.assertRaises(SizeLimitError):
            handle_upload("large.png", "image/png", data, self.tmpdir, "user1")

    def test_disallowed_type_rejected(self) -> None:
        """Disallowed content type is rejected."""
        data = b"\x00" * 100
        with self.assertRaises(ValidationError):
            handle_upload("test.exe", "application/x-msdownload", data, self.tmpdir, "user1")


class TestSSRFPrevention(unittest.TestCase):
    """Test SSRF prevention in external URL handling."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_private_ip_rejected(self) -> None:
        """Private IP addresses are rejected."""
        from domain.cms.assets import _is_ip_blocked
        self.assertTrue(_is_ip_blocked("10.0.0.1"))
        self.assertTrue(_is_ip_blocked("192.168.1.1"))
        self.assertTrue(_is_ip_blocked("172.16.0.1"))

    def test_localhost_rejected(self) -> None:
        """Localhost is rejected."""
        from domain.cms.assets import _is_ip_blocked
        self.assertTrue(_is_ip_blocked("127.0.0.1"))
        self.assertTrue(_is_ip_blocked("127.0.0.2"))

    def test_ipv6_loopback_rejected(self) -> None:
        """IPv6 loopback is rejected."""
        from domain.cms.assets import _is_ip_blocked
        self.assertTrue(_is_ip_blocked("::1"))

    def test_ipv6_private_rejected(self) -> None:
        """IPv6 private addresses are rejected."""
        from domain.cms.assets import _is_ip_blocked
        self.assertTrue(_is_ip_blocked("fc00::1"))
        self.assertTrue(_is_ip_blocked("fd00::1"))

    def test_link_local_rejected(self) -> None:
        """Link-local addresses are rejected."""
        from domain.cms.assets import _is_ip_blocked
        self.assertTrue(_is_ip_blocked("169.254.1.1"))
        self.assertTrue(_is_ip_blocked("fe80::1"))

    def test_metadata_service_rejected(self) -> None:
        """Cloud metadata service addresses are rejected."""
        from domain.cms.assets import _is_ip_blocked
        self.assertTrue(_is_ip_blocked("169.254.169.254"))

    def test_invalid_scheme_rejected(self) -> None:
        """Invalid URL schemes are rejected."""
        from domain.cms.assets import _validate_url
        with self.assertRaises(SSRFError):
            _validate_url("file:///etc/passwd")
        with self.assertRaises(SSRFError):
            _validate_url("ftp://example.com/file")
        with self.assertRaises(SSRFError):
            _validate_url("gopher://example.com")

    def test_valid_scheme_accepted(self) -> None:
        """Valid URL schemes are accepted."""
        from domain.cms.assets import _validate_url
        parsed = _validate_url("https://example.com/image.png")
        self.assertEqual(parsed.scheme, "https")
        parsed = _validate_url("http://example.com/image.png")
        self.assertEqual(parsed.scheme, "http")


if __name__ == "__main__":
    unittest.main()
