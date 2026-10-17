"""P8 CMS rollback and feature boundary.

P8 must be removable without modifying SPS2 core.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


# Feature flag key in LOCAL-STATE.json
P8_FEATURE_FLAG = "p8_cms_enabled"


class RollbackError(Exception):
    """Rollback operation failed."""


def is_p8_enabled(local_state_path: str | Path = "framework/sps2/project/LOCAL-STATE.json") -> bool:
    """Check if P8 is enabled via the feature flag."""
    path = Path(local_state_path)
    if not path.exists():
        return False
    with open(path) as f:
        state = json.load(f)
    return state.get(P8_FEATURE_FLAG, False)


def set_p8_enabled(
    enabled: bool,
    local_state_path: str | Path = "framework/sps2/project/LOCAL-STATE.json",
) -> None:
    """Enable or disable P8 via the feature flag."""
    path = Path(local_state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {}
    if path.exists():
        with open(path) as f:
            state = json.load(f)
    state[P8_FEATURE_FLAG] = enabled
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def remove_p8(
    domain_dir: str | Path = "framework/domain/cms",
    local_state_path: str | Path = "framework/sps2/project/LOCAL-STATE.json",
) -> None:
    """Remove P8 entirely. Does not modify SPS2 core."""
    # Disable feature flag
    set_p8_enabled(False, local_state_path)

    # Delete framework/domain/cms directory
    domain_path = Path(domain_dir)
    if domain_path.exists():
        shutil.rmtree(domain_path)


def verify_removal(
    domain_dir: str | Path = "framework/domain/cms",
    local_state_path: str | Path = "framework/sps2/project/LOCAL-STATE.json",
) -> tuple[bool, list[str]]:
    """Verify that P8 removal is clean."""
    issues = []

    # Check framework/domain/cms is gone
    if Path(domain_dir).exists():
        issues.append(f"{domain_dir} still exists")

    # Check feature flag is false
    if is_p8_enabled(local_state_path):
        issues.append("Feature flag is still enabled")

    # Check no imports from framework.domain.cms in core
    # This would be checked by the test suite

    return len(issues) == 0, issues


def get_p8_status() -> dict[str, Any]:
    """Get P8 status information."""
    return {
        "enabled": is_p8_enabled(),
        "domain_exists": Path("framework/domain/cms").exists(),
        "feature_flag_key": P8_FEATURE_FLAG,
    }
