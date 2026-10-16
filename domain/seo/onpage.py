"""P9 On-Page Structural Hierarchy and Internal Link Graph Engine.

Implements REQ-P9-04:
- Evaluates heading structure, single-H1 enforcement, and heading-level jumps.
- Extracts internal and external links from rendered HTML using Python stdlib HTMLParser (UQ-P9-04).
- Normalizes URLs and classifies internal vs external links.
- Evaluates internal link reachability against a known route inventory (static reference analysis).
- Explicitly excludes live network fetching / HTTP probing to prevent SSRF and maintain project-local isolation.
- Detects generic, empty, and duplicate anchor text and link patterns.
"""
from __future__ import annotations

import re
import urllib.parse
from html.parser import HTMLParser
from typing import Any

from domain.seo.metadata import (
    TRACKING_QUERY_PARAMS,
    _is_private_or_loopback_host,
)
from domain.seo.model import (
    HeadingAnalysisResult,
    HeadingItem,
    LinkGraphResult,
    LinkItem,
    OnPageAnalysisResult,
    ValidationIssue,
    ValidationSeverity,
)

# Generic anchor text phrases that provide low search/accessibility signal
GENERIC_ANCHOR_PATTERNS = {
    "click here",
    "click here to",
    "click",
    "here",
    "read more",
    "read",
    "learn more",
    "more",
    "view more",
    "view",
    "see more",
    "see details",
    "details",
    "link",
    "this link",
    "this page",
    "page",
    "website",
    "info",
    "continue",
    "go",
}

# Dangerous protocols to block immediately
UNSAFE_HREF_SCHEMES = {"javascript", "data", "vbscript", "file"}

# Non-web communication protocols to skip from internal route validation
SPECIAL_PROTOCOLS = {"mailto", "tel", "sms"}

# Block-level HTML tags that delimit text and auto-flush unclosed headings
BLOCK_TAGS = {
    "p", "div", "section", "article", "aside", "nav", "header", "footer",
    "main", "ul", "ol", "li", "table", "blockquote", "hr", "pre", "figure",
}


class OnPageHTMLParser(HTMLParser):
    """Linear streaming parser for headings and links."""

    def __init__(self) -> None:
        super().__init__()
        self.headings: list[HeadingItem] = []
        self.raw_links: list[dict[str, Any]] = []

        # Heading extraction state
        self._current_heading_level: int | None = None
        self._heading_text_parts: list[str] = []
        self._heading_id: str | None = None
        self._heading_order = 0

        # Link extraction state
        self._current_href: str | None = None
        self._link_text_parts: list[str] = []
        self._link_attrs: dict[str, str] = {}

    def _flush_current_heading(self) -> None:
        if self._current_heading_level is not None:
            text = " ".join("".join(self._heading_text_parts).split())
            self.headings.append(
                HeadingItem(
                    level=self._current_heading_level,
                    text=text,
                    order=self._heading_order,
                    id=self._heading_id,
                )
            )
            self._current_heading_level = None
            self._heading_text_parts = []
            self._heading_id = None

    def _flush_current_link(self) -> None:
        if self._current_href is not None:
            anchor_text = " ".join("".join(self._link_text_parts).split())
            self.raw_links.append(
                {
                    "href": self._current_href,
                    "anchor_text": anchor_text,
                    "target": self._link_attrs.get("target"),
                    "rel": self._link_attrs.get("rel"),
                }
            )
            self._current_href = None
            self._link_text_parts = []
            self._link_attrs = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs}

        # Heading detection: h1 through h6
        if len(tag_lower) == 2 and tag_lower[0] == "h" and tag_lower[1] in "123456":
            # Auto-flush previous unclosed heading if malformed
            self._flush_current_heading()
            self._current_heading_level = int(tag_lower[1])
            self._heading_text_parts = []
            self._heading_id = attr_dict.get("id") or None
            self._heading_order += 1

        # Block-level elements flush unclosed headings in malformed markup
        elif tag_lower in BLOCK_TAGS:
            self._flush_current_heading()

        # Link detection: <a>
        elif tag_lower == "a":
            # Auto-flush previous unclosed link if malformed
            self._flush_current_link()
            self._current_href = attr_dict.get("href")
            self._link_attrs = attr_dict
            self._link_text_parts = []

        # If an <img> tag is inside an <a>, use its alt text as part of anchor text
        elif tag_lower == "img" and self._current_href is not None:
            alt = attr_dict.get("alt", "").strip()
            if alt:
                self._link_text_parts.append(alt)

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if len(tag_lower) == 2 and tag_lower[0] == "h" and tag_lower[1] in "123456":
            level = int(tag_lower[1])
            if self._current_heading_level == level:
                self._flush_current_heading()

        elif tag_lower in BLOCK_TAGS:
            self._flush_current_heading()

        elif tag_lower == "a":
            self._flush_current_link()

    def handle_data(self, data: str) -> None:
        if self._current_heading_level is not None:
            self._heading_text_parts.append(data)
        if self._current_href is not None:
            self._link_text_parts.append(data)

    def close(self) -> None:
        super().close()
        # Flush any trailing unclosed tags at EOF
        self._flush_current_heading()
        self._flush_current_link()


