"""P9 URL Architecture, Redirect Taxonomy & Pagination Engine.

Implements REQ-P9-06:
- URL architecture analysis (lowercase normalization, hyphenated slug validation, trailing-slash policy).
- Preserves unmutated CMS content (pure analysis and functional normalization).
- Redirect taxonomy analysis (loop detection, chain detection, status-code verification).
- Open-redirect security validation (relative destination allowlist, canonical domain enforcement, SSRF defense).
- Strictly static graph analysis without network crawling or HTTP requests.
- Paginated collection canonicalization analysis (rel="prev"/rel="next" vs page 1 canonicalization).
- Python stdlib HTMLParser for extracting pagination link elements from HTML (UQ-P9-04).
"""
from __future__ import annotations

import re
import urllib.parse
from html.parser import HTMLParser
from typing import Any

from framework.domain.seo.metadata import _is_private_or_loopback_host
from framework.domain.seo.model import (
    PaginationAnalysisResult,
    PaginationSignals,
    RedirectAnalysisResult,
    RedirectChain,
    RedirectHop,
    RedirectRule,
    ValidationIssue,
    ValidationSeverity,
)

# Standard HTTP redirect status codes supported in the taxonomy
ALLOWED_REDIRECT_STATUS_CODES = {301, 302, 307, 308}
PERMANENT_STATUS_CODES = {301, 308}
TEMPORARY_STATUS_CODES = {302, 307}

# Dangerous schemes to reject in redirects
UNSAFE_REDIRECT_SCHEMES = {"javascript", "data", "vbscript", "file"}


# ---------------------------------------------------------------------------
# 1. URL Taxonomy & Slug Normalization
# ---------------------------------------------------------------------------

def normalize_slug(slug: str, trailing_slash: bool = False) -> str:
    """Deterministically normalize a URL path or slug without mutating original data.
    
    Rules:
    - Lowercase conversion
    - Replaces spaces / %20 and underscores with hyphens
    - Collapses multiple hyphens and slashes
    - Preserves file extensions (e.g. .html)
    - Enforces consistent trailing slash policy (except root '/')
    """
    if not slug:
        return "/"

    # Strip surrounding whitespace
    s = slug.strip()

    # Parse path component if a full URL was provided
    parsed = urllib.parse.urlparse(s)
    path = parsed.path if parsed.path else s

    # Lowercase
    path = path.lower()

    # Replace spaces and encoded spaces with hyphens
    path = path.replace("%20", "-").replace(" ", "-")

    # Replace underscores with hyphens
    path = path.replace("_", "-")

    # Remove illegal characters (keep alphanumeric, '/', '-', '.', '~')
    path = re.sub(r"[^a-z0-9/\-.~]", "", path)

    # Collapse multiple hyphens into a single hyphen
    path = re.sub(r"-+", "-", path)

    # Collapse multiple slashes into a single slash
    path = re.sub(r"/+", "/", path)

    # Ensure leading slash
    if not path.startswith("/"):
        path = f"/{path}"

    # Trailing slash consistency (root '/' always has a slash)
    if path != "/":
        if trailing_slash and not path.endswith("/"):
            path = f"{path}/"
        elif not trailing_slash and path.endswith("/"):
            path = path[:-1]

    # Reattach clean query if present (without trailing tracking params)
    return path


