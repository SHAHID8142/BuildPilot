"""P8 CMS domain model.

Defines ContentType, Content, Section, Revision, and Asset entities.
All entities are plain dicts validated against the approved P8 schemas.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id() -> str:
    return uuid.uuid4().hex


class ContentType:
    """Defines a content type with fields and validation rules."""

    def __init__(self, name: str, fields: list[dict]) -> None:
        self.id = _id()
        self.name = name
        self.fields = fields
        self.created_at = _now()
        self.updated_at = _now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "fields": self.fields,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ContentType":
        ct = cls.__new__(cls)
        ct.id = data["id"]
        ct.name = data["name"]
        ct.fields = data["fields"]
        ct.created_at = data["created_at"]
        ct.updated_at = data["updated_at"]
        return ct


class Content:
    """A single content item of a defined type."""

    VALID_STATUSES = ("draft", "published", "archived")

    def __init__(
        self,
        type_id: str,
        title: str,
        body: str = "",
        author_id: str = "",
    ) -> None:
        self.id = _id()
        self.type_id = type_id
        self.title = title
        self.body = body
        self.status = "draft"
        self.author_id = author_id
        self.created_at = _now()
        self.updated_at = _now()
        self.published_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type_id": self.type_id,
            "title": self.title,
            "body": self.body,
            "status": self.status,
            "author_id": self.author_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "published_at": self.published_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Content":
        c = cls.__new__(cls)
        c.id = data["id"]
        c.type_id = data["type_id"]
        c.title = data["title"]
        c.body = data["body"]
        c.status = data["status"]
        c.author_id = data["author_id"]
        c.created_at = data["created_at"]
        c.updated_at = data["updated_at"]
        c.published_at = data.get("published_at")
        return c


class Section:
    """A structural section that composes content into pages."""

    def __init__(
        self,
        name: str,
        layout: str,
        content_ids: list[str] | None = None,
        order: int = 0,
    ) -> None:
        self.id = _id()
        self.name = name
        self.layout = layout
        self.content_ids = content_ids or []
        self.order = order

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "layout": self.layout,
            "content_ids": self.content_ids,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Section":
        s = cls.__new__(cls)
        s.id = data["id"]
        s.name = data["name"]
        s.layout = data["layout"]
        s.content_ids = data["content_ids"]
        s.order = data["order"]
        return s


class Revision:
    """Immutable revision history for content."""

    def __init__(
        self,
        content_id: str,
        version: int,
        body: str,
        author_id: str,
    ) -> None:
        self.id = _id()
        self.content_id = content_id
        self.version = version
        self.body = body
        self.author_id = author_id
        self.created_at = _now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content_id": self.content_id,
            "version": self.version,
            "body": self.body,
            "author_id": self.author_id,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Revision":
        r = cls.__new__(cls)
        r.id = data["id"]
        r.content_id = data["content_id"]
        r.version = data["version"]
        r.body = data["body"]
        r.author_id = data["author_id"]
        r.created_at = data["created_at"]
        return r


class Asset:
    """Unified asset reference for all sources."""

    VALID_SOURCES = ("upload", "existing_media", "external_url")

    def __init__(
        self,
        source: str,
        local_path: str,
        media_type: str,
        size_bytes: int,
        uploaded_by: str,
        original_url: str | None = None,
    ) -> None:
        self.id = _id()
        self.source = source
        self.original_url = original_url
        self.local_path = local_path
        self.media_type = media_type
        self.size_bytes = size_bytes
        self.checksum = ""
        self.uploaded_at = _now()
        self.uploaded_by = uploaded_by

    def compute_checksum(self, data: bytes) -> None:
        self.checksum = hashlib.sha256(data).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "original_url": self.original_url,
            "local_path": self.local_path,
            "media_type": self.media_type,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "uploaded_at": self.uploaded_at,
            "uploaded_by": self.uploaded_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Asset":
        a = cls.__new__(cls)
        a.id = data["id"]
        a.source = data["source"]
        a.original_url = data.get("original_url")
        a.local_path = data["local_path"]
        a.media_type = data["media_type"]
        a.size_bytes = data["size_bytes"]
        a.checksum = data["checksum"]
        a.uploaded_at = data["uploaded_at"]
        a.uploaded_by = data["uploaded_by"]
        return a
