"""P8 CMS schema validation.

Validates all entities against the approved P8 schemas.
Uses only Python stdlib — no jsonschema dependency.
"""
from __future__ import annotations

import re
from typing import Any


# Field types allowed in ContentType
VALID_FIELD_TYPES = ("string", "text", "number", "boolean", "date", "asset")

# Content statuses
VALID_STATUSES = ("draft", "preview", "published", "archived")

# Asset sources
VALID_SOURCES = ("upload", "existing_media", "external_url")

# Section layouts (extensible)
VALID_LAYOUTS = ("hero", "grid", "list", "single", "custom")


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str = "") -> None:
        self.message = message
        self.field = field
        super().__init__(message)


def _require_string(data: dict, field: str, min_length: int = 1) -> str:
    value = data.get(field)
    if not isinstance(value, str) or len(value) < min_length:
        raise ValidationError(
            f"Field '{field}' must be a string with length >= {min_length}",
            field,
        )
    return value


def _require_int(data: dict, field: str, minimum: int | None = None) -> int:
    value = data.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"Field '{field}' must be an integer", field)
    if minimum is not None and value < minimum:
        raise ValidationError(
            f"Field '{field}' must be >= {minimum}", field
        )
    return value


def _require_object(data: Any, context: str = "root") -> dict:
    if not isinstance(data, dict):
        raise ValidationError(f"{context} must be an object", context)
    return data


def _require_list(data: Any, field: str, context: str = "root") -> list:
    value = data.get(field) if isinstance(data, dict) else None
    if not isinstance(value, list):
        raise ValidationError(f"Field '{field}' must be an array", field)
    return value


def validate_content_type(data: dict) -> dict:
    """Validate a ContentType definition."""
    data = _require_object(data, "ContentType")
    _require_string(data, "id")
    _require_string(data, "name")
    fields = _require_list(data, "fields", "ContentType")
    for i, field in enumerate(fields):
        field = _require_object(field, f"ContentType.fields[{i}]")
        _require_string(field, "name")
        field_type = field.get("type")
        if field_type not in VALID_FIELD_TYPES:
            raise ValidationError(
                f"ContentType.fields[{i}].type must be one of {VALID_FIELD_TYPES}",
                f"ContentType.fields[{i}].type",
            )
        if not isinstance(field.get("required"), bool):
            raise ValidationError(
                f"ContentType.fields[{i}].required must be a boolean",
                f"ContentType.fields[{i}].required",
            )
    _require_string(data, "created_at")
    _require_string(data, "updated_at")
    return data


def validate_content(data: dict) -> dict:
    """Validate a Content item."""
    data = _require_object(data, "Content")
    _require_string(data, "id")
    _require_string(data, "type_id")
    _require_string(data, "title")
    if not isinstance(data.get("body"), str):
        raise ValidationError("Content.body must be a string", "body")
    status = data.get("status")
    if status not in VALID_STATUSES:
        raise ValidationError(
            f"Content.status must be one of {VALID_STATUSES}", "status"
        )
    _require_string(data, "author_id")
    _require_string(data, "created_at")
    _require_string(data, "updated_at")
    published_at = data.get("published_at")
    if published_at is not None and not isinstance(published_at, str):
        raise ValidationError(
            "Content.published_at must be a string or null", "published_at"
        )
    return data


def validate_section(data: dict) -> dict:
    """Validate a Section."""
    data = _require_object(data, "Section")
    _require_string(data, "id")
    _require_string(data, "name")
    _require_string(data, "layout")
    content_ids = _require_list(data, "content_ids", "Section")
    for i, cid in enumerate(content_ids):
        if not isinstance(cid, str) or not cid:
            raise ValidationError(
                f"Section.content_ids[{i}] must be a non-empty string",
                f"content_ids[{i}]",
            )
    _require_int(data, "order", minimum=0)
    return data


def validate_revision(data: dict) -> dict:
    """Validate a Revision."""
    data = _require_object(data, "Revision")
    _require_string(data, "id")
    _require_string(data, "content_id")
    _require_int(data, "version", minimum=1)
    if not isinstance(data.get("body"), str):
        raise ValidationError("Revision.body must be a string", "body")
    _require_string(data, "author_id")
    _require_string(data, "created_at")
    return data