def analyze_headings(html_content: str) -> HeadingAnalysisResult:
    """Analyze document heading hierarchy, single-H1 rule, and level jumps."""
    parser = OnPageHTMLParser()
    parser.feed(html_content or "")
    parser.close()

    headings = parser.headings
    issues: list[ValidationIssue] = []

    h1_count = sum(1 for h in headings if h.level == 1)

    # 1. Enforce single-H1 rule
    if h1_count == 0:
        issues.append(
            ValidationIssue(
                code="HEADING_NO_H1",
                message="Document has no <h1> heading; exactly one <h1> is required for technical SEO",
                severity=ValidationSeverity.CRITICAL,
                field="h1",
            )
        )
    elif h1_count > 1:
        issues.append(
            ValidationIssue(
                code="HEADING_MULTIPLE_H1",
                message=f"Document contains {h1_count} <h1> headings; exactly one <h1> is recommended",
                severity=ValidationSeverity.WARNING,
                field="h1",
            )
        )

    # 2. Check first heading level
    if headings and headings[0].level != 1:
        issues.append(
            ValidationIssue(
                code="HEADING_STARTS_WITHOUT_H1",
                message=f"Document hierarchy begins with <h{headings[0].level}> instead of <h1>",
                severity=ValidationSeverity.WARNING,
                field=f"h{headings[0].level}",
            )
        )

    # 3. Check for skipped heading levels and empty headings
    prev_level = 0
    for h in headings:
        # Check empty heading text
        if not h.text.strip():
            issues.append(
                ValidationIssue(
                    code="HEADING_EMPTY",
                    message=f"Empty <h{h.level}> heading detected (no text content)",
                    severity=ValidationSeverity.WARNING,
                    field=f"h{h.level}",
                )
            )

        # Check level skips (only when increasing depth)
        if prev_level > 0 and h.level > prev_level + 1:
            issues.append(
                ValidationIssue(
                    code="HEADING_LEVEL_SKIPPED",
                    message=(
                        f"Heading level jump from <h{prev_level}> directly to <h{h.level}> "
                        f"(skipped <h{prev_level + 1}>)"
                    ),
                    severity=ValidationSeverity.WARNING,
                    field=f"h{h.level}",
                )
            )
        prev_level = h.level

    return HeadingAnalysisResult(
        headings=headings,
        h1_count=h1_count,
        issues=issues,
    )


def _normalize_route_path(path: str) -> str:
    """Normalize a URL path for route matching."""
    if not path:
        return "/"
    # Collapse multiple slashes
    norm = re.sub(r"/+", "/", path.strip())
    # Strip trailing slash unless root
    if len(norm) > 1 and norm.endswith("/"):
        norm = norm[:-1]
    return norm.lower()


