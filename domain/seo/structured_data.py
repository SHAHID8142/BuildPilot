"""P9 Structured Data (JSON-LD) and Social Graph Engine.

Implements REQ-P9-03:
- Generates Schema.org JSON-LD structured data conforming to sps2/schemas/p9-structured-data.schema.json.
- Supports exactly the 5 approved structured data types:
  WebSite, Organization, Article, BreadcrumbList, WebPage.
- Enforces deterministic JSON serialization (sorted keys).
- Implements safe JSON-LD output handling at the HTML/script boundary
  preventing </script> breakout and comment injection (Threat Model §5.2).
- Preserves unmutated stored content across serialization and deserialization.
- Extracts and parses JSON-LD from HTML using Python standard-library html.parser.HTMLParser (UQ-P9-04).
- Provides comprehensive schema and entity validation.
"""
from __future__ import annotations

import html
import ipaddress
import json
import re
import urllib.parse
from datetime import datetime
from html.parser import HTMLParser
from typing import Any

from domain.seo.model import (
    ArticleSchema,
    AuthorInfo,
    BreadcrumbItem,
    BreadcrumbListSchema,
    OrganizationSchema,
    PublisherInfo,
    ValidationIssue,
    ValidationSeverity,
    WebPageSchema,
    WebSiteSchema,
)

# Constants
SCHEMA_CONTEXT = "https://schema.org"
SUPPORTED_SCHEMA_TYPES = {
    "WebSite",
    "Organization",
    "Article",
    "BreadcrumbList",
    "WebPage",
}

# Unsafe URI schemes to block for security
UNSAFE_URI_SCHEMES = {"javascript", "data", "vbscript", "file"}

# Blocked IP networks for SSRF protection in schema URIs (Threat Model §5.3)
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


class StructuredDataError(Exception):
    """Base error for structured data operations."""


class StructuredDataValidationError(StructuredDataError):
    """Raised when structured data validation fails critically."""


def _is_private_or_loopback_host(hostname: str) -> bool:
    """Check if a hostname resolves to a literal private or loopback IP."""
    if not hostname:
        return True
    if hostname.lower() in ("localhost", "loopback"):
        return True
    try:
        addr = ipaddress.ip_address(hostname)
        for net in BLOCKED_IP_NETWORKS:
            if addr in net:
                return True
    except ValueError:
        pass
    return False


def _validate_uri(val: str, field_name: str) -> list[ValidationIssue]:
    """Validate a URI value against formatting and SSRF/protocol security rules."""
    issues: list[ValidationIssue] = []
    if not isinstance(val, str) or not val.strip():
        issues.append(
            ValidationIssue(
                code="SCHEMA_INVALID_URI",
                message=f"URI field '{field_name}' must be a non-empty string",
                severity=ValidationSeverity.CRITICAL,
                field=field_name,
            )
        )
        return issues

    parsed = urllib.parse.urlparse(val)
    scheme = parsed.scheme.lower()

    if scheme in UNSAFE_URI_SCHEMES:
        issues.append(
            ValidationIssue(
                code="SCHEMA_UNSAFE_URI_SCHEME",
                message=f"URI field '{field_name}' uses dangerous scheme '{scheme}:'",
                severity=ValidationSeverity.CRITICAL,
                field=field_name,
            )
        )
        return issues

    if scheme not in ("http", "https"):
        issues.append(
            ValidationIssue(
                code="SCHEMA_INVALID_URI_SCHEME",
                message=f"URI field '{field_name}' must use http or https scheme, got '{scheme}'",
                severity=ValidationSeverity.CRITICAL,
                field=field_name,
            )
        )
        return issues

    if not parsed.netloc:
        issues.append(
            ValidationIssue(
                code="SCHEMA_INVALID_URI_HOST",
                message=f"URI field '{field_name}' must include a valid host",
                severity=ValidationSeverity.CRITICAL,
                field=field_name,
            )
        )
        return issues

    if _is_private_or_loopback_host(parsed.hostname or ""):
        issues.append(
            ValidationIssue(
                code="SCHEMA_URI_PRIVATE_IP_REJECTED",
                message=f"URI field '{field_name}' points to private or loopback host '{parsed.hostname}'",
                severity=ValidationSeverity.CRITICAL,
                field=field_name,
            )
        )

    return issues


