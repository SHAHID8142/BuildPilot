"""P9 SEO metadata and canonical engine.

Implements REQ-P9-01:
- Generates page metadata, canonical URLs, and social tags from content models (Ingestion Interface A).
- Normalizes and validates canonical URLs with SSRF / private IP protection (Threat Model §5.3).
- Validates title and description lengths with SEO diagnostic warnings.
- Renders HTML meta tags with mandatory HTML entity escaping against stored XSS (Threat Model §5.1).
"""
from __future__ import annotations

import html
import ipaddress
import re
import urllib.parse
from typing import Any

from domain.seo.model import (
    CanonicalValidationResult,
    OpenGraph,
    RobotsDirectives,
    SEOMetadata,
    TwitterCard,
    ValidationIssue,
    ValidationSeverity,
)

# Blocked IP networks for SSRF protection in canonical URLs (Threat Model §5.3)
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

# Common tracking query parameters that should not appear in canonical URLs
TRACKING_QUERY_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
}


def _is_private_or_loopback_host(hostname: str) -> bool:
    """Check if a hostname resolves to a literal private or loopback IP."""
    if not hostname:
        return True
    if hostname.lower() in ("localhost", "loopback"):
        return True
    try:
        ip = ipaddress.ip_address(hostname)
        for net in BLOCKED_IP_NETWORKS:
            if ip in net:
                return True
        return False
    except ValueError:
        # Not a raw IP literal; domain hostname
        return False


def validate_canonical_url(url: str) -> CanonicalValidationResult:
    """Validate and normalize a canonical URL.
    
    Enforces:
    - Absolute URL with http or https scheme
    - Valid non-empty hostname
    - Rejection of private/loopback IP addresses (SSRF prevention)
    - Stripping of common tracking query parameters
    - Normalization of lowercase scheme, host, and clean path
    """
    issues: list[ValidationIssue] = []
    if not url or not isinstance(url, str) or not url.strip():
        issues.append(
            ValidationIssue(
                code="CANONICAL_EMPTY",
                message="Canonical URL must not be empty",
                severity=ValidationSeverity.CRITICAL,
                field="canonical_url",
            )
        )
        return CanonicalValidationResult(is_valid=False, normalized_url="", issues=issues)

    url = url.strip()

    try:
        parsed = urllib.parse.urlsplit(url)
    except Exception as e:
        issues.append(
            ValidationIssue(
                code="CANONICAL_MALFORMED",
                message=f"Failed to parse canonical URL: {e}",
                severity=ValidationSeverity.CRITICAL,
                field="canonical_url",
            )
        )
        return CanonicalValidationResult(is_valid=False, normalized_url=url, issues=issues)

    if parsed.scheme.lower() not in ("http", "https"):
        issues.append(
            ValidationIssue(
                code="CANONICAL_INVALID_SCHEME",
                message=f"Canonical URL must use http or https, found: '{parsed.scheme}'",
                severity=ValidationSeverity.CRITICAL,
                field="canonical_url",
            )
        )

    if not parsed.netloc:
        issues.append(
            ValidationIssue(
                code="CANONICAL_NOT_ABSOLUTE",
                message="Canonical URL must be an absolute URL with a hostname",
                severity=ValidationSeverity.CRITICAL,
                field="canonical_url",
            )
        )

    hostname = parsed.hostname or ""
    if _is_private_or_loopback_host(hostname):
        issues.append(
            ValidationIssue(
                code="CANONICAL_PRIVATE_IP_REJECTED",
                message=f"Canonical URL target resolves to private or loopback host '{hostname}'",
                severity=ValidationSeverity.CRITICAL,
                field="canonical_url",
            )
        )

    # Normalize hostname (lowercase)
    norm_scheme = parsed.scheme.lower()
    norm_netloc = hostname.lower()
    if parsed.port:
        if (norm_scheme == "http" and parsed.port != 80) or (norm_scheme == "https" and parsed.port != 443):
            norm_netloc = f"{norm_netloc}:{parsed.port}"

    # Normalize path (collapse multiple slashes)
    norm_path = re.sub(r"/+", "/", parsed.path) if parsed.path else "/"

    # Normalize query: strip tracking parameters
    norm_query_parts: list[tuple[str, str]] = []
    if parsed.query:
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        for k, v in query_pairs:
            if k.lower() in TRACKING_QUERY_PARAMS:
                issues.append(
                    ValidationIssue(
                        code="CANONICAL_TRACKING_PARAM_STRIPPED",
                        message=f"Tracking parameter '{k}' stripped from canonical URL",
                        severity=ValidationSeverity.WARNING,
                        field="canonical_url",
                    )
                )
            else:
                norm_query_parts.append((k, v))

    norm_query = urllib.parse.urlencode(sorted(norm_query_parts)) if norm_query_parts else ""

    # Reconstruct normalized URL without fragment (canonicals must not have fragments)
    if parsed.fragment:
        issues.append(
            ValidationIssue(
                code="CANONICAL_FRAGMENT_STRIPPED",
                message="URL fragment (#...) was stripped from canonical URL",
                severity=ValidationSeverity.WARNING,
                field="canonical_url",
            )
        )

    normalized_url = urllib.parse.urlunsplit((norm_scheme, norm_netloc, norm_path, norm_query, ""))
    has_critical = any(issue.severity == ValidationSeverity.CRITICAL for issue in issues)

    return CanonicalValidationResult(
        is_valid=not has_critical,
        normalized_url=normalized_url,
        issues=issues,
    )


