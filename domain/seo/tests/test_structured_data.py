"""Unit and security tests for P9 Structured Data (JSON-LD) Engine.

Covers REQ-P9-03:
- Schema.org JSON-LD generation for WebSite, Organization, Article, BreadcrumbList, WebPage
- Schema alignment with sps2/schemas/p9-structured-data.schema.json
- Required-field validation and error diagnostics
- Invalid URI, SSRF, and invalid date rejection
- Deterministic JSON serialization
- Script breakout prevention (</script> escaping) and HTML comment injection
- Unmutated content preservation through round-trip decoding
- HTML-boundary safe extraction with stdlib HTMLParser (UQ-P9-04)
- CMS Content entity integration
"""
from __future__ import annotations

import json
import os
import unittest
from html.parser import HTMLParser

from domain.cms.model import Content
from domain.seo.model import (
    ArticleSchema,
    AuthorInfo,
    BreadcrumbItem,
    BreadcrumbListSchema,
    OrganizationSchema,
    PublisherInfo,
    ValidationSeverity,
    WebPageSchema,
    WebSiteSchema,
)
from domain.seo.structured_data import (
    SUPPORTED_SCHEMA_TYPES,
    StructuredDataError,
    StructuredDataValidationError,
    build_article_schema,
    build_breadcrumb_list_schema,
    build_organization_schema,
    build_webpage_schema,
    build_website_schema,
    escape_json_ld_for_html,
    extract_json_ld_from_html,
    generate_article_structured_data,
    generate_breadcrumb_structured_data,
    generate_webpage_structured_data,
    generate_website_structured_data,
    render_json_ld_script_tag,
    serialize_json_ld,
    validate_against_schema_file,
    validate_structured_data,
    validate_structured_data_strict,
)


class TestStructuredDataGeneration(unittest.TestCase):
    """Test standard generation and data contract conformance."""

    def test_valid_website_generation(self) -> None:
        pub = PublisherInfo(name="SPS Corp", logo_url="https://example.com/logo.png")
        data = build_website_schema(
            name="Example Site",
            url="https://example.com",
            description="The premier test site",
            id="https://example.com/#website",
            publisher=pub,
        )
        self.assertEqual(data["@context"], "https://schema.org")
        self.assertEqual(data["@type"], "WebSite")
        self.assertEqual(data["name"], "Example Site")
        self.assertEqual(data["url"], "https://example.com")
        self.assertEqual(data["description"], "The premier test site")
        self.assertEqual(data["@id"], "https://example.com/#website")
        self.assertEqual(data["publisher"]["@type"], "Organization")

        issues = validate_structured_data(data)
        self.assertEqual(len(issues), 0, f"Expected 0 issues, got: {issues}")

    def test_valid_organization_generation(self) -> None:
        data = build_organization_schema(
            name="Acme Inc",
            url="https://acme.org",
            logo_url="https://acme.org/brand.png",
            description="Global widgets provider",
            id="https://acme.org/#org",
        )
        self.assertEqual(data["@context"], "https://schema.org")
        self.assertEqual(data["@type"], "Organization")
        self.assertEqual(data["name"], "Acme Inc")
        self.assertEqual(data["logo"]["@type"], "ImageObject")
        self.assertEqual(data["logo"]["url"], "https://acme.org/brand.png")

        issues = validate_structured_data(data)
        self.assertEqual(len(issues), 0)

    def test_valid_article_generation(self) -> None:
        author = AuthorInfo(name="Jane Doe", type="Person")
        publisher = PublisherInfo(name="Tech Weekly", logo_url="https://techweekly.com/logo.png")
        data = build_article_schema(
            headline="Understanding SEO 2.0",
            url="https://techweekly.com/seo-2-0",
            date_published="2026-10-06T12:00:00Z",
            date_modified="2026-10-06T15:30:00Z",
            description="Deep dive into modern technical search optimization",
            author=author,
            publisher=publisher,
            image="https://techweekly.com/images/seo.jpg",
            id="https://techweekly.com/seo-2-0#article",
        )
        self.assertEqual(data["@context"], "https://schema.org")
        self.assertEqual(data["@type"], "Article")
        self.assertEqual(data["headline"], "Understanding SEO 2.0")
        self.assertEqual(data["author"]["name"], "Jane Doe")
        self.assertEqual(data["author"]["@type"], "Person")
        self.assertEqual(data["publisher"]["name"], "Tech Weekly")
        self.assertEqual(data["image"], "https://techweekly.com/images/seo.jpg")

        issues = validate_structured_data(data)
        self.assertEqual(len(issues), 0)

    def test_valid_webpage_generation(self) -> None:
        data = build_webpage_schema(
            name="About Us",
            url="https://example.com/about",
            description="Our company history and mission",
            date_published="2026-01-01T00:00:00Z",
            id="https://example.com/about#webpage",
        )
        self.assertEqual(data["@context"], "https://schema.org")
        self.assertEqual(data["@type"], "WebPage")
        self.assertEqual(data["name"], "About Us")
        self.assertEqual(data["url"], "https://example.com/about")

        issues = validate_structured_data(data)
        self.assertEqual(len(issues), 0)

    def test_valid_breadcrumb_generation(self) -> None:
        trail = [
            ("Home", "https://example.com"),
            ("Products", "https://example.com/products"),
            ("Gadgets", "https://example.com/products/gadgets"),
        ]
        data = build_breadcrumb_list_schema(trail)
        self.assertEqual(data["@context"], "https://schema.org")
        self.assertEqual(data["@type"], "BreadcrumbList")
        elements = data["itemListElement"]
        self.assertEqual(len(elements), 3)

        self.assertEqual(elements[0]["position"], 1)
        self.assertEqual(elements[0]["name"], "Home")
        self.assertEqual(elements[0]["item"], "https://example.com")
        self.assertEqual(elements[0]["@type"], "ListItem")

        self.assertEqual(elements[2]["position"], 3)
        self.assertEqual(elements[2]["name"], "Gadgets")

        issues = validate_structured_data(data)
        self.assertEqual(len(issues), 0)


