"""P9 Core Web Vitals & Layout Stability Engine (REQ-P9-07).

Implements:
- Automated CLS verification using ONLY the approved researched CLS thresholds:
    * CLS <= 0.1 = Good / Pass
    * CLS > 0.25 = Poor / Critical
    * 0.1 < CLS <= 0.25 = Needs Improvement / Warning
- Static layout-shift prevention analysis:
    * Image dimension/layout stability checks reused from domain.seo.media
    * Font-display / layout-shift prevention analysis for web fonts
- Explicit LCP and INP gap representation:
    * LCP and INP are strictly reported as machine-readable NOT_APPLICABLE findings
    * Exact approved N/A rationale:
      "Unobserved research threshold per CONF-001; numeric thresholds not established. No synthetic thresholds permitted."
    * Zero invented, inferred, or calculated numeric thresholds
    * Explicit rejection of any attempt to provide invented LCP/INP numeric thresholds
- Strictly standard library only; project-local; zero network requests.
"""
from __future__ import annotations

import math
import re
import urllib.parse
from html.parser import HTMLParser
from typing import Any

from domain.seo.media import analyze_media
from domain.seo.model import (
    CWVAnalysisResult,
    CWVMetricResult,
    StaticShiftPreventionResult,
    ValidationIssue,
    ValidationSeverity,
)

# ---------------------------------------------------------------------------
# Approved CWV Research Thresholds (SRC-017 / web.dev)
# ---------------------------------------------------------------------------

CLS_GOOD_THRESHOLD: float = 0.1
CLS_POOR_THRESHOLD: float = 0.25

CONF_001_NA_RATIONALE: str = (
    "Unobserved research threshold per CONF-001; numeric thresholds not established. "
    "No synthetic thresholds permitted."
)

# Pattern to detect attempts to supply invented LCP or INP numeric thresholds
_INVENTED_THRESHOLD_PATTERN = re.compile(
    r"^(lcp|inp)(_threshold|_max|_target|_value|_numeric)?$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# 1. Automated CLS Evaluation
# ---------------------------------------------------------------------------

def evaluate_cls(observed_cls: float | None = None) -> CWVMetricResult:
    """Evaluate observed Cumulative Layout Shift against approved thresholds."""
    issues: list[ValidationIssue] = []

    if observed_cls is None:
        issues.append(
            ValidationIssue(
                code="CWV_CLS_NOT_PROVIDED",
                message=(
                    "Direct runtime CLS measurement was not provided; "
                    "layout stability assessment relies on static shift prevention rules"
                ),
                severity=ValidationSeverity.INFO,
                field="cls",
            )
        )
        return CWVMetricResult(
            metric_name="CLS",
            status="NOT_APPLICABLE",
            observed_value=None,
            threshold_description="<= 0.1 Good, > 0.25 Poor",
            issues=issues,
        )

    # Validate type and finite range
    if not isinstance(observed_cls, (int, float)) or math.isnan(observed_cls) or math.isinf(observed_cls) or observed_cls < 0.0:
        issues.append(
            ValidationIssue(
                code="CWV_CLS_INVALID",
                message=f"Invalid CLS value '{observed_cls}'; must be a finite, non-negative number",
                severity=ValidationSeverity.CRITICAL,
                field="cls",
            )
        )
        return CWVMetricResult(
            metric_name="CLS",
            status="FAIL",
            observed_value=observed_cls if isinstance(observed_cls, (int, float)) and not math.isnan(observed_cls) else None,
            threshold_description="<= 0.1 Good, > 0.25 Poor",
            issues=issues,
        )

    val = float(observed_cls)

    if val <= CLS_GOOD_THRESHOLD:
        status = "PASS"
        issues.append(
            ValidationIssue(
                code="CWV_CLS_GOOD",
                message=f"Observed CLS of {val:.4f} satisfies layout stability threshold (<= {CLS_GOOD_THRESHOLD})",
                severity=ValidationSeverity.INFO,
                field="cls",
            )
        )
    elif val <= CLS_POOR_THRESHOLD:
        status = "NEEDS_IMPROVEMENT"
        issues.append(
            ValidationIssue(
                code="CWV_CLS_NEEDS_IMPROVEMENT",
                message=(
                    f"Observed CLS of {val:.4f} exceeds {CLS_GOOD_THRESHOLD} and needs improvement "
                    f"(target <= {CLS_GOOD_THRESHOLD})"
                ),
                severity=ValidationSeverity.WARNING,
                field="cls",
            )
        )
    else:
        status = "FAIL"
        issues.append(
            ValidationIssue(
                code="CWV_CLS_POOR",
                message=(
                    f"Observed CLS of {val:.4f} exceeds poor threshold ({CLS_POOR_THRESHOLD}); "
                    "violates layout stability standards"
                ),
                severity=ValidationSeverity.CRITICAL,
                field="cls",
            )
        )

    return CWVMetricResult(
        metric_name="CLS",
        status=status,
        observed_value=val,
        threshold_description="<= 0.1 Good, > 0.25 Poor",
        issues=issues,
    )


# ---------------------------------------------------------------------------
# 2. Explicit LCP and INP Gap Representation (CONF-001 Boundary)
# ---------------------------------------------------------------------------

def evaluate_lcp() -> CWVMetricResult:
    """Represent Largest Contentful Paint (LCP) strictly as NOT_APPLICABLE per CONF-001."""
    return CWVMetricResult(
        metric_name="LCP",
        status="NOT_APPLICABLE",
        observed_value=None,
        threshold_description=None,
        na_rationale=CONF_001_NA_RATIONALE,
        issues=[],
    )


def evaluate_inp() -> CWVMetricResult:
    """Represent Interaction to Next Paint (INP) strictly as NOT_APPLICABLE per CONF-001."""
    return CWVMetricResult(
        metric_name="INP",
        status="NOT_APPLICABLE",
        observed_value=None,
        threshold_description=None,
        na_rationale=CONF_001_NA_RATIONALE,
        issues=[],
    )


def assert_no_invented_thresholds(**kwargs: Any) -> None:
    """Assert that no synthetic or invented LCP/INP numeric thresholds were supplied."""
    for key, value in kwargs.items():
        if _INVENTED_THRESHOLD_PATTERN.match(key):
            if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().replace(".", "", 1).isdigit()):
                raise ValueError(
                    f"Invented numeric threshold for '{key}' prohibited by CONF-001 boundary: "
                    f"{CONF_001_NA_RATIONALE}"
                )


