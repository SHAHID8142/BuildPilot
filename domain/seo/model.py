"""P9 SEO domain models.

Defines core data contracts for SEO metadata, robots directives,
social graph tags (Open Graph, Twitter Card), and validation issues.
All models are pure Python dataclasses that serialize to dicts conforming
to sps2/schemas/p9-metadata.schema.json.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    """Severity levels for SEO validation findings."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class ValidationIssue:
    """A single validation finding or diagnostic."""
    code: str
    message: str
    severity: ValidationSeverity
    field: str | None = None

    def to_dict(self) -> dict[str, str]:
        res = {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
        }
        if self.field:
            res["field"] = self.field
        return res


@dataclass
class RobotsDirectives:
    """Robots indexing and crawling directives."""
    index: bool = True
    follow: bool = True
    noarchive: bool = False
    nosnippet: bool = False
    max_snippet: int | None = None
    max_image_preview: str | None = None
    max_video_preview: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "index": self.index,
            "follow": self.follow,
        }
        if self.noarchive:
            data["noarchive"] = True
        if self.nosnippet:
            data["nosnippet"] = True
        if self.max_snippet is not None:
            data["max_snippet"] = self.max_snippet
        if self.max_image_preview is not None:
            data["max_image_preview"] = self.max_image_preview
        if self.max_video_preview is not None:
            data["max_video_preview"] = self.max_video_preview
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RobotsDirectives:
        return cls(
            index=bool(data.get("index", True)),
            follow=bool(data.get("follow", True)),
            noarchive=bool(data.get("noarchive", False)),
            nosnippet=bool(data.get("nosnippet", False)),
            max_snippet=data.get("max_snippet"),
            max_image_preview=data.get("max_image_preview"),
            max_video_preview=data.get("max_video_preview"),
        )

    def to_directive_string(self) -> str:
        """Render directives into a meta robots content string."""
        parts: list[str] = []
        parts.append("index" if self.index else "noindex")
        parts.append("follow" if self.follow else "nofollow")
        if self.noarchive:
            parts.append("noarchive")
        if self.nosnippet:
            parts.append("nosnippet")
        if self.max_snippet is not None:
            parts.append(f"max-snippet:{self.max_snippet}")
        if self.max_image_preview is not None:
            parts.append(f"max-image-preview:{self.max_image_preview}")
        if self.max_video_preview is not None:
            parts.append(f"max-video-preview:{self.max_video_preview}")
        return ", ".join(parts)


@dataclass
class OpenGraph:
    """Open Graph protocol metadata."""
    title: str
    description: str
    url: str
    type: str = "website"
    image: str | None = None
    site_name: str | None = None
    locale: str = "en_US"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "type": self.type,
            "locale": self.locale,
        }
        if self.image:
            data["image"] = self.image
        if self.site_name:
            data["site_name"] = self.site_name
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OpenGraph:
        return cls(
            title=data["title"],
            description=data["description"],
            url=data["url"],
            type=data.get("type", "website"),
            image=data.get("image"),
            site_name=data.get("site_name"),
            locale=data.get("locale", "en_US"),
        )


@dataclass
class TwitterCard:
    """Twitter Card metadata."""
    card: str
    title: str
    description: str
    image: str | None = None
    site: str | None = None
    creator: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "card": self.card,
            "title": self.title,
            "description": self.description,
        }
        if self.image:
            data["image"] = self.image
        if self.site:
            data["site"] = self.site
        if self.creator:
            data["creator"] = self.creator
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TwitterCard:
        return cls(
            card=data.get("card", "summary"),
            title=data["title"],
            description=data["description"],
            image=data.get("image"),
            site=data.get("site"),
            creator=data.get("creator"),
        )


@dataclass
class CanonicalValidationResult:
    """Result of canonical URL analysis."""
    is_valid: bool
    normalized_url: str
    issues: list[ValidationIssue] = field(default_factory=list)


