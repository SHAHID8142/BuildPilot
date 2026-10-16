"""P9 SEO crawling, indexing, robots.txt, and XML sitemaps engine.

Implements REQ-P9-02:
- Deterministic robots.txt generation and parsing (RFC 9309 rules).
- Sitemaps.org 0.9 XML sitemap and sitemap index generation conforming to sps2/schemas/p9-sitemap.schema.json.
- Absolute <loc> canonical validation and SSRF private-IP blocking (Threat Model §5.3).
- Safe XML processing with strict DOCTYPE / ENTITY / XXE rejection (Threat Model §5.5) using Python stdlib only.
- Integration with CMS published routes: only published content is indexable; draft/preview is strictly excluded (Threat Model §5.9).
"""
from __future__ import annotations

import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any

from domain.seo.metadata import validate_canonical_url
from domain.seo.model import (
    RobotsConfig,
    RobotsGroup,
    SitemapEntry,
    SitemapModel,
)

# Sitemaps.org 0.9 specification constants
SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
MAX_SITEMAP_URLS = 50000
VALID_CHANGEFREQS = {"always", "hourly", "daily", "weekly", "monthly", "yearly", "never"}

# Security pattern: Reject DOCTYPE or ENTITY declarations in XML to prevent XXE (Threat Model §5.5)
XXE_SECURITY_PATTERN = re.compile(r"<!(?:DOCTYPE|ENTITY)", re.IGNORECASE)


class IndexingError(Exception):
    """Base error for indexing operations."""


class SitemapParseError(IndexingError):
    """Raised when XML sitemap parsing fails."""


class SitemapSecurityError(IndexingError):
    """Raised when prohibited XML constructs (DOCTYPE, ENTITY, XXE) are detected."""


class SitemapLimitError(IndexingError):
    """Raised when sitemap URL limits are exceeded."""