def validate_url_taxonomy(url_or_path: str, trailing_slash: bool = False) -> list[ValidationIssue]:
    """Validate a URL path or slug against search-engine URL architecture rules."""
    issues: list[ValidationIssue] = []
    if not url_or_path or not url_or_path.strip():
        issues.append(
            ValidationIssue(
                code="URL_EMPTY",
                message="URL path is empty or whitespace",
                severity=ValidationSeverity.CRITICAL,
                field="url",
            )
        )
        return issues

    raw = url_or_path.strip()
    parsed = urllib.parse.urlparse(raw)
    path = parsed.path or "/"

    # 1. Casing check
    if any(c.isupper() for c in path):
        issues.append(
            ValidationIssue(
                code="URL_NOT_LOWERCASE",
                message=f"URL path '{path}' contains uppercase characters; search engines recommend lowercase URLs",
                severity=ValidationSeverity.WARNING,
                field="url",
            )
        )

    # 2. Underscores check
    if "_" in path:
        issues.append(
            ValidationIssue(
                code="URL_CONTAINS_UNDERSCORE",
                message=f"URL path '{path}' contains underscores; hyphens are recommended word separators",
                severity=ValidationSeverity.INFO,
                field="url",
            )
        )

    # 3. Spaces check
    if " " in raw or "%20" in raw.lower():
        issues.append(
            ValidationIssue(
                code="URL_CONTAINS_SPACES",
                message=f"URL path '{path}' contains spaces or encoded spaces (%20); use hyphens instead",
                severity=ValidationSeverity.WARNING,
                field="url",
            )
        )

    # 4. Consecutive hyphens check
    if "--" in path:
        issues.append(
            ValidationIssue(
                code="URL_CONSECUTIVE_HYPHENS",
                message=f"URL path '{path}' contains redundant consecutive hyphens ('--')",
                severity=ValidationSeverity.WARNING,
                field="url",
            )
        )

    # 5. Special characters check
    clean_chars = re.sub(r"[a-zA-Z0-9/\-.~_]", "", path)
    if clean_chars:
        issues.append(
            ValidationIssue(
                code="URL_SPECIAL_CHARACTERS",
                message=f"URL path '{path}' contains special characters ('{clean_chars}')",
                severity=ValidationSeverity.WARNING,
                field="url",
            )
        )

    # 6. Trailing slash consistency check
    if path != "/":
        has_trailing = path.endswith("/")
        if trailing_slash and not has_trailing:
            issues.append(
                ValidationIssue(
                    code="URL_TRAILING_SLASH_INCONSISTENT",
                    message=f"URL path '{path}' lacks expected trailing slash according to site policy",
                    severity=ValidationSeverity.WARNING,
                    field="url",
                )
            )
        elif not trailing_slash and has_trailing:
            issues.append(
                ValidationIssue(
                    code="URL_TRAILING_SLASH_INCONSISTENT",
                    message=f"URL path '{path}' has trailing slash violating site no-trailing-slash policy",
                    severity=ValidationSeverity.WARNING,
                    field="url",
                )
            )

    return issues


# ---------------------------------------------------------------------------
# 2. Redirect Taxonomy & Security Analysis (Threat Model §5.4)
# ---------------------------------------------------------------------------

def _clean_route_key(path_or_url: str) -> str:
    """Normalize a URL path or URL string into a stable route key for graph analysis."""
    if not path_or_url:
        return "/"
    parsed = urllib.parse.urlparse(path_or_url.strip())
    path = parsed.path or "/"
    norm = re.sub(r"/+", "/", path).lower()
    if len(norm) > 1 and norm.endswith("/"):
        norm = norm[:-1]
    return norm


