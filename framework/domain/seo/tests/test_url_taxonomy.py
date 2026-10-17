"""Unit and security tests for P9 URL Architecture, Redirect Taxonomy & Pagination Engine.

Covers REQ-P9-06:
- URL taxonomy and slug normalization (lowercase, hyphens, slashes)
- Pure functional analysis without CMS content or stored URL mutation
- Open-redirect security validation (relative allowlist, canonical domain check, SSRF defense)
- Dangerous scheme and protocol-relative redirect rejection
- Redirect graph analysis: self-loops, circular loops, multi-hop chains
- HTTP redirect status code validation (301, 302, 307, 308)
- Zero network crawling / strictly static reference analysis
- Pagination canonicalization analysis (rel="prev"/rel="next" vs canonical signals)
- Safe HTML parsing of pagination link elements
- Deterministic output serialization
"""
from __future__ import annotations

import unittest

from framework.domain.seo.model import (
    PaginationSignals,
    RedirectRule,
    ValidationSeverity,
)
from framework.domain.seo.url_taxonomy import (
    PaginationHTMLParser,
    analyze_pagination_html,
    analyze_redirect_graph,
    normalize_slug,
    validate_pagination_signals,
    validate_url_taxonomy,
)


class TestSlugNormalization(unittest.TestCase):
    """Test deterministic slug and URL path normalization."""

    def test_normalize_slug_basic(self) -> None:
        self.assertEqual(normalize_slug("Hello World"), "/hello-world")
        self.assertEqual(normalize_slug("about-us"), "/about-us")
        self.assertEqual(normalize_slug("/pricing/"), "/pricing")

    def test_normalize_slug_spaces_and_encoded_spaces(self) -> None:
        self.assertEqual(normalize_slug("case%20studies"), "/case-studies")
        self.assertEqual(normalize_slug("news & updates"), "/news-updates")

    def test_normalize_slug_underscores(self) -> None:
        self.assertEqual(normalize_slug("user_profile_settings"), "/user-profile-settings")

    def test_normalize_slug_collapsing(self) -> None:
        self.assertEqual(normalize_slug("blog///my--post__name"), "/blog/my-post-name")

    def test_normalize_slug_trailing_slash_policy(self) -> None:
        # Default: trailing_slash=False
        self.assertEqual(normalize_slug("blog/post/", trailing_slash=False), "/blog/post")
        # trailing_slash=True
        self.assertEqual(normalize_slug("blog/post", trailing_slash=True), "/blog/post/")
        # Root path "/" is always "/"
        self.assertEqual(normalize_slug("/", trailing_slash=False), "/")
        self.assertEqual(normalize_slug("/", trailing_slash=True), "/")
        self.assertEqual(normalize_slug("", trailing_slash=True), "/")

    def test_normalize_slug_illegal_characters_stripped(self) -> None:
        self.assertEqual(normalize_slug("page!@$%^&*()test"), "/pagetest")


class TestUrlTaxonomyValidation(unittest.TestCase):
    """Test URL taxonomy quality and architectural rule checks."""

    def test_valid_clean_url(self) -> None:
        issues = validate_url_taxonomy("/blog/modern-architecture", trailing_slash=False)
        serious = [i for i in issues if i.severity != ValidationSeverity.INFO]
        self.assertEqual(len(serious), 0)

    def test_empty_url_is_critical(self) -> None:
        issues = validate_url_taxonomy("")
        self.assertTrue(any(i.code == "URL_EMPTY" and i.severity == ValidationSeverity.CRITICAL for i in issues))

        issues_ws = validate_url_taxonomy("   ")
        self.assertTrue(any(i.code == "URL_EMPTY" for i in issues_ws))

    def test_uppercase_characters_detected(self) -> None:
        issues = validate_url_taxonomy("/Products/Item-1")
        self.assertTrue(any(i.code == "URL_NOT_LOWERCASE" for i in issues))

    def test_underscores_detected(self) -> None:
        issues = validate_url_taxonomy("/blog/my_first_post")
        self.assertTrue(any(i.code == "URL_CONTAINS_UNDERSCORE" for i in issues))

    def test_spaces_detected(self) -> None:
        issues = validate_url_taxonomy("/blog/my first post")
        self.assertTrue(any(i.code == "URL_CONTAINS_SPACES" for i in issues))

        issues_enc = validate_url_taxonomy("/blog/my%20first%20post")
        self.assertTrue(any(i.code == "URL_CONTAINS_SPACES" for i in issues_enc))

    def test_consecutive_hyphens_detected(self) -> None:
        issues = validate_url_taxonomy("/blog/my--post")
        self.assertTrue(any(i.code == "URL_CONSECUTIVE_HYPHENS" for i in issues))

    def test_special_characters_detected(self) -> None:
        issues = validate_url_taxonomy("/blog/post@2026!")
        self.assertTrue(any(i.code == "URL_SPECIAL_CHARACTERS" for i in issues))

    def test_trailing_slash_policy_enforcement(self) -> None:
        # Site expects trailing slash:
        issues_missing = validate_url_taxonomy("/blog/post", trailing_slash=True)
        self.assertTrue(any(i.code == "URL_TRAILING_SLASH_INCONSISTENT" for i in issues_missing))

        # Site expects NO trailing slash:
        issues_extra = validate_url_taxonomy("/blog/post/", trailing_slash=False)
        self.assertTrue(any(i.code == "URL_TRAILING_SLASH_INCONSISTENT" for i in issues_extra))


