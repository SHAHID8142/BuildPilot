"""P9 Media & Image SEO Engine.

Implements REQ-P9-05:
- Analyzes <img> elements in rendered HTML using Python stdlib HTMLParser (UQ-P9-04).
- Validates alt attribute presence and quality (meaningful vs empty/generic).
- Supports decorative-image exemption using aria-hidden="true" or role="presentation".
- Evaluates layout stability (width/height attributes or aspect-ratio style) for CLS prevention.
- Validates image filenames (descriptive, lowercase, hyphen-separated, non-hash).
- Integrates with P8 CMS Asset model without mutating stored records.
- Preserves CONF-001 boundary: zero invented numeric LCP or INP thresholds.
"""
from __future__ import annotations

import html
import re
import urllib.parse
from html.parser import HTMLParser
from typing import Any

from domain.seo.metadata import _is_private_or_loopback_host
from domain.seo.model import (
    ImageItem,
    MediaAnalysisResult,
    ValidationIssue,
    ValidationSeverity,
)

# Generic alt text phrases that provide low semantic/SEO value
GENERIC_ALT_PATTERNS = {
    "image",
    "img",
    "photo",
    "picture",
    "graphic",
    "icon",
    "banner",
    "logo",
    "untitled",
    "placeholder",
    "thumbnail",
    "pic",
    "screenshot",
    "drawing",
    "illustration",
}

# Standard web image extensions
COMMON_IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
    "svg",
    "avif",
    "bmp",
    "ico",
    "tiff",
}

# Unsafe schemes to reject immediately
UNSAFE_IMAGE_SCHEMES = {"javascript", "vbscript"}


def _extract_filename_and_stem(src: str) -> tuple[str, str, str]:
    """Extract clean filename, stem (basename without extension), and extension from a path/URL."""
    if not src:
        return "", "", ""
    # Strip query and fragment
    clean_src = src.split("?")[0].split("#")[0]
    filename = clean_src.rsplit("/", 1)[-1].strip()
    if "." in filename:
        stem, ext = filename.rsplit(".", 1)
        return filename, stem, ext.lower()
    return filename, filename, ""


def analyze_image_filename(src: str) -> list[ValidationIssue]:
    """Analyze image filename for SEO best practices (descriptive, lowercase, hyphenated)."""
    issues: list[ValidationIssue] = []
    filename, stem, ext = _extract_filename_and_stem(src)

    if not filename:
        return issues

    # Skip inline data URIs from filename check
    if src.lower().startswith("data:image/"):
        return issues

    # 1. Detect unreadable hash-like filenames or camera defaults
    # MD5 (32 hex), SHA-1 (40 hex), SHA-256 (64 hex)
    is_hex_hash = bool(re.match(r"^[0-9a-fA-F]{32,64}$", stem))
    # UUID pattern
    is_uuid = bool(
        re.match(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            stem,
        )
    )
    # Generic camera / timestamp patterns (e.g. IMG_0001, DSC_1234, 1728243600)
    is_camera_or_numeric = bool(
        re.match(r"^(?:IMG|DSC|PEXELS|SHUTTERSTOCK)[-_]?\d+$", stem, re.IGNORECASE)
        or re.match(r"^\d{10,}$", stem)
    )

    if is_hex_hash or is_uuid or is_camera_or_numeric:
        issues.append(
            ValidationIssue(
                code="IMAGE_FILENAME_HASH_LIKE",
                message=(
                    f"Image filename '{filename}' appears to be a raw hash or camera ID; "
                    "descriptive filenames are recommended for SEO"
                ),
                severity=ValidationSeverity.WARNING,
                field=src,
            )
        )

    # 2. Uppercase characters in filename
    if any(c.isupper() for c in filename):
        issues.append(
            ValidationIssue(
                code="IMAGE_FILENAME_UPPERCASE",
                message=f"Image filename '{filename}' contains uppercase characters; prefer all-lowercase",
                severity=ValidationSeverity.INFO,
                field=src,
            )
        )

    # 3. Spaces in filename
    if " " in filename or "%20" in filename.lower():
        issues.append(
            ValidationIssue(
                code="IMAGE_FILENAME_SPACES",
                message=f"Image filename '{filename}' contains spaces; prefer hyphen-delimited words",
                severity=ValidationSeverity.WARNING,
                field=src,
            )
        )

    # 4. Underscores in filename
    if "_" in stem and not is_hex_hash and not is_uuid:
        issues.append(
            ValidationIssue(
                code="IMAGE_FILENAME_UNDERSCORES",
                message=f"Image filename '{filename}' uses underscores; search engines recommend hyphens",
                severity=ValidationSeverity.INFO,
                field=src,
            )
        )

    # 5. Non-descriptive short names
    if len(stem) < 3 or stem.lower() in ("image", "img", "photo", "pic", "icon", "banner", "logo", "test"):
        issues.append(
            ValidationIssue(
                code="IMAGE_FILENAME_NOT_DESCRIPTIVE",
                message=f"Image filename '{filename}' is too short or generic to provide search relevance",
                severity=ValidationSeverity.WARNING,
                field=src,
            )
        )

    return issues