def _normalize_url(
    raw_href: str,
    base_url: str = "",
    current_path: str = "/",
) -> tuple[str, bool, list[ValidationIssue]]:
    """Normalize a URL, classify as internal or external, and run security checks."""
    issues: list[ValidationIssue] = []
    href = raw_href.strip()

    if not href:
        issues.append(
            ValidationIssue(
                code="LINK_EMPTY_HREF",
                message="Link has empty or missing href attribute",
                severity=ValidationSeverity.CRITICAL,
                field="href",
            )
        )
        return "", True, issues

    # Pure hash anchor on current page
    if href.startswith("#"):
        norm_path = _normalize_route_path(current_path)
        norm_url = f"{norm_path}{href}" if href != "#" else norm_path
        if href == "#":
            issues.append(
                ValidationIssue(
                    code="LINK_EMPTY_FRAGMENT",
                    message="Link href is bare '#' without an anchor identifier",
                    severity=ValidationSeverity.WARNING,
                    field="href",
                )
            )
        return norm_url, True, issues

    parsed = urllib.parse.urlparse(href)
    scheme = parsed.scheme.lower()

    # Block dangerous schemes
    if scheme in UNSAFE_HREF_SCHEMES:
        issues.append(
            ValidationIssue(
                code="LINK_UNSAFE_SCHEME",
                message=f"Link uses unsafe scheme '{scheme}:'",
                severity=ValidationSeverity.CRITICAL,
                field="href",
            )
        )
        return href, False, issues

    # Special non-HTTP protocols
    if scheme in SPECIAL_PROTOCOLS:
        return href, False, issues

    # Determine base host for classification
    base_parsed = urllib.parse.urlparse(base_url) if base_url else None
    base_netloc = base_parsed.netloc.lower() if base_parsed else ""

    is_internal = True

    if scheme in ("http", "https"):
        link_netloc = parsed.netloc.lower()
        if base_netloc and link_netloc == base_netloc:
            is_internal = True
        elif not base_netloc:
            # Without base_url, assume absolute URLs with hosts are external
            is_internal = False
        else:
            is_internal = False

        # SSRF check on link hostname
        if _is_private_or_loopback_host(parsed.hostname or ""):
            issues.append(
                ValidationIssue(
                    code="LINK_PRIVATE_IP_REJECTED",
                    message=f"Link points to private or loopback host '{parsed.hostname}'",
                    severity=ValidationSeverity.CRITICAL,
                    field="href",
                )
            )
    else:
        # Relative link without scheme
        is_internal = True

    # Build normalized URL
    if is_internal:
        # Resolve path relative to current_path or base
        path_only = parsed.path or "/"
        if not path_only.startswith("/"):
            # Relative to current path
            resolved_path = urllib.parse.urljoin(current_path, path_only)
        else:
            resolved_path = path_only

        norm_path = _normalize_route_path(resolved_path)

        # Filter tracking parameters
        clean_query = ""
        if parsed.query:
            query_parts = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            kept_params = [
                (k, v) for k, v in query_parts if k.lower() not in TRACKING_QUERY_PARAMS
            ]
            if kept_params:
                clean_query = f"?{urllib.parse.urlencode(sorted(kept_params))}"

        norm_url = f"{norm_path}{clean_query}"
    else:
        # Normalize external URL (lowercase scheme and host, collapse path slashes)
        ext_path = re.sub(r"/+", "/", parsed.path) if parsed.path else "/"
        query_part = f"?{parsed.query}" if parsed.query else ""
        norm_url = f"{scheme}://{parsed.netloc.lower()}{ext_path}{query_part}"

    return norm_url, is_internal, issues


