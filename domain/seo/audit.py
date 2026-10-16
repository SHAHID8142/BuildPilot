"""P9 Pre-Deployment SEO Audit Engine (REQ-P9-09).

Implements:
- Full pre-deployment audit orchestrating all 16+ roadmap dimensions (REQ-P9-01..08).
- Dual-mode execution:
    * advisory mode: reports findings without failing builds (exit code 0).
    * deployment mode: non-zero exit (exit code 1) on CRITICAL defects.
- Deterministic structured output:
    * JSON audit report conforming to sps2/schemas/p9-audit.schema.json.
    * Markdown human-readable summary report.
    * Formal EV-SEO-* evidence record conforming to sps2/governance/SCHEMAS/evidence.schema.json.
- Deterministic SHA-256 artifact digest of audited files/routes.
- Strict preservation of the CONF-001 boundary:
    * CLS uses only verified thresholds (<= 0.1, > 0.25).
    * LCP and INP are strictly reported as NOT_APPLICABLE with the exact authorized rationale:
      "Unobserved research threshold per CONF-001; numeric thresholds not established. No synthetic thresholds permitted."
    * Zero invented LCP/INP numeric thresholds.
- Pure Python standard library only; project-local; zero network crawling.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from domain.seo.cwv import (
    CONF_001_NA_RATIONALE,
    analyze_cwv,
    evaluate_cls,
    evaluate_inp,
    evaluate_lcp,
)
from domain.seo.indexing import (
    parse_robots_txt,
    parse_sitemap_xml,
)
from domain.seo.media import analyze_media
from domain.seo.metadata import (
    validate_canonical_url,
    validate_metadata,
)
from domain.seo.model import (
    AuditCheck,
    AuditDimension,
    AuditReport,
    AuditSummary,
    RedirectRule,
    SEOMetadata,
    ValidationIssue,
    ValidationSeverity,
)
from domain.seo.onpage import (
    analyze_headings,
    analyze_links,
)
from domain.seo.specialized import (
    DEFAULT_ECOMMERCE_NA_RATIONALE,
    DEFAULT_LOCAL_NA_RATIONALE,
    DEFAULT_MULTILINGUAL_NA_RATIONALE,
    analyze_specialized_dimensions,
    extract_hreflang_from_html,
)
from domain.seo.structured_data import (
    extract_json_ld_from_html,
    validate_structured_data,
)
from domain.seo.url_taxonomy import (
    analyze_pagination_html,
    analyze_redirect_graph,
    validate_url_taxonomy,
)

# ---------------------------------------------------------------------------
# Schema Validation Helper (pure stdlib conformance to p9-audit.schema.json)
# ---------------------------------------------------------------------------

_AUDIT_ID_REGEX = re.compile(r"^AUDIT-SEO-[0-9]{8}-[0-9]{4,}$")
_EVIDENCE_REF_REGEX = re.compile(r"^EV-SEO-[0-9]{3,}$")
_DIGEST_REGEX = re.compile(r"^[a-f0-9]{64}$")


def validate_audit_report_schema(report_dict: dict[str, Any]) -> list[str]:
    """Validate an audit report dictionary against sps2/schemas/p9-audit.schema.json rules."""
    errors: list[str] = []

    # Required and allowed top-level fields
    required_fields = [
        "audit_id",
        "timestamp",
        "mode",
        "exit_code",
        "summary",
        "dimensions",
        "evidence_ref",
    ]
    allowed_top_level = {
        "audit_id",
        "timestamp",
        "mode",
        "exit_code",
        "summary",
        "dimensions",
        "evidence_ref",
        "audited_artifacts_digest",
    }
    for k in report_dict:
        if k not in allowed_top_level:
            errors.append(f"Unexpected top-level property '{k}'")

    for rf in required_fields:
        if rf not in report_dict:
            errors.append(f"Missing required top-level property '{rf}'")

    if errors:
        return errors

    # audit_id format
    audit_id = report_dict.get("audit_id", "")
    if not _AUDIT_ID_REGEX.match(audit_id):
        errors.append(f"audit_id '{audit_id}' does not match pattern ^AUDIT-SEO-[0-9]{{8}}-[0-9]{{4,}}$")

    # mode
    mode = report_dict.get("mode")
    if mode not in ("advisory", "deployment"):
        errors.append(f"mode must be 'advisory' or 'deployment', got '{mode}'")

    # exit_code
    exit_code = report_dict.get("exit_code")
    if exit_code not in (0, 1, 2):
        errors.append(f"exit_code must be 0, 1, or 2, got '{exit_code}'")

    # summary
    summary = report_dict.get("summary", {})
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
    else:
        allowed_summary = {"total_checks", "passed", "warnings", "critical", "not_applicable"}
        for k in summary:
            if k not in allowed_summary:
                errors.append(f"Unexpected summary property '{k}'")
        for sf in ("total_checks", "passed", "warnings", "critical", "not_applicable"):
            if sf not in summary:
                errors.append(f"summary missing required property '{sf}'")
            elif not isinstance(summary[sf], int) or summary[sf] < 0:
                errors.append(f"summary.{sf} must be a non-negative integer")

    # dimensions (minItems: 16)
    dimensions = report_dict.get("dimensions", [])
    if not isinstance(dimensions, list):
        errors.append("dimensions must be an array")
    elif len(dimensions) < 16:
        errors.append(f"dimensions array has {len(dimensions)} items; schema requires at least 16")
    else:
        allowed_dim = {"dimension_id", "dimension_name", "status", "na_rationale", "checks"}
        allowed_chk = {"check_id", "name", "result", "severity", "message", "target_url"}
        for idx, dim in enumerate(dimensions):
            dim_path = f"dimensions[{idx}]"
            if not isinstance(dim, dict):
                errors.append(f"{dim_path} must be an object")
                continue
            for k in dim:
                if k not in allowed_dim:
                    errors.append(f"Unexpected property '{k}' in {dim_path}")
            for df in ("dimension_id", "dimension_name", "status"):
                if df not in dim:
                    errors.append(f"{dim_path} missing required property '{df}'")

            status = dim.get("status")
            if status not in ("PASS", "WARNING", "FAIL", "NOT_APPLICABLE"):
                errors.append(f"{dim_path}.status has invalid enum value '{status}'")

            # Mandatory na_rationale if NOT_APPLICABLE
            if status == "NOT_APPLICABLE":
                na_rat = dim.get("na_rationale")
                if not na_rat or not isinstance(na_rat, str) or not na_rat.strip():
                    errors.append(f"{dim_path} status is NOT_APPLICABLE but 'na_rationale' is missing or empty")

            # checks
            checks = dim.get("checks", [])
            if isinstance(checks, list):
                for c_idx, chk in enumerate(checks):
                    chk_path = f"{dim_path}.checks[{c_idx}]"
                    if not isinstance(chk, dict):
                        errors.append(f"{chk_path} must be an object")
                        continue
                    for k in chk:
                        if k not in allowed_chk:
                            errors.append(f"Unexpected property '{k}' in {chk_path}")
                    for cf in ("check_id", "name", "result", "severity"):
                        if cf not in chk:
                            errors.append(f"{chk_path} missing required property '{cf}'")
                    if chk.get("result") not in ("PASS", "FAIL", "NA"):
                        errors.append(f"{chk_path}.result has invalid enum value '{chk.get('result')}'")
                    if chk.get("severity") not in ("INFO", "WARNING", "CRITICAL"):
                        errors.append(f"{chk_path}.severity has invalid enum value '{chk.get('severity')}'")

    # evidence_ref
    ev_ref = report_dict.get("evidence_ref", "")
    if not _EVIDENCE_REF_REGEX.match(ev_ref):
        errors.append(f"evidence_ref '{ev_ref}' does not match pattern ^EV-SEO-[0-9]{{3,}}$")

    # audited_artifacts_digest
    digest = report_dict.get("audited_artifacts_digest", "")
    if digest and not _DIGEST_REGEX.match(digest):
        errors.append(f"audited_artifacts_digest '{digest}' does not match pattern ^[a-f0-9]{{64}}$")

    return errors


# ---------------------------------------------------------------------------
# Formatting Helpers (Markdown and Formal Evidence Record)
# ---------------------------------------------------------------------------

def render_audit_markdown(report: AuditReport) -> str:
    """Render an AuditReport as human-readable GitHub-flavored markdown."""
    status_icon = "PASS (CLEAN)" if report.exit_code == 0 else "FAIL (CRITICAL DEFECTS)"
    lines = [
        f"# SPS 2.0 SEO Pre-Deployment Audit Report",
        f"",
        f"- **Audit ID**: `{report.audit_id}`",
        f"- **Timestamp**: `{report.timestamp}`",
        f"- **Execution Mode**: `{report.mode}`",
        f"- **Exit Code**: `{report.exit_code}` ({status_icon})",
        f"- **Evidence Reference**: `{report.evidence_ref}`",
        f"- **Artifacts Digest**: `{report.audited_artifacts_digest}`",
        f"",
        f"## Summary Metrics",
        f"",
        f"| Metric | Count |",
        f"|---|---|",
        f"| Total Checks | {report.summary.total_checks} |",
        f"| Passed | {report.summary.passed} |",
        f"| Warnings | {report.summary.warnings} |",
        f"| Critical Defects | {report.summary.critical} |",
        f"| Not Applicable (N/A) | {report.summary.not_applicable} |",
        f"",
        f"## Dimension Breakdown (16+ Roadmap Dimensions)",
        f"",
        f"| # | Dimension ID | Dimension Name | Status | Rationale / Note |",
        f"|---|---|---|---|---|",
    ]

    for idx, d in enumerate(report.dimensions, 1):
        note = d.na_rationale if d.status == "NOT_APPLICABLE" else f"{len(d.checks)} check(s)"
        lines.append(f"| {idx} | `{d.dimension_id}` | {d.dimension_name} | **{d.status}** | {note} |")

    # List any issues/failures
    critical_checks: list[AuditCheck] = []
    warning_checks: list[AuditCheck] = []
    for d in report.dimensions:
        for c in d.checks:
            if c.result == "FAIL":
                if c.severity == "CRITICAL":
                    critical_checks.append(c)
                elif c.severity == "WARNING":
                    warning_checks.append(c)

    if critical_checks:
        lines.extend([
            f"",
            f"### CRITICAL Findings (Deployment Blocking in Deployment Mode)",
            f"",
        ])
        for c in critical_checks:
            url_str = f" (`{c.target_url}`)" if c.target_url else ""
            lines.append(f"- **[{c.check_id}] {c.name}**{url_str}: {c.message}")

    if warning_checks:
        lines.extend([
            f"",
            f"### WARNING Findings (Advisory)",
            f"",
        ])
        for c in warning_checks:
            url_str = f" (`{c.target_url}`)" if c.target_url else ""
            lines.append(f"- **[{c.check_id}] {c.name}**{url_str}: {c.message}")

    lines.append("")
    return "\n".join(lines)


def build_evidence_record(report: AuditReport, command: str = "") -> dict[str, Any]:
    """Generate a formal SPS 2.0 evidence record conforming to sps2/governance/SCHEMAS/evidence.schema.json."""
    result_enum = "PASS" if report.exit_code == 0 else "FAIL"
    cmd_str = command or f"python3 sps2/tools/seo_audit.py --mode={report.mode}"
    observed_str = (
        f"{report.audit_id}: {len(report.dimensions)} dimensions evaluated, "
        f"{report.summary.passed} passed, {report.summary.warnings} warnings, "
        f"{report.summary.critical} critical, exit {report.exit_code}"
    )

    return {
        "evidence_id": report.evidence_ref,
        "source": "VALIDATOR",
        "timestamp": report.timestamp,
        "command": cmd_str,
        "expected_result": (
            "Clean pre-deployment audit with 0 CRITICAL findings"
            if report.mode == "deployment"
            else "Advisory pre-deployment audit report"
        ),
        "observed_result": observed_str,
        "result": result_enum,
        "exit_code": report.exit_code,
        "relates_to": {
            "requirement_id": "REQ-P9-09",
        },
    }


# ---------------------------------------------------------------------------
# Core Pre-Deployment SEO Audit Engine
# ---------------------------------------------------------------------------

def run_seo_audit(
    pages: dict[str, str] | None = None,
    robots_txt_content: str | None = None,
    sitemap_xml_content: str | None = None,
    redirect_rules: list[dict[str, Any]] | list[RedirectRule] | None = None,
    canonical_domain: str = "https://example.com",
    mode: str = "advisory",
    observed_cls: float | None = None,
    is_multilingual: bool = False,
    multilingual_na_rationale: str | None = None,
    is_local_business: bool = False,
    local_na_rationale: str | None = None,
    is_ecommerce: bool = False,
    ecommerce_na_rationale: str | None = None,
    audit_counter: int = 1,
    evidence_counter: int = 1,
    command: str = "",
) -> AuditReport:
    """Execute a comprehensive, deterministic pre-deployment SEO audit over all 16+ dimensions."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    audit_id = f"AUDIT-SEO-{date_str}-{audit_counter:04d}"
    evidence_ref = f"EV-SEO-{evidence_counter:03d}"
    timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    pages_dict = pages or {}

    # Calculate deterministic SHA-256 digest of audited artifacts
    digest_hasher = hashlib.sha256()
    for route in sorted(pages_dict.keys()):
        digest_hasher.update(route.encode("utf-8"))
        digest_hasher.update(pages_dict[route].encode("utf-8"))
    if robots_txt_content:
        digest_hasher.update(b"robots.txt:")
        digest_hasher.update(robots_txt_content.encode("utf-8"))
    if sitemap_xml_content:
        digest_hasher.update(b"sitemap.xml:")
        digest_hasher.update(sitemap_xml_content.encode("utf-8"))
    if redirect_rules:
        digest_hasher.update(b"redirects:")
        digest_hasher.update(json.dumps([r.to_dict() if hasattr(r, "to_dict") else r for r in redirect_rules], sort_keys=True).encode("utf-8"))
    audited_digest = digest_hasher.hexdigest()

    dimensions: list[AuditDimension] = []
    total_checks = 0
    passed_checks = 0
    warning_checks = 0
    critical_checks = 0
    na_checks = 0

    def add_dimension(
        dim_id: str,
        dim_name: str,
        status: str,
        checks: list[AuditCheck],
        na_rationale: str | None = None,
    ) -> None:
        nonlocal total_checks, passed_checks, warning_checks, critical_checks, na_checks
        for c in checks:
            total_checks += 1
            if c.result == "PASS":
                passed_checks += 1
            elif c.result == "FAIL":
                if c.severity == "CRITICAL":
                    critical_checks += 1
                else:
                    warning_checks += 1
            elif c.result == "NA":
                na_checks += 1

        dimensions.append(
            AuditDimension(
                dimension_id=dim_id,
                dimension_name=dim_name,
                status=status,
                na_rationale=na_rationale,
                checks=checks,
            )
        )

    # -----------------------------------------------------------------------
    # Dimension 1: Technical SEO (REQ-P9-01)
    # -----------------------------------------------------------------------
    d1_checks: list[AuditCheck] = []
    if pages_dict:
        for url, content in sorted(pages_dict.items()):
            issues: list[str] = []
            if not re.search(r"<meta\s+[^>]*charset=", content, re.IGNORECASE):
                issues.append("Missing charset declaration in <head>")
            if not re.search(r'<meta\s+[^>]*name=["\']viewport["\']', content, re.IGNORECASE):
                issues.append("Missing responsive viewport meta tag")
            c_res = validate_canonical_url(url)
            for iss in c_res.issues:
                if iss.severity == ValidationSeverity.CRITICAL:
                    issues.append(iss.message)

            has_crit = any("Canonical" in s or "private" in s for s in issues)
            d1_checks.append(
                AuditCheck(
                    check_id=f"CHK-01-{len(d1_checks)+1:03d}",
                    name=f"Technical markup structure for {url}",
                    result="FAIL" if issues else "PASS",
                    severity="CRITICAL" if has_crit else ("WARNING" if issues else "INFO"),
                    message="Technical metadata valid" if not issues else "; ".join(issues),
                    target_url=url,
                )
            )
    else:
        d1_checks.append(
            AuditCheck(
                check_id="CHK-01-001",
                name="Technical SEO baseline",
                result="PASS",
                severity="INFO",
                message="No input pages provided for technical SEO extraction",
            )
        )
    d1_status = "FAIL" if any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d1_checks) else "PASS"
    add_dimension("1. technical SEO", "Technical SEO & Structure", d1_status, d1_checks)

    # -----------------------------------------------------------------------
    # Dimension 2: Metadata (REQ-P9-01)
    # -----------------------------------------------------------------------
    d2_checks: list[AuditCheck] = []
    if pages_dict:
        for url, content in sorted(pages_dict.items()):
            # Inspect <title> and <meta name="description">
            t_match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
            d_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)

            t_val = t_match.group(1).strip() if t_match else ""
            d_val = d_match.group(1).strip() if d_match else ""

            meta_obj = SEOMetadata(title=t_val, description=d_val, canonical_url=url)
            m_issues = validate_metadata(meta_obj)
            has_crit = any(i.severity == ValidationSeverity.CRITICAL for i in m_issues)
            has_warn = any(i.severity == ValidationSeverity.WARNING for i in m_issues)

            res = "FAIL" if (has_crit or has_warn) else "PASS"
            sev = "CRITICAL" if has_crit else ("WARNING" if has_warn else "INFO")
            msg = "; ".join(i.message for i in m_issues) if m_issues else "Title and meta description conform to length guidelines"

            d2_checks.append(
                AuditCheck(
                    check_id=f"CHK-02-{len(d2_checks)+1:03d}",
                    name=f"Metadata quality for {url}",
                    result=res,
                    severity=sev,
                    message=msg,
                    target_url=url,
                )
            )
    else:
        d2_checks.append(
            AuditCheck(
                check_id="CHK-02-001",
                name="Metadata baseline",
                result="PASS",
                severity="INFO",
                message="No input pages provided for metadata evaluation",
            )
        )
    d2_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d2_checks)
    d2_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d2_checks)
    d2_status = "FAIL" if d2_crit else ("WARNING" if d2_warn else "PASS")
    add_dimension("2. metadata", "Page Metadata (Title & Description)", d2_status, d2_checks)

    # -----------------------------------------------------------------------
    # Dimension 3: Canonical (REQ-P9-01)
    # -----------------------------------------------------------------------
    d3_checks: list[AuditCheck] = []
    if pages_dict:
        for url, content in sorted(pages_dict.items()):
            c_match = re.search(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', content, re.IGNORECASE)
            c_url = c_match.group(1).strip() if c_match else url
            c_res = validate_canonical_url(c_url)
            has_crit = any(i.severity == ValidationSeverity.CRITICAL for i in c_res.issues)
            has_warn = any(i.severity == ValidationSeverity.WARNING for i in c_res.issues)

            res = "FAIL" if (has_crit or has_warn) else "PASS"
            sev = "CRITICAL" if has_crit else ("WARNING" if has_warn else "INFO")
            msg = "; ".join(i.message for i in c_res.issues) if c_res.issues else "Canonical URL valid and absolute"

            d3_checks.append(
                AuditCheck(
                    check_id=f"CHK-03-{len(d3_checks)+1:03d}",
                    name=f"Canonical URL validation for {url}",
                    result=res,
                    severity=sev,
                    message=msg,
                    target_url=url,
                )
            )
    else:
        d3_checks.append(
            AuditCheck(
                check_id="CHK-03-001",
                name="Canonical baseline",
                result="PASS",
                severity="INFO",
                message="No input pages provided for canonical evaluation",
            )
        )
    d3_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d3_checks)
    d3_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d3_checks)
    d3_status = "FAIL" if d3_crit else ("WARNING" if d3_warn else "PASS")
    add_dimension("3. canonical", "Canonical URL Governance", d3_status, d3_checks)

    # -----------------------------------------------------------------------
    # Dimension 4: Robots (REQ-P9-02)
    # -----------------------------------------------------------------------
    d4_checks: list[AuditCheck] = []
    if robots_txt_content is not None:
        try:
            r_cfg = parse_robots_txt(robots_txt_content)
            # Check sensitive path leakage
            disallowed = []
            for g in r_cfg.groups:
                disallowed.extend(g.disallow)
            sensitive_patterns = ["/admin", "/api/private", "/internal", "/staging", "/auth"]
            leaks = [p for p in disallowed if any(sp in p.lower() for sp in sensitive_patterns)]
            if leaks:
                d4_checks.append(
                    AuditCheck(
                        check_id="CHK-04-001",
                        name="robots.txt sensitive path disclosure",
                        result="FAIL",
                        severity="WARNING",
                        message=f"robots.txt disallows sensitive paths: {', '.join(leaks)}; recommend noindex header",
                    )
                )
            else:
                d4_checks.append(
                    AuditCheck(
                        check_id="CHK-04-001",
                        name="robots.txt syntax and paths",
                        result="PASS",
                        severity="INFO",
                        message=f"Parsed {len(r_cfg.groups)} User-agent group(s) cleanly",
                    )
                )
        except Exception as e:
            d4_checks.append(
                AuditCheck(
                    check_id="CHK-04-001",
                    name="robots.txt syntax validity",
                    result="FAIL",
                    severity="CRITICAL",
                    message=f"Failed to parse robots.txt: {e}",
                )
            )
    else:
        d4_checks.append(
            AuditCheck(
                check_id="CHK-04-001",
                name="robots.txt presence",
                result="PASS",
                severity="INFO",
                message="robots.txt not supplied in audit bundle",
            )
        )
    d4_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d4_checks)
    d4_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d4_checks)
    d4_status = "FAIL" if d4_crit else ("WARNING" if d4_warn else "PASS")
    add_dimension("4. robots", "Robots Directives & robots.txt", d4_status, d4_checks)

    # -----------------------------------------------------------------------
    # Dimension 5: Sitemap (REQ-P9-02)
    # -----------------------------------------------------------------------
    d5_checks: list[AuditCheck] = []
    if sitemap_xml_content is not None:
        try:
            s_model = parse_sitemap_xml(sitemap_xml_content)
            # Validate sitemap size
            if len(s_model) > 50000:
                d5_checks.append(
                    AuditCheck(
                        check_id="CHK-05-001",
                        name="Sitemap entry count limit",
                        result="FAIL",
                        severity="CRITICAL",
                        message=f"Sitemap contains {len(s_model)} URLs; maximum is 50,000",
                    )
                )
            else:
                d5_checks.append(
                    AuditCheck(
                        check_id="CHK-05-001",
                        name="Sitemap XML schema and entries",
                        result="PASS",
                        severity="INFO",
                        message=f"Valid XML sitemap with {len(s_model)} entries",
                    )
                )
        except Exception as e:
            d5_checks.append(
                AuditCheck(
                    check_id="CHK-05-001",
                    name="Sitemap XML parsing",
                    result="FAIL",
                    severity="CRITICAL",
                    message=f"Sitemap XML parsing error: {e}",
                )
            )
    else:
        d5_checks.append(
            AuditCheck(
                check_id="CHK-05-001",
                name="Sitemap XML presence",
                result="PASS",
                severity="INFO",
                message="sitemap.xml not supplied in audit bundle",
            )
        )
    d5_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d5_checks)
    d5_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d5_checks)
    d5_status = "FAIL" if d5_crit else ("WARNING" if d5_warn else "PASS")
    add_dimension("5. sitemap", "XML Sitemap Governance", d5_status, d5_checks)

    # -----------------------------------------------------------------------
    # Dimension 6: Structured Data (REQ-P9-03)
    # -----------------------------------------------------------------------
    d6_checks: list[AuditCheck] = []
    found_any_ld = False
    if pages_dict:
        for url, content in sorted(pages_dict.items()):
            try:
                ld_blocks = extract_json_ld_from_html(content)
            except Exception as e:
                d6_checks.append(
                    AuditCheck(
                        check_id=f"CHK-06-{len(d6_checks)+1:03d}",
                        name=f"JSON-LD extraction on {url}",
                        result="FAIL",
                        severity="CRITICAL",
                        message=f"Failed to extract JSON-LD script block: {e}",
                        target_url=url,
                    )
                )
                continue
            if ld_blocks:
                found_any_ld = True
                for b in ld_blocks:
                    issues = validate_structured_data(b)
                    has_crit = any(i.severity == ValidationSeverity.CRITICAL for i in issues)
                    has_warn = any(i.severity == ValidationSeverity.WARNING for i in issues)
                    res = "FAIL" if (has_crit or has_warn) else "PASS"
                    sev = "CRITICAL" if has_crit else ("WARNING" if has_warn else "INFO")
                    d6_checks.append(
                        AuditCheck(
                            check_id=f"CHK-06-{len(d6_checks)+1:03d}",
                            name=f"JSON-LD @type={b.get('@type', 'Unknown')} on {url}",
                            result=res,
                            severity=sev,
                            message="; ".join(i.message for i in issues) if issues else "Valid Schema.org entity",
                            target_url=url,
                        )
                    )
    if not found_any_ld:
        d6_checks.append(
            AuditCheck(
                check_id="CHK-06-001",
                name="Structured data presence",
                result="PASS",
                severity="INFO",
                message="No JSON-LD structured data blocks present in audited pages",
            )
        )
    d6_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d6_checks)
    d6_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d6_checks)
    d6_status = "FAIL" if d6_crit else ("WARNING" if d6_warn else "PASS")
    add_dimension("6. structured data", "Schema.org Structured Data (JSON-LD)", d6_status, d6_checks)

    # -----------------------------------------------------------------------
    # Dimension 7: OG / Social (REQ-P9-03)
    # -----------------------------------------------------------------------
    d7_checks: list[AuditCheck] = []
    if pages_dict:
        for url, content in sorted(pages_dict.items()):
            og_title = bool(re.search(r'<meta\s+property=["\']og:title["\']', content, re.IGNORECASE))
            og_image = bool(re.search(r'<meta\s+property=["\']og:image["\']', content, re.IGNORECASE))
            tw_card = bool(re.search(r'<meta\s+name=["\']twitter:card["\']', content, re.IGNORECASE))

            missing_tags = []
            if not og_title:
                missing_tags.append("og:title")
            if not og_image:
                missing_tags.append("og:image")
            if not tw_card:
                missing_tags.append("twitter:card")

            if missing_tags:
                d7_checks.append(
                    AuditCheck(
                        check_id=f"CHK-07-{len(d7_checks)+1:03d}",
                        name=f"Social tags on {url}",
                        result="FAIL",
                        severity="WARNING",
                        message=f"Missing recommended social tags: {', '.join(missing_tags)}",
                        target_url=url,
                    )
                )
            else:
                d7_checks.append(
                    AuditCheck(
                        check_id=f"CHK-07-{len(d7_checks)+1:03d}",
                        name=f"Social tags on {url}",
                        result="PASS",
                        severity="INFO",
                        message="Open Graph and Twitter Card tags present",
                        target_url=url,
                    )
                )
    else:
        d7_checks.append(
            AuditCheck(
                check_id="CHK-07-001",
                name="Social graph baseline",
                result="PASS",
                severity="INFO",
                message="No input pages provided for social graph evaluation",
            )
        )
    d7_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d7_checks)
    d7_status = "WARNING" if d7_warn else "PASS"
    add_dimension("7. OG/social", "Open Graph & Social Graph", d7_status, d7_checks)

    # -----------------------------------------------------------------------
    # Dimension 8: Headings (REQ-P9-04)
    # -----------------------------------------------------------------------
    d8_checks: list[AuditCheck] = []
    if pages_dict:
        for url, content in sorted(pages_dict.items()):
            h_res = analyze_headings(content)
            has_crit = any(i.severity == ValidationSeverity.CRITICAL for i in h_res.issues)
            has_warn = any(i.severity == ValidationSeverity.WARNING for i in h_res.issues)

            res = "FAIL" if (has_crit or has_warn) else "PASS"
            sev = "CRITICAL" if has_crit else ("WARNING" if has_warn else "INFO")
            msg = "; ".join(i.message for i in h_res.issues) if h_res.issues else f"Clean heading hierarchy ({len(h_res.headings)} headings, {h_res.h1_count} H1)"

            d8_checks.append(
                AuditCheck(
                    check_id=f"CHK-08-{len(d8_checks)+1:03d}",
                    name=f"Heading hierarchy for {url}",
                    result=res,
                    severity=sev,
                    message=msg,
                    target_url=url,
                )
            )
    else:
        d8_checks.append(
            AuditCheck(
                check_id="CHK-08-001",
                name="Heading hierarchy baseline",
                result="PASS",
                severity="INFO",
                message="No input pages provided for heading evaluation",
            )
        )
    d8_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d8_checks)
    d8_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d8_checks)
    d8_status = "FAIL" if d8_crit else ("WARNING" if d8_warn else "PASS")
    add_dimension("8. headings", "Heading Hierarchy (H1..H6)", d8_status, d8_checks)

    # -----------------------------------------------------------------------
    # Dimension 9: Internal Linking (REQ-P9-04)
    # -----------------------------------------------------------------------
    d9_checks: list[AuditCheck] = []
    known_routes: set[str] = set()
    for u in pages_dict.keys():
        parsed_u = urllib.parse.urlparse(u)
        known_routes.add(parsed_u.path or "/")
        known_routes.add(u)
    if sitemap_xml_content is not None:
        try:
            s_entries = parse_sitemap_xml(sitemap_xml_content)
            for se in s_entries:
                p_se = urllib.parse.urlparse(se.loc)
                known_routes.add(p_se.path or "/")
                known_routes.add(se.loc)
        except Exception:
            pass

    if pages_dict:
        for url, content in sorted(pages_dict.items()):
            cur_path = urllib.parse.urlparse(url).path or "/"
            l_res = analyze_links(content, base_url=canonical_domain, current_path=cur_path, known_routes=known_routes)
            has_crit = any(i.severity == ValidationSeverity.CRITICAL for i in l_res.issues)
            has_warn = any(i.severity == ValidationSeverity.WARNING for i in l_res.issues)

            res = "FAIL" if (has_crit or has_warn) else "PASS"
            sev = "CRITICAL" if has_crit else ("WARNING" if has_warn else "INFO")
            tot_links = len(l_res.internal_links) + len(l_res.external_links)
            msg = "; ".join(i.message for i in l_res.issues) if l_res.issues else f"{tot_links} links analyzed ({len(l_res.internal_links)} internal, {len(l_res.broken_links)} broken)"

            d9_checks.append(
                AuditCheck(
                    check_id=f"CHK-09-{len(d9_checks)+1:03d}",
                    name=f"Link integrity for {url}",
                    result=res,
                    severity=sev,
                    message=msg,
                    target_url=url,
                )
            )
    else:
        d9_checks.append(
            AuditCheck(
                check_id="CHK-09-001",
                name="Internal link graph baseline",
                result="PASS",
                severity="INFO",
                message="No input pages provided for link graph evaluation",
            )
        )
    d9_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d9_checks)
    d9_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d9_checks)
    d9_status = "FAIL" if d9_crit else ("WARNING" if d9_warn else "PASS")
    add_dimension("9. internal linking", "Internal Link Graph & Anchor Text", d9_status, d9_checks)

    # -----------------------------------------------------------------------
    # Dimension 10: Image SEO (REQ-P9-05)
    # -----------------------------------------------------------------------
    d10_checks: list[AuditCheck] = []
    if pages_dict:
        for url, content in sorted(pages_dict.items()):
            m_res = analyze_media(content)
            has_crit = any(i.severity == ValidationSeverity.CRITICAL for i in m_res.issues)
            has_warn = any(i.severity == ValidationSeverity.WARNING for i in m_res.issues)

            res = "FAIL" if (has_crit or has_warn) else "PASS"
            sev = "CRITICAL" if has_crit else ("WARNING" if has_warn else "INFO")
            msg = "; ".join(i.message for i in m_res.issues) if m_res.issues else f"{m_res.total_images} images analyzed (all valid alt text & dimensions)"

            d10_checks.append(
                AuditCheck(
                    check_id=f"CHK-10-{len(d10_checks)+1:03d}",
                    name=f"Image SEO for {url}",
                    result=res,
                    severity=sev,
                    message=msg,
                    target_url=url,
                )
            )
    else:
        d10_checks.append(
            AuditCheck(
                check_id="CHK-10-001",
                name="Image SEO baseline",
                result="PASS",
                severity="INFO",
                message="No input pages provided for image SEO evaluation",
            )
        )
    d10_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d10_checks)
    d10_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d10_checks)
    d10_status = "FAIL" if d10_crit else ("WARNING" if d10_warn else "PASS")
    add_dimension("10. image SEO", "Media & Image SEO", d10_status, d10_checks)

    # -----------------------------------------------------------------------
    # Dimension 11: CWV - CLS (REQ-P9-07)
    # -----------------------------------------------------------------------
    d11_checks: list[AuditCheck] = []
    cls_res = evaluate_cls(observed_cls)
    d11_checks.append(
        AuditCheck(
            check_id="CHK-11-001",
            name="Cumulative Layout Shift (CLS) threshold",
            result="PASS" if cls_res.status in ("PASS", "NOT_APPLICABLE") else "FAIL",
            severity="CRITICAL" if cls_res.status == "FAIL" else ("WARNING" if cls_res.status == "NEEDS_IMPROVEMENT" else "INFO"),
            message="; ".join(i.message for i in cls_res.issues) if cls_res.issues else "CLS satisfies threshold <= 0.1",
        )
    )
    # Static layout shift checks over pages
    for url, content in sorted(pages_dict.items()):
        cwv_static = analyze_cwv(html_content=content, observed_cls=observed_cls)
        for issue in cwv_static.static_prevention.issues:
            d11_checks.append(
                AuditCheck(
                    check_id=f"CHK-11-{len(d11_checks)+1:03d}",
                    name=f"Static shift prevention on {url}",
                    result="FAIL" if issue.severity in (ValidationSeverity.CRITICAL, ValidationSeverity.WARNING) else "PASS",
                    severity=issue.severity.value,
                    message=issue.message,
                    target_url=url,
                )
            )
    d11_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d11_checks)
    d11_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d11_checks)
    d11_status = "FAIL" if d11_crit else ("WARNING" if d11_warn else "PASS")
    add_dimension("11. CWV (CLS)", "Core Web Vitals — Cumulative Layout Shift (CLS)", d11_status, d11_checks)

    # -----------------------------------------------------------------------
    # Dimension 12: CWV - LCP/INP (REQ-P9-07 strictly NOT_APPLICABLE per CONF-001)
    # -----------------------------------------------------------------------
    lcp_res = evaluate_lcp()
    inp_res = evaluate_inp()
    d12_checks = [
        AuditCheck(
            check_id="CHK-12-001",
            name="Largest Contentful Paint (LCP) evaluation",
            result="NA",
            severity="INFO",
            message=lcp_res.na_rationale,
        ),
        AuditCheck(
            check_id="CHK-12-002",
            name="Interaction to Next Paint (INP) evaluation",
            result="NA",
            severity="INFO",
            message=inp_res.na_rationale,
        ),
    ]
    add_dimension(
        "11. CWV (LCP/INP)",
        "Core Web Vitals — LCP & INP (CONF-001)",
        "NOT_APPLICABLE",
        d12_checks,
        na_rationale=CONF_001_NA_RATIONALE,
    )

    # -----------------------------------------------------------------------
    # Dimension 13: Redirects (REQ-P9-06)
    # -----------------------------------------------------------------------
    d13_checks: list[AuditCheck] = []
    if redirect_rules:
        red_res = analyze_redirect_graph(redirect_rules, canonical_domain=canonical_domain)
        for iss in red_res.issues:
            d13_checks.append(
                AuditCheck(
                    check_id=f"CHK-13-{len(d13_checks)+1:03d}",
                    name=f"Redirect rule issue: {iss.code}",
                    result="FAIL" if iss.severity in (ValidationSeverity.CRITICAL, ValidationSeverity.WARNING) else "PASS",
                    severity=iss.severity.value,
                    message=iss.message,
                    target_url=iss.field,
                )
            )
        if not d13_checks:
            d13_checks.append(
                AuditCheck(
                    check_id="CHK-13-001",
                    name="Redirect graph analysis",
                    result="PASS",
                    severity="INFO",
                    message=f"Analyzed {red_res.total_rules} redirect rules; 0 loops, 0 chains",
                )
            )
    else:
        d13_checks.append(
            AuditCheck(
                check_id="CHK-13-001",
                name="Redirect inventory presence",
                result="PASS",
                severity="INFO",
                message="No redirect inventory supplied in audit bundle",
            )
        )
    d13_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d13_checks)
    d13_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d13_checks)
    d13_status = "FAIL" if d13_crit else ("WARNING" if d13_warn else "PASS")
    add_dimension("12. redirects", "Redirect Taxonomy & Chains", d13_status, d13_checks)

    # -----------------------------------------------------------------------
    # Dimension 14: URL Architecture (REQ-P9-06)
    # -----------------------------------------------------------------------
    d14_checks: list[AuditCheck] = []
    if pages_dict:
        for url in sorted(pages_dict.keys()):
            url_issues = validate_url_taxonomy(url)
            has_crit = any(i.severity == ValidationSeverity.CRITICAL for i in url_issues)
            has_warn = any(i.severity == ValidationSeverity.WARNING for i in url_issues)

            res = "FAIL" if (has_crit or has_warn) else "PASS"
            sev = "CRITICAL" if has_crit else ("WARNING" if has_warn else "INFO")
            msg = "; ".join(i.message for i in url_issues) if url_issues else "URL slug conforms to search engine architecture"

            d14_checks.append(
                AuditCheck(
                    check_id=f"CHK-14-{len(d14_checks)+1:03d}",
                    name=f"URL taxonomy for {url}",
                    result=res,
                    severity=sev,
                    message=msg,
                    target_url=url,
                )
            )
    else:
        d14_checks.append(
            AuditCheck(
                check_id="CHK-14-001",
                name="URL architecture baseline",
                result="PASS",
                severity="INFO",
                message="No input routes provided for URL architecture check",
            )
        )
    d14_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d14_checks)
    d14_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d14_checks)
    d14_status = "FAIL" if d14_crit else ("WARNING" if d14_warn else "PASS")
    add_dimension("13. URL architecture", "URL Architecture & Slugs", d14_status, d14_checks)

    # -----------------------------------------------------------------------
    # Dimension 15: Pagination (REQ-P9-06)
    # -----------------------------------------------------------------------
    d15_checks: list[AuditCheck] = []
    has_paginated_pages = False
    if pages_dict:
        for url, content in sorted(pages_dict.items()):
            pag_res = analyze_pagination_html(content, current_url=url)
            if pag_res.signals.prev_url or pag_res.signals.next_url:
                has_paginated_pages = True
                has_crit = any(i.severity == ValidationSeverity.CRITICAL for i in pag_res.issues)
                has_warn = any(i.severity == ValidationSeverity.WARNING for i in pag_res.issues)

                res = "FAIL" if (has_crit or has_warn) else "PASS"
                sev = "CRITICAL" if has_crit else ("WARNING" if has_warn else "INFO")
                msg = "; ".join(i.message for i in pag_res.issues) if pag_res.issues else "Pagination signals consistent"

                d15_checks.append(
                    AuditCheck(
                        check_id=f"CHK-15-{len(d15_checks)+1:03d}",
                        name=f"Pagination signals on {url}",
                        result=res,
                        severity=sev,
                        message=msg,
                        target_url=url,
                    )
                )
    if not has_paginated_pages:
        d15_checks.append(
            AuditCheck(
                check_id="CHK-15-001",
                name="Pagination signals baseline",
                result="PASS",
                severity="INFO",
                message="No paginated collections detected across audited pages",
            )
        )
    d15_crit = any(c.severity == "CRITICAL" and c.result == "FAIL" for c in d15_checks)
    d15_warn = any(c.severity == "WARNING" and c.result == "FAIL" for c in d15_checks)
    d15_status = "FAIL" if d15_crit else ("WARNING" if d15_warn else "PASS")
    add_dimension("14. pagination", "Pagination Canonicalization", d15_status, d15_checks)

    # -----------------------------------------------------------------------
    # Specialized Dimensions 16..18 (REQ-P9-08)
    # -----------------------------------------------------------------------
    try:
        spec_res = analyze_specialized_dimensions(
            html_content="".join(pages_dict.values()),
            is_multilingual=is_multilingual,
            multilingual_na_rationale=multilingual_na_rationale,
            is_local_business=is_local_business,
            local_na_rationale=local_na_rationale,
            is_ecommerce=is_ecommerce,
            ecommerce_na_rationale=ecommerce_na_rationale,
        )
    except Exception:
        spec_res = analyze_specialized_dimensions(
            html_content="",
            is_multilingual=is_multilingual,
            multilingual_na_rationale=multilingual_na_rationale,
            is_local_business=is_local_business,
            local_na_rationale=local_na_rationale,
            is_ecommerce=is_ecommerce,
            ecommerce_na_rationale=ecommerce_na_rationale,
        )

    # Dimension 16: i18n
    d16_checks: list[AuditCheck] = []
    if spec_res.multilingual.status == "NOT_APPLICABLE":
        d16_checks.append(
            AuditCheck(
                check_id="CHK-16-001",
                name="Multilingual hreflang verification",
                result="NA",
                severity="INFO",
                message=spec_res.multilingual.na_rationale,
            )
        )
    else:
        for iss in spec_res.multilingual.issues:
            d16_checks.append(
                AuditCheck(
                    check_id=f"CHK-16-{len(d16_checks)+1:03d}",
                    name=f"Hreflang issue: {iss.code}",
                    result="FAIL" if iss.severity in (ValidationSeverity.CRITICAL, ValidationSeverity.WARNING) else "PASS",
                    severity=iss.severity.value,
                    message=iss.message,
                )
            )
        if not d16_checks:
            d16_checks.append(
                AuditCheck(
                    check_id="CHK-16-001",
                    name="Multilingual hreflang verification",
                    result="PASS",
                    severity="INFO",
                    message="Valid hreflang tags and reciprocity",
                )
            )
    add_dimension(
        "15. i18n",
        "International / Multilingual SEO",
        spec_res.multilingual.status,
        d16_checks,
        na_rationale=spec_res.multilingual.na_rationale,
    )

    # Dimension 17: local
    d17_checks: list[AuditCheck] = []
    if spec_res.local_business.status == "NOT_APPLICABLE":
        d17_checks.append(
            AuditCheck(
                check_id="CHK-17-001",
                name="LocalBusiness structured data verification",
                result="NA",
                severity="INFO",
                message=spec_res.local_business.na_rationale,
            )
        )
    else:
        for iss in spec_res.local_business.issues:
            d17_checks.append(
                AuditCheck(
                    check_id=f"CHK-17-{len(d17_checks)+1:03d}",
                    name=f"LocalBusiness issue: {iss.code}",
                    result="FAIL" if iss.severity in (ValidationSeverity.CRITICAL, ValidationSeverity.WARNING) else "PASS",
                    severity=iss.severity.value,
                    message=iss.message,
                )
            )
        if not d17_checks:
            d17_checks.append(
                AuditCheck(
                    check_id="CHK-17-001",
                    name="LocalBusiness structured data verification",
                    result="PASS",
                    severity="INFO",
                    message="Valid LocalBusiness entity",
                )
            )
    add_dimension(
        "15. local",
        "Local Business SEO",
        spec_res.local_business.status,
        d17_checks,
        na_rationale=spec_res.local_business.na_rationale,
    )

    # Dimension 18: ecommerce
    d18_checks: list[AuditCheck] = []
    if spec_res.ecommerce.status == "NOT_APPLICABLE":
        d18_checks.append(
            AuditCheck(
                check_id="CHK-18-001",
                name="Product & Offer structured data verification",
                result="NA",
                severity="INFO",
                message=spec_res.ecommerce.na_rationale,
            )
        )
    else:
        for iss in spec_res.ecommerce.issues:
            d18_checks.append(
                AuditCheck(
                    check_id=f"CHK-18-{len(d18_checks)+1:03d}",
                    name=f"Ecommerce issue: {iss.code}",
                    result="FAIL" if iss.severity in (ValidationSeverity.CRITICAL, ValidationSeverity.WARNING) else "PASS",
                    severity=iss.severity.value,
                    message=iss.message,
                )
            )
        if not d18_checks:
            d18_checks.append(
                AuditCheck(
                    check_id="CHK-18-001",
                    name="Product & Offer structured data verification",
                    result="PASS",
                    severity="INFO",
                    message="Valid Product and Offer entities",
                )
            )
    add_dimension(
        "15. ecommerce",
        "Ecommerce SEO (Product & Offer)",
        spec_res.ecommerce.status,
        d18_checks,
        na_rationale=spec_res.ecommerce.na_rationale,
    )

    # -----------------------------------------------------------------------
    # Dimension 19: Pre-Deployment Audit Gating (REQ-P9-09)
    # -----------------------------------------------------------------------
    d19_checks: list[AuditCheck] = []
    d19_status = "FAIL" if critical_checks > 0 else "PASS"
    d19_checks.append(
        AuditCheck(
            check_id="CHK-19-001",
            name="Pre-deployment audit critical defects gate",
            result="FAIL" if critical_checks > 0 else "PASS",
            severity="CRITICAL" if critical_checks > 0 else "INFO",
            message=(
                f"{critical_checks} critical defect(s) detected; deployment gate blocked"
                if critical_checks > 0
                else f"Zero critical defects detected across {total_checks} checks; deployment gate passed"
            ),
        )
    )
    add_dimension("16. pre-deployment audit", "Pre-Deployment Audit Gating", d19_status, d19_checks)

    # -----------------------------------------------------------------------
    # Exit Code Determination
    # -----------------------------------------------------------------------
    if mode == "deployment":
        exit_code = 1 if critical_checks > 0 else 0
    else:
        # Advisory mode never breaks build
        exit_code = 0

    summary = AuditSummary(
        total_checks=total_checks,
        passed=passed_checks,
        warnings=warning_checks,
        critical=critical_checks,
        not_applicable=na_checks,
    )

    return AuditReport(
        audit_id=audit_id,
        timestamp=timestamp_str,
        mode=mode,
        exit_code=exit_code,
        summary=summary,
        dimensions=dimensions,
        evidence_ref=evidence_ref,
        audited_artifacts_digest=audited_digest,
    )