def _validate_redirect_destination(
    target: str,
    canonical_domain: str = "",
    allow_external: bool = False,
) -> list[ValidationIssue]:
    """Validate a redirect target against open-redirect and SSRF threats."""
    issues: list[ValidationIssue] = []
    clean_target = target.strip()

    if not clean_target:
        issues.append(
            ValidationIssue(
                code="REDIRECT_TARGET_EMPTY",
                message="Redirect target destination is empty",
                severity=ValidationSeverity.CRITICAL,
                field="target",
            )
        )
        return issues

    # Reject protocol-relative open redirects (e.g. //evil.com/phish)
    if clean_target.startswith("//"):
        issues.append(
            ValidationIssue(
                code="REDIRECT_OPEN_REDIRECT",
                message=f"Protocol-relative redirect destination '{clean_target}' is an open-redirect vulnerability",
                severity=ValidationSeverity.CRITICAL,
                field="target",
            )
        )
        return issues

    parsed = urllib.parse.urlparse(clean_target)
    scheme = parsed.scheme.lower()

    # Reject dangerous schemes
    if scheme in UNSAFE_REDIRECT_SCHEMES:
        issues.append(
            ValidationIssue(
                code="REDIRECT_UNSAFE_SCHEME",
                message=f"Redirect destination uses dangerous scheme '{scheme}:'",
                severity=ValidationSeverity.CRITICAL,
                field="target",
            )
        )
        return issues

    # Handle absolute URLs
    if scheme in ("http", "https"):
        hostname = (parsed.hostname or "").lower()

        # Check SSRF / private IP destination
        if _is_private_or_loopback_host(hostname):
            issues.append(
                ValidationIssue(
                    code="REDIRECT_PRIVATE_IP_REJECTED",
                    message=f"Redirect destination points to private or loopback host '{hostname}'",
                    severity=ValidationSeverity.CRITICAL,
                    field="target",
                )
            )

        # Check domain boundary
        if not allow_external:
            canon_parsed = urllib.parse.urlparse(canonical_domain) if canonical_domain else None
            canon_host = (canon_parsed.hostname or "").lower() if (canon_parsed and canon_parsed.hostname) else canonical_domain.lower()

            if canon_host:
                if hostname != canon_host:
                    issues.append(
                        ValidationIssue(
                            code="REDIRECT_OPEN_REDIRECT",
                            message=(
                                f"External redirect to host '{hostname}' escapes canonical domain '{canon_host}' "
                                "without explicit external authorization"
                            ),
                            severity=ValidationSeverity.CRITICAL,
                            field="target",
                        )
                    )
            else:
                # Without a canonical domain specified, absolute URLs with foreign hosts trigger open redirect
                issues.append(
                    ValidationIssue(
                        code="REDIRECT_OPEN_REDIRECT",
                        message=(
                            f"Absolute external redirect to '{clean_target}' is not permitted without "
                            "explicit allowlist flag"
                        ),
                        severity=ValidationSeverity.CRITICAL,
                        field="target",
                    )
                )

    return issues