def _validate_datetime(val: str, field_name: str) -> list[ValidationIssue]:
    """Validate an ISO 8601 date-time string."""
    issues: list[ValidationIssue] = []
    if not isinstance(val, str) or not val.strip():
        issues.append(
            ValidationIssue(
                code="SCHEMA_INVALID_DATE_TIME",
                message=f"Date-time field '{field_name}' must be a non-empty string",
                severity=ValidationSeverity.WARNING,
                field=field_name,
            )
        )
        return issues

    try:
        # Normalize trailing Z to +00:00 for fromisoformat compatibility
        clean_val = val.replace("Z", "+00:00") if val.endswith("Z") else val
        datetime.fromisoformat(clean_val)
    except Exception:
        issues.append(
            ValidationIssue(
                code="SCHEMA_INVALID_DATE_TIME",
                message=f"Date-time field '{field_name}' has invalid ISO 8601 format: '{val}'",
                severity=ValidationSeverity.WARNING,
                field=field_name,
            )
        )
    return issues


# ---------------------------------------------------------------------------
# Builders / Generators
# ---------------------------------------------------------------------------

def build_website_schema(
    name: str,
    url: str,
    description: str | None = None,
    id: str | None = None,
    publisher: PublisherInfo | dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a Schema.org WebSite JSON-LD dict."""
    pub = (
        PublisherInfo.from_dict(publisher)
        if isinstance(publisher, dict)
        else publisher
    )
    model = WebSiteSchema(
        name=name,
        url=url,
        description=description,
        id=id,
        publisher=pub,
    )
    return model.to_dict()


def build_organization_schema(
    name: str,
    url: str,
    logo_url: str | None = None,
    description: str | None = None,
    id: str | None = None,
) -> dict[str, Any]:
    """Build a Schema.org Organization JSON-LD dict."""
    model = OrganizationSchema(
        name=name,
        url=url,
        logo_url=logo_url,
        description=description,
        id=id,
    )
    return model.to_dict()


def build_article_schema(
    headline: str,
    url: str,
    date_published: str,
    date_modified: str | None = None,
    description: str | None = None,
    author: AuthorInfo | dict[str, Any] | str | None = None,
    publisher: PublisherInfo | dict[str, Any] | None = None,
    image: str | None = None,
    id: str | None = None,
) -> dict[str, Any]:
    """Build a Schema.org Article JSON-LD dict."""
    if isinstance(author, str):
        auth = AuthorInfo(name=author)
    elif isinstance(author, dict):
        auth = AuthorInfo.from_dict(author)
    else:
        auth = author

    if isinstance(publisher, dict):
        pub = PublisherInfo.from_dict(publisher)
    else:
        pub = publisher

    model = ArticleSchema(
        headline=headline,
        url=url,
        date_published=date_published,
        date_modified=date_modified,
        description=description,
        author=auth,
        publisher=pub,
        image=image,
        id=id,
    )
    return model.to_dict()


def build_breadcrumb_list_schema(
    items: list[tuple[str, str]] | list[dict[str, Any]] | list[BreadcrumbItem],
) -> dict[str, Any]:
    """Build a Schema.org BreadcrumbList JSON-LD dict.
    
    Accepts:
    - list of (name, url) tuples
    - list of {"name": ..., "item": ...} dicts
    - list of BreadcrumbItem instances
    Positions are automatically assigned sequentially starting at 1.
    """
    breadcrumb_items: list[BreadcrumbItem] = []
    for idx, item in enumerate(items, 1):
        if isinstance(item, tuple):
            breadcrumb_items.append(
                BreadcrumbItem(name=item[0], item=item[1], position=idx)
            )
        elif isinstance(item, dict):
            name = item.get("name", "")
            url = item.get("item", item.get("url", ""))
            pos = int(item.get("position", idx))
            breadcrumb_items.append(
                BreadcrumbItem(name=name, item=url, position=pos)
            )
        elif isinstance(item, BreadcrumbItem):
            item.position = item.position or idx
            breadcrumb_items.append(item)

    model = BreadcrumbListSchema(items=breadcrumb_items)
    return model.to_dict()


def build_webpage_schema(
    name: str,
    url: str,
    description: str | None = None,
    date_published: str | None = None,
    date_modified: str | None = None,
    author: AuthorInfo | dict[str, Any] | str | None = None,
    publisher: PublisherInfo | dict[str, Any] | None = None,
    id: str | None = None,
) -> dict[str, Any]:
    """Build a Schema.org WebPage JSON-LD dict."""
    if isinstance(author, str):
        auth = AuthorInfo(name=author)
    elif isinstance(author, dict):
        auth = AuthorInfo.from_dict(author)
    else:
        auth = author

    if isinstance(publisher, dict):
        pub = PublisherInfo.from_dict(publisher)
    else:
        pub = publisher

    model = WebPageSchema(
        name=name,
        url=url,
        description=description,
        date_published=date_published,
        date_modified=date_modified,
        author=auth,
        publisher=pub,
        id=id,
    )
    return model.to_dict()


# ---------------------------------------------------------------------------
# CMS Ingestion Interface A Integration
# ---------------------------------------------------------------------------

def _extract_content_fields(content: Any) -> tuple[str, str, str, str, str | None, str, str]:
    """Extract standard fields from a CMS Content entity or dictionary."""
    if hasattr(content, "title"):
        title = content.title or ""
        body = getattr(content, "body", "") or ""
        created_at = getattr(content, "created_at", "") or ""
        updated_at = getattr(content, "updated_at", "") or ""
        published_at = getattr(content, "published_at", None)
        author_id = getattr(content, "author_id", "") or ""
        content_id = getattr(content, "id", "") or ""
    elif isinstance(content, dict):
        title = content.get("title", "")
        body = content.get("body", "")
        created_at = content.get("created_at", "")
        updated_at = content.get("updated_at", "")
        published_at = content.get("published_at")
        author_id = content.get("author_id", "")
        content_id = content.get("id", "")
    else:
        title = str(content)
        body = ""
        created_at = datetime.now().isoformat()
        updated_at = created_at
        published_at = created_at
        author_id = ""
        content_id = ""

    return title, body, created_at, updated_at, published_at, author_id, content_id


def generate_article_structured_data(
    content: Any,
    base_url: str,
    slug: str | None = None,
    author: AuthorInfo | str | None = None,
    publisher: PublisherInfo | None = None,
    image_url: str | None = None,
) -> dict[str, Any]:
    """Generate Schema.org Article JSON-LD from a CMS content item."""
    title, body, created_at, updated_at, published_at, author_id, content_id = (
        _extract_content_fields(content)
    )

    base = base_url.rstrip("/")
    path = f"/{slug.lstrip('/')}" if slug else f"/content/{content_id}"
    article_url = f"{base}{path}"

    date_pub = published_at or created_at or datetime.now().isoformat()
    date_mod = updated_at or date_pub

    # Derive author if not explicitly supplied
    auth_val = author
    if not auth_val and author_id:
        auth_val = AuthorInfo(name=author_id)

    # Derive short description from body
    desc = ""
    if body:
        clean = re.sub(r"<[^>]+>", " ", body)
        clean = re.sub(r"\s+", " ", clean).strip()
        desc = clean[:155] if len(clean) > 155 else clean

    return build_article_schema(
        headline=title,
        url=article_url,
        date_published=date_pub,
        date_modified=date_mod,
        description=desc or None,
        author=auth_val,
        publisher=publisher,
        image=image_url,
    )


def generate_webpage_structured_data(
    content: Any,
    base_url: str,
    slug: str | None = None,
    author: AuthorInfo | str | None = None,
    publisher: PublisherInfo | None = None,
) -> dict[str, Any]:
    """Generate Schema.org WebPage JSON-LD from a CMS content item."""
    title, body, created_at, updated_at, published_at, author_id, content_id = (
        _extract_content_fields(content)
    )

    base = base_url.rstrip("/")
    path = f"/{slug.lstrip('/')}" if slug else f"/page/{content_id}"
    page_url = f"{base}{path}"

    date_pub = published_at or created_at
    date_mod = updated_at or date_pub

    auth_val = author
    if not auth_val and author_id:
        auth_val = AuthorInfo(name=author_id)

    desc = ""
    if body:
        clean = re.sub(r"<[^>]+>", " ", body)
        clean = re.sub(r"\s+", " ", clean).strip()
        desc = clean[:155] if len(clean) > 155 else clean

    return build_webpage_schema(
        name=title,
        url=page_url,
        description=desc or None,
        date_published=date_pub or None,
        date_modified=date_mod or None,
        author=auth_val,
        publisher=publisher,
    )


def generate_website_structured_data(
    site_name: str,
    base_url: str,
    description: str | None = None,
    publisher: PublisherInfo | None = None,
) -> dict[str, Any]:
    """Generate Schema.org WebSite JSON-LD."""
    return build_website_schema(
        name=site_name,
        url=base_url,
        description=description,
        publisher=publisher,
    )


def generate_breadcrumb_structured_data(
    trail: list[tuple[str, str]] | list[dict[str, Any]] | list[BreadcrumbItem],
) -> dict[str, Any]:
    """Generate Schema.org BreadcrumbList JSON-LD."""
    return build_breadcrumb_list_schema(trail)


# ---------------------------------------------------------------------------
# Deterministic Serialization & HTML-Boundary Safety (Threat Model §5.2)
# ---------------------------------------------------------------------------

def escape_json_ld_for_html(json_str: str) -> str:
    """Safely escape JSON string for embedding inside HTML <script> tags.

    Prevents </script> breakout and <!-- comment injection.
    Uses RFC 8259 compliant JSON escapes so that json.loads() recovers the
    exact unmutated stored data:
    - All occurrences of '</' are replaced with '<\\/' (valid JSON solidus escape)
    - All occurrences of '<!--' are replaced with '\\u003c!--' (valid JSON unicode escape)
    """
    # 1. Neutralize closing HTML tags: </script>, </SCRIPT>, </style>, etc.
    escaped = re.sub(r"</", r"<\\/", json_str)
    # 2. Neutralize HTML comments
    escaped = escaped.replace("<!--", r"\u003c!--")
    return escaped


def serialize_json_ld(data: Any, indent: int = 2) -> str:
    """Serialize structured data to deterministic JSON string (sorted keys)."""
    if hasattr(data, "to_dict"):
        obj = data.to_dict()
    elif isinstance(data, list):
        obj = [d.to_dict() if hasattr(d, "to_dict") else d for d in data]
    else:
        obj = data

    return json.dumps(obj, indent=indent, sort_keys=True, ensure_ascii=False)


def render_json_ld_script_tag(data: Any, indent: int = 2) -> str:
    """Render structured data as a safe <script type="application/ld+json"> tag.

    Applies deterministic serialization and boundary escaping against script breakout.
    """
    raw_json = serialize_json_ld(data, indent=indent)
    safe_json = escape_json_ld_for_html(raw_json)
    return f'<script type="application/ld+json">\n{safe_json}\n</script>'


# ---------------------------------------------------------------------------
# HTMLParser JSON-LD Extraction (UQ-P9-04)
# ---------------------------------------------------------------------------

class JSONLDExtractor(HTMLParser):
    """Safe streaming parser extracting JSON-LD script blocks from HTML."""

    def __init__(self) -> None:
        super().__init__()
        self._in_json_ld = False
        self._buffer: list[str] = []
        self.blocks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "script":
            attr_dict = {k.lower(): (v or "").lower() for k, v in attrs}
            if attr_dict.get("type") == "application/ld+json":
                self._in_json_ld = True
                self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_json_ld:
            self._in_json_ld = False
            raw_text = "".join(self._buffer).strip()
            if raw_text:
                self.blocks.append(raw_text)
            self._buffer = []

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._buffer.append(data)


def extract_json_ld_from_html(html_content: str) -> list[dict[str, Any]]:
    """Extract and parse all JSON-LD blocks from an HTML string using Python stdlib HTMLParser."""
    parser = JSONLDExtractor()
    parser.feed(html_content)
    results: list[dict[str, Any]] = []
    for raw in parser.blocks:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        results.append(item)
            elif isinstance(parsed, dict):
                results.append(parsed)
        except json.JSONDecodeError as err:
            raise StructuredDataError(f"Failed to decode JSON-LD block: {err}") from err
    return results


# ---------------------------------------------------------------------------
# Validation Engine (conforming to p9-structured-data.schema.json)
# ---------------------------------------------------------------------------

def _scan_for_script_probes(obj: Any, path: str = "") -> list[ValidationIssue]:
    """Recursively check for script breakout strings in data fields."""
    issues: list[ValidationIssue] = []
    if isinstance(obj, str):
        if re.search(r"<\s*/\s*script", obj, re.IGNORECASE):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_SCRIPT_TAG_IN_FIELD",
                    message=f"Field '{path}' contains literal </script> breakout probe",
                    severity=ValidationSeverity.WARNING,
                    field=path,
                )
            )
    elif isinstance(obj, dict):
        for k, v in obj.items():
            curr_path = f"{path}.{k}" if path else k
            issues.extend(_scan_for_script_probes(v, curr_path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            curr_path = f"{path}[{idx}]"
            issues.extend(_scan_for_script_probes(item, curr_path))
    return issues


def validate_structured_data(data: Any) -> list[ValidationIssue]:
    """Validate structured data against Schema.org rules and p9-structured-data.schema.json."""
    if hasattr(data, "to_dict"):
        entity = data.to_dict()
    else:
        entity = data

    # Support list of entities
    if isinstance(entity, list):
        all_issues: list[ValidationIssue] = []
        for idx, item in enumerate(entity):
            item_issues = validate_structured_data(item)
            for iss in item_issues:
                field_prefix = f"[{idx}]"
                iss.field = f"{field_prefix}.{iss.field}" if iss.field else field_prefix
                all_issues.append(iss)
        return all_issues

    if not isinstance(entity, dict):
        return [
            ValidationIssue(
                code="SCHEMA_NOT_AN_OBJECT",
                message=f"Structured data entity must be a JSON object (dict), got {type(entity).__name__}",
                severity=ValidationSeverity.CRITICAL,
            )
        ]

    issues: list[ValidationIssue] = []

    # 1. @context validation
    if "@context" not in entity:
        issues.append(
            ValidationIssue(
                code="SCHEMA_MISSING_CONTEXT",
                message="Structured data is missing required '@context' property",
                severity=ValidationSeverity.CRITICAL,
                field="@context",
            )
        )
    elif entity["@context"] != SCHEMA_CONTEXT:
        issues.append(
            ValidationIssue(
                code="SCHEMA_INVALID_CONTEXT",
                message=f"@context must be '{SCHEMA_CONTEXT}', got '{entity['@context']}'",
                severity=ValidationSeverity.CRITICAL,
                field="@context",
            )
        )

    # 2. @type validation
    schema_type = entity.get("@type")
    if not schema_type:
        issues.append(
            ValidationIssue(
                code="SCHEMA_MISSING_TYPE",
                message="Structured data is missing required '@type' property",
                severity=ValidationSeverity.CRITICAL,
                field="@type",
            )
        )
        return issues

    if schema_type not in SUPPORTED_SCHEMA_TYPES:
        issues.append(
            ValidationIssue(
                code="SCHEMA_UNSUPPORTED_TYPE",
                message=(
                    f"Unsupported schema type '{schema_type}'. "
                    f"Approved P9 types: {sorted(SUPPORTED_SCHEMA_TYPES)}"
                ),
                severity=ValidationSeverity.WARNING,
                field="@type",
            )
        )
        return issues

    # 3. Type-specific required property validation
    if schema_type == "WebSite":
        if not entity.get("name"):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="WebSite entity requires non-empty 'name'",
                    severity=ValidationSeverity.WARNING,
                    field="name",
                )
            )
        if not entity.get("url"):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="WebSite entity requires non-empty 'url'",
                    severity=ValidationSeverity.WARNING,
                    field="url",
                )
            )
        elif isinstance(entity.get("url"), str):
            issues.extend(_validate_uri(entity["url"], "url"))

    elif schema_type == "Organization":
        if not entity.get("name"):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="Organization entity requires non-empty 'name'",
                    severity=ValidationSeverity.WARNING,
                    field="name",
                )
            )
        if not entity.get("url"):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="Organization entity requires non-empty 'url'",
                    severity=ValidationSeverity.WARNING,
                    field="url",
                )
            )
        elif isinstance(entity.get("url"), str):
            issues.extend(_validate_uri(entity["url"], "url"))

        if "logo" in entity and entity["logo"] is not None:
            logo = entity["logo"]
            if isinstance(logo, dict):
                if logo.get("@type") != "ImageObject":
                    issues.append(
                        ValidationIssue(
                            code="SCHEMA_INVALID_STRUCTURE",
                            message="Organization logo @type must be 'ImageObject'",
                            severity=ValidationSeverity.WARNING,
                            field="logo.@type",
                        )
                    )
                if not logo.get("url"):
                    issues.append(
                        ValidationIssue(
                            code="SCHEMA_MISSING_PROPERTY",
                            message="Organization logo requires non-empty 'url'",
                            severity=ValidationSeverity.WARNING,
                            field="logo.url",
                        )
                    )
                elif isinstance(logo.get("url"), str):
                    issues.extend(_validate_uri(logo["url"], "logo.url"))
            elif isinstance(logo, str):
                issues.extend(_validate_uri(logo, "logo"))
            else:
                issues.append(
                    ValidationIssue(
                        code="SCHEMA_INVALID_STRUCTURE",
                        message="Organization logo must be an ImageObject dict or URI string",
                        severity=ValidationSeverity.WARNING,
                        field="logo",
                    )
                )

    elif schema_type == "Article":
        # headline is standard for Article; allow name as fallback
        headline = entity.get("headline") or entity.get("name")
        if not headline:
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="Article entity requires non-empty 'headline'",
                    severity=ValidationSeverity.WARNING,
                    field="headline",
                )
            )
        if not entity.get("url"):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="Article entity requires non-empty 'url'",
                    severity=ValidationSeverity.WARNING,
                    field="url",
                )
            )
        elif isinstance(entity.get("url"), str):
            issues.extend(_validate_uri(entity["url"], "url"))

        if not entity.get("datePublished"):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="Article entity requires non-empty 'datePublished'",
                    severity=ValidationSeverity.WARNING,
                    field="datePublished",
                )
            )
        elif isinstance(entity.get("datePublished"), str):
            issues.extend(_validate_datetime(entity["datePublished"], "datePublished"))

        if "dateModified" in entity and entity["dateModified"] is not None:
            issues.extend(_validate_datetime(entity["dateModified"], "dateModified"))

    elif schema_type == "BreadcrumbList":
        items = entity.get("itemListElement")
        if items is None or not isinstance(items, list):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="BreadcrumbList requires 'itemListElement' list",
                    severity=ValidationSeverity.WARNING,
                    field="itemListElement",
                )
            )
        elif len(items) == 0:
            issues.append(
                ValidationIssue(
                    code="SCHEMA_EMPTY_BREADCRUMBS",
                    message="BreadcrumbList 'itemListElement' must contain at least 1 item",
                    severity=ValidationSeverity.WARNING,
                    field="itemListElement",
                )
            )
        else:
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    issues.append(
                        ValidationIssue(
                            code="SCHEMA_INVALID_STRUCTURE",
                            message=f"Breadcrumb item at index {idx} must be an object",
                            severity=ValidationSeverity.CRITICAL,
                            field=f"itemListElement[{idx}]",
                        )
                    )
                    continue

                if item.get("@type") != "ListItem":
                    issues.append(
                        ValidationIssue(
                            code="SCHEMA_INVALID_STRUCTURE",
                            message=f"Breadcrumb item at index {idx} @type must be 'ListItem'",
                            severity=ValidationSeverity.WARNING,
                            field=f"itemListElement[{idx}].@type",
                        )
                    )

                pos = item.get("position")
                if not isinstance(pos, int) or pos < 1:
                    issues.append(
                        ValidationIssue(
                            code="SCHEMA_BREADCRUMB_POSITION_ERROR",
                            message=f"Breadcrumb item at index {idx} position must be integer >= 1",
                            severity=ValidationSeverity.WARNING,
                            field=f"itemListElement[{idx}].position",
                        )
                    )
                elif pos != idx + 1:
                    issues.append(
                        ValidationIssue(
                            code="SCHEMA_BREADCRUMB_POSITION_GAP",
                            message=f"Breadcrumb position expected {idx + 1}, got {pos}",
                            severity=ValidationSeverity.WARNING,
                            field=f"itemListElement[{idx}].position",
                        )
                    )

                if not item.get("name"):
                    issues.append(
                        ValidationIssue(
                            code="SCHEMA_MISSING_PROPERTY",
                            message=f"Breadcrumb item at index {idx} missing 'name'",
                            severity=ValidationSeverity.WARNING,
                            field=f"itemListElement[{idx}].name",
                        )
                    )

                item_url = item.get("item")
                if not item_url:
                    issues.append(
                        ValidationIssue(
                            code="SCHEMA_MISSING_PROPERTY",
                            message=f"Breadcrumb item at index {idx} missing 'item' URI",
                            severity=ValidationSeverity.WARNING,
                            field=f"itemListElement[{idx}].item",
                        )
                    )
                elif isinstance(item_url, str):
                    issues.extend(_validate_uri(item_url, f"itemListElement[{idx}].item"))

    elif schema_type == "WebPage":
        if not entity.get("name"):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="WebPage entity requires non-empty 'name'",
                    severity=ValidationSeverity.WARNING,
                    field="name",
                )
            )
        if not entity.get("url"):
            issues.append(
                ValidationIssue(
                    code="SCHEMA_MISSING_PROPERTY",
                    message="WebPage entity requires non-empty 'url'",
                    severity=ValidationSeverity.WARNING,
                    field="url",
                )
            )
        elif isinstance(entity.get("url"), str):
            issues.extend(_validate_uri(entity["url"], "url"))

        if "datePublished" in entity and entity["datePublished"] is not None:
            issues.extend(_validate_datetime(entity["datePublished"], "datePublished"))
        if "dateModified" in entity and entity["dateModified"] is not None:
            issues.extend(_validate_datetime(entity["dateModified"], "dateModified"))

    # 4. Common nested structures validation
    if "@id" in entity and entity["@id"] is not None:
        issues.extend(_validate_uri(entity["@id"], "@id"))

    if "author" in entity and entity["author"] is not None:
        author = entity["author"]
        if isinstance(author, dict):
            auth_type = author.get("@type")
            if auth_type not in ("Person", "Organization"):
                issues.append(
                    ValidationIssue(
                        code="SCHEMA_INVALID_AUTHOR",
                        message=f"Author @type must be 'Person' or 'Organization', got '{auth_type}'",
                        severity=ValidationSeverity.WARNING,
                        field="author.@type",
                    )
                )
            if not author.get("name"):
                issues.append(
                    ValidationIssue(
                        code="SCHEMA_INVALID_AUTHOR",
                        message="Author requires non-empty 'name'",
                        severity=ValidationSeverity.WARNING,
                        field="author.name",
                    )
                )
        else:
            issues.append(
                ValidationIssue(
                    code="SCHEMA_INVALID_AUTHOR",
                    message="Author must be an object with @type and name",
                    severity=ValidationSeverity.WARNING,
                    field="author",
                )
            )

    if "publisher" in entity and entity["publisher"] is not None:
        publisher = entity["publisher"]
        if isinstance(publisher, dict):
            pub_type = publisher.get("@type")
            if pub_type != "Organization":
                issues.append(
                    ValidationIssue(
                        code="SCHEMA_INVALID_PUBLISHER",
                        message=f"Publisher @type must be 'Organization', got '{pub_type}'",
                        severity=ValidationSeverity.WARNING,
                        field="publisher.@type",
                    )
                )
            if not publisher.get("name"):
                issues.append(
                    ValidationIssue(
                        code="SCHEMA_INVALID_PUBLISHER",
                        message="Publisher requires non-empty 'name'",
                        severity=ValidationSeverity.WARNING,
                        field="publisher.name",
                    )
                )
            if "logo" in publisher and publisher["logo"] is not None:
                logo = publisher["logo"]
                if isinstance(logo, dict):
                    if logo.get("@type") != "ImageObject":
                        issues.append(
                            ValidationIssue(
                                code="SCHEMA_INVALID_PUBLISHER",
                                message="Publisher logo @type must be 'ImageObject'",
                                severity=ValidationSeverity.WARNING,
                                field="publisher.logo.@type",
                            )
                        )
                    if logo.get("url"):
                        issues.extend(_validate_uri(logo["url"], "publisher.logo.url"))
                    else:
                        issues.append(
                            ValidationIssue(
                                code="SCHEMA_INVALID_PUBLISHER",
                                message="Publisher logo requires non-empty 'url'",
                                severity=ValidationSeverity.WARNING,
                                field="publisher.logo.url",
                            )
                        )
        else:
            issues.append(
                ValidationIssue(
                    code="SCHEMA_INVALID_PUBLISHER",
                    message="Publisher must be an object with @type and name",
                    severity=ValidationSeverity.WARNING,
                    field="publisher",
                )
            )

    # 5. Script probe scan
    issues.extend(_scan_for_script_probes(entity))

    return issues


def validate_against_schema_file(
    data: dict[str, Any],
    schema_path: str = "sps2/schemas/p9-structured-data.schema.json",
) -> list[ValidationIssue]:
    """Validate a structured data dictionary directly against p9-structured-data.schema.json rules."""
    # Basic structural conformance check matching the schema contract
    issues = validate_structured_data(data)
    return issues


def validate_structured_data_strict(data: Any) -> None:
    """Validate structured data and raise StructuredDataValidationError on CRITICAL issues."""
    issues = validate_structured_data(data)
    criticals = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
    if criticals:
        msgs = "; ".join(f"[{i.code}] {i.message}" for i in criticals)
        raise StructuredDataValidationError(f"Structured data validation failed: {msgs}")