@dataclass
class SEOMetadata:
    """Top-level page SEO metadata container conforming to p9-metadata.schema.json."""
    title: str
    description: str
    canonical_url: str
    robots: RobotsDirectives = field(default_factory=RobotsDirectives)
    viewport: str = "width=device-width, initial-scale=1"
    charset: str = "UTF-8"
    open_graph: OpenGraph | None = None
    twitter_card: TwitterCard | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict validating against p9-metadata.schema.json."""
        data: dict[str, Any] = {
            "title": self.title,
            "description": self.description,
            "canonical_url": self.canonical_url,
            "robots": self.robots.to_dict(),
            "viewport": self.viewport,
            "charset": self.charset,
        }
        if self.open_graph:
            data["open_graph"] = self.open_graph.to_dict()
        if self.twitter_card:
            data["twitter_card"] = self.twitter_card.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SEOMetadata:
        robots = RobotsDirectives.from_dict(data["robots"]) if "robots" in data else RobotsDirectives()
        og = OpenGraph.from_dict(data["open_graph"]) if data.get("open_graph") else None
        twitter = TwitterCard.from_dict(data["twitter_card"]) if data.get("twitter_card") else None
        return cls(
            title=data["title"],
            description=data["description"],
            canonical_url=data["canonical_url"],
            robots=robots,
            viewport=data.get("viewport", "width=device-width, initial-scale=1"),
            charset=data.get("charset", "UTF-8"),
            open_graph=og,
            twitter_card=twitter,
        )


@dataclass
class SitemapEntry:
    """A single URL entry in a sitemap.org compliant XML sitemap."""
    loc: str
    lastmod: str | None = None
    changefreq: str | None = None
    priority: float | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"loc": self.loc}
        if self.lastmod is not None:
            data["lastmod"] = self.lastmod
        if self.changefreq is not None:
            data["changefreq"] = self.changefreq
        if self.priority is not None:
            data["priority"] = float(self.priority)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SitemapEntry:
        return cls(
            loc=data["loc"],
            lastmod=data.get("lastmod"),
            changefreq=data.get("changefreq"),
            priority=data.get("priority"),
        )


@dataclass
class SitemapModel:
    """Internal model for an XML sitemap conforming to p9-sitemap.schema.json."""
    entries: list[SitemapEntry] = field(default_factory=list)
    total_urls: int = 0
    generated_at: str = ""
    sitemap_index: bool = False
    sitemap_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "total_urls": self.total_urls,
            "generated_at": self.generated_at,
            "entries": [e.to_dict() for e in self.entries],
            "sitemap_index": self.sitemap_index,
        }
        if self.sitemap_files:
            data["sitemap_files"] = list(self.sitemap_files)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SitemapModel:
        entries = [SitemapEntry.from_dict(e) for e in data.get("entries", [])]
        return cls(
            entries=entries,
            total_urls=int(data.get("total_urls", len(entries))),
            generated_at=data.get("generated_at", ""),
            sitemap_index=bool(data.get("sitemap_index", False)),
            sitemap_files=data.get("sitemap_files", []),
        )


@dataclass
class RobotsGroup:
    """User-agent directive group in a robots.txt file."""
    user_agent: str = "*"
    allow: list[str] = field(default_factory=list)
    disallow: list[str] = field(default_factory=list)
    crawl_delay: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "user_agent": self.user_agent,
            "allow": list(self.allow),
            "disallow": list(self.disallow),
        }
        if self.crawl_delay is not None:
            data["crawl_delay"] = self.crawl_delay
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RobotsGroup:
        return cls(
            user_agent=data.get("user_agent", "*"),
            allow=data.get("allow", []),
            disallow=data.get("disallow", []),
            crawl_delay=data.get("crawl_delay"),
        )


@dataclass
class RobotsConfig:
    """Structured configuration for a robots.txt file."""
    groups: list[RobotsGroup] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)
    host: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "groups": [g.to_dict() for g in self.groups],
            "sitemaps": list(self.sitemaps),
        }
        if self.host is not None:
            data["host"] = self.host
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RobotsConfig:
        groups = [RobotsGroup.from_dict(g) for g in data.get("groups", [])]
        return cls(
            groups=groups,
            sitemaps=data.get("sitemaps", []),
            host=data.get("host"),
        )


@dataclass
class AuthorInfo:
    """Author representation for Schema.org structured data."""
    name: str
    type: str = "Person"  # "Person" or "Organization"

    def to_dict(self) -> dict[str, Any]:
        return {
            "@type": self.type,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthorInfo:
        return cls(
            name=data.get("name", ""),
            type=data.get("@type", data.get("type", "Person")),
        )


@dataclass
class PublisherInfo:
    """Publisher representation for Schema.org structured data."""
    name: str
    type: str = "Organization"
    logo_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "@type": self.type,
            "name": self.name,
        }
        if self.logo_url:
            res["logo"] = {
                "@type": "ImageObject",
                "url": self.logo_url,
            }
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PublisherInfo:
        logo_url = None
        logo = data.get("logo")
        if isinstance(logo, dict):
            logo_url = logo.get("url")
        elif isinstance(logo, str):
            logo_url = logo
        return cls(
            name=data.get("name", ""),
            type=data.get("@type", data.get("type", "Organization")),
            logo_url=logo_url,
        )


@dataclass
class BreadcrumbItem:
    """A single item in a Schema.org BreadcrumbList."""
    name: str
    item: str
    position: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "@type": "ListItem",
            "position": self.position,
            "name": self.name,
            "item": self.item,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BreadcrumbItem:
        return cls(
            name=data.get("name", ""),
            item=data.get("item", ""),
            position=int(data.get("position", 1)),
        )


@dataclass
class BreadcrumbListSchema:
    """Schema.org BreadcrumbList container."""
    items: list[BreadcrumbItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [it.to_dict() for it in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BreadcrumbListSchema:
        raw_items = data.get("itemListElement", [])
        return cls(items=[BreadcrumbItem.from_dict(it) for it in raw_items])


@dataclass
class WebSiteSchema:
    """Schema.org WebSite representation."""
    name: str
    url: str
    description: str | None = None
    id: str | None = None
    publisher: PublisherInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": self.name,
            "url": self.url,
        }
        if self.description:
            res["description"] = self.description
        if self.id:
            res["@id"] = self.id
        if self.publisher:
            res["publisher"] = self.publisher.to_dict()
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WebSiteSchema:
        pub = PublisherInfo.from_dict(data["publisher"]) if data.get("publisher") else None
        return cls(
            name=data.get("name", ""),
            url=data.get("url", ""),
            description=data.get("description"),
            id=data.get("@id", data.get("id")),
            publisher=pub,
        )


@dataclass
class OrganizationSchema:
    """Schema.org Organization representation."""
    name: str
    url: str
    logo_url: str | None = None
    description: str | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": self.name,
            "url": self.url,
        }
        if self.logo_url:
            res["logo"] = {
                "@type": "ImageObject",
                "url": self.logo_url,
            }
        if self.description:
            res["description"] = self.description
        if self.id:
            res["@id"] = self.id
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrganizationSchema:
        logo_url = None
        logo = data.get("logo")
        if isinstance(logo, dict):
            logo_url = logo.get("url")
        elif isinstance(logo, str):
            logo_url = logo
        return cls(
            name=data.get("name", ""),
            url=data.get("url", ""),
            logo_url=logo_url,
            description=data.get("description"),
            id=data.get("@id", data.get("id")),
        )


@dataclass
class ArticleSchema:
    """Schema.org Article representation."""
    headline: str
    url: str
    date_published: str
    date_modified: str | None = None
    description: str | None = None
    author: AuthorInfo | None = None
    publisher: PublisherInfo | None = None
    image: str | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": self.headline,
            "url": self.url,
            "datePublished": self.date_published,
        }
        if self.date_modified:
            res["dateModified"] = self.date_modified
        if self.description:
            res["description"] = self.description
        if self.author:
            res["author"] = self.author.to_dict()
        if self.publisher:
            res["publisher"] = self.publisher.to_dict()
        if self.image:
            res["image"] = self.image
        if self.id:
            res["@id"] = self.id
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArticleSchema:
        auth = AuthorInfo.from_dict(data["author"]) if data.get("author") else None
        pub = PublisherInfo.from_dict(data["publisher"]) if data.get("publisher") else None
        return cls(
            headline=data.get("headline", data.get("name", "")),
            url=data.get("url", ""),
            date_published=data.get("datePublished", ""),
            date_modified=data.get("dateModified"),
            description=data.get("description"),
            author=auth,
            publisher=pub,
            image=data.get("image"),
            id=data.get("@id", data.get("id")),
        )


@dataclass
class WebPageSchema:
    """Schema.org WebPage representation."""
    name: str
    url: str
    description: str | None = None
    date_published: str | None = None
    date_modified: str | None = None
    author: AuthorInfo | None = None
    publisher: PublisherInfo | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": self.name,
            "url": self.url,
        }
        if self.description:
            res["description"] = self.description
        if self.date_published:
            res["datePublished"] = self.date_published
        if self.date_modified:
            res["dateModified"] = self.date_modified
        if self.author:
            res["author"] = self.author.to_dict()
        if self.publisher:
            res["publisher"] = self.publisher.to_dict()
        if self.id:
            res["@id"] = self.id
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WebPageSchema:
        auth = AuthorInfo.from_dict(data["author"]) if data.get("author") else None
        pub = PublisherInfo.from_dict(data["publisher"]) if data.get("publisher") else None
        return cls(
            name=data.get("name", ""),
            url=data.get("url", ""),
            description=data.get("description"),
            date_published=data.get("datePublished"),
            date_modified=data.get("dateModified"),
            author=auth,
            publisher=pub,
            id=data.get("@id", data.get("id")),
        )


@dataclass
class HeadingItem:
    """A heading element extracted from HTML."""
    level: int  # 1 to 6
    text: str
    order: int = 1
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "level": self.level,
            "text": self.text,
            "order": self.order,
        }
        if self.id:
            data["id"] = self.id
        return data


@dataclass
class LinkItem:
    """A hyperlink element extracted from HTML."""
    href: str
    anchor_text: str
    is_internal: bool = True
    normalized_url: str = ""
    target: str | None = None
    rel: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "href": self.href,
            "anchor_text": self.anchor_text,
            "is_internal": self.is_internal,
            "normalized_url": self.normalized_url,
        }
        if self.target:
            data["target"] = self.target
        if self.rel:
            data["rel"] = self.rel
        return data


@dataclass
class HeadingAnalysisResult:
    """Result of document heading hierarchy analysis."""
    headings: list[HeadingItem] = field(default_factory=list)
    h1_count: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "headings": [h.to_dict() for h in self.headings],
            "h1_count": self.h1_count,
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class LinkGraphResult:
    """Result of page link extraction and graph analysis."""
    internal_links: list[LinkItem] = field(default_factory=list)
    external_links: list[LinkItem] = field(default_factory=list)
    broken_links: list[LinkItem] = field(default_factory=list)
    unique_internal_targets: list[str] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "internal_links": [l.to_dict() for l in self.internal_links],
            "external_links": [l.to_dict() for l in self.external_links],
            "broken_links": [l.to_dict() for l in self.broken_links],
            "unique_internal_targets": list(self.unique_internal_targets),
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class OnPageAnalysisResult:
    """Combined on-page structural hierarchy and link analysis result."""
    headings: HeadingAnalysisResult = field(default_factory=HeadingAnalysisResult)
    links: LinkGraphResult = field(default_factory=LinkGraphResult)
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "headings": self.headings.to_dict(),
            "links": self.links.to_dict(),
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class ImageItem:
    """An image element extracted from HTML."""
    src: str
    alt: str | None = None
    width: int | None = None
    height: int | None = None
    is_decorative: bool = False
    has_aspect_ratio: bool = False
    style: str | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "src": self.src,
            "alt": self.alt,
            "is_decorative": self.is_decorative,
            "has_aspect_ratio": self.has_aspect_ratio,
        }
        if self.width is not None:
            data["width"] = self.width
        if self.height is not None:
            data["height"] = self.height
        if self.style:
            data["style"] = self.style
        if self.id:
            data["id"] = self.id
        return data


@dataclass
class MediaAnalysisResult:
    """Result of media and image SEO analysis."""
    images: list[ImageItem] = field(default_factory=list)
    total_images: int = 0
    decorative_count: int = 0
    missing_alt_count: int = 0
    missing_dimensions_count: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "images": [img.to_dict() for img in self.images],
            "total_images": self.total_images,
            "decorative_count": self.decorative_count,
            "missing_alt_count": self.missing_alt_count,
            "missing_dimensions_count": self.missing_dimensions_count,
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class RedirectRule:
    """A configured HTTP redirect rule."""
    source: str
    target: str
    status_code: int = 301
    allow_external: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source": self.source,
            "target": self.target,
            "status_code": self.status_code,
            "allow_external": self.allow_external,
        }
        if self.reason:
            data["reason"] = self.reason
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RedirectRule:
        return cls(
            source=data.get("source", ""),
            target=data.get("target", ""),
            status_code=int(data.get("status_code", 301)),
            allow_external=bool(data.get("allow_external", False)),
            reason=data.get("reason", ""),
        )


@dataclass
class RedirectHop:
    """A single hop along a redirect chain."""
    source: str
    target: str
    status_code: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "status_code": self.status_code,
        }


@dataclass
class RedirectChain:
    """A chain or loop of redirects."""
    start_url: str
    final_target: str
    hops: list[RedirectHop] = field(default_factory=list)
    hop_count: int = 0
    is_loop: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_url": self.start_url,
            "final_target": self.final_target,
            "hops": [h.to_dict() for h in self.hops],
            "hop_count": self.hop_count,
            "is_loop": self.is_loop,
        }


@dataclass
class RedirectAnalysisResult:
    """Result of static redirect taxonomy analysis."""
    total_rules: int = 0
    valid_count: int = 0
    loop_count: int = 0
    chain_count: int = 0
    chains: list[RedirectChain] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_rules": self.total_rules,
            "valid_count": self.valid_count,
            "loop_count": self.loop_count,
            "chain_count": self.chain_count,
            "chains": [c.to_dict() for c in self.chains],
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class PaginationSignals:
    """Pagination link and canonical signals for a paginated collection page."""
    page: int = 1
    total_pages: int | None = None
    current_url: str = ""
    canonical_url: str | None = None
    prev_url: str | None = None
    next_url: str | None = None
    strategy: str = "self"  # "self" or "root"

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "page": self.page,
            "current_url": self.current_url,
            "strategy": self.strategy,
        }
        if self.total_pages is not None:
            data["total_pages"] = self.total_pages
        if self.canonical_url is not None:
            data["canonical_url"] = self.canonical_url
        if self.prev_url is not None:
            data["prev_url"] = self.prev_url
        if self.next_url is not None:
            data["next_url"] = self.next_url
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PaginationSignals:
        return cls(
            page=int(data.get("page", 1)),
            total_pages=data.get("total_pages"),
            current_url=data.get("current_url", ""),
            canonical_url=data.get("canonical_url"),
            prev_url=data.get("prev_url"),
            next_url=data.get("next_url"),
            strategy=data.get("strategy", "self"),
        )


@dataclass
class PaginationAnalysisResult:
    """Result of paginated collection canonicalization analysis."""
    signals: PaginationSignals
    is_valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "signals": self.signals.to_dict(),
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues],
        }


@dataclass
class CWVMetricResult:
    """Evaluation result for an individual Web Vitals metric."""
    metric_name: str
    status: str  # "PASS", "NEEDS_IMPROVEMENT", "FAIL", "NOT_APPLICABLE"
    observed_value: float | None = None
    threshold_description: str | None = None
    na_rationale: str | None = None
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "metric_name": self.metric_name,
            "status": self.status,
            "issues": [i.to_dict() for i in self.issues],
        }
        if self.observed_value is not None:
            data["observed_value"] = self.observed_value
        if self.threshold_description is not None:
            data["threshold_description"] = self.threshold_description
        if self.na_rationale is not None:
            data["na_rationale"] = self.na_rationale
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CWVMetricResult:
        return cls(
            metric_name=data.get("metric_name", ""),
            status=data.get("status", "NOT_APPLICABLE"),
            observed_value=data.get("observed_value"),
            threshold_description=data.get("threshold_description"),
            na_rationale=data.get("na_rationale"),
            issues=[
                ValidationIssue(
                    code=i["code"],
                    message=i["message"],
                    severity=ValidationSeverity(i["severity"]),
                    field=i.get("field"),
                )
                for i in data.get("issues", [])
            ],
        )


@dataclass
class StaticShiftPreventionResult:
    """Result of static HTML layout-shift prevention analysis."""
    total_images_analyzed: int = 0
    images_lacking_dimensions: int = 0
    font_issues_count: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_images_analyzed": self.total_images_analyzed,
            "images_lacking_dimensions": self.images_lacking_dimensions,
            "font_issues_count": self.font_issues_count,
            "issues": [i.to_dict() for i in self.issues],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StaticShiftPreventionResult:
        return cls(
            total_images_analyzed=int(data.get("total_images_analyzed", 0)),
            images_lacking_dimensions=int(data.get("images_lacking_dimensions", 0)),
            font_issues_count=int(data.get("font_issues_count", 0)),
            issues=[
                ValidationIssue(
                    code=i["code"],
                    message=i["message"],
                    severity=ValidationSeverity(i["severity"]),
                    field=i.get("field"),
                )
                for i in data.get("issues", [])
            ],
        )


@dataclass
class CWVAnalysisResult:
    """Aggregate result of Core Web Vitals and layout stability analysis."""
    cls: CWVMetricResult
    lcp: CWVMetricResult
    inp: CWVMetricResult
    static_prevention: StaticShiftPreventionResult
    is_valid: bool = True
    conf_001_status: str = "UNRESOLVED"
    issues: list[ValidationIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cls": self.cls.to_dict(),
            "lcp": self.lcp.to_dict(),
            "inp": self.inp.to_dict(),
            "static_prevention": self.static_prevention.to_dict(),
            "is_valid": self.is_valid,
            "conf_001_status": self.conf_001_status,
            "issues": [i.to_dict() for i in self.issues],
        }

    @classmethod
    def from_dict(cls_type, data: dict[str, Any]) -> CWVAnalysisResult:
        return cls_type(
            cls=CWVMetricResult.from_dict(data.get("cls", {})),
            lcp=CWVMetricResult.from_dict(data.get("lcp", {})),
            inp=CWVMetricResult.from_dict(data.get("inp", {})),
            static_prevention=StaticShiftPreventionResult.from_dict(data.get("static_prevention", {})),
            is_valid=bool(data.get("is_valid", True)),
            conf_001_status=data.get("conf_001_status", "UNRESOLVED"),
            issues=[
                ValidationIssue(
                    code=i["code"],
                    message=i["message"],
                    severity=ValidationSeverity(i["severity"]),
                    field=i.get("field"),
                )
                for i in data.get("issues", [])
            ],
        )






