"""SPS 2.0 SEO Subsystem (domain/seo).

Provides technical SEO metadata generation, canonical validation, robots and sitemap
governance, schema.org JSON-LD structured data, on-page analysis, and pre-deployment auditing.
"""
from __future__ import annotations

from domain.seo.indexing import (
    IndexingError,
    SitemapLimitError,
    SitemapParseError,
    SitemapSecurityError,
    build_sitemap_model,
    generate_robots_txt,
    generate_sitemap_from_cms_items,
    generate_sitemap_xml,
    is_path_allowed_by_robots,
    parse_robots_txt,
    parse_sitemap_index_xml,
    parse_sitemap_xml,
)
from domain.seo.metadata import (
    generate_metadata_from_content,
    render_html_meta_tags,
    validate_canonical_url,
    validate_metadata,
)
from domain.seo.model import (
    CanonicalValidationResult,
    OpenGraph,
    RobotsConfig,
    RobotsDirectives,
    RobotsGroup,
    SEOMetadata,
    SitemapEntry,
    SitemapModel,
    TwitterCard,
    ValidationIssue,
    ValidationSeverity,
)

__all__ = [
    "CanonicalValidationResult",
    "IndexingError",
    "OpenGraph",
    "RobotsConfig",
    "RobotsDirectives",
    "RobotsGroup",
    "SEOMetadata",
    "SitemapEntry",
    "SitemapLimitError",
    "SitemapModel",
    "SitemapParseError",
    "SitemapSecurityError",
    "TwitterCard",
    "ValidationIssue",
    "ValidationSeverity",
    "build_sitemap_model",
    "generate_metadata_from_content",
    "generate_robots_txt",
    "generate_sitemap_from_cms_items",
    "generate_sitemap_xml",
    "is_path_allowed_by_robots",
    "parse_robots_txt",
    "parse_sitemap_index_xml",
    "parse_sitemap_xml",
    "render_html_meta_tags",
    "validate_canonical_url",
    "validate_metadata",
]
