#!/usr/bin/env python3
"""Negative-test fixture generator for validate-capability.sh.

Emits a single VALID baseline capability record, optionally mutated by the
expression given as argv[1]. Used only by the negative suite; it never reads or
writes real repository state.
"""
import json
import sys

BASE = {
    "capability_id": "CAP-P04-090", "name": "Fixture", "type": "SKILL",
    "description": "Negative-test fixture", "purpose": "test", "domain": "test",
    "serves_requirements": ["REQ-P04-01"], "fact_class": "EVIDENCE",
    "source": "official_repo", "source_rank": 2,
    "official_url": "https://example.invalid",
    "repository_url": "https://example.invalid",
    "version": "1.0.0", "release_date": "2026-01-01",
    "tech_compatibility": "COMPATIBLE",
    "framework_compatibility": "COMPATIBLE",
    "agent_compatibility": "AGENT_NEUTRAL", "agent_specific_dependency": None,
    "maintenance_status": "ACTIVE", "licence": "MIT",
    "security_status": "VERIFIED_SAFE", "security_evidence": "fixture",
    "trust_level": "VERIFIED", "evidence": ["EV-P04-900"],
    "quality_indicators": {}, "adoption_indicators": {},
    "known_limitations": [], "dependencies": [],
    "install_method": "fixture", "install_scope": "PROJECT_LOCAL",
    "global_installation_authorized_by": "",
    "project_local_install_method": "fixture",
    "rollback_method": "fixture", "verification_method": "fixture",
    "researched_at": "2026-10-03T00:00:00Z", "research_id": "RSCH-P04-900",
    "version_checked": "1.0.0", "source_checked": "https://example.invalid",
    "last_verified": "2026-10-03T00:00:00Z",
    "review_due": "2027-10-03T00:00:00Z", "staleness": "CURRENT",
    "provenance": {"requirement": "REQ-P04-01", "discovery": "fixture",
                   "research": "RSCH-P04-900", "evaluation": "EVAL-P04-900",
                   "user_decision": None, "installation": "fixture",
                   "verification": "EV-P04-900"},
    "evaluation": {"evaluation_id": "EVAL-P04-900",
                   "criteria": {str(i): "OK" for i in range(1, 17)},
                   "selection_reason": "fixture", "rejection_reason": None},
    "lifecycle_state": "EVALUATED", "status": "IN_PROGRESS",
    "completion": "PARTIAL", "approval_status": "PENDING_USER_APPROVAL",
    "approval_decided_by": "",
}

c = dict(BASE)
expr = sys.argv[1] if len(sys.argv) > 1 else "pass"
if expr != "pass":
    exec(expr)
print(json.dumps({"capabilities": [c]}, indent=2))