class MediaHTMLParser(HTMLParser):
    """Linear streaming parser extracting <img> elements and attributes."""

    def __init__(self) -> None:
        super().__init__()
        self.raw_images: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "img":
            attr_dict: dict[str, str] = {}
            for k, v in attrs:
                attr_dict[k.lower()] = v if v is not None else ""
            self.raw_images.append(attr_dict)


def analyze_image_tag(attrs: dict[str, str], base_url: str = "") -> tuple[ImageItem, list[ValidationIssue]]:
    """Analyze a single <img> element's attributes for SEO, layout stability, and security."""
    issues: list[ValidationIssue] = []

    src = attrs.get("src", "").strip()
    alt_raw = attrs.get("alt")  # Note: None if omitted, "" if alt=""
    width_str = attrs.get("width", "").strip()
    height_str = attrs.get("height", "").strip()
    style = attrs.get("style", "").strip()
    aria_hidden = attrs.get("aria-hidden", "").strip().lower()
    role = attrs.get("role", "").strip().lower()
    img_id = attrs.get("id")

    # 1. Security & Scheme checks on src
    if not src:
        issues.append(
            ValidationIssue(
                code="IMAGE_SRC_EMPTY",
                message="<img> tag has empty or missing 'src' attribute",
                severity=ValidationSeverity.CRITICAL,
                field="src",
            )
        )
    else:
        parsed = urllib.parse.urlparse(src)
        scheme = parsed.scheme.lower()
        if scheme in UNSAFE_IMAGE_SCHEMES:
            issues.append(
                ValidationIssue(
                    code="IMAGE_UNSAFE_SCHEME",
                    message=f"<img> src uses dangerous scheme '{scheme}:'",
                    severity=ValidationSeverity.CRITICAL,
                    field="src",
                )
            )
        elif scheme in ("http", "https") and _is_private_or_loopback_host(parsed.hostname or ""):
            issues.append(
                ValidationIssue(
                    code="IMAGE_PRIVATE_IP_REJECTED",
                    message=f"<img> src points to private or loopback host '{parsed.hostname}'",
                    severity=ValidationSeverity.CRITICAL,
                    field="src",
                )
            )

    # 2. Decorative check
    is_decorative = (aria_hidden == "true") or (role in ("presentation", "none"))

    # 3. Alt attribute analysis
    if is_decorative:
        # Decorative images are exempt from required alt text
        if alt_raw is not None and alt_raw.strip():
            issues.append(
                ValidationIssue(
                    code="IMAGE_DECORATIVE_HAS_ALT",
                    message=(
                        f"Image with src='{src}' is marked decorative (aria-hidden/role) "
                        "but has non-empty alt text; assistive technology will ignore it"
                    ),
                    severity=ValidationSeverity.INFO,
                    field="alt",
                )
            )
    else:
        # Non-decorative images MUST have meaningful alt text
        if alt_raw is None:
            issues.append(
                ValidationIssue(
                    code="IMAGE_ALT_MISSING",
                    message=f"Image with src='{src}' is missing required 'alt' attribute",
                    severity=ValidationSeverity.CRITICAL,
                    field="alt",
                )
            )
        elif not alt_raw.strip():
            issues.append(
                ValidationIssue(
                    code="IMAGE_ALT_EMPTY",
                    message=f"Image with src='{src}' has empty alt attribute and is not marked decorative",
                    severity=ValidationSeverity.WARNING,
                    field="alt",
                )
            )
        else:
            clean_alt = alt_raw.strip().lower()
            if clean_alt in GENERIC_ALT_PATTERNS:
                issues.append(
                    ValidationIssue(
                        code="IMAGE_ALT_GENERIC",
                        message=f"Image with src='{src}' uses generic alt text '{alt_raw.strip()}'",
                        severity=ValidationSeverity.WARNING,
                        field="alt",
                    )
                )
            elif any(clean_alt.endswith(f".{ext}") for ext in COMMON_IMAGE_EXTENSIONS):
                issues.append(
                    ValidationIssue(
                        code="IMAGE_ALT_FILENAME",
                        message=f"Image with src='{src}' uses a raw filename as alt text ('{alt_raw.strip()}')",
                        severity=ValidationSeverity.WARNING,
                        field="alt",
                    )
                )
            elif len(alt_raw) > 150:
                issues.append(
                    ValidationIssue(
                        code="IMAGE_ALT_TOO_LONG",
                        message=(
                            f"Image alt text is {len(alt_raw)} characters; recommended max 125-150 characters"
                        ),
                        severity=ValidationSeverity.INFO,
                        field="alt",
                    )
                )

    # 4. Layout stability analysis (CLS prevention)
    # Check for width/height attributes or style dimensions / aspect-ratio
    width_val: int | None = None
    height_val: int | None = None
    if width_str and width_str.isdigit():
        width_val = int(width_str)
    if height_str and height_str.isdigit():
        height_val = int(height_str)

    has_aspect_ratio = False
    if style:
        # Check aspect-ratio style property (e.g. aspect-ratio: 16/9, aspect-ratio: 1.5)
        if re.search(r"aspect-ratio\s*:\s*[0-9./\s]+", style, re.IGNORECASE):
            has_aspect_ratio = True
        # If attributes were not present, check style for explicit width and height in px
        if width_val is None:
            w_match = re.search(r"(?:^|;)\s*width\s*:\s*(\d+)px", style, re.IGNORECASE)
            if w_match:
                width_val = int(w_match.group(1))
        if height_val is None:
            h_match = re.search(r"(?:^|;)\s*height\s*:\s*(\d+)px", style, re.IGNORECASE)
            if h_match:
                height_val = int(h_match.group(1))

    has_layout_dimensions = (
        (width_val is not None and height_val is not None)
        or has_aspect_ratio
    )

    if not has_layout_dimensions:
        issues.append(
            ValidationIssue(
                code="IMAGE_DIMENSIONS_MISSING",
                message=(
                    f"Image with src='{src}' missing explicit width and height attributes "
                    "(or aspect-ratio style); causes layout shift (CLS)"
                ),
                severity=ValidationSeverity.WARNING,
                field="width/height",
            )
        )

    # 5. Filename best-practices analysis
    if src:
        issues.extend(analyze_image_filename(src))

    item = ImageItem(
        src=src,
        alt=alt_raw,
        width=width_val,
        height=height_val,
        is_decorative=is_decorative,
        has_aspect_ratio=has_aspect_ratio,
        style=style or None,
        id=img_id,
    )

    return item, issues


