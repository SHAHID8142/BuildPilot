#!/usr/bin/env python3
"""SPS 2.0 SEO Pre-Deployment Audit CLI (REQ-P9-09).

Dual-mode pre-deployment audit runner:
- advisory mode: executes all 16+ dimension checks and prints/emits report (exit code 0).
- deployment mode: enforces non-zero exit code (exit code 1) on CRITICAL defects.
- emits structured JSON (conforming to sps2/schemas/p9-audit.schema.json), Markdown, or console summary.
- emits formal EV-SEO-* evidence records conforming to sps2/governance/SCHEMAS/evidence.schema.json.
- strictly preserves the CONF-001 boundary (zero invented LCP/INP thresholds).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path to enable domain/seo imports
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from domain.seo.audit import (
    audit_directory,
    build_evidence_record,
    render_audit_markdown,
    validate_audit_report_schema,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SPS 2.0 SEO Pre-Deployment Audit Tool (Dual-Mode CLI)"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target build/output directory or HTML file to audit (default: '.')",
    )
    parser.add_argument(
        "--mode",
        choices=["advisory", "deployment"],
        default="advisory",
        help="Audit enforcement mode: 'advisory' (exit 0) or 'deployment' (exit 1 on CRITICAL)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "md", "markdown"],
        default="text",
        help="Report output format (default: 'text')",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Write report output to specified file path instead of stdout",
    )
    parser.add_argument(
        "--evidence-out",
        help="Write formal EV-SEO-* evidence record JSON to specified file path",
    )
    parser.add_argument(
        "--canonical",
        default="https://example.com",
        help="Canonical domain URL for the project (default: 'https://example.com')",
    )
    parser.add_argument(
        "--cls",
        type=float,
        default=None,
        help="Observed Cumulative Layout Shift (CLS) runtime measurement (e.g. 0.05)",
    )
    parser.add_argument(
        "--multilingual",
        action="store_true",
        help="Enable Multilingual / hreflang dimension evaluation (default: N/A)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Enable LocalBusiness dimension evaluation (default: N/A)",
    )
    parser.add_argument(
        "--ecommerce",
        action="store_true",
        help="Enable Ecommerce Product/Offer dimension evaluation (default: N/A)",
    )
    parser.add_argument(
        "--validate-schema",
        action="store_true",
        help="Strictly assert emitted JSON report against sps2/schemas/p9-audit.schema.json",
    )

    args = parser.parse_args(argv)

    target_path = Path(args.target)
    if not target_path.exists():
        sys.stderr.write(f"Error: Target path '{args.target}' does not exist.\n")
        return 2

    command_str = " ".join(sys.argv) if argv is None else f"seo_audit.py {' '.join(argv)}"

    try:
        report = audit_directory(
            target_dir=target_path,
            mode=args.mode,
            canonical_domain=args.canonical,
            observed_cls=args.cls,
            is_multilingual=args.multilingual,
            is_local_business=args.local,
            is_ecommerce=args.ecommerce,
            command=command_str,
        )
    except Exception as exc:
        sys.stderr.write(f"Audit execution error: {exc}\n")
        return 2

    report_dict = report.to_dict()

    # Optional strict schema validation
    if args.validate_schema:
        schema_errors = validate_audit_report_schema(report_dict)
        if schema_errors:
            sys.stderr.write("Schema Validation Errors:\n")
            for err in schema_errors:
                sys.stderr.write(f"  - {err}\n")
            return 2

    # Render formatted report
    if args.format in ("json",):
        output_content = json.dumps(report_dict, indent=2, sort_keys=True)
    elif args.format in ("md", "markdown"):
        output_content = render_audit_markdown(report)
    else:
        # Default text format
        status_text = "PASS" if report.exit_code == 0 else "FAIL"
        summary = report.summary
        output_content = (
            f"SPS 2.0 SEO Audit [{report.audit_id}] ({report.mode} mode)\n"
            f"Status: {status_text} (Exit code: {report.exit_code})\n"
            f"Artifacts Digest: {report.audited_artifacts_digest[:16]}...\n"
            f"Checks: {summary.total_checks} total | {summary.passed} passed | "
            f"{summary.warnings} warnings | {summary.critical} critical | {summary.not_applicable} N/A\n"
            f"Dimensions: {len(report.dimensions)} evaluated\n"
        )
        if summary.critical > 0:
            output_content += "\nCRITICAL DEFECTS:\n"
            for d in report.dimensions:
                for c in d.checks:
                    if c.severity == "CRITICAL" and c.result == "FAIL":
                        output_content += f"  - [{d.dimension_id}] {c.name}: {c.message}\n"

    # Write report output
    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(output_content, encoding="utf-8")
    else:
        sys.stdout.write(output_content + ("\n" if not output_content.endswith("\n") else ""))

    # Write formal evidence record if requested
    if args.evidence_out:
        ev_record = build_evidence_record(report, command=command_str)
        ev_p = Path(args.evidence_out)
        ev_p.parent.mkdir(parents=True, exist_ok=True)
        ev_p.write_text(json.dumps(ev_record, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