# ---------------------------------------------------------------------------
# Directory-Based Audit Runner
# ---------------------------------------------------------------------------

def audit_directory(
    target_dir: str | Path,
    mode: str = "advisory",
    canonical_domain: str = "https://example.com",
    observed_cls: float | None = None,
    is_multilingual: bool = False,
    is_local_business: bool = False,
    is_ecommerce: bool = False,
    command: str = "",
) -> AuditReport:
    """Scan and audit an output/build directory containing HTML, robots.txt, and sitemap.xml."""
    p = Path(target_dir).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Target audit directory '{target_dir}' does not exist")

    pages: dict[str, str] = {}
    robots_content: str | None = None
    sitemap_content: str | None = None

    if p.is_file():
        # Single HTML file audit
        content = p.read_text(encoding="utf-8", errors="replace")
        pages[f"{canonical_domain}/{p.name}"] = content
    else:
        # Directory audit
        for html_file in p.glob("**/*.html"):
            rel = html_file.relative_to(p)
            url_path = f"/{rel.as_posix()}"
            if url_path.endswith("/index.html"):
                url_path = url_path[:-10] or "/"
            elif url_path.endswith(".html"):
                url_path = url_path[:-5]
            route_url = f"{canonical_domain.rstrip('/')}{url_path}"
            pages[route_url] = html_file.read_text(encoding="utf-8", errors="replace")

        robots_path = p / "robots.txt"
        if robots_path.exists():
            robots_content = robots_path.read_text(encoding="utf-8", errors="replace")

        sitemap_path = p / "sitemap.xml"
        if sitemap_path.exists():
            sitemap_content = sitemap_path.read_text(encoding="utf-8", errors="replace")

    return run_seo_audit(
        pages=pages,
        robots_txt_content=robots_content,
        sitemap_xml_content=sitemap_content,
        canonical_domain=canonical_domain,
        mode=mode,
        observed_cls=observed_cls,
        is_multilingual=is_multilingual,
        is_local_business=is_local_business,
        is_ecommerce=is_ecommerce,
        command=command,
    )