def analyze_media(html_content: str, base_url: str = "") -> MediaAnalysisResult:
    """Analyze all <img> elements in rendered HTML markup."""
    parser = MediaHTMLParser()
    parser.feed(html_content or "")
    parser.close()

    images: list[ImageItem] = []
    all_issues: list[ValidationIssue] = []

    decorative_count = 0
    missing_alt_count = 0
    missing_dimensions_count = 0

    for raw_attr in parser.raw_images:
        item, issues = analyze_image_tag(raw_attr, base_url=base_url)
        images.append(item)
        all_issues.extend(issues)

        if item.is_decorative:
            decorative_count += 1
        elif item.alt is None or not item.alt.strip():
            missing_alt_count += 1

        has_dims = (item.width is not None and item.height is not None) or item.has_aspect_ratio
        if not has_dims:
            missing_dimensions_count += 1

    return MediaAnalysisResult(
        images=images,
        total_images=len(images),
        decorative_count=decorative_count,
        missing_alt_count=missing_alt_count,
        missing_dimensions_count=missing_dimensions_count,
        issues=all_issues,
    )


# ---------------------------------------------------------------------------
# CMS Asset Model Integration (REQ-P9-05 Criterion 4)
# ---------------------------------------------------------------------------

def validate_asset_seo(
    asset: Any,
    alt_text: str | None = None,
    width: int | None = None,
    height: int | None = None,
    is_decorative: bool = False,
) -> list[ValidationIssue]:
    """Validate a CMS Asset record for SEO requirements prior to publishing.
    
    Accepts P8 CMS Asset entity or dict. Does not mutate stored records.
    """
    issues: list[ValidationIssue] = []

    # Extract fields from Asset object or dict
    if hasattr(asset, "local_path"):
        local_path = getattr(asset, "local_path", "") or ""
        original_url = getattr(asset, "original_url", None)
        media_type = getattr(asset, "media_type", "") or ""
    elif isinstance(asset, dict):
        local_path = asset.get("local_path", "")
        original_url = asset.get("original_url")
        media_type = asset.get("media_type", "")
    else:
        local_path = str(asset)
        original_url = None
        media_type = ""

    ref_path = original_url or local_path

    # Only perform image SEO checks on image assets
    is_image = media_type.startswith("image/") or any(
        ref_path.lower().endswith(f".{ext}") for ext in COMMON_IMAGE_EXTENSIONS
    )
    if not is_image:
        return issues

    # 1. Filename validation
    issues.extend(analyze_image_filename(ref_path))

    # 2. Alt text requirement
    if not is_decorative:
        if alt_text is None:
            issues.append(
                ValidationIssue(
                    code="IMAGE_ALT_MISSING",
                    message=f"Media asset '{ref_path}' requires alt text before publishing",
                    severity=ValidationSeverity.CRITICAL,
                    field="alt_text",
                )
            )
        elif not alt_text.strip():
            issues.append(
                ValidationIssue(
                    code="IMAGE_ALT_EMPTY",
                    message=f"Media asset '{ref_path}' has empty alt text and is not marked decorative",
                    severity=ValidationSeverity.WARNING,
                    field="alt_text",
                )
            )
        elif alt_text.strip().lower() in GENERIC_ALT_PATTERNS:
            issues.append(
                ValidationIssue(
                    code="IMAGE_ALT_GENERIC",
                    message=f"Media asset '{ref_path}' uses generic alt text '{alt_text}'",
                    severity=ValidationSeverity.WARNING,
                    field="alt_text",
                )
            )

    # 3. Layout dimension requirement
    if width is None or height is None:
        issues.append(
            ValidationIssue(
                code="IMAGE_DIMENSIONS_MISSING",
                message=f"Media asset '{ref_path}' missing explicit width/height dimensions",
                severity=ValidationSeverity.WARNING,
                field="dimensions",
            )
        )

    return issues


def render_image_tag(
    src: str,
    alt: str = "",
    width: int | None = None,
    height: int | None = None,
    is_decorative: bool = False,
    classes: str | None = None,
    loading: str | None = None,
) -> str:
    """Render an HTML <img> tag with safe attribute escaping against stored XSS."""
    escaped_src = html.escape(src, quote=True)
    parts = [f'<img src="{escaped_src}"']

    if is_decorative:
        parts.append('alt="" aria-hidden="true"')
    else:
        escaped_alt = html.escape(alt or "", quote=True)
        parts.append(f'alt="{escaped_alt}"')

    if width is not None:
        parts.append(f'width="{int(width)}"')
    if height is not None:
        parts.append(f'height="{int(height)}"')

    if classes:
        parts.append(f'class="{html.escape(classes, quote=True)}"')
    if loading:
        parts.append(f'loading="{html.escape(loading, quote=True)}"')

    return " ".join(parts) + " />"
