#!/usr/bin/env python3
"""SPS 2.0 P17 Master Agent Execution Backbone - Slice 1.

Governance: sps2/requirements/P17-REQUIREMENTS.json (REQ-P17-01..14,
SEC-P17-01..11), sps2/decisions/P17-DECISIONS.json (D-P17-4..7,
D-P17-GATE-P17-2-APPROVAL), sps2/schemas/p17-task-record.schema.json.

REAL-AGENT EXECUTION IS DISABLED BY DEFAULT. GATE-P17-4 is OPEN: unprivileged
standard-library execution cannot PREVENT an executed process from writing
outside the project directory. Only repository-local test doubles may run.
Test-double results are not evidence of real-agent isolation.

Python standard library only. No dependency installation. No network. No
server. No deployment. No shell execution.
"""

__all__ = [
    "confinement",
    "discovery",
    "execution",
    "intake",
    "plan",
    "record",
    "scrub",
    "selection",
    "state",
    "verification",
]
