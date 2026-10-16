"""Unit and security tests for P9 Specialized Dimensions Modular Evaluation.

Covers REQ-P9-08:
- Multilingual & International SEO:
    * BCP 47 language/region tag validation
    * x-default fallback validation
    * Duplicate & conflicting hreflang detection
    * Reciprocal consistency verification across supplied page inventory
    * URL safety checks (scheme validation, SSRF private IP rejection)
    * HTMLParser streaming extraction
- Local SEO:
    * Schema.org LocalBusiness structured data validation
    * Required fields (name, address/PostalAddress) and optional fields (geo, telephone)
    * Script injection detection
- Ecommerce SEO:
    * Schema.org Product & Offer structured data validation
    * Required fields (name, offers, price, currency, availability)
    * Currency ISO 4217 validation
    * AggregateOffer validation
    * Script injection detection
- 100% Check-or-N/A Coverage:
    * Machine-readable NOT_APPLICABLE results with deterministic rationales
    * Full coverage across all 3 specialized dimensions (15a, 15b, 15c)
- Deterministic dictionary serialization round-trip
"""
from __future__ import annotations

import unittest

from domain.seo.model import (
    HreflangItem,
    SpecializedAnalysisResult,
    ValidationSeverity,
)
from domain.seo.specialized import (
    DEFAULT_ECOMMERCE_NA_RATIONALE,
    DEFAULT_LOCAL_NA_RATIONALE,
    DEFAULT_MULTILINGUAL_NA_RATIONALE,
    analyze_specialized_dimensions,
    evaluate_ecommerce,
    evaluate_local_seo,
    evaluate_multilingual,
    extract_hreflang_from_html,
    validate_hreflang,
    validate_local_business,
    validate_product_offer,
)


