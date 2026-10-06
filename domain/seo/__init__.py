"""SPS 2.0 SEO Subsystem (domain/seo).

Provides technical SEO metadata generation, canonical validation, robots and sitemap
governance, schema.org JSON-LD structured data, on-page analysis, and pre-deployment auditing.
"""
from __future__ import annotations

from domain.seo.metadata import (
    generate_metadata_from_content,
    render_html_meta_tags,
    validate_canonical_url,
    validate_metadata,
)
from domain.seo.model import (
    CanonicalValidationResult,
    OpenGraph,
    RobotsDirectives,
    SEOMetadata,
    TwitterCard,
    ValidationIssue,
    ValidationSeverity,
)

__all__ = [
    "CanonicalValidationResult",
    "OpenGraph",
    "RobotsDirectives",
    "SEOMetadata",
    "TwitterCard",
    "ValidationIssue",
    "ValidationSeverity",
    "generate_metadata_from_content",
    "render_html_meta_tags",
    "validate_canonical_url",
    "validate_metadata",
]