def analyze_redirect_graph(
    rules: list[RedirectRule] | list[dict[str, Any]],
    canonical_domain: str = "",
) -> RedirectAnalysisResult:
    """Statically analyze a redirect inventory for loops, chains, and open redirects.
    
    Uses deterministic directed-graph algorithms without making live HTTP requests.
    """
    rule_models: list[RedirectRule] = []
    for r in rules:
        if isinstance(r, RedirectRule):
            rule_models.append(r)
        elif isinstance(r, dict):
            rule_models.append(RedirectRule.from_dict(r))

    issues: list[ValidationIssue] = []

    # Map normalized source -> (target, status_code, original_rule)
    graph: dict[str, tuple[str, int, RedirectRule]] = {}
    valid_rules_count = 0

    # 1. Validate individual rules
    for rule in rule_models:
        rule_issues = []

        # Validate status code
        if rule.status_code not in ALLOWED_REDIRECT_STATUS_CODES:
            rule_issues.append(
                ValidationIssue(
                    code="REDIRECT_INVALID_STATUS_CODE",
                    message=(
                        f"Redirect from '{rule.source}' specifies invalid status code {rule.status_code}; "
                        f"must be one of {sorted(ALLOWED_REDIRECT_STATUS_CODES)}"
                    ),
                    severity=ValidationSeverity.CRITICAL,
                    field=rule.source,
                )
            )

        # Validate open redirect security
        dest_issues = _validate_redirect_destination(
            target=rule.target,
            canonical_domain=canonical_domain,
            allow_external=rule.allow_external,
        )
        rule_issues.extend(dest_issues)

        # Self-loop check
        src_key = _clean_route_key(rule.source)
        tgt_key = _clean_route_key(rule.target)
        if src_key == tgt_key:
            rule_issues.append(
                ValidationIssue(
                    code="REDIRECT_SELF_LOOP",
                    message=f"Immediate self-redirect loop detected: '{rule.source}' -> '{rule.target}'",
                    severity=ValidationSeverity.CRITICAL,
                    field=rule.source,
                )
            )

        issues.extend(rule_issues)

        if not any(i.severity == ValidationSeverity.CRITICAL for i in rule_issues):
            valid_rules_count += 1
            graph[src_key] = (tgt_key, rule.status_code, rule)

    # 2. Graph analysis for multi-hop chains and cycles
    chains: list[RedirectChain] = []
    loop_count = 0
    chain_count = 0

    # Check each starting node in the graph
    for start_node in sorted(graph.keys()):
        visited = [start_node]
        current = start_node
        hops: list[RedirectHop] = []
        is_loop = False

        while current in graph:
            next_node, code, r_obj = graph[current]
            hops.append(RedirectHop(source=r_obj.source, target=r_obj.target, status_code=code))

            if next_node in visited:
                # Cycle / loop detected
                is_loop = True
                loop_count += 1
                loop_path = " -> ".join([h.source for h in hops] + [r_obj.target])
                issues.append(
                    ValidationIssue(
                        code="REDIRECT_LOOP_DETECTED",
                        message=f"Circular redirect loop detected: {loop_path}",
                        severity=ValidationSeverity.CRITICAL,
                        field=start_node,
                    )
                )
                break

            visited.append(next_node)
            current = next_node

        hop_count = len(hops)
        if hop_count > 1 and not is_loop:
            # Multi-hop redirect chain (> 1 hop)
            chain_count += 1
            chain_path = " -> ".join([h.source for h in hops] + [hops[-1].target])
            issues.append(
                ValidationIssue(
                    code="REDIRECT_CHAIN_DETECTED",
                    message=(
                        f"Redirect chain detected ({hop_count} hops): {chain_path}; "
                        f"recommend direct redirect '{hops[0].source}' -> '{hops[-1].target}'"
                    ),
                    severity=ValidationSeverity.WARNING,
                    field=start_node,
                )
            )

        if hop_count > 0:
            chains.append(
                RedirectChain(
                    start_url=start_node,
                    final_target=hops[-1].target if hops else "",
                    hops=hops,
                    hop_count=hop_count,
                    is_loop=is_loop,
                )
            )

    return RedirectAnalysisResult(
        total_rules=len(rule_models),
        valid_count=valid_rules_count,
        loop_count=loop_count,
        chain_count=chain_count,
        chains=chains,
        issues=issues,
    )


# ---------------------------------------------------------------------------
# 3. Pagination Canonicalization Analysis (REQ-P9-06 Criterion 4)
# ---------------------------------------------------------------------------

class PaginationHTMLParser(HTMLParser):
    """Linear streaming extractor for pagination <link> elements in HTML <head>."""

    def __init__(self) -> None:
        super().__init__()
        self.canonical_url: str | None = None
        self.prev_url: str | None = None
        self.next_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "link":
            attr_dict = {k.lower(): (v or "").strip() for k, v in attrs}
            rel = attr_dict.get("rel", "").lower()
            href = attr_dict.get("href")

            if href:
                if rel == "canonical":
                    self.canonical_url = href
                elif rel == "prev":
                    self.prev_url = href
                elif rel == "next":
                    self.next_url = href


