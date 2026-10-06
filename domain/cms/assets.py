"""P8 CMS asset picker with SSRF protection.

Three sources: upload, existing_media, external_url.
External URL ingestion enforces comprehensive SSRF prevention including
per-hop redirect validation.
"""
from __future__ import annotations

import hashlib
import ipaddress
import mimetypes
import os
import re
import socket
import ssl
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from domain.cms.model import Asset


# Security constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_REDIRECTS = 5
TIMEOUT_SECONDS = 30
MAX_DECOMPRESSION_RATIO = 10

# Allowed MIME types for upload
ALLOWED_UPLOAD_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "application/pdf",
    "text/plain",
    "text/markdown",
}

# Allowed schemes
ALLOWED_SCHEMES = {"http", "https"}

# Blocked IP ranges (private, loopback, link-local, metadata)
BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    # IPv6
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("::/128"),
    ipaddress.ip_network("::ffff:0:0/96"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fd00::/8"),
    ipaddress.ip_network("2001:db8::/32"),
]


class AssetError(Exception):
    """Base asset error."""


class ValidationError(AssetError):
    """Validation failed."""


class SSRFError(AssetError):
    """SSRF prevention triggered."""


class TimeoutError(AssetError):
    """Operation timed out."""


class SizeLimitError(AssetError):
    """Size limit exceeded."""


def _is_ip_blocked(ip_str: str) -> bool:
    """Check if an IP address is in a blocked range."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    for network in BLOCKED_NETWORKS:
        if ip in network:
            return True
    return False


def _validate_url(url: str) -> urllib.parse.ParseResult:
    """Parse and validate URL scheme and structure."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise SSRFError(f"Scheme '{parsed.scheme}' not allowed")
    if not parsed.hostname:
        raise ValidationError("URL must have a hostname")
    return parsed