def analyze_links(
    html_content: str,
    base_url: str = "",
    current_path: str = "/",
    known_routes: set[str] | list[str] | None = None,
) -> LinkGraphResult:
    """Extract links, classify internal/external, and evaluate broken routes against known routes.
    
    Adheres to project boundary: Does NOT perform live network probing.
    Reachability is verified statically against known_routes.
    """
    parser = OnPageHTMLParser()
    parser.feed(html_content or "")
    parser.close()

    raw_links = parser.raw_links
    internal_links: list[LinkItem] = []
    external_links: list[LinkItem] = []
    broken_links: list[LinkItem] = []
    issues: list[ValidationIssue] = []

    # Prepare normalized route inventory if provided
    norm_known_routes: set[str] | None = None
    if known_routes is not None:
        norm_known_routes = {_normalize_route_path(r) for r in known_routes}

    internal_target_counts: dict[str, int] = {}

    for raw in raw_links:
        href = raw["href"]
        anchor_text = raw["anchor_text"]

        norm_url, is_internal, norm_issues = _normalize_url(
            raw_href=href,
            base_url=base_url,
            current_path=current_path,
        )
        issues.extend(norm_issues)

        link_item = LinkItem(
            href=href,
            anchor_text=anchor_text,
            is_internal=is_internal,
            normalized_url=norm_url,
            target=raw.get("target"),
            rel=raw.get("rel"),
        )

        # 1. Anchor text diagnostics
        clean_anchor = anchor_text.strip().lower()
        if not clean_anchor and not href.startswith("#"):
            issues.append(
                ValidationIssue(
                    code="LINK_EMPTY_ANCHOR_TEXT",
                    message=f"Link '{href}' has empty anchor text and no descriptive content",
                    severity=ValidationSeverity.WARNING,
                    field=href,
                )
            )
        elif clean_anchor in GENERIC_ANCHOR_PATTERNS:
            issues.append(
                ValidationIssue(
                    code="LINK_GENERIC_ANCHOR_TEXT",
                    message=f"Link '{href}' uses generic anchor text '{anchor_text}'",
                    severity=ValidationSeverity.WARNING,
                    field=href,
                )
            )

        # 2. Link classification & graph tracking
        if is_internal:
            internal_links.append(link_item)
            # Track route target without query or fragment
            route_target = _normalize_route_path(norm_url.split("?")[0].split("#")[0])
            internal_target_counts[route_target] = (
                internal_target_counts.get(route_target, 0) + 1
            )

            # 3. Static broken-link detection against known_routes
            if norm_known_routes is not None:
                if route_target not in norm_known_routes:
                    broken_links.append(link_item)
                    issues.append(
                        ValidationIssue(
                            code="LINK_BROKEN_INTERNAL_ROUTE",
                            message=(
                                f"Internal link '{href}' resolves to non-existent route '{route_target}'"
                            ),
                            severity=ValidationSeverity.CRITICAL,
                            field=href,
                        )
                    )
        else:
            external_links.append(link_item)

    # 4. Report limitation when known_routes is not provided (explicit machine-readable notice)
    if known_routes is None and internal_links:
        issues.append(
            ValidationIssue(
                code="LINK_NETWORK_CHECK_SKIPPED",
                message=(
                    "Live HTTP link verification skipped by design (network requests not permitted "
                    "in project-local audit mode; supply known_routes for static verification)"
                ),
                severity=ValidationSeverity.INFO,
            )
        )

    # 5. Duplicate internal link targets advisory
    unique_targets = sorted(internal_target_counts.keys())
    for target, count in internal_target_counts.items():
        if count > 1:
            issues.append(
                ValidationIssue(
                    code="LINK_DUPLICATE_INTERNAL_TARGET",
                    message=f"Internal destination '{target}' linked {count} times from this page",
                    severity=ValidationSeverity.INFO,
                    field=target,
                )
            )

    return LinkGraphResult(
        internal_links=internal_links,
        external_links=external_links,
        broken_links=broken_links,
        unique_internal_targets=unique_targets,
        issues=issues,
    )


def analyze_onpage(
    html_content: str,
    base_url: str = "",
    current_path: str = "/",
    known_routes: set[str] | list[str] | None = None,
) -> OnPageAnalysisResult:
    """Analyze both heading hierarchy and link graph in a unified on-page audit."""
    headings_res = analyze_headings(html_content)
    links_res = analyze_links(
        html_content=html_content,
        base_url=base_url,
        current_path=current_path,
        known_routes=known_routes,
    )

    all_issues = list(headings_res.issues) + list(links_res.issues)

    return OnPageAnalysisResult(
        headings=headings_res,
        links=links_res,
        issues=all_issues,
    )