def validate_pagination_signals(signals: PaginationSignals) -> list[ValidationIssue]:
    """Validate paginated collection signals for canonicalization conflicts and errors."""
    issues: list[ValidationIssue] = []

    # 1. Page number validity
    if signals.page < 1:
        issues.append(
            ValidationIssue(
                code="PAGINATION_INVALID_PAGE_NUMBER",
                message=f"Pagination page number {signals.page} must be an integer >= 1",
                severity=ValidationSeverity.CRITICAL,
                field="page",
            )
        )
        return issues

    # 2. First page rules
    if signals.page == 1 and signals.prev_url:
        issues.append(
            ValidationIssue(
                code="PAGINATION_PREV_ON_FIRST_PAGE",
                message=f"First page (page 1) must not define rel='prev' link ('{signals.prev_url}')",
                severity=ValidationSeverity.WARNING,
                field="prev_url",
            )
        )

    # 3. Subsequent pages rules
    if signals.page > 1 and not signals.prev_url:
        issues.append(
            ValidationIssue(
                code="PAGINATION_MISSING_PREV",
                message=f"Page {signals.page} is missing required rel='prev' link to preceding page",
                severity=ValidationSeverity.WARNING,
                field="prev_url",
            )
        )

    # 4. Last page rules (when total_pages is known)
    if signals.total_pages is not None:
        if signals.page > signals.total_pages:
            issues.append(
                ValidationIssue(
                    code="PAGINATION_PAGE_EXCEEDS_TOTAL",
                    message=f"Page {signals.page} exceeds declared total pages ({signals.total_pages})",
                    severity=ValidationSeverity.WARNING,
                    field="page",
                )
            )
        elif signals.page == signals.total_pages and signals.next_url:
            issues.append(
                ValidationIssue(
                    code="PAGINATION_NEXT_ON_LAST_PAGE",
                    message=f"Last page (page {signals.page}) must not define rel='next' link ('{signals.next_url}')",
                    severity=ValidationSeverity.WARNING,
                    field="next_url",
                )
            )

    # 5. Circular links check
    if signals.prev_url and signals.current_url:
        if _clean_route_key(signals.prev_url) == _clean_route_key(signals.current_url):
            issues.append(
                ValidationIssue(
                    code="PAGINATION_CIRCULAR_LINK",
                    message=f"rel='prev' points circularly to the current page URL ('{signals.current_url}')",
                    severity=ValidationSeverity.CRITICAL,
                    field="prev_url",
                )
            )

    if signals.next_url and signals.current_url:
        if _clean_route_key(signals.next_url) == _clean_route_key(signals.current_url):
            issues.append(
                ValidationIssue(
                    code="PAGINATION_CIRCULAR_LINK",
                    message=f"rel='next' points circularly to the current page URL ('{signals.current_url}')",
                    severity=ValidationSeverity.CRITICAL,
                    field="next_url",
                )
            )

    # 6. Canonicalization strategy check
    if signals.canonical_url and signals.current_url:
        canon_key = _clean_route_key(signals.canonical_url)
        curr_key = _clean_route_key(signals.current_url)

        if signals.strategy == "self":
            # Self-referencing canonical model (standard Google recommendation)
            # Each paginated page should canonicalize to itself
            if signals.page > 1 and canon_key != curr_key:
                # If pointing to page 1 while on page > 1 with prev/next signals:
                issues.append(
                    ValidationIssue(
                        code="PAGINATION_CONFLICTING_SIGNALS",
                        message=(
                            f"Page {signals.page} emits rel='prev'/'next' links but canonical URL points to "
                            f"'{signals.canonical_url}' instead of self ('{signals.current_url}'); "
                            "causes search engine canonicalization conflict"
                        ),
                        severity=ValidationSeverity.WARNING,
                        field="canonical_url",
                    )
                )

    return issues


def analyze_pagination_html(
    html_content: str,
    current_page: int = 1,
    total_pages: int | None = None,
    strategy: str = "self",
    current_url: str = "",
) -> PaginationAnalysisResult:
    """Extract and validate pagination signals from rendered HTML document."""
    parser = PaginationHTMLParser()
    parser.feed(html_content or "")
    parser.close()

    signals = PaginationSignals(
        page=current_page,
        total_pages=total_pages,
        current_url=current_url,
        canonical_url=parser.canonical_url,
        prev_url=parser.prev_url,
        next_url=parser.next_url,
        strategy=strategy,
    )

    issues = validate_pagination_signals(signals)
    is_valid = not any(i.severity == ValidationSeverity.CRITICAL for i in issues)

    return PaginationAnalysisResult(
        signals=signals,
        is_valid=is_valid,
        issues=issues,
    )