def validate_asset(data: dict) -> dict:
    """Validate an Asset reference."""
    data = _require_object(data, "Asset")
    _require_string(data, "id")
    source = data.get("source")
    if source not in VALID_SOURCES:
        raise ValidationError(
            f"Asset.source must be one of {VALID_SOURCES}", "source"
        )
    original_url = data.get("original_url")
    if original_url is not None and not isinstance(original_url, str):
        raise ValidationError(
            "Asset.original_url must be a string or null", "original_url"
        )
    _require_string(data, "local_path")
    _require_string(data, "media_type")
    _require_int(data, "size_bytes", minimum=0)
    checksum = data.get("checksum")
    if not isinstance(checksum, str) or len(checksum) != 64:
        raise ValidationError(
            "Asset.checksum must be a 64-character hex string", "checksum"
        )
    _require_string(data, "uploaded_at")
    _require_string(data, "uploaded_by")
    return data


def validate_audit_entry(data: dict) -> dict:
    """Validate an audit log entry."""
    data = _require_object(data, "AuditEntry")
    _require_string(data, "timestamp")
    _require_string(data, "actor_id")
    _require_string(data, "action")
    _require_string(data, "resource_type")
    _require_string(data, "resource_id")
    for field in ("before_state", "after_state"):
        value = data.get(field)
        if value is not None and not isinstance(value, dict):
            raise ValidationError(
                f"AuditEntry.{field} must be an object or null", field
            )
    previous_hash = data.get("previous_hash")
    if not isinstance(previous_hash, str) or len(previous_hash) != 64:
        raise ValidationError(
            "AuditEntry.previous_hash must be a 64-character hex string",
            "previous_hash",
        )
    entry_hash = data.get("entry_hash")
    if not isinstance(entry_hash, str) or len(entry_hash) != 64:
        raise ValidationError(
            "AuditEntry.entry_hash must be a 64-character hex string",
            "entry_hash",
        )
    return data


def validate_permission_matrix(data: dict) -> dict:
    """Validate the role/permission matrix."""
    data = _require_object(data, "PermissionMatrix")
    roles = data.get("roles")
    if not isinstance(roles, list) or len(roles) != 2:
        raise ValidationError("PermissionMatrix.roles must have 2 entries", "roles")
    for role in roles:
        if role not in ("super_admin", "admin"):
            raise ValidationError(
                f"Invalid role '{role}'. Must be 'super_admin' or 'admin'",
                "roles",
            )
    permissions = data.get("permissions")
    if not isinstance(permissions, list) or len(permissions) != 2:
        raise ValidationError(
            "PermissionMatrix.permissions must have 2 entries", "permissions"
        )
    required_fields = [
        "role", "content_create", "content_edit", "content_delete",
        "content_publish", "content_preview", "section_create",
        "section_edit", "section_delete", "layout_modify",
        "media_upload", "media_select", "media_external_import",
        "revision_view", "revision_rollback", "user_admin", "role_admin",
        "audit_view", "audit_export",
    ]
    for i, perm in enumerate(permissions):
        perm = _require_object(perm, f"PermissionMatrix.permissions[{i}]")
        for field in required_fields:
            if field not in perm:
                raise ValidationError(
                    f"PermissionMatrix.permissions[{i}] missing field '{field}'",
                    field,
                )
            if field == "role":
                if perm[field] not in ("super_admin", "admin"):
                    raise ValidationError(
                        f"PermissionMatrix.permissions[{i}].role invalid",
                        "role",
                    )
            elif not isinstance(perm[field], bool):
                raise ValidationError(
                    f"PermissionMatrix.permissions[{i}].{field} must be boolean",
                    field,
                )
    invariants = data.get("invariants")
    if not isinstance(invariants, list) or len(invariants) < 6:
        raise ValidationError(
            "PermissionMatrix.invariants must have at least 6 entries",
            "invariants",
        )
    return data
