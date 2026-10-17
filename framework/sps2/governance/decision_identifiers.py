#!/usr/bin/env python3
"""Canonical decision identifier compatibility contract for DEC-7303."""
from __future__ import annotations

import re

DECISION_ID_PATTERN = r"^(?:DEC-[0-9]{4}|D-P[0-9]+(?:-[A-Z0-9]+)*)$"
DECISION_ID_REGEX = re.compile(DECISION_ID_PATTERN)


def is_valid_decision_id(value: object) -> bool:
    return isinstance(value, str) and DECISION_ID_REGEX.fullmatch(value) is not None
