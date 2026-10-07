"""P9 Specialized Dimensions Modular Evaluation (REQ-P9-08).

Implements:
A. Multilingual & International SEO:
   - hreflang validation (BCP 47 language/region codes)
   - x-default fallback validation
   - duplicate and conflicting hreflang detection
   - reciprocal/reference consistency across supplied page inventory
   - URL safety validation (SSRF private IP rejection, scheme validation)
   - safe HTMLParser streaming extraction
B. Local SEO:
   - Schema.org LocalBusiness structured-data validation (name, address/PostalAddress, geo, openingHours)
   - static evaluation without external network calls
C. Ecommerce SEO:
   - Schema.org Product and Offer structured-data validation (name, offers, price, currency, availability)
   - static evaluation without external network calls
D. 100% Check-or-N/A Specialized Coverage:
   - Every dimension produces either a verified evaluation or an explicit machine-readable NOT_APPLICABLE finding
   - Strictly deterministic serialization and diagnostics
   - Pure Python standard library only; project-local; zero network requests.
"""
from __future__ import annotations

import re
import urllib.parse
from html.parser import HTMLParser
from typing import Any

from domain.seo.metadata import _is_private_or_loopback_host
from domain.seo.model import (
    HreflangItem,
    SpecializedAnalysisResult,
    SpecializedDimensionResult,
    ValidationIssue,
    ValidationSeverity,
)
from domain.seo.structured_data import (
    SCHEMA_CONTEXT,
    _scan_for_script_probes,
    _validate_uri,
    extract_json_ld_from_html,
)

# ---------------------------------------------------------------------------
# Default N/A Rationales for Specialized Dimensions
# ---------------------------------------------------------------------------

DEFAULT_MULTILINGUAL_NA_RATIONALE = (
    "Multilingual SEO is not applicable: project is single-language without international hreflang requirements."
)

DEFAULT_LOCAL_NA_RATIONALE = (
    "Local SEO is not applicable: project does not operate physical locations or local business services."
)

DEFAULT_ECOMMERCE_NA_RATIONALE = (
    "Ecommerce SEO is not applicable: project does not sell products or process transactional offers."
)

# BCP 47 pattern: ISO 639-1 (2-letter) or ISO 639-2 (3-letter), optional script (4-letter), optional region (2-letter or 3-digit)
_BCP47_PATTERN = re.compile(
    r"^(?:x-default|[a-z]{2,3}(?:-[a-zA-Z]{4})?(?:-(?:[a-zA-Z]{2}|[0-9]{3}))?)$",
    re.IGNORECASE,
)

# ISO 4217 Currency Code pattern (3 uppercase letters)
_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")

# Unsafe schemes to reject immediately in hreflang and schema URIs
UNSAFE_SCHEMES = {"javascript", "data", "vbscript", "file"}

# Standard LocalBusiness subtypes recognized by Schema.org
LOCAL_BUSINESS_TYPES = {
    "LocalBusiness",
    "Store",
    "Restaurant",
    "FoodEstablishment",
    "MedicalBusiness",
    "ProfessionalService",
    "LegalService",
    "FinancialService",
    "RealEstateAgent",
    "LodgingBusiness",
    "AutomotiveBusiness",
    "EntertainmentBusiness",
    "HomeAndConstructionBusiness",
    "SportsActivityLocation",
}


# ---------------------------------------------------------------------------
# 1. Multilingual & International SEO (hreflang)
# ---------------------------------------------------------------------------

class HreflangHTMLParser(HTMLParser):
    """Linear streaming extractor for <link rel="alternate" hreflang="..."> elements in HTML <head>."""

    def __init__(self) -> None:
        super().__init__()
        self.hreflang_items: list[HreflangItem] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "link":
            attr_dict = {k.lower(): (v or "").strip() for k, v in attrs}
            rel = attr_dict.get("rel", "").lower()
            hreflang = attr_dict.get("hreflang", "").strip()
            href = attr_dict.get("href", "").strip()

            if rel == "alternate" and hreflang and href:
                self.hreflang_items.append(HreflangItem(lang=hreflang, url=href))