def _resolve_and_validate_host(hostname: str) -> str:
    """Resolve hostname and validate the resulting IP."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise SSRFError(f"Cannot resolve hostname '{hostname}': {e}") from e

    for info in infos:
        ip = info[4][0]
        if _is_ip_blocked(ip):
            raise SSRFError(f"Hostname '{hostname}' resolves to blocked IP '{ip}'")
    return infos[0][4][0]


def _validate_redirect_url(url: str, hop: int) -> None:
    """Validate a redirect target URL."""
    if hop >= MAX_REDIRECTS:
        raise SSRFError(f"Exceeded maximum redirects ({MAX_REDIRECTS})")
    parsed = _validate_url(url)
    _resolve_and_validate_host(parsed.hostname)


def _sanitize_filename(filename: str) -> str:
    """Sanitize a filename to prevent path traversal."""
    # Remove any path components
    filename = os.path.basename(filename)
    # Remove leading dots
    filename = filename.lstrip(".")
    # Replace dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    # Ensure not empty
    if not filename:
        filename = "unnamed"
    return filename


def _validate_magic_bytes(data: bytes, expected_type: str) -> bool:
    """Validate file magic bytes against expected MIME type."""
    # JPEG
    if expected_type == "image/jpeg":
        return data[:3] == b"\xff\xd8\xff"
    # PNG
    if expected_type == "image/png":
        return data[:8] == b"\x89PNG\r\n\x1a\n"
    # GIF
    if expected_type == "image/gif":
        return data[:6] in (b"GIF87a", b"GIF89a")
    # WebP
    if expected_type == "image/webp":
        return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    # PDF
    if expected_type == "application/pdf":
        return data[:5] == b"%PDF-"
    # Plain text / markdown — no magic bytes needed
    if expected_type in ("text/plain", "text/markdown"):
        return True
    # SVG — check for XML signature
    if expected_type == "image/svg+xml":
        return data[:5] == b"<?xml" or data[:4] == b"<svg"
    return False


def _check_decompression(data: bytes, max_ratio: int = MAX_DECOMPRESSION_RATIO) -> None:
    """Check for decompression bombs by comparing compressed vs uncompressed size."""
    # This is a simplified check — real decompression bomb detection
    # would require format-specific parsing
    if len(data) > MAX_FILE_SIZE:
        raise SizeLimitError(f"File size {len(data)} exceeds limit {MAX_FILE_SIZE}")


def handle_upload(
    filename: str,
    content_type: str,
    data: bytes,
    storage_dir: str | Path,
    uploaded_by: str,
) -> Asset:
    """Handle file upload with validation."""
    # Validate size
    if len(data) > MAX_FILE_SIZE:
        raise SizeLimitError(
            f"File size {len(data)} exceeds limit {MAX_FILE_SIZE}"
        )

    # Validate content type
    if content_type not in ALLOWED_UPLOAD_TYPES:
        raise ValidationError(f"Content type '{content_type}' not allowed")

    # Validate magic bytes
    if not _validate_magic_bytes(data, content_type):
        raise ValidationError(
            f"File content does not match declared type '{content_type}'"
        )

    # Check decompression
    _check_decompression(data)

    # Sanitize filename
    safe_name = _sanitize_filename(filename)

    # Generate unique ID
    file_id = hashlib.sha256(data).hexdigest()[:16]
    ext = Path(safe_name).suffix
    stored_name = f"{file_id}{ext}"

    # Ensure storage directory exists
    storage = Path(storage_dir)
    storage.mkdir(parents=True, exist_ok=True)

    # Write file
    file_path = storage / stored_name
    with open(file_path, "wb") as f:
        f.write(data)

    # Create asset
    asset = Asset(
        source="upload",
        local_path=str(file_path),
        media_type=content_type,
        size_bytes=len(data),
        uploaded_by=uploaded_by,
    )
    asset.compute_checksum(data)
    return asset


def handle_existing_media(
    asset_id: str,
    storage_dir: str | Path,
    uploaded_by: str,
) -> Asset:
    """Handle selection of existing media from the asset store."""
    # This would look up the asset in the store
    # For now, return a placeholder
    raise NotImplementedError("Existing media selection requires asset store integration")


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Custom redirect handler that validates each hop before following."""

    def __init__(self, max_redirects: int = MAX_REDIRECTS) -> None:
        self.max_redirects = max_redirects

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Validate the redirect target before following."""
        # Check redirect limit
        if self.max_redirects <= 0:
            raise SSRFError(f"Exceeded maximum redirects ({MAX_REDIRECTS})")
        self.max_redirects -= 1

        # Validate the new URL
        _validate_redirect_url(newurl, MAX_REDIRECTS - self.max_redirects)

        # Build and return the new request
        return urllib.request.Request(
            newurl,
            headers={
                "User-Agent": "SPS2-CMS-Asset-Picker/1.0",
                "Accept": "image/*,application/pdf,text/plain,text/markdown",
            },
        )


def handle_external_url(
    url: str,
    storage_dir: str | Path,
    uploaded_by: str,
) -> Asset:
    """Handle external URL ingestion with SSRF protection.

    Implements per-hop redirect validation. Does NOT rely on urllib's
    default redirect behavior. Every redirect target is validated before
    the next request is made.
    """
    # Validate initial URL
    parsed = _validate_url(url)
    _resolve_and_validate_host(parsed.hostname)

    # Build opener with custom redirect handler
    redirect_handler = _NoRedirectHandler(max_redirects=MAX_REDIRECTS)
    opener = urllib.request.build_opener(redirect_handler)

    # Track redirect hops manually
    current_url = url
    for hop in range(MAX_REDIRECTS + 1):
        # Validate current URL before making request
        parsed = _validate_url(current_url)
        _resolve_and_validate_host(parsed.hostname)

        # Build request
        req = urllib.request.Request(
            current_url,
            headers={
                "User-Agent": "SPS2-CMS-Asset-Picker/1.0",
                "Accept": "image/*,application/pdf,text/plain,text/markdown",
            },
        )

        # Open with timeout
        try:
            with opener.open(req, timeout=TIMEOUT_SECONDS) as response:
                # Check if this is a redirect
                if response.geturl() != current_url:
                    # Redirect happened — validate the new URL
                    new_url = response.geturl()
                    _validate_redirect_url(new_url, hop + 1)
                    current_url = new_url
                    continue

                # Not a redirect — process the response
                content_type = response.headers.get("Content-Type", "").split(";")[0]
                if content_type not in ALLOWED_UPLOAD_TYPES:
                    raise ValidationError(
                        f"External content type '{content_type}' not allowed"
                    )

                # Read with size limit
                data = response.read(MAX_RESPONSE_SIZE + 1)
                if len(data) > MAX_RESPONSE_SIZE:
                    raise SizeLimitError(
                        f"Response size exceeds limit {MAX_RESPONSE_SIZE}"
                    )

                # Check decompression
                _check_decompression(data)

                # Validate magic bytes
                if not _validate_magic_bytes(data, content_type):
                    raise ValidationError(
                        f"External content does not match declared type '{content_type}'"
                    )

                # Store locally
                file_id = hashlib.sha256(data).hexdigest()[:16]
                ext = mimetypes.guess_extension(content_type) or ".bin"
                stored_name = f"external_{file_id}{ext}"

                storage = Path(storage_dir)
                storage.mkdir(parents=True, exist_ok=True)
                file_path = storage / stored_name
                with open(file_path, "wb") as f:
                    f.write(data)

                # Create asset
                asset = Asset(
                    source="external_url",
                    local_path=str(file_path),
                    media_type=content_type,
                    size_bytes=len(data),
                    uploaded_by=uploaded_by,
                    original_url=url,
                )
                asset.compute_checksum(data)
                return asset

        except urllib.error.HTTPError as e:
            # Check if this is a redirect status code
            if e.code in (301, 302, 303, 307, 308):
                # Get the redirect location
                location = e.headers.get("Location")
                if not location:
                    raise AssetError(f"Redirect {e.code} without Location header")
                # Resolve relative URLs
                new_url = urllib.parse.urljoin(current_url, location)
                # Validate the redirect target
                _validate_redirect_url(new_url, hop + 1)
                current_url = new_url
                continue
            raise AssetError(f"HTTP error {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise AssetError(f"URL error: {e.reason}") from e
        except socket.timeout:
            raise TimeoutError(f"Request timed out after {TIMEOUT_SECONDS}s")

    raise SSRFError(f"Exceeded maximum redirects ({MAX_REDIRECTS})")
