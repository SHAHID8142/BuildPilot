"""P8 CMS audit system.

Append-only, tamper-evident audit log with HMAC-SHA256 signatures.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from domain.cms.persistence import JSONStore
from domain.cms.validation import validate_audit_entry


# Audit actions
AUDIT_ACTIONS = {
    "content_create",
    "content_update",
    "content_delete",
    "content_publish",
    "content_unpublish",
    "content_archive",
    "content_restore",
    "section_create",
    "section_update",
    "section_delete",
    "asset_upload",
    "asset_select",
    "asset_external_import",
    "revision_rollback",
    "role_change",
    "user_create",
    "user_delete",
}


class AuditError(Exception):
    """Audit operation failed."""


class AuditTamperError(AuditError):
    """Audit log tampering detected."""


class AuditService:
    """Append-only, tamper-evident audit log."""

    def __init__(
        self,
        store: JSONStore,
        hmac_key: bytes | None = None,
    ) -> None:
        self._store = store
        # HMAC key must be provided externally; no default/test key
        if hmac_key is None:
            raise AuditError(
                "HMAC key must be provided. No default or test key is permitted."
            )
        self._hmac_key = hmac_key

    def _compute_hash(self, entry: dict) -> str:
        """Compute HMAC-SHA256 of an audit entry."""
        # Exclude entry_hash from the computation
        data = {k: v for k, v in entry.items() if k != "entry_hash"}
        message = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hmac.new(self._hmac_key, message.encode(), hashlib.sha256).hexdigest()

    def _get_last_hash(self) -> str:
        """Get the hash of the last audit entry."""
        entries = self._store.read_lines("audit")
        if not entries:
            return "0" * 64
        return entries[-1]["entry_hash"]

    def record(
        self,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        before_state: dict | None = None,
        after_state: dict | None = None,
    ) -> dict:
        """Record an audit event. Append-only."""
        if action not in AUDIT_ACTIONS:
            raise AuditError(f"Unknown audit action '{action}'")

        # Sanitize states to ensure no secrets
        before_state = self._sanitize_state(before_state)
        after_state = self._sanitize_state(after_state)

        previous_hash = self._get_last_hash()
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor_id": actor_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "before_state": before_state,
            "after_state": after_state,
            "previous_hash": previous_hash,
        }
        entry["entry_hash"] = self._compute_hash(entry)
        validate_audit_entry(entry)
        self._store.append("audit", entry)
        return entry

    def _sanitize_state(self, state: dict | None) -> dict | None:
        """Remove any potential secrets from state."""
        if state is None:
            return None
        sanitized = {}
        for key, value in state.items():
            # Skip keys that might contain secrets
            if any(
                s in key.lower()
                for s in ("password", "secret", "token", "key", "credential", "auth")
            ):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify the integrity of the entire audit chain."""
        entries = self._store.read_lines("audit")
        errors = []
        for i, entry in enumerate(entries):
            # Verify entry hash
            computed = self._compute_hash(entry)
            if computed != entry["entry_hash"]:
                errors.append(f"Entry {i}: hash mismatch")

            # Verify chain linkage
            if i == 0:
                expected_previous = "0" * 64
            else:
                expected_previous = entries[i - 1]["entry_hash"]
            if entry["previous_hash"] != expected_previous:
                errors.append(f"Entry {i}: chain linkage broken")

        return len(errors) == 0, errors

    def get_entries(
        self,
        actor_id: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
    ) -> list[dict]:
        """Get audit entries with optional filtering."""
        entries = self._store.read_lines("audit")
        if actor_id:
            entries = [e for e in entries if e["actor_id"] == actor_id]
        if action:
            entries = [e for e in entries if e["action"] == action]
        if resource_type:
            entries = [e for e in entries if e["resource_type"] == resource_type]
        return entries

    def export(self) -> str:
        """Export audit log as JSON string."""
        entries = self._store.read_lines("audit")
        return json.dumps(entries, indent=2)