def validate_metadata(meta: SEOMetadata) -> list[ValidationIssue]:
    """Perform diagnostic validation on an SEOMetadata object."""
    issues: list[ValidationIssue] = []

    # Title validation
    title = meta.title.strip() if meta.title else ""
    if not title:
        issues.append(
            ValidationIssue(
                code="TITLE_MISSING",
                message="Page title is empty or missing",
                severity=ValidationSeverity.CRITICAL,
                field="title",
            )
        )
    elif len(title) < 30:
        issues.append(
            ValidationIssue(
                code="TITLE_TOO_SHORT",
                message=f"Page title is short ({len(title)} chars); recommended 50-60 characters",
                severity=ValidationSeverity.WARNING,
                field="title",
            )
        )
    elif len(title) > 70:
        issues.append(
            ValidationIssue(
                code="TITLE_EXCESSIVE_LENGTH",
                message=f"Page title exceeds 70 characters ({len(title)} chars); will be truncated by search engines",
                severity=ValidationSeverity.WARNING,
                field="title",
            )
        )
    elif len(title) > 60:
        issues.append(
            ValidationIssue(
                code="TITLE_SLIGHTLY_LONG",
                message=f"Page title is {len(title)} chars; recommended max 60 characters for desktop viewports",
                severity=ValidationSeverity.INFO,
                field="title",
            )
        )

    # Description validation
    desc = meta.description.strip() if meta.description else ""
    if not desc:
        issues.append(
            ValidationIssue(
                code="DESCRIPTION_MISSING",
                message="Meta description is empty or missing",
                severity=ValidationSeverity.CRITICAL,
                field="description",
            )
        )
    elif len(desc) < 70:
        issues.append(
            ValidationIssue(
                code="DESCRIPTION_TOO_SHORT",
                message=f"Meta description is short ({len(desc)} chars); recommended 120-160 characters",
                severity=ValidationSeverity.WARNING,
                field="description",
            )
        )
    elif len(desc) > 300:
        issues.append(
            ValidationIssue(
                code="DESCRIPTION_EXCEEDS_SCHEMA_LIMIT",
                message=f"Meta description exceeds maximum schema limit of 300 chars ({len(desc)} chars)",
                severity=ValidationSeverity.CRITICAL,
                field="description",
            )
        )
    elif len(desc) > 160:
        issues.append(
            ValidationIssue(
                code="DESCRIPTION_TRUNCATION_RISK",
                message=f"Meta description exceeds 160 chars ({len(desc)} chars); will be truncated by search engines",
                severity=ValidationSeverity.WARNING,
                field="description",
            )
        )

    # Canonical URL validation
    can_res = validate_canonical_url(meta.canonical_url)
    issues.extend(can_res.issues)

    # Open Graph validation
    if meta.open_graph:
        og = meta.open_graph
        if not og.title.strip():
            issues.append(
                ValidationIssue(
                    code="OG_TITLE_MISSING",
                    message="Open Graph og:title must not be empty",
                    severity=ValidationSeverity.WARNING,
                    field="open_graph.title",
                )
            )
        if not og.description.strip():
            issues.append(
                ValidationIssue(
                    code="OG_DESCRIPTION_MISSING",
                    message="Open Graph og:description must not be empty",
                    severity=ValidationSeverity.WARNING,
                    field="open_graph.description",
                )
            )

    return issues


def _summarize_body(body: str, max_length: int = 155) -> str:
    """Create a clean description snippet from a text body."""
    if not body:
        return ""
    # Strip HTML tags if any present
    text = re.sub(r"<[^>]+>", " ", body)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_length:
        return text
    # Cut at word boundary
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated.rstrip(".,;:-") + "..."