class TestMultilingualHreflang(unittest.TestCase):
    """Test hreflang formatting, URL safety, duplicate detection, and reciprocity."""

    def test_valid_hreflang_collection(self) -> None:
        items = [
            HreflangItem(lang="en", url="https://example.com/en/about"),
            HreflangItem(lang="en-US", url="https://example.com/us/about"),
            HreflangItem(lang="es-ES", url="https://example.com/es/about"),
            HreflangItem(lang="es-419", url="https://example.com/latam/about"),
            HreflangItem(lang="zh-Hans", url="https://example.com/zh/about"),
            HreflangItem(lang="x-default", url="https://example.com/about"),
        ]
        parsed, issues = validate_hreflang(
            items=items,
            current_url="https://example.com/en/about",
        )
        self.assertEqual(len(parsed), 6)
        serious_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        self.assertEqual(len(serious_issues), 0, f"Unexpected critical issues: {serious_issues}")
        # Self-reference should be detected for the en page
        en_item = next(it for it in parsed if it.lang == "en")
        self.assertTrue(en_item.is_self_reference)

    def test_invalid_bcp47_language_codes(self) -> None:
        items = [
            {"lang": "en_US", "url": "https://example.com/us"},
            {"lang": "123", "url": "https://example.com/num"},
            {"lang": "english", "url": "https://example.com/eng"},
        ]
        _, issues = validate_hreflang(items)
        issue_codes = [i.code for i in issues]
        self.assertIn("HREFLANG_UNDERSCORE_SEPARATOR", issue_codes)
        self.assertIn("HREFLANG_INVALID_CODE", issue_codes)

    def test_multiple_x_default_rejected(self) -> None:
        items = [
            {"lang": "x-default", "url": "https://example.com/home"},
            {"lang": "x-default", "url": "https://example.com/global"},
        ]
        _, issues = validate_hreflang(items)
        self.assertTrue(any(i.code == "HREFLANG_MULTIPLE_X_DEFAULT" and i.severity == ValidationSeverity.CRITICAL for i in issues))

    def test_duplicate_and_conflicting_hreflang(self) -> None:
        # Duplicate pointing to same URL -> Warning
        items_dup = [
            {"lang": "fr", "url": "https://example.com/fr"},
            {"lang": "fr", "url": "https://example.com/fr"},
        ]
        _, issues_dup = validate_hreflang(items_dup)
        self.assertTrue(any(i.code == "HREFLANG_DUPLICATE_ENTRY" for i in issues_dup))

        # Conflicting pointing to different URLs -> Critical
        items_conflict = [
            {"lang": "de", "url": "https://example.com/de-1"},
            {"lang": "de", "url": "https://example.com/de-2"},
        ]
        _, issues_conflict = validate_hreflang(items_conflict)
        self.assertTrue(any(i.code == "HREFLANG_CONFLICTING_TARGET" and i.severity == ValidationSeverity.CRITICAL for i in issues_conflict))

    def test_missing_self_reference_warning(self) -> None:
        items = [
            {"lang": "es", "url": "https://example.com/es/about"},
            {"lang": "x-default", "url": "https://example.com/about"},
        ]
        _, issues = validate_hreflang(items, current_url="https://example.com/en/about")
        self.assertTrue(any(i.code == "HREFLANG_MISSING_SELF_REFERENCE" for i in issues))

    def test_url_safety_and_private_ip_rejection(self) -> None:
        unsafe_items = [
            {"lang": "es", "url": "javascript:alert(1)"},
            {"lang": "fr", "url": "/relative/path"},
            {"lang": "de", "url": "http://127.0.0.1/admin"},
            {"lang": "it", "url": "http://169.254.169.254/meta"},
            {"lang": "ja", "url": "http://localhost:8080/ja"},
        ]
        _, issues = validate_hreflang(unsafe_items)
        issue_codes = [i.code for i in issues]
        self.assertIn("HREFLANG_UNSAFE_SCHEME", issue_codes)
        self.assertIn("HREFLANG_URL_NOT_ABSOLUTE", issue_codes)
        self.assertIn("HREFLANG_PRIVATE_IP_REJECTED", issue_codes)

    def test_reciprocal_reference_consistency_with_inventory(self) -> None:
        # Page EN links to Page ES, and Page ES links back to Page EN -> Valid
        inventory_valid = {
            "https://example.com/en": [
                HreflangItem(lang="en", url="https://example.com/en"),
                HreflangItem(lang="es", url="https://example.com/es"),
            ],
            "https://example.com/es": [
                HreflangItem(lang="en", url="https://example.com/en"),
                HreflangItem(lang="es", url="https://example.com/es"),
            ],
        }
        _, issues_valid = validate_hreflang(
            items=inventory_valid["https://example.com/en"],
            current_url="https://example.com/en",
            inventory=inventory_valid,
        )
        self.assertFalse(any(i.code == "HREFLANG_MISSING_RECIPROCAL" for i in issues_valid))

        # Missing reciprocal: Page ES does NOT link back to Page EN
        inventory_broken = {
            "https://example.com/en": [
                HreflangItem(lang="en", url="https://example.com/en"),
                HreflangItem(lang="es", url="https://example.com/es"),
            ],
            "https://example.com/es": [
                HreflangItem(lang="es", url="https://example.com/es"),
                # Missing link to EN!
            ],
        }
        _, issues_broken = validate_hreflang(
            items=inventory_broken["https://example.com/en"],
            current_url="https://example.com/en",
            inventory=inventory_broken,
        )
        self.assertTrue(any(i.code == "HREFLANG_MISSING_RECIPROCAL" for i in issues_broken))

    def test_html_streaming_extraction(self) -> None:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>International Page</title>
            <link rel="alternate" hreflang="en" href="https://example.com/en" />
            <link rel="alternate" hreflang="es" href="https://example.com/es" />
            <link rel="alternate" hreflang="x-default" href="https://example.com/" />
        </head>
        <body><p>Content</p></body>
        </html>
        """
        extracted = extract_hreflang_from_html(html)
        self.assertEqual(len(extracted), 3)
        self.assertEqual(extracted[0].lang, "en")
        self.assertEqual(extracted[0].url, "https://example.com/en")
        self.assertEqual(extracted[1].lang, "es")
        self.assertEqual(extracted[2].lang, "x-default")


class TestLocalBusinessEvaluation(unittest.TestCase):
    """Test LocalBusiness structured data evaluation and N/A handling."""

    def test_valid_local_business(self) -> None:
        data = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "Acme Coffee Roasters",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "123 Market St",
                "addressLocality": "San Francisco",
                "postalCode": "94105",
                "addressCountry": "US",
            },
            "telephone": "+1-415-555-0100",
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": 37.7891,
                "longitude": -122.4014,
            },
            "url": "https://example.com/cafe",
        }
        issues = validate_local_business(data)
        critical = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        self.assertEqual(len(critical), 0)

        res = evaluate_local_seo(data, is_local_business=True)
        self.assertEqual(res.status, "PASS")
        self.assertIsNone(res.na_rationale)
        self.assertEqual(res.data_summary["name"], "Acme Coffee Roasters")

    def test_local_business_missing_required_fields(self) -> None:
        data = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            # missing name and address
        }
        issues = validate_local_business(data)
        issue_codes = [i.code for i in issues]
        self.assertIn("LOCAL_BUSINESS_MISSING_NAME", issue_codes)
        self.assertIn("LOCAL_BUSINESS_MISSING_ADDRESS", issue_codes)

        res = evaluate_local_seo(data, is_local_business=True)
        self.assertEqual(res.status, "FAIL")

    def test_local_business_script_breakout_detected(self) -> None:
        data = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "Boutique </script><script>alert(1)</script>",
            "address": "456 Main St",
        }
        issues = validate_local_business(data)
        self.assertTrue(any(i.code == "SCHEMA_SCRIPT_TAG_IN_FIELD" for i in issues))

    def test_out_of_scope_local_seo_produces_not_applicable(self) -> None:
        res = evaluate_local_seo(entity=None, is_local_business=False)
        self.assertEqual(res.status, "NOT_APPLICABLE")
        self.assertEqual(res.na_rationale, DEFAULT_LOCAL_NA_RATIONALE)
        self.assertEqual(len(res.issues), 0)


class TestEcommerceProductOfferEvaluation(unittest.TestCase):
    """Test Product & Offer structured data evaluation and N/A handling."""

    def test_valid_product_with_single_offer(self) -> None:
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Aeropress Coffee Maker",
            "offers": {
                "@type": "Offer",
                "price": 39.95,
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
            },
            "sku": "AERO-01",
            "description": "Original Aeropress coffee and espresso maker",
        }
        issues = validate_product_offer(data)
        critical = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        self.assertEqual(len(critical), 0)

        res = evaluate_ecommerce(data, is_ecommerce=True)
        self.assertEqual(res.status, "PASS")
        self.assertIsNone(res.na_rationale)
        self.assertEqual(res.data_summary["name"], "Aeropress Coffee Maker")

    def test_valid_product_with_aggregate_offer(self) -> None:
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Specialty Espresso Beans",
            "offers": {
                "@type": "AggregateOffer",
                "lowPrice": "18.00",
                "priceCurrency": "EUR",
                "availability": "InStock",
            },
        }
        issues = validate_product_offer(data)
        critical = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        self.assertEqual(len(critical), 0)

    def test_product_missing_offers_and_name(self) -> None:
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
        }
        issues = validate_product_offer(data)
        issue_codes = [i.code for i in issues]
        self.assertIn("ECOMMERCE_MISSING_PRODUCT_NAME", issue_codes)
        self.assertIn("ECOMMERCE_MISSING_OFFERS", issue_codes)

        res = evaluate_ecommerce(data, is_ecommerce=True)
        self.assertEqual(res.status, "FAIL")

    def test_offer_invalid_price_and_currency(self) -> None:
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Widget",
            "offers": {
                "@type": "Offer",
                "price": -10,  # Negative price
                "priceCurrency": "$$",  # Invalid currency code
                "availability": "InvalidAvailability",
            },
        }
        issues = validate_product_offer(data)
        issue_codes = [i.code for i in issues]
        self.assertIn("ECOMMERCE_INVALID_PRICE", issue_codes)
        self.assertIn("ECOMMERCE_INVALID_CURRENCY", issue_codes)
        self.assertIn("ECOMMERCE_INVALID_AVAILABILITY", issue_codes)

    def test_out_of_scope_ecommerce_produces_not_applicable(self) -> None:
        res = evaluate_ecommerce(entity=None, is_ecommerce=False)
        self.assertEqual(res.status, "NOT_APPLICABLE")
        self.assertEqual(res.na_rationale, DEFAULT_ECOMMERCE_NA_RATIONALE)
        self.assertEqual(len(res.issues), 0)


class Test100PercentCheckOrNACoverage(unittest.TestCase):
    """Test full specialized dimension aggregate analysis and coverage contract."""

    def test_full_specialized_evaluation_all_active(self) -> None:
        hreflangs = [
            HreflangItem(lang="en", url="https://example.com/en"),
            HreflangItem(lang="es", url="https://example.com/es"),
            HreflangItem(lang="x-default", url="https://example.com/"),
        ]
        local_data = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "Local Shop",
            "address": "123 High St",
        }
        product_data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Handmade Mug",
            "offers": {
                "@type": "Offer",
                "price": "15.00",
                "priceCurrency": "GBP",
            },
        }

        res = analyze_specialized_dimensions(
            current_url="https://example.com/en",
            hreflang_items=hreflangs,
            is_multilingual=True,
            local_business_data=local_data,
            is_local_business=True,
            ecommerce_data=product_data,
            is_ecommerce=True,
        )
        self.assertTrue(res.is_valid)
        self.assertEqual(res.multilingual.status, "PASS")
        self.assertEqual(res.local_business.status, "PASS")
        self.assertEqual(res.ecommerce.status, "PASS")

        # Every dimension has status PASS (checked) and na_rationale None
        self.assertIsNone(res.multilingual.na_rationale)
        self.assertIsNone(res.local_business.na_rationale)
        self.assertIsNone(res.ecommerce.na_rationale)

    def test_specialized_evaluation_with_out_of_scope_dimensions(self) -> None:
        # Single-language blog: No i18n, no local business, no ecommerce
        res = analyze_specialized_dimensions(
            is_multilingual=False,
            is_local_business=False,
            is_ecommerce=False,
        )
        self.assertTrue(res.is_valid)
        # All three dimensions MUST be reported as NOT_APPLICABLE with explicit rationales
        self.assertEqual(res.multilingual.status, "NOT_APPLICABLE")
        self.assertEqual(res.multilingual.na_rationale, DEFAULT_MULTILINGUAL_NA_RATIONALE)

        self.assertEqual(res.local_business.status, "NOT_APPLICABLE")
        self.assertEqual(res.local_business.na_rationale, DEFAULT_LOCAL_NA_RATIONALE)

        self.assertEqual(res.ecommerce.status, "NOT_APPLICABLE")
        self.assertEqual(res.ecommerce.na_rationale, DEFAULT_ECOMMERCE_NA_RATIONALE)

    def test_serialization_round_trip(self) -> None:
        res = analyze_specialized_dimensions(
            is_multilingual=False,
            is_local_business=False,
            is_ecommerce=False,
        )
        d = res.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("multilingual", d)
        self.assertIn("local_business", d)
        self.assertIn("ecommerce", d)

        restored = SpecializedAnalysisResult.from_dict(d)
        self.assertEqual(restored.multilingual.status, "NOT_APPLICABLE")
        self.assertEqual(restored.local_business.status, "NOT_APPLICABLE")
        self.assertEqual(restored.ecommerce.status, "NOT_APPLICABLE")
        self.assertTrue(restored.is_valid)


if __name__ == "__main__":
    unittest.main()