class TestSchemaContractAlignment(unittest.TestCase):
    """Test direct alignment with sps2/schemas/p9-structured-data.schema.json."""

    def test_schema_file_exists_and_conforms(self) -> None:
        schema_path = "sps2/schemas/p9-structured-data.schema.json"
        self.assertTrue(os.path.exists(schema_path), f"Schema file not found at {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_json = json.load(f)

        self.assertEqual(schema_json["$id"], "sps2.p9-structured-data/v1")
        allowed_types = set(schema_json["properties"]["@type"]["enum"])

        # Assert all 5 approved P9 types exist in the schema
        for approved in SUPPORTED_SCHEMA_TYPES:
            self.assertIn(approved, allowed_types)

    def test_all_approved_types_validate_cleanly(self) -> None:
        entities = [
            build_website_schema(name="Site", url="https://example.com"),
            build_organization_schema(name="Org", url="https://example.com"),
            build_article_schema(
                headline="Article",
                url="https://example.com/a",
                date_published="2026-10-06T00:00:00Z",
            ),
            build_breadcrumb_list_schema([("A", "https://example.com")]),
            build_webpage_schema(name="Page", url="https://example.com/p"),
        ]
        for ent in entities:
            issues = validate_against_schema_file(ent)
            self.assertEqual(len(issues), 0, f"Failed for {ent.get('@type')}: {issues}")


class TestValidationAndSecurityRejection(unittest.TestCase):
    """Test required fields, malformed entities, and dangerous payloads."""

    def test_missing_context_or_type(self) -> None:
        # Missing @context
        issues1 = validate_structured_data({"@type": "WebSite", "name": "A", "url": "https://a.com"})
        self.assertTrue(any(i.code == "SCHEMA_MISSING_CONTEXT" for i in issues1))

        # Invalid @context
        issues2 = validate_structured_data(
            {"@context": "http://evil.org", "@type": "WebSite", "name": "A", "url": "https://a.com"}
        )
        self.assertTrue(any(i.code == "SCHEMA_INVALID_CONTEXT" for i in issues2))

        # Missing @type
        issues3 = validate_structured_data({"@context": "https://schema.org", "name": "A", "url": "https://a.com"})
        self.assertTrue(any(i.code == "SCHEMA_MISSING_TYPE" for i in issues3))

    def test_unsupported_schema_type(self) -> None:
        issues = validate_structured_data(
            {"@context": "https://schema.org", "@type": "BogusType", "name": "A", "url": "https://a.com"}
        )
        self.assertTrue(any(i.code == "SCHEMA_UNSUPPORTED_TYPE" for i in issues))

    def test_missing_type_specific_required_properties(self) -> None:
        # Article without headline
        art1 = build_article_schema(headline="", url="https://a.com", date_published="2026-10-06T00:00:00Z")
        issues1 = validate_structured_data(art1)
        self.assertTrue(any(i.code == "SCHEMA_MISSING_PROPERTY" and i.field == "headline" for i in issues1))

        # Article without datePublished
        art2 = build_article_schema(headline="Title", url="https://a.com", date_published="")
        issues2 = validate_structured_data(art2)
        self.assertTrue(any(i.code == "SCHEMA_MISSING_PROPERTY" and i.field == "datePublished" for i in issues2))

        # WebSite without url
        site = build_website_schema(name="Site", url="")
        issues3 = validate_structured_data(site)
        self.assertTrue(any(i.code == "SCHEMA_MISSING_PROPERTY" and i.field == "url" for i in issues3))

    def test_invalid_and_unsafe_uri_schemes(self) -> None:
        dangerous_uris = [
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox(1)",
            "file:///etc/passwd",
        ]
        for bad_uri in dangerous_uris:
            data = build_webpage_schema(name="Bad", url=bad_uri)
            issues = validate_structured_data(data)
            self.assertTrue(
                any(i.code == "SCHEMA_UNSAFE_URI_SCHEME" for i in issues),
                f"Failed to flag dangerous URI: {bad_uri}",
            )

    def test_ssrf_private_and_loopback_uri_rejection(self) -> None:
        private_uris = [
            "http://127.0.0.1:8080/admin",
            "http://localhost/secret",
            "http://10.0.0.5/api",
            "http://169.254.169.254/latest/meta-data/",
        ]
        for priv_uri in private_uris:
            data = build_website_schema(name="Private", url=priv_uri)
            issues = validate_structured_data(data)
            self.assertTrue(
                any(i.code == "SCHEMA_URI_PRIVATE_IP_REJECTED" for i in issues),
                f"Failed to reject private URI: {priv_uri}",
            )

    def test_invalid_datetime_format(self) -> None:
        data = build_article_schema(
            headline="News",
            url="https://example.com/news",
            date_published="not-an-iso-date",
        )
        issues = validate_structured_data(data)
        self.assertTrue(any(i.code == "SCHEMA_INVALID_DATE_TIME" for i in issues))

    def test_nested_breadcrumb_validation(self) -> None:
        # Empty breadcrumbs
        empty_bc = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": []}
        issues1 = validate_structured_data(empty_bc)
        self.assertTrue(any(i.code == "SCHEMA_EMPTY_BREADCRUMBS" for i in issues1))

        # Position gap (starts at 2 instead of 1)
        bad_pos_bc = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 2, "name": "Item", "item": "https://example.com"},
            ],
        }
        issues2 = validate_structured_data(bad_pos_bc)
        self.assertTrue(any(i.code == "SCHEMA_BREADCRUMB_POSITION_GAP" for i in issues2))

    def test_strict_validator_raises_on_critical(self) -> None:
        bad_data = {"@context": "https://schema.org", "@type": "WebPage", "name": "Bad", "url": "javascript:void(0)"}
        with self.assertRaises(StructuredDataValidationError):
            validate_structured_data_strict(bad_data)


