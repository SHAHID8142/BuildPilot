"""Tests for P9 SEO crawling, indexing, robots.txt, and XML sitemaps engine."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from framework.domain.cms.model import Content
from framework.domain.seo.indexing import (
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
from framework.domain.seo.model import (
    RobotsConfig,
    RobotsGroup,
    SitemapEntry,
    SitemapModel,
)


class TestSEOIndexingEngine(unittest.TestCase):
    """Test suite for REQ-P9-02 crawling, indexing, and sitemaps engine."""

    def setUp(self) -> None:
        schema_path = Path(__file__).resolve().parents[4] / "framework" / "sps2" / "schemas" / "p9-sitemap.schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    # ------------------------------------------------------------------
    # 1. Robots.txt Generation & Parsing Tests
    # ------------------------------------------------------------------

    def test_robots_txt_generation_deterministic(self) -> None:
        config = RobotsConfig(
            groups=[
                RobotsGroup(
                    user_agent="Googlebot",
                    allow=["/public", "/articles"],
                    disallow=["/private"],
                    crawl_delay=2,
                ),
                RobotsGroup(
                    user_agent="*",
                    allow=["/"],
                    disallow=["/admin", "/draft", "/preview"],
                ),
            ],
            sitemaps=["https://example.com/sitemap.xml", "https://example.com/sitemap2.xml"],
            host="example.com",
        )

        txt1 = generate_robots_txt(config)
        txt2 = generate_robots_txt(config)
        self.assertEqual(txt1, txt2)

        # '*' group appears first
        self.assertTrue(txt1.startswith("User-agent: *\n"))
        self.assertIn("Allow: /\n", txt1)
        self.assertIn("Disallow: /admin\n", txt1)
        self.assertIn("User-agent: Googlebot\n", txt1)
        self.assertIn("Crawl-delay: 2\n", txt1)
        self.assertIn("Sitemap: https://example.com/sitemap.xml\n", txt1)
        self.assertIn("Host: example.com\n", txt1)

    def test_robots_txt_parsing_and_matching(self) -> None:
        raw_robots = """
        # Robots.txt file for testing
        User-agent: Googlebot
        Disallow: /no-google/
        Allow: /no-google/public/

        User-agent: *
        Disallow: /secret/
        Disallow: /admin/
        Allow: /admin/login/
        Crawl-delay: 5

        Sitemap: https://example.com/sitemap.xml
        Host: example.com
        """

        parsed = parse_robots_txt(raw_robots)
        self.assertEqual(len(parsed.groups), 2)
        self.assertEqual(parsed.sitemaps, ["https://example.com/sitemap.xml"])
        self.assertEqual(parsed.host, "example.com")

        # RFC 9309 Path Matching rules
        # Googlebot specific rules
        self.assertFalse(is_path_allowed_by_robots(parsed, "/no-google/data", user_agent="Googlebot"))
        self.assertTrue(is_path_allowed_by_robots(parsed, "/no-google/public/page", user_agent="Googlebot"))

        # Fallback to '*' rules for other agents
        self.assertFalse(is_path_allowed_by_robots(parsed, "/secret/doc", user_agent="Bingbot"))
        self.assertFalse(is_path_allowed_by_robots(parsed, "/admin/dashboard", user_agent="Bingbot"))
        # Longest match wins: /admin/login/ (len 13) beats /admin/ (len 7)
        self.assertTrue(is_path_allowed_by_robots(parsed, "/admin/login/form", user_agent="Bingbot"))
        self.assertTrue(is_path_allowed_by_robots(parsed, "/other/page", user_agent="Bingbot"))

    # ------------------------------------------------------------------
    # 2. Sitemap Generation & Schema Alignment
    # ------------------------------------------------------------------

    def test_sitemap_model_and_xml_generation(self) -> None:
        entries = [
            SitemapEntry(loc="https://example.com/b", changefreq="daily", priority=0.8),
            SitemapEntry(loc="https://example.com/a", lastmod="2026-10-06T12:00:00Z", priority=1.0),
        ]

        model = build_sitemap_model(entries, generated_at="2026-10-06T12:00:00Z")
        self.assertEqual(model.total_urls, 2)
        self.assertEqual(model.entries[0].loc, "https://example.com/a")  # Deterministic sorting
        self.assertEqual(model.entries[1].loc, "https://example.com/b")

        # Verify dictionary schema alignment
        d = model.to_dict()
        self.assertEqual(d["total_urls"], 2)
        self.assertEqual(d["generated_at"], "2026-10-06T12:00:00Z")
        self.assertEqual(d["sitemap_index"], False)

        xml = generate_sitemap_xml(model)
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        self.assertIn('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', xml)
        self.assertIn("<loc>https://example.com/a</loc>", xml)
        self.assertIn("<lastmod>2026-10-06T12:00:00Z</lastmod>", xml)
        self.assertIn("<priority>1.0</priority>", xml)
        self.assertIn("<changefreq>daily</changefreq>", xml)

    def test_sitemap_index_xml_generation(self) -> None:
        model = SitemapModel(
            sitemap_index=True,
            sitemap_files=["https://example.com/sitemap-1.xml", "https://example.com/sitemap-2.xml"],
            generated_at="2026-10-06T12:00:00Z",
            total_urls=2,
        )

        xml = generate_sitemap_xml(model)
        self.assertIn('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', xml)
        self.assertIn("<loc>https://example.com/sitemap-1.xml</loc>", xml)
        self.assertIn("<loc>https://example.com/sitemap-2.xml</loc>", xml)

    def test_sitemap_url_limits(self) -> None:
        # Exceeding 50,000 URLs raises SitemapLimitError
        large_entries = [SitemapEntry(loc=f"https://example.com/{i}") for i in range(50001)]
        with self.assertRaises(SitemapLimitError):
            build_sitemap_model(large_entries)

    def test_sitemap_rejects_invalid_and_ssrf_urls(self) -> None:
        # Relative URL
        with self.assertRaises(IndexingError):
            build_sitemap_model([SitemapEntry(loc="/relative/path")])

        # Non-HTTP scheme
        with self.assertRaises(IndexingError):
            build_sitemap_model([SitemapEntry(loc="javascript:alert(1)")])

        # SSRF private IP
        with self.assertRaises(IndexingError):
            build_sitemap_model([SitemapEntry(loc="http://127.0.0.1:8080/admin")])

        with self.assertRaises(IndexingError):
            build_sitemap_model([SitemapEntry(loc="http://169.254.169.254/latest/meta-data")])

    # ------------------------------------------------------------------
    # 3. Safe XML Processing & XXE Defense (Threat Model §5.5)
    # ------------------------------------------------------------------

    def test_safe_xml_parsing_normal(self) -> None:
        valid_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url>
            <loc>https://example.com/page1</loc>
            <lastmod>2026-10-06T10:00:00Z</lastmod>
            <changefreq>monthly</changefreq>
            <priority>0.7</priority>
          </url>
        </urlset>
        """
        entries = parse_sitemap_xml(valid_xml)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].loc, "https://example.com/page1")
        self.assertEqual(entries[0].changefreq, "monthly")
        self.assertEqual(entries[0].priority, 0.7)

    def test_safe_xml_parsing_rejects_doctype_and_xxe(self) -> None:
        """Threat Model §5.5: DOCTYPE and ENTITY declarations are strictly rejected."""
        xxe_payloads = [
            """<?xml version="1.0"?>
            <!DOCTYPE foo [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
              <url><loc>&xxe;</loc></url>
            </urlset>""",
            """<!doctype sitemap [ <!entity test "value"> ]><urlset><url><loc>https://example.com/</loc></url></urlset>""",
            """<?xml version="1.0"?><!DOCTYPE urlset SYSTEM "http://127.0.0.1/evil.dtd"><urlset></urlset>""",
        ]
        for payload in xxe_payloads:
            with self.assertRaises(SitemapSecurityError, msg=f"Failed to reject: {payload}"):
                parse_sitemap_xml(payload)

            with self.assertRaises(SitemapSecurityError, msg=f"Failed to reject index: {payload}"):
                parse_sitemap_index_xml(payload)

    def test_safe_xml_parsing_rejects_malformed_xml(self) -> None:
        # Invalid XML structure
        with self.assertRaises(SitemapParseError):
            parse_sitemap_xml("<urlset><url><loc>https://example.com</loc></url>")

        # Missing loc tag
        with self.assertRaises(SitemapParseError):
            parse_sitemap_xml("<urlset><url><priority>1.0</priority></url></urlset>")

        # Invalid root tag
        with self.assertRaises(SitemapParseError):
            parse_sitemap_xml("<wrongroot><url><loc>https://example.com</loc></url></wrongroot>")

    # ------------------------------------------------------------------
    # 4. CMS Content Model Integration (Threat Model §5.9)
    # ------------------------------------------------------------------

    def test_cms_published_filtering(self) -> None:
        """Threat Model §5.9: Only published content is included in sitemaps; drafts/archived excluded."""
        item_published_1 = Content(
            type_id="post",
            title="Published Post One",
            body="Public body.",
            author_id="admin",
        )
        item_published_1.status = "published"

        item_published_2 = Content(
            type_id="post",
            title="Published Post Two",
            body="Public body two.",
            author_id="admin",
        )
        item_published_2.status = "published"

        item_draft = Content(
            type_id="post",
            title="Draft Confidential Post",
            body="Confidential content.",
            author_id="admin",
        )
        item_draft.status = "draft"

        item_archived = Content(
            type_id="post",
            title="Archived Old Post",
            body="Old content.",
            author_id="admin",
        )
        item_archived.status = "archived"

        items = [item_published_1, item_draft, item_published_2, item_archived]

        sitemap = generate_sitemap_from_cms_items(items=items, base_url="https://example.com")

        # Total entries must be exactly 2 (only the published items)
        self.assertEqual(sitemap.total_urls, 2)
        locs = [e.loc for e in sitemap.entries]
        self.assertIn(f"https://example.com/{item_published_1.id}", locs)
        self.assertIn(f"https://example.com/{item_published_2.id}", locs)
        self.assertNotIn(f"https://example.com/{item_draft.id}", locs)
        self.assertNotIn(f"https://example.com/{item_archived.id}", locs)


if __name__ == "__main__":
    unittest.main()