class TestRedirectSecurity(unittest.TestCase):
    """Test open-redirect, SSRF, and dangerous-scheme defenses."""

    def test_relative_destinations_allowed(self) -> None:
        rules = [RedirectRule(source="/old-path", target="/new-path", status_code=301)]
        res = analyze_redirect_graph(rules)
        self.assertEqual(res.valid_count, 1)
        self.assertEqual(len(res.issues), 0)

    def test_protocol_relative_open_redirect_rejected(self) -> None:
        rules = [RedirectRule(source="/login", target="//evil.com/phish", status_code=302)]
        res = analyze_redirect_graph(rules)
        self.assertEqual(res.valid_count, 0)
        self.assertTrue(any(i.code == "REDIRECT_OPEN_REDIRECT" and i.severity == ValidationSeverity.CRITICAL for i in res.issues))

    def test_unsafe_schemes_rejected(self) -> None:
        unsafe_targets = [
            "javascript:stealCookies()",
            "data:text/html,<script>alert(1)</script>",
            "file:///etc/passwd",
            "vbscript:msgbox(1)",
        ]
        for target in unsafe_targets:
            rules = [RedirectRule(source="/test", target=target, status_code=301)]
            res = analyze_redirect_graph(rules)
            self.assertEqual(res.valid_count, 0)
            self.assertTrue(
                any(i.code == "REDIRECT_UNSAFE_SCHEME" for i in res.issues),
                f"Target '{target}' did not trigger REDIRECT_UNSAFE_SCHEME",
            )

    def test_external_redirect_without_canonical_domain_or_allowlist_rejected(self) -> None:
        rules = [RedirectRule(source="/partner", target="https://other.com/portal", status_code=302)]
        res = analyze_redirect_graph(rules)
        self.assertEqual(res.valid_count, 0)
        self.assertTrue(any(i.code == "REDIRECT_OPEN_REDIRECT" for i in res.issues))

    def test_external_redirect_matching_canonical_domain_allowed(self) -> None:
        rules = [
            RedirectRule(
                source="/about-legacy",
                target="https://example.com/about",
                status_code=301,
            )
        ]
        res = analyze_redirect_graph(rules, canonical_domain="https://example.com")
        self.assertEqual(res.valid_count, 1)
        serious = [i for i in res.issues if i.severity == ValidationSeverity.CRITICAL]
        self.assertEqual(len(serious), 0)

    def test_external_redirect_mismatching_canonical_domain_rejected(self) -> None:
        rules = [
            RedirectRule(
                source="/outbound",
                target="https://phishing.org/login",
                status_code=302,
            )
        ]
        res = analyze_redirect_graph(rules, canonical_domain="https://example.com")
        self.assertEqual(res.valid_count, 0)
        self.assertTrue(any(i.code == "REDIRECT_OPEN_REDIRECT" for i in res.issues))

    def test_external_redirect_with_allow_external_flag_allowed(self) -> None:
        rules = [
            RedirectRule(
                source="/partner-link",
                target="https://trusted-partner.com/welcome",
                status_code=302,
                allow_external=True,
            )
        ]
        res = analyze_redirect_graph(rules, canonical_domain="https://example.com")
        self.assertEqual(res.valid_count, 1)

    def test_ssrf_private_and_loopback_destinations_rejected(self) -> None:
        private_targets = [
            "http://127.0.0.1/admin",
            "http://localhost:8080/metrics",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.0.0.5/internal",
            "http://192.168.1.1/router",
        ]
        for target in private_targets:
            rules = [RedirectRule(source="/admin-portal", target=target, status_code=302, allow_external=True)]
            res = analyze_redirect_graph(rules)
            self.assertEqual(res.valid_count, 0)
            self.assertTrue(
                any(i.code == "REDIRECT_PRIVATE_IP_REJECTED" for i in res.issues),
                f"Target '{target}' did not trigger REDIRECT_PRIVATE_IP_REJECTED",
            )

    def test_empty_target_rejected(self) -> None:
        rules = [RedirectRule(source="/empty", target="", status_code=301)]
        res = analyze_redirect_graph(rules)
        self.assertEqual(res.valid_count, 0)
        self.assertTrue(any(i.code == "REDIRECT_TARGET_EMPTY" for i in res.issues))