def _now_iso() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _xml_escape(text: str) -> str:
    """Escape XML special characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# ----------------------------------------------------------------------
# 1. Robots.txt Generation & Parsing (RFC 9309)
# ----------------------------------------------------------------------

def generate_robots_txt(config: RobotsConfig) -> str:
    """Generate deterministic robots.txt content from structured config.
    
    Groups are deterministically sorted by user_agent (with '*' first if present).
    Directives within groups are sorted deterministically.
    Sitemap references are appended at the end, deterministically sorted.
    """
    lines: list[str] = []

    # Sort groups deterministically: '*' group first, then alphabetical by user_agent
    def _group_key(g: RobotsGroup) -> tuple[int, str]:
        ua = g.user_agent.strip().lower()
        return (0 if ua == "*" else 1, ua)

    sorted_groups = sorted(config.groups, key=_group_key)

    for i, group in enumerate(sorted_groups):
        if i > 0:
            lines.append("")
        lines.append(f"User-agent: {group.user_agent.strip()}")
        # Deterministically sort Allow and Disallow rules
        for allow_rule in sorted(group.allow):
            lines.append(f"Allow: {allow_rule.strip()}")
        for disallow_rule in sorted(group.disallow):
            lines.append(f"Disallow: {disallow_rule.strip()}")
        if group.crawl_delay is not None:
            lines.append(f"Crawl-delay: {group.crawl_delay}")

    # Sitemaps at the end, sorted
    if config.sitemaps:
        if lines:
            lines.append("")
        for sm in sorted(config.sitemaps):
            lines.append(f"Sitemap: {sm.strip()}")

    # Host directive if configured
    if config.host:
        if not config.sitemaps and lines:
            lines.append("")
        lines.append(f"Host: {config.host.strip()}")

    return "\n".join(lines) + "\n"


def parse_robots_txt(content: str) -> RobotsConfig:
    """Parse a robots.txt string into a structured RobotsConfig object.
    
    Handles RFC 9309 line semantics, stripping comments, trailing whitespace,
    and grouping rules under their respective User-agent declarations.
    """
    groups: list[RobotsGroup] = []
    sitemaps: list[str] = []
    host: str | None = None

    current_agents: list[str] = []
    current_allow: list[str] = []
    current_disallow: list[str] = []
    current_delay: int | None = None

    def _flush_group() -> None:
        nonlocal current_agents, current_allow, current_disallow, current_delay
        if current_agents:
            for ua in current_agents:
                groups.append(
                    RobotsGroup(
                        user_agent=ua,
                        allow=list(current_allow),
                        disallow=list(current_disallow),
                        crawl_delay=current_delay,
                    )
                )
            current_agents = []
            current_allow = []
            current_disallow = []
            current_delay = None

    for raw_line in content.splitlines():
        # Strip comments
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        if ":" not in line:
            continue

        key, val = line.split(":", 1)
        key = key.strip().lower()
        val = val.strip()

        if key == "user-agent":
            # If we already have rules accumulated, flush the previous group
            if current_allow or current_disallow or current_delay is not None:
                _flush_group()
            current_agents.append(val)
        elif key == "allow":
            current_allow.append(val)
        elif key == "disallow":
            current_disallow.append(val)
        elif key == "crawl-delay":
            try:
                current_delay = int(val)
            except ValueError:
                pass
        elif key == "sitemap":
            if val and val not in sitemaps:
                sitemaps.append(val)
        elif key == "host":
            if val:
                host = val

    # Flush final group
    _flush_group()

    return RobotsConfig(groups=groups, sitemaps=sitemaps, host=host)


def is_path_allowed_by_robots(config: RobotsConfig, path: str, user_agent: str = "*") -> bool:
    """Check if a URL path is allowed for a user agent per RFC 9309 matching rules.
    
    1. Selects the most specific matching User-agent group, falling back to '*'.
    2. Longest matching rule wins.
    3. On equal match length, Allow beats Disallow.
    4. If no rule matches, returns True (allowed).
    """
    target_ua = user_agent.lower()

    # Find matching groups: exact UA match first, else '*' fallback
    matched_groups = [g for g in config.groups if g.user_agent.lower() == target_ua]
    if not matched_groups:
        matched_groups = [g for g in config.groups if g.user_agent.strip() == "*"]

    if not matched_groups:
        return True  # No applicable rules; allowed by default

    best_match_len = -1
    best_is_allow = True

    norm_path = "/" + path.lstrip("/")

    for group in matched_groups:
        for allow_pattern in group.allow:
            pattern = allow_pattern.strip()
            if not pattern:
                continue
            if norm_path.startswith(pattern):
                pat_len = len(pattern)
                if pat_len > best_match_len:
                    best_match_len = pat_len
                    best_is_allow = True
                elif pat_len == best_match_len:
                    best_is_allow = True  # Allow beats Disallow on tie

        for disallow_pattern in group.disallow:
            pattern = disallow_pattern.strip()
            if not pattern:
                continue
            if norm_path.startswith(pattern):
                pat_len = len(pattern)
                if pat_len > best_match_len:
                    best_match_len = pat_len
                    best_is_allow = False
                elif pat_len == best_match_len:
                    # Allow already beats Disallow, keep Allow if it was tied
                    pass

    if best_match_len >= 0:
        return best_is_allow

    return True


# ----------------------------------------------------------------------
# 2. Sitemap Model & XML Generation (sitemaps.org 0.9)
# ----------------------------------------------------------------------

def build_sitemap_model(
    entries: list[SitemapEntry],
    generated_at: str | None = None,
    sitemap_files: list[str] | None = None,
    sitemap_index: bool = False,
) -> SitemapModel:
    """Validate entries and build a SitemapModel conforming to p9-sitemap.schema.json.
    
    Enforces:
    - Absolute URLs matching http/https
    - Rejection of private/loopback IP targets (SSRF protection)
    - Valid changefreq enum values
    - Valid priority bounds (0.0 to 1.0)
    - Maximum 50,000 URLs per sitemap
    - Deterministic sorting by loc
    """
    if len(entries) > MAX_SITEMAP_URLS:
        raise SitemapLimitError(
            f"Sitemap entry count ({len(entries)}) exceeds maximum allowed ({MAX_SITEMAP_URLS})"
        )

    validated_entries: list[SitemapEntry] = []

    for entry in entries:
        # Validate canonical URL
        can_res = validate_canonical_url(entry.loc)
        if not can_res.is_valid:
            crit_msgs = [i.message for i in can_res.issues]
            raise IndexingError(f"Invalid sitemap URL '{entry.loc}': {'; '.join(crit_msgs)}")

        # Validate changefreq if present
        if entry.changefreq is not None:
            cf = str(entry.changefreq).lower()
            if cf not in VALID_CHANGEFREQS:
                raise IndexingError(
                    f"Invalid changefreq '{entry.changefreq}'; must be one of {sorted(VALID_CHANGEFREQS)}"
                )
            entry.changefreq = cf

        # Validate priority if present
        if entry.priority is not None:
            pri = float(entry.priority)
            if pri < 0.0 or pri > 1.0:
                raise IndexingError(f"Invalid priority {entry.priority}; must be between 0.0 and 1.0")
            entry.priority = round(pri, 2)

        # Use normalized canonical URL
        validated_entries.append(
            SitemapEntry(
                loc=can_res.normalized_url,
                lastmod=entry.lastmod,
                changefreq=entry.changefreq,
                priority=entry.priority,
            )
        )

    # Sort deterministically by loc
    sorted_entries = sorted(validated_entries, key=lambda e: e.loc)

    gen_time = generated_at or _now_iso()

    return SitemapModel(
        entries=sorted_entries,
        total_urls=len(sorted_entries),
        generated_at=gen_time,
        sitemap_index=sitemap_index,
        sitemap_files=sorted(sitemap_files) if sitemap_files else [],
    )


def generate_sitemap_xml(sitemap: SitemapModel) -> str:
    """Serialize SitemapModel to deterministic, valid sitemaps.org 0.9 XML string."""
    lines: list[str] = ['<?xml version="1.0" encoding="UTF-8"?>']

    if sitemap.sitemap_index:
        lines.append(f'<sitemapindex xmlns="{SITEMAP_NAMESPACE}">')
        # Sitemaps can be listed either via sitemap_files or entries
        index_urls = sitemap.sitemap_files if sitemap.sitemap_files else [e.loc for e in sitemap.entries]
        for url in sorted(index_urls):
            lines.append("  <sitemap>")
            lines.append(f"    <loc>{_xml_escape(url)}</loc>")
            if sitemap.generated_at:
                lines.append(f"    <lastmod>{_xml_escape(sitemap.generated_at)}</lastmod>")
            lines.append("  </sitemap>")
        lines.append("</sitemapindex>")
    else:
        lines.append(f'<urlset xmlns="{SITEMAP_NAMESPACE}">')
        for entry in sitemap.entries:
            lines.append("  <url>")
            lines.append(f"    <loc>{_xml_escape(entry.loc)}</loc>")
            if entry.lastmod:
                lines.append(f"    <lastmod>{_xml_escape(entry.lastmod)}</lastmod>")
            if entry.changefreq:
                lines.append(f"    <changefreq>{_xml_escape(entry.changefreq)}</changefreq>")
            if entry.priority is not None:
                lines.append(f"    <priority>{entry.priority:.1f}</priority>")
            lines.append("  </url>")
        lines.append("</urlset>")

    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------
# 3. Safe XML Processing (Threat Model §5.5 — XXE Defense)
# ----------------------------------------------------------------------

def _assert_safe_xml(content: str) -> None:
    """Verify XML content does not contain DOCTYPE, ENTITY, or XXE constructs."""
    if XXE_SECURITY_PATTERN.search(content):
        raise SitemapSecurityError(
            "XML document contains DOCTYPE or ENTITY declaration; strictly rejected for XXE defense"
        )


def parse_sitemap_xml(xml_content: str | bytes) -> list[SitemapEntry]:
    """Parse XML sitemap content safely into a list of SitemapEntry objects.
    
    Protects against XXE and entity expansion attacks without external dependencies.
    """
    text = xml_content.decode("utf-8") if isinstance(xml_content, bytes) else xml_content
    _assert_safe_xml(text)

    try:
        root = ET.fromstring(text)
    except Exception as e:
        raise SitemapParseError(f"Failed to parse sitemap XML: {e}") from e

    entries: list[SitemapEntry] = []

    # Namespace handling
    tag_clean = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if tag_clean != "urlset":
        raise SitemapParseError(f"Root tag must be 'urlset', found '{tag_clean}'")

    for url_elem in root:
        elem_tag = url_elem.tag.split("}")[-1] if "}" in url_elem.tag else url_elem.tag
        if elem_tag != "url":
            continue

        loc_val: str | None = None
        lastmod_val: str | None = None
        changefreq_val: str | None = None
        priority_val: float | None = None

        for child in url_elem:
            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            c_text = (child.text or "").strip()
            if child_tag == "loc":
                loc_val = c_text
            elif child_tag == "lastmod":
                lastmod_val = c_text
            elif child_tag == "changefreq":
                changefreq_val = c_text
            elif child_tag == "priority":
                try:
                    priority_val = float(c_text)
                except ValueError:
                    pass

        if not loc_val:
            raise SitemapParseError("Sitemap <url> entry is missing required <loc> element")

        # Validate canonical URL
        can_res = validate_canonical_url(loc_val)
        if not can_res.is_valid:
            crit_msgs = [i.message for i in can_res.issues]
            raise IndexingError(f"Invalid URL in parsed sitemap: '{loc_val}': {'; '.join(crit_msgs)}")

        entries.append(
            SitemapEntry(
                loc=can_res.normalized_url,
                lastmod=lastmod_val,
                changefreq=changefreq_val,
                priority=priority_val,
            )
        )

    return entries


def parse_sitemap_index_xml(xml_content: str | bytes) -> list[str]:
    """Parse sitemap index XML safely and return list of sitemap file URLs."""
    text = xml_content.decode("utf-8") if isinstance(xml_content, bytes) else xml_content
    _assert_safe_xml(text)

    try:
        root = ET.fromstring(text)
    except Exception as e:
        raise SitemapParseError(f"Failed to parse sitemap index XML: {e}") from e

    tag_clean = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if tag_clean != "sitemapindex":
        raise SitemapParseError(f"Root tag must be 'sitemapindex', found '{tag_clean}'")

    sitemap_urls: list[str] = []

    for sm_elem in root:
        elem_tag = sm_elem.tag.split("}")[-1] if "}" in sm_elem.tag else sm_elem.tag
        if elem_tag != "sitemap":
            continue

        loc_val: str | None = None
        for child in sm_elem:
            child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if child_tag == "loc":
                loc_val = (child.text or "").strip()

        if loc_val:
            can_res = validate_canonical_url(loc_val)
            if not can_res.is_valid:
                raise IndexingError(f"Invalid sitemap URL in index: '{loc_val}'")
            sitemap_urls.append(can_res.normalized_url)

    return sitemap_urls


# ----------------------------------------------------------------------
# 4. CMS Content Integration (Published Route Filtering)
# ----------------------------------------------------------------------

def generate_sitemap_from_cms_items(
    items: list[Any],
    base_url: str,
    default_priority: float = 0.5,
    default_changefreq: str = "weekly",
) -> SitemapModel:
    """Generate sitemap from CMS content items.
    
    Accepts CMS Content objects (from domain.cms.model) or plain dictionaries.
    STRICT FILTERING (Threat Model §5.9):
    Only items with status == 'published' are included.
    Items with status 'draft', 'archived', or other unpublished states are excluded.
    """
    entries: list[SitemapEntry] = []
    base = base_url.rstrip("/")

    for item in items:
        # Extract fields supporting Content object or dict
        if hasattr(item, "status"):
            status = getattr(item, "status", "")
            item_id = getattr(item, "id", "")
            slug = getattr(item, "slug", item_id)
            lastmod = getattr(item, "updated_at", None) or getattr(item, "published_at", None)
        elif isinstance(item, dict):
            status = item.get("status", "")
            item_id = item.get("id", "")
            slug = item.get("slug", item_id)
            lastmod = item.get("updated_at") or item.get("published_at")
        else:
            continue

        # Strict Gate: Published only
        if status != "published":
            continue

        if not slug:
            continue

        url = f"{base}/{slug.lstrip('/')}"
        entries.append(
            SitemapEntry(
                loc=url,
                lastmod=lastmod,
                changefreq=default_changefreq,
                priority=default_priority,
            )
        )

    return build_sitemap_model(entries=entries)