class TestDeterministicSerializationAndScriptBreakout(unittest.TestCase):
    """Test deterministic JSON-LD serialization and HTML boundary security."""

    def test_deterministic_serialization(self) -> None:
        data = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "url": "https://example.com",
            "name": "Determinism Test",
            "description": "Checking key ordering",
        }
        str1 = serialize_json_ld(data)
        str2 = serialize_json_ld(data)
        self.assertEqual(str1, str2)

        # Confirm sorted keys
        keys_in_output = [line.strip().split(":")[0].strip('"') for line in str1.splitlines() if ":" in line]
        self.assertEqual(keys_in_output, sorted(keys_in_output))

    def test_script_breakout_closing_tag_neutralized(self) -> None:
        malicious_headline = "</script><script>alert('xss')</script>"
        data = build_article_schema(
            headline=malicious_headline,
            url="https://example.com/article",
            date_published="2026-10-06T12:00:00Z",
        )
        tag = render_json_ld_script_tag(data)

        # 1. Assert unescaped </script> NEVER appears inside the script content body
        # Extract content between outer <script> and </script>
        script_open = '<script type="application/ld+json">'
        script_close = '</script>'
        self.assertTrue(tag.startswith(script_open))
        self.assertTrue(tag.endswith(script_close))

        inner = tag[len(script_open):-len(script_close)].strip()
        self.assertNotIn("</script>", inner.lower())
        self.assertIn(r"<\/script>", inner)

        # 2. Assert HTML parser treats this as a single script block without early breakout
        class ScriptCounter(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.script_count = 0
            def handle_starttag(self, tag, attrs):
                if tag.lower() == "script":
                    self.script_count += 1

        parser = ScriptCounter()
        parser.feed(tag)
        self.assertEqual(parser.script_count, 1, "Early script breakout detected: multiple script tags parsed!")

        # 3. Assert json.loads preserves the unmutated stored content with 100% fidelity
        decoded = json.loads(inner)
        self.assertEqual(decoded["headline"], malicious_headline)

    def test_script_breakout_variations(self) -> None:
        probes = [
            '</SCRIPT><script src="https://evil.com/x.js"></script>',
            '</script attr="malicious">',
            '<!-- <script>alert("comment-breakout")</script> -->',
            '</sCrIpT >',
            'Multiple </script> </script> probes',
        ]
        for probe in probes:
            raw_json = json.dumps({"test": probe}, sort_keys=True)
            escaped = escape_json_ld_for_html(raw_json)

            self.assertNotIn("</script>", escaped.lower())
            self.assertNotIn("<!--", escaped)

            # Assert decoded string matches original probe exactly
            decoded = json.loads(escaped)
            self.assertEqual(decoded["test"], probe, f"Content mutated for probe: {probe}")

    def test_html_boundary_round_trip_with_html_parser(self) -> None:
        original = build_article_schema(
            headline="A <Safe> & 'Interesting' Article: </script><script>alert(1)</script>",
            url="https://example.com/article-1",
            date_published="2026-10-06T10:00:00Z",
            description="Discussion on <!-- HTML comments --> and tags",
        )
        script_tag = render_json_ld_script_tag(original)
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<title>Test Page</title>
{script_tag}
</head>
<body><h1>Hello World</h1></body>
</html>"""

        extracted = extract_json_ld_from_html(full_html)
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0]["headline"], original["headline"])
        self.assertEqual(extracted[0]["description"], original["description"])
        self.assertEqual(extracted[0]["url"], original["url"])


class TestCMSContentIntegration(unittest.TestCase):
    """Test generating structured data from CMS Content entities."""

    def test_article_structured_data_from_cms_content(self) -> None:
        content = Content(
            type_id="type_blog_post",
            title="Building High Performance SEO Engines",
            body="Comprehensive tutorial covering robots.txt, XML sitemaps, and Schema.org.",
            author_id="author_alice",
        )
        content.status = "published"
        content.published_at = "2026-10-06T09:00:00Z"

        article_ld = generate_article_structured_data(
            content=content,
            base_url="https://example.com",
            slug="/blog/building-seo-engines",
            publisher=PublisherInfo(name="SPS Publication"),
        )
        self.assertEqual(article_ld["@type"], "Article")
        self.assertEqual(article_ld["headline"], "Building High Performance SEO Engines")
        self.assertEqual(article_ld["url"], "https://example.com/blog/building-seo-engines")
        self.assertEqual(article_ld["datePublished"], "2026-10-06T09:00:00Z")
        self.assertEqual(article_ld["author"]["name"], "author_alice")
        self.assertEqual(article_ld["publisher"]["name"], "SPS Publication")

        issues = validate_structured_data(article_ld)
        self.assertEqual(len(issues), 0)

    def test_webpage_structured_data_from_cms_content(self) -> None:
        content = Content(
            type_id="type_landing_page",
            title="Company Homepage",
            body="Welcome to SPS 2.0 platform.",
        )
        page_ld = generate_webpage_structured_data(
            content=content,
            base_url="https://example.com",
            slug="/",
        )
        self.assertEqual(page_ld["@type"], "WebPage")
        self.assertEqual(page_ld["name"], "Company Homepage")
        self.assertEqual(page_ld["url"], "https://example.com/")

        issues = validate_structured_data(page_ld)
        self.assertEqual(len(issues), 0)


if __name__ == "__main__":
    unittest.main()