def validate_cwv_config(config: dict[str, Any]) -> list[ValidationIssue]:
    """Audit a configuration dictionary for attempted CONF-001 threshold fabrications."""
    issues: list[ValidationIssue] = []
    if not isinstance(config, dict):
        return issues

    for k, v in config.items():
        if _INVENTED_THRESHOLD_PATTERN.match(k):
            if isinstance(v, (int, float)) or (isinstance(v, str) and v.strip().replace(".", "", 1).isdigit()):
                issues.append(
                    ValidationIssue(
                        code="CWV_CONF_001_VIOLATION",
                        message=(
                            f"Configuration defines prohibited numeric threshold for '{k}' ({v}); "
                            f"{CONF_001_NA_RATIONALE}"
                        ),
                        severity=ValidationSeverity.CRITICAL,
                        field=k,
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# 3. Static Layout-Shift Prevention (Images & Web Fonts)
# ---------------------------------------------------------------------------

def _strip_css_comments(css: str) -> str:
    """Safely strip CSS block comments without recursion."""
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def analyze_font_display_css(css_content: str) -> list[ValidationIssue]:
    """Analyze CSS declarations for @font-face layout shift prevention."""
    issues: list[ValidationIssue] = []
    if not css_content:
        return issues

    clean_css = _strip_css_comments(css_content)

    # Find @font-face rules
    font_face_blocks = re.findall(r"@font-face\s*\{([^}]+)\}", clean_css, re.IGNORECASE)
    for idx, block in enumerate(font_face_blocks, 1):
        m = re.search(r"font-display\s*:\s*([a-zA-Z]+)", block, re.IGNORECASE)
        if not m:
            issues.append(
                ValidationIssue(
                    code="CWV_FONT_DISPLAY_MISSING",
                    message=(
                        f"@font-face block #{idx} is missing 'font-display' descriptor; "
                        "recommend 'font-display: swap' or 'optional' to prevent layout shifts"
                    ),
                    severity=ValidationSeverity.WARNING,
                    field="font-display",
                )
            )
        else:
            val = m.group(1).lower()
            if val in ("auto", "block"):
                issues.append(
                    ValidationIssue(
                        code="CWV_FONT_DISPLAY_NOT_SWAP",
                        message=(
                            f"@font-face block #{idx} uses 'font-display: {val}'; "
                            "recommend 'swap' or 'optional' to minimize layout shifts"
                        ),
                        severity=ValidationSeverity.WARNING,
                        field="font-display",
                    )
                )

    return issues


class FontDisplayHTMLParser(HTMLParser):
    """Linear streaming extractor for font stylesheets and inline font declarations."""

    def __init__(self) -> None:
        super().__init__()
        self.in_style = False
        self.style_buffer: list[str] = []
        self.font_stylesheet_hrefs: list[str] = []
        self.style_contents: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower == "style":
            self.in_style = True
            self.style_buffer = []
        elif tag_lower == "link":
            attr_dict = {k.lower(): (v or "").strip() for k, v in attrs}
            rel = attr_dict.get("rel", "").lower()
            href = attr_dict.get("href", "")
            if rel == "stylesheet" and href:
                # Detect font providers or font stylesheets
                lower_href = href.lower()
                if "fonts.googleapis.com" in lower_href or "use.typekit.net" in lower_href or "font" in lower_href:
                    self.font_stylesheet_hrefs.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "style" and self.in_style:
            self.in_style = False
            self.style_contents.append("".join(self.style_buffer))
            self.style_buffer = []

    def handle_data(self, data: str) -> None:
        if self.in_style:
            self.style_buffer.append(data)


def analyze_font_display_html(html_content: str) -> list[ValidationIssue]:
    """Analyze font link elements and style blocks in rendered HTML for font-display issues."""
    issues: list[ValidationIssue] = []
    if not html_content:
        return issues

    parser = FontDisplayHTMLParser()
    parser.feed(html_content)
    parser.close()

    # 1. Check font stylesheet <link> URLs (e.g. Google Fonts)
    for href in parser.font_stylesheet_hrefs:
        parsed = urllib.parse.urlparse(href)
        query_params = urllib.parse.parse_qs(parsed.query)
        if "fonts.googleapis.com" in parsed.hostname.lower() if parsed.hostname else "":
            display_val = query_params.get("display", [""])[0].lower()
            if display_val != "swap":
                issues.append(
                    ValidationIssue(
                        code="CWV_FONT_DISPLAY_MISSING",
                        message=(
                            f"Google Font stylesheet link '{href}' does not specify 'display=swap'; "
                            "may cause Flash of Invisible Text or layout shifts"
                        ),
                        severity=ValidationSeverity.WARNING,
                        field="href",
                    )
                )

    # 2. Check inline <style> blocks
    for style_text in parser.style_contents:
        issues.extend(analyze_font_display_css(style_text))

    return issues


def analyze_static_shift_prevention(html_content: str) -> StaticShiftPreventionResult:
    """Analyze rendered HTML for static layout-shift causes (missing image dimensions & font-display).
    
    Reuses approved image dimension analysis from domain.seo.media.
    """
    issues: list[ValidationIssue] = []

    # 1. Reuse existing image dimension analysis from domain.seo.media
    media_res = analyze_media(html_content)
    images_lacking_dimensions = 0
    for img_issue in media_res.issues:
        if img_issue.code == "IMAGE_DIMENSIONS_MISSING":
            images_lacking_dimensions += 1
            issues.append(img_issue)

    # 2. Font-display layout-shift checks
    font_issues = analyze_font_display_html(html_content)
    issues.extend(font_issues)

    return StaticShiftPreventionResult(
        total_images_analyzed=media_res.total_images,
        images_lacking_dimensions=images_lacking_dimensions,
        font_issues_count=len(font_issues),
        issues=issues,
    )


# ---------------------------------------------------------------------------
# 4. Aggregate CWV Analyzer
# ---------------------------------------------------------------------------

def analyze_cwv(
    html_content: str = "",
    observed_cls: float | None = None,
    **kwargs: Any,
) -> CWVAnalysisResult:
    """Aggregate Core Web Vitals analyzer strictly preserving the CONF-001 boundary.
    
    - Evaluates CLS against approved researched thresholds (<= 0.1, > 0.25).
    - Analyzes static layout shift prevention (image dimensions & font-display).
    - Explicitly represents LCP and INP as NOT_APPLICABLE with approved rationale.
    - Rejects any supplied synthetic or invented LCP/INP numeric thresholds.
    """
    # Guard against invented thresholds
    assert_no_invented_thresholds(**kwargs)

    cls_result = evaluate_cls(observed_cls)
    lcp_result = evaluate_lcp()
    inp_result = evaluate_inp()
    static_result = analyze_static_shift_prevention(html_content)

    all_issues: list[ValidationIssue] = []
    all_issues.extend(cls_result.issues)
    all_issues.extend(lcp_result.issues)
    all_issues.extend(inp_result.issues)
    all_issues.extend(static_result.issues)

    # Valid if no critical issues in CLS or static layout prevention
    is_valid = not any(i.severity == ValidationSeverity.CRITICAL for i in all_issues)

    return CWVAnalysisResult(
        cls=cls_result,
        lcp=lcp_result,
        inp=inp_result,
        static_prevention=static_result,
        is_valid=is_valid,
        conf_001_status="UNRESOLVED",
        issues=all_issues,
    )