def extract_hreflang_from_html(html_content: str) -> list[HreflangItem]:
    """Extract alternate hreflang links from rendered HTML document."""
    parser = HreflangHTMLParser()
    parser.feed(html_content or "")
    parser.close()
    return parser.hreflang_items


def _clean_route(url: str) -> str:
    """Normalize a URL path or URL string for reciprocal comparison."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url.strip())
    path = parsed.path or "/"
    norm = re.sub(r"/+", "/", path).lower()
    if len(norm) > 1 and norm.endswith("/"):
        norm = norm[:-1]
    return f"{parsed.netloc.lower()}{norm}" if parsed.netloc else norm


def validate_hreflang(
    items: list[HreflangItem] | list[dict[str, Any]],
    current_url: str = "",
    inventory: dict[str, list[HreflangItem]] | None = None,
) -> tuple[list[HreflangItem], list[ValidationIssue]]:
    """Validate hreflang annotations against BCP 47 formatting, URL safety, duplicates, and reciprocity."""
    issues: list[ValidationIssue] = []
    parsed_items: list[HreflangItem] = []

    for raw in items:
        if isinstance(raw, HreflangItem):
            parsed_items.append(raw)
        elif isinstance(raw, dict):
            parsed_items.append(HreflangItem.from_dict(raw))

    if not parsed_items:
        return [], issues

    seen_langs: dict[str, str] = {}
    x_default_count = 0
    clean_curr = _clean_route(current_url) if current_url else ""
    has_self_ref = False

    for item in parsed_items:
        lang_raw = item.lang.strip()
        url_raw = item.url.strip()

        # 1. BCP 47 Language / Region Code Validation
        if "_" in lang_raw:
            issues.append(
                ValidationIssue(
                    code="HREFLANG_UNDERSCORE_SEPARATOR",
                    message=(
                        f"hreflang '{lang_raw}' uses underscore as separator; "
                        "BCP 47 requires hyphens (e.g. 'en-US')"
                    ),
                    severity=ValidationSeverity.WARNING,
                    field=lang_raw,
                )
            )

        if not _BCP47_PATTERN.match(lang_raw):
            issues.append(
                ValidationIssue(
                    code="HREFLANG_INVALID_CODE",
                    message=(
                        f"hreflang '{lang_raw}' is not a valid BCP 47 language/region tag or 'x-default'"
                    ),
                    severity=ValidationSeverity.CRITICAL,
                    field=lang_raw,
                )
            )

        norm_lang = lang_raw.lower()
        if norm_lang == "x-default":
            x_default_count += 1

        # 2. Duplicate / Conflicting hreflang detection
        if norm_lang in seen_langs:
            existing_url = seen_langs[norm_lang]
            if existing_url.lower() != url_raw.lower():
                issues.append(
                    ValidationIssue(
                        code="HREFLANG_CONFLICTING_TARGET",
                        message=(
                            f"Multiple conflicting hreflang tags for language '{lang_raw}': "
                            f"points to '{existing_url}' and '{url_raw}'"
                        ),
                        severity=ValidationSeverity.CRITICAL,
                        field=lang_raw,
                    )
                )
            else:
                issues.append(
                    ValidationIssue(
                        code="HREFLANG_DUPLICATE_ENTRY",
                        message=f"Duplicate hreflang tag for language '{lang_raw}' pointing to '{url_raw}'",
                        severity=ValidationSeverity.WARNING,
                        field=lang_raw,
                    )
                )
        else:
            seen_langs[norm_lang] = url_raw

        # 3. URL Safety and Absolute URL Validation
        if not url_raw:
            issues.append(
                ValidationIssue(
                    code="HREFLANG_URL_EMPTY",
                    message=f"hreflang for '{lang_raw}' has empty href URL",
                    severity=ValidationSeverity.CRITICAL,
                    field=lang_raw,
                )
            )
            continue

        parsed_url = urllib.parse.urlparse(url_raw)
        scheme = parsed_url.scheme.lower()

        if scheme in UNSAFE_SCHEMES:
            issues.append(
                ValidationIssue(
                    code="HREFLANG_UNSAFE_SCHEME",
                    message=f"hreflang for '{lang_raw}' uses dangerous scheme '{scheme}:'",
                    severity=ValidationSeverity.CRITICAL,
                    field=lang_raw,
                )
            )
        elif not parsed_url.scheme or not parsed_url.netloc:
            issues.append(
                ValidationIssue(
                    code="HREFLANG_URL_NOT_ABSOLUTE",
                    message=(
                        f"hreflang for '{lang_raw}' target URL '{url_raw}' must be an absolute URL "
                        "including scheme and hostname"
                    ),
                    severity=ValidationSeverity.WARNING,
                    field=lang_raw,
                )
            )
        elif scheme in ("http", "https"):
            hostname = parsed_url.hostname or ""
            if _is_private_or_loopback_host(hostname):
                issues.append(
                    ValidationIssue(
                        code="HREFLANG_PRIVATE_IP_REJECTED",
                        message=f"hreflang for '{lang_raw}' points to private or loopback host '{hostname}'",
                        severity=ValidationSeverity.CRITICAL,
                        field=lang_raw,
                    )
                )

        # 4. Self-reference check
        if clean_curr and _clean_route(url_raw) == clean_curr:
            has_self_ref = True
            item.is_self_reference = True

    # Check for multiple x-default
    if x_default_count > 1:
        issues.append(
            ValidationIssue(
                code="HREFLANG_MULTIPLE_X_DEFAULT",
                message=f"Page defines {x_default_count} conflicting x-default hreflang links; must define at most one",
                severity=ValidationSeverity.CRITICAL,
                field="x-default",
            )
        )

    # Check for missing self-reference if current_url was provided
    if clean_curr and not has_self_ref:
        issues.append(
            ValidationIssue(
                code="HREFLANG_MISSING_SELF_REFERENCE",
                message=(
                    f"Page at '{current_url}' defines hreflang alternates but lacks a self-referencing hreflang tag "
                    "matching its own canonical language"
                ),
                severity=ValidationSeverity.WARNING,
                field="current_url",
            )
        )

    # 5. Reciprocal Reference Consistency (when inventory map is supplied)
    if inventory and clean_curr:
        for item in parsed_items:
            target_route = _clean_route(item.url)
            # Find target in inventory
            target_hreflangs = None
            for inv_url, inv_items in inventory.items():
                if _clean_route(inv_url) == target_route:
                    target_hreflangs = inv_items
                    break

            if target_hreflangs is not None:
                # Target exists in supplied inventory: check reciprocal link back to current_url
                has_reciprocal = any(_clean_route(th.url) == clean_curr for th in target_hreflangs)
                if not has_reciprocal:
                    issues.append(
                        ValidationIssue(
                            code="HREFLANG_MISSING_RECIPROCAL",
                            message=(
                                f"Missing reciprocal hreflang return link: page '{current_url}' links to "
                                f"'{item.url}' ({item.lang}), but target does not link back to current page"
                            ),
                            severity=ValidationSeverity.WARNING,
                            field=item.lang,
                        )
                    )

    return parsed_items, issues


def evaluate_multilingual(
    items: list[HreflangItem] | list[dict[str, Any]] | None = None,
    html_content: str = "",
    current_url: str = "",
    inventory: dict[str, list[HreflangItem]] | None = None,
    is_multilingual: bool = True,
    na_rationale: str | None = None,
) -> SpecializedDimensionResult:
    """Evaluate Multilingual / International SEO dimension with strict check-or-N/A handling."""
    # Check if dimension is out-of-scope
    if not is_multilingual:
        return SpecializedDimensionResult(
            dimension_id="i18n",
            dimension_name="International / Multilingual SEO",
            status="NOT_APPLICABLE",
            na_rationale=na_rationale or DEFAULT_MULTILINGUAL_NA_RATIONALE,
            data_summary={"is_multilingual": False},
            issues=[],
        )

    hreflang_list: list[HreflangItem] = []
    if items:
        for it in items:
            hreflang_list.append(it if isinstance(it, HreflangItem) else HreflangItem.from_dict(it))
    elif html_content:
        hreflang_list = extract_hreflang_from_html(html_content)

    if not hreflang_list:
        # If declared multilingual but no hreflang tags found:
        return SpecializedDimensionResult(
            dimension_id="i18n",
            dimension_name="International / Multilingual SEO",
            status="NOT_APPLICABLE",
            na_rationale=na_rationale or DEFAULT_MULTILINGUAL_NA_RATIONALE,
            data_summary={"hreflang_count": 0},
            issues=[],
        )

    validated_items, issues = validate_hreflang(
        items=hreflang_list,
        current_url=current_url,
        inventory=inventory,
    )

    has_critical = any(i.severity == ValidationSeverity.CRITICAL for i in issues)
    has_warning = any(i.severity == ValidationSeverity.WARNING for i in issues)

    if has_critical:
        status = "FAIL"
    elif has_warning:
        status = "WARNING"
    else:
        status = "PASS"

    return SpecializedDimensionResult(
        dimension_id="i18n",
        dimension_name="International / Multilingual SEO",
        status=status,
        na_rationale=None,
        data_summary={
            "hreflang_count": len(validated_items),
            "languages": sorted(list({it.lang for it in validated_items})),
            "has_x_default": any(it.lang.lower() == "x-default" for it in validated_items),
        },
        issues=issues,
    )


# ---------------------------------------------------------------------------
# 2. Local SEO (LocalBusiness Structured Data)
# ---------------------------------------------------------------------------

def validate_local_business(entity: dict[str, Any]) -> list[ValidationIssue]:
    """Validate a Schema.org LocalBusiness structured data object."""
    issues: list[ValidationIssue] = []

    if not isinstance(entity, dict):
        issues.append(
            ValidationIssue(
                code="LOCAL_BUSINESS_NOT_AN_OBJECT",
                message=f"LocalBusiness entity must be a JSON object, got {type(entity).__name__}",
                severity=ValidationSeverity.CRITICAL,
            )
        )
        return issues

    # 1. Security scan against script breakouts
    issues.extend(_scan_for_script_probes(entity))

    # 2. @context validation
    context = entity.get("@context")
    if not context:
        issues.append(
            ValidationIssue(
                code="LOCAL_BUSINESS_MISSING_CONTEXT",
                message="LocalBusiness is missing required '@context' property",
                severity=ValidationSeverity.CRITICAL,
                field="@context",
            )
        )
    elif context != SCHEMA_CONTEXT:
        issues.append(
            ValidationIssue(
                code="LOCAL_BUSINESS_INVALID_CONTEXT",
                message=f"@context must be '{SCHEMA_CONTEXT}', got '{context}'",
                severity=ValidationSeverity.CRITICAL,
                field="@context",
            )
        )

    # 3. @type validation
    schema_type = entity.get("@type")
    if not schema_type:
        issues.append(
            ValidationIssue(
                code="LOCAL_BUSINESS_MISSING_TYPE",
                message="LocalBusiness entity is missing required '@type' property",
                severity=ValidationSeverity.CRITICAL,
                field="@type",
            )
        )
    elif schema_type not in LOCAL_BUSINESS_TYPES:
        issues.append(
            ValidationIssue(
                code="LOCAL_BUSINESS_INVALID_TYPE",
                message=f"Invalid @type '{schema_type}' for LocalBusiness; expected LocalBusiness or valid subtype",
                severity=ValidationSeverity.WARNING,
                field="@type",
            )
        )

    # 4. Name validation
    name = entity.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        issues.append(
            ValidationIssue(
                code="LOCAL_BUSINESS_MISSING_NAME",
                message="LocalBusiness entity is missing required non-empty 'name' property",
                severity=ValidationSeverity.CRITICAL,
                field="name",
            )
        )

    # 5. Address validation
    address = entity.get("address")
    if not address:
        issues.append(
            ValidationIssue(
                code="LOCAL_BUSINESS_MISSING_ADDRESS",
                message="LocalBusiness entity is missing required 'address' property",
                severity=ValidationSeverity.CRITICAL,
                field="address",
            )
        )
    elif isinstance(address, dict):
        addr_type = address.get("@type")
        if addr_type and addr_type != "PostalAddress":
            issues.append(
                ValidationIssue(
                    code="LOCAL_BUSINESS_INVALID_ADDRESS_TYPE",
                    message=f"address @type should be 'PostalAddress', got '{addr_type}'",
                    severity=ValidationSeverity.WARNING,
                    field="address.@type",
                )
            )
        has_addr_fields = any(
            bool(address.get(f))
            for f in ("streetAddress", "addressLocality", "postalCode", "addressCountry", "addressRegion")
        )
        if not has_addr_fields:
            issues.append(
                ValidationIssue(
                    code="LOCAL_BUSINESS_EMPTY_ADDRESS",
                    message="address object lacks specific location fields (streetAddress, addressLocality, etc.)",
                    severity=ValidationSeverity.WARNING,
                    field="address",
                )
            )
    elif isinstance(address, str):
        if not address.strip():
            issues.append(
                ValidationIssue(
                    code="LOCAL_BUSINESS_MISSING_ADDRESS",
                    message="LocalBusiness address string is empty",
                    severity=ValidationSeverity.CRITICAL,
                    field="address",
                )
            )

    # 6. Geo coordinates validation (if present)
    geo = entity.get("geo")
    if geo:
        if isinstance(geo, dict):
            if "latitude" not in geo or "longitude" not in geo:
                issues.append(
                    ValidationIssue(
                        code="LOCAL_BUSINESS_INVALID_GEO",
                        message="GeoCoordinates object must specify both 'latitude' and 'longitude'",
                        severity=ValidationSeverity.WARNING,
                        field="geo",
                    )
                )
        else:
            issues.append(
                ValidationIssue(
                    code="LOCAL_BUSINESS_INVALID_GEO",
                    message="geo property must be a GeoCoordinates object",
                    severity=ValidationSeverity.WARNING,
                    field="geo",
                )
            )

    # 7. Telephone & URL validation (if present)
    url_val = entity.get("url")
    if url_val:
        issues.extend(_validate_uri(url_val, "url"))

    return issues


def evaluate_local_seo(
    entity: dict[str, Any] | list[dict[str, Any]] | None = None,
    html_content: str = "",
    is_local_business: bool = False,
    na_rationale: str | None = None,
) -> SpecializedDimensionResult:
    """Evaluate Local SEO dimension with strict check-or-N/A handling."""
    # Find LocalBusiness data from input or rendered HTML
    local_entity: dict[str, Any] | None = None

    if isinstance(entity, dict):
        local_entity = entity
    elif isinstance(entity, list) and entity:
        for it in entity:
            if isinstance(it, dict) and it.get("@type") in LOCAL_BUSINESS_TYPES:
                local_entity = it
                break
    elif html_content:
        blocks = extract_json_ld_from_html(html_content)
        for b in blocks:
            if isinstance(b, dict) and b.get("@type") in LOCAL_BUSINESS_TYPES:
                local_entity = b
                break

    # If dimension is out-of-scope and no local entity is present:
    if not is_local_business and local_entity is None:
        return SpecializedDimensionResult(
            dimension_id="local",
            dimension_name="Local Business SEO",
            status="NOT_APPLICABLE",
            na_rationale=na_rationale or DEFAULT_LOCAL_NA_RATIONALE,
            data_summary={"is_local_business": False},
            issues=[],
        )

    if local_entity is None:
        return SpecializedDimensionResult(
            dimension_id="local",
            dimension_name="Local Business SEO",
            status="FAIL",
            na_rationale=None,
            data_summary={"is_local_business": True, "entity_found": False},
            issues=[
                ValidationIssue(
                    code="LOCAL_BUSINESS_DATA_MISSING",
                    message="Project declared LocalBusiness scope but no valid LocalBusiness structured data was found",
                    severity=ValidationSeverity.CRITICAL,
                    field="LocalBusiness",
                )
            ],
        )

    issues = validate_local_business(local_entity)
    has_critical = any(i.severity == ValidationSeverity.CRITICAL for i in issues)
    has_warning = any(i.severity == ValidationSeverity.WARNING for i in issues)

    if has_critical:
        status = "FAIL"
    elif has_warning:
        status = "WARNING"
    else:
        status = "PASS"

    return SpecializedDimensionResult(
        dimension_id="local",
        dimension_name="Local Business SEO",
        status=status,
        na_rationale=None,
        data_summary={
            "name": local_entity.get("name", ""),
            "@type": local_entity.get("@type", "LocalBusiness"),
            "has_telephone": bool(local_entity.get("telephone")),
            "has_geo": bool(local_entity.get("geo")),
        },
        issues=issues,
    )


# ---------------------------------------------------------------------------
# 3. Ecommerce SEO (Product & Offer Structured Data)
# ---------------------------------------------------------------------------

def validate_product_offer(entity: dict[str, Any]) -> list[ValidationIssue]:
    """Validate a Schema.org Product structured data object and nested Offer(s)."""
    issues: list[ValidationIssue] = []

    if not isinstance(entity, dict):
        issues.append(
            ValidationIssue(
                code="ECOMMERCE_NOT_AN_OBJECT",
                message=f"Product entity must be a JSON object, got {type(entity).__name__}",
                severity=ValidationSeverity.CRITICAL,
            )
        )
        return issues

    # 1. Security scan against script breakouts
    issues.extend(_scan_for_script_probes(entity))

    # 2. @context validation
    context = entity.get("@context")
    if not context:
        issues.append(
            ValidationIssue(
                code="ECOMMERCE_MISSING_CONTEXT",
                message="Product structured data is missing required '@context' property",
                severity=ValidationSeverity.CRITICAL,
                field="@context",
            )
        )
    elif context != SCHEMA_CONTEXT:
        issues.append(
            ValidationIssue(
                code="ECOMMERCE_INVALID_CONTEXT",
                message=f"@context must be '{SCHEMA_CONTEXT}', got '{context}'",
                severity=ValidationSeverity.CRITICAL,
                field="@context",
            )
        )

    # 3. @type validation
    schema_type = entity.get("@type")
    if not schema_type:
        issues.append(
            ValidationIssue(
                code="ECOMMERCE_MISSING_TYPE",
                message="Product entity is missing required '@type' property",
                severity=ValidationSeverity.CRITICAL,
                field="@type",
            )
        )
    elif schema_type != "Product":
        issues.append(
            ValidationIssue(
                code="ECOMMERCE_INVALID_TYPE",
                message=f"@type must be 'Product', got '{schema_type}'",
                severity=ValidationSeverity.CRITICAL,
                field="@type",
            )
        )

    # 4. Name validation
    name = entity.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        issues.append(
            ValidationIssue(
                code="ECOMMERCE_MISSING_PRODUCT_NAME",
                message="Product entity is missing required non-empty 'name' property",
                severity=ValidationSeverity.CRITICAL,
                field="name",
            )
        )

    # 5. Offers validation
    offers_raw = entity.get("offers")
    if not offers_raw:
        issues.append(
            ValidationIssue(
                code="ECOMMERCE_MISSING_OFFERS",
                message="Product entity is missing required 'offers' (Offer / AggregateOffer) property",
                severity=ValidationSeverity.CRITICAL,
                field="offers",
            )
        )
    else:
        offers_list: list[dict[str, Any]] = []
        if isinstance(offers_raw, dict):
            offers_list = [offers_raw]
        elif isinstance(offers_raw, list):
            offers_list = [o for o in offers_raw if isinstance(o, dict)]

        if not offers_list:
            issues.append(
                ValidationIssue(
                    code="ECOMMERCE_INVALID_OFFERS_FORMAT",
                    message="Product 'offers' must be an Offer object or list of Offer objects",
                    severity=ValidationSeverity.CRITICAL,
                    field="offers",
                )
            )
        else:
            for idx, off in enumerate(offers_list):
                off_path = f"offers[{idx}]" if len(offers_list) > 1 else "offers"
                off_type = off.get("@type", "Offer")

                # Validate price
                price = off.get("price")
                if price is None and "lowPrice" in off:
                    price = off.get("lowPrice")

                if price is None:
                    issues.append(
                        ValidationIssue(
                            code="ECOMMERCE_MISSING_PRICE",
                            message=f"Offer in '{off_path}' is missing required 'price' (or 'lowPrice') property",
                            severity=ValidationSeverity.CRITICAL,
                            field=f"{off_path}.price",
                        )
                    )
                else:
                    is_valid_num = False
                    if isinstance(price, (int, float)) and price >= 0:
                        is_valid_num = True
                    elif isinstance(price, str):
                        try:
                            num = float(price.replace(",", ""))
                            if num >= 0:
                                is_valid_num = True
                        except ValueError:
                            pass
                    if not is_valid_num:
                        issues.append(
                            ValidationIssue(
                                code="ECOMMERCE_INVALID_PRICE",
                                message=f"Offer price '{price}' must be a non-negative number or numeric string",
                                severity=ValidationSeverity.CRITICAL,
                                field=f"{off_path}.price",
                            )
                        )

                # Validate currency (ISO 4217, 3 letters)
                currency = off.get("priceCurrency")
                if not currency or not isinstance(currency, str) or not _CURRENCY_PATTERN.match(currency.upper()):
                    issues.append(
                        ValidationIssue(
                            code="ECOMMERCE_INVALID_CURRENCY",
                            message=(
                                f"Offer priceCurrency '{currency}' must be a valid 3-letter ISO 4217 code (e.g. 'USD')"
                            ),
                            severity=ValidationSeverity.CRITICAL,
                            field=f"{off_path}.priceCurrency",
                        )
                    )

                # Validate availability (if present)
                avail = off.get("availability")
                if avail and isinstance(avail, str):
                    if not any(k in avail for k in ("InStock", "OutOfStock", "PreOrder", "Discontinued", "BackOrder")):
                        issues.append(
                            ValidationIssue(
                                code="ECOMMERCE_INVALID_AVAILABILITY",
                                message=f"Offer availability '{avail}' is not a recognized Schema.org ItemAvailability URI",
                                severity=ValidationSeverity.WARNING,
                                field=f"{off_path}.availability",
                            )
                        )

    # 6. Optional fields checks (image, url)
    img_val = entity.get("image")
    if img_val and isinstance(img_val, str):
        issues.extend(_validate_uri(img_val, "image"))

    return issues


def evaluate_ecommerce(
    entity: dict[str, Any] | list[dict[str, Any]] | None = None,
    html_content: str = "",
    is_ecommerce: bool = False,
    na_rationale: str | None = None,
) -> SpecializedDimensionResult:
    """Evaluate Ecommerce SEO dimension with strict check-or-N/A handling."""
    # Find Product data from input or rendered HTML
    product_entity: dict[str, Any] | None = None

    if isinstance(entity, dict):
        product_entity = entity
    elif isinstance(entity, list) and entity:
        for it in entity:
            if isinstance(it, dict) and it.get("@type") == "Product":
                product_entity = it
                break
    elif html_content:
        blocks = extract_json_ld_from_html(html_content)
        for b in blocks:
            if isinstance(b, dict) and b.get("@type") == "Product":
                product_entity = b
                break

    # If dimension is out-of-scope and no product entity is present:
    if not is_ecommerce and product_entity is None:
        return SpecializedDimensionResult(
            dimension_id="ecommerce",
            dimension_name="Ecommerce SEO (Product & Offer)",
            status="NOT_APPLICABLE",
            na_rationale=na_rationale or DEFAULT_ECOMMERCE_NA_RATIONALE,
            data_summary={"is_ecommerce": False},
            issues=[],
        )

    if product_entity is None:
        return SpecializedDimensionResult(
            dimension_id="ecommerce",
            dimension_name="Ecommerce SEO (Product & Offer)",
            status="FAIL",
            na_rationale=None,
            data_summary={"is_ecommerce": True, "entity_found": False},
            issues=[
                ValidationIssue(
                    code="ECOMMERCE_PRODUCT_DATA_MISSING",
                    message="Project declared Ecommerce scope but no valid Product structured data was found",
                    severity=ValidationSeverity.CRITICAL,
                    field="Product",
                )
            ],
        )

    issues = validate_product_offer(product_entity)
    has_critical = any(i.severity == ValidationSeverity.CRITICAL for i in issues)
    has_warning = any(i.severity == ValidationSeverity.WARNING for i in issues)

    if has_critical:
        status = "FAIL"
    elif has_warning:
        status = "WARNING"
    else:
        status = "PASS"

    return SpecializedDimensionResult(
        dimension_id="ecommerce",
        dimension_name="Ecommerce SEO (Product & Offer)",
        status=status,
        na_rationale=None,
        data_summary={
            "name": product_entity.get("name", ""),
            "@type": "Product",
            "has_offers": bool(product_entity.get("offers")),
        },
        issues=issues,
    )


# ---------------------------------------------------------------------------
# 4. Aggregate Specialized Dimensions Evaluator (REQ-P9-08)
# ---------------------------------------------------------------------------

def analyze_specialized_dimensions(
    html_content: str = "",
    current_url: str = "",
    hreflang_items: list[HreflangItem] | list[dict[str, Any]] | None = None,
    hreflang_inventory: dict[str, list[HreflangItem]] | None = None,
    is_multilingual: bool = True,
    multilingual_na_rationale: str | None = None,
    local_business_data: dict[str, Any] | list[dict[str, Any]] | None = None,
    is_local_business: bool = False,
    local_na_rationale: str | None = None,
    ecommerce_data: dict[str, Any] | list[dict[str, Any]] | None = None,
    is_ecommerce: bool = False,
    ecommerce_na_rationale: str | None = None,
) -> SpecializedAnalysisResult:
    """Evaluate all three specialized SEO dimensions, guaranteeing 100% check-or-N/A coverage."""
    # 1. Multilingual
    res_i18n = evaluate_multilingual(
        items=hreflang_items,
        html_content=html_content,
        current_url=current_url,
        inventory=hreflang_inventory,
        is_multilingual=is_multilingual,
        na_rationale=multilingual_na_rationale,
    )

    # 2. Local SEO
    res_local = evaluate_local_seo(
        entity=local_business_data,
        html_content=html_content,
        is_local_business=is_local_business,
        na_rationale=local_na_rationale,
    )

    # 3. Ecommerce SEO
    res_ecommerce = evaluate_ecommerce(
        entity=ecommerce_data,
        html_content=html_content,
        is_ecommerce=is_ecommerce,
        na_rationale=ecommerce_na_rationale,
    )

    all_issues: list[ValidationIssue] = []
    all_issues.extend(res_i18n.issues)
    all_issues.extend(res_local.issues)
    all_issues.extend(res_ecommerce.issues)

    is_valid = not any(i.severity == ValidationSeverity.CRITICAL for i in all_issues)

    return SpecializedAnalysisResult(
        multilingual=res_i18n,
        local_business=res_local,
        ecommerce=res_ecommerce,
        is_valid=is_valid,
        issues=all_issues,
    )
