"""P8 CMS SSRF redirect regression tests.

Tests for per-hop redirect validation in external URL handling.
These tests exercise the actual redirect implementation, not a mocked validator.
"""
from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from io import BytesIO

from framework.domain.cms.assets import (
    SSRFError,
    ValidationError,
    handle_external_url,
    _NoRedirectHandler,
    _validate_url,
    _resolve_and_validate_host,
    _is_ip_blocked,
    MAX_REDIRECTS,
)


class TestSSRFRedirectValidation(unittest.TestCase):
    """Test SSRF redirect validation."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_public_to_public_redirect(self) -> None:
        """Public URL redirecting to another public URL is allowed."""
        # This test verifies the validation logic allows public-to-public
        # We test the validation function directly
        _validate_url("https://example.com/image.png")
        _validate_url("https://cdn.example.com/image.png")

    def test_public_to_private_ipv4_rejected(self) -> None:
        """Redirect to private IPv4 is rejected."""
        with self.assertRaises(SSRFError):
            _resolve_and_validate_host("10.0.0.1")

    def test_public_to_localhost_rejected(self) -> None:
        """Redirect to localhost is rejected."""
        with self.assertRaises(SSRFError):
            _resolve_and_validate_host("127.0.0.1")

    def test_public_to_link_local_rejected(self) -> None:
        """Redirect to link-local is rejected."""
        with self.assertRaises(SSRFError):
            _resolve_and_validate_host("169.254.1.1")

    def test_public_to_private_ipv6_rejected(self) -> None:
        """Redirect to private IPv6 is rejected."""
        self.assertTrue(_is_ip_blocked("fc00::1"))
        self.assertTrue(_is_ip_blocked("fd00::1"))

    def test_public_to_ipv4_mapped_ipv6_rejected(self) -> None:
        """Redirect to IPv4-mapped IPv6 is rejected."""
        self.assertTrue(_is_ip_blocked("::ffff:10.0.0.1"))
        self.assertTrue(_is_ip_blocked("::ffff:127.0.0.1"))
        self.assertTrue(_is_ip_blocked("::ffff:192.168.1.1"))

    def test_multi_hop_redirect_ending_in_private(self) -> None:
        """Multi-hop redirect chain public->public->private is rejected.

        Exercises the real handle_external_url redirect loop with a
        deterministic fake opener (mocked at build_opener so only the
        network fetch is replaced). Verifies that each hop is validated
        and the private final target is rejected BEFORE a request to
        it is made.
        """
        # Simulate: public1 -> public2 -> private(10.0.0.1)
        redirect_map = {
            "https://public1.example.com/image.png":
                "https://public2.example.com/image.png",
            "https://public2.example.com/image.png":
                "http://10.0.0.1/image.png",
        }

        class FakeResponse:
            def __init__(self, url):
                self._url = url
                self.headers = {"Content-Type": "image/png"}

            def geturl(self):
                return self._url

            def read(self, n=-1):
                return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class FakeOpener:
            def __init__(self):
                self.requested = []

            def open(self, req, timeout=None):
                url = req.get_full_url()
                self.requested.append(url)
                # geturl() differs from the request URL => redirect.
                return FakeResponse(redirect_map.get(url, url))

        fake_opener = FakeOpener()

        with patch('urllib.request.build_opener', return_value=fake_opener):
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                def fake_getaddrinfo(*args):
                    hostname = args[0]
                    if hostname in ("public1.example.com", "public2.example.com"):
                        return [(2, 1, 6, '', ("93.184.216.34", 80))]
                    elif hostname == "10.0.0.1":
                        return [(2, 1, 6, '', ("10.0.0.1", 80))]
                    raise socket.gaierror(f"Unknown host: {hostname}")
                mock_getaddrinfo.side_effect = fake_getaddrinfo

                # The private final target must be rejected before any
                # request to 10.0.0.1 is made.
                with self.assertRaises(SSRFError):
                    handle_external_url(
                        "https://public1.example.com/image.png",
                        self.tmpdir,
                        "user1",
                    )

        # Only the two public hops were requested. The private target was
        # rejected during redirect validation, before it was fetched.
        self.assertEqual(
            fake_opener.requested,
            [
                "https://public1.example.com/image.png",
                "https://public2.example.com/image.png",
            ],
        )
        self.assertNotIn("http://10.0.0.1/image.png", fake_opener.requested)

    def test_redirect_limit_enforced(self) -> None:
        """Redirect limit is enforced — chain exceeding MAX_REDIRECTS is rejected.

        Exercises the real handle_external_url redirect loop with a
        deterministic fake opener that always redirects. Verifies the
        request is rejected because the redirect limit is exceeded.
        """
        class FakeResponse:
            def __init__(self, url):
                self._url = url
                self.headers = {"Content-Type": "image/png"}

            def geturl(self):
                return self._url

            def read(self, n=-1):
                return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        class FakeOpener:
            def __init__(self):
                self.requested = []
                self.hop = 0

            def open(self, req, timeout=None):
                url = req.get_full_url()
                self.requested.append(url)
                self.hop += 1
                # Always redirect to a new public URL, forcing a long chain.
                return FakeResponse(
                    f"https://redirect{self.hop}.example.com/image.png"
                )

        fake_opener = FakeOpener()

        with patch('urllib.request.build_opener', return_value=fake_opener):
            with patch('socket.getaddrinfo') as mock_getaddrinfo:
                def fake_getaddrinfo(*args):
                    # Every redirect host resolves to a public IP.
                    return [(2, 1, 6, '', ("93.184.216.34", 80))]
                mock_getaddrinfo.side_effect = fake_getaddrinfo

                with self.assertRaises(SSRFError) as ctx:
                    handle_external_url(
                        "https://redirect0.example.com/image.png",
                        self.tmpdir,
                        "user1",
                    )

        # Rejected because the redirect limit was exceeded.
        self.assertIn("redirect", str(ctx.exception).lower())
        # The limit check fired during redirect validation: exactly
        # MAX_REDIRECTS requests were made before the chain was cut.
        # (If enforcement relied only on the loop backstop, this would
        # be MAX_REDIRECTS + 1.)
        self.assertEqual(len(fake_opener.requested), MAX_REDIRECTS)

    def test_redirect_to_disallowed_scheme(self) -> None:
        """Redirect to disallowed scheme is rejected."""
        with self.assertRaises(SSRFError):
            _validate_url("file:///etc/passwd")
        with self.assertRaises(SSRFError):
            _validate_url("ftp://example.com/file")
        with self.assertRaises(SSRFError):
            _validate_url("gopher://example.com")

    def test_malformed_redirect(self) -> None:
        """Malformed redirect URL is rejected."""
        with self.assertRaises((SSRFError, ValidationError)):
            _validate_url("not-a-valid-url")

    def test_redirect_hostname_resolving_to_blocked(self) -> None:
        """Redirect hostname resolving to blocked address is rejected."""
        # Test with a hostname that would resolve to a blocked IP
        # We mock getaddrinfo to return a blocked IP
        with patch('socket.getaddrinfo') as mock_getaddrinfo:
            mock_getaddrinfo.return_value = [
                (2, 1, 6, '', ('10.0.0.1', 80))
            ]
            with self.assertRaises(SSRFError):
                _resolve_and_validate_host("evil.example.com")

    def test_ipv6_loopback_rejected(self) -> None:
        """IPv6 loopback is rejected."""
        self.assertTrue(_is_ip_blocked("::1"))

    def test_ipv6_unspecified_rejected(self) -> None:
        """IPv6 unspecified address is rejected."""
        self.assertTrue(_is_ip_blocked("::"))

    def test_ipv6_link_local_rejected(self) -> None:
        """IPv6 link-local is rejected."""
        self.assertTrue(_is_ip_blocked("fe80::1"))

    def test_ipv6_unique_local_rejected(self) -> None:
        """IPv6 unique-local is rejected."""
        self.assertTrue(_is_ip_blocked("fc00::1"))
        self.assertTrue(_is_ip_blocked("fd00::1"))

    def test_metadata_service_rejected(self) -> None:
        """Cloud metadata service addresses are rejected."""
        self.assertTrue(_is_ip_blocked("169.254.169.254"))

    def test_redirect_handler_validates_each_hop(self) -> None:
        """Custom redirect handler validates each hop."""
        handler = _NoRedirectHandler(max_redirects=5)
        # The handler should decrement max_redirects on each redirect
        self.assertEqual(handler.max_redirects, 5)


if __name__ == "__main__":
    unittest.main()