def generate_metadata_from_content(
    content: Any,
    base_url: str,
    slug: str | None = None,
    default_description: str | None = None,
    site_name: str | None = None,
) -> SEOMetadata:
    """Ingestion Interface A: Derive SEOMetadata from a CMS content item.
    
    Accepts CMS Content entity (from domain.cms.model) or plain dict.
    Enforces Threat Model §5.9: draft/preview content is automatically set to noindex, nofollow.
    """
    # Extract fields supporting Content object or dict
    if hasattr(content, "title"):
        title = content.title or ""
        body = getattr(content, "body", "") or ""
        status = getattr(content, "status", "published")
        content_id = getattr(content, "id", "")
    elif isinstance(content, dict):
        title = content.get("title", "")
        body = content.get("body", "")
        status = content.get("status", "published")
        content_id = content.get("id", "")
    else:
        title = str(content)
        body = ""
        status = "published"
        content_id = ""

    # Derive description
    description = _summarize_body(body) if body else ""
    if not description and default_description:
        description = default_description

    # Derive canonical URL
    base = base_url.rstrip("/")
    path = f"/{slug.lstrip('/')}" if slug else f"/content/{content_id}"
    canonical_raw = f"{base}{path}"
    can_res = validate_canonical_url(canonical_raw)
    canonical = can_res.normalized_url if can_res.is_valid else canonical_raw

    # Threat Model §5.9: Draft/preview content gets noindex, nofollow
    is_published = (status == "published")
    robots = RobotsDirectives(index=is_published, follow=is_published)

    # Social graph
    og = OpenGraph(
        title=title,
        description=description or title,
        url=canonical,
        type="article",
        site_name=site_name,
    )
    twitter = TwitterCard(
        card="summary",
        title=title,
        description=description or title,
    )

    return SEOMetadata(
        title=title,
        description=description,
        canonical_url=canonical,
        robots=robots,
        open_graph=og,
        twitter_card=twitter,
    )


def _safe_attr(value: str) -> str:
    """Escape an attribute value and strip control newlines (Threat Model §5.1)."""
    clean = re.sub(r"[\r\n]+", " ", str(value)).strip()
    return html.escape(clean, quote=True)


def render_html_meta_tags(meta: SEOMetadata) -> str:
    """Render HTML <head> meta tags with mandatory HTML entity escaping.
    
    Protects against Stored XSS in meta tag content and attribute injections (Threat Model §5.1).
    """
    lines: list[str] = []

    # Charset and Viewport
    lines.append(f'<meta charset="{_safe_attr(meta.charset)}">')
    lines.append(f'<meta name="viewport" content="{_safe_attr(meta.viewport)}">')

    # Title & Description
    safe_title = _safe_attr(meta.title)
    lines.append(f"<title>{safe_title}</title>")

    if meta.description:
        lines.append(f'<meta name="description" content="{_safe_attr(meta.description)}">')

    # Canonical
    lines.append(f'<link rel="canonical" href="{_safe_attr(meta.canonical_url)}">')

    # Robots
    robots_str = meta.robots.to_directive_string()
    lines.append(f'<meta name="robots" content="{_safe_attr(robots_str)}">')

    # Open Graph
    if meta.open_graph:
        og = meta.open_graph
        lines.append(f'<meta property="og:title" content="{_safe_attr(og.title)}">')
        lines.append(f'<meta property="og:description" content="{_safe_attr(og.description)}">')
        lines.append(f'<meta property="og:url" content="{_safe_attr(og.url)}">')
        lines.append(f'<meta property="og:type" content="{_safe_attr(og.type)}">')
        if og.image:
            lines.append(f'<meta property="og:image" content="{_safe_attr(og.image)}">')
        if og.site_name:
            lines.append(f'<meta property="og:site_name" content="{_safe_attr(og.site_name)}">')
        if og.locale:
            lines.append(f'<meta property="og:locale" content="{_safe_attr(og.locale)}">')

    # Twitter Card
    if meta.twitter_card:
        tw = meta.twitter_card
        lines.append(f'<meta name="twitter:card" content="{_safe_attr(tw.card)}">')
        lines.append(f'<meta name="twitter:title" content="{_safe_attr(tw.title)}">')
        lines.append(f'<meta name="twitter:description" content="{_safe_attr(tw.description)}">')
        if tw.image:
            lines.append(f'<meta name="twitter:image" content="{_safe_attr(tw.image)}">')
        if tw.site:
            lines.append(f'<meta name="twitter:site" content="{_safe_attr(tw.site)}">')
        if tw.creator:
            lines.append(f'<meta name="twitter:creator" content="{_safe_attr(tw.creator)}">')

    return "\n".join(lines)