class TestRedirectGraphAnalysis(unittest.TestCase):
    """Test static directed-graph analysis for loops, chains, and status semantics."""

    def test_valid_redirect_status_codes(self) -> None:
        for code in (301, 302, 307, 308):
            rules = [RedirectRule(source=f"/old-{code}", target=f"/new-{code}", status_code=code)]
            res = analyze_redirect_graph(rules)
            self.assertEqual(res.valid_count, 1, f"Status {code} should be valid")

    def test_invalid_redirect_status_codes_rejected(self) -> None:
        for code in (200, 300, 304, 404, 500):
            rules = [RedirectRule(source="/old", target="/new", status_code=code)]
            res = analyze_redirect_graph(rules)
            self.assertEqual(res.valid_count, 0)
            self.assertTrue(any(i.code == "REDIRECT_INVALID_STATUS_CODE" for i in res.issues))

    def test_direct_self_loop_detected(self) -> None:
        rules = [RedirectRule(source="/same-page", target="/same-page", status_code=301)]
        res = analyze_redirect_graph(rules)
        self.assertEqual(res.valid_count, 0)
        self.assertTrue(any(i.code == "REDIRECT_SELF_LOOP" for i in res.issues))

    def test_self_loop_with_trailing_slash_difference_detected(self) -> None:
        rules = [RedirectRule(source="/same-page/", target="/same-page", status_code=301)]
        res = analyze_redirect_graph(rules)
        self.assertEqual(res.valid_count, 0)
        self.assertTrue(any(i.code == "REDIRECT_SELF_LOOP" for i in res.issues))

    def test_two_hop_circular_loop_detected(self) -> None:
        rules = [
            RedirectRule(source="/page-a", target="/page-b", status_code=301),
            RedirectRule(source="/page-b", target="/page-a", status_code=301),
        ]
        res = analyze_redirect_graph(rules)
        self.assertGreater(res.loop_count, 0)
        self.assertTrue(any(i.code == "REDIRECT_LOOP_DETECTED" for i in res.issues))

    def test_multi_hop_circular_loop_detected(self) -> None:
        rules = [
            RedirectRule(source="/page-a", target="/page-b", status_code=301),
            RedirectRule(source="/page-b", target="/page-c", status_code=301),
            RedirectRule(source="/page-c", target="/page-a", status_code=301),
        ]
        res = analyze_redirect_graph(rules)
        self.assertGreater(res.loop_count, 0)
        self.assertTrue(any(i.code == "REDIRECT_LOOP_DETECTED" for i in res.issues))

    def test_multi_hop_redirect_chain_detected(self) -> None:
        rules = [
            RedirectRule(source="/page-1", target="/page-2", status_code=301),
            RedirectRule(source="/page-2", target="/page-3", status_code=301),
        ]
        res = analyze_redirect_graph(rules)
        self.assertEqual(res.chain_count, 1)
        self.assertTrue(any(i.code == "REDIRECT_CHAIN_DETECTED" for i in res.issues))
        chain = next(c for c in res.chains if c.start_url == "/page-1")
        self.assertEqual(chain.hop_count, 2)
        self.assertEqual(chain.final_target, "/page-3")
        self.assertFalse(chain.is_loop)

    def test_dict_input_support_and_serialization(self) -> None:
        raw_rules = [
            {"source": "/old-docs", "target": "/docs/v2", "status_code": 301},
            {"source": "/docs/v2", "target": "/docs/v3", "status_code": 308},
        ]
        res = analyze_redirect_graph(raw_rules)
        self.assertEqual(res.total_rules, 2)
        self.assertEqual(res.valid_count, 2)
        self.assertEqual(res.chain_count, 1)

        d = res.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["total_rules"], 2)
        self.assertEqual(len(d["chains"]), 2)  # /old-docs has 2 hops, /docs/v2 has 1 hop


