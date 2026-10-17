"""Tests for P9 SEO domain models."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from framework.domain.seo.model import (
    OpenGraph,
    RobotsDirectives,
    SEOMetadata,
    TwitterCard,
    ValidationIssue,
    ValidationSeverity,
)


class TestSEOModel(unittest.TestCase):
    """Test suite for SEO domain models and serialization."""

    def setUp(self) -> None:
        schema_path = Path(__file__).resolve().parents[4] / "framework" / "sps2" / "schemas" / "p9-metadata.schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def test_basic_metadata_to_dict(self) -> None:
        meta = SEOMetadata(
            title="Home Page Title Example",
            description="A comprehensive meta description example that describes the home page content thoroughly.",
            canonical_url="https://example.com/",
            robots=RobotsDirectives(index=True, follow=True),
        )
        d = meta.to_dict()
        self.assertEqual(d["title"], "Home Page Title Example")
        self.assertEqual(d["canonical_url"], "https://example.com/")
        self.assertEqual(d["robots"]["index"], True)
        self.assertEqual(d["robots"]["follow"], True)
        self.assertEqual(d["charset"], "UTF-8")
        self.assertEqual(d["viewport"], "width=device-width, initial-scale=1")
        self.assertNotIn("open_graph", d)
        self.assertNotIn("twitter_card", d)

    def test_full_metadata_to_dict_and_roundtrip(self) -> None:
        og = OpenGraph(
            title="Article OG Title",
            description="Article OG Description",
            url="https://example.com/article",
            type="article",
            image="https://example.com/og.jpg",
            site_name="Example Site",
            locale="en_US",
        )
        tw = TwitterCard(
            card="summary_large_image",
            title="Article Twitter Title",
            description="Article Twitter Description",
            image="https://example.com/tw.jpg",
            site="@example",
            creator="@author",
        )
        robots = RobotsDirectives(
            index=True,
            follow=True,
            noarchive=True,
            nosnippet=False,
            max_snippet=100,
            max_image_preview="large",
        )
        meta = SEOMetadata(
            title="Complete Article Title",
            description="Complete article description with sufficient length for optimal search results.",
            canonical_url="https://example.com/article",
            robots=robots,
            open_graph=og,
            twitter_card=tw,
        )

        d = meta.to_dict()
        self.assertEqual(d["open_graph"]["site_name"], "Example Site")
        self.assertEqual(d["twitter_card"]["card"], "summary_large_image")
        self.assertEqual(d["robots"]["noarchive"], True)
        self.assertEqual(d["robots"]["max_snippet"], 100)

        # Roundtrip
        reconstructed = SEOMetadata.from_dict(d)
        self.assertEqual(reconstructed.title, meta.title)
        self.assertEqual(reconstructed.canonical_url, meta.canonical_url)
        self.assertIsNotNone(reconstructed.open_graph)
        self.assertEqual(reconstructed.open_graph.site_name, "Example Site")
        self.assertIsNotNone(reconstructed.twitter_card)
        self.assertEqual(reconstructed.twitter_card.creator, "@author")
        self.assertTrue(reconstructed.robots.noarchive)

    def test_robots_directive_string_generation(self) -> None:
        robots1 = RobotsDirectives(index=True, follow=True)
        self.assertEqual(robots1.to_directive_string(), "index, follow")

        robots2 = RobotsDirectives(index=False, follow=False)
        self.assertEqual(robots2.to_directive_string(), "noindex, nofollow")

        robots3 = RobotsDirectives(
            index=True,
            follow=True,
            noarchive=True,
            nosnippet=True,
            max_snippet=50,
            max_image_preview="large",
            max_video_preview=10,
        )
        directive_str = robots3.to_directive_string()
        self.assertIn("index, follow", directive_str)
        self.assertIn("noarchive", directive_str)
        self.assertIn("nosnippet", directive_str)
        self.assertIn("max-snippet:50", directive_str)
        self.assertIn("max-image-preview:large", directive_str)
        self.assertIn("max-video-preview:10", directive_str)

    def test_validation_issue_representation(self) -> None:
        issue = ValidationIssue(
            code="TITLE_TOO_SHORT",
            message="Title has only 10 chars",
            severity=ValidationSeverity.WARNING,
            field="title",
        )
        d = issue.to_dict()
        self.assertEqual(d["code"], "TITLE_TOO_SHORT")
        self.assertEqual(d["severity"], "WARNING")
        self.assertEqual(d["field"], "title")


if __name__ == "__main__":
    unittest.main()