class TestPaginationAnalysis(unittest.TestCase):
    """Test paginated collection signals and canonicalization consistency."""

    def test_valid_first_page_signals(self) -> None:
        signals = PaginationSignals(
            page=1,
            total_pages=5,
            current_url="/blog",
            canonical_url="/blog",
            prev_url=None,
            next_url="/blog/page/2",
            strategy="self",
        )
        issues = validate_pagination_signals(signals)
        serious = [i for i in issues if i.severity != ValidationSeverity.INFO]
        self.assertEqual(len(serious), 0)

    def test_first_page_with_prev_url_warns(self) -> None:
        signals = PaginationSignals(
            page=1,
            total_pages=5,
            current_url="/blog",
            canonical_url="/blog",
            prev_url="/blog/page/0",
            next_url="/blog/page/2",
        )
        issues = validate_pagination_signals(signals)
        self.assertTrue(any(i.code == "PAGINATION_PREV_ON_FIRST_PAGE" for i in issues))

    def test_page_two_missing_prev_url_warns(self) -> None:
        signals = PaginationSignals(
            page=2,
            total_pages=5,
            current_url="/blog/page/2",
            canonical_url="/blog/page/2",
            prev_url=None,
            next_url="/blog/page/3",
        )
        issues = validate_pagination_signals(signals)
        self.assertTrue(any(i.code == "PAGINATION_MISSING_PREV" for i in issues))

    def test_page_exceeding_total_pages_warns(self) -> None:
        signals = PaginationSignals(
            page=6,
            total_pages=5,
            current_url="/blog/page/6",
            prev_url="/blog/page/5",
        )
        issues = validate_pagination_signals(signals)
        self.assertTrue(any(i.code == "PAGINATION_PAGE_EXCEEDS_TOTAL" for i in issues))

    def test_last_page_with_next_url_warns(self) -> None:
        signals = PaginationSignals(
            page=5,
            total_pages=5,
            current_url="/blog/page/5",
            prev_url="/blog/page/4",
            next_url="/blog/page/6",
        )
        issues = validate_pagination_signals(signals)
        self.assertTrue(any(i.code == "PAGINATION_NEXT_ON_LAST_PAGE" for i in issues))

    def test_circular_prev_link_is_critical(self) -> None:
        signals = PaginationSignals(
            page=2,
            current_url="/blog/page/2",
            prev_url="/blog/page/2",
        )
        issues = validate_pagination_signals(signals)
        self.assertTrue(any(i.code == "PAGINATION_CIRCULAR_LINK" and i.severity == ValidationSeverity.CRITICAL for i in issues))

    def test_circular_next_link_is_critical(self) -> None:
        signals = PaginationSignals(
            page=2,
            current_url="/blog/page/2",
            prev_url="/blog/page/1",
            next_url="/blog/page/2",
        )
        issues = validate_pagination_signals(signals)
        self.assertTrue(any(i.code == "PAGINATION_CIRCULAR_LINK" and i.severity == ValidationSeverity.CRITICAL for i in issues))

    def test_conflicting_canonical_signals(self) -> None:
        # Page 2 has prev/next signals but points canonical back to page 1 under "self" strategy
        signals = PaginationSignals(
            page=2,
            total_pages=5,
            current_url="/blog/page/2",
            canonical_url="/blog",
            prev_url="/blog",
            next_url="/blog/page/3",
            strategy="self",
        )
        issues = validate_pagination_signals(signals)
        self.assertTrue(any(i.code == "PAGINATION_CONFLICTING_SIGNALS" for i in issues))

    def test_invalid_page_number_rejected(self) -> None:
        signals = PaginationSignals(page=0, current_url="/blog/page/0")
        issues = validate_pagination_signals(signals)
        self.assertTrue(any(i.code == "PAGINATION_INVALID_PAGE_NUMBER" for i in issues))

    def test_analyze_pagination_html_extraction(self) -> None:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Blog - Page 2</title>
            <link rel="canonical" href="https://example.com/blog/page/2" />
            <link rel="prev" href="https://example.com/blog" />
            <link rel="next" href="https://example.com/blog/page/3" />
        </head>
        <body>
            <h1>Articles</h1>
        </body>
        </html>
        """
        res = analyze_pagination_html(
            html_content=html,
            current_page=2,
            total_pages=5,
            current_url="https://example.com/blog/page/2",
            strategy="self",
        )
        self.assertTrue(res.is_valid)
        self.assertEqual(res.signals.canonical_url, "https://example.com/blog/page/2")
        self.assertEqual(res.signals.prev_url, "https://example.com/blog")
        self.assertEqual(res.signals.next_url, "https://example.com/blog/page/3")
        self.assertEqual(len([i for i in res.issues if i.severity != ValidationSeverity.INFO]), 0)

    def test_pagination_signals_serialization(self) -> None:
        signals = PaginationSignals(
            page=3,
            total_pages=10,
            current_url="/shop/category",
            canonical_url="/shop/category",
            prev_url="/shop/category?p=2",
            next_url="/shop/category?p=4",
            strategy="self",
        )
        data = signals.to_dict()
        restored = PaginationSignals.from_dict(data)
        self.assertEqual(restored.page, 3)
        self.assertEqual(restored.total_pages, 10)
        self.assertEqual(restored.canonical_url, "/shop/category")
        self.assertEqual(restored.prev_url, "/shop/category?p=2")
        self.assertEqual(restored.next_url, "/shop/category?p=4")


if __name__ == "__main__":
    unittest.main()
